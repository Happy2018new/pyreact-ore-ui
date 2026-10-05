# -*- coding: utf-8 -*-
"""Atlas metrics shared by layout and painting, including narrow Python 2."""
from __future__ import unicode_literals
from ._font_atlas import GLYPHS
from ._body_font import GLYPHS as BODY_GLYPHS


class OreFont(object):
    pixel = 'pixel'
    body = 'body'

CLOSING = frozenset('，。！？；：、）》】」』…,.!?;:%）')
OPENING = frozenset('（《【「『(')


class OreString(unicode):
    """Identify atlas text at the host's text measurement boundary."""
    def __new__(cls, value, fontFamily=OreFont.pixel, lineHeight=None):
        result = unicode.__new__(cls, value)
        result.font_family = fontFamily
        result.line_height = lineHeight
        return result


def text_value(value):
    if isinstance(value, unicode):
        return value
    if value is None:
        return u''
    return str(value).decode('utf8')


def characters(value):
    index = 0
    while index < len(value):
        char = value[index]
        index += 1
        if 0xd800 <= ord(char) <= 0xdbff and index < len(value) and 0xdc00 <= ord(value[index]) <= 0xdfff:
            char += value[index]
            index += 1
        yield char


def layout(value, font, width=None, spacing=None, font_family=None):
    font_family = font_family or getattr(value, 'font_family', OreFont.pixel)
    if spacing is None:
        spacing = 0.125 if font_family == OreFont.body else 0.2
    lines, widths = [[]], [0.0]
    for char in characters(value):
        if char == '\n':
            lines.append([])
            widths.append(0.0)
            continue
        data = (BODY_GLYPHS.get(char) if font_family == OreFont.body else None) or GLYPHS.get(char, GLYPHS.get('\ufffd', GLYPHS['?']))
        step = data[4] * font / 64.0 + spacing
        # Native sizes use floats; a measured single line must survive rounding.
        if width and lines[-1] and widths[-1] + step > width + max(0.0001, width * 0.000001):
            carry = []
            if char in CLOSING or lines[-1][-1][0] in OPENING:
                carry = [lines[-1].pop()]
                widths[-1] -= carry[0][1][4] * font / 64.0 + spacing
            lines.append(carry)
            widths.append(sum(item[1][4] * font / 64.0 + spacing for item in carry))
        lines[-1].append((char, data))
        widths[-1] += step
    pieces = []
    for row, line in enumerate(lines):
        x = 0.0
        for unused, data in line:
            pieces.append((data, row, x))
            x += data[4] * font / 64.0 + spacing
    return pieces, widths
