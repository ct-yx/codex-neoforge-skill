# Codex Minecraft Mod Skill

[![Validate](https://github.com/ct-yx/codex-neoforge-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/ct-yx/codex-neoforge-skill/actions/workflows/validate.yml)
[![Latest release](https://img.shields.io/github/v/release/ct-yx/codex-neoforge-skill)](https://github.com/ct-yx/codex-neoforge-skill/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

面向 Codex 的 Minecraft 模组开发 skill。**默认以 NeoForge 1.21.1 / Java 21 为开发基线**，并提供 Forge 1.20.1、Cleanroom 1.12.2 的版本知识库和后续迁移参考。

它不是加载器、Mod 模板或构建工具，而是一套让 Codex 按正确版本、正确项目结构和可复核验证流程工作的工程规范。

## 你会得到什么

| 能力 | 内容 |
| --- | --- |
| 项目识别 | 从 Gradle、元数据和目录识别 loader、Minecraft、Java、构建插件和资源布局 |
| 代码规范 | Java 命名、包结构、common/client/server 隔离、线程与网络输入校验提示词 |
| NeoForge 基线 | 1.21.1 的注册、事件、payload、资源、数据生成、存储、Mixin/AT 和验收流程 |
| 后续迁移 | Forge 1.20.1 与 Cleanroom 1.12.2 的版本差异、项目结构和分阶段迁移指南 |
| 辅助脚本 | 文档爬取、标题/关键词索引、loader 识别、项目结构检查 |
| 交付验证 | compile、build、数据生成、客户端/专用服务器、GameTest/JUnit 和日志证据记录 |

## 基线门控

迁移不是默认动作。skill 内置以下门控：

```text
BASELINE_GATE:
先完成 NeoForge 1.21.1 基线开发与验收。
基线未完成时，只记录迁移资料，不执行 Forge/Cleanroom 移植设计或代码修改。
只有基线验收完成且用户明确指定目标加载器和版本后，才进入移植任务。
```

因此，在 NeoForge 1.21.1 尚未完成 `compileJava`、`build`、数据生成、客户端/专用服务器和资源验收前，Codex 不会把 Forge 或 Cleanroom API 替换进基线代码。完整规则见 [`neoforge-dev/references/baseline-gate.md`](neoforge-dev/references/baseline-gate.md)。

## 支持的版本线

| 用途 | Minecraft | Java | 典型元数据/构建 | 状态 |
| --- | --- | --- | --- | --- |
| 当前开发基线 | NeoForge 1.21.1 | 21 | `neoforge.mods.toml`、ModDevGradle/NeoGradle | 默认执行 |
| 后续迁移目标 | Forge 1.20.1 | 17 | `mods.toml`、ForgeGradle/MDK、`SimpleChannel` | 基线验收后 |
| 后续迁移目标 | Cleanroom 1.12.2 | 以模板和 CI 为准；审计模板使用 Java 25 toolchain | Blossom 模板、`mcmod.info`、旧版 FML 生命周期 | 基线验收后 |

版本细节和官方来源：

- [NeoForge 1.21.1](neoforge-dev/references/neoforge/1.21.1.md)
- [Forge 1.20.1](neoforge-dev/references/forge/1.20.1.md)
- [Cleanroom 1.12.2](neoforge-dev/references/cleanroom/1.12.2.md)
- [版本审计记录](neoforge-dev/references/official-docs.md)

## 安装

### 方式一：从 Release 安装（macOS/Linux）

```bash
set -e
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
tmp="$(mktemp -d)"
mkdir -p "$CODEX_HOME/skills"

curl -fL https://github.com/ct-yx/codex-neoforge-skill/releases/latest/download/neoforge-dev.zip \
  -o "$tmp/neoforge-dev.zip"
curl -fL https://github.com/ct-yx/codex-neoforge-skill/releases/latest/download/neoforge-dev.zip.sha256 \
  -o "$tmp/neoforge-dev.zip.sha256"
(cd "$tmp" && shasum -a 256 -c neoforge-dev.zip.sha256)
unzip -q -o "$tmp/neoforge-dev.zip" -d "$CODEX_HOME/skills"
```

如果已有旧版本，推荐使用下面的源码安装方式；`install.sh --force` 会先把旧目录移动为带时间戳的备份。

### 方式二：从源码安装（推荐开发者）

```bash
git clone https://github.com/ct-yx/codex-neoforge-skill.git
cd codex-neoforge-skill
./install.sh
```

覆盖已有安装并保留备份：

```bash
./install.sh --force
```

Windows PowerShell：

```powershell
git clone https://github.com/ct-yx/codex-neoforge-skill.git
Set-Location codex-neoforge-skill
.\install.ps1
```

安装完成后，从下一个 Codex 回合开始使用 `$neoforge-dev`。

## 使用

显式调用：

```text
使用 $neoforge-dev 以 NeoForge 1.21.1 为基线检查当前项目，并完成这个模组开发任务。
```

常见请求：

```text
使用 $neoforge-dev 检查当前项目的 NeoForge 1.21.1 注册、资源和数据生成是否一致。
使用 $neoforge-dev 按 BASELINE_GATE 记录当前基线验收状态，不要开始 Forge 移植。
基线已验收；使用 $neoforge-dev 将当前模组迁移到 Forge 1.20.1，并逐阶段验证。
```

涉及 NeoForge/Forge/Cleanroom 模组开发、构建、数据生成、版本兼容、迁移或崩溃排查时，也可以让 Codex 自动触发。

## 推荐工作流

1. 读取仓库 `AGENTS.md`、README 和 Gradle 配置。
2. 运行 loader 与项目结构识别脚本，确认唯一目标版本。
3. 默认加载 NeoForge 1.21.1 知识库；迁移请求先检查 `BASELINE_GATE`。
4. 沿用现有包结构和注册体系，隔离 common、server、client 代码。
5. 同步 Java 源码、资源、数据生成和测试，避免跨 loader API 混用。
6. 运行实际存在的 Gradle 任务，再报告命令、产物、日志和未验证项。

## 辅助脚本

脚本位于已安装 skill 的 `scripts/` 目录，也可在仓库根目录使用同名 wrapper。

### 识别 loader 和版本

```bash
python3 neoforge-dev/scripts/validate_loader.py /path/to/mod-project --json
python3 neoforge-dev/scripts/validate_loader.py /path/to/mod-project \
  --expect-loader neoforge --expect-minecraft 1.21.1
```

### 检查项目结构

```bash
python3 neoforge-dev/scripts/validate_structure.py /path/to/mod-project --loader auto
python3 neoforge-dev/scripts/validate_structure.py /path/to/mod-project --loader forge --json
```

### 抓取和索引文档

```bash
python3 neoforge-dev/scripts/crawl_docs.py \
  --url https://docs.neoforged.net/docs/1.21.1/ \
  --output /tmp/neoforge-docs --max-pages 200

python3 neoforge-dev/scripts/build_doc_index.py \
  --input /tmp/neoforge-docs/pages \
  --output /tmp/neoforge-doc-index.json
```

爬虫只跟随起始站点同域名 HTML 链接，记录 URL、标题、哈希、链接数量和抓取错误；对 429/5xx 做有限退避，不修改模组项目。

## 仓库结构

```text
.
├── neoforge-dev/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   │   ├── common/                 # Java、包、资源、测试规范
│   │   ├── neoforge/1.21.1.md     # 当前基线
│   │   ├── forge/1.20.1.md         # 后续目标
│   │   ├── cleanroom/1.12.2.md    # 后续目标
│   │   ├── migration/              # 迁移差异与阶段顺序
│   │   └── baseline-gate.md        # 基线解锁条件
│   └── scripts/                    # 安装后可直接调用的辅助脚本
├── scripts/                        # 校验、打包和仓库 wrapper
├── install.sh / install.ps1
├── NOTICE.md
└── README.md
```

## 本地验证和打包

```bash
python3 scripts/validate.py
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" neoforge-dev
python3 -B neoforge-dev/scripts/crawl_docs.py --help
python3 -B neoforge-dev/scripts/build_doc_index.py --help
python3 -B neoforge-dev/scripts/validate_loader.py --help
python3 -B neoforge-dev/scripts/validate_structure.py --help
python3 scripts/package.py
unzip -t dist/neoforge-dev.zip
```

打包产物：`dist/neoforge-dev.zip` 和 `dist/neoforge-dev.zip.sha256`。ZIP 保留顶层 `neoforge-dev/`，可直接解压到 `$CODEX_HOME/skills`。

## 官方资料与适配来源

- [NeoForge 官方文档](https://docs.neoforged.net/)，Documentation 提交 `816c03d31ff7948179c7bd4a58d23bcfda09c18a`
- [Forge 1.20.x Documentation](https://github.com/MinecraftForge/Documentation/tree/1.20.x)，提交 `87526dd760129b356e88f130550d646d4eb2fa31`
- [CleanroomMC Website](https://github.com/CleanroomMC/Website)、[CleanroomModTemplate](https://github.com/CleanroomMC/CleanroomModTemplate)、[ForgeDevEnv](https://github.com/CleanroomMC/ForgeDevEnv)、[CleanroomGradle](https://github.com/CleanroomMC/CleanroomGradle)
- 上游适配：[cnlimiter/opencode-neoforge-skill](https://github.com/cnlimiter/opencode-neoforge-skill)

详细归属和改动边界见 [NOTICE.md](NOTICE.md)。

## 参与贡献

请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。所有版本知识必须引用对应 loader/Minecraft 版本的官方资料，且提交前通过本地校验与 GitHub Actions。

## License

[MIT](LICENSE)
