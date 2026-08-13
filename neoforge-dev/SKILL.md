---
name: neoforge-dev
description: "面向 Codex 的 Minecraft 模组工程 skill：默认以 NeoForge 1.21.1 为基线，支持项目识别、Java/Gradle 代码与结构规范、注册/事件/网络/资源/数据生成、构建调试、测试验收、跨版本 Mod 联动兼容矩阵，以及在基线完成后按官方资料完成 NeoForge 1.21.1、Forge 1.20.1、Cleanroom 1.12.2 六条有向迁移路径。用于 NeoForge、Forge、Cleanroom、模组开发、开发 mod、联动 Mod、依赖版本、物品、方块、实体、配方、世界生成、数据生成、构建、崩溃、移植或版本兼容请求。"
---

# Minecraft 模组开发（NeoForge 1.21.1 基线）

把当前请求当作真实工程任务执行：读取项目事实，选择唯一目标加载器和版本，修改最小文件集合，最后运行可复核的构建/运行验证。不要依赖未安装的子 skill、固定工作目录或未配置 MCP。

## 0. 基线门控（必须先执行）

默认目标是 **NeoForge 1.21.1 + Java 21**。Forge 1.20.1 和 Cleanroom 1.12.2 是后续候选迁移目标。

```text
BASELINE_GATE:
先完成 NeoForge 1.21.1 基线开发与验收。
基线未完成时，只记录迁移资料，不执行 Forge/Cleanroom 移植设计或代码修改。
只有基线验收完成且用户明确指定目标加载器和版本后，才进入移植任务。
```

详细门控和验收证据见 [references/baseline-gate.md](references/baseline-gate.md)。收到 Forge/Cleanroom 请求时，先检查 `baseline_status` 和证据；状态为 `in_progress`/`unknown` 时只做资料登记、只读识别和差异表，不替换 API、构建文件或资源。

## 1. 读取项目事实

按以下顺序执行，不凭目录名或记忆猜版本：

1. 从当前工作目录向上读取适用的 `AGENTS.md`、README 和构建说明。
2. 定位包含 `settings.gradle[.kts]`、`build.gradle[.kts]`、`gradlew`、`gradle.properties` 的项目根。
3. 运行只读识别：

   ```bash
   python3 neoforge-dev/scripts/validate_loader.py PROJECT --json
   python3 neoforge-dev/scripts/validate_structure.py PROJECT --loader auto --json
   ```

   如果从已安装 skill 运行，使用 `python3 $CODEX_HOME/skills/neoforge-dev/scripts/...`。

4. 从 Gradle toolchain、依赖声明、元数据和任务列表记录 Minecraft、loader、Java、Gradle、mappings、运行目录和数据生成任务。
5. 查看 `git status --short`，保留用户已有改动，只编辑本任务相关文件。

识别结果冲突时，以构建脚本、Gradle 解析和实际任务为准；把冲突写入报告，不静默选择一个版本。

## 2. 代码生成契约

将以下规则当作每次生成/修改代码前的固定提示词：

```text
CODE_CONTRACT:
先读 AGENTS.md、Gradle 配置和仓库内同类实现；再写代码。
基线默认 Java 21 + NeoForge 1.21.1；每个示例标注 loader、Minecraft、Java 和运行侧。
禁止跨 loader、跨 Minecraft 版本或 current-doc API import；不要做全局包名替换。
沿用已有包结构、注册方式、命名、日志和测试风格；不要为单个功能引入第二套架构。
输出完整可编译的最小改动，源码、资源、数据生成和测试一起检查，不留伪 API。
common/server 类不得加载 client-only 类；网络输入在服务端重新验证权限、范围、区块和状态。
注册名、资源路径、翻译键、配方、loot、tag 和模型使用同一个小写 mod_id。
改动后先 compileJava/build，再运行对应数据生成、客户端、专用服务器和测试；报告未运行项。
```

Java 命名、侧/线程、包结构和资源不变量见：

- [references/common/java-style.md](references/common/java-style.md)
- [references/common/package-structure.md](references/common/package-structure.md)
- [references/common/resources-layout.md](references/common/resources-layout.md)

## 3. 按目标版本加载知识库

只加载与已确认版本匹配的一个文件，禁止把下列 API 互相混用：

| 目标 | 先读 | 不得混入 |
| --- | --- | --- |
| NeoForge 1.21.1 基线 | [references/neoforge/1.21.1.md](references/neoforge/1.21.1.md) | Forge `mods.toml`/`SimpleChannel`、Cleanroom `mcmod.info`/旧生命周期、26.1 `Identifier`/Java 25 |
| Forge 1.20.1（门控后） | [references/forge/1.20.1.md](references/forge/1.20.1.md) | NeoForge payload/StreamCodec、Cleanroom 1.12.2 生命周期、Java 21 假设 |
| Cleanroom 1.12.2（门控后） | [references/cleanroom/1.12.2.md](references/cleanroom/1.12.2.md) | 1.20.1/1.21.1 注册、现代数据组件、现代 payload、现代事件签名 |

