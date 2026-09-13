r"""CHỌN THEO 3 TẦNG — mô phỏng đúng cách editor làm (user chốt 12/09).

  A: đúng NHÂN VẬT của ngách + đúng OBJECT của câu
  B: đúng NHÂN VẬT, object chung
  C: cảnh CẬN (ai cũng được, ƯU TIÊN người già)
  hết  -> ĐỂ TRỐNG (khối trống là thông tin thật cho editor, không lấp bừa)

Vì sao KHÔNG cộng điểm chữ nữa (đo 12/09 trên SH010, 3 cách đều thất bại):
  · IDF:            `glass` 0,5% kho -> trọng số 0,99 mà `nepal` 13% -> 0,38
                    => dìm Life In, không cứu Senior Health
  · chủ thể tập:    stock lệch chủ đề 31% -> 22% rồi đứng
  · đọc hình rồi vẫn đếm từ: khối h5 TỆ HƠN (L1 có chữ `desk`, clip đếm tiền
                    cũng có `desk`)
Đếm từ trùng là cơ chế sai — đổi chữ bên nào vào cũng sai. Ba tầng thì không so
chữ để QUYẾT ĐỊNH, chỉ dùng chữ ở tầng A để xếp trong cùng một tầng.

Kết quả đo khi áp lên SH010: miếng có người già da trắng 8/116 -> 79/116.
"""

from __future__ import annotations

import pytest


def the(cid, *, tuoi="none", ct="none", shot="medium", vat_the="", diem=10.0,
        nguon="envato"):
    """Một thẻ ứng viên trong khay, đúng các trường `do_ung_vien` ghi ra."""
    return {"id": cid, "nguon": nguon, "tieu_de": cid, "diem": diem,
            "tuoi": tuoi, "chung_toc": ct, "shot": shot, "vat_the": vat_the}


NV = {"tuoi": ["older"], "chung_toc": ["white"]}      # Senior Health


# --------------------------------------------------------------- thứ tự tầng

def test_tang_A_thang_tang_B_du_diem_thap_hon():
    """Đúng người + đúng vật phải thắng đúng người + vật chung, BẤT KỂ điểm chữ.
    Đây là chỗ cách cũ sai: nó chỉ nhìn điểm."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("B_diem_cao", tuoi="older", ct="white", diem=99),
           the("A_diem_thap", tuoi="older", ct="white", vat_the="water glass",
               diem=1)]]
    so = xep_3_tang(uv, [["water glass"]], NV)
    assert [x["id"] for x in uv[0]] == ["A_diem_thap", "B_diem_cao"]
    assert uv[0][0]["tang"] == "A" and uv[0][1]["tang"] == "B"
    assert so == [2]


def test_tang_B_thang_tang_C():
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("C_can", shot="close", vat_the="pill bottle", diem=99),
           the("B_nguoi_gia", tuoi="older", ct="white", diem=1)]]
    xep_3_tang(uv, [["pill bottle"]], NV)
    assert [x["id"] for x in uv[0]] == ["B_nguoi_gia", "C_can"]
    assert uv[0][1]["tang"] == "C"


def test_tang_C_CHI_nhan_canh_can():
    """Cảnh cận là đường thoát duy nhất. Cảnh rộng người trẻ thì không phải
    đường thoát — đó là núi Andes trong tập sức khoẻ."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("rong_nguoi_tre", tuoi="young", ct="asian", shot="wide",
               vat_the="water glass", diem=99),
           the("can", shot="close", vat_the="water glass", diem=1)]]
    so = xep_3_tang(uv, [["water glass"]], NV)
    assert so == [1], "chỉ cảnh cận được dùng"
    assert uv[0][0]["id"] == "can" and uv[0][0]["tang"] == "C"
    assert uv[0][1]["tang"] == "-"


