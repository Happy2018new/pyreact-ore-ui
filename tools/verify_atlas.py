"""Real native mouse/F11 input regression for the redesigned component atlas."""
import argparse
import json
import re
import time
from pathlib import Path

from live_support import ROOT, RuntimeTools, find_key, labels, nodes


PAGES = ('overview', 'buttons', 'selection', 'toggles', 'fields', 'dropdowns',
         'sliders', 'feedback', 'cards', 'navigation', 'containers', 'messages',
         'dialogs', 'media', 'coverage')


class AtlasVerification(RuntimeTools):
    def check(self, label, condition):
        super().check(label, condition)
        print('PASS ' + label, flush=True)

    def code(self, source, name='exec'):
        path = self.output / (name + '.py')
        path.write_text(source.encode('ascii', 'backslashreplace').decode('ascii'), encoding='utf8')
        return json.loads(self.run('mcdk.py', 'exec', str(path)))

    def input(self, steps, name='input'):
        remaining = steps
        for attempt in range(3):
            windows = json.loads(self.run('resize_window.py', '--list-windows'))['windows']
            if len(windows) != 1:
                raise RuntimeError('Expected the bound game window')
            window = windows[0]
            self.run('resize_window.py', '--pid', str(window['pid']), '--size',
                     '%dx%d' % (window['width'], window['height']), '--no-center', '--settle', '0.2')
            path = self.output / (name + '.json')
            path.write_text(json.dumps({'op': '/run', 'args': {'steps': remaining,
                             'budget_ms': 5000}}), encoding='utf8')
            try:
                result = json.loads(self.run('mcdk.py', 'call', 'mc_input', '--args-file', str(path)))
            except RuntimeError as error:
                message = str(error)
                if '{' not in message:
                    raise
                result, _ = json.JSONDecoder().raw_decode(message[message.index('{'):])
            (self.output / (name + '-result-%d.json' % attempt)).write_text(json.dumps(result), encoding='utf8')
            details = result.get('structuredContent', {})
            if details.get('ok'):
                return result
            error = details.get('error') or {}
            progress = error.get('progress') or {}
            if error.get('code') not in ('FOCUS_DENIED', 'FOCUS_LOST') or progress.get('held'):
                raise RuntimeError(json.dumps(result, ensure_ascii=False))
            # Resume only the tool-confirmed unfinished steps; never replay a tap.
            remaining = remaining[progress.get('failed_index', 0):]
            print('RESUME after ' + error['code'], flush=True)
        raise RuntimeError('Game foreground remained unavailable after bounded recovery')

    def state(self):
        return self.code('from ore_demo import dev_probe\n_result=dev_probe.input_mode()\n', 'input-mode')

    def mount(self):
        self.code('from ore_demo.pyreact import navigator\nfrom ore_demo.playground import OrePlayground\n'
                  'navigator.reset(OrePlayground)\n_result=True\n', 'mount')
        time.sleep(0.4)
        self.current_page = 'buttons'

    def page(self, page):
        self.click('lab_page_' + page)
        self.current_page = page
        return self.dump('page-' + page)

    def scroll(self, page, percent):
        self.code('from ore_demo import dev_probe\n_result=dev_probe.scroll_to(%r,%r)\n'
                  % ('lab_scroll_' + page + '_0', percent), 'scroll-' + page)
        time.sleep(0.2)

    def at(self, key):
        probe = self.native_probe('native-' + key, [key])[key]
        screen = self.screen
        x, y = probe['position']
        width, height = probe['size']
        at = [(x + width / 2) / screen[0], (y + height / 2) / screen[1]]
        if not all(0 < number < 1 for number in at):
            raise AssertionError('Target off screen: %s %s' % (key, at))
        return at

    def tap(self, key):
        self.code('from ore_demo import dev_probe\n_result=dev_probe.reveal(%r,%r)\n'
                  % ('lab_scroll_' + self.current_page + '_0', key), 'reveal-' + key)
        time.sleep(0.35)
        at = self.at(key)
        self.tap_at(at, 'tap-' + key)

    def tap_at(self, at, name):
        self.input([{'do': 'move', 'at': at}, {'do': 'wait', 'ms': 150},
                    {'do': 'click', 'at': at, 'hold_ms': 150},
                    {'do': 'wait', 'ms': 350}], name)

    def capture(self, name):
        self.run('mcdk.py', 'capture', '--output', str(self.output / (name + '.jpg')))

    def event_count(self):
        tree = self.dump('event-state')
        content = find_key(tree, 'lab_events')['props']['content']
        return int(re.match(r'操作 (\d+) 次', content)[1])

    def disabled(self, key):
        before = self.event_count()
        self.tap(key)
        self.check('disabled rejects native tap: ' + key, self.event_count() == before)

    def hover(self, key, native_child='hover'):
        self.code('from ore_demo import dev_probe\n_result=dev_probe.reveal(%r,%r)\n'
                  % ('lab_scroll_' + self.current_page + '_0', key), 'reveal-hover-' + key)
        time.sleep(0.3)
        probe = self.native_probe('hover-' + key, [key])[key]
        self.input([{'do': 'move', 'at': [0.95, 0.08]}, {'do': 'wait', 'ms': 150},
                    {'do': 'move', 'at': self.at(key)}, {'do': 'wait', 'ms': 250}], 'hover-' + key)
        visible = self.code('from ore_demo.pyreact import host\n'
                            '_result=host._ACTIVE_HOST[0].GetBaseUIControl(%r).GetVisible()\n'
                            % (probe['path'] + '/' + native_child), 'hover-visible-' + key)
        self.check('native Ore hover visible: ' + key, visible)
        self.capture('hover-' + key)

    def set_touch(self, enabled):
        if self.state()['simulated'] == enabled:
            return
        self.tap('lab_close')
        depth = self.code('from ore_demo.pyreact import navigator\n_result=navigator.depth\n', 'closed')
        self.check('UI closed before F11', depth == 0)
        self.input([{'do': 'key', 'keys': 'f11'}, {'do': 'wait', 'ms': 350}], 'f11')
        self.check('native F11 readback: ' + str(enabled), self.state()['simulated'] == enabled)
        self.input([{'do': 'key', 'keys': 'f8'}, {'do': 'wait', 'ms': 500}], 'f8')
        opened = self.dump('f8-reopened')
        self.check('F8 reopens real UI', 'Ore UI · 控件图鉴' in labels(opened))
        self.mount()

    def drag_slider(self, key, target=0.8):
        probe = self.native_probe('slider-before', [key])[key]
        x, y = probe['position']
        width, height = probe['size']
        fraction = probe['value']
        if key == 'lab_step_slider':
            fraction /= 4
        start = [(x + width * fraction) / self.screen[0],
                 (y + height / 2) / self.screen[1]]
        end = [(x + width * target) / self.screen[0], start[1]]
        self.input([{'do': 'move', 'at': start}, {'do': 'wait', 'ms': 250},
                    {'do': 'drag', 'from': start, 'to': end, 'segments': 20,
                     'hold_ms': 300}, {'do': 'wait', 'ms': 400}], 'drag-' + key)
        return self.native_probe('slider-after', [key])[key]['value']

    def verify_controls(self, touch=False):
        mode = 'touch' if touch else 'mouse'
        self.page('buttons')
        self.tap('lab_primary_raised')
        self.check(mode + ' primary button tap', self.event_count() == 1)
        self.disabled('lab_primary_disabled')
        self.disabled('lab_neutral_disabled')
        before = self.event_count()
        self.input([{'do': 'move', 'at': self.at('lab_primary_raised')}, {'do': 'wait', 'ms': 250},
                    {'do': 'click', 'at': self.at('lab_primary_raised'), 'hold_ms': 500},
                    {'do': 'wait', 'ms': 250}], mode + '-long-press')
        self.check(mode + ' long press fires once', self.event_count() == before + 1)
        if not touch:
            self.input([{'do': 'move', 'at': [0.95, 0.1]}, {'do': 'wait', 'ms': 150},
                        {'do': 'move', 'at': self.at('lab_primary_raised')},
                        {'do': 'wait', 'ms': 350}], 'mouse-hover')
            data = self.native_probe('hover-probe', ['lab_primary_raised'])
            self.check('native hover state visible', data['lab_primary_raised']['states']['hover']['visible'])
        self.capture(mode + '-buttons')

        self.page('selection')
        self.tap('lab_list_a')
        selected = self.dump(mode + '-selection')
        self.check(mode + ' list selection', find_key(selected, 'lab_list_a')['props']['selected'])
        self.disabled('lab_list_disabled')
        if not touch:
            for key in ('lab_list_a', 'lab_list_b'):
                self.input([{'do': 'move', 'at': self.at(key)}, {'do': 'wait', 'ms': 250}], 'hover-' + key)
                self.capture('selection-hover-' + key)
            first = self.edge_score(selected, 'lab_list_a', 'selection-hover-lab_list_a.jpg')
            other = self.edge_score(selected, 'lab_list_a', 'selection-hover-lab_list_b.jpg')
            self.check('selected outline persists across hover targets', first > 20 and other > 20)
        self.capture(mode + '-selection')

        self.page('toggles')
        if not touch:
            self.hover('lab_controlled_checkbox')
            self.hover('lab_switch')
        self.tap('lab_controlled_checkbox')
        self.check(mode + ' checkbox', '受控：开' in labels(self.dump('checked')))
        self.tap('lab_switch')
        self.check(mode + ' switch', '多人游戏：关' in labels(self.dump('switched')))
        self.disabled('lab_switch_disabled')
        self.scroll('toggles', 100)
        self.tap('ore_radio_creative')
        self.check(mode + ' radio selection', '游戏模式：创造' in labels(self.dump('radio')))
        self.disabled('ore_radio_adventure')
        self.capture(mode + '-toggles')

        self.page('sliders')
        if not touch:
            self.hover('lab_slider', 'slider_bar_hover')
        value = self.drag_slider('lab_slider')
        self.check(mode + ' continuous slider drag', 0.7 < value < 0.9)
        self.tap('lab_lock_slider')
        locked_value = self.drag_slider('lab_slider', 0.2)
        self.check(mode + ' locked slider rejects drag', abs(value - locked_value) < 0.001)
        step = self.drag_slider('lab_step_slider')
        self.check(mode + ' discrete slider snaps', step == 3)
        self.scroll('sliders', 100)
        disabled_value = self.drag_slider('lab_slider_disabled', 0.2)
        self.check(mode + ' disabled slider value', abs(disabled_value - 0.65) < 0.001)
        self.capture(mode + '-sliders')

        self.page('fields')
        if not touch:
            self.hover('lab_name')
        self.tap('lab_name_clear')
        self.tap('lab_name')
        self.input([{'do': 'text', 'value': 'Atlas123'}, {'do': 'key', 'keys': 'enter'},
                    {'do': 'wait', 'ms': 350}], mode + '-text')
        data = self.native_probe('text-probe', ['lab_name'])
        self.check(mode + ' native text input', data['lab_name']['text'] == 'Atlas123')
        self.tap('lab_name_submit')
        self.capture(mode + '-fields')
        self.tap('lab_field_disabled')
        self.input([{'do': 'text', 'value': 'CannotEdit'}, {'do': 'key', 'keys': 'enter'},
                    {'do': 'wait', 'ms': 200}], mode + '-disabled-field')
        self.check(mode + ' disabled field stays unchanged',
                   self.native_probe('disabled-field', ['lab_field_disabled'])['lab_field_disabled']['text'] == 'Locked')

        self.page('dropdowns')
        if not touch:
            self.hover('lab_dropdown')
        self.tap('lab_dropdown')
        menu = self.dump('dropdown-open')
        target = find_key(menu, 'ore_option_1')
        frame = target['layout']
        self.tap_at([(frame['x'] + frame['width'] / 2) / self.screen[0],
                     (frame['y'] + frame['height'] / 2) / self.screen[1]], 'dropdown-option')
        self.check(mode + ' native dropdown selection',
                   '当前类型：创造' in labels(self.dump('dropdown-selected')))
        self.disabled('lab_dropdown_disabled')
        self.tap('lab_dropdown')
        self.tap_at([0.96, 0.8], 'menu-background')
        self.check(mode + ' dropdown outside closes',
                   not any(node['type'] == 'Modal' and node['props'].get('visible')
                           for node in nodes(find_key(self.dump('dropdown-closed'), 'lab_dropdown'))))
        self.capture(mode + '-dropdowns')

        self.page('navigation')
        self.scroll('navigation', 100)
        self.tap('lab_page_last')
        self.check(mode + ' paging boundary', '世界 13–15' in labels(self.dump('last-page')))

        self.page('containers')
        self.tap('lab_accordion')
        self.check(mode + ' accordion collapse', '坐标会显示在游戏画面中。' not in labels(self.dump('collapsed')))
        self.scroll('containers', 100)
        at = self.at('lab_nested_scroll')
        before = self.native_probe('scroll-before', ['lab_nested_scroll'])['lab_nested_scroll']['scroll']
        if touch:
            steps = [{'do': 'drag', 'from': [at[0], at[1] + 0.08], 'to': [at[0], at[1] - 0.08], 'segments': 12}]
        else:
            steps = [{'do': 'scroll', 'at': at, 'amount': -10}]
        self.input([{'do': 'move', 'at': at}, {'do': 'wait', 'ms': 250}]
                   + steps + [{'do': 'wait', 'ms': 350}], mode + '-nested-scroll')
        after = self.native_probe('scroll-after', ['lab_nested_scroll'])['lab_nested_scroll']['scroll']
        self.check(mode + ' nested native scrolling', after != before)
        self.capture(mode + '-containers')

        self.page('dialogs')
        self.tap('lab_open_dialog')
        self.check(mode + ' dialog opens', find_key(self.dump('dialog-open'), 'lab_dialog')['props']['visible'])
        panel = self.native_probe('dialog-panel', ['ore_dialog_surface'])['ore_dialog_surface']
        self.tap_at([(panel['position'][0] + 5) / self.screen[0],
                     (panel['position'][1] + 5) / self.screen[1]], 'dialog-inside')
        self.check(mode + ' dialog surface does not dismiss', find_key(self.dump('dialog-kept'), 'lab_dialog')['props']['visible'])
        self.tap_at([0.97, 0.75], 'dialog-outside')
        self.check(mode + ' dialog backdrop closes', not find_key(self.dump('dialog-closed'), 'lab_dialog')['props']['visible'])
        self.tap('lab_open_menu')
        self.tap('lab_modal_edit')
        self.check(mode + ' menu action reads naturally',
                   any('已选择编辑' in (text or '') for text in labels(self.dump('menu-action'))))
        self.tap('ore_dialog_close')
        self.tap('lab_open_warning')
        self.tap('ore_dialog_confirm')
        warning = self.dump('warning-confirmed')
        self.check(mode + ' destructive confirmation is labeled',
                   any('已确认删除' in (text or '') for text in labels(warning)))
        self.check(mode + ' destructive confirmation closes',
                   not find_key(warning, 'lab_dialog')['props']['visible'])
        self.tap('lab_drawer_right')
        self.capture(mode + '-drawer')
        self.tap_at([0.1, 0.7], 'drawer-outside')
        self.check(mode + ' drawer outside closes', not find_key(self.dump('drawer-closed'), 'lab_drawer')['props']['visible'])

        self.page('cards')
        before = self.event_count()
        self.tap('lab_card_more')
        self.check(mode + ' card additional action', self.event_count() == before + 1)
        self.tap('lab_card_enter')
        self.check(mode + ' card primary action', self.event_count() == before + 2)
        self.capture(mode + '-cards')

        self.page('messages')
        self.tap('lab_banner_info')
        self.check(mode + ' dismiss banner', not any(node.get('key') == 'lab_banner_info'
                   for node in nodes(self.dump('banner-dismissed'))))
        self.tap('lab_restore_banners')
        self.check(mode + ' restore banners', bool(find_key(self.dump('banners-restored'), 'lab_banner_info')))
        self.scroll('messages', 40)
        self.tap('lab_help')
        self.check(mode + ' tap-accessible help', '只有受邀好友可以加入这个世界。' in labels(self.dump('help')))
        self.capture(mode + '-messages')

        self.page('feedback')
        self.tap('lab_progress_up')
        self.check(mode + ' progress changes', '进度：55%' in labels(self.dump('progress')))
        self.scroll('feedback', 100)
        self.tap('lab_progress_animation')
        animations = [node for node in nodes(self.dump('animation-paused')) if node['type'] == 'OreImage'
                      and node['props'].get('name') == 'animation']
        self.check(mode + ' animation pause', animations and all(not node['props']['animate'] for node in animations))
        self.page('media')
        self.tap('lab_asset_search')
        self.input([{'do': 'text', 'value': 'pressable'}, {'do': 'key', 'keys': 'enter'},
                    {'do': 'wait', 'ms': 250}], mode + '-asset-search')
        assets = [node['props']['name'] for node in nodes(self.dump('asset-matches'))
                  if node['type'] == 'OreImage' and node['props'].get('name', '').startswith('pressable')]
        self.check(mode + ' asset catalogue search', len(assets) > 0)
        self.capture(mode + '-assets')

    def verify(self):
        self.mount()
        tree = self.dump('initial')
        frame = next(node['layout'] for node in nodes(tree) if node.get('layout'))
        self.screen = [frame['width'], frame['height']]
        for page in PAGES:
            mounted = self.page(page)
            self.check('page mounts: ' + page, bool(labels(mounted)))
        self.mount()
        original = self.state()['simulated']
        try:
            self.set_touch(False)
            self.verify_controls(False)
            self.set_touch(True)
            self.verify_controls(True)
            self.tap('lab_reset')
            self.check('native touch input mode readback', self.state()['touch'])
        finally:
            self.set_touch(original)
        return {'ok': True, 'count': len(self.checks), 'checks': self.checks,
                'hardware_touch_tested': False, 'touch_test': 'F11 native single-touch simulation'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=ROOT / '.runtime/acceptance-atlas')
    args = parser.parse_args()
    verifier = AtlasVerification(args.session, args.owner, args.output)
    try:
        result = verifier.verify()
    except Exception as error:
        result = {'ok': False, 'checks': verifier.checks, 'error': str(error)}
    (verifier.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
