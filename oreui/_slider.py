# -*- coding: utf-8 -*-
"""Reuse the host slider's input lifecycle and disable native interaction."""
from ..pyreact.primitives import SliderPrimitive as BaseSliderPrimitive
from ..pyreact import native


def _finish_listener(host):
    records = getattr(host, '_ore_slider_records', None)
    if records is not None or not hasattr(host, '_pyreact_dispatch_slider_change'):
        return records
    records = {}
    host._ore_slider_records = records
    original = host._pyreact_dispatch_slider_change

    def dispatch(value=None, is_finish=False):
        for record in records.values():
            record['in_event'] = True
        try:
            original(value, is_finish)
            if is_finish:
                for record in list(records.values()):
                    if record.get('dragging'):
                        record['finish']()
        finally:
            for record in records.values():
                record['in_event'] = False
    host._pyreact_dispatch_slider_change = dispatch
    return records


class SliderPrimitive(BaseSliderPrimitive):
    template_path = '/root/ore_slider_tmpl'

    def apply_props(self, host, fiber, control, prev_props, next_props):
        steps = max(1, int(next_props.get('steps', 1)))
        callback = next_props.get('onChange')
        if steps > 1 and control is not None and not next_props.get('disabled'):
            slider = control.asSlider()
            records = _finish_listener(host)
            record = records.setdefault(fiber.native_path, {}) if records is not None else {}

            def finish():
                record['dragging'] = False
                target = max(0, min(steps - 1, int(float(slider.GetSliderValue()) + 0.5)))
                self._set_property_bag(control, steps, target)
                slider.SetSliderValue(target)
                host.pyreact_set_slider_value(fiber.native_path, target)
                if next_props.get('value') is not None:
                    host.pyreact_set_slider_controlled_value(fiber.native_path, target)
                record['finished'] = True
                host.schedule_render(fiber)
            record['finish'] = finish

            def snapped_change(value):
                snapped = max(0, min(steps - 1, int(float(value) + 0.5)))
                if record.get('in_event'):
                    record['dragging'] = True
                    host.pyreact_unset_slider_controlled_value(fiber.native_path)
                elif float(value) != snapped:
                    self._set_property_bag(control, steps, snapped)
                    slider.SetSliderValue(snapped)
                    host.pyreact_set_slider_value(fiber.native_path, snapped)
                    host.pyreact_set_slider_controlled_value(fiber.native_path, snapped)
                if callback is not None:
                    callback(snapped)
            applied_props = dict(next_props, onChange=snapped_change)
            if record.get('dragging'):
                applied_props['value'] = None
            elif record.pop('finished', False):
                prev_props = None
        else:
            records = getattr(host, '_ore_slider_records', None)
            if records is not None:
                records.pop(fiber.native_path, None)
            applied_props = next_props
        BaseSliderPrimitive.apply_props(self, host, fiber, control, prev_props, applied_props)
        if control is None:
            return
        disabled = bool(next_props.get('disabled', False))
        if fiber.primitive_state.get('ore_disabled') != disabled:
            control.SetTouchEnable(not disabled)
            fiber.primitive_state['ore_disabled'] = disabled
            for state in ('default', 'hover', 'indent', 'locked'):
                image = native.get_control(host, fiber.native_path + '/slider_box/' + state)
                if image is not None:
                    texture = 'thumb_disabled' if disabled else 'thumb_hover' if state in ('hover', 'indent') else 'thumb_default'
                    image.asImage().SetSprite('textures/pyreact_ore/skin/' + texture)
            fade = native.get_control(host, fiber.native_path + '/slider_box/locked/transparent_grey')
            if fade is not None:
                fade.SetAlpha(0.0)
            for state in ('default', 'hover'):
                background = 'slider_background' + ('_hover' if state == 'hover' else '')
                image = native.get_control(host, fiber.native_path + '/slider_bar_' + state + '/sizing_panel/' + background)
                if image is not None:
                    image.asImage().SetSprite('textures/pyreact_ore/skin/track' + ('_disabled' if disabled else ''))
                name = 'slider_progress' + ('_hover' if state == 'hover' else '')
                path = fiber.native_path + '/slider_bar_' + state + '/sizing_panel/' + name
                image = native.get_control(host, path)
                if image is not None:
                    image.asImage().SetSprite('textures/pyreact_ore/skin/progress' + ('_hover' if state == 'hover' else ''))
                    image.SetAlpha(0.0 if disabled else 1.0)

    def unmount(self, host, fiber):
        records = getattr(host, '_ore_slider_records', None)
        if records is not None:
            records.pop(fiber.native_path, None)
        BaseSliderPrimitive.unmount(self, host, fiber)


NativeOreSlider = SliderPrimitive()
