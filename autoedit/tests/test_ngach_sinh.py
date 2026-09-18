# -*- coding: utf-8 -*-
"""SINH ĐỀ XUẤT hồ sơ ngách từ pool Radary (QĐ18 bước 4, 18/09/2026).

LUẬT CỨNG 4 — *Python đo, LLM hiểu/sinh, không đảo vai*. Nên ở đây:

* **Python quyết** "ngách này có lọc theo người không", bằng tỉ lệ tiêu đề
  nhắc tới người. Đo thật trên pool 18/09 (600 tiêu đề/ngách):

      X FILE 16.3% · COOKING 8.5% · STORM 11.2% · SPACE 19.8%
      LIFE IN 29.3% || RETIREMENT 50.0% · SENIOR HEALTH 60.3%

  Khe hở giữa 29.3% và 50.0% rộng, nên ngưỡng **40%** nằm giữa khoảng trống
  thật chứ không phải con số tôi bịa cho tròn.
* **LLM chỉ sinh TỪ VỰNG** (quay cái gì) và, khi đã lọc người, gợi ý tuổi /
  chủng tộc. Nó không được quyền lật cờ `loc_nguoi`.
"""
from __future__ import annotations

import pytest

from autoedit import ngach_sinh as ns


class LLMGia:
    """LLM giả — không chạm mạng. `tra` là thứ nó sẽ trả về."""

    def __init__(self, tra=None, no=None):
        self.tra, self.no, self.goi = tra, no, []

    def complete(self, system, user, output_model, context=None):
        self.goi.append({"system": system, "user": user})
        if self.no:
            raise self.no
        return output_model(**(self.tra or {})), {}


DO_VAT = ["How Duct Tape Is Made", "Why Do Batteries Die", "Every Yogurt Explained"]
CO_NGUOI = ["What seniors eat", "Why grandma saves foil", "How people age well"]


# --------------------------------------------------------------- Python đo

def test_do_nguoi_dem_dung_tieu_de_nhac_toi_nguoi(_kho):
    d = ns.do_nguoi(DO_VAT + CO_NGUOI)
    assert d["tong"] == 6 and d["co_nguoi"] == 3
    assert d["ty_le"] == pytest.approx(0.5)


def test_do_nguoi_pool_rong(_kho):
    assert ns.do_nguoi([])["ty_le"] == 0.0


def test_nguong_40_phan_tram__so_do_that_18_09(_kho):
    """Bảng số thật ở docstring module — ngưỡng phải tách đúng nó."""
    assert ns.nen_loc_nguoi(0.163) is False       # X FILE
    assert ns.nen_loc_nguoi(0.085) is False       # COOKING
    assert ns.nen_loc_nguoi(0.293) is False       # LIFE IN
    assert ns.nen_loc_nguoi(0.500) is True        # RETIREMENT
    assert ns.nen_loc_nguoi(0.603) is True        # SENIOR HEALTH


# ------------------------------------------------------------ LLM sinh từ

def test_LLM_KHONG_duoc_quyet_co_loc_nguoi_hay_khong(_kho):
    """LLM trả về tuổi/chủng tộc, nhưng số đo nói ngách đồ vật -> KHÔNG lọc."""
    llm = LLMGia({"vat_the": ["duct tape"], "tuoi": ["older"],
                  "chung_toc": ["white"]})
    d = ns.de_xuat("X FILE", DO_VAT, llm=llm)
    assert d["loc_nguoi"] is False
    assert d["nhan_vat"] == {}, "LLM lật được cờ lọc người"


def test_da_lo_c_nguoi_thi_giu_tuoi_chung_toc_cua_LLM(_kho):
    llm = LLMGia({"vat_the": ["kitchen"], "tuoi": ["older"], "chung_toc": ["white"]})
    d = ns.de_xuat("SENIOR HEALTH", CO_NGUOI * 4, llm=llm)
    assert d["loc_nguoi"] is True
    assert d["nhan_vat"] == {"tuoi": ["older"], "chung_toc": ["white"]}


