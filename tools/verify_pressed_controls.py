"""Hold each public input in an owned game; retain pixels and native readback.

Only interaction states and scrollbar clearance are in scope. Comparison with
the recorded international specimens is performed by publish_pressed_audit.py.
"""
import argparse
import atexit
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from verify_component_boundaries import BoundaryVerification
from capture_settings_pixels import operate

ROOT=Path(__file__).resolve().parents[1]


def neighbor_difference(states, context_box, target_box):
    before=np.asarray(Image.open(states['default']['output']).crop(context_box))
    held=np.asarray(Image.open(states['pressed']['output']).crop(context_box))
    changed=np.any(before!=held,axis=2)
    left,top,right,bottom=target_box
    x,y,_,_=context_box
    changed[max(0,top-y):max(0,bottom-y),max(0,left-x):max(0,right-x)]=False
    return int(changed.sum())


def configurations():
    cases=[]
    for kind in ('primary','secondary','neutral','destructive','realms'):
        for selected,disabled in ((False,False),(True,False),(False,True)):
            cases.append(dict(kind=kind,selected=selected,disabled=disabled))
    for kind in ('segments','tabs','icon-tabs','navigation','packs','players','group',
                 'switch','slider','field','search','icons','extras','worlds',
                 'world-navigation','dialog','drawer','menu','friends','settings','dropdown'):
        cases.append(dict(kind=kind))
    cases += [dict(kind=k,selected=s,disabled=d) for k,s,d in [
        ('switch',True,False),('switch',False,True),('switch',True,True),
        ('slider',True,False),('slider',False,True),('slider',True,True),
        ('segments',False,True),('packs',False,True),('icons',False,True),
        ('extras',True,True),('dropdown',False,True),('field',False,True)]]
    cases.extend([dict(kind='dropdown',opened=True),dict(kind='slider-reference')])
    return cases


class PressVerification(BoundaryVerification):
    def __init__(self,session,owner,output):
        super().__init__(session,owner,output)
        sys.path.insert(0,str(ROOT/'.agents/skills/pyreact-debugging/scripts'))
        from mcdk import Client, return_value
        # Reuse the skill's bound client. It still validates process identity
        # and the in-game session token before every read or mutation.
        os.environ['MCDEV_SESSION_FILE']=str(session)
        os.environ['MCDEV_OWNER']=owner
        self.client=Client().__enter__()
        self.decode=return_value
        atexit.register(self.client.close)

    def code(self,source,name='exec'):
        source=source.encode('ascii','backslashreplace').decode('ascii')
        (self.output/(name+'.py')).write_text(source,encoding='utf8')
        return self.decode(self.client.call('execute_code',dict(code=source,is_client=True,direct_return=True)))

    def install(self):
        source=(ROOT/'tools/fixtures/pressed_scene.py').read_text(encoding='utf8')
        self.code('import sys,types\nm=types.ModuleType("ore_pressed_fixture")\n'
            'sys.modules[m.__name__]=m\nexec(%r,m.__dict__)\n_result=True\n'
            % source.encode('ascii','backslashreplace').decode('ascii'),'install-pressed')

    def scene(self,case):
        self.code('import ore_pressed_fixture as f\nf.mount(%r,%r,%r)\n_result=True\n'
            % (case['kind'],case.get('selected',False),case.get('disabled',False)),'mount-pressed')
        time.sleep(.35)
        if case.get('opened'):
            t=self.targets()[0]
            self.tap_at(self.point(t),'open-dropdown')
        targets=self.targets()
        if not targets:
            raise RuntimeError('Fixture did not mount; do not report an empty inventory as tested')
        return targets

    def targets(self):
        return self.code('import ore_pressed_fixture as f\n_result=[r for _,r in f.interactive()]','targets')

    def point(self,target):
        x,y=target['position'];w,h=target['size']
        if 'Slider' in target['type']:
            return [(x+w*target['value']/max(1,target['steps']-1))/self.screen[0],(y+h/2)/self.screen[1]]
        return [(x+w/2)/self.screen[0],(y+h/2)/self.screen[1]]

    def sample(self,case,index,stem):
        target=self.scene(case)[index]
        x,y=target['position'];w,h=target['size']
        # Whole fixture plus a logical pixel of surrounding space. Modal cases
        # use the complete screen; state metrics still use the target rectangle.
        modal=case['kind'] in ('dialog','drawer','menu','friends','settings') or case.get('opened')
        if modal:
            box=[0,100,2016,1164]
        else:
            f=self.frame('bounds');bx,by=f['position'];bw,bh=f['size']
            box=[max(0,round((bx-6)*4)),max(100,round((by-1)*4)),
                 min(2016,round((bx+bw+6)*4)),min(1164,round((by+bh+1)*4))]
        def observe(state):
            return self.code('import ore_pressed_fixture as f\n_result=f.snapshot(%d)\n'%index,'readback')
        result=operate(self.session,self.owner,output=self.output/(stem+'.png'),sample=dict(
            at=self.point(target),away=(.85,.95) if modal else (.9,.1),context_box=box,
            control_type='slider' if 'Slider' in target['type'] else 'button',observe=observe))
        return target,box,result


