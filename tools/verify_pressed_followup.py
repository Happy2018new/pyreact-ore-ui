"""Focused cold-start list clicks, simulated touch, and scrollbar gutter checks."""
import argparse
import json
import time
from pathlib import Path

from capture_settings_pixels import operate
from verify_pressed_controls import PressVerification


def verify(session, owner, output):
    r=PressVerification(session,owner,output)
    r.install()
    checks=[]
    transitions=[]
    report=dict(checks=checks,transitions=transitions,passed=False,
                touch_scope='NetEase simulated touch on Windows; not a physical phone')
    def check(name,value):
        checks.append(dict(name=name,passed=bool(value)))
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print(('PASS ' if value else 'FAIL ')+name,flush=True)
    for kind in ('packs','players'):
        targets=r.scene(dict(kind=kind))
        for target in targets:
            r.tap_at(r.point(target),'cold-click')
        events=r.code('import ore_pressed_fixture as f\n_result=f.events','cold-events-'+kind)
        check('cold start '+kind+' callbacks exactly once',len(events)==len(targets))
    try:
        r.code('from ore_demo.pyreact import navigator\nnavigator.clear()\n_result=navigator.depth','close-ui')
        operate(session,owner,steps=[dict(do='key',key='f11'),dict(do='wait',ms=350)])
        method='F11'
        if not r.state()['simulated']:
            method='GameComponentClient.SimulateTouchWithMouse'
            r.code('import mod.client.extraClientApi as c\n'
                'c.GetEngineCompFactory().CreateGame(c.GetLevelId()).SimulateTouchWithMouse(True)\n_result=True','touch-api')
        r.scene(dict(kind='secondary'));r.tap_at((.9,.8),'touch-mode-input')
        mode=r.state();transitions.append(dict(method=method,actual=mode))
        check('native touch mode confirmed',mode['simulated'] and mode['touch'])
        if not (mode['simulated'] and mode['touch']):
            raise RuntimeError('Cannot test in an unconfirmed input mode')
        for kind,index in [('secondary',0),('segments',1),('tabs',0),('packs',1),('packs',2),
                           ('players',1),('icons',1),('switch',0)]:
            target,box,result=r.sample(dict(kind=kind),index,'touch-'+kind+'-'+str(index))
            probe=result['states']['pressed']['observation']['runtime']
            check('touch held state '+kind+str(index),probe.get('pressed',{}).get('visible') is True)
            if 'content_position' in probe:
                check('touch content follows face '+kind,probe['content_position']==[0,target['press_offset']])
            # Mount again so counters cannot be affected by outside-release
            # semantics, then count the actual native inside-up dispatcher.
            target=r.scene(dict(kind=kind))[index]
            r.code('''from ore_demo.pyreact import host
h=host._ACTIVE_HOST[0]
h._touch_count=[]
old=h._button_handlers[%r]
def clicked(callback=old[2]):
    h._touch_count.append(1)
    if callback:
        callback()
h._button_handlers[%r]=(old[0],old[1],clicked)
_result=True
'''%(target['path'],target['path']),'touch-count')
            r.tap_at(r.point(target),'touch-release')
            count=r.code('from ore_demo.pyreact import host\n_result=len(host._ACTIVE_HOST[0]._touch_count)','touch-clicks')
            check('touch inside release once '+kind+str(index),count==1)
        target=r.scene(dict(kind='slider',selected=True))[0]
        x,y=target['position'];w,h=target['size']
        operate(session,owner,steps=[dict(do='drag',**{'from':r.point(target),'to':[(x+w)/504,(y+h/2)/291],'segments':12})])
        events=r.code('import ore_pressed_fixture as f\n_result=f.events','touch-slider-events')
        check('touch stepped slider reaches final integer',bool(events) and events[-1]==['slider',4])
        for kind in ('dialog','drawer','menu','friends'):
            r.scene(dict(kind=kind));r.tap_at((.04,.9),'touch-backdrop')
            events=r.code('import ore_pressed_fixture as f\n_result=f.events','touch-backdrop-events')
            check('touch backdrop closes '+kind,events==[['close',None]])
    finally:
        r.code('from ore_demo.pyreact import navigator\nimport mod.client.extraClientApi as c\n'
            'navigator.clear()\nc.GetEngineCompFactory().CreateGame(c.GetLevelId()).SimulateTouchWithMouse(False)\n_result=True','restore-mouse')
        r.scene(dict(kind='secondary'));r.tap_at((.9,.8),'mouse-mode-input')
        mode=r.state();transitions.append(dict(method='GameComponentClient.SimulateTouchWithMouse',actual=mode))
        check('mouse mode restored',not mode['simulated'] and not mode['touch'])
    scroll_checks(r,check)
    report=dict(checks=checks,transitions=transitions,passed=all(c['passed'] for c in checks),
                touch_scope='NetEase simulated touch on Windows; not a physical phone')
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report


