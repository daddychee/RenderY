"""Thư viện ambient <ambient_root>/<niche>/ — C1 (MO_TA_VAN_HANH_C1_AMBIENT §3/§7).

Cấu trúc THEO NICHE (user chốt 2026-07-10): F:\\AutoEdit\\ambient\\space\\...
Root suy từ library_root CHA (machine.json) — đổi ổ không sửa code, 0 config mới.

File chuẩn: <kind>.wav, <kind>_2.wav... — kind = scene_type GLM (vision.py) + "default"
+ SUBJECT_KINDS (tiếng theo CHỦ THỂ trên hình — S2) + "drone" (nền suốt video — S1).
Hai file yaml trong folder niche:
  ambient_manifest.yaml — INPUT chờ nhập ({ambient: [{file, kind, artlist_url, title}]});
                          nhập xong dọn vào raw/ đổi đuôi .done.yaml
  ambient_library.yaml  — RECORDS thư viện (kèm source_file + artlist_url truy license)
Nguồn thô nằm TRONG folder niche -> sau nhập dọn vào raw/; nằm NGOÀI -> giữ nguyên
(TUYỆT ĐỐI không đụng draft editor).
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from autoedit.library.vision import SCENE_TYPES
from autoedit.packager.transcode import normalize_audio

# C đợt 3b (MO_TA_VAN_HANH_SFX_HOAN_THIEN §2/§3): tiếng chủ thể + drone nền.
# `ocean` tách khỏi `water` (tai V7: biển cần tiếng SÓNG nhẹ, water của kho là rót/sôi)
# — kho chưa có file ocean thì beat biển IM (thà im còn hơn sai), gom file sau.
SUBJECT_KINDS: tuple[str, ...] = ("fire", "rocket", "explosion", "rumble", "water", "ocean", "signal")
# S3-HOOK (MO_TA_VAN_HANH_HOOK_SFX §2): hit/whoosh/click tại cut trong hook — kho
# PER-NICHE (không vào ~/AutoEdit/sfx toàn cục: rotation overlay-SFX mọi niche).
# KHÔNG khai trong subject_rules.yaml (không phải tiếng chủ thể — tránh S2 spam).
HOOK_SFX_KINDS: tuple[str, ...] = ("impact", "whoosh", "click")
AMBIENT_KINDS: tuple[str, ...] = (tuple(SCENE_TYPES) + ("default",) + SUBJECT_KINDS
                                  + ("drone",) + HOOK_SFX_KINDS)
MANIFEST_FILE = "ambient_manifest.yaml"
RECORDS_FILE = "ambient_library.yaml"
RULES_FILE = "subject_rules.yaml"
RAW_DIR = "raw"


def load_subject_rules(
    niche_path: Path,
) -> tuple[tuple[str, tuple[str, ...]], ...] | None:
    """Bảng chủ thể -> kind RIÊNG của niche (subject_rules.yaml trong folder niche —
    sheet SFX editor 2026-07-13). Có file -> THAY TRỌN SUBJECT_RULES built-in (không
    merge — tránh luật space rơi nhầm vào deepsea); không có -> None (dùng built-in).
    Schema: {rules: [{kind, keywords: [...]}]} — keywords EN = tag vision (schedule
    match), VN = tên file editor (editor-learn classify dùng chung bảng)."""
    f = Path(niche_path) / RULES_FILE
    if not f.is_file():
        return None
    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    return tuple(
        (r["kind"], tuple(r.get("keywords") or ()))
        for r in data.get("rules", []) if r.get("kind")
    )


def niche_kinds(niche_path: Path) -> tuple[str, ...]:
    """AMBIENT_KINDS + kind riêng của niche (khai trong subject_rules.yaml)."""
    rules = load_subject_rules(niche_path) or ()
    extra = tuple(k for k, _ in rules if k not in AMBIENT_KINDS)
    return AMBIENT_KINDS + extra


@dataclass
class ImportResult:
    imported: list[str]                 # "<kind> <- <file thô>"
    failed: list[tuple[str, str]]       # (file, lý do)


def ambient_root(override: str | Path | None = None) -> Path:
    """<library_root cha>/ambient — vd library F:\\AutoEdit\\library -> F:\\AutoEdit\\ambient."""
    if override:
        return Path(override).expanduser()
    from autoedit.library.profile import resolve_library_root

    return resolve_library_root().parent / "ambient"


def niche_dir(niche: str, root: str | Path | None = None) -> Path:
    return ambient_root(root) / niche


def _variant_no(p: Path) -> int:
    m = re.search(r"_(\d+)\.wav$", p.name)
    return int(m.group(1)) if m else 1


EPIDEMIC_URL_MARK = "epidemicsound.com"


def epidemic_files(niche_path: Path) -> frozenset[str]:
    """Tên file có nguồn Epidemic (đọc artlist_url trong records).

    Dùng cho cờ `--no-epidemic` lúc dựng: editor tắt thì kho VẪN GIỮ file, chỉ không
    chọn tới. Không xóa, không folder riêng — bật lại là có ngay."""
    return frozenset(
        r["file"] for r in _load_records(niche_path)
        if EPIDEMIC_URL_MARK in str(r.get("artlist_url", "")) and r.get("file")
    )


def list_variants(kind: str, niche_path: Path,
                  exclude_files: "frozenset[str] | None" = None) -> list[Path]:
    """Biến thể của 1 kind, đúng thứ tự số. Khớp CHẶT ^kind(_n).wav$ — urban_street
    không dính urban_landmark. Folder niche chưa có -> [] (fail-open, tầng ambient tắt).

    exclude_files: loại theo TÊN FILE (dùng cho --no-epidemic). Giữ nguyên thứ tự số
    của phần còn lại — rotation vẫn deterministic."""
    if not niche_path.is_dir():
        return []
    pat = re.compile(rf"^{re.escape(kind)}(_\d+)?\.wav$")
    skip = exclude_files or frozenset()
    return sorted((p for p in niche_path.iterdir()
                   if p.is_file() and pat.match(p.name) and p.name not in skip),
                  key=_variant_no)


def _next_name(kind: str, niche_path: Path) -> Path:
    vs = list_variants(kind, niche_path)
    n = _variant_no(vs[-1]) + 1 if vs else 1
    return niche_path / (f"{kind}.wav" if n == 1 else f"{kind}_{n}.wav")


def import_from_manifest(
    manifest_path: Path,
    downloads_dir: Path,
    niche_path: Path,
) -> ImportResult:
    """Nhập file thô theo manifest -> chuẩn hóa WAV PCM 48k thành <kind>_<n>.wav."""
    manifest_path = Path(manifest_path)
    downloads_dir = Path(downloads_dir)
    niche_path.mkdir(parents=True, exist_ok=True)
    entries = (yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}).get("ambient", [])
    result = ImportResult(imported=[], failed=[])
    records = _load_records(niche_path)
    raw_dir = niche_path / RAW_DIR
    kinds = niche_kinds(niche_path)  # + kind riêng niche (subject_rules.yaml)
    to_move: set[Path] = set()  # dọn SAU vòng lặp — 1 file thô có thể vào 2 kind

    for e in entries:
        fname, kind = e.get("file", ""), e.get("kind", "")
        if kind not in kinds:
            result.failed.append((fname, f"kind '{kind}' không hợp lệ (scene_type GLM + default + subject + drone + subject_rules.yaml)"))
            continue
        src = downloads_dir / fname
        if not src.is_file():
            result.failed.append((fname, f"không thấy file trong {downloads_dir}"))
            continue
        try:
            dst = _next_name(kind, niche_path)
            normalize_audio(src, dst)  # mp3/aac/wav 24bit -> WAV PCM 48k (luật C4)
        except Exception as exc:
            result.failed.append((fname, f"chuẩn hóa lỗi: {exc}"))
            continue
        records.append({
            "kind": kind, "file": dst.name, "source_file": fname,
            "artlist_url": e.get("artlist_url", ""), "title": e.get("title", fname),
            "added_date": date.today().isoformat(),
        })
        result.imported.append(f"{kind} <- {fname}")
        if src.parent.resolve() == niche_path.resolve():
            to_move.add(src)

    for src in to_move:
        raw_dir.mkdir(parents=True, exist_ok=True)
        _move_overwrite(src, raw_dir / src.name)
    _save_records(niche_path, records)
    if result.imported and manifest_path.parent.resolve() == niche_path.resolve():
        raw_dir.mkdir(parents=True, exist_ok=True)
        _move_overwrite(manifest_path, raw_dir / (manifest_path.stem + ".done.yaml"))
    return result


def _move_overwrite(src: Path, dst: Path) -> None:
    if dst.exists():
        dst.unlink()
    shutil.move(str(src), dst)


def _load_records(niche_path: Path) -> list[dict]:
    f = niche_path / RECORDS_FILE
    if not f.is_file():
        return []
    return (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("ambient", [])


def _save_records(niche_path: Path, records: list[dict]) -> None:
    (niche_path / RECORDS_FILE).write_text(
        yaml.safe_dump({"ambient": records}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def library_status(niche_path: Path) -> dict[str, int]:
    """kind -> số biến thể (chỉ kind có file)."""
    out = {k: len(list_variants(k, niche_path)) for k in niche_kinds(niche_path)}
    return {k: n for k, n in out.items() if n}
