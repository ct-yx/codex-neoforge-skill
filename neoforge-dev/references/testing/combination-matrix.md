# 三加载器组合测试模板

此模板用于迁移分支，不代表已经替用户完成真实 Minecraft 运行。每一行都要填目标加载器、Mod 构件、命令、日志和结果；真实组合测试需要目标游戏、Java、第三方 Mod 和客户端/专用服务器环境。

## 状态与证据

```text
planned -> implemented -> built -> launched -> verified
blocked（记录阻塞原因和无联动降级）
```

- `static`：源代码、资源、metadata 和依赖声明检查。
- `build`：Gradle 解析、`compileJava`、`build`、Data/资源生成。
- `launch`：目标实例启动并读取日志。
- `client` / `server`：客户端或 dedicated server 实例实际运行。
- `save`：创建、关闭、重载旧/新存档并检查注册 ID/NBT/Attachment/SavedData。
- `network`：客户端连接、payload/message codec、方向、线程和服务端权限校验。

## 最小组合矩阵

| Case ID | 联动 Mod | 目标构件 | 侧 | 预期 | 命令/日志 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| BASELINE_ONLY | 缺失 | 无 | client + server | 核心功能启动，adapter 关闭 | TODO | planned |
| TARGET_MOD_PRESENT | 目标版本 | 已锁定 | client + server | 注册、事件、数据、网络和渲染联动正常 | TODO | planned |
| TARGET_MOD_WRONG_VERSION | 错误版本 | 不满足范围 | client + server | 不加载错误 API，明确降级日志 | TODO | planned |
| CLIENT_ONLY | 目标版本 | 仅客户端 | client | 客户端入口正常，服务端不解析 client-only 类 | TODO | planned |
| SERVER_ONLY | 目标版本 | 仅服务端 | dedicated server | 服务端权威状态正常 | TODO | planned |
| INIT_ORDER_CHANGED | 目标版本 | 改变加载/注册顺序 | client + server | 延迟读取或明确失败，不出现竞态 | TODO | planned |
| DATA_AND_SAVE | 目标版本 | 已锁定 | server | 配方/tag/worldgen/旧存档可读或有迁移 | TODO | planned |
| NETWORK_IF_USED | 目标版本 | 已锁定 | client + server | schema、方向、线程和权限校验正确 | TODO | planned |
| MIXIN_AT_CONFLICT | 目标版本 | 已锁定 | client + server | 注入冲突有证据和失败策略 | TODO | planned |

## 完成门槛

仅当本 Mod `build` 成功、目标实例启动、目标 Mod 组合运行和需要的存档/网络回归均有证据时，才将对应兼容矩阵行升级为 `verified`。缺少客户端或专用服务器环境时，保留 `planned`/`blocked`，不要把静态检查当作运行通过。
