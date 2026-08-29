"""Ống nạp draft CapCut nguồn (PB4 — spec MO_TA_VAN_HANH_TAG_GLM §2 loại 1).

Draft nguồn là project của editor công ty: `draft_content.json` cho SẴN mép cắt
(segment + source range + file nguồn). Ống CHỈ ĐỌC draft (không ghi -> luật C1/C3/C5
không kích hoạt), cắt clip bằng ffmpeg theo source range + chuẩn C4, bỏ vào
`<niche>/nap/<tên draft>/`, tag qua máy `tag_jobs` chung với indexer, ghi cache.db
kèm cột §3b (source_video / scene_start / scene_index / has_voice).

Chốt điểm treo spec §2 "cảnh nào thành ASSET":
- Mọi segment video/photo trên track video có file nguồn còn trên đĩa.
- BỎ: cảnh nguồn < MIN_SCENE_S (flash cut, không tái dùng — PB5 vẫn đếm được từ draft),
  material trong Cache CapCut (onlineMaterial = nền/sticker tải về, không phải footage),
  segment trùng (cùng file nguồn + cùng khúc — tên clip cắt deterministic nên
  nạp lại / draft khác dùng chung khúc tự dedup qua needs_index).
- has_voice: track audio NHIỀU segment nhất = voice (voice bị chém theo script thành
  hàng trăm khúc, nhạc chỉ vài khúc dài); cảnh có voice khi voice phủ ≥ VOICE_OVERLAP
  thời lượng cảnh trên timeline. Không có track audio -> -1 (chưa biết).
"""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence

from autoedit.library import db, ytpeaks
from autoedit.library.indexer import INGEST_DIR, TagJob, tag_jobs
from autoedit.library.vision import VisionTagger
from autoedit.library.ytpeaks import YTVideoInfo

MIN_SCENE_S = 2.0     # sàn cảnh (c8 luật 6, user chốt 2026-07-08): <2s bỏ TRƯỚC khi
#                       cắt/vision — flash cut không tái dùng, đỡ tiền tag. Áp MỌI mẻ nạp.
VOICE_OVERLAP = 0.25  # voice phủ ≥25% thời lượng cảnh -> has_voice=1

# c8 — luật cắt nguồn viral (foundation/c8-cat-nguon-viral.md), chỉ áp source_class='viral':
VIRAL_MAX_S = 10.0    # luật 1: trần miếng cắt từ 1 nguồn
VIRAL_SAFE_S = 6.0    # luật 1: cảnh >10s bóp còn 6s KHÚC GIỮA (chuẩn an toàn)
VIRAL_ZOOM = 1.12     # luật 4: crop tâm ~112% NƯỚNG CHẾT vào clip -> mất logo/chữ mép
# ytref §3a (user chốt 2026-07-10, áp MỌI mẻ viral từ nay): cảnh >20s = CapCut dò trượt
# chuyển cảnh mềm, trong cảnh có mối nối -> BỎ (đếm too_long). NGOẠI LỆ cảnh CÓ điểm
# nhô: cắt 6s NEO ĐỈNH (§3f) — 6s sát đỉnh ít rủi ro dính mối nối hơn nhiều so 20s trọn.
VIRAL_DROP_S = 20.0
# §3e 📌 ĐIỀU CHỈNH 2026-07-11 (cổng mắt user: "cắt không đúng đỉnh, đặc biệt video
# nhiều điểm nhô"): cửa sổ gắn cờ gốc [foot, apex+1s] ôm cả DỐC LÊN (đo thật: dốc tới
# 45s+) -> cảnh ở chân dốc cách đỉnh cả phút vẫn mang cờ (video 17 đỉnh cờ 50% cảnh).
# Cửa sổ MỚI = BIN ĐỈNH heatmap nới ±1s ([apex-1s, apex_end+1s]) — value đo trên bin,
# khoảnh khắc xem-lại nằm trong bin; foot chỉ còn là thông tin.
PEAK_FLAG_PAD = 1.0
# 📌 ĐIỀU CHỈNH 2 cùng ngày (user duyệt cắt-đúng-đỉnh rồi chốt thêm): điểm nhô = chuỗi
# **3 footage TỪ ĐỈNH VỀ TRƯỚC** (vd đỉnh 60s -> footage đắt ~4x..60s, build-up liên
# quan trực tiếp nhau) — lấy CẢ 3; luật kề ±1 của ledger MIỄN cho cảnh điểm nhô
# (sourcer/viral.py), trần 8% giữ nguyên.
PEAK_RUNUP_N = 3       # cảnh chứa đỉnh + 2 cảnh liền trước
PEAK_CHAIN_GAP_S = 3.0  # cảnh trước hở >3s nguồn = đứt chuỗi build-up, dừng lấy lùi
_PLACEHOLDER = re.compile(r"^##_draftpath_placeholder_[0-9A-Fa-f-]+_##[/\\]")

