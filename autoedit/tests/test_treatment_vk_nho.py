"""Bớt lượt hỏi trạng thái video (user duyệt 30/10, phương án 1 + 1b).

Đo 30/10 11:19–11:39: ≥4 tab, mỗi tab hỏi MỌI shot đang dựng 20 s một lần -> khoảng 5 lượt/giây
tới Lightvisual, sáng cùng ngày dính 429. Máy chủ nhớ trạng thái MỖI TASK 20 s, mọi tab dùng
chung; lỗi không nhớ. Lượt hỏi gặp 429 không thử lại, route trả "dang" (giữ mã task) để cả tab
chạy JS CŨ cũng hiểu là chưa xong và 20 s sau hỏi tiếp. Nhà giả — không mạng, không khoá thật.
"""

from __future__ import annotations

import json
import pathlib
import threading
import time

import pytest
from fastapi.testclient import TestClient

import autoedit.treatment.app as mapp
import test_treatment_drama_shot_api as mshot
import test_treatment_video as mvideo
from autoedit.aigen import lightvisual as mlv
from autoedit.aigen.client import AigenError
from test_aigen_seedvis import PhienGia, _Tra

VID = "lv_job_a@api-041"


class VeDem:
    """Nhà video giả đếm lượt hỏi / tải. `tt` trạng thái trả, `nem` lỗi ném khi hỏi, `cham` giây tải."""

    def __init__(self, tt="running", nem=None, cham=0.0):
        self.tt, self.nem, self.cham, self.hoi, self.tai = tt, nem, cham, 0, 0

    def bat_dau(self, prompt, anh, giay, am, model=None):
        return VID

    def trang_thai(self, tid):
        self.hoi += 1
        if self.nem:
            raise self.nem
        return {"status": self.tt, "video_url": "https://lightvisual.studio/v1/videos/lv_job_a/content#api-041"}

    def tai_ve(self, url, dich):
        self.tai += 1
        time.sleep(self.cham)
        dich.parent.mkdir(parents=True, exist_ok=True)
        dich.write_bytes(mvideo.MP4)
        return dich


def _qua_tai():
    e = AigenError('Lightvisual HTTP 429: {"error":{"message":"Hệ thống đang giới hạn tốc độ request"}}')
    e.ma = 429
    return e


def _dung(tmp_path, loai, vv):
    """(client, đường video-kiem, đọc `vid` trong kho) cho cảnh narration hoặc shot drama."""
    if loai == "canh":
        c, kho, ma = mvideo._bo(tmp_path, vv)
        assert c.post(f"/api/tap/SE001/H/canh/{ma}/video").status_code == 200
        return c, f"/api/tap/SE001/H/canh/{ma}/video-kiem", lambda: mvideo._canh(kho).get("vid")
    kho, c = mshot._san(tmp_path, vv=vv)
    p1 = mshot._clip(kho)
    sid = json.loads(p1["sh"])[0]["sid"]
    kho.sua_canh("D1", "C1", p1["id"], lambda y: y.update(ss=json.dumps({sid: {"duyet": "1", "vid": VID}})), "thu")
    return (c, f"/api/tap/D1/C1/canh/{p1['id']}/shot/{sid}/video-kiem",
            lambda: (json.loads(mshot._clip(kho).get("ss") or "{}").get(sid) or {}).get("vid"))


@pytest.fixture
def gio(monkeypatch):
    """Đồng hồ của bộ nhớ đệm, test tự vặn."""
    t = [1000.0]
    monkeypatch.setattr(mapp, "_gio", lambda: t[0])
    return t


def test_dung_code_cua_cay_dang_test():
    goc = pathlib.Path(__file__).resolve().parents[1]
    assert pathlib.Path(mapp.__file__).resolve().is_relative_to(goc), mapp.__file__


