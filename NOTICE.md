# 来源与归属声明

## 上游适配

本项目的入口 skill 思路改编自：

- 仓库：[cnlimiter/opencode-neoforge-skill](https://github.com/cnlimiter/opencode-neoforge-skill)
- 审阅快照：`6b1b55cefaa0be602ad1f96b678d9a4cd26eb67c`
- 快照作者：Xin Luo

审阅到的上游快照主要包含 `neoforge-dev/SKILL.md` 和 README 文件，未包含 README 所描述的示例/依赖子 skill，也未发现随快照提供的 `LICENSE` 文件。当前仓库的 Codex 改写、知识库、脚本、安装器和打包代码由本仓库维护，并按根目录 [MIT License](LICENSE) 发布。

## 适配范围

本仓库对上游入口做了以下工程化改写：

- 移除 OpenCode 专属权限、缺失的子 skill 调度、强制 MCP 和硬编码 Windows 路径；
- 改为原生 Codex `SKILL.md`、`agents/openai.yaml` 和可独立执行的工作流；
- 增加 NeoForge 1.21.1 基线门控、Java/项目结构契约和版本识别；
- 增加 Forge 1.20.1、Cleanroom 1.12.2 的官方资料索引与迁移参考；
- 增加文档抓取/索引、loader/结构校验、安装和确定性打包流程。

## 官方资料引用

版本知识库引用的 NeoForge、Forge 和 CleanroomMC 官方资料及固定提交，统一记录在 [`neoforge-dev/references/official-docs.md`](neoforge-dev/references/official-docs.md)。这些链接用于版本事实核对，不表示本项目隶属于任何 loader 项目或 Minecraft 项目。
