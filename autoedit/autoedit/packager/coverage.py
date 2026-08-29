"""Cửa sổ phủ footage L1 — footage phải PHỦ KÍN timeline (PRD 3.2), kể cả hình thở
và khoảng lead-silence đầu segment (sinh ra từ fix khởi âm M4).

Pure functions — test bất biến: liền mạch, không hở, không đè.
"""

from __future__ import annotations

from dataclasses import dataclass

from autoedit.project import Beat, VoiceSegment

# F5 shot_count: sàn thời lượng 1 shot con — chặn cắt vụn không xem kịp. Cũng là mẫu số
# kẹp N ở sourcer (beat ngắn → ít shot). Khởi điểm 0.7s, chỉnh theo cổng mắt.
MIN_SHOT_DUR = 0.7


def split_window(start: float, end: float, n: int, tail: float = 0.0) -> list[tuple[float, float]]:
    """Chia cửa sổ [start, end] thành n khoảng con ĐỀU, liền khít.

    Mép con dùng CHUNG một giá trị float (boundary[k] = start + k*(end-start)/n) nên khi
    assembler round(mép*SEC) thì mép con sau == mép con trước trong không gian microsecond
    → không hở/đè (đúng bài học SegmentOverlap). n<=1 → nguyên cửa sổ.

    tail = ô thở cuối cửa sổ: KHÔNG chia vào đó — chỉ chia đều phần THOẠI
    [start, end-tail], khoảng con cuối kéo dài phủ trọn tail (d2: ô thở = 1 hình giữ,
    nhát cắt không được rơi giữa im lặng — rà chồng chéo 2026-07-04 #1).
    """
    if n <= 1:
        return [(start, end)]
    speech_end = end - tail
    if speech_end <= start:  # tail nuốt cả cửa sổ (không xảy ra sau kẹp N ở sourcer) — chia cả
        speech_end = end
    step = (speech_end - start) / n
    bounds = [start + k * step for k in range(n)] + [end]
    return [(bounds[k], bounds[k + 1]) for k in range(n)]


@dataclass
class CoverWindow:
    """Khoảng timeline mà footage của beat này phải phủ."""

    beat_id: int
    start: float
    end: float
    breathing_dur: float = 0.0  # GIÂY hình thở cuối cửa sổ (0 = không) — multi-shot không chia vào đây
    micro_dur: float = 0.0      # GIÂY giãn nghỉ máy cuối cửa sổ (hình thở 2.0) — nhỏ, không J-cut
    breath_shot: bool = False   # cửa sổ LÀ shot thở riêng (MO_TA_SHOT_THO §2b) — 1 clip, không J-cut
    j_cut_start: bool = False   # mép VÀO cửa sổ là J-cut (apply_j_cuts đánh dấu) — body miễn snap
    insert: bool = False        # NHIP-M2: cửa sổ LÀ đoạn chèn Δ editor khai (M2: slug giữ chỗ)

    @property
    def is_breathing_tail(self) -> bool:
        """Phần cuối có chứa hình thở (M6+ có thể đổi shot đẹp)."""
        return self.breathing_dur > 0

    @property
    def tail_dur(self) -> float:
        """Tổng phần KHÔNG-THOẠI cuối cửa sổ (thở + giãn nghỉ) — multi-shot không chia vào đây."""
        return self.breathing_dur + self.micro_dur

    @property
    def duration(self) -> float:
        return self.end - self.start


