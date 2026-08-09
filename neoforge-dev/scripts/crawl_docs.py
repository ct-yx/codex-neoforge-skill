#!/usr/bin/env python3
"""Crawl a documentation site into a small, reproducible HTML manifest.

This is intentionally a dependency-free crawler for versioned loader docs. It
only follows links on the starting host and stores metadata plus HTML pages;
it does not attempt to turn a site into a permanent copy of its contents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.links: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "a" and attrs_map.get("href"):
            self.links.append(attrs_map["href"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def normalize_url(url: str) -> str:
    clean, _fragment = urldefrag(url)
    parts = urlsplit(clean)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def same_host(url: str, host: str) -> bool:
    return urlsplit(url).netloc.lower() == host.lower()


def fetch(url: str, timeout: float, user_agent: str, retries: int, backoff: float) -> tuple[bytes | None, str | None, str | None]:
    request = Request(url, headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"})
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get_content_type()
                return response.read(), content_type, None
        except HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if retryable and attempt < retries:
                time.sleep(backoff * (2**attempt))
                continue
            return None, None, f"HTTP {exc.code}: {exc.reason}"
        except URLError as exc:
            if attempt < retries:
                time.sleep(backoff * (2**attempt))
                continue
            return None, None, f"URL error: {exc.reason}"
        except TimeoutError as exc:
            if attempt < retries:
                time.sleep(backoff * (2**attempt))
                continue
            return None, None, f"timeout: {exc}"
    return None, None, "unreachable fetch state"


def iter_links(base_url: str, links: Iterable[str], host: str) -> Iterable[str]:
    for link in links:
        absolute = normalize_url(urljoin(base_url, link))
        parts = urlsplit(absolute)
        if parts.scheme in {"http", "https"} and same_host(absolute, host):
            yield absolute


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="文档站点的起始 URL")
    parser.add_argument("--output", required=True, type=Path, help="输出目录")
    parser.add_argument("--max-pages", type=int, default=100, help="最多抓取页面数（默认 100）")
    parser.add_argument("--max-depth", type=int, default=8, help="最多链接深度（默认 8）")
    parser.add_argument("--delay", type=float, default=0.2, help="请求间隔秒数（默认 0.2）")
    parser.add_argument("--timeout", type=float, default=20.0, help="单次请求超时秒数")
    parser.add_argument("--retries", type=int, default=2, help="429/5xx/网络错误重试次数")
    parser.add_argument("--backoff", type=float, default=1.0, help="重试退避基数秒数")
    parser.add_argument("--user-agent", default="codex-neoforge-skill-doc-crawler/1.0", help="User-Agent")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = normalize_url(args.url)
    host = urlsplit(start).netloc
    if not host:
        raise SystemExit("--url 必须是 http(s) URL")
    if args.max_pages < 1 or args.max_depth < 0:
        raise SystemExit("--max-pages 必须大于 0，--max-depth 不得为负数")

    pages_dir = args.output / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    queue = deque([(start, 0)])
    seen: set[str] = set()
    records: list[dict[str, object]] = []

    while queue and len(records) < args.max_pages:
        url, depth = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        if records:
            time.sleep(max(0.0, args.delay))
        body, content_type, error = fetch(url, args.timeout, args.user_agent, args.retries, args.backoff)
        record: dict[str, object] = {"url": url, "depth": depth}
        if error:
            record["error"] = error
            records.append(record)
            print(f"ERROR {url}: {error}")
            continue
        if body is None:
            record["error"] = "empty response"
            records.append(record)
            continue

        digest = hashlib.sha256(body).hexdigest()
        record.update({"sha256": digest, "bytes": len(body), "content_type": content_type or ""})
        if content_type in {"text/html", "application/xhtml+xml"} or not content_type:
            text = body.decode("utf-8", errors="replace")
            parser = LinkParser()
            parser.feed(text)
            record.update({"title": parser.title, "links": len(parser.links)})
            filename = f"{hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]}.html"
            (pages_dir / filename).write_text(text, encoding="utf-8")
            record["file"] = f"pages/{filename}"
            if depth < args.max_depth:
                for next_url in iter_links(url, parser.links, host):
                    if next_url not in seen:
                        queue.append((next_url, depth + 1))
        else:
            record["skipped"] = "non-HTML content"
        records.append(record)
        print(f"OK {url}")

    manifest = {
        "start_url": start,
        "host": host,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "max_pages": args.max_pages,
        "pages": records,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {len(records)} 条记录：{args.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