# spec TOPIC_CHAPTER_FILE (user chốt 2026-07-11): editor đặt file này TRONG folder draft
# — dòng trước chapter đầu = tiêu đề/chủ đề, dòng "M:SS Tên" = chapter (format YouTube,
# copy từ mô tả video). own = nguồn chính; viral = fallback khi YouTube trống.
CONTEXT_FILE = "topic + chapter video.txt"
_CHAPTER_LINE = re.compile(r"^\s*(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\b[\s\-–—:.]*(\S.*)$")
# format thật editor (SP1-012): có dòng NHÃN "Topic video:" / "chapter" — bỏ nhãn,
# giữ nội dung. Prefix chỉ strip khi CÓ dấu hai chấm (tiêu đề bắt đầu "Chapter..." an toàn).
_LABEL_ONLY = re.compile(r"^(topic(\s+video)?|chapters?|tiêu đề|chủ đề|chương)\s*[:：]?$",
                         re.IGNORECASE)
_LABEL_PREFIX = re.compile(r"^(topic(\s+video)?|tiêu đề|chủ đề)\s*[:：]\s*", re.IGNORECASE)


@dataclass
class DraftScene:
    """1 segment video/photo trong draft nguồn -> 1 asset ứng viên."""

    source: Path        # file nguồn (đã resolve placeholder)
    media_type: str     # video | photo
    start: float        # giây bắt đầu trong FILE NGUỒN (source_timerange)
    duration: float     # giây (source range — footage gốc, không theo speed)
    index: int          # ytref §3g: thứ tự source_start TRONG TỪNG file nguồn (1-based)
    has_voice: int      # 0/1; -1 nếu draft không có track audio
    target_start: float = 0.0     # vị trí trên TIMELINE (giây) — thống kê DNA (dna.py)
    target_duration: float = 0.0
    source_duration: float = 0.0  # tổng giây FILE NGUỒN (c8: mẫu số trần 8% gói CHỌN)
    peak_value: float = 0.0       # ytref §3e: value đỉnh Most Replayed giao cảnh (0 = không cờ)
    peak_type: str = ""           # primary | secondary
    peak_apex: float = 0.0        # giây apex trong FILE NGUỒN — neo bóp 6s (§3f), không vào db


@dataclass
class IngestResult:
    scenes: int                 # cảnh thành asset ứng viên (sau lọc)
    cut_new: int = 0            # clip mới cắt ra
    cut_reused: int = 0         # clip đã có trên đĩa (nạp lại)
    skipped_db: int = 0         # đã tag trong db, không đổi
    indexed: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)  # cắt hoặc tag lỗi
    stats: dict = field(default_factory=dict)  # số liệu lọc cho kill-log


def _resolve_material_path(raw: str, draft_dir: Path) -> Path:
    """Path material: placeholder `##_draftpath_placeholder_<GUID>_##/...` -> trong
    folder draft; còn lại là path tuyệt đối (C2). Path tuyệt đối CHẾT (draft dời máy,
    vd `D:/CapCut Drafts/...` của mẻ deepsea) -> fallback `<draft>/materials/<basename>`
    nếu file có thật — chỉ kích hoạt khi path gốc missing, hành vi cũ giữ nguyên."""
    if _PLACEHOLDER.match(raw):
        return draft_dir / _PLACEHOLDER.sub("", raw).replace("\\", "/")
    p = Path(raw)
    if raw and not p.is_file():
        local = draft_dir / "materials" / p.name
        if local.is_file():
            return local
    return p


