"""Pexels API — route stock (P5: 3 tier, tier sau khi tier trước nghèo; 4.1 cache;
4.5 lọc landscape; 4.7 verify sau tải)."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol

import requests

from autoedit.project import SearchQueries, ffprobe_duration

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
MIN_CANDIDATES_PER_TIER = 5   # 4.2: tier sau chỉ chạy khi tier trước < ngưỡng này
PER_PAGE = 10
MAX_DOWNLOAD_SEC = 75   # trần WALL-CLOCK 1 lần tải — chặn stream "nhỏ giọt" treo vô hạn
                        # (timeout=(connect,read) per-read KHÔNG bắt được khi server trickle
                        # vài byte < read-timeout; bug thật 20/06: source kẹt 15' trên 1 beat)


class _StreamStalled(Exception):
    """Stream vượt trần wall-clock -> bỏ URL, thử ứng viên kế (KHÔNG retry cùng URL)."""


def collect_pexels_keys(env: Optional[dict] = None) -> list[str]:
    """Gom MỌI key Pexels từ .env (nhiều key = nhân hạn mức 200 query/giờ/key).

    Nhận:
    - PEXELS_API_KEY: 1 key, HOẶC nhiều key ngăn bằng dấu phẩy/khoảng trắng/xuống dòng
    - PEXELS_API_KEYS: như trên (tên số nhiều, tuỳ chọn)
    - PEXELS_API_KEY_2, _3, ... _10: mỗi biến 1 key (cách thêm dễ nhất)
    Trả list đã khử trùng lặp, giữ thứ tự.
    """
    env = env if env is not None else os.environ
    raw: list[str] = []
    for name in ("PEXELS_API_KEY", "PEXELS_API_KEYS"):
        raw += re.split(r"[,\s]+", env.get(name, ""))
    for i in range(2, 11):
        raw += re.split(r"[,\s]+", env.get(f"PEXELS_API_KEY_{i}", ""))
    seen: set[str] = set()
    out: list[str] = []
    for k in raw:
        k = k.strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


class StockClient(Protocol):
    """Interface tách rời để test bằng fake."""

    def search_tiered(self, queries: SearchQueries) -> list[dict]: ...
    def download(self, candidate: dict, dest: Path) -> Path: ...


class PexelsClient:
    SOURCE_NAME = "pexels"   # MultiStockClient định tuyến download theo tên này

    def __init__(
        self,
        api_key: "str | list[str]",
        conn: Optional[sqlite3.Connection] = None,
    ) -> None:
        # Chấp nhận 1 key (str) hoặc nhiều key (list) — nhiều key nhân hạn mức.
        self.keys: list[str] = [api_key] if isinstance(api_key, str) else list(api_key)
        self.conn = conn  # cache search (4.1); None = không cache (test)
        self.key_idx = 0                  # key đang dùng
        self.exhausted: set[int] = set()  # index các key đã dính 429 trong run này
        # rate_limited = MỌI key đều hết hạn mức -> NGỪNG gọi mạng phần còn lại run,
        # trả rỗng ngay, beat thành needs_human. Video dài không bị giết cả stage.
        self.rate_limited = False

    @property
    def api_key(self) -> str:
        """Key hiện hành (giữ thuộc tính cũ cho tương thích)."""
        return self.keys[self.key_idx] if self.keys else ""

    # ------------------------- search ---------------------------------------
    def search_tiered(self, queries: SearchQueries) -> list[dict]:
        """Gom ứng viên theo 3 tier; dừng sớm khi đủ MIN_CANDIDATES_PER_TIER."""
        candidates: list[dict] = []
        seen: set[str] = set()
        for tier in (queries.specific, queries.broad, queries.thematic):
            for q in tier:
                for c in self._search_one(q):
                    if c["asset_key"] not in seen:
                        seen.add(c["asset_key"])
                        candidates.append(c)
            if len(candidates) >= MIN_CANDIDATES_PER_TIER:
                break  # tier này đủ giàu — không nới thêm
        return candidates

    def _search_one(self, query: str) -> list[dict]:
        data = self._cached_get(query)
        results = []
        for v in data.get("videos", []):
            best = _pick_video_file(v)
            if best is None:
                continue  # không có bản landscape HD nào (4.5)
            results.append(
                {
                    "asset_key": f"pexels:{v['id']}",
                    "url": best["link"],
                    "media_type": "video",
                    "duration": float(v.get("duration", 0)),
                    "width": best["width"],
                    "height": best["height"],
                    "description": v.get("url", ""),
                    "source": "pexels",
                }
            )
        return results

    def _cached_get(self, query: str) -> dict:
        if self.conn is not None:
            row = self.conn.execute(
                "SELECT response FROM search_cache WHERE provider='pexels' AND query=?",
                (query,),
            ).fetchone()
            if row:
                return json.loads(row["response"])
        if self.rate_limited:
            return {}  # đã rate-limit trong run này -> bỏ qua mạng, không cache
        data = self._http_get(query)
        if data is None:  # rate-limit kéo dài -> đánh dấu, trả rỗng, KHÔNG cache (chạy sau retry)
            self.rate_limited = True
            return {}
        if self.conn is not None:
            self.conn.execute(
                # G2: INSERT OR REPLACE là phương ngữ SQLite — ON CONFLICT chạy cả 2 lưng
                "INSERT INTO search_cache (provider, query, response, cached_at) "
                "VALUES ('pexels', ?, ?, ?) ON CONFLICT(provider, query) DO UPDATE SET "
                "response=excluded.response, cached_at=excluded.cached_at",
                (query, json.dumps(data), datetime.now(timezone.utc).isoformat()),
            )
            self.conn.commit()
        return data

    def _http_get(self, query: str) -> Optional[dict]:
        """Trả dict kết quả, hoặc None nếu MỌI key đều hết hạn mức (caller xử lý mềm).

        429 trên key hiện tại -> đánh dấu key đó cạn, XOAY sang key kế (không chờ).
        Chỉ trả None khi tất cả key đã cạn. 5xx (lỗi server tạm) -> backoff + thử lại
        cùng key (không tính là cạn key).
        """
        while len(self.exhausted) < len(self.keys):
            if self.key_idx in self.exhausted:               # key hiện tại đã cạn -> nhảy
                self.key_idx = self._next_active_key()
                continue
            key = self.keys[self.key_idx]
            got_429 = False
            for attempt in range(3):  # 5xx: backoff 1+2+4s; 429: cạn ngay, xoay key
                resp = requests.get(
                    PEXELS_VIDEO_URL,
                    headers={"Authorization": key},
                    params={"query": query, "per_page": PER_PAGE, "orientation": "landscape"},
                    timeout=30,
                )
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 429:                  # hết hạn mức key này
                    got_429 = True
                    break
                if resp.status_code in (500, 502, 503):      # lỗi server tạm -> chờ rồi thử lại
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
            if got_429:
                self.exhausted.add(self.key_idx)             # cạn key -> xoay sang key kế
                self.key_idx = self._next_active_key()
                continue
            return None  # key này 5xx kéo dài (không cạn) -> coi như không có kết quả
        return None      # MỌI key đã cạn

    def _next_active_key(self) -> int:
        """Index key chưa cạn kế tiếp (vòng tròn); nếu hết thì trả index hiện tại."""
        for step in range(1, len(self.keys) + 1):
            idx = (self.key_idx + step) % len(self.keys)
            if idx not in self.exhausted:
                return idx
        return self.key_idx

    # ------------------------- download -------------------------------------
    def download(self, candidate: dict, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(3):  # 4.7: retry + verify
            try:
                start = time.monotonic()
                with requests.get(candidate["url"], stream=True, timeout=(10, 30)) as r:
                    r.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1 << 16):
                            if time.monotonic() - start > MAX_DOWNLOAD_SEC:
                                raise _StreamStalled  # nhỏ giọt -> bỏ URL ngay, thử cái khác
                            f.write(chunk)
                if ffprobe_duration(dest) is not None:
                    return dest
            except _StreamStalled:
                dest.unlink(missing_ok=True)
                raise RuntimeError(
                    f"Tải treo >{MAX_DOWNLOAD_SEC}s (stream nhỏ giọt) — bỏ URL: {candidate['url']}"
                )
            except (requests.RequestException, OSError):
                pass  # lỗi mạng tạm -> backoff rồi thử lại CÙNG url
            dest.unlink(missing_ok=True)
            time.sleep(2 ** attempt)
        raise RuntimeError(f"Tải hỏng sau 3 lần: {candidate['url']}")


def _pick_video_file(video: dict) -> Optional[dict]:
    """Chọn bản file tốt nhất: landscape, ưu tiên ~1080p (đủ nét, nhẹ hơn 4K)."""
    files = [
        f for f in video.get("video_files", [])
        if f.get("width") and f.get("height") and f["width"] > f["height"]
    ]
    if not files:
        return None
    return min(files, key=lambda f: abs(f["height"] - 1080))
