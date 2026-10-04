# -*- coding: utf-8 -*-
"""Exercise the real supplied Pyreact Element, hook, and Button machinery.

ModSDK controls alone are faked. Build the disposable demo first; no fake
Component decorator or fake hooks are substituted for the host framework.
"""
import os
import sys
import types
import unittest
for name in ('mod', 'mod.client', 'mod.client.extraClientApi'):
    sys.modules[name] = types.ModuleType(name)
sdk = sys.modules['mod.client.extraClientApi']
sys.modules['mod'].client = sys.modules['mod.client']
sys.modules['mod.client'].extraClientApi = sdk
sdk.GetScreenNodeCls = lambda: object
sdk.GetViewBinderCls = lambda: object
sdk.GetViewViewRequestCls = lambda: object
sys.path.insert(0, os.environ['ORE_TEST_BEHAVIOR'].decode('mbcs'))

from ore_demo import oreui, pyreact
from ore_demo.oreui._button import NativeOreButton
from ore_demo.pyreact import hooks
from ore_demo.pyreact.reconciler import Fiber
from ore_demo.pyreact.layout import LayoutNode


class FakeControl:
    def __init__(self):
        self.adaptions = []
        self.alpha = None

    def asImage(self):
        return self

    def asButton(self):
        return self

    def asSlider(self):
        return self

    def GetSize(self):
        return (0.0, 0.0)

    def SetImageAdaptionType(self, *arguments):
        self.adaptions.append(arguments)
        return True

    def SetSprite(self, src):
        self.src = src

    def SetSpriteUV(self, uv):
        self.uv = uv

    def SetSpriteUVSize(self, size):
        self.uv_size = size

    def SetSize(self, size):
        self.size = size

    def SetPosition(self, position):
        self.position = position

    def SetSpriteColor(self, color):
        self.color = color

    def SetAlpha(self, alpha):
        self.alpha = alpha

    def SetTouchEnable(self, enabled):
        self.touch_enabled = enabled

    def GetSliderValue(self):
        return getattr(self, 'slider_value', 0.0)

    def SetSliderValue(self, value):
        self.slider_value = value

    def SetPropertyBag(self, bag):
        self.property_bag = bag

    def GetChildrenName(self):
        return []

    def AddTouchEventParams(self, parameters):
        self.parameters = parameters

    def SetButtonTouchUpCallback(self, callback):
        self.callback = callback


class FakeHost:
    def __init__(self):
        self.controls = {}
        self.scheduled = 0
        self.registered = None

    def GetBaseUIControl(self, path):
        return self.controls.setdefault(path, FakeControl())

    def pyreact_register_button(self, path, down, move, click):
        self.registered = click

    def pyreact_register_slider(self, path, callback):
        self.slider_callback = callback

    def pyreact_get_slider_value(self, path):
        return self.controls[path].GetSliderValue()

    def pyreact_set_slider_value(self, path, value):
        self.controls[path].SetSliderValue(value)

    def pyreact_set_slider_controlled_value(self, path, value):
        self.controls[path].SetSliderValue(value)

    def pyreact_unset_slider_controlled_value(self, path):
        pass

    def pyreact_unregister_slider(self, path):
        pass

    def _pyreact_dispatch_touch_up(self, *args):
        pass

    def schedule_render(self, fiber):
        self.scheduled += 1


def render(component, fiber=None, **props):
    element = component(**props)
    fiber = fiber or Fiber(element, FakeHost())
    fiber.hook_index = 0
    hooks.push_fiber(fiber)
    try:
        return component._render(**element.props), fiber
    finally:
        hooks.pop_fiber()


