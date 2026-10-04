# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Interactive families derived from the supplied browser component atlas."""
from functools import partial
from .pyreact import (Component, Panel, Image, Style, ScrollView, FlexDirection,
                      AlignItems, FontSize, TextAlignment, Color)
from .oreui import (OreButton, OreCard, OreCheckbox, OreField, OreDropdown,
                    OreSwitch, OreRadio, OreTag, OreBadge, OreBanner,
                    OreAccordion, OrePagination, OreHelp, OreImage,
                    OreListItem, OreTabs, OreProgress, OreText, OreColors,
                    OreVariant, OreIconName, OreTone, OreScrollView as ScrollView, asset, asset_names, palette_color)
from .lab_chrome import AtlasColor, AtlasGrid


@Component
def Section(title, note='', children=None, style=None):
    return Panel(style=Style(width='100%', marginBottom=12).merge(style), children=[
        OreText(content=title.split(' / ')[0], fontSize=9,
                style=Style(width='100%', marginBottom=5)),
        Image(color=AtlasColor.surface, style=Style(width='100%', padding=9, gap=8), children=children),
    ])


@Component
def LabToggles(values, onChange, onAction):
    return Panel(style=Style(width='100%'), children=[
        Section(title='复选框', children=[
            Panel(style=Style(flexDirection=FlexDirection.row, gap=6), children=[
                OreCheckbox(key='lab_controlled_checkbox', value=values['checked'],
                            onChange=partial(onChange, 'checked')),
                OreButton(key='lab_check_label', label='受控：' + ('开' if values['checked'] else '关'),
                          elevated=False, onClick=partial(onChange, 'checked', not values['checked'])),
                OreCheckbox(key='lab_uncontrolled_checkbox', defaultValue=True,
                            onChange=partial(onAction, '非受控复选框')),
            ]),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=6), children=[
                OreCheckbox(key='lab_disabled_checkbox_on', value=True, disabled=True),
                OreCheckbox(key='lab_disabled_checkbox_off', value=False, disabled=True),
                OreText(content='已锁定', color=OreColors.disabled),
            ]),
        ]),
        Section(title='开关', children=[
            OreSwitch(key='lab_switch', value=values['switch'], label='多人游戏：' + ('开' if values['switch'] else '关'),
                      onChange=partial(onChange, 'switch')),
            OreSwitch(key='lab_switch_uncontrolled', defaultValue=False, label='非受控开关',
                      onChange=partial(onAction, '非受控开关')),
            OreSwitch(key='lab_switch_disabled', value=True, disabled=True, label='已锁定开关',
                      onChange=partial(onAction, '错误：禁用开关')),
        ]),
        Section(title='游戏模式', children=[
            OreRadio(key='lab_radio', options=[('生存', 'survival'), ('创造', 'creative'), ('冒险（禁用）', 'adventure')],
                     value=values['radio'], disabled=['adventure'], onChange=partial(onChange, 'radio')),
            OreText(key='lab_radio_value', content='游戏模式：' + dict(survival='生存', creative='创造', adventure='冒险')[values['radio']], color=OreColors.muted),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=4), children=[
                OreButton(key='lab_difficulty_' + value, label=label, focused=values['difficulty'] == value,
                          elevated=False, onClick=partial(onChange, 'difficulty', value), style=Style(flex=1))
                for label, value in [('简单', 'easy'), ('普通', 'normal'), ('困难', 'hard')]
            ]),
        ]),
    ])