def coverage_windows(beats: list[Beat], segments: list[VoiceSegment]) -> list[CoverWindow]:
    """Chia timeline thành cửa sổ phủ theo beat.

    Trong mỗi segment: beat đầu phủ từ mép segment (nuốt lead-silence),
    beat cuối phủ tới mép segment + hình thở sau nó. Giữa các beat: ranh giới
    là timeline_start của beat kế (cut on word).
    """
    by_id = {b.beat_id: b for b in beats}
    windows: list[CoverWindow] = []
    for seg in segments:
        seg_beats = [by_id[bid] for bid in seg.beat_ids]
        for i, beat in enumerate(seg_beats):
            if beat.timeline_start is None or beat.timeline_end is None:
                raise ValueError(f"beat {beat.beat_id} chưa có timeline (chạy cut trước)")
            start = seg.timeline_start if i == 0 else beat.timeline_start
            if i < len(seg_beats) - 1:
                nxt = seg_beats[i + 1]
                end = nxt.timeline_start
                breathing = micro = 0.0
            else:
                micro = getattr(seg, "micro_pause_after", 0.0)
                end = seg.timeline_end + seg.breathing_after + micro
                breathing = seg.breathing_after
            windows.append(
                CoverWindow(beat_id=beat.beat_id, start=round(start, 4),
                            end=round(end, 4), breathing_dur=round(breathing, 4),
                            micro_dur=round(micro, 4))
            )
        # NHIP-M2: đoạn chèn Δ = cửa sổ RIÊNG sau thở+giãn của segment (không phải ô
        # thở — breath/J-cut/snap không đụng). beat_id = beat cuối segment (truy vết).
        ins = getattr(seg, "insert_after", 0.0)
        if ins > 0:
            w = windows[-1]
            windows.append(CoverWindow(beat_id=w.beat_id, start=w.end,
                                       end=round(w.end + ins, 4), insert=True))
    return windows


# --- Shot thở (MO_TA_VAN_HANH_SHOT_THO.md) -----------------------------------------
# DNA 3 project: ~25% ô (ô sâu / cuối chương) editor giữ hình cũ 0,4-0,9s rồi CẮT sang
# footage khác chạy im lặng tới khi voice vào. LUẬT LẬT có chủ đích của rà 2026-07-04 #1
# ("nhát cắt không rơi giữa im lặng") TẠI Ô ĐẠT NGƯỠNG — nhát cắt ở hết-voice+HOLD là
# chủ đích theo DNA, không phải chia đều vô thức; ô dưới ngưỡng luật cũ vẫn giữ.
BREATH_SHOT_MIN = 2.5          # ô thở >= 2,5s ở bất kỳ đâu
BREATH_SHOT_MIN_CHAPTER = 1.5  # ô cuối chương (beat kế thuộc chương khác)
BREATH_SHOT_HOLD = 0.5         # giây giữ hình cũ trước khi cắt sang shot thở


# --- NHIP-M4: lưới beat trong đoạn chèn Δ -------------------------------------------
# Δ là vùng KHÔNG VOICE -> nhịp nhạc quyết 100% mép cắt (luật đứng BAN_GIAO §1, không
# đụng vùng có voice). Nhắm theo GIÂY rồi quy ngược ra số beat — bài học đo 4 bài
# 2026-07-19: đếm theo SỐ BEAT cố định thì shot co giãn gần 2× giữa nhạc nhanh và chậm
# (89 BPM: 8 beat = 5,4s vs 172 BPM: 8 beat = 2,8s), tai người cảm nhận shot theo GIÂY.
# Δ nhắm 2,0s/hình — USER CHỐT 2026-07-20 sau khi nghe draft V9 ("nhịp dựng nhanh").
# 📌 LỆCH SO VỚI M1 (ô thở dùng 3,0s = p50 246 miếng thở editor thật): Δ là montage
# CHỦ ĐÍCH của editor trên nhạc dồn dập, không phải ô thở giữa hai câu nói — nhịp
# nhanh hơn là ý đồ, không phải lệch chuẩn.
INSERT_TARGET_SHOT = 2.0
INSERT_MIN_SHOT = 1.5          # sàn miếng — bằng min_piece DNA ô thở (M1)
# Bán kính hạ cánh beat mạnh — Δ dùng 0 (TẮT), khác mini-hook/M1 (±2).
# 📌 LỆCH SO VỚI BẢN GỐC (mini-hook §5a): hạ-cánh-beat-mạnh ±2 quanh mốc k CHỐNG LẠI
# lưới đều khi chu kỳ nhịp mạnh không chia hết cho k (đo "End of an Era" 89 BPM:
# ±2 -> kc beat 6,6,3,6,3,3 = shot 2,0s/4,0s chênh 2,53×; ±1 -> vẫn chênh 2,00×).
# Nay KHÔNG cần tìm bù nữa vì `_meter_k` chọn thẳng k = bội số của CHU KỲ NHỊP MẠNH
# -> mốc tự rơi beat mạnh mà lưới vẫn đều. Giữ 0 để không phá lại nhịp đều.
INSERT_SEARCH_BEATS = 0
# Chu kỳ nhịp mạnh tối đa xét (2..8 beat = 1 ô nhịp thường gặp: 2/4, 3/4, 4/4, 6/8).
INSERT_METER_MAX = 8

