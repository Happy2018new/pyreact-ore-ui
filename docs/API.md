# Ore 公共 API

所有组件用 `@Component` 定义。`style` 必须是宿主 Pyreact 的 `Style`；`key`/`ref` 按 Pyreact 通用 Element 语义使用。props 用小驼峰，枚举使用下面列出的类常量。

| 组件 | 参数与默认值 |
| --- | --- |
| `OreImage` | `name` 必填，`style=None`，`animate=False`，`color=None`，`children=None`，`contain=None`。普通图片默认等比完整显示，九宫格默认拉伸，`contain=True` 可预览原始九宫格图片。动画保留每帧时长，暂停保持当前帧，首次静止显示第一帧。 |
| `OreIcon` | `name=OreIconName.check`；`size=12`；`style=None`；`color=None`。size 是高度，宽度按资源比例计算。 |
| `OreText` | `content=''`，`style=None`，`color=OreColors.text`，`fontSize=FontSize.normal`，`textAlign=TextAlignment.left`，`fontFamily=OreFont.pixel`，`lineHeight=None`。中文使用 Noto Sans SC Regular，默认西文使用 Minecraft Seven。`OreFont.body` 改用烘焙的 Noto Sans 西文字形，适合说明正文。字号最小为 1，紧凑操作标签可用 5。默认行高为字号的 1.5 倍，可用 `lineHeight` 指定逻辑像素值。无文字阴影。 |
| `OreButton` | `label=''`；`variant=OreVariant.secondary`；`elevated=True`；`disabled=False`；`focused=False`；`onClick=None`；`style=None`；`labelStyle=None`；`icon=None`；`children=None`。默认高 24、最小宽 36、水平 padding 8。传 children 时完全自定义内容。 |
| `OreCard` | `style=None`，`children=None`。默认 padding 8，不透明灰色表面，尺寸可由 children 决定。原始边框纹理仍可通过 OreImage 查询。 |
| `OreListItem` | `title=''`，`description=''`，`icon=None`，`selected=False`，`disabled=False`，`onClick=None`，`style=None`，`children=None`。默认宽 100%，有描述时高 40，否则高 28，padding 6。长内容可覆盖 height。selected 在 default、hover、pressed 中均保留选中框。 |
| `OreTabs` | `options`、`value` 必填；`onChange=None`，`disabled=None`，`style=None`，`keyboardHints=False`。options 接受 `(显示文本, 值)` 或 `(显示文本, 值, 图标名)`，禁用值通过 disabled 列表指定。选中项下沉，未选中项抬起，相邻边框共用。keyboardHints 显示可点按的方括号提示，循环到下一个可用选项；组件不注册键盘按键。 |
| `OreCheckbox` | `value` 省略即非受控；`defaultValue=False`；`onChange=None`；`disabled=False`；`style=None`。默认 16×16。回调 `onChange(next_bool)`。 |
| `OreSlider` | `value` 省略即非受控；`defaultValue=0.5`；`steps=1`；`onChange=None`；`disabled=False`；`style=None`；`tickLabels=None`。steps=1 的范围为 0..1，steps>1 的范围为 0..steps-1。拖动时业务接收最近整数，松手后原生手柄吸附到该整数。手柄中心在两端各留 8 个逻辑像素，端点数字保持这个内缩；中间数字按整段轨道排列，与实际刻度中心对齐。`tickLabels` 应提供与 steps 相同数量的标签。禁用使用灰色皮肤并阻断原生触摸。 |
| `OreProgress` | `value=0`；`style=None`；`color=OreColors.primary`。value 以 0..1 裁剪；默认高 5、宽 100%。 |
| `OreDialog` | `visible=False`，`title=''`，`message=''`，`confirmLabel='确定'`，`onConfirm=None`，`onClose=None`，`children=None`，`confirmVariant=OreVariant.primary`。不透明弹窗按内容收紧高度，最大 260×220，屏幕四边至少留 12。长正文独立滚动，标题和页脚固定。背景、取消及关闭图标调用 onClose。调用者管理 visible。 |

新增的公共控件：

