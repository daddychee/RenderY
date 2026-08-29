"""Route entity — ảnh THẬT của thực thể (P1: ưu tiên 1, không phải fallback).

Provider chính: Serper.dev (Google Images qua API — Google đã ĐÓNG Custom Search
JSON API với khách mới 2026, xem CLAUDE.md). GoogleCSEClient giữ lại cho tài
khoản cũ còn quyền (chết hạn 1/1/2027).

- Thiếu key -> beat đánh dấu needs_human (P8), pipeline không chết.
- Cấm tuyệt đối domain hãng ảnh có watermark (rủi ro pháp lý thật — PRD Stage 4).
- Mọi ảnh entity gắn cờ ⚠ licensing — editor quyết cuối.
- Cache theo thực thể: library/<niche>/entity/<slug>/ — video sau tái dùng miễn phí.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional, Protocol

import requests

from autoedit.project import slugify

CSE_URL = "https://www.googleapis.com/customsearch/v1"

# Hãng ảnh bản quyền có watermark — cấm tuyệt đối (PRD Stage 4 route entity)
BANNED_DOMAINS = (
    "gettyimages", "shutterstock", "istockphoto", "alamy", "dreamstime",
    "afp.com", "apimages", "stock.adobe", "depositphotos", "123rf",
)
PREFERRED_DOMAINS = ("reuters.com", "apnews.com", ".gov", "wikipedia.org", "wikimedia.org")

# Lớp 2 (2026-07-03): sàn phân giải ảnh entity. Timeline 1080p; ảnh hẹp hơn ngưỡng này
# phóng lên là MỜ (đo thật: 250px → ×5.7 nát). Coi ảnh dưới sàn = "hỏng kỹ thuật" (cùng
# họ với watermark/quá-ngắn), BỎ và thử ảnh nét hơn — KHÔNG phải veto nghĩa thứ 3.
MIN_IMAGE_WIDTH = 1280


class EntityClient(Protocol):
    def search_images(self, query: str, n: int = 5) -> list[dict]: ...
    def download(self, candidate: dict, dest: Path) -> Path: ...


def image_width(path: Path) -> int:
    """Chiều rộng ảnh (px) đã tải; 0 nếu không đo được → caller FAIL-OPEN (không loại oan)."""
    try:
        from PIL import Image

        with Image.open(path) as im:
            return int(im.size[0])
    except Exception:
        return 0


def filter_and_rank_images(raw: list[dict], n: int, min_width: int = MIN_IMAGE_WIDTH) -> list[dict]:
    """Lọc blocklist watermark + SÀN PHÂN GIẢI (metadata) + xếp domain báo chí/.gov/wiki
    lên đầu, cùng hạng thì ảnh TO hơn (nét hơn) trước. raw: {url, origin, description, width?}.
    """
    results = []
    for item in raw:
        link, origin = item["url"], item["origin"]
        if any(b in link.lower() or b in origin.lower() for b in BANNED_DOMAINS):
            continue  # watermark/bản quyền hãng ảnh — loại tuyệt đối
        w = item.get("width") or 0
        if w and w < min_width:
            continue  # Google báo sẵn kích thước → loại ảnh nhỏ TRƯỚC khi tải (rẻ)
        results.append(
            item
            | {
                "asset_key": f"entity:{hashlib.sha1(link.encode()).hexdigest()[:16]}",
                "media_type": "image",
                "preferred": any(p in origin.lower() for p in PREFERRED_DOMAINS),
                "source": "entity",
            }
        )
    return sorted(results, key=lambda r: (not r["preferred"], -(r.get("width") or 0)))[:n]


def looks_like_image(path: Path) -> bool:
    """True nếu file có magic bytes của ẢNH THẬT. Chặn trang HTML lưu nhầm .jpg
    (URL trả 200 + body HTML lỗi/chặn nặng vài trăm KB → lọt cửa lọc 'file >10KB',
    ffmpeg sau đó chết '-22 Invalid argument' → beat thành gap). Bug thật 19/06."""
    try:
        with open(path, "rb") as f:
            head = f.read(12)
    except OSError:
        return False
    return (
        head[:3] == b"\xff\xd8\xff"                       # JPEG
        or head[:8] == b"\x89PNG\r\n\x1a\n"               # PNG
        or head[:4] == b"GIF8"                            # GIF
        or (head[:4] == b"RIFF" and head[8:12] == b"WEBP")  # WEBP
        or head[:2] == b"BM"                              # BMP
    )


def _download_image(url: str, dest: Path) -> Path:
    """Tải ảnh + retry; chặn trang lỗi giả dạng ảnh (file quá nhỏ HOẶC không phải ảnh)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            start = time.monotonic()
            with requests.get(
                url, stream=True, timeout=(10, 30),
                headers={"User-Agent": "Mozilla/5.0 (AutoEdit fetch)"},
            ) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 16):
                        if time.monotonic() - start > 45:  # trần wall-clock chống nhỏ giọt treo
                            dest.unlink(missing_ok=True)
                            raise RuntimeError(f"Tải ảnh treo >45s (nhỏ giọt) — bỏ URL: {url}")
                        f.write(chunk)
            if dest.stat().st_size > 10_000:
                if not looks_like_image(dest):
                    # body không phải ảnh (HTML/khác) — retry cùng URL vô ích, BÁO ngay
                    # để caller thử ẢNH KHÁC
                    dest.unlink(missing_ok=True)
                    raise RuntimeError(f"Nội dung tải về KHÔNG phải ảnh (HTML?): {url}")
                # Lớp 2 backstop: metadata có thể thiếu/sai — đo pixel thật, ảnh mờ thì
                # BÁO để caller thử ảnh khác (0 = không đo được → fail-open, giữ lại).
                w = image_width(dest)
                if w and w < MIN_IMAGE_WIDTH:
                    dest.unlink(missing_ok=True)
                    raise RuntimeError(
                        f"Ảnh phân giải thấp {w}px < {MIN_IMAGE_WIDTH}px (mờ khi phóng 1080p) — bỏ: {url}"
                    )
                return dest
        except requests.RequestException:
            pass
        dest.unlink(missing_ok=True)
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Tải ảnh hỏng sau 3 lần: {url}")