def _overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def read_timeline(draft_dir: Path) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """(shots, voice) trên TIMELINE draft, giây — cho thống kê DNA (dna.py) + ống nạp.

    shots: (start, duration) MỌI segment track video theo thứ tự timeline (kể cả cảnh
    ống nạp bỏ — nhịp cắt thật cần đủ). voice: (start, end) track audio NHIỀU segment
    nhất (voice bị chém theo script thành hàng trăm khúc; nhạc vài khúc dài).
    """
    content = json.loads((draft_dir / "draft_content.json").read_text(encoding="utf-8"))
    tracks = content.get("tracks", [])
    shots: list[tuple[float, float]] = []
    for t in tracks:
        if t.get("type") != "video":
            continue
        for s in t.get("segments", []):
            tt = s.get("target_timerange") or {}
            shots.append((tt.get("start", 0) / 1e6, tt.get("duration", 0) / 1e6))
    shots.sort()
    voice: list[tuple[float, float]] = []
    audio_tracks = [t for t in tracks if t.get("type") == "audio" and t.get("segments")]
    if audio_tracks:
        for s in max(audio_tracks, key=lambda t: len(t["segments"]))["segments"]:
            tt = s.get("target_timerange") or {}
            t0 = tt.get("start", 0) / 1e6
            voice.append((t0, t0 + tt.get("duration", 0) / 1e6))
    return shots, sorted(voice)


def read_draft_scenes(draft_dir: Path) -> tuple[list[DraftScene], dict]:
    """Đọc draft_content.json (ĐỌC-ONLY) -> cảnh ứng viên + số liệu lọc."""
    content = json.loads((draft_dir / "draft_content.json").read_text(encoding="utf-8"))
    materials = {m["id"]: m for m in content.get("materials", {}).get("videos", [])}
    tracks = content.get("tracks", [])
    _, voice_ranges = read_timeline(draft_dir)

    stats = {"segments": 0, "missing_file": 0, "cache_material": 0,
             "too_short": 0, "duplicate": 0, "no_source_range": 0}
    raw: list[tuple[float, Path, str, float, float, float]] = []
    seen: set[tuple[str, float, float]] = set()
    for t in tracks:
        if t.get("type") != "video":
            continue
        for s in t.get("segments", []):
            m = materials.get(s.get("material_id"))
            if m is None or m.get("type") not in ("video", "photo"):
                continue
            stats["segments"] += 1
            src = _resolve_material_path(str(m.get("path", "")), draft_dir)
            # material trong Cache CapCut (onlineMaterial = nền đen/sticker tải về,
            # không phải footage) — chỉ bỏ khi nằm ĐÚNG trong cache CapCut
            parts = {part.lower() for part in src.parts}
            if "capcut" in parts and "cache" in parts:
                stats["cache_material"] += 1
                continue
            if not src.is_file():
                stats["missing_file"] += 1
                continue
            st, tt = s.get("source_timerange") or {}, s.get("target_timerange") or {}
            if not st:
                stats["no_source_range"] += 1
                continue
            start, dur = st.get("start", 0) / 1e6, st.get("duration", 0) / 1e6
            if m.get("type") == "video" and dur < MIN_SCENE_S:
                stats["too_short"] += 1
                continue
            key = (str(src), round(start, 1), round(dur, 1))
            if key in seen:
                stats["duplicate"] += 1
                continue
            seen.add(key)
            t0 = tt.get("start", 0) / 1e6
            t_dur = tt.get("duration", 0) / 1e6
            if not voice_ranges:
                has_voice = -1
            else:
                covered = sum(_overlap(t0, t0 + t_dur, v0, v1) for v0, v1 in voice_ranges)
                has_voice = int(t_dur > 0 and covered / t_dur >= VOICE_OVERLAP)
            src_total = m.get("duration", 0) / 1e6  # tổng giây file nguồn (c8 trần 8%)
            raw.append((t0, t_dur, src, m["type"], start, dur, has_voice, src_total))

    raw.sort(key=lambda r: r[0])  # thứ tự LIST = timeline (dna.py duyệt theo list)
    scenes = [DraftScene(source=src, media_type=mt, start=start, duration=dur,
                         index=0, has_voice=hv, target_start=t0, target_duration=t_dur,
                         source_duration=sd)
              for (t0, t_dur, src, mt, start, dur, hv, sd) in raw]
    # ytref §3g (gia cố luật c8 số 3): index = thứ tự source_start TRONG TỪNG file
    # nguồn — ledger check kề ±1 theo NGUỒN; index timeline toàn draft cũ làm 2 cảnh
    # kề thật mang index xa nhau nếu nguồn trộn xen kẽ. Sàn 2s lọc TRƯỚC đây nên không
    # để lỗ; trần 20s (§3a) lọc SAU nên để lỗ -> 2 cảnh hai bên thành kề index =
    # ledger chặn RỘNG hơn thật một chút, đúng chiều bảo thủ pháp lý (MO_TA §3g).
    by_src: dict[str, list[DraftScene]] = {}
    for sc in scenes:
        by_src.setdefault(str(sc.source), []).append(sc)
    for group in by_src.values():
        for i, sc in enumerate(sorted(group, key=lambda s: s.start), start=1):
            sc.index = i
    return scenes, stats


