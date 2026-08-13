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


DEFAULT_MAX_BYTES = 10 * 1024 * 1024
READ_CHUNK_SIZE = 64 * 1024


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
    """Compare the URL authority with the authority captured at startup.

    The crawler deliberately keeps the comparison strict (including an
    explicitly supplied port).  A redirect to a different port is a
    different origin even when the hostname is the same.
    """

    try:
        return urlsplit(url).netloc.casefold() == host.casefold()
    except ValueError:
        return False


def validate_final_url(final_url: str, host: str) -> str | None:
    """Return a diagnostic when a response URL is outside the crawl origin."""

    try:
        parts = urlsplit(final_url)
    except ValueError as exc:
        return f"invalid final URL: {exc}"
    if parts.scheme.lower() not in {"http", "https"}:
        return f"redirected to unsupported scheme: {parts.scheme or 'missing'}"
    if parts.username or parts.password:
        return "redirected URL contains credentials"
    if not parts.netloc or not same_host(final_url, host):
        return f"cross-host redirect rejected: {final_url}"
    return None


def fetch(
    url: str,
    host: str,
    timeout: float,
    user_agent: str,
    retries: int,
    backoff: float,
    max_bytes: int,
) -> tuple[bytes | None, str | None, int | None, str | None, str | None]:
    """Fetch one page without following an untrusted redirect target.

    ``urllib`` follows redirects internally, so the final URL is checked
    before reading any response bytes.  The body is read in bounded chunks;
    this protects both memory and the output page files when Content-Length
    is absent or dishonest.
    """

    request = Request(url, headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"})
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                final_url = response.geturl()
                final_error = validate_final_url(final_url, host)
                if final_error:
                    return None, None, None, final_url, final_error

                content_type = response.headers.get_content_type()
                declared_raw = response.headers.get("Content-Length")
                declared_length: int | None = None
                if declared_raw is not None:
                    try:
                        declared_length = int(declared_raw.strip())
                    except ValueError:
                        return None, content_type, None, final_url, "invalid Content-Length header"
                    if declared_length < 0:
                        return None, content_type, declared_length, final_url, "negative Content-Length header"
                    if declared_length > max_bytes:
                        return None, content_type, declared_length, final_url, (
                            f"response exceeds --max-bytes ({declared_length} > {max_bytes})"
                        )

                body = bytearray()
                while True:
                    chunk = response.read(min(READ_CHUNK_SIZE, max_bytes + 1 - len(body)))
                    if not chunk:
                        break
                    body.extend(chunk)
                    if len(body) > max_bytes:
                        return None, content_type, declared_length, final_url, (
                            f"response exceeds --max-bytes ({len(body)} > {max_bytes})"
                        )
                if declared_length is not None and declared_length != len(body):
                    return None, content_type, declared_length, final_url, (
                        f"Content-Length mismatch ({declared_length} != {len(body)})"
                    )
                return bytes(body), content_type, declared_length, final_url, None
        except HTTPError as exc:
            error_url = getattr(exc, "url", None)
            if error_url:
                redirect_error = validate_final_url(error_url, host)
                if redirect_error:
                    return None, None, None, error_url, redirect_error
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if retryable and attempt < retries:
                time.sleep(backoff * (2**attempt))
                continue
            return None, None, None, getattr(exc, "url", None), f"HTTP {exc.code}: {exc.reason}"
        except URLError as exc:
            if attempt < retries:
                time.sleep(backoff * (2**attempt))
                continue
            return None, None, None, None, f"URL error: {exc.reason}"
        except TimeoutError as exc:
            if attempt < retries:
                time.sleep(backoff * (2**attempt))
                continue
            return None, None, None, None, f"timeout: {exc}"
    return None, None, None, None, "unreachable fetch state"


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
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help=f"单个响应最多读取字节数（默认 {DEFAULT_MAX_BYTES}）",
    )
    parser.add_argument("--user-agent", default="codex-neoforge-skill-doc-crawler/1.0", help="User-Agent")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        start = normalize_url(args.url)
        start_parts = urlsplit(start)
    except ValueError as exc:
        raise SystemExit(f"--url 不是有效 URL：{exc}") from exc
    if start_parts.scheme not in {"http", "https"} or not start_parts.netloc or not start_parts.hostname:
        raise SystemExit("--url 必须是 http(s) URL")
    if start_parts.username or start_parts.password:
        raise SystemExit("--url 不得包含用户名或密码")
    host = start_parts.netloc
    if args.max_pages < 1 or args.max_depth < 0 or args.max_bytes < 1:
        raise SystemExit("--max-pages 必须大于 0、--max-depth 不得为负数、--max-bytes 必须大于 0")

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
        body, content_type, declared_length, final_url, error = fetch(
            url,
            host,
            args.timeout,
            args.user_agent,
            args.retries,
            args.backoff,
            args.max_bytes,
        )
        record: dict[str, object] = {"url": url, "depth": depth}
        if final_url:
            try:
                record["final_url"] = normalize_url(final_url)
            except ValueError:
                record["final_url"] = final_url
        if content_type is not None:
            record["content_type"] = content_type
        if declared_length is not None:
            record["content_length"] = declared_length
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
            resolved_url = final_url or url
            filename = f"{hashlib.sha256(resolved_url.encode('utf-8')).hexdigest()[:16]}.html"
            (pages_dir / filename).write_text(text, encoding="utf-8")
            record["file"] = f"pages/{filename}"
            if depth < args.max_depth:
                for next_url in iter_links(resolved_url, parser.links, host):
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
    manifest["max_bytes"] = args.max_bytes
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {len(records)} 条记录：{args.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
