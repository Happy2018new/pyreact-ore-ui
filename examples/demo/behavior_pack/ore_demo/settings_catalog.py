# -*- coding: utf-8 -*-
"""Settings inventory transcribed from Bedrock 1.26.5203.0, Chinese desktop UI.

All values belong to this example. They never write Minecraft's preferences.
"""
from __future__ import unicode_literals
from .settings_copy import DESCRIPTIONS


def row(kind, title, value=None, description=None, **options):
    result = dict(kind=kind, title=title, value=value,
                  description=DESCRIPTIONS.get(title, '') if description is None else description)
    result.update(options)
    return result


def toggle(title, value=False, **options):
    return row('toggle', title, value, **options)


def slider(title, value=1., **options):
    return row('slider', title, value, **options)


def choices(title, labels, value=0, **options):
    return row('choices', title, value, options=labels, **options)


def action(title, label='打开', **options):
    return row('action', title, label=label, **options)


def section(title='', description='', *rows):
    return dict(title=title, description=description, rows=list(rows))


NAVIGATION = [('', [('可访问性', 'accessibility')]),
    ('控制', [('键盘和鼠标','keyboard'),('控制器','controller'),('轻触','touch')]),
    ('社交', [('队伍','party')]),
    ('通用', [('通用','general'),('视频','video'),('音频','audio'),('帐户','account'),
        ('订阅','subscriptions'),('全局资源','resources'),('存储','storage'),('语言','language'),('创建者','creator')])]

HEADINGS = {
    'accessibility': ('可访问性','《Minecraft》适合所有人，包括你'),
    'keyboard': ('键盘和鼠标','调整输入和映射选项'),
    'controller': ('控制器','控制器的输入选项、灵敏度设置和按钮映射'),
    'touch': ('轻触','屏幕触摸屏的输入选项、灵敏度设置和按钮映射'),
    'general': ('通用','一堆东西，从网络设置到游戏制作团队'),
    'video': ('视频','调整图形显示效果及视觉质量'),
    'audio': ('音频','调整音乐和音效的音量设置'),
    'account': ('帐户','访问你的账号信息'),
    'storage': ('存储','管理世界、世界模板、资源包、行为包和缓存数据'),
    'language': ('语言','选择你的 Minecraft 首选语言'),
    'creator': ('创建者','调整日志、调试器、诊断等等'),
}

RESET = action('重置为默认设置','重置', reset=True)
GUI_SCALE = choices('GUI 标度修正', ['50%','75%','100%'],2,
    description='选择 HUD 和其他 UI 元素的大小，使它们在不同的设备上更易于使用')