# ---------------- ytref: điểm nhô + bối cảnh YouTube (MO_TA_YTREF §3b-3f) ----------------

def youtube_infos_for(scenes: list[DraftScene]) -> tuple[dict[str, YTVideoInfo], list[str]]:
    """Mỗi file nguồn 1 call yt-dlp (§3c) -> {str(source): YTVideoInfo} + warnings.

    Fail-open từng nguồn: thiếu ID / yt-dlp lỗi -> nguồn đó nạp như viral thường,
    1 dòng warning để editor bổ sung (luật user 2026-07-10: mọi mẻ viral PHẢI kèm
    URL/YouTube ID — tên file hoặc urls.txt cạnh file nguồn).
    """
    infos: dict[str, YTVideoInfo] = {}
    warnings: list[str] = []
    for src in dict.fromkeys(str(s.source) for s in scenes):
        vid = ytpeaks.resolve_youtube_id(Path(src))
        if not vid:
            warnings.append(f"{Path(src).name}: không tìm ra YouTube ID (tên file / "
                            "urls.txt) — nạp thiếu bối cảnh + điểm nhô")
            continue
        info = ytpeaks.fetch_video_info(vid)
        if info.error:
            warnings.append(f"{Path(src).name}: yt-dlp lỗi ({info.error}) — nạp thiếu "
                            "bối cảnh + điểm nhô")
            continue
        infos[src] = info
    return infos, warnings


def apply_viral_rules(scenes: list[DraftScene], stats: dict,
                      infos: dict[str, YTVideoInfo], warnings: list[str]) -> list[DraftScene]:
    """Luật viral §3a/§3d/§3e/§3f — thuần, không mạng (dry-run/test gọi thẳng).

    Gắn cờ điểm nhô (cảnh giao BIN ĐỈNH ±1s — điều chỉnh 2026-07-11, xem PEAK_FLAG_PAD;
    video lệch duration >3% bỏ cờ cả video — §3d) rồi lọc/bóp: >20s BỎ trừ cảnh có cờ
    (6s NEO GIỮA BIN ĐỈNH), 10-20s bóp 6s (neo đỉnh nếu có cờ, khúc giữa nếu không).
    """
    stats["squeezed_6s"] = 0
    stats["too_long"] = 0
    stats["peak_videos"] = 0
    stats["peak_total"] = 0
    for src, info in infos.items():
        group = [s for s in scenes if str(s.source) == src and s.media_type == "video"]
        if not info.peaks or not group:
            continue
        file_dur = group[0].source_duration
        if ytpeaks.duration_mismatch(file_dur, info.duration):  # §3d chống mốc trượt
            warnings.append(f"{Path(src).name}: duration file {file_dur:.0f}s lệch "
                            f"YouTube {info.duration:.0f}s >3% — KHÔNG gắn cờ điểm nhô "
                            "(gắn sai còn hại hơn không gắn)")
            continue
        stats["peak_videos"] += 1
        stats["peak_total"] += len(info.peaks)
        group = sorted(group, key=lambda s: s.start)
        for p in info.peaks:
            apex_end = p.apex_end or p.apex_time
            apex_mid = (p.apex_time + apex_end) / 2  # khoảnh khắc đỉnh ~ giữa bin
            hits = [i for i, s in enumerate(group)
                    if _overlap(s.start, s.start + s.duration,
                                p.apex_time - PEAK_FLAG_PAD, apex_end + PEAK_FLAG_PAD) > 0]
            if not hits:
                continue
            # cảnh CHỨA đỉnh; đỉnh rơi vào khe (cảnh <2s đã bỏ) -> cảnh giao muộn nhất
            k = next((i for i in hits
                      if group[i].start <= apex_mid < group[i].start + group[i].duration),
                     None)
            if k is None:
                before = [i for i in hits if group[i].start <= apex_mid]
                k = before[-1] if before else hits[0]
            # 📌 điều chỉnh 2: trio = cảnh chứa đỉnh + 2 cảnh LIỀN TRƯỚC (build-up),
            # dừng khi hở >PEAK_CHAIN_GAP_S; cảnh SAU đỉnh không lấy
            trio = [k]
            while len(trio) < PEAK_RUNUP_N and trio[0] > 0:
                prev, cur = group[trio[0] - 1], group[trio[0]]
                if cur.start - (prev.start + prev.duration) > PEAK_CHAIN_GAP_S:
                    break
                trio.insert(0, trio[0] - 1)
            for i in trio:
                sc = group[i]
                if p.value > sc.peak_value:  # cảnh dính 2 đỉnh -> giữ đỉnh cao hơn
                    sc.peak_value, sc.peak_type, sc.peak_apex = p.value, p.type, apex_mid

    kept: list[DraftScene] = []
    for sc in scenes:
        if sc.media_type != "video":
            kept.append(sc)
            continue
        if sc.duration > VIRAL_DROP_S and not sc.peak_type:
            stats["too_long"] += 1  # §3a: trong cảnh có mối nối dò trượt — bỏ, đếm công khai
            continue
        if sc.duration > VIRAL_MAX_S:
            if sc.peak_type:
                # §3f: 6s SÁT ĐỈNH nhất trong biên cảnh — cảnh chứa đỉnh ôm giữa bin;
                # cảnh build-up trước đỉnh lấy 6s CUỐI (phần dẫn vào đỉnh, 📌 đc 2)
                tail = min(sc.peak_apex + VIRAL_SAFE_S / 2, sc.start + sc.duration)
                sc.start = max(tail - VIRAL_SAFE_S, sc.start)
            else:
                sc.start += (sc.duration - VIRAL_SAFE_S) / 2  # khúc giữa (y cũ)
            sc.duration = VIRAL_SAFE_S
            stats["squeezed_6s"] += 1
        kept.append(sc)
    stats["peak_scenes"] = sum(1 for s in kept if s.peak_type)
    return kept