def test_tang_C_uu_tien_nguoi_gia():
    """User chốt: "cảnh cận có thể lấy tùy ý nhưng ưu tiên là người già"."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("can_tre", tuoi="young", ct="asian", shot="close",
               vat_the="water pitcher", diem=99),
           the("can_gia", tuoi="older", ct="black", shot="close",
               vat_the="water glass", diem=1)]]
    xep_3_tang(uv, [["water glass pitcher"]], NV)
    assert uv[0][0]["id"] == "can_gia"


# ------------------------------------------------------------ để trống

def test_khong_co_gi_hop_thi_KHONG_dung_duoc_mieng_nao():
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("rong_tre", tuoi="young", ct="latino", shot="wide"),
           the("aerial", shot="aerial")]]
    so = xep_3_tang(uv, [["x"]], NV)
    assert so == [0]


def test_de_trong_thi_chon_mac_dinh_tra_TRU_MOT():
    """Khối trống đi tiếp vào đường placeholder đã có — không cần code mới."""
    from types import SimpleNamespace

    from autoedit.offline.dung import chon_mac_dinh, xep_3_tang

    uv = [[the("rong_tre", tuoi="young", ct="latino", shot="wide")]]
    so = xep_3_tang(uv, [["x"]], NV)
    khoi = [SimpleNamespace(v0=0.0, v1=3.0, tho=0.0)]
    assert chon_mac_dinh(khoi, [uv[0][:so[0]]]) == [-1]


def test_the_khong_dat_VAN_NAM_TRONG_khay():
    """Người vẫn phải tự chọn được. Xoá khỏi khay là bịt mắt editor — nhất là
    lúc kho còn nghèo (đo 12/09: chỉ 64/548 clip khay SH010 đạt cửa người)."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("loai", tuoi="young", ct="asian", shot="wide"),
           the("dat", tuoi="older", ct="white")]]
    so = xep_3_tang(uv, [["x"]], NV)
    assert so == [1]
    assert len(uv[0]) == 2 and uv[0][1]["id"] == "loai"


# ------------------------------------------------ ngách chưa khai / ngách geo

def test_nhan_vat_RONG_thi_GIU_NGUYEN_thu_tu():
    """Ngách gắn địa lý (Life In) không khai nhân vật — cửa geo lo việc đó. Ở
    đây phải là KHÔNG ĐỤNG GÌ, không được vô tình đổi cách Life In đang chạy."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("mot", diem=1), the("hai", diem=99)]]
    so = xep_3_tang(uv, [["x"]], {})
    assert [x["id"] for x in uv[0]] == ["mot", "hai"]
    assert so == [2]
    assert all(not x.get("tang") for x in uv[0])


def test_chi_khai_tuoi_thi_KHONG_doi_chung_toc():
    """Ngách khai một nửa (chỉ tuổi) thì chỉ soi tuổi — không tự thêm điều kiện."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("gia_da_den", tuoi="older", ct="black", diem=5)]]
    so = xep_3_tang(uv, [["x"]], {"tuoi": ["older"]})
    assert so == [1] and uv[0][0]["tang"] == "B"


# --------------------------------------------------------------- object khớp

def test_object_bo_tu_do_dac_chung():
    """`table`/`glass`/`hand` là đồ đạc có ở mọi thể loại — chính chúng làm clip
    đếm tiền thắng clip nước cam (48% điểm L1 đến từ nhóm này, đo 12/09)."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("chi_trung_do_dac", tuoi="older", ct="white",
               vat_the="table, glass, hand", diem=1),
           the("trung_vat_that", tuoi="older", ct="white",
               vat_the="orange juice, carton", diem=1)]]
    xep_3_tang(uv, [["orange juice glass table"]], NV)
    assert uv[0][0]["id"] == "trung_vat_that"
    assert uv[0][0]["tang"] == "A" and uv[0][1]["tang"] == "B"


def test_nhieu_khoi_moi_khoi_object_rieng():
    from autoedit.offline.dung import xep_3_tang

    a = the("nuoc", tuoi="older", ct="white", vat_the="water glass")
    b = the("thuoc", tuoi="older", ct="white", vat_the="pill bottle")
    uv = [[dict(a), dict(b)], [dict(a), dict(b)]]
    so = xep_3_tang(uv, [["water glass"], ["pill bottle"]], NV)
    assert so == [2, 2]
    assert uv[0][0]["id"] == "nuoc" and uv[1][0]["id"] == "thuoc"


def test_the_thieu_truong_doc_hinh_KHONG_no():
    """Clip cũ trong kho chưa đọc hình -> thiếu `tuoi`/`shot`. Phải rơi xuống
    đáy khay, không được ném lỗi giữa lúc dựng."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[{"id": "cu", "nguon": "envato", "tieu_de": "cu", "diem": 50.0},
           the("moi", tuoi="older", ct="white")]]
    so = xep_3_tang(uv, [["x"]], NV)
    assert so == [1] and uv[0][0]["id"] == "moi"


