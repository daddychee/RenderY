"""Treatment — CREATE PROMPT: dịch cảnh sang prompt tiếng Anh + cột kỹ thuật.

Chạy cho ĐÚNG MỘT CẢNH (user chốt 25/09: *"đưa Sinh prompt về từng cảnh luôn.
Đổi tên thành Create Prompt"*). Cùng lý do với ảnh: mỗi cảnh là một quyết định,
không chạy hàng loạt rồi mới ngồi soát.

Hai việc nó làm:

1. **Dịch nội dung cảnh sang prompt tiếng Anh.** Đội viết treatment bằng tiếng
   Việt ("Ảnh vệ tinh Cuba, bệ phóng tên lửa của Nga đang đứng sừng sững"),
   nhưng prompt gửi Seedream phải là tiếng Anh. Ghép thẳng chữ Việt vào là nhà
   AI đọc lõm bõm rồi ra ảnh sai.
2. **Điền cỡ cảnh · góc máy · chuyển động · SFX · asset dùng trong cảnh.**

Luật ghim: LLM KHÔNG đụng `t` (chữ của người viết) và KHÔNG tự chọn `tong` —
hai thứ user giữ quyền. Nó chỉ thêm, không sửa.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho


class KyThuatGia:
    def __init__(self, tra=None):
        self.goi = []
        self.tra = tra

    def ky_thuat(self, muc, tai_san):
        self.goi.append((list(muc), list(tai_san)))
        if self.tra is not None:
            return self.tra(muc, tai_san)
        return [{"id": m["id"], "co": "CU", "goc": "eye level",
                 "cd": "slow push in", "sfx": "sonar ping", "ts": ["k129"],
                 "pa": "Close-up of a hand flipping a switch, 1968",
                 "pv": "The hand flips the switch, slow push in"} for m in muc]


def _dung(tmp_path, kt, canh=("Cận bàn tay bật công tắc", "Sonar nhấp nháy"),
          so=({"ma": "k129", "loai": "dao_cu", "ten": "Tàu K-129",
               "chu": "Soviet Golf-II"},)):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    if so:
        kho.luu_so("SE001", [dict(x) for x in so])
    c = TestClient(tao_app(kho, ky_thuat=kt))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    c.put("/api/tap/SE001/H", json={"outline": "", "dong": [
        {"en": "Voice one.", "vi": "", "het": 0,
         "canh": [{"t": t} for t in canh]}]})
    return c, kho


@pytest.fixture()
def bo(tmp_path):
    kt = KyThuatGia()
    c, kho = _dung(tmp_path, kt)
    return c, kho, kt


def _cs(kho):
    return kho.doc("SE001", "H")["dong"][0]["canh"]


def _ma(kho, k=0):
    return _cs(kho)[k]["id"]


def _goi(c, kho, k=0):
    return c.post(f"/api/tap/SE001/H/canh/{_ma(kho, k)}/ky-thuat")


# ------------------------------------------------------- chạy theo TỪNG CẢNH
def test_chi_dung_dung_canh_duoc_goi(bo):
    c, kho, _ = bo
    assert _goi(c, kho, 0).status_code == 200
    cs = _cs(kho)
    assert cs[0]["pa"] and cs[0]["pv"] and cs[0]["co"]
    assert not cs[1].get("pa"), "không được đụng cảnh bên cạnh"


def test_KHONG_con_duong_chay_ca_chuong(bo):
    """Bỏ nút mà để đường API lại là một tab cũ vẫn gọi được cho cả chương."""
    c, _, _ = bo
    assert c.post("/api/tap/SE001/H/ky-thuat").status_code == 404


# ------------------------------------------------------- dịch prompt
def test_dien_prompt_TIENG_ANH(bo):
    c, kho, _ = bo
    _goi(c, kho)
    assert "flipping a switch" in _cs(kho)[0]["pa"]


def test_KHONG_dung_chu_cua_nguoi_viet(bo):
    c, kho, _ = bo
    _goi(c, kho)
    assert [x["t"] for x in _cs(kho)] == ["Cận bàn tay bật công tắc",
                                          "Sonar nhấp nháy"]


def test_KHONG_tu_chon_tong(bo):
    """Tông là quyền của user (chốt 24/09)."""
    c, kho, _ = bo
    _goi(c, kho)
    assert "tong" not in _cs(kho)[0]


def test_dien_du_cot_ky_thuat(bo):
    c, kho, _ = bo
    _goi(c, kho)
    x = _cs(kho)[0]
    assert x["co"] == "CU" and x["goc"] and x["cd"] and x["sfx"]


def test_co_canh_la_bi_bo(tmp_path):
    """Cỡ cảnh ngoài bảng thì bỏ — chip trên thẻ chỉ nhận WS/MS/CU/ECU/AERIAL."""
    kt = KyThuatGia(tra=lambda m, t: [{"id": m[0]["id"], "pa": "x", "pv": "y",
                                       "co": "SIEU_RONG"}])
    c, kho = _dung(tmp_path, kt, canh=("a",))
    _goi(c, kho)
    assert "co" not in _cs(kho)[0]


# ------------------------------------------------------- asset
def test_LLM_KHONG_duoc_GAN_ASSET(tmp_path):
    """User chốt 25/09: *"Người dùng chọn nhân vật và bối cảnh (nếu bắt buộc cần
    đồng nhất)… Không để LLM tự nhớ"*.

    Người chọn, không phải máy. Bớt một chỗ LLM bịa mã, và bớt một đường ghi đè
    lựa chọn có chủ đích của người dùng. Đo thật trên SE001 trước khi đổi: 0/83
    cảnh có asset — LLM chưa từng gán nổi mã nào, vì sổ trống thì không có gì
    để gán."""
    kt = KyThuatGia(tra=lambda m, t: [{"id": m[0]["id"], "pa": "x", "pv": "y",
                                       "ts": ["k129"]}])
    c, kho = _dung(tmp_path, kt, canh=("a",))
    _goi(c, kho)
    assert "ts" not in _cs(kho)[0], "LLM trả `ts` thì cũng phải bị bỏ ngoài"


def test_create_prompt_KHONG_XOA_asset_nguoi_dung_da_chon(tmp_path):
    """Chọn asset xong bấm Create Prompt lại là mất lựa chọn thì không ai dám
    bấm lần hai."""
    kt = KyThuatGia(tra=lambda m, t: [{"id": m[0]["id"], "pa": "x", "pv": "y"}])
    c, kho = _dung(tmp_path, kt, canh=("a",))
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = ["k129"]
    kho.luu("SE001", "H", d, "", "thu")
    _goi(c, kho)
    assert _cs(kho)[0]["ts"] == ["k129"]


def test_gui_kem_VOICE(bo):
    """Không có voice thì LLM không biết cảnh đang kể gì."""
    c, kho, kt = bo
    _goi(c, kho)
    assert kt.goi[0][0][0]["voice"] == "Voice one."


def test_chi_gui_asset_CUA_CANH_khong_gui_ca_so(bo):
    """LLM không còn việc CHỌN asset nữa, nên đưa cả sổ là đưa thừa — nó chỉ
    cần biết chủ thể của CẢNH NÀY trông ra sao để tả cho khớp. Sổ 30 mục mà
    cảnh dùng 1 thì 29 mục kia chỉ là chỗ cho nó lạc."""
    c, kho, kt = bo
    _goi(c, kho)
    assert kt.goi[0][1] == [], "cảnh chưa chọn asset thì không gửi mục nào"

    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = ["k129"]
    kho.luu("SE001", "H", d, "", "thu")
    kt.goi.clear()
    _goi(c, kho)
    assert [x["ma"] for x in kt.goi[0][1]] == ["k129"]


def test_tra_ve_so_asset_CUA_CANH(bo):
    """Con số này là số asset CẢNH ĐANG CÓ (người dùng đã chọn), không còn là số
    LLM vừa gán — trang dùng nó để nói prompt vừa kèm bao nhiêu mô tả."""
    c, kho, _ = bo
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"][0]["ts"] = ["k129"]
    kho.luu("SE001", "H", d, "", "thu")
    assert _goi(c, kho).json()["gan_asset"] == 1


# ------------------------------------------------------- hỏng
def test_LLM_nga_thi_502(tmp_path):
    def no(m, t):
        raise RuntimeError("LLM ngã")

    c, kho = _dung(tmp_path, KyThuatGia(tra=no), canh=("a",))
    assert _goi(c, kho).status_code == 502


def test_LLM_tra_RONG_thi_502(tmp_path):
    c, kho = _dung(tmp_path, KyThuatGia(tra=lambda m, t: []), canh=("a",))
    assert _goi(c, kho).status_code == 502


def test_canh_RONG_thi_tu_choi(bo):
    c, kho, _ = bo
    d = kho.doc("SE001", "H")["dong"]
    d[0]["canh"].append({"t": ""})
    c.put("/api/tap/SE001/H", json={"dong": d, "outline": ""})
    ma = _cs(kho)[-1]["id"]
    assert c.post(f"/api/tap/SE001/H/canh/{ma}/ky-thuat").status_code == 400


def test_ma_canh_la_thi_404(bo):
    c, _, _ = bo
    assert c.post("/api/tap/SE001/H/canh/khong-co/ky-thuat").status_code == 404


def test_nguoi_khac_giu_chuong_thi_409(bo):
    c, kho, _ = bo
    kho.giu("SE001", "H", "nguoi_khac")
    assert _goi(c, kho).status_code == 409


# ------------------------------------------------------- cửa gác
def test_L2_khong_chay_duoc(bo):
    _, kho, kt = bo
    xem = TestClient(tao_app(kho, ky_thuat=kt))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/ky-thuat").status_code == 403


def test_chua_bat_LLM_thi_503(bo):
    _, kho, _ = bo
    c = TestClient(tao_app(kho))
    c.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    assert c.post(f"/api/tap/SE001/H/canh/{_ma(kho)}/ky-thuat").status_code == 503


# ═════ việc 2 — ĐO 26/09: `pa` đang tả lại y nguyên thứ hệ thống sẽ chêm ═════
# Đo trên tập SE001 thật, 5 cặp cảnh–asset: mô tả asset trùng vào `pa` trung
# bình 26%, cao nhất 55% (cảnh thang máy: 28/51 từ của khối mô tả đã nằm sẵn
# trong `pa`). Hậu quả đo được: prompt 137 từ thì chủ thể thật ("a human hand
# gripping the handle") chỉ chiếm ~12 từ, còn lại tả CĂN PHÒNG — nên Seedream
# vẽ căn phòng, bàn tay thành phụ kiện. Gen lại bao nhiêu lần cũng vậy.
#
# Gốc: LLM viết `pa` KHÔNG BIẾT phần mô tả asset sẽ được chêm vào sau, nên nó tự
# tả lại bối cảnh cho đủ ý. Phải nói cho nó biết.
from autoedit.treatment import dich as _dich


def test_lenh_ky_thuat_CAM_ta_lai_asset_trong_pa():
    L = _dich._LENH_KY_THUAT
    assert "Bám mô tả asset khi tả chủ thể" not in L, (
        "chính câu này đẻ ra trùng lặp — nó bảo LLM chép lại mô tả asset")
    assert "KHÔNG tả lại" in L or "ĐỪNG tả lại" in L, (
        "lệnh phải cấm tả lại asset trong `pa`")


def test_than_goi_LLM_ghi_ro_day_la_ASSET_CUA_CANH():
    """Nhãn cũ là "SỔ TÀI SẢN" trong khi app chỉ gửi asset CỦA CẢNH ĐÓ. Nhãn sai
    thì LLM tưởng đang được đưa cả danh mục để tự chọn — đúng thứ user đã bỏ
    ("Không để LLM tự nhớ")."""
    llm = _dich.LLM.__new__(_dich.LLM)
    bat = {}

    def goi_gia(lenh, than):
        bat["than"] = than
        return {"canh": []}

    llm.goi = goi_gia
    llm.ky_thuat([{"id": "c1", "canh": "Cận bàn tay"}],
                 [{"ma": "k129", "ten": "Tàu K-129", "chu": "Soviet Golf-II"}])
    assert "ĐÃ GÁN CHO CẢNH" in bat["than"], bat["than"][:200]
    assert "Soviet Golf-II" in bat["than"], "mô tả asset vẫn phải đưa làm ngữ cảnh"
