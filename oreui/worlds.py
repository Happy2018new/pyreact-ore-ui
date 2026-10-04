# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""World preview with independent open and edit actions."""
from ..pyreact import Component, Panel, Image, Style, Color, FlexDirection, AlignItems, JustifyContent, Position
from .components import OreImage, OreText, OreIcon, OreButton
from .assets import OreVariant
from ._button import NativeOreButton
from ._skins import state_skin


@Component
def OreWorldCard(title='', subtitle='', mode='', image='world_demo_screen_big',
                 onOpen=None, onEdit=None, disabled=False, style=None):
    return Panel(style=Style(width='100%').merge(style), children=[
        NativeOreButton(key='ore_world_preview', onClick=None if disabled else onOpen,
            buttonBuilder=state_skin('pack', disabled=disabled, slices=(2, 2, 2, 2)),
            style=Style(width='100%', height=90, padding=1), children=[
                OreImage(name=image, style=Style(width='100%', height='100%')),
                Image(color=Color(0x313233FF), style=Style(position=Position.absolute,
                    left=1, bottom=1, paddingHorizontal=3), children=OreText(content=mode, fontSize=8)) if mode else None,
            ]),
        Panel(style=Style(width='100%', flexDirection=FlexDirection.row), children=[
            NativeOreButton(key='ore_world_open', onClick=None if disabled else onOpen,
                buttonBuilder=state_skin('pack', disabled=disabled, slices=(2, 2, 2, 2)),
                style=Style(flex=1, height=32, paddingHorizontal=5, alignItems=AlignItems.flex_start),
                children=[OreText(content=title, fontSize=8),
                          OreText(content=subtitle, fontSize=8, color=Color(0xD0D1D4FF)) if subtitle else None]),
            NativeOreButton(key='ore_world_edit', onClick=None if disabled else onEdit,
                buttonBuilder=state_skin('pack', disabled=disabled, slices=(2, 2, 2, 2)), style=Style(width=32, height=32),
                children=OreIcon(name='edit', size=12)),
        ]),
    ])


@Component
def OreWorldNavigation(image='world_demo_screen_big', onPlay=None, onRealms=None,
                       children=None, style=None):
    """World-edit sidebar preview and actions above the navigation entries."""
    return Panel(style=Style(width='100%').merge(style), children=[
        Panel(style=Style(width='100%', padding=8, gap=3), children=[
            Image(color=Color(0x1E1E1FFF), style=Style(width='100%', height=86, padding=1),
                children=OreImage(name=image, style=Style(width='100%', height='100%'))),
            OreButton(label='游戏', variant=OreVariant.primary, onClick=onPlay, style=Style(width='100%')),
            OreButton(label='在 Realms 上开始游戏', variant=OreVariant.realms, onClick=onRealms,
                style=Style(width='100%')),
            Panel(style=Style(width='100%', height=18, flexDirection=FlexDirection.row, gap=4,
                alignItems=AlignItems.center, justifyContent=JustifyContent.center), children=[
                OreIcon(name='information', color=Color(0xFFFFFFFF), size=9),
                OreText(content='禁用成就', fontSize=8)]),
        ]),
        children,
    ])
