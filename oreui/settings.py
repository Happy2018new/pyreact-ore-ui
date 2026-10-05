# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""International Ore navigation, setting rows and joined choice controls."""
from functools import partial
from ..pyreact import (Component, Panel, Image, Style, Color, Position,
                      FlexDirection, AlignItems, JustifyContent, TextAlignment,
                      SafeArea, use_state, use_event, use_effect, native)
from .components import OreText, OreIcon, OreScrollView, OreDrawer
from ._button import NativeOreButton, NativeOreNavigationButton, NativeOrePressable
from ._joined import NativeOreJoinedRow
from ._scroll import NativeOreNavigationScrollView
from ._skins import state_skin
from .theme import OreSide
from ..pyreact.element import Element, normalize_children


class OreSettingLayout(object):
    inline = 'inline'
    stacked = 'stacked'
    field = 'field'


@Component
def OreDivider(style=None):
    return Panel(style=Style(width='100%', height=2).merge(style), children=[
        Image(color=Color(0x333334FF), style=Style(width='100%', height=1)),
        Image(color=Color(0x5A5B5CFF), style=Style(width='100%', height=1)),
    ])


@Component
def OreNavigationItem(label='', icon=None, selected=False, disabled=False,
                      onClick=None, style=None):
    return NativeOreNavigationButton(style=Style(width='100%', height=24, paddingHorizontal=8,
        flexDirection=FlexDirection.row, gap=4, alignItems=AlignItems.center,
        justifyContent=JustifyContent.flex_start).merge(style),
        buttonBuilder=state_skin('navigation', selected, disabled, (0, 0, 0, 0)),
        onClick=None if disabled else onClick, children=[
            OreIcon(name=icon, size=12) if icon else None,
            OreText(content=label, fontSize=8, color=Color(0x8B8B8EFF) if disabled else Color(0xFFFFFFFF),
                    style=Style(flex=1)),
        ])


@Component
def OreNavigationGroup(title='', children=None, style=None):
    return Panel(style=Style(width='100%').merge(style), children=[
        Panel(style=Style(width='100%', height=23, paddingHorizontal=8, paddingTop=10, paddingBottom=5,
              justifyContent=JustifyContent.flex_end), children=OreText(
                  content=title, fontSize=7, color=Color(0xD0D1D4FF))) if title else None,
        Panel(style=Style(width='100%', height=2), children=[
            Image(color=Color(0x1D1E1FFF), style=Style(width='100%', height=1)),
            Image(color=Color(0x454647FF), style=Style(width='100%', height=1)),
        ]) if title else None,
        children,
    ])


@Component
def OreSettingsRow(title='', description='', valueText='', children=None,
                   layout=OreSettingLayout.inline, disabled=False, divider=True,
                   style=None):
    color = Color(0xB1B2B5FF) if disabled else Color(0xFFFFFFFF)
    caption = OreText(content=description, fontSize=7, color=Color(0xD0D1D4FF),
                      style=Style(width='100%')) if description else None
    heading = OreText(content=title, fontSize=8, color=color,
        style=Style(flex=1, marginBottom=-4 if layout == OreSettingLayout.field else -2))
    if layout == OreSettingLayout.inline:
        body = Panel(style=Style(width='100%', minHeight=20, flexDirection=FlexDirection.row,
            gap=8, alignItems=AlignItems.center), children=[
                Panel(style=Style(flex=1), children=[heading, caption]), children,
            ])
    else:
        body = Panel(style=Style(width='100%'), children=[
            Panel(style=Style(width='100%', flexDirection=FlexDirection.row,
                alignItems=AlignItems.center, gap=6), children=[heading,
                    OreText(content=valueText, fontSize=8, color=color) if valueText else None]),
            caption if layout == OreSettingLayout.stacked else None,
            Panel(style=Style(width='100%', marginTop=6 if layout == OreSettingLayout.stacked else 3),
                  children=children),
            Panel(style=Style(width='100%', marginTop=3), children=caption)
            if layout == OreSettingLayout.field and description else None,
        ])
    return Panel(style=Style(width='100%').merge(style), children=[
        Panel(style=Style(width='100%', paddingHorizontal=12, paddingVertical=6), children=body),
        OreDivider() if divider else None,
    ])


