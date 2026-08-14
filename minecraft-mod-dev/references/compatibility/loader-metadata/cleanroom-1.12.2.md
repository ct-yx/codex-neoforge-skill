# Cleanroom 1.12.2 联动依赖元数据

来源：当前 `CleanroomModTemplate`、Cleanroom Website 的旧 Forge API/模组开发资料及固定提交，详见 [`official-docs.md`](../official-docs.md)。本文件描述 Cleanroom loader 的元数据，不扩展 Forge 1.12.2 支持。

## 模板事实

- 模板用 Blossom 生成 `mcmod.info`，当前模板只提供 `mod_id`、名称、版本、描述和 `mcversion` 等基础字段。
- 构件依赖在 `gradle/scripts/dependencies.gradle` 中使用 `modImplementation` 或 `modRuntimeOnly`；不要迁入 `fg.deobf()`/`rfg.deobf()`。
- Cleanroom 入口和侧隔离沿用 Forge 1.12.2 API 体系中的 `@Mod`、FML 生命周期、`@SidedProxy`/物理侧类加载规则；运行目标仍是 Cleanroom，不是独立 Forge 1.12.2。

## 矩阵记录规则

Cleanroom 没有可直接等同于现代 `mods.toml` 的统一依赖表时，`loader_metadata.raw_fields` 记录实际生成的 `mcmod.info`、Manifest 或模板配置字段，规范化字段仍填写：

```json
{
  "mod_id": "compat_mod",
  "mandatory": false,
  "version_range": "[target-version]",
  "ordering": "NONE",
  "side": "BOTH",
  "raw_fields": {"source": "mcmod.info or dependencies.gradle", "verified": false}
}
```

不要把 NeoForge/Forge 的 TOML 键名假设为 Cleanroom loader 行为。目标 Mod 缺失、错误版本和 client/server 不对称都必须通过目标实例日志验证；必要时使用无联动降级。
