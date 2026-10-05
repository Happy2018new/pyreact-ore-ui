"""Exercise the desktop sampler against an owned, deterministic GUI window."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/skills/bedrock-ore-reference/scripts'))
import desktop
from PIL import Image


def window():
    import tkinter as tk
    root = tk.Tk()
    root.title('Ore reference sampler self-test')
    root.geometry('320x180+700+400')
    root.resizable(False, False)
    canvas = tk.Canvas(root, width=320, height=180, highlightthickness=0, bg='#101010')
    canvas.pack()
    left = canvas.create_rectangle(20, 40, 149, 139, fill='#444444', outline='')
    canvas.create_rectangle(150, 40, 280, 139, fill='#22aa66', outline='')
    canvas.tag_bind(left, '<Enter>', lambda e: canvas.itemconfig(left, fill='#888888'))
    canvas.tag_bind(left, '<Leave>', lambda e: canvas.itemconfig(left, fill='#444444'))
    canvas.tag_bind(left, '<ButtonPress-1>', lambda e: canvas.itemconfig(left, fill='#cc3344'))
    canvas.bind('<ButtonRelease-1>', lambda e: canvas.itemconfig(left, fill='#444444'))
    root.mainloop()


def verify(output):
    output.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--window'],
                               creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        target = None
        for unused in range(50):
            target = next((w for w in desktop.windows() if w['pid'] == process.pid), None)
            if target:
                break
            time.sleep(.1)
        if target is None:
            raise RuntimeError('Owned sampler-test window did not appear')
        with desktop.desktop_lock():
            desktop.activate(target)
            result = desktop.sample_states(target, (.25,.5), output / 'sample',
                away=(.95,.05), context_box=(16,36,284,144))
        for state, color in [('default',(68,68,68)),('hover',(136,136,136)),
                             ('pressed',(204,51,68)),('pressed-held',(204,51,68)),
                             ('pressed-outside',(68,68,68)),('pressed-reentered',(136,136,136)),
                             ('released',(68,68,68))]:
            metadata = result['states'][state]
            image = Image.open(metadata['output'])
            assert image.getpixel((80,90)) == color, state
            assert image.getpixel((200,90)) == (34,170,102), 'Neighbor changed'
            expected = state.startswith('pressed')
            assert metadata['mouse_left_down_before'] == expected
            assert metadata['mouse_left_down_after'] == expected
            assert Image.open(output / ('sample-' + state + '-context.png')).size == (268,108)
        assert result['mouse_released']
        result['verified'] = ['default','hover','pressed','pressed-held','pressed-outside',
                              'pressed-reentered','unchanged neighbor','fixed crop','release']
        (output / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf8')
        print('PASS actual held-button capture, default/hover separation, neighbor context and release')
    finally:
        process.terminate()
        process.wait(timeout=5)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/pressed-audit/sampler')
    args = parser.parse_args()
    window() if args.window else verify(args.output)
