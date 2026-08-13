# Forge 1.20.1 → NeoForge 1.21.1

本指南只能在基线门控解锁且用户明确指定目标后使用。反向迁移不是 `neoforge-to-forge.md` 的简单逆操作。

联动 Mod 必须按 `source=forge:1.20.1 → target=neoforge:1.21.1` 单独解析目标构件和运行语义；目标 Mod 缺失或 API 不等价时使用 optional adapter 降级，不复用 Forge 构件。

## 差异重点

- 从 Java 17/ForgeGradle/`mods.toml` 重新建立 Java 21/目标 NeoForge 构建和 `neoforge.mods.toml`。
- 逐项重写 Forge 事件总线、注册、SimpleChannel、Capabilities、数据生成和 client Dist 代码。
- 以目标项目实际任务和 1.21.1 版本文档为准，不能把当前文档线 API 直接复制进来。

## 联动 Mod 规则

每个联动 Mod 单独建立 `source=forge:1.20.1 → target=neoforge:1.21.1` 矩阵行。目标 Mod 版本必须重新解析；同一个 `mod_id` 的 NeoForge 构件可能有不同注册事件、payload、Capability/Attachment 或客户端入口。

迁移顺序：先确认目标构件存在，再分析运行语义，最后实现 adapter。目标构件缺失时保留 optional 降级，禁止继续使用 Forge 构件并宣称 NeoForge 联动完成。

## 验证

除本 Mod 的 `compileJava`/`build`/Data/client/server 外，还要执行：无联动、目标 Mod 存在、错误版本、client/server 不对称、存档/网络联动五组检查，并将证据写入矩阵。
