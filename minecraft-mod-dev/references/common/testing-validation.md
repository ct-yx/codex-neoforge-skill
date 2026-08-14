# 测试与验收

## 命令选择

```bash
./gradlew tasks --all                 # 先确认真实任务名
./gradlew compileJava                 # 任务存在时
./gradlew build                       # 通用回归
./gradlew runData                     # Forge 1.20.1 常见；不可盲猜
./gradlew runClientData runServerData # 当前 NeoForge 文档线常见；不可盲猜
./gradlew runClient
./gradlew runServer
```

命令只作为候选；始终以 `./gradlew tasks`、构建脚本和项目生成的 run configuration 为准。Cleanroom 模板常见 `runClient`、`runServer`、`genSources`，也必须现场确认。

## 证据记录

每次任务至少记录：目标 loader/Minecraft/Java、执行命令、退出码、产物路径、首个有效错误栈帧和未运行原因。把静态检查、CI 和真实客户端/专用服务器验证分开描述。

## 联动 Mod 验收

有跨 Mod 联动时，不能只验证本 Mod 单独启动。对 `compatibility-matrix.json` 中每个有向迁移行执行：

1. 目标联动 Mod 缺失：本 Mod 核心功能能启动，联动安全关闭。
2. 目标版本联动 Mod 存在：注册、事件、网络、数据、渲染和存档行为符合目标版本语义。
3. 版本不满足：阻止错误 API 加载，输出 mod_id/版本范围/降级原因。
4. 只装客户端或只装服务端：不加载错误侧类，不破坏 dedicated server。
5. 需要时回归网络 payload、配方/tag、世界生成、旧存档和注册 ID。

矩阵行必须先声明 `verification_requirements` 的 required/not_applicable 组合；只有 required 集合中的全部 observed 构建与适用运行证据存在时，才能从 `implemented` 更新为 `verified`。不能用任意一个运行证据替代客户端、服务端或专用测试的明确要求。

## 回归矩阵

| 范围 | 最小检查 |
| --- | --- |
| 注册/资源 | `compileJava`、资源路径检查、客户端启动 |
| 网络/菜单 | `build`、服务端启动、客户端连接/handler 日志 |
| 数据生成 | 对应 Data 任务、`src/generated/resources` diff、加载资源 |
| 世界生成/存档 | dedicated server、创建/重载世界、旧存档回归 |
| 客户端渲染 | `runClient`、日志无 client classpath 错误 |
| Mixin/AT | 构建、启动、目标类注入审计和失败策略 |

没有图形或专用服务器环境时，保留可复核的静态/构建证据，并把运行验证标记为待完成。
