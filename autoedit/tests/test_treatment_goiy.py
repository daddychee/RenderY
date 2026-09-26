"""Treatment — LLM ĐỌC CẢ KỊCH BẢN rồi gọi tên Asset + đề xuất Mood.

User chốt 25/09: "LLM tự đọc full kịch bản bằng tiếng Anh sau đó chia cụm đề
xuất: Nhân vật, Bối cảnh" và "LLM cũng đọc kịch bản và đề xuất mood dựa trên
việc hiểu kịch bản".

Khác bản trước ở ba chỗ, cả ba đều đo được:

1. Trước đây quét `canh[i].t` — mô tả cảnh BIÊN KỊCH VIẾT BẰNG TIẾNG VIỆT. Nguồn
   sự thật là bản tiếng Anh; đi qua một lớp dịch là trôi tên riêng.
2. Trước đây chia lô 25 cảnh vì sợ JSON cụt. Đo thật 25/09: toàn bộ `en` của
   SE001 là 36.542 ký tự ~ 9.100 token — lọt một lượt thoải mái, và bỏ được cả
   vòng chia lô lẫn đoạn gộp trùng giữa các lô.
3. Chương chưa viết treatment thì quét theo cảnh là VÔ HÌNH. Đo thật: C6 và E
   của SE001 có 0 cảnh. Đọc kịch bản thì asset của cả tập hiện ra ngay từ đầu —
   đúng thứ tự làm việc: lập sổ trước, viết cảnh sau.

Giữ nguyên hai luật cũ: gộp trùng, và KHÔNG tự ghi vào sổ (luật cứng #5).

LLM chỉ GỌI TÊN, không viết mô tả nhận dạng: mô tả sinh ở bước sau, từ yêu cầu
của chính người dùng (user chốt 25/09 — "Người dùng click vào từng nhân vật,
bối cảnh, đưa ref và yêu cầu. LLM sinh Asset").
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

MOOD = {"ten": "Tối & bí ẩn", "chu": "Photorealistic. Mood and tone: dark.",
        "tb": "Shot on ARRI Alexa 35, 40mm anamorphic prime.",
        "ly_do": "Kịch bản kể một chiến dịch tình báo bị giấu kín."}


class GoiYGia:
    """Nhận CẢ kịch bản trong MỘT lượt, trả tài sản + mood."""

    def __init__(self):
        self.goi = []

    def goi_y(self, kich_ban):
        self.goi.append(kich_ban)
        return {"tai_san": [
            {"loai": "dao_cu", "ten": "Tàu ngầm K-129", "ly_do": "lặp nhiều cảnh"},
            {"loai": "boi_canh", "ten": "Đáy Thái Bình Dương",
             "ly_do": "bối cảnh chính"},
            {"loai": "dao_cu", "ten": "tàu ngầm k-129", "ly_do": "khác hoa thường"}],
            "mood": dict(MOOD)}


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
        {"en": "In March 1968 a Soviet submarine vanished.", "vi": "", "het": 0,
         "canh": [{"t": "Tàu ngầm lướt đáy biển"}]}]})
    c.put("/api/tap/SE001/C1", json={"outline": "", "dong": [
        {"en": "The CIA built a ship to steal it.", "vi": "", "het": 0,
         "canh": [{"t": "Cận bàn tay"}, {"t": "Sonar nhấp nháy"}]}]})
    return c, kho, gg


# ─────────────────────────────────────────────────── đọc kịch bản tiếng Anh
def test_gui_TOAN_BO_KICH_BAN_TIENG_ANH(bo):
    """Nguồn sự thật là bản tiếng Anh. Gửi mô tả cảnh tiếng Việt là bắt LLM
    đoán ngược tên riêng qua một lớp dịch."""
    c, _, gg = bo
    c.post("/api/tap/SE001/so/goi-y")
    assert len(gg.goi) == 1, "cả tập đi MỘT lượt, không chia lô nữa"
    than = gg.goi[0]
    assert "In March 1968 a Soviet submarine vanished." in than
    assert "The CIA built a ship to steal it." in than


def test_KHONG_gui_mo_ta_canh_tieng_Viet(bo):
    c, _, gg = bo
    c.post("/api/tap/SE001/so/goi-y")
    assert "Sonar nhấp nháy" not in gg.goi[0]


def test_chuong_CHUA_viet_treatment_van_quet_duoc(tmp_path):
    """Đo thật trên SE001: C6 và E có 0 cảnh. Quét theo cảnh thì hai chương đó
    vô hình — mà chúng vẫn có kịch bản, vẫn có nhân vật cần vào sổ."""
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "x")
    gg = GoiYGia()
    c = TestClient(tao_app(kho, goi_y=gg))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "A ghost fleet under the ice.", "vi": "", "het": 0}]})
    r = c.post("/api/tap/SE001/so/goi-y")
    assert r.status_code == 200, r.text
    assert "A ghost fleet under the ice." in gg.goi[0]


def test_tap_chua_co_kich_ban_thi_bao_ro(bo):
    c, kho, _ = bo
    kho.tao_tap("SE002", "trống")
    r = c.post("/api/tap/SE002/so/goi-y")
    assert r.status_code == 400


# ─────────────────────────────────────────────────────────── tài sản đề xuất
def test_goi_y_gop_TRUNG(bo):
    """Cùng một thứ gọi hai cách thì sổ chỉ nên có MỘT mục — không thì mỗi cảnh
    một ref, nhân vật lệch nhau giữa các cảnh."""
    c, _, _ = bo
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    assert [x["ten"] for x in ds] == ["Tàu ngầm K-129", "Đáy Thái Bình Dương"]


def test_goi_y_mang_theo_LY_DO(bo):
    """Người duyệt phải thấy VÌ SAO, không thì duyệt mù cả danh sách."""
    c, _, _ = bo
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    assert ds[0]["ly_do"] == "lặp nhiều cảnh"


def test_goi_y_KHONG_kem_mo_ta_nhan_dang(bo):
    """Mô tả sinh ở bước sau, từ YÊU CẦU của người dùng. LLM tự đoán ra một con
    cá mập chung chung thì người ta phải xoá đi gõ lại — thà để trống."""
    c, _, _ = bo
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    assert all(not x["chu"] and not x["pr"] for x in ds)


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
    for x in c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]:
        kho.duong_ref("SE001", x["ma"], ".png")      # ném ValueError là hỏng


def test_ma_khong_trung_nhau(bo):
    c, _, _ = bo
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    assert len({x["ma"] for x in ds}) == len(ds)


def test_loai_la_tu_LLM_bi_loai(tmp_path):
    class Bay:
        def goi_y(self, kich_ban):
            return {"tai_san": [{"loai": "vu_tru", "ten": "X"},
                                {"loai": "dao_cu", "ten": "Tốt"}]}

    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "x")
    c = TestClient(tao_app(kho, goi_y=Bay()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "A", "vi": "", "het": 0}]})
    ds = c.post("/api/tap/SE001/so/goi-y").json()["goi_y"]
    assert [x["ten"] for x in ds] == ["Tốt"]


# ─────────────────────────────────────────────────────────────── mood đề xuất
def test_de_xuat_MOOD_cho_ca_tap(bo):
    """User 25/09: "Chưa thấy có phần yêu cầu mood. Đề xuất tính năng LLM cũng
    đọc kịch bản và đề xuất mood". Cùng một lượt đọc — nó đã đọc hết rồi thì
    hỏi luôn, không tốn thêm lượt gọi."""
    c, _, _ = bo
    r = c.post("/api/tap/SE001/so/goi-y").json()
    assert r["mood"]["ten"] == MOOD["ten"]
    assert r["mood"]["chu"] == MOOD["chu"]
    assert r["mood"]["tb"] == MOOD["tb"]


def test_mood_mang_theo_LY_DO(bo):
    """Duyệt mood mà không thấy căn cứ thì chỉ là bấm đồng ý."""
    c, _, _ = bo
    assert c.post("/api/tap/SE001/so/goi-y").json()["mood"]["ly_do"] == MOOD["ly_do"]


def test_mood_KHONG_tu_ghi_vao_so(bo):
    c, kho, _ = bo
    c.post("/api/tap/SE001/so/goi-y")
    assert kho.ds_so("SE001") == []
    assert kho.tong_tap("SE001") == ""


def test_LLM_khong_tra_mood_thi_van_chay(bo):
    """Mất mood còn hơn mất cả bảng tài sản."""
    c, _, gg = bo
    gg.goi_y = lambda kich_ban: {"tai_san": [{"loai": "dao_cu", "ten": "X"}]}
    r = c.post("/api/tap/SE001/so/goi-y").json()
    assert r["mood"] == {}
    assert [x["ten"] for x in r["goi_y"]] == ["X"]


# ───────────────────────────────────────────────────────────────── quyền / cổng
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


# ─────────────────────── xếp loại PHƯƠNG TIỆN (đo thật 26/09)
def test_lenh_quet_KHONG_xep_phuong_tien_vao_boi_canh():
    """Đo trên sổ SE001 thật: ba con tàu rơi vào HAI nhóm khác nhau —
    `Tàu ngầm K-129` và `Tàu Hughes Glomar Explorer` thành `boi_canh`, còn
    `Tàu hải quân Liên Xô theo dõi` thành `nhan_vat`.

    Loại không phải chuyện phân loại cho đẹp: nó quyết định LUẬT của prompt ref.
    Xếp con tàu vào bối cảnh thì ref ra một tấm phong cảnh biển — user báo 26/09
    "không dùng được, nó cũng không có đủ góc cạnh và fullshot".

    Ranh giới phải viết thành câu dứt khoát: bối cảnh là NƠI CHỐN. Vật có hình
    dáng cố định — người, sinh vật, phương tiện, máy móc — không bao giờ là bối
    cảnh; BÊN TRONG nó thì mới là."""
    from autoedit.treatment.dich import _LENH_TAI_SAN

    t = _LENH_TAI_SAN.lower()
    assert "nơi chốn" in t
    assert "phương tiện" in t
    i = t.index("`boi_canh`")
    assert "không" in t[i:i + 500], "phải nói RÕ cái gì KHÔNG phải bối cảnh"
    j = t.index("`dao_cu`")
    assert "phương tiện" in t[min(i, j):], "phương tiện phải được xếp dứt khoát"
