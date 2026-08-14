# 跨版本 Mod 联动与运行语义

迁移时不能只迁移本 Mod 的 loader API。若项目与其他 Mod 联动，必须同时回答：**源版本依赖哪个 Mod 构件、目标版本应使用哪个构件、两者的运行逻辑是否等价、适配代码如何隔离、组合运行是否有证据**。

## 核心模型

把一次迁移描述成一条有向边，而不是一个版本号替换：

```text
SOURCE_GAME (loader + Minecraft + Java)
  + SOURCE_COMPAT_MOD (mod_id + version/range + artifact)
  + INTEGRATION_SURFACE (registry/event/capability/payload/command/data/client)
  + RUNTIME_SEMANTICS (lifecycle/thread/side/authority/save/network)
  + ADAPTER (source set / module / reflection boundary)
  -> TARGET_GAME (loader + Minecraft + Java)
  + TARGET_COMPAT_MOD (mod_id + version/range + artifact)
  + EVIDENCE (docs/source/log/test)
```

同一个 Mod 在不同 Minecraft 版本通常不是同一份 API，也不保证行为相同。`mod_id` 相同只代表生态身份，不代表类名、注册表、事件时序、网络协议、Capability/Attachment、数据格式或客户端入口可直接复用。

## 版本联动矩阵

在迁移分支根目录维护 `compatibility-matrix.json`（Schema v2 见 [`schema.json`](schema.json)，模板见 [`compatibility-matrix.example.json`](compatibility-matrix.example.json)）。构件解析版本、下载来源、许可证和 SHA-256 另记录在 `artifact-lock.json`（模板见 [`artifact-lock.example.json`](artifact-lock.example.json)）。每个联动 Mod 至少有一行：

| 字段 | 要求 |
| --- | --- |
| `source` / `target` | loader、Minecraft、Java；必须与当前有向迁移路径一致 |
| `mod_id` | 依赖 Mod 的稳定 ID，不使用显示名或文件名代替 |
| `source_version_range` / `target_version_range` | 源/目标版本分别填写，不能假设相同版本号可用 |
| `source_artifact` / `target_artifact` | Modrinth/CurseForge/Maven 坐标或本地构件；记录来源和下载验证信息 |
| `dependency_scope` | `compile`、`runtime`、`compile_runtime` 或 `optional` |
| `sides` | `common`、`server`、`client`；客户端联动不能被服务端加载 |
| `loader_metadata` | 目标 loader 元数据中的依赖表达：例如 Forge `mods.toml` 的 `mandatory`、`versionRange`、`ordering`、`side`；NeoForge/Cleanroom 按目标模板/元数据字段核对 |
| `integration_surfaces` | `registry`、`event`、`capability`、`attachment`、`payload`、`command`、`data`、`render` 等 |
| `runtime_checks` | 必须描述生命周期、线程、逻辑/物理侧、权威状态、网络和存档等实际行为检查 |
| `adapter` | 适配层路径、source set、模块或明确的“无适配层原因” |
| `evidence` | 对应版本的官方文档、Mod 源码/Javadoc、构件元数据、日志或测试报告 |
| `dependency_graph` | `requires`、`ordering`、`conflicts`；必须检查有向顺序环 |
| `save_schema` / `network_schema` | 数据/网络格式、版本、迁移策略和证据 |
| `fallback_behavior` | 缺失 Mod、错误版本、client/server 不对称时的明确行为 |
| `evidence` | 对象化记录 `type`、来源、commit 和 observed/planned/blocked 状态 |
| `status` | `planned` → `implemented` → `built` → `launched` → `verified`，或 `blocked` |

### 必须区分的依赖状态

- **编译依赖**：需要目标版本的 API、接口或注解才能编译。
- **运行依赖**：代码可编译，但目标实例运行时必须装载该 Mod。
- **可选联动**：Mod 不存在时仍能启动；用目标 loader 的 optional metadata、条件注册或隔离 adapter 表达。`mandatory=false` 只表示加载前不强制，不代表运行时 API 可直接调用。
- **客户端专属**：渲染、屏幕、键位和模型类只能在物理客户端加载；专用服务端不能解析它们。
- **数据/存档依赖**：配方、标签、世界生成、NBT、Attachment/Capability 或注册表 ID 变化时，必须有迁移/回退策略。