PAGES = {
 'accessibility': [
    section('文字转语音输出','调整你听到屏幕上文字的方式',
        toggle('UI 文本转语音输出',description='听取菜单选项和其他 UI 元素'),
        toggle('聊天文本转语音输出',description='使用文字转语音输出功能听取聊天消息'),
        slider('文本转语音',description='游戏文本转语音的声音'),
        toggle('加入聊天说明',True,description='加入世界时获取如何开启聊天的提醒')),
    section('游戏','更改游戏中的视觉效果和摄像头移动的辅助功能选项',
        toggle('隐藏字幕',description='在《Minecraft》中为所有声音添加字幕'),
        toggle('摄像机摇晃',True), toggle('隐藏天空闪光'),
        toggle('方块淡化效果',True),toggle('玩家和生物淡化效果',True),
        slider('黑暗效果强度'),slider('屏幕失真'),slider('闪光强度',.75),slider('闪光速度',.5)),
    section('用户界面','设置游戏的 UI 以符合你的游戏风格',
        slider('操作栏背景不透明度',.6,description='动作栏可以看到的范围'),
        slider('聊天背景透明度',.7),slider('文本背景透明度',.6,description='控制工具提示 /title 指令聊天的背景'),
        choices('聊天消息持续时间',['3 秒','10 秒（默认值）','30 秒']),
        choices('吐司通知持续时间',['3 秒（默认）','10 秒','30 秒']),
        GUI_SCALE,toggle('超大的新 UI',description='增加 UI 的大小以提高清晰度和阅读舒适度'),
        action('重置为默认设置','重置',description='将所有辅助功能设置和滑块都恢复到其原始值',reset=True))],
 'keyboard': [section('','',
    slider('摄像机灵敏度（鼠标）',.5),slider('望远镜移动速度',.5),
    toggle('反转摄像机 Y 轴',description='环顾四周时上下反转。对于键盘和鼠标用户来说，这是一个不太常见的选择，但随你喜好。'),
    toggle('自动跳跃'),toggle('全键盘模式',description='将鼠标输入映射到键盘上'),
    action('将设置重置为默认','重置',description='恢复上述所有键盘和鼠标选项为原始值',reset=True)),
    section('键盘和鼠标映射','随心定制键盘和鼠标按键，打造个性化游戏操控体验'),
    section('组合键','与 Ctrl+Alt 组合使用的按键',row('binding','复制坐标','C'),row('binding','复制朝向坐标','D')),
    section('宏','为一个按键分配操作，当按下 ALT 与该绑定按键时执行命令',
        *[row('macro','命令宏 %d'%i,'未指派') for i in range(1,11)]),
    section('','',action('重置为默认映射','重置',description='恢复所有键盘和鼠标按钮映射为原始值',reset=True))],
 'controller': [section('','',slider('摄像机灵敏度',.5),slider('望远镜移动速度',.5),
    toggle('反转摄像机 Y 轴',description='在环顾四周时上下反转'),toggle('自动跳跃'),
    toggle('隐藏控制器提示'),toggle('隐藏控制器光标'),toggle('清除热键'),
    toggle('A/B 键切换',description='交换 A 键和 B 键的功能'),toggle('X/Y 键切换',description='交换 X 键和 Y 键的功能'),
    slider('控制器光标灵敏度',.5,description='调整菜单中光标的速度'),
    action('将设置重置为默认','重置',description='恢复上述所有控制器选项为原始值',reset=True)),
    section('按钮映射','随心定制控制器按键，打造个性化游戏操控体验'),
    section('','',action('将映射重置为默认','重置',description='恢复所有控制器按钮映射为其原始值',reset=True))],
 'touch': [section('','',
    row('touch_customize','自定义控件',description='更改屏幕上按钮的大小和位置以符合你的游戏风格'),
    row('touch_mode','控制模式',0,options=['摇杆并点击进行互动','方向键并点击进行互动','摇杆并瞄准十字线'],
        description='拖动摇杆进行移动。拖动至其他任意位置可环顾四周。点击并按住方块可与它们进行互动。'),
    toggle('显示操作按钮',True,visibleWhen=('控制模式',[2])),
    toggle('左撇子物品栏访问',visibleWhen=('控制模式',[0,1])),
    choices('摇杆可见性',['始终可见','始终隐藏','在未使用时隐藏'],disabled=True,
        visibleWhen=('控制模式',[0,2]),description='选择何时可以看见屏幕上的摇杆'),
    toggle('反转摄像机 Y 轴',description='交换视角的上下方向。有些用户会觉得这样更舒适'),
    slider('摄像机灵敏度',.5),slider('望远镜移动速度',.5),toggle('选取方块'),toggle('摄像机视角按钮'),
    toggle('自动跳跃'),toggle('轻松冲刺',True),choices('顶部按钮尺寸',['小','中','大'],description='选择 HUD 按钮的大小'),
    choices('潜行按钮行为',['点击一下按钮','按住按钮']),toggle('延迟方块破坏（仅限创造模式）',True),
    toggle('破坏方块时振动',True),toggle('拆分物品时振动',True),toggle('仅对快捷栏使用触摸输入'),
    action('重置为默认设置','重置',description='将所有触摸设置和滑块恢复为初始值',reset=True))],
 'general': [section('','',toggle('仅允许受信任的皮肤',True),toggle('筛选猥亵语言',True,description='过滤不当语言')),
    section('暂停','独自游戏时，记得适当休息哦',toggle('启用游戏暂停',True),toggle('焦点丢失时显示暂停菜单',True)),
    section('网络设置','在技术和社交层面上调整在线体验',toggle('启用 WebSocket'),toggle('自动更新内容包',True)),
    section('教程','帮助学习游戏',toggle('教程',True,description='获取游戏内提示，了解《Minecraft》的基础知识'),
        action('重启教程','重新启动',description='重新启动教程，以防万一错过某些内容')),
    section('其他','我们不知道可放置这些设置的其他地方',toggle('当控制器断开连接时降低帧率',True),
        action('帮助中心'),action('制作团队','查看',description='所有帮助制作这个游戏的人'),action('署名'),
        action('授权内容'),action('字体证书'),action('改造列表','查看',description='与玩家无关的技术信息。如果你感兴趣，欢迎随意查阅！'),
        row('version','版本：v26.52',description='版本：51798919\nBranch: r/26_u5\n协议版本：293'))],
 'video': [section('通用','普通视频设置',slider('视野',.375,minimum=30,maximum=110,unit='°'),
    choices('摄像机视角',['第一人称','第三人称背面','第三人称正面'],description='选择游戏内摄像机的视角')),
    section('图形、性能和布局','控制 Minecraft 的外观和运行',toggle('游戏内图形模式切换',True),
        choices('模式：',['简约','花式','灵动视效','光线追踪'],2,description='选择游戏视觉效果的质量',disabledOptions=[3]),
        row('notice','高级实时照明和反射'),row('notice','光线追踪需使用受支持的设备及兼容的市场内容。'),
        slider('亮度',.5),slider('帧率限制',1.,minimum=10,maximum=250,unit=' FPS',endLabel='无限制'),
        slider('抗锯齿',0,steps=4,display=['2','4','8','16']),toggle('画质提升',disabled=True),
        slider('光线追踪能见度',0,steps=4,display=['8 个区块（建议）','12 个区块','16 个区块','24 个区块'],disabled=True),
        toggle('渲染云',True),toggle('花俏的树叶',True),toggle('华丽气泡',True),toggle('改善输入反馈',True),
        choices('UI 档案',['经典','携带版'],description='选择袖珍（移动）或经典界面布局')),
    section('视图自定义','不受干扰地构建、传输或截取截图',toggle('全屏'),toggle('隐藏手'),toggle('隐藏纸娃娃'),toggle('隐藏 HUD'),
        slider('HUD 不透明度',1.,description='平视显示器可以看到的范围'),action('更改安全区画面','更改'),
        toggle('视野可通过游戏修改',True),toggle('显示玩家名称',True),toggle('显示自动保存图标',True)),
    section('无障碍：视频','让《Minecraft》玩起来更舒适的控制工具',GUI_SCALE,
        toggle('超大的新 UI',description='增加 UI 的大小以提高清晰度和阅读舒适度'),toggle('屏幕动画',True),slider('全景滚动速度'),
        toggle('视角摇晃',True),slider('伤害倾斜'),toggle('摄像机摇晃',True),toggle('轮廓选择',True),
        action('重置为默认设置','重置',description='恢复所有视频设置到原始值',reset=True))],
 'audio': [section('','',*[slider(title,value,description=description) for title,value,description in [
    ('全局',.5,'游戏的整体音量'),('音乐',.3,'背景音乐'),('音效',1.,'调整音效音量'),('环境音频',1.,'环境产生的环境声音'),
    ('方块',1.,'放置或移除方块时的声音'),('敌对生物',1.,'比如僵尸和骷髅'),('友好生物',1.,'比如动物和村民'),
    ('玩家',1.,'你和附近其他玩家发出的声音'),('音乐方块',1.,'比如唱片机和音符盒'),('天气',1.,'雨、风等天气的声音'),
    ('文本转语音',1.,'游戏文本转语音的声音')]] + [action('重置为默认设置','重置',description='将所有选项设置为原始值',reset=True)])],
 'account': [section('','',row('profile','玩家代号:','Player'),action('更改玩家代号'),action('管理账号'),action('隐私和在线安全'),
    action('管理 Realms 成员邀请','管理'),row('identifiers','DID: 00000000000000000000000000000000',description='MCID: 0000000000000000'))],
 'storage': [section('','',row('storage','本地存储',.16),action('清除市场缓存','晴天'),action('清除下载存储','晴天'),
    action('清除截图缓存','晴天'),action('删除本地截图','删除'),
    action('世界','管理',description='50.5MB - 7 项目'),action('世界模板','管理',description='65.0MB - 1 项目'),
    action('资源包','管理',description='500.8MB - 11 项目'),action('行为包','管理',description='1.7MB - 2 项目'))],
 'creator': [section('','',toggle('启用复制坐标',description='复制并粘贴相对的世界内坐标')),
    section('内容日志设置','',toggle('启用内容日志文件'),toggle('显示内容日志 UI'),
        toggle('在加载期间出错时显示内容日志 UI',True,enabledBy='显示内容日志 UI'),
        choices('GUI 日志级别',['详细','信息','警告','错误'],2),action('内容日志历史','查看',disabled=True),
        action('删除旧的日志','删除'),row('log_path','内容日志位置：',description='%APPDATA%/Minecraft Bedrock/logs/ContentLog.txt')),
    section('脚本调试器设置','',toggle('需要密码'),
        row('field','密码','',visibleWhen=('需要密码',[True]),nested=True),
        toggle('加载时附加调试器'),
        row('field','主机','localhost',visibleWhen=('加载时附加调试器',[True]),nested=True),
        row('field','端口','19144',visibleWhen=('加载时附加调试器',[True]),nested=True),
        slider('连接超时',0,steps=11,maximum=100,unit=' 秒',visibleWhen=('加载时附加调试器',[True]),nested=True)),
    section('脚本诊断设置','',row('notice','需要重启客户端才能查看内存统计信息'),toggle('启用客户端诊断'),
        action('删除诊断和分析器截取','删除',description='删除《Minecraft》日志文件夹中生成的文件')),
    section('脚本监视器设置','',slider('以下时间过后中断：',7,steps=18,minimum=3,maximum=20,unit=' 秒'),
        toggle('脚本尖峰警告'),
        slider('尖峰超过',1,steps=10,maximum=900,unit=' 毫秒',visibleWhen=('脚本尖峰警告',[True]),nested=True),
        toggle('慢速脚本警告'),
        slider('平均超过',1,steps=10,maximum=90,unit=' 毫秒',visibleWhen=('慢速脚本警告',[True]),nested=True)),
    section('设备信息设置','',toggle('启用内存层覆盖'),
        row('dropdown','内存层',4,options=['超低','低','中','高','超高'],visibleWhen=('启用内存层覆盖',[True]),nested=True)),
    section('编辑器设置','',toggle('收集网络指标',True)),
    section('文本筛选','',toggle('启用调试文本筛选延迟覆盖'),
        slider('文本筛选延迟',0,steps=6,maximum=5,unit=' 秒',visibleWhen=('启用调试文本筛选延迟覆盖',[True]),nested=True))],
}

