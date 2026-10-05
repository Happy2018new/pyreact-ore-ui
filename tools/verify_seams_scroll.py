"""Targeted regression for joined edges, friend-page scrolling and page chrome.

This deliberately does not run the general component inventory.
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from verify_pressed_controls import PressVerification, ROOT, neighbor_difference
from capture_settings_pixels import operate


FRIEND_PROBE = '''from ore_demo.pyreact import host
from ore_demo import dev_probe
from ore_demo.oreui import OreFriendsPanel, OrePlayerGroup
from ore_demo.oreui._scroll import ScrollViewPrimitive
h=host._ACTIVE_HOST[0]
f=next(f for f in dev_probe._walk(h._root_fiber) if f.comp_type is OreFriendsPanel)
s=next(f for f in dev_probe._walk(f) if isinstance(f.comp_type,ScrollViewPrimitive))
c=h.GetBaseUIControl(s.native_path)
groups=[]
for g in dev_probe._walk(f):
    if g.comp_type is OrePlayerGroup:
        p=next(k for k in dev_probe._walk(g) if k.native_path)
        q=h.GetBaseUIControl(p.native_path)
        groups.append(dict(title=g.props.get('title'),position=q.GetGlobalPosition(),size=q.GetSize()))
_result=dict(tab=f.props['tab'],path=s.native_path,pos=s.comp_type.get_scroll_position(c),
    size=c.GetSize(),content=s.primitive_state.get('_scroll_content_signature'),groups=groups)
'''


class SeamVerification(PressVerification):
    def install(self):
        super().install()
        source=(ROOT/'tools/fixtures/seams_scene.py').read_text(encoding='utf8')
        self.code('import sys,types\nm=types.ModuleType("ore_seam_fixture")\n'
            'sys.modules[m.__name__]=m\nexec(%r,m.__dict__)\n_result=True\n'
            % source.encode('ascii','backslashreplace').decode('ascii'),'install-seams')

    def seam(self,kind,value=1,width=314.25):
        self.code('import ore_seam_fixture as f\nf.mount(%r,%r,%r)\n_result=True'
                  %(kind,value,width),'mount-seam')
        time.sleep(.25)
        self.screen=self.code('from ore_demo.pyreact import native\n_result=native.get_screen_size()', 'screen-size')
        return self.targets()

    def observe(self, index):
        return self.code('import ore_pressed_fixture as p\nimport ore_seam_fixture as s\n'
            '_result=p.snapshot(%d)\n_result["events"]=list(s.events)' % index, 'state-readback')


def verify(session,owner,output,only=None):
    r=SeamVerification(session,owner,output)
    r.install()
    report=dict(scope='joined edges, icon tabs, friend transitions, world separator and header',checks=[],samples=[])
    report['dimensions']=r.code('from ore_demo.pyreact import native\n'
        'g=native.clientApi.GetEngineCompFactory().CreateGame(native.clientApi.GetLevelId())\n'
        '_result=dict(logical=g.GetScreenSize(),viewport=g.GetScreenViewInfo())','dimensions')
    sizes=report['dimensions']
    sizes['client']=operate(session,owner)['client_size']
    if list(sizes['viewport'][:2])!=sizes['client']:
        raise AssertionError('Engine viewport and Windows client differ; resize the owned client before comparing pixels')
    if any(abs(sizes['logical'][axis]*4-sizes['viewport'][axis])>.001 for axis in (0,1)):
        raise AssertionError('Pixel fixtures need native scale 4; resize the client and verify its viewport first')
    def check(name,value,**details):
        report['checks'].append(dict(name=name,passed=bool(value),**details))
        report['passed']=all(x['passed'] for x in report['checks'])
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print(('PASS ' if value else 'FAIL ')+name,flush=True)

    if only is None or any(k in only for k in ('seams','segments','tabs','icons','world','header')):
        for kind,width in [('segments',314.25),('tabs',486),('icons',178)]:
            if only and 'seams' not in only and kind not in only:
                continue
            for value in range(2 if kind=='icons' else 3):
                ts=r.seam(kind,value,width)
                check('%s selected %d: shared boundaries land on physical pixels'%(kind,value),all(
                    abs(v*4-round(v*4))<.0002 for t in ts for v in
                    (t['position'][0],t['position'][0]+t['size'][0])))
                for index in ([value] if kind=='icons' else sorted(set([max(0,value-1),value,min(2,value+1)]))):
                    stem='%s-%d-%d'%(kind,value,index)
                    states=operate(session,owner,output=output/(stem+'.png'),sample=dict(
                        at=r.point(ts[index]),away=(.9,.08),context_box=[28,156,2016,292],
                        observe=lambda state:r.observe(index)))
                    a=states['states']
                    def frame(name):return np.asarray(Image.open(a[name]['output']).crop((28,156,2016,292)))
                    check(stem+': held frame stable',np.array_equal(frame('pressed'),frame('pressed-held')))
                    check(stem+': mouse released',states['mouse_released'])
                    report['samples'].append(dict(name=stem,targets=ts,states=states))
        for kind,width in [('world',154),('header',505.25)]:
            if only and 'seams' not in only and kind not in only:
                continue
            if kind=='header' and r.code('from ore_demo.pyreact import native\n_result=native.get_screen_size()[0]',
                    'header-screen-width') < width:
                raise AssertionError('Header comparison needs at least a 2024-pixel client at scale 4')
            ts=r.seam(kind,width=width)
            for i,t in enumerate(ts):
                stem=kind+'-'+str(i)
                box=[0,156,2024,260] if kind=='header' else [28,156,2016,680]
                states=operate(session,owner,output=output/(stem+'.png'),sample=dict(
                    at=r.point(t),away=(.9,.08),context_box=box,observe=lambda state:r.observe(i)))
                report['samples'].append(dict(name=stem,targets=ts,states=states))
                check(stem+': mouse released',states['mouse_released'])
                if kind=='header':
                    a=states['states']
                    probes={s:m['observation']['runtime'] for s,m in a.items()}
                    check(stem+': native default is not hover',not probes['default']['hover']['visible'])
                    check(stem+': native pressed visible',probes['pressed']['pressed']['visible'])
                    check(stem+': actual button held',all(a[s]['mouse_left_down_before'] and
                        a[s]['mouse_left_down_after'] for s in ('pressed','pressed-held')))
                    check(stem+': no callback while held or released outside',
                        probes['default']['events']==probes['pressed']['events']==probes['released']['events'])
                    x,y=t['position'];w,h=t['size']
                    target_box=[round(x*4),round(y*4),round((x+w)*4),round((y+h)*4)]
                    changed=neighbor_difference(a,box,target_box)
                    check(stem+': neighbors unchanged',changed==0,differing_pixels=changed)
                    frames=[np.asarray(Image.open(a[s]['output']).crop(box)) for s in ('pressed','pressed-held')]
                    check(stem+': held frame stable',np.array_equal(*frames))
                    before=list(probes['released']['events'])
                    r.tap_at(r.point(t),'click-'+stem)
                    after=r.code('import ore_seam_fixture as f\n_result=list(f.events)','callback-'+stem)
                    check(stem+': click invokes correct callback exactly once',
                        after==before+['back' if i==0 else 'social'],events=after)

    if only is None or 'friends' in only:
        r.mount()
        r.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
               'f=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) '
               'if f.key=="ore_settings_social")\nf.props["onClick"]()\n_result=True','friends-open')
        time.sleep(.2)
        for position in (0,60,119.75,120):
            r.code(FRIEND_PROBE.replace('_result=dict(',
                's.comp_type.scroll_to(c,%r)\n_result=dict('%position),'scroll-position')
            time.sleep(.3)
            data=r.code(FRIEND_PROBE,'group-position')
            name='friends-scroll-'+str(position)
            r.png(name)
            group=next(g for g in data['groups'] if g['title']=='离线')
            x,y=group['position']
            # The empty left padding in the heading must connect to its bar.
            # Text is outside this explicit seam-only assertion.
            box=[round((x+1)*4),round((y+10)*4),round((x+2)*4),round((y+11)*4)]
            image=np.asarray(Image.open(output/(name+'.png')).convert('RGB').crop(box))
            check(name+': heading joins bar without a black cut',bool(np.all(image==[208,209,212])),box=box)
        transitions=[]
        for target in ('team','friends','team'):
            if target=='team':
                r.code(FRIEND_PROBE.replace('_result=dict(',
                    's.comp_type.scroll_to_percent(c,100)\n_result=dict('),'scroll-bottom')
                time.sleep(.2)
            before=r.code(FRIEND_PROBE,'before-tab')
            at=r.scoped_at('ore_friends_tabs','1' if target=='team' else '0')
            frames=[]
            with ThreadPoolExecutor(max_workers=1) as pool:
                action=pool.submit(r.tap_at,at,'tab-'+target)
                start=time.monotonic()
                for unused in range(22):
                    data=r.code(FRIEND_PROBE,'transition-frame')
                    data['time']=time.monotonic()-start
                    frames.append(data)
                    time.sleep(.015)
                action.result()
            changed=[f for f in frames if f['tab']==target]
            check('switch to '+target+': starts at zero without rebound',
                  bool(changed) and all(f['pos']==0 for f in changed))
            check('switch to '+target+': independent native scroll',bool(changed) and
                  all(f['path']!=before['path'] for f in changed))
            transitions.append(dict(before=before,target=target,frames=frames))
            r.png('tab-'+target)
        report['transitions']=transitions
    report['passed']=all(c['passed'] for c in report['checks'])
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('--owner',required=True)
    p.add_argument('--output',type=Path,default=ROOT/'.runtime/seams-scroll/after')
    p.add_argument('--only',nargs='+',choices=('seams','friends','segments','tabs','icons','world','header'))
    a=p.parse_args()
    raise SystemExit(0 if verify(a.session,a.owner,a.output,a.only)['passed'] else 1)
