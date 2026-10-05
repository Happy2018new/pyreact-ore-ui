# 按压状态核验

本轮检查公共可点击组件在默认、悬停、持续按住、移出、移回和松开时的表现。国际版样本来自 Minecraft for Windows 1.26.5203.0，网易实机为 ModSDK 3.10.0.420447，GUI 比例均为 4 个物理像素对应 1 个逻辑像素。

## 组件行为

凸起的 `OreButton`、未选中的 `OreTabs` 和 `OreSegmentedControl` 在按下时将表面与内容下移 2 个逻辑像素，底部凸起随之收起。选中态和平面按钮保持位置。实现位于公共 `NativeOrePressable`，自定义 children 中的图标和文字也随同一个内容面板移动。

移出会取消按压，移回遵循网易原生引擎显示 hover 的行为。松开前先恢复内容位置，再派发一次点击。取消只恢复位置。没有逐帧轮询。

导航、资源包行、玩家行和折叠组使用国际版长按采集的填充色、反光边和角点色。浅色页头按钮单独提供 `OreIconButton(light=True)`。

资源页启用公共 `scrollbarGutter` 属性，为滚动条预留 10 个逻辑像素。该属性同时由 `OreScrollView` 和 `OreSettingsScreen` 暴露。国际版资源页也有滚动条覆盖部分边框、键盘提示的情况，对照图保留了这个差异。

列表真实点击检查额外发现，内部生成的 Python 2 `unicode` key 会让网易原生回调失效，而渲染和 hover 仍正常。`joined_rows` 已改为生成 `str` key，资源包详情、激活、玩家资料和选项按钮共用此修复。

禁用字段改用相同布局的静态模板，避免长按取得原生编辑焦点后提示文字消失。下拉菜单修正标题与列表之间的黑色间隔和灰色分隔，关闭按钮及勾选图标使用测量尺寸。选项按压色为 `#313233`。禁用开关按原版使用平面填充和暗边，不沿用 hover 的亮色反光。

世界卡片的名称区域和编辑按钮共用外框，按下时保留两块按钮之间的反光接缝。编辑图标使用可着色的 alpha 材质，避免黑色原图在灰底上难以辨认。

## 覆盖清单

| 公共组件 | 运行时场景 | 国际版参照 |
| --- | --- | --- |
| OreButton | 五种 variant，凸起、平面、禁用 | 创建新世界、放弃更改，primary 与 secondary 实测；其余保留 ZIP 材质 |
| OreSegmentedControl | 首项选中，中间及末项按压，禁用 | 世界编辑的游戏模式 |
| OreTabs | 文字与图标，选中与未选中，左右键盘提示 | 资源包与好友面板 |
| OreNavigationItem、OreNavigationGroup | 选中与未选中，邻居分隔 | 世界编辑的通用、高级、多人游戏 |
| OrePackRow、OrePackGroup | 多行详情与激活，组标题，禁用行 | 资源包列表 |
| OrePlayerRow、OrePlayerGroup | 多行资料与选项 | 好友列表 |
| OreSwitch | 开关两值，禁用两值 | 世界设置开关 |
| OreSlider | 连续、步进、禁用，拖动 | 文本转语音音量、视角 |
| OreField | 普通、搜索、禁用 | 好友搜索框 |
| OreDropdown | 触发器、选中项、未选中项、关闭、禁用 | 世界模拟距离 |
| OreIconButton | 普通、边框、浅色页头、禁用 | 页头返回、好友关闭、弹窗关闭 |
| OreWorldCard、OreWorldNavigation | 打开、编辑、游玩、Realms | 游戏列表的世界编辑按钮；Realms 未进行账户操作 |
| OreActionMenu、OreFriendsPanel | 菜单项、关闭、搜索、标签页 | 好友操作菜单和好友面板 |
| OreDialog、OreDrawer、OreSettingsScreen | 关闭、确认、取消、返回、社交入口 | 原生确认框和设置页头，布局由库自行组合 |
| OreCheckbox、OreRadio、OreListItem | 未选中、选中、禁用 | ZIP 扩展组件，未取得同形国际版控件的完整状态组 |
| OreAccordion、OrePagination、OreHelp、OreBanner | 展开、翻页、帮助、关闭 | 组合组件，按其公共按钮实现检查，不宣称独立国际版逐像素还原 |
| OreScrollView | 资源页内容避让、实际滚动条拖动 | 资源页右侧滚动条 |

