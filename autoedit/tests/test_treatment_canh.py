"""Treatment — CẢNH: một dòng treatment = một cảnh (user chốt 24/09).

*"Một phân cảnh có 6 cảnh treatment là 6 dòng riêng biệt"* — và dữ liệu thật xác
nhận: ô treatment ở SE001/H dòng 2 chính là `1) … 2) … 3) … 4) … 5)`, người viết
vẫn đang đánh số tay để tách cảnh trong MỘT ô.

Vì sao đổi `tr` (chuỗi) -> `canh` (danh sách): cảnh còn phải đeo cỡ cảnh, góc
máy, chuyển động, SFX, tông, prompt. Nhét hết vào một chuỗi thì không có chỗ.
Metadata gắn TRÊN TỪNG CẢNH, không giữ bảng chỉ số riêng — cùng bài học của
`cum` (bảng theo chỉ số thì chẻ/gộp lần nào cũng lệch).

Không có bước migration chạy một lần: `doc_canh` nhận CẢ HAI kiểu, `ghi_canh`
luôn ghi kiểu mới. Mỗi dòng tự nâng cấp lúc được lưu. Đang có người dùng thật
trên production nên không được đổi kho dưới chân họ.
"""

from __future__ import annotations

import copy

from autoedit.treatment import dong as mdong


# ------------------------------------------------------- đọc: kiểu cũ
def test_doc_chuoi_nhieu_dong_thanh_nhieu_canh():
    d = {"en": "x", "tr": "Mở cảnh biển đêm\nCắt sang tàu cá\nCận lưới kéo"}
    assert [c["t"] for c in mdong.doc_canh(d)] == [
        "Mở cảnh biển đêm", "Cắt sang tàu cá", "Cận lưới kéo"]


def test_doc_chuoi_MOT_dong_thi_dung_MOT_canh():
    """KHÔNG tự đoán mốc `2)` `3)` để tách hộ. 28 ô đang dính là do lỗi cũ,
    user chốt 24/09 tự sửa tay — máy đoán hộ là sửa chữ của người viết."""
    d = {"tr": "Hai máy bay bay song song 2) Bên ngoài sở chỉ huy 3) Mưa tầm tã"}
    canh = mdong.doc_canh(d)
    assert len(canh) == 1
    assert canh[0]["t"].startswith("Hai máy bay")


def test_doc_o_trong_thi_khong_co_canh_nao():
    assert mdong.doc_canh({"en": "x"}) == []
    assert mdong.doc_canh({"en": "x", "tr": ""}) == []
    assert mdong.doc_canh({"en": "x", "tr": "   \n  \n "}) == []


def test_doc_bo_dong_trong_o_giua():
    d = {"tr": "Cảnh một\n\n\nCảnh hai"}
    assert [c["t"] for c in mdong.doc_canh(d)] == ["Cảnh một", "Cảnh hai"]


# ------------------------------------------------------- đọc: kiểu mới
def test_co_canh_thi_canh_THANG_tr():
    """Dòng đã nâng cấp mà đâu đó còn sót `tr` cũ thì `canh` là bản đúng."""
    d = {"tr": "chữ cũ còn sót", "canh": [{"t": "Cảnh mới"}]}
    assert [c["t"] for c in mdong.doc_canh(d)] == ["Cảnh mới"]


def test_metadata_cua_canh_song_qua_vong_doc():
    d = {"canh": [{"t": "Cận bàn tay", "co": "CU", "goc": "ngang tầm mắt",
                   "cd": "lia trái", "sfx": "tiếng kim loại", "tong": "nuoc"}]}
    c = mdong.doc_canh(d)[0]
    assert c["co"] == "CU" and c["goc"] == "ngang tầm mắt"
    assert c["cd"] == "lia trái" and c["sfx"] == "tiếng kim loại"
    assert c["tong"] == "nuoc"


def test_khoa_la_tu_client_bi_loai():
    """Trang gửi lên gì cũng nhận thì một tab hỏng là phình kho bằng rác."""
    d = {"canh": [{"t": "Cảnh", "rac": "x" * 5000, "__proto__": "bậy"}]}
    assert set(mdong.doc_canh(d)[0]) <= set(mdong.KHOA_CANH)


def test_canh_khong_phai_danh_sach_thi_ROI_ve_tr():
    """Dữ liệu hỏng không được giết cả chương."""
    d = {"canh": "hỏng", "tr": "Cảnh một\nCảnh hai"}
    assert len(mdong.doc_canh(d)) == 2


# ------------------------------------------------------- ghi
def test_ghi_canh_ghi_kieu_moi_va_DON_tr_cu():
    d = {"en": "x", "vi": "y", "het": 0, "tr": "chữ cũ"}
    ra = mdong.ghi_canh(d, [{"t": "Cảnh một"}, {"t": "Cảnh hai"}])
    assert "tr" not in ra
    assert [c["t"] for c in ra["canh"]] == ["Cảnh một", "Cảnh hai"]
    assert ra["en"] == "x" and ra["vi"] == "y"      # không đụng phần kịch bản


def test_ghi_canh_bo_canh_RONG():
    ra = mdong.ghi_canh({}, [{"t": "Cảnh một"}, {"t": "  "}, {"t": "Cảnh hai"}])
    assert [c["t"] for c in ra["canh"]] == ["Cảnh một", "Cảnh hai"]


def test_ghi_canh_rong_thi_XOA_han_khoa():
    """Dòng không có treatment thì đừng để lại `canh: []` — kho phình vô ích."""
    ra = mdong.ghi_canh({"en": "x", "tr": "cũ"}, [])
    assert "canh" not in ra and "tr" not in ra


def test_ghi_canh_la_HAM_THUAN():
    d = {"en": "x", "tr": "cũ"}
    goc = copy.deepcopy(d)
    mdong.ghi_canh(d, [{"t": "Cảnh"}])
    assert d == goc, "ghi_canh không được sửa dòng của người gọi"


def test_doc_ghi_doc_khong_mat_gi():
    d = {"en": "x", "canh": [{"t": "Một", "co": "WS"}, {"t": "Hai", "tong": "can"}]}
    assert mdong.doc_canh(mdong.ghi_canh(d, mdong.doc_canh(d))) == mdong.doc_canh(d)


# --------------------------------------------- chẻ / gộp dòng kịch bản
def test_che_dong_thi_canh_di_theo_NUA_TREN():
    """Chẻ một dòng kịch bản làm đôi: treatment đã viết là của Ý ĐÓ, mà ý đó nằm
    ở nửa trên. Nhân đôi sang cả hai nửa là đẻ ra cảnh ma, đếm tiền sai."""
    d = [{"en": "Câu một dài. Phần sau.", "vi": "", "het": 0,
          "canh": [{"t": "Cảnh A"}, {"t": "Cảnh B"}]}]
    ra = mdong.che(d, 0, 14)
    assert [c["t"] for c in ra[0]["canh"]] == ["Cảnh A", "Cảnh B"]
    assert "canh" not in ra[1] or ra[1]["canh"] == []


def test_gop_dong_thi_canh_NOI_LAI_dung_thu_tu():
    d = [{"en": "Trên", "vi": "", "het": 0, "canh": [{"t": "A"}]},
         {"en": "Dưới", "vi": "", "het": 0, "canh": [{"t": "B"}, {"t": "C"}]}]
    ra = mdong.gop(d, 1)
    assert [c["t"] for c in ra[0]["canh"]] == ["A", "B", "C"]