class SerperEntityClient:
    """Provider chính: Serper.dev — Google Images thật, 2.500 query free."""

    SERPER_URL = "https://google.serper.dev/images"

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        from dotenv import load_dotenv

        load_dotenv()
        self.key = os.environ.get("SERPER_API_KEY", "")
        if not self.key:
            raise RuntimeError(
                "Thiếu SERPER_API_KEY trong .env — route entity cần Serper.dev "
                "(serper.dev, 2.500 query free)."
            )
        self.conn = conn

    def search_images(self, query: str, n: int = 5) -> list[dict]:
        import json
        from datetime import datetime, timezone

        data = None
        if self.conn is not None:
            row = self.conn.execute(
                "SELECT response FROM search_cache WHERE provider='serper' AND query=?",
                (query,),
            ).fetchone()
            data = json.loads(row["response"]) if row else None
        if data is None:
            resp = requests.post(
                self.SERPER_URL,
                headers={"X-API-KEY": self.key, "Content-Type": "application/json"},
                json={"q": query, "num": 10},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if self.conn is not None:
                self.conn.execute(
                    # G2: ON CONFLICT thay INSERT OR REPLACE — chạy cả 2 lưng
                    "INSERT INTO search_cache (provider, query, response, cached_at) "
                    "VALUES ('serper', ?, ?, ?) ON CONFLICT(provider, query) DO UPDATE SET "
                    "response=excluded.response, cached_at=excluded.cached_at",
                    (query, json.dumps(data), datetime.now(timezone.utc).isoformat()),
                )
                self.conn.commit()

        raw = [
            {
                "url": im.get("imageUrl", ""),
                "origin": im.get("domain", ""),
                "description": im.get("title", ""),
                "width": im.get("imageWidth") or 0,   # Serper báo sẵn → lọc sàn phân giải
            }
            for im in data.get("images", [])
            if im.get("imageUrl")
        ]
        return filter_and_rank_images(raw, n)

    def download(self, candidate: dict, dest: Path) -> Path:
        return _download_image(candidate["url"], dest)


class GoogleCSEClient:
    """Client thật. Khởi tạo lỗi nếu thiếu key — caller bắt và rơi về needs_human."""

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        from dotenv import load_dotenv

        load_dotenv()
        self.key = os.environ.get("GOOGLE_CSE_KEY", "")
        self.cx = os.environ.get("GOOGLE_CSE_CX", "")
        if not self.key or not self.cx:
            raise RuntimeError(
                "Thiếu GOOGLE_CSE_KEY/GOOGLE_CSE_CX trong .env — route entity cần "
                "Google Custom Search (free 100 query/ngày, xem hướng dẫn M5)."
            )
        self.conn = conn

    def search_images(self, query: str, n: int = 5) -> list[dict]:
        import json
        from datetime import datetime, timezone

        cached = None
        if self.conn is not None:
            row = self.conn.execute(
                "SELECT response FROM search_cache WHERE provider='cse' AND query=?",
                (query,),
            ).fetchone()
            cached = json.loads(row["response"]) if row else None
        if cached is None:
            resp = requests.get(
                CSE_URL,
                params={
                    "key": self.key, "cx": self.cx, "q": query,
                    "searchType": "image", "imgSize": "xlarge", "safe": "active",
                    "num": 10,
                },
                timeout=30,
            )
            resp.raise_for_status()
            cached = resp.json()
            if self.conn is not None:
                self.conn.execute(
                    # G2: ON CONFLICT thay INSERT OR REPLACE — chạy cả 2 lưng
                    "INSERT INTO search_cache (provider, query, response, cached_at) "
                    "VALUES ('cse', ?, ?, ?) ON CONFLICT(provider, query) DO UPDATE SET "
                    "response=excluded.response, cached_at=excluded.cached_at",
                    (query, json.dumps(cached), datetime.now(timezone.utc).isoformat()),
                )
                self.conn.commit()

        raw = [
            {
                "url": item.get("link", ""),
                "origin": item.get("displayLink", ""),
                "description": item.get("title", ""),
                "width": (item.get("image") or {}).get("width") or 0,
            }
            for item in cached.get("items", [])
            if item.get("link")
        ]
        return filter_and_rank_images(raw, n)

    def download(self, candidate: dict, dest: Path) -> Path:
        return _download_image(candidate["url"], dest)


def entity_cache_dir(niche: str, entity_query: str, library_root: Path) -> Path:
    return library_root / niche / "entity" / slugify(entity_query)
