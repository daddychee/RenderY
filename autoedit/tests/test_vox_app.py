"""Tool VOX riêng (cổng 9123) — user chốt 07/10/2026: chuỗi 2–3 ảnh nối nhau, nhập giây TỪNG ảnh,
vào qua cổng 9000 (danh tính + quyền do gateway tiêm), không đụng treatment.

Web chỉ XẾP HÀNG + đọc kết quả; dựng nặng ở thợ `autoedit.collage.tho` (tiến trình riêng).
"""

from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient

from autoedit.collage.hang_doi import HangDoi
from autoedit.collage.kho_tach import KhoTach
from autoedit.vox import app as vapp


def _png(mau=(50, 70, 90), w=320, h=180) -> bytes:
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (w, h), mau).save(b, "PNG")
    return b.getvalue()


AI = {"X-Remote-User": "an", "X-Remote-Actions": "vao,dung"}
CH = {"anh": [{"giay": 2.0, "mau": "popup", "cd": "push_in"},
              {"giay": 3.5, "mau": "chieu_sau", "cd": ""}], "noi": ["lia_len"]}


@pytest.fixture
def c(tmp_path, monkeypatch):
    monkeypatch.delenv("VOX_TRUST_PROXY", raising=False)
    return TestClient(vapp.tao_app(tmp_path / "collage"))


def _gui(c, ch=CH, anh=None, h=AI):
    anh = anh or [_png((50, 70, 90)), _png((90, 70, 50))]
    return c.post("/api/viec", headers=h, data={"cau_hinh": json.dumps(ch)},
                  files=[("anh", (f"a{i}.png", b, "image/png")) for i, b in enumerate(anh)])


# ═══════ bảng mã: cùng luật với bộ dựng ═══════════════════════════════════════
def test_bang_ma_khop_bo_dung():
    pytest.importorskip("torch")
    from autoedit.collage import mau
    assert set(vapp.CAMERA) == set(mau.MA_CAMERA) | {""}
    assert set(vapp.NOI) == set(mau.NOI) and set(vapp.MAU) == set(mau.MAU_ANH)


def test_nhan_anh_khop_bo_dung(tmp_path):
    pytest.importorskip("torch")
    from autoedit.collage import mau
    p = tmp_path / "a.png"
    p.write_bytes(_png())
    assert vapp.nhan_anh(p.read_bytes()) == mau.nhan_anh(p), "web và thợ phải nhìn CÙNG bản tách"


# ═══════ gửi việc ═════════════════════════════════════════════════════════════
def test_gui_chuoi_hai_anh_xep_hang_dung_cau_hinh(c, tmp_path):
    r = _gui(c)
    assert r.status_code == 200, r.text
    v = HangDoi(tmp_path / "collage" / "hang_doi.db").doc(r.json()["id"])
    assert v["nguoi"] == "an" and v["trang_thai"] == "cho" and v["giay"] == 5.5
    ch = json.loads(v["chuoi"])
    assert [x["giay"] for x in ch["anh"]] == [2.0, 3.5] and ch["noi"] == ["lia_len"]
    assert [x["mau"] for x in ch["anh"]] == ["popup", "chieu_sau"]
    from pathlib import Path
    assert all(Path(x["anh"]).read_bytes()[:4] == b"\x89PNG" for x in ch["anh"]), "ảnh chép vào thư mục việc"


@pytest.mark.parametrize("sai", [
    {"anh": [{"giay": 2, "mau": "popup", "cd": ""}] * 2, "noi": []},               # thiếu cú nối
    {"anh": [{"giay": 0, "mau": "popup", "cd": ""}] * 2, "noi": ["cat"]},          # 0 giây
    {"anh": [{"giay": 2, "mau": "la", "cd": ""}] * 2, "noi": ["cat"]},             # mẫu lạ
    {"anh": [{"giay": 2, "mau": "popup", "cd": "bay"}] * 2, "noi": ["cat"]},       # camera lạ
    {"anh": [{"giay": 2, "mau": "popup", "cd": ""}] * 2, "noi": ["xoay"]},         # nối lạ
])
def test_cau_hinh_sai_bi_chan(c, sai):
    assert _gui(c, sai).status_code == 400


