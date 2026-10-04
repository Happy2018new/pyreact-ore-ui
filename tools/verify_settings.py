"""Native regression for the public-component Ore settings playground."""
import argparse
import json
import time
from pathlib import Path

from live_support import find_key, nodes
from verify_atlas import AtlasVerification
from verify_visual_repair import PROBE
from capture_settings_pixels import operate as native_pixels

PAGES = ('overview', 'selection', 'toggles', 'buttons', 'fields', 'dropdowns',
         'sliders', 'navigation', 'containers', 'messages', 'dialogs', 'media', 'social')


class SettingsVerification(AtlasVerification):
    def __init__(self, session, owner, output):
        super().__init__(session, owner, output)
        self.session, self.owner = session, owner

    def hover(self, key, native_child='hover'):
        self.code('from ore_demo import dev_probe\n_result=dev_probe.reveal(%r,%r)\n'
                  % ('lab_scroll_' + self.current_page + '_0', key), 'reveal-hover-' + key)
        time.sleep(.3)
        probe = self.native_probe('hover-' + key, [key])[key]
        evidence = native_pixels(self.session, self.owner, points=[(.95, .08), self.at(key)])
        (self.output / ('hover-pointer-' + key + '.json')).write_text(json.dumps(evidence), encoding='utf8')
        visible = self.code('from ore_demo.pyreact import host\n'
            '_result=host._ACTIVE_HOST[0].GetBaseUIControl(%r).GetVisible()\n'
            % (probe['path'] + '/' + native_child), 'hover-visible-' + key)
        self.check('native Ore hover visible: ' + key, visible)
        native_pixels(self.session, self.owner, output=self.output / ('hover-' + key + '.png'))

    def tap_at(self, at, name):
        # A game-window capture can leave the engine cursor at a different
        # location than the desktop cursor. Move away before the target so
        # even a repeated tap receives a fresh pointer-motion event.
        away = [.95,.08] if at != [.95,.08] else [.04,.8]
        evidence = native_pixels(self.session, self.owner, points=[away,at], click=True)
        (self.output / (name + '-absolute.json')).write_text(json.dumps(evidence), encoding='utf8')

    def input(self, steps, name='input'):
        deadline = time.monotonic() + 120
        while True:
            try:
                return super().input(steps, name)
            except RuntimeError as error:
                if '锁屏' in str(error) or 'LockApp' in str(error):
                    raise RuntimeError('Windows is locked; no input sent. Unlock before resuming native tests.')
                if 'Resource busy:' not in str(error) or time.monotonic() >= deadline:
                    raise
                print('WAIT desktop lock: no input sent', flush=True)
                time.sleep(1)

    def mount(self):
        super().mount()
        self.current_page = 'overview'
        frame = next(node['layout'] for node in nodes(self.dump('mounted')) if node.get('layout'))
        self.screen = [frame['width'], frame['height']]

    def business(self):
        return self.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
                         'from ore_demo.settings_playground import OrePlayground\n'
                         'fiber=next(f for f in dev_probe._walk(host._ACTIVE_HOST[0]._root_fiber) if f.comp_type is OrePlayground)\n'
                         '_result=dict(page=fiber.hooks[0]["value"],values=fiber.hooks[1]["value"],'
                         'overlay=fiber.hooks[2]["value"],events=fiber.hooks[3]["value"])\n', 'business')

    def event_count(self):
        return self.business()['events']

    def set_touch(self, enabled):
        if self.state()['simulated'] == enabled:
            return
        self.code('from ore_demo.pyreact import navigator\nnavigator.clear()\n_result=navigator.depth\n', 'close-for-f11')
        depth = self.code('from ore_demo.pyreact import navigator\n_result=navigator.depth\n', 'closed')
        self.check('UI closed before F11', depth == 0)
        self.input([{'do': 'key', 'keys': 'f11'}, {'do': 'wait', 'ms': 350}], 'f11')
        self.check('F11 switches simulated touch to ' + str(enabled), self.state()['simulated'] == enabled)
        self.input([{'do': 'key', 'keys': 'f8'}, {'do': 'wait', 'ms': 500}], 'f8')
        self.check('F8 opens playground', any(n['type'] == 'OreSettingsScreen' for n in nodes(self.dump('reopened'))))
        self.mount()

    def drag_slider(self, key, target=0.8):
        self.code('from ore_demo import dev_probe\n_result=dev_probe.reveal(%r,%r)\n'
                  % ('lab_scroll_' + self.current_page + '_0', key), 'reveal-drag-' + key)
        time.sleep(.25)
        probe = self.native_probe('slider-before', [key])[key]
        x, y = probe['position']
        width, height = probe['size']
        fraction = probe['value'] / 4 if key in ('lab_step_slider', 'lab_step_disabled') else probe['value']
        start = [(x + width * fraction) / self.screen[0], (y + height / 2) / self.screen[1]]
        end = [(x + width * target) / self.screen[0], start[1]]
        native_pixels(self.session, self.owner, points=[start])
        evidence = native_pixels(self.session, self.owner, steps=[{'do': 'move', 'at': start}, {'do': 'wait', 'ms': 250},
            {'do': 'drag', 'from': start, 'to': end, 'segments': 20, 'hold_ms': 300},
            {'do': 'wait', 'ms': 400}])
        (self.output / ('drag-' + key + '-absolute.json')).write_text(json.dumps(evidence), encoding='utf8')
        return self.native_probe('slider-after', [key])[key]['value']

    def scoped_at(self, parent_key, child_key, within=None):
        probe = self.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
            'from ore_demo.pyreact.primitives import ButtonPrimitive\n'
            'runtime=host._ACTIVE_HOST[0]\n'
            'scope=next(f for f in dev_probe._walk(runtime._root_fiber) if f.key==%r) if %r else runtime._root_fiber\n'
            'parent=next(f for f in dev_probe._walk(scope) if f.key==%r)\n'
            'target=next(f for f in dev_probe._walk(parent) if f.key==%r)\n'
            'button=next(f for f in dev_probe._walk(target) if isinstance(f.comp_type,ButtonPrimitive))\n'
            'control=runtime.GetBaseUIControl(button.native_path)\n'
            '_result=dict(position=control.GetGlobalPosition(),size=control.GetSize())\n'
            % (within, within, parent_key, child_key), 'scoped-position')
        x, y = probe['position']
        width, height = probe['size']
        at = [(x + width / 2) / self.screen[0], (y + height / 2) / self.screen[1]]
        if not all(0 < coordinate < 1 for coordinate in at):
            raise AssertionError('Scoped target off screen: %s %s' % (child_key, at))
        return at

    def visual(self):
        results = []
        for page in PAGES:
            self.page(page)
            self.check('page mounts ' + page, self.business()['page'] == page)
            probe = self.code(PROBE, 'geometry-' + page)
            self.check('text and image geometry ' + page, not probe['text_errors'] and not probe['image_errors'])
            self.capture(page)
            results.append(dict(page=page, **probe))
        (self.output / 'geometry.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')

    def verify_mode(self, touch):
        mode = 'touch' if touch else 'mouse'
        self.set_touch(touch)
        self.mount()
        self.tap('lab_switch')
        self.check(mode + ' switch updates controlled state', not self.business()['values']['multiplayer'])
        if not touch:
            self.hover('lab_switch')
            self.hover('lab_page_overview')
            self.hover('lab_page_selection')
        self.capture(mode + '-overview')

        self.page('selection')
        self.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('lab_scroll_selection_0','lab_distance')\n", 'reveal-distance')
        time.sleep(.25)
        self.tap_at(self.scoped_at('lab_distance', 'ore_segment_4'), 'distance-fifth')
        self.check(mode + ' segmented fifth option', self.business()['values']['distance'] == 4)
        self.capture(mode + '-selection')

        self.page('toggles')
        self.tap('lab_switch_off')
        self.check(mode + ' off switch turns on', self.business()['values']['respawn'])
        if not touch:
            self.hover('lab_switch_off')
        self.disabled('lab_switch_disabled')
        self.tap('lab_checkbox')
        self.check(mode + ' checkbox selects', self.business()['values']['checkbox'])
        self.disabled('lab_checkbox_disabled_off')
        self.disabled('lab_checkbox_disabled_on')
        self.tap('lab_switch_uncontrolled')
        self.check(mode + ' uncontrolled switch updates native skin',
            'switch_on_' in self.native_probe('uncontrolled-switch', ['lab_switch_uncontrolled'])[
                'lab_switch_uncontrolled']['states']['default']['applied'][2])
        self.tap('ore_radio_creative')
        self.check(mode + ' radio selects', self.business()['values']['radio'] == 'creative')
        self.disabled('ore_radio_adventure')
        self.capture(mode + '-toggles')

        self.page('buttons')
        before = self.event_count()
        self.tap('lab_primary_raised')
        self.check(mode + ' button fires once', self.event_count() == before + 1)
        self.disabled('lab_primary_disabled')
        for variant in ('secondary', 'neutral', 'destructive', 'realms'):
            before = self.event_count()
            self.tap('lab_' + variant + '_raised')
            self.check(mode + ' button fires once ' + variant, self.event_count() == before + 1)
            self.disabled('lab_' + variant + '_disabled')
        for variant in ('primary', 'secondary', 'neutral', 'destructive', 'realms'):
            before = self.event_count()
            self.tap('lab_' + variant + '_flat')
            self.check(mode + ' flat button fires once ' + variant, self.event_count() == before + 1)
        self.disabled('lab_icon_disabled')
        if not touch:
            self.hover('lab_primary_raised')

        self.verify_sliders(mode, touch)
        self.verify_remaining(mode, touch)

    def verify_radio(self):
        for touch in (False, True):
            mode = 'touch' if touch else 'mouse'
            self.set_touch(touch)
            self.mount()
            self.page('toggles')
            for option in ('creative', 'survival'):
                key = 'ore_radio_' + option
                if not touch:
                    self.hover(key)
                self.tap(key)
                self.check(mode + ' full radio row selects ' + option,
                    self.business()['values']['radio'] == option)
                geometry = self.native_probe(mode + '-radio-' + option, [key])[key]
                states = self.code('from ore_demo.pyreact import host\n'
                    'root=host._ACTIVE_HOST[0]\n'
                    '_result={name:root.GetBaseUIControl(%r+"/"+name).GetSize() '
                    'for name in ("default","hover","pressed")}\n' % geometry['path'], 'radio-state-size')
                self.check(mode + ' diamond image remains 16 square ' + option,
                    all(list(size) == [16, 16] for size in states.values()))
            radio = find_key(self.dump(mode + '-radio-bounds'), 'lab_radio')
            bounds = dict(parent=next(node['layout'] for node in nodes(radio) if node.get('layout')),
                children=[find_key(radio, 'ore_radio_' + option)['layout']
                          for option in ('survival', 'creative', 'adventure')])
            self.check(mode + ' complete radio group fits measured parent',
                all(frame['y'] >= bounds['parent']['y'] and frame['y'] + frame['height'] <=
                    bounds['parent']['y'] + bounds['parent']['height'] + .1 for frame in bounds['children']))
            self.disabled('ore_radio_adventure')
            self.capture(mode + '-diamond-radio')

    def verify_social(self):
        for touch in (False, True):
            mode = 'touch' if touch else 'mouse'
            self.set_touch(touch)
            self.mount()
            self.page('social')
            self.tap('lab_open_friends')
            self.tap('ore_friends_search')
            self.input([{'do':'text','value':'Steve'},{'do':'key','keys':'enter'},
                        {'do':'wait','ms':250}], mode + '-friend-query')
            self.check(mode + ' friends search updates controlled query',
                self.business()['values']['friendQuery'] == 'Steve')
            self.check(mode + ' search click keeps drawer open', self.business()['overlay'] == 'drawer')
            self.check(mode + ' search filters player list',
                not any(node.get('key') == 'lab_player_1' for node in nodes(self.dump(mode + '-filtered-friends'))))
            guards = self.code('from ore_demo.pyreact import host\n'
                'runtime=host._ACTIVE_HOST[0]\n'
                '_result=[runtime.GetBaseUIControl(path).GetSize() for path in runtime._button_handlers '
                'if "/ore_guard_" in path]\n', mode + '-guard-sizes')
            self.check(mode + ' visible modal guards have nonzero hit rectangles',
                bool(guards) and all(width > 0 and height > 0 for width, height in guards))
            bounds = self.native_probe('drawer-surface', ['ore_friends_surface'])['ore_friends_surface']
            x, y = bounds['position']
            width, height = bounds['size']
            before = self.event_count()
            self.tap_at([(x + width - 2) / self.screen[0], (y + height - 2) / self.screen[1]],
                mode + '-drawer-blank-surface')
            self.check(mode + ' blank drawer surface blocks background', self.business()['overlay'] == 'drawer'
                and self.event_count() == before)
            self.tap_at(self.scoped_at('lab_player_0', 'ore_player_options', within='ore_friends_surface'),
                mode + '-friend-options')
            self.tap('ore_action_close')
            self.check(mode + ' menu close returns above drawer', self.business()['overlay'] == 'drawer')
            self.tap_at(self.scoped_at('lab_player_0', 'ore_player_options', within='ore_friends_surface'),
                mode + '-friend-options-again')
            before = self.event_count()
            self.tap('ore_action_4')
            self.check(mode + ' last menu action fires once', self.event_count() == before + 1 and
                self.business()['overlay'] == 'drawer')
            self.tap('ore_friends_close')
            self.check(mode + ' drawer close returns to settings', self.business()['overlay'] is None)
            self.tap('lab_open_friends')
            self.tap_at([.04,.8], mode + '-friends-backdrop')
            self.check(mode + ' backdrop closes without clicking underlying navigation',
                self.business()['overlay'] is None and self.business()['page'] == 'social')
            self.page('dialogs')
            self.tap('lab_open_dialog')
            self.tap('lab_dialog_name')
            self.input([{'do':'key','keys':'ctrl+a'}, {'do':'text','value':'Workshop'},
                        {'do':'key','keys':'enter'}, {'do':'wait','ms':250}], mode + '-dialog-input')
            self.check(mode + ' dialog field receives real text', self.business()['values']['name'] == 'Workshop')
            self.check(mode + ' dialog input keeps surface open', self.business()['overlay'] == 'form')
            self.tap('ore_dialog_confirm')
            self.check(mode + ' edited dialog confirms', self.business()['overlay'] is None)
            guards = self.code('from ore_demo.pyreact import host\n'
                '_result=[path for path in host._ACTIVE_HOST[0]._button_handlers if "/ore_guard_" in path]\n',
                mode + '-guard-cleanup')
            self.check(mode + ' closed overlays unregister input guards', not guards)

    def verify_overlays(self):
        for touch in (False, True):
            mode = 'touch' if touch else 'mouse'
            self.set_touch(touch)
            self.mount()
            self.page('dropdowns')
            self.capture(mode + '-before-dropdown-tap')
            self.tap('lab_dropdown')
            short_list = self.code('from ore_demo import dev_probe\nfrom ore_demo.pyreact import host\n'
                'from ore_demo.pyreact.primitives import ScrollViewPrimitive\n'
                'runtime=host._ACTIVE_HOST[0]\n'
                'surface=next(f for f in dev_probe._walk(runtime._root_fiber) if f.key=="ore_dropdown_surface")\n'
                'scroll=next(f for f in dev_probe._walk(surface) if isinstance(f.comp_type,ScrollViewPrimitive))\n'
                'content_path=scroll.comp_type._content_path(scroll.native_path,runtime)\n'
                'viewport=runtime.GetBaseUIControl(content_path.rsplit("/",1)[0])\n'
                'content=runtime.GetBaseUIControl(content_path)\n'
                '_result=dict(viewport=viewport.GetSize(),content=content.GetSize())\n', mode + '-short-list-range')
            self.check(mode + ' short dropdown fits all rows without scrolling',
                short_list['content'][1] <= short_list['viewport'][1] + .1)
            self.tap('ore_option_2')
            self.check(mode + ' nested dropdown selects and closes', self.business()['values']['drop'] == 'fancy'
                and not any(node.get('key') == 'ore_option_2' for node in nodes(self.dump(mode + '-nested-dropdown'))))
            self.tap('lab_long_dropdown')
            self.tap('ore_dropdown_close')
            self.check(mode + ' long dropdown close is reachable',
                not any(node.get('key') == 'ore_dropdown_close' for node in nodes(self.dump(mode + '-long-closed'))))
            self.tap('lab_dropdown')
            self.tap_at([.04,.8], mode + '-dropdown-backdrop')
            self.check(mode + ' dropdown backdrop blocks underlying navigation', self.business()['page'] == 'dropdowns'
                and not any(node.get('key') == 'ore_option_2' for node in nodes(self.dump(mode + '-backdrop-closed'))))

    def verify_sliders(self, mode, touch):
        self.page('sliders')
        value = self.drag_slider('lab_slider', 0.8)
        self.check(mode + ' continuous drag', 0.7 < value < 0.9)
        self.check(mode + ' native and controlled continuous values match', abs(value - self.business()['values']['volume']) < .001)
        for target, expected in ((0, 0), (.25, 1), (.5, 2), (.75, 3), (1, 4)):
            actual = self.drag_slider('lab_step_slider', target)
            self.check(mode + ' native integer stop ' + str(expected), actual == expected and self.business()['values']['step'] == expected)
            probe = self.native_probe('step-geometry', ['lab_step_slider'])['lab_step_slider']
            thumb = self.code('from ore_demo.pyreact import host\n'
                'control=host._ACTIVE_HOST[0].GetBaseUIControl(%r)\n'
                '_result=dict(position=control.GetGlobalPosition(),size=control.GetSize())\n'
                % (probe['path'] + '/slider_box'), 'step-thumb')
            desired_center = probe['position'][0] + probe['size'][0] * expected / 4
            self.check(mode + ' integer thumb aligns at stop ' + str(expected),
                abs(thumb['position'][0] + thumb['size'][0] / 2 - desired_center) < .26)
            self.check(mode + ' integer thumb fits track at stop ' + str(expected),
                thumb['position'][0] >= probe['position'][0] - 8.1 and
                thumb['position'][0] + thumb['size'][0] <= probe['position'][0] + probe['size'][0] + 8.1)
            self.capture(mode + '-step-' + str(expected))
        if not touch:
            self.hover('lab_step_slider', 'slider_bar_hover')
        self.tap('lab_lock_slider')
        self.check(mode + ' locked slider rejects drag', abs(self.drag_slider('lab_slider', .2) - value) < .001)
        self.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('lab_scroll_sliders_0','lab_slider_disabled')\n", 'reveal-disabled')
        self.check(mode + ' disabled continuous value', abs(self.drag_slider('lab_slider_disabled', .2) - .65) < .001)
        self.check(mode + ' disabled integer value', self.drag_slider('lab_step_disabled', .9) == 2)
        self.check(mode + ' uncontrolled continuous drag', .7 < self.drag_slider('lab_uncontrolled_slider', .8) < .9)
        self.capture(mode + '-disabled-sliders')

    def verify_remaining(self, mode, touch):

        self.page('fields')
        self.tap('lab_field_empty')
        self.input([{'do': 'text', 'value': 'Ore123'}, {'do': 'key', 'keys': 'enter'}, {'do': 'wait', 'ms': 250}], mode + '-field-input')
        self.check(mode + ' editable field native text', self.native_probe('field-value', ['lab_field_empty'])['lab_field_empty']['text'] == 'Ore123')
        self.tap('lab_field_disabled')
        self.check(mode + ' disabled field retains text', self.native_probe('disabled-field', ['lab_field_disabled'])['lab_field_disabled']['text'] == '我的世界')
        self.capture(mode + '-fields')

        self.page('dropdowns')
        self.tap('lab_dropdown')
        self.check(mode + ' dropdown opens', bool(find_key(self.dump('open-menu'), 'ore_option_2')))
        if not touch:
            self.hover('ore_option_2')
            self.hover('ore_dropdown_close')
        self.tap('ore_option_2')
        self.check(mode + ' dropdown selects and closes', self.business()['values']['drop'] == 'fancy' and
                   not any(n.get('key') == 'ore_option_2' for n in nodes(self.dump('selected-menu'))))
        self.disabled('lab_dropdown_disabled')
        self.tap('lab_long_dropdown')
        self.capture(mode + '-long-dropdown')
        self.tap('ore_dropdown_close')

        self.page('navigation')
        self.tap('lab_list_b')
        self.check(mode + ' list selection', self.business()['values']['selected'] == 'b')
        if not touch:
            self.hover('lab_list_b')
            self.hover('lab_list_a')
        self.disabled('lab_list_disabled')
        self.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('lab_scroll_navigation_0','lab_tabs')\n", 'reveal-tabs')
        time.sleep(.25)
        self.tap_at(self.scoped_at('lab_tabs', '2'), 'servers-tab')
        self.check(mode + ' icon tab selects servers', self.business()['values']['tab'] == 'servers')
        self.tap('ore_page_previous')
        self.check(mode + ' pagination rejects previous at first page', self.business()['values']['page'] == 1)
        self.tap('ore_page_next')
        self.check(mode + ' pagination advances', self.business()['values']['page'] == 2)
        self.capture(mode + '-navigation')
        before = self.event_count()
        self.tap('ore_world_open')
        self.check(mode + ' world card opens once', self.event_count() == before + 1)
        self.tap('ore_world_edit')
        self.check(mode + ' world card edit opens dialog', self.business()['overlay'] == 'form')
        self.tap('ore_dialog_close')

        self.page('containers')
        self.tap('lab_accordion')
        self.check(mode + ' accordion collapse', not self.business()['values']['expanded'])
        self.tap('lab_accordion')
        self.check(mode + ' accordion expands', self.business()['values']['expanded'])
        self.tap_at(self.scoped_at('lab_pack_0', 'ore_pack_details'), 'pack-details')
        self.check(mode + ' pack details collapse', self.business()['values']['packOpen'] is None)
        self.tap_at(self.scoped_at('lab_pack_0', 'ore_pack_details'), 'pack-details-open')
        self.check(mode + ' pack details expand', self.business()['values']['packOpen'] == 0)
        self.tap_at(self.scoped_at('lab_pack_0', 'ore_pack_action'), 'activate-pack')
        self.check(mode + ' pack activates independently', self.business()['values']['activePacks'] == [0])
        self.tap_at(self.scoped_at('lab_pack_tabs', '0'), 'active-packs-tab')
        self.check(mode + ' active pack tab', self.business()['values']['packTab'] == 'active')
        self.tap_at(self.scoped_at('lab_pack_0', 'ore_pack_action'), 'deactivate-pack')
        self.check(mode + ' pack deactivates independently', self.business()['values']['activePacks'] == [])
        self.capture(mode + '-containers')

        self.page('messages')
        self.tap('lab_help')
        self.check(mode + ' help expands', any(n['props'].get('content') ==
            '在同一账号下登录后，可以继续查看已保存的世界。' for n in nodes(self.dump('help-open'))))
        self.tap('lab_help')
        self.tap('lab_message_accordion')
        self.check(mode + ' message accordion collapses', not self.business()['values']['messageExpanded'])
        self.tap('lab_message_accordion')
        self.check(mode + ' message accordion expands', self.business()['values']['messageExpanded'])
        self.tap('ore_banner_close')
        self.check(mode + ' banner dismisses', not self.business()['values']['notice'])

        self.page('dialogs')
        for key, overlay in (('lab_open_dialog', 'form'), ('lab_open_progress', 'progress'), ('lab_open_warning', 'warning')):
            self.tap(key)
            self.check(mode + ' opens ' + overlay, self.business()['overlay'] == overlay)
            self.capture(mode + '-dialog-' + overlay)
            self.tap('ore_dialog_confirm')
            self.check(mode + ' confirm closes ' + overlay, self.business()['overlay'] is None)
        self.tap('lab_drawer_right')
        self.capture(mode + '-drawer')
        self.tap_at([.04, .8], 'drawer-backdrop')
        self.check(mode + ' drawer backdrop closes', self.business()['overlay'] is None)

        self.page('social')
        self.tap('lab_open_friends')
        self.check(mode + ' friends panel opens', self.business()['overlay'] == 'drawer')
        self.tap_at(self.scoped_at('lab_player_0', 'ore_player_options', within='ore_friends_surface'), 'player-options')
        self.check(mode + ' player options open', self.business()['overlay'] == 'friend_options')
        before = self.event_count()
        self.tap('ore_action_0')
        self.check(mode + ' player action fires once and returns',
            self.event_count() == before + 1 and self.business()['overlay'] == 'drawer')
        self.tap('ore_friends_close')
        self.check(mode + ' friends panel closes', self.business()['overlay'] is None)

        self.page('media')
        self.tap('lab_asset_search')
        self.input([{'do': 'text', 'value': 'animation'}, {'do': 'key', 'keys': 'enter'}, {'do': 'wait', 'ms': 250}], mode + '-search')
        self.check(mode + ' asset search state', self.business()['values']['query'] == 'animation')
        self.tap('lab_asset_animation')
        self.check(mode + ' animations pause', not self.business()['values']['animated'])
        self.capture(mode + '-media')

    def verify_calibrated(self):
        for touch in (False, True):
            mode = 'touch' if touch else 'mouse'
            self.set_touch(touch)
            self.mount()
            self.page('toggles')
            for index, permission in enumerate(('visitor', 'member', 'operator')):
                self.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('lab_scroll_toggles_0','lab_permission')\n",
                          'reveal-permission')
                time.sleep(.25)
                self.tap_at(self.scoped_at('lab_permission', 'ore_segment_' + str(index)), 'permission-' + permission)
                self.check(mode + ' permission selects ' + permission,
                           self.business()['values']['permission'] == permission)
                self.capture(mode + '-permission-' + permission)
            self.page('selection')
            self.code("from ore_demo import dev_probe\n_result=dev_probe.reveal('lab_scroll_selection_0','lab_distance')\n",
                      'reveal-distance')
            time.sleep(.25)
            self.tap_at(self.scoped_at('lab_distance', 'ore_segment_4'), 'calibrated-distance')
            self.check(mode + ' joined fifth segment remains reachable', self.business()['values']['distance'] == 4)
            self.page('fields')
            self.tap('lab_field_empty')
            self.input([{'do': 'text', 'value': 'Ore123'}, {'do': 'key', 'keys': 'enter'},
                        {'do': 'wait', 'ms': 250}], mode + '-calibrated-field')
            self.check(mode + ' calibrated field accepts text',
                       self.native_probe('calibrated-field', ['lab_field_empty'])['lab_field_empty']['text'] == 'Ore123')
            geometry = self.code(PROBE, mode + '-calibrated-geometry')
            self.check(mode + ' calibrated glyph and image geometry',
                       not geometry['text_errors'] and not geometry['image_errors'])
            self.capture(mode + '-calibrated-field')

    def verify(self, phase):
        self.mount()
        original = self.state()['simulated']
        try:
            if phase in ('all', 'visual'):
                self.visual()
            if phase in ('all', 'mouse'):
                self.verify_mode(False)
            if phase in ('all', 'touch'):
                self.verify_mode(True)
            if phase == 'sliders':
                self.verify_sliders('mouse', False)
            if phase == 'remaining':
                self.set_touch(False)
                self.verify_remaining('mouse', False)
            if phase == 'radio':
                self.verify_radio()
            if phase in ('all', 'social'):
                self.verify_social()
            if phase in ('all', 'overlays'):
                self.verify_overlays()
            if phase in ('all', 'calibrated'):
                self.verify_calibrated()
        finally:
            self.set_touch(original)
        self.mount()
        self.capture('preview')
        return dict(ok=True, checks=self.checks, count=len(self.checks), hardware_touch_tested=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--output', type=Path, default=Path('.runtime/settings-verification'))
    parser.add_argument('--phase', choices=('all', 'visual', 'mouse', 'touch', 'sliders', 'remaining', 'calibrated', 'radio', 'social', 'overlays'), default='all')
    args = parser.parse_args()
    verifier = SettingsVerification(args.session, args.owner, args.output)
    try:
        result = verifier.verify(args.phase)
    except Exception as error:
        result = dict(ok=False, checks=verifier.checks, error=str(error))
    (verifier.output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