| 组件 | 参数与默认值 |
| --- | --- |
| `OreField` | `label=''`；省略 `value` 为非受控；`defaultValue=''`；`onChange=None`；`disabled=False`；`placeholder=''`；`style=None`；`search=False`。24 高的原生单行文本框，上边缘有暗色内凹边。search 在左侧放置搜索图标，并为图标保留文字空间。空值提示不写入原生值，编辑时隐藏。禁用阻断原生触摸。 |
| `OreDropdown` | `options=None`，格式 `(文本, 值)`，`value` 和 `defaultValue` 可省略，`onChange=None`，`placeholder='请选择'`，`disabled=False`，`style=None`，`title='请选择'`。浅灰按钮展开为居中灰色菜单，标题居中，关闭按钮有 hover 底色，选项间有细分隔线。选中项右侧显示勾号，超过五项时可滚动。 |
| `OreSwitch` | `value` 可省略，`defaultValue=False`，`onChange=None`，`disabled=False`，`label=''`，`style=None`。Ore 方形手柄和开关标记，回调为布尔值，默认 30×16。hover 与按下使用较深手柄，标签本身不切换状态。 |
| `OreRadio` | `options`、`value`、`onChange` 必填；`disabled=None` 为禁用值列表；`style=None`。受控互斥单选，使用 Ore 菱形指示器，整行可点按。选中、未选中、hover、pressed 和禁用分别绘制。 |
| `OreTag` | `label=''`，`color=None`，`style=None`。默认绿色，高 16，宽度由字形 advance 加 12 计算，列容器中不自动拉满。 |
| `OreBadge` | `label=''`，`color=None`，`style=None`。默认红色，高 16，最小宽 18，宽度随内容增加。 |
| `OreBanner` | `message=''`；`tone='info'`（info/success/warning/error）；`onClose=None`；`style=None`。可关闭的消息横幅；是否移除由调用者决定。 |
| `OreAccordion` | `title=''`；`expanded=False`；`onToggle=None`；`children=None`；`style=None`。受控开合分组，收起时卸载内容。 |
| `OrePagination` | `page=1`；`pages=1`；`onChange=None`；`style=None`。页码裁剪到 1..pages，边界禁止前进/后退。 |
| `OreDrawer` | `visible=False`；`title=''`；`onClose=None`；`side='right'`（left/right）；`children=None`。宽 200、最大屏宽 85% 的全高抽屉；内部吞噬背景输入。 |
| `OreHelp` | `label='说明'`；`message=''`；`style=None`。点按展开/收起提示，触屏也可访问。 |
| `OreScrollView` | `style=None`；`children=None`；`showScrollbar=True`。style 必须给出稳定 height 或 flex，宽度也必须可解析。原生 ScrollView 的本地适配器，嵌套滚动内容在内层视口边界停止向外传播。静态操作沿用宿主 `ScrollView.scroll_to` / `scroll_to_percent` / `get_scroll_position`，参数为 ref 得到的原生根控件。 |

`OreVariant`：`primary`、`secondary`、`neutral`、`destructive`、`realms`。

用于设置页的公共组件：

| 组件 | 参数与用途 |
| --- | --- |
| `OreDivider` | `style=None`。2 高的深色与浅色双线分隔。 |
| `OreNavigationItem` | `label=''`，`icon=None`，`selected=False`，`disabled=False`，`onClick=None`，`style=None`。24 高的灰色侧栏行，选中状态与 hover 独立。 |
| `OreNavigationGroup` | `title=''`，`children=None`，`style=None`。带小标题和分隔线的导航组。 |
| `OreSettingsRow` | `title=''`，`description=''`，`valueText=''`，`children=None`，`layout=OreSettingLayout.inline`，`disabled=False`，`divider=True`，`style=None`。统一标题、说明、右侧控件和分隔线。inline 用于开关，stacked 用于说明在上方的滑块，field 用于输入和分段选项。 |
| `OreSettingsSection` | `title=''`，`description=''`，`children=None`，`style=None`。每段连续的直接 `OreSettingsRow` 子项以一条浅线开始，以一条深线结束，中间保留深浅双线。组件复制行的 props，不修改传入的 Element，保留 key 与 ref。支持嵌套 section，下一组标题前保留空白。直接传入行或行数组即可；自定义包装组件自行组织行时，应在包装内部使用 section。 |
| `OreSegmentedControl` | `options` 和 `value` 必填，`onChange=None`，`disabled=False`，`disabledOptions=None`，`style=None`。options 为 `(文本, 值)` 或 `(文本, 值, 图标名)`。绿色选中项有居中的底部白色短线，禁用项可逐项指定。 |
| `OreIconButton` | `icon='cross_white'`，`onClick=None`，`disabled=False`，`size=20`，`color=None`，`style=None`，`iconSize=8`，`framed=False`。默认透明背景，`framed=True` 使用完整外框和一像素内侧明暗边。好友搜索旁的关闭按钮使用 22×24、iconSize=7。命中区域与图标尺寸分别设置。 |
| `OreWorldCard` | `title=''`，`subtitle=''`，`mode=''`，`image='world_demo_screen_big'`，`onOpen=None`，`onEdit=None`，`disabled=False`，`style=None`。完整比例的世界预览，下方名称与日期，打开和铅笔编辑分别回调。 |
| `OreSettingsScreen` | `title='设置'`，`navigation=None`，`children=None`，`onClose=None`，`onSocial=None`，`scrollKey='ore_settings_scroll'`，`activeItem=None`，`style=None`。浅灰顶栏、灰色侧栏和独立滚动内容。宽屏可显示社交入口，标题始终居中；窄屏用目录抽屉，activeItem 变化时收起目录。 |
| `OreWorldNavigation` | `image='world_demo_screen_big'`，`onPlay=None`，`onRealms=None`，`children=None`，`style=None`。世界预览、游戏按钮、Realms 按钮和成就状态组成的存档编辑导航区。 |

资源包与好友组件：

