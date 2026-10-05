# 字体渲染

OreText 使用提前烘焙的 Noto Sans SC Regular 中文字形和源包 Minecraft Seven 西文字形，与 better-building-editor 采用相同的图集方式。字体来自用户提供的新 ZIP，烘焙尺寸为 64 像素，图集为 2048×2048。完整 cmap 提供 30759 个字形，共 50 页，覆盖后续模组输入的中文名称，不依赖示例里的固定文案。中文基线为 69，西文基线为 64，可通过 `--latin-baseline` 调整。西文使用 `Minecraft-Seven-66398119c2c20ee73019.otf`，数字 advance 为 38，先前的 v4 字体为 48。源包字体没有附加开源许可，不能将整套图集都视为 OFL 内容。

`tools/build_typography.py` 生成纹理和 `oreui/_font_atlas.py`。需要 Pillow 和 fontTools，字体许可证随图集部署在 `textures/pyreact_ore/type/OFL.txt`。

```powershell
python -X utf8 tools/build_typography.py --font 'D:/Fonts/NotoSansSC-Regular.otf' --latin-font 'D:/Fonts/Minecraft-Seven.otf' --latin-baseline 64 --license 'D:/Fonts/OFL.txt'
```

布局和绘制共享 advance、基线和换行规则，默认行高为字号的 1.5 倍。默认像素字体采用源 CSS 的 `letter-spacing: 0.04rem`，对应 0.2 个游戏 UI 单位。测量、居中、换行和实际绘制使用同一字间距。逗号、句号和右括号会与前一个字一起换行。最小字号为 1 个游戏 UI 单位，普通正文推荐使用 7 或更大。缺失字形显示替代符，不会静默删除文字。

当前 PyreactMC 没有自定义文字测量钩子。本库安装一个限定作用范围的适配：只有 OreString 文本使用图集测量，普通 Label 仍走宿主的原生测量。另一处适配只为本库 Label 解析百分比和 flex 祖先的可用宽度。初始化发生在客户端控件首次挂载时，import 不会创建游戏控件。升级 PyreactMC 时须复核 `_resolve_label_max_width` 和文字测量签名。

文字的原生 Label 保留逻辑文本属性，实际 ink 由 bilinear 字形图像显示。每个 Label 保存自己的可增长字形池，更新文本时复用已有控件，卸载父控件时一起释放。

资源包说明可使用 `OreText(fontFamily=OreFont.body, fontSize=7, lineHeight=10)`。正文西文来自源包 `NotoSansMerged-Regular-5df70ade1ecaa8cdc5e2.ttf`，另烘焙 671 个拉丁与标点字形到一页 `body_000.png`，其余字符共用现有中文图集。正文的字距为 0.125 个逻辑像素，默认像素字体仍为 0.2。测量、换行和实际绘制使用同一组字形与行高参数，切换字体或行高会触发布局更新。

```powershell
python -X utf8 tools/build_typography.py --body-font 'D:/Fonts/NotoSansMerged-Regular.ttf'
```

正文图集随 core 和 all 部署。`fontSize` 现在允许小于 7，供参考中的紧凑操作标签使用；例如资源包的“激活”文字使用字号 5。

OreField 未编辑时使用同一套烘焙字形。进入编辑状态后，原生 display_text 显示文字、光标和输入法组合串，烘焙层自动隐藏。编辑状态保留游戏字体，这是原生光标定位的边界，与参考编辑器保持一致。两层都位于原生裁剪面板内，长输入不会盖到框外。

烘焙字体仍有可测量的栅格差异。国际版 Gameface 的文字抗锯齿与 ModSDK 字形纹理采样不同，部分字形宽度和边缘有一到三个物理像素差异。完整控件比对会保留这些差异，不用排除文字的边框结果代替文字验收。
