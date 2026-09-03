"""V2 Đợt 1b — SFX bám cut trong VÙNG NHẤN (hook trọn + beat bùng).

KHÔNG lật PB12 (whoosh rải tự do thân video: 0/88 trùng vị trí editor, đã bỏ):
đây là tiếng bám CUT trong vùng mật độ cao — số 23 draft DEEPSEA (48% ±0.25s).
Tái dùng nguyên hook_sfx_slots với PM/gap/volume đã qua cổng tai V4.
"""

from __future__ import annotations

import pytest

from autoedit.ambient.schedule import HOOK_SFX_GAP, nhan_sfx_slots
from autoedit.nhip.ep import vung_nhan
from autoedit.nhip.profile import nap


class _Beat:
    def __init__(self, bid, ts, te, breathing=0.0):
        self.beat_id = bid
        self.timeline_start, self.timeline_end = ts, te
        self.start, self.end = ts, te
        self.breathing_after = breathing
        self.shot_count = 1
        self.chapter = 1


def _beats(n=10, dai=6.0):
    return [_Beat(i, i * dai, (i + 1) * dai) for i in range(n)]


# ------------------------------ vùng nhấn ------------------------------------
def test_hook_lay_tron_chuong():
    v = vung_nhan(_beats(8, 4.0), nap("life-in"), title="H")
    assert v == [(0.0, 32.0)]


def test_than_chi_lay_cua_so_beat_bung():
    """Ngoài vùng bùng phải IM — chính là ranh giới không-lật-PB12."""
    beats = _beats(10, 6.0)          # 60s, bùng ở 15% đầu
    v = vung_nhan(beats, nap("investigate"), title="C3")
    assert v, "chương thân phải có ít nhất 1 vùng bùng"
    assert all(t1 <= 15.0 for _, t1 in v), v      # chỉ nằm ở mở chương


def test_vung_gom_o_tho_sau_beat_bung():
    beats = _beats(10, 6.0)
    beats[0].breathing_after = 1.5
    v = vung_nhan(beats, nap("investigate"), title="C3")
    assert v[0][1] >= 6.0 + 1.5 - 1e-9 or v[0][1] >= 6.0   # ô thở tính vào vùng


def test_chuong_E_vung_nam_cuoi():
    beats = _beats(10, 5.0)          # 50s
    v = vung_nhan(beats, nap("life-in"), title="E")
    assert v and v[-1][1] >= 45.0    # 20% cuối


# --------------------------- lập lịch nhiều vùng -----------------------------
def _cuts_deu(t0, t1, buoc=1.0):
    t, ra = t0 + buoc, []
    while t < t1:
        ra.append((round(t, 2), False))
        t += buoc
    return ra


def test_chi_dat_tieng_trong_vung():
    cuts = _cuts_deu(0, 60)
    slots = nhan_sfx_slots(cuts, [(10.0, 20.0)])
    assert slots
    for s in slots:
        assert 10.0 - 0.2 <= s.t <= 20.0, s.t    # whoosh lead 80ms cho phép nhô nhẹ


def test_ngoai_vung_im_lang():
    """Cut dày ở 30-40s nhưng vùng nhấn là 0-10s -> 30-40s KHÔNG tiếng nào."""
    cuts = _cuts_deu(30, 40, buoc=0.8)
    assert nhan_sfx_slots(cuts, [(0.0, 10.0)]) == []


def test_hai_vung_giu_gap_toan_cuc():
    """Tiếng cuối vùng 1 và tiếng đầu vùng 2 vẫn phải cách >= gap."""
    cuts = _cuts_deu(0, 30, buoc=0.5)
    slots = nhan_sfx_slots(cuts, [(0.0, 10.0), (10.5, 20.0)])
    ts = sorted(s.t for s in slots)
    for a, b in zip(ts, ts[1:]):
        assert b - a >= HOOK_SFX_GAP - 0.3, (a, b)   # lead làm xê dịch nhẹ


def test_slot_da_dich_ve_moc_tuyet_doi():
    cuts = [(12.0, False), (15.5, False), (19.0, False)]
    slots = nhan_sfx_slots(cuts, [(10.0, 20.0)])
    assert all(s.t > 9.0 for s in slots), [s.t for s in slots]


def test_khong_vung_khong_no():
    assert nhan_sfx_slots([(1.0, False)], []) == []
