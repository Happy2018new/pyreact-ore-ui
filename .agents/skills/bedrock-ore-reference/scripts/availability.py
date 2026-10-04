# -*- coding: utf-8 -*-
"""Visible desktop availability prompts for an Ore reference capture batch."""
import argparse
import json
import time
import tkinter as tk
from tkinter import ttk
from pathlib import Path


def prompt(completed=False, evidence=None):
    root = tk.Tk()
    root.withdraw()
    root.title('Ore UI 国际版采集')
    root.resizable(False, False)
    root.attributes('-topmost', True)
    shell = ttk.Frame(root, padding=22)
    shell.pack(fill='both', expand=True)
    buttons = ttk.Frame(shell)
    buttons.pack(side='bottom', fill='x', pady=(16, 0))
    frame = ttk.Frame(shell)
    frame.pack(side='top', fill='both', expand=True)
    result = {'accepted': False, 'source': 'closed'}
    started = None

    def finish(accepted, source):
        result.update(accepted=accepted, source=source,
                      elapsed_seconds=round(time.monotonic() - started, 3))
        root.destroy()

    if completed:
        ttk.Label(frame, text='国际版 UI 采集已结束', font=('Microsoft YaHei UI', 14)).pack(anchor='w')
        ttk.Label(frame, text='自动操作已停止，你现在可以继续使用电脑。',
                  wraplength=440).pack(anchor='w', pady=(14, 20))
        countdown = ttk.Label(frame)
        countdown.pack(anchor='w')
        ttk.Button(buttons, text='知道了', width=12, command=lambda: finish(True, 'button')).pack(side='right')
        root.protocol('WM_DELETE_WINDOW', lambda: finish(True, 'closed'))
    else:
        ttk.Label(frame, text='现在方便采集国际版 UI 吗？', font=('Microsoft YaHei UI', 14)).pack(anchor='w')
        ttk.Label(frame, text='程序将切换到 Minecraft，自动移动鼠标并截取控件状态。\n'
                  '完成后会再次通知你。点击“稍后”可取消这次操作。',
                  wraplength=440).pack(anchor='w', pady=(12, 10))
        countdown = ttk.Label(frame)
        countdown.pack(anchor='w')
        ttk.Button(buttons, text='稍后', width=12, command=lambda: finish(False, 'deferred')).pack(side='left')
        ttk.Button(buttons, text='开始采集', width=12, command=lambda: finish(True, 'button')).pack(side='right')
        root.protocol('WM_DELETE_WINDOW', lambda: finish(False, 'closed'))

    root.update_idletasks()
    width = max(520, root.winfo_reqwidth() + 16)
    height = max(260, root.winfo_reqheight() + 16)
    x = max(0, (root.winfo_screenwidth() - width) // 2)
    y = max(0, (root.winfo_screenheight() - height) // 2)
    root.geometry('%dx%d+%d+%d' % (width, height, x, y))
    root.deiconify()
    started = time.monotonic()

    def tick():
        remaining = max(0, 5 - int(time.monotonic() - started))
        countdown.config(text=('%d 秒后自动关闭。' if completed else '%d 秒内没有回应，将自动开始。') % remaining)
        if time.monotonic() - started >= 5:
            finish(True, 'notification_timeout' if completed else 'timeout')
        else:
            root.after(100, tick)
    tick()
    if evidence:
        def verify_visible():
            import mss
            from PIL import Image
            root.update_idletasks()
            bounds = [root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()]
            controls = []
            for button in buttons.winfo_children():
                box = [button.winfo_rootx() - bounds[0], button.winfo_rooty() - bounds[1],
                       button.winfo_width(), button.winfo_height()]
                visible = button.winfo_ismapped() and box[0] >= 0 and box[1] >= 0 and box[0] + box[2] <= bounds[2] and box[1] + box[3] <= bounds[3]
                controls.append(dict(text=button.cget('text'), box=box, visible=bool(visible)))
            output = Path(evidence)
            output.parent.mkdir(parents=True, exist_ok=True)
            with mss.MSS() as screen:
                shot = screen.grab(dict(zip(('left', 'top', 'width', 'height'), bounds)))
            Image.frombytes('RGB', shot.size, shot.rgb).save(output.with_suffix('.png'))
            output.with_suffix('.json').write_text(json.dumps(dict(bounds=bounds, buttons=controls,
                all_buttons_visible=all(item['visible'] for item in controls)), ensure_ascii=False, indent=2), encoding='utf8')
        root.after(400, verify_visible)
    root.lift()
    root.mainloop()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--completed', action='store_true')
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    print(json.dumps(prompt(args.completed, args.evidence), ensure_ascii=False))
