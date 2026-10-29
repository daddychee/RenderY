"""Storage — tải video đã gen một lượt (user chốt 29/10).

Luật đã chốt: ZIP theo CHƯƠNG (gateway gom trọn body vào RAM — proxy.py aread), trần
1,5 GB trả 413; có lọc "chỉ video mới từ lần trước"; video đang gen lại vẫn vào ZIP,
đánh dấu ⟳. Liệt kê THEO KỊCH BẢN (thứ tự dựng), không quét thư mục: file mồ côi
không lọt. Tên file xếp đúng thứ tự timeline: `C1_P001_s1_CU_6s.mp4`.
"""

from __future__ import annotations

import io
import os
import time
import zipfile

from fastapi.testclient import TestClient

import autoedit.treatment.app as mapp
from autoedit.treatment.app import tao_app
from autoedit.treatment.kho import Kho
from test_treatment_drama_api import _bd, _bo, _clip, _tap_drama


def _sh(kho, ch, j=0):
    import json
    return json.loads(_clip(kho, ch=ch, j=j)["sh"])


def _ghi(kho, ma, noi_dung, cu=True):
    """MP4 giả, MỖI FILE MỘT NỘI DUNG (byte giống nhau thì so khớp nguồn là xanh giả).
    `cu`: lùi giờ sửa 100 s — file vừa ghi bị coi là đang ghi dở."""
    p = kho.duong_video("D1", ma)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x00\x00\x00\x18ftypmp42" + noi_dung.encode() * 50)
    if cu:
        t = time.time() - 100
        os.utime(p, (t, t))
    return p


def _san(tmp_path):
    """D1: C1 có P001 (2 shot) + P002 (1 shot), C2 có P003 (1 shot).
    Có video: P001 s1, s2 · P002 cả clip (đường cũ) · P003 s1 · một file mồ côi."""
    kho, c = _bo(tmp_path)
    _tap_drama(c)
    _bd(c)
    _bd(c, ch="C2")
    p1, p2, p3 = _clip(kho), _clip(kho, j=1), _clip(kho, ch="C2")
    s1, s3 = _sh(kho, "C1"), _sh(kho, "C2")
    _ghi(kho, f"{p1['id']}-{s1[0]['sid']}", "a")
    _ghi(kho, f"{p1['id']}-{s1[1]['sid']}", "b")
    _ghi(kho, p2["id"], "c")
    _ghi(kho, f"{p3['id']}-{s3[0]['sid']}", "d")
    _ghi(kho, f"{p1['id']}-sdead00", "mo-coi")
    return kho, c, (p1, p2, p3)


TEN_C1 = ["C1_P001_s1_CU_6s.mp4", "C1_P001_s2_MS_6s.mp4", "C1_P002_clip_15s.mp4"]


def test_danh_sach_theo_thu_tu_dung_ten_xep_duoc_khong_lot_mo_coi(tmp_path):
    kho, c, _ = _san(tmp_path)
    r = c.get("/api/tap/D1/kho-video")
    # Khai sau `/api/tap/{tap}/{chuong}` là "kho-video" bị nuốt làm mã chương -> không có "ds".
    assert r.status_code == 200 and "ds" in r.json(), r.text
    ds = r.json()["ds"]
    assert [x["ten"] for x in ds] == TEN_C1 + ["C2_P003_s1_CU_6s.mp4"]
    assert [x["loai"] for x in ds] == ["shot", "shot", "clip", "shot"]
    assert [x["ch"] for x in ds] == ["C1", "C1", "C1", "C2"]
    assert all(x["byte"] > 0 and not x["dang"] and not x["ghi"] for x in ds)
    assert r.json()["moc"] <= time.time() - mapp.GIAY_GHI + 1


def test_zip_chuong_khong_nen_byte_khop_nguon(tmp_path):
    kho, c, (p1, p2, _) = _san(tmp_path)
    r = c.get("/api/tap/D1/kho-video.zip?ch=C1")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"
    assert 'filename="D1_C1_' in r.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert z.testzip() is None
    assert z.namelist() == TEN_C1
    assert all(i.compress_type == zipfile.ZIP_STORED for i in z.infolist())
    s1 = _sh(kho, "C1")
    nguon = [kho.duong_video("D1", f"{p1['id']}-{s1[0]['sid']}"),
             kho.duong_video("D1", f"{p1['id']}-{s1[1]['sid']}"), kho.duong_video("D1", p2["id"])]
    assert [z.read(n) for n in TEN_C1] == [p.read_bytes() for p in nguon]


