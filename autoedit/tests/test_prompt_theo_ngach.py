r"""CÂU LỆNH LLM PHẢI THEO NHÓM NGÁCH (user chốt 12/09: "prompt sai là sai hết").

Quy ước đã chốt (QĐ12–QĐ14, `docs/SEQUENCE.md`, `tests/test_ngach.py`): chỉ
LIFE IN · LIVING IN · TRAVEL DOCUMENTARY bắt buộc khai địa danh; ngách khác bỏ
trống và `tra()` tự tắt cửa geo. Địa danh CHÍNH LÀ biến mang ngách vào luồng —
không đẻ thêm khái niệm mới.

Hai chỗ còn chèn địa lý vào ngách KHÔNG gắn địa lý:

1. `lop4._SYS` mở đầu "đạo diễn phim tài liệu **du lịch** về {DIA_DANH}", địa
   danh rỗng thì thay bằng "địa danh trong lời"; kèm luật "neo=true trừ khi câu
   nói rõ về nơi khác" -> đo thật trên SH010: **neo=True 26/26 và 19/20 khối**.
   Cửa neo bật thì clip CÓ nhãn geo được +2 điểm và đi thẳng qua cửa L0.

2. `nap_ref_tap` khi tập KHÔNG khai quốc gia vẫn lấy `geo` do GLM đọc chữ trên
   màn hình -> 26/119 ref SH010 mang nhãn rác: `cardiac specialist`,
   `university of galway`, `diet soda & zero sugar drinks`.

A/B THẬT trên chương SH010 (2 lượt GLM mỗi bên, cùng lời thoại):

| Chương | Prompt hiện tại | Prompt trung tính |
|---|---|---|
| h (26 khối) | neo 26/26 · **41%** clip du lịch trong khay | neo 0/26 · **18%** |
| c1 (20 khối) | neo 19/20 · **52%** | neo 1/20 · **28%** |

Từ khoá hai bên tương đương; số thẻ ref/khối KHÔNG đổi (1,9–2,2) — ref mỏng là
luật cắt khay, việc khác.
"""

from __future__ import annotations

import pytest

from autoedit.offline import lop4
from autoedit.sotra import db as sdb


# ────────────────────────── câu lệnh 4 lớp ──────────────────────────

def test_co_dia_danh_thi_GIU_NGUYEN_cau_lenh_du_lich():
    """Life In không được đụng tới — ref của nó đang gánh cả tập."""
    s = lop4.cau_lenh("Nepal")
    assert "du lịch về Nepal" in s
    assert "neo=true trừ khi câu nói rõ về nơi khác" in s
    assert "neo=false" not in s


def test_khong_dia_danh_thi_BO_vai_dao_dien_du_lich():
    s = lop4.cau_lenh("")
    assert "du lịch" not in s
    assert "địa danh trong lời" not in s, "chèn địa danh ảo vào ngách không địa lý"
    assert "{DIA_DANH}" not in s, "còn sót chỗ thay biến"


def test_khong_dia_danh_thi_KHONG_ep_neo():
    s = lop4.cau_lenh("")
    assert "neo=false" in s
    assert "neo=true trừ khi câu nói rõ về nơi khác" not in s


def test_THAN_cau_lenh_giong_het_nhau_giua_hai_nhanh():
    """Chỉ đổi phần địa lý; luật 4 lớp là tài sản đã hiệu chỉnh, không được lệch."""
    a, b = lop4.cau_lenh("Nepal"), lop4.cau_lenh("")
    for doan in ("truc_chi  —", "ngu_canh  —", "khong_khi —", "truu_tuong=true"):
        assert doan in a and doan in b


def test_gan_lop_dung_dung_cau_lenh_theo_dia_danh():
    ghi = {}

    class _LLM:
        def complete(self, sys, body, model):
            ghi["sys"] = sys
            return model(chu_the_tap=[], khoi=[]), {}

    lop4.gan_lop(["câu một"], dia_danh="Nepal", llm=_LLM())
    assert ghi["sys"] == lop4.cau_lenh("Nepal")
    lop4.gan_lop(["câu một"], dia_danh="", llm=_LLM())
    assert ghi["sys"] == lop4.cau_lenh("")


# ────────────────────────── nhãn geo của ref ──────────────────────────

def test_geo_ref_khong_quoc_gia_thi_BO_nhan_doc_duoc():
    """Ngách không địa lý: chữ trên màn hình KHÔNG phải địa danh."""
    assert lop4_geo("", "university of galway") == ""
    assert lop4_geo("", "") == ""


def test_geo_ref_co_quoc_gia_thi_GIU_CA_HAI():
    assert lop4_geo("Nepal", "himalayas") == "nepal>himalayas"
    assert lop4_geo("ecuador", "") == "ecuador"


def lop4_geo(quoc_gia, geo_doc):
    from autoedit.sotra.hut import geo_ref

    return geo_ref(quoc_gia, geo_doc)


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    yield c
    c.close()


def _gia_lap(monkeypatch, doc_geo):
    import autoedit.sotra.hut as h
    from autoedit.sotra.canh import Canh
    from autoedit.sotra.doc_canh import DocRa

    monkeypatch.setattr("autoedit.sotra.canh.cat_canh",
                        lambda v, **k: [Canh(0.0, 4.0, False)])
    monkeypatch.setattr("autoedit.sotra.doc_canh.trich_anh",
                        lambda v, t0, t1, dich, **k: dich)
    monkeypatch.setattr("autoedit.sotra.doc_canh.doc_nhieu",
                        lambda al, **k: [DocRa(i=1, subject="senior drinking",
                                               geo=doc_geo)])
    return h


def test_nap_ref_ngach_KHONG_dia_danh_khong_de_lai_nhan_geo(conn, tmp_path, monkeypatch):
    h = _gia_lap(monkeypatch, "university of galway")
    (tmp_path / "ref 1.mp4").write_bytes(b"v")
    assert h.nap_ref_tap(conn, tmp_path, tap="SH010", quoc_gia="") == 1
    r = conn.execute("SELECT geo, subject FROM clip").fetchone()
    assert r["subject"] == "senior drinking", "vẫn phải đọc hình như cũ"
    assert r["geo"] == "", "nhãn geo rác -> +2 điểm neo cho clip không đáng"


def test_nap_ref_tap_CO_quoc_gia_giu_nguyen_hanh_vi(conn, tmp_path, monkeypatch):
    h = _gia_lap(monkeypatch, "himalayas")
    (tmp_path / "ref 1.mp4").write_bytes(b"v")
    h.nap_ref_tap(conn, tmp_path, tap="LI106", quoc_gia="Nepal")
    assert conn.execute("SELECT geo FROM clip").fetchone()["geo"] == "nepal>himalayas"