@Component
def OreSettingsSection(title='', description='', children=None, style=None):
    # A run of setting rows owns one light opening edge and one dark closing
    # edge. Keep row keys/refs intact and never mutate the caller's Elements.
    items = normalize_children(children)
    grouped = []
    for index, child in enumerate(items):
        if child.comp_type is not OreSettingsRow:
            grouped.append(child)
            continue
        first = index == 0 or items[index - 1].comp_type is not OreSettingsRow
        last = index == len(items) - 1 or items[index + 1].comp_type is not OreSettingsRow
        if first:
            grouped.append(Image(color=Color(0x5A5B5CFF), style=Style(width='100%', height=1)))
        props = dict(child.props)
        if last:
            props['divider'] = False
        grouped.append(Element(child.comp_type, props, child.style, child.children, child.key, child.ref))
        if last:
            grouped.append(Image(color=Color(0x333334FF), style=Style(width='100%', height=1)))
    return Panel(style=Style(width='100%').merge(style), children=[
        Panel(style=Style(width='100%', paddingHorizontal=12, paddingTop=12,
              paddingBottom=8), children=[
                  OreText(content=title, fontSize=8),
                  OreText(content=description, fontSize=7, color=Color(0xD0D1D4FF),
                          style=Style(width='100%')) if description else None,
              ]) if title or description else None,
        grouped,
    ])


@Component
def OreSegmentedControl(options, value, onChange=None, disabled=False,
                        disabledOptions=None, style=None):
    disabledOptions = disabledOptions or ()
    return NativeOreJoinedRow(style=Style(width='100%', flexDirection=FlexDirection.row).merge(style), children=[
        NativeOrePressable(key='ore_segment_' + str(index),
            style=Style(flex=1, height=30, paddingHorizontal=3, gap=4,
                        marginLeft=-1 if index else 0, flexDirection=FlexDirection.row),
            buttonBuilder=state_skin('segment', option[1] == value,
                disabled or option[1] in disabledOptions,
                (2, 2, 4, 2) if option[1] == value else (2, 2, 2, 4),
                pressedSlices=(2, 2, 4, 2) if option[1] == value else (2, 2, 2, 2)),
            pressOffset=2 if option[1] != value and not disabled and option[1] not in disabledOptions else 0,
            onClick=partial(onChange, option[1]) if onChange and not disabled and option[1] not in disabledOptions else None,
            children=[Panel(style=Style(flexDirection=FlexDirection.row, gap=4,
                        alignItems=AlignItems.center, marginTop=3 if option[1] == value else -.5),
                children=[OreIcon(name=option[2], size=12,
                        color=Color(0xFFFFFFFF) if option[1] == value else Color(0x1E1E1FFF)) if len(option) > 2 else None,
                OreText(content=option[0], fontSize=8, textAlign=TextAlignment.center,
                        color=Color(0xFFFFFFFF) if option[1] == value else Color(0x1E1E1FFF))]),
                Image(color=Color(0xFFFFFFFF), style=Style(position=Position.absolute,
                      width=24, maxWidth='65%', height=1, bottom=1, left='50%', marginLeft=-12)) if option[1] == value else None,
            ]) for index, option in enumerate(options)
    ])


@Component
def OreIconButton(icon='cross_white', onClick=None, disabled=False, size=20,
                  color=None, style=None, iconSize=8, framed=False, light=False):
    return NativeOreButton(style=Style(width=size, height=size).merge(style),
        buttonBuilder=state_skin('pack' if framed else 'icon_light' if light else 'icon', disabled=disabled,
                                slices=(2, 2, 2, 2) if framed else (0, 0, 0, 0)),
        onClick=None if disabled else onClick, children=OreIcon(name=icon, size=iconSize, color=color))


