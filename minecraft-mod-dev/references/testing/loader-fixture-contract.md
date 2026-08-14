# 三加载器 fixture 合约

为脚本回归准备最小项目时，fixture 只表达结构识别，不宣称 Minecraft 已启动。每个 fixture 应包含以下最小文件：

| Loader | 必需元数据 | 版本锚点 | Java 锚点 | 构建标记 |
| --- | --- | --- | --- | --- |
| NeoForge 1.21.1 | `src/main/resources/META-INF/neoforge.mods.toml` | `minecraft_version=1.21.1` | `JavaLanguageVersion.of(21)` | `net.neoforged`/ModDevGradle |
| Forge 1.20.1 | `src/main/resources/META-INF/mods.toml` | `minecraft_version=1.20.1` | `JavaLanguageVersion.of(17)` | `net.minecraftforge`/ForgeGradle |
| Cleanroom 1.12.2 | `src/main/resources/mcmod.info` 或模板资源 | `unimined.minecraft { version '1.12.2' }` | `JavaLanguageVersion.of(25)` | Unimined/Cleanroom |

## 结构检查边界

- `validate_loader.py` 必须按 Gradle 子项目输出 loader、Minecraft、Java、模块路径、证据文件和扫描文件；根项目检测到多个活动 loader 或版本时必须返回 `ambiguous`，要求使用显式目标。
- `validate_structure.py` 必须检查 wrapper、Gradle、Java、资源和对应 metadata。
- 缺少可选 `src/generated/resources` 或 `src/main/resource-templates` 时只产生 warning。
- 同时出现多套活动 metadata 时必须产生 warning，不静默选择。

## 组合测试夹具边界

兼容矩阵 fixture 至少覆盖：

```text
BASELINE_ONLY
TARGET_MOD_PRESENT
TARGET_MOD_WRONG_VERSION
CLIENT_SERVER_ASYMMETRY
INIT_ORDER_CHANGED
DATA_AND_SAVE
NETWORK_IF_USED
MIXIN_AT_CONFLICT
```

这些 fixture 验证的是矩阵状态机和诊断路径；实际 Mod jar、客户端和 dedicated server 仍需迁移项目单独提供并记录 evidence。
