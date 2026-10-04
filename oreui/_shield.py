# -*- coding: utf-8 -*-
"""Modal hit guards with no button overlapping a native edit box."""
from ..pyreact import native
from ..pyreact.primitives import PanelPrimitive, InputPrimitive


def subtract_rectangles(bounds, holes):
    rectangles = [bounds]
    for hole in holes:
        remaining = []
        for left, top, right, bottom in rectangles:
            x0, y0 = max(left, hole[0]), max(top, hole[1])
            x1, y1 = min(right, hole[2]), min(bottom, hole[3])
            if x0 >= x1 or y0 >= y1:
                remaining.append((left, top, right, bottom))
                continue
            for rectangle in ((left, top, right, y0), (left, y1, right, bottom),
                              (left, y0, x0, y1), (x1, y0, right, y1)):
                if rectangle[0] < rectangle[2] and rectangle[1] < rectangle[3]:
                    remaining.append(rectangle)
        rectangles = remaining
    return rectangles


class SurfacePrimitive(PanelPrimitive):
    pass


class ShieldPrimitive(PanelPrimitive):
    def apply_layout(self, host, node):
        # GetSize can remain zero until UpdateScreen when a newly mounted
        # modal is still hidden while measuring its origin. Use the completed
        # layout frames, so the first visible frame already blocks input.
        width = node.frame_w * node.visual_scale_x
        height = node.frame_h * node.visual_scale_y
        holes = []
        pending = list(node.parent.children)
        backdrop = bool(node.fiber.props.get('backdrop'))
        while pending:
            child = pending.pop()
            primitive = child.fiber.comp_type
            if child.display_none or (child.style is not None and child.style.get('visible') is False):
                continue
            excluded = isinstance(primitive, SurfacePrimitive) if backdrop else (
                isinstance(primitive, InputPrimitive) and not child.fiber.props.get('disabled'))
            if excluded:
                x = (child.frame_x - node.frame_x) * node.visual_scale_x
                y = (child.frame_y - node.frame_y) * node.visual_scale_y
                w = child.frame_w * child.visual_scale_x
                h = child.frame_h * child.visual_scale_y
                holes.append((x, y, x + w, y + h))
            else:
                pending.extend(child.children)
        rectangles = subtract_rectangles((0, 0, width, height), holes)
        state = node.fiber.primitive_state
        guards = state.setdefault('ore_guards', [])
        for index, rectangle in enumerate(rectangles):
            if index == len(guards):
                name = 'ore_guard_' + str(index)
                path = native.join_path(node.fiber.native_path, name)
                if not native.clone(host, native.TEMPLATE_BUTTON, node.fiber.native_path, name):
                    raise RuntimeError('Could not create Ore modal input guard')
                guard = native.get_control(host, path)
                guard.asButton().AddTouchEventParams({'isSwallow': True})
                guard.asButton().SetButtonTouchUpCallback(host._pyreact_dispatch_touch_up)
                native.set_layer(guard, 0)
                for label in ('default', 'hover', 'pressed'):
                    native.get_control(host, native.join_path(path, label)).SetAlpha(0)
                guards.append((guard, path))
            guard, path = guards[index]
            host.pyreact_register_button(path, None, None, node.fiber.props.get('onClick'))
            if state.get(('ore_guard_rect', index)) != rectangle:
                left, top, right, bottom = rectangle
                guard.SetPosition((left, top))
                native.set_size(guard, (right - left, bottom - top))
                native.set_visible(guard, True)
                state[('ore_guard_rect', index)] = rectangle
        while len(guards) > len(rectangles):
            guard, path = guards.pop()
            host.pyreact_unregister_button(path)
            native.remove(host, guard)
            state.pop(('ore_guard_rect', len(guards)), None)

    def unmount(self, host, fiber):
        for guard, path in fiber.primitive_state.get('ore_guards', ()):
            host.pyreact_unregister_button(path)


NativeOreSurface = SurfacePrimitive()
NativeOreShield = ShieldPrimitive()
