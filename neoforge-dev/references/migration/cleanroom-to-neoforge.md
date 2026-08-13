# Cleanroom 1.12.2 → NeoForge 1.21.1

本指南只能在基线门控解锁且用户明确指定目标后使用。该路径跨越最大，必须按目标版本重新设计构建、生命周期、注册、网络、资源和存档。

联动 Mod 必须按 `source=cleanroom:1.12.2 → target=neoforge:1.21.1` 单独建立矩阵行；不能复用反向路径的版本范围或运行结论。

## 联动 Mod 规则

每个联动 Mod 单独建立 `source=cleanroom:1.12.2 → target=neoforge:1.21.1` 矩阵行，不能复用反向路径的版本范围或运行结论。重点核对：

- 旧版 `mcmod.info`/FML 依赖条件与 NeoForge metadata；
- 旧版注册/事件/Capability/NBT 与 1.21.1 holder、event、Attachment/data component；
- 旧版网络消息与 1.21.1 payload/StreamCodec；
- 客户端入口、资源重载、渲染和服务端 classpath；
- 注册 ID、世界数据和存档迁移。

如果目标版本没有联动 Mod 构件，保留降级路径或将该项标为 `blocked`；不要把 Cleanroom jar 放入 NeoForge 运行时。

## 阶段顺序

1. 建立 NeoForge 1.21.1 空项目和公共业务层。
2. 逐个迁移联动 Mod 的目标构件和 adapter，再迁移本 Mod 功能。
3. 完成资源、数据生成、网络、存档和服务器回归。