@Component
def OreHeader(title='', onBack=None, onSocial=None, socialCount=0, onMenu=None, style=None):
    """Shared Ore page chrome: 22-unit face and two-unit lower depth."""
    return Panel(style=Style(width='100%', height=24).merge(style), children=[
        Image(color=Color(0xE6E8EBFF), style=Style(width='100%', height=22,
            flexDirection=FlexDirection.row, alignItems=AlignItems.center), children=[
            NativeOreButton(key='ore_header_back', onClick=onBack,
                buttonBuilder=state_skin('icon_light', slices=(0, 0, 0, 0)),
                style=Style(width=20, height=20, margin=1),
                children=OreIcon(name='chevron_left', size=7, color=Color(0x1E1E1FFF))),
            OreText(content=title, fontSize=10, color=Color(0x1E1E1FFF),
                textAlign=TextAlignment.center, style=Style(position=Position.absolute,
                    left=76.5 if onSocial else 22.5, right=75.5 if onSocial else 21.5, top=4.25)),
            Panel(style=Style(flex=1)),
            Panel(style=Style(width=68.5, height=22, flexDirection=FlexDirection.row), children=[
                Image(color=Color(0xA1A3A5FF), style=Style(width=1, height='100%'), children=
                    Image(color=Color(0xB4B5B7FF), style=Style(position=Position.absolute,
                        bottom=0, left=0, width=1, height=1))),
                Image(color=Color(0xFFFFFFFF), style=Style(width=1, height='100%')),
                NativeOreButton(key='ore_settings_social',
                    buttonBuilder=state_skin('icon_light', slices=(0, 0, 0, 0)), onClick=onSocial,
                    style=Style(flex=1, height=20, marginVertical=1, marginRight=.25, paddingRight=.25,
                        flexDirection=FlexDirection.row, gap=2),
                    children=[OreIcon(name='reference_social', color=Color(0x1E1E1FFF), size=12,
                            style=Style(marginTop=-1)),
                        OreText(content='社交 (%d)' % socialCount, fontSize=8, color=Color(0x1E1E1FFF),
                            style=Style(marginTop=1.5, left=-.25))]),
            ]) if onSocial else OreIconButton(key='ore_settings_menu', icon='settings',
                color=Color(0x1E1E1FFF), size=20, light=True, style=Style(margin=1), onClick=onMenu)
                if onMenu else Panel(style=Style(width=22)),
            Image(color=Color(0xEBEDEFFF), style=Style(position=Position.absolute,
                left=0, right=68.5 if onSocial else 0, bottom=0, height=1)),
            Image(color=Color(0xEBEDEFFF), style=Style(position=Position.absolute,
                right=0, width=66.5, bottom=0, height=1)) if onSocial else None,
        ]),
        Image(color=Color(0xB1B2B5FF), style=Style(width='100%', height=2)),
    ])


@Component
def OreSettingsScreen(title='设置', navigation=None, children=None, onClose=None, onSocial=None,
                      scrollKey='ore_settings_scroll', activeItem=None, style=None, scrollbarGutter=False):
    size, set_size = use_state(native.get_screen_size())
    menu, set_menu = use_state(False)
    use_event('ScreenSizeChanged', lambda _: set_size(native.get_screen_size()))
    wide = size[0] >= 320 and size[0] >= size[1]
    use_effect(partial(set_menu, False), [activeItem, wide])
    return Image(color=Color(0x48494AFF), style=Style(width='100%', height='100%').merge(style), children=[
        SafeArea(style=Style(width='100%', height='100%'), children=[
            OreHeader(title=title, onBack=onClose, onSocial=onSocial if wide else None,
                onMenu=partial(set_menu, not menu) if not wide else None),
            Panel(style=Style(width='100%', flex=1, flexDirection=FlexDirection.row), children=[
                Image(color=Color(0x313233FF), style=Style(width=max(0, int(size[0] / 3) - 1), height='100%'), children=[
                    NativeOreNavigationScrollView(key='ore_settings_navigation', style=Style(width='100%', height='100%'),
                                  children=Panel(style=Style(width='100%', paddingLeft=1), children=navigation)),
                    Image(color=Color(0x1E1E1FFF), style=Style(position=Position.absolute,
                          left=0, top=0, width=1, height='100%', zIndex=101)),
                    Image(color=Color(0x00000093), style=Style(position=Position.absolute,
                          left=1, right=0, top=0, height=1, zIndex=101)),
                ]) if wide else None,
                Image(color=Color(0x1E1E1FFF), style=Style(width=1, height='100%')) if wide else None,
                Panel(style=Style(flex=1, height='100%'), children=[
                    OreScrollView(key=scrollKey, style=Style(width='100%', height='100%'),
                                  scrollbarGutter=scrollbarGutter, children=children),
                    Image(color=Color(0x00000020), style=Style(position=Position.absolute,
                          left=0, right=0, top=0, height=1, zIndex=101)),
                ]),
            ]),
        ]),
        OreDrawer(key='ore_settings_directory', visible=menu and not wide, title=title, side=OreSide.left, onClose=partial(set_menu, False),
                  children=OreScrollView(key='ore_settings_directory_scroll', style=Style(width='100%', flex=1), children=navigation)),
    ])
