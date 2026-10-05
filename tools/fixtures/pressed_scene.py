# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Public components with recorded input data for held-pointer acceptance."""
from functools import partial
from ore_demo.pyreact import (Component, Panel, Image, Style, Color, FlexDirection,
                             Position, use_state, navigator)
from ore_demo.oreui import *
from ore_demo.oreui.assets import REFERENCE_ASSETS

events = []
for prefix in ('avatar', 'pack'):
    for index in range(4):
        name = 'boundary_%s_%d' % (prefix, index)
        REFERENCE_ASSETS[name] = dict(src='textures/boundary_fixture/' + name, size=(96, 96))


def record(action, value=None):
    events.append((action, value))


@Component
def PressedScene(kind='secondary', selected=False, disabled=False):
    value, set_value = use_state(0)
    expanded, set_expanded = use_state(False)
    background = 0x48494AFF
    width = 314.25
    if kind in ('primary', 'secondary', 'neutral', 'destructive', 'realms'):
        width = 220 if kind == 'secondary' else 128
        body = OreButton(key='target', label=u'放弃更改' if kind == 'secondary' else u'创建新世界',
            variant=kind, elevated=not selected, disabled=disabled,
            onClick=partial(record, 'button'), style=Style(width=width))
    elif kind == 'segments':
        body = OreSegmentedControl(key='target', options=[(u'生存', 0), (u'创造', 1), (u'冒险', 2)],
            value=value, onChange=set_value, disabled=disabled)
    elif kind in ('tabs', 'icon-tabs'):
        width = 325.25 if kind == 'tabs' else 180
        body = OreTabs(key='target', options=[(u'活跃', 0), (u'可用', 1)] if kind == 'tabs' else
            [('', 0, 'reference_friends'), ('', 1, 'reference_team')],
            value=1, onChange=partial(record, 'tab'), disabled=(0,1) if disabled else (), keyboardHints=True)
    elif kind == 'navigation':
        width = 166.75
        background = 0x313233FF
        body = Panel(key='target', style=Style(width='100%'), children=[
            OreNavigationItem(key='nav_' + str(i), label=label, icon=icon, selected=i == 1,
                onClick=partial(record, 'navigation', i), disabled=disabled)
            for i,(label,icon) in enumerate([(u'通用','general_icon'),(u'高级','advanced_icon'),(u'多人游戏','multiplayer_icon')])])
    elif kind == 'packs':
        width = 325.25
        body = OrePackGroup(key='target', title=u'已拥有', count=12, expanded=True,
            onToggle=partial(record, 'group'), children=[
                OrePackRow(key='pack_' + str(i), title='Defined PBR - ' + name,
                    thumbnail='boundary_pack_' + str(i), onToggle=partial(record, 'details', i),
                    onAction=partial(record, 'activate', i), disabled=disabled)
                for i,name in enumerate(['Clear Water','Cinematic Fog','Borderless Glass'])])
    elif kind == 'players':
        width = 160
        background = 0x313233FF
        body = OrePlayerGroup(key='target', title=u'离线', count=3, children=[
            OrePlayerRow(key='player_' + str(i), name=name, avatar='boundary_avatar_' + str(i),
                onClick=partial(record, 'profile', i), onOptions=partial(record, 'options', i))
            for i,name in enumerate(['MC2020510','FamousQUJU','MinecraftTaiBai'])])
    elif kind == 'group':
        width=325.25
        body=OrePackGroup(key='target',title=u'已拥有',count=12,expanded=False,onToggle=partial(record,'group'))
    elif kind == 'switch':
        width = 30
        body = OreSwitch(key='target', value=selected, disabled=disabled, onChange=partial(record,'switch'))
    elif kind in ('slider','slider-reference'):
        width=313
        body=OreSlider(key='target', value=.375 if kind=='slider-reference' else .5 if not selected else 2, steps=5 if selected else 1,
                       disabled=disabled, onChange=partial(record,'slider'))
    elif kind in ('field','search'):
        width=152 if kind=='search' else 312
        body=OreField(key='target', value='',placeholder=u'搜索人员' if kind=='search' else u'我的世界',
                      search=kind=='search',disabled=disabled,onChange=partial(record,'field'))
    elif kind=='dropdown':
        body=OreDropdown(key='target',title=u'模拟距离',defaultValue=4,disabled=disabled,
            options=[(u'%d个区块' % n,n) for n in (4,6,8,10,12)],onChange=partial(record,'dropdown'))
    elif kind=='icons':
        body=Panel(style=Style(flexDirection=FlexDirection.row,gap=8),children=[
            OreIconButton(key='icon',onClick=partial(record,'icon'),disabled=disabled),
            OreIconButton(key='framed',onClick=partial(record,'framed'),framed=True,iconSize=7,
                          disabled=disabled,style=Style(width=22,height=24)),
            Image(color=Color(0xE6E8EBFF),children=OreIconButton(key='light',light=True,
                onClick=partial(record,'light'),disabled=disabled,icon='chevron_left',color=Color(0x1E1E1FFF)))])
    elif kind=='extras':
        body=Panel(style=Style(width='100%',gap=4),children=[
            OreCheckbox(key='checkbox',value=selected,disabled=disabled,onChange=partial(record,'checkbox')),
            OreRadio(key='radio',options=[(u'生存','survival'),(u'创造','creative')],value='survival',
                disabled=('survival','creative') if disabled else (),onChange=partial(record,'radio')),
            OreListItem(key='list',title=u'选项',selected=selected,disabled=disabled,onClick=partial(record,'list')),
            OreAccordion(key='accordion',title=u'更多选项',expanded=expanded,onToggle=partial(set_expanded,not expanded)),
            OrePagination(key='pagination',page=2,pages=3,onChange=partial(record,'pagination')),
            OreHelp(key='help',label=u'说明',message=u'控件说明'),
            OreBanner(key='banner',message=u'更改已保存',onClose=partial(record,'banner'))])
    elif kind=='worlds':
        width=154
        body=OreWorldCard(key='world',title=u'我的世界',subtitle='10/05/26',mode=u'生存',
            onOpen=partial(record,'open'),onEdit=partial(record,'edit'),disabled=disabled)
    elif kind=='world-navigation':
        width=160
        body=OreWorldNavigation(key='world-navigation',onPlay=partial(record,'play'),onRealms=partial(record,'realms'))
    elif kind=='dialog':
        body=OreDialog(visible=True,title=u'是否要保存更改？',message=u'您有未保存的更改。',
            onConfirm=partial(record,'confirm'),onClose=partial(record,'close'))
    elif kind=='drawer':
        body=OreDrawer(visible=True,title=u'设置',onClose=partial(record,'close'))
    elif kind=='menu':
        body=OreActionMenu(visible=True,title=u'MC2020510 的选项',onClose=partial(record,'close'),
            actions=[(label,partial(record,'action',i)) for i,label in enumerate(
                [u'添加到收藏夹',u'静音',u'拉黑',u'举报',u'移除好友'])])
    elif kind=='friends':
        body=OreFriendsPanel(visible=True,onClose=partial(record,'close'),onSearch=partial(record,'search'),
            onTabChange=partial(record,'tab'),children=OrePlayerGroup(title=u'在线',count=0,online=True))
    else:
        return OreSettingsScreen(title=u'设置',onClose=partial(record,'back'),onSocial=partial(record,'social'))
    return Image(color=Color(background),style=Style(width='100%',height='100%'),children=
        Panel(key='bounds',style=Style(position=Position.absolute,left=8,top=40,width=width),children=body))


