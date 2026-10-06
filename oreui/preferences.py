# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Settings notices, binding cells, storage meters and language choices."""
from functools import partial
from ..pyreact import (Component, Panel, Image, Style, Color, FlexDirection,
    AlignItems, TextAlignment, ButtonState)
from .components import OreText, OreIcon, OreProgress
from ._button import NativeOreButton, NativeOreRadioButton
from ._skins import state_skin


@Component
def OreStatusLabel(text='未实现', style=None):
    return Image(color=Color(0x2E6BE5FF), style=Style(paddingHorizontal=4,
        paddingVertical=2).merge(style), children=OreText(content=text,fontSize=8))


@Component
def OreNotice(text='', style=None):
    return Image(color=Color(0x1E1E1FFF), style=Style(width='100%',padding=10,
        flexDirection=FlexDirection.row,gap=10,alignItems=AlignItems.center).merge(style),children=[
        OreIcon(name='settings_notice',size=10),
        OreText(content=text,fontSize=8,style=Style(flex=1))])


@Component
def OreKeyBinding(value='未指派', icon=None, onClick=None, disabled=False, style=None):
    return NativeOreButton(buttonBuilder=state_skin('binding',disabled=disabled,slices=(1,2,1,1)),
        onClick=None if disabled else onClick,style=Style(width=120,height=24).merge(style),children=
        OreIcon(name=icon,size=16) if icon else OreText(content=value,fontSize=8,
            textAlign=TextAlignment.center,color=Color(0xFFFFFFFF if not disabled else 0x1E1E1FFF)))


@Component
def OreLanguageOption(title='', description='', selected=False, onClick=None, style=None):
    return Panel(style=Style(width='100%',paddingHorizontal=12).merge(style),children=NativeOreRadioButton(onClick=onClick,
        buttonBuilder=state_skin('radio_on' if selected else 'radio_off',slices=(0,0,0,0)),
        style=Style(width='100%',height=36,paddingLeft=18,
            flexDirection=FlexDirection.row,alignItems=AlignItems.center),children=[
            Panel(style=Style(flex=1),children=[OreText(content=title,fontSize=8),
                OreText(content=description,fontSize=7,color=Color(0xD0D1D4FF))])]))


@Component
def OreStorageMeter(title='本地存储', detail='', value=0., icon='settings_drive', style=None):
    return Image(color=Color(0x1E1E1FFF),style=Style(width='100%',padding=1).merge(style),children=
        Image(color=Color(0x313233FF),style=Style(width='100%',padding=8,
            flexDirection=FlexDirection.row,gap=6,alignItems=AlignItems.center),children=[
            OreIcon(name=icon,size=12) if icon else None,
            Panel(style=Style(flex=1,gap=1),children=[
                Panel(style=Style(width='100%',flexDirection=FlexDirection.row,alignItems=AlignItems.center),children=[
                    OreText(content=title,fontSize=8,style=Style(flex=1)),
                    OreText(content=detail,fontSize=7,color=Color(0xD0D1D4FF))]),
                OreProgress(value=value,color=Color(0x2E6BE5FF),style=Style(height=2))])]))