@Component
def LabFields(values, onChange, onAction):
    return Panel(style=Style(width='100%'), children=[
        Section(title='世界名称', children=[
            OreField(key='lab_name', label='名称', value=values['name'],
                     onChange=partial(onChange, 'name')),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=5), children=[
                OreButton(key='lab_name_clear', label='清除', onClick=partial(onChange, 'name', ''), elevated=False),
                OreButton(key='lab_name_submit', label='创建演示世界', variant=OreVariant.primary,
                          onClick=partial(onAction, '已提交名称', values['name']), disabled=not bool(values['name'])),
            ]),
            OreText(key='lab_name_value', content='草稿：' + values['name'], style=Style(width='100%')),
            OreBanner(message='名称不能为空', tone=OreTone.error) if not values['name'] else None,
        ]),
        Section(title='搜索与其他输入', children=[
            OreField(key='lab_search', label='本地搜索', value=values['search'],
                     onChange=partial(onChange, 'search'), placeholder='输入 tower 或 cottage 查看匹配结果'),
            OreText(key='lab_search_result', content='匹配：' + ', '.join(
                item for item in ('cottage', 'tower', 'garden') if values['search'].lower() in item)),
            OreField(key='lab_field_uncontrolled', label='备注', defaultValue='Ore UI',
                     onChange=partial(onAction, '非受控文本')),
            OreField(key='lab_field_disabled', label='禁用输入', value='Locked', disabled=True,
                     onChange=partial(onAction, '错误：禁用输入')),
        ]),
    ])


@Component
def LabDropdowns(values, onChange, onAction):
    options = [('生存 · 普通', 'survival'), ('创造 · 平坦', 'creative'), ('冒险 · 山地', 'adventure')]
    return Panel(style=Style(width='100%'), children=[
        Section(title='世界类型', children=[
            OreDropdown(key='lab_dropdown', options=options, value=values['dropdown'],
                        onChange=partial(onChange, 'dropdown')),
            OreText(key='lab_dropdown_value', content='当前类型：' + dict(survival='生存', creative='创造', adventure='冒险')[values['dropdown']]),
            OreDropdown(key='lab_dropdown_placeholder', options=options, value=values['placeholder'],
                        placeholder='尚未选择', onChange=partial(onChange, 'placeholder')),
            OreDropdown(key='lab_dropdown_disabled', options=options, value='survival', disabled=True,
                        onChange=partial(onAction, '错误：禁用下拉菜单')),
        ]),
        Section(title='更多世界', children=[
            OreDropdown(key='lab_dropdown_long', options=[('世界 %02d' % index, index) for index in range(1, 15)],
                        value=values['longMenu'], onChange=partial(onChange, 'longMenu')),
            OreButton(key='lab_dropdown_reset', label='恢复初始选项', elevated=False,
                      onClick=partial(onChange, 'dropdown', 'survival')),
        ]),
    ])


@Component
def LabCards(values, onChange, onAction):
    return Panel(style=Style(width='100%'), children=[
        Section(title='精选世界', children=[
            OreImage(name='realms_core_banner_image', style=Style(width='100%', height=80)),
            OreText(content='探索你的世界'),
            OreText(content='生存 · 普通 · 本地存档', color=OreColors.muted),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=5), children=[
                OreButton(key='lab_card_enter', label='进入世界', variant=OreVariant.primary,
                          style=Style(flex=1), onClick=partial(onAction, '卡片主操作')),
                OreButton(key='lab_card_more', label='设置', elevated=False,
                          onClick=partial(onAction, '卡片附加操作')),
            ]),
        ]),
        Section(title='本地存档', children=[
            Panel(key='world_' + str(index), style=Style(flexDirection=FlexDirection.row, gap=3), children=[
                OreListItem(key='lab_world_' + str(index), title=label, description='本地世界 · %d MB' % (index + 3),
                            selected=values['world'] == index, style=Style(flex=1, minWidth=0),
                            onClick=partial(onChange, 'world', index)),
                OreButton(key='lab_world_more_' + str(index), label='···', style=Style(width=28),
                          onClick=partial(onAction, '更多世界操作', index)),
            ]) for index, label in enumerate(('草原营地', '山间小屋', '海边基地'))
        ]),
        Section(title='还没有世界', children=[
            OreText(content='一起创造，尽情探索。', fontSize=FontSize.medium),
            OreText(content='这里还没有世界。创建一个演示世界以查看成功反馈。', color=OreColors.muted,
                    style=Style(width='100%')),
            OreButton(key='lab_empty_action', label='创建第一个世界', onClick=partial(onAction, '空状态操作')),
            OreText(content='世界大小：24.6 MB · 最近游玩：今天'),
            OreProgress(value=0.8),
        ]),
    ])


