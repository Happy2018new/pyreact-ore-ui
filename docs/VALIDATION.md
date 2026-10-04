# 验证与复现

本页记录 2026-10-04 的新版设置测试页。旧图鉴的 105 项交互、40 项滑块和 211 项适配记录仅属于旧版，不能证明当前页面通过。

## 离线检查

使用 PyreactMC commit `9580d0123584ae8b4b4b3a7b0357250e151c54cd`，游戏侧代码通过 Python 2.7.13 验证。

```powershell
python -X utf8 tools/build_skin.py
python -X utf8 tools/build_demo.py --pyreact 'D:/Path/To/PyreactMC' --output .runtime/settings_demo_addon
$env:ORE_PYTHON2 = 'D:/Path/To/Python27/python.exe'
$env:ORE_DEMO_PATH = (Resolve-Path '.runtime/settings_demo_addon').Path
python -X utf8 -m unittest discover -s tests -v
```

七项宿主检查包括 589 项资源的尺寸、hash、UV、九宫格、动画时序、刻度工厂、权限图标蒙版和重复安装保留行为。其内部的 26 项 Python 2.7 组件契约检查受控与非受控输入、整数滑块拖动与松手、禁用状态、字体、动画、图像比例及设置页渲染。ModSDK 控件接口由离线替身提供，真实命中另由游戏回归验证。

## 新版实机入口

按 `.agents/skills/pyreact-debugging` 创建专用实例。构建目录的 `.mcdev.json` 使用 `auto_hot_reload_mods=false` 和 `auto_hot_reload_ui=false`，资源修改后受控重启，避免在复制源码中途重载 navigator。

```powershell
$scripts = '.agents/skills/pyreact-debugging/scripts'
$raw = python -X utf8 "$scripts/instances.py" start --project .runtime/settings_demo_addon --owner ore-ui --preset ui --wait 90 --game-exe 'D:/Path/To/Minecraft.Windows.exe'
$instance = ($raw -join "`n") | ConvertFrom-Json
python -X utf8 tools/verify_settings.py --session $instance.session_file --owner ore-ui
python -X utf8 tools/verify_settings_viewports.py --session $instance.session_file --owner ore-ui
python -X utf8 tools/verify_settings_pixels.py --session $instance.session_file --owner ore-ui
```

`verify_settings.py` 验证 12 页、五种按钮、禁用项、复选框、开关、单选、分段选项、页签、分页、输入、下拉菜单、连续与整数滑块、消息、折叠列表、帮助、弹窗、抽屉和资源搜索。游戏业务状态、原生值和真实截图同时保留。`--phase mouse`、`touch`、`sliders`、`remaining`、`visual` 和 `calibrated` 可缩小回归范围。最后一个阶段针对三种权限图标、相接选项的第五个命中区域和修正后的输入框，同时覆盖鼠标及 F11 模拟。

真实 hover 与点按使用参考技能的 PID 绑定绝对输入。MCDK 的指针移动曾出现 Windows 指针已移动、游戏仍命中旧位置的现象，因此不能只看“输入已投递”。键盘、F11 和拖动仍由受管 MCDK 操作。桌面锁、前台检查和进程创建时间同时约束两条输入路径。

`verify_settings_viewports.py` 检查 1200×540、1008×1440、540×800 客户区，逐页检查字形、图片比例和横向边界，真实点按窄屏目录与弹窗。该客户端最小窗口宽度会把 504 强制改成 519，因此紧凑尺寸采用 540，不将未达到请求尺寸的结果计为通过。

完整适配在 `.runtime/settings-viewports-unlocked/result.json` 中通过 172 项检查。完整触屏回归在 `.runtime/settings-touch-unlocked/result.json` 中通过 68 项检查。鼠标阶段在 `.runtime/settings-final/result.json` 中完成 72 项检查，该次完整批次后来因失焦中断，因此不将整个批次标为通过。最终图标和切片修正后，`.runtime/settings-calibrated-input/result.json` 的 18 项定点鼠标与触屏检查通过。这些范围分别记录，避免把中断批次描述成完整成功。

最终修正后的四个受影响页面又通过三种尺寸的 56 项定点适配检查，记录在 `.runtime/settings-viewports-calibrated/result.json`。用 `--pages overview selection toggles fields` 复现。原生分辨率的展示图由 `tools/capture_settings_gallery.py --session <session.json> --owner <owner>` 生成，截图结束恢复原窗口尺寸并回到默认设置页。

触屏验证必须先关闭 UI，再按 F11 切换，按 F8 重开，结束恢复原输入模式。Windows 单指模拟不能替代 Android、iOS、手机软键盘、安全区和多指硬件验收。

## 国际版采集

使用 `.agents/skills/bedrock-ore-reference`，本机国际版为 `1.26.5203.0`。开始弹窗有“稍后”和“开始采集”，五秒无回应自动接受；完成弹窗有“知道了”，五秒自动关闭。真实弹窗测试包含按钮可见性、开始超时、完成超时及点击取消。

设置页、游戏列表、存档通用、高级和多人游戏页分别采集。选中与未选中、开与关、hover、禁用单独记录。世界设置只移动指针采集，不通过切换选项制造参考状态。早期只用 SetCursorPos 的 hover 截图已从最终证据中排除。

[international-evidence.json](international-evidence.json) 记录版本、页面、状态、指针位置、原始 PNG hash、裁切框及比较范围。`audit_reference_skins.py` 比较国际版与生成皮肤，`verify_settings_pixels.py` 比较实际游戏无损像素。比较显式记录缩放和对齐搜索，`native_exact=false` 不能描述为原尺寸 1:1。

实际渲染比较使用 2016×1164 客户区，使控件与参考都采用 4 倍逻辑像素。先用控件主体命中，hover 可见后再测量状态图层，防止隐藏图层的零尺寸导致坐标错误。16 处比较完整收集，结果在 `.runtime/settings-pixels-calibrated/result.json`；裁切图和数据同时发布到 `docs/images/pixel-audit/` 与上述清单。分段选项侧边的四种状态、输入框左边的两种状态、滑块手柄的两种状态与未选中侧栏的默认侧边像素一致。这些边框检查不包含文字与图标，不证明整页一致。

当前国际版的 UI 标度修正使用分段选项，与用户提供的旧版下拉菜单有差异。下拉菜单按用户图片校准，不能冒称已采集到该版本的同款菜单。整页、文字栅格、所有 pressed、键盘与手柄焦点尚未完成逐像素一致验收。

## 版本边界

实机使用网易开发客户端 `3.9.0.401155`。本机 3.10 客户端未建立可用 IPC，不记为 3.10 实机通过。资源来源于用户的 Ore 3.10 ZIP。最新通过范围与像素误差见 [VISUAL_REPAIR.md](VISUAL_REPAIR.md)，截图在 `docs/images/` 和忽略目录 `.runtime/`。
