"""tcf-gen — máy tự sinh file 'topic + chapter video.txt' cho draft editor own.

Luồng: voice track (điểm lai seg×duration, y pause_scan; transcript <MIN_WORDS hoặc
transcribe lỗi → tự thử track điểm kế — REAL72/79) → transcribe từng file nguồn
(cache CHUNG pause_scan_cache — pause-dna dùng lại, không tốn 2 lần) → ghép words
theo TIMELINE draft → 1 call NÃO chọn title + ranh chương.

NT4 giữ nguyên: NÃO chỉ CHỌN mốc trong danh sách block [M:SS] cho sẵn (mốc lệch →
snap về block gần nhất); mọi timestamp gốc từ whisper + target_timerange, không bịa.

BẪY draft editor (DS1-050): material `name` ("voi ds 1.mp3") ≠ file trên đĩa
("voi ds 1_TRIM_1.mp3") — resolve theo BASENAME của `path`, không theo `name`.
BẪY 2 (DS-53 v2): path placeholder `##_draftpath_placeholder_<GUID>_##/Resources/local/x.mp3`
— voice KHÔNG nằm trong materials/ → resolve phần path SAU `_##/` về folder draft.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, Optional

from pydantic import BaseModel, Field

from autoedit.library.pause_scan import _resolve_rel, voice_track_candidates

TCF_NAME = "topic + chapter video.txt"
BLOCK_S = 45.0        # gộp transcript thành block ~45s — mốc ứng viên cho ranh chương
MIN_WORDS = 200       # transcript ngắn hơn = nghi không phải voice chính -> lỗi rõ ràng

WordsFn = Callable[[str], Optional[list[dict]]]


class TCFChapter(BaseModel):
    start: str = Field(description="mốc M:SS — PHẢI là một mốc [M:SS] có trong transcript")
    title: str = Field(min_length=1)


class TCFOut(BaseModel):
    title: str = Field(min_length=3, description="tiêu đề video kiểu YouTube, ngôn ngữ của voice")
    chapters: list[TCFChapter] = Field(min_length=2, max_length=15)


SYSTEM = """Bạn nhận transcript một video YouTube dạng các block "[M:SS] text..." (mốc theo timeline video).
Nhiệm vụ: (1) đặt TITLE kiểu YouTube tóm đúng chủ đề video, (2) chia video thành 4-12 CHAPTER theo mạch nội dung.
Luật:
- title và tên chapter viết bằng ĐÚNG NGÔN NGỮ của transcript (transcript tiếng Anh → title/chapter TIẾNG ANH; TUYỆT ĐỐI KHÔNG dịch sang tiếng Việt dù đề bài này viết bằng tiếng Việt).
- start của mỗi chapter PHẢI là một mốc [M:SS] có sẵn trong transcript (chọn block mở đầu ý mới, KHÔNG tự chế mốc).
- chapter đầu tiên start "0:00". Tên chapter ngắn gọn 2-8 từ, mô tả ĐOẠN đó nói về gì.
- KHÔNG chapter nào ngắn hơn 90 giây trừ intro."""


def _mmss(t: float) -> str:
    m, s = divmod(int(round(t)), 60)
    return f"{m}:{s:02d}"


def _parse_mmss(s: str) -> Optional[float]:
    m = re.match(r"^\s*(\d+):(\d{1,2})\s*$", s)
    return int(m.group(1)) * 60 + int(m.group(2)) if m else None


def timeline_blocks(draft_dir: Path, get_words: WordsFn,
                    candidate: int = 0) -> Optional[list[dict]]:
    """Transcript theo TIMELINE: [{start (giây timeline), text}], block ~BLOCK_S giây.

    Words của mỗi segment lấy trong source_timerange file nguồn rồi dời sang
    target_timerange (spec TCF: chapter own tính theo TIMELINE draft).
    candidate = hạng track audio theo điểm lai (0 = cao nhất); vượt số track → None
    (KHÁC [] = track có nhưng toàn nhạc/SFX VAD lọc sạch 0 từ — phải thử track kế)."""
    dc = json.loads((draft_dir / "draft_content.json").read_text(encoding="utf-8"))
    cands = voice_track_candidates(dc)  # mats = path tương đối theo đĩa (bẫy name≠file)
    if candidate >= len(cands):
        return None
    segs, disk = cands[candidate]

    tl_words: list[dict] = []
    for s in segs:
        fname = disk.get(s["material_id"], "")
        ws = get_words(fname) if fname else None
        if not ws:
            continue
        src0 = s["source_timerange"]["start"] / 1e6
        src1 = src0 + s["source_timerange"]["duration"] / 1e6
        tgt0 = s["target_timerange"]["start"] / 1e6
        for w in ws:
            if src0 - 0.05 <= w["start"] < src1 + 0.05:
                tl_words.append({"t": tgt0 + (w["start"] - src0), "text": w["text"]})
    tl_words.sort(key=lambda w: w["t"])

    blocks: list[dict] = []
    for w in tl_words:
        if not blocks or w["t"] - blocks[-1]["start"] >= BLOCK_S:
            blocks.append({"start": w["t"], "texts": []})
        blocks[-1]["texts"].append(w["text"])
    return [{"start": b["start"], "text": " ".join(b["texts"])} for b in blocks]


def _snap_chapters(chapters: list[TCFChapter], allowed: list[float]) -> list[tuple[float, str]]:
    """Mốc NÃO trả → snap về block gần nhất (NT4); chapter đầu ép 0:00; sort + dedupe."""
    out: list[tuple[float, str]] = []
    for c in chapters:
        t = _parse_mmss(c.start)
        if t is None:
            continue
        snapped = min(allowed, key=lambda a: abs(a - t))
        if abs(snapped - t) > BLOCK_S:  # lệch quá 1 block = mốc bịa -> bỏ
            continue
        out.append((snapped, c.title.strip()))
    out.sort(key=lambda x: x[0])
    dedup: list[tuple[float, str]] = []
    for t, title in out:
        if not dedup or t - dedup[-1][0] >= 1.0:
            dedup.append((t, title))
    if dedup:
        dedup[0] = (0.0, dedup[0][1])  # chapter đầu luôn 0:00 (chuẩn YouTube/ingest)
    return dedup


def render_tcf(title: str, chapters: list[tuple[float, str]]) -> str:
    """Format đúng parser ingest.py: dòng trước chapter đầu = topic, dòng 'M:SS Tên'."""
    lines = [title.strip(), ""]
    lines += [f"{_mmss(t)} {name}" for t, name in chapters]
    return "\n".join(lines) + "\n"


def source_blocks(words: list[dict]) -> list[dict]:
    """Words thô (giây FILE) -> block ~BLOCK_S: [{start, text}] (mode FILE NGUỒN)."""
    blocks: list[dict] = []
    for w in sorted(words, key=lambda x: x["start"]):
        if not blocks or w["start"] - blocks[-1]["start"] >= BLOCK_S:
            blocks.append({"start": w["start"], "texts": []})
        blocks[-1]["texts"].append(w["text"])
    return [{"start": b["start"], "text": " ".join(b["texts"])} for b in blocks]


def source_chapters(media_path: Path, cache_dir: Path, client_factory,
                    language: str = "en", echo=lambda s: None) -> list[dict]:
    """Mode FILE NGUỒN (MO_TA_VAN_HANH_TCF_FILE_NGUON.md — chốt 2026-07-13): chapter
    theo GIÂY FILE cho video mẫu/viral khi chapter YouTube không dùng được (mất link /
    duration lệch >3% = mốc trượt vì editor cắt bỏ đoạn).

    Trả [{start_time, end_time, title}] — ĐÚNG khuôn YTVideoInfo.chapters để
    `ingest._chapter_at` đọc thẳng. Cache 2 tầng bền trong pause_scan_cache
    (SRC__<file>.words.json + SRC__<file>.tcf.json) -> re-ingest/retag 0 call.
    client_factory: tạo NÃO LƯỜI — cache hit thì không import claude."""
    from autoedit.library.pause_scan import sanitize

    cache_dir.mkdir(parents=True, exist_ok=True)
    key = sanitize(media_path.name)
    done = cache_dir / f"SRC__{key}.tcf.json"
    if done.exists():
        return json.loads(done.read_text(encoding="utf-8"))["chapters"]

    wcache = cache_dir / f"SRC__{key}.words.json"
    if wcache.exists():
        words = json.loads(wcache.read_text(encoding="utf-8"))
    else:
        from autoedit.align.whisper_local import FasterWhisperAligner
        ws = FasterWhisperAligner(model_size="small", language=language).transcribe(media_path)
        words = [{"text": w.text, "start": w.start, "end": w.end} for w in ws]
        wcache.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")

    blocks = source_blocks(words)
    n_words = sum(len(b["text"].split()) for b in blocks)
    echo(f"  tcf file nguồn {media_path.name}: {len(blocks)} block, {n_words} từ")
    if n_words < MIN_WORDS:
        raise RuntimeError(f"{media_path.name}: transcript {n_words} từ (<{MIN_WORDS}) — "
                           "video ít lời, không sinh chapter mù")
    user = "\n".join(f"[{_mmss(b['start'])}] {b['text']}" for b in blocks)
    parsed, _usage = client_factory().complete(SYSTEM, user, TCFOut)
    snapped = _snap_chapters(parsed.chapters, [b["start"] for b in blocks])
    if len(snapped) < 2:
        raise RuntimeError(f"{media_path.name}: mốc NÃO bịa quá nhiều — sau snap còn "
                           f"{len(snapped)} chapter")
    chapters = [{"start_time": t, "end_time": None, "title": name} for t, name in snapped]
    for a, b in zip(chapters, chapters[1:]):
        a["end_time"] = b["start_time"]
    done.write_text(json.dumps({"title": parsed.title, "chapters": chapters},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    return chapters


def generate_tcf(draft_dir: Path, client, get_words: WordsFn,
                 force: bool = False, echo=lambda s: None) -> tuple[Path, str]:
    """Sinh file TCF cho 1 draft. Trả (path, status: fresh|skip). Draft nguồn chỉ
    được ghi THÊM đúng file TCF này, không đụng gì khác (P3)."""
    out = draft_dir / TCF_NAME
    if out.exists() and not force:
        return out, "skip"

    # Thử LẦN LƯỢT mọi track audio theo điểm lai: track cao nhất có thể là nhạc trải dài
    # (REAL79) hoặc file hỏng transcribe nổ (REAL72 avcodec) — fail rõ mới sang track kế.
    # BUG EX247 2026-07-18: voice trong .mp4 ÍT-cắt (2 seg) tụt hạng dưới nhạc nhiều-seg;
    # track nhạc VAD lọc sạch -> 0 từ -> [] -> KHÔNG được thoát vòng (khác None = hết track).
    blocks: list[dict] = []
    best_words = 0
    cand = 0
    while True:
        try:
            cand_blocks = timeline_blocks(draft_dir, get_words, candidate=cand)
        except Exception as exc:
            echo(f"  track#{cand} transcribe lỗi: {exc} — thử track kế")
            cand += 1
            continue
        if cand_blocks is None:  # đã hết track audio (KHÁC [] = track nhạc 0 từ)
            break
        n_words = sum(len(b["text"].split()) for b in cand_blocks)
        if cand_blocks:  # track có từ mới đáng in (track nhạc rỗng: im lặng thử kế)
            suffix = f" (track hạng {cand})" if cand else ""
            echo(f"  transcript{suffix}: {len(cand_blocks)} block, {n_words} từ, "
                 f"dài {_mmss(cand_blocks[-1]['start'])}")
        if n_words >= MIN_WORDS:
            blocks = cand_blocks
            break
        best_words = max(best_words, n_words)
        cand += 1
    if not blocks:
        raise RuntimeError(
            f"transcript chỉ {best_words} từ (<{MIN_WORDS}) sau khi thử các track audio "
            f"— nghi thiếu file voice, KHÔNG sinh TCF mù")

    user = "\n".join(f"[{_mmss(b['start'])}] {b['text']}" for b in blocks)
    parsed, usage = client.complete(SYSTEM, user, TCFOut)

    chapters = _snap_chapters(parsed.chapters, [b["start"] for b in blocks])
    if len(chapters) < 2:
        raise RuntimeError(f"NÃO trả {len(parsed.chapters)} chapter nhưng sau snap chỉ "
                           f"còn {len(chapters)} — mốc bịa quá nhiều, xem lại transcript")
    out.write_text(render_tcf(parsed.title, chapters), encoding="utf-8")
    return out, "fresh"
