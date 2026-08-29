"""Tra file SFX theo kind. P1.3 dùng thư mục đơn giản + fallback; P1.4 thay bằng
thư viện SFX có tag đầy đủ (mirror thư viện nhạc)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".aac")


def resolve_sfx_variants(
    sfx_kind: str, sfx_dir: Optional[Path], fallback: Optional[Path] = None
) -> list[Path]:
    """Mọi biến thể <sfx_dir>/<kind>*.<ext> (để assembler xoay vòng cho đỡ lặp).

    Rỗng -> [fallback] nếu có; sfx_kind 'none' -> [].
    """
    if sfx_kind == "none":
        return []
    variants: list[Path] = []
    if sfx_dir is not None:
        d = Path(sfx_dir)
        if d.is_dir():
            for ext in AUDIO_EXTS:
                variants += sorted(p for p in d.glob(f"{sfx_kind}*{ext}") if p.is_file())
    if variants:
        return variants
    return [fallback] if fallback and Path(fallback).is_file() else []


def resolve_sfx(
    sfx_kind: str, sfx_dir: Optional[Path], fallback: Optional[Path] = None
) -> Optional[Path]:
    """1 file SFX (biến thể đầu) — giữ cho tương thích; assembler dùng variants."""
    v = resolve_sfx_variants(sfx_kind, sfx_dir, fallback)
    return v[0] if v else None