def _chapter_at(chapters: Sequence[dict], t: float) -> str:
    """Tên chapter chứa mốc t giây; '' = không rơi vào chapter nào (fail-open)."""
    for c in chapters:
        if c["start_time"] <= t < (c["end_time"] or float("inf")):
            return c["title"]
    return ""


def yt_chapter_gate(scenes: Sequence["DraftScene"],
                    infos: dict[str, YTVideoInfo]) -> tuple[set, list[str]]:
    """Cổng chapter YouTube (MO_TA_TCF_FILE_NGUON §1): editor cắt bỏ đoạn -> file lệch
    duration YouTube -> chapter map giây file TRƯỢT MỐC (section_hint sai mọi cảnh sau
    điểm cắt). Cùng bệnh với cờ điểm nhô (§3d) — cổng ĐỘC LẬP, không đụng logic peak.
    Trả (set nguồn có chapter TIN ĐƯỢC, warnings)."""
    ok: set = set()
    warns: list[str] = []
    for src, info in infos.items():
        if not info.chapters:
            continue
        fdur = next((s.source_duration for s in scenes if str(s.source) == src), 0.0)
        if ytpeaks.duration_mismatch(fdur, info.duration):
            warns.append(f"{Path(src).name}: chapter YouTube BỎ — duration file "
                         f"{fdur:.0f}s lệch YouTube {info.duration:.0f}s >3% (mốc trượt; "
                         "dùng file bối cảnh editor / tcf-gen file nguồn)")
        else:
            ok.add(src)
    return ok, warns


def _chapter_title(info: Optional[YTVideoInfo], t: float) -> str:
    """§3i-2: tên YouTube chapter chứa mốc t (giây FILE NGUỒN); '' = không có (fail-open)."""
    return _chapter_at(info.chapters, t) if info is not None else ""


@dataclass
class DraftContext:
    """Bối cảnh từ file CONTEXT_FILE editor đặt trong folder draft (spec TCF §2)."""

    topic: str = ""
    # cùng khuôn YTVideoInfo.chapters: [{start_time, end_time (None = hết video), title}]
    chapters: list = field(default_factory=list)


