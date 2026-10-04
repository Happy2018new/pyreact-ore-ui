# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Ore social panel, player groups and local action menus."""
from functools import partial
from ..pyreact import (Component, Panel, Image, Style, Color, Position, FlexDirection,
                      AlignItems, JustifyContent, TextAlignment, AlignSelf, ImageAdaptionType, use_state)
from .typography import layout as text_layout, text_value
from .components import (OreText, OreIcon, OreImage, OreField, OreTabs,
                         OreScrollView, _ore_modal, _menu_row)
from ._button import NativeOreButton
from ._portal import modal_surface
from ._skins import state_skin
from .settings import OreIconButton


@Component
def OrePlayerRow(name='', status='离线', avatar='no_player_profile', selfPlayer=False,
                 online=False, onClick=None, onOptions=None, style=None):
    return Panel(style=Style(width='100%', height=36 if selfPlayer else 35,
        flexDirection=FlexDirection.row).merge(style), children=[
        NativeOreButton(key='ore_player_profile', buttonBuilder=state_skin('pack', slices=(2, 2, 2, 2)),
            onClick=onClick, style=Style(flex=1, height='100%', paddingVertical=4, paddingHorizontal=5, gap=4,
                flexDirection=FlexDirection.row, alignItems=AlignItems.center,
                justifyContent=JustifyContent.flex_start), children=[
            Image(color=Color(0x1E1E1FFF), style=Style(width=26, height=26, padding=1), children=[
                OreImage(name=avatar, style=Style(width=24, height=24)),
                Image(color=Color(0xFFFFFFFF), style=Style(position=Position.absolute,
                    right=-1, top=-1, width=6, height=6, padding=1), children=
                    Image(color=Color(0x6CC349FF), style=Style(width='100%', height='100%'))) if online else None,
            ]),
            Panel(style=Style(flex=1), children=[
                OreText(content=name + (' （你）' if selfPlayer else ''), fontSize=8, style=Style(marginTop=.5)),
                OreText(content=status, fontSize=7, color=Color(0xD0D1D4FF), style=Style(marginTop=-1.5)),
            ]),
        ]),
        NativeOreButton(key='ore_player_options', onClick=onOptions,
            buttonBuilder=state_skin('pack_action', slices=(2, 2, 2, 2)),
            style=Style(width=36, height='100%'), children=Image(src='textures/pyreact_ore/skin/more_vertical',
                style=Style(width=2, height=8)))
        if not selfPlayer else None,
    ])


@Component
def OrePlayerGroup(title='在线', count=0, online=False, children=None, style=None):
    color = Color(0xA0E081FF) if online else Color(0xD0D1D4FF)
    label = '%s (%d)' % (title, count)
    unused, widths = text_layout(text_value(label), 7)
    return Panel(style=Style(width='100%', marginTop=8).merge(style), children=[
        Image(color=Color(0x1E1E1FFF), style=Style(height=14, width=max(widths) + 10,
            maxWidth='100%', padding=1, alignSelf=AlignSelf.flex_start), children=
            Image(color=color, style=Style(height=13, paddingHorizontal=4), children=
                OreText(content=label, fontSize=7, color=Color(0x1E1E1FFF), style=Style(marginTop=1)))),
        Image(color=Color(0x1E1E1FFF), style=Style(width='100%', padding=1, marginTop=-4), children=[
            Image(color=color, style=Style(width='100%', height=3)),
            Panel(style=Style(width='100%', gap=1), children=children) if count else
            Image(color=Color(0x313233FF), style=Style(width='100%', height=27,
                alignItems=AlignItems.center, justifyContent=JustifyContent.center),
                children=OreText(content='没有好友在线' if online else '没有离线好友',
                    color=Color(0xB1B2B5FF), fontSize=7, style=Style(marginTop=2))),
        ]),
    ])


