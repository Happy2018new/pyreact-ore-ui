# -*- coding: utf-8 -*-
# pylint: disable=unexpected-keyword-arg,E1123
"""Interactive settings and component collection built from public Ore controls."""
from functools import partial
from .pyreact import (Component, Panel, Style, FlexDirection, AlignItems,
                      use_state, navigator)
from .oreui import (OreSettingsScreen, OreNavigationItem, OreNavigationGroup,
                    OreSettingsRow, OreSettingsSection, OreSettingLayout,
                    OreSegmentedControl, OreDivider, OreIconButton,
                    OreText, OreButton, OreVariant, OreColors, OreSwitch,
                    OreSlider, OreField, OreDropdown, OreTabs, OreCheckbox,
                    OreRadio, OreListItem, OreCard, OreWorldCard, OreImage, OreIcon,
                    OreScrollView, OreDialog, OreDrawer, OreSide, OreBanner,
                    OreTone, OreProgress, OreTag, OreBadge, OreAccordion,
                    OrePagination, OreHelp, asset_names, OreWorldNavigation,
                    OreFriendsPanel, OreActionMenu)
from .settings_examples import DemoPacks, DemoPlayers

PAGES = [('通用', 'overview', 'general_icon'), ('高级', 'selection', 'advanced_icon'),
         ('多人游戏', 'toggles', 'multiplayer_icon'), ('按钮', 'buttons', None),
         ('输入框', 'fields', None), ('下拉菜单', 'dropdowns', None),
         ('滑块', 'sliders', None), ('导航', 'navigation', 'ui_menu_worlds_tab'),
         ('列表与容器', 'containers', 'grass_block'), ('消息', 'messages', 'accessibility'),
         ('弹窗', 'dialogs', None), ('资源图鉴', 'media', 'world'), ('好友', 'social', 'friends')]
INITIAL = dict(name='我的世界', seed='8675309', mode='creative', difficulty='peaceful',
               distance=0, multiplayer=True, coordinates=False, days=False,
               recipes=True, fire=True, respawn=False, beds=True, volume=0.6,
               step=2, locked=False, permission='member', access='friends',
               invite=True, checkbox=False, radio='survival', tab='worlds',
               drop='normal', language='zh', expanded=True, page=1,
               animated=True, query='', selected='a', notice=True,
               packTab='available', packShare=False, packOpen=0, activePacks=[],
               friendQuery='', friendTab='friends', friendName='Steve', messageExpanded=True)


