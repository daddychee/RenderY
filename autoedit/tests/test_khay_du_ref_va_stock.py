r"""KHAY PHẢI ĐỦ REF VÀ ĐỦ NGUỒN STOCK (user chốt 12/09).

User: *"trong mỗi chương phải có đủ ref, và 2 nguồn stock"*.

ĐO TRƯỚC KHI CODE — SH010, 116 khối:

| | Số khối |
|---|---|
| đạt "≥3 ref + ≥2 nguồn stock" ở khay hiện tại | **2** |
| kho CÓ SẴN hàng để đạt | **97** |
| kho thiếu thật | 19 (11 khối ở chương c2) |

Tức 95/116 khối bị chính luật cắt khay làm mất, không phải thiếu dữ liệu:
khay 12 ô · mỗi tầng tối đa 6 · ref sàn 2 suất · pexels/pixabay giữ chỗ 1 ô
(envato không có suất nào vì không nằm trong `PHAT_NGUON`).

Mô phỏng "giữ chỗ trước, xếp điểm sau": SH010 **2 -> 97 khối đạt**, khay vẫn
đúng 12 ô. Life In không đổi vì cửa geo đã loại sạch stock từ trước — đo LI106
c1: cửa bật thì chỉ còn envato 171 · pexels 1 · pixabay 0 cho 31 khối.
"""

from __future__ import annotations

import pytest

from autoedit.sotra import db as sdb
from autoedit.sotra.tra import SAN_REF, tra

STOCK = ("envato", "pexels", "pixabay")
LOP = {"L0": [], "L1": ["market"], "L2": ["street"], "L3": ["morning"]}


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    yield c
    c.close()


def _them(c, nguon, i, ten, tap="T1", geo="nepal"):
    cid = (sdb.lam_id("ref", f"{tap}-ref 1", f"{i}.00-{i + 4}.00")
           if nguon == "ref" else f"{nguon}:{i}")
    sdb.them_clip(c, {"id": cid, "nguon": nguon, "tieu_de": f"{ten} ({i})",
                      "tap": tap if nguon == "ref" else "", "geo": geo,
                      "t0": float(i), "t1": float(i + 4)})
    return cid


def _kho_day(c, so_ref=8, so_stock=8):
    for i in range(so_ref):
        _them(c, "ref", i, "market street morning")
    for j, ng in enumerate(STOCK):
        for i in range(so_stock):
            _them(c, ng, 100 + j * 50 + i, "market street morning")


def _dem(ra):
    from collections import Counter

    return Counter(u["nguon"] for u in ra)


# ───────────────────────────── sàn ref ─────────────────────────────

def test_san_ref_la_ba():
    assert SAN_REF == 3


def test_khay_du_SAN_REF_khi_kho_co(conn):
    _kho_day(conn)
    ra = tra(conn, LOP, so=12, tap="T1")
    assert _dem(ra)["ref"] >= SAN_REF


def test_kho_it_ref_thi_KHONG_bia_them(conn):
    _kho_day(conn, so_ref=1)
    ra = tra(conn, LOP, so=12, tap="T1")
    assert _dem(ra)["ref"] == 1


# ──────────────────────── mỗi nguồn stock một ô ────────────────────────

def test_moi_nguon_stock_co_it_nhat_mot_o(conn):
    """envato trước đây không có suất nào — chỉ pexels/pixabay được giữ chỗ."""
    _kho_day(conn)
    d = _dem(tra(conn, LOP, so=12, tap="T1"))
    for ng in STOCK:
        assert d[ng] >= 1, f"khay thiếu hẳn nguồn {ng}"


def test_nguon_vang_mat_trong_kho_thi_thoi(conn):
    """Kho không có pixabay thì khay không có — không được lỗi."""
    for i in range(8):
        _them(conn, "ref", i, "market street morning")
    for i in range(8):
        _them(conn, "envato", 100 + i, "market street morning")
    d = _dem(tra(conn, LOP, so=12, tap="T1"))
    assert d["pixabay"] == 0 and d["envato"] >= 1 and d["ref"] >= SAN_REF


