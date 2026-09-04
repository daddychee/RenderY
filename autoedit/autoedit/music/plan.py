"""MUSIC SYNC M1 (M-STAGE) — stage `music`: chọn nhạc per-chapter TRƯỚC source/assemble.

Thuật toán chọn bài = `select_music()` NGUYÊN VẸN (đường cũ). Cái mới duy nhất: neo
`start_offset` về accent/downbeat gần nhất quanh offset section cũ, để điểm nhấn đầu
tiên của bài rơi ĐÚNG cắt đầu chương (trừ SNAP_LEAD — ngữ pháp "whoosh vào hit" đo từ
kênh top). Kết quả ghi `project.music_plan`; assemble đọc nguyên, không chọn lại.
Không có plan -> assemble tự chọn như cũ (fallback, đường cũ nguyên vẹn).
Chạy lại CUT -> timeline đổi -> plan STALE, run_cut gọi mark_music_stale() xóa.
MO_TA_VAN_HANH_MUSIC_SYNC.md §1 M-STAGE.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from autoedit.project import (
    MusicPlanEntry,
    Project,
    Stage,
    StageRecord,
    StageStatus,
)

MUSIC_XFADE = 3.0  # giây fade in/out + chồng crossfade ranh giới chương (assembler dùng chung)
# 🔸 MUSIC SYNC (MO_TA §5)
ANCHOR_WIN = 2.0   # cửa sổ neo offset quanh section (± giây) — quá xa thì thà giữ section
SNAP_LEAD = 0.08   # accent rơi SAU cắt ~80ms (kênh top lệch trước beat 120-175ms, knob 0-0.12)
SNAP_TOL = 0.30    # M-ACCENT: mép video cách accent ≤ tol mới trượt (video-only, voice không đụng)
SNAP_CAP = 0.15    # trần tỷ lệ mép được snap (editor thật ~7-14% cắt chủ đích vào accent)
M_CHANGE_WIN = 2.0                 # M-CHANGE: điểm đổi nhạc chương neo vào cut trong ±2s
M_CHANGE_XFADE = {"deepsea": 0.5}  # deepsea đổi gần-thẳng (174 lần đo; fade ngắn chống click);
                                   # niche khác giữ crossfade MUSIC_XFADE (space 4 lần, toàn crossfade)


def change_xfade_for(niche: str | None) -> float:
    """Kiểu chuyển nhạc giữa chương theo niche (chỉ khi music-sync bật)."""
    return M_CHANGE_XFADE.get((niche or "").strip().lower(), MUSIC_XFADE)


def chapters_with_time(project) -> list[dict]:
    """Ghép outline.chapters với dải timeline (từ beats cùng chapter)."""
    chs = (project.outline or {}).get("chapters", [])
    if not chs:
        return []
    rng: dict[int, list] = {}
    for b in project.beats:
        if b.timeline_start is None:
            continue
        s, e = rng.get(b.chapter, [1e9, -1e9])
        rng[b.chapter] = [min(s, b.timeline_start), max(e, b.timeline_end or b.timeline_start)]
    out = []
    for c in chs:
        cid = c.get("chapter_id")
        if cid not in rng:
            continue
        out.append({
            "chapter_id": cid, "mood": c.get("mood", ""), "energy": c.get("energy", "medium"),
            "music_hint": c.get("music_hint", ""),
            "timeline_start": rng[cid][0], "timeline_end": rng[cid][1],
        })
    out.sort(key=lambda c: c["timeline_start"])
    return out


def anchor_offset(offset: float, cut_in_seg: float, track: dict) -> tuple[float, str]:
    """Lượng tử offset về accent/downbeat để điểm nhấn rơi đúng cắt đầu chương.

    cut_in_seg: cắt đầu chương cách đầu segment nhạc bao nhiêu giây (0 chương đầu;
    chương sau = XFADE vì nhạc vào sớm để crossfade). Vị trí trong BÀI tại cắt =
    offset + cut_in_seg -> tìm target trong ±ANCHOR_WIN, dời offset sao cho target
    rơi tại cắt + SNAP_LEAD. Tier A ưu tiên downbeat, hết mới accent; B chỉ accent;
    C (ambient) giữ nguyên — TẮT sync, chạy y đường cũ."""
    tier = track.get("beat_tier") or "C"
    if tier == "C":
        return offset, "tier C: giữ offset section (sync tắt)"
    cand = [("downbeat", track.get("downbeats") or [])] if tier == "A" else []
    cand.append(("accent", track.get("accents") or []))
    want = offset + cut_in_seg
    for kind, ts in cand:
        near = [t for t in ts if abs(t - want) <= ANCHOR_WIN]
        if near:
            t = min(near, key=lambda x: abs(x - want))
            new_off = max(0.0, t - SNAP_LEAD - cut_in_seg)
            return round(new_off, 3), f"{kind} {t:.2f}s -> cắt chương (lead {SNAP_LEAD:.2f}s)"
    return offset, f"tier {tier}: không có mục tiêu trong ±{ANCHOR_WIN:.0f}s — giữ offset section"


def run_music(project: Project, lib_root: Path) -> Project:
    """Stage music: select_music (nguyên vẹn) + neo offset -> project.music_plan.

    Usage đếm Ở ĐÂY khi có plan (assemble dùng plan sẽ KHÔNG đếm nữa — tránh đếm đôi;
    fallback không plan thì assemble đếm như cũ)."""
    from autoedit.music.library import _load_index, load_usage, save_usage
    from autoedit.music.select import select_music

    cut = project.stages.get(Stage.CUT)
    if cut is None or cut.status != StageStatus.DONE:
        raise RuntimeError("Stage cut chưa xong — music cần timeline chương (chạy `autoedit cut` trước).")

    record = StageRecord.running()
    project.stages[Stage.MUSIC] = record
    project.save()
    try:
        index = _load_index(lib_root)
        if not index:
            raise RuntimeError(f"thư viện nhạc rỗng ({lib_root}) — chạy music-import trước.")
        chapters = chapters_with_time(project)
        if not chapters:
            raise RuntimeError("thiếu outline chương / timeline beat — chạy direct + cut trước.")
        usage = load_usage(lib_root)
        picks = select_music(chapters, index, usage=usage)  # thuật toán cũ NGUYÊN VẸN
        if not picks:
            raise RuntimeError("không chọn được nhạc cho chương nào (kiểm mood pool vs outline).")
        pick_by_ch = {p["chapter_id"]: p for p in picks}
        plan: list[MusicPlanEntry] = []
        n_anchor = 0
        for i, ch in enumerate(chapters):
            pick = pick_by_ch.get(ch["chapter_id"])
            if pick is None:
                continue
            # khớp assembler: chương sau vào sớm XFADE (kẹp 0 nếu chương bắt đầu <XFADE)
            cut_in_seg = 0.0 if i == 0 else min(MUSIC_XFADE, ch["timeline_start"])
            off, note = anchor_offset(pick.get("start_offset", 0.0), cut_in_seg, pick["track"])
            if off != pick.get("start_offset", 0.0):
                n_anchor += 1
            plan.append(MusicPlanEntry(
                chapter_id=ch["chapter_id"], file=pick["file"], start_offset=off,
                beat_tier=pick["track"].get("beat_tier") or "C",
                score=pick.get("score", 0.0), anchor_note=note,
            ))
            usage[pick["file"]] = usage.get(pick["file"], 0) + 1
        project.music_plan = plan
        save_usage(lib_root, usage)
        record.warnings.append(
            f"music plan: {len(plan)} chương, {n_anchor} offset neo accent/downbeat — "
            + ", ".join(f"ch{p.chapter_id}:{Path(p.file).stem}[{p.beat_tier}]" for p in plan)
        )
    except Exception as exc:
        record.status = StageStatus.FAILED
        record.error = str(exc)
        project.save()
        raise
    record.status = StageStatus.DONE
    record.completed_at = datetime.now(timezone.utc).isoformat()
    project.save()
    return project


def music_boundaries(chapters: list[dict], edges: list[float],
                     win: float = M_CHANGE_WIN) -> tuple[list[float], list[bool]]:
    """M-CHANGE: điểm đổi nhạc chương i (i>0) neo vào mép cắt VIDEO gần ranh giới
    chương nhất trong ±win — đổi bài trùng chuyển cảnh (deepsea 174 lần đo).
    Trả (boundaries, anchored). Chương 0 luôn boundary = timeline_start (đầu video)."""
    bounds: list[float] = []
    anchored: list[bool] = []
    for i, ch in enumerate(chapters):
        ts = ch["timeline_start"]
        e = min(edges, key=lambda x: abs(x - ts)) if (i > 0 and edges) else None
        if e is not None and abs(e - ts) <= win:
            bounds.append(round(e, 4))
            anchored.append(True)
        else:
            bounds.append(ts)
            anchored.append(False)
    return bounds, anchored


def insert_edges(project: Project) -> dict[int, tuple[float, float]]:
    """NHIP-M3: mép VÀO/RA của mỗi Δ trên timeline, khóa theo after_beat.

    Δ nằm SAU voice + thở + giãn của beat đó (cutter/timeline.py:83) nên mép VÀO =
    timeline_end của SEGMENT chứa beat + breathing + micro (KHÔNG phải beat.timeline_end
    — beat cuối run mới trùng segment). Trả {} khi cut chưa chạy / chưa khai Δ."""
    if not project.inserts or not project.segments:
        return {}
    by_last_beat = {s.beat_ids[-1]: s for s in project.segments if s.beat_ids}
    out: dict[int, tuple[float, float]] = {}
    for ins in project.inserts:
        seg = by_last_beat.get(ins.after_beat)
        if seg is None or seg.timeline_end is None:
            continue                      # Δ khai sau khi cut -> chạy lại cut mới có
        start = seg.timeline_end + seg.breathing_after + seg.micro_pause_after
        out[ins.after_beat] = (round(start, 4), round(start + ins.dur, 4))
    return out


def music_spans(project: Project, chapters: list[dict],
                boundaries: list[float] | None = None,
                total_end: float | None = None) -> list[dict]:
    """NHIP-M3 phương án B: chẻ chương mang Δ-có-nhạc-editor thành 2 NHỊP NHẠC.

    Trước M3 bất biến là "1 chương = 1 bài" (đo thật 14/14 project). M3 phá bất biến
    đó ĐÚNG MỘT CHỖ: Δ mà editor đưa nhạc (`InsertSpec.music`) mở một span mới chạy
    từ mép VÀO Δ tới HẾT CHƯƠNG (user chốt 2026-07-20) — không quay lại bài cũ
    (phương án B; A gây 2 lần chuyển nhạc trong vài chục giây, user đã bác).

    Trả [{chapter_id, file|None, start_offset|None, seg_start, seg_end, is_insert}]
    theo thứ tự timeline. file=None => span dùng bài của music_plan/select như cũ.
    Chương không có Δ-nhạc => đúng 1 span, TỌA ĐỘ Y HỆT đường cũ (hồi quy bằng 0).

    seg_start ở đây là ranh giới NGHE ĐƯỢC (chưa trừ crossfade) — caller lùi XFADE
    khi đặt, y như đường cũ."""
    bounds = boundaries or [c["timeline_start"] for c in chapters]
    edges = insert_edges(project)
    music_by_beat = {i.after_beat: i.music for i in project.inserts if i.music}
    spans: list[dict] = []
    for i, ch in enumerate(chapters):
        lo = bounds[i]
        hi = bounds[i + 1] if i + 1 < len(bounds) else (
            total_end if total_end is not None else float("inf"))
        spans.append({"chapter_id": ch["chapter_id"], "file": None, "start_offset": None,
                      "seg_start": lo, "seg_end": hi, "is_insert": False})
        # Δ có nhạc editor nằm TRONG chương này -> chẻ: bài cũ tới mép vào Δ, bài
        # editor từ đó tới hết chương. Nhiều Δ cùng chương -> Δ sau chẻ tiếp span sau.
        for beat_id, (d_start, _d_end) in sorted(edges.items(), key=lambda kv: kv[1][0]):
            path = music_by_beat.get(beat_id)
            if path is None:
                continue
            cur = spans[-1]
            if not (cur["seg_start"] < d_start < cur["seg_end"]):
                continue                  # Δ không thuộc span đang mở (chương khác)
            cur["seg_end"] = d_start
            spans.append({"chapter_id": ch["chapter_id"], "file": path,
                          "start_offset": 0.0, "seg_start": d_start, "seg_end": hi,
                          "is_insert": True})
    return [s for s in spans if s["seg_end"] - s["seg_start"] > 0.2]


# NHỚ: bung_chu_ky_s ~4 phút đo thật 03/09 (5/5 video Fern/WUFO, 2 thước hội tụ).
# Đây là mắt xích N2 còn treo — nối chu kỳ bùng đã đo vào nhạc: KHÔNG đổi bài (rủi
# ro lệch mood/tone giữa 2 bài), chỉ NHẢY ĐOẠN trong CHÍNH bài đang phát tới
# sections.drop (năng lượng đỉnh, đã có sẵn từ analyze.py) — user chốt 04/09.
def bung_music_spans(spans: list[dict], beats: list, hs, title: str,
                     index_by_file: dict[str, dict]) -> tuple[list[dict], list[str]]:
    """Chèn điểm NHẢY ĐOẠN (không đổi file) vào các span thân/kết tại mốc bùng.

    1 project RenderY = 1 CHƯƠNG file (H/C1../E, title="H"/"C1"...) — KHÔNG map
    chapter_id -> title (mỗi project chỉ có 1 outline-chapter nội bộ, b.chapter
    luôn 0). `title` ở đây là project.title, y hệt cách vung_nhan/S3-HOOK đọc
    (packager/assembler.py:1215) — không suy nhầm thành tên video.

    Mỗi beat bùng (lap_ke_hoach.bung_beat_ids) rơi trong 1 span đang mở -> chẻ
    span đó tại mép ĐẦU vùng bùng; nửa sau nhảy tới track["sections"]["drop"]
    của CHÍNH bài span đó (không có drop -> bỏ qua, giữ nguyên bài phát liên
    tục — thà im còn hơn nhảy về 0.0 tụt năng lượng).
    Chương H (vai_tro_chuong=="hook") không qua đây — N2 chỉ lo thân/kết.
    Trả (spans mới, log dòng cho record.warnings)."""
    from autoedit.nhip.ep import vai_tro_chuong, lap_ke_hoach

    if vai_tro_chuong(title) == "hook":
        return spans, []
    kh = lap_ke_hoach(beats, hs, title=title)
    by_id = {b.beat_id: b for b in beats}
    tho: list[float] = []
    for bid in kh.bung_beat_ids:
        b = by_id.get(bid)
        if b is None or b.timeline_start is None:
            continue
        tho.append(float(b.timeline_start))
    if not tho:
        return spans, []
    tho.sort()
    # bung_beat_ids là 1-2 CỤM liền kề (mở chương + kết chương ~15% mỗi đầu) — gộp
    # theo khoảng cách tới ĐẦU CỤM (không phải mốc liền trước) nên cả cụm chỉ ra
    # 1 điểm nhảy dù trải qua nhiều beat/giây; cụm mới (>90s so gốc cụm) mới mở.
    moc: list[float] = [tho[0]]
    goc_cum = tho[0]
    for t in tho[1:]:
        if t - goc_cum >= 90.0:
            moc.append(t)
            goc_cum = t

    ra: list[dict] = []
    log: list[str] = []
    for sp in spans:
        cac_moc = sorted(m for m in moc if sp["seg_start"] + 20.0 < m < sp["seg_end"] - 5.0)
        cur = dict(sp)
        for m in cac_moc:
            track = index_by_file.get(cur.get("file") or "")
            drop = (track or {}).get("sections", {}).get("drop")
            if not drop:
                continue                      # bài không đo được drop -> bỏ mốc này
            truoc = dict(cur)
            truoc["seg_end"] = m
            ra.append(truoc)
            cur = {**cur, "seg_start": m, "start_offset": float(drop[0]),
                  "is_insert": True, "is_bung": True}
            log.append(f"bùng {m:.0f}s: nhảy '{Path(cur.get('file') or '').stem}' "
                       f"-> drop {drop[0]:.0f}s")
        ra.append(cur)
    return ra, log


def _span_specs(project: Project, chs: list[dict],
                bounds: list[float]) -> tuple[list[dict], dict]:
    """(spans nhạc, {file: InsertSpec}) cho timeline_accents/timeline_beats (M4c).

    Sửa tồn đọng M3 #1: hai hàm chiếu accent/beat trước đây coi chương LIỀN MẠCH một
    bài — chương mang Δ-nhạc-editor thì từ mép Δ tới hết chương bài THẬT là bài editor,
    accent bài kế hoạch trong vùng đó là mốc SAI (M4c có footage trong Δ + vùng sau Δ
    vẫn snap nên thành hại thật). Project không Δ-nhạc -> mỗi chương đúng 1 span tọa
    độ y cũ (hồi quy bằng 0)."""
    spans = music_spans(project, chs, boundaries=bounds)
    specs: dict = {}
    for i in project.inserts:
        if i.music:
            specs.setdefault(i.music, i)
    return spans, specs


def timeline_accents(project: Project, index_rows: list[dict],
                     boundaries: list[float] | None = None) -> list[float]:
    """M-ACCENT: accent của bài ĐANG PHÁT chiếu lên TIMELINE — mục tiêu snap.

    Bất biến từ M1: vị-trí-trong-bài tại ranh giới nghe được của chương i là
    P_i = start_offset + min(XFADE, timeline_start) (assemble giữ P_i kể cả khi
    M-CHANGE dời boundary / đổi xfade niche) -> accent a rơi tại boundary + (a - P_i).
    Pass đầu của bài, KHÔNG unwrap vòng loop (chương dài hơn phần còn lại thì hết
    target — chấp nhận v1). Tier C: không target (sync tắt).
    M4c: đi theo SPAN của music_spans — span Δ-nhạc-editor dùng DOWNBEAT madmom của
    bài editor làm accent (bài vào từ đầu tại mép span, P=0; không downbeat -> vùng đó
    không target, còn hơn target bài cũ đã tắt tiếng)."""
    chs = chapters_with_time(project)
    if not chs or not project.music_plan:
        return []
    by_file = {r.get("file"): r for r in index_rows}
    plan_by = {p.chapter_id: p for p in project.music_plan}
    bounds = boundaries or [c["timeline_start"] for c in chs]
    grid_hook = getattr(project, "music_sync_targets", "accent") == "grid"
    ch_index = {ch["chapter_id"]: (i, ch) for i, ch in enumerate(chs)}
    spans, specs = _span_specs(project, chs, bounds)
    out: list[float] = []
    for sp in spans:
        lo, hi = sp["seg_start"], sp["seg_end"]
        if sp["is_insert"]:
            spec = specs.get(sp["file"])
            if spec is None or (spec.music_tier or "C") == "C":
                continue
            for a in spec.music_downbeats or []:
                t = lo + a
                if lo <= t < hi:
                    out.append(round(t, 4))
            continue
        i, ch = ch_index[sp["chapter_id"]]
        p = plan_by.get(ch["chapter_id"])
        rec = by_file.get(p.file) if p else None
        if not rec or (rec.get("beat_tier") or "C") == "C":
            continue
        src_times = rec.get("accents") or []
        if grid_hook and i == 0:
            # M4 M-GRID (thử nghiệm, mặc định TẮT): hook snap theo DOWNBEAT — chỉ tier A
            # có downbeats; tier B rỗng thì rơi về accent (không chết)
            src_times = rec.get("downbeats") or src_times
        pos_at_bound = p.start_offset + min(MUSIC_XFADE, ch["timeline_start"])
        for a in src_times:
            t = lo + (a - pos_at_bound)
            if lo <= t < hi:
                out.append(round(t, 4))
    return sorted(out)


def timeline_beats(project: Project, index_rows: list[dict],
                   boundaries: list[float] | None = None) -> list[tuple[float, float]]:
    """NHIP-M1 (lưới beat ô thở): beat_times + beat_strength của bài ĐANG PHÁT chiếu
    lên TIMELINE — trả [(t, strength)] sorted. CÙNG bất biến P như `timeline_accents`
    (P_i = start_offset + min(XFADE, timeline_start); không unwrap loop). Tier C bỏ.
    Record cũ thiếu beat_strength / lệch độ dài -> strength 0 cả bài (vẫn cắt được,
    chỉ mất ưu tiên beat mạnh — không chết).
    M4c: theo SPAN như timeline_accents — span Δ dùng music_beats/strength đo lúc khai."""
    chs = chapters_with_time(project)
    if not chs or not project.music_plan:
        return []
    by_file = {r.get("file"): r for r in index_rows}
    plan_by = {p.chapter_id: p for p in project.music_plan}
    bounds = boundaries or [c["timeline_start"] for c in chs]
    ch_index = {ch["chapter_id"]: (i, ch) for i, ch in enumerate(chs)}
    spans, specs = _span_specs(project, chs, bounds)
    out: list[tuple[float, float]] = []
    for sp in spans:
        lo, hi = sp["seg_start"], sp["seg_end"]
        if sp["is_insert"]:
            spec = specs.get(sp["file"])
            if spec is None or (spec.music_tier or "C") == "C":
                continue
            bt = spec.music_beats or []
            st = spec.music_beat_strength or []
            if len(st) != len(bt):
                st = [0.0] * len(bt)
            for b, s in zip(bt, st):
                t = lo + b
                if lo <= t < hi:
                    out.append((round(t, 4), s))
            continue
        _i, ch = ch_index[sp["chapter_id"]]
        p = plan_by.get(ch["chapter_id"])
        rec = by_file.get(p.file) if p else None
        if not rec or (rec.get("beat_tier") or "C") == "C":
            continue
        bt = rec.get("beat_times") or []
        st = rec.get("beat_strength") or []
        if len(st) != len(bt):
            st = [0.0] * len(bt)
        pos_at_bound = p.start_offset + min(MUSIC_XFADE, ch["timeline_start"])
        for b, s in zip(bt, st):
            t = lo + (b - pos_at_bound)
            if lo <= t < hi:
                out.append((round(t, 4), s))
    return sorted(out)


def mark_music_stale(project: Project) -> str | None:
    """CUT chạy lại -> timeline đổi -> plan cũ SAI. run_cut gọi trước khi save.
    Trả message cho record.warnings của cut (None = không có gì để xóa)."""
    had_plan = bool(project.music_plan)
    music = project.stages.get(Stage.MUSIC)
    if not had_plan and (music is None or music.status == StageStatus.PENDING):
        return None
    project.music_plan = []
    project.stages[Stage.MUSIC] = StageRecord()  # về pending
    return "timeline đổi — music_plan cũ đã xóa, chạy lại `autoedit music` nếu dùng music-sync"
