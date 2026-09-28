"""Treatment — NHIỀU NGƯỜI cùng làm một chương (lỗi ngày đầu vận hành 28/09).

Đo trên log production 28/09: hai máy (.14 và .20) cùng làm chương C2 và chặn
nhau 28 lần — `duyet` 15, `giu` 10, `anh`/`video`/`video-kiem` mỗi thứ 1. Một
lượt `video` đã gửi Seedvis (đã trả tiền) rồi mới bị 409 lúc lưu mã task → clip
mất dấu. Đo thêm trên bản sao: sửa một cú TRONG LÚC đang vẽ ảnh cú khác thì vẽ
xong là bản sửa biến mất (máy chủ ghi lại cả chương theo bản đọc TRƯỚC khi vẽ).

Luật mới:
  - Việc MÁY làm (ảnh xong, duyệt, gửi video, video xong, create prompt) đọc bản
    MỚI NHẤT rồi vá ĐÚNG MỘT CẢNH, không cần khoá chương.
  - Sửa trong hộp cảnh ghi RIÊNG từng cảnh (PATCH), mang số bản `v`.
  - Tự lưu cả chương: trường máy luôn theo máy chủ; cảnh người khác vừa sửa ở
    hộp cảnh (máy chủ `v` lớn hơn) thì giữ bản của họ và báo lại.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


class VeAnhGia:
    """`giua` chạy GIỮA lượt vẽ — giả một người khác sửa kho lúc ảnh đang vẽ."""

    def __init__(self):
        self.giua = None

    def gen_anh(self, prompt, dich, ref=None):
        if self.giua:
            self.giua()
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(PNG)
        return dich


class VeVideoGia:
    def bat_dau(self, prompt, anh, giay, am):
        return "task-1"

    def trang_thai(self, tid):
        return {"status": "succeeded", "video_url": "https://vi-du/x.mp4"}

    def tai_ve(self, url, dich):
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(MP4)
        return dich


class KyThuatGia:
    def __init__(self):
        self.giua = None

    def ky_thuat(self, muc, tai_san):
        if self.giua:
            self.giua()
        return [{"id": m["id"], "lap": "LAP", "pa": "PA MOI", "pv": "PV MOI",
                 "sfx": "SFX"} for m in muc]

    def breakdown(self, voice, y, giay, tai_san):
        if self.giua:
            self.giua()
        return [{"t": "VIET LAI " + t, "co": "CU", "goc": "eye", "cd": "static"} for t in y]

    def bo_tro(self, voice, canh, giay, toi_da, tai_san):
        return []


@pytest.fixture
def bo(tmp_path):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("SE001", "K-129")
    va, kt = VeAnhGia(), KyThuatGia()
    app = tao_app(kho, ve_anh=va, ve_video=VeVideoGia(), ky_thuat=kt)
    an = TestClient(app)
    an.headers.update({"X-Remote-User": "an", "X-Remote-Actions": "sua"})
    binh = TestClient(app)
    binh.headers.update({"X-Remote-User": "binh", "X-Remote-Actions": "sua"})
    an.post("/api/tap/SE001/chuong", json={"ma": "C2"})
    an.put("/api/tap/SE001/C2", json={"outline": "", "dong": [
        {"en": "Voice one two three four five six seven eight nine ten eleven twelve.",
         "canh": [{"t": "cu mot", "pa": "PA1", "pv": "PV1"},
                  {"t": "cu hai", "pa": "PA2", "pv": "PV2"}]}]})
    kho.nha("SE001", "C2", "an")
    return an, binh, kho, va, kt


def _cs(kho):
    return kho.doc("SE001", "C2")["dong"][0]["canh"]


def _id(kho, j):
    return _cs(kho)[j]["id"]


def _sua_cu_hai(kho, t="cu hai DA SUA"):
    """Người khác sửa cú 2 thẳng vào kho (như một lượt tự lưu)."""
    d = kho.doc("SE001", "C2")
    d["dong"][0]["canh"][1]["t"] = t
    kho.luu("SE001", "C2", d["dong"], d["outline"], "binh")
    kho.nha("SE001", "C2", "binh")


# ──────────────────────────── việc máy làm: không bị khoá chương chặn
def test_gen_anh_khi_nguoi_khac_giu_chuong(bo):
    an, _, kho, _, _ = bo
    ma = _id(kho, 0)
    kho.giu("SE001", "C2", "binh")
    assert an.post(f"/api/tap/SE001/C2/canh/{ma}/anh").status_code == 200
    assert kho.ai_giu("SE001", "C2") == "binh"      # khoá của người kia còn nguyên


def test_anh_moi_thi_bo_dau_duyet_du_nguoi_khac_giu(bo):
    """Trước: ảnh đã ghi xuống đĩa rồi mới 409 — dấu duyệt CŨ nằm trên ảnh MỚI
    chưa ai xem, và video có thể dựng từ tấm ảnh đó."""
    an, _, kho, _, _ = bo
    ma = _id(kho, 0)
    an.post(f"/api/tap/SE001/C2/canh/{ma}/anh")
    an.post(f"/api/tap/SE001/C2/canh/{ma}/duyet")
    kho.giu("SE001", "C2", "binh")
    an.post(f"/api/tap/SE001/C2/canh/{ma}/anh")
    assert not _cs(kho)[0].get("duyet")


def test_duyet_khi_nguoi_khac_giu_chuong(bo):
    an, _, kho, _, _ = bo
    ma = _id(kho, 0)
    an.post(f"/api/tap/SE001/C2/canh/{ma}/anh")
    kho.giu("SE001", "C2", "binh")
    assert an.post(f"/api/tap/SE001/C2/canh/{ma}/duyet").status_code == 200
    assert _cs(kho)[0]["duyet"] == "1"


def test_gen_video_khi_nguoi_khac_giu_KHONG_mat_ma_task(bo):
    """Đo 28/09: video đã gửi Seedvis rồi mới 409 lúc lưu mã → clip trả tiền mất dấu."""
    an, _, kho, _, _ = bo
    ma = _id(kho, 0)
    an.post(f"/api/tap/SE001/C2/canh/{ma}/anh")
    an.post(f"/api/tap/SE001/C2/canh/{ma}/duyet")
    kho.giu("SE001", "C2", "binh")
    assert an.post(f"/api/tap/SE001/C2/canh/{ma}/video").status_code == 200
    assert _cs(kho)[0]["vid"] == "task-1"
    r = an.post(f"/api/tap/SE001/C2/canh/{ma}/video-kiem")
    assert r.status_code == 200 and r.json()["trang_thai"] == "xong"
    assert not _cs(kho)[0].get("vid")


def test_create_prompt_khi_nguoi_khac_giu_chuong(bo):
    an, _, kho, _, _ = bo
    ma = _id(kho, 0)
    kho.giu("SE001", "C2", "binh")
    assert an.post(f"/api/tap/SE001/C2/canh/{ma}/ky-thuat").status_code == 200
    assert _cs(kho)[0]["pa"] == "PA MOI"


# ──────────────────────────── không đè bản sửa của người khác
def test_sua_cu_khac_TRONG_LUC_ve_anh_khong_mat(bo):
    """Đo trên bản sao 28/09: vẽ xong là bản sửa cú 2 biến mất, máy chủ vẫn 200."""
    an, _, kho, va, _ = bo
    va.giua = lambda: _sua_cu_hai(kho)
    an.post(f"/api/tap/SE001/C2/canh/{_id(kho, 0)}/anh")
    assert _cs(kho)[1]["t"] == "cu hai DA SUA"


def test_sua_cu_khac_TRONG_LUC_create_prompt_khong_mat(bo):
    an, _, kho, _, kt = bo
    kt.giua = lambda: _sua_cu_hai(kho)
    an.post(f"/api/tap/SE001/C2/canh/{_id(kho, 0)}/ky-thuat")
    assert _cs(kho)[1]["t"] == "cu hai DA SUA"
    assert _cs(kho)[0]["pa"] == "PA MOI"


def test_sua_TRONG_LUC_breakdown_khong_mat_truong_khac(bo):
    """Breakdown viết lại `t`/khung; asset người ta vừa gán trong lúc chờ LLM
    phải còn."""
    an, _, kho, _, kt = bo

    def gan_asset():
        d = kho.doc("SE001", "C2")
        d["dong"][0]["canh"][1]["ts"] = ["k129"]
        kho.luu("SE001", "C2", d["dong"], d["outline"], "binh")
        kho.nha("SE001", "C2", "binh")

    kt.giua = gan_asset
    assert an.post("/api/tap/SE001/C2/dong/0/breakdown").status_code == 200
    cs = _cs(kho)
    assert cs[1]["ts"] == ["k129"]
    assert cs[1]["t"] == "VIET LAI cu hai"


def test_breakdown_ma_phan_canh_vua_them_cu_thi_409_khong_de(bo):
    an, _, kho, _, kt = bo

    def them_cu():
        d = kho.doc("SE001", "C2")
        d["dong"][0]["canh"].append({"t": "cu ba moi them"})
        kho.luu("SE001", "C2", d["dong"], d["outline"], "binh")
        kho.nha("SE001", "C2", "binh")

    kt.giua = them_cu
    assert an.post("/api/tap/SE001/C2/dong/0/breakdown").status_code == 409
    assert [c["t"] for c in _cs(kho)] == ["cu mot", "cu hai", "cu ba moi them"]


def test_tu_luu_ban_cu_khong_xoa_ket_qua_may(bo):
    """Trang của An nạp chương TRƯỚC khi Bình duyệt/gửi video/create prompt.
    An gõ ở màn Kịch bản -> tự lưu cả chương bản cũ -> không được xoá dấu
    duyệt, mã task video (clip đã trả tiền) và prompt máy vừa viết."""
    an, binh, kho, _, _ = bo
    cu = an.get("/api/tap/SE001/C2").json()
    ma = _id(kho, 0)
    binh.post(f"/api/tap/SE001/C2/canh/{ma}/anh")
    binh.post(f"/api/tap/SE001/C2/canh/{ma}/duyet")
    binh.post(f"/api/tap/SE001/C2/canh/{ma}/ky-thuat")
    binh.post(f"/api/tap/SE001/C2/canh/{ma}/video")
    cu["dong"][0]["en"] = "An sua voice."
    assert an.put("/api/tap/SE001/C2", json={"dong": cu["dong"], "outline": ""}).status_code == 200
    c0 = _cs(kho)[0]
    assert (c0.get("duyet"), c0.get("vid"), c0.get("pa")) == ("1", "task-1", "PA MOI")
    assert kho.doc("SE001", "C2")["dong"][0]["en"] == "An sua voice."


# ──────────────────────────── hộp cảnh ghi riêng từng cảnh
def test_patch_mot_canh_khi_nguoi_khac_giu_chuong(bo):
    an, _, kho, _, _ = bo
    ma = _id(kho, 1)
    kho.giu("SE001", "C2", "binh")
    r = an.patch(f"/api/tap/SE001/C2/canh/{ma}", json={"truong": {"t": "an sua o hop", "co": "CU"}})
    assert r.status_code == 200
    c1 = _cs(kho)[1]
    assert (c1["t"], c1["co"]) == ("an sua o hop", "CU")
    assert int(r.json()["v"]) == int(c1["v"]) >= 1
    assert _cs(kho)[0]["t"] == "cu mot"


def test_patch_rong_la_xoa_khoa(bo):
    an, _, kho, _, _ = bo
    ma = _id(kho, 0)
    an.patch(f"/api/tap/SE001/C2/canh/{ma}", json={"truong": {"pat": "tay"}})
    assert _cs(kho)[0]["pat"] == "tay"
    an.patch(f"/api/tap/SE001/C2/canh/{ma}", json={"truong": {"pat": ""}})
    assert "pat" not in _cs(kho)[0]


def test_patch_khong_cho_sua_truong_may(bo):
    """`duyet`/`vid`/`pa` chỉ máy chủ viết — trang tự đặt `duyet` là lách cổng tiền video."""
    an, _, kho, _, _ = bo
    ma = _id(kho, 0)
    r = an.patch(f"/api/tap/SE001/C2/canh/{ma}", json={"truong": {"duyet": "1"}})
    assert r.status_code == 400
    assert not _cs(kho)[0].get("duyet")


def test_patch_canh_khong_co_thi_404(bo):
    an, *_ = bo
    r = an.patch("/api/tap/SE001/C2/canh/ckhongco", json={"truong": {"t": "x"}})
    assert r.status_code == 404 and "ckhongco" in r.json()["detail"]


def test_patch_nguoi_chi_xem_bi_chan(bo):
    _, _, kho, _, _ = bo
    xem = TestClient(tao_app(kho))
    xem.headers.update({"X-Remote-User": "nv"})
    r = xem.patch(f"/api/tap/SE001/C2/canh/{_id(kho, 0)}", json={"truong": {"t": "x"}})
    assert r.status_code == 403


def test_tu_luu_ban_cu_giu_ban_hop_canh_cua_nguoi_khac_va_bao_lai(bo):
    """An giữ chương, gõ ở màn Kịch bản với bản nạp từ trước. Bình sửa cú 2 ở
    hộp cảnh. An tự lưu -> cú 2 giữ bản của Bình, và An được báo mã cú đó để
    trang nạp lại."""
    an, binh, kho, _, _ = bo
    cu = an.get("/api/tap/SE001/C2").json()
    an.post("/api/tap/SE001/C2/giu")
    ma = _id(kho, 1)
    binh.patch(f"/api/tap/SE001/C2/canh/{ma}", json={"truong": {"t": "binh sua"}})
    cu["dong"][0]["canh"][0]["t"] = "an sua cu mot"
    r = an.put("/api/tap/SE001/C2", json={"dong": cu["dong"], "outline": ""})
    assert r.status_code == 200
    assert [c["t"] for c in _cs(kho)] == ["an sua cu mot", "binh sua"]
    assert r.json()["giu_ban_moi"] == [ma]


def test_tu_luu_sau_patch_cua_chinh_minh_khong_bao_gia(bo):
    """Cùng một trang: PATCH xong rồi tự lưu bản trong tay (đã mang nội dung
    vừa PATCH) — không phải xung đột, không được báo."""
    an, _, kho, _, _ = bo
    d = an.get("/api/tap/SE001/C2").json()["dong"]
    ma = d[0]["canh"][1]["id"]
    an.patch(f"/api/tap/SE001/C2/canh/{ma}", json={"truong": {"t": "an sua o hop"}})
    d[0]["canh"][1]["t"] = "an sua o hop"
    r = an.put("/api/tap/SE001/C2", json={"dong": d, "outline": ""})
    assert r.json()["giu_ban_moi"] == []


# ──────────────────────────── tab chạy JS CŨ (bẫy đắt nhất, 24/09)
def test_tab_JS_cu_doi_co_canh_qua_tu_luu_van_luu_duoc(bo):
    """Tab mở trước lúc deploy vẫn gửi mọi sửa ở hộp cảnh qua tự lưu cả
    chương, KHÔNG có cờ `hop_rieng`. Không được nuốt im lặng bản sửa đó —
    nhưng vẫn giữ trường máy (duyệt, mã video, prompt máy)."""
    an, binh, kho, _, _ = bo
    cu = an.get("/api/tap/SE001/C2").json()
    ma = _id(kho, 0)
    binh.post(f"/api/tap/SE001/C2/canh/{ma}/anh")
    binh.post(f"/api/tap/SE001/C2/canh/{ma}/duyet")
    cu["dong"][0]["canh"][0]["co"] = "ECU"
    cu["dong"][0]["canh"][0]["ts"] = ["k129"]
    an.put("/api/tap/SE001/C2", json={"dong": cu["dong"], "outline": ""})
    c0 = _cs(kho)[0]
    assert (c0.get("co"), c0.get("ts"), c0.get("duyet")) == ("ECU", ["k129"], "1")


def test_trang_moi_tu_luu_ban_cu_khong_de_truong_hop_canh_nguoi_khac(bo):
    """Trang MỚI (có cờ `hop_rieng`) ghi hộp cảnh bằng PATCH, nên tự lưu cả
    chương chỉ mang được chữ `t` — cỡ cảnh Bình vừa đổi không bị bản cũ đè."""
    an, binh, kho, _, _ = bo
    cu = an.get("/api/tap/SE001/C2").json()
    ma = _id(kho, 1)
    binh.patch(f"/api/tap/SE001/C2/canh/{ma}", json={"truong": {"co": "ECU", "tong": "toi"}})
    cu["dong"][0]["en"] = "An sua voice."
    an.put("/api/tap/SE001/C2", json={"dong": cu["dong"], "outline": "", "hop_rieng": 1})
    c1 = _cs(kho)[1]
    assert (c1.get("co"), c1.get("tong")) == ("ECU", "toi")
