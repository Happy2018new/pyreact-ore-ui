# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Interactive public-component playground; no world or server operations."""
from functools import partial
from .pyreact import (Component, Panel, Image, Style, SafeArea, ScrollView, Modal,
                      FlexDirection, FlexWrap, AlignItems, JustifyContent,
                      use_state, navigator)
from .oreui import (OreButton, OreCard, OreCheckbox, OreDialog, OreIcon, OreImage, OreTone,
                    OreListItem, OreProgress, OreSlider, OreTabs, OreText,
                    OreColors, OreVariant, OreIconName, OreState, button_asset)
from .oreui import OreDrawer, OreField, OreDropdown, OreSwitch, OreBanner, OreSide, OreScrollView as ScrollView
from .gallery import OreGallery
from .lab_samples import (Section, LabToggles, LabFields, LabDropdowns, LabCards,
                          LabNavigation, LabContainers, LabMessages, LabAssets)
from .lab_chrome import AtlasShell, AtlasGrid


class LabPage(object):
    overview = 'overview'
    buttons = 'buttons'
    selection = 'selection'
    sliders = 'sliders'
    feedback = 'feedback'
    media = 'media'
    dialogs = 'dialogs'
    toggles = 'toggles'
    fields = 'fields'
    dropdowns = 'dropdowns'
    cards = 'cards'
    navigation = 'navigation'
    containers = 'containers'
    messages = 'messages'
    coverage = 'coverage'


PAGES = [('总览', LabPage.overview), ('按钮', LabPage.buttons), ('选项', LabPage.selection),
         ('开关与单选', LabPage.toggles), ('文本与表单', LabPage.fields),
         ('下拉菜单', LabPage.dropdowns), ('滑块', LabPage.sliders), ('进度', LabPage.feedback),
         ('卡片与列表', LabPage.cards), ('导航与分页', LabPage.navigation),
         ('容器与滚动', LabPage.containers), ('消息与文字', LabPage.messages),
         ('弹窗与抽屉', LabPage.dialogs), ('资源图鉴', LabPage.media), ('组件目录', LabPage.coverage)]
VARIANTS = [('主要', OreVariant.primary), ('次要', OreVariant.secondary),
            ('中性', OreVariant.neutral), ('删除', OreVariant.destructive),
            ('Realms', OreVariant.realms)]


@Component
def LabButtonStates():
    return Section(title='按钮状态', children=AtlasGrid(gap=12, children=[
        Panel(key=variant + str(elevated), style=Style(width=76, gap=4), children=[
            OreText(content=label + (' · 立体' if elevated else ' · 平面'), fontSize=7,
                    color=OreColors.muted, style=Style(width='100%', marginBottom=3)),
            [Panel(key=state, style=Style(width=76, gap=3, marginBottom=3), children=[
                    OreImage(name=button_asset(variant, state, elevated), style=Style(width=76, height=21,
                        alignItems=AlignItems.center, justifyContent=JustifyContent.center), children=OreText(
                            content=label, fontSize=8, color=OreColors.darkText
                            if variant == OreVariant.secondary else OreColors.text)),
                    OreText(content=dict(default='默认', hovered='悬停', focused='焦点', pressed='按下', disabled='禁用')[state], fontSize=7, color=OreColors.muted),
                ]) for state in (OreState.default, OreState.hovered, OreState.focused, OreState.pressed, OreState.disabled)],
        ]) for label, variant in VARIANTS for elevated in (True, False)
    ]))


@Component
def LabButtons(onAction):
    return Section(title='常用按钮', children=AtlasGrid(cellWidth=60, children=
        [OreButton(key='lab_' + variant + '_raised', label=label, variant=variant,
                   style=Style(width=60, height=22), onClick=partial(onAction, label))
         for label, variant in VARIANTS] + [
        OreButton(key='lab_primary_disabled', label='禁用', disabled=True, style=Style(width=60, height=22)),
        OreButton(key='lab_neutral_disabled', label='锁定', variant=OreVariant.neutral, disabled=True,
                  style=Style(width=60, height=22)),
        OreButton(key='lab_primary_flat', label='平面', variant=OreVariant.primary, elevated=False,
                  style=Style(width=60, height=22), onClick=partial(onAction, '平面')),
        OreButton(key='lab_primary_focus', label='焦点', variant=OreVariant.primary, focused=True,
                  style=Style(width=60, height=22), onClick=partial(onAction, '焦点')),
    ]))


