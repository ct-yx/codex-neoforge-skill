# Java 代码契约

下面的规则可直接作为给 AI 的代码生成提示词。它们是工程约束，不是某个加载器的 API 文档。

```text
CODE_CONTRACT:
先读取目标项目的 AGENTS.md、Gradle 配置和现有同类代码；再写代码。
默认基线使用 Java 21、NeoForge 1.21.1；版本未确认时不要猜 API。
每个示例必须标注 loader、Minecraft、Java 和运行侧；禁止跨加载器/跨版本 import。
沿用仓库已有包名、注册方式、命名和日志门面；不要为单个功能引入第二套架构。
输出完整可编译的最小改动：源码、资源、数据生成和测试一起考虑，不留伪 API 或省略关键 import。
common/server 类不得静态引用 client-only 类；在逻辑侧判断前先说明数据应由哪一侧权威保存。
注册名、资源路径、翻译键和数据文件使用同一个小写 mod_id；不要把显示名称当作标识符。
网络输入视为不可信：服务端重新校验权限、范围、区块加载和状态；handler 明确线程切换。
修改后按目标项目实际任务运行 compileJava、build、数据生成和相关测试，并报告未运行项。
有联动 Mod 时，每个示例同时标注 source/target Mod 版本范围、依赖 scope、运行侧和 adapter 路径；不要用同一个 import 假设三个游戏版本的联动 API 等价。
```

## 命名与包

- Java 包名全部小写，根包与 `gradle.properties`/模组元数据一致，例如 `com.example.examplemod`。
- 类名使用 PascalCase，方法/字段使用 camelCase，常量使用 `UPPER_SNAKE_CASE`；注册路径使用 `snake_case` 或项目既有风格。
- 一个类只负责一个清晰的生命周期/领域边界；事件订阅、注册、网络 payload 和客户端渲染不要混在入口类中。
- 优先构造器注入和不可变字段；只有框架要求时才使用静态注册器或反射。
- 日志包含 mod_id、对象标识和失败上下文；不要在正常 tick 中打印高频日志。

## 侧与线程

先区分逻辑侧和物理侧：`Level#isClientSide()`/目标版本等价物用于游戏逻辑，`Dist`/目标版本等价物用于类加载隔离。事件或网络 handler 不默认运行在主线程；按目标版本 API 显式 `enqueueWork` 或使用上下文提供的调度器。

## 交付前自检

```text
[ ] 版本和 loader 已从项目文件确认
[ ] 没有跨 loader 包名、跨版本类名或 current-doc API 泄漏
[ ] common/server classpath 不包含 client-only 引用
[ ] 注册、资源、数据、翻译、测试命名一致
[ ] 网络数据在服务端重新验证
[ ] 运行命令和失败证据已记录
[ ] 联动 Mod 的源/目标构件、运行语义、降级和组合测试已记录
```