def mount(kind, selected=False, disabled=False):
    events[:] = []
    navigator.reset(PressedScene(kind=kind,selected=selected,disabled=disabled))


def interactive():
    from ore_demo.pyreact import host
    from ore_demo.pyreact.primitives import ButtonPrimitive, SliderPrimitive, InputPrimitive
    from ore_demo.oreui._input import ReadOnlyInputPrimitive
    h = host._ACTIVE_HOST[0]
    found = []
    def walk(fiber, keys):
        keys = keys + ([str(fiber.key)] if fiber.key is not None else [])
        if isinstance(fiber.comp_type, (ButtonPrimitive, SliderPrimitive, InputPrimitive, ReadOnlyInputPrimitive)):
            c = h.GetBaseUIControl(fiber.native_path)
            found.append((fiber,dict(keys=keys,path=fiber.native_path,type=type(fiber.comp_type).__name__,
                position=c.GetGlobalPosition(),size=c.GetSize(),clickable=bool(fiber.props.get('onClick')),
                press_offset=fiber.props.get('pressOffset',0),value=fiber.props.get('value'),steps=fiber.props.get('steps',1))))
        for child in fiber.child_fibers:
            walk(child,keys)
    if h is not None:
        walk(h._root_fiber,[])
    return found


def snapshot(index):
    from ore_demo.pyreact import host
    h=host._ACTIVE_HOST[0]
    items=interactive()
    if index>=len(items):
        return dict(missing=True,events=events)
    f,result=items[index]
    result['events']=list(events)
    result['held']=bool(f.primitive_state.get('ore_held'))
    for state in ('default','hover','pressed'):
        c=h.GetBaseUIControl(f.native_path+'/'+state)
        if c is not None:
            result[state]=dict(visible=c.GetVisible(),position=c.GetPosition(),size=c.GetSize())
    c=f.primitive_state.get('ore_press_content')
    if c is not None:
        result['content_position']=c.GetPosition()
    return result