@Component
def LabSelection(selected, onSelect, tab, onTab, onAction):
    return Panel(style=Style(flexDirection=FlexDirection.row, flexWrap=FlexWrap.wrap,
                            alignItems=AlignItems.flex_start, gap=10), children=[
        Section(title='列表选项', style=Style(flex=1, minWidth=140), children=[
            OreListItem(key='lab_list_a', title='林间小屋', description='草原 · 12 MB',
                        selected=selected == 'a', onClick=partial(onSelect, 'a')),
            OreListItem(key='lab_list_b', title='瞭望塔', description='山地 · 8 MB',
                        selected=selected == 'b', onClick=partial(onSelect, 'b')),
            OreListItem(key='lab_list_disabled', title='禁用项', disabled=True,
                        onClick=partial(onAction, '不应收到禁用列表回调')),
            OreListItem(key='lab_list_disabled_selected', title='禁用且选中',
                        selected=True, disabled=True,
                        onClick=partial(onAction, '不应收到禁用选中列表回调')),
        ]),
        Section(title='页签', style=Style(flex=1, minWidth=140), children=[
            OreTabs(key='lab_tabs', options=[('概览', 'overview'), ('详情', 'details')],
                    value=tab, onChange=onTab),
            OreText(key='lab_tab_value', content='概览' if tab == 'overview' else '详情', color=OreColors.muted),
            OreButton(key='lab_clear_selection', label='清除列表选择', elevated=False,
                      onClick=partial(onSelect, None)),
        ]),
    ])


@Component
def LabSliders(value, onChange, stepValue, onStepChange, locked, onLock, onAction):
    return Panel(style=Style(flexDirection=FlexDirection.row, flexWrap=FlexWrap.wrap,
                            alignItems=AlignItems.flex_start, gap=10), children=[
        Section(title='连续与分段', style=Style(flex=1, minWidth=140), children=[
            OreText(key='lab_slider_value', content='连续值：%.2f' % value),
            OreSlider(key='lab_slider', value=value, onChange=onChange, disabled=locked),
            OreText(key='lab_step_value', content='分段值：%d' % int(stepValue)),
            OreSlider(key='lab_step_slider', value=stepValue, steps=5, onChange=onStepChange),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=5), children=[
                OreButton(key='lab_slider_min', label='最小值', style=Style(flex=1),
                          onClick=partial(onChange, 0.0)),
                OreButton(key='lab_slider_max', label='最大值', style=Style(flex=1),
                          onClick=partial(onChange, 1.0)),
            ]),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=6, alignItems=AlignItems.center), children=[
                OreCheckbox(key='lab_lock_slider', value=locked, onChange=onLock),
                OreText(content='锁定连续滑块'),
            ]),
        ]),
        Section(title='自由调节与锁定', style=Style(flex=1, minWidth=140), children=[
            OreText(content='自由调节'),
            OreSlider(key='lab_uncontrolled_slider', defaultValue=0.25,
                      onChange=partial(onAction, '非受控滑块')),
            OreText(content='已锁定'),
            OreSlider(key='lab_slider_disabled', value=0.65, disabled=True,
                      onChange=partial(onAction, '不应收到禁用滑块回调')),
        ]),
    ])


@Component
def LabFeedback(checked, onCheck, progress, onProgress, onAction):
    return Panel(style=Style(flexDirection=FlexDirection.row, flexWrap=FlexWrap.wrap,
                            alignItems=AlignItems.flex_start, gap=10), children=[
        Section(title='复选框', style=Style(flex=1, minWidth=140), children=[
            Panel(style=Style(flexDirection=FlexDirection.row, gap=7, alignItems=AlignItems.center), children=[
                OreCheckbox(key='lab_controlled_checkbox', value=checked, onChange=onCheck),
                OreText(key='lab_checkbox_value', content='受控：' + ('开' if checked else '关')),
            ]),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=7, alignItems=AlignItems.center), children=[
                OreCheckbox(key='lab_uncontrolled_checkbox', defaultValue=True,
                            onChange=partial(onAction, '非受控复选框')),
                OreText(content='非受控：初始勾选'),
            ]),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=7, alignItems=AlignItems.center), children=[
                OreCheckbox(key='lab_disabled_checkbox_on', value=True, disabled=True),
                OreCheckbox(key='lab_disabled_checkbox_off', value=False, disabled=True),
                OreText(content='禁用', color=OreColors.disabled),
            ]),
        ]),
        Section(title='进度条', style=Style(flex=1, minWidth=140), children=[
            OreText(key='lab_progress_value', content='进度：%d%%' % int(round(progress * 100))),
            OreProgress(key='lab_progress', value=progress),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=4), children=[
                OreButton(key='lab_progress_down', label='-10%', style=Style(flex=1),
                          onClick=partial(onProgress, -0.1)),
                OreButton(key='lab_progress_up', label='+10%', style=Style(flex=1),
                          onClick=partial(onProgress, 0.1)),
            ]),
            OreProgress(value=0.0), OreProgress(value=1.0),
            OreText(content='尚未开始与已完成', color=OreColors.muted,
                    style=Style(width='100%')),
        ]),
    ])


