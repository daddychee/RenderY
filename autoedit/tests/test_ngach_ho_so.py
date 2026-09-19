# -*- coding: utf-8 -*-
"""HỒ SƠ NGÁCH — file khai "ngách này quay ai, quay cái gì" (QĐ18, 18/09/2026).

Vì sao cần: cổng QĐ15 chặn cứng 422 khi ngách chưa khai nhân vật. Đo trên danh
bạ thật 18/09: **13/16 ngách chưa khai** — gồm cả X FILE (`N-003`) vừa mở. Cách
khai duy nhất đang có là biến môi trường `RENDERY_NGACH_NHAN_VAT`, mà câu báo
lỗi lại chỉ sang "trang Cài đặt" — **trang đó không còn trong giao diện đang
chạy**, chỉ còn trong `index_cu.html`. Tức là đang không có đường nào khai.

Hai thứ mới ở đây:

1. **"Không lọc theo người"** (user chốt 18/09). X FILE nói về ĐỒ VẬT, ép khai
   tuổi/chủng tộc là bịa ra luật cho một ngách không cần. Trước đây "đã khai"
   được suy ra từ "có nhân vật", nên không có cách nào nói "tôi cố ý không lọc".
2. **Hồ sơ là FILE trong kho dữ liệu**, không nhét `.env`: sửa được bằng giao
   diện, ghi được ai duyệt và duyệt lúc nào — `.env` không ghi nổi hai thứ đó.
"""
from __future__ import annotations

import json
import sqlite3

import pytest

from autoedit import ngach
from autoedit import ngach_ho_so as hs

NGACH_THAT = [                      # sao y danh bạ thật 18/09 (16 ngách, rút gọn)
    ("N-003", "X FILE", "khai_thac"),
    ("N-SENIOR-HEALTH", "SENIOR HEALTH", "khai_thac"),
    ("N-LIFE-IN", "LIFE IN", "mo_rong"),
    ("N-COOKING", "COOKING", "khai_thac"),
]


@pytest.fixture
def kho(tmp_path, monkeypatch):
    """Danh bạ giả + gốc kho giả. Không test nào chạm sổ thật."""
    f = tmp_path / "danh_ba.db"
    c = sqlite3.connect(f)
    c.execute("CREATE TABLE ngach(ma TEXT PRIMARY KEY, ten_chuan TEXT, "
              "trang_thai TEXT, ghi_chu TEXT, tao_luc TEXT)")
    c.executemany("INSERT INTO ngach(ma, ten_chuan, trang_thai) VALUES(?,?,?)",
                  NGACH_THAT)
    c.commit()
    c.close()
    monkeypatch.setenv("RENDERY_DANH_BA", str(f))
    monkeypatch.delenv("RENDERY_NGACH_NHAN_VAT", raising=False)
    monkeypatch.setattr(hs, "resolve_data_root", lambda *a, **k: tmp_path)
    return tmp_path


def _hs(ma="N-003", **kw):
    d = {"ma": ma, "ten": "X FILE", "loc_nguoi": False, "nhan_vat": {},
         "vat_the": ["duct tape"], "nguoi_duyet": "haint"}
    d.update(kw)
    return d


# ------------------------------------------------------------ đọc / ghi file

def test_KHONG_dung_kho_that(kho):
    assert hs.thu_muc() == kho / "ho_so_ngach"
    assert "AutoEdit" not in str(hs.thu_muc())


def test_luu_roi_doc_lai_ra_dung(kho):
    hs.luu(_hs())
    d = hs.doc("N-003")
    assert d["ma"] == "N-003" and d["loc_nguoi"] is False
    assert d["vat_the"] == ["duct tape"]


def test_luu_ghi_lai_NGUOI_DUYET_va_NGAY(kho):
    """`.env` không ghi nổi hai thứ này — đó là lý do hồ sơ thành file."""
    hs.luu(_hs())
    d = hs.doc("N-003")
    assert d["nguoi_duyet"] == "haint"
    from datetime import datetime
    assert datetime.fromisoformat(d["duyet_luc"]).year == datetime.now().year


def test_chua_co_ho_so_thi_doc_ra_None(kho):
    assert hs.doc("N-003") is None


def test_file_hong_thi_coi_nhu_CHUA_KHAI_chu_khong_no(kho):
    hs.thu_muc().mkdir(parents=True, exist_ok=True)
    (hs.thu_muc() / "N-003.json").write_text("{ day khong phai json", encoding="utf-8")
    assert hs.doc("N-003") is None


def test_ma_bay_KHONG_thoat_ra_khoi_thu_muc(kho):
    """Mã đi từ HTTP vào — không được để nó trỏ ra ngoài kho."""
    assert hs.doc("../../../etc/passwd") is None
    with pytest.raises(ValueError):
        hs.luu(_hs(ma="../ngoai"))


def test_vat_the_duoc_lam_sach(kho):
    hs.luu(_hs(vat_the=["  Duct Tape ", "duct tape", "FORKLIFT", "", "  "]))
    assert hs.doc("N-003")["vat_the"] == ["duct tape", "forklift"]


def test_liet_ke_tra_moi_ho_so(kho):
    hs.luu(_hs())
    hs.luu(_hs(ma="N-COOKING", ten="COOKING"))
    assert {d["ma"] for d in hs.liet_ke()} == {"N-003", "N-COOKING"}


