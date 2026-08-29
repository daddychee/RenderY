"""MINI-HOOK — đoạn mở màn CHỈ NHẠC + HÌNH, cắt theo LƯỚI BEAT, chèn TRƯỚC voice đầu tiên.

Bằng chứng (đo project mẫu editor `E:\\CapCut Drafts\\0719`, user dựng tay 2026-07-19):
13/13 cut rơi trong ±0,09s của một beat (nhạc 152 BPM, beat 0,395s). Quy về CHỈ SỐ beat:

    beat idx:  0, 3, 8, 13, 16, 20, 24, 29, 33, 41, 49, 57, 65
    khoảng:      3  5  5   3   4   4   5   4 |  8   8   8   8

=> ngữ pháp editor: đoạn ĐẦU cắt dày, độ dài BIẾN THIÊN (3-5 beat); về sau KHOÁ 8 beat
(= 2 bar 4/4) đều tăm tắp. Mọi cut hạ cánh trên beat, không ngoại lệ.

LƯU Ý PHẠM VI (user chốt 2026-07-19): gói này CHỈ làm mini-hook — vùng KHÔNG có voice.
Phần thân bài giữ nguyên luật cũ (cut theo ngữ nghĩa, nhạc chỉ snap ≤15% mép — xem
MO_TA_VAN_HANH_MUSIC_SYNC.md). Lý do: nghiên cứu ~11.000 cut editor thật kết luận video
CÓ VOICE thì editor KHÔNG cắt theo lưới nhịp (lift đo 0,86 < 1,6 cần thiết). Hai bằng
chứng không mâu thuẫn — chúng nói về hai loại video khác nhau (có lời / không lời).

Pure functions — không I/O, không ffmpeg.
"""

from __future__ import annotations

# Mẫu 0719: 3,5,5,3,4,4,5,4 beat rồi khoá 8. Giữ nguyên số đo, KHÔNG làm tròn cho đẹp.
HOOK_PATTERN: tuple[int, ...] = (3, 5, 5, 3, 4, 4, 5, 4)
HOOK_LOCK = 8               # sau khi hết pattern: khoá 8 beat = 2 bar 4/4
MIN_HOOK_SHOT = 0.7         # sàn 1 shot — bằng MIN_SHOT_DUR của coverage (chặn cắt vụn)
# Bán kính hạ cánh (số beat) quanh mốc pattern để tìm beat MẠNH. Đo trên 4 bài nhạc
# nhịp nhanh của user 2026-07-19: ±1 -> 4/33 cut rơi vào beat yếu hơn beat kề; ±2 -> 1/33.
# Không nới thêm: rộng quá thì lưới bỏ nhịp pattern, mất cảm giác đều.
SEARCH_BEATS = 2


def beat_grid(duration: float, beat_times: list[float], *,
              pattern: tuple[int, ...] = HOOK_PATTERN,
              lock: int = HOOK_LOCK,
              min_shot: float = MIN_HOOK_SHOT,
              beat_strength: list[float] | None = None,
              search: int = SEARCH_BEATS) -> list[float]:
    """Mốc cắt cho mini-hook dài `duration` giây, hạ cánh trên BEAT THẬT của nhạc.

    `beat_times` = beat_track của bản nhạc (giây, tính từ đầu FILE nhạc — mini-hook đặt
    nhạc từ giây 0 nên trùng luôn hệ timeline).
    `beat_strength` = onset strength TẠI từng beat (cùng độ dài `beat_times`). Có thì
    dùng để ƯU TIÊN beat mạnh; không có thì lấy đúng beat theo pattern.

    Cut ĐẦU luôn ở 0.0 kể cả khi beat đầu của nhạc muộn hơn (mẫu 0719: beat đầu 0,58s
    nhưng editor vẫn cho hình vào từ giây 0 — hình đứng yên chờ cú beat đầu).

    🐛 BUG ĐÃ SỬA (user bắt 2026-07-19, cut b08/b09 draft MINIHOOK_TEST): bản đầu tính
    mốc bằng SỐ HỌC `b0 + n*period` với period = khoảng cách beat TRUNG BÌNH. Hai hậu quả:
      ① lưới TRÔI khỏi beat thật (cộng dồn sai số ~30ms) — tưởng vô hại, hoá ra là
         triệu chứng của ②;
      ② mốc rơi vào beat YẾU ngay sau beat mạnh -> tai nghe cao trào ở 13,421s nhưng
         hình đổi ở 13,785s, TRỄ ĐÚNG MỘT BEAT. Cùng lỗi ở b09 (16,602 -> 16,997).
    Nay: đi theo pattern để ra mốc DỰ KIẾN, rồi HẠ CÁNH xuống beat thật gần đó, trong
    cửa sổ ±`search` beat CHỌN BEAT MẠNH NHẤT. Toạ độ lấy từ `beat_times` nên lệch ~0ms.

    Trả mốc BẮT ĐẦU của từng shot; shot cuối kéo tới `duration`. Mốc nào làm shot ngắn
    hơn `min_shot` thì BỎ (thà ít shot còn hơn cắt vụn không xem kịp).
    """
    if duration <= 0:
        return []
    if not beat_times:
        return [0.0]

    st = beat_strength if beat_strength and len(beat_strength) == len(beat_times) else None

    cuts = [0.0]
    idx = 0                                      # chỉ số beat của mốc trước (0 = beat đầu)
    for i in range(10_000):                      # trần chống lặp vô hạn (P2: không xảy ra)
        idx += pattern[i] if i < len(pattern) else lock
        if idx >= len(beat_times):
            break
        # hạ cánh: trong ±search beat quanh idx, ưu tiên beat MẠNH nhất (tai nghe cao
        # trào ở beat mạnh — cắt vào beat yếu kề bên bị cảm nhận là TRỄ một nhịp)
        lo = max(0, idx - search)
        hi = min(len(beat_times) - 1, idx + search)
        pick = idx
        if st is not None:
            cand = range(lo, hi + 1)
            # mạnh nhất; hoà thì lấy gần mốc dự kiến nhất (giữ đúng nhịp pattern)
            pick = max(cand, key=lambda k: (st[k], -abs(k - idx)))
        t = beat_times[pick]
        if t > duration - min_shot:              # shot cuối phải còn ≥ min_shot
            break
        if t - cuts[-1] >= min_shot:
            cuts.append(round(t, 4))
            idx = pick                           # neo lại theo beat ĐÃ CHỌN, không trôi
    return cuts


