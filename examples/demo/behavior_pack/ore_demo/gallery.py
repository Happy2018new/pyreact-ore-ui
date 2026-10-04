# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""A small functional workshop, also serving as the Ore component gallery."""
from functools import partial
from .pyreact import (Component, Panel, Image, Style, SafeArea, ScrollView, FontSize,
                      FlexDirection, FlexWrap, AlignItems, JustifyContent, use_state, navigator)
from .oreui import (OreButton, OreCard, OreCheckbox, OreDialog, OreIcon, OreImage,
                    OreListItem, OreProgress, OreSlider, OreTabs, OreText, OreColors,
                    OreVariant)


class GalleryTab(object):
    workshop = 'workshop'
    components = 'components'


class Blueprint(object):
    cottage = 'cottage'
    tower = 'tower'
    garden = 'garden'


BLUEPRINTS = [(Blueprint.cottage, '林间小屋', '48 方块 · 建筑'),
              (Blueprint.tower, '瞭望塔', '128 方块 · 建筑'),
              (Blueprint.garden, '花园', '36 方块 · 景观')]


@Component
def ComponentSamples(onAction=None):
    selected_item, set_selected_item = use_state('selected')
    checkbox, set_checkbox = use_state(False)
    slider, set_slider = use_state(0.35)
    progress, set_progress = use_state(0.45)
    mini_tab, set_mini_tab = use_state('overview')
    actions, set_actions = use_state(0)

    def action():
        set_actions(lambda current: current + 1)
        if onAction is not None:
            onAction()

    def shift_progress(amount):
        set_progress(lambda current: max(0.0, min(1.0, current + amount)))

    return Panel(style=Style(gap=7), children=[
        OreText(content='Ore UI 控件实验台', fontSize=FontSize.normal),
        OreText(content='悬停与拖动查看状态；向下滚动浏览全部控件。',
                color=OreColors.muted),
        OreCard(style=Style(gap=5), children=[
            OreText(content='按钮状态与变体', fontSize=FontSize.normal),
            OreText(content='普通 / 悬停 / 按下 / 焦点 / 禁用', color=OreColors.muted),
            Panel(style=Style(flexDirection=FlexDirection.row, flexWrap=FlexWrap.wrap, gap=5), children=[
                OreButton(key='lab_primary', label='主要', variant=OreVariant.primary, onClick=action),
                OreButton(key='lab_secondary', label='次要', onClick=action),
                OreButton(key='lab_neutral', label='中性', variant=OreVariant.neutral, onClick=action),
                OreButton(key='lab_destructive', label='删除', variant=OreVariant.destructive, onClick=action),
                OreButton(key='lab_realms', label='Realms', variant=OreVariant.realms, onClick=action),
                OreButton(key='lab_flat', label='平面', variant=OreVariant.primary, elevated=False,
                          onClick=action),
                OreButton(key='lab_disabled', label='不可用', disabled=True, onClick=action),
                OreButton(key='lab_focused', label='显式焦点', variant=OreVariant.primary,
                          focused=True, onClick=action),
            ]),
            OreText(key='lab_action_count', content='按钮回调：%d 次' % actions, color=OreColors.muted),
        ]),
        OreCard(style=Style(gap=5), children=[
            OreText(content='列表项：选中框与悬停', fontSize=FontSize.normal),
            OreText(content='选中项移动鼠标时白色选中框应保持；按下时使用 pressed focused。',
                    color=OreColors.muted),
            OreListItem(key='lab_list_selected', title='当前选中项',
                        description='悬停不会丢失白框', selected=selected_item == 'selected',
                        onClick=partial(set_selected_item, 'selected')),
            OreListItem(key='lab_list_other', title='可选项', description='点击切换选中状态',
                        selected=selected_item == 'other',
                        onClick=partial(set_selected_item, 'other')),
            OreListItem(key='lab_list_disabled', title='禁用项', description='不会触发回调', disabled=True,
                        onClick=action),
        ]),
        OreCard(style=Style(gap=5), children=[
            OreText(content='页签、复选框与滑块', fontSize=FontSize.normal),
            OreTabs(key='lab_tabs', options=[('概览', 'overview'), ('详情', 'details'), ('日志', 'logs')],
                    value=mini_tab, onChange=set_mini_tab),
            OreText(content='当前页签：' + mini_tab, color=OreColors.muted),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=6, alignItems=AlignItems.center), children=[
                OreCheckbox(key='lab_checkbox', value=checkbox, onChange=set_checkbox),
                OreText(content='受控复选框：' + ('开' if checkbox else '关')),
                OreCheckbox(key='lab_checkbox_disabled', value=True, disabled=True),
                OreText(content='禁用'),
            ]),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=6, alignItems=AlignItems.center), children=[
                OreSlider(key='lab_slider', value=slider, onChange=set_slider,
                          style=Style(width='100%', flex=1)),
                OreText(key='lab_slider_value', content='%.2f' % slider),
            ]),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=6, alignItems=AlignItems.center), children=[
                OreSlider(key='lab_slider_disabled', value=0.65, disabled=True,
                          style=Style(width='100%', flex=1)),
                OreText(content='禁用滑块', color=OreColors.disabled),
            ]),
        ]),
        OreCard(style=Style(gap=5), children=[
            OreText(content='进度、图片、图标与动画', fontSize=FontSize.normal),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=5, alignItems=AlignItems.center), children=[
                OreButton(key='lab_progress_down', label='-', variant=OreVariant.neutral,
                          onClick=partial(shift_progress, -0.1)),
                OreProgress(key='lab_progress', value=progress, style=Style(flex=1)),
                OreButton(key='lab_progress_up', label='+', variant=OreVariant.neutral,
                          onClick=partial(shift_progress, 0.1)),
                OreText(key='lab_progress_value', content='%d%%' % int(progress * 100)),
            ]),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=7, alignItems=AlignItems.center), children=[
                OreImage(name='a', style=Style(width=18, height=18)),
                OreImage(name='shift', style=Style(width=32.5, height=18)),
                OreImage(name='mouse_left_click', style=Style(width=18, height=20)),
                OreImage(name='animation', animate=True, style=Style(width=14, height=14)),
                OreIcon(name='magnifying_glass'),
                OreIcon(name='settings'),
            ]),
        ]),
        OreCard(style=Style(gap=5), children=[
            OreText(content='弹窗与卡片', fontSize=FontSize.normal),
            OreText(content='卡片自动包裹子内容；弹窗支持确认、取消和背景关闭。',
                    color=OreColors.muted),
            OreButton(key='lab_open_dialog', label='打开测试弹窗', variant=OreVariant.primary,
                      onClick=onAction),
        ]),
    ])


