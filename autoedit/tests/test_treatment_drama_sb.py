"""Thẻ clip drama ở Storyboard: ảnh shot + trạng thái từng shot (user chốt 29/10).

Trạng thái lấy MỘT lượt cùng GET chương (khoá `fs`), không gọi `/shot` cho từng clip —
DM002 có 348 clip. Ảnh trên thẻ là ảnh NHỎ: ảnh gốc 2,2 MB × 50 thẻ = 110 MB mỗi chương.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path

from PIL import Image

from test_treatment_drama_api import MP4, _clip
from test_treatment_drama_shot_api import _dan_duyet, _san

HTML = Path(__file__).resolve().parents[1] / "autoedit" / "treatment" / "static" / "treatment.html"


def test_doc_chuong_tra_tem_file_tung_shot(tmp_path):
    """`fs` = {sid: [giờ sửa ảnh, giờ sửa video]} suy từ ĐĨA, 0 là chưa có file."""
    kho, c = _san(tmp_path)
    p1 = _clip(kho)
    s1, s2 = [s["sid"] for s in json.loads(p1["sh"])]
    a = kho.duong_anh("D1", f"{p1['id']}-{s1}")
    a.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (480, 270)).save(a)
    v = kho.duong_video("D1", f"{p1['id']}-{s1}")
    v.parent.mkdir(parents=True, exist_ok=True)
    v.write_bytes(MP4)
    x = c.get("/api/tap/D1/C1").json()["dong"][0]["canh"][0]
    assert x["fs"] == {s1: [int(a.stat().st_mtime), int(v.stat().st_mtime)], s2: [0, 0]}
    # `fs` là khoá suy ra: trang gửi lại cả chương thì không được rơi xuống kho
    d = c.get("/api/tap/D1/C1").json()
    assert c.put("/api/tap/D1/C1", json={"dong": d["dong"], "outline": d["outline"]}).status_code == 200
    assert "fs" not in _clip(kho)


def test_anh_nho_shot_jpeg_cache_dia_va_lam_lai_khi_ve_lai(tmp_path):
    kho, c = _san(tmp_path)
    _dan_duyet(c)
    p1 = _clip(kho)
    sid = json.loads(p1["sh"])[0]["sid"]
    goc = f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sid}"
    assert c.get(goc + "/anh-nho").status_code == 404, "chưa có ảnh"
    assert c.post(goc + "/anh").status_code == 200
    r = c.get(goc + "/anh-nho?v=1")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    cc = r.headers["cache-control"]
    assert "private" in cc and "immutable" in cc and "max-age" in cc, cc
    im = Image.open(io.BytesIO(r.content))
    assert im.format == "JPEG" and max(im.size) == 320 and abs(im.size[0] / im.size[1] - 480 / 270) < 0.02
    nho = kho.duong_anh("D1", f"{p1['id']}-{sid}").with_name(f"{p1['id']}-{sid}-nho.jpg")
    assert nho.exists()
    t0 = nho.stat().st_mtime_ns
    assert c.get(goc + "/anh-nho").status_code == 200 and nho.stat().st_mtime_ns == t0, "đã có thì không làm lại"
    # vẽ lại: ảnh gốc mới hơn ảnh nhỏ thì làm lại
    a = kho.duong_anh("D1", f"{p1['id']}-{sid}")
    Image.new("RGB", (480, 270), (220, 0, 0)).save(a)
    os.utime(a, (a.stat().st_atime, nho.stat().st_mtime + 5))
    r = c.get(goc + "/anh-nho")
    assert Image.open(io.BytesIO(r.content)).convert("RGB").getpixel((5, 5))[0] > 180
    assert c.get(f"/api/tap/D1/C1/canh/{p1['id']}/shot/a.b/anh-nho").status_code == 400


def test_dungCanhTap_cho_khoa_fs():
    """Thiếu khoá ở khung nhìn thì máy chủ trả mà thẻ không thấy (bài học `pat`/`pvt` 26/09)."""
    h = HTML.read_text(encoding="utf-8")
    i = h.index("function dungCanhTap(")
    assert "fs: cn.fs" in h[i:h.index("\n}", i)]
