"""Thư viện SFX ~/AutoEdit/sfx/ — nhập file từ manifest Cowork (Artlist).

Lưu phẳng: <kind>_<n>.wav. Giữ artlist_url trong sfx_manifest.yaml để truy ngược
license (THU_VIEN_NHAC.md mục 6). Mỗi loại nhiều biến thể -> assembler xoay vòng.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from autoedit.packager.machine import resolve_data_root
from autoedit.packager.transcode import normalize_audio

# G1: root theo machine.json `set-data-root` (chưa set = ~/AutoEdit/sfx như cũ)
SFX_ROOT = resolve_data_root() / "sfx"
MANIFEST_FILE = "sfx_manifest.yaml"
KINDS = (
    "cash", "impact", "pop", "whoosh", "riser",
    # Phase 2A: SFX biểu đồ (Req 2) + chữ gõ máy (Req 1)
    "chart_bar", "chart_line", "chart_pie", "ding", "keyboard",
    # S3 (M4): whoosh DÀI cho chuyển chương. Tên cố ý KHÔNG bắt đầu bằng "whoosh" —
    # resolve_sfx_variants glob lỏng "whoosh*" sẽ nuốt nó vào kind whoosh overlay cũ.
    "swell",
)


@dataclass
class ImportResult:
    imported: list[str]                 # "<kind> <- <file>"
    failed: list[tuple[str, str]]       # (file, lý do)


def list_variants(kind: str, sfx_root: Path = SFX_ROOT) -> list[Path]:
    """Mọi biến thể của 1 loại: <kind>.wav, <kind>_2.wav... (sort ổn định)."""
    if not sfx_root.is_dir():
        return []
    return sorted(p for p in sfx_root.glob(f"{kind}*.wav") if p.is_file())


def _next_name(kind: str, sfx_root: Path) -> Path:
    existing = list_variants(kind, sfx_root)
    n = len(existing) + 1
    return sfx_root / (f"{kind}.wav" if n == 1 else f"{kind}_{n}.wav")


def import_from_manifest(
    manifest_path: Path,
    downloads_dir: Path,
    sfx_root: Path = SFX_ROOT,
) -> ImportResult:
    """Đọc manifest Cowork -> chuẩn hóa WAV vào thư viện + ghi sfx_manifest.yaml.

    manifest YAML: {sfx: [{file, kind, artlist_url, title}, ...]}.
    """
    sfx_root.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(Path(manifest_path).read_text(encoding="utf-8")) or {}
    entries = data.get("sfx", [])
    result = ImportResult(imported=[], failed=[])
    records = _load_records(sfx_root)

    for e in entries:
        fname, kind = e.get("file", ""), e.get("kind", "")
        if kind not in KINDS:
            result.failed.append((fname, f"kind '{kind}' không hợp lệ (chọn {KINDS})"))
            continue
        src = Path(downloads_dir) / fname
        if not src.is_file():
            result.failed.append((fname, f"không thấy file trong {downloads_dir}"))
            continue
        try:
            dst = _next_name(kind, sfx_root)
            normalize_audio(src, dst)  # mp3/aac Artlist -> WAV PCM 48k
        except Exception as exc:
            result.failed.append((fname, f"chuẩn hóa lỗi: {exc}"))
            continue
        records.append({
            "kind": kind, "file": dst.name, "artlist_url": e.get("artlist_url", ""),
            "title": e.get("title", fname), "added_date": date(2026, 6, 13).isoformat(),
        })
        result.imported.append(f"{kind} <- {fname}")

    _save_records(sfx_root, records)
    return result


def _load_records(sfx_root: Path) -> list[dict]:
    f = sfx_root / MANIFEST_FILE
    if not f.is_file():
        return []
    return (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("sfx", [])


def _save_records(sfx_root: Path, records: list[dict]) -> None:
    (sfx_root / MANIFEST_FILE).write_text(
        yaml.safe_dump({"sfx": records}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def library_status(sfx_root: Path = SFX_ROOT) -> dict[str, int]:
    """kind -> số biến thể."""
    return {k: len(list_variants(k, sfx_root)) for k in KINDS}
