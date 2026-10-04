# -*- coding: utf-8 -*-
"""Preserve the host input implementation and add native disable handling."""
from ..pyreact.primitives import InputPrimitive


class OreInputPrimitive(InputPrimitive):
    template_path = '/root/ore_input_tmpl'

    def children_path(self, native_path, host=None):
        return native_path + '/centering_panel/clipper_panel'

    def apply_props(self, host, fiber, control, prev_props, next_props):
        InputPrimitive.apply_props(self, host, fiber, control, prev_props, next_props)
        if control is not None and (prev_props is None or
                bool(prev_props.get('disabled')) != bool(next_props.get('disabled'))):
            control.SetTouchEnable(not bool(next_props.get('disabled')))
        if control is not None and prev_props is None:
            label = host.GetBaseUIControl(fiber.native_path + '/centering_panel/clipper_panel/display_text')
            label.asLabel().SetTextFontSize(1.4)


NativeOreInput = OreInputPrimitive()
NativeOreSearchInput = OreInputPrimitive()
NativeOreSearchInput.template_path = '/root/ore_search_input_tmpl'
