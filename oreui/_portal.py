# -*- coding: utf-8 -*-
"""Mount overlay children at the render root, outside native scroll clipping."""
from ..pyreact.primitives import PanelPrimitive


class PortalPrimitive(PanelPrimitive):
    def children_path(self, native_path, host=None):
        return getattr(host, '_root_path', '/root')

    def apply_children(self, host, node, apply_func):
        for child in node.children:
            apply_func(child, host, 0.0, 0.0, node.visual_scale_x, node.visual_scale_y)
        return True


NativeOrePortal = PortalPrimitive()