## 采集与复现

国际版操作经 `.agents/skills/bedrock-ore-reference/scripts/desktop.py begin` 开启，显示用户要求的可用性弹窗，结束经 `finish` 通知。采集记录进程身份、窗口尺寸、物理左键状态、实际按住时间和原图 SHA-256。按压态连续采两帧，并强制在 finally 中松开左键。

默认态先进入控件再移到空白处，确保游戏重新命中测试。单纯将鼠标放在原有空白坐标会保留页面挂载时的旧 hover。网易样本还读回原生三态可见性、内容位置和业务事件，避免凭截图名称认定状态。

邻居检查对默认态和按压态逐像素相减。分数坐标控件的占用范围取左上 floor、右下 ceil，纳入边缘实际覆盖的物理像素；完整控件对照仍使用固定半开裁图，不作误差寻优。两种检查的边界与目的分别记录。

```powershell
python -X utf8 tools/verify_reference_sampler.py
python -X utf8 tools/verify_pressed_controls.py --session SESSION --owner OWNER --output .runtime/pressed-audit/acceptance
python -X utf8 tools/verify_pressed_followup.py --session SESSION --owner OWNER --output .runtime/pressed-audit/followup
python -X utf8 tools/publish_pressed_audit.py
python -m unittest discover -s tests -p test_deploy.py
```

`--only packs players` 等参数可以缩小回归范围。Fixture 只组合公共组件，缩略图和头像作为固定内容输入，不绘制替代控件。

## 像素证据的含义

[固定裁图报告](images/pressed-states/comparison.json)保留原始大小，容差为 0，不搜索对齐、不缩放、不遮罩文字。每组包含参考、实现、差分、叠加和并排图。完整控件的 `native_exact` 是严格相等条件，有残余差异就为 false。

[交互结果](images/pressed-states/interaction-report.json)包含 120 个实际输入目标。[触屏及滚动条结果](images/pressed-states/followup-report.json)记录模式切换、点击、弹窗遮罩、滑块拖动和滚动条拖动。[采集器自检](images/pressed-states/sampler-report.json)验证真实左键状态、长按持续帧、固定裁图与邻居不变。

开关关闭态及其禁用态的三种状态裁图达到 0 像素差异。开启态仍有 2 个像素差异，滑块样本约 0.084%。包含文字的分段选项约 2.019%，标签页约 2.822%～3.109%，菜单和列表保留字体等残余差异。完整对照没有全部达到严格相等，发布脚本因此返回非零退出码，并打印 `NOT EXACT`。

本轮发布 22 组控件的 66 份状态对照，其中 6 份达到严格相等。下拉菜单的完整裁图差异为 4.282%，世界卡片底部为 18.542%，primary 按钮为 14.005%～21.579%。世界卡片仍有文字位置、字形和图标像素差异，不能将这些数值全部归因于外围背景。最后一次冷启动重测了世界卡片的三个点击目标，白色编辑图标正常渲染，按住、移出和松开检查通过；完整像素一致性仍未通过。

分段选项和标签页的按压位移、边界结构已按国际版调整。完整图仍包含文字栅格、图标、外围背景及滚动条覆盖差异，因此不能把局部边框一致或交互通过称为整控件 1:1。primary 示例的原版外围是动态全景，实现的测试底色是固定灰色，该差异也保留在报告中。

触屏回归是 Windows 上网易客户端的触屏模拟。关闭 UI 后先发送 F11 并读回模式，本环境中按键未能改变模拟状态，随后使用文档明确对应的 `GameComponentClient.SimulateTouchWithMouse` 切换，并核对 `IsTouchWithMouse` 与 Pyreact 输入模式。测试结束恢复鼠标模式。这不等同于手机真机验证。
