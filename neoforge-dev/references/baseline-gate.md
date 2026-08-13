# 基线门控

本 skill 的默认基线是 **NeoForge 1.21.1**。Forge 1.20.1 和 Cleanroom 1.12.2 只作为后续迁移目标，不得在基线尚未验收时混入实现代码。

```text
BASELINE_GATE:
先完成 NeoForge 1.21.1 基线开发与验收。
基线未完成时，只记录迁移资料，不执行 Forge/Cleanroom 移植设计或代码修改。
只有基线验收完成且用户明确指定目标加载器和版本后，才进入移植任务。
```

## 门控输入

在项目根目录记录以下事实，不以目录名或用户猜测代替：

- `loader`: `neoforge`、`forge` 或 `cleanroom`
- `minecraft`: `1.21.1`、`1.20.1` 或 `1.12.2`
- `java`: 实际 toolchain、`java -version` 和 CI 版本
- `baseline_status`: `in_progress`、`accepted` 或 `unknown`
- `baseline_evidence`: 命令、日志、提交或 CI 链接

没有证据时使用 `unknown`，并继续做识别和静态检查；不要把 `unknown` 当作 `accepted`。

## NeoForge 1.21.1 验收清单

只有下列项目全部通过或明确记录为环境无法运行，才可把 `baseline_status` 标为 `accepted`：

1. `./gradlew compileJava`（项目存在该任务时）。
2. `./gradlew build`，并检查 `build/libs` 中的产物。
3. 项目配置的数据生成任务或 Data run configuration；检查 `src/generated/resources`。
4. `runClient` 与 `runServer` 至少各启动一次；检查 `runs/*/logs/latest.log` 和 crash report。
5. 资源静态检查：mod 元数据、assets/data 命名空间、语言、模型、配方、标签和 pack 元数据。
6. 项目存在 GameTest/JUnit 时运行相应测试。
7. 记录 Minecraft、NeoForge、Java、Gradle、mappings 和提交版本。

显示、图形、专用服务器或网络环境阻止的项目必须保留未通过项及原因；不要宣称完整验收。

## 迁移解锁条件

满足以下条件后才允许编辑迁移代码：

- 基线验收清单已有可复核证据；
- 用户明确指定目标加载器和版本（`Forge 1.20.1` 或 `Cleanroom 1.12.2`）；
- 迁移分支/提交已与基线实现分离；
- 先读取对应 `references/<loader>/<version>.md` 和迁移指南。
- 如果存在联动 Mod，已建立源/目标版本的 `compatibility-matrix.json`，并为每个 Mod 记录目标构件、运行语义、适配层和缺失/错版本降级策略。

门控未解锁时，可以更新资料、建立差异表、建立联动矩阵草稿和运行只读识别脚本，但不能做 Forge/Cleanroom API 替换、重写构建文件或提交移植代码。
