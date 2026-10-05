"""Lossless capture of an owned NetEase instance through the reference skill."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / '.agents/skills/bedrock-ore-reference/scripts'


def operate(session, owner, output=None, points=None, click=False, steps=None, sample=None):
    data = json.loads(Path(session).read_text(encoding='utf8'))
    if data['owner'] != owner:
        raise RuntimeError('Instance owner does not match')
    sys.path.insert(0, str(REFERENCE))
    spec = importlib.util.spec_from_file_location('ore_reference_desktop', REFERENCE / 'desktop.py')
    desktop = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(desktop)
    with desktop.desktop_lock():
        identity = desktop.process(data['game_pid'])
        if not identity or str(identity['created']) != str(data['game_identity']) or not desktop.same_path(
                identity['exe'], data['game_executable']):
            raise RuntimeError('Owned game process identity is stale')
        if 'MinecraftPE_Netease' not in identity['exe']:
            raise RuntimeError('International captures require the skill availability dialog')
        windows = [window for window in desktop.windows() if window['pid'] == data['game_pid']]
        if len(windows) != 1:
            raise RuntimeError('Expected one owned NetEase window')
        window = windows[0]
        desktop.activate(window)
        if sample is not None:
            if output is None:
                raise ValueError('Held sampling requires an output path')
            return desktop.sample_states(window, output=output, **sample)
        if steps:
            desktop.run(window, steps)
        for point in points or ():
            desktop.foreground(window)
            desktop.pointer(window, point)
            desktop.time.sleep(.25)
        if click:
            if not points or not all(0 <= number <= 1 for number in points[-1]):
                raise ValueError('Click requires a client point')
            desktop.foreground(window)
            desktop.U.mouse_event(2, 0, 0, 0, 0)
            try:
                desktop.time.sleep(.15)
            finally:
                desktop.U.mouse_event(4, 0, 0, 0, 0)
            desktop.time.sleep(.35)
        if output is not None:
            return desktop.capture(window, output)
        cursor = desktop.Point()
        desktop.U.GetCursorPos(desktop.ctypes.byref(cursor))
        x, y, width, height = desktop.geometry(window)
        return dict(pid=window['pid'], points=points, click=click, steps=steps, cursor=[cursor.x - x, cursor.y - y],
                    client_size=[width, height], input='absolute desktop pointer')


def capture(session, owner, output):
    return operate(session, owner, output=output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(capture(args.session, args.owner, args.output), ensure_ascii=False, indent=2))