### NeoForge 1.21.1 默认规则

- 使用 Java 21 和 `META-INF/neoforge.mods.toml`；标识符仍按 1.21.1 的 `ResourceLocation` 体系核对。
- 注册优先现有 `DeferredRegister`/holder 并挂到 mod event bus；区分 `NeoForge.EVENT_BUS` 与 mod bus。
- 网络按目标版本的 `RegisterPayloadHandlersEvent`、`PayloadRegistrar`、`CustomPacketPayload`、`StreamCodec`、`IPayloadContext` 签名核对；不要凭当前文档线猜任务或线程。
- 逻辑侧使用 `Level#isClientSide()` 等价 API，物理侧用 `Dist`/客户端注册隔离；服务端保存权威状态。
- 附加持久数据先核对 `AttachmentType`，ItemStack 先核对 data components，动态接口再考虑 capabilities。

## 4. 联动 Mod 与迁移工作流

迁移时必须同时迁移“本 Mod API”和“联动 Mod 在目标版本的运行逻辑”。不要因为 `mod_id` 相同或找到了同名方法，就假设其他 Mod 的注册、事件时序、Capability/Attachment、payload、数据格式、客户端入口和存档行为相同。

先读取 [references/compatibility/mod-compatibility.md](references/compatibility/mod-compatibility.md)、[references/compatibility/schema.json](references/compatibility/schema.json)、[references/compatibility/integration-template.md](references/compatibility/integration-template.md)、[references/compatibility/artifact-lock.example.json](references/compatibility/artifact-lock.example.json) 和 [references/compatibility/compatibility-matrix.example.json](references/compatibility/compatibility-matrix.example.json)，在迁移分支维护 `compatibility-matrix.json`。矩阵使用 `schema_version: 2`，构件解析版本和 SHA-256 另由 `artifact-lock.json` 锁定。每个联动 Mod 必须按有向路径记录：

```text
SOURCE loader/Minecraft/Java
  + SOURCE Mod 构件和版本范围
  + 注册/事件/网络/数据/渲染/存档运行语义
  + 适配层和可选依赖降级
-> TARGET loader/Minecraft/Java
  + TARGET Mod 构件和版本范围
  + 组合运行证据
```

### 六条有向迁移路径

| 源 → 目标 | 指南 |
| --- | --- |
| NeoForge 1.21.1 → Forge 1.20.1 | [neoforge-to-forge.md](references/migration/neoforge-to-forge.md) |
| Forge 1.20.1 → NeoForge 1.21.1 | [forge-to-neoforge.md](references/migration/forge-to-neoforge.md) |
| NeoForge 1.21.1 → Cleanroom 1.12.2 | [neoforge-to-cleanroom.md](references/migration/neoforge-to-cleanroom.md) |
| Cleanroom 1.12.2 → NeoForge 1.21.1 | [cleanroom-to-neoforge.md](references/migration/cleanroom-to-neoforge.md) |
| Forge 1.20.1 → Cleanroom 1.12.2 | [forge-to-cleanroom.md](references/migration/forge-to-cleanroom.md) |
| Cleanroom 1.12.2 → Forge 1.20.1 | [cleanroom-to-forge.md](references/migration/cleanroom-to-forge.md) |

反向路径必须独立核对，不能把正向迁移当作逆操作。若目标联动 Mod 没有对应构件，标为 `blocked` 或实现无联动降级；不要把源版本 jar 放入目标运行时。

### 适配层与验证

- 领域逻辑放在 `common/`；联动 Mod 的公共、客户端、服务端代码放在 `compat/<mod_id>/...`，按目标 loader/source set 隔离。
- 用 `compile`、`runtime`、`compile_runtime`、`optional` 明确依赖范围；客户端联动不得被 dedicated server 加载。
- 对每个联动 Mod 验证：无 Mod、目标版本、错误版本、client/server 不对称、数据/存档、网络（如使用）。
- 读取对应的 [loader metadata 说明](references/compatibility/loader-metadata/)，不要把 NeoForge/Forge TOML 字段直接套到 Cleanroom 的 `mcmod.info`/模板依赖。
- 状态按 `planned -> implemented -> built -> launched -> verified` 推进；目标构件未锁定、没有 observed 构建证据或没有 observed 客户端/服务端/启动/GameTest 组合证据时，不得标为 `verified`。目标缺失或版本不可用时使用 `blocked` 并写明降级。

运行矩阵检查：

```bash
python3 neoforge-dev/scripts/validate_compatibility.py compatibility-matrix.json --json
python3 neoforge-dev/scripts/validate_compatibility.py compatibility-matrix.json \
  --source neoforge:1.21.1 --target forge:1.20.1
# 可选：同时核对目标项目的 Gradle、metadata 和已实现 adapter
python3 neoforge-dev/scripts/validate_compatibility.py compatibility-matrix.json \
  --target forge:1.20.1 --project /path/to/forge-project --json
python3 neoforge-dev/scripts/validate_dependency_graph.py compatibility-matrix.json --json
python3 neoforge-dev/scripts/generate_compatibility_report.py compatibility-matrix.json \
  --output /tmp/compatibility-report.md
python3 neoforge-dev/scripts/validate_matrix_fixtures.py
```

