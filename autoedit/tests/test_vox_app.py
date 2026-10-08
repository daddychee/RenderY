"""Tool VOX riêng (cổng 9123). User chốt 07/10/2026:
- chuỗi 1–3 ảnh nối nhau, nhập giây TỪNG ảnh, chọn khung hình;
- "Mẫu" đổi thành STYLE: Collage art / Black Grid / Non-Grid; BỎ ô camera (máy tự lên nhịp + camera);
- bước LỚP: máy đề xuất khung, người kéo / xoá khung, xem phần máy cắt TRƯỚC khi dựng.
Danh tính + quyền 'dung' do gateway 9000 tiêm. Web chỉ xếp hàng; dựng ở thợ `autoedit.collage.tho`.
"""

from __future__ import annotations

import io
import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from autoedit.collage.hang_doi import HangDoi
from autoedit.vox import app as vapp


def _png(mau=(50, 70, 90), w=320, h=180) -> bytes:
    from PIL import Image
    b = io.BytesIO()
    Image.new("RGB", (w, h), mau).save(b, "PNG")
    return b.getvalue()


AI = {"X-Remote-User": "an", "X-Remote-Actions": "vao,dung"}
CH = {"anh": [{"giay": 2.0, "khung_lop": [[0.1, 0.2, 0.5, 0.9]]}, {"giay": 3.5, "khung_lop": []}],
      "khung": "16:9", "style": "black_grid"}


