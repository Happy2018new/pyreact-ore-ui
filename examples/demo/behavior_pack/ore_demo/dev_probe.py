# -*- coding: utf-8 -*-
"""Development-only native observations used by tools/verify_live.py."""
import mod.client.extraClientApi as clientApi
from .pyreact import host, native, ButtonState, ScrollView
from .pyreact.primitives import ButtonPrimitive, SliderPrimitive, InputPrimitive, ScrollViewPrimitive

def _walk(fiber):
    yield fiber
    for child in fiber.child_fibers:
        for descendant in _walk(child):
            yield descendant


def controls(keys):
    runtime = host._ACTIVE_HOST[0]
    if runtime is None or runtime._root_fiber is None:
        raise RuntimeError('Open the playground before probing controls')
    fibers = list(_walk(runtime._root_fiber))
    result = {}
    for key in keys:
        matches = [fiber for fiber in fibers if fiber.key == key]
        if len(matches) != 1:
            raise ValueError('Expected one control key: ' + key)
        button = next((fiber for fiber in _walk(matches[0])
                       if isinstance(fiber.comp_type, (ButtonPrimitive, SliderPrimitive, InputPrimitive,
                                                       ScrollViewPrimitive))), None)
        if button is None:
            raise ValueError('Expected a native button or slider: ' + key)
        control = runtime.GetBaseUIControl(button.native_path)
        data = {'position': control.GetGlobalPosition(), 'size': control.GetSize(),
                'path': button.native_path}
        if isinstance(button.comp_type, InputPrimitive):
            data['text'] = control.asTextEditBox().GetEditText()
            data['disabled'] = bool(button.props.get('disabled'))
        elif isinstance(button.comp_type, ScrollViewPrimitive):
            data['scroll'] = ScrollView.get_scroll_position(control)
        elif isinstance(button.comp_type, SliderPrimitive):
            data['value'] = control.asSlider().GetSliderValue()
            data['disabled'] = bool(button.props.get('disabled'))
        else:
            data['states'] = {}
            for state in (ButtonState.default, ButtonState.hover, ButtonState.pressed):
                state_control = runtime.GetBaseUIControl(native.join_path(button.native_path, state))
                applied = button.primitive_state.get('state_' + state)
                data['states'][state] = {'visible': state_control.GetVisible(),
                                         'applied': applied}
        result[key] = data
    return result


def input_mode():
    enum = clientApi.GetMinecraftEnum()
    view = clientApi.GetEngineCompFactory().CreatePlayerView(clientApi.GetLevelId())
    mode = view.GetToggleOption(enum.OptionId.INPUT_MODE)
    return {'simulated': clientApi.IsTouchWithMouse(), 'mode': mode,
            'touch': mode == enum.InputMode.Touch}


def scroll_to(key, percent):
    runtime = host._ACTIVE_HOST[0]
    fibers = [fiber for fiber in _walk(runtime._root_fiber) if fiber.key == key]
    fiber = next(fiber for fiber in _walk(fibers[0]) if isinstance(fiber.comp_type, ScrollViewPrimitive))
    root = runtime.GetBaseUIControl(fiber.native_path)
    return ScrollView.scroll_to_percent(root, percent)


def reveal(scroll_key, target_key):
    runtime = host._ACTIVE_HOST[0]
    fibers = list(_walk(runtime._root_fiber))
    scroll_root = next((fiber for fiber in fibers if fiber.key == scroll_key), None)
    target_root = next((fiber for fiber in fibers if fiber.key == target_key), None)
    if scroll_root is None or target_root is None:
        return False
    scroll_fiber = next(fiber for fiber in _walk(scroll_root)
                        if isinstance(fiber.comp_type, ScrollViewPrimitive))
    target = next((fiber for fiber in _walk(target_root) if fiber.native_path), None)
    if target is None or not target.native_path.startswith(scroll_fiber.native_path + '/'):
        return False
    viewport = runtime.GetBaseUIControl(scroll_fiber.native_path)
    control = runtime.GetBaseUIControl(target.native_path)
    top = control.GetGlobalPosition()[1]
    bottom = top + control.GetSize()[1]
    view_top = viewport.GetGlobalPosition()[1]
    view_bottom = view_top + viewport.GetSize()[1]
    offset = min(0, top - view_top - 4) if top < view_top else max(0, bottom - view_bottom + 4)
    if offset:
        position = viewport.asScrollView().GetScrollViewPos()
        return ScrollView.scroll_to(viewport, max(0, position + offset))
    return True
