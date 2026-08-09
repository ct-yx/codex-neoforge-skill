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
