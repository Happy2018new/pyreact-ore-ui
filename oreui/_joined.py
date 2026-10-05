# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Shared outer borders for player and resource-pack lists."""
from ..pyreact import Panel, Style
from ..pyreact.element import normalize_children


def joined_rows(children, expanded_spacing=False):
    rows = normalize_children(children)
    return [Panel(key=u'ore_joined_' + unicode(child.key) if child.key is not None else None, style=Style(width='100%',
                marginTop=(6 if expanded_spacing and rows[index - 1].props.get('expanded') else -1)
                if index else 0), children=child)
            for index, child in enumerate(rows)]
