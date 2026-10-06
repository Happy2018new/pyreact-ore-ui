# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Bounded, lazily mounted pages for frequently switched settings categories."""
from collections import OrderedDict
from ..pyreact import Component, Panel, Style, Position, use_ref
from ._scroll import ScrollViewPrimitive
from ..pyreact import native, layout as host_layout


def _content_version(fiber):
    # Retain Element objects, not ids which Python may reuse after a render.
    result = []
    pending = list(fiber.child_fibers)
    while pending:
        child = pending.pop()
        result.append(child.element)
        pending.extend(child.child_fibers)
    return tuple(result)


def _install_page_layout():
    """Exclude inactive cached pages from the host's global layout walk.

    Their native geometry remains intact. Activation invalidates it when the
    parent viewport or retained content changed. Ordinary ScrollViews keep the
    framework's original behavior, including nested scroll measurement.
    """
    if getattr(host_layout._collect, '_ore_pages', False):
        return
    original = host_layout._collect

    def collect(fiber, opacity):
        if isinstance(fiber.comp_type, PageScrollPrimitive) and not fiber.props.get('active'):
            return []
        nodes = original(fiber, opacity)
        for node in nodes:
            if isinstance(node.fiber.comp_type, PageScrollPrimitive) and not node.fiber.props.get('active'):
                # Layout-only exclusion: Style.visible controls native display.
                node.display_none = True
        return nodes
    collect._ore_pages = True
    host_layout._collect = collect


class PageScrollPrimitive(ScrollViewPrimitive):
    def apply_props(self, host, fiber, control, prev_props, next_props):
        ScrollViewPrimitive.apply_props(self, host, fiber, control, prev_props, next_props)
        if prev_props is not None and next_props.get('active') and not prev_props.get('active'):
            if fiber is not None:
                viewport = native.get_size(host, fiber.native_parent_path)
                version = (viewport, _content_version(fiber))
                if fiber.primitive_state.get('ore_page_layout') != version:
                    host._commit_layout_dirty = True
            if next_props.get('resetScroll'):
                self.scroll_to_top(control)

    def apply_layout(self, host, node):
        ScrollViewPrimitive.apply_layout(self, host, node)
        fiber = node.fiber
        fiber.primitive_state['ore_page_layout'] = (
            native.get_size(host, fiber.native_parent_path), _content_version(fiber))


NativePageScroll = PageScrollPrimitive()


@Component
def OrePageCache(activeKey, renderPage, cacheSize=8, resetScroll=True,
                 scrollbarGutter=False, style=None):
    """Keep at most cacheSize visited pages, evicting the least recently used.

    renderPage(key) is called only on first visit or after eviction. Each page
    owns its state and scroll container. Hidden pages retain effects, so pause
    any background work explicitly in applications that need it. Close/unmount
    this component to dispose every cached page. Use a new key to invalidate it.
    """
    if isinstance(cacheSize, bool) or not isinstance(cacheSize, (int, long)) or cacheSize < 1:
        raise ValueError('OrePageCache.cacheSize must be a positive integer')
    _install_page_layout()
    pages = use_ref(OrderedDict())
    order = use_ref([])
    if activeKey not in pages.current:
        pages.current[activeKey] = Panel(style=Style(width='100%',
            paddingRight=10 if scrollbarGutter else 0), children=renderPage(activeKey))
        order.current.append(activeKey)
    elif not order.current or order.current[-1] != activeKey:
        order.current.remove(activeKey)
        order.current.append(activeKey)
    while len(pages.current) > cacheSize:
        del pages.current[order.current.pop(0)]
    # Insertion order is stable: activating a page must not reorder siblings,
    # which would make Pyreact invalidate the whole layout on every switch.
    return Panel(style=Style(width='100%', height='100%').merge(style), children=[
        NativePageScroll(key=name, active=name == activeKey, resetScroll=resetScroll,
            style=Style(position=Position.absolute, left=0, top=0, width='100%', height='100%',
                        visible=name == activeKey), children=content)
        for name, content in pages.current.items()])