def test_qua_ba_anh_hoac_khong_phai_anh_bi_chan(c):
    bon = {"anh": [{"giay": 1, "mau": "chieu_sau", "cd": ""}] * 4, "noi": ["cat"] * 3}
    assert _gui(c, bon, [_png()] * 4).status_code == 400
    assert _gui(c, anh=[b"khong phai anh", _png()]).status_code == 400
    lech = {"anh": CH["anh"][:1], "noi": []}
    assert _gui(c, lech, [_png(), _png()]).status_code == 400, "số ảnh phải khớp cấu hình"


def test_mot_anh_van_dung_duoc(c):
    assert _gui(c, {"anh": CH["anh"][:1], "noi": []}, [_png()]).status_code == 200


def test_khong_danh_tinh_hoac_khong_co_quyen_dung_thi_chan(c):
    assert _gui(c, h={}).status_code == 401
    assert _gui(c, h={"X-Remote-User": "an", "X-Remote-Actions": "vao"}).status_code == 403


def test_bat_co_tin_proxy_thi_khong_tin_header_tu_may_ngoai(tmp_path, monkeypatch):
    monkeypatch.setenv("VOX_TRUST_PROXY", "1")
    c = TestClient(vapp.tao_app(tmp_path / "collage"), client=("192.168.1.9", 5000))
    assert _gui(c).status_code == 401


# ═══════ xem việc của mình ════════════════════════════════════════════════════
def test_danh_sach_chi_viec_cua_minh_kem_thu_tu_va_co(c, tmp_path):
    ma = _gui(c).json()["id"]
    _gui(c, h={"X-Remote-User": "binh", "X-Remote-Actions": "vao,dung"})
    import numpy as np

    from autoedit.collage import tach
    ch = json.loads(HangDoi(tmp_path / "collage" / "hang_doi.db").doc(ma)["chuoi"])
    m = np.zeros((180, 320), bool)
    KhoTach(tmp_path / "collage").ghi(ch["anh"][0]["nhan"], "x", tach.KetQuaTach(
        [(m, 5.0)], np.zeros((180, 320, 3), np.float32), np.zeros((180, 320), np.float32), ["mep_yeu"]),
        np.zeros((180, 320, 3), np.float32))
    ds = c.get("/api/viec", headers=AI).json()["viec"]
    assert [v["id"] for v in ds] == [ma]
    v = ds[0]
    assert v["trang_thai"] == "cho" and v["thu_tu"] == 1 and v["giay"] == 5.5
    assert v["anh"][0]["co"] == ["mep_yeu"] and v["anh"][1]["co"] == [], "▲ theo từng ảnh Pop-up"


def test_xong_thi_tai_video_va_anh(c, tmp_path):
    ma = _gui(c).json()["id"]
    hd = HangDoi(tmp_path / "collage" / "hang_doi.db")
    assert c.get(f"/api/viec/{ma}/video", headers=AI).status_code == 409, "chưa xong thì chưa có video"
    hd.lay_tiep()
    ra = tmp_path / "ra.mp4"
    ra.write_bytes(b"mp4-gia")
    hd.xong(ma, str(ra))
    r = c.get(f"/api/viec/{ma}/video", headers=AI)
    assert r.status_code == 200 and r.content == b"mp4-gia"
    assert c.get(f"/api/viec/{ma}/anh/1", headers=AI).content[:4] == b"\x89PNG"
    assert c.get(f"/api/viec/{ma}/anh/7", headers=AI).status_code == 404


# ═══════ tách lại ảnh Pop-up bằng điểm bấm ════════════════════════════════════
def test_tach_lai_tao_viec_moi_mang_diem_dung_anh(c, tmp_path):
    ma = _gui(c).json()["id"]
    d = [{"x": 0.5, "y": 0.4, "dau": 1}, {"x": 0.1, "y": 0.9, "dau": 0}]
    r = c.post(f"/api/viec/{ma}/tach/0", headers=AI, json={"diem": d})
    assert r.status_code == 200, r.text
    hd = HangDoi(tmp_path / "collage" / "hang_doi.db")
    cu, moi = json.loads(hd.doc(ma)["chuoi"]), json.loads(hd.doc(r.json()["id"])["chuoi"])
    assert moi["anh"][0]["diem"] == d and "diem" not in moi["anh"][1]
    assert [x["nhan"] for x in moi["anh"]] == [x["nhan"] for x in cu["anh"]] and moi["noi"] == cu["noi"]
    assert all(r.json()["id"] in x["anh"] for x in moi["anh"]), "ảnh chép sang thư mục việc MỚI — video cũ không bị ghi đè"


