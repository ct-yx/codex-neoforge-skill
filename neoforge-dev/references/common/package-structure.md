# 项目结构规则

## NeoForge 1.21.1 基线

```text
project/
├── gradlew*                 # wrapper；不要提交本机绝对路径
├── settings.gradle[.kts]
├── build.gradle[.kts]
├── gradle.properties         # mod_id、版本、Minecraft/NeoForge 版本等
├── src/main/java/<root>/
│   ├── <Mod>.java            # 只做入口和总线连接
│   ├── registry/             # DeferredRegister/holder
│   ├── event/                # mod bus 与 NeoForge bus 订阅
│   ├── network/              # payload、codec、handler
│   ├── data/                 # datagen providers
│   ├── world/                # worldgen、attachment 等
│   └── client/               # client-only 注册、屏幕、渲染
├── src/main/resources/
│   ├── META-INF/neoforge.mods.toml
│   ├── assets/<mod_id>/      # lang、models、textures、音效等
│   └── data/<mod_id>/        # recipe、loot、tags、worldgen 等
└── src/generated/resources/  # datagen 输出；按仓库策略纳入版本控制
```

`client/` 不得被 common 入口直接加载；使用目标版本支持的客户端事件/Dist 隔离。不要手工复制现代 NeoForge 自动合成的 `pack.mcmeta`，除非项目确有覆盖需求。

## Forge 1.20.1 迁移形状

```text
src/main/java/<root>/
├── <Mod>.java
├── registry/       # DeferredRegister + RegistryObject
├── event/          # mod event bus / MinecraftForge.EVENT_BUS
├── network/        # SimpleChannel message
└── client/         # Dist.CLIENT / DistExecutor 隔离
src/main/resources/
├── META-INF/mods.toml
├── pack.mcmeta
├── assets/<mod_id>/
└── data/<mod_id>/
```

Forge 的 `mods.toml`、Java 17、SimpleChannel 和旧版事件签名不能出现在 NeoForge 1.21.1 基线源码中。

## Cleanroom 1.12.2 迁移形状

```text
src/main/java/<root>/
├── <Mod>.java
├── registry/       # 1.12.2 Forge 注册事件/对象
├── event/          # FML 生命周期与 MinecraftForge.EVENT_BUS
├── network/        # 1.12.2 网络实现
└── client/         # 物理客户端隔离
src/main/resources/
├── ${mod_id}_at.cfg             # 使用 MCP 名称，构建时转换
├── assets/<mod_id>/
├── data/<mod_id>/
└── （模板）mcmod.info、pack.mcmeta
src/main/resource-templates/
├── mcmod.info
└── pack.mcmeta
```

Cleanroom 模板还使用 `gradle.properties` 驱动的 Blossom 替换、`use_access_transformer`、`use_mixins` 和 `is_coremod` 开关。只有迁移任务解锁后才建立这些文件。

## 结构选择算法

1. 先运行 `scripts/validate_loader.py PROJECT`，再运行 `scripts/validate_structure.py PROJECT`。
2. 元数据文件和依赖声明冲突时，以构建脚本、Gradle 解析结果和实际任务为准，并把冲突记录下来。
3. 目录缺失时只创建目标功能需要的最小目录；不要为了“完整模板”生成空包或空资源。
4. 同一个项目不要同时保留 `neoforge.mods.toml`、`mods.toml`、`mcmod.info` 三套活动元数据；迁移分支可暂存目标模板，但不能让错误 loader 读取它。
