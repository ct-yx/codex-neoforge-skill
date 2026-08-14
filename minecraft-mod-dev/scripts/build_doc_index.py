#!/usr/bin/env python3
"""Build a compact heading/keyword index for Markdown, MDX and HTML docs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_KEYWORDS = (
    "neoforge",
    "forge",
    "cleanroom",
    "minecraft",
    "java",
    "gradle",
    "registry",
    "event",
    "network",
    "datagen",
    "mixin",
    "access transformer",
)


class HeadingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.headings: list[dict[str, object]] = []
        self._tag = ""
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "title" or re.fullmatch(r"h[1-6]", tag):
            self._tag = tag
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._tag:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag != self._tag:
            return
        text = " ".join("".join(self._parts).split())
        if tag == "title":
            self.title = text
        elif text:
            self.headings.append({"level": int(tag[1]), "text": text})
        self._tag = ""
        self._parts = []


def markdown_headings(text: str) -> tuple[str, list[dict[str, object]]]:
    headings: list[dict[str, object]] = []
    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match:
            headings.append({"level": len(match.group(1)), "text": match.group(2).strip()})
    title = next((str(item["text"]) for item in headings if item["level"] == 1), "")
    return title, headings


def parse_document(path: Path) -> tuple[str, list[dict[str, object]], str]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        parser = HeadingParser()
        parser.feed(text)
        return parser.title or (parser.headings[0]["text"] if parser.headings else ""), parser.headings, text
    title, headings = markdown_headings(text)
    return title, headings, text


def collect_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    extensions = {".md", ".mdx", ".html", ".htm"}
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in extensions and ".git" not in path.parts)


def keyword_counts(text: str, keywords: list[str]) -> dict[str, int]:
    lowered = text.casefold()
    return {keyword: len(re.findall(re.escape(keyword.casefold()), lowered)) for keyword in keywords}


def render_markdown(index: dict[str, object]) -> str:
    lines = ["# 文档索引", "", f"文件数：{index['file_count']}", "", "| 文件 | 标题 | 章节 | 关键词命中 |", "| --- | --- | ---: | --- |"]
    for item in index["documents"]:  # type: ignore[index]
        counts = item["keywords"]  # type: ignore[index]
        hits = ", ".join(f"{key}={value}" for key, value in counts.items() if value)
        relative = str(item["path"]).replace("|", "\\|")  # type: ignore[index]
        title = str(item["title"]).replace("|", "\\|")  # type: ignore[index]
        lines.append(f"| `{relative}` | {title or '-'} | {len(item['headings'])} | {hits or '-'} |")  # type: ignore[index]
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Markdown/HTML 文件或目录")
    parser.add_argument("--output", required=True, type=Path, help="索引输出文件")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--keywords", default=", ".join(DEFAULT_KEYWORDS), help="逗号分隔的关键词")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"输入不存在：{args.input}")
    keywords = [item.strip() for item in args.keywords.split(",") if item.strip()]
    documents: list[dict[str, object]] = []
    for path in collect_files(args.input):
        title, headings, text = parse_document(path)
        documents.append(
            {
                "path": str(path.relative_to(args.input.parent if args.input.is_file() else args.input)),
                "title": title,
                "headings": headings,
                "keywords": keyword_counts(text, keywords),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "bytes": len(text.encode("utf-8")),
            }
        )
    index = {"input": str(args.input), "file_count": len(documents), "keywords": keywords, "documents": documents}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        content = json.dumps(index, ensure_ascii=False, indent=2) + "\n"
    else:
        content = render_markdown(index)
    args.output.write_text(content, encoding="utf-8")
    print(f"已索引 {len(documents)} 个文件：{args.output}")


if __name__ == "__main__":
    main()
