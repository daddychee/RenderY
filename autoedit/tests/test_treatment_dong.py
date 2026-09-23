"""Bàn kịch bản — thao tác DÒNG (chẻ / gộp / ranh đoạn / xuất .txt).

Vì sao đơn vị là DÒNG chứ không phải CÂU (user chốt 15/09): team dán kịch bản vào
rồi tự **xuống dòng theo mạch dựng**. Tool không được tự chẻ câu bằng dấu chấm —
chỗ xuống dòng chính là chỗ người đọc voice sẽ nghỉ, tức là nhịp của video.

Hai bất biến đắt nhất, hỏng là mất chữ của người viết:
  1. chẻ rồi gộp lại phải ra ĐÚNG nguyên văn (không rơi ký tự, không đẻ dấu cách)
  2. nap(xuat(d)) == d — xuất ra .txt rồi dán lại phải ra đúng bấy nhiêu dòng

Bản .txt là thứ đem đi ren voice TTS, nên nó KHÔNG được dính số thứ tự (số vẽ
bằng CSS counter ở UI, không nằm trong dữ liệu) và phải dọn rác `""` mà Google
Sheet để lại (đo thật: 16 chỗ trong 5/51 kịch bản trên NAS).
"""

from __future__ import annotations

from autoedit.treatment.dong import bo_cum, che, gom_cum, gop, nap, ranh, xuat

MAU = """Number two is the one people switch to thinking they are doing the healthy thing.
Diet soda and zero-sugar drinks.

If you gave up regular soda, I understand the logic completely.
"""


# --------------------------------- nap --------------------------------------
def test_nap_moi_dong_la_mot_dong():
    d = nap(MAU)
    assert [x["en"] for x in d] == [
        "Number two is the one people switch to thinking they are doing the healthy thing.",
        "Diet soda and zero-sugar drinks.",
        "If you gave up regular soda, I understand the logic completely.",
    ]


def test_nap_dong_trong_thanh_ranh_doan():
    d = nap(MAU)
    assert d[1]["het"] == 1, "dòng trống trong file = ranh đoạn của dòng TRƯỚC nó"
    assert d[0]["het"] == 0
    assert d[2]["het"] == 0, "dòng cuối không mang ranh đoạn thừa"


def test_nap_nhieu_dong_trong_lien_tiep_van_la_mot_ranh():
    d = nap("A\n\n\n\nB\n")
    assert [x["en"] for x in d] == ["A", "B"]
    assert d[0]["het"] == 1


def test_nap_bo_khoang_trang_thua_hai_dau():
    assert nap("   A   \n")[0]["en"] == "A"


def test_nap_van_ban_rong_ra_danh_sach_rong():
    assert nap("") == [] and nap("\n\n  \n") == []


# --------------------------------- chẻ --------------------------------------
def test_che_tach_dung_vi_tri_con_tro():
    d = nap("If you gave up regular soda, I understand the logic.\n")
    r = che(d, 0, len("If you gave up regular soda,"))
    assert len(r) == 2
    assert r[0]["en"] == "If you gave up regular soda,"
    assert r[1]["en"] == "I understand the logic."


def test_che_o_cuoi_dong_de_ra_dong_rong():
    """Enter ở cuối dòng = mở dòng mới để gõ tiếp, không phải không làm gì."""
    d = nap("A\n")
    r = che(d, 0, 1)
    assert [x["en"] for x in r] == ["A", ""]


def test_che_chuyen_ranh_doan_xuong_nua_duoi():
    """Ranh đoạn thuộc về CUỐI đoạn — chẻ xong nó phải ở dòng dưới, không ở giữa."""
    d = nap("A B\n\nC\n")
    r = che(d, 0, 1)
    assert r[0]["het"] == 0 and r[1]["het"] == 1


def test_che_giu_nguyen_ket_luan_citation():
    """Chẻ KHÔNG đổi một chữ nào -> bằng chứng vẫn chống lưng đúng nội dung đó
    (user chốt 15/09). Chỉ SỬA CHỮ mới phải kiểm lại."""
    d = nap("A B\n")
    d[0]["doan"] = 7
    d[0]["tt"] = "dung"
    r = che(d, 0, 1)
    assert [x.get("doan") for x in r] == [7, 7]
    assert [x.get("tt") for x in r] == ["dung", "dung"]


def test_che_khong_dung_vao_ban_goc():
    d = nap("A B\n")
    che(d, 0, 1)
    assert len(d) == 1, "hàm thuần: không mutate danh sách của người gọi"


# --------------------------------- gộp --------------------------------------
def test_gop_noi_bang_dung_mot_dau_cach():
    d = nap("If you gave up regular soda,\nI understand the logic.\n")
    r = gop(d, 1)
    assert len(r) == 1
    assert r[0]["en"] == "If you gave up regular soda, I understand the logic."


