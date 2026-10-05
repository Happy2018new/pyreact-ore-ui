# 验证与复现

本页记录 2026-10-05 的设置测试页。当前示例有 13 个分区，包含资源包和好友页面。旧图鉴的回归次数不能证明当前页面通过。

## 结果的范围

最新完整控件像素结果和分批交互检查保存在 [validation-latest.json](validation-latest.json)。实际裁切、并排图、差分图和叠加图位于 `docs/images/reference/audit/`。每张图保留文字、图标、边框与外围 1 个逻辑像素。

**最新 26 个状态中，0 个达到完整控件原像素一致。** 采集成功与视觉通过是两个独立字段，工具会在任一状态存在差异时返回非零退出码。早期边框条带的零误差结果只属于那一条边框，不能作为完整控件或整个页面通过的证据。

行为回归检查业务回调、原生值、实际命中、拖动和窗口边界。它不能证明外观与国际版完全一致。窗口适配也不等同于手机硬件验证。

## 离线检查

外部依赖为 PyreactMC commit `9580d0123584ae8b4b4b3a7b0357250e151c54cd`。游戏侧代码用真正的 Python 2.7.13 执行契约测试。

```powershell
python -X utf8 tools/build_skin.py
python -X utf8 tools/build_demo.py --pyreact 'D:/Path/To/PyreactMC' --output .runtime/settings_demo_addon
$env:ORE_PYTHON2 = 'D:/Path/To/Python27/python.exe'
$env:ORE_DEMO_PATH = (Resolve-Path '.runtime/settings_demo_addon').Path
python -X utf8 -m unittest discover -s tests -v
```

12 项宿主检查包括资源元数据、像素裁切规则、实例重载配置、部署与重复安装。内部 30 项 Python 2 组件契约覆盖受控与非受控状态、整数滑块吸附、禁用行为、文字换行、图片比例、独立资源包和玩家回调、页签提示、模态命中区域的无重叠分割以及示例构建。离线 ModSDK 替身不代表真实输入命中，后者由游戏回归验证。

## 实际游戏回归

按 `.agents/skills/pyreact-debugging` 创建专用实例。构建目录的 `.mcdev.json` 使用 `auto_hot_reload_mods=false` 和 `auto_hot_reload_ui=false`，修改 Python 结构或 native 模板后使用受管停止与启动，确保载入完整构建。

