# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Resource and social examples modeled on international world editing."""
from functools import partial
from .pyreact import Component, Panel, Image, Style, Color, AlignItems, JustifyContent
from .oreui import (OreSettingsRow, OreSettingsSection, OreSettingLayout, OreSwitch,
    OreTabs, OrePackGroup, OrePackRow, OrePlayerRow, OrePlayerGroup,
    OreButton, OreText, OreField)

PACKS = [('自然纹理', 'minecraft_texture_pack', '让方块和物品呈现自然的纹理。'),
         ('经典世界', 'grass_block', '保留熟悉的方块外观，适合建造与探索。'),
         ('清澈水面', 'world', '清澈的水面让你更容易观察水下的世界。'),
         ('柔和天空', 'world_demo_screen_big', '柔和的天空色彩与远处的风景。')]
PLAYERS = [('Steve', 'reference_steve_face'), ('Alex', 'icon_alex'), ('Ari', 'no_player_profile'),
           ('Kai', 'no_player_profile'), ('Efe', 'no_player_profile'), ('Sunny', 'no_player_profile')]


@Component
def DemoPacks(values, onChange):
    available = values['packTab'] == 'available'
    shown = [index for index in range(len(PACKS)) if available or index in values['activePacks']]

    def action(index):
        active = list(values['activePacks'])
        if index in active:
            active.remove(index)
        else:
            active.append(index)
        onChange('activePacks', active)

    return Panel(style=Style(width='100%'), children=[
        OreSettingsRow(title='共享包', description='系统要求玩家下载所有本地包，才能加入游戏。',
            children=OreSwitch(key='lab_pack_share', value=values['packShare'], onChange=partial(onChange, 'packShare'))),
        Panel(style=Style(width='100%', paddingHorizontal=6, paddingTop=4, paddingBottom=8, gap=4), children=[
            OreTabs(key='lab_pack_tabs', options=[('活跃', 'active'), ('可用', 'available')],
                value=values['packTab'], onChange=partial(onChange, 'packTab'), keyboardHints=True),
            OrePackGroup(key='lab_accordion', title='已拥有' if available else '活跃', count=len(shown),
                expanded=values['expanded'], onToggle=partial(onChange, 'expanded', not values['expanded']), children=[
                    OrePackRow(key='lab_pack_' + str(index), title=PACKS[index][0], thumbnail=PACKS[index][1],
                        description=PACKS[index][2], expanded=values['packOpen'] == index,
                        active=index in values['activePacks'],
                        onToggle=partial(onChange, 'packOpen', None if values['packOpen'] == index else index),
                        onAction=partial(action, index),
                        style=Style(marginBottom=6 if values['packOpen'] == index else 0)) for index in shown]),
            OreText(content='尚未激活资源包' if not shown else '', fontSize=7),
        ]),
    ])


@Component
def DemoPlayers(values, onOptions):
    query = values['friendQuery'].strip().lower()
    players = [entry for entry in PLAYERS if query in entry[0].lower()]
    if values['friendTab'] == 'team':
        return Panel(style=Style(width='100%', gap=8), children=[
            OreText(content='队伍', fontSize=8),
            OreText(content='与好友组队，一起探索世界。', fontSize=7),
            OreButton(label='创建队伍', onClick=partial(onOptions, '队伍')),
        ])
    return Panel(style=Style(width='100%'), children=[
        Image(color=Color(0x1E1E1FFF), style=Style(width='100%', height=16,
            alignItems=AlignItems.center, justifyContent=JustifyContent.center),
            children=OreText(content='玩家', fontSize=10)),
        OrePlayerRow(key='lab_player_self', name='Player', status='在 Minecraft 菜单中', online=True,
            selfPlayer=True, style=Style(marginTop=4)),
        OrePlayerGroup(title='在线', count=0, online=True),
        OrePlayerGroup(title='离线', count=len(players), children=[
            OrePlayerRow(key='lab_player_' + str(index), name=name, avatar=avatar,
                onOptions=partial(onOptions, name)) for index, (name, avatar) in enumerate(players)]),
    ])
