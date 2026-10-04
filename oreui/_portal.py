# -*- coding: utf-8 -*-
"""Mount overlay children at the render root, outside native scroll clipping."""
from ..pyreact import (Component, Panel, Style, Position,
                      AlignItems, JustifyContent, native, use_effect, use_ref, use_event, use_state)
from ..pyreact.element import normalize_children
from ..pyreact.primitives import PanelPrimitive
from ._shield import NativeOreSurface, NativeOreShield


class PortalPrimitive(PanelPrimitive):
    def children_path(self, native_path, host=None):
        return getattr(host, '_root_path', '/root')

    def apply_children(self, host, node, apply_func):
        for child in node.children:
            apply_func(child, host, 0.0, 0.0, node.visual_scale_x, node.visual_scale_y)
        return True


NativeOrePortal = PortalPrimitive()


def _shield(on_click=None, backdrop=False):
    return NativeOreShield(style=Style(position=Position.absolute, left=0, top=0,
        width='100%', height='100%', zIndex=0),
        backdrop=backdrop, onClick=on_click)


def modal_surface(style=None, children=None, **props):
    """Block blank-surface clicks without making a button the input ancestor.

    The trailing guard measures input rectangles after child layout and leaves
    them uncovered. Blank-surface clicks are swallowed without losing focus.
    """
    return NativeOreSurface(style=Style(zIndex=1, alignItems=AlignItems.center,
        justifyContent=JustifyContent.center).merge(style),
        children=normalize_children(children) + [_shield()], **props)


@Component
def OreModal(visible=True, style=None, onClick=None, children=None):
    anchor_ref = use_ref()
    origin, set_origin = use_state(None)
    revision, set_revision = use_state(0)

    def on_resize(args):
        set_revision(lambda value: value + 1)

    use_event('ScreenSizeChangedClientEvent', on_resize, active=visible)

    def measure_origin():
        if not visible or anchor_ref.current is None:
            return
        position = tuple(anchor_ref.current.GetGlobalPosition())
        if position != origin:
            set_origin(position)

    use_effect(measure_origin)
    if not visible:
        return None
    width, height = native.get_screen_size()
    # Portal children have root native parents but retain their logical mount
    # origin. Measure that origin exactly as the host Modal does, including
    # nested dropdowns and directory drawers, then cancel it in layout.
    ready = origin is not None
    x, y = origin if ready else (0, 0)
    return [Panel(ref=anchor_ref, style=Style(position=Position.absolute,
        left=0, top=0, width=0, height=0)),
        Panel(style=Style(zIndex=1000).merge(style).merge(Style(
            position=Position.absolute, left=-x, top=-y, width=width, height=height, visible=ready)),
            children=normalize_children(children) + [_shield(onClick, backdrop=True)])]