## 5. 实现与调试工作流

### 新功能或结构调整

1. 搜索同类注册、事件、资源、数据生成和测试。
2. 列出最小文件集合：Java、资源、数据 provider、语言、模型/纹理、测试。
3. 确认 common/server/client 侧和事件线程；隔离 client-only 类。
4. 按目标版本知识库实现注册、事件、网络、菜单、渲染、世界生成或存储。
5. 同步 `assets/<mod_id>` 与 `data/<mod_id>`，确认资源路径和注册名一致。
6. 先编译，再运行最贴近改动的任务；保留日志、产物和 diff。

### 构建或崩溃

1. 先运行 `./gradlew tasks --all`，确认真实任务名和运行目录。
2. 重现最小失败命令并保留完整输出；定位首个有效异常和首个项目代码栈帧。
3. 区分编译、模组加载、逻辑/物理侧、资源/数据包、网络和游戏逻辑错误。
4. 修改最小范围，重新运行同一复现步骤和 `build`；不要只修最后一条连锁错误。

### 迁移任务（仅门控解锁后）

1. 选择六条有向路径中的一条，记录源/目标 loader、Minecraft、Java、Gradle、mappings、元数据、事件、注册、网络、存储、AT/Mixin 差异。
2. 为所有联动 Mod 建立矩阵行，分别解析源/目标构件、版本范围和运行语义；读取对应 Mod 的版本源码/Javadocs/构件元数据。
3. 使用对应迁移指南，创建独立迁移分支；先让目标 Gradle 解析，再逐层迁移入口/注册/事件、联动 adapter、网络/存储、资源/数据、客户端/服务器。
4. 每阶段运行编译和最小启动；完成无联动/有联动/错版本/两侧不对称/存档网络回归后，才把矩阵行标为 `verified`。
5. 不把迁移失败或目标联动 API 修复回写到已验收的 NeoForge 基线。

## 5. 验证与验收

使用仓库 wrapper，不假定所有项目存在同名任务：

```bash
./gradlew tasks --all
./gradlew compileJava       # 任务存在时
./gradlew build
./gradlew runClient         # 需要运行时验证时
./gradlew runServer         # 需要专用服务器验证时
```

- NeoForge 1.21.1：运行项目生成的 Data run configuration/GatherDataEvent，查看 `runs/client`、`runs/server`；不要盲猜 `runData`。
- Forge 1.20.1：常见 `GatherDataEvent` + `runData`，但以任务列表为准；默认运行目录通常 `run`。
- Cleanroom 1.12.2：模板常见 `runClient`、`runServer`、`genSources`，仍以项目任务为准。
- 项目有 GameTest/JUnit 时运行相应测试；检查 `build/libs`、生成资源、日志和 crash report。
- 把静态、构建、CI、客户端和 dedicated server 证据分开；环境不允许的验证标记为待完成，不宣称通过。

完整检查表见 [references/common/testing-validation.md](references/common/testing-validation.md)、[references/testing/combination-matrix.md](references/testing/combination-matrix.md)、[references/testing/loader-fixture-contract.md](references/testing/loader-fixture-contract.md) 和 [references/baseline-gate.md](references/baseline-gate.md)。

## 6. 辅助脚本

脚本只读或写指定输出目录，不修改模组源码：

```bash
# 抓取同域名 HTML，处理 429/5xx 退避，输出 manifest.json 与 pages/
python3 neoforge-dev/scripts/crawl_docs.py \
  --url https://docs.neoforged.net/docs/1.21.1/ \
  --output /tmp/neoforge-docs --max-pages 200

# 从 Markdown/MDX/HTML 建立标题、关键词、哈希索引
python3 neoforge-dev/scripts/build_doc_index.py \
  --input /tmp/neoforge-docs/pages --output /tmp/neoforge-doc-index.json

# 识别 loader、Minecraft、Java，期望不匹配时返回非零
python3 neoforge-dev/scripts/validate_loader.py . --expect-loader neoforge --expect-minecraft 1.21.1

# 检查对应目录和元数据文件
python3 neoforge-dev/scripts/validate_structure.py . --loader auto

# 校验迁移分支的跨版本 Mod 联动矩阵
python3 neoforge-dev/scripts/validate_compatibility.py compatibility-matrix.json --json
```

仓库根目录的同名 `scripts/*.py` 是上述 bundled script 的 CLI wrapper；安装后优先使用 skill 目录内版本。

## 7. 交付格式

完成后只报告事实：

1. 修改的文件和关键决策（含目标 loader/版本）。
2. 执行的命令、退出结果、产物和日志路径。
3. 仍需真实客户端/专用服务器或用户确认的项目。

不要把未执行的计划写成完成结果，也不要声称缺失的 API、MCP、示例或验证已经存在。