def test_vat_the_lam_sach_va_cat_tran(_kho):
    llm = LLMGia({"vat_the": ["  Duct Tape ", "duct tape", "FORKLIFT"]
                            + [f"tu{i:03d}" for i in range(200)]})
    d = ns.de_xuat("X FILE", DO_VAT, llm=llm)
    assert d["vat_the"][:2] == ["duct tape", "forklift"], d["vat_the"][:4]
    assert len(d["vat_the"]) == ns.TRAN_VAT_THE


def test_tra_ve_SO_DO_de_man_hinh_in_so_that(_kho):
    """Màn hình phải in được «98/600 tiêu đề» chứ không phải câu chữ của LLM."""
    d = ns.de_xuat("X FILE", DO_VAT + CO_NGUOI, llm=LLMGia({"vat_the": ["x"]}))
    assert d["do_nguoi"]["co_nguoi"] == 3 and d["do_nguoi"]["tong"] == 6


def test_pool_rong_thi_bao_ro_chu_khong_goi_LLM(_kho):
    llm = LLMGia({"vat_the": ["x"]})
    with pytest.raises(ValueError, match="pool"):
        ns.de_xuat("X FILE", [], llm=llm)
    assert llm.goi == [], "gọi LLM khi không có gì để đọc — tiêu tiền vô ích"


def test_LLM_chet_thi_nem_len_cho_caller_xu_ly(_kho):
    llm = LLMGia(no=RuntimeError("GLM 500"))
    with pytest.raises(RuntimeError):
        ns.de_xuat("X FILE", DO_VAT, llm=llm)


def test_tieu_de_duoc_dua_vao_prompt(_kho):
    llm = LLMGia({"vat_the": ["x"]})
    ns.de_xuat("X FILE", DO_VAT, llm=llm)
    assert "Duct Tape" in llm.goi[0]["user"]


@pytest.fixture
def _kho():
    """Chỗ giữ chỗ — module này không chạm đĩa, nhưng giữ khuôn chung."""
    return None


def test_LLM_tra_gia_tri_NGOAI_kho_thi_bi_loai(_kho):
    """Kho chỉ có tuoi ∈ {none,older,young,mixed,middle,child} và chung_toc ∈
    {none,white,unclear,asian,black,mixed,latino} (đo 18/09). LLM trả "elderly"
    nghe rất hợp lý mà lọc ra ĐÚNG 0 clip — prompt dặn thôi không đủ, phải chặn.
    """
    llm = LLMGia({"vat_the": ["x"], "tuoi": ["elderly", "older"],
                  "chung_toc": ["caucasian"]})
    d = ns.de_xuat("SENIOR HEALTH", CO_NGUOI * 4, llm=llm)
    assert d["nhan_vat"] == {"tuoi": ["older"]}, d["nhan_vat"]


# ------------------------------------- sinh NHIỀU LƯỢT rồi giữ phần lặp lại
# Đo thật trên pool X FILE 18/09: sinh 4 lượt ra **59 từ khoá khác nhau**, chỉ 5
# từ hiện cả 4 lượt, 37 từ hiện đúng 1 lượt. Pool có cả đồ vật lẫn đồ ăn, mỗi
# lượt GLM bám vào một nửa. Một lượt = một lá thăm; người duyệt không có cách
# nào biết mình đang xem lá nào.

class LLMNhieuLuot:
    """Mỗi lần gọi trả một kết quả khác — đúng hành vi thật của GLM."""

    def __init__(self, day, no_tu_lan=None):
        self.day, self.no_tu_lan, self.lan = list(day), no_tu_lan, 0

    def complete(self, system, user, output_model, context=None):
        self.lan += 1
        if self.no_tu_lan is not None and self.lan >= self.no_tu_lan:
            raise RuntimeError("GLM 500")
        return output_model(**self.day[(self.lan - 1) % len(self.day)]), {}


