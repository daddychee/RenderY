"""Bàn kịch bản — kho lưu (SQLite riêng) + khoá theo chương + bản lùi.

Giai đoạn 1 KHÔNG nối vào đâu (user chốt 15/09): không đọc NAS, không đụng
`jobs.db`, không import `autoedit.web.server`. Một file DB riêng, một cổng riêng —
hỏng cũng không chạm tới dây chuyền dựng đang chạy production ở 9118.

Hai chỗ dễ mất dữ liệu của người khác, test khoá chặt:
  1. THỨ TỰ CHƯƠNG là H -> C1..Cn -> E. Sắp theo tên là sai cả hai đầu
     ("E" trước "H", "C10" trước "C2") — dùng lại luật có sẵn ở web/chapters.py.
  2. KHOÁ THEO CHƯƠNG: 2-3 người làm cùng lúc trên cùng một tập. Người thứ hai
     không được ghi đè chương người thứ nhất đang giữ.
"""

from __future__ import annotations

import pytest

from factcheck.kho import Kho, KhoaBiGiu


@pytest.fixture()
def kho(tmp_path):
    return Kho(tmp_path / "kichban.db")


# --------------------------------- tập / chương ------------------------------
def test_tao_va_liet_ke_tap(kho):
    kho.tao_tap("SH011", "Đồ uống sau tuổi 60")
    assert [t["ma"] for t in kho.ds_tap()] == ["SH011"]


def test_tap_trung_ma_bi_tu_choi(kho):
    kho.tao_tap("SH011", "x")
    with pytest.raises(ValueError):
        kho.tao_tap("SH011", "y")


def test_chuong_dung_quy_uoc_moi_duoc_nhan(kho):
    kho.tao_tap("SH011", "x")
    for ma in ("H", "C1", "C12", "E", "h", "c3"):
        kho.tao_chuong("SH011", ma)
    with pytest.raises(ValueError):
        kho.tao_chuong("SH011", "Hook")


def test_thu_tu_chuong_khong_phai_a_z(kho):
    """Thứ tự timeline: H -> C1..C10 -> E."""
    kho.tao_tap("SH011", "x")
    for ma in ("E", "C10", "C2", "H", "C1"):
        kho.tao_chuong("SH011", ma)
    assert [c["ma"] for c in kho.ds_chuong("SH011")] == ["H", "C1", "C2", "C10", "E"]


