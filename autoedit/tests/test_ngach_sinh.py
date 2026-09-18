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
                            + [f"tu{i}" for i in range(40)]})
    d = ns.de_xuat("X FILE", DO_VAT, llm=llm)
    assert d["vat_the"][:2] == ["duct tape", "forklift"]
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
