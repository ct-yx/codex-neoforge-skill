# NeoForge 1.21.1 联动依赖元数据

来源：NeoForge Documentation 1.21.1 的 `gettingstarted/modfiles.md`，固定提交见 [`official-docs.md`](../official-docs.md)。

## 规范化字段

`neoforge.mods.toml` 的 `[[dependencies.<mod_id>]]` 至少按以下字段记录：

```toml
modId = "compat_mod"
mandatory = false
versionRange = "[target-version]"
ordering = "AFTER"
side = "BOTH"
```

矩阵统一映射为 `loader_metadata.mod_id`、`mandatory`、`version_range`、`ordering`、`side`；原始字段保存在 `raw_fields`。`mandatory=false` 仍不等于 adapter 自动安全，代码必须处理 Mod 缺失和错误版本。

## 关键约束

- 文件为 `src/main/resources/META-INF/neoforge.mods.toml`。
- `modLoader`/`loaderVersion`、`[[mods]]` 和依赖表必须与目标 NeoForge 项目一致。
- `side=CLIENT` 的联动不得让服务端解析客户端类；`BOTH` 表示两侧都要满足加载条件。
- `ordering` 只表达初始化顺序，不能替代注册完成检查；检查是否存在循环顺序。
- 版本范围使用 Maven version range；锁文件另记录解析后的实际构件和 SHA-256。