@Component
def OreActionMenu(visible=False, title='', actions=None, onClose=None, style=None):
    """Actions are (label, callback) pairs; callers own all account operations."""
    actions = actions or ()
    height = 38 + (27 if actions else 0) + max(0, len(actions) - 1) * 24.5 + (2 if len(actions) > 1 else 0)
    return _ore_modal(visible=visible, onClick=onClose,
        style=Style(zIndex=2000, alignItems=AlignItems.center, justifyContent=JustifyContent.center), children=[
            Image(color=Color(0x000000BB), style=Style(position=Position.absolute,
                left=0, top=0, width='100%', height='100%')),
            modal_surface(key='ore_action_surface',
                style=Style(width=238, maxWidth='90%', height=height, maxHeight='90%').merge(style), children=
                Image(color=Color(0x1E1E1FFF), style=Style(width='100%', height='100%', padding=1), children=[
                    Image(src='textures/pyreact_ore/skin/menu_header',
                        imageAdaption=ImageAdaptionType.origin_nine_slice, nineSliceData=(1, 1, 1, 1),
                        style=Style(width='100%', height=24, alignItems=AlignItems.center,
                            justifyContent=JustifyContent.center), children=[
                            OreText(content=title, textAlign=TextAlignment.center, fontSize=8, style=Style(marginTop=1)),
                            OreIconButton(key='ore_action_close', onClick=onClose, iconSize=7,
                                style=Style(position=Position.absolute, right=2, top=2)),
                        ]),
                    Image(color=Color(0x313233FF), style=Style(width='100%', flex=1, paddingHorizontal=4, paddingTop=5, paddingBottom=6),
                        children=OreScrollView(key='ore_action_scroll', style=Style(width='100%', flex=1), children=
                        Panel(style=Style(width='100%', gap=2), children=[
                        NativeOreButton(key='ore_action_0', buttonBuilder=state_skin('menu_action', slices=(2, 2, 2, 2)),
                            onClick=actions[0][1], style=Style(width='100%', height=27, paddingHorizontal=10,
                                justifyContent=JustifyContent.flex_start, alignItems=AlignItems.center,
                                flexDirection=FlexDirection.row), children=OreText(content=actions[0][0], fontSize=8,
                                    style=Style(marginTop=1))) if actions else None,
                        Image(color=Color(0x1E1E1FFF), style=Style(width='100%', padding=1), children=
                            Image(color=Color(0x8C8D90FF), style=Style(width='100%', padding=1), children=[
                            NativeOreButton(key='ore_action_' + str(index), buttonBuilder=partial(_menu_row, index),
                                onClick=callback, style=Style(width='100%', height=23 if index == len(actions) - 1 else 24,
                                    minHeight=23 if index == len(actions) - 1 else 24, flexShrink=0, paddingHorizontal=8,
                                    justifyContent=JustifyContent.flex_start, alignItems=AlignItems.center,
                                    flexDirection=FlexDirection.row), children=[OreText(content=label, fontSize=8,
                                        style=Style(marginTop=.5)),
                                    Image(color=Color(0x8C8D90FF), style=Style(position=Position.absolute,
                                        left=-8, right=-8, height=1, bottom=0)) if index < len(actions) - 1 else None])
                            for index, (label, callback) in enumerate(actions[1:], 1)])) if len(actions) > 1 else None,
                    ]))),
                ])),
        ])


@Component
def OreFriendsPanel(visible=False, onClose=None, children=None, query='', onSearch=None,
                    tab='friends', onTabChange=None, style=None):
    return _ore_modal(visible=visible, onClick=onClose,
        style=Style(alignItems=AlignItems.flex_end, justifyContent=JustifyContent.center), children=[
            Image(color=Color(0x000000B3), style=Style(position=Position.absolute,
                left=0, top=0, width='100%', height='100%')),
            modal_surface(key='ore_friends_surface',
                style=Style(width=188, maxWidth='90%', height='100%').merge(style), children=
                Image(color=Color(0x1E1E1FFF), style=Style(width='100%', height='100%', padding=1), children=
                    Image(color=Color(0x48494AFF), style=Style(width='100%', height='100%', padding=4, gap=4), children=[
                        Panel(style=Style(width='100%', height=24, flexDirection=FlexDirection.row, gap=4), children=[
                            OreField(key='ore_friends_search', value=query, onChange=onSearch, search=True,
                                placeholder='搜索人员', style=Style(flex=1)),
                            NativeOreButton(key='ore_friends_close', buttonBuilder=state_skin('pack', slices=(1, 1, 1, 1)),
                                onClick=onClose, style=Style(width=22, height=24),
                                children=OreIcon(name='cross_white', size=8)),
                        ]),
                        OreTabs(key='ore_friends_tabs', value=tab, onChange=onTabChange,
                            options=[('', 'friends', 'reference_friends'), ('', 'team', 'reference_team')], keyboardHints=True),
                        Image(color=Color(0x1E1E1FFF), style=Style(width='100%', flex=1, padding=1, marginTop=-4), children=
                            Image(color=Color(0x313233FF), style=Style(width='100%', height='100%'), children=
                                OreScrollView(style=Style(width='100%', height='100%'), children=
                                    Panel(style=Style(width='100%', paddingLeft=4, paddingRight=12, paddingVertical=4), children=children)))),
                    ]))),
        ])
