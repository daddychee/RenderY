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


def test_ghi_canh_CHUAN_HOA_khoang_trang():
    """Luật CŨ ở đây là bỏ cảnh rỗng. Đổi 24/09 sau khi user báo: bỏ nó thì màn
    Kịch bản thấy 4 khối mà Storyboard thấy 3. Nay cảnh rỗng được giữ (xem
    test_giu_canh_rong_khi_con_canh_co_chu), chỉ khoảng trắng bị chuẩn hoá."""
    ra = mdong.ghi_canh({}, [{"t": "  Cảnh một  "}, {"t": "	Cảnh hai"}])
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


# ----------------------------- tài sản gán vào cảnh -------------------------
def test_canh_gan_duoc_TAI_SAN():
    """Sổ tài sản chỉ thay được bước "ném ref vào, ghi nhớ đặc điểm" nếu CẢNH
    chỉ được vào sổ. `ts` là danh sách mã tài sản, không phải chuỗi."""
    assert "ts" in mdong.KHOA_CANH
    d = {"canh": [{"t": "Cận tàu ngầm", "ts": ["k129", "day_bien"]}]}
    assert mdong.doc_canh(d)[0]["ts"] == ["k129", "day_bien"]


def test_ts_rac_thi_bo_di():
    d = {"canh": [{"t": "A", "ts": "k129"}, {"t": "B", "ts": [1, "", "ok"]}]}
    ra = mdong.doc_canh(d)
    assert "ts" not in ra[0], "ts không phải danh sách thì bỏ"
    assert ra[1]["ts"] == ["ok"], "phần tử rỗng/không phải chữ thì bỏ"


# ------------------------- cảnh RỖNG người vừa tạo --------------------------
# ĐO THẬT 24/09 (user báo): bấm Enter ở cuối khối treatment để mở một cảnh mới
# thì màn Kịch bản thấy 4 khối, Storyboard chỉ thấy 3 — vì cảnh rỗng bị lọc lúc
# lưu. Hai màn nói hai chuyện khác nhau, người dùng tưởng tool không cập nhật.
#
# Luật mới: GIỮ cảnh rỗng khi danh sách còn ít nhất một cảnh có chữ. Dòng chưa
# viết treatment thì tất cả đều rỗng -> xoá hẳn khoá, không đẻ cảnh ma cho mọi
# dòng trong tập.

def test_giu_canh_rong_khi_con_canh_co_chu():
    ra = mdong.ghi_canh({}, [{"t": "Cảnh một"}, {"t": ""}, {"t": "Cảnh hai"}])
    assert [c["t"] for c in ra["canh"]] == ["Cảnh một", "", "Cảnh hai"]


def test_canh_rong_o_CUOI_cung_duoc_giu():
    """Đây chính là ca người dùng gặp: Enter ở cuối để mở cảnh kế."""
    ra = mdong.ghi_canh({}, [{"t": "Cảnh một"}, {"t": "  "}])
    assert [c["t"] for c in ra["canh"]] == ["Cảnh một", ""]


def test_TAT_CA_rong_thi_xoa_han_khoa():
    """Dòng chưa viết treatment: UI vẫn vẽ một khối trống để gõ vào, nhưng nó
    KHÔNG được thành cảnh ma trong kho."""
    ra = mdong.ghi_canh({"en": "x"}, [{"t": ""}, {"t": "   "}])
    assert "canh" not in ra


def test_doc_lai_van_thay_canh_rong():
    d = {"canh": [{"t": "A"}, {"t": ""}]}
    assert [c["t"] for c in mdong.doc_canh(d)] == ["A", ""]


def test_chuoi_cu_van_BO_dong_trong():
    """Dòng trống giữa một đoạn dán vào không phải là cảnh."""
    assert [c["t"] for c in mdong.doc_canh({"tr": "A" + chr(10)*3 + "B"})] == ["A", "B"]