def verify(session,owner,output,only=None):
    r=PressVerification(session,owner,output)
    r.install()
    previous=output/'report.json'
    rows=([row for row in json.loads(previous.read_text(encoding='utf8'))['rows']
           if row['case']['kind'] not in only] if only and previous.exists() else [])
    report=dict(scope='public clickable controls: held states and release',rows=rows)
    for case in configurations():
        if only and case['kind'] not in only:
            continue
        targets=r.scene(case)
        for index,t in enumerate(targets):
            if case.get('opened') and index==0:
                continue
            stem='%s%s%s%s-%02d'%(case['kind'],'-selected' if case.get('selected') else '',
                '-disabled' if case.get('disabled') else '', '-open' if case.get('opened') else '',index)
            target,box,result=r.sample(case,index,stem)
            states=result['states'];probes={s:m['observation']['runtime'] for s,m in states.items()}
            checks={}
            checks['physical_button_held']=all(states[s]['mouse_left_down_before'] and
                states[s]['mouse_left_down_after'] for s in ('pressed','pressed-held'))
            checks['physical_button_released']=result['mouse_released']
            pressed=probes['pressed'];released=probes['released']
            button='Button' in target['type'] or 'Pressable' in target['type']
            if button:
                checks['native_default_not_hovered']=probes['default'].get('hover',{}).get('visible') is False
                checks['native_pressed_visible']=pressed.get('pressed',{}).get('visible') is True
                checks['no_click_while_held']=pressed['events']==probes['default']['events']
                checks['outside_release_does_not_click']=released['events']==probes['default']['events']
            if 'content_position' in pressed:
                checks['content_depressed']=pressed['content_position']==[0.0,target['press_offset']]
                checks['face_depressed']=pressed['pressed']['position']==[0.0,target['press_offset']]
                checks['move_out_restores_content']=probes['pressed-outside'].get('content_position')==[0.0,0.0]
                again=probes['pressed-reentered']
                reentry_offset=target['press_offset'] if again.get('pressed',{}).get('visible') else 0
                checks['reentry_content_matches_native_face']=again.get('content_position')==[0.0,reentry_offset]
                checks['release_restores_content']=released.get('content_position')==[0.0,0.0]
                checks['release_clears_hold']=not released.get('held')
            # Only target pixels are used for stability, so game clocks and
            # the animated world outside the control do not hide a failure.
            x,y=target['position'];w,h=target['size']
            target_box=[math.floor(x*4+.5),math.floor(y*4+.5),
                        math.floor((x+w)*4+.5),math.floor((y+h)*4+.5)]
            # Neighbor isolation uses every physical pixel touched by the
            # fractional target. This is independent of the fixed comparison
            # crop: floor/ceil prevents treating a rasterized edge as overflow.
            coverage_box=[math.floor(x*4),math.floor(y*4),math.ceil((x+w)*4),math.ceil((y+h)*4)]
            def crop(s):return np.asarray(Image.open(states[s]['output']).crop(target_box))
            if button:
                checks['held_frame_stable']=np.array_equal(crop('pressed'),crop('pressed-held'))
                result['changed_neighbor_pixels']=neighbor_difference(states,box,coverage_box)
                checks['neighbors_unchanged']=result['changed_neighbor_pixels']==0
                reentry_state='pressed' if probes['pressed-reentered'].get('pressed',{}).get('visible') else 'hover'
                checks['reentered_frame_matches_native_state']=np.array_equal(crop(reentry_state),crop('pressed-reentered'))
            if button and target['clickable']:
                r.code('''from ore_demo.pyreact import host
h=host._ACTIVE_HOST[0]
h._audit_clicks=[]
old=h._button_handlers[%r]
def counted(callback=old[2]):
    h._audit_clicks.append(1)
    if callback:
        callback()
h._button_handlers[%r]=(old[0],old[1],counted)
_result=True
''' % (target['path'],target['path']),'count-release')
                r.tap_at(r.point(target),'release-inside')
                dispatched=r.code('from ore_demo.pyreact import host\nimport ore_pressed_fixture as f\n'
                    '_result=dict(count=len(host._ACTIVE_HOST[0]._audit_clicks),events=f.events)','release-count')
                checks['inside_release_dispatches_once']=dispatched['count']==1
                result['inside_release']=dispatched
            if case.get('disabled') and target['keys'][-1] not in ('ore_page_previous','ore_page_next',
                    'accordion','ore_help_trigger','ore_banner_close','ore_pack_group_toggle'):
                # Disabled visual controls retain their fixed material.
                if case['kind']!='extras' or any(k in ('checkbox','radio','list') for k in target['keys']):
                    checks['disabled_visual_stable']=np.array_equal(crop('default'),crop('pressed'))
                    checks['disabled_no_event']=released['events']==probes['default']['events']
            row=dict(name=stem,case=case,target=target,context_box=box,target_box=target_box,coverage_box=coverage_box,
                     checks=checks,passed=all(checks.values()),states=result)
            rows.append(row)
            report['passed']=all(row['passed'] for row in rows)
            (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
            print(('PASS ' if row['passed'] else 'FAIL ')+stem+' '+','.join(k for k,v in checks.items() if not v),flush=True)
    return report


def recheck(output):
    """Re-evaluate saved frames without repeating any game input."""
    path=output/'report.json'
    report=json.loads(path.read_text(encoding='utf8'))
    for row in report['rows']:
        if 'native_pressed_visible' not in row['checks']:
            continue
        x,y=row['target']['position'];w,h=row['target']['size']
        box=[math.floor(x*4),math.floor(y*4),math.ceil((x+w)*4),math.ceil((y+h)*4)]
        row['coverage_box']=box
        states=row['states']['states']
        count=neighbor_difference(states,row['context_box'],box)
        row['states']['changed_neighbor_pixels']=count
        row['checks']['neighbors_unchanged']=count==0
        row['checks']['outside_release_does_not_click']=(
            states['released']['observation']['runtime']['events']==
            states['default']['observation']['runtime']['events'])
        row['passed']=all(row['checks'].values())
    report['passed']=all(row['passed'] for row in report['rows'])
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('%d targets; failed: %s'%(len(report['rows']),[r['name'] for r in report['rows'] if not r['passed']]))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--session');parser.add_argument('--owner')
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--only',nargs='+')
    parser.add_argument('--recheck',action='store_true')
    args=parser.parse_args()
    if not args.recheck and not (args.session and args.owner):
        parser.error('--session and --owner are required for game interaction')
    report=recheck(args.output) if args.recheck else verify(args.session,args.owner,args.output,args.only)
    raise SystemExit(0 if report['passed'] else 1)
