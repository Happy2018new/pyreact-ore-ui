# 来源与权利

本库原创适配器、组件、工具和示例代码采用根目录 MIT License。下列第三方内容保留各自权利。

## OreUI / Minecraft 资源

`resource_pack/textures/pyreact_ore/` 中的导入图片、生成的颜色与资源元数据来自用户提供的 `ORE饼干-3.10新.zip`。该包的报告说明它是网易开发游戏 `3.10.0.420447/data/gui/dist/hbui` 的 webpack 重构产物，并非 Mojang 原始源码。源模块写有 `Copyright (c) Mojang AB. All rights reserved.`。包内未附针对这些纹理的开源或再分发许可。

Minecraft、OreUI、Mojang、Microsoft、网易及资源相关权利仍归相应权利人所有。根目录 MIT License 不授予这些资产的再分发或商业使用权；使用者须按适用游戏条款及所获授权使用。逐项来源、源哈希、转换后哈希和切片信息见 `assets/manifest.json`。本库不部署 webpack 游戏逻辑、字体源文件、视频或游戏服务接口。当前字体图集包含源包字体的派生字形，见下文。

## Noto Sans SC

`textures/pyreact_ore/type/` 和 `oreui/_font_atlas.py` 的中文部分由源包 `NotoSansSC-Regular-a4317c614d07055b56ed.otf` 烘焙生成，采用 SIL Open Font License 1.1。完整许可证位于 `resource_pack/textures/pyreact_ore/type/OFL.txt`，随 core 和 all 包部署。源字体 SHA-256 为 `8c37936063c7c8ab747a939e13833894f9edc80dd41b98874ca8f3938a33c32f`。生成器独立实现，其图集尺寸、基线与 advance 方法参考 better-building-editor。

## Minecraft Seven

图集中西文部分来自用户 ZIP 的 `Minecraft-Seven-v4-c172545dc1c7c7ec7951.ttf`，SHA-256 为 `a71f94a2cc2993eda7438ea2805ed3c52981ae00502cba54a34b5d9a72cea31a`。源包没有附加字体开源许可，相关字形保留 Minecraft 资产权利，不能引用 Noto 的 OFL 授予其许可。字体版权及许可不被根目录 MIT 覆盖。

## PyreactMC

运行时是外部依赖，未作为根目录组件库的一部分复制。示例构建时从用户提供的 PyreactMC 本地仓库部署，并附带其 `LICENSE` / `NOTICE`。PyreactMC 使用自定义许可，非 MIT/Apache-2.0；应保留上游要求的“本项目使用 PyreactMC 客户端 UI 框架”归属陈述，并遵守其 NOTICE 全部条件。`.agents/skills/pyreact-*` 来自同一仓库；上游许可副本见 `docs/vendor/PyreactMC.LICENSE` / `PyreactMC.NOTICE`。

## 开发技能

七项通用 Mod 技能来自用户提供的 better-building-editor 中的 mcdk-assistant 技能，保留其本地统一工具入口适配。上游 `GitHub-Zero123/mcdk-assistant` 的 BSD 3-Clause 许可见 `docs/vendor/mcdk-assistant.LICENSE.txt`。技能来源和文件指纹见 `docs/skills-sources.json`。建筑编辑器专用参考只描述参考项目，不构成本库的运行要求。