@Component
def OreGallery():
    tab, set_tab = use_state(GalleryTab.workshop)
    selected, set_selected = use_state(Blueprint.cottage)
    snapping, set_snapping = use_state(True)
    builds, set_builds = use_state(0)
    dialog, set_dialog = use_state(False)
    selected_label = next(item[1] for item in BLUEPRINTS if item[0] == selected)

    def confirm_build():
        set_builds(lambda current: current + 1)
        set_dialog(False)

    body = ComponentSamples(onAction=partial(set_dialog, True))
    if tab == GalleryTab.workshop:
        body = Panel(style=Style(flexDirection=FlexDirection.row, flexWrap=FlexWrap.wrap, gap=8), children=[
            OreCard(style=Style(flex=1, minWidth=100, gap=4), children=[
                OreText(content='选择蓝图', fontSize=FontSize.normal, style=Style(marginBottom=3)),
                [OreListItem(key='blueprint_' + item[0], title=item[1], description=item[2],
                             selected=selected == item[0], onClick=partial(set_selected, item[0]))
                 for item in BLUEPRINTS],
            ]),
            OreCard(style=Style(flex=1.3, minWidth=122, gap=7), children=[
                OreText(content=selected_label, fontSize=FontSize.normal),
                OreText(content='整理你的蓝图，然后开始下一次创造。', color=OreColors.muted,
                        style=Style(width='100%')),
                Panel(style=Style(flexDirection=FlexDirection.row, gap=6, alignItems=AlignItems.center), children=[
                    OreCheckbox(key='snapping', value=snapping, onChange=set_snapping),
                    OreText(content='自动对齐' + ('：开' if snapping else '：关')),
                ]),
                OreProgress(value=min(builds, 5) / 5.0),
                OreText(key='build_status', content='已创建 %d 次' % builds, color=OreColors.muted),
                OreButton(key='create_blueprint', label='创建蓝图', variant=OreVariant.primary,
                          onClick=partial(set_dialog, True), style=Style(width='100%')),
                OreButton(key='disabled_export', label='导出（示例禁用）', disabled=True,
                          onClick=confirm_build, style=Style(width='100%')),
            ]),
        ])
    return Image(color=OreColors.background, style=Style(width='100%', height='100%'), children=[
        SafeArea(style=Style(width='100%', height='100%', padding=8, gap=6), children=[
            Panel(style=Style(flexDirection=FlexDirection.row, alignItems=AlignItems.center,
                             justifyContent=JustifyContent.space_between, height=23), children=[
                Panel(children=[OreText(content='ORE / 创造工作台', fontSize=FontSize.normal),
                                OreText(content='PYREACT COMPONENT GALLERY', color=OreColors.muted)]),
                OreButton(label='关闭', variant=OreVariant.neutral, onClick=navigator.pop,
                          style=Style(height=20)),
            ]),
            OreTabs(key='gallery_tabs', options=[('工作台', GalleryTab.workshop), ('组件库', GalleryTab.components)],
                    value=tab, onChange=set_tab),
            ScrollView(style=Style(flex=1, width='100%'), children=Panel(
                style=Style(width='100%', paddingBottom=6), children=body)),
            OreText(content='O R E  ·  点选蓝图 / 切换页签 / 创建', color=OreColors.muted),
        ]),
        OreDialog(key='build_dialog', visible=dialog, title='创建蓝图',
                  message='将 %s 加入本次工作区？' % selected_label,
                  confirmLabel='创建', onConfirm=confirm_build, onClose=partial(set_dialog, False)),
    ])
