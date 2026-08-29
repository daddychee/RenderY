"""MINI-HOOK: lưới cắt theo beat cho đoạn mở màn không voice."""

from __future__ import annotations

from autoedit.music.minihook import HOOK_PATTERN, beat_grid, grid_windows

# Nhạc mẫu 0719: 152 BPM, beat đầu 0,58s -> chu kỳ 0,3947s
B0, PERIOD = 0.58, 60.0 / 152.0
BEATS = [B0 + k * PERIOD for k in range(120)]


def test_cut_dau_luon_o_0():
    """Hình vào từ giây 0 kể cả khi beat đầu muộn hơn (mẫu 0719: beat đầu 0,58s)."""
    cuts = beat_grid(20.0, BEATS)
    assert cuts[0] == 0.0


def test_moi_cut_roi_dung_beat():
    """Bất biến CỐT LÕI: trừ cut đầu (=0), mọi cut phải nằm trên một beat (±10ms)."""
    for t in beat_grid(20.0, BEATS)[1:]:
        assert min(abs(t - b) for b in BEATS) <= 0.01, f"cut {t} lệch beat"


def test_tai_hien_moc_cut_mau_0719():
    """Tái hiện số đo THẬT từ draft editor `E:\\CapCut Drafts\\0719` (13 cut đo được).

    Mốc editor dựng tay: 0, 2.0, 3.733, 5.9, 6.967, 8.733, 10.167, 12.3, 13.4,
    16.533, 19.733, 22.967, 26.133 — quy về beat idx: 0,3,8,13,16,20,24,29,33,41,49,57,65.
    Lưới sinh ra phải khớp các mốc SAU pattern (từ beat 33 trở đi khoá 8 beat).
    """
    cuts = beat_grid(30.0, BEATS)
    idx = [round((t - B0) / PERIOD) for t in cuts[1:]]
    assert idx[:8] == [3, 8, 13, 16, 20, 24, 29, 33], idx
    assert idx[8:12] == [41, 49, 57, 65], idx          # khoá 8 beat = 2 bar


def test_khoa_8_beat_sau_pattern():
    """Sau khi hết pattern biến thiên -> khoảng cách đều đúng 8 beat."""
    cuts = beat_grid(40.0, BEATS)
    idx = [round((t - B0) / PERIOD) for t in cuts[1:]]
    tail = idx[len(HOOK_PATTERN):]
    assert all(b - a == 8 for a, b in zip(tail, tail[1:])), idx


def test_hoi_quy_khong_cat_vao_beat_yeu_ke_beat_manh():
    """🐛 HỒI QUY (user bắt 2026-07-19, cut b08/b09 draft MINIHOOK_TEST).

    Trước fix: mốc tính bằng SỐ HỌC b0+n*period -> rơi vào beat YẾU ngay sau beat MẠNH.
    Tai nghe cao trào ở 13,421s nhưng hình đổi ở 13,785s = TRỄ ĐÚNG MỘT BEAT.
    Sau fix: hạ cánh xuống beat thật, ưu tiên beat mạnh -> phải chọn 13,421 chứ không 13,785.
    """
    # dựng lại đúng vùng nhạc thật: beat mạnh 13.421 (0.25) rồi beat yếu 13.785 (0.21)
    beats = [B0 + k * PERIOD for k in range(60)]
    strength = [0.20] * len(beats)
    manh = {}
    for k, b in enumerate(beats):
        if abs(b - 13.421) < 0.02:
            strength[k] = 0.25; manh["b08"] = b
        if abs(b - 16.602) < 0.02:
            strength[k] = 0.28; manh["b09"] = b
        if abs(b - 13.816) < 0.02 or abs(b - 16.997) < 0.02:
            strength[k] = 0.21                       # beat yếu kề bên — KHÔNG được chọn
    cuts = beat_grid(20.0, beats, beat_strength=strength)
    for ten, t_manh in manh.items():
        assert any(abs(c - t_manh) < 0.02 for c in cuts), \
            f"{ten}: phải cắt tại beat MẠNH {t_manh:.3f}, cuts={cuts}"
        assert not any(abs(c - (t_manh + PERIOD)) < 0.02 for c in cuts), \
            f"{ten}: cắt vào beat YẾU {t_manh + PERIOD:.3f} = trễ 1 nhịp (bug cũ)"


def test_cut_lay_toa_do_beat_that_khong_troi():
    """Sau fix: mốc = toạ độ beat THẬT -> lệch ~0ms, không cộng dồn sai số.

    Ngưỡng 0,1ms = dung sai round(t,4) của beat_grid; bug cũ lệch tới 33ms (330 lần).
    """
    for t in beat_grid(20.0, BEATS)[1:]:
        assert min(abs(t - b) for b in BEATS) < 1e-4, f"cut {t} không phải beat thật"


def test_khong_shot_nao_duoi_san():
    """Mọi shot ≥ MIN_HOOK_SHOT — chặn cắt vụn không xem kịp."""
    for s, e in grid_windows(20.0, BEATS):
        assert e - s >= 0.7 - 1e-9, (s, e)


