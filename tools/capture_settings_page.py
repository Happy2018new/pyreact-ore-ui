"""Record a settings page with overlapping scroll positions and measured thumb bounds."""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.agents/skills/bedrock-ore-reference/scripts'))
import desktop


def thumb(image, x):
    pixels=np.asarray(image.convert('RGB'))
    ys=np.where(np.all(pixels[108:-12,x]==[230,232,235],axis=1))[0]+108
    runs=np.split(ys,np.where(np.diff(ys)>1)[0]+1)
    runs=[r for r in runs if len(r)>12]
    return (int(max(runs,key=len)[0]),int(max(runs,key=len)[-1])+1) if runs else None


def capture(session,output,name):
    window=desktop.bound(session)
    desktop.begin_mode(session,window)
    directory=output/name;directory.mkdir(parents=True,exist_ok=True)
    records=[]
    try:
        with desktop.desktop_lock():
            desktop.activate(window)
            for index in range(80):
                desktop.pointer(window,[.5,.04]);time.sleep(.35)
                path=directory/('%02d.png'%index)
                meta=desktop.capture(window,path)
                image=Image.open(path)
                bounds=thumb(image,image.width-20)
                records.append(dict(file=path.name,thumb=bounds,sha256=meta['sha256']))
                if not bounds or bounds[1]>=image.height-40:
                    break
                if len(records)>1 and records[-2]['thumb']==bounds:
                    raise RuntimeError('Scroll did not advance; inspect focus and measured thumb before continuing')
                y=(bounds[0]+bounds[1])/2
                end=min(y+(bounds[1]-bounds[0])*.67,image.height-12-(bounds[1]-bounds[0])/2)
                if end<=y+1:
                    break
                desktop.run(window,[dict(do='move',at=[(image.width-20)/(image.width-1),y/(image.height-1)]),
                    dict(do='wait',ms=120),dict(do='drag',**{'from':[(image.width-20)/(image.width-1),y/(image.height-1)],
                    'to':[(image.width-20)/(image.width-1),end/(image.height-1)],'segments':12}),dict(do='wait',ms=450)])
            else:
                raise RuntimeError('Page exceeded 80 captures; inspect scroll detection')
    finally:
        if True:
            desktop.finish_mode(session, window)
    panels=[]
    for row in records:
        original=Image.open(directory/row['file']).convert('RGB')
        crop=original.crop((672,96,original.width,original.height))
        panel=crop.resize((674,530),Image.Resampling.LANCZOS)
        ImageDraw.Draw(panel).text((5,5),name+' '+row['file'],fill='yellow')
        panels.append(panel)
    overview=Image.new('RGB',(674*min(3,len(panels)),530*((len(panels)+2)//3)),'#111111')
    for i,panel in enumerate(panels):overview.paste(panel,((i%3)*674,(i//3)*530))
    overview.save(directory/'overview.jpg')
    (directory/'manifest.json').write_text(json.dumps(dict(name=name,frames=records,preview_resampled=True),indent=2),'utf8')
    print(name,len(records),records[-1]['thumb'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--session',type=Path,default=ROOT/'.runtime/bedrock-reference/session.json');p.add_argument('--output',type=Path,default=ROOT/'.runtime/settings-replica/pages')
    a=p.parse_args();capture(a.session,a.output,a.name)
