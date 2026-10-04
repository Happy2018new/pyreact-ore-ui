# -*- coding: utf-8 -*-
"""Colors from Ore's palette; uses the host mod's single Pyreact runtime."""
from ..pyreact import Color
from ._catalog import PALETTE


class OreColors(object):
    background = Color(PALETTE['gray100'])
    surface = Color(PALETTE['gray90'])
    raised = Color(PALETTE['gray80'])
    border = Color(PALETTE['gray60'])
    text = Color(PALETTE['white'])
    muted = Color(PALETTE['gray40'])
    disabled = Color(PALETTE['gray50'])
    darkText = Color(PALETTE['gray100'])
    primary = Color(PALETTE['green30'])
    destructive = Color(PALETTE['red20'])


class OreTone(object):
    info = 'info'
    success = 'success'
    warning = 'warning'
    error = 'error'


class OreSide(object):
    left = 'left'
    right = 'right'


def palette_color(name):
    if name not in PALETTE:
        raise ValueError('Unknown Ore palette color: ' + str(name))
    return Color(PALETTE[name])