def scroll_checks(r,check):
    session,owner,output=r.session,r.owner,r.output
    r.mount();r.page('containers')
    # Expand one row to make a real scroll range at the reference client size.
    if r.business()['values']['packOpen'] is None:
        r.tap_at(r.scoped_at('lab_pack_0','ore_pack_details'),'expand-first-pack')
    r.png('scrollbar-gutter')
    geometry=r.code('''from ore_demo.pyreact import host
from ore_demo import dev_probe
from ore_demo.pyreact.primitives import ScrollViewPrimitive
import ore_pressed_fixture as f
h=host._ACTIVE_HOST[0]
group=next(x for x in dev_probe._walk(h._root_fiber) if x.key=='lab_scroll_containers_0')
sf=next(x for x in dev_probe._walk(group) if isinstance(x.comp_type,ScrollViewPrimitive))
p=sf.comp_type._scrollbar_track_path(sf.native_path,h)
c=h.GetBaseUIControl(p)
_result=dict(track=dict(path=p,position=c.GetGlobalPosition(),size=c.GetSize(),children=h.GetChildrenName(p)),
             scroll_path=sf.native_path,scroll_before=ScrollViewPrimitive.get_scroll_position(h.GetBaseUIControl(sf.native_path)),
             targets=[t for _,t in f.interactive() if 'lab_pack_tabs' in t['keys'] or 'ore_pack_action' in t['keys']])
''','gutter-geometry')
    track=geometry['track'];left=track['position'][0]
    check('scrollbar does not overlap tabs or pack actions',all(
        t['position'][0]+t['size'][0]<=left for t in geometry['targets']))
    x,y=track['position'];w,h=track['size']
    operate(session,owner,steps=[dict(do='drag',**{'from':[(x+w/2)/504,(y+h/2)/291],
        'to':[(x+w/2)/504,(y+h-2)/291],'segments':12})])
    after=r.code('from ore_demo.pyreact import host,ScrollView\n'
        '_result=ScrollView.get_scroll_position(host._ACTIVE_HOST[0].GetBaseUIControl(%r))'%geometry['scroll_path'],
        'scrollbar-drag-position')
    geometry['scroll_after']=after
    check('scrollbar thumb drag changes content position',after is not None and after>geometry['scroll_before'])
    r.png('scrollbar-dragged')
    (output/'gutter-geometry.json').write_text(json.dumps(geometry,indent=2),encoding='utf8')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--session',required=True);p.add_argument('--owner',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--scroll-only',action='store_true')
    args=p.parse_args()
    if args.scroll_only:
        r=PressVerification(args.session,args.owner,args.output)
        r.install()
        result=json.loads((args.output/'report.json').read_text(encoding='utf8'))
        def check(name,value):
            result['checks'].append(dict(name=name,passed=bool(value)))
            print(('PASS ' if value else 'FAIL ')+name,flush=True)
        scroll_checks(r,check)
        result['passed']=all(c['passed'] for c in result['checks'])
        (args.output/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    else:
        result=verify(args.session,args.owner,args.output)
    raise SystemExit(0 if result['passed'] else 1)
