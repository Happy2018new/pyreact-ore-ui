"""PID-bound Windows desktop capture and input, without game injection."""
import argparse
import contextlib
import ctypes
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET
from availability import prompt as availability_prompt

from PIL import Image

U = ctypes.WinDLL('user32', use_last_error=True)
K = ctypes.WinDLL('kernel32', use_last_error=True)
U.SetProcessDPIAware()
U.GetForegroundWindow.restype = W.HWND
U.GetAsyncKeyState.argtypes = [ctypes.c_int]
U.GetAsyncKeyState.restype = ctypes.c_short
U.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
U.GetWindowThreadProcessId.restype = W.DWORD
U.GetWindowTextW.argtypes = [W.HWND, W.LPWSTR, ctypes.c_int]
U.IsWindowVisible.argtypes = [W.HWND]
U.SetForegroundWindow.argtypes = [W.HWND]
U.BringWindowToTop.argtypes = [W.HWND]
U.ShowWindow.argtypes = [W.HWND, ctypes.c_int]
U.IsIconic.argtypes = [W.HWND]
U.IsZoomed.argtypes = [W.HWND]
U.AttachThreadInput.argtypes = [W.DWORD, W.DWORD, W.BOOL]
K.GetCurrentThreadId.restype = W.DWORD
K.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
K.OpenProcess.restype = W.HANDLE
K.CloseHandle.argtypes = [W.HANDLE]
K.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)]
K.GetProcessTimes.argtypes = [W.HANDLE] + [ctypes.POINTER(W.FILETIME)] * 4


class Rect(ctypes.Structure):
    _fields_ = [('left', W.LONG), ('top', W.LONG), ('right', W.LONG), ('bottom', W.LONG)]


class Point(ctypes.Structure):
    _fields_ = [('x', W.LONG), ('y', W.LONG)]


U.GetClientRect.argtypes = [W.HWND, ctypes.POINTER(Rect)]
U.ClientToScreen.argtypes = [W.HWND, ctypes.POINTER(Point)]
U.GetWindowRect.argtypes = [W.HWND, ctypes.POINTER(Rect)]
U.WindowFromPoint.argtypes = [Point]
U.WindowFromPoint.restype = W.HWND
U.GetAncestor.argtypes = [W.HWND, W.UINT]
U.GetAncestor.restype = W.HWND
U.SendMessageTimeoutW.argtypes = [W.HWND, W.UINT, W.WPARAM, W.LPARAM,
                                W.UINT, W.UINT, ctypes.POINTER(ctypes.c_size_t)]


