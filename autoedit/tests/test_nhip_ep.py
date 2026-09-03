"""Ép nhịp — tầng dang dở từ 14/07 (tempo map chỉ khai + cảnh báo, không ép).

Bằng chứng cần ép: đo 02/09 hai chương CÙNG TẬP ra nhịp cụm 6,5× và 2,3× —
chênh gấp ba, ngẫu nhiên theo hứng LLM. Đòn bẩy: beat.shot_count (assembler
chia đều beat thành N khoảng — N do mình quyết là độ dài shot do mình quyết).
"""

from __future__ import annotations

import pytest

from autoedit.nhip.ep import (
    MIN_SHOT_DUR,
    ap_dung,
    lap_ke_hoach,
    vai_tro_chuong,
)
from autoedit.nhip.profile import nap


class _Beat:
    def __init__(self, bid, ts, te, breathing=0.0, shot_count=1, chapter=1):
        self.beat_id = bid
        self.timeline_start, self.timeline_end = ts, te
        self.start, self.end = ts, te
        self.breathing_after = breathing
        self.shot_count = shot_count
        self.chapter = chapter


def _beats_deu(n=10, dai=6.0):
    """n beat đều nhau `dai` giây — đúng bệnh 'đều tăm tắp' cần chữa."""
    return [_Beat(i, i * dai, (i + 1) * dai) for i in range(n)]


# ------------------------------ vai trò chương -------------------------------
def test_vai_tro_theo_quy_uoc_thu_muc():
    assert vai_tro_chuong("H") == "hook"
    assert vai_tro_chuong("h") == "hook"
    assert vai_tro_chuong("E") == "ket"
    assert vai_tro_chuong("C3") == "than"
    assert vai_tro_chuong("chuong_ref") == "than"


# ------------------------------ ép thân --------------------------------------
def test_beat_dai_bi_chia_theo_trung_vi_ho_so():
    """Beat 6s với hồ sơ trung vị 2.5s phải thành ~2-3 shot, hết cảnh 1 beat 1 shot."""
    hs = nap("investigate")            # than_trung_vi=2.5
    kh = lap_ke_hoach(_beats_deu(10, dai=6.0), hs, title="C3")
    giua = [kh.shot_count[i] for i in range(3, 8)]      # tránh vùng bùng mở chương
    assert all(n >= 2 for n in giua), giua
    assert kh.du_bao_trung_vi <= 3.5


def test_bung_mo_chuong_day_hon_nen():
    """15% đầu chương thân = vùng bùng: shot dày hơn phần nền (đo thật: đợt bùng
    trùng điểm chuyển ý; mở chương = điểm chuyển trong video ghép)."""
    hs = nap("investigate")
    beats = _beats_deu(10, dai=6.0)
    kh = lap_ke_hoach(beats, hs, title="C3")
    assert kh.bung_beat_ids, "phải có beat bùng ở mở chương"
    assert kh.shot_count[kh.bung_beat_ids[0]] > kh.shot_count[5]


def test_o_tho_luon_1_hinh_giu():
    """Luật d2 THẮNG hồ sơ: beat mang ô thở không bị chia dù dài."""
    hs = nap("investigate")
    beats = _beats_deu(6, dai=8.0)
    beats[3].breathing_after = 2.0
    kh = lap_ke_hoach(beats, hs, title="C2")
    assert kh.shot_count[3] == 1


def test_khong_vi_pham_san_MIN_SHOT_DUR():
    """Không bao giờ đề xuất shot ngắn hơn sàn cứng 0.7s của máy."""
    hs = nap("life-in")                # hook_trung_vi=1.0
    beats = _beats_deu(8, dai=1.5)     # beat ngắn
    kh = lap_ke_hoach(beats, hs, title="H")
    for b in beats:
        n = kh.shot_count[b.beat_id]
        assert 1.5 / n >= MIN_SHOT_DUR - 1e-9, (b.beat_id, n)


# ------------------------------ hook -----------------------------------------
def test_hook_no_day_dac_roi_tha():
    """Kiểu 'nổ' (Fern info): 2/3 đầu dày, đuôi giãn — đo thật 57→5 cắt/phút."""
    hs = nap("life-in")                # hook_kieu=no
    beats = _beats_deu(9, dai=4.0)
    kh = lap_ke_hoach(beats, hs, title="H")
    assert kh.shot_count[1] > kh.shot_count[8]


def test_hook_leo_thua_roi_day_dan():
    """Kiểu 'leo' (Fern điều tra, Hansa 9→19→29): đỉnh ở CUỐI hook."""
    hs = nap("investigate")            # hook_kieu=leo
    beats = _beats_deu(9, dai=4.0)
    kh = lap_ke_hoach(beats, hs, title="H")
    assert kh.shot_count[8] > kh.shot_count[0]


def test_hook_lam_shot_ngan_hon_han_than():
    hs = nap("life-in")
    hook = lap_ke_hoach(_beats_deu(8, dai=5.0), hs, title="H")
    than = lap_ke_hoach(_beats_deu(8, dai=5.0), hs, title="C2")
    assert hook.du_bao_trung_vi < than.du_bao_trung_vi


# ------------------------------ bùng kết -------------------------------------
def test_chuong_E_co_bung_ket():
    """4/5 video đo được tăng tốc phút chót — chương E nhận bùng ở 20% cuối."""
    hs = nap("life-in")                # bung_ket=True
    beats = _beats_deu(10, dai=5.0)
    kh = lap_ke_hoach(beats, hs, title="E")
    assert 9 in kh.bung_beat_ids or 8 in kh.bung_beat_ids


# ------------------------------ ap_dung --------------------------------------
class _Inputs:
    channel = "investigate"


class _Project:
    def __init__(self, beats, title="C3"):
        self.beats = beats
        self.title = title
        self.inputs = _Inputs()


def test_ap_dung_chi_nang_khong_ha():
    """LLM đã đọc nội dung — nó đòi 5 shot cho beat montage thì giữ 5, hồ sơ chỉ
    đảm bảo SÀN mật độ."""
    beats = _beats_deu(6, dai=6.0)
    beats[4].shot_count = 5
    p = _Project(beats)
    ap_dung(p, nap("investigate"))
    assert beats[4].shot_count == 5
    assert beats[3].shot_count >= 2       # beat thường được nâng


def test_ap_dung_o_tho_ep_ve_1_ke_ca_llm_doi_nhieu():
    beats = _beats_deu(6, dai=6.0)
    beats[2].breathing_after = 1.5
    beats[2].shot_count = 4               # LLM đòi 4 — luật d2 vẫn thắng
    p = _Project(beats)
    ap_dung(p, nap("investigate"))
    assert beats[2].shot_count == 1


def test_ap_dung_ghi_du_bao_vao_canh_bao():
    p = _Project(_beats_deu(8, dai=5.0))
    ra = ap_dung(p, nap("investigate"))
    assert any("dự báo trung vị" in x for x in ra)


def test_beat_chua_co_timeline_thi_bo_qua_em():
    """Gọi nhầm trước cut (chưa có timeline) → cảnh báo, không nổ, không sửa gì."""
    b = _Beat(0, 0, 0)
    b.timeline_start = b.timeline_end = None
    b.start = b.end = 0
    kh = lap_ke_hoach([b], nap("life-in"), title="C1")
    assert kh.shot_count == {} or all(v == 1 for v in kh.shot_count.values())
