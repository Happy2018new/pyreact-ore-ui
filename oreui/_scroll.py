# -*- coding: utf-8 -*-
"""Keep nested scroll content from expanding the outer native scroll range."""
from ..pyreact.primitives import ScrollViewPrimitive as BaseScrollViewPrimitive
from ..pyreact import native


class ScrollViewPrimitive(BaseScrollViewPrimitive):
    template_path = '/root/ore_scroll_tmpl'

    def _sync_scroll_view_branch(self, host, scroll_view_path, is_touch, width, height, show_scrollbar):
        BaseScrollViewPrimitive._sync_scroll_view_branch(self, host, scroll_view_path,
            is_touch, width, height, show_scrollbar)
        body = scroll_view_path + ('/panel' if is_touch else '/stack_panel')
        track = native.get_control(host, body + '/bar_and_track')
        if track is not None:
            native.set_size(track, (6.0, height))
            track.SetPosition((max(0.0, width - 6.0), 0.0))
        for suffix in ('/background_and_viewport', '/background_and_viewport/scrolling_view_port'):
            control = native.get_control(host, body + suffix)
            if control is not None:
                native.set_size(control, (max(0.0, width - (8 if show_scrollbar else 0)), height))

    def _scroll_content_size(self, node):
        right = node.frame_x + node.frame_w
        bottom = node.frame_y + node.frame_h
        for child in node.children:
            child_right, child_bottom = self._visible_bounds(child, True)
            right = max(right, child_right)
            bottom = max(bottom, child_bottom)
        return (max(0.0, right - node.frame_x), max(0.0, bottom - node.frame_y))

    def _visible_bounds(self, node, direct=False):
        if node.display_none:
            return (node.frame_x, node.frame_y)
        if isinstance(node.fiber.comp_type, BaseScrollViewPrimitive):
            return (node.frame_x + node.frame_w, node.frame_y + node.frame_h)
        height = node.frame_h
        # The host expands the direct auto-height content to its descendants'
        # content_h. Use the measured height and actual children at this boundary.
        if direct and node.style.get('height') is None:
            height = node.measured_h or 0.0
        right = node.frame_x + node.frame_w
        bottom = node.frame_y + height
        for child in node.children:
            child_right, child_bottom = self._visible_bounds(child)
            right = max(right, child_right)
            bottom = max(bottom, child_bottom)
        return (right, bottom)


NativeOreScrollView = ScrollViewPrimitive()
