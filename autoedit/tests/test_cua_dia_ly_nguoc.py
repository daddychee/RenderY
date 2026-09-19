r"""CỬA ĐỊA LÝ CHIỀU NGƯỢC — ngách KHÔNG gắn nơi chốn thì loại clip CÓ nơi chốn.

Vì sao. Cửa geo trong `tra.py` chỉ bật khi TẬP HIỆN TẠI có khai địa danh:

    gt = _tokens([geo_tap]) if geo_tap else set()
    if gt and not (gt & gc): continue      # gt rỗng -> cửa TẮT HẲN

Mọi lần sửa trước đều đi một chiều: *"clip Ecuador không được chảy vào tập
Afghanistan"*. Chiều ngược lại chưa có cửa nào, nên ngách không gắn địa lý cứ
khớp chữ là nuốt sạch footage nơi chốn của ngách khác.

ĐO THẬT 19/09 trên tập X FILE đang chạy — đếm HÌNH MÁY ĐÃ CHỌN, không phải khay:

| tập | ngách | hình đã chọn | dính clip có nơi chốn |
|---|---|---|---|
| XF001 | X FILE | 86 | **38 (44%)** — 33 Ecuador |
| XF004 | X FILE | 92 | **45 (49%)** — 41 Ecuador |
| KIM048 | SENIOR HEALTH | 230 | 22 (10%) — 13 Oman |

Ca tệ nhất, máy chọn làm hình chính:

    khối : "Back in the 1930s, a young pilot named Frank Whittle had a wild pitch"
    lớp  : young pilot portrait · 1930s biplane
    hình : «Smiling Man with Ecuadorian Flag on Forehead»

Hai chỗ đã loại trừ: khâu phân tích SẠCH (536 cụm máy sinh cho XF001, 0 cụm
dính địa danh) và cửa `ref` chạy đúng (83 clip ref trong khay đều của XF001).
Lỗi nằm gọn ở phía kho dùng chung.

Giá phải trả, đo trên 3 tập thật: khay còn 68-84%, sinh thêm ĐÚNG 1 miếng
trống trên tổng 452. Không có đường lùi "hết hàng thì cho qua" — user chốt
07/09: *"khối trống là THÔNG TIN thật cho editor, không phải chỗ để lấp bừa"*.
"""

from __future__ import annotations

import pytest

from autoedit.sotra import db as sdb
from autoedit.sotra.tra import tra

LOP = {"L0": [], "L1": ["cash stack"], "L2": ["counting money"], "L3": []}


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    yield c
    c.close()


def _them(c, cid, nguon, tieu_de, geo="", tap=""):
    sdb.them_clip(c, {"id": cid, "nguon": nguon, "tieu_de": tieu_de,
                      "geo": geo, "tap": tap, "t0": 0.0, "t1": 4.0})
    return cid


def _kho(c):
    """4 clip trung tính + 4 clip gắn Ecuador — cùng khớp từ khoá như nhau."""
    for i in range(4):
        _them(c, f"envato:tt{i}", "envato", f"Hands Counting Cash Stack ({i})")
    for i in range(4):
        _them(c, f"envato:ec{i}", "envato",
              f"Counting Cash Stack in Quito Market ({i})", geo="ecuador")


# ------------------------------------------------------------ cửa mới

def test_ngach_khong_khai_dia_danh_thi_LOAI_clip_co_noi_chon(conn):
    _kho(conn)
    ra = tra(conn, LOP, so=12, geo_tap="", tap="XF001", can_neo=False)
    assert ra, "chặn sạch cả khay là sai — clip trung tính phải còn"
    assert all(not u["id"].startswith("envato:ec") for u in ra), \
        [u["tieu_de"] for u in ra]