@Component
def LabNavigation(values, onChange, onAction):
    return Panel(style=Style(width='100%'), children=[
        Section(title='页面导航', children=[
            OreTabs(key='lab_nav_tabs', options=[('世界', 'worlds'), ('好友', 'friends'), ('服务器', 'servers')],
                    value=values['navTab'], onChange=partial(onChange, 'navTab')),
            OreText(key='lab_nav_content', content='内容页面：' + values['navTab']),
            Panel(style=Style(flexDirection=FlexDirection.row, gap=4), children=[
                OreButton(key='lab_nav_back', label='返回', icon=OreIconName.back,
                          onClick=partial(onAction, '导航返回')),
                OreButton(key='lab_nav_friends', label='好友', onClick=partial(onAction, '导航好友')),
                OreButton(key='lab_nav_menu', label='菜单', onClick=partial(onAction, '导航菜单')),
            ]),
            OreRadio(options=[('游戏', 'game'), ('多人游戏', 'multi'), ('资源包', 'packs')],
                     value=values['sideMenu'], onChange=partial(onChange, 'sideMenu')),
        ]),
        Section(title='分页', children=[
            OrePagination(key='lab_pagination', page=values['listPage'], pages=5,
                          onChange=partial(onChange, 'listPage')),
            OreText(key='lab_page_content', content='世界 %d–%d' % ((values['listPage'] - 1) * 3 + 1,
                                                                values['listPage'] * 3)),
            OreTag(label='3 个存档'),
            OreButton(key='lab_page_last', label='跳到最后一页', elevated=False,
                      onClick=partial(onChange, 'listPage', 5)),
        ]),
    ])


@Component
def LabContainers(values, onChange, onAction):
    return Panel(style=Style(width='100%'), children=[
        Section(title='折叠分区', children=[
            OreAccordion(key='lab_accordion', title='游戏设置', expanded=values['expanded'],
                         onToggle=partial(onChange, 'expanded', not values['expanded']), children=[
                OreSwitch(label='显示坐标', value=values['switch'], onChange=partial(onChange, 'switch')),
                OreText(key='lab_accordion_content', content='坐标会显示在游戏画面中。'),
            ]),
            OreAccordion(key='lab_accordion_closed', title='高级设置', expanded=values['advanced'],
                         onToggle=partial(onChange, 'advanced', not values['advanced']),
                         children=OreHelp(message='高级选项会影响游戏体验。')),
        ]),
        Section(title='网格', children=[
            AtlasGrid(cellWidth=68, gap=5, children=[
                OreButton(key='lab_grid_' + str(index), label='格子 %d' % index,
                          style=Style(width=68, height=32), onClick=partial(onAction, '网格', index))
                for index in range(1, 7)
            ]),
        ]),
        Section(title='滚动列表', children=[
            ScrollView(key='lab_nested_scroll', style=Style(width='100%', height=90), children=Panel(
                style=Style(width='100%', gap=2), children=[
                    OreListItem(key='lab_scroll_item_' + str(index), title='滚动项目 %02d' % index,
                                onClick=partial(onAction, '滚动项目', index)) for index in range(1, 19)
                ])),
            OreText(content='列表结束 · 18 个项目', color=OreColors.muted),
        ]),
    ])


