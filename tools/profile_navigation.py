"""Profile rapid mouse navigation changes in the Ore settings replica.

The script uses the existing bound-game verification client and the reference
desktop input helper, but keeps all counters temporary.  It records the game
process timestamps for button touch-up, NavigatorScreen.Update, and layout
passes, then correlates each physical click with the first update that shows
the requested page.  No runtime source files are modified.

Example::

    python tools/profile_navigation.py --session session.json --owner agent \
        --output .runtime/navigation-profile --rate-hz 10 --cycles 2
"""
from __future__ import print_function

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

from verify_seams_scroll import SeamVerification


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / '.agents/skills/bedrock-ore-reference/scripts'


# All code in this string executes in the game's Python 2 client.  It only
# appends compact, JSON-compatible dictionaries to temporary class/module
# buffers and restores are performed by CLEANUP in the finally block below.
INSTALL_PROBE = r'''
import time as _ore_profile_time
from ore_demo.pyreact import host as _ore_profile_host
from ore_demo.pyreact import layout as _ore_profile_layout
import sys as _ore_profile_sys
_ore_profile_nav = _ore_profile_sys.modules["ore_demo.pyreact.navigator"]
from ore_demo import dev_probe as _ore_profile_probe
from ore_demo.oreui.navigation import NavigationGlintPrimitive as _OreGlint

if not hasattr(_OreGlint, '_ore_profile_sync'):
    _OreGlint._ore_profile_sync = _OreGlint._sync_frame_animation
    _OreGlint._ore_profile_frames = []
    def _ore_glint_sync(self, host, fiber, image, frames, props):
        starts = fiber.primitive_state.get('ore_glint_selected') is False and props.get('selected')
        _OreGlint._ore_profile_sync(self, host, fiber, image, frames, props)
        if starts:
            _OreGlint._ore_profile_frames.append(dict(time=_ore_profile_time.clock(),
                action='start', path=fiber.native_path, index=0))
    _OreGlint._sync_frame_animation = _ore_glint_sync

_ore_profile_screen = _ore_profile_nav.NavigatorScreen
if not hasattr(_ore_profile_screen, '_ore_profile_original_update'):
    _ore_profile_screen._ore_profile_original_update = _ore_profile_screen.Update
    _ore_profile_screen._ore_profile_updates = []
    _ore_profile_runtime = _ore_profile_host._ACTIVE_HOST[0]
    _ore_profile_fibers = list(_ore_profile_probe._walk(_ore_profile_runtime._root_fiber))
    _ore_profile_glints = [f for f in _ore_profile_fibers if isinstance(f.comp_type, _OreGlint)]
    _ore_profile_seen_frames = {}
    _ore_profile_replica = next((f for f in _ore_profile_fibers
        if getattr(getattr(f, 'comp_type', None), '__name__', '') == 'OreSettingsReplica'), None)
    if _ore_profile_replica is None:
        raise RuntimeError('OreSettingsReplica is not mounted')
    _ore_profile_screen._ore_profile_replica = _ore_profile_replica
    _ore_profile_screen._ore_profile_last_page = _ore_profile_replica.hooks[0]['value']
    _ore_profile_screen._ore_profile_updates.append(dict(
        time=_ore_profile_time.clock(), page=_ore_profile_screen._ore_profile_last_page,
        fibers=len(_ore_profile_fibers), native=sum(1 for f in _ore_profile_fibers if f.native_path),
        glyphs=sum(len(f.primitive_state.get('ore_glyph_pool', ())) for f in _ore_profile_fibers),
        animations=len(getattr(_ore_profile_runtime, '_animation_frames', {})), baseline=True))
    _ore_profile_original_update = _ore_profile_screen._ore_profile_original_update
    def _ore_profile_update(self):
        _ore_profile_original_update(self)
        if not getattr(self, '_navigator_active', False):
            return
        try:
            runtime = _ore_profile_host._ACTIVE_HOST[0]
            replica = _ore_profile_screen._ore_profile_replica
            page = replica.hooks[0]['value'] if replica and replica.hooks else None
            sample = dict(time=_ore_profile_time.clock(), page=page,
                          animations=len(getattr(runtime, '_animation_frames', {})))
            if page != _ore_profile_screen._ore_profile_last_page:
                fibers = list(_ore_profile_probe._walk(runtime._root_fiber))
                sample.update(fibers=len(fibers),
                    native=sum(1 for f in fibers if f.native_path),
                    glyphs=sum(len(f.primitive_state.get('ore_glyph_pool', ())) for f in fibers),
                    dirty=len(getattr(runtime, '_dirty', ())),
                    layout_dirty=bool(getattr(runtime, '_commit_layout_dirty', False)))
                _ore_profile_screen._ore_profile_last_page = page
            _ore_profile_screen._ore_profile_updates.append(sample)
            for f in _ore_profile_glints:
                index = f.primitive_state['_image_frame_animation']['index']
                if _ore_profile_seen_frames.get(f.native_path) != index:
                    _ore_profile_seen_frames[f.native_path] = index
                    _OreGlint._ore_profile_frames.append(dict(time=sample['time'],
                        action='frame', path=f.native_path, index=index))
        except Exception:
            # Profiling must not change game behavior if a transient screen is
            # between native teardown and the next mount.
            pass
    _ore_profile_screen.Update = _ore_profile_update

if not hasattr(_ore_profile_layout, '_ore_profile_original_layout_tree'):
    _ore_profile_layout._ore_profile_original_layout_tree = _ore_profile_layout.layout_tree
    _ore_profile_layout._ore_profile_layouts = []
    _ore_profile_original_layout = _ore_profile_layout._ore_profile_original_layout_tree
    def _ore_profile_layout_tree(*args, **kwargs):
        started = _ore_profile_time.clock()
        result = _ore_profile_original_layout(*args, **kwargs)
        _ore_profile_layout._ore_profile_layouts.append(dict(
            time=_ore_profile_time.clock(), duration_ms=(_ore_profile_time.clock() - started) * 1000.0,
            ready=bool(result[0]) if isinstance(result, tuple) else bool(result)))
        return result
    _ore_profile_layout.layout_tree = _ore_profile_layout_tree

if not hasattr(_ore_profile_host.PyreactScreenNode, '_ore_profile_original_register_animation'):
    _ore_profile_host.PyreactScreenNode._ore_profile_original_register_animation = _ore_profile_host.PyreactScreenNode.pyreact_register_animation_frame
    _ore_profile_host.PyreactScreenNode._ore_profile_original_unregister_animation = _ore_profile_host.PyreactScreenNode.pyreact_unregister_animation_frame
    _ore_profile_host.PyreactScreenNode._ore_profile_animation_events = []
    _ore_profile_original_register = _ore_profile_host.PyreactScreenNode._ore_profile_original_register_animation
    _ore_profile_original_unregister = _ore_profile_host.PyreactScreenNode._ore_profile_original_unregister_animation
    def _ore_profile_register_animation(self, slot):
        _ore_profile_original_register(self, slot)
        _ore_profile_host.PyreactScreenNode._ore_profile_animation_events.append(dict(
            time=_ore_profile_time.clock(), action='register', active=len(self._animation_frames)))
    def _ore_profile_unregister_animation(self, slot):
        _ore_profile_original_unregister(self, slot)
        _ore_profile_host.PyreactScreenNode._ore_profile_animation_events.append(dict(
            time=_ore_profile_time.clock(), action='unregister', active=len(self._animation_frames)))
    _ore_profile_host.PyreactScreenNode.pyreact_register_animation_frame = _ore_profile_register_animation
    _ore_profile_host.PyreactScreenNode.pyreact_unregister_animation_frame = _ore_profile_unregister_animation

_ore_profile_runtime = _ore_profile_host._ACTIVE_HOST[0]
_ore_profile_runtime._ore_profile_page_by_path = {}
for f in _ore_profile_probe._walk(_ore_profile_runtime._root_fiber):
    if f.key and str(f.key).startswith('settings_page_'):
        button = next(child for child in _ore_profile_probe._walk(f) if child.native_path)
        _ore_profile_runtime._ore_profile_page_by_path[button.native_path] = str(f.key)[len('settings_page_'):]


_ore_profile_class = _ore_profile_host.PyreactScreenNode
if not hasattr(_ore_profile_class, '_ore_profile_original_register_button'):
    from functools import partial as _ore_profile_partial
    _ore_profile_class._ore_profile_original_register_button = _ore_profile_class.pyreact_register_button
    _ore_profile_class._ore_profile_touch_ups = []
    def _ore_profile_click(self, path, callback):
        started = _ore_profile_time.clock()
        callback()
        _ore_profile_class._ore_profile_touch_ups.append(dict(time=started,
            end_time=_ore_profile_time.clock(), path=path,
            page=self._ore_profile_page_by_path.get(path)))
    def _ore_profile_register_button(self, path, down, up, click):
        if click and path in getattr(self, '_ore_profile_page_by_path', {}):
            click = _ore_profile_partial(_ore_profile_click, self, path, click)
        return _ore_profile_class._ore_profile_original_register_button(self, path, down, up, click)
    _ore_profile_class.pyreact_register_button = _ore_profile_register_button
    for path in _ore_profile_runtime._ore_profile_page_by_path:
        handlers = _ore_profile_runtime._button_handlers.get(path)
        if handlers:
            _ore_profile_runtime.pyreact_register_button(path, *handlers)

_result=True
'''