def test_giu_tu_LAP_LAI_bo_tu_chi_hien_mot_luot(_kho):
    llm = LLMNhieuLuot([
        {"vat_the": ["duct tape", "forklift", "chi lan 1"]},
        {"vat_the": ["duct tape", "forklift", "chi lan 2"]},
        {"vat_the": ["duct tape", "chi lan 3"]},
    ])
    d = ns.de_xuat("X FILE", DO_VAT, llm=llm, so_lan=3)
    assert llm.lan == 3, "chưa gọi đủ số lượt"
    assert d["vat_the"] == ["duct tape", "forklift"]


def test_xep_theo_DO_ON_DINH_giam_dan(_kho):
    llm = LLMNhieuLuot([
        {"vat_the": ["hai luot", "ba luot"]},
        {"vat_the": ["ba luot"]},
        {"vat_the": ["hai luot", "ba luot"]},
    ])
    d = ns.de_xuat("X FILE", DO_VAT, llm=llm, so_lan=3)
    assert d["vat_the"] == ["ba luot", "hai luot"]
    assert d["lap_lai"] == {"ba luot": 3, "hai luot": 2}
    assert d["so_lan"] == 3


def test_mot_luot_thi_KHONG_loc_mat_het(_kho):
    """so_lan=1 mà vẫn đòi lặp 2 lần thì kết quả rỗng trơn."""
    llm = LLMNhieuLuot([{"vat_the": ["duct tape", "forklift"]}])
    d = ns.de_xuat("X FILE", DO_VAT, llm=llm, so_lan=1)
    assert d["vat_the"] == ["duct tape", "forklift"]


def test_tran_tu_khoa_nang_len_80(_kho):
    assert ns.TRAN_VAT_THE >= 80
    llm = LLMNhieuLuot([{"vat_the": [f"tu {i}" for i in range(200)]}])
    d = ns.de_xuat("X FILE", DO_VAT, llm=llm, so_lan=1)
    assert len(d["vat_the"]) == ns.TRAN_VAT_THE


def test_mot_luot_CHET_van_dung_duoc_cac_luot_con_lai(_kho):
    """Hỏng lượt 3 mà vứt cả 2 lượt đã trả tiền là phí."""
    llm = LLMNhieuLuot([
        {"vat_the": ["duct tape", "forklift"]},
        {"vat_the": ["duct tape", "forklift"]},
    ], no_tu_lan=3)
    d = ns.de_xuat("X FILE", DO_VAT, llm=llm, so_lan=3)
    assert d["vat_the"] == ["duct tape", "forklift"]
    assert d["so_lan"] == 2, "phải báo số lượt THẬT đã chạy"


def test_CHET_HET_cac_luot_thi_nem_len_caller(_kho):
    llm = LLMNhieuLuot([{"vat_the": ["x"]}], no_tu_lan=1)
    with pytest.raises(RuntimeError):
        ns.de_xuat("X FILE", DO_VAT, llm=llm, so_lan=3)


def test_nhan_vat_GOP_ca_cac_luot(_kho):
    """Khác từ khoá: tuổi/chủng tộc lấy từ bộ 6-7 giá trị đóng nên ổn định sẵn,
    lọc theo lặp lại chỉ tổ làm rỗng bộ lọc của ngách quay người."""
    llm = LLMNhieuLuot([
        {"vat_the": ["x"], "tuoi": ["older"], "chung_toc": ["white"]},
        {"vat_the": ["x"], "tuoi": ["older"], "chung_toc": ["black"]},
    ])
    d = ns.de_xuat("SENIOR HEALTH", CO_NGUOI * 4, llm=llm, so_lan=2)
    assert d["nhan_vat"]["tuoi"] == ["older"]
    assert set(d["nhan_vat"]["chung_toc"]) == {"white", "black"}