@Component
def LabMessages(values, onChange, onAction):
    return Panel(style=Style(width='100%'), children=[
        Section(title='消息横幅', children=[
            [OreBanner(key='lab_banner_' + tone, tone=tone, message=message,
                       onClose=partial(onChange, 'hidden_' + tone, True))
             for tone, message in [(OreTone.success, '世界已保存'), (OreTone.info, '连接提示'),
                                   (OreTone.warning, '资源包需要更新'), (OreTone.error, '连接失败，请重试')]
             if not values.get('hidden_' + tone)],
            OreButton(key='lab_restore_banners', label='恢复横幅', elevated=False,
                      onClick=partial(onAction, 'restore_banners')),
            AtlasGrid(cellWidth=40, gap=6, children=[
                OreBadge(label='3'),
                OreBadge(label='99+'),
                OreTag(label='NEW'),
                OreTag(label='BETA', color=palette_color('purple40')),
                OreTag(label='锁定', color=OreColors.border),
            ]),
        ]),
        Section(title='提示', children=[
            OreHelp(key='lab_help', label='世界权限', message='只有受邀好友可以加入这个世界。'),
        ]),
        Section(title='文字', children=[
            OreText(content='我的世界 Minecraft 0123', fontSize=FontSize.large),
            OreText(content='一起创造，尽情探索。', fontSize=FontSize.medium),
            Image(color=OreColors.border, style=Style(width='100%', height=1)),
            OreText(content='小字号 caption', fontSize=FontSize.small),
            OreText(content='居中说明', textAlign=TextAlignment.center, style=Style(width='100%')),
            OreText(content='游戏模式：生存\n难度：普通\n多人游戏：启用', style=Style(width='100%')),
        ]),
    ])


@Component
def LabAssets(values, onChange, onAction):
    names = asset_names()
    mode = values['assetFilter']
    query = values['assetQuery'].lower()
    if mode == 'borders':
        names = [name for name in names if 'nineSliceData' in asset(name)]
    elif mode == 'animations':
        names = [name for name in names if 'frames' in asset(name)]
    elif mode == 'icons':
        names = [name for name in names if max(asset(name)['size']) <= 96 and 'frames' not in asset(name)]
    names = [name for name in names if query in name.lower()]
    pages = max(1, (len(names) + 7) // 8)
    page = min(values['assetPage'], pages)
    shown = names[(page - 1) * 8:page * 8]
    return Panel(style=Style(width='100%'), children=[
        Section(title='资源浏览', children=[
            OreTabs(options=[('全部', 'all'), ('图标', 'icons'), ('九宫格', 'borders'), ('动画', 'animations')],
                    value=mode, onChange=partial(onChange, 'assetFilter')),
            OreField(key='lab_asset_search', label='搜索资源名称', value=values['assetQuery'],
                     onChange=partial(onChange, 'assetQuery')),
            OrePagination(key='lab_asset_pagination', page=page, pages=pages,
                          onChange=partial(onChange, 'assetPage')),
            OreText(key='lab_asset_count', content='%d 项资源' % len(names)),
            AtlasGrid(cellWidth=104, gap=5, children=[
                OreCard(key='asset_' + name, style=Style(width=104, height=110, gap=5), children=[
                    OreImage(name=name, contain=True, animate=values['animated'], style=Style(width=88, height=44)),
                    OreText(content=name.replace('_', ' '), fontSize=7, style=Style(width=88)),
                ]) for name in shown
            ]),
            OreButton(key='lab_toggle_animation', label='暂停动画' if values['animated'] else '播放动画',
                      onClick=partial(onChange, 'animated', not values['animated'])),
        ]),
        Section(title='按键图标', children=[
            Panel(style=Style(flexDirection=FlexDirection.row, gap=6, alignItems=AlignItems.center), children=[
                OreImage(name='a', style=Style(width=18, height=18)),
                OreImage(name='shift', style=Style(width=32, height=18)),
                OreImage(name='mouse_left_click', style=Style(width=18, height=20)),
                OreText(content='游戏操作'),
            ]),
        ]),
    ])
