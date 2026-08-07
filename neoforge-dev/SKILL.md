---
name: neoforge-dev
description: "Develop, debug, migrate, test, and release Minecraft mods built with NeoForge. Use when working on a NeoForge project or when the user asks about NeoForge mod setup, registries, items, blocks, entities, menus/screens, networking payloads, events, data generation, resources, world generation, Forge-to-NeoForge migration, Gradle failures, crash logs, or Minecraft/NeoForge 1.21.x, 1.21.11, or 26.1+ development. Also trigger for Chinese requests mentioning NeoForge, 模组开发, 开发mod, 物品, 方块, 实体, 配方, 数据生成, 世界生成, Forge迁移, 构建, or 崩溃 in a NeoForge development context."
---

# NeoForge 模组开发

把当前任务当作真实工程任务执行：先检查项目与版本，再修改文件，最后运行尽可能贴近任务的验证。不要依赖其他未安装的子 skill，也不要假定存在特定 MCP。NeoForge 官方文档按 Minecraft 版本分站；当前文档线已使用 26.1/Java 25，而 1.21.1 版本线使用 Java 21。所有 API 和命令都必须以项目目标版本对应的文档为准。

## 1. 确认项目上下文

1. 从当前工作目录开始，先读取适用范围内的 `AGENTS.md` 或其他仓库说明。
2. 定位项目根目录。优先查找：
   - `settings.gradle` / `settings.gradle.kts`
   - `build.gradle` / `build.gradle.kts`
   - `gradlew`
   - `gradle.properties`
   - `src/main/resources/META-INF/neoforge.mods.toml`
3. 使用现有工作区，不要强制切换到固定目录。除非用户明确要求，不要在工作区外新建项目。
4. 检查 `git status --short`，保留用户已有改动；只编辑本任务相关文件。
5. 从构建文件而非文件夹名推断 Minecraft、NeoForge、Java、Gradle 插件和 mappings 版本。记录实际版本后再选择 API。

如果用户要求创建新项目但没有指定版本，优先采用官方 Mod Generator/MDK 当前可用版本和项目生态；没有任何上下文时，先读取官方文档当前版本，而不是静默固定旧版本。本次核对的官方文档当前线为 Minecraft 26.1、Java 25；只有用户明确要求 1.21.1 时才使用 Java 21 和对应的 1.21.1 文档线。

## 2. 选择工作路径

### 实现或修改功能

1. 在仓库中搜索同类注册、事件、资源和命名约定。
2. 列出该功能涉及的最小文件集合：Java 源码、资源、数据生成器、语言文件、模型/纹理或测试。
3. 确认逻辑运行侧：common、server 或 client。避免从服务端可加载类直接引用仅客户端类。
4. 沿用项目已有的注册体系与包结构；不要为单个功能引入第二套架构。
5. 同步补齐资源与数据：注册名、资源路径、翻译键、模型、loot table、recipe、tag 等必须一致。
6. 完成后先编译，再运行更贴近改动的任务。

### 调试构建或崩溃

1. 复现最小失败命令并保留完整错误输出。
2. 按需检查：
   - Gradle 输出及 `--stacktrace`
   - `runs/<side>/logs/latest.log` and `runs/<side>/crash-reports/`（或项目构建脚本配置的运行目录）
   - Mixin audit、数据包加载错误、registry/resource location 错误
3. 先定位最早的有效异常和首个项目代码栈帧，不要只修最后一条连锁错误。
4. 区分编译错误、模组加载错误、客户端/服务端边界错误、资源错误和游戏逻辑错误。
5. 做最小修复后执行同一复现步骤，并补跑回归构建。

### Forge 迁移到 NeoForge

1. 先盘点源版本、目标版本、构建插件、mappings、入口注解、事件总线、注册、网络、能力/附件、配置和 access transformer/mixin。
2. 分阶段迁移：构建可解析 → 主源码可编译 → 资源可加载 → 数据生成可运行 → 客户端/服务端启动 → 功能回归。
3. 不要机械替换包名。对目标版本逐项核对事件、payload、registry、attachment/capability 和生命周期 API。
4. 保持每阶段改动可验证，避免同时重写无关业务逻辑。

### 创建新项目

1. 优先使用与目标版本匹配的官方 MDK 或官方示例作为基础，不要凭记忆拼装 Gradle 配置。
2. 确定 `mod_id`、显示名称、包名、版本、许可证和基础功能；只有真正影响工程结构的缺失信息才需要询问。
3. 生成后立即验证 wrapper、Java toolchain、依赖解析、模组元数据和空项目构建。

## 3. 核对版本专属 API

NeoForge API 会随 Minecraft 小版本变化。对注册、网络、菜单、渲染、数据生成、世界生成、attachments/capabilities、配置和事件签名执行以下核对顺序：

