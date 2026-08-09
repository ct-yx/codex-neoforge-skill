# 资源与数据布局

## 标识符不变量

```text
mod_id == Java 注册命名空间 == assets/<mod_id> == data/<mod_id> == 资源 JSON 中的 namespace
```

`mod_id` 使用小写 ASCII、数字和下划线；显示名、翻译文本和仓库名不参与资源路径。注册对象名、模型文件、配方、loot、tags 和语言键必须能通过同一映射互相定位。

## 三条版本线

| 目标 | 元数据 | 客户端资源 | 服务端数据 | 数据生成提示 |
| --- | --- | --- | --- | --- |
| NeoForge 1.21.1 | `META-INF/neoforge.mods.toml` | `assets/<mod_id>/` | `data/<mod_id>/` | 以项目生成的 Data run configuration 和 `GatherDataEvent` 为准 |
| Forge 1.20.1 | `META-INF/mods.toml` | `assets/<mod_id>/` | `data/<mod_id>/` | 通常 `GatherDataEvent` + `runData` |
| Cleanroom 1.12.2 | 模板生成 `mcmod.info` | `assets/<mod_id>/` | `data/<mod_id>/` | 以 CleanroomGradle/项目任务为准 |

三行不能混用。尤其不要把 Forge 的 `mods.toml`、Cleanroom 的 `mcmod.info` 或旧版数据路径复制回 NeoForge 基线。

## 资源检查顺序

1. 从注册代码提取 `mod_id` 和注册路径。
2. 检查 `assets/<mod_id>/lang`、`models`、`textures`、音效和客户端专属文件。
3. 检查 `data/<mod_id>/recipes`、`loot_tables`、`tags`、`worldgen` 和目标版本要求的 JSON 命名。
4. 运行数据生成后只审查生成差异，不手改生成目录覆盖 provider 逻辑。
5. 用目标 loader 启动一次，阅读最早的 resource location、JSON schema 或 pack 报错。

`pack.mcmeta` 是否由 loader 合成取决于目标版本和构建插件；先看项目模板，避免重复文件导致覆盖或警告。