# --------------------------------- lưu / đọc ---------------------------------
def test_luu_roi_doc_lai_ra_dung_dong(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    dong = [{"en": "A", "vi": "Một", "het": 1}, {"en": "B", "vi": "Hai", "het": 0}]
    kho.luu("SH011", "H", dong=dong, outline="• mở bài", nguoi="haint")
    d = kho.doc("SH011", "H")
    assert d["dong"] == dong and d["outline"] == "• mở bài"


def test_doc_chuong_chua_nhap_ra_rong_chu_khong_no(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "C1")
    assert kho.doc("SH011", "C1")["dong"] == []


# --------------------------------- khoá --------------------------------------
def test_nguoi_dau_giu_duoc_chuong(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    assert kho.giu("SH011", "H", "haint") is True
    assert kho.ai_giu("SH011", "H") == "haint"


def test_nguoi_thu_hai_khong_giat_duoc_khi_con_han(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.giu("SH011", "H", "haint")
    assert kho.giu("SH011", "H", "thanhdn") is False
    assert kho.ai_giu("SH011", "H") == "haint"


def test_nguoi_dang_giu_gia_han_duoc(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.giu("SH011", "H", "haint")
    assert kho.giu("SH011", "H", "haint") is True


def test_khoa_het_han_thi_nguoi_khac_vao_duoc(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.giu("SH011", "H", "haint", giay=0)
    assert kho.giu("SH011", "H", "thanhdn") is True


def test_nha_khoa_thi_nguoi_khac_vao_ngay(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.giu("SH011", "H", "haint")
    kho.nha("SH011", "H", "haint")
    assert kho.ai_giu("SH011", "H") is None


def test_luu_khi_nguoi_khac_dang_giu_thi_bi_chan(kho):
    """Cửa gác THẬT: chặn ở tầng ghi, không chỉ ẩn nút trên UI."""
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.giu("SH011", "H", "haint")
    with pytest.raises(KhoaBiGiu):
        kho.luu("SH011", "H", dong=[{"en": "X", "vi": "", "het": 0}],
                outline="", nguoi="thanhdn")


def test_chuong_khong_ai_giu_thi_luu_duoc(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.luu("SH011", "H", dong=[], outline="", nguoi="thanhdn")


# --------------------------------- bản lùi -----------------------------------
def test_moi_lan_luu_de_ra_mot_ban_lui(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    for i in range(3):
        kho.luu("SH011", "H", dong=[{"en": str(i), "vi": "", "het": 0}],
                outline="", nguoi="haint")
    assert len(kho.ban_cu("SH011", "H")) == 3


def test_chi_giu_12_ban_gan_nhat(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    for i in range(20):
        kho.luu("SH011", "H", dong=[{"en": str(i), "vi": "", "het": 0}],
                outline="", nguoi="haint")
    ban = kho.ban_cu("SH011", "H")
    assert len(ban) == 12
    assert ban[0]["dong"][0]["en"] == "19", "bản mới nhất đứng đầu"


def test_lui_ve_ban_cu(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.luu("SH011", "H", dong=[{"en": "cũ", "vi": "", "het": 0}], outline="", nguoi="haint")
    kho.luu("SH011", "H", dong=[{"en": "mới", "vi": "", "het": 0}], outline="", nguoi="haint")
    ban = kho.ban_cu("SH011", "H")[-1]
    kho.lui("SH011", "H", ban["id"], nguoi="haint")
    assert kho.doc("SH011", "H")["dong"][0]["en"] == "cũ"


def test_kho_mo_lai_van_con_du_lieu(tmp_path):
    duong = tmp_path / "kichban.db"
    k1 = Kho(duong)
    k1.tao_tap("SH011", "x"); k1.tao_chuong("SH011", "H")
    k1.luu("SH011", "H", dong=[{"en": "A", "vi": "", "het": 0}], outline="", nguoi="haint")
    assert Kho(duong).doc("SH011", "H")["dong"][0]["en"] == "A"


# ------------------------------- citation ------------------------------------
def _kq(doan="The WHI found a 23 percent higher risk.", ket="dung"):
    return {"doan": doan, "chu_ky": "ab12", "ket": ket, "ly_do": "2 nguồn hạng 1",
            "truy_van": "WHI stroke", "nguon": [{"url": "https://www.cdc.gov/x",
                                                 "trich": "y", "hang": 1}]}


def test_luu_va_doc_citation(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.luu_citation("SH011", "H", _kq(), nguoi="haint")
    ds = kho.ds_citation("SH011", "H")
    assert len(ds) == 1 and ds[0]["ket"] == "dung" and ds[0]["boi"] == "haint"
    assert ds[0]["nguon"][0]["url"] == "https://www.cdc.gov/x"


def test_kiem_lai_cung_doan_thi_DE_LEN_khong_de_ra_hai_the(kho):
    """Bấm 'Kiểm lại' nhiều lần không được đẻ ra một chồng thẻ cho cùng một đoạn."""
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.luu_citation("SH011", "H", _kq(ket="sai"), nguoi="haint")
    kho.luu_citation("SH011", "H", _kq(ket="dung"), nguoi="thanhdn")
    ds = kho.ds_citation("SH011", "H")
    assert len(ds) == 1 and ds[0]["ket"] == "dung" and ds[0]["boi"] == "thanhdn"


def test_hai_doan_khac_nhau_thi_hai_the(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    a = _kq("đoạn một"); a["chu_ky"] = "aa"
    b = _kq("đoạn hai"); b["chu_ky"] = "bb"
    kho.luu_citation("SH011", "H", a, nguoi="haint")
    kho.luu_citation("SH011", "H", b, nguoi="haint")
    assert len(kho.ds_citation("SH011", "H")) == 2


def test_xoa_citation(kho):
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.luu_citation("SH011", "H", _kq(), nguoi="haint")
    kho.xoa_citation("SH011", "H", "ab12")
    assert kho.ds_citation("SH011", "H") == []


def test_citation_khong_di_theo_ban_lui(kho):
    """Bản lùi là của CHỮ, không phải của kết luận kiểm chứng: lùi chữ về bản cũ
    thì thẻ vẫn nằm đó, và tự rơi về 'cần kiểm lại' nếu chữ đã khác (UI so chữ ký)."""
    kho.tao_tap("SH011", "x"); kho.tao_chuong("SH011", "H")
    kho.luu_citation("SH011", "H", _kq(), nguoi="haint")
    kho.luu("SH011", "H", dong=[{"en": "A", "vi": "", "het": 0}], outline="", nguoi="haint")
    assert len(kho.ds_citation("SH011", "H")) == 1


def test_luat_ten_chuong_khop_voi_ban_goc():
    """Chép luật tên chương sang Factcheck là đẻ nguy cơ HAI LUẬT LỆCH NHAU.
    Máy nào còn RenderY cạnh bên thì so từng tên; không có thì bỏ qua."""
    import pytest as _pt

    from factcheck.chuong import phan_tich_ten as ta
    try:
        from autoedit.web.chapters import phan_tich_ten as goc
    except ImportError:
        _pt.skip("máy này không có RenderY cạnh bên — không đối chiếu được")
    for ten in ("H", "h", "C1", "c3", "C10", "C0", "E", "e", "Hook", "", "C", "chuong 1"):
        assert ta(ten) == goc(ten), ten