def test_clip_CO_bi_chan__ca_that_cua_XF004(conn):
    """«Animated Ecuador Flag with Global Financial Market Data» — 36 clip cờ
    Ecuador trong kho thật đều mang geo='ecuador' nên cửa này bắt trọn."""
    _them(conn, "envato:co", "envato",
          "Animated Ecuador Flag with Global Financial Market Data",
          geo="ecuador")
    _them(conn, "envato:sach", "envato", "Financial Market Data Chart Close Up")
    lop = {"L0": [], "L1": ["financial market data"], "L2": [], "L3": []}
    # Rào chống XANH RỖNG (dính đúng bẫy này lúc chạy pha đỏ 19/09): chứng minh
    # clip cờ KHỚP từ khoá đã, không thì nó bị loại vì lệch chữ chứ đâu phải vì cửa.
    truoc = tra(conn, lop, so=12, geo_tap="ecuador", tap="XF004", can_neo=False)
    assert "envato:co" in [u["id"] for u in truoc], "clip cờ không khớp -> test vô nghĩa"

    ra = tra(conn, lop, so=12, geo_tap="", tap="XF004", can_neo=False)
    assert [u["id"] for u in ra] == ["envato:sach"], [u["tieu_de"] for u in ra]


def test_clip_khong_gan_geo_van_vao_binh_thuong(conn):
    _kho(conn)
    ra = tra(conn, LOP, so=12, geo_tap="", tap="XF001", can_neo=False)
    assert len(ra) == 4


# ------------------------------------------- KHÔNG được đổi hành vi cũ

def test_tap_CO_khai_dia_danh_giu_NGUYEN_nhu_cu(conn):
    """Life In không được lệch một thẻ: khai ecuador thì vẫn chỉ lấy ecuador."""
    _kho(conn)
    ra = tra(conn, LOP, so=12, geo_tap="ecuador", tap="LI200", can_neo=False)
    assert ra and all(u["id"].startswith("envato:ec") for u in ra), \
        [u["tieu_de"] for u in ra]


def test_ref_cua_CHINH_TAP_co_geo_thi_KHONG_bi_chan(conn):
    """Video mẫu của chính tập là tư liệu của mình — nạp ref gắn cứng quốc gia
    nên nhiều cảnh có geo. Chặn chúng là chặn nhầm nhà."""
    cid = sdb.lam_id("ref", "XF001-ref 1", "0.00-4.00")
    _them(conn, cid, "ref", "Hands Counting Cash Stack", geo="ecuador", tap="XF001")
    ra = tra(conn, LOP, so=12, geo_tap="", tap="XF001", can_neo=False)
    assert [u["id"] for u in ra] == [cid]


def test_kho_rieng_va_tu_quay_KHONG_bi_chan(conn):
    """`kho` / `rec` là tư liệu của mình (sổ nguồn gốc xếp chung 'local')."""
    _them(conn, "kho:1", "kho", "Hands Counting Cash Stack", geo="ecuador")
    _them(conn, "rec:1", "rec", "Counting Money Close Up", geo="ecuador")
    ra = tra(conn, LOP, so=12, geo_tap="", tap="XF001", can_neo=False)
    assert {u["id"] for u in ra} == {"kho:1", "rec:1"}


def test_khong_co_duong_lui_khi_het_hang(conn):
    """Mọi ứng viên đều gắn nơi chốn -> khay TRỐNG, không lấp bừa."""
    for i in range(6):
        _them(conn, f"envato:ec{i}", "envato",
              f"Counting Cash Stack in Quito ({i})", geo="ecuador")
    assert tra(conn, LOP, so=12, geo_tap="", tap="XF001", can_neo=False) == []


# ------------------------------------------- nhãn địa lý NGẮN (usa, uk)

def test_usa_KHONG_bi_nuot_mat(conn):
    """`_tokens` lấy từ >=4 chữ cái nên «usa» ra RỖNG — cửa địa lý mù hẳn với
    nó. Đo trên tập XF001 thật: 27 thẻ stock geo='usa' lọt qua cửa mới, gồm
    «Crowd of People in Times Square, New York City». Kho thật có 84 clip mang
    nhãn geo bị nuốt kiểu này."""
    _them(conn, "envato:us", "envato", "Girl Taking Money Hundred Dollars",
          geo="usa")
    _them(conn, "envato:sach", "envato", "Hands Counting Money Close Up")
    ra = tra(conn, {"L0": [], "L1": ["counting money"], "L2": [], "L3": []},
             so=12, geo_tap="", tap="XF001", can_neo=False)
    assert [u["id"] for u in ra] == ["envato:sach"], [u["tieu_de"] for u in ra]


