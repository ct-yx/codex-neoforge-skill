# Forge 1.20.1 → Cleanroom 1.12.2

本指南只能在基线门控解锁、且用户明确指定 Cleanroom 1.12.2 后使用。Cleanroom 是 1.12.2 生态，不是 Forge 1.20.1 的小版本升级；应视为重新适配目标平台。

如果存在联动 Mod，必须为 `source=forge:1.20.1 → target=cleanroom:1.12.2` 的每个 Mod 建立矩阵行，分别验证目标构件和旧版运行逻辑；不能把 Forge 1.20.1 构件塞进 Cleanroom 运行时。

## 差异表

| 领域 | Forge 1.20.1 | Cleanroom 1.12.2 | 移植动作 |
| --- | --- | --- | --- |
| Java/构建 | Java 17、ForgeGradle、MDK | 模板的 Unimined/CleanroomGradle；审计模板 Java 25 | 以模板和 CI 为准重建构建，移除 `fg.deobf`/`rfg.deobf` |
| 元数据 | `mods.toml` | Blossom 生成的 `mcmod.info`/模板资源 | 重新定义模板变量与 loader 依赖 |
| 生命周期 | 1.20.1 mod bus/events | `FMLConstructionEvent` 到 `FMLLoadCompleteEvent` | 逐事件重写，不保留现代生命周期假设 |
| 逻辑侧 | `Level#isClientSide` | `World#isRemote` | 逐处核对读写侧和线程 |
| 网络 | SimpleChannel 现代消息 | 1.12.2 网络实现 | 重新定义消息注册、序列化和权限校验 |
| 持久数据 | 现代数据 API/Capabilities | 1.12.2 NBT、Capability 等 | 设计存档迁移与旧数据回退 |
| AT/Mixin | ForgeGradle/目标版本语法 | `${mod_id}_at.cfg` + CleanMix/MixinBooter | 以 MCP 名称、ASM9 和 manifest 注册为准 |
| 资源/数据 | 1.20.1 JSON/schema | 1.12.2 资源和 block flag 语义 | 重新生成并在目标客户端/服务器加载 |

## 分阶段顺序

1. 复制 Forge 基线业务代码，建立 Cleanroom 当前模板分支并锁定 Java 25、MCP、Cleanroom loader 和 artifact lock。
2. 填写 `gradle.properties` 和 Blossom 模板，确认 `runClient`/`runServer`/`genSources`，先让空项目构建和启动。
3. 为每个联动 Mod 解析 1.20.1 源构件和 1.12.2 目标构件，记录旧版生命周期、注册、侧、网络、Capability/NBT 和存档差异。
4. 先迁移入口、生命周期、注册和侧隔离，再迁移业务逻辑；目标 API 放入独立 compat source set。
5. 重写网络、NBT/Capability、资源、AT/Mixin；每个阶段保留构建、客户端和服务端日志。
6. 执行无联动/目标版本/错误版本/两侧不对称/旧存档/网络组合，按证据状态更新矩阵。

## 重点陷阱

- 不要把 `ResourceLocation`、现代 payload、data components 或 1.20.1 事件签名直接带入 1.12.2。
- 使用 `Launch.classLoader` 扩展类路径；不要强转系统 AppClassLoader。
- 对 `javax`/`jakarta`、Guava、FastUtil、LWJGL 和 ASM 版本做依赖级核对。
- 迁移结果的运行时行为必须以 Cleanroom 客户端和专用服务器日志为证据，静态编译通过不等于完成。