READ_PROBE = r'''
from ore_demo.pyreact import host as _ore_profile_host
from ore_demo.pyreact import layout as _ore_profile_layout
import sys as _ore_profile_sys
_ore_profile_nav = _ore_profile_sys.modules["ore_demo.pyreact.navigator"]
from ore_demo.oreui.navigation import NavigationGlintPrimitive as _OreGlint
_result=dict(
    glint_frames=list(getattr(_OreGlint, '_ore_profile_frames', ())),
    updates=list(getattr(_ore_profile_nav.NavigatorScreen, '_ore_profile_updates', ())),
    touch_ups=list(getattr(_ore_profile_host.PyreactScreenNode, '_ore_profile_touch_ups', ())),
    animation_events=list(getattr(_ore_profile_host.PyreactScreenNode, '_ore_profile_animation_events', ())),
    layouts=list(getattr(_ore_profile_layout, '_ore_profile_layouts', ())))
'''


CLEANUP_PROBE = r'''
from ore_demo.oreui.navigation import NavigationGlintPrimitive as _OreGlint
if hasattr(_OreGlint, '_ore_profile_sync'):
    _OreGlint._sync_frame_animation = _OreGlint._ore_profile_sync
    del _OreGlint._ore_profile_sync
    del _OreGlint._ore_profile_frames
from ore_demo.pyreact import host as _ore_profile_host
from ore_demo.pyreact import layout as _ore_profile_layout
import sys as _ore_profile_sys
_ore_profile_nav = _ore_profile_sys.modules["ore_demo.pyreact.navigator"]
_ore_profile_screen = _ore_profile_nav.NavigatorScreen
if hasattr(_ore_profile_screen, '_ore_profile_original_update'):
    _ore_profile_screen.Update = _ore_profile_screen._ore_profile_original_update
    del _ore_profile_screen._ore_profile_original_update
    del _ore_profile_screen._ore_profile_updates
    for name in ('_ore_profile_replica', '_ore_profile_last_page'):
        if hasattr(_ore_profile_screen, name):
            delattr(_ore_profile_screen, name)
if hasattr(_ore_profile_layout, '_ore_profile_original_layout_tree'):
    _ore_profile_layout.layout_tree = _ore_profile_layout._ore_profile_original_layout_tree
    del _ore_profile_layout._ore_profile_original_layout_tree
    del _ore_profile_layout._ore_profile_layouts
_ore_profile_class = _ore_profile_host.PyreactScreenNode
if hasattr(_ore_profile_class, '_ore_profile_original_register_button'):
    _ore_profile_class.pyreact_register_button = _ore_profile_class._ore_profile_original_register_button
    del _ore_profile_class._ore_profile_original_register_button
    del _ore_profile_class._ore_profile_touch_ups
    runtime = _ore_profile_host._ACTIVE_HOST[0]
    if runtime:
        for path, handlers in list(runtime._button_handlers.items()):
            callback = handlers[2]
            if getattr(getattr(callback, 'func', None), '__name__', '') == '_ore_profile_click':
                runtime._button_handlers[path] = (handlers[0], handlers[1], callback.args[2])
if hasattr(_ore_profile_host, '_ACTIVE_HOST') and _ore_profile_host._ACTIVE_HOST[0] is not None:
    _ore_profile_host._ACTIVE_HOST[0].__dict__.pop('_ore_profile_page_by_path', None)
if hasattr(_ore_profile_host.PyreactScreenNode, '_ore_profile_original_register_animation'):
    _ore_profile_host.PyreactScreenNode.pyreact_register_animation_frame = _ore_profile_host.PyreactScreenNode._ore_profile_original_register_animation
    _ore_profile_host.PyreactScreenNode.pyreact_unregister_animation_frame = _ore_profile_host.PyreactScreenNode._ore_profile_original_unregister_animation
    del _ore_profile_host.PyreactScreenNode._ore_profile_original_register_animation
    del _ore_profile_host.PyreactScreenNode._ore_profile_original_unregister_animation
    del _ore_profile_host.PyreactScreenNode._ore_profile_animation_events
_result=True
'''


