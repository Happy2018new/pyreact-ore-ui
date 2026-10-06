# 设置导航与鼠标滚动性能

2026-10-06 在网易 3.10.0.420447 的独立开发实例上测试。客户区为 2020×1156。
本轮只验证快速切页、图标动画、页面缓存、滚动及相关组件契约，没有运行全量组件回归。

## 原因与修改

旧设置示例随选项改变重建内容页和滚动容器，同时销毁并重建大量烘焙字形。
图标还通过 effect 更新状态来挂载动画，增加了一轮布局。MCDK Python CPU 采样确认布局是主要开销。
仅保留隐藏页仍会使其参加整个界面的布局，所以新增缓存同时排除隐藏页布局。

- `OrePageCache` 在公共组件库中提供按需挂载、最多八页的 LRU 保留、激活时回到顶部、尺寸及内容失效检查。
  稳定的页面顺序避免切换时因节点重排触发布局。被淘汰的设置由示例业务层保存，重进后恢复。
- `OreNavigationIcon` 的闪光图像保持挂载，在选中边沿原地重播。切走允许动画结束，再次选中从头开始。
  帧推进直接更新 UV，完成后注销时钟，没有 effect 引起的额外布局。
- `OreSliderRow` 保存行内草稿，在释放时通过 `onCommit` 提交。连续拖动不用反复更新整页状态。
- Ore 滚动模板的鼠标分支使用原生 `scroll_speed=40`。原版 `common.scroll_view_control` 为 15。
  参数依据来自 mc-search 资料库的 `BedrockWiki/json-ui/json-ui-documentation.md` 和
  `GameAssets/resource_packs/vanilla_netease/ui/ui_common.json`。没有添加全局滚轮监听器。

## 实机数据

响应时间从实际按钮回调开始，到首次观察到目标页面的 UI Update。
Update 间隔来自 Python `NavigatorScreen.Update` 的时钟，不能当作 GPU 帧时间或实际 FPS。
CPU 插桩采样单独进行，没有用于下表。基线与最终实例使用相同客户区，启动时 SDK 的逻辑尺寸读回有一像素差异。

| 场景 | 回调数 | 观察到切换的次数 | 整页布局次数 | 切页响应中位数 | UI Update 间隔 P95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 修改前，三个分类，5 次每秒 | 13 | 10 | 10 | 226.8 ms | 208.9 ms |
| 修改后，包含首次访问，5 次每秒 | 17 | 17 | 3 | 21.3 ms | 41.8 ms |
| 修改后，三个已访问分类，10 次每秒 | 25 | 25 | 0 | 23.7 ms | 45.4 ms |
| 修改后，六个已访问分类，10 次每秒 | 31 | 31 | 0 | 19.6 ms | 45.0 ms |

基线中的三次点击收到了回调，但目标页在绘制前被后续点击替代。工具按实际回调时间区间匹配，
不会把后面某次同名页面访问算给前面的点击。未收到任何实际点击回调的采样直接报错。

六分类测试覆盖可访问性、键盘和鼠标、控制器、轻触、通用、视频。响应范围 16.2–32.9 ms。
观察到 31 次动画启动和 254 次帧状态变化，各图标最后一次播放均到达末帧，耗时约 499–532 ms。
帧材质及时间表没有改动，离线契约检查同步核对其 UV。

**首次访问仍有可见成本。** 键盘、控制器、轻触的首次切入分别约 250、174、151 ms。
缓存不能消除首次创建控件的成本，被淘汰后再次访问也需要重建。尚未实现列表虚拟化或分帧创建，
不能把重复切换的结果推广为所有页面首次打开都在一帧内完成。

单次物理滚轮在轻触页移动 **14.0625 → 37.5** 个逻辑像素，约为原来的 2.67 倍。
32 次快速滚轮操作时，UI Update 间隔 P95 为 35.5 ms，最大 37.4 ms，没有超过 50 ms 的样本。
隐藏页滚动位置不变。

## 定向验证

通过 11 项离线组件契约检查及以下实机检查：

- 返回已访问页面时保留同一原生路径，复位滚动，保留编辑值。
- 页面内容在切走前和返回后逐像素相同。对比范围为右侧内容区域，排除开发版 FPS 文字和侧栏动画。
- 隐藏页面在客户区改为 1600×1000 后重新显示，尺寸与新父容器一致。
- 连续访问九个分类后缓存仍只有八页，被淘汰页重新创建并恢复编辑值。
- 关闭设置页后动画及按钮处理器数量为零。
- 鼠标滚轮只影响当前可见页。

F11 补充检查未能在该开发实例切换触屏模式。改用 SDK 模拟触屏后，Windows 拒绝激活目标窗口，
工具停止发送输入并恢复鼠标模式。这一轮没有成功完成触屏手势验证；鼠标分支的测试结果不能替代它。

精简证据：[navigation-performance.json](evidence/navigation-performance.json)。
原始时钟、点击序列、布局时间与图标帧记录保存在本机 `.runtime/rapid-navigation-test/`。
首次异常热重载及无回调的采样均未纳入结论。最终启动关闭自动热重载，避免改变采样期间的运行代码。

```powershell
python tools/profile_navigation.py --session <session.json> --owner <owner> `
  --output .runtime/navigation --rate-hz 10 --cycles 3 --warm-cache `
  --pages accessibility keyboard controller touch general video
python tools/verify_navigation_cache.py --session <session.json> --owner <owner> `
  --output .runtime/navigation-cache
python tools/profile_pages.py --session <session.json> --owner <owner> `
  --output .runtime/touch-wheel --suite settings --pages touch --motion wheel
```