KEYBOARD_BINDINGS = [('攻击/摧毁','按钮 1'),('选取方块','按钮 3'),('使用物品/放置方块','按钮 2'),('丢弃物品','Q')] + [
    ('快捷栏 %d'%i,str(i)) for i in range(1,10)] + [('物品栏','E'),('合成','Z'),('切换视角','F5'),('跳跃/向上飞','空格'),
    ('潜行/向下飞','SHIFT'),('疾跑','控制'),('向左移动','A'),('向右移动','D'),('向后移动','S'),('向前移动','W'),
    ('生物效果','未指派'),('聊天按钮','T, 返回'),('输入指令','斜杠'),('表情','B'),('识别方块','未指派'),
    ('截图','F2'),('社交抽屉','N'),('菜单左选项卡','左括号'),('菜单右选项卡','右括号'),('菜单取消','按钮 5'),('打开通知','未指派')]
CONTROLLER_BINDINGS = [('跳跃/向上飞','A'),('丢弃物品','down'),('攻击/摧毁','RT'),('使用物品/放置方块','LT'),
    ('合成','X'),('物品栏','Y'),('向左循环物品','LB'),('向右循环物品','RB'),('切换视角','up'),('潜行/向下飞','B'),
    ('疾跑','LS_press'),('缓慢飞起',''),('缓慢下降','RS_press'),('表情','left'),('打开通知/社交抽屉/生物效果','view'),
    ('聊天按钮','right'),('向左移动','LS_left'),('向右移动','LS_right'),('向后移动','LS_down'),('向前移动','LS_up'),('选取方块',''),('识别方块','')]
PAGES['keyboard'][1]['rows'] = [row('binding',label,key) for label,key in KEYBOARD_BINDINGS]
PAGES['controller'][1]['rows'] = [row('controller_binding',label,key) for label,key in CONTROLLER_BINDINGS]

LANGUAGES = [('Bahasa Indonesia','Indonesia'),('Dansk','DA'),('Deutsch','Deutschland'),('English','UK'),('English','US'),
    ('Español','España'),('Español','México'),('Français','Canada'),('Français','France'),('Italiano','Italia'),
    ('Magyar','HU'),('Nederlands','Nederland'),('Norsk bokmål','Norge'),('Polski','PL'),('Português','Brasil'),
    ('Português','Portugal'),('Slovenský','SK'),('Suomi','FI'),('Svenska','Sverige'),('Türkçe','Türkiye'),('Čeština','Česká republika'),
    ('Ελληνικά','GR'),('Български','BG'),('Русский','Россия'),('Українська','Україна'),('日本語','日本'),('简体中文','中国'),('繁體中文','台灣'),('한국어','대한민국')]
