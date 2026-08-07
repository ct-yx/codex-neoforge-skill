# NeoForge 官方文档核对记录

本文件用于在需要版本事实时快速定位官方资料；不要把它当成 API 替代品。每次复制代码或命令前，仍需打开目标版本的页面并检查项目实际 Gradle 配置。

## 审计来源

- 文档入口：[https://docs.neoforged.net/](https://docs.neoforged.net/)
- 官方文档源码：[https://github.com/neoforged/Documentation](https://github.com/neoforged/Documentation)
- 本次核对源码提交：`816c03d31ff7948179c7bd4a58d23bcfda09c18a`
- 核对时间：2026-08-08

## 版本与 Java

- 当前文档线标签为 **26.1**，入门页要求 **64 位 Java 25 JDK/JVM**。
- 版本化文档 `/docs/1.21.1/` 对应 **Minecraft 1.21.1**，入门页要求 **64 位 Java 21 JDK/JVM**。
- 不要把 26.1 的 `Identifier`、Gradle 插件示例或事件签名直接复制到 1.21.1；1.21.1 文档中仍常见 `ResourceLocation`，网络双向 payload 也使用目标版本的 handler 形式。

## 官方流程要点

1. 新项目优先使用官方 Mod Generator 或匹配版本的 MDK；官方文档列出 ModDevGradle 和 NeoGradle 两条工具链。
2. 基础 mod 信息主要放在 `gradle.properties`；构建脚本才用于改变构建流程。
3. `gradlew build` 是官方入门页的构建验证，产物位于 `build/libs`。
4. 测试运行使用生成的 run configuration 或 `runClient`/`runServer`；默认运行目录为 `runs/client`、`runs/server`。
5. 当前文档线的数据生成使用 `GatherDataEvent.Client`/`.Server`，常见 Gradle 任务是 `runClientData`/`runServerData`；1.21.1 文档主要描述 Data run configuration、`GatherDataEvent` 和命令行参数。
6. 资源页区分客户端 assets 与服务端 data，并说明现代 NeoForge 会合成 `pack.mcmeta`。
7. 事件页区分 `NeoForge.EVENT_BUS` 游戏总线和每个 mod 的 mod 总线；很多生命周期事件并行执行，主线程工作需要 `enqueueWork`。
8. 注册页推荐 `DeferredRegister`，并要求在 mod 总线上注册；`RegisterEvent` 是另一种方式。
9. 网络页以 `RegisterPayloadHandlersEvent`、`PayloadRegistrar`、`CustomPacketPayload` 和 `StreamCodec` 为核心；handler 的阶段、方向和线程必须按版本核对。
10. 数据存储页将 attachments 用于方块实体/区块/实体/世界附加数据；物品堆栈优先使用 data components；capabilities 用于动态行为接口。

## 关键入口

- 入门：[gettingstarted](https://docs.neoforged.net/docs/gettingstarted/)
- 项目结构：[structuring](https://docs.neoforged.net/docs/gettingstarted/structuring)
- 模组文件：[modfiles](https://docs.neoforged.net/docs/gettingstarted/modfiles)
- 事件：[events](https://docs.neoforged.net/docs/concepts/events)
- 注册表：[registries](https://docs.neoforged.net/docs/concepts/registries)
- 网络 payload：[payload](https://docs.neoforged.net/docs/networking/payload)
- Stream codecs：[streamcodecs](https://docs.neoforged.net/docs/networking/streamcodecs)
- 资源与数据生成：[resources](https://docs.neoforged.net/docs/resources/)
- 数据 attachments：[attachments](https://docs.neoforged.net/docs/datastorage/attachments)
- Capabilities：[capabilities](https://docs.neoforged.net/docs/inventories/capabilities)
- 1.21.1 版本入口：[1.21.1 gettingstarted](https://docs.neoforged.net/docs/1.21.1/gettingstarted/)
