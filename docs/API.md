# Ore 公共 API

所有组件用 `@Component` 定义。`style` 必须是宿主 Pyreact 的 `Style`；`key`/`ref` 按 Pyreact 通用 Element 语义使用。props 用小驼峰，枚举使用下面列出的类常量。

| 组件 | 参数与默认值 |
| --- | --- |
| `OreImage` | `name` 必填，`style=None`，`animate=False`，`color=None`，`children=None`，`contain=None`。普通图片默认等比完整显示，九宫格默认拉伸，`contain=True` 可预览原始九宫格图片。动画保留每帧时长，暂停保持当前帧，首次静止显示第一帧。 |
| `OreIcon` | `name=OreIconName.check`；`size=12`；`style=None`；`color=None`。size 是高度，宽度按资源比例计算。 |
| `OreText` | `content=''`，`style=None`，`color=OreColors.text`，`fontSize=FontSize.normal`，`textAlign=TextAlignment.left`。中文使用 Noto Sans SC Regular，西文使用源包 Minecraft Seven 烘焙字形，最小字号 7，行高为字号的 1.5 倍，无文字阴影。 |
| `OreButton` | `label=''`；`variant=OreVariant.secondary`；`elevated=True`；`disabled=False`；`focused=False`；`onClick=None`；`style=None`；`labelStyle=None`；`icon=None`；`children=None`。默认高 24、最小宽 36、水平 padding 8。传 children 时完全自定义内容。 |
| `OreCard` | `style=None`，`children=None`。默认 padding 8，不透明灰色表面，尺寸可由 children 决定。原始边框纹理仍可通过 OreImage 查询。 |
| `OreListItem` | `title=''`，`description=''`，`icon=None`，`selected=False`，`disabled=False`，`onClick=None`，`style=None`，`children=None`。默认宽 100%，有描述时高 40，否则高 28，padding 6。长内容可覆盖 height。selected 在 default、hover、pressed 中均保留选中框。 |
| `OreTabs` | `options`、`value` 必填；`onChange=None`，`disabled=None`，`style=None`。options 接受 `(显示文本, 值)` 或 `(显示文本, 值, 图标名)`，禁用值通过 disabled 列表指定。连排页签有独立选中皮肤和底部短线，点击触发 `onChange(value)`。 |
| `OreCheckbox` | `value` 省略即非受控；`defaultValue=False`；`onChange=None`；`disabled=False`；`style=None`。默认 16×16。回调 `onChange(next_bool)`。 |
| `OreSlider` | `value` 省略即非受控；`defaultValue=0.5`；`steps=1`；`onChange=None`；`disabled=False`；`style=None`；`tickLabels=None`。steps=1 的范围为 0..1，steps>1 的范围为 0..steps-1，输入和原生回调都会取最近整数，并同步手柄值。tickLabels 按各档位置居中显示。禁用使用灰色皮肤并阻断原生触摸。 |
| `OreProgress` | `value=0`；`style=None`；`color=OreColors.primary`。value 以 0..1 裁剪；默认高 5、宽 100%。 |
| `OreDialog` | `visible=False`，`title=''`，`message=''`，`confirmLabel='确定'`，`onConfirm=None`，`onClose=None`，`children=None`，`confirmVariant=OreVariant.primary`。不透明弹窗按内容收紧高度，最大 260×220，屏幕四边至少留 12。长正文独立滚动，标题和页脚固定。背景、取消及关闭图标调用 onClose。调用者管理 visible。 |

新增的公共控件：

| 组件 | 参数与默认值 |
| --- | --- |
| `OreField` | `label=''`；省略 `value` 为非受控；`defaultValue=''`；`onChange=None`；`disabled=False`；`placeholder=''`；`style=None`。24 高的原生单行文本框，上边缘有暗色内凹边。空值提示在框内显示，不写入原生值，编辑时隐藏。禁用阻断原生触摸。 |
| `OreDropdown` | `options=None`，格式 `(文本, 值)`，`value` 和 `defaultValue` 可省略，`onChange=None`，`placeholder='请选择'`，`disabled=False`，`style=None`，`title='请选择'`。浅灰按钮展开为居中灰色菜单，标题居中，关闭按钮有 hover 底色，选项间有细分隔线。选中项右侧显示勾号，超过五项时可滚动。 |
| `OreSwitch` | `value` 可省略，`defaultValue=False`，`onChange=None`，`disabled=False`，`label=''`，`style=None`。Ore 方形手柄和开关标记，回调为布尔值，默认 30×16。hover 与按下使用较深手柄，标签本身不切换状态。 |
| `OreRadio` | `options`、`value`、`onChange` 必填；`disabled=None` 为禁用值列表；`style=None`。受控互斥单选，选中项保留白框。 |
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
| `OreSettingsSection` | `title=''`，`description=''`，`children=None`，`style=None`。带标题的连续设置行。 |
| `OreSegmentedControl` | `options` 和 `value` 必填，`onChange=None`，`disabled=False`，`disabledOptions=None`，`style=None`。options 为 `(文本, 值)` 或 `(文本, 值, 图标名)`。绿色选中项有居中的底部白色短线，禁用项可逐项指定。 |
| `OreIconButton` | `icon='cross_white'`，`onClick=None`，`disabled=False`，`size=20`，`color=None`，`style=None`。透明默认背景的图标按钮。 |
| `OreWorldCard` | `title=''`，`subtitle=''`，`mode=''`，`image='world_demo_screen_big'`，`onOpen=None`，`onEdit=None`，`disabled=False`，`style=None`。完整比例的世界预览，下方名称与日期，打开和铅笔编辑分别回调。 |
| `OreSettingsScreen` | `title='设置'`，`navigation=None`，`children=None`，`onClose=None`，`scrollKey='ore_settings_scroll'`，`activeItem=None`，`style=None`。浅灰顶栏、灰色侧栏和独立滚动内容；窄屏用目录抽屉，activeItem 变化时收起目录。 |

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

原生按钮提供 default、hover、pressed 三态，`focused` 由调用者指定。禁用控件不绑定业务回调，滑块和输入框调用 `SetTouchEnable(False)`。OreDialog、OreDrawer、OreDropdown 将 Modal 子树挂到当前 render root，避免祖先滚动视口裁剪遮罩。正文自动滚动，内部点击被表面拦截，背景点击关闭。
