# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Expandable resource-pack rows with separate details and activation actions."""
from ..pyreact import (Component, Panel, Image, Style, Color, FlexDirection,
                      AlignItems, JustifyContent)
from .components import OreText, OreIcon, OreImage
from ._button import NativeOreButton
from ._skins import state_skin
from ._joined import joined_rows
from .typography import OreFont


@Component
def OrePackRow(title='', thumbnail='grass_block', description='', expanded=False,
               active=False, disabled=False, onToggle=None, onAction=None, style=None):
    return Panel(style=Style(width='100%').merge(style), children=[
        Image(color=Color(0x1E1E1FFF), style=Style(width='100%', height=36, padding=1,
              flexDirection=FlexDirection.row), children=[
            NativeOreButton(key='ore_pack_details', buttonBuilder=state_skin('pack_cell', disabled=disabled,
                slices=(1, 1, 1, 1)), onClick=None if disabled else onToggle,
                style=Style(flex=1, height='100%', padding=4, gap=4,
                    flexDirection=FlexDirection.row, alignItems=AlignItems.center,
                    justifyContent=JustifyContent.flex_start), children=[
                Image(color=Color(0x1E1E1FFF), style=Style(width=26, height=26, padding=1),
                    children=OreImage(name=thumbnail, style=Style(width=24, height=24))),
                OreText(content=title, fontSize=8, style=Style(flex=1, marginTop=1.75)),
                OreIcon(name='chevron_up' if expanded else 'chevron_down', size=4,
                    color=Color(0xFFFFFFFF), style=Style(marginHorizontal=8)),
            ]),
            NativeOreButton(key='ore_pack_action', buttonBuilder=state_skin('pack_options', disabled=disabled,
                slices=(1, 1, 1, 1)), onClick=None if disabled else onAction,
                style=Style(width=34, height='100%', paddingVertical=4, gap=1,
                    alignItems=AlignItems.center, justifyContent=JustifyContent.center), children=[
                OreIcon(name='remove_resource_pack' if active else 'add_resource_pack', size=12, color=Color(0xFFFFFFFF)),
                OreText(content='停用' if active else '激活', fontSize=5),
            ]),
        ]),
        Image(color=Color(0x1E1E1FFF), style=Style(width='100%', paddingHorizontal=1, paddingBottom=1), children=
            Image(color=Color(0x313233FF), style=Style(width='100%', padding=6), children=
                OreText(content=description, fontSize=7, fontFamily=OreFont.body, lineHeight=10,
                        style=Style(width='100%'))))
        if expanded else None,
    ])


@Component
def OrePackGroup(title='已拥有', count=None, expanded=False, onToggle=None,
                 children=None, style=None):
    return Panel(style=Style(width='100%').merge(style), children=[
        Image(color=Color(0x1E1E1FFF), style=Style(width='100%', padding=1), children=
        NativeOreButton(key='ore_pack_group_toggle', buttonBuilder=state_skin('pack_group', slices=(1, 1, 1, 1)),
            onClick=onToggle, style=Style(width='100%', height=22, paddingLeft=8, paddingRight=10,
                flexDirection=FlexDirection.row, gap=4, alignItems=AlignItems.center,
                justifyContent=JustifyContent.flex_start), children=[
                OreText(content=title, fontSize=8, style=Style(marginTop=.5)),
                OreText(content='(%d)' % count, fontSize=8, color=Color(0xB1B2B5FF),
                        style=Style(marginTop=.5)) if count is not None else None,
                Panel(style=Style(flex=1)),
                OreIcon(name='chevron_up' if expanded else 'chevron_down', size=4, color=Color(0xFFFFFFFF)),
            ])),
        Panel(style=Style(width='100%'), children=joined_rows(children, expanded_spacing=True)) if expanded else None,
    ])
