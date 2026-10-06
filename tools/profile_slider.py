"""Repeat the same physical drag on the playground's continuous slider."""
import argparse
import json
import time
from pathlib import Path

from verify_seams_scroll import SeamVerification
from capture_settings_pixels import operate


def run(session, owner, output):
    r = SeamVerification(session, owner, output)
    r.mount()
    r.page('sliders')
    geometry = r.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host,native\n'
        'from ore_demo.oreui._slider import SliderPrimitive\n'
        'h=host._ACTIVE_HOST[0]\nf=next(f for f in dev_probe._walk(h._root_fiber) if f.key=="lab_slider")\n'
        's=next(f for f in dev_probe._walk(f) if isinstance(f.comp_type,SliderPrimitive))\n'
        'c=h.GetBaseUIControl(s.native_path)\n'
        '_result=dict(position=c.GetGlobalPosition(),size=c.GetSize(),screen=native.get_screen_size())', 'geometry')
    x,y=geometry['position'];w,h=geometry['size'];sw,sh=geometry['screen']
    left=[x/sw,(y+h/2)/sh];right=[(x+w)/sw,(y+h/2)/sh]
    operate(session, owner, steps=[dict(do='move',at=left),dict(do='wait',ms=200),dict(do='click',at=left)])
    result=r.client.call('mc_profiler',dict(op='/start',args=dict(kind='python.cpu',target='client',clock='wall',duration_seconds=24,storage='disk')))
    (output/'start.json').write_text(json.dumps(result,indent=2),'utf8')
    job=result['structuredContent']['job']['id']
    steps=[]
    for unused in range(3):
        for start,end in ((left,right),(right,left)):
            steps.extend([dict(do='move',at=start),dict(do='wait',ms=150),
                dict(do='drag',**{'from':start,'to':end,'segments':100}),dict(do='wait',ms=200)])
    operate(session,owner,steps=steps,output=output/'after-drag.png')
    for unused in range(20):
        status=r.client.call('mc_profiler',dict(op='/status',args=dict(job_id=job)))
        (output/'status.json').write_text(json.dumps(status,indent=2),'utf8')
        if status['structuredContent']['job']['state'] in ('completed','failed','cancelled'):
            break
        time.sleep(1)
    for op,args in [('/query',dict(job_id=job,view='hotspots',limit=40)),('/export',dict(job_id=job,format='markdown'))]:
        data=r.client.call('mc_profiler',dict(op=op,args=args))
        (output/(op[1:]+'.json')).write_text(json.dumps(data,indent=2),'utf8')
    print(job)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--owner',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.session,a.owner,a.output)
