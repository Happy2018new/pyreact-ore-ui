# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Runtime fixture: public components at the supplied reference crop sizes.

Thumbnails/avatars are test inputs cut from the reference, never UI skins.
No geometry or border overrides are applied to the components under test.
"""
from functools import partial
from ore_demo.pyreact import Component, Panel, Image, Style, Color, use_state, navigator
from ore_demo.oreui import (OrePlayerRow, OrePlayerGroup, OrePackRow, OrePackGroup,
    OreIconButton, OreSettingsScreen, OreSettingsSection, OreSettingsRow,
    OreSwitch, OreSlider, OreSettingLayout)
from ore_demo.oreui.assets import REFERENCE_ASSETS

events = []
PLAYERS = ['MC2020510', 'FamousQUJU', 'MinecraftTaiBai', 'Evoltohan']
PACKS = ['Clear Water', 'Cinematic Fog', 'Borderless Glass', 'Lower Grass']
DESCRIPTION = 'Adds borderless glass to Defined PBR. Be sure to place this pack above the base pack!\nVersion 1.2.0.'
for prefix in ('avatar', 'pack'):
    for index in range(4):
        name = 'boundary_%s_%d' % (prefix, index)
        REFERENCE_ASSETS[name] = dict(src='textures/boundary_fixture/' + name, size=(96, 96))


def record(action, index=None):
    events.append((action, index))


@Component
def BoundaryScene(page='players', disabled=False):
    opened, set_opened = use_state(2 if page == 'expanded' else None)
    group, set_group = use_state(True)
    slider, set_slider = use_state(2)
    if page == 'players':
        body = OrePlayerGroup(key='fixture_players', title=u'离线', count=4, children=[
            OrePlayerRow(key='fixture_player_' + str(i), name=name, avatar='boundary_avatar_' + str(i),
                onClick=partial(record, 'profile', i), onOptions=partial(record, 'options', i))
            for i, name in enumerate(PLAYERS)])
        width = 160
    elif page in ('packs', 'expanded'):
        shown = range(4) if page == 'packs' else (2, 3)
        body = OrePackGroup(key='fixture_packs', title=u'已拥有', count=12, expanded=group,
            onToggle=partial(set_group, not group), children=[
                OrePackRow(key='fixture_pack_' + str(i), title='Defined PBR - ' + PACKS[i],
                    thumbnail='boundary_pack_' + str(i), expanded=opened == i, description=DESCRIPTION,
                    disabled=disabled, onToggle=partial(set_opened, None if opened == i else i),
                    onAction=partial(record, 'activate', i)) for i in shown])
        width = 325.25
    elif page == 'close':
        body = OreIconButton(key='fixture_close', framed=True, iconSize=7,
            onClick=partial(record, 'close'), style=Style(width=22, height=24))
        width = 22
    elif page == 'sliders':
        body = OreSlider(key='fixture_slider', value=slider, onChange=set_slider, steps=5,
            tickLabels=(4, 5, 6, 7, 8), disabled=disabled)
        width = 312
    else:
        body = OreSettingsSection(title=u'文字转语音输出', description=u'调整你听到屏幕上文字的方式', children=[
            OreSettingsRow(key='fixture_first', title=u'UI 文本转语音输出', description=u'听取菜单选项和其他 UI 元素',
                children=OreSwitch(defaultValue=False)),
            OreSettingsRow(key='fixture_middle', title=u'聊天文本转语音输出', description=u'使用文字转语音功能听取聊天消息',
                children=OreSwitch(defaultValue=False)),
            OreSettingsRow(key='fixture_last', title=u'加入聊天说明', description=u'加入世界时获取如何开启聊天的提醒',
                children=OreSwitch(defaultValue=True)),
            OreSettingsSection(key='fixture_next', title=u'游戏', description=u'更改游戏中的视觉效果和摄像头移动的辅助功能选项',
                children=[OreSettingsRow(title=u'视角', children=OreSwitch())]),
        ])
        return OreSettingsScreen(title=u'设置', children=body)
    return Image(color=Color(0x48494AFF), style=Style(width='100%', height='100%', paddingLeft=8, paddingTop=32),
        children=Panel(key='fixture_content', style=Style(width=width), children=body))


def mount(page, disabled=False):
    events[:] = []
    navigator.reset(BoundaryScene(page=page, disabled=disabled))
