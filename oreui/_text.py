# -*- coding: utf-8 -*-
"""Render baked glyphs while preserving Label semantics and exact metrics."""
from ..pyreact import native, TextAlignment, Style, Position, FlexWrap
from ..pyreact.primitives import LabelPrimitive as BaseLabelPrimitive
from ..pyreact.style import resolve_padding, resolve_margin
from .typography import OreString, text_value, layout


def install_metrics():
    # The host has one shared text measurement entry. Dispatch only our unicode
    # subtype; ordinary host labels retain their native measurement behavior.
    if getattr(native.measure_text, '_ore_metrics', False):
        return
    original = native.measure_text

    def measure(host, text, font_scale=None, line_padding=None,
                text_alignment=None, shadow=None, max_width=None):
        if not isinstance(text, OreString):
            return original(host, text, font_scale, line_padding, text_alignment, shadow, max_width)
        font = (font_scale or 1.0) * 10.0
        unused, widths = layout(text, font, max_width)
        return max(widths), len(widths) * font * 1.5
    measure._ore_metrics = True
    native.measure_text = measure
    from ..pyreact import layout as host_layout
    original_width = host_layout._resolve_label_max_width

    def resolve_width(node):
        if isinstance(node.fiber.comp_type, LabelPrimitive):
            return max(1.0, available_width(node, host_layout))
        return original_width(node)
    host_layout._resolve_label_max_width = resolve_width


def intrinsic_width(node, host_layout):
    style = node.style or Style()
    width = style.get('width')
    if isinstance(width, (int, float)):
        return float(width)
    if node.measured_w is not None:
        return node.measured_w
    if isinstance(node.fiber.comp_type, LabelPrimitive):
        unused, widths = layout(node.fiber.props['content'], node.fiber.props['fontSize'])
        return max(widths)
    pad = resolve_padding(style)
    children = [intrinsic_width(child, host_layout) for child in node.children
                if child.position != Position.absolute]
    if not node.column:
        return sum(children) + max(0, len(children) - 1) * node.gap_main + pad[1] + pad[3]
    return max(children or [0]) + pad[1] + pad[3]


def available_width(node, host_layout):
    """Resolve percent and flex ancestors before the host's bottom-up measure."""
    style = node.style or Style()
    parent = node.parent
    parent_width = available_width(parent, host_layout) if parent else native.get_screen_size()[0]
    if parent:
        pad = resolve_padding(parent.style or Style())
        parent_width = max(0, parent_width - pad[1] - pad[3])
    width, explicit = host_layout._parse_dimension(style.get('width'), parent_width, None)
    if not explicit:
        width = parent_width
        if parent and not parent.column:
            flex = style.get('flex') or style.get('flexGrow') or 0
            if flex > 0:
                siblings = [child for child in parent.children if child.position != Position.absolute and not child.display_none]
                growers = [child for child in siblings if child.style and (child.style.get('flex') or child.style.get('flexGrow') or 0) > 0]
                minimum = sum(child.style.get('minWidth') or 0 for child in growers)
                gap = max(0, len(siblings) - 1) * parent.gap_main
                if parent.style and parent.style.get('flexWrap') == FlexWrap.wrap and minimum + gap > parent_width:
                    width = parent_width
                else:
                    occupied = sum(intrinsic_width(child, host_layout) for child in siblings if child not in growers)
                    total = sum(child.style.get('flex') or child.style.get('flexGrow') for child in growers)
                    width = max(0, parent_width - occupied - gap) * flex / total
            else:
                width = min(parent_width, intrinsic_width(node, host_layout))
    margin = resolve_margin(style, parent_width, None)
    return max(0, width - margin[1] - margin[3])


class LabelPrimitive(BaseLabelPrimitive):
    def apply_props(self, host, fiber, control, prev_props, next_props):
        install_metrics()
        BaseLabelPrimitive.apply_props(self, host, fiber, control,
            dict(prev_props, content='') if prev_props else None, dict(next_props, content=''))
        self.paint(host, fiber)

    def apply_layout(self, host, node):
        self.paint(host, node.fiber)

    def paint(self, host, fiber):
        state = fiber.primitive_state
        applied = state.get('_layout_applied')
        if not applied:
            return
        width, height = applied[:2]
        props = fiber.props
        font = props['fontSize'] * abs(state.get('_visual_scale', (1.0, 1.0))[1])
        color = props['color']
        alpha = state.get('_inherited_opacity', 1.0) * color.a
        signature = (props['content'], font, width, height, color.to_rgb_tuple(), alpha, props.get('textAlign'))
        if state.get('ore_text_paint') == signature:
            return
        state['ore_text_paint'] = signature
        pieces, widths = layout(text_value(props['content']), font, None if props.get('singleLine') else width)
        pool = state.setdefault('ore_glyph_pool', [])
        while len(pool) < len(pieces):
            name = 'ink%d' % len(pool)
            native.clone(host, '/root/ore_glyph_tmpl', fiber.native_path, name)
            pool.append(host.GetBaseUIControl(fiber.native_path + '/' + name))
        for index, patch in enumerate(pool):
            shown = index < len(pieces)
            patch.SetVisible(shown, False)
            if not shown:
                continue
            data, row, x = pieces[index]
            page, u, v, glyph_width, unused = data
            if props.get('textAlign') == TextAlignment.center:
                x += (width - widths[row]) / 2.0
            elif props.get('textAlign') == TextAlignment.right:
                x += width - widths[row]
            image = patch.asImage()
            image.SetSprite('textures/pyreact_ore/type/atlas_%03d' % page)
            image.SetSpriteUV((u, v))
            image.SetSpriteUVSize((glyph_width, 88))
            image.SetSpriteColor(color.to_rgb_tuple())
            patch.SetPosition((x, row * font * 1.5))
            patch.SetSize((glyph_width * font / 64.0, 88 * font / 64.0))
            patch.SetAlpha(alpha)
        host._commit_native_dirty = True


NativeOreText = LabelPrimitive()
NativeOreFieldText = LabelPrimitive()
NativeOreFieldText.template_path = '/root/ore_field_text_tmpl'
