"""Sinh manifest TỪ TÊN FILE — editor gắn mood ngay vào tên (luồng chốt 14/06).

Quy ước tên: `Artist - Title __mood [__mood2 ...].mp3`. Delimiter `__`. Editor (hiểu niche
nhất) tự gắn mood khi tải — KHÔNG cần Cowork đọc Artlist (cào mood chập chờn). Tool parse tên
→ manifest → librosa đo phần khách quan.
"""

from __future__ import annotations

import re
from pathlib import Path

from autoedit.music.library import MOOD, _norm

AUDIO_EXTS = (".mp3", ".wav", ".aac", ".m4a", ".flac")


def manifest_from_tracks(tracks_dir: Path) -> tuple[list[dict], set]:
    """Quét tracks/ → [entry] gộp theo base "Artist - Title" (union mood). Trả (entries, tag_lạ).
    Bỏ qua file có 'short version' (Artlist short = quá ngắn)."""
    tracks_dir = Path(tracks_dir)
    by_base: dict[str, dict] = {}
    unknown: set = set()
    for p in sorted(tracks_dir.glob("*")):
        if p.suffix.lower() not in AUDIO_EXTS or not p.is_file():
            continue
        if "short version" in p.stem.lower():
            continue
        parts = re.split(r"\s*__\s*", p.stem)
        base = parts[0].strip()
        moods = []
        for tok in parts[1:]:
            t = _norm(tok)
            if t in MOOD:
                moods.append(t)
            elif t:
                unknown.add(t)
        artist, _, title = base.partition(" - ")
        if not title:                       # không có " - " -> coi cả là title
            artist, title = "", base
        key = base.lower()
        if key in by_base:                  # base trùng -> union mood, giữ 1 file
            cur = by_base[key]
            cur["mood"] = sorted(set(cur["mood"]) | set(moods))
        else:
            by_base[key] = {
                "file": p.name,
                "title": title.strip(),
                "artist": artist.strip(),
                "vocals": "instrumental",
                "mood": sorted(set(moods)),
                "genre": [],
                "video_theme": [],
                "instruments": [],
            }
    return list(by_base.values()), unknown
