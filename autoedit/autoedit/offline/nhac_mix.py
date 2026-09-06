r"""Đường âm lượng nhạc nền cho MỘT CHƯƠNG — ducking theo voice + fade chương.

User chốt 06/09: nhạc theo chương, máy đặt sẵn fade chuyển chương + hạ nhạc
khi voice nói ("down toner để mix cho mượt"). Tất cả thành keyframe CapCut
chỉnh được — đúng triết lý draft-để-chỉnh-tiếp, editor tinh chỉnh tay phần cuối.

Hàm ở đây THUẦN (không đụng pycapcut) để test bằng số; thay_mau.dung_draft
đổ kết quả vào AudioSegment.add_keyframe / add_fade.
"""
from __future__ import annotations

CAO = 0.9            # nhạc khi không có voice (khoảng thở, mở/đóng chương)
THAP = 0.25          # nhạc khi voice đang nói
DOC_XUONG_S = 0.30   # nhạc hạ xuống TRƯỚC khi câu bắt đầu
DOC_LEN_S = 0.40     # nhạc nhả lên SAU khi câu dứt
FADE_VAO_S = 1.5     # đầu chương
FADE_RA_S = 2.0      # cuối chương


def _gop_noi(khoang: list[tuple[float, float]], ke: float) -> list[tuple[float, float]]:
    """Gộp các khoảng cách nhau < `ke` — thở quá ngắn thì nhạc GIỮ THẤP luôn,
    không nhấp nhô lên-xuống trong nửa giây (nghe rất amateur)."""
    if not khoang:
        return []
    ra = [list(khoang[0])]
    for a, b in khoang[1:]:
        if a - ra[-1][1] < ke:
            ra[-1][1] = b
        else:
            ra.append([a, b])
    return [(a, b) for a, b in ra]


def duong_am_luong(khoi: list[dict], cao: float = CAO, thap: float = THAP,
                   xuong_s: float = DOC_XUONG_S, len_s: float = DOC_LEN_S,
                   ) -> list[tuple[float, float]]:
    """[(giây TIMELINE, volume)] — keyframe ducking cho cả chương.

    Mỗi vùng NÓI (đã gộp các vùng sát nhau): nhạc bắt đầu hạ `xuong_s` trước
    câu, chạm `thap` đúng lúc câu vào, giữ tới hết câu, nhả lên `cao` sau
    `len_s`. Ngoài vùng nói nhạc ở `cao`.
    """
    from autoedit.offline.hinh import moc_timeline

    moc = moc_timeline(khoi)
    if not moc:
        return [(0.0, cao)]
    noi = _gop_noi([(t0, t1) for t0, t1, _ in moc], ke=xuong_s + len_s + 0.2)
    kf: list[tuple[float, float]] = []
    if noi[0][0] - xuong_s > 0.05:
        kf.append((0.0, cao))                       # chương mở bằng nhạc to
    for a, b in noi:
        xa = max(0.0, a - xuong_s)
        if kf and kf[-1][0] >= xa:                  # dính keyframe trước -> bỏ nhịp lên
            kf.pop()
        else:
            kf.append((xa, cao))
        kf.append((max(0.0, a), thap))
        kf.append((b, thap))
        kf.append((b + len_s, cao))
    return [(round(t, 3), v) for t, v in kf]


def cat_lap(dai_nhac_s: float, dai_chuong_s: float) -> list[tuple[float, float]]:
    """[(bắt_đầu_trên_timeline, dài)] các miếng nhạc phủ hết chương.

    Track ngắn hơn chương -> LẶP nối đuôi (can_loop trong tiêu chí kho).
    Miếng lặp cuối cắt cụt cho khít mép chương.
    """
    if dai_nhac_s <= 0 or dai_chuong_s <= 0:
        return []
    ra, t = [], 0.0
    while t < dai_chuong_s - 0.01:
        ra.append((round(t, 3), round(min(dai_nhac_s, dai_chuong_s - t), 3)))
        t += dai_nhac_s
    return ra
