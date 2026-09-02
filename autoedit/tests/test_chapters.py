"""Test nhận diện chương theo quy ước OUTLIERY — H / C<số> / E.

Thứ tự chương là thứ dễ sai mà hậu quả nặng nhất: dựng nhầm thứ tự thì phải dựng
lại cả tập. Sắp theo tên là SAI CẢ HAI ĐẦU ("E" trước "H", "C10" trước "C2") nên
test khoá chặt phần này.
"""

from __future__ import annotations

import pytest

from autoedit.web.chapters import (
    THU_MUC_CON,
    doc_chuong,
    phan_tich_ten,
    thu_muc_rendery,
    tom_tat,
)


def _tap(root, ten="IN002", chuong=("H", "C1", "C2", "E"), du=True, srt=False):
    """Dựng 1 thư mục tập đúng quy ước: <tập>/RenderY/{H,C1,...}."""
    goc = root / ten / THU_MUC_CON
    for c in chuong:
        d = goc / c
        d.mkdir(parents=True)
        (d / "script.txt").write_text("xin chào", encoding="utf-8")
        if du:
            (d / "voice.mp3").write_bytes(b"\x00" * 10)
        if srt:
            (d / "voice.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nx\n",
                                         encoding="utf-8")
    return root / ten


# ------------------------------ phan_tich_ten -------------------------------
def test_nhan_dung_ky_hieu():
    assert phan_tich_ten("H")[:2] == ("H", 0)
    assert phan_tich_ten("C1")[:2] == ("C1", 1)
    assert phan_tich_ten("C12")[:2] == ("C12", 12)
    assert phan_tich_ten("E")[0] == "E"


def test_khong_phan_biet_hoa_thuong():
    assert phan_tich_ten("h")[0] == "H"
    assert phan_tich_ten("c3")[0] == "C3"
    assert phan_tich_ten("e")[0] == "E"


def test_nhan_chuan_doc_duoc():
    assert phan_tich_ten("H")[2] == "Hook"
    assert phan_tich_ten("C5")[2] == "Chương 5"
    assert phan_tich_ten("E")[2] == "Kết"


def test_tu_choi_ten_sai_quy_uoc():
    """Quy ước CHẶT (user chốt 30/08) — tên khác bị báo lỗi, không đoán bừa."""
    for xau in ("ch01", "chapter1", "hook", "clue 1", "C", "C0", "CC1", "1", "", "E2"):
        assert phan_tich_ten(xau) is None, f"'{xau}' lẽ ra phải bị từ chối"


# ------------------------------ THỨ TỰ --------------------------------------
def test_thu_tu_H_truoc_C_truoc_E(tmp_path):
    """Sắp theo tên thì 'E' đứng trước 'H' — phải theo khoá thứ tự."""
    tap = _tap(tmp_path, chuong=("E", "C2", "H", "C1"))
    chuong, loi = doc_chuong(tap)
    assert [c.ma for c in chuong] == ["H", "C1", "C2", "E"]
    assert loi == []


def test_C10_dung_SAU_C2(tmp_path):
    """Sắp theo tên thì 'C10' đứng trước 'C2' — phải so theo SỐ."""
    tap = _tap(tmp_path, chuong=("C1", "C2", "C10", "C11"))
    assert [c.ma for c in doc_chuong(tap)[0]] == ["C1", "C2", "C10", "C11"]


def test_chi_co_hook_va_ket(tmp_path):
    tap = _tap(tmp_path, chuong=("E", "H"))
    assert [c.ma for c in doc_chuong(tap)[0]] == ["H", "E"]


# ------------------------------ báo lỗi -------------------------------------
def test_thieu_thu_muc_RenderY(tmp_path):
    (tmp_path / "IN002").mkdir()
    chuong, loi = doc_chuong(tmp_path / "IN002")
    assert chuong == []
    assert any(THU_MUC_CON in x for x in loi)


def test_RenderY_trong(tmp_path):
    (tmp_path / "IN002" / THU_MUC_CON).mkdir(parents=True)
    chuong, loi = doc_chuong(tmp_path / "IN002")
    assert chuong == [] and any("trống" in x for x in loi)


def test_ten_sai_bi_bao_ro_ten_nao(tmp_path):
    tap = _tap(tmp_path, chuong=("H", "C1"))
    (tap / THU_MUC_CON / "clue 1").mkdir()
    chuong, loi = doc_chuong(tap)
    assert [c.ma for c in chuong] == ["H", "C1"]        # chương đúng vẫn nhận
    assert any("clue 1" in x and "sai quy ước" in x for x in loi)


def test_bao_thieu_file_kem_ten_chuong(tmp_path):
    tap = _tap(tmp_path, chuong=("H", "C1"), du=False)   # không có voice
    _, loi = doc_chuong(tap)
    assert any("Hook" in x and "thiếu voice" in x for x in loi)
    assert any("Chương 1" in x and "thiếu voice" in x for x in loi)


