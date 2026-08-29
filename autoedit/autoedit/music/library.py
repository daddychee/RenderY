"""Thư viện nhạc — THU_VIEN_NHAC.md. Lưu PHẲNG + tag metadata (KHÔNG chia folder mood).

Nguồn tag: Cowork ghi `music_manifest.yaml` (mood/genre/vocals/bpm từ Artlist) + librosa
(energy/sections/duration). `overrides.yaml` của editor luôn THẮNG. Index = `music_index.json`
(đọc được, commit git). KHÔNG copy file — nhạc ở nguyên `tracks/`, chỉ ghi index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from autoedit.music.analyze import analyze_rhythm, analyze_track, tempo_class
from autoedit.packager.machine import resolve_data_root

# field librosa trong index — record cũ (trước MUSIC SYNC) thiếu nhóm RHYTHM_KEYS
ANALYSIS_KEYS = ("duration_sec", "bpm", "tempo_class", "energy", "energy_curve",
                 "sections", "loopable")
# beat_strength/accent_strength thêm 2026-07-19 (mini-hook + lưới beat ô thở). PHẢI có
# trong list này, nếu không regrid_index đo xong mà KHÔNG lưu (backfill chạy rỗng im lặng).
RHYTHM_KEYS = ("beat_times", "beat_strength", "downbeats", "accents", "accent_strength",
               "beat_quality", "beat_tier")

# G1: root theo machine.json `set-data-root` (chưa set = ~/AutoEdit/music như cũ)
MUSIC_ROOT = resolve_data_root() / "music"
TRACKS_DIR = "tracks"
INDEX_FILE = "music_index.json"
MANIFEST_FILE = "music_manifest.yaml"
OVERRIDES_FILE = "overrides.yaml"


def music_root_for(niche: str | None) -> Path:
    """Pool nhạc theo NICHE (user chốt 2026-07-17, mở đầu life-in): tồn tại
    <music_root>/<niche>/tracks/ -> niche đó CHỈ dùng pool riêng (KHÔNG rơi về
    pool chung — nhạc không lẫn 2 chiều giữa niche); chưa có folder -> pool chung.
    Tên folder = niche NGUYÊN VĂN (khớp ambient niche_dir, vd music/life-in/)."""
    niche = (niche or "").strip()
    if niche and (MUSIC_ROOT / niche / TRACKS_DIR).is_dir():
        return MUSIC_ROOT / niche
    return MUSIC_ROOT

# Vocabulary đóng (THU_VIEN mục 3) — tag lạ ngoài đây bị bỏ (báo để bổ sung map)
MOOD = {"epic", "uplifting", "inspiring", "hopeful", "happy", "playful", "peaceful",
        "dreamy", "romantic", "nostalgic", "mysterious", "suspenseful", "tense", "dark",
        "sad", "angry", "scary", "serious", "determined"}
GENRE = {"cinematic", "ambient", "electronic", "acoustic", "classical", "hip_hop",
         "rock", "pop", "folk", "jazz", "world", "lo_fi"}
VOCALS = {"instrumental", "female_vocals", "male_vocals", "duet", "group", "acapella",
          "vocal_samples"}
VIDEO_THEME = {"documentary", "true_crime", "travel", "technology", "business_finance",
               "history", "nature", "lifestyle", "motivational"}


@dataclass
class ImportResult:
    imported: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)
    unknown_tags: set[str] = field(default_factory=set)


def _norm(tag: str) -> str:
    return tag.strip().lower().replace(" ", "_").replace("-", "_")


def _map_tags(values, allowed: set, sink: set) -> list[str]:
    """Chuẩn hóa list tag tự do về vocabulary đóng; tag lạ -> sink để báo."""
    out = []
    for v in values or []:
        t = _norm(str(v))
        if t in allowed:
            out.append(t)
        else:
            sink.add(t)
    return out


def import_from_filenames(lib_root: Path = MUSIC_ROOT, reanalyze: bool = False) -> ImportResult:
    """Luồng CHỐT: dựng manifest TỪ TÊN FILE (`Artist - Title __mood`) rồi import.
    Ghi lại music_manifest.yaml (để xem/sửa) + music_index.json."""
    from autoedit.music.naming import manifest_from_tracks

    lib_root = Path(lib_root)
    entries, unknown = manifest_from_tracks(lib_root / TRACKS_DIR)
    # ghi manifest (đọc được) để minh bạch
    (lib_root / MANIFEST_FILE).write_text(
        yaml.safe_dump({"tracks": entries}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    res = _import_entries(entries, lib_root, reanalyze=reanalyze)
    res.unknown_tags |= unknown
    return res


def import_manifest(manifest_path: Path, lib_root: Path = MUSIC_ROOT,
                    reanalyze: bool = False) -> ImportResult:
    """Đọc manifest YAML viết tay -> import. (Luồng mặc định nay là import_from_filenames.)"""
    data = yaml.safe_load(Path(manifest_path).read_text(encoding="utf-8")) or {}
    return _import_entries(data.get("tracks", []), Path(lib_root), reanalyze=reanalyze)


def _import_entries(entries: list[dict], lib_root: Path, reanalyze: bool = False) -> ImportResult:
    """Core: map vocab + librosa analyze mỗi entry -> ghi music_index.json. overrides thắng."""
    tracks_dir = lib_root / TRACKS_DIR
    overrides = _load_overrides(lib_root)
    index = {r["file"]: r for r in _load_index(lib_root)}  # giữ record cũ (đỡ analyze lại)
    res = ImportResult()

    for e in entries:
        fname = e.get("file", "")
        src = tracks_dir / fname
        if not src.is_file():
            res.failed.append((fname, f"không thấy file trong {tracks_dir}"))
            continue
        vocals = _norm(e.get("vocals", "instrumental"))
        if vocals not in VOCALS:
            res.unknown_tags.add(vocals)
            vocals = "instrumental"
        rec = {
            "file": fname,
            "title": e.get("title", Path(fname).stem),
            "artist": e.get("artist", ""),
            "artlist_url": e.get("artlist_url", ""),
            "vocals": vocals,
            "mood": _map_tags(e.get("mood"), MOOD, res.unknown_tags),
            "genre": _map_tags(e.get("genre"), GENRE, res.unknown_tags),
            "video_theme": _map_tags(e.get("video_theme"), VIDEO_THEME, res.unknown_tags),
            "instruments": [_norm(x) for x in (e.get("instruments") or [])],
            "added_date": date(2026, 6, 14).isoformat(),
        }
        # librosa: chỉ phân tích nếu chưa có (đỡ tốn) — analyze lỗi thì vẫn giữ tag
        prev = index.get(fname, {})
        if not reanalyze and prev.get("energy_curve"):
            obj = {k: prev[k] for k in ANALYSIS_KEYS + RHYTHM_KEYS if k in prev}
            # record cũ thiếu grid (trước MUSIC SYNC) HOẶC thiếu độ mạnh (trước 2026-07-19)
            # -> đo lại nhịp. Tier C hợp lệ khi có beat_tier mà beat_times rỗng, nên phải
            # hỏi "có KEY không", KHÔNG hỏi "có giá trị không" (nếu không tier C đo lại mãi).
            if "beat_tier" not in obj or "beat_strength" not in obj:
                # luật: mọi bài phải có grid; lỗi -> thiếu beat_tier = downstream coi
                # như tier C (fail-open)
                try:
                    obj.update(analyze_rhythm(src))
                except Exception as exc:
                    res.failed.append((fname, f"librosa rhythm lỗi: {exc}"))
        else:
            try:
                obj = analyze_track(src)
            except Exception as exc:
                res.failed.append((fname, f"librosa lỗi: {exc}"))
                obj = {}
        # BPM ưu tiên Artlist (nếu manifest có) — librosa hay lệch gấp đôi/nửa
        if e.get("bpm"):
            try:
                obj["bpm"] = float(e["bpm"])
                obj["tempo_class"] = tempo_class(obj["bpm"])
            except (TypeError, ValueError):
                pass
        rec.update(obj)
        if fname in overrides:                      # editor sửa tay luôn thắng
            rec.update(overrides[fname])
        index[fname] = rec
        res.imported.append(fname)

    _save_index(lib_root, list(index.values()))
    return res


def regrid_index(lib_root: Path = MUSIC_ROOT) -> tuple[list[dict], list[tuple[str, str]]]:
    """MUSIC SYNC M0 backfill: đo lại nhịp/accent cho MỌI bài trong index (field khác
    giữ nguyên — PRESERVE). Trả (rows sau cập nhật, [(file, lỗi)])."""
    rows = _load_index(lib_root)
    tracks_dir = Path(lib_root) / TRACKS_DIR
    failed: list[tuple[str, str]] = []
    for r in rows:
        src = tracks_dir / r.get("file", "")
        if not src.is_file():
            failed.append((r.get("file", "?"), f"không thấy file trong {tracks_dir}"))
            continue
        try:
            r.update(analyze_rhythm(src))
        except Exception as exc:
            failed.append((r["file"], f"librosa lỗi: {exc}"))
    _save_index(lib_root, rows)
    return rows, failed


def list_tracks(lib_root: Path = MUSIC_ROOT, mood: str = "", energy: str = "") -> list[dict]:
    rows = _load_index(lib_root)
    if mood:
        rows = [r for r in rows if _norm(mood) in r.get("mood", [])]
    if energy:
        rows = [r for r in rows if _energy_class(r.get("energy", 0.5)) == energy]
    return rows


def _energy_class(e: float) -> str:
    return "low" if e < 0.45 else ("high" if e > 0.7 else "medium")


def library_status(lib_root: Path = MUSIC_ROOT) -> dict:
    rows = _load_index(lib_root)
    moods: dict[str, int] = {}
    for r in rows:
        for m in r.get("mood", []):
            moods[m] = moods.get(m, 0) + 1
    return {"tracks": len(rows), "by_mood": moods}


# ---------------- I/O ----------------
def _index_path(lib_root: Path) -> Path:
    return Path(lib_root) / INDEX_FILE


def _load_index(lib_root: Path) -> list[dict]:
    import json
    f = _index_path(lib_root)
    if not f.is_file():
        return []
    return json.loads(f.read_text(encoding="utf-8")).get("tracks", [])


def _save_index(lib_root: Path, rows: list[dict]) -> None:
    import json
    Path(lib_root).mkdir(parents=True, exist_ok=True)
    _index_path(lib_root).write_text(
        json.dumps({"tracks": rows}, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _load_overrides(lib_root: Path) -> dict:
    f = Path(lib_root) / OVERRIDES_FILE
    if not f.is_file():
        return {}
    return yaml.safe_load(f.read_text(encoding="utf-8")) or {}


USAGE_FILE = "music_usage.json"


def load_usage(lib_root: Path = MUSIC_ROOT) -> dict:
    """{file: số lần đã dùng} — phạt mềm cho đa dạng giữa video."""
    import json
    f = Path(lib_root) / USAGE_FILE
    if not f.is_file():
        return {}
    return json.loads(f.read_text(encoding="utf-8"))


def save_usage(lib_root: Path, usage: dict) -> None:
    import json
    Path(lib_root).mkdir(parents=True, exist_ok=True)
    (Path(lib_root) / USAGE_FILE).write_text(
        json.dumps(usage, indent=2, ensure_ascii=False), encoding="utf-8"
    )