| 组件 | 参数与用途 |
| --- | --- |
| `OrePackRow` | `title=''`，`thumbnail='grass_block'`，`description=''`，`expanded=False`，`active=False`，`disabled=False`，`onToggle=None`，`onAction=None`，`style=None`。预览与详情在左侧，激活或停用按钮在右侧。两个区域分别回调，禁用时均不触发。 |
| `OrePackGroup` | `title='已拥有'`，`count=None`，`expanded=False`，`onToggle=None`，`children=None`，`style=None`。带数量和开合箭头的资源包分组，收起时卸载内容。直接传入 `OrePackRow` 列表，相邻折叠行共用一像素外框。展开说明之后到下一行保留 6 个逻辑像素，不需要业务页面再加 margin。 |
| `OrePlayerRow` | `name=''`，`status='离线'`，`avatar='no_player_profile'`，`selfPlayer=False`，`online=False`，`onClick=None`，`onOptions=None`，`style=None`。头像与资料在左侧，其他玩家的选项在右侧，在线头像带状态标记。两种点击分别回调。 |
| `OrePlayerGroup` | `title='在线'`，`count=0`，`online=False`，`children=None`，`style=None`。绿色在线组或灰色离线组，标签宽度随文字变化，彩色横线与列表相接；数量为零时显示空状态。 |
| `OreFriendsPanel` | `visible=False`，`onClose=None`，`children=None`，`query=''`，`onSearch=None`，`tab='friends'`，`onTabChange=None`，`style=None`。右侧全高好友面板，宽 188，最大屏宽 90%，包含搜索、关闭、好友和队伍页签及独立滚动列表。 |
| `OreActionMenu` | `visible=False`，`title=''`，`actions=None`，`onClose=None`，`style=None`。actions 是 `(文本, 回调)` 序列。第一项与后续选项分组，宽 238，最大屏宽和屏高 90%。正文在小窗口中滚动，标题和关闭按钮固定。 |

以上资源包和好友组件负责展示与输入回调。示例的激活、停用与玩家操作使用本地状态，实际的游戏资源管理和好友服务由调用模组接入。

`OrePackRow` 和 `OrePlayerRow` 的整行高度均为 36 个逻辑像素。外框由整行绘制，左右按钮之间只保留相接的明暗边，两个命中区域仍然独立。`OrePlayerGroup` 中每个后续玩家行与前一行共用 1 像素外框，行距为 35。资源包说明使用 `OreFont.body`、字号 7、行高 10，并由行组件绘制说明区的侧边和底边。

`OreSettingsScreen` 的左右滚动区域分别绘制固定的半透明顶边。右侧使用约 12.5% 黑色，随其下方滚动内容混色。`OreScrollView` 的滚动块下方有 1 像素、20% 黑色阴影，鼠标与触屏模板共用同一材质。

玩家行默认使用不含状态标记的占位头像，`online=True` 才叠加在线标记。`reference_steve_face` 是当前玩家的历史截图裁切，图片内含在线标记，仅用于在线参考展示。业务模组应传入独立头像资源。

`OreSettingLayout`：`inline`、`stacked`、`field`。灰色侧栏使用 `OreNavigationItem`，带白色选中框的世界列表使用 `OreListItem`。

`OreState`：`default`、`hovered`、`pressed`、`focused`、`disabled`，列表项还使用 `pressed_focused` 和 `disabled_focused`。用于资源查询，不替代原生 `ButtonState`。

`OreIconName`：`check`、`checkMuted`、`close`、`back`、`search`、`settings`、`world`。还可以传 catalog 中任何图片名。

`OreColors`：`background`、`surface`、`raised`、`border`、`text`、`muted`、`disabled`、`darkText`、`primary`、`destructive`。`palette_color('green30')` 等可读取全部 58 个源码 hex 颜色。

横幅 `tone` 使用 `OreTone` 枚举，抽屉 `side` 使用 `OreSide` 枚举。单行输入保留原生光标和输入法，未编辑时显示烘焙字体。帮助气泡可点按，不依赖鼠标悬停。

```python
from .oreui import asset, asset_names, texture, OreImage
from .pyreact import Style

print(asset_names('pressable_'))
print(texture('pressable_primary_default'))
# textures/pyreact_ore/pressable_primary_default
print(asset('pressable_elevated_primary_default'))
# {'src': ..., 'size': (5, 7), 'nineSliceData': (2, 2, 2, 4)}

OreImage(name='animation', animate=True, style=Style(width=14, height=14))
```

`asset(name)` 返回独立元数据副本；src 不含 `.png` 后缀。未识别的资源/变体/状态会抛出明确 ValueError。GIF 的 frames 也复制，调用者更改不会污染 catalog。

原生按钮提供 default、hover、pressed 三态，`focused` 由调用者指定。禁用控件不绑定业务回调，滑块和输入框调用 `SetTouchEnable(False)`。OreDialog、OreDrawer、OreDropdown、OreFriendsPanel 和 OreActionMenu 将模态子树挂到当前 render root，避免祖先滚动视口裁剪遮罩。正文自动滚动，内部点击被表面拦截，背景点击关闭。表面使用普通容器，透明命中区域按布局避开输入框，保留鼠标与 F11 触屏模式下的原生输入焦点。关闭组件时注销拦截按钮的事件处理器。
