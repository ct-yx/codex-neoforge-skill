# 联动 Mod 运行语义记录模板

将本文件复制到迁移项目中，为每个 `mod_id` 建立一份源版本 → 目标版本记录。没有目标构件或运行证据时保持 `planned`/`blocked`，不要填写成 `verified`。

## 身份与构件

```yaml
mod_id: compat_mod
source: neoforge:1.21.1
target: forge:1.20.1
source_artifact_ref: compat_mod-neoforge-1.21.1
target_artifact_ref: compat_mod-forge-1.20.1
source_resolved_version: TODO
target_resolved_version: TODO
source_sha256: TODO
target_sha256: TODO
license: TODO
artifact_repository: TODO
verification_requirements:
  profile: build_client_server
  required: [build, client, server]
  not_applicable: [launch, game_test]
  reason: TODO
```

## 运行语义审查

逐版本填写事实来源，不要用类名相同代替行为证据：

| 领域 | 源版本事实/证据 | 目标版本事实/证据 | adapter 或降级 |
| --- | --- | --- | --- |
| 生命周期与初始化顺序 | TODO | TODO | TODO |
| 注册表、ID、tag | TODO | TODO | TODO |
| 事件总线、优先级、线程 | TODO | TODO | TODO |
| 逻辑侧/物理侧 | TODO | TODO | TODO |
| Capability/Attachment/NBT/Data Component | TODO | TODO | TODO |
| 网络 payload/message、codec、方向、协议 | TODO | TODO | TODO |
| 配方、数据生成、世界生成 | TODO | TODO | TODO |
| 客户端渲染、屏幕、键位 | TODO | TODO | TODO |
| 存档、注册 ID、数据迁移 | TODO | TODO | TODO |
| 性能、tick、缓存和失效 | TODO | TODO | TODO |

## 依赖和 source set

- 目标 loader 元数据：记录 `mod_id`、`mandatory`、版本范围、`ordering`、`side` 和目标模板字段。
- 依赖范围：`compile`、`runtime`、`compile_runtime` 或 `optional`。
- 公共逻辑只调用本 Mod adapter 接口；目标 Mod API 放入 `compat/<mod_id>/<target-loader><target-minecraft>/`。
- 客户端类不得进入 dedicated server classpath；需要反射时记录类名、签名和失败降级。
- `dependency_graph` 必须列出 requires、ordering、conflicts；不得形成循环。

## 失败降级

| 情况 | 预期行为 | 日志/证据 |
| --- | --- | --- |
| 目标 Mod 缺失 | 核心功能继续运行，联动关闭 | TODO |
| 版本范围不满足 | 不加载目标 API，说明实际/期望版本 | TODO |
| 仅客户端或仅服务端存在 | 只在允许侧加载 adapter | TODO |
| 初始化顺序变化 | 延迟到目标注册完成后读取 | TODO |

## 验证记录

按 `verification_requirements` 记录 required 类型的 observed 证据，并把不适用的运行类型显式列在 `not_applicable`；除此之外可补充 `static`、`save`、`network` 证据。组合矩阵：

```text
BASELINE_ONLY / TARGET_MOD_PRESENT / TARGET_MOD_WRONG_VERSION
CLIENT_SERVER_ASYMMETRY / DATA_AND_SAVE / NETWORK_IF_USED
```
