# -*- coding: utf-8 -*-
"""Preserve source aspect ratios and GIF frame-specific timing."""
from bisect import bisect_right
from ..pyreact import native
from ..pyreact.primitives import ImagePrimitive as BaseImagePrimitive


class ImagePrimitive(BaseImagePrimitive):
    def apply_layout(self, host, node):
        if not node.fiber.props.get('contain'):
            return
        w, h = node.fiber.props['sourceSize']
        scale = min(node.frame_w / float(w), node.frame_h / float(h))
        fitted_w, fitted_h = w * scale, h * scale
        control = native.get_control(host, node.fiber.native_path)
        applied = node.fiber.primitive_state['_layout_applied']
        control.SetSize((fitted_w, fitted_h))
        control.SetPosition((applied[2] + (node.frame_w - fitted_w) / 2.0,
                             applied[3] + (node.frame_h - fitted_h) / 2.0))

    def _tick_frame_animation(self, host, fiber, now):
        durations = fiber.props.get('frameDurations')
        if not durations:
            return BaseImagePrimitive._tick_frame_animation(self, host, fiber, now)
        state = fiber.primitive_state.get('_image_frame_animation')
        if not state or not state['playing'] or state['completed']:
            return
        if state['last_time'] is None:
            state['last_time'] = now
            return
        signature = tuple(durations)
        if state.get('ore_duration_key') != signature:
            ends, total = [], 0.0
            for duration in durations:
                total += max(0.01, float(duration))
                ends.append(total)
            state.update(ore_duration_key=signature, ore_ends=ends, ore_total=total)
        previous = state['index']
        start = 0.0 if previous == 0 else state['ore_ends'][previous - 1]
        elapsed = start + state['elapsed'] + max(0.0, now - state['last_time'])
        state['last_time'] = now
        completed = not state['loop'] and elapsed >= state['ore_total']
        if state['loop']:
            elapsed %= state['ore_total']
        index = min(len(durations) - 1, bisect_right(state['ore_ends'], elapsed))
        state['index'] = index
        state['elapsed'] = elapsed - (state['ore_ends'][index - 1] if index else 0.0)
        if index != previous:
            self._apply_frame(native.get_control(host, fiber.native_path).asImage(), state['frames'][index])
            host._commit_native_dirty = True
        if completed:
            state['completed'] = True
            self._set_frame_animation_active(host, state, False)
            if state.get('on_end'):
                state['on_end']()


NativeOreImage = ImagePrimitive()
