# -*- coding: utf-8 -*-
r"""Hai bug đo được ngày 07/09, cùng một gốc: việc CỦA TẬP làm sai chỗ.

1. `nap_ref_tap` không hỏi "ref này nạp chưa?" -> mỗi chương được phân tích lại
   cắt cảnh + đọc hình TOÀN BỘ ref của tập. LI103: 480 cảnh, ~15 phút GLM mỗi
   chương, `them_clip` trả về 0 cảnh mới. 17 chương = 17 lần trả tiền cho câu
   trả lời đã có. User: "phân tích 1 chương lâu vậy hả".

2. Mã tập suy ở hai nơi bằng hai regex khác nhau -> worker nạp ref dưới `LI104`
   trong khi tab Offline tra `LI104 TOOL`. Rào geo khi đó chặn nhầm ref của
   chính tập mình — đúng thứ rào sinh ra để ngăn.
"""
from pathlib import Path

import pytest

from autoedit.sotra import db as sdb


@pytest.fixture()
def conn(tmp_path):
    return sdb.mo(tmp_path / "so_tra.db")


# ----------------------------------------------------- mã tập: MỘT nguồn sự thật
@pytest.mark.parametrize("duong_dan, mong", [
    (r"F:\OutlierY Nas 2\Life In\US\LI103\Rendery", "LI103"),
    (r"F:\Nas\LI104 TOOL\RenderY", "LI104"),          # hậu tố ngăn bằng KHOẢNG TRẮNG
    (r"F:\Nas\LI096_Hai\RenderY", "LI096"),           # ngăn bằng gạch dưới
    (r"F:\Nas\LI093_Test tool\C1", "LI093"),
    ("//192.168.1.250/Video/RenderY/LI105/RenderY/C3", "LI105"),   # UNC, gạch xuôi
    (r"F:\Nas\LI103", "LI103"),                       # mã ở cuối, không có / sau
])
def test_ma_tap_bat_moi_kieu_ten_that_tren_nas(duong_dan, mong):
    assert sdb.ma_tap_tu_duong_dan(duong_dan) == mong


@pytest.mark.parametrize("duong_dan", [
    r"F:\linh tinh\abc",
    r"C:\projects\h-20260905-104130",       # tên project, KHÔNG phải mã tập
    r"C:\projects\chuong-ref-20260902-070916",
])
def test_khong_suy_duoc_thi_tra_rong_khong_doan_bua(duong_dan):
    """Đoán bừa ở đây đẻ ra `tap='h-20260905-104130'` nằm lẫn trong kho."""
    assert sdb.ma_tap_tu_duong_dan(duong_dan) == ""


def test_worker_va_offline_suy_cung_mot_ma(tmp_path):
    """Lệch một ký tự giữa hai nơi là ref của tập bị rào geo chặn nhầm."""
    import json

    from autoedit.offline.runner import _ma_tap
    from autoedit.web.worker import _ma_tap_tu_folder

    goc = r"F:\Nas\LI104 TOOL\RenderY\C3\script.txt"
    pd = tmp_path / "c3-20260907-000000"
    pd.mkdir()
    (pd / "project.json").write_text(
        json.dumps({"inputs": {"original_script_path": goc}}), encoding="utf-8")

    assert _ma_tap(pd) == _ma_tap_tu_folder(Path(goc).parent.parent) == "LI104"


# ----------------------------------------------------- ref: nạp rồi thì thôi
def test_da_nap_bao_chua_khi_kho_trong(conn, tmp_path):
    from autoedit.sotra.hut import _da_nap

    vid = tmp_path / "ref 1.mp4"
    vid.write_bytes(b"x")
    assert _da_nap(conn, vid) is False


def test_da_nap_bao_roi_khi_canh_phu_het_video(conn, tmp_path, monkeypatch):
    from autoedit.sotra import hut

    vid = tmp_path / "ref 1.mp4"
    vid.write_bytes(b"x")
    monkeypatch.setattr("autoedit.project.ffprobe_duration", lambda p: 600.0)
    sdb.them_clip(conn, {"id": "ref:t-r1:0-590", "nguon": "ref",
                         "path_local": str(vid), "t0": 0.0, "t1": 590.0})
    conn.commit()
    assert hut._da_nap(conn, vid) is True


def test_cat_do_giua_chung_thi_van_chay_lai(conn, tmp_path, monkeypatch):
    """Job trước bị ngắt ở phút 3/60 — bỏ qua thì 57 phút ref mất luôn."""
    from autoedit.sotra import hut

    vid = tmp_path / "ref 5.mp4"
    vid.write_bytes(b"x")
    monkeypatch.setattr("autoedit.project.ffprobe_duration", lambda p: 3600.0)
    sdb.them_clip(conn, {"id": "ref:t-r5:0-180", "nguon": "ref",
                         "path_local": str(vid), "t0": 0.0, "t1": 180.0})
    conn.commit()
    assert hut._da_nap(conn, vid) is False


def test_nap_lai_tap_da_co_khong_goi_llm_lan_nao(conn, tmp_path, monkeypatch):
    """Cổng chính: chạy lần 2 trên cùng thư mục -> KHÔNG một lượt đọc hình nào.

    Đây là 15 phút GLM mỗi chương mà bản vá phải cắt.
    """
    from autoedit.sotra import canh, doc_canh, hut

    vid = tmp_path / "ref 1.mp4"
    vid.write_bytes(b"x")
    monkeypatch.setattr("autoedit.project.ffprobe_duration", lambda p: 30.0)
    dem = {"n": 0, "cat": 0}

    def gia_cat(v, **k):
        dem["cat"] += 1
        return [canh.Canh(t0=0.0, t1=10.0), canh.Canh(t0=10.0, t1=25.0)]

    monkeypatch.setattr(canh, "cat_canh", gia_cat)
    monkeypatch.setattr(doc_canh, "trich_anh",
                        lambda v, t0, t1, ra, **k: Path(str(ra)))

    def gia_doc(cap, log=None):
        dem["n"] += 1
        return [doc_canh.DocRa(i=j, subject="mountain")
                for j, _ in enumerate(cap, 1)]

    monkeypatch.setattr(doc_canh, "doc_nhieu", gia_doc)

    n1 = hut.nap_ref_tap(conn, tmp_path, tap="LI103", quoc_gia="afghanistan")
    goi_lan_1, cat_lan_1 = dem["n"], dem["cat"]
    n2 = hut.nap_ref_tap(conn, tmp_path, tap="LI103", quoc_gia="afghanistan")

    assert n1 == 2, "lần đầu phải nạp đủ 2 cảnh"
    assert goi_lan_1 >= 1 and cat_lan_1 == 1, "lần đầu phải cắt cảnh + đọc hình"
    assert n2 == 0, "lần hai không được thêm cảnh nào"
    assert dem["n"] == goi_lan_1, "lần hai KHÔNG được gọi đọc hình lần nào nữa"
    # Tầng 1: bỏ qua TRƯỚC cả bước cắt cảnh. Thiếu nó thì ffmpeg vẫn quét lại
    # 153 phút ref mỗi lần — 6 phút mỗi chương, chỉ là không lộ ra hoá đơn GLM.
    assert dem["cat"] == cat_lan_1, "lần hai KHÔNG được cắt cảnh lại"