1. 当前仓库内已编译的同版本用法。
2. Gradle 缓存中的同版本源码或生成源码。
3. 与目标版本匹配的 [NeoForge 官方文档](https://docs.neoforged.net/)、Javadocs、MDK 和官方仓库示例。
4. 经过版本筛选的真实项目代码，仅作为补充证据。

需要快速核对版本事实时，读取随 skill 提供的 `references/official-docs.md`；它记录了本次官方文档审计的版本映射和关键入口。不要把当前文档线的示例复制到 1.21.1 项目，反之亦然。

使用可用的浏览器、代码搜索或 MCP；某个 MCP 不存在时直接使用其他可用工具。不要编造工具名或声称调用了未配置工具。引用外部示例前确认它属于同一 Minecraft/NeoForge 版本。

## 4. 实现检查点

- **注册**：沿用项目的 `DeferredRegister`/holder 模式；确认注册器挂到正确的 mod event bus。当前文档线常见 `Identifier`，1.21.1 文档线常见 `ResourceLocation`，不要跨版本混用命名类型。
- **事件**：区分 `NeoForge.EVENT_BUS` 游戏总线和 mod 构造器传入的 mod 总线；确认静态/实例订阅方式、生命周期事件的并行执行和运行侧。并行生命周期事件需要把主线程工作交给 `enqueueWork`。
- **网络**：核对目标版本的 `RegisterPayloadHandlersEvent`/`PayloadRegistrar`、payload 类型、`StreamCodec`、handler thread/`IPayloadContext`、阶段和方向；客户端处理器按目标版本使用对应的 client payload 注册事件；在服务端重新验证客户端输入。
- **菜单与界面**：服务端保存真实状态，客户端只负责展示和输入；检查容器同步、数据槽与 client-only 注册。
- **客户端/服务端**：用 `Level#isClientSide()` 判断逻辑侧；用 `Dist`/client-only 注册隔离物理客户端代码。单人游戏同时包含物理客户端和逻辑服务端，必须用 dedicated server 做一次兼容性验证。
- **资源**：区分客户端 assets 与服务端 data；统一使用小写命名空间和路径，确保 Java 注册名、JSON、翻译键、纹理及 datagen 输出匹配。现代 NeoForge 会合成 mod 的 `pack.mcmeta`，除非项目有明确需求，不要重复生成冲突文件。
- **数据生成**：沿用仓库已有的 `GatherDataEvent` 变体和 provider 注册方式；当前文档线使用 `GatherDataEvent.Client`/`.Server` 与 `runClientData`/`runServerData`，1.21.1 文档线主要描述生成的 Data run configuration 和 `GatherDataEvent`。先查看项目任务和 run 配置，不要根据版本猜任务名。
- **数据存储**：需要给方块实体、区块、实体或世界附加持久数据时优先核对 `AttachmentType`；物品堆栈数据优先核对 vanilla data components；需要跨模组动态能力接口时再核对 block/entity/item capabilities。
- **世界生成**：核对 configured/placed feature、biome modifier 或目标版本所用数据驱动入口及其加载顺序。
- **Mixin/Access Transformer**：优先使用公开 API/事件；确需 Mixin 时核对目标版本的配置、映射、方法描述符、加载侧和注入点，并启用可验证的失败策略。Access Transformer 要先在目标 Gradle 插件中声明；ModDevGradle 的默认 `META-INF/accesstransformer.cfg` 会自动纳入，非默认路径还要在 `neoforge.mods.toml` 中声明，改动后刷新 Gradle 项目。
- **兼容性**：不要无意提高最低 Java、Minecraft 或 NeoForge 版本；新增依赖时说明原因和作用域。

## 5. 验证

使用仓库自带 wrapper。macOS/Linux 通常运行 `./gradlew`，Windows 通常运行 `gradlew.bat`。先查看 `./gradlew tasks` 或构建脚本以确认任务名，不要假定所有项目都有同名任务。

按改动范围选择：

1. `./gradlew compileJava`：在项目任务列表存在时快速验证 Java 编译。
2. `./gradlew build`：官方入门文档的默认回归验证，产物通常位于 `build/libs`；除非耗时明显不合理，代码修改后应运行。
3. 数据生成：优先运行生成的 Data run configuration；当前文档线通常对应 `runClientData`/`runServerData`，旧版本可能只有 Data 或 IDE run configuration，必须以 `./gradlew tasks` 和项目构建脚本为准，并检查 `src/generated/resources` 的差异。
4. 测试任务：项目存在 GameTest/JUnit 时运行相关测试。
5. `runClient` / `runServer`：仅在任务需要运行时行为验证且环境允许时运行；默认运行目录通常是 `runs/client`、`runs/server`（项目也可能自定义为 `run/`）。检查对应目录下的 `logs/latest.log` 和 `crash-reports/`。Dedicated server 首次启动需要接受 `eula.txt`；要从开发客户端连接时，按官方文档检查 `server.properties` 的 `online-mode` 设置。

如果某项验证受环境、网络或图形界面限制，仍完成其余可运行检查，并准确报告未验证项及原因。

## 6. 交付格式

完成任务后简洁报告：

1. 实际修改了什么，以及关键文件路径。
2. 运行了哪些命令及其结果。
3. 仍需人工进游戏验证的行为，或任何明确遗留问题。

不要把计划当作完成结果，也不要声称缺失的示例、子 skill、MCP 或构建产物已经存在。
