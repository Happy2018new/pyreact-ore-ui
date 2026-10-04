# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Same-text reference fixtures, assembled exclusively from public controls."""
from .pyreact import Component, Image, Panel, Style, Color, Position, use_state
from .oreui import (OreSegmentedControl, OreField, OreNavigationGroup,
                    OreNavigationItem, OreSlider, OreSwitch, OreTabs, OreDropdown,
                    OrePlayerGroup, OrePlayerRow, OreActionMenu, OrePackRow, OrePackGroup)


@Component
def OreReferenceFixture(kind='segment', selected=True, disabled=False):
    value, set_value = use_state(0)
    if kind == 'segment':
        control = OreSegmentedControl(key='reference_control', style=Style(width=313),
            options=[('3 秒', 0), ('10 秒（默认值）', 1), ('30 秒', 2)], value=value, onChange=set_value)
    elif kind == 'field':
        control = OreField(key='reference_control', value='我的世界', style=Style(width=312))
    elif kind == 'search':
        control = OreField(key='reference_control', placeholder='搜索人员', search=True, style=Style(width=152))
    elif kind == 'navigation':
        control = OreNavigationGroup(key='reference_control', title='通用', style=Style(width=160), children=[
            OreNavigationItem(key='reference_first', label='通用', icon='general_icon', selected=value == 1,
                onClick=lambda: set_value(1)),
            OreNavigationItem(key='reference_second', label='视频', icon='reference_video', selected=value == 2,
                onClick=lambda: set_value(2)),
            OreNavigationItem(key='reference_selected', label='音频', icon='reference_audio', selected=value == 0,
                onClick=lambda: set_value(0)),
            OreNavigationItem(key='reference_last', label='帐户', icon='reference_account', selected=value == 3,
                onClick=lambda: set_value(3)),
        ])
    elif kind == 'switch':
        control = OreSwitch(key='reference_control', value=selected, disabled=disabled)
    elif kind == 'slider':
        control = OreSlider(key='reference_control', value=1 if disabled else .5,
            steps=5 if disabled else 1, disabled=disabled, style=Style(width=312))
    elif kind == 'tabs':
        control = OreTabs(key='reference_control', style=Style(width=324), value='available',
            options=[('活跃', 'active'), ('可用', 'available')], keyboardHints=True)
    elif kind == 'players':
        control = OrePlayerGroup(key='reference_control', title='在线', count=0, online=True,
            style=Style(width=160, marginTop=0))
    elif kind == 'pack-group':
        control = OrePackGroup(key='reference_control', title='已拥有', count=12, expanded=False,
            style=Style(width=324))
    elif kind == 'self-player':
        control = OrePlayerRow(key='reference_control', name='Happy2018new', status='在 Minecraft 菜单中',
            avatar='reference_steve_face',
            selfPlayer=True, online=True, style=Style(width=160))
    elif kind == 'action-menu':
        return Image(color=Color(0x48494AFF), style=Style(width='100%', height='100%'), children=
            OreActionMenu(visible=True, title='MC2020510 的选项',
                actions=[(label, lambda: None) for label in
                    ('添加到收藏夹', '静音', '拉黑', '举报', '移除好友')]))
    else:
        control = OreDropdown(key='reference_control', title='模拟距离', defaultValue=4,
            options=[('%d 个区块' % n, n) for n in (4, 6, 8, 10, 12)], style=Style(width=312))
    return Image(color=Color(0x313233FF) if kind in ('navigation', 'players', 'self-player') or disabled else Color(0x48494AFF),
        style=Style(width='100%', height='100%'), children=
        Panel(key='reference_bounds', style=Style(position=Position.absolute, left=8, top=40), children=control))