@Component
def LabMedia(animated, onAnimate):
    return OreCard(style=Style(gap=8), children=[
        OreText(content='图片、图标、文字、九宫格与序列帧'),
        Panel(style=Style(flexDirection=FlexDirection.row, gap=10, alignItems=AlignItems.center), children=[
            [OreIcon(key=name, name=name, size=14) for name in
             (OreIconName.check, OreIconName.close, OreIconName.back, OreIconName.search,
              OreIconName.settings, OreIconName.world)],
            OreImage(name='a', style=Style(width=18, height=18)),
            OreImage(name='shift', style=Style(width=32.5, height=18)),
            OreImage(name='mouse_left_click', style=Style(width=18, height=20)),
        ]),
        Panel(style=Style(flexDirection=FlexDirection.row, gap=10, alignItems=AlignItems.center), children=[
            OreImage(key='lab_animation', name='animation', animate=animated,
                     style=Style(width=24, height=24)),
            OreButton(key='lab_toggle_animation', label='暂停动画' if animated else '播放动画',
                      onClick=partial(onAnimate, not animated)),
            OreText(content='静态时显示第一帧', color=OreColors.muted),
        ]),
        OreCard(style=Style(width='100%', padding=7), children=[
            OreText(content='嵌套卡片：边框拉伸、文字颜色和内容自动尺寸'),
            OreText(content='白色正文 / 灰色辅助文字', color=OreColors.muted),
        ]),
    ])


INITIAL = {
    'selected': 'b', 'tab': 'overview', 'slider': 0.35, 'step': 2.0,
    'locked': False, 'checked': False, 'progress': 0.45, 'animated': True,
    'switch': True, 'radio': 'survival', 'difficulty': 'normal',
    'name': 'Ore World', 'search': '', 'dropdown': 'survival', 'placeholder': None,
    'longMenu': 1, 'world': 0, 'navTab': 'worlds', 'sideMenu': 'game',
    'listPage': 1, 'expanded': True, 'advanced': False,
    'assetFilter': 'all', 'assetPage': 1, 'assetQuery': '',
}


