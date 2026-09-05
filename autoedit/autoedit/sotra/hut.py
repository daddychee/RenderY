r"""HÚT nguồn vào Sổ Tra — Envato (scraping preview công khai) + Pexels/Pixabay
(API chính thức, key sẵn trong .env/két) + nạp REF từ thư mục tập.

RÓN RÉN là luật (bài học YouTube ~9 lượt bị chặn IP + Envato cấm tải song song):
1 luồng tuần tự, giãn nhịp ngẫu nhiên GIAN_NHIP giữa 2 request, fail-open từng
từ khóa (lỗi thì ghi log đi tiếp, không giết phiên).

Hút CHỈ lấy metadata + URL (ảnh/video preview hotlink được trong app) — không
tải file nào về. Frames JPEG rút LAZY khi cần (media.py).
"""

from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from autoedit.sotra import db as sdb
from autoedit.sotra.tag7 import tag_tu_tieu_de

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
GIAN_NHIP = (2.5, 5.0)


def _get(url: str, headers: dict | None = None, timeout: float = 45.0) -> bytes:
    h = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read()


# ------------------------------------------------------------ ENVATO (scraping)
def hut_envato(tu_khoa: str, trang: int = 1) -> list[dict]:
    """1 trang search công khai -> clip records. Đã kiểm 06/09: 200 OK không cần
    login; ảnh cover phải GIỮ NGUYÊN query (có chữ ký, tự chế là 403); video
    preview watermarked URL BỀN không ký."""
    q = urllib.parse.quote_plus(tu_khoa)
    url = f"https://elements.envato.com/stock-video/{q}" + (f"?page={trang}" if trang > 1 else "")
    h = _get(url).decode("utf-8", "replace")
    mp4: dict[str, str] = {}
    for m in re.finditer(r'https://video-previews\.elements\.envatousercontent\.com/'
                         r'([0-9a-f-]{36})/watermarked_preview/watermarked_preview\.mp4', h):
        mp4[m.group(1)] = m.group(0)
    ra, thay = [], set()
    mau = (r'<img[^>]+src="(https://elements-resized\.envatousercontent\.com/'
           r'elements-video-cover-images/([0-9a-f-]{36})/video_preview/'
           r'video_preview_\d{4}\.jpg[^"]*)"[^>]*alt="([^"]{5,160})"')
    for m in re.finditer(mau, h):
        uid = m.group(2)
        if uid in thay:
            continue
        thay.add(uid)
        ten = re.sub(r"\s+", " ", m.group(3)).strip()
        ra.append({"id": sdb.lam_id("envato", uid), "nguon": "envato", "tieu_de": ten,
                   "url_trang": f"https://elements.envato.com/stock-video/item-{uid}",
                   "url_anh": m.group(1).replace("&amp;", "&"),
                   "url_video": mp4.get(uid, ""), "tu_khoa_hut": tu_khoa,
                   **tag_tu_tieu_de(ten)})
    return ra


# ------------------------------------------------------------ PEXELS (API)
def hut_pexels(tu_khoa: str, trang: int = 1, per_page: int = 40) -> list[dict]:
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        raise RuntimeError("thiếu PEXELS_API_KEY")
    d = json.loads(_get(
        "https://api.pexels.com/videos/search?query="
        f"{urllib.parse.quote_plus(tu_khoa)}&per_page={per_page}&page={trang}",
        headers={"Authorization": key}))
    ra = []
    for v in d.get("videos", []):
        # preview nhỏ nhất >=540p cho hover-play; link gốc để re-locate đợt 5
        files = sorted((f for f in v.get("video_files", []) if f.get("height")),
                       key=lambda f: f["height"])
        prev = next((f for f in files if f["height"] >= 360), files[0] if files else None)
        ten = (v.get("url") or "").rstrip("/").rsplit("/", 1)[-1].replace("-", " ")
        ten = re.sub(r"\s+\d+$", "", ten).strip() or f"pexels {v['id']}"
        ra.append({"id": sdb.lam_id("pexels", v["id"]), "nguon": "pexels",
                   "tieu_de": ten, "url_trang": v.get("url", ""),
                   "url_anh": v.get("image", ""),
                   "url_video": (prev or {}).get("link", ""),
                   "dai_s": float(v.get("duration") or 0), "tu_khoa_hut": tu_khoa,
                   **tag_tu_tieu_de(ten)})
    return ra


