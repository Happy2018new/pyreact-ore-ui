# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Interactive global Settings example, independent of real game preferences."""
from __future__ import unicode_literals
from functools import partial

from .pyreact import (Component, Panel, Image, Style, Color, FlexDirection, AlignItems,
    use_state, use_ref, navigator)
from .oreui import (OreSettingsScreen, OreNavigationGroup, OreNavigationItem,
    OreSettingsSection, OreSettingsRow, OreSettingLayout, OreSliderRow,
    OreSwitch, OreSegmentedControl, OreButton, OreField, OreImage, OreText,
    OreIcon, OreStatusLabel, OreNotice, OreKeyBinding, OreLanguageOption,
    OreStorageMeter, OreDialog, OreDropdown, OrePageCache)
from .settings_catalog import NAVIGATION, HEADINGS, PAGES, LANGUAGES


def initial_values(page):
    return dict((spec['title'], spec['value']) for group in PAGES.get(page, [])
                for spec in group['rows'] if spec['value'] is not None)


def slider_text(spec, value):
    if spec.get('display'):
        return spec['display'][max(0, min(len(spec['display']) - 1, int(value)))]
    steps = spec.get('steps', 1)
    ratio = value / float(steps - 1) if steps > 1 else value
    if ratio >= 1 and spec.get('endLabel'):
        return spec['endLabel']
    number = spec.get('minimum', 0) + ratio * (spec.get('maximum', 100) - spec.get('minimum', 0))
    return str(int(round(number))) + spec.get('unit', '%')


