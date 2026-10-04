# 本仓库与上游结构

本仓库 `pyreact-ore-ui` 是组件库：`oreui/` 与宿主模组的 `pyreact/` 同级部署，纹理位于 `resource_pack/textures/pyreact_ore/`。示例入口在 `examples/demo/`；通过 `tools/build_demo.py` 将外部 PyreactMC 依赖组装到 `.runtime/demo_addon/`。接入和 API 见根目录 `docs/INTEGRATION.md` / `docs/API.md`。以下目录说明描述上游框架，不能假定本仓库根目录已有这些文件。

## 上游 PyreactMC

- `pyreact/`：Pyreact-MC 框架核心，需放到 `behavior\YourClientScript\pyreact`
    - `component.py`：组件装饰器与组件包装逻辑。
    - `element.py`：虚拟元素结构和 children 归一化。
    - `hooks.py`：类 react 的 hooks。
    - `host.py`：ScreenNode、root、运行时初始化和宿主侧调度。
    - `renderer.py`：提交阶段，将虚拟节点变化应用到原生控件。
    - `reconciler.py`：虚拟 DOM diff 与 fiber 调和。
    - `layout.py`：类 React Native 的 flex 布局计算。
    - `native.py`：ModSDK / JsonUI 原生控件访问与模板路径。
    - `primitives.py`：Primitive 组件。
    - `composites/`：Composite 组件包，按组件拆分。
    - `style.py`：`Style` 对象和样式解析。
    - `constants.py`：颜色、枚举和常量。
- `jsonui/PyreactBase`: JsonUI 模板文件，需放入 `resource/ui` 下并在 `_ui_defs.json` 注册。
- `examples/`：示例Pyreact组件代码。
- `.agents/skills/pyreact-ui-building`：UI 开发文档 skill，术语、Style 规范和 Primitive / Composite 参数表。
- `.agents/skills/pyreact-debugging`：调试用 Agent Skill，可让 Agent 打开游戏自动测试调试。