@Component
def DemoAssetPage(values, onChange):
    query = values['query'].strip().lower()
    names = [name for name in asset_names() if query in name]
    pages = max(1, (len(names) + 7) // 8)
    page = min(pages, values['page'])
    shown = names[(page - 1) * 8:page * 8]
    return OreSettingsSection(title='资源图鉴', children=[
        OreSettingsRow(title='搜索', layout=OreSettingLayout.field,
            children=OreField(key='lab_asset_search', value=values['query'], onChange=partial(onChange, 'query'))),
        OreSettingsRow(title='动画', children=OreSwitch(key='lab_asset_animation', value=values['animated'],
            onChange=partial(onChange, 'animated'))),
        [OreSettingsRow(key=name, title=name.replace('_', ' '), layout=OreSettingLayout.stacked,
            children=OreImage(name=name, animate=values['animated'], style=Style(width='100%', height=52)))
         for name in shown],
        OreSettingsRow(children=OrePagination(key='lab_asset_pagination', page=page, pages=pages,
            onChange=partial(onChange, 'page'))),
    ])


@Component
def OrePlayground():
    page, set_page = use_state('overview')
    values, set_values = use_state(dict(INITIAL))
    overlay, set_overlay = use_state(None)
    events, set_events = use_state(0)
    latest, set_latest = use_state('')
    generation, set_generation = use_state(0)

    def record(message):
        set_events(lambda count: count + 1)
        set_latest(message)

    def change(name, value):
        def update(current):
            result = dict(current)
            result[name] = value
            if name == 'query':
                result['page'] = 1
            return result
        set_values(update)
        record('设置已更新')

    def reset():
        set_values(dict(INITIAL))
        set_generation(lambda count: count + 1)
        record('已恢复默认设置')

    def open_player(name):
        change('friendName', name)
        set_overlay('friend_options')

    def player_action(label):
        record(label)
        set_overlay('drawer')

    def row_switch(title, description, name, key=None, disabled=False):
        return OreSettingsRow(title=title, description=description, disabled=disabled,
            children=OreSwitch(key=key or 'setting_' + name, value=values[name], disabled=disabled,
                               onChange=partial(change, name)))

    def choices(title, description, name, options, key=None, disabled=False):
        return OreSettingsRow(title=title, description=description, layout=OreSettingLayout.field,
            children=OreSegmentedControl(key=key or 'choices_' + name, value=values[name],
                options=options, disabled=disabled, onChange=partial(change, name)))

    navigation = OreWorldNavigation(onPlay=partial(record, '选择了游戏'),
        onRealms=partial(record, '选择了 Realms'), children=[
        OreNavigationGroup(children=[OreNavigationItem(key='lab_page_' + value, label=label,
            icon=icon, selected=page == value, onClick=partial(set_page, value))
            for label, value, icon in PAGES[:3]]),
        OreNavigationItem(key='lab_page_containers', label='资源包', icon='resource_packs_icon',
            selected=page == 'containers', onClick=partial(set_page, 'containers')),
        OreNavigationGroup(title='界面', children=[OreNavigationItem(key='lab_page_' + value,
            label=label, icon=icon, selected=page == value, onClick=partial(set_page, value))
            for label, value, icon in PAGES[3:] if value != 'containers']),
        OreNavigationGroup(title='设置', children=[
            OreNavigationItem(key='lab_reset', label='恢复默认设置', icon='general_icon', onClick=reset),
            OreNavigationItem(key='lab_close', label='返回游戏', icon='world', onClick=navigator.pop),
        ]),
    ])
    body = OreSettingsSection(children=[
        OreSettingsRow(title='世界名称', layout=OreSettingLayout.field,
            children=OreField(key='lab_name', value=values['name'], onChange=partial(change, 'name'))),
        choices('游戏模式', '创建、建造和探索你的世界。', 'mode',
                [('生存', 'survival'), ('创造', 'creative'), ('冒险', 'adventure')], 'lab_game_mode'),
        choices('难度', '选择世界中的挑战程度。', 'difficulty',
                [('和平', 'peaceful'), ('简单', 'easy'), ('一般', 'normal'), ('困难', 'hard')], 'lab_difficulty'),
        row_switch('多人游戏', '其他玩家可以加入你的世界', 'multiplayer', 'lab_switch'),
        row_switch('显示坐标', '显示你当前的位置', 'coordinates', 'lab_coordinates'),
        row_switch('显示游玩的天数', '显示游戏内游玩的天数', 'days', 'lab_days'),
        OreSettingsRow(title='世界种子', description='创建世界时使用的种子', layout=OreSettingLayout.field,
            children=OreField(key='lab_seed', value=values['seed'], onChange=partial(change, 'seed'))),
    ])
    if page == 'selection':
        body = OreSettingsSection(title='世界选项', children=[
            row_switch('通过睡觉跳过夜晚', '晚上在床上睡觉会跳到早上', 'beds', 'lab_beds'),
            OreSettingsRow(title='需要睡觉的玩家', description='必须有多少玩家躺在床上才能跳过夜晚？',
                valueText='%d%%' % int(values['volume'] * 100), layout=OreSettingLayout.stacked,
                children=OreSlider(key='lab_sleep_slider', value=values['volume'], onChange=partial(change, 'volume'))),
            row_switch('立即重生', '跳过死亡菜单并立即重生', 'respawn', 'lab_respawn'),
            row_switch('重生方块爆炸', '重生锚和床会爆炸', 'fire', 'lab_fire'),
            OreSettingsRow(title='重生半径', description='在此方块半径内重生', layout=OreSettingLayout.field,
                children=OreField(key='lab_respawn_radius', defaultValue='10')),
            choices('模拟距离', '游戏加载并应用玩家周围方块范围内的更改', 'distance',
                    [('4 个区块', 0), ('6 个区块', 1), ('8 个区块', 2), ('10 个区块', 3), ('12 个区块', 4)], 'lab_distance'),
            row_switch('配方解锁', '收集材料以解锁配方书中的配方', 'recipes', 'lab_recipes'),
        ])
    elif page == 'toggles':
        body = Panel(style=Style(width='100%'), children=[
            row_switch('多人游戏', '其他玩家可以加入你的世界', 'multiplayer', 'lab_switch'),
            OreSettingsSection(title='设置', children=[
                choices('玩家访问', '已添加为好友的玩家都可以加入', 'access',
                    [('受邀玩家', 'invited'), ('好友', 'friends'), ('好友的好友', 'everyone')], 'lab_access'),
                choices('默认玩家权限', '成员可以建造、挖掘并与世界进行互动', 'permission',
                    [('访客', 'visitor', 'player_permissions'), ('成员', 'member', 'member'),
                     ('管理员', 'operator', 'operator')], 'lab_permission'),
                row_switch('对局域网内玩家可见', '本地网络上的玩家可以加入你的世界', 'invite', 'lab_invite'),
                row_switch('关闭的开关', '显示未启用的设置', 'respawn', 'lab_switch_off'),
                row_switch('禁用的开关', '此设置暂时不可修改', 'multiplayer', 'lab_switch_disabled', True),
                OreSettingsRow(title='消息提醒', children=OreCheckbox(key='lab_checkbox',
                    value=values['checkbox'], onChange=partial(change, 'checkbox'))),
                OreSettingsRow(title='世界更新提醒', disabled=True,
                    children=OreCheckbox(key='lab_checkbox_disabled_off', value=False, disabled=True)),
                OreSettingsRow(title='资源更新提醒', disabled=True,
                    children=OreCheckbox(key='lab_checkbox_disabled_on', value=True, disabled=True)),
                OreSettingsRow(title='访客提醒', children=OreSwitch(key='lab_switch_uncontrolled', defaultValue=False)),
                OreSettingsRow(title='首选模式', layout=OreSettingLayout.stacked,
                    children=OreRadio(key='lab_radio', options=[('生存', 'survival'), ('创造', 'creative'), ('冒险', 'adventure')],
                        disabled=['adventure'],
                        value=values['radio'], onChange=partial(change, 'radio'))),
            ]),
        ])
    elif page == 'sliders':
        body = OreSettingsSection(title='声音与显示', children=[
            OreSettingsRow(title='主音量', description='游戏声音的音量', valueText='%d%%' % (values['volume'] * 100),
                layout=OreSettingLayout.stacked, children=OreSlider(key='lab_slider', value=values['volume'],
                    disabled=values['locked'], onChange=partial(change, 'volume'))),
            OreSettingsRow(title='渲染距离', description='可见的区块范围', valueText=str(values['step'] + 4) + ' 个区块',
                layout=OreSettingLayout.stacked, children=OreSlider(key='lab_step_slider', value=values['step'],
                    steps=5, tickLabels=['4', '5', '6', '7', '8'], onChange=partial(change, 'step'))),
            row_switch('锁定主音量', '保持当前音量', 'locked', 'lab_lock_slider'),
            OreSettingsRow(title='锁定的音量', description='当前环境无法修改此设置', valueText='65%',
                disabled=True, layout=OreSettingLayout.stacked,
                children=OreSlider(key='lab_slider_disabled', value=0.65, disabled=True)),
            OreSettingsRow(title='锁定的渲染距离', valueText='6 个区块', disabled=True,
                layout=OreSettingLayout.stacked, children=OreSlider(key='lab_step_disabled', value=2, steps=5, disabled=True)),
            OreSettingsRow(title='界面亮度', layout=OreSettingLayout.stacked,
                children=OreSlider(key='lab_uncontrolled_slider', defaultValue=0.25)),
        ])
    elif page == 'fields':
        body = OreSettingsSection(title='世界信息', children=[
            OreSettingsRow(title='世界名称', layout=OreSettingLayout.field,
                children=OreField(key='lab_field', value=values['name'], onChange=partial(change, 'name'))),
            OreSettingsRow(title='世界种子', description='留空时使用随机种子', layout=OreSettingLayout.field,
                children=OreField(key='lab_field_uncontrolled', defaultValue='8675309')),
            OreSettingsRow(title='锁定的名称', disabled=True, layout=OreSettingLayout.field,
                children=OreField(key='lab_field_disabled', value='我的世界', disabled=True)),
            OreSettingsRow(title='名称', layout=OreSettingLayout.field,
                children=OreField(key='lab_field_empty', placeholder='世界名称')),
            OreSettingsRow(title='状态', description=latest or '尚未修改设置'),
        ])
    elif page == 'dropdowns':
        body = OreSettingsSection(title='菜单', children=[
            OreSettingsRow(title='画面模式', layout=OreSettingLayout.field,
                children=OreDropdown(key='lab_dropdown', title='画面模式', options=[('简单', 'simple'), ('精美', 'normal'), ('绚丽', 'fancy')],
                    value=values['drop'], onChange=partial(change, 'drop'))),
            OreSettingsRow(title='语言', layout=OreSettingLayout.field,
                children=OreDropdown(key='lab_long_dropdown', title='语言', options=[('简体中文', 'zh'), ('English', 'en'),
                    ('繁體中文', 'tw'), ('日本語', 'jp'), ('Deutsch', 'de'), ('Français', 'fr'), ('Español', 'es')],
                    value=values['language'], onChange=partial(change, 'language'))),
            OreSettingsRow(title='默认权限', layout=OreSettingLayout.field,
                children=OreDropdown(key='lab_dropdown_uncontrolled', title='默认权限', defaultValue='member',
                    options=[('访客', 'visitor'), ('成员', 'member'), ('管理员', 'operator')], onChange=partial(change, 'permission'))),
            OreSettingsRow(title='锁定的画面模式', disabled=True, layout=OreSettingLayout.field,
                children=OreDropdown(key='lab_dropdown_disabled', value='normal', disabled=True, options=[('精美', 'normal')])),
        ])
    elif page == 'navigation':
        body = OreSettingsSection(title='游戏', children=[
            OreSettingsRow(layout=OreSettingLayout.stacked, children=OreTabs(key='lab_tabs', value=values['tab'],
                onChange=partial(change, 'tab'), options=[('世界 (6)', 'worlds', 'ui_menu_worlds_tab'),
                    ('Realms', 'realms', 'realms'), ('服务器', 'servers', 'ui_menu_server_tab')])),
            OreSettingsRow(title='世界列表', layout=OreSettingLayout.stacked, children=[
                OreListItem(key='lab_list_a', title='林间小屋', description='创造模式', icon='world',
                    selected=values['selected'] == 'a', onClick=partial(change, 'selected', 'a')),
                OreListItem(key='lab_list_b', title='瞭望塔', description='生存模式', icon='world',
                    selected=values['selected'] == 'b', onClick=partial(change, 'selected', 'b')),
                OreListItem(key='lab_list_disabled', title='暂不可用', disabled=True),
            ]),
            OreSettingsRow(title='世界', children=OrePagination(key='lab_pagination', page=values['page'], pages=3,
                onChange=partial(change, 'page'))),
            OreSettingsRow(title='世界预览', layout=OreSettingLayout.stacked, children=
                OreWorldCard(key='lab_world_card', title='我的世界', subtitle='创造模式',
                    onOpen=partial(record, '打开了世界'), onEdit=partial(set_overlay, 'form'))),
        ])
    elif page == 'buttons':
        body = OreSettingsSection(title='世界操作', children=[
            [OreSettingsRow(title=label, layout=OreSettingLayout.field, children=OreButton(key='lab_' + variant + '_raised',
                label=label, variant=variant, style=Style(width='100%'), onClick=partial(record, label)))
             for label, variant in [('游戏', OreVariant.primary), ('复制世界', OreVariant.secondary),
                                   ('导出世界', OreVariant.neutral), ('删除世界', OreVariant.destructive),
                                   ('在 Realms 上开始游戏', OreVariant.realms)]],
            OreSettingsRow(title='锁定的操作', layout=OreSettingLayout.field,
                children=OreButton(key='lab_primary_disabled', label='游戏', variant=OreVariant.primary, disabled=True)),
            OreSettingsSection(title='快捷操作', children=[
                OreSettingsRow(title=label, children=OreButton(key='lab_' + variant + '_flat',
                    label=label, variant=variant, elevated=False, onClick=partial(record, label)))
                for label, variant in [('游戏', OreVariant.primary), ('复制', OreVariant.secondary),
                    ('导出', OreVariant.neutral), ('删除', OreVariant.destructive), ('Realms', OreVariant.realms)]]),
            OreSettingsSection(title='暂不可用', children=[
                OreSettingsRow(title=label, disabled=True, children=OreButton(key='lab_' + variant + '_disabled',
                    label=label, variant=variant, disabled=True))
                for label, variant in [('复制世界', OreVariant.secondary), ('导出世界', OreVariant.neutral),
                    ('删除世界', OreVariant.destructive), ('Realms', OreVariant.realms)]]),
            OreSettingsRow(title='快捷操作', children=Panel(style=Style(flexDirection=FlexDirection.row), children=[
                OreIconButton(key='lab_icon_back', icon='arrow_back_white', onClick=partial(record, '返回')),
                OreIconButton(key='lab_icon_check', icon='check_white', onClick=partial(record, '确认')),
                OreIconButton(key='lab_icon_only', icon='cross_white', onClick=partial(record, '关闭')),
                OreIconButton(key='lab_icon_disabled', icon='cross_white', disabled=True),
            ])),
        ])
    elif page == 'containers':
        body = DemoPacks(values=values, onChange=change)
    elif page == 'messages':
        body = OreSettingsSection(title='消息', children=[
            [OreSettingsRow(title=label, layout=OreSettingLayout.stacked,
                children=OreBanner(message=message, tone=tone)) for label, message, tone in [
                    ('世界', '世界已保存', OreTone.success), ('资源', '正在加载资源包', OreTone.info),
                    ('连接', '连接可能不稳定', OreTone.warning), ('同步', '无法同步世界', OreTone.error)]],
            OreSettingsRow(title='邀请', layout=OreSettingLayout.stacked, children=OreBanner(
                key='lab_notice', message='Alex 已邀请你加入世界', onClose=partial(change, 'notice', False)))
                if values['notice'] else None,
            OreSettingsRow(title='同步进度', valueText='%d%%' % (values['volume'] * 100), layout=OreSettingLayout.stacked,
                children=[OreProgress(value=values['volume']), OreImage(name='animation', animate=values['animated'], style=Style(width=20, height=20))]),
            OreSettingsRow(title='邀请', children=OreBadge(label='3')),
            OreSettingsRow(title='世界状态', children=OreTag(label='已保存')),
            OreSettingsRow(layout=OreSettingLayout.stacked, children=OreHelp(key='lab_help',
                label='如何同步世界？', message='在同一账号下登录后，可以继续查看已保存的世界。')),
            OreSettingsRow(layout=OreSettingLayout.stacked, children=OreAccordion(key='lab_message_accordion',
                title='世界信息', expanded=values['messageExpanded'],
                onToggle=partial(change, 'messageExpanded', not values['messageExpanded']),
                children=OreCard(children=OreText(content='我的世界已保存。你可以随时返回继续建造。',
                    style=Style(width='100%'))))),
            OreSettingsRow(title='操作 %d 次' % events, description=latest),
        ])
    elif page == 'dialogs':
        body = OreSettingsSection(title='世界操作', children=[
            [OreSettingsRow(title=label, layout=OreSettingLayout.field,
                children=OreButton(key=key, label=label, style=Style(width='100%'), onClick=partial(set_overlay, value)))
             for label, value, key in [('编辑世界', 'form', 'lab_open_dialog'), ('同步世界', 'progress', 'lab_open_progress'),
                    ('删除世界', 'warning', 'lab_open_warning'), ('好友与邀请', 'drawer', 'lab_drawer_right')]],
        ])
    elif page == 'media':
        body = DemoAssetPage(values=values, onChange=change)
    elif page == 'social':
        body = OreSettingsSection(title='好友', children=[
            OreSettingsRow(title='搜索人员', layout=OreSettingLayout.field, children=OreField(
                key='lab_friend_search', value=values['friendQuery'], onChange=partial(change, 'friendQuery'))),
            OreSettingsRow(layout=OreSettingLayout.field, children=OreButton(key='lab_open_friends',
                label='打开好友面板', onClick=partial(set_overlay, 'drawer'))),
            OreSettingsRow(layout=OreSettingLayout.stacked, children=DemoPlayers(values=values,
                onOptions=open_player)),
        ])
    dialog_content = OreField(key='lab_dialog_name', value=values['name'], onChange=partial(change, 'name'))
    if overlay == 'progress':
        dialog_content = Panel(style=Style(width='100%'), children=[OreImage(name='animation', animate=True,
            style=Style(width=20, height=20)), OreProgress(value=values['volume'])])
    return Panel(style=Style(width='100%', height='100%'), children=[
        OreSettingsScreen(title='编辑世界', navigation=navigation, activeItem=page, onClose=navigator.pop,
            onSocial=partial(set_overlay, 'drawer'),
            scrollKey='lab_scroll_' + page + '_' + str(generation), children=body),
        OreDialog(key='lab_dialog', visible=overlay in ('form', 'progress', 'warning'),
            title='删除世界？' if overlay == 'warning' else '同步世界' if overlay == 'progress' else '编辑世界',
            message='删除后无法恢复这个存档。' if overlay == 'warning' else '',
            confirmLabel='删除' if overlay == 'warning' else '完成',
            confirmVariant=OreVariant.destructive if overlay == 'warning' else OreVariant.primary,
            onClose=partial(set_overlay, None), onConfirm=partial(set_overlay, None), children=dialog_content),
        OreFriendsPanel(key='lab_drawer', visible=overlay in ('drawer', 'friend_options'),
            onClose=partial(set_overlay, None), query=values['friendQuery'], onSearch=partial(change, 'friendQuery'),
            tab=values['friendTab'], onTabChange=partial(change, 'friendTab'),
            children=DemoPlayers(values=values, onOptions=open_player)),
        OreActionMenu(key='lab_friend_menu', visible=overlay == 'friend_options', title=values['friendName'] + ' 的选项',
            onClose=partial(set_overlay, 'drawer'), actions=[(label, partial(player_action, label))
                for label in ('添加到收藏夹', '静音', '拉黑', '举报', '移除好友')]),
    ])
