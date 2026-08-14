# Codex Minecraft Mod Skill

[![Validate](https://github.com/ct-yx/codex-minecraft-mod-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/ct-yx/codex-minecraft-mod-skill/actions/workflows/validate.yml)
[![Latest release](https://img.shields.io/github/v/release/ct-yx/codex-minecraft-mod-skill)](https://github.com/ct-yx/codex-minecraft-mod-skill/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

面向 **Codex** 的 Minecraft 模组开发 skill。默认以 **NeoForge 1.21.1 / Java 21** 为开发基线，提供项目识别、Java/Gradle 规范、注册与事件、资源与数据生成、构建验收，以及基线完成后的 Forge 1.20.1、Cleanroom 1.12.2 迁移和联动 Mod 兼容知识库。

它不是加载器、Mod 模板或构建工具，而是把版本事实、代码约束、项目结构和可复核证据组织成 Codex 可以执行的工程流程。

## 目录

- [30 秒开始](#30-秒开始)
- [范围与版本状态](#范围与版本状态)
- [基线门控](#基线门控)
- [核心能力](#核心能力)
- [推荐工作流](#推荐工作流)
- [跨版本迁移](#跨版本迁移)
- [联动 Mod 兼容](#联动-mod-兼容)
- [辅助脚本](#辅助脚本)
- [仓库结构](#仓库结构)
- [开发、验证与发布](#开发验证与发布)
- [资料、贡献与许可证](#资料贡献与许可证)

## 30 秒开始

### 前置条件

- 已安装 Codex；
- 源码安装需要 Git 和 Python 3；
- 只有实际操作 Minecraft 模组项目时，才需要该项目声明的 Java/Gradle 工具链。

### 方式一：从源码安装（推荐）

macOS/Linux：

```bash
git clone https://github.com/ct-yx/codex-minecraft-mod-skill.git
cd codex-minecraft-mod-skill
./install.sh
```

安装脚本默认写入 `${CODEX_HOME:-$HOME/.codex}/skills/minecraft-mod-dev`。目标目录已经存在时，脚本会停止；确认替换并保留带时间戳的备份：

```bash
./install.sh --force
```

Windows PowerShell：

```powershell
git clone https://github.com/ct-yx/codex-minecraft-mod-skill.git
Set-Location codex-minecraft-mod-skill
.\install.ps1
```

覆盖已有安装：

```powershell
.\install.ps1 -Force
```

从旧版 `neoforge-dev` 迁移时，安装新 skill 后可把旧目录移出扫描路径：

```bash
old="${CODEX_HOME:-$HOME/.codex}/skills/neoforge-dev"
if [[ -e "$old" || -L "$old" ]]; then
  mv "$old" "${old}.backup-renamed-$(date +%Y%m%d-%H%M%S)"
fi
```

旧版目录只作为迁移备份保留，新的调用名是 `$minecraft-mod-dev`。

安装完成后，从下一个 Codex 回合开始显式调用：

```text
使用 $minecraft-mod-dev 以 NeoForge 1.21.1 为基线检查当前项目，并完成这个模组开发任务。
```

也可以直接描述目标，或把 `$minecraft-mod-dev` 写在请求中：

```text
使用 $minecraft-mod-dev 检查 NeoForge 1.21.1 的注册、资源和数据生成是否一致。
使用 $minecraft-mod-dev 按 BASELINE_GATE 记录当前基线验收状态，不要开始 Forge 移植。
基线已验收；使用 $minecraft-mod-dev 将模组迁移到 Forge 1.20.1，并逐阶段验证。
基线已验收；使用 $minecraft-mod-dev 检查迁移分支中联动 Mod 的目标版本运行逻辑。
```

### 方式二：从 Release 安装（macOS/Linux）

Release 页面：[最新版本](https://github.com/ct-yx/codex-minecraft-mod-skill/releases/latest)。下载 ZIP 和同名 `.sha256` 后，下面的流程会先校验哈希，再在 staging 目录完整解压，最后原子替换安装目录；旧版本会移动为备份，不会和新旧文件混合：

```bash
set -euo pipefail
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$CODEX_HOME/skills"

curl -fL https://github.com/ct-yx/codex-minecraft-mod-skill/releases/latest/download/minecraft-mod-dev.zip \
  -o "$tmp/minecraft-mod-dev.zip"
curl -fL https://github.com/ct-yx/codex-minecraft-mod-skill/releases/latest/download/minecraft-mod-dev.zip.sha256 \
  -o "$tmp/minecraft-mod-dev.zip.sha256"

python3 - "$tmp/minecraft-mod-dev.zip" "$tmp/minecraft-mod-dev.zip.sha256" "$CODEX_HOME/skills" <<'PY'
import datetime
import hashlib
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

archive, checksum_file, skills_dir = map(Path, sys.argv[1:])
expected = checksum_file.read_text(encoding="utf-8").split()[0].lower()
digest = hashlib.sha256()
with archive.open("rb") as stream:
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
if digest.hexdigest() != expected:
    raise SystemExit("SHA-256 校验失败")

staging = Path(tempfile.mkdtemp(prefix=".minecraft-mod-dev.staging-", dir=skills_dir))
backup = None
target = skills_dir / "minecraft-mod-dev"
try:
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            path = Path(member.filename.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"不安全的 ZIP 路径: {member.filename}")
        if bundle.testzip() is not None:
            raise SystemExit("ZIP CRC 校验失败")
        bundle.extractall(staging)

    extracted = staging / "minecraft-mod-dev"
    if not (extracted / "SKILL.md").is_file():
        raise SystemExit("ZIP 缺少 minecraft-mod-dev/SKILL.md")
    if target.exists() or target.is_symlink():
        suffix = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = skills_dir / f"minecraft-mod-dev.backup-{suffix}"
        index = 1
        while backup.exists() or backup.is_symlink():
            backup = skills_dir / f"minecraft-mod-dev.backup-{suffix}-{index}"
            index += 1
        target.rename(backup)
    extracted.rename(target)
    print(f"已安装: {target}")
    if backup:
        print(f"旧版本备份: {backup}")
except Exception:
    if backup and backup.exists() and not target.exists():
        backup.rename(target)
    raise
finally:
    shutil.rmtree(staging, ignore_errors=True)
PY
```

Release ZIP 保留顶层 `minecraft-mod-dev/`，可直接用于 `$CODEX_HOME/skills`。Release 安装只依赖 Python 3，不要求 `shasum` 或 `sha256sum`。

## 范围与版本状态

| 用途 | Minecraft | Java | 典型元数据/构建 | 状态 |
| --- | --- | --- | --- | --- |
| 当前开发基线 | NeoForge 1.21.1 | 21 | `neoforge.mods.toml`、ModDevGradle/NeoGradle | 默认执行 |
| 后续迁移目标 | Forge 1.20.1 | 17 | `mods.toml`、ForgeGradle/MDK、`SimpleChannel` | 基线验收后 |
| 后续迁移目标 | Cleanroom 1.12.2 | 以模板和 CI 为准；审计模板使用 Java 25 toolchain | Blossom、`mcmod.info`、旧版 FML 生命周期 | 基线验收后 |

版本表是工作边界，不是对任意项目模板的强制配置。每次任务仍需读取项目实际的 Gradle toolchain、loader 元数据、mapping、运行目录和任务列表。

## 基线门控

迁移默认锁定在基线完成之后。skill 使用以下不可省略的规则：

```text
BASELINE_GATE:
先完成 NeoForge 1.21.1 基线开发与验收。
基线未完成时，只记录迁移资料，不执行 Forge/Cleanroom 移植设计或代码修改。
只有基线验收完成且用户明确指定目标加载器和版本后，才进入移植任务。
```

NeoForge 1.21.1 基线至少要记录以下证据：

1. `compileJava`（项目存在该任务时）和 `build`；
2. 数据生成或 Data run configuration，以及生成资源检查；
3. `runClient` 和 `runServer` 各至少一次，包含日志/crash report 结论；
4. 资源、metadata、语言、模型、配方、标签和 pack 元数据检查；
5. 项目存在时的 GameTest/JUnit；
6. Minecraft、loader、Java、Gradle、mapping 和提交版本。

图形、专用服务器或网络环境不可用时，保留未完成项和原因，不能把静态检查当作完整验收。详细门控见 [`baseline-gate.md`](minecraft-mod-dev/references/baseline-gate.md)。

## 核心能力

| 能力 | 产出 |
| --- | --- |
| 项目识别 | 按 Gradle 子项目识别 loader、Minecraft、Java、metadata、wrapper 和证据文件；多 loader/多版本默认标记 `ambiguous` |
| Java/项目规范 | 包结构、命名、common/client/server 隔离、资源命名、线程和网络输入校验提示词 |
| NeoForge 基线开发 | 1.21.1 的注册、事件、payload、资源、数据生成、存储、Mixin/AT 和构建调试规则 |
| 迁移规划与实施 | NeoForge、Forge、Cleanroom 三者之间六条独立的有向迁移路径 |
| 联动 Mod 适配 | 同时记录目标 Mod 的版本构件、metadata、注册/事件/网络/数据/存档语义、adapter、降级和组合测试 |
| 可复核交付 | 区分静态、构建、启动、client、server、GameTest、存档和网络 evidence |

## 推荐工作流

### 1. 先读项目事实

不要按目录名或记忆猜版本。先读取适用的 `AGENTS.md`、README、`settings.gradle[.kts]`、`build.gradle[.kts]`、`gradle.properties` 和 `gradlew`，再运行：

```bash
python3 minecraft-mod-dev/scripts/validate_loader.py /path/to/mod-project --json
python3 minecraft-mod-dev/scripts/validate_structure.py /path/to/mod-project --loader auto --json
```

识别到多模块、多 loader 或版本冲突时，显式选择目标，不要静默把整个项目压成一个 loader。

### 2. 按目标版本加载知识库

只读取与已确认目标匹配的参考文件：

| 目标 | 入口 | 不要混入 |
| --- | --- | --- |
| NeoForge 1.21.1 | [`neoforge/1.21.1.md`](minecraft-mod-dev/references/neoforge/1.21.1.md) | Forge `mods.toml`/`SimpleChannel`、Cleanroom `mcmod.info`/旧生命周期、26.1/Java 25 API |
| Forge 1.20.1 | [`forge/1.20.1.md`](minecraft-mod-dev/references/forge/1.20.1.md) | NeoForge payload/StreamCodec、Cleanroom 1.12.2 生命周期、Java 21 假设 |
| Cleanroom 1.12.2 | [`cleanroom/1.12.2.md`](minecraft-mod-dev/references/cleanroom/1.12.2.md) | 1.20.1/1.21.1 注册、现代 data components、现代 payload |

### 3. 实现并验证

1. 沿用仓库已有包结构、注册方式、日志和测试风格；列出最小文件集合。
2. 将领域逻辑放在 `common/`，将 client/server 和联动 adapter 隔离；专用服务器不能加载 client-only 类。
3. 同步 Java 源码、资源、数据生成和测试，保持 `mod_id`、注册名、资源路径、翻译键、配方、loot 和 tag 一致。
4. 先运行真实存在的 `compileJava`/`build` 任务，再运行对应的数据生成、客户端、专用服务器和测试。
5. 报告命令、退出结果、产物、日志路径和仍未运行的验证；不把计划写成通过。

常见任务仅作示例，最终以 `./gradlew tasks --all` 为准：

```bash
./gradlew tasks --all
./gradlew compileJava   # 存在时
./gradlew build
./gradlew runClient     # 需要且存在时
./gradlew runServer     # 需要且存在时
```

## 跨版本迁移

三条版本线之间共有 **六条有向路径**；任意两个版本可以分别建立源 → 目标迁移，但反向路径不是正向迁移的机械逆操作，必须独立核对构建、生命周期、注册、事件、网络、资源、存档和联动 Mod 语义。

| 源 → 目标 | 指南 |
| --- | --- |
| NeoForge 1.21.1 → Forge 1.20.1 | [`neoforge-to-forge.md`](minecraft-mod-dev/references/migration/neoforge-to-forge.md) |
| Forge 1.20.1 → NeoForge 1.21.1 | [`forge-to-neoforge.md`](minecraft-mod-dev/references/migration/forge-to-neoforge.md) |
| NeoForge 1.21.1 → Cleanroom 1.12.2 | [`neoforge-to-cleanroom.md`](minecraft-mod-dev/references/migration/neoforge-to-cleanroom.md) |
| Cleanroom 1.12.2 → NeoForge 1.21.1 | [`cleanroom-to-neoforge.md`](minecraft-mod-dev/references/migration/cleanroom-to-neoforge.md) |
| Forge 1.20.1 → Cleanroom 1.12.2 | [`forge-to-cleanroom.md`](minecraft-mod-dev/references/migration/forge-to-cleanroom.md) |
| Cleanroom 1.12.2 → Forge 1.20.1 | [`cleanroom-to-forge.md`](minecraft-mod-dev/references/migration/cleanroom-to-forge.md) |

迁移分支的最小顺序：

1. 基线门控已解锁，且用户明确指定目标 loader/Minecraft/Java；
2. 先让目标 Gradle、metadata 和空入口解析；
3. 再迁移入口/注册/事件、联动 adapter、网络/存储、资源/数据和 client/server；
4. 运行无联动、目标版本、错误版本、client/server 不对称、数据/存档和网络回归；
5. 迁移失败或目标联动 API 的修复留在迁移分支，不回写已验收的 NeoForge 基线。

## 联动 Mod 兼容

迁移的不只是本 Mod API，还包括其他 Mod 在目标版本中的**实际运行逻辑**。同名 `mod_id`、类名或依赖声明不能证明注册时序、事件线程、Capability/Attachment、payload、客户端入口或存档格式相同。

每个联动 Mod、每条源 → 目标路径各建立一行 `compatibility-matrix.json`：

- 根节点使用 `schema_version: 2`；
- `artifact-lock.json` 锁定解析版本、来源、许可证和 SHA-256；
- 分别记录源/目标构件、版本范围、loader metadata、依赖 scope、side、integration surfaces、adapter、存档/网络 schema 和缺失/错版本降级；
- 状态按 `planned → implemented → built → launched → verified` 推进；目标构件缺失时使用 `blocked` 并写明无联动降级；
- `verification_requirements` 必须声明 `profile`、全部 `required` evidence、`not_applicable` 和理由；只有 required 集合中的证据全部为 `observed` 才能标记 `verified`。

可用 profile 包括：`build_client_server`、`build_launch_gametest`、`build_client_only`、`build_server_only`、`build_launch_only` 和 `custom`。示例和模板：

- [`mod-compatibility.md`](minecraft-mod-dev/references/compatibility/mod-compatibility.md)
- [`compatibility-matrix.example.json`](minecraft-mod-dev/references/compatibility/compatibility-matrix.example.json)
- [`schema.json`](minecraft-mod-dev/references/compatibility/schema.json)
- [`artifact-lock.example.json`](minecraft-mod-dev/references/compatibility/artifact-lock.example.json)
- [`integration-template.md`](minecraft-mod-dev/references/compatibility/integration-template.md)
- [`combination-matrix.md`](minecraft-mod-dev/references/testing/combination-matrix.md)

推荐的 adapter 布局：

```text
src/main/java/<root-package>/
├── common/                    # 不依赖具体联动 Mod 的领域逻辑
├── compat/<mod_id>/           # 联动接口
│   ├── neoforge1211/          # NeoForge 1.21.1 adapter
│   ├── forge1201/             # Forge 1.20.1 adapter
│   └── cleanroom1122/         # Cleanroom 1.12.2 adapter
├── client/                    # 客户端入口与渲染
└── server/                    # 服务端入口与权威状态
```

## 辅助脚本

安装后脚本位于 `${CODEX_HOME:-$HOME/.codex}/skills/minecraft-mod-dev/scripts`；在本仓库中可直接使用 `minecraft-mod-dev/scripts/`，根目录 `scripts/` 提供相同的 CLI wrapper。

| 脚本 | 用途 | 示例 |
| --- | --- | --- |
| `validate_loader.py` | 按 Gradle 子项目识别 loader、Minecraft、Java 和证据；期望不匹配时返回非零 | `python3 minecraft-mod-dev/scripts/validate_loader.py PROJECT --expect-loader neoforge --expect-minecraft 1.21.1` |
| `validate_structure.py` | 检查 wrapper、Gradle、Java/资源目录和 loader metadata | `python3 minecraft-mod-dev/scripts/validate_structure.py PROJECT --loader auto --json` |
| `validate_compatibility.py` | 校验 Schema v2、构件、依赖图和 verification requirements | `python3 minecraft-mod-dev/scripts/validate_compatibility.py compatibility-matrix.json --json` |
| `validate_dependency_graph.py` | 检查 requires/ordering/conflicts 及循环 | `python3 minecraft-mod-dev/scripts/validate_dependency_graph.py compatibility-matrix.json --json` |
| `generate_compatibility_report.py` | 将矩阵生成 Markdown 报告 | `python3 minecraft-mod-dev/scripts/generate_compatibility_report.py compatibility-matrix.json --output /tmp/compatibility-report.md` |
| `validate_matrix_fixtures.py` | 回归 planned/blocked/verified、缺失/错版本/侧不对称等 fixture | `python3 minecraft-mod-dev/scripts/validate_matrix_fixtures.py` |
| `crawl_docs.py` | 抓取同主机 HTTP(S) HTML，限制重定向、页面数和单响应大小 | `python3 minecraft-mod-dev/scripts/crawl_docs.py --url https://docs.neoforged.net/docs/1.21.1/ --output /tmp/neoforge-docs --max-pages 200 --max-bytes 10485760` |
| `build_doc_index.py` | 从 Markdown/MDX/HTML 建立标题、关键词、哈希索引 | `python3 minecraft-mod-dev/scripts/build_doc_index.py --input /tmp/neoforge-docs/pages --output /tmp/neoforge-doc-index.json` |

文档爬虫只接受 `http`/`https` 起始 URL，只跟随起始站点同主机的 HTML 链接，并拒绝跨主机或非 HTTP(S) 重定向；`--max-bytes` 默认 10 MiB。输出目录包含 `manifest.json` 和 `pages/`，不会修改模组源码。

## 仓库结构

```text
.
├── minecraft-mod-dev/
│   ├── SKILL.md                    # Codex skill 入口与执行契约
│   ├── agents/openai.yaml          # Codex UI 元数据和默认提示词
│   ├── references/
│   │   ├── common/                 # Java、包结构、资源和测试规范
│   │   ├── neoforge/1.21.1.md      # 当前基线速查
│   │   ├── forge/1.20.1.md         # 后续目标速查
│   │   ├── cleanroom/1.12.2.md     # 后续目标速查
│   │   ├── migration/              # 六条有向迁移指南
│   │   ├── compatibility/          # 联动 Mod Schema、矩阵和 metadata
│   │   ├── testing/                # 组合测试和 fixture 合约
│   │   └── baseline-gate.md        # 基线解锁条件
│   └── scripts/                    # 安装后可直接调用的辅助脚本
├── scripts/                        # 校验、打包和仓库 CLI wrapper
├── install.sh / install.ps1        # 源码安装器
├── NOTICE.md                       # 上游归属与适配边界
└── README.md
```

## 开发、验证与发布

提交前运行完整检查：

```bash
python3 scripts/validate.py
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" minecraft-mod-dev
python3 -m py_compile minecraft-mod-dev/scripts/*.py
python3 -B minecraft-mod-dev/scripts/crawl_docs.py --help
python3 -B minecraft-mod-dev/scripts/build_doc_index.py --help
python3 -B minecraft-mod-dev/scripts/validate_loader.py --help
python3 -B minecraft-mod-dev/scripts/validate_structure.py --help
python3 -B minecraft-mod-dev/scripts/validate_compatibility.py --help
python3 -B minecraft-mod-dev/scripts/validate_dependency_graph.py --help
python3 -B minecraft-mod-dev/scripts/generate_compatibility_report.py --help
python3 -B minecraft-mod-dev/scripts/validate_matrix_fixtures.py
python3 minecraft-mod-dev/scripts/validate_compatibility.py \
  minecraft-mod-dev/references/compatibility/compatibility-matrix.example.json --json
python3 scripts/package.py
unzip -t dist/minecraft-mod-dev.zip
git diff --check
```

`scripts/package.py` 会先执行 `scripts/validate.py`，再生成可重复的 `dist/minecraft-mod-dev.zip` 和 `dist/minecraft-mod-dev.zip.sha256`。ZIP 只包含 `minecraft-mod-dev/`，不会把根目录 README、`dist/`、`__pycache__/` 或本机配置打入 skill。

GitHub Actions 会在 push 和 pull request 上运行同一组核心检查。发布前还应确认 ZIP 完整性、SHA-256、公开下载和 CI 结果；提交与发布使用维护者已登录的 GitHub CLI 账号。

## 资料、贡献与许可证

版本知识优先使用固定版本的一手资料：

- [NeoForge 1.21.1 文档](https://docs.neoforged.net/docs/1.21.1/)，审计提交 `816c03d31ff7948179c7bd4a58d23bcfda09c18a`；
- [Forge 1.20.x 文档](https://docs.minecraftforge.net/en/1.20.x/)，源码提交 `87526dd760129b356e88f130550d646d4eb2fa31`；
- [Cleanroom Wiki](https://cleanroommc.com/zh/wiki/end-user-guide/introduction) 及 [官方源码仓库](https://github.com/CleanroomMC)，各快照见 [`official-docs.md`](minecraft-mod-dev/references/official-docs.md)；
- 上游适配来源：[cnlimiter/opencode-neoforge-skill](https://github.com/cnlimiter/opencode-neoforge-skill)。

仓库内参考入口：

- [`official-docs.md`](minecraft-mod-dev/references/official-docs.md)：版本、Java、构建任务和官方页面索引；
- [`java-style.md`](minecraft-mod-dev/references/common/java-style.md)、[`package-structure.md`](minecraft-mod-dev/references/common/package-structure.md)、[`resources-layout.md`](minecraft-mod-dev/references/common/resources-layout.md)：通用代码与项目结构约束；
- [`testing-validation.md`](minecraft-mod-dev/references/common/testing-validation.md)：构建、运行和证据记录检查表；
- [`loader-fixture-contract.md`](minecraft-mod-dev/references/testing/loader-fixture-contract.md)：三种 loader 的识别与结构 fixture 合约。

详细归属、引用和改动边界见 [`NOTICE.md`](NOTICE.md)。贡献前阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)，每条版本事实都要能回溯到对应 loader/Minecraft 版本的官方资料或固定提交。

本项目使用 [MIT License](LICENSE)。