TARGETS = r'''
from ore_demo.pyreact import host as _ore_profile_host, native as _ore_profile_native
from ore_demo.pyreact.primitives import ScrollViewPrimitive as _OreScrollView
from ore_demo import dev_probe as _ore_profile_probe
runtime = _ore_profile_host._ACTIVE_HOST[0]
screen = _ore_profile_native.get_screen_size()
nav_scroll = next(f for f in _ore_profile_probe._walk(runtime._root_fiber)
                  if f.key == 'ore_settings_navigation' and isinstance(f.comp_type, _OreScrollView))
nav_control = runtime.GetBaseUIControl(nav_scroll.native_path)
nav_x, nav_y = nav_control.GetGlobalPosition()
nav_w, nav_h = nav_control.GetSize()
result = {}
for fiber in _ore_profile_probe._walk(runtime._root_fiber):
    key = fiber.key
    if not key or not str(key).startswith('settings_page_'):
        continue
    button = next(child for child in _ore_profile_probe._walk(fiber) if child.native_path)
    control = runtime.GetBaseUIControl(button.native_path)
    if control is None:
        continue
    x, y = control.GetGlobalPosition()
    width, height = control.GetSize()
    clipped_left = max(x, nav_x)
    clipped_top = max(y, nav_y)
    clipped_right = min(x + width, nav_x + nav_w)
    clipped_bottom = min(y + height, nav_y + nav_h)
    is_visible = clipped_right > clipped_left and clipped_bottom > clipped_top
    result[str(key)[len('settings_page_'):]] = dict(
        key=key, path=button.native_path,
        position=[((clipped_left + clipped_right) / 2.0) / screen[0],
                  ((clipped_top + clipped_bottom) / 2.0) / screen[1]],
        size=[width, height], visible=is_visible,
        geometry=[x, y, width, height])
_result=dict(screen=screen, viewport=[nav_x, nav_y, nav_w, nav_h], targets=result)
'''


