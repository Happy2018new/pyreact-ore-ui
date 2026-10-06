"""Crop Settings icons and the measured selection glint from lossless captures."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '.runtime/settings-replica'
OUTPUT = ROOT / 'resource_pack/textures/pyreact_ore/settings'


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assets, provenance = {}, {}
    sources = [('touch', [('accessibility',156),('keyboard',352),('controller',448),('touch',544),('party',740),('general',936),('video',1032)]),
               ('sidebar-bottom2', [('audio',472),('account',568),('subscriptions',664),('resources',760),('storage',856),('language',952),('creator',1048)])]
    for stem, icons in sources:
        path = SOURCE / 'reference' / (stem + '.png')
        image = Image.open(path).convert('RGBA')
        for name,y in icons:
            name='settings_'+name
            box=[36,y,84,y+48]
            image.crop(box).save(OUTPUT/(name+'.png'))
            assets[name]=dict(src='textures/pyreact_ore/settings/'+name,size=[48,48],navigationAnimation=True)
            provenance[name]=dict(source=path.name,crop=box,scale=4,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    # Use only observed white pixels that differ from the resting icon. The
    # unchanged colored interior stays in the caller's icon; no background mask.
    directory=SOURCE/'animation-controller'
    metadata=json.loads((directory/'frames.json').read_text('utf8'))
    box=(16,16,64,64)
    baseline=np.asarray(Image.open(directory/metadata['frames'][-1]['file']).convert('RGB').crop(box))
    changes=[]
    for frame in metadata['frames']:
        if frame['held']:
            continue
        pixels=np.asarray(Image.open(directory/frame['file']).convert('RGB').crop(box))
        alpha=(np.all(pixels==255,axis=2)&np.any(pixels!=baseline,axis=2)).astype('uint8')*255
        if not changes or not np.array_equal(alpha,changes[-1][1]):
            changes.append((frame['milliseconds'],alpha,frame['file']))
    atlas=Image.new('RGBA',(48*len(changes),48),(255,255,255,0))
    durations=[]
    for index,(timestamp,alpha,unused) in enumerate(changes):
        patch=Image.new('RGBA',(48,48),'white');patch.putalpha(Image.fromarray(alpha));atlas.paste(patch,(48*index,0))
        end=changes[index+1][0] if index+1<len(changes) else timestamp+25
        durations.append(round((end-timestamp)/1000.,4))
    atlas.save(OUTPUT/'navigation_glint.png')
    assets['navigation_glint']=dict(src='textures/pyreact_ore/settings/navigation_glint',size=[48,48],
        frames=[dict(uv=[48*i,0],uvSize=[48,48]) for i in range(len(changes))],frameDuration=.06,frameDurations=durations)
    provenance['navigation_glint']=dict(source='animation-controller/frames.json',crop=list(box),scale=4,
        release_ms=metadata['release_ms'],states=[dict(time=t,file=f) for t,_,f in changes],
        loop=False,extraction='White changed pixels against resting icon; other pixels transparent')
    # The touch layout drawing has its own square pixels and aspect ratio.
    for name, source, box in [
            ('settings_touch_layout','touch.png',[1392,560,1972,876]),
            ('settings_touch_dpad','touch-dpad.png',[1392,560,1972,876]),
            ('settings_touch_crosshair','touch-crosshair.png',[1392,560,1972,876]),
            ('settings_drive','storage-current.png',[724,288,772,336]),
            ('settings_notice','touch-current.png',[760,440,800,480])]:
        path=SOURCE/'reference'/source
        patch=Image.open(path).convert('RGBA').crop(box)
        if name in ('settings_drive','settings_notice'):
            rgba=np.asarray(patch).copy()
            rgba[np.all(rgba[:,:,:3]==([49,50,51] if name=='settings_drive' else [30,30,31]),axis=2),3]=0
            patch=Image.fromarray(rgba)
        patch.save(OUTPUT/(name+'.png'))
        assets[name]=dict(src='textures/pyreact_ore/settings/'+name,size=list(patch.size))
        provenance[name]=dict(source=path.name,crop=box,scale=4,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    controller=[('A',4,527),('down',5,143),('RT',5,287),('LT',5,431),('X',5,575),('Y',5,719),
        ('LB',6,341),('RB',6,485),('up',6,630),('B',6,773),('LS_press',6,917),
        ('RS_press',9,143),('left',9,287),('view',9,431),('right',9,575),
        ('LS_left',10,191),('LS_right',10,335),('LS_down',10,479),('LS_up',10,623)]
    for name,index,y in controller:
        path=SOURCE/('pages/controller/%02d.png'%index)
        # The measured cells are centered at x=1732. Preserve a 16-unit canvas.
        box=[1700,y-17,1764,y+47]
        patch=Image.open(path).convert('RGBA').crop(box)
        rgba=np.asarray(patch).copy()
        rgba[np.all(rgba[:,:,:3]==[177,178,181],axis=2),3]=0
        patch=Image.fromarray(rgba)
        name='controller_'+name
        patch.save(OUTPUT/(name+'.png'))
        assets[name]=dict(src='textures/pyreact_ore/settings/'+name,size=[64,64])
        provenance[name]=dict(source='controller/'+path.name,crop=box,scale=4,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),extraction='Exact uniform cell background made transparent')
    (ROOT/'assets/settings-reference.json').write_text(json.dumps(dict(version='1.26.5203.0',assets=provenance),indent=2)+'\n','utf8')
    (ROOT/'oreui/_settings_assets.py').write_text('# Generated by tools/build_settings_assets.py.\nASSETS = '+repr(assets)+'\n','utf8')
    print('Cropped',len(assets),'assets; glint durations',durations)


if __name__=='__main__':
    build()