# --- LƯỚI BEAT Ô HÌNH THỞ (NHIP-M1, MO_TA_VAN_HANH_NHIP_O_THO.md) --------------------
# Bài học §4a bàn giao: đếm SỐ BEAT cứng co giãn theo BPM quá tay (89 BPM ra shot 5,4s).
# Tai cảm shot theo GIÂY -> nhắm THỜI GIAN, quy ngược ra số beat. Khoảng nhắm ĐO 2026-07-19:
# 0719 đoạn khoá 3,13-3,23s (8 beat @152) · 246 miếng thở editor thật p50 2,86s.
BREATH_TARGET_SHOT = 3.0   # giây/miếng nhắm tới (89 BPM -> 4 beat 2,7s; 172 -> 9 beat 3,1s)
BREATH_MIN_PIECE = 1.5     # sàn miếng — p10 editor ~1,4-1,9; = min_piece DNA (nay dùng thật)


def breath_cuts(duration: float, beat_times: list[float],
                beat_strength: list[float] | None = None, *,
                target: float = BREATH_TARGET_SHOT,
                min_piece: float = BREATH_MIN_PIECE) -> list[float]:
    """Mốc cắt trong vùng footage của Ô THỞ (hệ tọa độ CỤC BỘ, 0 = sau HOLD).

    Pattern ĐỀU k beat (không dùng mẫu hook 3-5-5... — ô thở là vùng tĩnh, mẫu 0719
    đoạn khoá cũng đều tăm tắp); k = target quy ra số beat theo period ĐO từ chính
    đoạn beat trong ô. Hạ cánh beat MẠNH ±SEARCH_BEATS qua `beat_grid` NGUYÊN VẸN
    (2 test hồi quy bug b08/b09 canh sẵn). <2 beat trong ô -> [0.0] (1 miếng)."""
    if duration <= 0:
        return []
    if len(beat_times) < 2:
        return [0.0]
    diffs = sorted(b - a for a, b in zip(beat_times, beat_times[1:]))
    period = diffs[len(diffs) // 2]
    if period <= 0:
        return [0.0]
    k = max(2, round(target / period))
    # 🐛 BUG ĐÃ SỬA (RD89-10min beat 65, 2026-07-20): beat vượt trần đuôi
    # (> duration − min_piece) phải LOẠI TRƯỚC khi vào lưới — để lại thì hạ-cánh-beat-
    # MẠNH ±SEARCH có thể nhảy trúng nó, beat_grid break và MẤT nhát cắt hợp lệ ngay
    # trước đó (footage 5,3s/12 beat mà ra 1 miếng). Chỉ đường ô thở — mini-hook giữ nguyên.
    keep = [i for i, t in enumerate(beat_times) if t <= duration - min_piece]
    bt = [beat_times[i] for i in keep]
    st = ([beat_strength[i] for i in keep]
          if beat_strength and len(beat_strength) == len(beat_times) else None)
    if len(bt) < 2:
        return [0.0]
    return beat_grid(duration, bt, pattern=(k,), lock=k,
                     min_shot=min_piece, beat_strength=st)


def breath_pieces(duration: float, beat_times: list[float],
                  beat_strength: list[float] | None = None, *,
                  min_piece: float = BREATH_MIN_PIECE) -> list[float]:
    """`breath_cuts` dạng DURS (giây từng miếng, tổng = duration) — khớp shape
    `_pieces` DNA để sourcer/breath.py cắm thẳng. Round 2 như _pieces (vị trí mép
    chính xác 4 số do retime_breath_grid ở assemble chốt lại trên boundary thật)."""
    cuts = breath_cuts(duration, beat_times, beat_strength, min_piece=min_piece)
    if not cuts:
        return []
    if len(cuts) == 1:
        return [round(duration, 2)]
    bounds = cuts + [duration]
    durs = [round(b - a, 2) for a, b in zip(bounds[:-1], bounds[1:])]
    durs[-1] = round(duration - sum(durs[:-1]), 2)  # miếng cuối = phần còn lại, tổng khít
    return durs


def grid_windows(duration: float, beat_times: list[float], **kw) -> list[tuple[float, float]]:
    """`beat_grid` nhưng trả (start, end) liền khít — dạng coverage cần.

    Mép dùng CHUNG một giá trị float giữa 2 shot kề nhau (bài học SegmentOverlap 1µs:
    round(mép*SEC) hai bên phải ra đúng một số microsecond).
    """
    cuts = beat_grid(duration, beat_times, **kw)
    if not cuts:
        return []
    bounds = cuts + [round(duration, 4)]
    return [(bounds[k], bounds[k + 1]) for k in range(len(bounds) - 1)]