```powershell
$scripts = '.agents/skills/pyreact-debugging/scripts'
$raw = python -X utf8 "$scripts/instances.py" start --project .runtime/settings_demo_addon --owner ore-ui --preset ui --game-exe 'D:/Path/To/Minecraft.Windows.exe'
$instance = ($raw -join "`n") | ConvertFrom-Json
python -X utf8 tools/verify_settings.py --session $instance.session_file --owner ore-ui --phase all
python -X utf8 tools/verify_settings_viewports.py --session $instance.session_file --owner ore-ui
python -X utf8 tools/verify_reference_controls.py --session $instance.session_file --owner ore-ui
```

`verify_settings.py` 覆盖 13 页，包含五种按钮、禁用项、复选框、开关、单选、相接选项、页签、分页、输入、下拉菜单、连续与整数滑块、消息、帮助、弹窗、抽屉、资源包激活与停用、好友选项、资源搜索及动画暂停。整数滑块逐档检查业务整数、原生值、手柄中心和两端是否越界。`--phase social` 额外在鼠标与 F11 模式真实输入好友查询及弹窗名称，检查过滤列表、焦点、遮罩拦截和关闭后事件清理。`--phase overlays` 在两种模式检查截图后的再次点击、短菜单内容范围、嵌套下拉选项、长菜单关闭和背景拦截。这些阶段也包含在 `--phase all` 中。`--phase mouse`、`touch`、`sliders`、`remaining`、`visual`、`calibrated`、`radio` 、`social` 和 `overlays` 可复现指定范围。

真实 hover 与点按使用参考技能的 PID 绑定绝对输入。MCDK 键盘用于 F11 切换和文字编辑，拖动使用绑定窗口的绝对输入。输入投递后仍检查状态，不能把投递成功当作业务成功。桌面锁、前台检查和进程创建时间共同约束输入。

`verify_settings_viewports.py` 在 1200×540、1008×1440 和 540×800 客户区逐页检查字形、图片比例和横向边界，并点按窄屏目录、下拉菜单、弹窗、好友面板及操作菜单。报告记录实际客户区与逻辑尺寸，不能把未达到请求大小的窗口算作该尺寸通过。

触屏验证先关闭 UI，再按 F11，按 F8 重开，结束后恢复原输入模式。`hardware_touch_tested=false` 表示 Windows 单指模拟。Android、iOS、软键盘、输入法候选窗、多指和手机安全区尚无硬件结果。

## 国际版参考与严格比较

使用 `.agents/skills/bedrock-ore-reference`，本机国际版为 `1.26.5203.0`。开始弹窗有“稍后”和“开始采集”，五秒无回应自动接受。完成弹窗有“知道了”，五秒自动关闭。自动操作前后必须分别调用 `begin` 和 `finish`，编码期间结束自动模式。

国际版设置、游戏列表、存档通用、高级、多人游戏、资源包和好友页面分别采集。selected、unselected、hover、disabled 独立记录。世界设置只移动指针观察已有状态，不为采集改变存档。早期仅用 SetCursorPos 的 hover 截图不属于最终参考。

`tools/reference_cases.json` 记录 26 个完整控件状态，包含参考版本、客户区、鼠标位置、原截图哈希、裁切端点与裁切哈希。参考 PNG 随仓库保存在 `docs/images/reference/native/`，复查不依赖开发机的忽略目录。

`verify_reference_controls.py` 将实际游戏设置为 2016×1172 客户区，测量并验证每逻辑像素对应 4 个物理像素。国际版客户区宽 2015，两个客户端的控件尺度相同，不能把窗口宽差当成缩放差。裁切使用半开区间，分别舍入两端。接受比较使用固定端点，不调整尺寸、不搜索偏移、不隐藏文字、不裁掉边缘，容差为零。

```powershell
python -X utf8 tools/verify_reference_controls.py --session '<session.json>' --owner ore-ui --output .runtime/reference-latest
python -X utf8 tools/publish_validation.py --audit .runtime/reference-latest --client-version 3.9.0.401155 --engine-version 1.21.120.0 --behavior input=.runtime/settings-verification viewports=.runtime/settings-viewports
```

并排图左侧为国际版，右侧为实际 Pyreact 游戏渲染。差分图显示实际误差，叠加图用于观察位置。`publish_validation.py` 发布现有比较结果，不把失败改为成功。

## 已知边界

实机为网易开发客户端 `3.9.0.401155`，可执行文件的 FileVersion 与 ProductVersion 均为 `1.21.120.0`。分发客户端版本和引擎文件版本分别记录。本机 3.10 尚未建立可用 IPC，不能声称 3.10 实机通过。源资产来自用户的 Ore 3.10 ZIP。

中文与西文均提前烘焙。Gameface 与 ModSDK 对抗锯齿、分数坐标和纹理采样的处理存在可见差异，完整比较会保留这些误差。编辑状态保留原生光标与输入法。

当前国际版部分旧下拉设置已改为分段选项，旧版下拉弹层依据用户图片和源 CSS。菱形单选依据源 CSS 与 Wiki 设计系统，目前缺少本机同版本 native 单选截图。下拉、单选及其他未进入 26 状态清单的控件不能声称已通过同版本原像素验收。全部 pressed、键盘与手柄焦点、整页视觉一致性仍需补充。

早期采集和条带结果保留在 [international-evidence.json](international-evidence.json)，属于历史范围。当前结论以 [validation-latest.json](validation-latest.json) 为准。
