# Forge 1.20.1 联动依赖元数据

来源：Forge Documentation 1.20.x 的 `gettingstarted/modfiles.md`，固定提交见 [`official-docs.md`](../official-docs.md)。

## 规范化字段

`src/main/resources/META-INF/mods.toml` 使用：

```toml
[[dependencies.examplemod]]
modId="compat_mod"
mandatory=false
versionRange="[target-version]"
ordering="AFTER"
side="BOTH"
```

矩阵统一映射为 `loader_metadata.mod_id`、`mandatory`、`version_range`、`ordering`、`side`，并在 `raw_fields` 中保留 Forge 原始键名。

## 关键约束

- `modLoader`、`loaderVersion`、`license`、`[[mods]]` 和 `[[dependencies.<mod_id>]]` 必须位于目标 Forge 构件的 `mods.toml`。
- `mandatory` 是加载前的硬依赖判断；可选联动必须设为 `false`，并在 adapter 中实现缺失降级。
- `versionRange` 是 Maven 版本范围；`ordering` 只能是 `BEFORE`、`AFTER` 或 `NONE`，并检查循环。
- `side=CLIENT` 的依赖和代码不能被 dedicated server 解析；目标 Mod API 仍需单独检查生命周期、事件、网络和存档语义。