# ──────────────────────── khay không phình ────────────────────────

def test_khay_KHONG_vuot_qua_so_o_yeu_cau(conn):
    _kho_day(conn, so_ref=20, so_stock=20)
    for so in (8, 12, 16):
        ra = tra(conn, LOP, so=so, tap="T1")
        assert len(ra) <= so, f"khay {len(ra)} ô > {so} ô yêu cầu"


def test_khay_van_xep_theo_diem_giam_dan(conn):
    _kho_day(conn)
    diem = [u["diem"] for u in tra(conn, LOP, so=12, tap="T1")]
    assert diem == sorted(diem, reverse=True)


# ──────────────────── Life In: cửa geo vẫn phải thắng ────────────────────

def test_cua_geo_van_loai_stock_lech_vung(conn):
    """Giữ chỗ KHÔNG được phá rào geo: stock sai vùng vẫn phải bị loại."""
    for i in range(8):
        _them(conn, "ref", i, "market street morning", geo="nepal")
    for i in range(8):
        _them(conn, "envato", 100 + i, "market street morning", geo="ecuador")
    ra = tra(conn, LOP, so=12, tap="T1", geo_tap="Nepal")
    assert _dem(ra)["envato"] == 0, "stock Ecuador lọt vào tập Nepal"
    assert _dem(ra)["ref"] >= SAN_REF


# ─────────────── ref TRÙNG TIÊU ĐỀ vẫn phải đủ thẻ (đo 12/09) ───────────────
# Ref cắt theo cảnh nên tiêu đề rất ngắn và lặp: `woman speaking` ×3. `gop_ban_trung`
# gộp chúng về MỘT thẻ (bản còn lại nằm ở `ban_khac`), nên khay giữ chỗ 3 ref mà
# hiện ra 1. Đo trên SH010: 22 khối thiếu ref thì **22/22 rơi vì gộp**, kho không
# thiếu cảnh nào.

def test_ref_trung_tieu_de_van_du_the_phan_biet(conn):
    """Ca thật: 3 cảnh TRÙNG TÊN điểm cao chiếm hết suất, kho còn cảnh tên khác
    điểm thấp hơn — gộp xong khay chỉ còn 1 thẻ ref."""
    for i in range(3):                                   # điểm cao: trúng cả 2 từ
        cid = sdb.lam_id("ref", "T1-ref 1", f"{i}.00-{i + 3}.00")
        sdb.them_clip(conn, {"id": cid, "nguon": "ref", "tieu_de": "woman speaking",
                             "tap": "T1", "geo": "nepal", "t0": float(i),
                             "t1": float(i + 3)})
    for i, ten in enumerate(("woman at desk", "woman walking", "woman cooking")):
        cid = sdb.lam_id("ref", "T1-ref 2", f"{i}.00-{i + 3}.00")
        sdb.them_clip(conn, {"id": cid, "nguon": "ref", "tieu_de": ten, "tap": "T1",
                             "geo": "nepal", "t0": float(i), "t1": float(i + 3)})
    for j, ng in enumerate(STOCK):          # khay ĐẦY stock -> hết chỗ vá ref
        for i in range(6):
            _them(conn, ng, 200 + j * 20 + i, "woman speaking scene")
    ra = tra(conn, {"L0": [], "L1": ["woman speaking"], "L2": [], "L3": []},
             so=12, tap="T1")
    the_ref = [u for u in ra if u["nguon"] == "ref"]
    ten = [(u.get("tieu_de") or "").lower() for u in the_ref]
    assert len(the_ref) >= SAN_REF, f"gộp bản trùng nuốt mất sàn ref: {ten}"
    assert len(set(ten)) == len(ten), f"thẻ ref phải là cảnh KHÁC nhau: {ten}"