def test_gop_qua_ranh_doan_thi_chi_bo_ranh():
    """Backspace ở đầu dòng sau một dòng trống = xoá dòng trống, KHÔNG dính hai
    đoạn vào nhau. Dính nhầm là mất ranh đoạn của cả bài."""
    d = nap("A\n\nB\n")
    r = gop(d, 1)
    assert [x["en"] for x in r] == ["A", "B"]
    assert r[0]["het"] == 0


def test_gop_dong_dau_tien_khong_lam_gi():
    d = nap("A\nB\n")
    assert gop(d, 0) == d


def test_che_roi_gop_ra_nguyen_van():
    """Cú thật của người dùng: bấm vào KHE GIỮA HAI TỪ rồi Enter."""
    goc = "If you're over sixty and most mornings start with juice, the next minutes are for you."
    d = nap(goc + "\n")
    r = gop(che(d, 0, goc.index("the next")), 1)
    assert r[0]["en"] == goc, "chẻ rồi gộp phải khôi phục từng ký tự"


def test_che_giua_mot_tu_roi_gop_thi_them_dau_cach():
    """Giới hạn đã biết, ghi lại để sau này không ai tưởng là lỗi: chẻ GIỮA một
    từ rồi gộp lại thì hai nửa nối bằng một dấu cách — không có cách nào biết chỗ
    đó vốn không có cách. Chẻ giữa từ là thao tác vô nghĩa với kịch bản."""
    d = nap("juice\n")
    assert gop(che(d, 0, 2), 1)[0]["en"] == "ju ice"


# ------------------------------ ranh đoạn -----------------------------------
def test_ranh_bat_tat():
    d = nap("A\nB\n")
    assert ranh(d, 0)[0]["het"] == 1
    assert ranh(ranh(d, 0), 0)[0]["het"] == 0


# --------------------------------- xuất -------------------------------------
def test_xuat_giu_dung_cho_xuong_dong():
    d = nap(MAU)
    assert xuat(d) == MAU


def test_xuat_ranh_doan_thanh_dong_trong():
    d = nap("A\nB\n")
    assert xuat(ranh(d, 0)) == "A\n\nB\n"


def test_xuat_don_rac_nhay_kep_cua_sheet():
    """Đo thật trên NAS: 16 chỗ `""` trong 5/51 kịch bản — rác escape CSV của
    Google Sheet. TTS đọc sai chỗ đó."""
    d = nap('So the ""diet"" label.\n')
    assert xuat(d) == 'So the "diet" label.\n'
    assert d[0]["en"] == 'So the ""diet"" label.', "bản gốc giữ nguyên, chỉ bản XUẤT mới dọn"


def test_xuat_khong_dinh_so_thu_tu():
    d = nap(MAU)
    ra = xuat(d)
    assert not any(l[:2].strip().isdigit() for l in ra.splitlines() if l)


def test_xuat_cot_tieng_viet_rieng():
    d = nap("A\nB\n")
    d[0]["vi"], d[1]["vi"] = "Một", "Hai"
    assert xuat(d, "vi") == "Một\nHai\n"


def test_xuat_ket_thuc_bang_dung_mot_xuong_dong():
    assert xuat(nap("A\n\n\n")).endswith("A\n")


def test_nap_xuat_khu_hoi():
    d = nap(MAU)
    assert nap(xuat(d)) == d


# ------------------------- CỤM (user chốt 23/09) ----------------------------
def test_gom_may_dong_thanh_mot_cum():
    """Gom các câu thành CỤM và tô màu — để người viết nhìn ra mảng ý, và người
    dựng biết đoạn nào đi liền một mạch."""
    d = nap("A\nB\nC\nD\n")
    r = gom_cum(d, 1, 2, 3)
    assert [x.get("cum") for x in r] == [None, 3, 3, None]


def test_mau_cum_chi_nhan_trong_bang_mau_co_san():
    """Màu là BẢNG CỐ ĐỊNH, không cho nhập mã màu tự do: nhập bậy thì UI vẽ ra
    thứ không đọc được trên nền tối."""
    d = nap("A\nB\n")
    import pytest

    with pytest.raises(ValueError):
        gom_cum(d, 0, 1, 99)


def test_bo_cum():
    d = gom_cum(nap("A\nB\nC\n"), 0, 2, 1)
    assert [x.get("cum") for x in bo_cum(d, 1, 1)] == [1, None, 1]


def test_gom_cum_khong_dung_vao_ban_goc():
    d = nap("A\nB\n")
    gom_cum(d, 0, 1, 2)
    assert all(x.get("cum") is None for x in d), "hàm thuần: không mutate"


def test_che_dong_trong_cum_thi_ca_hai_nua_van_thuoc_cum():
    """Chẻ một câu trong cụm: cả hai nửa vẫn nằm trong cụm đó — chẻ dòng không
    phải là tách ý."""
    d = gom_cum(nap("A B\nC\n"), 0, 0, 2)
    r = che(d, 0, 1)
    assert [x.get("cum") for x in r] == [2, 2, None]


def test_gop_giu_cum_cua_dong_tren():
    d = gom_cum(nap("A\nB\n"), 0, 0, 4)
    assert gop(d, 1)[0].get("cum") == 4