依赖元数据和代码适配是两层约束：元数据负责 loader 在加载前判断“是否允许进入游戏”，adapter 负责 Mod 存在后如何调用目标版本 API。两者都必须与矩阵一致。以 Forge 1.20.1 为例，`mods.toml` 依赖项要分别核对 `modId`、`mandatory`、Maven `versionRange`、`ordering` 和物理 `side`，不要只写一个宽泛版本号；其他目标 loader 的字段以对应官方模板为准。

## 逐 Mod 运行语义审查

对每个联动 Mod 按目标版本分别阅读资料和代码，至少回答：

1. **生命周期**：入口、注册事件、初始化顺序和事件总线是否改变？是否需要在对方 Mod 注册完成后再执行？
2. **注册表**：对象 ID、命名空间、holder/RegistryObject、延迟注册和 tag 是否仍然可用？
3. **逻辑侧与线程**：回调在哪一侧、哪个线程运行？handler 是否必须切到主线程？单人游戏的逻辑服务端是否仍是权威？
4. **网络**：payload/message ID、codec、方向、协议版本和服务端校验是否变化？不要复用不兼容的 wire schema。
5. **数据模型**：Capability、Attachment、data component、NBT、SavedData、配置或 API 返回值是否改变？
6. **客户端行为**：screen、renderer、keybind、model layer、shader 或资源重载入口是否需要独立 client adapter？
7. **失败降级**：目标 Mod 缺失、版本不满足、只装在一侧或初始化失败时，本 Mod 是否安全禁用该联动而继续启动？
8. **存档/世界**：注册 ID、维度、实体、方块实体或 NBT schema 变化时，旧存档是否可读，是否需要数据 fixer/迁移脚本？

不要把“能找到同名方法”当作运行逻辑兼容。至少需要一个目标版本启动日志或组合测试证据；网络、存档和世界生成联动需要专项回归。

## 适配层规则

```text
common/                  # 不依赖任一联动 Mod 的领域逻辑
compat/<mod_id>/common/  # 目标 Mod 的公共 API 适配
compat/<mod_id>/client/  # 目标 Mod 的客户端适配
compat/<mod_id>/server/  # 目标 Mod 的服务端/存档适配
```

- 每个 loader/Minecraft 目标使用独立 source set、模块或迁移分支；不要在一个活动类中堆叠三个版本的 import。
- 通过编译期依赖、目标版本 metadata、Dist/side 隔离和明确的 adapter 接口控制可选联动。
- 反射只作为最后的兼容边界，并记录类名、方法签名、失败降级和版本证据；不能用反射掩盖未验证的 API 差异。
- 联动逻辑不得改变本 Mod 的核心状态权威；目标 Mod 只通过 adapter 接口参与。

## 验证矩阵

每条有向迁移路径至少验证：

```text
BASELINE_ONLY                         # 目标 Mod 缺失，本 Mod 可启动
TARGET_MOD_PRESENT                    # 目标版本 Mod 已安装，联动功能启用
TARGET_MOD_WRONG_VERSION              # 版本不满足，安全降级并给出明确日志
CLIENT_SERVER_ASYMMETRY               # 仅一侧安装时不加载错误侧类
DATA_AND_SAVE                         # 配方/标签/存档/世界数据回归
NETWORK_IF_USED                       # payload/message、方向、线程和校验
```

证据必须标注是静态检查、构建、CI、客户端、专用服务器还是实际组合游戏测试。每个矩阵行都必须填写 `verification_requirements`，显式列出 required evidence、`not_applicable` 类型和理由；已知 profile 包括 `build_client_server`、`build_launch_gametest`、`build_client_only`、`build_server_only`、`build_launch_only` 和 `custom`。`verified` 必须满足该行 required 集合中的全部 observed 证据，不能再用“任意一种运行证据”推断。只有静态检查时状态为 `implemented`，只有构建时为 `built`，只有启动时为 `launched`。
