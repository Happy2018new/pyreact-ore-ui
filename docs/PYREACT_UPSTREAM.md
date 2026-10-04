# Pyreact 依赖记录

参考运行时来自用户提供的 PyreactMC 文件夹，基准 commit `9580d0123584ae8b4b4b3a7b0357250e151c54cd`（由 `tools/build_demo.py` 写入示例 dependency.json）。本仓库不在根组件包中捆绑或修改该 runtime。

`oreui/_button.py` 继承上游 `ButtonPrimitive`，只补充 Image 的九宫格参数。内部类保留 `ButtonPrimitive` 名称，使上游 Fiber 检查工具仍将其识别为 `Button`。公共 API 使用 OreButton Composite。来源许可完整副本见 vendor/PyreactMC.LICENSE 和 vendor/PyreactMC.NOTICE。

类签名、基础模板或 state image 行为发生变化时需要重新运行 tests/runtime_contracts.py 与实机回归。运行目录中的 Pyreact 依赖不由每次示例构建自动更新。