def test_loc_loai_va_chi_video_moi(tmp_path):
    kho, c, (p1, _, _) = _san(tmp_path)
    r = c.get("/api/tap/D1/kho-video.zip?ch=C1&loai=shot")
    assert zipfile.ZipFile(io.BytesIO(r.content)).namelist() == TEN_C1[:2]
    moc = time.time() - 50
    # gen lại shot 2 sau mốc lần tải trước -> chỉ shot đó
    p = kho.duong_video("D1", f"{p1['id']}-{_sh(kho, 'C1')[1]['sid']}")
    t = time.time() - 20
    os.utime(p, (t, t))
    r = c.get(f"/api/tap/D1/kho-video.zip?ch=C1&sau={moc}")
    assert zipfile.ZipFile(io.BytesIO(r.content)).namelist() == ["C1_P001_s2_MS_6s.mp4"]


def test_file_dang_ghi_hien_tren_danh_sach_nhung_khong_vao_zip(tmp_path):
    kho, c, (p1, _, _) = _san(tmp_path)
    _ghi(kho, f"{p1['id']}-{_sh(kho, 'C1')[0]['sid']}", "moi", cu=False)
    ds = c.get("/api/tap/D1/kho-video").json()["ds"]
    assert [x["ghi"] for x in ds] == [True, False, False, False]
    r = c.get("/api/tap/D1/kho-video.zip?ch=C1")
    assert zipfile.ZipFile(io.BytesIO(r.content)).namelist() == TEN_C1[1:]


def test_dang_gen_lai_van_vao_zip_co_dau(tmp_path):
    """User chốt: video đang gen lại (file cũ còn) vẫn tải, trang đánh dấu ⟳."""
    import json
    kho, c, (p1, p2, _) = _san(tmp_path)
    sid = _sh(kho, "C1")[1]["sid"]
    kho.sua_canh("D1", "C1", p1["id"], lambda x: x.update(ss=json.dumps({sid: {"vid": "task-9"}})), "minh")
    kho.sua_canh("D1", "C1", p2["id"], lambda x: x.update(vid="task-8"), "minh")
    ds = c.get("/api/tap/D1/kho-video").json()["ds"]
    assert [x["dang"] for x in ds] == [False, True, True, False]
    r = c.get("/api/tap/D1/kho-video.zip?ch=C1")
    assert zipfile.ZipFile(io.BytesIO(r.content)).namelist() == TEN_C1


def test_qua_tran_413_chuong_la_va_rong_404(tmp_path, monkeypatch):
    _, c, _ = _san(tmp_path)
    monkeypatch.setattr(mapp, "TRAN_ZIP", 100)
    r = c.get("/api/tap/D1/kho-video.zip?ch=C1")
    assert r.status_code == 413 and "quá trần" in r.json()["detail"], r.text
    monkeypatch.undo()
    assert c.get("/api/tap/D1/kho-video.zip?ch=C9").status_code == 404
    assert c.get(f"/api/tap/D1/kho-video.zip?ch=C1&sau={time.time()}").status_code == 404


def test_narration_ten_theo_so_phan_canh_chay_lien_chuong(tmp_path):
    """Phân cảnh đánh số LIỀN H -> C1 (user chốt 24/09): dòng đầu C1 sau 2 dòng H là PC003."""
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("N1", "x")
    kho.luu("N1", "H", [{"en": "a", "canh": [{"id": "ca1", "t": "x"}]},
                        {"en": "b", "canh": [{"id": "ca2", "t": "y"}]}], "", "minh")
    kho.luu("N1", "C1", [{"en": "c", "canh": [{"id": "cb1", "t": "z"}, {"id": "cb2", "t": "w"}]}], "", "minh")
    for ma in ("ca1", "cb2"):
        p = kho.duong_video("N1", ma)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(ma.encode() * 40)
        os.utime(p, (time.time() - 100, time.time() - 100))
    c = TestClient(tao_app(kho))
    ds = c.get("/api/tap/N1/kho-video").json()["ds"]
    assert [(x["ten"], x["loai"]) for x in ds] == [("H_PC001-1.mp4", "canh"), ("C1_PC003-2.mp4", "canh")]
    r = c.get("/api/tap/N1/kho-video.zip?ch=C1")
    assert zipfile.ZipFile(io.BytesIO(r.content)).namelist() == ["C1_PC003-2.mp4"]


