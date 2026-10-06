"""Scoped native checks for slider fixes and the separate Settings example."""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image

from verify_seams_scroll import SeamVerification
from capture_settings_pixels import operate


WALK = 'from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\nh=host._ACTIVE_HOST[0]\n'


def run(session, owner, output):
    r=SeamVerification(session,owner,output)
    report=dict(checks=[],pages=[],session=str(session))
    def check(name, passed, **details):
        report['checks'].append(dict(name=name,passed=bool(passed),**details))
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
        print(('PASS ' if passed else 'FAIL ')+name,flush=True)

    dimensions=r.code('from ore_demo.pyreact import native\n'
        'g=native.clientApi.GetEngineCompFactory().CreateGame(native.clientApi.GetLevelId())\n'
        '_result=dict(logical=g.GetScreenSize(),viewport=g.GetScreenViewInfo())','dimensions')
    dimensions['client']=operate(session,owner)['client_size']
    report['dimensions']=dimensions
    check('matching native viewport at scale four',dimensions['client']==[2020,1156]
        and list(dimensions['viewport'][:2])==[2020,1156] and list(dimensions['logical'])==[505,289])

    r.mount();r.page('sliders')
    before=r.business()
    value=r.drag_slider('lab_slider',.73)
    after=r.business()
    check('continuous drag reaches requested value',abs(value-.73)<.015,value=value)
    check('continuous draft commits once to page',after['events']==before['events']+1,
          before=before['events'],after=after['events'])
    check('continuous release preserves its final value',abs(after['values']['volume']-value)<.002)
    r.png('playground-sliders')

    r.install_fixture();r.fixture('sliders')
    frame=r.frame('fixture_slider')
    r.png('ticks-active')
    def cap(name, expected):
        arr=np.asarray(Image.open(output/(name+'.png')).convert('RGB'))
        x,y=frame['position'];w,h=frame['size']
        # Native cap is 1 by 6 logical pixels, centered in the 16-unit slider.
        box=[round((x+w-1)*4),round((y+5)*4),round((x+w)*4),round((y+11)*4)]
        patch=arr[box[1]:box[3],box[0]:box[2]]
        check(name+' right endpoint closes without green bleed',bool(np.all(patch==expected)),box=box)
    cap('ticks-active',[30,30,31])
    r.fixture('sliders',True);r.png('ticks-disabled')
    cap('ticks-disabled',[140,141,144])
    data=r.code(WALK+'from ore_demo.oreui._slider import SliderPrimitive\n'
        'f=next(f for f in dev_probe._walk(h._root_fiber) if isinstance(f.comp_type,SliderPrimitive))\n'
        '_result=dict(ticks=f.primitive_state.get("ore_ticks"),values=[c.asImage().GetSprite() for c in f.primitive_state["ore_tick_pool"]])','disabled-ticks')
    check('disabled ticks distinguish filled and unfilled sections',
        [v.rsplit('/',1)[-1] for v in data['values']]==['cap_disabled','cap_disabled','step_disabled'],data=data)

    r.install();targets=r.seam('world',width=154)
    frame=r.frame('target');r.png('world-preview')
    arr=np.asarray(Image.open(output/'world-preview.png').convert('RGB'))
    x,y=frame['position'];w,h=frame['size']
    line=arr[round((y+1)*4):round((y+2)*4),round((x+2)*4):round((x+w-2)*4)]
    check('world preview retains the upper bevel band',len(np.unique(line.reshape(-1,3),axis=0))==1)

    r.mount();r.page('dropdowns');r.tap_at(r.at('lab_long_dropdown'),'long-dropdown-open')
    r.png('long-dropdown')
    menu=r.code(WALK+'from ore_demo.oreui._scroll import ScrollViewPrimitive\n'
        '_result=[dict(position=h.GetBaseUIControl(f.native_path).GetGlobalPosition(),size=h.GetBaseUIControl(f.native_path).GetSize(),gutter=f.children[0].style.get("paddingRight")) '
        'for f in dev_probe._walk(h._root_fiber) if isinstance(f.comp_type,ScrollViewPrimitive) and f.children and f.children[0].style and f.children[0].style.get("paddingRight")==10]','dropdown-gutter')
    check('long dropdown reserves space beside option checks',bool(menu),scrolls=menu)

    r.code('from ore_demo.pyreact import navigator\nfrom ore_demo.settings_replica import OreSettingsReplica\n'
        'navigator.reset(OreSettingsReplica)\n_result=True','open-replica')
    time.sleep(.6)
    pages=r.code('from ore_demo.settings_catalog import NAVIGATION\n_result=[n for _,items in NAVIGATION for _,n in items]','page-inventory')
    for page in pages:
        r.code(WALK+'f=next(f for f in dev_probe._walk(h._root_fiber) if f.key==%r)\n'
            'f.props["onClick"]()\n_result=True'%('settings_page_'+page),'select-'+page)
        time.sleep(.45)
        state=r.code(WALK+'from ore_demo.settings_replica import ReplicaPage\n'
            'from ore_demo.oreui import OreStatusLabel\nfrom ore_demo.oreui._scroll import ScrollViewPrimitive\n'
            'fs=list(dev_probe._walk(h._root_fiber))\n'
            's=next(f for f in fs if isinstance(f.comp_type,ScrollViewPrimitive) and f.props.get("active",True) and h.GetBaseUIControl(f.native_path).GetGlobalPosition()[0]>100)\n'
            'page_fs=list(dev_probe._walk(s))\n'
            '_result=dict(content=[f.props["page"] for f in page_fs if f.comp_type is ReplicaPage],placeholder=any(f.comp_type is OreStatusLabel for f in page_fs),'
            'scroll=s.comp_type.get_scroll_position(h.GetBaseUIControl(s.native_path)),native=sum(bool(f.native_path) for f in fs))','page-state')
        placeholder=page in ('party','subscriptions','resources')
        check(page+' renders its requested content',state['placeholder']==placeholder and
              (placeholder or state['content']==[page]),state=state)
        check(page+' opens at the top',state['scroll']==0)
        r.png('settings-'+page)
        report['pages'].append(dict(page=page,**state))
    r.code(WALK+'f=next(f for f in dev_probe._walk(h._root_fiber) if f.key=="settings_page_accessibility")\n'
        'f.props["onClick"]()\n_result=True','leave-accessibility')
    time.sleep(.6)
    r.png('settings-accessibility')
    report['passed']=all(c['passed'] for c in report['checks'])
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',required=True,type=Path)
    p.add_argument('--owner',required=True);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();raise SystemExit(0 if run(a.session,a.owner,a.output)['passed'] else 1)
