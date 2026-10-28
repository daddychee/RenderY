"""Bảng vẽ P3 — biết node nào CŨ.

Mỗi lần Create Prompt / Vẽ ảnh / Video chạy xong, máy chủ ghi DẤU đầu vào đã
dùng. "Cũ" = đầu vào hôm nay khác dấu đó. Ba luật khoá chặt:
  1. Chưa từng ghi dấu (dữ liệu trước tính năng) thì KHÔNG báo cũ — kêu oan cả
     tập là người dùng thôi tin cờ này.
  2. Video chỉ ghi dấu khi task XONG. Task hỏng thì video cũ (nếu có) vẫn mang
     dấu cũ của nó, không nhận dấu của lượt hỏng.
  3. Vẽ lại ảnh -> video dựng từ ảnh cũ thành cũ.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64


class KyThuatGia:
    def __init__(self):
        self.lan = 0

    def ky_thuat(self, muc, tai_san):
        self.lan += 1
        return [{"id": m["id"], "lap": "x", "pa": f"pa lần {self.lan}",
                 "pv": f"pv lần {self.lan}", "sfx": ""} for m in muc]


class VeAnhGia:
    def gen_anh(self, prompt, dich, ref=None):
        dich.parent.mkdir(parents=True, exist_ok=True)
        # nội dung đổi theo prompt -> mtime đổi thật
        dich.write_bytes(PNG + prompt.encode("utf-8"))


class VeVideoGia:
    def __init__(self):
        self.tra = "succeeded"

    def bat_dau(self, prompt, anh, giay, am):
        return "task-1"

    def trang_thai(self, tid):
        return {"status": self.tra, "video_url": "u", "loi": "hỏng giả"}

    def tai_ve(self, url, dich):
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(MP4)


def _bo(tmp_path):
    kho = Kho(tmp_path / "k.db")
    vv = VeVideoGia()
    c = TestClient(tao_app(kho, ky_thuat=KyThuatGia(), ve_anh=VeAnhGia(), ve_video=vv))
    c.headers.update({"X-Remote-User": "haint", "X-Remote-Actions": "sua"})
    c.post("/api/tap", json={"ma": "SE001", "ten": "x"})
    c.post("/api/tap/SE001/chuong", json={"ma": "H"})
    kho.luu("SE001", "H", [{"en": "The hatch opens.", "vi": "", "het": 0,
                            "canh": [{"id": "k1", "t": "nắp mở"}]}], "", "haint")
    return c, kho, vv


def _cu(c):
    return c.get("/api/tap/SE001/H/cu").json()["k1"]


def _sua(c, **truong):
    assert c.patch("/api/tap/SE001/H/canh/k1", json={"truong": truong}).status_code == 200


def test_chua_ghi_dau_thi_khong_bao_cu(tmp_path):
    c, kho, _ = _bo(tmp_path)
    # dữ liệu "cũ": có pa sẵn mà chưa từng qua Create Prompt của bản này
    _sua(c, pat="viết tay")
    assert _cu(c) == {"prompt": False, "anh": False, "video": False}


def test_sua_mo_ta_thi_prompt_cu_chay_lai_thi_het(tmp_path):
    c, _, _ = _bo(tmp_path)
    assert c.post("/api/tap/SE001/H/canh/k1/ky-thuat").status_code == 200
    assert _cu(c)["prompt"] is False
    _sua(c, t="nắp mở TOANG")
    assert _cu(c)["prompt"] is True
    c.post("/api/tap/SE001/H/canh/k1/ky-thuat")
    assert _cu(c)["prompt"] is False


def test_prompt_doi_thi_anh_cu(tmp_path):
    c, _, _ = _bo(tmp_path)
    c.post("/api/tap/SE001/H/canh/k1/ky-thuat")
    assert c.post("/api/tap/SE001/H/canh/k1/anh").status_code == 200
    assert _cu(c)["anh"] is False
    _sua(c, pat="prompt sửa tay khác")
    assert _cu(c)["anh"] is True
    c.post("/api/tap/SE001/H/canh/k1/anh")
    assert _cu(c)["anh"] is False


def _dung_video(c):
    c.post("/api/tap/SE001/H/canh/k1/duyet")
    assert c.post("/api/tap/SE001/H/canh/k1/video", json={}).status_code == 200
    return c.post("/api/tap/SE001/H/canh/k1/video-kiem").json()


def test_ve_lai_anh_thi_video_cu(tmp_path):
    import os
    import time

    c, kho, _ = _bo(tmp_path)
    c.post("/api/tap/SE001/H/canh/k1/ky-thuat")
    c.post("/api/tap/SE001/H/canh/k1/anh")
    assert _dung_video(c)["trang_thai"] == "xong"
    assert _cu(c)["video"] is False
    # vẽ lại ảnh: mtime phải nhích thật (hệ tệp có thể làm tròn giây)
    _sua(c, pat="ảnh khác")
    c.post("/api/tap/SE001/H/canh/k1/anh")
    t = kho.duong_anh("SE001", "k1")
    os.utime(t, (time.time() + 5, time.time() + 5))
    assert _cu(c)["video"] is True


def test_video_hong_khong_nhan_dau(tmp_path):
    c, _, vv = _bo(tmp_path)
    c.post("/api/tap/SE001/H/canh/k1/ky-thuat")
    c.post("/api/tap/SE001/H/canh/k1/anh")
    vv.tra = "failed"
    assert _dung_video(c)["trang_thai"] == "hong"
    # không có video, không có dấu -> không "cũ"; và lượt sau xong thì có dấu
    assert _cu(c)["video"] is False
    vv.tra = "succeeded"
    assert _dung_video(c)["trang_thai"] == "xong"
    assert _cu(c)["video"] is False
    _sua(c, pvt="chuyển động khác")
    assert _cu(c)["video"] is True