def read_draft_context(draft_dir: Path) -> DraftContext:
    """Đọc file 'topic + chapter video.txt' (spec TOPIC_CHAPTER_FILE, không phân biệt
    hoa thường). Mọi dòng TRƯỚC chapter đầu = tiêu đề (gộp); "đủ chapter" = >=2 dòng
    (1 chapter = cả video, không có giá trị chia đoạn -> chỉ lấy tiêu đề). Fail-open:
    không file / lỗi đọc -> rỗng, tag y cũ; dòng hỏng bỏ đúng dòng đó."""
    ctx = DraftContext()
    try:
        f = next((p for p in draft_dir.iterdir()
                  if p.is_file() and p.name.lower() == CONTEXT_FILE), None)
        if f is None:
            return ctx
        text = f.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ctx
    topic_lines: list[str] = []
    raw: list[tuple[float, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _CHAPTER_LINE.match(line)
        if m:
            h, mnt, sec, title = m.groups()
            raw.append((float((int(h or 0)) * 3600 + int(mnt) * 60 + int(sec)),
                        title.strip()))
        elif not raw:  # sau chapter đầu, dòng không-timestamp = dòng hỏng -> bỏ
            if _LABEL_ONLY.match(line):
                continue
            line = _LABEL_PREFIX.sub("", line).strip()
            if line:
                topic_lines.append(line)
    ctx.topic = " ".join(topic_lines).strip()
    if len(raw) >= 2:
        raw.sort(key=lambda x: x[0])
        ctx.chapters = [
            {"start_time": s,
             "end_time": raw[i + 1][0] if i + 1 < len(raw) else None,
             "title": t}
            for i, (s, t) in enumerate(raw)
        ]
    return ctx


def _safe_stem(name: str, max_len: int = 48) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()[:max_len].rstrip(". ")


def scene_clip_name(scene: DraftScene, zoom: float = 0.0) -> str:
    """Tên clip DETERMINISTIC theo (file nguồn + khúc [+ zoom]) — nạp lại/draft khác
    dùng chung khúc ra cùng tên -> tự dedup qua file tồn tại + needs_index. Zoom vào
    tên: sau này đổi % zoom -> tên mới -> cắt + tag lại, không tái dùng clip zoom cũ."""
    ext = ".mp4" if scene.media_type == "video" else ".jpg"
    z = f"_z{round(zoom * 100)}" if zoom > 1 else ""
    return (f"{_safe_stem(scene.source.stem)}"
            f"__{int(scene.start * 1000):09d}_{int(scene.duration * 1000):07d}{z}{ext}")


def _zoom_vf(zoom: float) -> str:
    """Filter crop tâm 1/zoom rồi scale về ~cỡ gốc (số chẵn cho yuv420p) — c8 luật 4."""
    return (f"crop=trunc(iw/{zoom}/2)*2:trunc(ih/{zoom}/2)*2,"
            f"scale=trunc(iw*{zoom}/2)*2:trunc(ih*{zoom}/2)*2")


def cut_scene(scene: DraftScene, out_dir: Path, zoom: float = 0.0) -> tuple[Path, bool]:
    """Cắt cảnh khỏi file nguồn + chuẩn C4. Trả (clip, mới cắt?). Idempotent: có rồi bỏ qua.

    Video: H.264 CFR 30fps yuv420p (C4), `-an` bỏ audio nguồn (voice/nhạc của video
    gốc — không tái dùng được, đỡ ~1/3 dung lượng; viral = luật c8-2). `-ss` TRƯỚC
    `-i` + re-encode = seek chính xác tới frame mà không decode từ đầu file (nguồn
    dài 10-60 phút). Ảnh: JPEG bỏ EXIF (C4), giữ nguyên kích thước (sàn F5 lọc sau).
    zoom > 1 (viral, c8 luật 4): crop tâm nướng chết vào clip/ảnh — logo/chữ mép mất
    ngay trong kho, vision tag SAU zoom nên tag đúng hình dùng thật.
    """
    dst = out_dir / scene_clip_name(scene, zoom)
    if dst.is_file() and dst.stat().st_size > 0:
        return dst, False
    dst.parent.mkdir(parents=True, exist_ok=True)
    vf = ["-vf", _zoom_vf(zoom)] if zoom > 1 else []
    if scene.media_type == "video":
        cmd = ["ffmpeg", "-y", "-v", "error",
               "-ss", f"{scene.start:.3f}", "-i", str(scene.source),
               "-t", f"{scene.duration:.3f}", *vf,
               "-c:v", "libx264", "-preset", "fast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-r", "30", "-vsync", "cfr",
               "-an", "-movflags", "+faststart", str(dst)]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(scene.source),
               *vf, "-map_metadata", "-1", "-q:v", "2", str(dst)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0 or not dst.is_file():
        dst.unlink(missing_ok=True)  # không để file cụt đánh lừa lần nạp sau
        raise RuntimeError(f"Cắt {scene.source.name} [{scene.start:.1f}s] thất bại: "
                           f"{result.stderr[-200:]}")
    return dst, True


def ingest_draft(
    conn: sqlite3.Connection,
    niche: str,
    niche_dir: Path,
    draft_dir: Path,
    taggers: Sequence[VisionTagger],
    on_progress: Optional[Callable[[int, int, Path], None]] = None,
    limit: Optional[int] = None,
    stagger_s: float = 0.0,
    source_class: str = "own",
    topic: str = "",
    retag: bool = False,
    channel: str = "",
) -> IngestResult:
    """Nạp 1 draft nguồn: đọc cảnh -> cắt -> tag song song -> db (resume an toàn).

    limit: chỉ xử lý N cảnh đầu (chạy thử/ngân sách). Chạy lại tự tiếp: clip đã cắt
    không cắt lại, asset đã tag không tag lại (needs_index).
    retag (TCF M2): ÉP tag lại cảnh đã có trong db (hồi tố tag bối cảnh) — clip vẫn
    tái dùng (không cắt lại), upsert đè tag cũ; chạy đúng --source-class như mẻ gốc.
    source_class='viral' (c8 + ytref): rút YouTube ID -> heatmap Most Replayed -> cờ
    điểm nhô + title thật/chapters cho tag; >20s bỏ trừ điểm nhô (6s neo đỉnh);
    10-20s bóp 6s + crop-zoom 112% nướng chết; nhãn viral vào db (gate ở ViralLedger).
    topic (§3i-3): 1 dòng chủ đề editor khai — vào prompt vision cùng bậc source_title.
    channel (VD4 ghi công): kênh nguồn cả mẻ do người nạp khai (--channel, explicit
    thắng); rỗng + viral có YouTube ID -> tự lấy yt-dlp channel TỪNG file nguồn.
    """
    scenes, stats = read_draft_scenes(draft_dir)
    result = IngestResult(scenes=len(scenes), stats=stats)
    if limit is not None:
        scenes = scenes[:limit]
    viral = source_class == "viral"
    yt_infos: dict[str, YTVideoInfo] = {}
    yt_ch_ok: set = set()
    if viral:
        yt_infos, warnings = youtube_infos_for(scenes)  # §3b/§3c — 1 call/video nguồn
        stats["warnings"] = warnings
        # MO_TA_TCF_FILE_NGUON §1: chapter YouTube qua cổng duration (trước khi bóp cảnh)
        yt_ch_ok, ch_warns = yt_chapter_gate(scenes, yt_infos)
        warnings.extend(ch_warns)
        scenes = apply_viral_rules(scenes, stats, yt_infos, warnings)
    # spec TCF §3c — file bối cảnh editor: own = nguồn chính, --topic CLI ĐÈ file
    # (explicit thắng); own thiếu cả 2 -> warning nhắc (luật vận hành mới).
    ctx = read_draft_context(draft_dir)
    warns = stats.setdefault("warnings", [])  # viral đã gán list ở trên -> giữ nguyên
    if topic and ctx.topic and topic.strip() != ctx.topic.strip():
        warns.append(f"--topic CLI đè tiêu đề trong '{CONTEXT_FILE}' (spec TCF §3c)")
    topic = topic or ctx.topic
    if source_class == "own" and not topic:
        warns.append(f"own thiếu chủ đề: không có '{CONTEXT_FILE}' lẫn --topic — "
                     "tag mù chủ đề như cũ (spec TCF §3c)")
    out_dir = niche_dir / INGEST_DIR / draft_dir.name
    folder_path = f"{INGEST_DIR}/{draft_dir.name}"

    # MO_TA_TCF_FILE_NGUON §2: chapter sinh từ voice CHÍNH FILE mẫu — chỉ khi chapter
    # YouTube không dùng được VÀ không có file bối cảnh editor. Lười + memo per source;
    # lỗi gì cũng fail-open hint "" (không chặn mẻ).
    gen_chapters: dict[str, list] = {}

    def _gen_chapters_for(src: str) -> list:
        if src in gen_chapters:
            return gen_chapters[src]
        chs: list = []
        try:
            from autoedit.director.cc_client import ClaudeCodeDirectorClient
            from autoedit.library import tcf_gen as tg
            chs = tg.source_chapters(
                Path(src), niche_dir / "pause_scan_cache",
                lambda: ClaudeCodeDirectorClient(model="sonnet", thinking=False))
        except Exception as exc:
            stats.setdefault("warnings", []).append(
                f"tcf file nguồn {Path(src).name}: {exc} — cảnh nguồn này tag không hint")
        gen_chapters[src] = chs
        return chs

    jobs: list[TagJob] = []
    for scene in scenes:
        try:
            clip, is_new = cut_scene(scene, out_dir, zoom=VIRAL_ZOOM if viral else 0.0)
        except Exception as exc:
            result.failed.append((str(scene.source), str(exc)))
            continue
        result.cut_new += is_new
        result.cut_reused += not is_new
        mtime = clip.stat().st_mtime
        if not retag and not db.needs_index(conn, str(clip), mtime):
            result.skipped_db += 1
            continue
        info = yt_infos.get(str(scene.source))
        # spec TCF §3b — BẪY 2 HỆ QUY CHIẾU: chapter file txt của own tính theo
        # TIMELINE draft (= video đã dựng) -> map bằng target_start; chapter viral
        # (YouTube hoặc file fallback) tính theo FILE NGUỒN -> map bằng scene.start.
        if viral:
            mid_src = scene.start + scene.duration / 2
            src = str(scene.source)
            # cổng MO_TA_TCF_FILE_NGUON: chapter yt chỉ khi duration khớp; hết ctx ->
            # tcf-gen file nguồn (giây FILE THẬT — không bao giờ trượt mốc)
            hint = (_chapter_title(info, mid_src) if src in yt_ch_ok else "") \
                or _chapter_at(ctx.chapters, mid_src)
            if not hint and src not in yt_ch_ok and not ctx.chapters:
                hint = _chapter_at(_gen_chapters_for(src), mid_src)
        else:
            hint = _chapter_at(ctx.chapters,
                               scene.target_start + scene.target_duration / 2)
        jobs.append(TagJob(
            path=clip, mtime=mtime, category=INGEST_DIR, folder_path=folder_path,
            folder_context="",  # tên PROJECT nguồn không phải ground truth ngữ nghĩa
            # 2a (§C6-DIEU-TRA): tiêu đề video nguồn = gợi ý chủ đề (khác folder
            # ground-truth) — chặn GLM đoán Pluto thành "moon". §3i-1: nguồn YouTube
            # dùng tiêu đề THẬT từ yt-dlp (stem tên file tải thường cụt + lẫn mã);
            # còn lại fallback stem y cũ (own: tiêu đề file txt đi ngả `topic`,
            # KHÔNG đè stem — stem stock thường tự mô tả tốt, spec TCF §3a).
            source_title=(info.title if info and info.title else Path(scene.source).stem),
            # §3i-2: chapter chứa điểm GIỮA miếng cắt (sau bóp) — gợi ý về ĐOẠN
            section_hint=hint,
            topic=topic,
            extra={"source_video": str(scene.source), "scene_start": scene.start,
                   "scene_index": scene.index, "has_voice": scene.has_voice,
                   "source_class": source_class,
                   "source_duration": scene.source_duration,
                   # VD4 ghi công: --channel (cả mẻ) thắng; không khai -> kênh YouTube
                   # THẬT từng nguồn (yt-dlp); rỗng thì upsert giữ giá trị cũ (backfill)
                   "source_channel": channel or (info.channel if info else ""),
                   # §3e: chống lặp bug PB7 — cột mới phải chảy tới db ngay tại đây
                   "peak_value": scene.peak_value or None,
                   "peak_type": scene.peak_type or None},
        ))

    indexed, failed = tag_jobs(conn, niche, jobs, taggers,
                               on_progress=on_progress, stagger_s=stagger_s)
    result.indexed.extend(indexed)
    result.failed.extend(failed)
    return result