@pytest.mark.parametrize("loai", ["canh", "shot"])
def test_nhieu_tab_trong_20s_chi_mot_luot_hoi_nha(tmp_path, gio, loai):
    vv = VeDem()
    c, duong, vid = _dung(tmp_path, loai, vv)
    assert [c.post(duong).json()["trang_thai"] for _ in range(3)] == ["dang"] * 3
    assert vv.hoi == 1, "ba tab trong 20 s dùng chung một lượt hỏi"
    gio[0] += 21
    assert c.post(duong).json()["trang_thai"] == "dang" and vv.hoi == 2, "quá 20 s thì hỏi lại"
    assert vid() == VID


@pytest.mark.parametrize("loai", ["canh", "shot"])
def test_hoi_gap_429_thi_van_dang_giu_ma_task_khong_nho(tmp_path, gio, loai):
    """Trang (cả JS cũ) chỉ coi 200 + "dang" là chưa xong; mã khác là lỗi đỏ và ngừng hỏi."""
    vv = VeDem(nem=_qua_tai())
    c, duong, vid = _dung(tmp_path, loai, vv)
    r = c.post(duong)
    assert r.status_code == 200 and r.json()["trang_thai"] == "dang", r.text
    assert vid() == VID, "429 không phải hỏng: giữ mã task"
    c.post(duong)
    assert vv.hoi == 2, "429 là lỗi: không nhớ, lượt sau hỏi lại"


def test_loi_khac_van_bao_502_va_khong_nho(tmp_path, gio):
    vv = VeDem(nem=AigenError("Lightvisual HTTP 401: invalid key"))
    c, duong, vid = _dung(tmp_path, "shot", vv)
    assert c.post(duong).status_code == 502
    assert c.post(duong).status_code == 502 and vv.hoi == 2
    assert vid() == VID


@pytest.mark.parametrize("loai", ["canh", "shot"])
def test_xong_roi_tab_khac_hoi_khong_tai_lai_khong_bao_loi(tmp_path, gio, loai):
    """Hai tab cùng hỏi lúc task vừa xong: chỉ MỘT lượt tải, cả hai thấy "xong"; tab hỏi sau đó
    (trạng thái `succeeded` còn trong bộ nhớ 20 s) cũng không tải lại."""
    vv = VeDem(tt="succeeded", cham=0.5)
    c, duong, vid = _dung(tmp_path, loai, vv)
    c2 = TestClient(c.app)
    c2.headers.update(c.headers)
    rao, ra = threading.Barrier(2), []

    def tab(cl):
        rao.wait()
        r = cl.post(duong)
        ra.append((r.status_code, r.json().get("trang_thai")))
    ds = [threading.Thread(target=tab, args=(x,)) for x in (c, c2)]
    for t in ds:
        t.start()
    for t in ds:
        t.join()
    assert ra == [(200, "xong")] * 2 and vv.tai == 1, (ra, vv.tai)
    assert vid() is None
    assert c.post(duong).json()["trang_thai"] == "xong" and vv.tai == 1


def test_lightvisual_hoi_trang_thai_gap_429_khong_thu_lai_gui_van_thu_lai(monkeypatch):
    ngu = []
    monkeypatch.setattr(mlv.time, "sleep", lambda s: ngu.append(s))
    tai = _Tra(429, {"error": {"message": "Hệ thống đang giới hạn tốc độ request"}})
    c = mlv.LightvisualClient(api_key="LV_test_key")
    c._session = PhienGia([tai, _Tra(200, {"id": "lv_job_b", "status": "queued"})])
    with pytest.raises(AigenError) as e:
        c.trang_thai_video("lv_job_b")
    assert getattr(e.value, "ma", None) == 429 and len(c._session.goi) == 1 and not ngu, "hỏi: không thử lại"
    c._session = PhienGia([tai, _Tra(200, {"id": "lv_job_c", "status": "queued"})])
    assert c._nop({"model": "m"}) == "lv_job_c" and len(c._session.goi) == 2 and ngu, "gửi: vẫn chờ rồi thử lại"
