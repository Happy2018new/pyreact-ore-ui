# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Shared outer borders for player and resource-pack lists."""
from ..pyreact import Panel, Style
from ..pyreact.element import normalize_children
from ..pyreact import native
from ..pyreact.primitives import PanelPrimitive
from ._button import PressablePrimitive
from math import floor


class JoinedRowPrimitive(PanelPrimitive):
    """Rasterize both ends of joined buttons on the same physical pixel grid.

    Fractional flex widths otherwise round the right edge of one nine-slice
    differently from its neighbor's left edge, exposing a one-pixel spur above
    the selected face. Keep the layout and hit rectangle on that same grid.
    """
    def apply_children(self, host, node, apply_func):
        game = getattr(host, '_ore_pixel_game', None)
        if game is None:
            game = native.clientApi.GetEngineCompFactory().CreateGame(native.clientApi.GetLevelId())
            host._ore_pixel_game = game
        logical = game.GetScreenSize()
        view = game.GetScreenViewInfo()
        pixels = float(view[0]) / logical[0] if logical[0] else 1.0
        control = native.get_control(host, node.fiber.native_path)
        origin = control.GetGlobalPosition()[0]
        scale = node.visual_scale_x
        for child in node.children:
            if scale > 0 and isinstance(child.fiber.comp_type, PressablePrimitive):
                left = origin + (child.frame_x - node.frame_x) * scale
                right = left + child.frame_w * scale
                left = floor(left * pixels + .5) / pixels
                right = floor(right * pixels + .5) / pixels
                child.frame_x = node.frame_x + (left - origin) / scale
                child.frame_w = (right - left) / scale
            apply_func(child, host, node.frame_x, node.frame_y,
                       node.visual_scale_x, node.visual_scale_y)
        return True


NativeOreJoinedRow = JoinedRowPrimitive()


def joined_rows(children, expanded_spacing=False):
    rows = normalize_children(children)
    # ModSDK accepts unicode paths for drawing, but does not dispatch button
    # callbacks below them. Keep generated native names as Python 2 bytes.
    return [Panel(key='ore_joined_' + unicode(child.key).encode('utf-8') if child.key is not None else None, style=Style(width='100%',
                marginTop=(6 if expanded_spacing and rows[index - 1].props.get('expanded') else -1)
                if index else 0), children=child)
            for index, child in enumerate(rows)]
