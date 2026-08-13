# 贡献指南

感谢参与维护 Codex Minecraft Mod Skill。这个仓库维护的是 Codex skill 和版本知识库，不是 Minecraft 模组本体。

## 修改原则

1. 默认基线始终是 NeoForge 1.21.1 / Java 21。
2. Forge 1.20.1 和 Cleanroom 1.12.2 内容只能作为后续迁移参考；不要把它们的 API 示例混入 NeoForge 基线章节。
3. 每条版本事实都应附带官方文档、官方仓库或固定提交；不要用未标版本的博客替代主来源。
4. 优先修改 `neoforge-dev/SKILL.md` 和对应 `references/` 文件；不要把完整外站原文复制进仓库。
5. 辅助脚本只使用 Python 标准库，保持可在干净 Python 环境运行。
6. 迁移或联动 Mod 变更必须更新对应有向路径和 `compatibility-matrix` 证据；不能只修改 API 差异表。

## 本地检查

```bash
python3 scripts/validate.py
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" neoforge-dev
python3 -B neoforge-dev/scripts/crawl_docs.py --help >/dev/null
python3 -B neoforge-dev/scripts/build_doc_index.py --help >/dev/null
python3 -B neoforge-dev/scripts/validate_loader.py --help >/dev/null
python3 -B neoforge-dev/scripts/validate_structure.py --help >/dev/null
python3 -B neoforge-dev/scripts/validate_compatibility.py --help >/dev/null
python3 scripts/package.py
unzip -t dist/neoforge-dev.zip
git diff --check
```

如果修改了脚本，请至少用临时 fixture 验证 NeoForge、Forge、Cleanroom 三种项目识别和结构检查；不要修改真实模组项目作为测试副作用。
如果修改了兼容矩阵逻辑，请至少验证目标 Mod 存在、缺失、错误版本和 `verified` 证据不足四种情况。

## 提交和发布

- 提交信息使用清晰的动词，例如 `Expand loader references`。
- 只提交本次任务相关文件；不要提交 `dist/`、`__pycache__/` 或本机配置。
- 发布前确认 ZIP 可重复构建、SHA-256、`unzip -t`、公开下载和 GitHub Actions。
- 使用维护者已登录的 GitHub CLI 账号发布；Release 资产至少包含 ZIP 和 `.sha256` 文件。

## Pull Request 内容

请说明：

- 修改涉及的 loader/Minecraft/Java 版本；
- 使用的官方来源和提交；
- 本地运行的命令与结果；
- 尚未完成的客户端、专用服务器或网络验证。