# A′ SHUFFLE RUN+HOLD (foundation e2 §5, user gật 2026-07-21) — craft editor giỏi:
# "pattern trước, phá sau, trả thưởng" — CHUỖI hình ngắn (RUN) + hình giữ lâu THƯA
# (HOLD) làm điểm nhấn; mở và KẾT Δ đều bằng RUN ("fast to enter, fast to release").
# Độ dài run theo pace (min, max — số hình 1-unit liên tiếp giữa hai hold):
INSERT_PACE_RUNS = {"fast": (3, 5), "medium": (2, 4), "slow": (2, 3)}


def _shaped_pattern(units: int, rng, pace: str = "medium",
                    group_units: int = 4) -> list[int]:
    """Chuỗi số-unit của từng shot (1=RUN, 2|3=HOLD), tổng ĐÚNG `units`.

    Ngữ pháp A′ (nguồn craft ghi ở foundation e2 §5): mở bằng RUN ≥2 · HOLD=2 unit
    (1 lần được 3 unit nếu Δ đủ dài — điểm nhấn hiếm) · giữa hai HOLD luôn ≥2 RUN ·
    kết bằng RUN ≥2 (siết nhịp dồn về lúc voice quay lại) · HOLD ưu tiên rơi ĐẦU nhóm
    `group_units` (~đầu câu nhạc 4 ô nhịp, đệm thêm ≤2 RUN để tới ranh giới).
    `rng` = random.Random(seed cố định) -> cùng project dựng lại Y HỆT (NT5)."""
    lo, hi = INSERT_PACE_RUNS.get(pace, INSERT_PACE_RUNS["medium"])
    out: list[int] = []
    pos, remaining = 0, units
    big_left = 1 if units >= 12 else 0
    while remaining > 0:
        run = min(rng.randint(lo, hi), remaining)
        out += [1] * run
        pos += run
        remaining -= run
        if remaining < 4:              # hết chỗ cho hold + 2 RUN kết -> RUN nốt
            out += [1] * remaining
            break
        hold = 3 if big_left and remaining >= 5 and rng.random() < 0.25 else 2
        off = (-pos) % group_units     # đệm RUN tới đầu nhóm 4 bar nếu chỉ lệch ≤2
        if 0 < off <= 2 and remaining - off >= hold + 2:
            out += [1] * off
            pos += off
            remaining -= off
        if hold == 3:
            big_left = 0
        out.append(hold)
        pos += hold
        remaining -= hold
    return out