# ------------------------------------------------------------ PIXABAY (API)
def hut_pixabay(tu_khoa: str, trang: int = 1, per_page: int = 40) -> list[dict]:
    key = os.getenv("PIXABAY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("thiếu PIXABAY_API_KEY")
    d = json.loads(_get(
        f"https://pixabay.com/api/videos/?key={key}&q="
        f"{urllib.parse.quote_plus(tu_khoa)}&per_page={per_page}&page={trang}"))
    ra = []
    for v in d.get("hits", []):
        vid = v.get("videos", {})
        prev = vid.get("small") or vid.get("tiny") or {}
        ten = (v.get("tags") or f"pixabay {v['id']}").replace(",", " ")
        ra.append({"id": sdb.lam_id("pixabay", v["id"]), "nguon": "pixabay",
                   "tieu_de": ten, "url_trang": v.get("pageURL", ""),
                   "url_anh": prev.get("thumbnail", ""),
                   "url_video": prev.get("url", ""),
                   "dai_s": float(v.get("duration") or 0), "tu_khoa_hut": tu_khoa,
                   **tag_tu_tieu_de(ten)})
    return ra


_BO_HUT = {"envato": hut_envato, "pexels": hut_pexels, "pixabay": hut_pixabay}


def phien_hut(conn, tu_khoas: list[str], nguons: list[str],
              so_trang: int = 1, log=None) -> dict:
    """Chạy 1 PHIÊN hút tuần tự rón rén. Trả {"moi": n, "trung": n, "loi": [..]}."""
    def ghi(m):
        if log:
            log(m)

    kq = {"moi": 0, "trung": 0, "loi": []}
    for tk in tu_khoas:
        for ng in nguons:
            ham = _BO_HUT.get(ng)
            if ham is None:
                continue
            for tr in range(1, so_trang + 1):
                try:
                    ds = ham(tk, tr)
                except Exception as exc:  # noqa: BLE001 — fail-open từng lượt
                    kq["loi"].append(f"{ng} «{tk}» tr{tr}: {str(exc)[:90]}")
                    ghi(f"sotra: ! {ng} «{tk}»: {str(exc)[:80]}")
                    break
                moi = sum(sdb.them_clip(conn, r) for r in ds)
                sdb.ghi_phien_hut(conn, tk, ng, moi, len(ds) - moi)
                conn.commit()
                kq["moi"] += moi
                kq["trung"] += len(ds) - moi
                ghi(f"sotra: {ng} «{tk}» trang {tr}: {len(ds)} kq ({moi} mới)")
                time.sleep(random.uniform(*GIAN_NHIP))
    return kq


# ------------------------------------------------------------ REF của tập
def nap_ref_tap(conn, thu_muc_tap: Path, tap: str = "", toi_thieu_s: float = 2.5,
                log=None) -> int:
    """Quét *.srt + .mp4 cùng tên trong thư mục tập -> mỗi câu thoại đủ dài là
    một KHÚC ref (id mang timecode). File KHÔNG copy — chỉ ghi path + t0/t1."""
    thu_muc_tap = Path(thu_muc_tap)
    tap = tap or thu_muc_tap.name
    moi = 0
    for srt in sorted(thu_muc_tap.rglob("*.srt")):
        vid = srt.with_suffix(".mp4")
        if not vid.is_file():
            continue
        txt = srt.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"(\d\d):(\d\d):(\d\d),\d+\s*-->\s*"
                             r"(\d\d):(\d\d):(\d\d),\d+\s*\n(.+?)(?:\n\n|\Z)", txt, re.S):
            g = m.groups()
            t0 = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2])
            t1 = int(g[3]) * 3600 + int(g[4]) * 60 + int(g[5])
            if t1 - t0 < toi_thieu_s:
                continue
            loi = re.sub(r"\s+", " ", g[6]).strip()[:120]
            r = {"id": sdb.lam_id("ref", f"{tap}-{vid.stem}", f"{t0}-{t1}"),
                 "nguon": "ref", "tieu_de": loi, "path_local": str(vid),
                 "t0": float(t0), "t1": float(t1), "dai_s": float(t1 - t0),
                 "tap": tap, **tag_tu_tieu_de(loi)}
            moi += sdb.them_clip(conn, r)
    conn.commit()
    if log:
        log(f"sotra: nạp ref «{tap}»: +{moi} khúc")
    return moi
