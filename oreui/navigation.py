# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Selection glints advance without mounting controls or scheduling layouts."""
from ..pyreact import Component, Panel, Style, Position
from .assets import asset
from .components import OreIcon
from ._image import ImagePrimitive


class NavigationGlintPrimitive(ImagePrimitive):
    def _sync_frame_animation(self, host, fiber, image, frames, next_props):
        selected = bool(next_props.get('selected'))
        previous = fiber.primitive_state.get('ore_glint_selected')
        changed = previous is False and selected
        fiber.primitive_state['ore_glint_selected'] = selected
        state = fiber.primitive_state.get('_image_frame_animation')
        props = dict(next_props, playing=changed or bool(state and state['playing']))
        ImagePrimitive._sync_frame_animation(self, host, fiber, image, frames, props)
        if changed:
            state = fiber.primitive_state['_image_frame_animation']
            state.update(index=state['initial_frame'], elapsed=0.0, last_time=None, completed=False)
            self._apply_frame(image, state['frames'][state['index']])
            self._set_frame_animation_active(host, state, True)


NativeNavigationGlint = NavigationGlintPrimitive()


@Component
def OreNavigationIcon(name, selected=False, animated=True, size=12, style=None):
    glint = asset('navigation_glint')
    return Panel(style=Style(width=size, height=size).merge(style), children=[
        OreIcon(name=name, size=size),
        # The first and last atlas frames are transparent. This one small image
        # stays mounted, and registers a frame callback only during playback.
        NativeNavigationGlint(key='ore_glint', selected=selected, src=glint['src'],
            frames=glint['frames'], frameDuration=glint['frameDuration'],
            frameDurations=glint['frameDurations'], loop=False,
            # Native siblings on the same layer can cover the glint with the
            # base icon even though its atlas frames continue to advance.
            style=Style(position=Position.absolute, left=0, top=0, width=size, height=size, zIndex=2))
        if animated else None,
    ])
