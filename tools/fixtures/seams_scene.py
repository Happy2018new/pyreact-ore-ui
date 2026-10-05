# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Only the joined edges, icon tabs, world seam and header under repair."""
from functools import partial
from ore_demo.pyreact import Component, Image, Panel, Style, Color, Position, use_state, navigator
from ore_demo.oreui import OreSegmentedControl, OreTabs, OreWorldCard, OreHeader

events = []


def record(name):
    events.append(name)


@Component
def SeamScene(kind='segments', value=1, width=314.25):
    selected, change = use_state(value)
    if kind == 'segments':
        body = OreSegmentedControl(key='target', value=selected, onChange=change,
            options=[(u'生存', 0), (u'创造', 1), (u'冒险', 2)])
    elif kind in ('tabs', 'icons'):
        body = OreTabs(key='target', value=selected, onChange=change,
            keyboardHints=True,
            options=[('', 0, 'reference_friends'), ('', 1, 'reference_team')] if kind == 'icons' else
                [(u'世界 (7)', 0, 'ui_menu_worlds_tab'), ('Realms', 1, 'realms'),
                 (u'服务器', 2, 'ui_menu_server_tab')])
    elif kind == 'world':
        body = OreWorldCard(key='target', title=u'我的世界', subtitle='10/05/26',
            onOpen=partial(record,'open'), onEdit=partial(record,'edit'))
    else:
        body = OreHeader(key='target', title=u'游戏', onBack=partial(record,'back'),
            onSocial=partial(record,'social'))
    return Image(color=Color(0x48494AFF), style=Style(width='100%', height='100%'), children=
        Panel(key='bounds',style=Style(position=Position.absolute,left=0 if kind=='header' else 8,
            top=40,width=width),children=body))


def mount(kind, value=1, width=314.25):
    events[:] = []
    navigator.reset(SeamScene(kind=kind,value=value,width=width))