def test_tach_lai_chan_sai(c):
    ma = _gui(c).json()["id"]
    ok = [{"x": 0.5, "y": 0.5, "dau": 1}]
    assert c.post(f"/api/viec/{ma}/tach/1", headers=AI, json={"diem": ok}).status_code == 400, "ảnh Chiều sâu"
    assert c.post(f"/api/viec/{ma}/tach/0", headers=AI, json={"diem": [{"x": 2, "y": 0.5, "dau": 1}]}).status_code == 400
    assert c.post(f"/api/viec/{ma}/tach/0", headers=AI, json={"diem": [{"x": 0.5, "y": 0.5, "dau": 0}]}).status_code == 400
    khac = {"X-Remote-User": "binh", "X-Remote-Actions": "vao,dung"}
    assert c.post(f"/api/viec/{ma}/tach/0", headers=khac, json={"diem": ok}).status_code == 403


# ═══════ sức khoẻ: thợ không chạy thì KHÔNG báo xanh ══════════════════════════
def test_suc_khoe_bao_tho_chua_chay(c, tmp_path):
    j = c.get("/api/suc-khoe").json()
    tho = [m for m in j["mo_dun"] if m["ten"] == "tho"][0]
    assert tho["trang_thai"] == "canh_bao" and j["trang_thai"] == "canh_bao"
    (tmp_path / "collage" / "tho.song").write_text("1")
    j = c.get("/api/suc-khoe").json()
    assert j["trang_thai"] == "ok"


def test_tho_ghi_dau_song_moi_vong(tmp_path):
    from autoedit.collage import tho
    tho.danh_dau_song(tmp_path)
    assert (tmp_path / "tho.song").exists()


def test_trang_chu_va_api_toi(c):
    r = c.get("/")
    assert r.status_code == 200 and "VOX" in r.text and r.headers["cache-control"] == "no-store"
    assert c.get("/api/toi", headers=AI).json() == {"nguoi": "an", "dung_duoc": True}


def test_tho_giu_cong_de_start_all_biet_da_chay_va_khong_bat_trung():
    """start-all.ps1 nhận biết dịch vụ đã chạy bằng CỔNG đang nghe; thợ không có cổng thì mỗi lần
    chạy start-all lại bật thêm một thợ. Thợ giữ cổng loopback: lần bật thứ hai tự lùi."""
    import socket

    from autoedit.collage import tho
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        cong = s.getsockname()[1]
    giu = tho.giu_cong(cong)
    assert giu is not None
    try:
        assert tho.giu_cong(cong) is None, "đã có thợ giữ cổng thì thợ thứ hai không được chạy"
        with socket.create_connection(("127.0.0.1", cong), timeout=2):
            pass                                              # Test-Cong của start-all nối được
    finally:
        giu.close()


def test_khung_luu_theo_viec_va_mac_dinh_16_9(c, tmp_path):
    hd = HangDoi(tmp_path / "collage" / "hang_doi.db")
    ma = _gui(c, dict(CH, khung="4:5")).json()["id"]
    assert json.loads(hd.doc(ma)["chuoi"])["khung"] == "4:5"
    ma = _gui(c).json()["id"]
    assert json.loads(hd.doc(ma)["chuoi"])["khung"] == "16:9"
    assert _gui(c, dict(CH, khung="21:9")).status_code == 400
    assert c.get("/api/bang").json()["khung"] == {"16:9": "Ngang 16:9", "4:5": "Dọc 4:5", "9:16": "Đứng 9:16"}
    assert c.get("/api/viec", headers=AI).json()["viec"][0]["khung"] == "16:9"


def test_bang_khung_khop_bo_dung():
    pytest.importorskip("torch")
    from autoedit.collage import mau
    assert set(vapp.KHUNG) == set(mau.KHUNG)
