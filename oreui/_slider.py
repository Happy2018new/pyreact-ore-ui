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
        host._ore_slider_in_event = True
        try:
            original(value, is_finish)
            if is_finish:
                for record in list(records.values()):
                    if record.get('dragging'):
                        record['finish']()
        finally:
            host._ore_slider_in_event = False
    host._pyreact_dispatch_slider_change = dispatch
    return records


class SliderPrimitive(BaseSliderPrimitive):
    template_path = '/root/ore_slider_tmpl'

    def apply_props(self, host, fiber, control, prev_props, next_props):
        steps = max(1, int(next_props.get('steps', 1)))
        if control is not None and not next_props.get('disabled'):
            records = _finish_listener(host)
            record = records.setdefault(fiber.native_path, {}) if records is not None else {}
            record['props'] = next_props
            if 'change' not in record:
                slider = control.asSlider()

                def normalize(value):
                    count = max(1, int(record['props'].get('steps', 1)))
                    return max(0, min(count - 1, int(float(value) + .5))) if count > 1 else max(0., min(1., float(value)))

                def finish():
                    props = record['props']
                    count = max(1, int(props.get('steps', 1)))
                    record['dragging'] = False
                    target = normalize(slider.GetSliderValue())
                    if count > 1:
                        self._set_property_bag(control, count, target)
                        slider.SetSliderValue(target)
                    host.pyreact_set_slider_value(fiber.native_path, target)
                    if props.get('value') is not None:
                        host.pyreact_set_slider_controlled_value(fiber.native_path, target)
                    if record.get('last') != target and props.get('onChange'):
                        props['onChange'](target)
                    record['last'] = target
                    if props.get('onChangeEnd'):
                        props['onChangeEnd'](target)
                    record['finished'] = True

                def change(value):
                    props = record['props']
                    snapped = normalize(value)
                    if getattr(host, '_ore_slider_in_event', False):
                        record['dragging'] = True
                        host.pyreact_unset_slider_controlled_value(fiber.native_path)
                    elif float(value) != snapped:
                        self._set_property_bag(control, props.get('steps', 1), snapped)
                        slider.SetSliderValue(snapped)
                        host.pyreact_set_slider_value(fiber.native_path, snapped)
                        host.pyreact_set_slider_controlled_value(fiber.native_path, snapped)
                    if record.get('last') != snapped:
                        record['last'] = snapped
                        if props.get('onChange'):
                            props['onChange'](snapped)
                record.update(finish=finish, change=change, last=None)
            elif not record.get('dragging'):
                record['last'] = next_props.get('value')
            applied_props = dict(next_props, onChange=record['change'])
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
                    image.asImage().SetSprite('textures/pyreact_ore/skin/progress_disabled' if disabled else
                        'textures/pyreact_ore/skin/progress' + ('_hover' if state == 'hover' else ''))
                    image.SetAlpha(1.0)
                for side in ('left', 'right'):
                    cap = native.get_control(host, fiber.native_path + '/slider_bar_' + state + '/sizing_panel/progress_' + side + '_cap')
                    if cap is not None:
                        name = ('cap_disabled' if side == 'left' else 'step_disabled') if disabled else 'step'
                        cap.asImage().SetSprite('textures/pyreact_ore/skin/' + name)
        # A disabled value can change without a new layout pass.
        self._paint_ticks(host, fiber)

    def apply_layout(self, host, node):
        # Native factories create duplicate child names, which the SDK cannot
        # address independently. Keep their offsets, paint addressable markers.
        self._paint_ticks(host, node.fiber)

    def _paint_ticks(self, host, fiber):
        props = fiber.props
        steps = max(1, int(props.get('steps', 1)))
        count = max(0, steps - 2) if steps > 1 else 0
        state = fiber.primitive_state
        applied = state.get('_layout_applied')
        if not applied:
            return
        width, height = applied[:2]
        disabled = bool(props.get('disabled'))
        cutoff = float(props.get('value') or 0) if disabled else None
        signature = (steps, disabled, width, height, cutoff)
        if state.get('ore_ticks') == signature:
            return
        pool = state.setdefault('ore_tick_pool', [])
        while len(pool) < count:
            name = 'ore_tick_' + str(len(pool))
            native.clone(host, '/root/ore_step_tmpl', fiber.native_path, name)
            pool.append(host.GetBaseUIControl(fiber.native_path + '/' + name))
        for index, tick in enumerate(pool):
            tick.SetVisible(index < count, False)
            if index >= count:
                continue
            tick.SetPosition(((width + 16) * (index + 1) / (steps - 1) - 9, (height - 6) / 2))
            tick.SetSize((1, 6))
            texture = ('cap_disabled' if index + 1 <= cutoff else 'step_disabled') if disabled else 'step'
            tick.asImage().SetSprite('textures/pyreact_ore/skin/' + texture)
        state['ore_ticks'] = signature

    def unmount(self, host, fiber):
        records = getattr(host, '_ore_slider_records', None)
        if records is not None:
            records.pop(fiber.native_path, None)
        BaseSliderPrimitive.unmount(self, host, fiber)


NativeOreSlider = SliderPrimitive()
