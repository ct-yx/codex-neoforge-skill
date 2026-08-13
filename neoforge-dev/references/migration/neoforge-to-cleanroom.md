# NeoForge 1.21.1 → Cleanroom 1.12.2

本指南只能在基线门控解锁、且用户明确指定目标后使用。它是跨越两个时代的重新适配，不是连续包名替换。

联动 Mod 必须按 `source=neoforge:1.21.1 → target=cleanroom:1.12.2` 单独建立矩阵行；目标 Mod 没有 1.12.2 构件时只能标为 `blocked` 或实现无联动降级。

## 平台差异

| 领域 | NeoForge 1.21.1 | Cleanroom 1.12.2 | 移植动作 |
| --- | --- | --- | --- |
| 构建/Java | Java 21、ModDevGradle/NeoGradle | Cleanroom 模板、Unimined/CleanroomGradle | 新建目标模板并锁定目标 toolchain |
| 元数据 | `neoforge.mods.toml` | Blossom 生成 `mcmod.info`/模板 | 重新生成元数据和依赖条件 |
| 生命周期 | 现代 mod bus 与 NeoForge bus | FML construction/pre/init/post/load complete | 重写入口和初始化顺序 |
| 注册 | DeferredRegister/holder | 1.12.2 注册事件/对象 | 建立目标版本 registry adapter |
| 网络 | payload/StreamCodec | 1.12.2 消息实现 | 重新设计 codec、方向、协议和校验 |
| 存储 | Attachment/data components/现代 Capability | NBT/Capability/旧存档格式 | 设计数据迁移与回退 |
| 资源/数据 | 现代 JSON/schema | 1.12.2 资源和 block flag | 重新生成并目标端加载 |

## 联动 Mod 迁移

对每个联动 Mod 建立 `source=neoforge:1.21.1 → target=cleanroom:1.12.2` 的独立矩阵行。目标 Mod 的 1.12.2 构件、注册 ID、FML 生命周期、Capability/NBT、网络和客户端入口必须分别审查；不能用 NeoForge 版本的 API 说明代替 Cleanroom 运行证据。

如果目标 Mod 没有 1.12.2 版本：

- 标记为 `blocked`，不要把现代构件塞进 Cleanroom；
- 提供无联动降级路径，保证本 Mod 核心功能可启动；
- 若确实需要功能，记录重建桥接 Mod 的范围，不把它伪装成普通迁移。

## 阶段顺序

1. 复制业务逻辑，建立 Cleanroom 当前模板分支，锁定 Java 25、Unimined/MCP、Cleanroom loader 和 artifact lock。
2. 让目标 Gradle、`genSources`、`runClient`/`runServer` 的空入口运行，再迁移 `mcmod.info`、FML 生命周期和侧隔离。
3. 为每个联动 Mod 分别确认 1.12.2 构件、模板依赖、旧事件/Capability/NBT/网络语义和 client/server 入口。
4. 重写网络、NBT/Capability、资源、AT/Mixin 和存档迁移；不把现代 payload、Attachment 或 data component 带入目标。
5. 运行无联动/目标版本/错误版本/两侧不对称/旧存档组合；只有 observed 构建和客户端/服务端运行证据齐全才标为 `verified`。