def test_cua_XUOI_cung_phai_thay_dia_danh_ngan(conn):
    """Tập khai «usa» thì clip usa phải QUA, clip ecuador phải bị loại.

    Clip TRUNG TÍNH cũng phải bị loại — đó mới là thứ chứng minh cửa XUÔI có
    chạy: luật cũ ghi rõ "geo lệch LẪN geo trống đều loại". Thiếu nó thì test
    xanh nhờ cửa ngược trong khi `geo_tap='usa'` vẫn bị nuốt mất.
    """
    _them(conn, "envato:us", "envato", "Counting Money in Store", geo="usa")
    _them(conn, "envato:ec", "envato", "Counting Money in Market", geo="ecuador")
    _them(conn, "envato:tt", "envato", "Counting Money Close Up")
    ra = tra(conn, {"L0": [], "L1": ["counting money"], "L2": [], "L3": []},
             so=12, geo_tap="usa", tap="LI300", can_neo=False)
    assert [u["id"] for u in ra] == ["envato:us"], [u["tieu_de"] for u in ra]


# ------------------------- ngách khai NƠI CHỐN CHẤP NHẬN (hồ sơ ngách)
# Cửa ngược ở trên chặn MỌI clip có nơi chốn. Nhưng SENIOR HEALTH là ngách Mỹ:
# clip geo='usa' là ĐÚNG người đúng cảnh của nó, chặn đi là chặn nhầm.
#
# Đo thật 19/09, để không ai kỳ vọng nhầm: khai 'usa' cho KIM048 chỉ thêm 4 thẻ
# (1742 -> 1746) và KHÔNG cứu được khay trống nào (19 -> 19). 19 khay đó trống
# vì thứ khớp với chúng chỉ còn clip Oman/Ecuador — trống ĐÚNG.
#
# Khác `geo_tap` (địa danh của TẬP, luật CHẶT: clip phải khớp, geo trống cũng
# loại). Đây là luật NỚI: clip có nơi chốn thì phải nằm trong danh sách ngách
# chấp nhận, còn clip KHÔNG gắn nơi chốn vẫn đi bình thường.

def test_ngach_khai_usa_thi_clip_usa_duoc_qua(conn):
    _them(conn, "envato:us", "envato", "Counting Money in Store", geo="usa")
    _them(conn, "envato:ec", "envato", "Counting Money in Market", geo="ecuador")
    _them(conn, "envato:tt", "envato", "Counting Money Close Up")
    ra = tra(conn, {"L0": [], "L1": ["counting money"], "L2": [], "L3": []},
             so=12, geo_tap="", tap="KIM049", can_neo=False,
             dia_ly_cho_phep="usa")
    assert {u["id"] for u in ra} == {"envato:us", "envato:tt"}, \
        [u["tieu_de"] for u in ra]


def test_khai_nhieu_noi_chon(conn):
    _them(conn, "envato:us", "envato", "Counting Money in Store", geo="usa")
    _them(conn, "envato:uk", "envato", "Counting Money in London", geo="uk")
    _them(conn, "envato:ec", "envato", "Counting Money in Market", geo="ecuador")
    ra = tra(conn, {"L0": [], "L1": ["counting money"], "L2": [], "L3": []},
             so=12, geo_tap="", tap="T", can_neo=False, dia_ly_cho_phep="usa uk")
    assert {u["id"] for u in ra} == {"envato:us", "envato:uk"}


def test_khong_khai_thi_giu_nguyen_cua_nguoc(conn):
    _kho(conn)
    ra = tra(conn, LOP, so=12, geo_tap="", tap="XF001", can_neo=False,
             dia_ly_cho_phep="")
    assert all(not u["id"].startswith("envato:ec") for u in ra)


def test_dia_danh_cua_TAP_van_thang(conn):
    """Tập khai địa danh thì luật CHẶT của tập thắng, không bị nới ra."""
    _them(conn, "envato:us", "envato", "Counting Money in Store", geo="usa")
    _them(conn, "envato:ec", "envato", "Counting Money in Market", geo="ecuador")
    ra = tra(conn, {"L0": [], "L1": ["counting money"], "L2": [], "L3": []},
             so=12, geo_tap="ecuador", tap="LI300", can_neo=False,
             dia_ly_cho_phep="usa")
    assert [u["id"] for u in ra] == ["envato:ec"]
