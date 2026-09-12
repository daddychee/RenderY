r"""ĐƠN HÀNG HÚT TỪ REF — "lấy ref làm gốc" (user chốt 12/09).

Mỗi cảnh ref đã được đọc hình (có nhân vật + vật thể) nên nó TỰ SINH RA câu tìm
chính xác: `older adult` + vật thể của cảnh. Đây đúng là thứ kho đang thiếu.

Đo 12/09 — kho hiện có, đếm theo cửa nhân vật (già + da trắng):
    ref 31/95 (33%) · envato 28/372 (7,5%) · pexels 5/62 (8%) · pixabay 0/16 (0%)

Tra thật ngoài kia: **Pexels có hàng** ("elderly men running on the beach",
"an elderly couple exercising together"); **Pixabay thì không** — cùng từ khoá
`elderly hands coffee cup` nó trả "pie fruit pie dessert", "mount fuji morning
clouds": nó bỏ qua chữ `elderly`, chỉ khớp token rời.

Nên tỉ lệ 1:1:1 là **mục tiêu có báo cáo**, KHÔNG phải hạn mức cứng: nguồn nào
không giao được thì GHI LÀ THIẾU. Ép một suất pixabay mỗi khay = ép một clip sai
vào khay, đúng cái bệnh đang chữa.

Chủng tộc KHÔNG đưa vào câu tìm (kho stock không đánh chỉ mục việc đó) — nó là
CỬA lúc đọc hình, không phải từ khoá lúc hút.
"""

from __future__ import annotations

import pytest

NV = {"tuoi": ["older"], "chung_toc": ["white"]}


@pytest.fixture
def kho(tmp_path):
    from autoedit.sotra import db as sdb

    conn = sdb.mo(tmp_path / "so_tra.db")
    yield conn
    conn.close()


def _ref(conn, khuc, vat_the, tap="SH010", **kw):
    from autoedit.sotra import db as sdb

    sdb.them_clip(conn, {"id": f"ref:v:{khuc}", "nguon": "ref", "tap": tap,
                         "tieu_de": kw.get("tieu_de", "canh"), "vat_the": vat_the})


# ------------------------------------------------------------------ câu tìm

def test_cau_tim_gom_tu_TUOI_va_VAT_THE():
    from autoedit.sotra import don_hang

    c = don_hang.cau_tim(NV, "water glass, pill bottle")
    assert c.startswith("older adult ")
    assert "water glass" in c and "pill bottle" in c


def test_cau_tim_KHONG_chua_chung_toc():
    """Kho stock không đánh chỉ mục chủng tộc — nhồi vào chỉ làm câu tìm lệch."""
    from autoedit.sotra import don_hang

    assert "white" not in don_hang.cau_tim(NV, "water glass")


def test_cau_tim_bo_tu_do_dac_chung():
    from autoedit.sotra import don_hang

    c = don_hang.cau_tim(NV, "table, glass, hand, blood pressure monitor")
    assert "blood pressure monitor" in c
    assert " table" not in c and " hand" not in c


def test_nhan_vat_rong_thi_cau_tim_CHI_co_vat_the():
    from autoedit.sotra import don_hang

    assert don_hang.cau_tim({}, "marigold garland") == "marigold garland"


# ------------------------------------------------------------------ lập đơn

def test_don_lay_ref_CUA_TAP_do(kho):
    from autoedit.sotra import don_hang

    _ref(kho, "1", "water glass", tap="SH010")
    _ref(kho, "2", "prayer flags", tap="LI106")
    ds = don_hang.don_tu_ref(kho, "SH010", NV)
    assert len(ds) == 1 and "water glass" in ds[0]


def test_ref_khong_co_vat_the_thi_KHONG_sinh_cau(kho):
    """Không có vật thể thì câu tìm chỉ còn `older adult` — hút về một rổ vô
    hướng. Thà không hút."""
    from autoedit.sotra import don_hang

    _ref(kho, "1", "")
    assert don_hang.don_tu_ref(kho, "SH010", NV) == []


def test_cau_trung_nhau_chi_HUT_MOT_LAN(kho):
    from autoedit.sotra import don_hang

    _ref(kho, "1", "water glass")
    _ref(kho, "2", "water glass")
    assert len(don_hang.don_tu_ref(kho, "SH010", NV)) == 1


# ------------------------------------------------------------------ chạy đơn

def _tim_gia(tra: dict):
    """tim(nguon, cau) -> list[clip]; `tra` khai sẵn mỗi nguồn trả gì."""
    def tim(nguon, cau):
        if isinstance(tra.get(nguon), Exception):
            raise tra[nguon]
        # id PHẢI khác nhau từng clip — trùng id là kho gộp về một dòng, rồi
        # test đếm thiếu mà tưởng code sai (bắt được đúng lúc 12/09).
        return [{"id": f"{nguon}:{abs(hash(cau)) % 9999}-{k}", "nguon": nguon,
                 "tieu_de": f"{nguon} {cau} {k}"} for k in range(tra.get(nguon, 0))]
    return tim


def test_chay_don_ghi_clip_moi_va_dem_theo_nguon(kho):
    from autoedit.sotra import don_hang

    _ref(kho, "1", "water glass")
    bc = don_hang.chay_don(kho, "SH010", NV,
                           tim=_tim_gia({"envato": 1, "pexels": 1, "pixabay": 1}))
    assert bc["so_cau"] == 1
    assert bc["theo_nguon"] == {"envato": 1, "pexels": 1, "pixabay": 1}
    assert kho.execute("SELECT COUNT(*) FROM clip WHERE nguon='pexels'"
                       ).fetchone()[0] == 1


def test_nguon_khong_giao_duoc_thi_GHI_LA_THIEU(kho):
    """Đúng lời user: "thiếu thì ghi sổ chứ không lấp"."""
    from autoedit.sotra import don_hang

    _ref(kho, "1", "water glass")
    bc = don_hang.chay_don(kho, "SH010", NV,
                           tim=_tim_gia({"envato": 1, "pexels": 1, "pixabay": 0}))
    assert bc["theo_nguon"]["pixabay"] == 0
    assert any("pixabay" in x for x in bc["thieu"])


def test_mot_nguon_loi_KHONG_giet_don_hang(kho):
    from autoedit.sotra import don_hang

    _ref(kho, "1", "water glass")
    bc = don_hang.chay_don(kho, "SH010", NV, tim=_tim_gia(
        {"envato": RuntimeError("captcha"), "pexels": 2, "pixabay": 1}))
    assert bc["theo_nguon"]["pexels"] == 2
    assert any("envato" in x for x in bc["thieu"])


def test_clip_hut_ve_mang_dau_TAP(kho):
    """Hàng tạm của một tập phải mang dấu tập — đóng job thì dọn được
    (cột `tam_tap` đã có từ 08/09)."""
    from autoedit.sotra import don_hang

    _ref(kho, "1", "water glass")
    don_hang.chay_don(kho, "SH010", NV, tim=_tim_gia({"pexels": 1}), tam_tap=True)
    r = kho.execute("SELECT tam_tap FROM clip WHERE nguon='pexels'").fetchone()
    assert r[0] == "SH010"
