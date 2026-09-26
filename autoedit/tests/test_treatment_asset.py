"""Treatment — SINH ASSET TỪ YÊU CẦU CỦA NGƯỜI DÙNG (user chốt 25/09).

*"Người dùng click vào từng nhân vật, bối cảnh, đưa ref và yêu cầu. LLM sinh
Asset"* — hai bước, không phải một.

Trước 25/09 chỉ có MỘT bước: LLM vừa đoán tên vừa tự viết luôn mô tả nhận dạng.
Cái nó đoán từ kịch bản là *một* con cá mập chung chung; cái đội cần là *con* cá
mập trong đầu đạo diễn. Người dùng chỉ được duyệt hoặc không — muốn khác thì
phải xoá đi gõ lại bằng tay.

Nay bước 1 (`/so/goi-y`) chỉ GỌI TÊN. Bước 2 là đường này: người dùng gõ yêu cầu
của mình, LLM mới viết hồ sơ nhận dạng theo yêu cầu đó.

Yêu cầu là BẮT BUỘC: để trống thì lại quay về đúng chỗ LLM tự đoán, mà đó chính
là thứ vừa bỏ đi.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho


class SinhGia:
    def __init__(self):
        self.goi = []

    def sinh_asset(self, muc, tong):
        self.goi.append({"muc": dict(muc), "tong": tong})
        return {"chu": "Scarred old great white shark, 5m, torn dorsal fin.",
                "pr": "Full body, three angles, plain white background."}


@pytest.fixture()
def bo(tmp_path):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    kho.luu_so("SE001", [
        {"ma": "toi", "loai": "tong", "ten": "Tối", "chu": "DARK MOOD",
         "tb": "Shot on ARRI"},
        {"ma": "ca_map", "loai": "nhan_vat", "ten": "Cá mập trắng",
         "yc": "con đực già, sẹo dài trên vây lưng, dài chừng 5 mét"}])
    kho.dat_tong_tap("SE001", "toi")
    sg = SinhGia()
    c = TestClient(tao_app(kho, sinh_asset=sg))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    return c, kho, sg


def test_sinh_asset_dien_CHU_va_PR(bo):
    c, kho, _ = bo
    r = c.post("/api/tap/SE001/so/ca_map/sinh")
    assert r.status_code == 200, r.text
    x = [y for y in kho.ds_so("SE001") if y["ma"] == "ca_map"][0]
    assert "torn dorsal fin" in x["chu"]
    assert "plain white background" in x["pr"]


def test_gui_kem_YEU_CAU_cua_nguoi_dung(bo):
    """Đây là cả lý do bước này tồn tại. Không gửi yêu cầu lên thì LLM lại đoán."""
    c, _, sg = bo
    c.post("/api/tap/SE001/so/ca_map/sinh")
    assert sg.goi[0]["muc"]["yc"] == "con đực già, sẹo dài trên vây lưng, dài chừng 5 mét"


def test_gui_kem_TEN_va_LOAI(bo):
    c, _, sg = bo
    c.post("/api/tap/SE001/so/ca_map/sinh")
    assert sg.goi[0]["muc"]["ten"] == "Cá mập trắng"
    assert sg.goi[0]["muc"]["loai"] == "nhan_vat"


def test_gui_kem_MOOD_cua_TAP(bo):
    """Mô tả nhận dạng phải hợp với mood của tập, không thì asset đẹp riêng nó
    mà lạc giữa các cảnh."""
    c, _, sg = bo
    c.post("/api/tap/SE001/so/ca_map/sinh")
    assert "DARK MOOD" in sg.goi[0]["tong"]


def test_CHUA_co_yeu_cau_thi_TU_CHOI(bo):
    """Để trống yêu cầu là quay về đúng chỗ LLM tự đoán — thứ vừa bỏ đi. Chặn
    ở đây, và nói thẳng phải làm gì."""
    c, kho, sg = bo
    so = kho.ds_so("SE001")
    for x in so:
        if x["ma"] == "ca_map":
            x["yc"] = ""
    kho.luu_so("SE001", so)
    r = c.post("/api/tap/SE001/so/ca_map/sinh")
    assert r.status_code == 400
    assert "yêu cầu" in r.json()["detail"].lower()
    assert sg.goi == [], "đã từ chối thì đừng gọi LLM"


def test_yeu_cau_SONG_qua_lan_luu(bo):
    """`yc` là chữ người dùng gõ. Mất nó thì sinh lại ra một asset khác hẳn."""
    c, kho, _ = bo
    x = [y for y in kho.ds_so("SE001") if y["ma"] == "ca_map"][0]
    assert x["yc"] == "con đực già, sẹo dài trên vây lưng, dài chừng 5 mét"


def test_khong_dung_cho_muc_TONG(bo):
    """Tông không phải tài sản — nó không có ref, không có hồ sơ nhận dạng."""
    c, _, _ = bo
    assert c.post("/api/tap/SE001/so/toi/sinh").status_code == 400


def test_khong_co_ma_do_thi_404(bo):
    c, _, _ = bo
    assert c.post("/api/tap/SE001/so/khong_co/sinh").status_code == 404


def test_LLM_hong_thi_502_va_KHONG_mat_yeu_cau(bo):
    class Hong:
        def sinh_asset(self, muc, tong):
            raise RuntimeError("cổng ngã")

    _, kho, _ = bo
    c = TestClient(tao_app(kho, sinh_asset=Hong()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    assert c.post("/api/tap/SE001/so/ca_map/sinh").status_code == 502
    x = [y for y in kho.ds_so("SE001") if y["ma"] == "ca_map"][0]
    assert x["yc"], "hỏng lượt gọi thì cũng không được đụng chữ người dùng gõ"


def test_L2_khong_sinh_duoc(bo):
    _, kho, sg = bo
    xem = TestClient(tao_app(kho, sinh_asset=sg))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.post("/api/tap/SE001/so/ca_map/sinh").status_code == 403


def test_chua_bat_LLM_thi_503(bo):
    _, kho, _ = bo
    c = TestClient(tao_app(kho))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    assert c.post("/api/tap/SE001/so/ca_map/sinh").status_code == 503


# ────────────────────────── prompt ref: phông trắng/xanh, nhiều góc (26/09)
def test_lenh_ref_doi_PHONG_TRANG_HOAC_XANH():
    """User chốt 26/09: "asset cần là phông trắng, hoặc phông xanh, các góc
    khác nhau". Ref là bản mặt để tách ra dùng lại; nền có cảnh thì kéo theo cả
    bối cảnh vào mọi cảnh dùng nó."""
    from autoedit.treatment.dich import _LENH_ASSET

    t = _LENH_ASSET.lower()
    assert "trắng" in t and "xanh" in t, "phải nêu cả nền trắng lẫn nền xanh"


def test_lenh_ref_doi_NHIEU_GOC_cho_nhan_vat_va_dao_cu():
    """Một góc thì nhà AI chỉ có một mặt để bám; quay sang bên là nó tự bịa."""
    from autoedit.treatment.dich import _LENH_ASSET

    t = _LENH_ASSET.lower()
    assert "góc" in t
    for tu in ("chính diện", "bên hông"):
        assert tu in t, f"thiếu góc: {tu}"
    i, j = t.index("nhan_vat"), t.index("boi_canh")
    assert "đạo cụ" in t[:j] or "dao_cu" in t[:j], (
        "đạo cụ cũng phải có nhiều góc, không chỉ nhân vật")
    assert i >= 0


def test_boi_canh_KHONG_bi_ep_phong_trang():
    """Nền trắng cho một bối cảnh là vô nghĩa — bối cảnh cần khung tả không
    gian, không phải bản cắt rời."""
    from autoedit.treatment.dich import _LENH_ASSET

    i = _LENH_ASSET.lower().index("boi_canh")
    assert "nền trắng" not in _LENH_ASSET.lower()[i:i + 400]


def test_lenh_ref_doi_KHONG_CAT_CUT():
    """Đo thật 26/09 với Seedream: bảng ref của nhân vật lọt khung đẹp, nhưng
    bảng ref của càng cẩu Clementine bị CẮT CỤT phần đầu — nhà AI đóng khung
    quá sát. Ref cụt thì mất đúng chi tiết cần tham chiếu."""
    from autoedit.treatment.dich import _LENH_ASSET

    t = _LENH_ASSET.lower()
    assert "thu nhỏ chủ thể" in t, (
        "cấm cắt thì Seedream vẫn cắt — phải bảo nó lùi máy ra")
