"""Treatment — ẢNH REF của tài sản: tool giữ file, không giữ cái link.

User chốt 24/09: *"ông call đủ các asset, tôi sẽ upload ref"*. Chọn giữ FILE
chứ không giữ link vì hai lẽ: link Drive chết là mất cả sổ, và đợt 2 gọi API
thì phải có BYTES trong tay mới đính ref vào lượt gọi được.

Mỗi tài sản mang hai đoạn chữ khác nhau — trước gộp làm một là sai:
  `pr`  — prompt TẠO ref ("toàn thân, 3 góc, nền trắng, photorealistic, 19xx"),
          dùng ĐÚNG MỘT LẦN để đẻ ra ref
  `chu` — mô tả nhận dạng ngắn, đính vào MỌI prompt cảnh dùng tài sản đó
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

PNG = (b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)


@pytest.fixture()
def kho(tmp_path):
    k = Kho(tmp_path / "kho" / "k.db")
    k.tao_tap("SE001", "K-129")
    return k


@pytest.fixture()
def c(kho):
    cl = TestClient(tao_app(kho))
    cl.headers.update({"X-Remote-User": "thu", "X-Remote-Actions": "sua"})
    cl.put("/api/tap/SE001/so", json={"so": [
        {"ma": "k129", "loai": "dao_cu", "ten": "Tàu K-129",
         "chu": "Soviet Golf-II, weathered black hull",
         "pr": "Full body, 3 angles, white background, photorealistic, 1968"}]})
    return cl


# ------------------------------------------------- sổ giữ hai đoạn chữ
def test_so_giu_ca_prompt_tao_ref_va_mo_ta(c):
    x = [y for y in c.get("/api/tap/SE001/so").json() if y["ma"] == "k129"][0]
    assert x["chu"].startswith("Soviet Golf-II")
    assert "3 angles" in x["pr"], "prompt tạo ref phải giữ riêng, không gộp vào mô tả"


# ------------------------------------------------- đường dẫn file
def test_duong_ref_nam_trong_thu_muc_kho(kho):
    d = kho.duong_ref("SE001", "k129", ".png")
    assert kho.duong.parent in d.parents


@pytest.mark.parametrize("ma", ["../../thoat", "a/b", "a\\b", "..", ""])
def test_ma_bay_khong_thoat_duoc_ra_ngoai(kho, ma):
    """`ma` đi thẳng vào tên file. Không chặn là ghi đè được file bất kỳ trên ổ."""
    with pytest.raises(ValueError):
        kho.duong_ref("SE001", ma, ".png")


# ------------------------------------------------- tải lên / tải về
def test_tai_ref_len_roi_lay_ve_dung_bytes(c):
    r = c.post("/api/tap/SE001/so/k129/ref",
               files={"tep": ("ref.png", PNG, "image/png")})
    assert r.status_code == 200, r.text
    g = c.get("/api/tap/SE001/so/k129/ref")
    assert g.status_code == 200 and g.content == PNG


def test_so_ghi_nho_la_da_co_ref(c):
    c.post("/api/tap/SE001/so/k129/ref", files={"tep": ("ref.png", PNG, "image/png")})
    x = [y for y in c.get("/api/tap/SE001/so").json() if y["ma"] == "k129"][0]
    assert x["ref"], "sổ phải biết tài sản nào đã có ref — để đếm việc còn dở"


def test_chua_co_ref_thi_404(c):
    assert c.get("/api/tap/SE001/so/k129/ref").status_code == 404


def test_duoi_tep_la_bi_tu_choi(c):
    r = c.post("/api/tap/SE001/so/k129/ref",
               files={"tep": ("x.exe", b"MZ" + b"\x00" * 10, "application/octet-stream")})
    assert r.status_code == 400


def test_tep_qua_to_bi_tu_choi(c):
    to = b"\x89PNG\r\n\x1a\n" + b"\x00" * (Kho.REF_TOI_DA + 1)
    r = c.post("/api/tap/SE001/so/k129/ref",
               files={"tep": ("to.png", to, "image/png")})
    assert r.status_code == 413


def test_tai_lai_thi_DE_len_ban_cu(c):
    c.post("/api/tap/SE001/so/k129/ref", files={"tep": ("a.png", PNG, "image/png")})
    moi = b"\x89PNG\r\n\x1a\n" + b"\xff" * 32
    c.post("/api/tap/SE001/so/k129/ref", files={"tep": ("b.png", moi, "image/png")})
    assert c.get("/api/tap/SE001/so/k129/ref").content == moi


def test_doi_duoi_tep_thi_khong_de_lai_ban_cu(c):
    """Tải .png rồi tải .jpg cùng mã: để lại cả hai thì lần sau lấy nhầm bản cũ."""
    c.post("/api/tap/SE001/so/k129/ref", files={"tep": ("a.png", PNG, "image/png")})
    jpg = b"\xff\xd8\xff" + b"\x00" * 32
    c.post("/api/tap/SE001/so/k129/ref", files={"tep": ("b.jpg", jpg, "image/jpeg")})
    assert c.get("/api/tap/SE001/so/k129/ref").content == jpg


def test_L2_khong_tai_len_duoc(kho):
    kho.luu_so("SE001", [{"ma": "k129", "loai": "dao_cu", "ten": "Tàu", "chu": ""}])
    xem = TestClient(tao_app(kho))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    r = xem.post("/api/tap/SE001/so/k129/ref",
                 files={"tep": ("a.png", PNG, "image/png")})
    assert r.status_code == 403


def test_L2_van_XEM_duoc_ref(c, kho):
    c.post("/api/tap/SE001/so/k129/ref", files={"tep": ("a.png", PNG, "image/png")})
    xem = TestClient(tao_app(kho))
    xem.headers.update({"X-Remote-User": "nhanvien"})
    assert xem.get("/api/tap/SE001/so/k129/ref").status_code == 200


def test_xoa_ref(c):
    c.post("/api/tap/SE001/so/k129/ref", files={"tep": ("a.png", PNG, "image/png")})
    assert c.delete("/api/tap/SE001/so/k129/ref").status_code == 200
    assert c.get("/api/tap/SE001/so/k129/ref").status_code == 404


# ------------------------------------------------- chỉ nhận ẢNH
def test_asset_CHI_LA_ANH(kho):
    """User chốt 24/09: "asset chỉ nên là ảnh". Ref là bản mặt của nhân vật/đạo
    cụ để giữ nhất quán — clip không phục vụ việc đó, mà mở cửa cho video nghĩa
    là kho phình bằng file nặng và đợt 2 phải xử hai kiểu đầu vào."""
    assert set(kho.DUOI_REF) == {".png", ".jpg", ".jpeg", ".webp"}


@pytest.mark.parametrize("ten", ["clip.mp4", "clip.webm", "clip.mov"])
def test_video_bi_tu_choi(c, ten):
    r = c.post("/api/tap/SE001/so/k129/ref",
               files={"tep": (ten, b"x" * 64, "video/mp4")})
    assert r.status_code == 400


def test_tran_dung_luong_hop_voi_ANH(kho):
    """60MB là cỡ đặt cho clip. Một bản ref ảnh 4K nặng vài MB."""
    assert kho.REF_TOI_DA == 25 * 1024 * 1024
