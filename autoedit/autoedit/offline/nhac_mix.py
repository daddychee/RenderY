r"""Đường âm lượng nhạc nền cho MỘT CHƯƠNG — ducking theo voice + fade chương.

User chốt 06/09: nhạc theo chương, máy đặt sẵn fade chuyển chương + hạ nhạc
khi voice nói ("down toner để mix cho mượt"). Tất cả thành keyframe CapCut
chỉnh được — đúng triết lý draft-để-chỉnh-tiếp, editor tinh chỉnh tay phần cuối.

Hàm ở đây THUẦN (không đụng pycapcut) để test bằng số; thay_mau.dung_draft
đổ kết quả vào AudioSegment.add_keyframe / add_fade.
"""
from __future__ import annotations

NEN = 0.25           # mức NỀN của nhạc — giữ đều suốt, kể cả thở ngắn
CAO = 0.40           # thở DÀI: +4dB so với nền — đo theo tai: +1.6dB (0.30) không ai
                     # nhận ra, +11dB (0.9 bản đầu) là shock; +4dB là điểm cân
NGUONG_THO_S = 3.0   # thở >= mức này mới được nhích — thở 1s mà nhấp nhô là vụn
DOC_LEN_S = 0.40     # dốc nhích lên ở đầu khoảng thở dài
DOC_XUONG_S = 0.30   # dốc hạ về nền trước khi câu kế vào
FADE_VAO_S = 1.5     # đầu chương
FADE_RA_S = 2.0      # cuối chương


def duong_am_luong(khoi: list[dict], nen: float = NEN, cao: float = CAO,
                   nguong_s: float = NGUONG_THO_S, len_s: float = DOC_LEN_S,
                   xuong_s: float = DOC_XUONG_S) -> list[tuple[float, float]]:
    """[(giây TIMELINE, volume)] cho cả chương.

    Luật user chốt 06/09 (thay bản ducking bậc thang cũ): nhạc giữ ĐỀU ở mức
    nền — thở ngắn không đụng tới, vì "đôi khi hình thở chỉ có 1s, to nhỏ như
    vậy rất vụn". Chỉ khoảng thở >= nguong_s mới nhích lên +20%, có dốc lên ở
    đầu và dốc hạ trước khi câu kế vào.
    """
    from autoedit.offline.hinh import moc_timeline

    moc = moc_timeline(khoi)
    kf: list[tuple[float, float]] = [(0.0, nen)]
    if not moc:
        return kf
    # khoảng lặng = giữa t1 nói của khối này và t0 nói của khối kế
    for i, (_t0, t1, _tt) in enumerate(moc):
        b = moc[i + 1][0] if i + 1 < len(moc) else moc[i][2]
        if b - t1 < nguong_s:
            continue
        kf.append((t1, nen))
        kf.append((round(t1 + len_s, 3), cao))
        kf.append((round(b - xuong_s, 3), cao))
        kf.append((round(b, 3), nen))
    return kf


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