def test_luu_hai_lan_khong_de_lai_file_tam(kho):
    hs.luu(_hs())
    hs.luu(_hs(vat_the=["battery"]))
    con = sorted(p.name for p in hs.thu_muc().iterdir())
    assert con == ["N-003.json"], con
    assert hs.doc("N-003")["vat_the"] == ["battery"]


# ------------------------------------- nối vào cổng nộp tập (ngach.py, QĐ15)

def test_KHONG_LOC_NGUOI_van_tinh_la_DA_KHAI(kho):
    """Trọng tâm QĐ18: ngách đồ vật khai rõ «không lọc» thì phải qua cổng."""
    hs.luu(_hs(loc_nguoi=False))
    assert ngach.da_khai_nhan_vat("X FILE") is True
    assert ngach.nhan_vat("X FILE") == {}, "không lọc mà vẫn trả bộ lọc"


def test_chua_co_ho_so_thi_VAN_BI_CHAN_nhu_cu(kho):
    assert ngach.da_khai_nhan_vat("X FILE") is False


def test_ho_so_co_khai_nguoi_thi_tra_dung_bo_loc(kho):
    hs.luu(_hs(ma="N-COOKING", ten="COOKING", loc_nguoi=True,
               nhan_vat={"tuoi": ["adult"], "chung_toc": ["asian"]}))
    assert ngach.nhan_vat("COOKING") == {"tuoi": ["adult"], "chung_toc": ["asian"]}
    assert ngach.da_khai_nhan_vat("COOKING") is True


def test_tra_theo_TEN_hay_MA_deu_ra(kho):
    """Form nộp tập gửi TÊN («X FILE»), hồ sơ lưu theo MÃ («N-003»)."""
    hs.luu(_hs())
    assert ngach.da_khai_nhan_vat("N-003") is True
    assert ngach.da_khai_nhan_vat("x file") is True


def test_ho_so_DE_LEN_bien_moi_truong(kho, monkeypatch):
    """Hồ sơ là thứ NGƯỜI duyệt trên màn hình — nó thắng `.env` gõ tay."""
    monkeypatch.setenv("RENDERY_NGACH_NHAN_VAT",
                       json.dumps({"N-003": {"tuoi": ["older"]}}))
    hs.luu(_hs(loc_nguoi=False))
    assert ngach.nhan_vat("X FILE") == {}


def test_ho_so_DE_LEN_mac_dinh_trong_code(kho):
    hs.luu(_hs(ma="N-SENIOR-HEALTH", ten="SENIOR HEALTH", loc_nguoi=True,
               nhan_vat={"tuoi": ["older"], "chung_toc": ["white", "black"]}))
    assert ngach.nhan_vat("SENIOR HEALTH")["chung_toc"] == ["white", "black"]


def test_NGACH_KHAC_khong_bi_anh_huong(kho):
    """Rào chống hồi quy: SENIOR HEALTH chưa có hồ sơ thì giữ nguyên mặc định cũ."""
    hs.luu(_hs())
    assert ngach.nhan_vat("SENIOR HEALTH") == {"tuoi": ["older"], "chung_toc": ["white"]}
    assert ngach.da_khai_nhan_vat("LIFE IN") is True      # geo, như cũ


def test_kho_hong_thi_KHONG_keo_ca_tool_chet(kho, monkeypatch):
    """Gốc kho biến mất -> coi như chưa có hồ sơ, không ném lên tận form nộp."""
    monkeypatch.setattr(hs, "resolve_data_root", lambda *a, **k: kho / "khong-ton-tai")
    assert hs.doc("N-003") is None
    assert hs.liet_ke() == []


def test_CA_SUITE_khong_doc_ho_so_that(tmp_path):
    """Không dùng fixture `kho` — chứng minh rào ở conftest.py có hiệu lực."""
    assert "AutoEdit" not in str(hs.thu_muc())
    assert hs.liet_ke() == []


# --------------------------- NƠI CHỐN ngách chấp nhận (QĐ18b, 19/09)

def test_khai_dia_ly_cho_phep(kho):
    hs.luu(_hs(ma="N-SENIOR-HEALTH", ten="SENIOR HEALTH", dia_ly=["USA", " usa ", "uk"]))
    assert hs.doc("N-SENIOR-HEALTH")["dia_ly"] == ["usa", "uk"]
    assert ngach.dia_ly("SENIOR HEALTH") == ["usa", "uk"]


def test_khong_khai_thi_rong(kho):
    hs.luu(_hs())
    assert ngach.dia_ly("X FILE") == []
    assert ngach.dia_ly("COOKING") == []       # chưa có hồ sơ


def test_dia_ly_khong_lam_hong_ho_so_cu(kho):
    """Hồ sơ lưu trước khi có trường này -> đọc ra [] chứ không nổ."""
    hs.thu_muc().mkdir(parents=True, exist_ok=True)
    (hs.thu_muc() / "N-003.json").write_text(
        '{"ma": "N-003", "loc_nguoi": false, "vat_the": ["x"]}', encoding="utf-8")
    assert ngach.dia_ly("X FILE") == []
