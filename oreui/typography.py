# -*- coding: utf-8 -*-
"""Atlas metrics shared by layout and painting, including narrow Python 2."""
from __future__ import unicode_literals
from ._font_atlas import GLYPHS

CLOSING = frozenset('，。！？；：、）》】」』…,.!?;:%）')
OPENING = frozenset('（《【「『(')


class OreString(unicode):
    """Identify atlas text at the host's text measurement boundary."""


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


def layout(value, font, width=None):
    lines, widths = [[]], [0.0]
    for char in characters(value):
        if char == '\n':
            lines.append([])
            widths.append(0.0)
            continue
        data = GLYPHS.get(char, GLYPHS.get('\ufffd', GLYPHS['?']))
        step = data[4] * font / 64.0
        # Native sizes use floats; a measured single line must survive rounding.
        if width and lines[-1] and widths[-1] + step > width + max(0.0001, width * 0.000001):
            carry = []
            if char in CLOSING or lines[-1][-1][0] in OPENING:
                carry = [lines[-1].pop()]
                widths[-1] -= carry[0][1][4] * font / 64.0
            lines.append(carry)
            widths.append(sum(item[1][4] * font / 64.0 for item in carry))
        lines[-1].append((char, data))
        widths[-1] += step
    pieces = []
    for row, line in enumerate(lines):
        x = 0.0
        for unused, data in line:
            pieces.append((data, row, x))
            x += data[4] * font / 64.0
    return pieces, widths