class ComponentTests(unittest.TestCase):
    def test_demo_pages_and_overlay_branches_render_in_python2(self):
        from ore_demo.settings_playground import OrePlayground, PAGES

        def descendants(element):
            yield element
            for child in element.children:
                for item in descendants(child):
                    yield item

        unused, fiber = render(OrePlayground)
        for label, page, icon in PAGES:
            fiber.hooks[0]['value'] = page
            element, unused = render(OrePlayground, fiber=fiber)
            self.assertTrue(element.children)
        for overlay in ('form', 'progress', 'warning', 'drawer', None):
            fiber.hooks[2]['value'] = overlay
            element, unused = render(OrePlayground, fiber=fiber)
            dialogs = [item for item in descendants(element) if item.comp_type is oreui.OreDialog]
            self.assertEqual(dialogs[0].props['visible'], overlay in ('form', 'progress', 'warning'))
            drawers = [item for item in descendants(element) if item.comp_type is oreui.OreDrawer]
            self.assertEqual(drawers[0].props['visible'], overlay == 'drawer')
            if overlay == 'warning':
                self.assertEqual(dialogs[0].props['confirmVariant'], oreui.OreVariant.destructive)
                dialogs[0].props['onConfirm']()
                self.assertIsNone(fiber.hooks[2]['value'])

    def test_every_button_variant_has_real_states(self):
        for variant in (oreui.OreVariant.primary, oreui.OreVariant.secondary,
                        oreui.OreVariant.neutral, oreui.OreVariant.destructive, oreui.OreVariant.realms):
            for elevated in (False, True):
                for state in (oreui.OreState.default, oreui.OreState.hovered,
                              oreui.OreState.pressed, oreui.OreState.focused, oreui.OreState.disabled):
                    self.assertTrue(oreui.asset(oreui.button_asset(variant, state, elevated)))

    def test_native_adapter_applies_and_updates_slice_data(self):
        button, _ = render(oreui.OreButton, variant=oreui.OreVariant.primary, elevated=True)
        host = FakeHost()
        fiber = Fiber(button, host)
        fiber.native_path = '/button'
        control = host.GetBaseUIControl('/button')
        NativeOreButton.apply_props(host, fiber, control, None, button.props)
        self.assertEqual(host.GetBaseUIControl('/button/default').adaptions[-1],
                         (pyreact.ImageAdaptionType.origin_nine_slice, (2, 2, 2, 4)))
        self.assertEqual(host.GetBaseUIControl('/button/pressed').adaptions[-1],
                         (pyreact.ImageAdaptionType.origin_nine_slice, (2, 2, 2, 2)))
        NativeOreButton.apply_props(host, fiber, control, button.props, button.props)
        self.assertEqual(len(host.GetBaseUIControl('/button/default').adaptions), 1)
        disabled, _ = render(oreui.OreButton, disabled=True)
        NativeOreButton.apply_props(host, fiber, control, button.props, disabled.props)
        self.assertEqual(host.GetBaseUIControl('/button/default').adaptions[-1],
                         (pyreact.ImageAdaptionType.origin_nine_slice, (1, 1, 1, 3)))
        self.assertIsNone(host.registered)

    def test_checkbox_controlled_and_uncontrolled_state(self):
        changes = []
        element, fiber = render(oreui.OreCheckbox, defaultValue=False, onChange=changes.append)
        element.props['onClick']()
        self.assertEqual(changes, [True])
        updated, _ = render(oreui.OreCheckbox, fiber=fiber, onChange=changes.append)
        self.assertEqual(updated.props['variant'], oreui.OreVariant.primary)
        controlled, controlled_fiber = render(oreui.OreCheckbox, value=False, onChange=changes.append)
        controlled.props['onClick']()
        unchanged, _ = render(oreui.OreCheckbox, fiber=controlled_fiber, value=False)
        self.assertEqual(unchanged.props['variant'], oreui.OreVariant.neutral)
        self.assertEqual(controlled_fiber.host.scheduled, 0)

    def test_tabs_bind_each_value(self):
        changes = []
        tabs, _ = render(oreui.OreTabs, options=[('A', 'a'), ('B', 'b')], value='a', onChange=changes.append)
        for button in tabs.children:
            button.props['onClick']()
        self.assertEqual(changes, ['a', 'b'])

    def test_segment_icons_and_disabled_choices_preserve_values(self):
        changes = []
        options = [('Guest', 'visitor', 'player_permissions'), ('Member', 'member', 'member')]
        segments, unused = render(oreui.OreSegmentedControl, options=options, value='member',
            disabledOptions=['visitor'], onChange=changes.append)
        self.assertIsNone(segments.children[0].props['onClick'])
        segments.children[1].props['onClick']()
        self.assertEqual(changes, ['member'])
        self.assertEqual(segments.children[1].children[0].comp_type, oreui.OreIcon)
        icon, unused = render(oreui.OreIcon, **segments.children[1].children[0].props)
        self.assertEqual(icon.props['src'], 'textures/pyreact_ore/skin/member_tintable')

    def test_field_placeholder_does_not_become_native_value(self):
        changes = []
        field, unused = render(oreui.OreField, placeholder='World name', onChange=changes.append)
        native_field = field.children[0]
        self.assertEqual(native_field.props['value'], '')
        self.assertEqual(native_field.children[0].props['content'], 'World name')
        native_field.props['onChange']('A')
        self.assertEqual(changes, ['A'])

    def test_card_can_size_from_children_and_animation_catalog_is_immutable(self):
        card, _ = render(oreui.OreCard, children=pyreact.Panel(style=pyreact.Style(height=40)))
        self.assertIsNone(card.style.get('height'))
        first = oreui.asset('animation')
        original = first['frames'][0]['uv']
        first['frames'][0]['uv'] = (999, 999)
        self.assertEqual(oreui.asset('animation')['frames'][0]['uv'], original)

    def test_disabled_button_and_list_do_not_bind_business_callback(self):
        for component in (oreui.OreButton, oreui.OreListItem):
            button, _ = render(component, disabled=True, onClick=lambda: self.fail('disabled clicked'))
            self.assertIsNone(button.props['onClick'])

    def test_selected_list_keeps_selection_ring_through_hover_and_press(self):
        selected, _ = render(oreui.OreListItem, selected=True)
        builder = selected.props['buttonBuilder']
        self.assertEqual(builder(pyreact.ButtonState.default).props['src'],
                         oreui.texture('list_item_action_focused'))
        self.assertEqual(builder(pyreact.ButtonState.hover).props['src'],
                         oreui.texture('list_item_action_hovered'))
        self.assertEqual(builder(pyreact.ButtonState.pressed).props['src'],
                         oreui.texture('list_item_action_pressed_focused'))
        self.assertTrue(any(child.key == 'ore_focus_outline' for child in selected.children))

        tabs, _ = render(oreui.OreTabs, options=[('A', 'a'), ('B', 'b')], value='a', onChange=None)
        self.assertEqual(tabs.children[0].props['buttonBuilder'](pyreact.ButtonState.default).props['src'],
                         'textures/pyreact_ore/skin/tab_selected_default')

        plain, _ = render(oreui.OreListItem, selected=False)
        plain_builder = plain.props['buttonBuilder']
        self.assertEqual(plain_builder(pyreact.ButtonState.hover).props['src'],
                         oreui.texture('list_item_action_hovered'))

    def test_slider_supports_controlled_uncontrolled_and_disabled_modes(self):
        changes = []
        slider, _ = render(oreui.OreSlider, defaultValue=0.25, onChange=changes.append)
        self.assertEqual(slider.props['value'], 0.25)
        slider.props['onChange'](0.75)
        self.assertEqual(changes, [0.75])

        controlled, _ = render(oreui.OreSlider, value=0.4, onChange=changes.append)
        self.assertEqual(controlled.props['value'], 0.4)

        disabled, _ = render(oreui.OreSlider, value=0.4, disabled=True,
                             onChange=lambda value: self.fail('disabled slider changed'))
        self.assertIsNone(disabled.props['onChange'])

        host = FakeHost()
        fiber = Fiber(disabled, host)
        fiber.native_path = '/slider'
        control = host.GetBaseUIControl('/slider')
        oreui.components.NativeOreSlider.apply_props(host, fiber, control, None, disabled.props)
        self.assertFalse(control.touch_enabled)

    def test_stepped_slider_rounds_values_and_native_callback_to_same_stop(self):
        from ore_demo.oreui._slider import NativeOreSlider
        changes = []
        for value, expected in [(0.49, 0), (0.5, 1), (2.4, 2), (2.5, 3), (99, 4), (-1, 0)]:
            element, _ = render(oreui.OreSlider, value=value, steps=5, onChange=changes.append)
            self.assertEqual(element.props['value'], expected)
            element.props['onChange'](value)
            self.assertEqual(changes[-1], expected)
        element, _ = render(oreui.OreSlider, value=2, steps=5, onChange=changes.append)
        host = FakeHost()
        fiber = Fiber(element, host)
        fiber.native_path = '/slider'
        control = host.GetBaseUIControl('/slider')
        NativeOreSlider.apply_props(host, fiber, control, None, element.props)
        host.slider_callback(2.4)
        self.assertEqual(control.GetSliderValue(), 2)
        self.assertEqual(changes[-1], 2)

    def test_navigation_and_segments_use_independent_selected_hover_skins(self):
        for selected in (False, True):
            item, _ = render(oreui.OreNavigationItem, selected=selected, label='Settings')
            for state in (pyreact.ButtonState.default, pyreact.ButtonState.hover):
                src = item.props['buttonBuilder'](state).props['src']
                self.assertIn('navigation' + ('_selected' if selected else '') + '_' + state, src)
            self.assertFalse(any(child.key == 'ore_focus_outline' for child in item.children))
        changes = []
        group, _ = render(oreui.OreSegmentedControl, options=[('A', 0), ('B', 1)], value=0, onChange=changes.append)
        group.children[1].props['onClick']()
        self.assertEqual(changes, [1])
        self.assertIn('segment_selected_default', group.children[0].props['buttonBuilder'](pyreact.ButtonState.default).props['src'])

    def test_step_drag_preserves_native_position_until_release(self):
        from ore_demo.oreui._slider import NativeOreSlider
        class EventHost(FakeHost):
            def _pyreact_dispatch_slider_change(self, value=None, is_finish=False):
                self.controls['/slider'].SetSliderValue(value)
                self.slider_callback(value)
        changes = []
        element, _ = render(oreui.OreSlider, value=1, steps=5, onChange=changes.append)
        host = EventHost()
        fiber = Fiber(element, host)
        fiber.native_path = '/slider'
        control = host.GetBaseUIControl('/slider')
        NativeOreSlider.apply_props(host, fiber, control, None, element.props)
        host._pyreact_dispatch_slider_change(1.4, False)
        self.assertEqual(changes[-1], 1)
        self.assertAlmostEqual(control.GetSliderValue(), 1.4)
        NativeOreSlider.apply_props(host, fiber, control, element.props, element.props)
        self.assertAlmostEqual(control.GetSliderValue(), 1.4)
        host._pyreact_dispatch_slider_change(2.4, True)
        self.assertEqual(changes[-1], 2)
        self.assertEqual(control.GetSliderValue(), 2)
        # A controlled caller can reject a change; the next commit restores it.
        NativeOreSlider.apply_props(host, fiber, control, element.props, element.props)
        self.assertEqual(control.GetSliderValue(), 1)
        NativeOreSlider.unmount(host, fiber)
        self.assertEqual(host._ore_slider_records, {})

    def test_field_controlled_uncontrolled_and_disabled_behavior(self):
        changes = []
        field, fiber = render(oreui.OreField, defaultValue='draft', onChange=changes.append)
        text_input = field.children[0]
        text_input.props['onChange']('edited')
        updated, _ = render(oreui.OreField, fiber=fiber, onChange=changes.append)
        self.assertEqual(updated.children[0].props['value'], 'edited')
        self.assertEqual(changes, ['edited'])
        controlled, _ = render(oreui.OreField, value='fixed', onChange=changes.append)
        self.assertEqual(controlled.children[0].props['value'], 'fixed')
        disabled, _ = render(oreui.OreField, value='locked', disabled=True)
        self.assertIsNone(disabled.children[0].props['onChange'])

    def test_dropdown_selection_closes_and_respects_controlled_state(self):
        changed = []
        dropdown, fiber = render(oreui.OreDropdown, options=[('A', 1), ('B', 2)], value=None, onChange=changed.append)
        dropdown.children[0].props['onClick']()
        opened, _ = render(oreui.OreDropdown, fiber=fiber, options=[('A', 1), ('B', 2)], value=None, onChange=changed.append)
        self.assertTrue(opened.children[1].children[0].props['visible'])
        modal = opened.children[1].children[0]
        surface = modal.props['children'][1].children[0]
        menu = surface.children[1].props['children'][0]
        menu.children[1].props['onClick']()
        self.assertEqual(changed, [2])
        closed, _ = render(oreui.OreDropdown, fiber=fiber, options=[('A', 1), ('B', 2)], value=None)
        self.assertFalse(closed.children[1].children[0].props['visible'])
        self.assertEqual(closed.children[0].props['children'][0].props['content'], '请选择')

    def test_switch_disabled_and_uncontrolled(self):
        switch, _ = render(oreui.OreSwitch, value=False, disabled=True, label='Locked')
        self.assertIsNone(switch.children[0].props['onClick'])
        changed = []
        switch, fiber = render(oreui.OreSwitch, defaultValue=False, onChange=changed.append)
        switch.children[0].props['onClick']()
        updated, _ = render(oreui.OreSwitch, fiber=fiber, onChange=changed.append)
        self.assertEqual(changed, [True])
        self.assertIn('switch_on', updated.children[0].props['buttonBuilder'](pyreact.ButtonState.default).props['src'])

    def test_complete_baked_font_has_cjk_and_matching_wrap_metrics(self):
        from ore_demo.oreui.typography import GLYPHS, layout
        self.assertGreater(len(GLYPHS), 30000)
        for char in u'瞭望塔林间小屋世界设置':
            self.assertIn(char, GLYPHS)
        pieces, widths = layout(u'世界设置，生存模式。', 8, 32)
        self.assertGreater(len(widths), 1)
        self.assertTrue(all(width <= 32 for width in widths))
        self.assertEqual(len(pieces), len(u'世界设置，生存模式。'))

    def test_atlas_text_resolves_percent_and_flex_width_without_native_measurement(self):
        from ore_demo.oreui._text import NativeOreText, available_width
        from ore_demo.oreui.typography import OreString
        from ore_demo.pyreact import layout, native
        host = FakeHost()
        original = native.get_screen_size
        native.get_screen_size = lambda: (200, 120)
        try:
            root = LayoutNode(Fiber(pyreact.Panel(style=pyreact.Style(width='100%',
                flexDirection=pyreact.FlexDirection.row, gap=8)), host))
            left = LayoutNode(Fiber(pyreact.Panel(style=pyreact.Style(flex=1, padding=8)), host))
            right = LayoutNode(Fiber(pyreact.Panel(style=pyreact.Style(flex=1)), host))
            text = LayoutNode(Fiber(NativeOreText(content=OreString(u'较长文字，应该换行。'),
                fontSize=8, style=pyreact.Style(width='100%')), host))
            root.children, left.parent, right.parent = [left, right], root, root
            left.children, text.parent = [text], left
            self.assertEqual(available_width(text, layout), 80)
            blank = LayoutNode(Fiber(pyreact.Panel(), host))
            right.children, blank.parent = [blank], right
            self.assertEqual(available_width(text, layout), 80)
        finally:
            native.get_screen_size = original

    def test_compact_tags_keep_text_on_one_line_at_native_float_boundaries(self):
        import struct
        from ore_demo.oreui.typography import layout
        for component in (oreui.OreTag, oreui.OreBadge):
            for label in (u'3 个存档', u'99+', u'NEW', u'锁定'):
                tag, _ = render(component, label=label)
                text = tag.children[0]
                unused, widths = layout(label, text.props['fontSize'])
                native_width = struct.unpack('f', struct.pack('f', widths[0]))[0]
                pieces, wrapped = layout(label, text.props['fontSize'], native_width)
                self.assertEqual(len(wrapped), 1)
                self.assertLessEqual(text.props['fontSize'] * 1.5, tag.style.get('height'))

    def test_variable_animation_timing_preserves_holds_and_pause(self):
        from ore_demo.oreui._image import NativeOreImage
        host = FakeHost()
        element = NativeOreImage(frameDurations=[0.1, 1.2, 0.1])
        fiber = Fiber(element, host)
        fiber.native_path = '/animation'
        state = dict(playing=True, completed=False, last_time=0.0, index=0,
                     elapsed=0.0, loop=True, frames=[{'src': 'a'}, {'src': 'b'}, {'src': 'c'}])
        fiber.primitive_state['_image_frame_animation'] = state
        NativeOreImage._tick_frame_animation(host, fiber, 0.11)
        self.assertEqual(state['index'], 1)
        NativeOreImage._tick_frame_animation(host, fiber, 1.1)
        self.assertEqual(state['index'], 1)
        NativeOreImage._tick_frame_animation(host, fiber, 1.31)
        self.assertEqual(state['index'], 2)
        NativeOreImage._tick_frame_animation(host, fiber, 2.81)
        self.assertEqual(state['index'], 0)
        state['playing'] = False
        NativeOreImage._tick_frame_animation(host, fiber, 4.0)
        self.assertEqual(state['index'], 0)

    def test_all_imported_animation_timelines_apply_the_matching_native_uv(self):
        from ore_demo.oreui._image import NativeOreImage
        for name in oreui.asset_names():
            metadata = oreui.asset(name)
            if 'frames' not in metadata:
                continue
            element, unused = render(oreui.OreImage, name=name, animate=True)
            host = FakeHost()
            fiber = Fiber(element, host)
            fiber.native_path = '/animation'
            state = dict(playing=True, completed=False, last_time=0.0, index=0,
                         elapsed=0.0, loop=True, frames=metadata['frames'])
            fiber.primitive_state['_image_frame_animation'] = state
            start = 0.0
            for index, duration in enumerate(metadata['frameDurations']):
                NativeOreImage._tick_frame_animation(host, fiber, start + duration / 2.0 + 0.00001)
                self.assertEqual(state['index'], index, name)
                if index:
                    self.assertEqual(host.GetBaseUIControl('/animation').uv, metadata['frames'][index]['uv'])
                start += duration
            NativeOreImage._tick_frame_animation(host, fiber,
                start + metadata['frameDurations'][0] / 2.0 + 0.00001)
            self.assertEqual(state['index'], 0, name)

    def test_every_resource_fits_wide_and_tall_preview_without_distortion(self):
        from ore_demo.oreui._image import NativeOreImage
        for name in oreui.asset_names():
            element, unused = render(oreui.OreImage, name=name, contain=True)
            for width, height in ((88, 44), (44, 88)):
                host = FakeHost()
                fiber = Fiber(element, host)
                fiber.native_path = '/image'
                fiber.primitive_state['_layout_applied'] = (width, height, 0, 0, 1)
                node = LayoutNode(fiber)
                node.frame_w, node.frame_h = width, height
                NativeOreImage.apply_layout(host, node)
                control = host.GetBaseUIControl('/image')
                w, h = control.size
                x, y = control.position
                sw, sh = oreui.asset(name)['size']
                self.assertAlmostEqual(w / h, float(sw) / sh)
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, width + .0001)
                self.assertLessEqual(y + h, height + .0001)

    def test_radio_and_pagination_reject_disabled_and_out_of_range_values(self):
        changed = []
        radio, _ = render(oreui.OreRadio, options=[('A', 'a'), ('B', 'b')],
                          value='a', onChange=changed.append, disabled=['b'])
        radio.children[0].props['onClick']()
        self.assertEqual(changed, ['a'])
        self.assertIsNone(radio.children[1].props['onClick'])
        pagination, _ = render(oreui.OrePagination, page=1, pages=3, onChange=changed.append)
        pagination.children[0].props['onClick']()
        self.assertEqual(changed, ['a'])
        pagination.children[2].props['onClick']()
        self.assertEqual(changed, ['a', 2])
        last, _ = render(oreui.OrePagination, page=99, pages=3, onChange=changed.append)
        last.children[2].props['onClick']()
        self.assertEqual(changed, ['a', 2])

    def test_nested_scroll_range_stops_at_inner_viewport(self):
        from ore_demo.oreui._scroll import NativeOreScrollView
        host = FakeHost()
        outer = LayoutNode(Fiber(NativeOreScrollView(style=pyreact.Style(height=100)), host))
        outer.frame_w, outer.frame_h = 200, 100
        wrapper = LayoutNode(Fiber(pyreact.Panel(style=pyreact.Style(width=200)), host))
        wrapper.frame_w, wrapper.frame_h, wrapper.measured_h = 200, 800, 240
        inner = LayoutNode(Fiber(NativeOreScrollView(style=pyreact.Style(height=90)), host))
        inner.frame_y, inner.frame_w, inner.frame_h, inner.content_h = 120, 200, 90, 600
        tall = LayoutNode(Fiber(pyreact.Panel(style=pyreact.Style(height=600)), host))
        tall.frame_y, tall.frame_w, tall.frame_h = 120, 200, 600
        inner.children = [tall]
        wrapper.children = [inner]
        outer.children = [wrapper]
        self.assertEqual(NativeOreScrollView._scroll_content_size(outer), (200, 240))

    def test_banner_parent_reserves_full_height_before_following_content(self):
        from ore_demo.pyreact import layout, native

        def materialize(element, host):
            if element.is_component:
                return materialize(element.comp_type._render(**element.props), host)
            fiber = Fiber(element, host)
            fiber.last_props = element.props
            node = LayoutNode(fiber)
            node.children = [materialize(child, host) for child in element.children]
            for child in node.children:
                child.parent = node
            return node

        original_measure = native.measure_text
        try:
            for text_height in (10, 40):
                native.measure_text = lambda *args, **kwargs: (80, text_height)
                for on_close in (None, lambda: None):
                    parent = materialize(pyreact.Panel(children=[
                        oreui.OreBanner(message='Saved', onClose=on_close),
                        pyreact.Panel(style=pyreact.Style(height=18)),
                    ]), FakeHost())
                    layout.measure(parent, parent.fiber.host)
                    self.assertGreaterEqual(parent.children[0].measured_h, max(28, text_height + 8))
                    self.assertGreaterEqual(parent.measured_h, max(28, text_height + 8) + 18)
        finally:
            native.measure_text = original_measure


if __name__ == '__main__':
    unittest.main()