def test_bat_trung_ma_chuong(tmp_path):
    """'C1' và 'C01' cùng ra mã C1 — không bắt thì dựng sai thứ tự lặng lẽ.

    (Trên Windows 'c1' và 'C1' là CÙNG một thư mục nên không tạo được để test;
    'C01' là ca trùng thật sự có thể xảy ra.)
    """
    tap = _tap(tmp_path, chuong=("H", "C1"))
    d = tap / THU_MUC_CON / "C01"
    d.mkdir()
    (d / "script.txt").write_text("x", encoding="utf-8")
    (d / "voice.mp3").write_bytes(b"\x00")
    _, loi = doc_chuong(tap)
    assert any("Trùng mã C1" in x for x in loi)


def test_bo_qua_thu_muc_an_va_file_le(tmp_path):
    tap = _tap(tmp_path, chuong=("H", "C1"))
    (tap / THU_MUC_CON / ".tam").mkdir()
    (tap / THU_MUC_CON / "ghi-chu.txt").write_text("x", encoding="utf-8")
    chuong, loi = doc_chuong(tap)
    assert [c.ma for c in chuong] == ["H", "C1"] and loi == []


# ------------------------------ đường dẫn -----------------------------------
def test_nhan_ca_duong_dan_tap_lan_RenderY(tmp_path):
    tap = _tap(tmp_path)
    assert thu_muc_rendery(tap).name == THU_MUC_CON
    # đã trỏ sẵn vào RenderY thì không lồng thêm một tầng nữa
    assert thu_muc_rendery(tap / THU_MUC_CON) == tap / THU_MUC_CON
    assert [c.ma for c in doc_chuong(tap / THU_MUC_CON)[0]] == ["H", "C1", "C2", "E"]


# ------------------------------ tom_tat -------------------------------------
def test_tom_tat_cho_UI(tmp_path):
    tap = _tap(tmp_path, ten="LI001", chuong=("H", "C1", "E"), srt=True)
    d = tom_tat(tap)
    assert d["tap"] == "LI001" and d["so_chuong"] == 3
    assert d["san_sang"] is True and d["loi"] == []
    assert [c["ma"] for c in d["chuong"]] == ["H", "C1", "E"]
    assert all(c["srt"] and c["du_file"] for c in d["chuong"])


def test_tom_tat_bao_chua_san_sang_khi_thieu(tmp_path):
    tap = _tap(tmp_path, chuong=("H",), du=False)
    d = tom_tat(tap)
    assert d["san_sang"] is False and d["loi"]


def test_tom_tat_khong_co_srt_van_san_sang(tmp_path):
    """.srt là tuỳ chọn — thiếu thì align dùng whisper."""
    d = tom_tat(_tap(tmp_path, chuong=("H", "C1"), srt=False))
    assert d["san_sang"] is True
    assert all(c["srt"] is False for c in d["chuong"])


def test_tom_tat_nhac_khi_thieu_srt(tmp_path):
    """Thiếu .srt KHÔNG chặn nhưng phải báo TRƯỚC khi nộp: whisper chậm hơn và
    khớp chữ kém hơn. Job từng chết 24 phút sau vì lỗi này không hiện sớm."""
    d = tom_tat(_tap(tmp_path, chuong=("H", "C1"), srt=False))
    assert d["san_sang"] is True
    assert len(d["nhac"]) == 1
    assert "Hook" in d["nhac"][0] and "Chương 1" in d["nhac"][0]


def test_tom_tat_khong_nhac_khi_du_srt(tmp_path):
    d = tom_tat(_tap(tmp_path, chuong=("H", "C1"), srt=True))
    assert d["nhac"] == []


def test_bo_qua_thu_muc_ket_qua_cua_chinh_tool(tmp_path):
    """Tool giao kết quả vào `RenderY/Compose Timeline/` — nằm CẠNH các chương.
    Không loại trừ thì nộp lại tập đã dựng bị chặn ngay ở bước Kiểm tra:
    "'Compose Timeline' sai quy ước" (31/08, job LI093 lần 2)."""
    from autoedit.web.chapters import THU_MUC_GIAO

    tap = _tap(tmp_path, chuong=("H", "C1"))
    (tap / "RenderY" / THU_MUC_GIAO / "H" / "draft").mkdir(parents=True)
    d = tom_tat(tap)
    assert d["san_sang"] is True, d["loi"]
    assert d["so_chuong"] == 2
    assert [c["ma"] for c in d["chuong"]] == ["H", "C1"]


def test_ten_thu_muc_giao_khop_giua_hai_module():
    """chapters.THU_MUC_GIAO phải đúng thư mục compose thật sự ghi ra — lệch một
    ký tự là bộ lọc vô dụng và lỗi trên quay lại."""
    from pathlib import Path

    from autoedit.web.chapters import THU_MUC_GIAO
    from autoedit.web.compose import thu_muc_giao

    assert thu_muc_giao(Path("X:/tap")).name == THU_MUC_GIAO
