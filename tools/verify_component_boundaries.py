"""Only the settings edges, player/pack lists, close button and tick labels.

prepare() writes reference content inputs into a disposable demo resource pack.
The fixture uses the public library; it never paints replacement control edges.
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

from PIL import Image
import numpy as np

from capture_settings_pixels import operate
from verify_settings import SettingsVerification

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / 'docs/images/component-boundaries/references'
PIXELS = ROOT / '.agents/skills/bedrock-ore-reference/scripts/pixels.py'
spec = importlib.util.spec_from_file_location('ore_reference_pixels', PIXELS)
pixels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pixels)


def prepare(project):
    target = project / 'resource_pack/textures/boundary_fixture'
    target.mkdir(parents=True, exist_ok=True)
    for prefix, name, first in [('avatar', 'players.png', 24), ('pack', 'packs.png', 120)]:
        source = Image.open(REFERENCES / name)
        for index in range(4):
            source.crop((24, first + index * 140, 120, first + index * 140 + 96)).save(
                target / ('boundary_%s_%d.png' % (prefix, index)))


class BoundaryVerification(SettingsVerification):
    def __init__(self, session, owner, output):
        super().__init__(session, owner, output)
        self.screen = [504, 291]
        self.current_page = 'overview'

    def page(self, page):
        self.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
            'f=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) if f.key==%r)\n'
            'f.props["onClick"]()\n_result=True\n' % ('lab_page_' + page), 'page-' + page)
        self.current_page = page
        time.sleep(.3)

    def install_fixture(self):
        source = (ROOT / 'tools/fixtures/boundary_scene.py').read_text(encoding='utf8')
        self.code('import sys, types\nm=types.ModuleType("ore_boundary_fixture")\n'
                  'sys.modules[m.__name__]=m\nexec(%r,m.__dict__)\n_result=True\n'
                  % source.encode('ascii', 'backslashreplace').decode('ascii'), 'install-fixture')
        self.screen = [504, 291]

    def fixture(self, page, disabled=False):
        self.code('import ore_boundary_fixture as f\nf.mount(%r,%r)\n_result=True\n' % (page, disabled), 'fixture-' + page)
        time.sleep(.4)

    def frame(self, key):
        return self.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
            'h=host._ACTIVE_HOST[0]\nf=next(f for f in dev_probe._walk(h._root_fiber) if f.key==%r)\n'
            'p=next(c for c in dev_probe._walk(f) if c.native_path)\n'
            'c=h.GetBaseUIControl(p.native_path)\n_result=dict(position=c.GetGlobalPosition(),size=c.GetSize())\n' % key,
            'frame-' + key)

    def png(self, name, at=None):
        return operate(self.session, self.owner, output=self.output / (name + '.png'),
                       points=[(.03, .15), (.9, .04), (.95, .9)] + ([at] if at else []))

    def crop(self, name, frame, size=None):
        box = pixels.logical_box(frame['position'], size or frame['size'], 4)
        result = self.output / (name + '-crop.png')
        pixels.checked_crop(self.output / (name + '.png'), box).save(result)
        return result, box


def inspect(session, owner, output):
    r = BoundaryVerification(session, owner, output)
    r.install_fixture()
    observations = {}
    for page, key, name, size in [
            ('players', 'fixture_player_0', 'players', (160, 141)),
            ('packs', 'fixture_packs', 'packs', (325.25, 165)),
            ('expanded', 'fixture_pack_2', 'expanded', None),
            ('close', 'fixture_close', 'close', (22, 24)),
            ('sliders', 'fixture_content', 'sliders', None),
            ('sections', 'fixture_first', 'sections', None)]:
        r.fixture(page)
        frame = r.frame(key)
        if page == 'expanded':
            last = r.frame('fixture_pack_3')
            size = (325.25, last['position'][1] + last['size'][1] - frame['position'][1])
        metadata = r.png(name)
        crop, box = r.crop(name, frame, size)
        observations[name] = dict(frame=frame, crop_box=box, metadata=metadata)
        reference = REFERENCES / (name + '.png')
        if page == 'sections':
            # This fixture isolates the boundary structure. Its copy and row
            # layout differ from the complete supplied accessibility page.
            observations[name]['reference_scope'] = 'Boundary colors and one-pixel bands only; no full-page fidelity claim'
            continue
        if reference.exists():
            if Image.open(reference).size == Image.open(crop).size:
                observations[name]['comparison'] = pixels.compare(reference, crop, output / (name + '-comparison'))
            else:
                observations[name]['size_mismatch'] = dict(reference=Image.open(reference).size, actual=Image.open(crop).size)
        print(name, observations[name].get('comparison', observations[name].get('size_mismatch', frame)), flush=True)
    (output / 'inspection.json').write_text(json.dumps(observations, ensure_ascii=False, indent=2), encoding='utf8')
    return r


def verify_touch(r, check, native_switch=False):
    session, owner = r.session, r.owner
    transitions = []
    for touch in (True, False):
        depth = r.code('from ore_demo.pyreact import navigator\nnavigator.clear()\n_result=navigator.depth\n', 'close-before-f11')
        if depth != 0:
            raise AssertionError('Close the UI before F11')
        time.sleep(.3)
        if native_switch:
            # Documented as the engine API corresponding to PC F11. Never
            # label this fallback as a successful keyboard-mode-switch test.
            r.code('import mod.client.extraClientApi as c\n'
                'c.GetEngineCompFactory().CreateGame(c.GetLevelId()).SimulateTouchWithMouse(%r)\n'
                '_result=dict(simulated=c.IsTouchWithMouse())\n'
                % touch, 'native-touch-switch')
            time.sleep(.4)
        else:
            r.input([{'do':'key','keys':'f11'}, {'do':'wait','ms':400}], 'f11-touch' if touch else 'f11-mouse')
        # INPUT_MODE follows the next input, while IsTouchWithMouse changes
        # immediately. Tap the fixture's empty background before requiring
        # both native readbacks to agree; no control callback is invoked.
        r.fixture('players')
        r.tap_at((.9, .8), 'activate-' + ('touch' if touch else 'mouse'))
        r.png('input-mode-' + ('touch' if touch else 'mouse'))
        state = r.state()
        transitions.append(dict(requested_touch=touch, keyboard_changed=None if native_switch else state['simulated'] == touch and state['touch'] == touch,
            method='GameComponentClient.SimulateTouchWithMouse' if native_switch else 'F11', actual=state))
        ready = state['simulated'] == touch and state['touch'] == touch
        check('verified native input mode is ' + ('touch' if touch else 'mouse'), ready)
        if not ready:
            raise AssertionError('Input mode readback does not match; no checks executed in the wrong mode')
        if not touch:
            continue
        r.fixture('players')
        r.tap_at(r.scoped_at('fixture_player_0', 'ore_player_options'), 'touch-player-options')
        check('touch player options dispatch once', r.code('import ore_boundary_fixture as f\n_result=f.events\n', 'touch-player-events') == [['options',0]])
        r.fixture('packs')
        r.tap_at(r.scoped_at('fixture_pack_0', 'ore_pack_details'), 'touch-pack-details')
        r.tap_at(r.scoped_at('fixture_pack_0', 'ore_pack_action'), 'touch-pack-action')
        check('touch pack expansion and activation remain independent',
              r.frame('fixture_pack_0')['size'][1] > 36 and r.code('import ore_boundary_fixture as f\n_result=f.events\n', 'touch-pack-events') == [['activate',0]])
        r.fixture('close')
        r.tap_at(r.at('fixture_close'), 'touch-close')
        check('touch framed close dispatches once', r.code('import ore_boundary_fixture as f\n_result=f.events\n', 'touch-close-events') == [['close',None]])
        r.fixture('sliders')
        p = r.native_probe('touch-slider', ['fixture_slider'])['fixture_slider']
        x,y=p['position'];w,h=p['size']
        start=[(x+w*.5)/504,(y+h*.5)/291];end=[(x+w)/504,start[1]]
        operate(session, owner, steps=[{'do':'drag','from':start,'to':end,'segments':12,'hold_ms':240},{'do':'wait','ms':200}])
        check('touch labeled slider still snaps', r.native_probe('touch-slider-result',['fixture_slider'])['fixture_slider']['value'] == 4)
        r.mount();r.png('touch-scroll-shadows')
    return transitions


def verify(session, owner, output, native_switch=False):
    r = inspect(session, owner, output)
    comparisons = json.loads((output / 'inspection.json').read_text(encoding='utf8'))
    checks = []

    def check(name, condition):
        checks.append(dict(name=name, passed=bool(condition)))
        print(('PASS ' if condition else 'FAIL ') + name, flush=True)

    def reference(name):
        return np.asarray(Image.open(REFERENCES / (name + '.png')).convert('RGB'))

    def actual(name):
        return np.asarray(Image.open(output / (name + '-crop.png')).convert('RGB'))

    # Full-control comparisons retain text/antialias differences. These narrow
    # samples additionally test the precise defects without hiding that residual.
    for name, column in [('players', 450), ('packs', 800), ('expanded', 1280)]:
        a, b = actual(name), reference(name)
        check(name + ': complete reference dimensions', a.shape == b.shape)
        check(name + ': first, middle and final row borders', np.array_equal(a[:, column], b[:, column]))
    check('players: joined profile/options bevels have no black seam',
          np.array_equal(actual('players')[16:20, 492:508], reference('players')[16:20, 492:508]))
    check('packs: expanded gap is six logical pixels',
          np.array_equal(actual('expanded')[272:304], reference('expanded')[272:304]))
    check('close: all 8448 default pixels match', comparisons['close']['comparison']['native_exact'])
    # The whole controls must also meet a declared, nonzero residual budget.
    # Exact geometry is required above; fonts are still a different renderer.
    for name, budget in [('players', .04), ('packs', .045), ('expanded', .065)]:
        check(name + ': full control residual below ' + str(budget),
              comparisons[name]['comparison']['different_fraction'] <= budget)

    r.fixture('players')
    default = r.frame('fixture_player_0')
    for child, event in [('ore_player_profile', 'profile'), ('ore_player_options', 'options')]:
        point = r.scoped_at('fixture_player_0', child)
        r.png('players-hover-' + event, point)
        r.tap_at(point, 'players-click-' + event)
        events = r.code('import ore_boundary_fixture as f\n_result=f.events\n', 'player-events-' + event)
        check('player real click dispatches only ' + event, events[-1] == [event, 0] and len(events) == (1 if event == 'profile' else 2))
        image = np.asarray(Image.open(output / ('players-hover-' + event + '.png')).convert('RGB'))
        x, y = [round(n * 4) for n in default['position']]
        check('player hover preserves shared horizontal border: ' + event,
              np.all(image[y + 140:y + 144, x:x + 640] == (30, 30, 31)))
        check('player hover changes only its own cell: ' + event,
              tuple(image[y + 16, x + 450]) == ((88,88,90) if event == 'profile' else (72,73,74)) and
              tuple(image[y + 16, x + 600]) == ((112,112,113) if event == 'options' else (72,73,74)))

    r.fixture('packs')
    for child, action in [('ore_pack_details', 'details'), ('ore_pack_action', 'action')]:
        point = r.scoped_at('fixture_pack_0', child)
        r.png('packs-hover-' + action, point)
        r.tap_at(point, 'packs-click-' + action)
        events = r.code('import ore_boundary_fixture as f\n_result=f.events\n', 'pack-events-' + action)
        first, second = r.frame('fixture_pack_0'), r.frame('fixture_pack_1')
        check('pack ' + action + ' keeps independent activation', events == ([] if action == 'details' else [['activate', 0]]))
        check('expanded row reserves description plus six-pixel gap',
              abs(second['position'][1] - first['position'][1] - first['size'][1] - 6) < .001)
    r.fixture('packs', disabled=True)
    for child in ('ore_pack_details', 'ore_pack_action'):
        r.tap_at(r.scoped_at('fixture_pack_0', child), 'disabled-' + child)
    check('disabled pack blocks both actions', r.code('import ore_boundary_fixture as f\n_result=f.events\n', 'disabled-events') == [])
    check('disabled pack stays collapsed', r.frame('fixture_pack_0')['size'][1] == 36)

    r.fixture('close')
    point = r.at('fixture_close')
    r.png('close-hover', point)
    r.tap_at(point, 'close-click')
    check('framed close responds once', r.code('import ore_boundary_fixture as f\n_result=f.events\n', 'close-events') == [['close', None]])

    r.fixture('sliders')
    r.png('sliders-alignment')
    probe = r.native_probe('label-slider', ['fixture_slider'])['fixture_slider']
    markers = r.code('from ore_demo.pyreact import host\nh=host._ACTIVE_HOST[0]\n'
        '_result=[dict(position=h.GetBaseUIControl(%r+"/ore_tick_"+str(i)).GetGlobalPosition(),'
        'size=h.GetBaseUIControl(%r+"/ore_tick_"+str(i)).GetSize()) for i in range(3)]\n' % (probe['path'], probe['path']), 'markers')
    image = np.asarray(Image.open(output / 'sliders-alignment.png').convert('RGB'))
    label_y = round((probe['position'][1] + 16) * 4)
    for index, marker in enumerate(markers):
        center = (marker['position'][0] + marker['size'][0] / 2) * 4
        left = round(center) - 24
        white = np.all(image[label_y:label_y + 48, left:left + 48] > 200, axis=2)
        ys, xs = np.nonzero(white)
        ink_center = left + (int(xs.min()) + int(xs.max()) + 1) / 2
        check('label %d is centered under native tick' % (index + 5), abs(ink_center - center) <= .5)
    for target, expected in [(0, 0), (.24, 1), (.51, 2), (.78, 3), (1, 4)]:
        p = r.native_probe('drag-position', ['fixture_slider'])['fixture_slider']
        x, y = p['position']; w, h = p['size']
        start = [(x + w * p['value'] / 4) / 504, (y + h / 2) / 291]
        end = [(x + w * target) / 504, start[1]]
        operate(session, owner, points=[start], steps=None)
        operate(session, owner, steps=[{'do':'drag', 'from':start, 'to':end, 'segments':12, 'hold_ms':240}, {'do':'wait','ms':200}])
        check('labeled slider still snaps to %d' % expected,
              r.native_probe('drag-result', ['fixture_slider'])['fixture_slider']['value'] == expected)

    r.fixture('sections')
    frames = {key:r.frame('fixture_' + key) for key in ('first', 'middle', 'last', 'next')}
    r.png('sections-edges')
    image = np.asarray(Image.open(output / 'sections-edges.png').convert('RGB'))
    x = 1700
    first, middle, last, following = (frames[n] for n in ('first', 'middle', 'last', 'next'))
    fy = round(first['position'][1] * 4)
    my = round(middle['position'][1] * 4)
    ly = round((last['position'][1] + last['size'][1]) * 4)
    check('section starts with only one light line', np.all(image[fy - 4:fy, x] == (90,91,92)))
    check('section internal separator is dark then light',
          np.all(image[my - 8:my - 4, x] == (51,51,52)) and np.all(image[my - 4:my, x] == (90,91,92)))
    check('section ends with only one dark line', np.all(image[ly:ly + 4, x] == (51,51,52)))
    check('next heading starts after blank space', np.all(image[ly + 4:ly + 44, x] == (72,73,74)))

    # Measure font-family changes and line-height in the genuine Python 2 host.
    metrics = r.code('from ore_demo.oreui.typography import OreString,OreFont\n'
        'from ore_demo.pyreact import native,host\nfrom ore_demo.oreui._text import NativeOreText\n'
        'h=host._ACTIVE_HOST[0]\n'
        '_result=dict(pixel=native.measure_text(h,OreString("Version 1.2.0."),.7),'
        'body=native.measure_text(h,OreString("Version 1.2.0.",OreFont.body),.7),'
        'lines=native.measure_text(h,OreString("First\\nSecond",OreFont.body,10),.7),'
        'invalidate=NativeOreText.props_affect_layout({"fontFamily":OreFont.pixel},{"fontFamily":OreFont.body},None))\n', 'body-metrics')
    check('body font has independent width and explicit line height', metrics['pixel'][0] != metrics['body'][0] and metrics['lines'][1] == 20 and metrics['invalidate'])
    contract = r.code('from ore_demo.oreui import OreSettingsRow,OreSettingsSection\n'
        'marker=object()\nchild=OreSettingsRow(key="preserved",ref=marker,title="Last")\n'
        'section=OreSettingsSection._render(children=[child])\n'
        'copy=next(e for e in section.children if e.comp_type is OreSettingsRow)\n'
        '_result=copy is not child and copy.key==child.key and copy.ref is marker and '
        '"divider" not in child.props and copy.props["divider"] is False\n', 'section-contract')
    check('section preserves caller element, key and ref', contract)
    joined_keys = r.code('from ore_demo.oreui._joined import joined_rows\n'
        'from ore_demo.oreui import OrePlayerRow\n'
        'x=joined_rows([OrePlayerRow(key=u"\\u73a9\\u5bb6"),OrePlayerRow(key="second")])\n'
        '_result=x[0].key==u"ore_joined_\\u73a9\\u5bb6" and x[1].key=="ore_joined_second"\n', 'joined-unicode-key')
    check('joined rows preserve Unicode and ASCII keys', joined_keys)

    # Check both real scroll panes with content under their shadows.
    r.mount()
    r.png('scroll-shadows')
    roots = r.native_probe('scroll-roots', ['ore_settings_navigation', 'lab_scroll_overview_0'])
    image = Image.open(output / 'scroll-shadows.png').convert('RGB')
    check('right pane top shadow blends over light section edge', all(image.getpixel((1000,y)) == (79,80,80) for y in range(100,104)))
    suffix = '/scroll_mouse/scroll_view/stack_panel/bar_and_track/stack_panel/panel/centered_panel/scroll_box/box/mouse_box'
    thumb = r.code('from ore_demo.pyreact import host\nh=host._ACTIVE_HOST[0]\n'
        'c=h.GetBaseUIControl(%r)\n_result=dict(position=c.GetGlobalPosition(),size=c.GetSize())\n'
        % (roots['ore_settings_navigation']['path'] + suffix), 'thumb-bounds')
    bottom = round((thumb['position'][1] + thumb['size'][1]) * 4)
    left = round(thumb['position'][0] * 4)
    image.crop((left, bottom - 20, left + 24, bottom + 8)).save(output / 'thumb-bottom.png')
    pixels.checked_crop(REFERENCES / 'scroll-shadow.png', (0,23,24,51)).save(output / 'thumb-bottom-reference.png')
    thumb_comparison = pixels.compare(output / 'thumb-bottom-reference.png', output / 'thumb-bottom.png', output / 'thumb-bottom-comparison')
    check('thumb bevel, black edge and full-width translucent shadow match', thumb_comparison['native_exact'])
    # Put a light divider under the top shadow to rule out a hardcoded gray strip.
    r.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host,ScrollView\n'
        'h=host._ACTIVE_HOST[0]\nc=dev_probe.controls(["lab_scroll_overview_0","lab_game_mode"])\n'
        's=c["lab_scroll_overview_0"]\n'
        '_result=ScrollView.scroll_to(h.GetBaseUIControl(s["path"]), c["lab_game_mode"]["position"][1]-s["position"][1])\n', 'scroll-under-shadow')
    r.png('right-shadow-content')
    # The first selected segment is a different color from the section surface.
    top = Image.open(output / 'right-shadow-content.png').convert('RGB')
    check('right shadow blends over scrolling control content',
          all(top.getpixel((800,y)) == (26,26,27) and top.getpixel((1300,y)) == (63,64,65) for y in range(100,104)))

    # One focused touch pass through the same changed controls. Always close
    # the UI before F11, and restore mouse mode at the end.
    transitions = verify_touch(r, check, native_switch=native_switch)

    r.mount(); r.page('containers')
    # Use the tab callback only to choose the demonstration's available list.
    r.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
        'f=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) if f.key=="lab_pack_tabs")\n'
        'f.props["onChange"]("available")\n_result=True\n', 'demo-available-packs')
    r.png('demo-packs-final')
    r.tap_at(r.scoped_at('lab_pack_1','ore_pack_details'),'demo-expand')
    r.png('demo-packs-expanded-final')
    r.tap('ore_settings_social')
    r.png('demo-friends-final')
    r.tap_at(r.at('ore_friends_close'),'demo-close-friends')
    check('public friends close dismisses actual overlay', r.business()['overlay'] is None)
    report = dict(scope='Only the changed component boundaries and their input behavior',
        client=[2016,1164], scale=4, comparisons=comparisons, thumb_comparison=thumb_comparison,
        checks=checks, mode_transitions=transitions, hardware_touch_tested=False,
        f11_automation_verified=not native_switch and all(t['keyboard_changed'] for t in transitions),
        passed=all(c['passed'] for c in checks))
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    return report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--session')
    parser.add_argument('--owner', default='codex-boundaries')
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/component-boundaries/actual')
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--touch-only', action='store_true')
    parser.add_argument('--touch-via-api', action='store_true', help='Use the documented native touch-mode API instead of sending F11')
    args = parser.parse_args()
    if args.prepare:
        prepare(args.prepare)
    if args.session:
        if args.touch_only:
            r = BoundaryVerification(args.session, args.owner, args.output.resolve())
            r.install_fixture()
            revised = []
            def check(name, condition):
                revised.append(dict(name=name, passed=bool(condition)))
                print(('PASS ' if condition else 'FAIL ') + name, flush=True)
            transitions = verify_touch(r, check, native_switch=args.touch_via_api)
            report = json.loads((r.output / 'report.json').read_text(encoding='utf8'))
            names = {item['name'] for item in revised}
            report['checks'] = [item for item in report['checks'] if item['name'] not in names and not item['name'].startswith('F11 input mode')] + revised
            report['passed'] = all(item['passed'] for item in report['checks'])
            report['mode_transitions'] = transitions
            report['f11_automation_verified'] = not args.touch_via_api and all(t['keyboard_changed'] for t in transitions)
            report['hardware_touch_tested'] = False
            (r.output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
            r.mount()
            raise SystemExit(0 if report['passed'] else 1)
        if args.verify:
            raise SystemExit(0 if verify(args.session, args.owner, args.output.resolve(), native_switch=args.touch_via_api) else 1)
        inspect(args.session, args.owner, args.output.resolve())