def _reference_desktop():
    """Load the skill desktop helper without relying on PYTHONPATH state."""
    sys.path.insert(0, str(REFERENCE))
    path = REFERENCE / 'desktop.py'
    spec = importlib.util.spec_from_file_location('ore_profile_desktop', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _navigation_pages(r):
    return r.code(
        'from ore_demo.settings_catalog import NAVIGATION\n'
        '_result=[name for unused,items in NAVIGATION for unused,name in items]\n',
        'navigation-pages')


def _mount(r):
    r.code('from ore_demo.pyreact import navigator\n'
           'navigator.clear()\n_result=True\n', 'close-existing')
    time.sleep(.2)
    r.code('from ore_demo.pyreact import navigator\n'
           'from ore_demo.settings_replica import OreSettingsReplica\n'
           'navigator.push(OreSettingsReplica)\n_result=True\n', 'open-settings')
    time.sleep(.8)


def _click_sequence(pages, cycles):
    forward = list(pages)
    backward = list(reversed(pages))
    result = []
    for unused in range(cycles):
        for page in forward + backward:
            if not result or result[-1] != page:
                result.append(page)
    return result


def _send_clicks(desktop, session, targets, sequence, rate_hz, hold_ms):
    """Send clicks under the shared desktop lock and return host-side times."""
    binding = json.loads(session.read_text('utf8'))
    identity = desktop.process(binding['game_pid'])
    if not identity or str(identity['created']) != str(binding['game_identity']) or not desktop.same_path(identity['exe'], binding['game_executable']):
        raise RuntimeError('Owned game identity is stale')
    if 'MinecraftPE_Netease' not in identity['exe']:
        raise RuntimeError('Navigation profiling requires the bound development client')
    matches = [w for w in desktop.windows() if w['pid'] == binding['game_pid']]
    if len(matches) != 1:
        raise RuntimeError('Expected one owned game window')
    data = matches[0]
    interval = 1.0 / rate_hz
    records = []
    next_release = time.perf_counter()
    with desktop.desktop_lock():
        desktop.activate(data)
        for index, page in enumerate(sequence):
            target = targets[page]
            next_release = max(next_release, time.perf_counter())
            desktop.foreground(data)
            desktop.pointer(data, target['position'])
            desktop.U.mouse_event(2, 0, 0, 0, 0)
            down = time.perf_counter()
            try:
                time.sleep(max(0.0, hold_ms / 1000.0))
            finally:
                desktop.U.mouse_event(4, 0, 0, 0, 0)
            released = time.perf_counter()
            records.append(dict(index=index, page=page, target=target,
                                down_monotonic=down, release_monotonic=released,
                                interval_target=interval))
            next_release += interval
            delay = next_release - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
    return records


def _summarize(clicks, runtime):
    updates = runtime.get('updates', [])
    touch_ups = runtime.get('touch_ups', [])
    # Align event sequences once; never match a dropped click to a later visit.
    from difflib import SequenceMatcher
    matched = {}
    for block in SequenceMatcher(None, [c['page'] for c in clicks],
                                 [e.get('page') for e in touch_ups], autojunk=False).get_matching_blocks():
        for offset in range(block.size):
            matched[block.a + offset] = block.b + offset
    rows = []
    for click_index, click in enumerate(clicks):
        event_index = matched.get(click_index)
        event = touch_ups[event_index] if event_index is not None else None
        deadline = (touch_ups[event_index + 1]['time']
                    if event_index is not None and event_index + 1 < len(touch_ups) else float('inf'))
        expected_time = event.get('time') if event else None
        first = None
        before = None
        if expected_time is not None:
            for update in reversed(updates):
                if update.get('time', 0) < expected_time and 'fibers' in update:
                    before = update
                    break
            for update in updates:
                if (expected_time <= update.get('time', 0) < deadline and update.get('page') == click['page']
                        and 'fibers' in update):
                    first = update
                    break
        row = dict(click)
        row['touch_up'] = event
        row['status'] = ('committed' if first else 'superseded_before_update' if event else 'no_callback')
        row['first_matching_update'] = first
        row['commit_delay_ms'] = ((first['time'] - expected_time) * 1000.0
                                  if first is not None and expected_time is not None else None)
        row['physical_hold_ms'] = (click['release_monotonic'] - click['down_monotonic']) * 1000.0
        row['pre_transition_counts'] = ({name: before.get(name) for name in ('fibers', 'native', 'glyphs', 'animations')}
                                        if before else None)
        row['post_transition_counts'] = ({name: first.get(name) for name in ('fibers', 'native', 'glyphs', 'animations')}
                                         if first else None)
        row['count_delta'] = ({name: first.get(name, 0) - before.get(name, 0)
                               for name in ('fibers', 'native', 'glyphs', 'animations')}
                              if first and before else None)
        rows.append(row)
    deltas = [max(0.0, updates[i]['time'] - updates[i - 1]['time']) * 1000.0
              for i in range(1, len(updates))]
    ordered = sorted(deltas)
    def percentile(value):
        if not ordered:
            return None
        return ordered[int((len(ordered) - 1) * value)]
    return dict(clicks=rows, update_count=len(updates), touch_up_count=len(touch_ups),
                layout_count=len(runtime.get('layouts', [])), layouts=runtime.get('layouts', []),
                update_intervals_ms=deltas,
                update_interval_p50_ms=percentile(.50),
                update_interval_p95_ms=percentile(.95),
                update_interval_p99_ms=percentile(.99),
                max_update_interval_ms=max(deltas) if deltas else None,
                matching_commits=sum(1 for row in rows if row['first_matching_update'] is not None),
                missing_callbacks=sum(1 for row in rows if row['status'] == 'no_callback'),
                superseded_clicks=sum(1 for row in rows if row['status'] == 'superseded_before_update'),
                animation_events=runtime.get('animation_events', []),
                commit_delays_ms=[row['commit_delay_ms'] for row in rows
                                  if row['commit_delay_ms'] is not None])


def profile(session, owner, output, rate_hz=10.0, cycles=1, pages=None, hold_ms=45, warm_cache=False):
    if not 5.0 <= rate_hz <= 10.0:
        raise ValueError('rate_hz must be between 5 and 10')
    output.mkdir(parents=True, exist_ok=True)
    r = SeamVerification(session, owner, output)
    from capture_settings_pixels import operate
    operate(session, owner)
    time.sleep(1.0)  # Allow foreground-triggered hot reload before installing hooks.
    _mount(r)
    try:
        available = _navigation_pages(r)
        target_data = r.code(TARGETS, 'navigation-targets')
        visible = [page for page in available
                   if page in target_data['targets'] and target_data['targets'][page]['visible']]
        selected = list(pages or visible)
        unknown = [page for page in selected if page not in available]
        if unknown:
            raise ValueError('Unknown settings page(s): ' + ', '.join(unknown))
        missing = [page for page in selected if page not in target_data['targets']]
        if missing:
            raise RuntimeError('Navigation item geometry missing: ' + ', '.join(missing))
        hidden = [page for page in selected if not target_data['targets'][page]['visible']]
        if hidden:
            raise ValueError('Settings navigation target is outside the visible sidebar: ' + ', '.join(hidden))
        if warm_cache:
            for page in selected:
                r.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
                    'f=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) if f.key==%r)\n'
                    'f.props["onClick"]()\n_result=True' % ('settings_page_'+page), 'warm-'+page)
                time.sleep(.5)
            time.sleep(.8)
        r.code(INSTALL_PROBE, 'install-navigation-probe')
        sequence = _click_sequence(selected, cycles)
        desktop = _reference_desktop()
        clicks = _send_clicks(desktop, session, target_data['targets'], sequence, rate_hz, hold_ms)
        # Let the last touch-up schedule and flush before reading the buffers.
        time.sleep(max(.9, 3.0 / rate_hz))
        runtime = r.code(READ_PROBE, 'read-navigation-probe')
        report = dict(scope='OreSettingsReplica rapid mouse navigation', rate_hz=rate_hz,
                      hold_ms=hold_ms, cycles=cycles, pages=selected, warm_cache=warm_cache,
                      sequence=sequence, targets=target_data, runtime=runtime,
                      actual_click_rate_hz=((len(clicks) - 1) /
                          (clicks[-1]['release_monotonic'] - clicks[0]['release_monotonic'])
                          if len(clicks) > 1 else None),
                      sample=_summarize(clicks, runtime))
        (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
        print(json.dumps(dict(output=str(output), clicks=len(clicks),
                              updates=report['sample']['update_count'],
                              layouts=report['sample']['layout_count'],
                              matching_commits=report['sample']['matching_commits']), ensure_ascii=False), flush=True)
        if not report['sample']['touch_up_count']:
            raise RuntimeError('No actual click callbacks observed; this is not a valid navigation timing sample')
        return report
    finally:
        try:
            r.code(CLEANUP_PROBE, 'cleanup-navigation-probe')
        finally:
            # Leave the sample page available for an interactive developer,
            # while ensuring no profiling hooks survive this process.
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rate-hz', type=float, default=10.0)
    parser.add_argument('--cycles', type=int, default=1)
    parser.add_argument('--hold-ms', type=float, default=45.0)
    parser.add_argument('--pages', nargs='+')
    parser.add_argument('--warm-cache', action='store_true')
    args = parser.parse_args()
    if args.cycles < 1 or args.hold_ms < 0 or args.hold_ms > 5000:
        parser.error('--cycles must be positive and --hold-ms must be 0..5000')
    profile(args.session, args.owner, args.output, args.rate_hz, args.cycles,
            args.pages, args.hold_ms, args.warm_cache)


if __name__ == '__main__':
    main()
