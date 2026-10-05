# -*- coding: utf-8 -*-
"""Local Button primitive adapter: forward slice data to native state images.

Upstream ButtonPrimitive applies src/color only. Inheriting its template and
event lifecycle keeps native hover/press behavior, without patching Pyreact.
"""
from ..pyreact import ButtonState, ImageAdaptionType
from ..pyreact import native
from ..pyreact.primitives import ButtonPrimitive as BaseButtonPrimitive


class ButtonPrimitive(BaseButtonPrimitive):
    # Keep the native primitive name: upstream debug tools identify Button
    # controls by this name, while OreButton remains the public Composite.
    def apply_props(self, host, fiber, control, prev_props, next_props):
        BaseButtonPrimitive.apply_props(self, host, fiber, control, prev_props, next_props)
        builder = next_props.get('buttonBuilder')
        if control is None or builder is None:
            return
        for state in (ButtonState.default, ButtonState.hover, ButtonState.pressed):
            element = builder(state)
            props = element.props
            signature = (props.get('src'), props.get('imageAdaption'), props.get('nineSliceData'))
            cache_key = ('ore_slice', state)
            if fiber.primitive_state.get(cache_key) == signature:
                continue
            state_control = native.get_control(host, native.join_path(fiber.native_path, state))
            image = state_control.asImage() if state_control is not None else None
            if image is None:
                continue
            adaption = props.get('imageAdaption', ImageAdaptionType.filled)
            edges = props.get('nineSliceData')
            applied = (image.SetImageAdaptionType(adaption, edges) if edges is not None
                       else image.SetImageAdaptionType(adaption))
            if applied is False:
                raise RuntimeError('Ore button image adaption failed: ' + state)
            fiber.primitive_state[cache_key] = signature


NativeOreButton = ButtonPrimitive()


def _press_state(host, args):
    path = args.get('ButtonPath') if isinstance(args, dict) else None
    return getattr(host, '_ore_press_states', {}).get(path)


def _move_content(state, active):
    state['ore_inside'] = active
    offset = state.get('ore_press_offset', 0) if active else 0
    content = state.get('ore_press_content')
    if content is not None:
        content.SetPosition((0, offset * state.get('ore_press_scale', 1)))


def _ore_press_down(host, args):
    state = _press_state(host, args)
    if state is not None:
        state['ore_held'] = True
        _move_content(state, True)


def _ore_press_up(host, args):
    state = _press_state(host, args)
    if state is not None:
        state['ore_held'] = False
        _move_content(state, False)
    # Restore geometry before a click can replace or unmount this control.
    host._pyreact_dispatch_touch_up(args)


def _ore_press_cancel(host, args):
    state = _press_state(host, args)
    if state is not None:
        state['ore_held'] = False
        _move_content(state, False)


def _ore_press_out(host, args):
    state = _press_state(host, args)
    if state is not None:
        # The native button cancels its pressed state on exit. Re-entering
        # while the physical mouse is still held produces hover, not a second
        # down event. Keep the content in sync with that native face.
        state['ore_held'] = False
        _move_content(state, False)


def _ore_press_in(host, args):
    state = _press_state(host, args)
    if state is not None:
        _move_content(state, state.get('ore_held', False))


