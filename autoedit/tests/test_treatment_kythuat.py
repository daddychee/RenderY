"""Treatment — LLM điền CỘT KỸ THUẬT và dịch nội dung cảnh sang prompt tiếng Anh.

Việc 4/4 của đợt 1. Hai thứ nó phải làm:

1. **Dịch nội dung cảnh sang prompt tiếng Anh.** Đội viết treatment bằng tiếng
   Việt ("Ảnh vệ tinh Cuba, bệ phóng tên lửa của Nga đang đứng sừng sững"),
   nhưng prompt gửi Seedream/Gemini phải là tiếng Anh. Trước việc này, prompt
   ghép thẳng chữ Việt vào — nhà AI đọc được lõm bõm là ra ảnh sai.
2. **Điền cỡ cảnh · góc máy · chuyển động · SFX · nhân vật.** Đây là các cột
   trong bảng storyboard user đang xin Gemini làm tay ở bước 5.

Luật ghim: LLM KHÔNG đụng `t` (chữ của người viết) và KHÔNG tự chọn tông — đó
là hai thứ user chốt giữ quyền. Nó chỉ thêm, không sửa.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho


class KyThuatGia:
    """Trả về ĐÚNG số mục nhận vào, như LLM thật phải làm."""

    def __init__(self, hong_tu_lo=None):
        self.lo = []
        self.hong_tu_lo = hong_tu_lo

    def ky_thuat(self, muc, tai_san):
        self.lo.append(list(muc))
        if self.hong_tu_lo is not None and len(self.lo) > self.hong_tu_lo:
            raise RuntimeError("LLM ngã")
        return [{"id": m["id"], "co": "CU", "goc": "eye level",
                 "cd": "slow push in", "sfx": "sonar ping", "ts": ["k129"],
                 "pa": "Close-up of a hand flipping a switch, 1968",
                 "pv": "The hand flips the switch, slow push in"} for m in muc]


@pytest.fixture()
def bo(tmp_path):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    kho.luu_so("SE001", [{"ma": "k129", "loai": "dao_cu", "ten": "Tàu K-129",
                          "chu": "Soviet Golf-II"}])
    kt = KyThuatGia()
    c = TestClient(tao_app(kho, ky_thuat=kt))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "Voice one.", "vi": "", "het": 0,
         "canh": [{"t": "Cận bàn tay bật công tắc"}, {"t": "Sonar nhấp nháy"}]},
        {"en": "Voice two.", "vi": "", "het": 0,
         "canh": [{"t": "Tàu ngầm lướt đáy biển"}]}]})
    return c, kho, kt


def _canh(kho):
    return [c for d in kho.doc("SE001", "H")["dong"] for c in d.get("canh", [])]


# ------------------------------------------------------------- dịch prompt
def test_dien_prompt_TIENG_ANH_cho_tung_canh(bo):
    c, kho, _ = bo
    r = c.post("/api/tap/SE001/H/ky-thuat")
    assert r.status_code == 200, r.text
    assert all(x["pa"] and x["pv"] for x in _canh(kho))


def test_KHONG_dung_chu_cua_nguoi_viet(bo):
    """`t` là chữ người viết. LLM chỉ được THÊM, không sửa."""
    c, kho, _ = bo
    c.post("/api/tap/SE001/H/ky-thuat")
    assert [x["t"] for x in _canh(kho)] == [
        "Cận bàn tay bật công tắc", "Sonar nhấp nháy", "Tàu ngầm lướt đáy biển"]


def test_KHONG_tu_chon_tong(bo):
    """Tông là quyền của user (chốt 24/09)."""
    c, kho, _ = bo
    c.post("/api/tap/SE001/H/ky-thuat")
    assert all("tong" not in x for x in _canh(kho))


# ------------------------------------------------------------- cột kỹ thuật
def test_dien_du_cot_ky_thuat(bo):
    c, kho, _ = bo
    c.post("/api/tap/SE001/H/ky-thuat")
    x = _canh(kho)[0]
    assert x["co"] == "CU" and x["goc"] and x["cd"] and x["sfx"]


def test_ts_la_ma_co_trong_SO(tmp_path):
    """LLM trả mã tài sản không có trong sổ thì bỏ — không thì prompt đính mô tả
    rỗng, hoặc tệ hơn là trỏ vào thứ không tồn tại."""
    class Bay:
        def ky_thuat(self, muc, tai_san):
            return [{"id": m["id"], "pa": "x", "pv": "y",
                     "ts": ["k129", "khong_co"]} for m in muc]

    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "x")
    kho.luu_so("SE001", [{"ma": "k129", "loai": "dao_cu", "ten": "T", "chu": ""}])
    c = TestClient(tao_app(kho, ky_thuat=Bay()))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "A", "vi": "", "het": 0, "canh": [{"t": "x"}]}]})
    c.post("/api/tap/SE001/H/ky-thuat")
    assert _canh(kho)[0]["ts"] == ["k129"]


# ------------------------------------------------------------- chạy lại
def test_chi_dien_canh_CON_THIEU(bo):
    c, kho, kt = bo
    c.post("/api/tap/SE001/H/ky-thuat")
    kt.lo.clear()
    r = c.post("/api/tap/SE001/H/ky-thuat").json()
    assert kt.lo == [], "cảnh đã có prompt thì đừng gọi LLM lần nữa"
    assert r["xong"] == 0


def test_gui_kem_VOICE_va_SO_TAI_SAN(bo):
    """Không có voice thì LLM không biết cảnh đang kể gì; không có sổ thì nó
    không gắn được nhân vật vào cảnh."""
    c, _, kt = bo
    c.post("/api/tap/SE001/H/ky-thuat")
    dau = kt.lo[0][0]
    assert "Voice one." in str(dau)


# ------------------------------------------------------------- hỏng giữa chừng
def test_lo_hong_thi_GIU_phan_da_xong(tmp_path):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "x")
    kt = KyThuatGia(hong_tu_lo=1)
    c = TestClient(tao_app(kho, ky_thuat=kt))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "A", "vi": "", "het": 0,
         "canh": [{"t": "c%d" % i} for i in range(20)]}]})
    r = c.post("/api/tap/SE001/H/ky-thuat").json()
    assert 0 < r["xong"] < 20 and r["con_thieu"] > 0 and r["loi"]
    assert sum(1 for x in _canh(kho) if x.get("pa")) == r["xong"], \
        "lô nào xong phải được lưu ngay, đừng để lô sau ngã là mất sạch"


def _bo(tmp_path, may, canh):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "x")
    c = TestClient(tao_app(kho, ky_thuat=may))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "A", "vi": "", "het": 0, "canh": [{"t": t} for t in canh]}]})
    return c, kho


def test_LLM_NUOT_mot_muc_thi_khong_lech_hang(tmp_path):
    """ĐO THẬT 24/09 trên C1 bằng claude-sonnet-5: gửi 8 cảnh, nó trả 7. Khớp
    theo VỊ TRÍ thì cảnh 2 nhận prompt của cảnh 3 — sai câm. Nên mỗi cảnh mang
    MÃ và khớp theo mã: mục nào nó nuốt thì cảnh đó để trống, bấm lại chạy tiếp.
    """
    class Nuot:
        def ky_thuat(self, muc, tai_san):
            return [{"id": m["id"], "pa": "EN " + m["canh"], "pv": "mv"}
                    for m in muc if m["canh"] != "b"]

    c, kho = _bo(tmp_path, Nuot(), ["a", "b", "c"])
    r = c.post("/api/tap/SE001/H/ky-thuat").json()
    cs = [x for d in kho.doc("SE001", "H")["dong"] for x in d["canh"]]
    assert cs[0]["pa"] == "EN a" and cs[2]["pa"] == "EN c", "không được lệch hàng"
    assert "pa" not in cs[1], "mục bị nuốt để trống, không nhận nhầm của cảnh khác"
    assert r["con_thieu"] == 1


def test_ma_la_tu_LLM_bi_bo(tmp_path):
    class Bay:
        def ky_thuat(self, muc, tai_san):
            return [{"id": "khong-co-that", "pa": "x", "pv": "y"}]

    c, kho = _bo(tmp_path, Bay(), ["a"])
    assert c.post("/api/tap/SE001/H/ky-thuat").status_code == 502


def test_ca_lo_khong_khop_gi_thi_bao_loi(tmp_path):
    class Rong:
        def ky_thuat(self, muc, tai_san):
            return []

    c, _ = _bo(tmp_path, Rong(), ["a", "b"])
    assert c.post("/api/tap/SE001/H/ky-thuat").status_code == 502


# ------------------------------------------------------------- cửa gác
def test_L2_khong_chay_duoc(bo):
    _, kho, kt = bo
    xem = TestClient(tao_app(kho, ky_thuat=kt))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.post("/api/tap/SE001/H/ky-thuat").status_code == 403


def test_chua_bat_LLM_thi_503(bo):
    _, kho, _ = bo
    c = TestClient(tao_app(kho))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    assert c.post("/api/tap/SE001/H/ky-thuat").status_code == 503
