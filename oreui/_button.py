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