class PressablePrimitive(ButtonPrimitive):
    """Keep the hit rectangle fixed while the raised face and content sink.

    Native state images own the face visibility. Event callbacks move one
    content panel, including caller-supplied icons and custom children. There
    is no frame polling and no duplicated text or interaction subtree.
    """
    template_path = '/root/ore_pressable_tmpl'

    def children_path(self, native_path, host=None):
        return native_path + '/content'

    def fill_children(self, native_path):
        return ButtonPrimitive.fill_children(self, native_path) + [native_path + '/content']

    def props_affect_layout(self, prev_props, next_props, style):
        return prev_props.get('pressOffset') != next_props.get('pressOffset')

    def apply_props(self, host, fiber, control, prev_props, next_props):
        ButtonPrimitive.apply_props(self, host, fiber, control, prev_props, next_props)
        if control is None:
            return
        state = fiber.primitive_state
        state['ore_press_offset'] = max(0, next_props.get('pressOffset', 0))
        if prev_props is None:
            if not hasattr(host, '_ore_press_states'):
                host._ore_press_states = {}
            host._ore_press_states[fiber.native_path] = state
            state['ore_press_content'] = native.get_control(host, self.children_path(fiber.native_path))
            button = control.asButton()
            for setter, callback in (
                    (button.SetButtonTouchDownCallback, _ore_press_down),
                    (button.SetButtonTouchUpCallback, _ore_press_up),
                    (button.SetButtonTouchCancelCallback, _ore_press_cancel),
                    (button.SetButtonTouchMoveOutCallback, _ore_press_out),
                    (button.SetButtonTouchMoveInCallback, _ore_press_in)):
                # ModSDK requires a ScreenNode class method, not a closure.
                setattr(type(host), callback.__name__, callback)
                setter(getattr(host, callback.__name__))
        if not state['ore_press_offset']:
            state['ore_held'] = False
        _move_content(state, state.get('ore_held', False) and state.get('ore_inside', False))

    def apply_layout(self, host, node):
        ButtonPrimitive.apply_layout(self, host, node)
        state = node.fiber.primitive_state
        offset = state.get('ore_press_offset', 0) * node.visual_scale_y
        pressed = native.get_control(host, node.fiber.native_path + '/pressed')
        if pressed is not None:
            pressed.SetPosition((0, offset))
            native.set_size(pressed, (node.frame_w * node.visual_scale_x,
                                     max(0, node.frame_h * node.visual_scale_y - offset)))
        state['ore_press_scale'] = node.visual_scale_y
        content = state.get('ore_press_content')
        if content is not None:
            content.SetAlpha(node.inherited_opacity)
        _move_content(state, state.get('ore_held', False) and state.get('ore_inside', False))

    def unmount(self, host, fiber):
        getattr(host, '_ore_press_states', {}).pop(fiber.native_path, None)
        ButtonPrimitive.unmount(self, host, fiber)


NativeOrePressable = PressablePrimitive()


class NavigationButtonPrimitive(ButtonPrimitive):
    """Stretch the fill, keeping both rows of each bevel in one logical pixel."""
    template_path = '/root/ore_navigation_tmpl'

    def apply_props(self, host, fiber, control, prev_props, next_props):
        ButtonPrimitive.apply_props(self, host, fiber, control, prev_props, next_props)
        builder = next_props.get('buttonBuilder')
        if control is None or builder is None:
            return
        for state in (ButtonState.default, ButtonState.hover, ButtonState.pressed):
            src = builder(state).props['src']
            cache_key = ('ore_navigation_edges', state)
            if fiber.primitive_state.get(cache_key) == src:
                continue
            path = native.join_path(fiber.native_path, state)
            image = native.get_control(host, path).asImage()
            image.SetSpriteUV((0, 2))
            image.SetSpriteUVSize((4, 2))
            for edge in ('top_edge', 'bottom_edge'):
                native.get_control(host, native.join_path(path, edge)).asImage().SetSprite(src)
            fiber.primitive_state[cache_key] = src


NativeOreNavigationButton = NavigationButtonPrimitive()


class RadioButtonPrimitive(ButtonPrimitive):
    """A full-row hit target whose native state image is a small diamond."""

    def fill_children(self, native_path):
        return []

    def apply_layout(self, host, node):
        ButtonPrimitive.apply_layout(self, host, node)
        signature = (node.frame_w, node.frame_h)
        state = node.fiber.primitive_state
        if state.get('ore_radio_geometry') == signature:
            return
        for name in (ButtonState.default, ButtonState.hover, ButtonState.pressed):
            control = native.get_control(host, native.join_path(node.fiber.native_path, name))
            if control is not None:
                control.SetSize((16, 16))
                control.SetPosition((0, (node.frame_h - 16) / 2.0))
        state['ore_radio_geometry'] = signature


NativeOreRadioButton = RadioButtonPrimitive()
