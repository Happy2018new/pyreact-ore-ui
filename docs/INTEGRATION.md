# 接入与部署

这是客户端 UI 库。宿主客户端包下的 `oreui` 与 `pyreact` 必须同级，所有导入通过相对路径进入宿主的同一个框架实例。不要把 oreui 添加到服务端入口，不要在同一 Mod 内为它创建第二份 navigator / runtime。

## 已有 Pyreact 模组

1. 复制 `oreui/` 到 `behavior_pack/<client_package>/oreui/`。
2. 复制 `resource_pack/textures/pyreact_ore/` 到你的资源包同名路径；可用 deploy 工具选择 core。
3. 用 deploy 工具合并 `OreUI.json`、`PyreactBase.rootBase` 的 Ore 模板以及 `_ui_defs.json` 注册条目。
4. 在 UI 页面中 `from .oreui import ...`，沿用原有初始化与导航方式。

```powershell
python -X utf8 tools/deploy.py `
  --client-package 'D:/MyMod/behavior_pack/my_client' `
  --resource-pack 'D:/MyMod/resource_pack' --assets core
```

工具检查依赖和 `_ui_defs.json`，追加 `ui/OreUI.json` 注册及 `ore_glyph_tmpl`、`ore_field_text_tmpl`、`ore_input_tmpl`、`ore_slider_tmpl`、`ore_scroll_tmpl` 隐藏模板。宿主原有模板不被替换，重复部署不会追加重复条目。工具不改变资源包 manifest、模组系统注册或业务代码。库升级会覆盖目的目录中同名的 Ore 文件和纹理。

## 新建示例

```powershell
python -X utf8 tools/build_demo.py --pyreact 'D:/Path/To/PyreactMC'
```

完整例子生成在 `.runtime/demo_addon/`，依赖源码 fingerprint 写在该目录 `dependency.json`。第一次部署从指定 PyreactMC 复制 runtime/template/LICENSE/NOTICE。后续构建复用已有 runtime，不用新版本悄悄覆盖它；更新 runtime 时使用新的 `--output` 目录。

模组入口是 `ore_demo/modMain.py`，注册客户端系统；系统首次初始化开启 debug，监听 `UiInitFinished` 并打开控件图鉴。关闭后可用 F8 重新打开，销毁时注销本系统监听。示例没有服务端业务、世界方块写入或联网能力。

## 包选型

`--assets core` 包含 gameplay 核心控件资源、世界图标、资源包与好友组件使用的预览及图标。`--assets all` 包含全部 589 项导入图片。两种包都包含 OreUI.json、生成的控件皮肤、完整字体图集、国际版参考派生图标和 OFL 许可证。完整 catalog 随组件提供，因此部署 core 后，渲染额外图片前须确认对应 PNG 已部署。

```powershell
python -X utf8 tools/package_library.py --assets core
python -X utf8 tools/package_library.py --assets all
```

推荐用 ZIP 中的 deploy 工具完成模板合并。仅复制 Python 和纹理会缺少 Ore 模板。手工部署时也须添加 OreUI.json 并向 rootBase 注册上述隐藏模板。自定义 ScreenNode 挂载点必须包含同样的模板，或继承已合并的 PyreactBase.rootBase。包不捆绑 Pyreact、技能、游戏实例、编译缓存或示例世界。

## 兼容与来源

当前适配基于 PyreactMC commit `9580d01` 的 Image、Button、Slider、Input、Dropdown、Toggle 和 Modal 接口。`_button.py` 补齐 state image 切片；`_slider.py` 和 `_input.py` 补充原生 `SetTouchEnable` 禁用路径，并使用 Ore 皮肤模板。填充布局、回调注册和卸载沿用宿主。升级框架时先运行运行时 contract tests，再检查游戏 hover/press、拖动、文本输入和 F11 模式；不依赖上游尚未实现的复杂 buttonBuilder 子树。

`OreListItem(selected=True)` 在 default / hover / pressed 中保持独立的选中边框，悬停仍使用明亮的 hover 贴图；`OreTabs` 保留当前页签的 focused 外观。禁用的按钮、列表项、复选框和滑块不绑定业务回调；滑块和输入框还调用原生 `SetTouchEnable(False)`。

资源路径统一在 `textures/pyreact_ore/`，原版纹理不被覆盖。PyreactBase 仅追加 Ore 隐藏模板。多个模组使用同版本资源可以共享相同路径，不同版本混装时需统一版本或重命名资源并同步 catalog。

需要嵌套列表时使用 `OreScrollView`。当前宿主的滚动 content_h 会把内层被裁剪的长内容向外传播，导致外层尾部空白；本库 `_scroll.py` 使用 Ore 滚动条模板，保留原生输入，在计算滚动范围时停止于嵌套视口。升级 Pyreact 后重点复核此内部适配路径。原生滚动位置 API 使用 ScrollView 根控件；对内部同名 scroll_view 节点调用，在本机版本没有更新实际位置。

导入源包的权利归相应权利人。MIT 只覆盖本库原创代码。使用/再分发前保留 THIRD_PARTY_NOTICES，并遵守 PyreactMC LICENSE/NOTICE；部署工具会同时复制依赖的许可文件。