def process(pid):
    handle = K.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        path = ctypes.create_unicode_buffer(32768)
        size = W.DWORD(32768)
        times = [W.FILETIME() for _ in range(4)]
        if not K.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
            return None
        if not K.GetProcessTimes(handle, *[ctypes.byref(item) for item in times]):
            return None
        return dict(exe=path.value, created=(times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
    finally:
        K.CloseHandle(handle)


def windows():
    result = []
    callback_type = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)

    @callback_type
    def visit(hwnd, unused):
        if U.IsWindowVisible(hwnd):
            title = ctypes.create_unicode_buffer(1024)
            U.GetWindowTextW(hwnd, title, len(title))
            pid = W.DWORD()
            U.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            info = process(pid.value)
            if title.value and info:
                result.append(dict(hwnd=int(hwnd), pid=pid.value, title=title.value, **info))
        return True
    U.EnumWindows.argtypes = [callback_type, W.LPARAM]
    U.EnumWindows(visit, 0)
    return result


def same_path(first, second):
    return os.path.normcase(os.path.abspath(first)) == os.path.normcase(os.path.abspath(second))


def save_session(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.pending.json')
    temporary.write_text(json.dumps(data, indent=2), encoding='utf8')
    os.replace(temporary, path)


def begin_mode(session, window, renew=False):
    mode = window.get('automation', {})
    if not renew and mode.get('active') and time.time() < mode.get('expires', 0):
        return mode
    answer = availability_prompt()
    if not answer['accepted']:
        window['automation'] = dict(active=False, response=answer)
        save_session(session, window)
        raise RuntimeError('AVAILABILITY_DEFERRED: no game activation or input sent')
    mode = dict(active=True, began=time.time(), expires=time.time() + 3600, response=answer)
    window['automation'] = mode
    save_session(session, window)
    return mode


def finish_mode(session, window):
    window['automation'] = dict(active=False, ended=time.time())
    save_session(session, window)
    return dict(ok=True, automation=window['automation'], notification=availability_prompt(completed=True))


def bound(session):
    data = json.loads(Path(session).read_text(encoding='utf8'))
    info = process(data['pid'])
    if not info or info['created'] != data['created'] or not same_path(info['exe'], data['exe']):
        raise RuntimeError('Bound process identity is stale')
    matches = [item for item in windows() if item['pid'] == data['pid']]
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one bound visible game window')
    data.update(matches[0])
    return data


@contextlib.contextmanager
def desktop_lock():
    import msvcrt
    root = Path(os.environ['USERPROFILE']) / '.pyreact-debug/instances'
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'desktop.lock').open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        deadline = time.monotonic() + 10
        while True:
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('Desktop busy: another input operation owns the lock')
                time.sleep(0.05)
        try:
            lease = root / 'desktop-lease.json'
            if lease.exists() and json.loads(lease.read_text(encoding='utf8')).get('until', 0) > time.time():
                raise RuntimeError('Uncertain Pyreact input is still reserved')
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def activate(window):
    hwnd = window['hwnd']
    current = K.GetCurrentThreadId()
    threads = {U.GetWindowThreadProcessId(U.GetForegroundWindow(), None),
               U.GetWindowThreadProcessId(hwnd, None)} - {0, current}
    attached = []
    try:
        for thread in threads:
            if U.AttachThreadInput(current, thread, True):
                attached.append(thread)
        if U.IsIconic(hwnd):
            U.ShowWindow(hwnd, 9)
        U.BringWindowToTop(hwnd)
        U.SetForegroundWindow(hwnd)
        if U.GetForegroundWindow() != hwnd:
            # Win32 permits foreground activation after an ALT input event.
            U.keybd_event(0x12, 0, 0, 0)
            U.keybd_event(0x12, 0, 2, 0)
            U.SetForegroundWindow(hwnd)
        if U.GetForegroundWindow() != hwnd and not U.IsZoomed(hwnd):
            U.ShowWindow(hwnd, 9)
            U.SetForegroundWindow(hwnd)
    finally:
        for thread in attached:
            U.AttachThreadInput(current, thread, False)
    time.sleep(0.15)
    if U.GetForegroundWindow() != hwnd:
        _activate_title_bar(window)
    foreground(window)


def _activate_title_bar(window):
    rect = Rect()
    x, y, width, unused = geometry(window)
    if not U.GetWindowRect(window['hwnd'], ctypes.byref(rect)) or y <= rect.top:
        return
    point = Point(x + width // 2, rect.top + (y - rect.top) // 2)
    hit = U.WindowFromPoint(point)
    if not hit or U.GetAncestor(hit, 2) != window['hwnd']:
        return
    result = ctypes.c_size_t()
    coordinates = (point.x & 0xffff) | ((point.y & 0xffff) << 16)
    if not U.SendMessageTimeoutW(window['hwnd'], 0x84, 0, coordinates, 2, 250, ctypes.byref(result)) or result.value != 2:
        return
    _desktop_pointer(point.x, point.y)
    if U.GetAncestor(U.WindowFromPoint(point), 2) != window['hwnd']:
        return
    U.mouse_event(2, 0, 0, 0, 0)
    U.mouse_event(4, 0, 0, 0, 0)
    time.sleep(.15)


def foreground(window):
    if U.GetForegroundWindow() != window['hwnd']:
        raise RuntimeError('FOCUS_DENIED: bound game is not foreground; no input sent')


def geometry(window):
    rect, origin = Rect(), Point()
    if not U.GetClientRect(window['hwnd'], ctypes.byref(rect)) or not U.ClientToScreen(window['hwnd'], ctypes.byref(origin)):
        raise RuntimeError('Client geometry unavailable')
    return origin.x, origin.y, rect.right, rect.bottom


def capture(window, output, expected_down=None, observation=None):
    import mss
    foreground(window)
    down_before = bool(U.GetAsyncKeyState(1) & 0x8000)
    if expected_down is not None and down_before != expected_down:
        raise RuntimeError('Mouse state does not match requested capture state')
    x, y, width, height = geometry(window)
    with mss.MSS() as screen:
        shot = screen.grab(dict(left=x, top=y, width=width, height=height))
    down_after = bool(U.GetAsyncKeyState(1) & 0x8000)
    foreground(window)
    if expected_down is not None and down_after != expected_down:
        raise RuntimeError('Mouse state changed during capture')
    image = Image.frombytes('RGB', shot.size, shot.rgb)
    if image.getextrema() == ((0, 0),) * 3:
        raise RuntimeError('Blank game capture')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    cursor = Point()
    U.GetCursorPos(ctypes.byref(cursor))
    metadata = dict(window, client=[x, y, width, height], cursor=[cursor.x - x, cursor.y - y], timestamp=time.time(),
                    output=str(output.resolve()), sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                    mouse_left_down_before=down_before, mouse_left_down_after=down_after,
                    observation=observation)
    output.with_suffix('.json').write_text(json.dumps(metadata, indent=2), encoding='utf8')
    return metadata


def pointer(window, at):
    if len(at) != 2 or not all(0 <= n <= 1 for n in at):
        raise ValueError('Pointer coordinates must be normalized inside the client')
    x, y, width, height = geometry(window)
    target = (round(x + at[0] * (width - 1)), round(y + at[1] * (height - 1)))
    _desktop_pointer(*target)


def _desktop_pointer(x, y):
    target = (x, y)
    left, top = U.GetSystemMetrics(76), U.GetSystemMetrics(77)
    desktop_width, desktop_height = U.GetSystemMetrics(78), U.GetSystemMetrics(79)
    if not (left <= target[0] < left + desktop_width and top <= target[1] < top + desktop_height):
        raise RuntimeError('Requested game pixel is outside the desktop; no click sent')
    # Absolute input also updates the game's input cursor, unlike SetCursorPos.
    U.mouse_event(0xC001, round((target[0] - left + 0.5) * 65536 / desktop_width),
                  round((target[1] - top + 0.5) * 65536 / desktop_height), 0, 0)
    actual = Point()
    for unused in range(5):
        U.GetCursorPos(ctypes.byref(actual))
        if abs(actual.x - target[0]) <= 1 and abs(actual.y - target[1]) <= 1:
            return
        # Absolute input delivery can lag GetCursorPos by one desktop frame.
        # Wait for that same event; do not replay input or release confinement.
        time.sleep(.025)
    raise RuntimeError('Pointer constrained outside requested position; no click sent: requested %r, actual %r'
                       % (target, (actual.x, actual.y)))


def sample_states(window, at, output, control_type='button', states=('default', 'hover', 'pressed'),
                  away=(0.75, 0.04), context_box=None, observe=None):
    prefix = Path(output)
    results = {}
    held_since = None

    def frame(state, position, down):
        observation = dict(state=state, hold_ms=round((time.monotonic() - held_since) * 1000)
            if held_since is not None and down else 0, requested_pointer=position, context_box=context_box)
        if observe is not None:
            observation['runtime'] = observe(state)
        return capture(window, prefix.with_name(prefix.stem + '-' + state + '.png'),
                       expected_down=down, observation=observation)
    if U.GetAsyncKeyState(1) & 0x8000:
        raise RuntimeError('Mouse is already held; no sampling input sent')
    for state, position in (('default', away), ('hover', at), ('pressed', at)):
        if state not in states:
            continue
        foreground(window)
        if state == 'default':
            # A remounted native UI can retain its old hover until it receives
            # a nonzero pointer delta, even when GetCursorPos already says away.
            pointer(window, at)
            time.sleep(.15)
            refresh = (away[0] - .01 if away[0] >= .01 else away[0] + .01, away[1])
            pointer(window, refresh)
            time.sleep(.15)
        pointer(window, position)
        # Let the engine update hit testing before sending mouse-down.
        time.sleep(.2)
        foreground(window)
        if state == 'pressed':
            U.mouse_event(2, 0, 0, 0, 0)
            held_since = time.monotonic()
        try:
            time.sleep(0.45)
            results[state] = frame(state, position, state == 'pressed')
            if state == 'pressed':
                time.sleep(.45)
                results['pressed-held'] = frame('pressed-held', position, True)
                if control_type != 'slider':
                    pointer(window, away)
                    time.sleep(.2)
                    results['pressed-outside'] = frame('pressed-outside', away, True)
                    pointer(window, at)
                    time.sleep(.2)
                    results['pressed-reentered'] = frame('pressed-reentered', at, True)
        finally:
            if state == 'pressed':
                try:
                    if control_type != 'slider':
                        pointer(window, away)
                        time.sleep(.1)
                finally:
                    U.mouse_event(4, 0, 0, 0, 0)
    time.sleep(.2)
    results['released'] = frame('released', at if control_type == 'slider' else away, False)
    if context_box is not None:
        import pixels
        for state, metadata in results.items():
            pixels.checked_crop(metadata['output'], context_box).save(prefix.with_name(prefix.stem + '-' + state + '-context.png'))
    return dict(ok=True, states=results, release_moved_outside=control_type != 'slider',
                mouse_released=not bool(U.GetAsyncKeyState(1) & 0x8000))


def run(window, steps):
    if not isinstance(steps, list) or len(steps) > 64:
        raise ValueError('Maximum 64 steps')
    keys = {'escape': 27, 'enter': 13, 'f11': 122, 'tab': 9,
            'home': 36, 'end': 35, 'up': 38, 'down': 40}
    for step in steps:
        action = step.get('do')
        if action not in ('move', 'click', 'scroll', 'drag', 'key', 'wait'):
            raise ValueError('Unsupported action: ' + str(action))
        for field in ('at',) if action in ('move', 'click', 'scroll') else ('from', 'to') if action == 'drag' else ():
            coords = step.get(field)
            if not isinstance(coords, list) or len(coords) != 2 or not all(isinstance(n, (int, float)) and 0 <= n <= 1 for n in coords):
                raise ValueError('Invalid normalized coordinates: ' + field)
        if action == 'key' and step.get('key') not in keys:
            raise ValueError('Unsupported navigation key')
        if action == 'wait' and not 0 <= step.get('ms', -1) <= 5000:
            raise ValueError('Wait must be 0 to 5000 ms')
        if action == 'click' and not 0 <= step.get('hold_ms', 90) <= 5000:
            raise ValueError('Invalid click duration')
        if action == 'drag' and not 1 <= step.get('segments', 20) <= 100:
            raise ValueError('Invalid drag segments')
        if action == 'scroll' and not isinstance(step.get('amount'), (int, float)):
            raise ValueError('Invalid scroll amount')
    executed = 0
    for step in steps:
        foreground(window)
        action = step['do']
        if action in ('move', 'click', 'scroll'):
            pointer(window, step['at'])
        if action == 'click':
            time.sleep(0.1)
            foreground(window)
            U.mouse_event(2, 0, 0, 0, 0)
            try:
                time.sleep(step.get('hold_ms', 90) / 1000)
            finally:
                U.mouse_event(4, 0, 0, 0, 0)
        elif action == 'scroll':
            time.sleep(0.1)
            foreground(window)
            U.mouse_event(0x800, 0, 0, int(step['amount'] * 120), 0)
        elif action == 'key':
            key = keys[step['key']]
            U.keybd_event(key, 0, 0, 0)
            U.keybd_event(key, 0, 2, 0)
        elif action == 'drag':
            pointer(window, step['from'])
            U.mouse_event(2, 0, 0, 0, 0)
            try:
                count = step.get('segments', 20)
                for index in range(1, count + 1):
                    foreground(window)
                    pointer(window, [a + (b - a) * index / count for a, b in zip(step['from'], step['to'])])
                    time.sleep(0.03)
            finally:
                U.mouse_event(4, 0, 0, 0, 0)
        elif action == 'wait':
            time.sleep(min(5000, step['ms']) / 1000)
        elif action != 'move':
            raise ValueError('Unsupported action: ' + action)
        executed += 1
    foreground(window)
    return dict(ok=True, executed=executed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('op', choices=('list', 'launch', 'bind', 'begin', 'finish', 'capture', 'sample', 'run', 'state'))
    parser.add_argument('--exe', type=Path)
    parser.add_argument('--pid', type=int)
    parser.add_argument('--session', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--recipe', type=Path)
    parser.add_argument('--at', nargs=2, type=float)
    parser.add_argument('--control-type', choices=('button', 'slider'), default='button')
    parser.add_argument('--states', choices=('default', 'hover', 'pressed'), nargs='+', default=['default', 'hover', 'pressed'])
    parser.add_argument('--away', nargs=2, type=float, default=[.75, .04])
    parser.add_argument('--context-box', nargs=4, type=int, help='Half-open client box including the control and its neighbors')
    args = parser.parse_args()
    if args.op == 'list':
        return windows()
    if args.op in ('launch', 'bind'):
        if not args.exe or not args.session:
            parser.error('Binding requires --exe and --session')
        matches = [item for item in windows() if same_path(item['exe'], args.exe) and
                   (args.pid is None or args.pid == item['pid'])]
        if not matches and args.op == 'launch':
            answer = availability_prompt()
            if not answer['accepted']:
                raise RuntimeError('AVAILABILITY_DEFERRED: game was not launched')
            subprocess.Popen([str(args.exe.resolve())], cwd=args.exe.parent)
            for unused in range(60):
                matches = [item for item in windows() if same_path(item['exe'], args.exe)]
                if matches:
                    break
                time.sleep(0.5)
        if len(matches) != 1:
            raise RuntimeError('Expected one matching game; specify --pid')
        data = matches[0]
        if args.op == 'launch' and 'answer' in locals():
            data['automation'] = dict(active=True, began=time.time(), expires=time.time() + 3600, response=answer)
        manifest = args.exe.parent / 'appxmanifest.xml'
        if manifest.exists():
            data['version'] = ET.parse(manifest).getroot().find('{*}Identity').get('Version')
        save_session(args.session, data)
        return data
    window = bound(args.session)
    if args.op == 'begin':
        return dict(ok=True, automation=begin_mode(args.session, window, renew=True))
    if args.op == 'finish':
        return finish_mode(args.session, window)
    if args.op in ('capture', 'sample', 'run'):
        begin_mode(args.session, window)
    with desktop_lock():
        if args.op == 'state':
            return dict(window, client=geometry(window), foreground=U.GetForegroundWindow() == window['hwnd'])
        activate(window)
        if args.op == 'capture':
            return capture(window, args.output)
        if args.op == 'sample':
            if not args.at or not args.output:
                parser.error('State sampling requires --at and --output')
            return sample_states(window, args.at, args.output, args.control_type, args.states, args.away, args.context_box)
        recipe = json.loads(args.recipe.read_text(encoding='utf8'))
        result = run(window, recipe['steps'])
        if args.output:
            result['capture'] = capture(window, args.output)
        return result


if __name__ == '__main__':
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2))
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps(dict(ok=False, error=str(error))))
        raise SystemExit(1)
