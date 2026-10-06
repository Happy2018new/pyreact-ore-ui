"""Capture actual held/released icon frames without PNG I/O in the timing loop."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import mss
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/skills/bedrock-ore-reference/scripts'))
import desktop


def capture(session, output, at, box, owner=None):
    if owner:
        data=json.loads(session.read_text('utf8'))
        identity=desktop.process(data['game_pid'])
        if data['owner']!=owner or not identity or str(identity['created'])!=str(data['game_identity']):
            raise RuntimeError('Owned game identity is stale')
        if not desktop.same_path(identity['exe'],data['game_executable']) or 'MinecraftPE_Netease' not in identity['exe']:
            raise RuntimeError('Owned capture is limited to the bound development client')
        matches=[w for w in desktop.windows() if w['pid']==data['game_pid']]
        if len(matches)!=1:
            raise RuntimeError('Expected one owned game window')
        window=matches[0]
    else:
        window = desktop.bound(session)
        desktop.begin_mode(session, window)
    output.mkdir(parents=True, exist_ok=True)
    frames = []
    try:
        with desktop.desktop_lock():
            desktop.activate(window)
            desktop.pointer(window, at)
            time.sleep(.25)
            desktop.capture(window, output / 'before.png')
            x, y, width, height = desktop.geometry(window)
            left, top, right, bottom = box
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                raise ValueError('Animation crop is outside the bound client')
            with mss.MSS() as screen:
                started = time.perf_counter()
                desktop.U.mouse_event(2, 0, 0, 0, 0)
                released = False
                try:
                    for index in range(49):
                        delay = started + index / 40.0 - time.perf_counter()
                        if delay > 0:
                            time.sleep(delay)
                        desktop.foreground(window)
                        if not released and time.perf_counter() - started >= .25:
                            desktop.U.mouse_event(4, 0, 0, 0, 0)
                            released = True
                        held = bool(desktop.U.GetAsyncKeyState(1) & 0x8000)
                        shot = screen.grab(dict(left=x+left, top=y+top, width=right-left, height=bottom-top))
                        frames.append((time.perf_counter()-started, held, Image.frombytes('RGB', shot.size, shot.rgb)))
                finally:
                    desktop.U.mouse_event(4, 0, 0, 0, 0)
            desktop.pointer(window, [.5, .04])
            desktop.capture(window, output / 'after.png')
    finally:
        if not owner:
            desktop.finish_mode(session, window)
    records = []
    for index, (seconds, held, image) in enumerate(frames):
        file = output / ('frame-%03d.png' % index)
        image.save(file)
        records.append(dict(file=file.name, milliseconds=seconds*1000, held=held,
                            sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
    data = dict(client_size=[width, height], crop=box, version=window.get('version'),
                release_ms=250, frames=records)
    (output / 'frames.json').write_text(json.dumps(data, indent=2), encoding='utf8')
    print(json.dumps(dict(output=str(output), frames=len(records),
                         unique_frames=len(set(r['sha256'] for r in records)))))


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--session',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--at',type=float,nargs=2,required=True)
    p.add_argument('--box',type=int,nargs=4,required=True)
    p.add_argument('--owner',help='Use an owned NetEase instance rather than international reference mode')
    a=p.parse_args()
    capture(a.session,a.output,a.at,a.box,a.owner)