def _meter_k(strength: list[float], period: float, target: float) -> int:
    """Số beat/hình = BỘI SỐ của chu kỳ nhịp mạnh, gần `target` giây nhất.

    🐛 Bug user nghe 2026-07-20 (draft V9): ép k = round(target/period) cho ra k=4
    trên bài nhịp 3 -> lưới LỆCH PHA với nhịp mạnh, 3/10 nhát cắt rơi beat YẾU
    (strength 0,18-0,22 vs trung vị 0,29) -> tai nghe "không khớp nhạc". Đúng lớp lỗi
    b08/b09: cắt vào beat yếu kề beat mạnh bị cảm nhận là TRỄ MỘT NHỊP.

    Cách đo: với mỗi chu kỳ m, thử mọi pha, lấy strength trung bình cao nhất — chu kỳ
    nào cho điểm cao nhất là nhịp thật của bài (đo "End of an Era": m=3 và m=6 đạt
    0,458-0,460 vs m=4 chỉ 0,364). Rồi lấy bội số của m gần `target` nhất.
    Không có strength (record cũ) -> về công thức cũ round(target/period)."""
    if not strength or period <= 0:
        return max(2, round(target / period))
    n = len(strength)
    scores: dict[int, float] = {}
    for m in range(2, min(INSERT_METER_MAX, max(2, n // 3)) + 1):
        best = -1.0
        for phase in range(m):
            vals = [strength[k] for k in range(phase, n, m)]
            if len(vals) >= 3:
                best = max(best, sum(vals) / len(vals))
        if best >= 0:
            scores[m] = best
    if not scores:
        return max(2, round(target / period))
    # Chu kỳ NGẮN NHẤT đạt ~điểm cao nhất: m=6 và m=3 gần bằng nhau trên nhạc nhịp 3
    # (0,460 vs 0,458) vì m=6 chỉ là bội của m=3 — lấy m nhỏ mới ra ĐÚNG ô nhịp gốc,
    # rồi mới nhân lên cho gần target. Lấy m lớn thì shot dài gấp đôi ý editor.
    top = max(scores.values())
    base = min(m for m, s in scores.items() if s >= top * 0.97)
    mult = max(1, round(target / (base * period)))
    return max(2, base * mult)


def insert_grid_cuts(start: float, end: float, beats: list[float],
                     strength: list[float] | None = None,
                     downbeats: list[float] | None = None,
                     meter: int = 0,
                     target: float = INSERT_TARGET_SHOT,
                     min_shot: float = INSERT_MIN_SHOT,
                     seed: int = 0,
                     pace: str = "medium") -> list[float]:
    """Mốc cắt TUYỆT ĐỐI trên timeline chia Δ [start,end] theo nhịp bài editor.

    ★ NHIP-M4b (foundation e2, user chốt 2026-07-21) — có `downbeats` (madmom) +
    `meter` (3|4): lưới sinh bằng CÔNG THỨC ĐỀU, pha neo downbeat thật:
        mốc[n] = downbeat_đầu + n × bước,   bước = bội của (bar nhịp 3 | nửa-bar nhịp 4)
    Luật editor: nhịp 3 chuyển ở phách 1 (mỗi ô nhịp); nhịp 4 chuyển ở phách 1&3.
    Mọi bội của bước đều rơi phách LẺ -> thưa hơn khi cần mà không phá luật.
    Vì sao công thức mà KHÔNG dính bug b08/b09 (mini-hook §5a từng cấm "b0+n*period"):
    bug đó do period + pha lấy từ beat librosa (trôi 46ms, mù phách mạnh); nay pha =
    downbeat RNN, period = trung vị bar madmom — cả hai đúng, lưới đều 0ms (GT1).

    Fallback (không downbeats/meter — madmom lỗi, project cũ): lưới beat librosa như
    trước qua `beat_grid`. `beats`/`downbeats` = giây từ ĐẦU FILE nhạc; assemble đặt
    bài editor từ đầu bài tại mép Δ nên timeline = start + mốc.

    Trả [start, ...mốc giữa...] (mốc BẮT ĐẦU từng shot). Không đủ dữ liệu -> [start]
    = 1 hình phủ trọn Δ (hành vi M3, fail-open)."""
    from autoedit.music.minihook import beat_grid

    dur = end - start
    if dur <= 0:
        return [start]

    downs_in = [d for d in (downbeats or []) if 0 <= d <= dur]
    if len(downs_in) >= 2 and meter in (3, 4):
        import statistics
        # bar từ TOÀN BÀI (nhiều mẫu, trung vị chống jitter đo); pha từ downbeat đầu trong Δ
        src = downbeats if len(downbeats or []) >= 2 else downs_in
        bar = statistics.median(b - a for a, b in zip(src, src[1:]))
        if bar > 0:
            import random
            base = bar if meter == 3 else bar / 2.0
            mult = max(1, round(target / base))
            while base * mult < min_shot:
                mult += 1
            step = base * mult
            # A′ shuffle: thời lượng shot = pattern RUN+HOLD (bội của step -> mọi mốc
            # vẫn rơi phách LẺ, lưới vẫn công thức 0ms). Seed cố định -> tái lập.
            first = downs_in[0]
            group = max(1, round(4 * bar / step))          # 4 ô nhịp ~ 1 câu nhạc
            pat = _shaped_pattern(max(0, int((dur - first) / step)),
                                  random.Random(seed), pace, group)
            cuts = [start]
            c = first
            for p in pat:
                if c > dur - min_shot:
                    break
                if c - (cuts[-1] - start) >= min_shot:
                    cuts.append(round(start + c, 4))
                c += p * step
            # biên SAU shot pattern chót cũng là mốc (không thì shot cuối nuốt luôn
            # phần dư tới mép Δ — V11 grid đều có mốc này, giữ nguyên hành vi)
            if c <= dur - min_shot and c - (cuts[-1] - start) >= min_shot:
                cuts.append(round(start + c, 4))
            return cuts

    if not beats:
        return [start]
    # beat trong vùng Δ, quy về hệ ĐẦU Δ (bài editor bắt đầu từ 0 tại mép Δ)
    rel = [(b, s) for b, s in zip(beats, strength or [0.0] * len(beats)) if 0 <= b <= dur]
    if len(rel) < 2:
        return [start]
    bt = [b for b, _ in rel]
    st = [s for _, s in rel]
    period = (bt[-1] - bt[0]) / max(1, len(bt) - 1)
    if period <= 0:
        return [start]
    # k = bội số CHU KỲ NHỊP MẠNH gần target — không ép round(target/period) (lệch pha
    # nhịp -> cắt vào beat yếu, user nghe ra ở draft V9)
    k = _meter_k(st, period, target)
    cuts = beat_grid(dur, bt, pattern=(k,), lock=k, min_shot=min_shot,
                     beat_strength=st if any(st) else None,
                     search=INSERT_SEARCH_BEATS)
    return [round(start + c, 4) for c in cuts]


def insert_grids(project) -> dict[int, list[float]]:
    """Lưới mốc cắt của MỌI Δ có nhịp — {after_beat: [mốc tuyệt đối]}.

    Dời từ assembler về đây (M4c): assemble chẻ cửa sổ + source pick footage cùng gọi
    MỘT chỗ tính — hai tầng tự khớp từng mốc, không có bản sao logic để trôi lệch.
    Seed A′: shuffle_seed editor khai, 0 = crc32(beat, tên bài) — dựng lại Y HỆT."""
    import zlib
    from pathlib import Path

    from autoedit.music.plan import insert_edges

    edges = insert_edges(project)
    grids: dict[int, list[float]] = {}
    for ins in project.inserts:
        edge = edges.get(ins.after_beat)
        if not edge or not ins.music_beats or ins.music_tier not in ("A", "B"):
            continue
        seed = ins.shuffle_seed or zlib.crc32(
            f"{ins.after_beat}:{Path(ins.music).name}".encode("utf-8"))
        cuts = insert_grid_cuts(edge[0], edge[1], ins.music_beats,
                                ins.music_beat_strength,
                                downbeats=ins.music_downbeats,
                                meter=ins.music_meter,
                                seed=seed, pace=ins.music_pace or "medium")
        if len(cuts) > 1:
            grids[ins.after_beat] = cuts
    return grids


def insert_hold_flags(durs: list[float]) -> list[bool]:
    """Ô nào của lưới Δ là HOLD (A′ e2 §5: dur ≥1,5× trung vị, chỉ khi Δ có ≥4 ô).

    DÙNG CHUNG: source pick footage cảnh RỘNG cho ô HOLD (M4c) + assemble chọn ảnh
    slug hold — 1 luật 2 nơi, suy từ chính durations nên không cần nối dây."""
    if len(durs) < 4:
        return [False] * len(durs)
    unit = sorted(durs)[len(durs) // 2]
    return [d >= 1.5 * unit for d in durs]


def split_insert_windows(windows: list[CoverWindow],
                         grids: dict[int, list[float]]) -> list[CoverWindow]:
    """Chẻ cửa sổ Δ thành N miếng theo mốc lưới beat (grids: {beat_id: [mốc tuyệt đối]}).

    Miếng giữ nguyên cờ `insert=True` -> mọi luật né-Δ của M2 (J-cut, snap, ambient,
    pacing) vẫn tự né từng miếng. Δ không có grid -> đi qua NGUYÊN VẸN (1 cửa sổ như
    M2/M3). Mốc cuối luôn kéo tới hết Δ: Δ phải giữ ĐÚNG độ dài editor khai."""
    out: list[CoverWindow] = []
    for w in windows:
        cuts = grids.get(w.beat_id) if w.insert else None
        if not w.insert or not cuts or len(cuts) < 2:
            out.append(w)
            continue
        pts = [c for c in cuts if w.start <= c < w.end] or [w.start]
        pts[0] = w.start
        for a, b in zip(pts, pts[1:] + [w.end]):
            out.append(CoverWindow(beat_id=w.beat_id, start=round(a, 4),
                                   end=round(b, 4), insert=True))
    return out


def breath_shot_beat_ids(beats: list[Beat]) -> set[int]:
    """Beat MANG ô thở đạt ngưỡng nhận shot thở riêng. Beat cuối video không bao giờ
    (không có voice vào sau — outro giữ hình, backlog MO_TA_SHOT_THO §5)."""
    ids: set[int] = set()
    for a, b in zip(beats, beats[1:]):
        if a.breathing_after >= BREATH_SHOT_MIN or (
            a.breathing_after >= BREATH_SHOT_MIN_CHAPTER and a.chapter != b.chapter
        ):
            ids.add(a.beat_id)
    return ids


def split_breath_shots(
    windows: list[CoverWindow], breath_specs: dict[int, list[float]]
) -> list[CoverWindow]:
    """Chẻ cửa sổ có ô thở ĐÃ PICK thành [thoại + HOLD giữ hình] + k cửa sổ shot thở.

    breath_specs = {beat_id: [dur từng miếng]} lấy từ project.breath_shots THẬT (không
    tính lại predicate) — pick hụt ô nào thì ô đó giữ nguyên hành vi cũ; pick hụt GIỮA
    chừng thì miếng cuối đã pick tự phủ dài ra (cửa sổ cuối LUÔN chạm w.end — nuốt cả
    sai số làm tròn). dur=0 (record v1) = 1 miếng phủ trọn ô. Cửa sổ giữ còn
    breathing_dur=HOLD < J_CUT_MIN_BREATH nên tự thoát apply_j_cuts; cửa sổ shot thở
    breathing_dur=0 — mép voice kế không dịch.
    """
    out: list[CoverWindow] = []
    for w in windows:
        durs = breath_specs.get(w.beat_id)
        # đủ chỗ cho HOLD + 1 shot xem kịp (dữ liệu lệch/ô quá nông -> giữ nguyên)
        if not durs or w.breathing_dur < BREATH_SHOT_HOLD + MIN_SHOT_DUR:
            out.append(w)
            continue
        cut_at = round(w.end - w.breathing_dur + BREATH_SHOT_HOLD, 4)
        out.append(CoverWindow(beat_id=w.beat_id, start=w.start, end=cut_at,
                               breathing_dur=BREATH_SHOT_HOLD, micro_dur=w.micro_dur))
        for d in durs[:-1]:
            nxt = round(cut_at + d, 4)
            out.append(CoverWindow(beat_id=w.beat_id, start=cut_at, end=nxt,
                                   breath_shot=True))
            cut_at = nxt
        out.append(CoverWindow(beat_id=w.beat_id, start=cut_at, end=w.end,
                               breath_shot=True))
    return out


# J-cut (hình thở 2.0 — MO_TA_VAN_HANH_HINH_THO_2.md §3B, mẫu 14/18 ô SP1-003):
# shot kế vào TRƯỚC khi voice nói lại. Chỉ dịch mép VIDEO — voice/nhạc không đổi.
J_CUT_LEAD = 0.30        # giây shot kế vào sớm
J_CUT_MIN_BREATH = 1.2   # chỉ ô thở thật; tầng giãn nghỉ máy (≤0.7s) không bao giờ J-cut


def apply_j_cuts(windows: list[CoverWindow]) -> list[CoverWindow]:
    """Dịch mép CHUNG giữa cửa sổ có ô thở ≥ J_CUT_MIN_BREATH và cửa sổ kế về sớm
    J_CUT_LEAD — liền khít giữ nguyên (mutate in place, trả lại list). Ô nhỏ nhất
    1,2s vẫn còn ≥0,9s hình giữ trước khi shot kế vào."""
    for w, nxt in zip(windows, windows[1:]):
        if w.breathing_dur < J_CUT_MIN_BREATH:
            continue
        if nxt.insert:
            # NHIP-M2: sau ô là ĐOẠN CHÈN, không phải voice quay lại — J-cut vô nghĩa
            # (Δ giữ ĐÚNG độ dài editor khai, không gặm 0,3s của ô thở)
            continue
        w.end = round(w.end - J_CUT_LEAD, 4)
        w.breathing_dur = round(w.breathing_dur - J_CUT_LEAD, 4)  # giữ nguyên phần THOẠI khi chia multi-shot
        nxt.start = round(nxt.start - J_CUT_LEAD, 4)
        nxt.j_cut_start = True  # M-ACCENT đọc: body J-cut thắng snap (luật user 2026-07-13)
    return windows


def snap_to_accents(
    windows: list[CoverWindow],
    targets: list[float],
    hook_end: float,
    tol: float,
    lead: float,
    cap_ratio: float,
    exempt: set[float] | None = None,
) -> dict:
    """M-ACCENT (MUSIC SYNC M3): trượt mép CHUNG giữa 2 cửa sổ về `accent − lead` gần
    nhất nếu cách ≤ tol. Chạy SAU apply_j_cuts, TRƯỚC đặt footage — chỉ dịch mép VIDEO,
    voice/nhạc không đụng (hệ tọa độ kép). Mutate in place, trả stats.

    Luật (user chốt 2026-07-13): hook snap thắng (kể cả mép J-cut); body mép J-cut miễn.
    Miễn thêm: mép GIỮA các miếng shot thở (đợt sau) + mép đã neo M-CHANGE (exempt).
    Trần cap_ratio tổng mép; ưu tiên khi chạm trần: hook > mép vào ô thở > body,
    cùng hạng lấy mép dịch ít nhất. 2 cửa sổ quanh mép giữ ≥ MIN_SHOT_DUR."""
    import bisect
    import math

    stats = {"snapped": 0, "edges": max(0, len(windows) - 1),
             "hook": 0, "breath": 0, "body": 0, "shift_ms": []}
    if not targets or len(windows) < 2:
        return stats
    exempt = exempt or set()
    cands: list[tuple[int, float, int, float]] = []
    for i, (w, nxt) in enumerate(zip(windows, windows[1:])):
        edge = nxt.start
        if round(edge, 2) in exempt:
            continue                                  # mép = điểm đổi nhạc M-CHANGE
        if w.breath_shot and nxt.breath_shot:
            # giữa các miếng thở: NHIP-M1 các mép này đã nằm TRÊN beat (retime_breath_grid
            # chạy sau) — snap accent−lead 80ms sẽ kéo LỆCH beat; ô đường DNA cũng miễn như cũ
            continue
        if w.insert or nxt.insert:
            # NHIP-M2: mép VÀO/RA đoạn chèn giữ ĐÚNG mốc editor khai (độ dài Δ do editor
            # quyết — snap sẽ co/giãn Δ lệch số khai); footage TRONG Δ cắt nhịp ở M4
            continue
        breath_entry = nxt.breath_shot and not w.breath_shot
        zone_hook = edge < hook_end
        if nxt.j_cut_start and not zone_hook:
            continue                                  # body: J-cut thắng
        j = bisect.bisect_left(targets, edge)
        best = None
        for k in (j - 1, j):
            if 0 <= k < len(targets):
                t = targets[k] - lead
                if best is None or abs(t - edge) < abs(best - edge):
                    best = t
        if best is None or abs(best - edge) > tol:
            continue
        lo = w.start + MIN_SHOT_DUR
        hi = nxt.end - MIN_SHOT_DUR
        if breath_entry:                              # DNA hold 0.4-0.9s: giữ hình ≥0.2s sau voice
            lo = max(lo, w.end - w.breathing_dur + 0.2)
        if not (lo <= best <= hi) or abs(best - edge) < 1e-4:
            continue
        prio = 0 if zone_hook else (1 if breath_entry else 2)
        cands.append((prio, abs(best - edge), i, best))
    quota = max(1, math.floor(stats["edges"] * cap_ratio)) if cands else 0
    for prio, _dist, i, best in sorted(cands)[:quota]:
        w, nxt = windows[i], windows[i + 1]
        delta = round(best - w.end, 4)
        w.end = round(best, 4)
        nxt.start = round(best, 4)
        # phần không-thoại cuối cửa sổ co/giãn theo mép (như apply_j_cuts) — multi-shot
        # vẫn chỉ chia phần thoại
        if w.breathing_dur > 0:
            w.breathing_dur = round(max(0.0, w.breathing_dur + delta), 4)
        elif w.micro_dur > 0:
            w.micro_dur = round(max(0.0, w.micro_dur + delta), 4)
        stats["snapped"] += 1
        stats["hook" if prio == 0 else ("breath" if prio == 1 else "body")] += 1
        stats["shift_ms"].append(round(delta * 1000))
    return stats


def retime_breath_grid(
    windows: list[CoverWindow],
    beat_pts: list[tuple[float, float]],
    ids: set[int],
    min_piece: float = 1.5,
) -> dict:
    """NHIP-M1 tầng 2: dời mép GIỮA các miếng shot thở (ô `beat_cut`) về beat THẬT.

    Chạy SAU M-CHANGE + snap_to_accents (boundary nhạc đã chốt -> beat_pts đúng;
    mép VÀO/RA ô đã snap xong, lưới tôn trọng chúng). Vì sao phải tính lại ở đây:
    source dự đoán boundary = timeline_start chương, M-CHANGE có thể dời ≤2s ->
    lưới source lệch theo (lệch 1 beat là tai nghe ra — bug b08/b09).

    SỐ MIẾNG GIỮ NGUYÊN (= số clip đã pick ở source — bẫy ① hở timeline/NAM CHÂM):
    lưới mới thiếu mốc (m < n−1, hiếm) -> ô đó GIỮ mép cũ (off-beat nhưng lành), đếm
    `kept`. Mutate in place; trả stats {"retimed", "kept", "durs": {beat_id: [dur]}}
    — assembler ghi durs mới ngược vào project.breath_shots (first_piece_end SFX đọc)."""
    from autoedit.music.minihook import breath_cuts

    stats: dict = {"retimed": 0, "kept": 0, "durs": {}}
    i = 0
    while i < len(windows):
        if not (windows[i].breath_shot and windows[i].beat_id in ids):
            i += 1
            continue
        j = i
        while (j < len(windows) and windows[j].breath_shot
               and windows[j].beat_id == windows[i].beat_id):
            j += 1
        run = windows[i:j]
        i = j
        if len(run) < 2:
            continue  # 1 miếng — không có mép giữa để dời
        start, end = run[0].start, run[-1].end
        local = [(t - start, s) for t, s in beat_pts if start < t < end]
        cuts = breath_cuts(end - start, [t for t, _ in local],
                           [s for _, s in local], min_piece=min_piece)
        interior = [c for c in cuts if c > 0]
        if len(interior) < len(run) - 1:
            stats["kept"] += 1
            continue
        for w, c in zip(run[:-1], interior[: len(run) - 1]):
            edge = round(start + c, 4)  # mép CHUNG một float (bài học SegmentOverlap 1µs)
            w.end = edge
        for a, b in zip(run, run[1:]):
            b.start = a.end
        stats["retimed"] += 1
        stats["durs"][run[0].beat_id] = [round(w.end - w.start, 4) for w in run]
    return stats


def check_coverage_invariants(windows: list[CoverWindow], total_end: float) -> list[str]:
    """Bất biến phủ kín — trả list lỗi (rỗng = đạt)."""
    errors = []
    if not windows:
        return ["không có cửa sổ phủ nào"]
    if abs(windows[0].start) > 1e-3:
        errors.append(f"cửa sổ đầu bắt đầu {windows[0].start}, phải là 0")
    for a, b in zip(windows, windows[1:]):
        if abs(b.start - a.end) > 1e-3:
            errors.append(f"hở/đè giữa beat {a.beat_id} (end {a.end}) và {b.beat_id} (start {b.start})")
    if abs(windows[-1].end - total_end) > 1e-3:
        errors.append(f"cửa sổ cuối kết thúc {windows[-1].end}, timeline dài {total_end}")
    for w in windows:
        if w.duration <= 0:
            errors.append(f"beat {w.beat_id}: cửa sổ rỗng/âm ({w.duration})")
    return errors
