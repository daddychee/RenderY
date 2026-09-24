"""Treatment — TOOL TỰ GỌI TÊN ĐỦ TÀI SẢN (user chốt 24/09).

*"Ông call đủ các asset, tôi sẽ upload ref"* — đúng bước 2 trong quy trình tay
của user: *"liệt kê tất cả nhân vật, đạo cụ, bối cảnh trong X shot trên và tạo
prompt tiếng anh cho từng đạo cụ, bối cảnh"*.

Khác quy trình tay ở hai chỗ, và cả hai đều là lý do tool tồn tại:
  - chat quét được một lần rồi quên; tool quét CẢ TẬP và gộp trùng
  - đề xuất KHÔNG tự ghi vào sổ — người duyệt rồi mới nhận (luật cứng #5)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho


class GoiYGia:
    """Trả về theo LÔ như LLM thật, có trùng lặp giữa các lô."""

    def __init__(self):
        self.lo = []

    def goi_y(self, canh):
        self.lo.append(list(canh))
        return [{"loai": "dao_cu", "ten": "Tàu ngầm K-129",
                 "chu": "Soviet Golf-II class", "pr": "Full body, 3 angles"},
                {"loai": "boi_canh", "ten": "Đáy Thái Bình Dương",
                 "chu": "Abyssal plain", "pr": "Wide establishing"}]


@pytest.fixture()
def bo(tmp_path):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    gg = GoiYGia()
    c = TestClient(tao_app(kho, goi_y=gg))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    for ma in ("H", "C1"):
        c.post("/api/tap/SE001/chuong", json={"ma": ma})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "A", "vi": "", "het": 0, "canh": [{"t": "Tàu ngầm lướt đáy biển"}]}]})
    c.put("/api/tap/SE001/C1", json={"outline": "", "dong": [
        {"en": "B", "vi": "", "het": 0, "canh": [{"t": "Cận bàn tay"},
                                                 {"t": "Sonar nhấp nháy"}]}]})
    return c, kho, gg


def test_goi_y_gop_TRUNG_giua_cac_lo(bo):
    """Hai chương cùng nhắc tàu ngầm thì sổ chỉ nên có MỘT mục — không thì mỗi
    chương một ref, nhân vật lệch nhau giữa các cảnh."""
    c, _, gg = bo
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    assert [x["ten"] for x in ds] == ["Tàu ngầm K-129", "Đáy Thái Bình Dương"],         "hai chương cùng nhắc tàu ngầm mà ra hai mục là mỗi chương một ref"


def test_tap_dai_thi_QUET_THEO_LO(bo):
    """Bài học 23/09: JSON dài là cụt giữa chừng. Cả tập thật ~98 cảnh nên
    không được nhét một lượt."""
    c, _, gg = bo
    c.post("/api/tap/SE001/chuong", json={"ma": "C2"})
    c.put("/api/tap/SE001/C2", json={"outline": "", "dong": [
        {"en": "x", "vi": "", "het": 0,
         "canh": [{"t": "cảnh %d" % i} for i in range(60)]}]})
    gg.lo.clear()
    c.post("/api/tap/SE001/so/goi-y")
    assert len(gg.lo) >= 3, "63 cảnh phải chia làm nhiều lô"
    assert max(len(x) for x in gg.lo) <= 25


def test_goi_y_gui_dung_NOI_DUNG_CANH_cho_LLM(bo):
    c, _, gg = bo
    c.post("/api/tap/SE001/so/goi-y")
    het = [t for lo in gg.lo for t in lo]
    assert "Tàu ngầm lướt đáy biển" in het and "Sonar nhấp nháy" in het


def test_goi_y_KHONG_tu_ghi_vao_so(bo):
    """Luật cứng #5: tool đề xuất, người duyệt. Tự ghi là sổ đầy rác sau một
    lần bấm nhầm."""
    c, kho, _ = bo
    c.post("/api/tap/SE001/so/goi-y")
    assert [x for x in kho.ds_so("SE001") if x["loai"] != "tong"] == []


def test_ma_tu_sinh_DUNG_DUOC_lam_ten_file(bo):
    """`ma` đi thẳng vào tên file ref. Tên tiếng Việt có dấu và dấu cách nên
    phải chuyển thành mã sạch, không thì tải ref lên là 400."""
    c, kho, _ = bo
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    for x in ds:
        kho.duong_ref("SE001", x["ma"], ".png")      # ném ValueError là hỏng


def test_ma_khong_trung_nhau(bo):
    c, _, _ = bo
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    assert len({x["ma"] for x in ds}) == len(ds)


def test_loai_la_tu_LLM_bi_loai(tmp_path):
    class Bay:
        def goi_y(self, canh):
            return [{"loai": "vu_tru", "ten": "X", "chu": "", "pr": ""},
                    {"loai": "dao_cu", "ten": "Tốt", "chu": "", "pr": ""}]

    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "x")
    c = TestClient(tao_app(kho, goi_y=Bay()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "A", "vi": "", "het": 0, "canh": [{"t": "x"}]}]})
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    assert [x["ten"] for x in ds] == ["Tốt"]


def test_khong_co_canh_nao_thi_bao_ro(bo):
    c, kho, _ = bo
    kho.tao_tap("SE002", "trống")
    r = c.post("/api/tap/SE002/so/goi-y")
    assert r.status_code == 400


def test_L2_khong_goi_y_duoc(bo):
    _, kho, gg = bo
    xem = TestClient(tao_app(kho, goi_y=gg))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.post("/api/tap/SE001/so/goi-y").status_code == 403


def test_chua_bat_LLM_thi_503(bo):
    _, kho, _ = bo
    c = TestClient(tao_app(kho))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    assert c.post("/api/tap/SE001/so/goi-y").status_code == 503
