"""Shot thở — footage riêng phủ ô thở hết ý/cuối chương (MO_TA_VAN_HANH_SHOT_THO.md).

Chọn MÁY THUẦN 0 call NÃO. 3.0 (user chốt 2026-07-13, §7): LIÊN TỤC CHỦ THỂ — shot thở
TIẾP TỤC chủ thể của clip liền trước ô (đang chiếu cá mập -> vẫn cá mập), ĐỔI CỠ CẢNH
cho đỡ nhàm. Đo bằng token subject/tags kho, demote token nền niche theo tần suất pool
(deepsea: underwater/ocean...); mood chỉ còn phụ trợ; BỎ bonus wide/aerial (proxy "đắt"
cũ — chính là nguồn nhặt sai chủ thể ở SP1 + DS5-083: sói tuyết -> tiểu hành tinh).
Chỉ CỘNG ĐIỂM, không đẻ cửa loại mới (filter-overload-guard); loại duy nhất = P7
đã-dùng-trong-video. Pick hụt ô nào -> không có record -> assemble tự về hành vi cũ
(giữ hình + J-cut), không bao giờ hở hình.

2.0 (§6): ô đã được cut kéo sâu (footage 4-10s). Mỗi ô 1-3 MIẾNG footage: k chọn theo
ngưỡng DNA + seed crc32(project_id:beat_id) (KHÔNG hash() builtin — bị salt mỗi lần
chạy); MỌI miếng cùng neo chủ thể của ô (3.0 — chuỗi-mood-nối cũ làm miếng 2/3 trôi
chủ thể); cỡ cảnh so với miếng liền trước. Pick hụt giữa chừng -> miếng cuối đã pick
tự phủ dài ra (coverage), không bao giờ hở.
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import zlib
from collections import Counter
from pathlib import Path
from typing import Callable, Optional

from autoedit.cutter.pause import load_breath_dna
from autoedit.library import db
from autoedit.library.db import _VOCAB_STOPWORDS
from autoedit.packager.coverage import BREATH_SHOT_HOLD, breath_shot_beat_ids
from autoedit.project import BreathShot, Project, ShotPick, slugify
from autoedit.sourcer import usage
from autoedit.sourcer.local import _blob, _row_to_candidate, passes_geo

SUBJ_W = 3.0    # /token chủ thể trùng clip liền trước (trần SUBJ_CAP) — luật 1 MỚI user 2026-07-13
SIZE_W = 2.0    # khác cỡ cảnh miếng liền trước (luật 2 — đổi cỡ cho đỡ nhàm); trùng/thiếu tag = 0, vẫn chọn được
DUR_W = 1.5    # đủ dài phủ phần ô còn lại (thiếu -> slow-mo fallback sẵn của assembler)
MOOD_W = 0.5    # /tag trùng (max 2 = 1,0) — 3.0 hạ từ chủ đạo 2,0 xuống phụ trợ
UNUSED_W = 0.5  # P7 mềm: chưa dùng trên kênh
SUBJ_CAP = 3          # trần token chủ thể tính điểm (3×3,0 = 9,0 — chủ đạo tuyệt đối)
GENERIC_DF = 0.25     # token có mặt >25% pool = từ nền niche, khớp nó không nói "cùng chủ thể"
GENERIC_MIN_POOL = 40  # pool nhỏ hơn -> thống kê tần suất vô nghĩa, không demote


def _mood_set(raw: str) -> set[str]:
    """'epic, mysterious' (tag db) hoặc mood tự do của beat -> set từ vocab 19 từ.
    Tách cả '_'/'/' — director hay trả mood ghép 'awe_urgent_cautionary' (DS5-083),
    trước đây cả chuỗi không dịch được -> tiêu chí mood câm toàn video.
    Từ lạ không dịch được -> bỏ (fail-open: tiêu chí mood im lặng, tiêu chí khác gánh)."""
    from autoedit.music.library import MOOD
    from autoedit.music.select import _MOOD_SYNONYMS

    out: set[str] = set()
    for m in re.split(r"[,_/]+", raw):
        m = m.strip().lower()
        if m in MOOD:
            out.add(m)
        elif m in _MOOD_SYNONYMS:
            out.add(sorted(_MOOD_SYNONYMS[m])[0])
    return out


def _subject_tokens(*texts: str) -> set[str]:
    """Token chủ thể từ subject/tags kho hoặc visual_concept beat: thường hóa, bỏ
    stopword + từ <3 ký tự. Tag cụm ('sperm whale') tách từng từ — 'whale' phía neo
    vẫn khớp."""
    out: set[str] = set()
    for text in texts:
        for w in re.split(r"[^a-z0-9]+", str(text).lower()):
            if len(w) >= 3 and w not in _VOCAB_STOPWORDS:
                out.add(w)
    return out


def _generic_tokens(token_sets: list[set[str]]) -> set[str]:
    """Token nền của cả niche = có mặt ở > GENERIC_DF pool (deepsea: underwater 72%,
    ocean 64%, marine 71%...) — đo từ pool thật nên tự thích nghi mọi niche, không
    hardcode danh sách. Pool < GENERIC_MIN_POOL -> trả rỗng (thống kê vô nghĩa)."""
    if len(token_sets) < GENERIC_MIN_POOL:
        return set()
    df: Counter = Counter()
    for ts in token_sets:
        df.update(ts)
    cut = GENERIC_DF * len(token_sets)
    return {t for t, c in df.items() if c > cut}


def _score(cand: dict, need_dur: float, anchor: set[str], prev_moods: set[str],
           prev_size: str, times_used: Optional[Callable[[str], int]],
           generic: set[str]) -> float:
    hits = ((cand.get("_tokens") or set()) & anchor) - generic
    s = SUBJ_W * min(SUBJ_CAP, len(hits))
    size = (cand.get("shot_size") or "").strip()
    if size and prev_size and size != prev_size:
        s += SIZE_W
    s += MOOD_W * len(prev_moods & _mood_set(cand.get("mood", "")))
    if float(cand.get("duration") or 0) >= need_dur:
        s += DUR_W
    if times_used is not None and times_used(cand["asset_key"]) == 0:
        s += UNUSED_W
    return s


def _pieces(footage: float, seed_key: str, pool_max_dur: float, bdna: dict) -> list[float]:
    """Chia phần footage của ô thành 1-3 miếng (GIÂY, miếng đầu dài nhất — mẫu editor).

    k theo ngưỡng DNA + seed định trước (đa dạng giữa các ô nhưng chạy lại y kết quả).
    Guard: k=1 mà pool không clip nào đủ dài -> nâng k (né slow-mo giãn quá xấu).
    """
    t1, t2 = bdna["k_thresholds"]
    if footage < t1:
        allowed = [1]
    elif footage < t2:
        allowed = [1, 2]
    else:
        allowed = [1, 2, 3]
    k = allowed[zlib.crc32(seed_key.encode("utf-8")) % len(allowed)]
    if k == 1 and len(allowed) > 1 and pool_max_dur < footage - 0.5:
        k = 2
    if k == 1:
        return [round(footage, 2)]
    fracs = bdna["k_fractions"][k]
    durs = [round(footage * f, 2) for f in fracs[:-1]]
    durs.append(round(footage - sum(durs), 2))  # miếng cuối = phần còn lại, tổng khít
    return durs


def _beat_map(project: Project) -> list[tuple[float, float]]:
    """NHIP-M1: beat nhạc trên hệ TIMELINE [(t, strength)] — chỉ khi music-sync bật
    (có music_plan). Boundary DỰ ĐOÁN = timeline_start chương; M-CHANGE ở assemble có
    thể dời ≤2s -> retime_breath_grid tính LẠI trên boundary thật (số miếng giữ nguyên).
    Fail-open: lỗi gì (index thiếu, pool khác --music-lib tay...) -> [] = đường DNA cũ."""
    if not project.music_plan:
        return []
    try:
        from autoedit.music.library import _load_index, music_root_for
        from autoedit.music.plan import timeline_beats

        return timeline_beats(project, _load_index(music_root_for(project.niche)))
    except Exception:
        return []


def _anchor_tags(pick: Optional[ShotPick], conn: sqlite3.Connection,
                 beat) -> tuple[set[str], set[str], str]:
    """CHỦ THỂ + mood + cỡ cảnh của clip LIỀN TRƯỚC ô = clip cuối cửa sổ beat mang ô
    (extra_shots[-1] nếu multi-shot). Clip local -> tra db theo path (kể cả ảnh/viral —
    cái ĐANG CHIẾU là cái cần nối, không giới hạn trong pool); clip stock/entity/gen
    không tag -> nghĩa beat (visual_concept = mô tả cái NÃO đặt lên màn hình = proxy
    chủ thể sát nhất; beat.mood/shot_size như cũ)."""
    key = ""
    if pick is not None:
        key = pick.extra_shots[-1].asset_key if pick.extra_shots else pick.asset_key
    if key.startswith("local:"):
        row = conn.execute(
            "SELECT subject, tags, mood, shot_size FROM library_assets WHERE path = ?",
            (key[len("local:"):],),
        ).fetchone()
        if row is not None:
            tags = " ".join(str(t) for t in json.loads(row["tags"] or "[]"))
            return (_subject_tokens(row["subject"], tags),
                    _mood_set(row["mood"] or ""), (row["shot_size"] or ""))
    return (_subject_tokens(beat.visual_concept or ""),
            _mood_set(beat.mood or ""), (beat.shot_size or ""))


def pick_breath_shots(project: Project, conn: sqlite3.Connection,
                      used_in_video: set[str], assets_dir: Path,
                      record) -> list[BreathShot]:
    """Chọn shot thở cho MỌI ô đạt ngưỡng (chốt 1: 100%) — chạy SAU khi mọi beat có
    clip (chủ thể clip liền trước đã biết; used_in_video đầy đủ -> không cắt sang chính
    clip hàng xóm). Copy asset vào assets/, ghi usage kênh, trả list BreathShot."""
    ids = breath_shot_beat_ids(project.beats)
    if not ids or not project.niche:
        return []
    script_blob = _blob(project.inputs.script_text or "")
    pool: list[dict] = []
    for row in db.videos_for_niche(conn, project.niche):
        if not Path(row["path"]).is_file():
            continue
        # geo-gate PA2 như phễu: shot thở sai quốc gia còn chối hơn shot thoại sai
        if script_blob and not passes_geo(row.get("folder_path", ""), script_blob):
            continue
        cand = _row_to_candidate(row)
        cand["_tokens"] = _subject_tokens(row["subject"],
                                          " ".join(str(t) for t in row["tags"]))
        pool.append(cand)
    if not pool:
        record.warnings.append("shot thở: pool local rỗng — mọi ô giữ hành vi cũ (giữ hình + J-cut)")
        return []
    generic = _generic_tokens([c["_tokens"] for c in pool])

    channel = project.inputs.channel or ""
    times_used = (lambda k: usage.times_used(conn, channel, k)) if channel else None
    shots_by_beat = {s.beat_id: s for s in project.shots}
    project_dir = Path(project.project_dir)
    bdna = load_breath_dna(project.niche)
    beat_map = _beat_map(project)  # NHIP-M1: rỗng khi music-sync tắt/tier C/lỗi -> DNA
    min_piece = float(bdna.get("min_piece", 1.5))
    out: list[BreathShot] = []
    for beat in project.beats:
        if beat.beat_id not in ids:
            continue
        # neo CỐ ĐỊNH cho cả ô (mọi miếng cùng chủ thể/mood); chỉ cỡ cảnh chuỗi theo miếng
        anchor, anchor_moods, prev_size = _anchor_tags(
            shots_by_beat.get(beat.beat_id), conn, beat)
        footage = beat.breathing_after - BREATH_SHOT_HOLD
        pool_max = max((float(c.get("duration") or 0) for c in pool
                        if c["asset_key"] not in used_in_video), default=0.0)
        # NHIP-M1: vùng footage của ô = [timeline_end + HOLD, timeline_end + breathing]
        # (beat mang ô luôn cuối segment, micro=0 — plan_micro_pauses không chọn beat có
        # breathing). ≥2 beat nhạc trong vùng -> lưới beat, TRẦN 3 MIẾNG KHÔNG áp
        # (user chốt 2026-07-19); không thì đường DNA cũ nguyên vẹn.
        beat_cut = False
        zone = (beat.timeline_end or 0.0) + BREATH_SHOT_HOLD
        local = [(t - zone, s) for t, s in beat_map if zone < t < zone + footage]
        if len(local) >= 2:
            from autoedit.music.minihook import breath_pieces

            durs = breath_pieces(footage, [t for t, _ in local],
                                 [s for _, s in local], min_piece=min_piece)
            beat_cut = True
        else:
            durs = _pieces(footage, f"{project.project_id}:{beat.beat_id}", pool_max, bdna)
        for i, need in enumerate(durs):
            best: Optional[dict] = None
            best_s = -1.0
            for c in pool:  # pool đã sort ổn định (approved/indexed_at) -> hòa điểm lấy đầu
                if c["asset_key"] in used_in_video:
                    continue  # P7 — luật cứng duy nhất
                s = _score(c, need, anchor, anchor_moods, prev_size, times_used, generic)
                if s > best_s:
                    best, best_s = c, s
            if best is None:
                record.warnings.append(
                    f"beat {beat.beat_id}: shot thở miếng {i + 1}/{len(durs)} pick hụt "
                    "(pool cạn) — " + ("miếng trước phủ dài ra" if i else "ô giữ hành vi cũ"))
                break
            src = Path(best["path"])
            dest = assets_dir / (f"b{beat.beat_id:03d}_breath{i + 1}_"
                                 f"{slugify(src.stem)[:32]}{src.suffix.lower()}")
            shutil.copy2(src, dest)
            used_in_video.add(best["asset_key"])
            if channel:
                usage.log_usage(conn, channel, best["asset_key"], project.project_id)
            subj_hit = "+".join(sorted((best["_tokens"] & anchor) - generic)[:SUBJ_CAP]) or "—"
            moods_hit = "+".join(sorted(anchor_moods & _mood_set(best.get("mood", "")))) or "—"
            out.append(BreathShot(
                beat_id=beat.beat_id, asset_path=str(dest.relative_to(project_dir)),
                asset_key=best["asset_key"], dur=need, beat_cut=beat_cut,
                source_channel=best.get("source_channel") or "",
                note=(f"miếng {i + 1}/{len(durs)}"
                      + (" [lưới beat]" if beat_cut else "")
                      + f" {need:.1f}s · chủ thể {subj_hit} · "
                      f"mood {moods_hit} · cỡ {prev_size or '?'}→{best.get('shot_size') or '?'}"
                      f" · clip {float(best.get('duration') or 0):.1f}s, ô {beat.breathing_after:.1f}s"),
            ))
            # miếng kế: neo chủ thể/mood GIỮ NGUYÊN, chỉ cỡ cảnh so với miếng vừa đặt
            prev_size = (best.get("shot_size") or "").strip() or prev_size
    return out
