# NeoForge 1.21.1 → Forge 1.20.1

本指南只能在 `baseline-gate.md` 解锁后使用。目标明确后建立独立迁移分支，保留 NeoForge 基线可构建。

如果存在联动 Mod，必须同时读取 [跨版本联动规范](../compatibility/mod-compatibility.md)，为 `source=neoforge:1.21.1 → target=forge:1.20.1` 的每个 Mod 建立矩阵行。目标 Mod 版本、事件/注册/网络/数据语义和组合运行证据都必须独立确认。

## 差异表

| 领域 | NeoForge 1.21.1 | Forge 1.20.1 | 移植动作 |
| --- | --- | --- | --- |
| Java/构建 | Java 21；ModDevGradle/NeoGradle | Java 17；ForgeGradle/MDK | 先复制项目，再重建构建声明，不做全局文本替换 |
| 元数据 | `neoforge.mods.toml` | `mods.toml` | 重新生成依赖范围和入口元数据 |
| 注册 | 目标版本的 DeferredRegister/holder | DeferredRegister + RegistryObject | 保留注册顺序，逐个核对泛型和事件总线 |
| 事件 | `NeoForge.EVENT_BUS`、mod bus、并行生命周期 | `MinecraftForge.EVENT_BUS`、mod bus | 对每个事件找 1.20.1 签名和线程语义 |
| 网络 | payload + `StreamCodec` + `PayloadRegistrar` | `SimpleChannel` + message codec | 重新设计 wire schema、方向、版本和服务端校验 |
| 数据 | data components/attachments 等现代入口 | 1.20.1 对应的数据/Capability API | 不把新 API 名称机械替换成旧 API |
| 数据生成 | 项目 Data run configuration | `GatherDataEvent`、常见 `runData` | 先看任务列表和 provider 签名 |
| 资源 | 现代 NeoForge 元数据/pack 行为 | Forge `mods.toml`/pack 行为 | 重新跑生成和资源加载 |

## 分阶段顺序

1. 复制基线并锁定依赖、Java、mappings；为每个联动 Mod 填写 Schema v2 矩阵和 artifact lock。
2. 让 Gradle 只解析 Forge 1.20.1；此阶段不改业务代码。
3. 重建入口、metadata、注册和事件；每一步运行 `compileJava`，核对 `mandatory/versionRange/ordering/side`。
4. 迁移网络和持久数据，明确服务端权威、SimpleChannel wire schema、Capability/SavedData 和旧存档策略。
5. 迁移资源、数据生成、客户端注册和渲染；确保 client adapter 不进入 dedicated server。
6. 运行 `build`、数据生成、`runClient`、`runServer` 并保留日志、产物和 crash report。
7. 对每个联动 Mod 运行无联动、目标版本、错误版本、两侧不对称、存档和网络组合测试；只有 observed 构建与组合运行证据齐全才标为 `verified`。

## 禁止事项

- 禁止在同一源集留下 NeoForge 和 Forge 两套活动入口。
- 禁止只替换 `net.neoforged`/`net.minecraftforge` 包名而保留错误事件、线程和 codec 语义。
- 禁止把迁移失败修复回写到已验收的基线分支。