@Component
def ReplicaPage(page, saved, onSave):
    values, set_values = use_state(lambda: dict(saved or initial_values(page)))
    dialog, set_dialog = use_state(None)
    binding, set_binding = use_state('')
    reset_generation, set_reset_generation = use_state(0)

    def change(title, value):
        def update(current):
            result = dict(current)
            result[title] = value
            onSave(page, result)
            return result
        set_values(update)

    def reset():
        result = initial_values(page)
        set_values(result)
        onSave(page, result)
        set_reset_generation(lambda old: old + 1)
        set_dialog(None)

    def open_action(spec):
        set_dialog(spec)
        set_binding(values.get(spec['title'], ''))

    def confirm():
        if dialog.get('reset'):
            reset()
            return
        if dialog['kind'] in ('binding', 'macro'):
            change(dialog['title'], binding or '未指派')
        set_dialog(None)

    def render_row(spec):
        title = spec['title']; kind = spec['kind']
        value = values.get(title, spec['value'])
        disabled = spec.get('disabled', False) or (spec.get('enabledBy') and not values.get(spec['enabledBy']))
        common = dict(key=title, title=title, description=spec['description'], disabled=bool(disabled), compact=True)
        if kind == 'slider':
            return OreSliderRow(value=value, steps=spec.get('steps',1), formatValue=partial(slider_text,spec),
                onCommit=partial(change,title), sliderKey='preference_'+title, **common)
        if kind == 'toggle':
            return OreSettingsRow(children=OreSwitch(value=value,disabled=bool(disabled),onChange=partial(change,title),
                style=Style(top=-1,left=1)), **common)
        if kind == 'choices':
            return OreSettingsRow(layout=OreSettingLayout.stacked,children=OreSegmentedControl(
                options=[(text,i) for i,text in enumerate(spec['options'])],value=value,
                disabled=bool(disabled),disabledOptions=spec.get('disabledOptions'),onChange=partial(change,title)), **common)
        if kind == 'field':
            return OreSettingsRow(layout=OreSettingLayout.field,children=OreField(
                value=value,onChange=partial(change,title),placeholder=title),**common)
        if kind == 'dropdown':
            return OreSettingsRow(layout=OreSettingLayout.field,children=OreDropdown(
                title=title,value=value,options=[(text,i) for i,text in enumerate(spec['options'])],
                onChange=partial(change,title)),**common)
        if kind in ('binding','controller_binding'):
            icon='controller_'+value if kind=='controller_binding' and value else None
            return OreSettingsRow(children=OreKeyBinding(value=value,icon=icon,
                disabled=kind=='controller_binding',onClick=partial(open_action,spec)), **common)
        if kind == 'macro':
            return Panel(key=title,style=Style(width='100%'),children=[
                OreSettingsRow(children=OreKeyBinding(value=value,onClick=partial(open_action,spec)), **common),
                OreSettingsRow(compact=True,children=OreField(placeholder='运行命令',disabled=value=='未指派',
                    value=values.get(title+'_command',''),onChange=partial(change,title+'_command')))])
        if kind == 'notice':
            return Panel(key=title,style=Style(width='100%',padding=4),children=OreNotice(text=title))
        if kind == 'touch_customize':
            return Panel(key=title,style=Style(width='100%'),children=[
                OreSettingsRow(divider=False,children=OreButton(label='自定义',disabled=True,style=Style(width=70,height=24)),**common),
                Panel(style=Style(width='100%',paddingHorizontal=12,paddingBottom=6),children=OreNotice(text='加载一个世界以自定义控件'))])
        if kind == 'touch_mode':
            description=[spec['description'],
                '使用方向键移动。拖动至其他任意位置可环顾四周。点击并按住方块可与它们进行互动。',
                '拖动摇杆进行移动。拖动至其他任意位置可环顾四周。瞄准十字线并使用按钮与方块进行互动。'][value]
            return OreSettingsRow(key=title,compact=True,children=Panel(style=Style(width='100%'),children=[
                Panel(style=Style(width='100%',flexDirection=FlexDirection.row,gap=8),children=[
                    Panel(style=Style(flex=1),children=[OreText(content=title,fontSize=8),
                        OreText(content=description,fontSize=7,lineHeight=10,color=Color(0xD0D1D4FF))]),
                    OreImage(name=['settings_touch_layout','settings_touch_dpad','settings_touch_crosshair'][value],
                        style=Style(width='46%',height=79))]),
                OreSegmentedControl(options=[(text,i) for i,text in enumerate(spec['options'])],value=value,
                    onChange=partial(change,title),style=Style(marginTop=6))]))
        if kind == 'storage':
            return Panel(key=title,style=Style(width='100%',padding=4),children=OreStorageMeter(
                title=title,detail='已使用 48 GB 个，共 300 GB 个',value=value))
        if kind == 'profile':
            return OreSettingsRow(key=title,compact=True,children=Panel(style=Style(width='100%',height=8,
                flexDirection=FlexDirection.row,gap=2,alignItems=AlignItems.center),children=[
                OreText(content=title,fontSize=8),OreIcon(name='settings_account',size=10),OreText(content=value,fontSize=8)]))
        if kind in ('version','log_path','identifiers'):
            return OreSettingsRow(children=OreButton(label='复制' if kind=='log_path' else '复制文本',
                style=Style(width=70,height=24),onClick=partial(open_action,spec)), **common)
        return OreSettingsRow(children=OreButton(label=spec.get('label','打开'),disabled=bool(disabled),
            style=Style(width=70,height=24),onClick=partial(open_action,spec)), **common)

    def visible(spec):
        condition=spec.get('visibleWhen')
        return not condition or values.get(condition[0]) in condition[1]

    def setting(spec):
        element=render_row(spec)
        if spec.get('nested'):
            return Image(key='nested_'+spec['title'],color=Color(0x313233FF),
                style=Style(width='100%'),children=element)
        return element

    if page=='language':
        content=Panel(style=Style(width='100%',paddingTop=7,paddingBottom=7),children=[
            OreLanguageOption(key='language_'+str(index),title=label,description=country,
                selected=values.get('language',26)==index,onClick=partial(change,'language',index))
            for index,(label,country) in enumerate(LANGUAGES)])
    else:
        content=[OreSettingsSection(key=page+'_'+str(index)+'_'+str(reset_generation),compact=True,
            title=group['title'],description=group['description'],children=[setting(spec) for spec in group['rows'] if visible(spec)])
            for index,group in enumerate(PAGES[page])]
    heading=HEADINGS[page]
    return Panel(style=Style(width='100%'),children=[
        OreSettingsSection(title=heading[0],description=heading[1],compact=True),content,
        OreDialog(visible=dialog is not None,title=dialog['title'] if dialog else '',
            message=('将本页设置恢复为原始值。' if dialog and dialog.get('reset') else
                '设置示例中的操作。' if dialog and dialog['kind'] not in ('binding','macro') else ''),
            onClose=partial(set_dialog,None),onConfirm=confirm,
            children=OreField(value=binding,onChange=set_binding,placeholder='输入按键名称')
                if dialog and dialog['kind'] in ('binding','macro') else None),
    ])


@Component
def OreSettingsReplica():
    page, set_page = use_state('accessibility')
    saved = use_ref({})

    def save(name, values):
        saved.current[name] = values

    navigation = Panel(style=Style(width='100%',paddingTop=9,paddingBottom=9),children=[
        OreNavigationGroup(key='settings_group_'+str(index),title=title,children=[
            OreNavigationItem(key='settings_page_'+name,label=label,icon='settings_'+name,
                selected=page==name,onClick=partial(set_page,name)) for label,name in entries])
        for index,(title,entries) in enumerate(NAVIGATION)])
    def render_page(name):
        return (Panel(style=Style(width='100%',padding=12,alignItems=AlignItems.flex_start),
            children=OreStatusLabel()) if name in ('party','subscriptions','resources') else
            ReplicaPage(key='settings_content_'+name,page=name,saved=saved.current.get(name),onSave=save))
    return OreSettingsScreen(title='设置',navigation=navigation,activeItem=page,
        scrollContent=False,onClose=navigator.pop,
        children=OrePageCache(activeKey=page,renderPage=render_page,cacheSize=8))
