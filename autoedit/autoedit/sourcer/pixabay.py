"""Pixabay API — nguồn stock free thứ hai, chạy sau Pexels khi Pexels nghèo ứng viên.

Cùng interface StockClient với PexelsClient (search_tiered + download) nên cắm thẳng
vào runner qua MultiStockClient. Tải dùng lại `PexelsClient.download` — logic retry +
chống stream nhỏ giọt + verify ffprobe giống hệt, không viết lại.

Pixabay free cho dùng thương mại (Content License), không cần ghi công — nhưng
`asset_key` vẫn ghi `pixabay:<id>` để truy ngược nguồn gốc từng clip trong draft.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from autoedit.project import SearchQueries
from autoedit.sourcer.pexels import MIN_CANDIDATES_PER_TIER, PexelsClient

PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"
PER_PAGE = 10  # API bắt buộc trong [3, 200]


def _pick_video_file(hit: dict) -> Optional[dict]:
    """Chọn bản landscape gần 1080p nhất (đủ nét, nhẹ hơn 4K) — như Pexels."""
    files = [
        v for v in (hit.get("videos") or {}).values()
        if isinstance(v, dict) and v.get("url") and v.get("width") and v.get("height")
        and v["width"] > v["height"]
    ]
    if not files:
        return None
    return min(files, key=lambda v: abs(v["height"] - 1080))


class PixabayClient(PexelsClient):
    """Kế thừa PexelsClient để dùng lại download() + xoay key + cờ rate_limited."""

    SOURCE_NAME = "pixabay"

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
                break
        return candidates

    def _search_one(self, query: str) -> list[dict]:
        results = []
        for hit in self._cached_get(query).get("hits", []):
            best = _pick_video_file(hit)
            if best is None:
                continue  # không có bản landscape nào
            results.append({
                "asset_key": f"pixabay:{hit['id']}",
                "url": best["url"],
                "media_type": "video",
                "duration": float(hit.get("duration", 0)),
                "width": best["width"],
                "height": best["height"],
                "description": hit.get("pageURL", ""),
                "source": "pixabay",
            })
        return results

    def _cached_get(self, query: str) -> dict:
        """Cache search dùng chung bảng với Pexels, phân biệt bằng cột provider."""
        if self.conn is not None:
            row = self.conn.execute(
                "SELECT response FROM search_cache WHERE provider='pixabay' AND query=?",
                (query,),
            ).fetchone()
            if row:
                return json.loads(row["response"])
        if self.rate_limited:
            return {}
        data = self._http_get(query)
        if data is None:
            self.rate_limited = True
            return {}
        if self.conn is not None:
            # ON CONFLICT (không phải INSERT OR REPLACE): chạy được cả SQLite lẫn
            # Postgres — cùng lý do đã ghi ở pexels._cached_get (G2 hai lưng).
            self.conn.execute(
                "INSERT INTO search_cache (provider, query, response, cached_at) "
                "VALUES ('pixabay', ?, ?, ?) ON CONFLICT(provider, query) DO UPDATE SET "
                "response=excluded.response, cached_at=excluded.cached_at",
                (query, json.dumps(data), datetime.now(timezone.utc).isoformat()),
            )
            self.conn.commit()
        return data

    def _http_get(self, query: str) -> Optional[dict]:
        """Trả dict, hoặc None khi hết hạn mức (429) -> caller bật cờ rate_limited."""
        for idx in range(len(self.keys)):
            if idx in self.exhausted:
                continue
            self.key_idx = idx
            try:
                resp = requests.get(
                    PIXABAY_VIDEO_URL,
                    params={"key": self.keys[idx], "q": query,
                            "per_page": PER_PAGE, "video_type": "film"},
                    timeout=(10, 30),
                )
            except requests.RequestException:
                return {}  # lỗi mạng tạm: coi như không có kết quả, KHÔNG giết cả stage
            if resp.status_code == 429:
                self.exhausted.add(idx)
                continue  # key này hết hạn mức -> thử key sau
            if not resp.ok:
                return {}
            try:
                return resp.json()
            except ValueError:
                return {}
        return None  # mọi key đều hết hạn mức


def collect_pixabay_keys(env: Optional[dict] = None) -> list[str]:
    """Gom key Pixabay từ .env — cùng quy ước với collect_pexels_keys."""
    env = env if env is not None else os.environ
    raw: list[str] = []
    for name in ("PIXABAY_API_KEY", "PIXABAY_API_KEYS"):
        raw += re.split(r"[,\s]+", env.get(name, ""))
    for i in range(2, 11):
        raw += re.split(r"[,\s]+", env.get(f"PIXABAY_API_KEY_{i}", ""))
    seen: set[str] = set()
    out: list[str] = []
    for k in raw:
        k = k.strip()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


class MultiStockClient:
    """Gộp nhiều StockClient theo THỨ TỰ ƯU TIÊN.

    Nguồn sau chỉ chạy khi nguồn trước chưa đủ MIN_CANDIDATES_PER_TIER — cùng luật
    "tier sau chỉ chạy khi tier trước nghèo" của Pexels, áp lên cấp nguồn.
    download() định tuyến theo `candidate["source"]` nên clip nào về nguồn nấy.
    """

    def __init__(self, clients: list) -> None:
        if not clients:
            raise ValueError("MultiStockClient cần ít nhất 1 client")
        self.clients = clients

    def search_tiered(self, queries: SearchQueries) -> list[dict]:
        out: list[dict] = []
        seen: set[str] = set()
        for client in self.clients:
            for c in client.search_tiered(queries):
                if c["asset_key"] not in seen:
                    seen.add(c["asset_key"])
                    out.append(c)
            if len(out) >= MIN_CANDIDATES_PER_TIER:
                break  # đủ giàu — khỏi gọi nguồn sau, tiết kiệm hạn mức
        return out

    def download(self, candidate: dict, dest: Path) -> Path:
        src = candidate.get("source", "")
        for client in self.clients:
            # Client nào nhận nguồn này thì client đó tải (giữ đúng key/referer của nó)
            if getattr(client, "SOURCE_NAME", "") == src:
                return client.download(candidate, dest)
        # Không khớp tên nguồn -> client đầu (download chỉ cần candidate["url"])
        return self.clients[0].download(candidate, dest)

    @property
    def rate_limited(self) -> bool:
        """True khi MỌI nguồn đều hết hạn mức — runner dừng gọi mạng."""
        return all(getattr(c, "rate_limited", False) for c in self.clients)
