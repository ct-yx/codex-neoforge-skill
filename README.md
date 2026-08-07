# Codex NeoForge Skill

[![Validate](https://github.com/ct-yx/codex-neoforge-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/ct-yx/codex-neoforge-skill/actions/workflows/validate.yml)
[![Latest release](https://img.shields.io/github/v/release/ct-yx/codex-neoforge-skill)](https://github.com/ct-yx/codex-neoforge-skill/releases/latest)

面向 Codex 的 NeoForge 模组开发 skill，覆盖项目识别、功能开发、构建调试、Forge 迁移、版本专属 API 核对和交付验证。

## 特点

- 原生 Codex `SKILL.md` 与 `agents/openai.yaml` 结构
- 自动读取项目 `AGENTS.md` 和 Gradle 配置，不绑定固定工作目录
- 从项目文件识别 Minecraft、NeoForge、Java 与 mappings 版本
- 覆盖注册、事件、网络、菜单、资源、数据生成、世界生成和 Mixin
- 包含编译、构建、数据生成、测试及运行日志验证流程
- 不强制依赖额外 MCP；有可用工具时才使用
- 默认参考 Minecraft 1.21.1、NeoForge 21.1.x、Java 21，但始终以项目配置为准

## 安装

### 从 Release 安装

macOS/Linux：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
curl -fL https://github.com/ct-yx/codex-neoforge-skill/releases/latest/download/neoforge-dev.zip -o /tmp/neoforge-dev.zip
unzip /tmp/neoforge-dev.zip -d "${CODEX_HOME:-$HOME/.codex}/skills"
```

### 从源码安装

```bash
git clone https://github.com/ct-yx/codex-neoforge-skill.git
cd codex-neoforge-skill
./install.sh
```

覆盖已有安装并保留时间戳备份：

```bash
./install.sh --force
```

Windows PowerShell：

```powershell
git clone https://github.com/ct-yx/codex-neoforge-skill.git
Set-Location codex-neoforge-skill
.\install.ps1
```

安装后从下一个 Codex 回合开始可用。

## 使用

显式调用：

```text
使用 $neoforge-dev 检查当前项目并完成这个 NeoForge 模组开发任务。
```

涉及 NeoForge 模组开发、构建、迁移、数据生成或崩溃排查时也可自动触发。

## 仓库结构

```text
.
├── neoforge-dev/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── scripts/
│   ├── package.py
│   └── validate.py
├── install.sh
├── install.ps1
└── README.md
```

## 验证与打包

```bash
python3 scripts/validate.py
python3 scripts/package.py
```

打包产物位于 `dist/neoforge-dev.zip`，ZIP 内保留顶层 `neoforge-dev/` 目录，可直接解压到 Codex skills 目录。

## 来源与适配

本项目基于 [cnlimiter/opencode-neoforge-skill](https://github.com/cnlimiter/opencode-neoforge-skill) 的入口 skill 思路进行 Codex 适配。上游快照未包含其 README 所列出的示例和依赖子 skill，因此本项目将入口改写为可独立执行的工作流，并移除了 OpenCode 专属权限、缺失子 skill 调度及硬编码 Windows 路径。详细来源信息见 [NOTICE.md](NOTICE.md)。

## License

[MIT](LICENSE)