@Component
def LegacyOrePlayground():
    page, set_page = use_state(LabPage.buttons)
    values, set_values = use_state(dict(INITIAL))
    overlay, set_overlay = use_state(None)
    events, set_events = use_state(0)
    latest, set_latest = use_state('就绪')
    generation, set_generation = use_state(0)

    def record(name, value=None):
        if name == 'restore_banners':
            def restore(current):
                updated = dict(current)
                for tone in ('success', 'info', 'warning', 'error'):
                    updated['hidden_' + tone] = False
                return updated
            set_values(restore)
            name = '已恢复横幅'
        set_events(lambda count: count + 1)
        set_latest(name if value is None else '%s：%s' % (name, value))

    def change(name, value):
        def update(current):
            updated = dict(current)
            updated[name] = value
            if name in ('assetFilter', 'assetQuery'):
                updated['assetPage'] = 1
            return updated
        set_values(update)
        record('已更新设置')

    def select_page(next_page):
        set_page(next_page)

    def reset_values():
        set_values(dict(INITIAL))
        set_generation(lambda count: count + 1)
        set_events(0)
        set_latest('已恢复初始设置')

    def close_overlay():
        set_overlay(None)
        record('关闭弹层')

    def confirm():
        status = {'form': '设置已保存', 'progress': '同步已完成',
                  'menu': '已关闭操作菜单', 'warning': '已确认删除'}
        latest_status = status.get(overlay, '已完成')
        set_overlay(None)
        record(latest_status)

    body = Panel(style=Style(width='100%'), children=[
        Section(title='世界设置', children=[
            OreField(label='世界名称', value=values['name'], onChange=partial(change, 'name')),
            OreDropdown(title='游戏模式', options=[('生存', 'survival'), ('创造', 'creative')],
                        value=values['radio'], onChange=partial(change, 'radio')),
            OreSwitch(label='多人游戏', value=values['switch'], onChange=partial(change, 'switch')),
            OreText(content='音量'),
            OreSlider(value=values['slider'], onChange=partial(change, 'slider')),
            OreButton(key='lab_start', label='创建世界', variant=OreVariant.primary,
                      onClick=partial(set_overlay, 'form')),
        ]),
        Section(title='浏览图鉴', children=[
            OreButton(label='按钮',
                      onClick=partial(select_page, LabPage.buttons)),
            OreButton(key='lab_start_fields', label='表单', elevated=False,
                      onClick=partial(select_page, LabPage.fields)),
            OreButton(label='资源', onClick=partial(select_page, LabPage.media)),
        ]),
    ])
    if page == LabPage.buttons:
        body = Panel(style=Style(width='100%', gap=7), children=[
            LabButtons(onAction=record),
            LabButtonStates(),
            Section(title='图标按钮', children=AtlasGrid(
                cellWidth=60, gap=5, children=[
                    OreButton(key='lab_icon_check', icon=OreIconName.check, label='确认', style=Style(width=60),
                              onClick=partial(record, '图标确认')),
                    OreButton(key='lab_icon_back', icon=OreIconName.back, label='返回', style=Style(width=60),
                              onClick=partial(record, '图标返回')),
                    OreButton(key='lab_icon_only', icon=OreIconName.close, style=Style(width=60),
                              onClick=partial(record, '纯图标关闭')),
                    OreButton(key='lab_icon_disabled', icon=OreIconName.close, label='禁用', disabled=True,
                              style=Style(width=60),
                              onClick=partial(record, '错误：禁用图标按钮')),
                ])),
            Section(title='连续操作', children=[
                OreButton(key='lab_repeat', label='再次保存', onClick=partial(record, '重复点按')),
                OreButton(key='lab_long_button', label='保存并返回世界列表',
                          style=Style(width='100%', height=32), onClick=partial(record, '长文本按钮')),
            ]),
        ])
    elif page == LabPage.selection:
        body = LabSelection(selected=values['selected'], onSelect=partial(change, 'selected'),
                            tab=values['tab'], onTab=partial(change, 'tab'), onAction=record)
    elif page == LabPage.toggles:
        body = LabToggles(values=values, onChange=change, onAction=record)
    elif page == LabPage.fields:
        body = LabFields(values=values, onChange=change, onAction=record)
    elif page == LabPage.dropdowns:
        body = LabDropdowns(values=values, onChange=change, onAction=record)
    elif page == LabPage.sliders:
        body = LabSliders(value=values['slider'], onChange=partial(change, 'slider'),
                          stepValue=values['step'], onStepChange=partial(change, 'step'),
                          locked=values['locked'], onLock=partial(change, 'locked'), onAction=record)
    elif page == LabPage.feedback:
        body = Panel(style=Style(width='100%', gap=7), children=[
            LabFeedback(checked=values['checked'], onCheck=partial(change, 'checked'), progress=values['progress'],
                        onProgress=lambda amount: change('progress', max(0.0, min(1.0, values['progress'] + amount))),
                        onAction=record),
            Section(title='同步进度', children=[
                OreSlider(key='lab_progress_slider', value=values['progress'], onChange=partial(change, 'progress')),
                OreProgress(value=values['progress'], style=Style(height=10)),
                OreProgress(value=values['progress'], style=Style(height=10), color=OreColors.destructive),
                OreImage(name='animation', animate=values['animated'], style=Style(width=20, height=20)),
                OreButton(key='lab_progress_animation', label='暂停动画' if values['animated'] else '播放动画',
                          onClick=partial(change, 'animated', not values['animated'])),
            ]),
        ])
    elif page == LabPage.cards:
        body = LabCards(values=values, onChange=change, onAction=record)
    elif page == LabPage.navigation:
        body = LabNavigation(values=values, onChange=change, onAction=record)
    elif page == LabPage.containers:
        body = LabContainers(values=values, onChange=change, onAction=record)
    elif page == LabPage.messages:
        body = LabMessages(values=values, onChange=change, onAction=record)
    elif page == LabPage.media:
        body = LabAssets(values=values, onChange=change, onAction=record)
    elif page == LabPage.dialogs:
        body = Section(title='对话框与侧栏', children=[
            OreButton(key='lab_open_dialog', label='表单弹窗', variant=OreVariant.primary,
                      onClick=partial(set_overlay, 'form')),
            OreButton(key='lab_open_progress', label='进度弹窗', onClick=partial(set_overlay, 'progress')),
            OreButton(key='lab_open_menu', label='菜单弹窗', onClick=partial(set_overlay, 'menu')),
            OreButton(key='lab_open_warning', label='删除确认', onClick=partial(set_overlay, 'warning')),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=4), children=[
                OreButton(key='lab_drawer_left', label='左抽屉', style=Style(flex=1), onClick=partial(set_overlay, 'left')),
                OreButton(key='lab_drawer_right', label='右抽屉', style=Style(flex=1), onClick=partial(set_overlay, 'right')),
            ]),
            OreButton(key='lab_under_dialog', label='保存设置', onClick=partial(record, '设置已保存')),
        ])
    elif page == LabPage.coverage:
        from .reference_catalog import COVERAGE
        body = Section(title='Web 组件目录', children=[
            OreText(content=name + ' · ' + status,
                    color=OreColors.muted, style=Style(width='100%'))
            for name, status, destination in COVERAGE
        ])

    dialog_title, dialog_message, dialog_confirm = '世界设置', '设置你的演示世界。', '保存'
    dialog_variant = OreVariant.primary
    dialog_content = None
    if overlay == 'form':
        dialog_content = Panel(style=Style(width='100%', gap=5), children=[
            OreField(key='lab_dialog_name', value=values['name'], onChange=partial(change, 'name')),
            OreSwitch(label='多人游戏', value=values['switch'], onChange=partial(change, 'switch')),
        ])
    elif overlay == 'progress':
        dialog_title, dialog_message, dialog_confirm = '同步世界', '正在准备世界资源。', '完成'
        dialog_content = Panel(style=Style(width='100%', gap=6), children=[
            OreImage(name='animation', animate=True, style=Style(width=20, height=20)),
            OreProgress(value=values['progress']), OreText(content='同步进度：%d%%' % (values['progress'] * 100)),
        ])
    elif overlay == 'menu':
        dialog_title, dialog_message, dialog_confirm = '世界操作', '', '完成'
        dialog_content = Panel(style=Style(width='100%', gap=3), children=[
            OreListItem(key='lab_modal_' + value, title=label,
                        onClick=partial(record, '已选择' + label))
            for label, value in [('编辑', 'edit'), ('复制', 'copy'), ('删除', 'delete')]
        ])
    elif overlay == 'warning':
        dialog_title, dialog_message, dialog_confirm = '删除世界？', '删除后无法恢复这个存档。', '删除'
        dialog_variant = OreVariant.destructive
        dialog_content = OreBanner(message='世界：' + values['name'], tone=OreTone.warning)

    return Panel(style=Style(width='100%', height='100%'), children=[
        AtlasShell(pages=PAGES, page=page, onPage=select_page, onReset=reset_values,
                   onClose=navigator.pop, onWorkshop=partial(navigator.push, OreGallery),
                   events=events, latest=latest, generation=generation, children=body),
        OreDialog(key='lab_dialog', visible=overlay is not None and overlay not in ('left', 'right'),
                  title=dialog_title, message=dialog_message,
                  confirmLabel=dialog_confirm, confirmVariant=dialog_variant,
                  onConfirm=confirm, onClose=close_overlay, children=dialog_content),
        OreDrawer(key='lab_drawer', visible=overlay in (OreSide.left, OreSide.right), side=overlay or OreSide.right,
                  title='好友与邀请', onClose=close_overlay, children=ScrollView(style=Style(width='100%', flex=1),
                  children=Panel(style=Style(width='100%', gap=5), children=[
                      OreListItem(title='Steve', description='在线', onClick=partial(record, '邀请 Steve')),
                      OreListItem(title='Alex', description='离线', disabled=True),
                      OreSwitch(label='接收邀请', value=values['switch'], onChange=partial(change, 'switch')),
                      OreText(content='暂无新的邀请', color=OreColors.muted, style=Style(width='100%')),
                  ]))),
    ])


from .settings_playground import OrePlayground