# ═══════ sửa sau dùng thử prod 29/10: thẻ có ảnh + tích chọn nhiều ô ═══════════════
def _anh(kho, tap, ma):
    p = kho.duong_anh(tap, ma)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"png")
    return int(p.stat().st_mtime)


def test_danh_sach_co_khoa_chon_va_tem_anh_cho_the(tmp_path):
    """Thẻ Storage lấy ảnh nhỏ theo TEM trong JSON — không gọi thêm request mỗi thẻ."""
    kho, c, (p1, p2, _) = _san(tmp_path)
    s1 = _sh(kho, "C1")
    t = _anh(kho, "D1", f"{p1['id']}-{s1[0]['sid']}")
    _anh(kho, "D1", p2["id"])              # clip kiểu cũ: ảnh của clip không phải ảnh của video
    ds = c.get("/api/tap/D1/kho-video").json()["ds"]
    assert [x["anh"] for x in ds] == [t, 0, 0, 0]
    assert [x["khoa"] for x in ds][:3] == [f"{p1['id']}-{s1[0]['sid']}", f"{p1['id']}-{s1[1]['sid']}", p2["id"]]


def test_narration_the_lay_anh_canh(tmp_path):
    kho = Kho(tmp_path / "kho" / "k.db")
    kho.tao_tap("N1", "x")
    kho.luu("N1", "H", [{"en": "a", "canh": [{"id": "ca1", "t": "x"}]}], "", "minh")
    p = kho.duong_video("N1", "ca1")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"v" * 40)
    t = _anh(kho, "N1", "ca1")
    ds = TestClient(tao_app(kho)).get("/api/tap/N1/kho-video").json()["ds"]
    assert [(x["khoa"], x["anh"]) for x in ds] == [("ca1", t)]


def test_zip_chon_nhieu_khac_chuong_ma_la_bo_qua_thu_tu_dung(tmp_path):
    kho, c, (p1, _, p3) = _san(tmp_path)
    k2 = f"{p1['id']}-{_sh(kho, 'C1')[1]['sid']}"
    k3 = f"{p3['id']}-{_sh(kho, 'C2')[0]['sid']}"
    # chọn ngược thứ tự + mã lạ + mã mồ côi có file trên đĩa + đường lạ: chỉ mã trong kịch bản
    chon = ",".join([k3, "cxxxxxxxxxx-sbogus", f"{p1['id']}-sdead00", "..%2F..%2Fk", k2])
    r = c.get(f"/api/tap/D1/kho-video.zip?chon={chon}")
    assert r.status_code == 200, r.text
    assert 'filename="D1_chon_2_' in r.headers["content-disposition"]
    z = zipfile.ZipFile(io.BytesIO(r.content))
    assert z.testzip() is None
    assert z.namelist() == ["C1_P001_s2_MS_6s.mp4", "C2_P003_s1_CU_6s.mp4"]
    assert [z.read(n) for n in z.namelist()] == [kho.duong_video("D1", k).read_bytes() for k in (k2, k3)]


def test_zip_chon_qua_tran_413_rong_404_thieu_400(tmp_path, monkeypatch):
    kho, c, (p1, _, _) = _san(tmp_path)
    k = f"{p1['id']}-{_sh(kho, 'C1')[0]['sid']}"
    monkeypatch.setattr(mapp, "TRAN_ZIP", 10)      # một MP4 giả ~66 byte
    r = c.get(f"/api/tap/D1/kho-video.zip?chon={k}")
    assert r.status_code == 413 and "quá trần" in r.json()["detail"], r.text
    monkeypatch.undo()
    assert c.get("/api/tap/D1/kho-video.zip?chon=cbogus").status_code == 404
    assert c.get("/api/tap/D1/kho-video.zip").status_code == 400
