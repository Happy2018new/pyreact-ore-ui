"""Measure real scrollbar drags and SDK FPS on each public demo page.

FPS samples are engine estimates, not PresentMon frame timings. Keep unprofiled
samples separate from Python CPU instrumentation, which changes frame cost.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from verify_seams_scroll import SeamVerification
from capture_settings_pixels import operate


FRAME_CLOCK = '''from collections import deque as _OreDeque
import time as _ore_time
import sys as _ore_sys
_ore_nav=_ore_sys.modules["ore_demo.pyreact.navigator"]
_OreScreen=_ore_nav.NavigatorScreen
if not hasattr(_OreScreen,'_ore_perf_original_update'):
    _OreScreen._ore_perf_original_update=_OreScreen.Update
    _OreScreen._ore_perf_times=_OreDeque(maxlen=12000)
    _ore_original=_OreScreen._ore_perf_original_update
    def _ore_sampled_update(self):
        if self._navigator_active:
            _OreScreen._ore_perf_times.append(_ore_time.clock())
        return _ore_original(self)
    _OreScreen.Update=_ore_sampled_update
_OreScreen._ore_perf_times.clear()
_result=True
'''

FRAME_READ = '''import sys as _ore_sys
_ore_nav=_ore_sys.modules["ore_demo.pyreact.navigator"]
_times=list(_ore_nav.NavigatorScreen._ore_perf_times)
_delta=sorted(max(0.0,(_times[i]-_times[i-1])*1000.0) for i in range(1,len(_times)))
def _pct(p):
    if not _delta:return None
    return round(_delta[min(len(_delta)-1,int((len(_delta)-1)*p))],3)
_result=dict(updates=len(_times),p50_ms=_pct(.50),p95_ms=_pct(.95),p99_ms=_pct(.99),
    max_ms=round(_delta[-1],3) if _delta else None,
    over_16_7=sum(1 for x in _delta if x>16.7),over_33_3=sum(1 for x in _delta if x>33.3),
    over_50=sum(1 for x in _delta if x>50))
'''

FRAME_CLEANUP = '''import sys as _ore_sys
_ore_nav=_ore_sys.modules["ore_demo.pyreact.navigator"]
_OreScreen=_ore_nav.NavigatorScreen
if hasattr(_OreScreen,'_ore_perf_original_update'):
    _OreScreen.Update=_OreScreen._ore_perf_original_update
    del _OreScreen._ore_perf_original_update
    del _OreScreen._ore_perf_times
_result=True
'''

PROBE = '''from ore_demo.pyreact import host,native
from ore_demo import dev_probe
from ore_demo.oreui._scroll import ScrollViewPrimitive
h=host._ACTIVE_HOST[0]
fs=list(dev_probe._walk(h._root_fiber))
ss=[f for f in fs if isinstance(f.comp_type,ScrollViewPrimitive) and f.props.get('active',True) and h.GetBaseUIControl(f.native_path).GetGlobalPosition()[0]>100]
f=ss[0]
c=h.GetBaseUIControl(f.native_path)
g=native.clientApi.GetEngineCompFactory().CreateGame(native.clientApi.GetLevelId())
_result=dict(path=f.native_path,position=c.GetGlobalPosition(),size=c.GetSize(),
    content=f.primitive_state.get('_scroll_content_signature'),scroll=f.comp_type.get_scroll_position(c),
    fps=g.GetFps(),fibers=len(fs),native=sum(bool(x.native_path) for x in fs),
    glyphs=sum(len(x.primitive_state.get('ore_glyph_pool',[])) for x in fs),screen=native.get_screen_size())
'''


def _start_tracy(script, output, label, seconds):
    store = output / 'tracy'
    store.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(script), '--store-dir', str(store), 'capture',
               '--seconds', str(seconds), '--label', label, '--top', '30']
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _finish_tracy(process, timeout):
    stdout, stderr = process.communicate(timeout=timeout)
    text = stdout.decode('utf8')
    if process.returncode:
        raise RuntimeError('Tracy capture failed: ' + stderr.decode('utf8')[-1000:])
    result = json.loads(text)
    if not result.get('ok'):
        raise RuntimeError('Tracy capture returned an error: ' + text)
    return result


def run(session, owner, output, suite, pages=None, cpu=False, motion='thumb',
        tracy_cli=None, tracy_seconds=5):
    output.mkdir(parents=True, exist_ok=True)
    r = SeamVerification(session, owner, output)
    if suite == 'playground':
        r.mount()
        inventory = r.code('from ore_demo.settings_playground import PAGES\n_result=[p[1] for p in PAGES]', 'pages')
    else:
        r.code('from ore_demo.pyreact import navigator\nnavigator.clear()\n_result=True', 'close')
        time.sleep(.2)
        r.code('from ore_demo.pyreact import navigator\nfrom ore_demo.settings_replica import OreSettingsReplica\n'
               'navigator.push(OreSettingsReplica)\n_result=True', 'open')
        time.sleep(.6)
        inventory = r.code('from ore_demo.settings_catalog import NAVIGATION\n_result=[name for _,items in NAVIGATION for _,name in items]', 'pages')
    report = dict(suite=suite, motion=motion, cpu_instrumented=cpu, session=str(session), pages=[])
    if tracy_cli and cpu:
        raise ValueError('Use either Tracy Native capture or MCDK Python CPU capture per run')
    if not tracy_cli:
        r.code(FRAME_CLOCK, 'install-frame-clock')
    try:
        for page in pages or inventory:
            if suite == 'playground':
                r.page(page)
            else:
                r.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
                    'f=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) if f.key==%r)\n'
                    'f.props["onClick"]()\n_result=True' % ('settings_page_'+page), 'select-'+page)
            time.sleep(1.8)
            # Keep the idle and input captures in the same foreground state. The
            # desktop input helper activates the game, so without this baseline
            # step a background-throttled idle sample is compared to foreground
            # scrolling and can look like a false FPS improvement.
            operate(session, owner)
            before = r.code(PROBE, 'before-'+page)
            if tracy_cli:
                idle_job = _start_tracy(tracy_cli, output, 'ore_%s_%s_idle' % (suite, page), tracy_seconds)
                idle = _finish_tracy(idle_job, tracy_seconds + 90)
            else:
                r.code(FRAME_CLOCK, 'reset-idle-clock-'+page)
                time.sleep(1.5)
                idle = r.code(FRAME_READ, 'idle-frame-clock-'+page)
            x,y=before['position']; w,h=before['size']; sw,sh=before['screen']
            content_h=before['content'][1]
            # Start in the measured thumb, drag it along the track, then return.
            thumb=max(6.,(h-8)*min(1.,h/content_h))
            left=[(x+w-5)/sw,(y+4+thumb/2)/sh]
            right=[left[0],(y+h-4-thumb/2)/sh]
            steps=[dict(do='move',at=left),dict(do='wait',ms=200),
                dict(do='drag',**{'from':left,'to':right,'segments':50}),dict(do='wait',ms=200)]
            if motion == 'wheel':
                steps=[dict(do='scroll',at=[(x+w*.6)/sw,(y+h*.5)/sh],amount=-2)
                       for unused in range(32)]
            elif motion == 'touch':
                high=[(x+w*.35)/sw,(y+h*.25)/sh]
                low=[high[0],(y+h*.85)/sh]
                steps=[dict(do='move',at=low),dict(do='wait',ms=200),
                    dict(do='drag',**{'from':low,'to':high,'segments':40}),dict(do='wait',ms=200)]
            job=None
            if cpu:
                started=r.client.call('mc_profiler',dict(op='/start',args=dict(kind='python.cpu',target='client',clock='wall',duration_seconds=6,storage='disk')))
                job=started['structuredContent']['job']['id']
            if tracy_cli:
                scroll_job = _start_tracy(tracy_cli, output, 'ore_%s_%s_%s' % (suite, page, motion), tracy_seconds)
                time.sleep(.25)
            else:
                r.code(FRAME_CLOCK, 'reset-scroll-clock-'+page)
            operate(session,owner,steps=steps)
            scrolling = (_finish_tracy(scroll_job, tracy_seconds + 90) if tracy_cli else
                         r.code(FRAME_READ, 'scroll-frame-clock-'+page))
            after=r.code(PROBE,'after-'+page)
            row=dict(page=page,before=before,after=after,idle=idle,scrolling=scrolling,
                     scrolled=abs(after['scroll']-before['scroll'])>.5)
            if cpu:
                while True:
                    status=r.client.call('mc_profiler',dict(op='/status',args=dict(job_id=job)))
                    if status['structuredContent']['job']['state'] in ('completed','failed','cancelled'):
                        break
                    time.sleep(.3)
                query=r.client.call('mc_profiler',dict(op='/query',args=dict(job_id=job,view='hotspots',limit=50)))
                (output/(page+'-cpu.json')).write_text(json.dumps(query,indent=2),'utf8')
                row['job']=job
            report['pages'].append(row)
            (output/'report.json').write_text(json.dumps(report,indent=2),'utf8')
            print(json.dumps(dict(page=page,scrolled=row['scrolled'],idle=idle,scrolling=scrolling,
                                  native=before['native'],glyphs=before['glyphs'])),flush=True)
    finally:
        if not tracy_cli:
            r.code(FRAME_CLEANUP, 'remove-frame-clock')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--session',required=True,type=Path);p.add_argument('--owner',required=True)
    p.add_argument('--output',required=True,type=Path);p.add_argument('--suite',choices=('playground','settings'),required=True)
    p.add_argument('--pages',nargs='+');p.add_argument('--cpu',action='store_true')
    p.add_argument('--motion',choices=('thumb','wheel','touch'),default='thumb')
    p.add_argument('--tracy-cli',type=Path,help='Use a Tracy CLI from another project for native frame and zone capture')
    p.add_argument('--tracy-seconds',type=int,default=5)
    p.add_argument('--native-touch',action='store_true',help='Explicit SDK fallback when the development F11 shortcut does not switch mode')
    a=p.parse_args()
    r=SeamVerification(a.session,a.owner,a.output)
    original_touch=r.state()['simulated']
    requested_touch=a.motion=='touch'
    def mode(touch):
        if r.state()['simulated']==touch:
            return
        r.code('from ore_demo.pyreact import navigator\nnavigator.clear()\n_result=True','close-for-mode')
        time.sleep(.3)
        if r.code('from ore_demo.pyreact import navigator\n_result=navigator.depth','closed')!=0:
            raise AssertionError('UI must close before F11')
        if a.native_touch:
            r.code('import mod.client.extraClientApi as c\n'
                'c.GetEngineCompFactory().CreateGame(c.GetLevelId()).SimulateTouchWithMouse(%r)\n_result=True'%touch,'native-mode')
            time.sleep(.4)
        else:
            r.input([dict(do='key',keys='f11',hold_ms=150),dict(do='wait',ms=400)],'mode-f11')
        if r.state()['simulated']!=touch:
            raise AssertionError('F11 did not change native touch mode')
    try:
        mode(requested_touch)
        report=run(a.session,a.owner,a.output,a.suite,a.pages,a.cpu,a.motion,
                   a.tracy_cli,a.tracy_seconds)
        report['mode_method']='SimulateTouchWithMouse' if a.native_touch else 'F11'
        (a.output/'report.json').write_text(json.dumps(report,indent=2),'utf8')
    finally:
        mode(original_touch)
