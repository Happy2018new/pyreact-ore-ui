# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Game-native layout following the supplied HTML atlas's visual hierarchy."""
import mod.client.extraClientApi as clientApi
from functools import partial
from .pyreact import (Component, Panel, Image, Style, Color, SafeArea, ScrollView,
                      FlexDirection, AlignItems, JustifyContent, Position,
                      ButtonState, use_state, use_event)
from .oreui import OreText, OreIcon, OreIconName, OreColors, OreDrawer, OreSide, OreScrollView as ScrollView
from .oreui._button import NativeOreButton


class AtlasColor(object):
    background = Color(0x313233FF)
    header = Color(0x48494AFF)
    surface = Color(0x48494AFF)
    inset = Color(0x1E1E1FFF)
    border = Color(0x58585AFF)
    accent = Color(0xFFFFFFFF)
    selected = Color(0x3C8527FF)
    muted = Color(0xD0D1D4FF)


def _is_wide(size):
    return size[0] >= 360 and size[0] >= size[1]


@Component
def AtlasCommand(label='', icon=None, selected=False, onClick=None, style=None):
    def builder(state):
        color = AtlasColor.selected if selected else AtlasColor.header
        if state == ButtonState.hover:
            color = Color(0x58585AFF)
        elif state == ButtonState.pressed:
            color = Color(0x101214FF)
        return Image(color=color)
    return NativeOreButton(style=Style(height=25, paddingHorizontal=7,
        flexDirection=FlexDirection.row, gap=5,
        alignItems=AlignItems.center, justifyContent=JustifyContent.flex_start).merge(style),
        buttonBuilder=builder, onClick=onClick, children=[
            Image(color=AtlasColor.accent, style=Style(position=Position.absolute,
                  left=-7, top=0, bottom=0, width=2)) if selected else None,
            OreIcon(name=icon, size=10) if icon else None,
            OreText(content=label, fontSize=8, color=OreColors.text)
            if label else None,
        ])


GROUPS = [('基础控件', ('buttons', 'selection', 'toggles', 'fields', 'dropdowns', 'sliders', 'feedback')),
          ('结构与导航', ('cards', 'navigation', 'containers', 'dialogs')),
          ('反馈与资源', ('messages', 'media', 'coverage'))]


@Component
def AtlasGrid(children, cellWidth=76, gap=6):
    game = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
    size, set_size = use_state(game.GetScreenSize())
    use_event('ScreenSizeChanged', lambda _: set_size(game.GetScreenSize()))
    available = size[0] - (157 if _is_wide(size) else 52)
    columns = max(1, int((available + gap) / (cellWidth + gap)))
    # Explicit rows keep auto-height deterministic in the host's measure pass.
    return Panel(style=Style(width='100%', gap=gap), children=[
        Panel(key=str(start), style=Style(width='100%', flexDirection=FlexDirection.row, gap=gap),
              children=children[start:start + columns])
        for start in range(0, len(children), columns)
    ])


@Component
def AtlasNavigation(pages, page, onChange, onWorkshop):
    labels = dict((value, label) for label, value in pages)
    return Panel(style=Style(width='100%', gap=3), children=[
        AtlasCommand(key='lab_page_overview', label='图鉴总览', selected=page == 'overview',
                     onClick=partial(onChange, 'overview')),
        [Panel(key=group, style=Style(width='100%', gap=2, marginTop=6), children=[
            OreText(content=group, fontSize=6, color=AtlasColor.muted,
                    style=Style(marginLeft=7, marginBottom=3)),
            [AtlasCommand(key='lab_page_' + value, label=labels[value], selected=value == page,
                          style=Style(width='100%'), onClick=partial(onChange, value))
             for value in values],
        ]) for group, values in GROUPS],
        Image(color=AtlasColor.border, style=Style(width='100%', height=1, marginVertical=6)),
        AtlasCommand(key='lab_workshop', label='创造工作台', onClick=onWorkshop),
    ])


@Component
def AtlasShell(pages, page, onPage, onReset, onClose, onWorkshop, events, latest,
               generation=0, children=None):
    game = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
    size, set_size = use_state(game.GetScreenSize())
    menu, set_menu = use_state(False)
    use_event('ScreenSizeChanged', lambda _: set_size(game.GetScreenSize()))
    wide = _is_wide(size)
    index = next(index for index, (_, value) in enumerate(pages) if value == page)
    label = pages[index][0]

    def choose(value):
        onPage(value)
        set_menu(False)

    navigation = AtlasNavigation(pages=pages, page=page, onChange=choose, onWorkshop=onWorkshop)
    return Image(color=AtlasColor.background, style=Style(width='100%', height='100%'), children=[
        SafeArea(style=Style(width='100%', height='100%'), children=[
            Image(color=Color(0xE6E8EBFF), style=Style(width='100%', height=34, paddingHorizontal=10,
                  flexDirection=FlexDirection.row, alignItems=AlignItems.center, gap=7), children=[
                OreText(content='Ore UI · 控件图鉴', fontSize=12,
                        color=OreColors.darkText, style=Style(flex=1)),
                AtlasCommand(key='lab_catalogue', label='目录', onClick=partial(set_menu, True)) if not wide else None,
                AtlasCommand(key='lab_reset', icon=OreIconName.back, label='重置', onClick=onReset),
                AtlasCommand(key='lab_close', icon=OreIconName.close, onClick=onClose,
                             style=Style(width=25)),
            ]),
            Image(color=AtlasColor.border, style=Style(width='100%', height=1)),
            Panel(style=Style(width='100%', flex=1, flexDirection=FlexDirection.row), children=[
                Image(color=AtlasColor.header, style=Style(width=96, height='100%', padding=6), children=[
                    ScrollView(key='lab_sidebar', style=Style(width='100%', flex=1), children=navigation),
                ]) if wide else None,
                Image(color=AtlasColor.border, style=Style(width=1, height='100%')) if wide else None,
                Panel(style=Style(flex=1, height='100%', paddingHorizontal=12 if wide else 8,
                                 paddingTop=9, gap=7), children=[
                    Panel(style=Style(width='100%', flexDirection=FlexDirection.row,
                                      alignItems=AlignItems.center, gap=5), children=[
                        Panel(style=Style(flex=1, gap=2), children=[
                            OreText(key='lab_page_title', content=label, fontSize=12),
                        ]),
                        AtlasCommand(key='lab_previous', icon='chevron_left',
                            onClick=partial(choose, pages[max(0, index - 1)][1]), style=Style(width=25)),
                        AtlasCommand(key='lab_next', icon='chevron_right',
                            onClick=partial(choose, pages[min(len(pages) - 1, index + 1)][1]), style=Style(width=25)),
                    ]),
                    ScrollView(key='lab_scroll_' + page + '_' + str(generation),
                               style=Style(width='100%', flex=1), children=Panel(
                               style=Style(width='100%', paddingBottom=8), children=children)),
                ]),
            ]),
            Image(color=AtlasColor.border, style=Style(width='100%', height=1)),
            Image(color=AtlasColor.inset, style=Style(width='100%', minHeight=20,
                  paddingHorizontal=10, paddingVertical=4, flexDirection=FlexDirection.row, gap=8), children=[
                OreText(key='lab_events', content='操作 %d 次 · %s' % (events, latest),
                        fontSize=6, color=AtlasColor.muted, style=Style(flex=1)),
            ]),
        ]),
        OreDrawer(key='lab_directory', visible=menu, title='控件目录', side=OreSide.left,
                  onClose=partial(set_menu, False), children=ScrollView(style=Style(width='100%', flex=1),
                  children=navigation)),
    ])
