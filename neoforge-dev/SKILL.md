---
name: neoforge-dev
description: "Develop, debug, migrate, test, and release Minecraft mods built with NeoForge. Use when working on a NeoForge project or when the user asks about NeoForge mod setup, registries, items, blocks, entities, menus/screens, networking payloads, events, data generation, resources, world generation, Forge-to-NeoForge migration, Gradle failures, crash logs, or Minecraft/NeoForge 1.21.x development. Also trigger for Chinese requests mentioning NeoForge, 模组开发, 开发mod, 物品, 方块, 实体, 配方, 数据生成, 世界生成, Forge迁移, 构建, or 崩溃 in a NeoForge development context."
---

# NeoForge 模组开发

把当前任务当作真实工程任务执行：先检查项目与版本，再修改文件，最后运行尽可能贴近任务的验证。不要依赖其他未安装的子 skill，也不要假定存在特定 MCP。

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

如果用户要求创建新项目但没有指定版本，优先采用其现有生态或相邻项目的版本；没有任何上下文时，可将 Minecraft 1.21.1、NeoForge 21.1.x、Java 21 作为明确说明的默认值。

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
   - `run/logs/latest.log`
   - `run/crash-reports/`
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
3. 与目标版本匹配的 NeoForge 官方文档、Javadocs、MDK 和官方仓库示例。
4. 经过版本筛选的真实项目代码，仅作为补充证据。

使用可用的浏览器、代码搜索或 MCP；某个 MCP 不存在时直接使用其他可用工具。不要编造工具名或声称调用了未配置工具。引用外部示例前确认它属于同一 Minecraft/NeoForge 版本。

## 4. 实现检查点

- **注册**：沿用项目的 `DeferredRegister`/holder 模式；确认注册器挂到正确的 mod event bus。
- **事件**：区分 mod 生命周期事件和游戏运行时事件；确认事件总线、静态订阅方式和运行侧。
- **网络**：核对目标版本的 payload 注册、codec、handler thread/上下文和方向；在服务端重新验证客户端输入。
- **菜单与界面**：服务端保存真实状态，客户端只负责展示和输入；检查容器同步、数据槽与 client-only 注册。
- **资源**：统一使用小写命名空间和路径；确保 Java 注册名、JSON、翻译键、纹理及数据生成输出匹配。
- **数据生成**：优先扩展仓库现有 provider；避免手写一份又由 datagen 生成另一份相互覆盖的 JSON。
- **世界生成**：核对 configured/placed feature、biome modifier 或目标版本所用数据驱动入口及其加载顺序。
- **Mixin**：优先使用公开 API/事件；确需 Mixin 时核对映射、方法描述符、加载侧和注入点，并启用可验证的失败策略。
- **兼容性**：不要无意提高最低 Java、Minecraft 或 NeoForge 版本；新增依赖时说明原因和作用域。

## 5. 验证

使用仓库自带 wrapper。macOS/Linux 通常运行 `./gradlew`，Windows 通常运行 `gradlew.bat`。先查看 `./gradlew tasks` 或构建脚本以确认任务名，不要假定所有项目都有同名任务。

按改动范围选择：

1. `./gradlew compileJava`：快速验证 Java 编译。
2. `./gradlew build`：默认回归验证；除非耗时明显不合理，代码修改后应运行。
3. `./gradlew runData` 或项目对应任务：修改数据生成器时运行，并检查生成差异。
4. 测试任务：项目存在 GameTest/JUnit 时运行相关测试。
5. `runClient` / `runServer`：仅在任务需要运行时行为验证且环境允许时运行；避免让交互式进程无限挂起，设置合理超时并检查日志。

如果某项验证受环境、网络或图形界面限制，仍完成其余可运行检查，并准确报告未验证项及原因。

## 6. 交付格式

完成任务后简洁报告：

1. 实际修改了什么，以及关键文件路径。
2. 运行了哪些命令及其结果。
3. 仍需人工进游戏验证的行为，或任何明确遗留问题。

不要把计划当作完成结果，也不要声称缺失的示例、子 skill、MCP 或构建产物已经存在。