class _MayLopGia:
    """Thay SAM/độ sâu: đề xuất 1 khung cố định; 'cắt' = đúng hình chữ nhật của khung."""

    def __init__(self):
        self.goi = []

    def de_xuat(self, rgb):
        self.goi.append(("de_xuat", rgb.shape))
        return [[0.25, 0.25, 0.75, 0.75]]

    def cat(self, rgb, khung_lop):
        self.goi.append(("cat", rgb.shape, [list(k) for k in khung_lop]))
        h, w = rgb.shape[:2]
        ra = []
        for x0, y0, x1, y1 in khung_lop:
            m = np.zeros((h, w), bool)
            m[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = True
            ra.append(m)
        return ra


@pytest.fixture
def may():
    return _MayLopGia()


@pytest.fixture
def c(tmp_path, monkeypatch, may):
    monkeypatch.delenv("VOX_TRUST_PROXY", raising=False)
    return TestClient(vapp.tao_app(tmp_path / "collage", may_lop=may))


def _gui(c, ch=CH, anh=None, h=AI):
    anh = anh or [_png((50, 70, 90)), _png((90, 70, 50))]
    return c.post("/api/viec", headers=h, data={"cau_hinh": json.dumps(ch)},
                  files=[("anh", (f"a{i}.png", b, "image/png")) for i, b in enumerate(anh)])


# ═══════ bảng: cùng luật với bộ dựng ═════════════════════════════════════════
def test_bang_style_khung_khop_bo_dung(c):
    pytest.importorskip("torch")
    from autoedit.collage import mau
    b = c.get("/api/bang").json()
    assert b["style"] == {"collage": "Collage art", "black_grid": "Black Grid", "non_grid": "Non-Grid"}
    assert set(b["style"]) == set(mau.STYLE) and set(vapp.KHUNG) == set(mau.KHUNG)
    assert "camera" not in b and "mau" not in b, "user chốt 07/10: bỏ ô camera, Mẫu đổi thành Style"


# ═══════ gửi việc ═════════════════════════════════════════════════════════════
def test_gui_chuoi_luu_style_khung_va_lop(c, tmp_path):
    r = _gui(c)
    assert r.status_code == 200, r.text
    v = HangDoi(tmp_path / "collage" / "hang_doi.db").doc(r.json()["id"])
    assert v["nguoi"] == "an" and v["trang_thai"] == "cho" and v["giay"] == 5.5
    ch = json.loads(v["chuoi"])
    assert ch["style"] == "black_grid" and ch["khung"] == "16:9"
    assert [x["giay"] for x in ch["anh"]] == [2.0, 3.5]
    assert ch["anh"][0]["khung_lop"] == [[0.1, 0.2, 0.5, 0.9]] and ch["anh"][1]["khung_lop"] == []
    from pathlib import Path
    assert all(Path(x["anh"]).read_bytes()[:4] == b"\x89PNG" for x in ch["anh"]), "ảnh chép vào thư mục việc"


@pytest.mark.parametrize("sai", [
    dict(CH, style="la"),                                                        # style lạ
    dict(CH, khung="21:9"),                                                      # khung lạ
    dict(CH, anh=[{"giay": 0, "khung_lop": []}, CH["anh"][1]]),                  # 0 giây
    dict(CH, anh=[{"giay": 2, "khung_lop": [[0.5, 0.2, 0.4, 0.9]]}, CH["anh"][1]]),   # khung ngược
    dict(CH, anh=[{"giay": 2, "khung_lop": [[-0.2, 0, 0.5, 1]]}, CH["anh"][1]]),      # ra ngoài ảnh
    dict(CH, anh=[{"giay": 2, "khung_lop": [[0, 0, 0.1, 0.1]] * 13}, CH["anh"][1]]),  # quá 12 lớp
])
def test_cau_hinh_sai_bi_chan(c, sai):
    assert _gui(c, sai).status_code == 400


def test_qua_ba_anh_hoac_khong_phai_anh_bi_chan(c):
    bon = dict(CH, anh=[{"giay": 1, "khung_lop": []}] * 4)
    assert _gui(c, bon, [_png()] * 4).status_code == 400
    assert _gui(c, anh=[b"khong phai anh", _png()]).status_code == 400
    assert _gui(c, dict(CH, anh=CH["anh"][:1]), [_png(), _png()]).status_code == 400, "số ảnh phải khớp cấu hình"


def test_mot_anh_khong_lop_van_dung_duoc(c):
    assert _gui(c, dict(CH, anh=[{"giay": 2, "khung_lop": []}]), [_png()]).status_code == 200


def test_khong_danh_tinh_hoac_khong_co_quyen_dung_thi_chan(c):
    assert _gui(c, h={}).status_code == 401
    assert _gui(c, h={"X-Remote-User": "an", "X-Remote-Actions": "vao"}).status_code == 403


def test_bat_co_tin_proxy_thi_khong_tin_header_tu_may_ngoai(tmp_path, monkeypatch, may):
    monkeypatch.setenv("VOX_TRUST_PROXY", "1")
    c = TestClient(vapp.tao_app(tmp_path / "collage", may_lop=may), client=("192.168.1.9", 5000))
    assert _gui(c).status_code == 401


# ═══════ bước LỚP: máy đề xuất khung + xem phần cắt ═══════════════════════════
def _lop(c, khung_lop=None, de_xuat=False, khung="16:9", anh=None, h=AI):
    data = {"khung": khung, "de_xuat": "1" if de_xuat else ""}
    if khung_lop is not None:
        data["khung_lop"] = json.dumps(khung_lop)
    return c.post("/api/lop", headers=h, data=data, files=[("anh", ("a.png", anh or _png(w=400, h=400), "image/png"))])


def test_lop_may_de_xuat_tra_khung_va_anh_xem(c, may):
    r = _lop(c, de_xuat=True)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["khung_lop"] == [[0.25, 0.25, 0.75, 0.75]]
    assert j["xem"].startswith("data:image/jpeg;base64,")
    assert may.goi[0][0] == "de_xuat" and may.goi[1] == ("cat", may.goi[1][1], [[0.25, 0.25, 0.75, 0.75]])


def test_lop_cat_theo_khung_nguoi_keo_tren_anh_da_cat_khung_hinh(c, may):
    """Ảnh vuông 400x400 mà khung hình 16:9 -> máy cắt trên phần GIỮA đúng tỉ lệ (như lúc dựng)."""
    r = _lop(c, khung_lop=[[0.1, 0.1, 0.4, 0.9]])
    assert r.status_code == 200 and r.json()["khung_lop"] == [[0.1, 0.1, 0.4, 0.9]]
    h, w = may.goi[-1][1][:2]
    assert abs(w / h - 16 / 9) < 0.02, "cắt trên ảnh đã cắt khung hình"
    assert not any(g[0] == "de_xuat" for g in may.goi), "không bấm đề xuất thì không đề xuất"


def test_lop_chan_sai(c):
    assert _lop(c, khung_lop=[[0.6, 0.1, 0.4, 0.9]]).status_code == 400
    assert _lop(c, h={"X-Remote-User": "an", "X-Remote-Actions": "vao"}).status_code == 403
    assert _lop(c, anh=b"rac").status_code == 400


# ═══════ xem việc của mình ════════════════════════════════════════════════════
def test_danh_sach_chi_viec_cua_minh_kem_style_va_so_lop(c):
    ma = _gui(c).json()["id"]
    _gui(c, h={"X-Remote-User": "binh", "X-Remote-Actions": "vao,dung"})
    ds = c.get("/api/viec", headers=AI).json()["viec"]
    assert [v["id"] for v in ds] == [ma]
    v = ds[0]
    assert v["trang_thai"] == "cho" and v["thu_tu"] == 1 and v["giay"] == 5.5
    assert v["style"] == "Black Grid" and v["khung"] == "16:9"
    assert [a["so_lop"] for a in v["anh"]] == [1, 0]


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


# ═══════ sức khoẻ + thợ ═══════════════════════════════════════════════════════
def test_suc_khoe_bao_tho_chua_chay(c, tmp_path):
    j = c.get("/api/suc-khoe").json()
    tho = [m for m in j["mo_dun"] if m["ten"] == "tho"][0]
    assert tho["trang_thai"] == "canh_bao" and j["trang_thai"] == "canh_bao"
    (tmp_path / "collage" / "tho.song").write_text("1")
    assert c.get("/api/suc-khoe").json()["trang_thai"] == "ok"


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
            pass
    finally:
        giu.close()


# ═══════ nhập PSD team đã chia layer (user chốt 08/10) ══════════════════════════════════════════════
def _psd_bytes():
    pytest.importorskip("psd_tools")
    from PIL import Image
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer

    p = PSDImage.new("RGB", (320, 180), color=(0, 0, 0))
    p.append(PixelLayer.frompil(Image.new("RGBA", (320, 180), (40, 80, 160, 255)), p, "Nen", 0, 0))
    p.append(PixelLayer.frompil(Image.new("RGBA", (80, 60), (250, 20, 20, 255)), p, "Nguoi", 60, 120))
    an = PixelLayer.frompil(Image.new("RGBA", (20, 20), (0, 255, 0, 255)), p, "An", 5, 5)
    an.visible = False
    p.append(an)
    p.append(PixelLayer.frompil(Image.new("RGBA", (100, 20), (240, 220, 30, 255)), p, "Chu", 10, 110))
    b = io.BytesIO()
    p.save(b)
    return b.getvalue()


def _psd(c, b=None, h=AI):
    return c.post("/api/psd", headers=h, files=[("anh", ("a.psd", b or _psd_bytes(), "image/vnd.adobe.photoshop"))])


def test_psd_doc_tra_khoi_anh_xem_va_de_xuat(c):
    r = _psd(c)
    assert r.status_code == 200, r.text
    j = r.json()
    assert (j["rong"], j["cao"]) == (320, 180)
    assert [x["ten"] for x in j["lop"]] == ["Nen", "Nguoi", "An", "Chu"]
    assert j["de_xuat"] == [1, 3], "máy tick sẵn mọi khối đang hiện, chừa nền dưới cùng"
    assert j["xem"].startswith("data:image/jpeg;base64,"), "trình duyệt không xem được PSD -> máy chủ trả ảnh xem"
    assert all(x["nho"].startswith("data:image/png;base64,") for x in j["lop"] if x["hien"])
    assert j["con_trong_nen"] == [], "nền xanh không chứa khối nào"


def test_psd_bao_nen_con_chua_khoi(c):
    """Nền (Layer 1) còn bản sao khối -> trả tên để trang cảnh báo team xoá trong Photoshop."""
    pytest.importorskip("psd_tools")
    from PIL import Image
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer

    p = PSDImage.new("RGB", (320, 180), color=(0, 0, 0))
    nen = Image.new("RGBA", (320, 180), (40, 80, 160, 255))
    nen.paste((250, 20, 20, 255), (120, 60, 200, 120))
    p.append(PixelLayer.frompil(nen, p, "Layer 1", 0, 0))
    p.append(PixelLayer.frompil(Image.new("RGBA", (80, 60), (250, 20, 20, 255)), p, "Elon", 60, 120))
    b = io.BytesIO()
    p.save(b)
    j = _psd(c, b=b.getvalue()).json()
    assert j["de_xuat"] == [1] and j["con_trong_nen"] == [1]


def test_psd_chan_sai(c):
    assert _psd(c, b=_png()).status_code == 400
    assert _psd(c, h={"X-Remote-User": "an", "X-Remote-Actions": "vao"}).status_code == 403


def _gui_psd(c, psd_lop, anh=None):
    ch = {"anh": [{"giay": 3, "khung_lop": [], "psd_lop": psd_lop}], "khung": "16:9", "style": "non_grid"}
    return c.post("/api/viec", headers=AI, data={"cau_hinh": json.dumps(ch)},
                  files=[("anh", ("a.psd", anh or _psd_bytes(), "image/vnd.adobe.photoshop"))])


def test_gui_psd_luu_file_psd_va_khoi_da_chon(c, tmp_path):
    r = _gui_psd(c, [3, 1])
    assert r.status_code == 200, r.text
    v = HangDoi(tmp_path / "collage" / "hang_doi.db").doc(r.json()["id"])
    ch = json.loads(v["chuoi"])
    assert ch["anh"][0]["anh"].endswith(".psd") and ch["anh"][0]["psd_lop"] == [1, 3]
    ds = c.get("/api/viec", headers=AI).json()["viec"][0]
    assert ds["anh"][0]["so_lop"] == 2 and ds["anh"][0]["psd"] is True
    im = c.get(f"/api/viec/{r.json()['id']}/anh/0")
    assert im.status_code == 200 and im.headers["content-type"] == "image/jpeg", "ảnh nhỏ của việc PSD xem được"


@pytest.mark.parametrize("psd_lop, bao", [([9], "không có khối"), ([2], "đang ẩn"), ([0, 1, 3], "nền")])
def test_gui_psd_chan_khoi_sai(c, psd_lop, bao):
    r = _gui_psd(c, psd_lop)
    assert r.status_code == 400 and bao in r.json()["detail"], r.text


def test_gui_anh_thuong_khong_duoc_khai_khoi_psd(c):
    ch = {"anh": [{"giay": 3, "khung_lop": [], "psd_lop": [1]}], "khung": "16:9", "style": "non_grid"}
    r = c.post("/api/viec", headers=AI, data={"cau_hinh": json.dumps(ch)}, files=[("anh", ("a.png", _png(), "image/png"))])
    assert r.status_code == 400
