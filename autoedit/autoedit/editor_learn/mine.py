"""Mót file audio từ draft editor — COPY-only, TUYỆT ĐỐI không ghi vào folder draft
(S4/M5, MO_TA_SFX_HOAN_THIEN §4b.2).

Phân loại theo TÊN file (chuẩn tay PB10 làm precedent — xem bảng kind đã gán trong
F:\\AutoEdit\\ambient\\space\\ambient_library.yaml) + thời lượng đặt trên timeline:
  voice -> bỏ · whoosh ngắn/dài -> sfx whoosh/swell · tên chủ thể -> ambient subject-kind
  · tên UI (pop/typing/data...) -> sfx · tên cảnh (storm/crowd/space...) -> ambient
  · đặt cả bài >40s không keyword -> NHẠC staging music_editor/<draft>/ (KHÔNG vào pool
  chọn nhạc — tránh lật hệ mood, user gọi mới nạp) · còn lại -> hold tu_editor_chua_phan_loai.

Danh tính file = TÊN MATERIAL trong draft (file SFX kho CapCut nằm trên đĩa dưới tên
HASH md5 — tên material mới là tên có nghĩa; copy ra kho cũng mang tên material).
Dedup theo stem tên material + tên file đĩa: đối chiếu records ambient/sfx
(source_file/title), manifest chờ, hold, staging nhạc — draft đã học chạy lại ra 0 đề
xuất mới. Manifest sinh ra ĐÚNG schema ambient-import/sfx-import; provenance ghi
``artlist_url: editor:<tên draft>``.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from autoedit.ambient.library import (
    AMBIENT_KINDS,
    MANIFEST_FILE,
    RECORDS_FILE,
    load_subject_rules,
)
from autoedit.ambient.schedule import SUBJECT_RULES
from autoedit.editor_learn.dna import (
    SEC,
    VOICE_HINTS,
    WHOOSH_HINTS,
    audio_name_map,
    load_draft,
    voice_tracks,
)

HOLD_DIR = "tu_editor_chua_phan_loai"
# "Clip ghép" = compound clip CapCut — khúc timeline editor trộn sẵn (SP1-001 chứa voice
# nửa sau video), không phải SFX tái dùng được -> skip như voice
COMPOUND_HINTS = ("clip ghép",)
AUDIO_EXTS = (".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".wma")
SFX_STAGING = "tu_editor"
SFX_STAGING_MANIFEST = "sfx_manifest_editor.yaml"
MUSIC_SEG_MIN_S = 40.0   # đặt cả bài (PB13: nhạc/drone >40s)
SWELL_SPLIT_S = 4.0      # whoosh dài hơn -> kind swell (whoosh dài trải khúc chuyển)

# Mở rộng SUBJECT_RULES (vision, EN chuẩn hóa) cho TÊN FILE editor: tiếng Việt +
# biến thể precedent mót tay ("fireworks rocket" -> explosion; "Earth rumbling" -> rumble).
# Xét TRƯỚC SUBJECT_RULES để precedent thắng ("fireworks rocket" không rơi vào rocket).
_MINE_SUBJECT_EXTRA: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("explosion", ("fireworks",)),
    ("rumble", ("rumbling",)),
    ("fire", ("lửa", "sôi", "mặt trời")),
    ("rocket", ("tên lửa",)),
    ("signal", ("tín hiệu",)),
)

# SFX UI/data (thứ tự xét) — theo kind thư viện sfx (sfx/library.py KINDS)
_SFX_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("riser", ("riser",)),
    ("swell", ("swell", "swells")),
    ("pop", ("pop", "tap")),
    ("keyboard", ("typing", "keyboard", "keyboards")),
    ("ding", ("ding", "data")),
    ("impact", ("impact",)),
)

# Cảnh (thứ tự xét — precedent mót tay SP1: storm/roaring -> mountain_desert TRƯỚC
# space vì "wind roaring ... devastated space"; default là catch-all pad cuối cùng)
_SCENE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("mountain_desert", ("storm", "snow", "roaring", "blizzard", "desert")),
    ("people_activity", ("crowd", "people", "applause", "cheering")),
    # nature TRƯỚC urban_street: "Chuo City, Yamanashi" — tên địa danh chứa "city"
    # cướp mất tiếng côn trùng đêm (bug SP1-012); KHÔNG thêm "nature" vào keyword —
    # "Wind sound effects (nature, breeze...)" phải rơi xuống sky_cloud
    ("nature_forest_field", ("insect", "cricket", "forest")),
    ("urban_street", ("traffic", "city", "street", "birds")),
    ("sky_cloud", ("wind", "breeze", "sky")),
    ("space", ("space", "vũ trụ", "cosmos", "galaxy", "universe", "cosmic")),
    ("default", ("ambient", "amvien", "drone", "ù ù", "hum", "atmosphere", "atmospheric")),
)

_KIND_NAME_PAT = re.compile(
    rf"^({'|'.join(re.escape(k) for k in AMBIENT_KINDS)})(_\d+)?\.wav$")


def norm_name(name: str) -> str:
    """Stem thường hóa để match keyword + dedup: bỏ đuôi audio, lower, _-. thành space.

    CHỈ cắt đuôi khi là đuôi audio thật — Path.stem cắt mù ".(1424901)" làm 2 SFX kho
    CapCut "Whoosh sound effect.(1424899/1424901)" trùng danh tính -> dedup oan."""
    p = Path(name)
    stem = name[: -len(p.suffix)] if p.suffix.lower() in AUDIO_EXTS else name
    return re.sub(r"\s+", " ", re.sub(r"[_\-.]+", " ", stem.lower())).strip()


def _kw(norm: str, words: tuple[str, ...]) -> bool:
    # s? bắt số nhiều ("Rockets, missiles" phải ra rocket); \d* bắt số DÁN liền đuôi —
    # editor đặt tên kiểu "cá nhà táng2", "Water Whoosh2" (không space, \b không ăn)
    return any(re.search(rf"\b{re.escape(w)}s?\d*\b", norm) for w in words)


def resolve_media(draft_dir: Path, material: dict) -> Path | None:
    """path placeholder ##_draftpath_..._##/materials/x -> <draft>/materials/x;
    path tuyệt đối giữ nguyên; không thấy file -> None (báo missing, không đoán)."""
    p = material.get("path", "")
    cand: Path | None = None
    if "_draftpath_placeholder_" in p:
        cand = Path(draft_dir) / p.split("_##", 1)[1].lstrip("/\\")
    elif p:
        cand = Path(p)
    if cand and cand.is_file():
        return cand
    # path chết (draft dời máy) -> thử materials/<basename path> rồi materials/<name>
    # (mẻ deepsea 2026-07-13: name material hay lệch file đĩa — cùng khuôn fix ingest)
    for nm in (Path(p.replace("\\", "/")).name if p else "", material.get("name") or ""):
        fb = Path(draft_dir) / "materials" / nm if nm else None
        if fb and fb.is_file():
            return fb
    return None


@dataclass
class AudioUse:
    name: str
    path: Path | None
    file_dur_s: float
    max_seg_s: float = 0.0
    in_voice_track: bool = False


def collect_audio_usage(draft_dir: Path, d: dict) -> dict[str, AudioUse]:
    """Gom material audio theo TÊN (CapCut nhân bản material — nhiều id cùng 1 file)."""
    name_of = audio_name_map(d)
    uses: dict[str, AudioUse] = {}
    for a in d["materials"].get("audios", []):
        nm = a.get("name") or ""
        if nm and nm not in uses:
            uses[nm] = AudioUse(name=nm, path=resolve_media(draft_dir, a),
                                file_dur_s=(a.get("duration") or 0) / SEC)
    vtracks = voice_tracks(d, name_of)
    for t in d["tracks"]:
        if t.get("type") != "audio":
            continue
        for s in t.get("segments", []):
            u = uses.get(name_of.get(s.get("material_id"), ""))
            if u is None:
                continue
            u.max_seg_s = max(u.max_seg_s, s["target_timerange"]["duration"] / SEC)
            if t in vtracks:
                u.in_voice_track = True
    return uses


def classify(u: AudioUse, rules=None) -> tuple[str, str]:
    """-> (dest, kind). dest: voice|sfx|ambient|music|hold. rules = bảng chủ thể
    per-niche (subject_rules.yaml — keywords VN khớp tên file editor); None -> built-in."""
    if u.in_voice_track or any(h in u.name.lower() for h in VOICE_HINTS + COMPOUND_HINTS):
        return "voice", ""
    n = norm_name(u.name)
    if any(h in n for h in WHOOSH_HINTS):
        dur = u.file_dur_s or u.max_seg_s
        return "sfx", ("whoosh" if dur <= SWELL_SPLIT_S else "swell")
    for kind, words in _MINE_SUBJECT_EXTRA + tuple(rules if rules is not None else SUBJECT_RULES):
        if _kw(n, words):
            return "ambient", kind
    for kind, words in _SFX_RULES:
        if _kw(n, words):
            return "sfx", kind
    for kind, words in _SCENE_RULES:
        if _kw(n, words):
            return "ambient", kind
    if u.max_seg_s > MUSIC_SEG_MIN_S:
        return "music", ""
    return "hold", ""


@dataclass
class MineResult:
    ambient: list[tuple[str, str]] = field(default_factory=list)   # (kind, file đã copy)
    sfx: list[tuple[str, str]] = field(default_factory=list)
    music: list[str] = field(default_factory=list)
    hold: list[str] = field(default_factory=list)
    known: list[str] = field(default_factory=list)      # đã có trong kho -> bỏ qua
    voice: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)    # material không thấy file


def _stems_of_dir(d: Path) -> set[str]:
    return {norm_name(p.name) for p in d.iterdir() if p.is_file()} if d.is_dir() else set()


def _manifest_entries(path: Path, key: str) -> list[dict]:
    if not path.is_file():
        return []
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(key, [])


def _known_stems(niche_path: Path, sfx_root: Path, music_root: Path) -> set[str]:
    known: set[str] = set()
    for rec in (_manifest_entries(niche_path / RECORDS_FILE, "ambient")
                + _manifest_entries(niche_path / MANIFEST_FILE, "ambient")):
        known |= {norm_name(rec.get("source_file") or rec.get("file") or ""),
                  norm_name(rec.get("title") or "")}
    known |= _stems_of_dir(niche_path)
    known |= _stems_of_dir(niche_path / "raw")
    known |= _stems_of_dir(niche_path / "raw" / HOLD_DIR)
    staging = sfx_root / SFX_STAGING
    for rec in (_manifest_entries(sfx_root / "sfx_manifest.yaml", "sfx")
                + _manifest_entries(staging / SFX_STAGING_MANIFEST, "sfx")):
        known |= {norm_name(rec.get("title") or ""), norm_name(rec.get("file") or "")}
    known |= _stems_of_dir(staging)
    if music_root.is_dir():
        known |= {norm_name(p.name) for p in music_root.rglob("*") if p.is_file()}
    known.discard("")
    return known


def _out_name(material_name: str, src: Path) -> str:
    """Tên file copy ra kho = tên material (có nghĩa), thêm đuôi từ file đĩa nếu thiếu,
    lọc ký tự Windows cấm; tên đụng khuôn <kind>_<n>.wav của thư viện -> thêm tiền tố
    'editor - ' (list_variants không được nuốt file thô chưa chuẩn hóa)."""
    name = re.sub(r'[<>:"/\\|?*]', " ", material_name).strip().rstrip(". ")
    if Path(name).suffix.lower() not in AUDIO_EXTS:  # "effect.(1424899)" không phải đuôi
        name += src.suffix
    if _KIND_NAME_PAT.match(name.lower()):
        name = f"editor - {name}"
    return name


def _copy(src: Path, dst_dir: Path, name: str, dry_run: bool) -> str:
    if not dry_run:
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / name
        if not dst.exists():
            shutil.copy2(src, dst)
    return name


def _merge_manifest(path: Path, key: str, new_entries: list[dict], dry_run: bool) -> None:
    if not new_entries or dry_run:
        return
    entries = _manifest_entries(path, key)
    have = {norm_name(e.get("file") or "") for e in entries}
    entries += [e for e in new_entries if norm_name(e["file"]) not in have]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({key: entries}, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")


def mine_draft(
    draft_dir: Path,
    niche_path: Path,
    sfx_root: Path,
    music_root: Path,
    dry_run: bool = False,
) -> MineResult:
    """music_root = <library_root cha>/music_editor; nhạc copy vào <music_root>/<draft>/."""
    draft_dir = Path(draft_dir)
    d = load_draft(draft_dir)
    known = _known_stems(niche_path, sfx_root, music_root)
    res = MineResult()
    amb_entries: list[dict] = []
    sfx_entries: list[dict] = []
    provenance = f"editor:{draft_dir.name}"
    rules = load_subject_rules(niche_path)  # kind loài per-niche (None -> built-in)

    for u in collect_audio_usage(draft_dir, d).values():
        dest, kind = classify(u, rules)
        if dest == "voice":
            res.voice.append(u.name)
            continue
        if u.path is None:
            res.missing.append(u.name)
            continue
        # danh tính = tên material (file kho CapCut trên đĩa mang tên hash md5)
        if norm_name(u.name) in known or norm_name(u.path.name) in known:
            res.known.append(u.name)
            continue
        known |= {norm_name(u.name), norm_name(u.path.name)}
        fname = _out_name(u.name, u.path)
        if dest == "ambient":
            _copy(u.path, niche_path, fname, dry_run)
            amb_entries.append({"file": fname, "kind": kind,
                               "artlist_url": provenance, "title": u.name})
            res.ambient.append((kind, fname))
        elif dest == "sfx":
            _copy(u.path, sfx_root / SFX_STAGING, fname, dry_run)
            sfx_entries.append({"file": fname, "kind": kind,
                               "artlist_url": provenance, "title": u.name})
            res.sfx.append((kind, fname))
        elif dest == "music":
            res.music.append(_copy(u.path, music_root / draft_dir.name, fname, dry_run))
        else:
            res.hold.append(_copy(u.path, niche_path / "raw" / HOLD_DIR, fname, dry_run))

    _merge_manifest(niche_path / MANIFEST_FILE, "ambient", amb_entries, dry_run)
    _merge_manifest(sfx_root / SFX_STAGING / SFX_STAGING_MANIFEST, "sfx", sfx_entries, dry_run)
    return res