def test_windows_lien_khit_khong_ho_khong_de():
    """Bất biến phủ kín: mép chung DÙNG CHUNG float (bài học SegmentOverlap 1µs)."""
    ws = grid_windows(20.0, BEATS)
    assert ws[0][0] == 0.0
    assert abs(ws[-1][1] - 20.0) < 1e-9
    for (_, e), (s, _) in zip(ws, ws[1:]):
        assert e == s, "mép hai bên phải là ĐÚNG một giá trị float"


def test_20s_ra_khoang_10_shot():
    """Cỡ mẻ user chốt để test: 20s ~ 10 shot (152 BPM)."""
    assert 8 <= len(grid_windows(20.0, BEATS)) <= 12


def test_khong_beat_thi_tra_1_shot():
    """Nhạc tier C / không đo được beat -> fail-open: 1 shot phủ TRỌN, KHÔNG vỡ.

    Quan trọng: phải trả 1 window phủ kín [0, dur] chứ KHÔNG phải rỗng — rỗng = lỗ ở
    đầu video_l1 = bug NAM CHÂM CapCut dồn segment (DS3-084 trôi -187s).
    """
    assert beat_grid(20.0, []) == [0.0]
    assert grid_windows(20.0, []) == [(0.0, 20.0)]


def test_duration_0_khong_vo():
    assert beat_grid(0.0, BEATS) == []


# ===================== LƯỚI BEAT Ô THỞ (NHIP-M1) ==============================
from autoedit.music.minihook import BREATH_MIN_PIECE, breath_cuts, breath_pieces  # noqa: E402


def test_breath_nham_theo_giay_khong_theo_so_beat():
    """Bài học §4a bàn giao: đếm SỐ BEAT cứng thì 89 BPM ra shot 5,4s (sai gần 2×).
    Lưới ô thở nhắm GIÂY (target 3,0) -> mọi BPM 86-172 đều ra miếng trong khoảng
    nhắm đo từ editor (p10 1,5 — p90+ ~4,6), không co giãn theo tempo."""
    for period in (0.674, 0.441, 0.395, 0.348):        # 89 / 136 / 152 / 172 BPM
        beats = [round(i * period, 4) for i in range(1, 40)]
        cuts = breath_cuts(9.5, beats)
        durs = [b - a for a, b in zip(cuts, cuts[1:])] + [9.5 - cuts[-1]]
        assert all(1.5 - 1e-9 <= d <= 4.6 for d in durs), (period, durs)


def test_breath_cuts_ha_canh_beat_manh():
    """Tái dùng landing beat MẠNH của beat_grid (bug b08/b09): beat yếu tại mốc dự
    kiến, beat kề mạnh hơn -> cắt vào beat mạnh."""
    period = 0.5                                        # k = 6 -> mốc dự kiến idx 6
    beats = [round((i + 1) * period, 4) for i in range(20)]
    strength = [0.1] * len(beats)
    strength[4] = 1.0                                   # idx 4 (t=2.5) mạnh, trong ±2 của idx 6
    cuts = breath_cuts(9.0, beats, strength)
    assert 2.5 in cuts and 3.5 not in cuts


def test_breath_pieces_tong_khit_va_bo_tran_3_mieng():
    """User chốt 2026-07-19: BỎ trần 3 miếng ở đường beat — ô 10s @109 BPM ra 4 miếng
    (~2,8s trên beat + đuôi ≥ sàn); tổng khít duration."""
    beats = [round(0.1 + i * 0.55, 4) for i in range(18)]   # beat đầu 0,1s, period 0,55
    durs = breath_pieces(10.0, beats)
    assert durs == [2.85, 2.75, 2.75, 1.65]                 # 4 miếng — trần 3 đã bỏ
    assert round(sum(durs), 2) == 10.0
    assert all(d >= BREATH_MIN_PIECE for d in durs)


def test_breath_hoi_quy_beat_manh_vuot_tran_duoi_khong_nuot_cut():
    """🐛 HỒI QUY (RD89-10min beat 65, 2026-07-20): footage 5,3s / 12 beat period 0,464 —
    mốc dự kiến idx 6 (2,99s) HỢP LỆ nhưng beat mạnh nhất trong ±2 nằm ở 3,92s > trần
    đuôi 3,8 -> bản lỗi break luôn, ra 1 miếng. Sau fix: beat vượt trần bị loại khỏi
    ứng viên -> vẫn cắt được 2 miếng, mép trên beat hợp lệ."""
    beats = [0.23, 0.694, 1.159, 1.6, 2.064, 2.529, 2.993, 3.458, 3.922, 4.386, 4.851, 5.292]
    strength = [0.2] * len(beats)
    strength[8] = 1.0                                  # 3.922 mạnh nhất — vượt trần đuôi
    cuts = breath_cuts(5.3, beats, strength)
    assert len(cuts) == 2 and cuts[1] in beats and cuts[1] <= 5.3 - BREATH_MIN_PIECE
    durs = breath_pieces(5.3, beats, strength)
    assert len(durs) == 2 and round(sum(durs), 2) == 5.3


def test_breath_it_beat_fail_open_1_mieng():
    """<2 beat trong ô / duration 0 -> không vỡ, 1 miếng phủ trọn (đường DNA gánh)."""
    assert breath_cuts(5.0, [2.0]) == [0.0]
    assert breath_pieces(5.0, [2.0]) == [5.0]
    assert breath_pieces(0.0, []) == []
