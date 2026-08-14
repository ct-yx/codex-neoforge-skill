# Cleanroom 1.12.2 → Forge 1.20.1

本指南只能在基线门控解锁且用户明确指定目标后使用。Cleanroom 1.12.2 到 Forge 1.20.1 是向现代 API 的重新实现，不是把旧 FML 生命周期映射成同名事件。

联动 Mod 必须按 `source=cleanroom:1.12.2 → target=forge:1.20.1` 单独建立矩阵行；目标没有 Forge 构件时标为 `blocked` 或实现无联动降级。

## 差异重点

- 从 Unimined/CleanroomGradle、Blossom、`mcmod.info`、MCP/旧 mappings 迁移到 Java 17、ForgeGradle、`mods.toml`。
- 旧版 `World#isRemote`、FML construction/pre/init/post/load complete、NBT/Capability、block update flags、Mixin/AT 必须逐项核对目标语义。
- 重新设计 SimpleChannel、资源 JSON、数据生成、专用服务器和存档格式。

## 分阶段顺序

1. 锁定 Cleanroom 1.12.2 模板、Java 25、MCP、`mcmod.info` 和源联动构件；建立 `source=cleanroom:1.12.2 -> target=forge:1.20.1` 的 Schema v2 行。
2. 新建 Forge 1.20.1 MDK，先解析 Java 17/ForgeGradle、`mods.toml` 和空入口。
3. 逐项重写入口、生命周期、注册、事件总线、侧隔离和目标联动 adapter，不将旧构件带入运行时。
4. 重做 SimpleChannel、资源/数据生成、Capability/SavedData、AT/Mixin、旧存档和网络协议。
5. 运行构建、Data、客户端、专用服务器及无联动/目标/错误版本/侧不对称/存档组合测试。

## 联动 Mod 规则

每个联动 Mod 单独建立 `source=cleanroom:1.12.2 → target=forge:1.20.1` 矩阵行，分别记录两端构件、API 表面和运行时语义。不能因旧版 Mod 有同名类，就推断 Forge 1.20.1 的事件、注册、网络或数据格式相同。

目标 Mod 没有 Forge 1.20.1 构件时，标记 `blocked` 或实现无联动降级；不要在生产构建中偷偷打包旧版构件。