# --------------------------------------------- tầng C: nới NGƯỜI, không nới VẬT
# Đo chương E của SH010 (user thử 13/09): tầng C nhận BẤT KỲ cảnh cận, không cần
# liên quan vật gì —
#     câu "hands holding glass"      -> "Man Hands Weaving Carpet in Uzbekistan"
#     câu "pouring water into glass" -> "Hands Count and Place Money Into Envelope"
# Luật user: "câu nào không tả được bằng 1+2 thì tìm các cảnh cận". Nới ở đây là
# nới điều kiện NGƯỜI (cận bàn tay thì không thấy tuổi), KHÔNG phải nới điều kiện
# VẬT. Cận bàn tay đếm tiền cho câu "rót nước" thì thà để trống.

def test_tang_C_van_phai_LIEN_QUAN_VAT(the=the):
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("can_lech", shot="close", vat_the="loom, threads, fabric", diem=99),
           the("can_dung", shot="close", vat_the="water glass, pitcher", diem=1)]]
    so = xep_3_tang(uv, [["pouring water into glass"]], NV)
    assert uv[0][0]["id"] == "can_dung"
    assert so == [1], "cảnh cận không liên quan vật thì KHÔNG được dùng"


def test_tang_C_khong_co_gi_lien_quan_thi_DE_TRONG():
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("can_tien", shot="close", vat_the="money, envelope, papers"),
           the("can_det", shot="close", vat_the="loom, threads")]]
    assert xep_3_tang(uv, [["pouring water into glass"]], NV) == [0]


def test_tang_C_uu_tien_nguoi_gia_TRONG_SO_lien_quan():
    """Ưu tiên người già vẫn giữ — nhưng chỉ xét trong nhóm đã liên quan vật."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("can_tre_dung_vat", tuoi="young", ct="asian", shot="close",
               vat_the="water glass", diem=99),
           the("can_gia_dung_vat", tuoi="older", ct="white", shot="close",
               vat_the="water pitcher", diem=1)]]
    xep_3_tang(uv, [["pouring water into glass"]], NV)
    assert uv[0][0]["id"] == "can_gia_dung_vat"


# ------------------------------------- khớp vật phải đọc CẢ TIÊU ĐỀ, không chỉ vat_the

def test_khop_vat_doc_ca_TIEU_DE():
    """Chương E: câu cần `fruit juice glass`, clip "Mature Woman Drinking Juice"
    bị hạ xuống tầng B vì `vat_the` vision ghi "glass, sweater, shirt" — chữ
    `juice` nằm ở TIÊU ĐỀ. Clip đúng mà mất hạng."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[{"id": "juice", "nguon": "envato", "diem": 10,
            "tieu_de": "Mature Woman Drinking Juice and Talking at Table",
            "tuoi": "older", "chung_toc": "white", "shot": "medium",
            "vat_the": "glass, sweater, shirt"}]]
    xep_3_tang(uv, [["fruit juice glass"]], NV)
    assert uv[0][0]["tang"] == "A"


def test_tu_GIAO_DIEN_khong_phai_vat_quay_duoc():
    """Đo chương E sau khi cho khớp cả tiêu đề: câu outro "subscribe button
    screen / notification bell icon" nhận "Animated Check Signing Flat Design
    ICON" — khớp nhờ chữ `icon`. Câu kêu gọi đăng ký không có vật nào quay được;
    để nó rơi xuống tầng B (đúng người, hình chung) mới đúng."""
    from autoedit.offline.dung import xep_3_tang

    uv = [[the("icon_lech", tuoi="older", ct="white",
               vat_the="check, pen, dollar sign", diem=50)]]
    uv[0][0]["tieu_de"] = "Animated Check Signing Flat Design Icon"
    xep_3_tang(uv, [["subscribe button screen", "notification bell icon"]], NV)
    assert uv[0][0]["tang"] == "B", "chữ giao diện không được tính là khớp vật"
