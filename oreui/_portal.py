# -*- coding: utf-8 -*-
"""Mount overlay children at the render root, outside native scroll clipping."""
from ..pyreact import (Component, Panel, Style, Position,
                      AlignItems, JustifyContent, native, use_event, use_state)
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
    revision, set_revision = use_state(0)

    def on_resize(args):
        set_revision(lambda value: value + 1)

    use_event('ScreenSizeChangedClientEvent', on_resize, active=visible)
    if not visible:
        return None
    width, height = native.get_screen_size()
    # The portal mounts this panel directly at the screen origin. The guard
    # runs after content layout so its holes use current native rectangles.
    return Panel(style=Style(zIndex=1000).merge(style).merge(Style(
        position=Position.absolute, left=0, top=0, width=width, height=height)),
        children=normalize_children(children) + [_shield(onClick, backdrop=True)])
