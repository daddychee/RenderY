r"""SUẤT GIỮ CHỖ CHO ĐÚNG NGƯỜI trong `tra()` (user chốt 13/09).

Vì sao cần — đo trên hai chương SH010 vừa chạy bằng luật QĐ15:

    chương h: khay 54/279 thẻ đạt cửa nhân vật = 19%
    chương e: khay 12/168 thẻ đạt cửa nhân vật =  7%  -> 7/16 miếng tụt tầng C

Cửa nhân vật chạy ĐÚNG (chặn sạch người sai tuổi), nhưng khay đưa cho nó chỉ có
7-19% thẻ đúng người nên nó chỉ còn ba đường: lấy ref, tụt xuống cảnh cận, hoặc
để trống. `xep_3_tang` chỉ XẾP LẠI thứ đã vào khay — ai được vào 12 suất thì vẫn
do ĐẾM CHỮ CŨ quyết. Đặt luật nhân vật ở bước chọn mà không đặt ở bước tra là
làm nửa việc.

Cách chữa đúng khuôn đã có: `SAN_REF` giữ chỗ cho ref, `NGUON_STOCK` giữ mỗi
nguồn một ô — thêm suất giữ chỗ cho thẻ ĐÚNG NGƯỜI.

Lưu ý thật thà: suất này chỉ cứu được clip ĐÃ ĐỌC HÌNH. Clip chưa đọc có
`tuoi` rỗng nên không qua cửa — kho đọc được 6% thì suất giữ chỗ cũng chỉ có 6%
kho để chọn. Đó là việc 2 (đọc hình cả kho), không phải việc này.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def kho(tmp_path):
    from autoedit.sotra import db as sdb

    conn = sdb.mo(tmp_path / "so_tra.db")
    yield conn
    conn.close()


def _clip(conn, cid, tieu_de, *, nguon="envato", tuoi="", ct="", doc=1, **kw):
    """Thêm clip + ghi trực tiếp trường nhân vật (doc_hinh mới được ghi cột này)."""
    from autoedit.sotra import db as sdb

    sdb.them_clip(conn, {"id": cid, "nguon": nguon, "tieu_de": tieu_de,
                         "url_video": kw.get("url_video", cid), **kw})
    conn.execute("UPDATE clip SET tuoi=?, chung_toc=?, doc_nguoi=? WHERE id=?",
                 (tuoi, ct, doc, cid))
    conn.commit()


NV = {"tuoi": ["older"], "chung_toc": ["white"]}
LOP = {"L0": [], "L1": ["water glass"], "L2": ["kitchen scene"], "L3": ["calm mood"]}
# `can_neo=False` là ĐÚNG thực tế của ngách không gắn địa lý: từ 12/09 `lop4` sinh
# `neo=false` cho chúng, nên cửa L0 (đòi geo hoặc trúng chủ thể tập) không bật.
# Để True thì cửa đó loại sạch clip stock không geo và khay rỗng — không đo được gì.


def test_the_DUNG_NGUOI_diem_thap_van_vao_duoc_khay(kho):
    """Chỗ hỏng thật: 12 suất bị clip sai người điểm cao chiếm hết."""
    from autoedit.sotra.tra import tra

    for i in range(12):                        # sai người, điểm cao (trúng 2 lớp)
        _clip(kho, f"envato:sai{i}", "water glass kitchen scene", tuoi="young", ct="asian")
    _clip(kho, "envato:dung", "water glass", tuoi="older", ct="white")   # đúng người, thấp hơn
    ra = tra(kho, LOP, so=12, nhan_vat=NV, can_neo=False)
    assert "envato:dung" in [c["id"] for c in ra], "thẻ đúng người phải có suất giữ chỗ"


def test_khong_khai_nhan_vat_thi_KHAY_KHONG_DOI(kho):
    """Life In không khai nhân vật — khay phải y như trước, không lệch một thẻ."""
    from autoedit.sotra.tra import tra

    for i in range(12):
        _clip(kho, f"envato:sai{i}", "water glass kitchen scene", tuoi="young", ct="asian")
    _clip(kho, "envato:dung", "water glass", tuoi="older", ct="white")
    a = [c["id"] for c in tra(kho, LOP, so=12, can_neo=False)]
    b = [c["id"] for c in tra(kho, LOP, so=12, nhan_vat={}, can_neo=False)]
    assert a == b
    assert "envato:dung" not in a, "không khai thì KHÔNG được ưu ai"


def test_clip_CHUA_DOC_HINH_khong_qua_cua(kho):
    """`tuoi` rỗng = chưa đọc hình. Cho qua là đoán bừa."""
    from autoedit.sotra.tra import tra

    for i in range(12):
        _clip(kho, f"envato:sai{i}", "water glass kitchen scene", tuoi="young", ct="asian")
    _clip(kho, "envato:chua", "water glass", tuoi="", ct="", doc=0)
    ra = tra(kho, LOP, so=12, nhan_vat=NV, can_neo=False)
    ids = [c["id"] for c in ra]
    assert "envato:chua" not in ids or ids.index("envato:chua") >= 12


def test_khong_co_the_dung_nguoi_thi_KHONG_no_khong_bu_bua(kho):
    from autoedit.sotra.tra import tra

    # tiêu đề PHẢI khác nhau: `gop_ban_trung` gộp cùng nguồn + cùng tiêu đề về
    # MỘT thẻ (luật 09/09) — để trùng thì đếm ra 1 rồi tưởng code sai.
    for i in range(5):
        _clip(kho, f"envato:sai{i}", f"water glass kitchen so {i}",
              tuoi="young", ct="asian")
    ra = tra(kho, LOP, so=12, nhan_vat=NV, can_neo=False)
    assert len(ra) == 5, "không có thẻ đúng người thì trả đúng thứ có, không bù bừa"


def test_suat_nhan_vat_KHONG_an_san_ref(kho):
    """Sàn ref 3 thẻ (tiêu đề khác nhau) là luật đã chốt 12/09 — không được đụng."""
    from autoedit.sotra.tra import tra

    for i in range(6):
        _clip(kho, f"envato:g{i}", "water glass kitchen scene",
              tuoi="older", ct="white")
    for i, t in enumerate(("woman drinking", "senior hand", "doctor visit")):
        _clip(kho, f"ref:v:{i}", t, nguon="ref", tap="SH010", url_video="")
    ra = tra(kho, LOP, so=12, nhan_vat=NV, can_neo=False, tap="SH010")
    assert sum(1 for c in ra if c["nguon"] == "ref") >= 3


def test_suat_nhan_vat_dem_theo_DIEM(kho):
    """Trong số thẻ đúng người, lấy thẻ điểm cao trước — không lấy đại."""
    from autoedit.sotra.tra import tra

    for i in range(12):
        _clip(kho, f"envato:sai{i}", "water glass kitchen scene", tuoi="young", ct="asian")
    _clip(kho, "envato:gia_thap", "water glass", tuoi="older", ct="white")
    _clip(kho, "envato:gia_cao", "water glass kitchen scene calm mood",
          tuoi="older", ct="white")
    ra = [c["id"] for c in tra(kho, LOP, so=12, nhan_vat=NV, can_neo=False)]
    assert "envato:gia_cao" in ra
    assert ra.index("envato:gia_cao") < ra.index("envato:gia_thap") \
        if "envato:gia_thap" in ra else True


def test_do_ung_vien_chuyen_nhan_vat_xuong_tra(kho):
    """Khớp nối phải thông — BH2: tham số không tới nơi thì luật thành trang trí."""
    from autoedit.offline import dung, lop4

    for i in range(12):
        _clip(kho, f"envato:sai{i}", "water glass kitchen scene", tuoi="young", ct="asian")
    _clip(kho, "envato:dung", "water glass", tuoi="older", ct="white")
    khoi = [type("K", (), {"loi": "x"})()]
    lop = [lop4.LopKhoi(khoi=0, truc_chi=["water glass"], ngu_canh=["kitchen scene"],
                        khong_khi=["calm mood"], neo=False)]
    uv = dung.do_ung_vien(kho, khoi, lop, [], nhan_vat=NV)
    assert "envato:dung" in [t["id"] for t in uv[0]]


def test_REF_dat_cua_KHONG_an_suat_nguoi_cua_stock(kho):
    """Đo 13/09: suất giữ chỗ chỉ nhích khay 20% -> 22% vì ref của SH010 là video
    người già — 3 thẻ ref sàn đã lấp gần hết 4 suất, stock chỉ còn 1 chỗ. Mà vấn
    đề user báo chính là STOCK sai người. Ref đã có sàn riêng (`SAN_REF`), nên
    suất này phải đếm RIÊNG stock."""
    from autoedit.sotra.tra import SAN_NHAN_VAT, tra

    # ref đúng người, tiêu đề khác nhau -> lấp sàn ref
    for i, t in enumerate(("senior hand", "older couple", "doctor and patient")):
        _clip(kho, f"ref:v:{i}", t, nguon="ref", tap="SH010", url_video="",
              tuoi="older", ct="white")
    # stock sai người nhưng điểm cao
    for i in range(12):
        _clip(kho, f"envato:sai{i}", f"water glass kitchen scene {i}",
              tuoi="young", ct="asian")
    # stock ĐÚNG người, điểm thấp hơn
    for i in range(6):
        _clip(kho, f"envato:gia{i}", f"water glass {i}", tuoi="older", ct="white")
    ra = tra(kho, LOP, so=12, nhan_vat=NV, can_neo=False, tap="SH010")
    gia_stock = [c for c in ra if c["nguon"] != "ref"
                 and c["tuoi"] == "older" and c["chung_toc"] == "white"]
    assert len(gia_stock) >= SAN_NHAN_VAT, (
        f"chỉ {len(gia_stock)} thẻ stock đúng người vào khay — ref đã ăn mất suất")


def test_the_SAI_NGUOI_chi_lap_cho_TRONG_khong_tranh_suat(kho):
    """Đo 13/09 sau khi đếm riêng stock: khay mới 25% đúng người — vẫn 75% sai.
    Vì suất giữ chỗ chỉ là SÀN 4, phần còn lại vẫn xếp theo điểm chữ nên thẻ sai
    người tiếp tục chiếm suất. Mà `xep_3_tang` chấm chúng là "-" (máy không lấy)
    -> chúng ngồi chiếm chỗ vô ích.

    Luật đúng: ngách ĐÃ KHAI nhân vật thì thẻ stock đúng người đi TRƯỚC hết, thẻ
    sai người chỉ lấp chỗ còn trống."""
    from autoedit.sotra.tra import tra

    for i in range(12):                    # sai người, điểm CAO (trúng 2 lớp)
        _clip(kho, f"envato:sai{i}", f"water glass kitchen scene {i}",
              tuoi="young", ct="asian")
    for i in range(8):                     # đúng người, điểm thấp (trúng 1 lớp)
        _clip(kho, f"envato:gia{i}", f"water glass {i}", tuoi="older", ct="white")
    ra = tra(kho, LOP, so=12, nhan_vat=NV, can_neo=False)
    dat = sum(1 for c in ra if c["tuoi"] == "older" and c["chung_toc"] == "white")
    assert dat >= 8, f"chỉ {dat}/12 suất là đúng người — thẻ sai người vẫn tranh suất"


def test_chua_khai_nhan_vat_thi_VAN_xep_theo_diem(kho):
    """Rào chống hồi quy cho Life In: không khai thì thứ tự phải y như cũ."""
    from autoedit.sotra.tra import tra

    for i in range(6):
        _clip(kho, f"envato:cao{i}", f"water glass kitchen scene {i}",
              tuoi="young", ct="asian")
    for i in range(6):
        _clip(kho, f"envato:thap{i}", f"water glass {i}", tuoi="older", ct="white")
    ra = [c["id"] for c in tra(kho, LOP, so=12, can_neo=False)]
    assert ra[0].startswith("envato:cao"), "không khai nhân vật thì điểm cao đứng đầu"
