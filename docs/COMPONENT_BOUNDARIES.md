# 设置边界与列表组件的局部验收

2026-10-05。这轮只修复滚动条阴影、设置内容顶边、设置分组边界、玩家列表堆叠、好友关闭按钮、资源包列表和滑块数字对齐。使用用户提供的国际版原始裁图，完成修改后再比较网易实机渲染。没有运行全量回归。

修复位于公共组件中，示例页直接使用这些组件：

| 组件 | 本轮变化 |
| --- | --- |
| `OreScrollView` | 滚动块底部增加覆盖整个宽度的半透明阴影，修正九宫格底边，避免反光行被拉伸。鼠标与触屏模板共用材质。 |
| `OreSettingsScreen` | 右侧内容区增加固定半透明顶边。其颜色与实际滚动内容混合。 |
| `OreSettingsSection` | 连续的直接子项 `OreSettingsRow` 自动绘制浅色开头、深浅两行内部分隔、深色结尾。下一个标题通过自身间距形成留白。复制末项属性时保留 key 和 ref，不修改调用者的 Element。 |
| `OrePlayerRow`、`OrePlayerGroup` | 单行高 36，堆叠步距 35，相邻行共用一条外框。整行绘制外框，资料与更多选项各自绘制内部明暗边并独立响应输入。 |
| `OreIconButton`、`OreFriendsPanel` | 新增 `framed=True`，好友搜索右侧关闭按钮使用该公共样式，尺寸为 22×24，叉号大小为 7。 |
| `OrePackRow`、`OrePackGroup` | 统一外框、相邻行拼接、箭头和操作区位置。详情区补齐侧边与底边，展开后到下一行的 6 像素间距由分组负责。移除示例页对应的 margin 补丁。 |
| `OreText`、`OreFont` | 增加 `OreFont.body` 和 `lineHeight`，资源包说明使用烘焙正文西文字体。默认标题字体保留像素字形。 |
| `OreSlider` | 内部数字按实际绘制轨道定位，端点数字保留滑块拇指的端点内缩。 |

之前修复的导航选中与悬浮明暗边仍在 `OreNavigationItem` 和公共材质中。其半逻辑像素厚度未在本轮放大。列表拼接辅助函数也支持中文 key。

实机客户区为 2016×1164，逻辑尺寸 504×291，GUI Scale 为 4。比较使用原始 PNG 和固定的半开裁切坐标，分别取整两端。没有缩放、自动找偏移，也没有排除文字和图标。参考文件来源、尺寸和 SHA-256 记录在 [manifest.json](images/component-boundaries/references/manifest.json)。

| 比较对象 | 原始尺寸 | 不同像素比例 | 平均通道误差，0–255 | 判定 |
| --- | --- | --- | --- | --- |
| 4 行玩家列表 | 640×564 | 3.3627% | 2.5952 | 行高、共享横边与左右衔接边通过。完整控件仍有文字差异。 |
| 资源包分组与 4 行列表 | 1301×660 | 3.0171% | 2.1914 | 分组尺寸和行边界通过。完整控件仍有文字及小数坐标采样差异。 |
| 展开说明与下一行 | 1301×444 | 4.2331% | 3.3125 | 说明区尺寸、边框和展开间距通过。正文栅格仍有差异。 |
| 关闭按钮默认态 | 88×96 | 0% | 0 | 全部 8448 个像素相同。 |
| 滚动块底部及周围条带 | 24×28 | 0% | 0 | 明暗边、黑色边框、全宽阴影与下方背景均相同。此结果只代表该条带。 |

完整列表的差异阈值分别为 4%、4.5%、6.5%，这是显式的残余误差预算，不代表逐像素完全一致。原始差异图保留在下方。文字抗锯齿、部分字形 advance，以及宽度 1301 对应的小数逻辑坐标仍有可测差异。本轮没有声称整个设置页完全匹配。设置分组只验收首线、中间线、末线和标题前留白。

- [玩家列表并排图](images/component-boundaries/players-comparison.pair.png)，[差异图](images/component-boundaries/players-comparison.diff.png)
- [资源包列表并排图](images/component-boundaries/packs-comparison.pair.png)，[差异图](images/component-boundaries/packs-comparison.diff.png)
- [展开说明并排图](images/component-boundaries/expanded-comparison.pair.png)，[差异图](images/component-boundaries/expanded-comparison.diff.png)
- [关闭按钮并排图](images/component-boundaries/close-comparison.pair.png)
- [滚动块底部并排图](images/component-boundaries/thumb-bottom-comparison.pair.png)
- [设置分组实机图](images/component-boundaries/sections-edges.png)
- [滑块刻度实机图](images/component-boundaries/sliders-alignment.png)
- [示例资源包页](images/component-boundaries/demo-packs-expanded-final.png)
- [示例好友面板](images/component-boundaries/demo-friends-final.png)

并排图左侧为国际版参考，右侧为公共组件实机渲染。测试场景为了保持内容一致，只从参考裁图提取头像和资源包缩略图的内部内容，写入临时测试资源。边框、文字、箭头、操作图标均由公共组件绘制，未将截图边框作为组件皮肤。该临时内容不会加入发布资源包。

[验收报告](images/component-boundaries/report.json)包含 50 项通过的局部断言。鼠标检查包含资料与更多选项独立 hover 和点击、资源包展开与激活互不误触、禁用行阻止操作、关闭好友面板、滑块拖动吸附到 0–4。滑块中间三个数字的可见字形中心与原生刻度中心误差均不超过 0.5 个物理像素。

半透明顶边分别覆盖浅色分组边线、普通背景和控件深色外框后取样，确认不是固定颜色横线。分组浅线为 `#5a5b5c`，深线为 `#333334`。右侧顶边使用约 12.5% 黑色，滚动块底部阴影使用 20% 黑色。

触屏检查使用 PC 的原生鼠标模拟触屏。自动发送 F11 未可靠触发切换，因此使用文档说明与 F11 等效的 `GameComponentClient.SimulateTouchWithMouse`。切换后先点击测试场景空白区域，再同时核对 `IsTouchWithMouse` 和 `INPUT_MODE`，确认进入触屏模式后执行点按与拖动。玩家选项、资源包展开及激活、关闭按钮、滑块吸附均通过。结束后同样核对已恢复鼠标模式。这不是手机真机测试，也没有将 F11 自动化标记为通过。

复现只涉及本轮组件。先安装示例到独立目录，在启动游戏前准备测试内容：

```powershell
python -X utf8 tools/verify_component_boundaries.py --prepare .runtime/component-boundaries/demo_addon
```

用 `pyreact-debugging` 启动该目录并取得受管 session，然后运行：

```powershell
python -X utf8 tools/verify_component_boundaries.py --session '<session.json>' --owner '<owner>' --output .runtime/component-boundaries/acceptance --verify --touch-via-api
```

已有鼠标证据时可只重跑触屏部分：

```powershell
python -X utf8 tools/verify_component_boundaries.py --session '<session.json>' --owner '<owner>' --output .runtime/component-boundaries/acceptance --touch-only --touch-via-api
```

工具读取实际输入模式。若模式不符，会停止依赖该模式的检查，不会把鼠标交互记成触屏通过。省略 `--touch-via-api` 时使用 F11。打开示例 UI 的快捷键仍为 **F8**。
