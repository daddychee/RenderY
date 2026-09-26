"""Treatment — SỔ DÙNG CHUNG CẢ TẬP: tài sản · hồ sơ tông · phân nhân sự.

Đây là thứ tool ăn đứt quy trình chat của user (24/09). Bước 6 của họ là *"ném
ref vào Gemini, đây là tàu ngầm K-19 hãy ghi nhớ đặc điểm"* — mẹo đó chỉ sống
trong MỘT phiên chat; mở phiên mới là quên. API lại càng không có trí nhớ giữa
các lượt. Nên mô tả nhân vật / đạo cụ / bối cảnh phải nằm trong SỔ của tập, và
mỗi lần sinh prompt thì tự đính vào.

Ba thứ cùng một hình dạng (mã · tên · một đoạn chữ) nên dùng CHUNG MỘT BẢNG với
cột `loai`, không đẻ ba bảng ba bộ endpoint:
  tong      — đoạn boilerplate ghép vào cuối prompt, `canh[i].tong` trỏ tới
  nhan_vat / dao_cu / boi_canh — mô tả tiếng Anh của tài sản
  nhan_su   — cụm màu 1..6 là AI (user chốt: "cụm màu để phân nhân sự")
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho


@pytest.fixture()
def kho(tmp_path):
    k = Kho(tmp_path / "k.db")
    k.tao_tap("SE001", "K-129")
    return k


@pytest.fixture()
def c(kho):
    cl = TestClient(tao_app(kho))
    cl.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    return cl


# ──────────────────────────────── kho ───────────────────────────────────────
def test_so_moi_thi_rong(kho):
    assert kho.ds_so("SE001") == []


def test_luu_roi_doc_lai_dung_thu_tu(kho):
    kho.luu_so("SE001", [
        {"ma": "k129", "loai": "dao_cu", "ten": "Tàu K-129", "chu": "Soviet Golf-II…"},
        {"ma": "day", "loai": "boi_canh", "ten": "Đáy Thái Bình Dương", "chu": "Abyssal…"},
    ])
    ds = kho.ds_so("SE001")
    assert [x["ma"] for x in ds] == ["k129", "day"]
    assert ds[0]["loai"] == "dao_cu" and ds[0]["ten"] == "Tàu K-129"


def test_luu_so_THAY_HAN_danh_sach_cu(kho):
    """Sổ nhỏ và sửa thưa nên ghi cả danh sách: bỏ một mục là nó biến mất thật,
    không để lại rác."""
    kho.luu_so("SE001", [{"ma": "a", "loai": "dao_cu", "ten": "A", "chu": ""}])
    kho.luu_so("SE001", [{"ma": "b", "loai": "dao_cu", "ten": "B", "chu": ""}])
    assert [x["ma"] for x in kho.ds_so("SE001")] == ["b"]


def test_so_cua_tap_nay_khong_lan_sang_tap_khac(kho):
    kho.tao_tap("SE002", "khác")
    kho.luu_so("SE001", [{"ma": "a", "loai": "dao_cu", "ten": "A", "chu": ""}])
    assert kho.ds_so("SE002") == []


def test_loai_la_bi_tu_choi(kho):
    """Sổ này chảy thẳng vào prompt gửi cho nhà AI. Nhận loại bậy là mở cửa cho
    một tab hỏng đẩy rác vào prompt của cả tập."""
    with pytest.raises(ValueError):
        kho.luu_so("SE001", [{"ma": "x", "loai": "linh_tinh", "ten": "X", "chu": ""}])


def test_muc_thieu_ma_hoac_ten_bi_bo(kho):
    kho.luu_so("SE001", [
        {"ma": "", "loai": "dao_cu", "ten": "không mã", "chu": ""},
        {"ma": "ok", "loai": "dao_cu", "ten": "  ", "chu": ""},
        {"ma": "tot", "loai": "dao_cu", "ten": "Tốt", "chu": ""},
    ])
    assert [x["ma"] for x in kho.ds_so("SE001")] == ["tot"]


# ──────────────────────────────── app ───────────────────────────────────────
def test_api_so_tra_TONG_MAC_DINH_khi_chua_co_gi(c):
    """Prompt luôn phải có đoạn tông ghép vào cuối. Sổ rỗng mà trả rỗng thì
    prompt đầu tiên của tập nào cũng cụt — nên máy chủ đưa sẵn một tông mồi.

    Trước 25/09 mồi là HAI mục tên "dưới nước" / "trên cạn". User bắt đúng:
    đó là BỐI CẢNH, không phải tông. Ruột hai mục chỉ khác nhau ở câu ánh sáng
    dưới nước — mà ánh sáng là thuộc tính của bối cảnh. Mood thật thì y hệt
    nhau. Nên tông còn đúng MỘT: mood + phong cách + thiết bị."""
    ds = c.get("/api/tap/SE001/so").json()
    tong = [x for x in ds if x["loai"] == "tong"]
    assert len(tong) == 1, "một tập một mood, không chẻ theo môi trường"
    assert "underwater" not in tong[0]["chu"].lower(), (
        "ánh sáng môi trường thuộc về bối cảnh, không thuộc tông")
    assert "nước" not in tong[0]["ten"].lower() and "cạn" not in tong[0]["ten"].lower()


def test_tong_mac_dinh_co_O_THIET_BI_rieng(c):
    """User 25/09: prompt video thiếu hẳn thiết bị (ống kính / máy quay). Để
    nó thành một ô RIÊNG chứ không chôn trong đoạn mood: chôn thì người ta
    không biết là phải điền, và LLM đề xuất mood cũng không biết điền vào đâu."""
    tong = [x for x in c.get("/api/tap/SE001/so").json() if x["loai"] == "tong"]
    assert "tb" in tong[0], "mục tông phải có ô thiết bị"


def test_tap_GIU_tone_mac_dinh(c):
    """Tone gán ở cấp TẬP (user chốt 25/09), cảnh lệch mới đổi riêng. Bắt chọn
    tay từng cảnh thì không ai chọn — đo thật trên SE001: 0/83 cảnh có chọn."""
    moi = [{"ma": "toi", "loai": "tong", "ten": "Tối & bí ẩn", "chu": "DARK LOOK"},
           {"ma": "sang", "loai": "tong", "ten": "Sáng", "chu": "BRIGHT LOOK"}]
    assert c.put("/api/tap/SE001/so",
                 json={"so": moi, "tong": "sang"}).status_code == 200
    ds = c.get("/api/tap/SE001/so").json()
    assert [x["ma"] for x in ds if x.get("mac_dinh")] == ["sang"]


def test_tone_mac_dinh_song_qua_lan_luu_khac(c):
    """Lưu sổ lần sau mà không gửi kèm `tong` thì không được im lặng xoá lựa
    chọn cũ — sổ và tone mặc định là hai thứ, sửa cái này đừng dọn cái kia."""
    moi = [{"ma": "toi", "loai": "tong", "ten": "Tối", "chu": "DARK"}]
    c.put("/api/tap/SE001/so", json={"so": moi, "tong": "toi"})
    c.put("/api/tap/SE001/so", json={"so": moi})
    ds = c.get("/api/tap/SE001/so").json()
    assert [x["ma"] for x in ds if x.get("mac_dinh")] == ["toi"]


def test_api_so_ghi_roi_doc_lai(c):
    moi = [{"ma": "nuoc", "loai": "tong", "ten": "dưới nước", "chu": "X"},
           {"ma": "k129", "loai": "dao_cu", "ten": "Tàu K-129", "chu": "Soviet…"}]
    assert c.put("/api/tap/SE001/so", json={"so": moi}).status_code == 200
    ds = c.get("/api/tap/SE001/so").json()
    assert [x["ma"] for x in ds] == ["nuoc", "k129"]
    assert [x["chu"] for x in ds if x["ma"] == "nuoc"] == ["X"], "sửa tông phải ăn"


def test_L2_doc_duoc_so_nhung_khong_ghi(kho):
    xem = TestClient(tao_app(kho))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.get("/api/tap/SE001/so").status_code == 200
    assert xem.put("/api/tap/SE001/so", json={"so": []}).status_code == 403


def test_api_tu_choi_loai_la(c):
    r = c.put("/api/tap/SE001/so",
              json={"so": [{"ma": "x", "loai": "bay", "ten": "X", "chu": ""}]})
    assert r.status_code == 400
