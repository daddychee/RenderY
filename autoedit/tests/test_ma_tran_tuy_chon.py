"""Rà cuối (08/09) — MỌI tuỳ chọn phải đi TRỌN ĐƯỜNG và các tuỳ chọn phải
khớp nhau khi kết hợp.

Đây là họ nhà lỗi PH1: tham số khai ở form nhưng rớt giữa đường và **im lặng**
— chương vẫn dựng, chỉ là dựng bằng mặc định. Không có test bắt được thì không
ai biết. Rà theo hai trục:

  (1) DỌC   — form -> JobRequest -> opts hàng đợi -> cờ dòng lệnh `make`
  (2) NGANG — ma trận kiểu chạy × vị trí chương × độ dày khay
"""

from __future__ import annotations

import pytest

from autoedit.offline.runner import du_khay_cho_auto, tinh_dong_kiem

# Mọi tuỳ chọn form gửi lên, kèm cờ dòng lệnh mà worker PHẢI sinh ra.
# Sửa form mà quên worker thì bảng này đỏ.
TUY_CHON = [
    ("niche", "life-in", ["--channel", "life-in"]),
    ("align_backend", "srt", ["--align-backend", "srt"]),
    ("no_sub", True, ["--no-sub"]),
    ("aigen", True, ["--aigen"]),
    ("phuong_an", "tu_quay", ["--phuong-an", "tu_quay"]),
    ("kenh_ref", "godoc", ["--kenh-ref", "godoc"]),
    ("avd_phut", 8.0, ["--avd-phut", "8.0"]),
    ("dia_danh", "afghanistan", ["--dia-danh", "afghanistan"]),
    ("uu_tien_nguon", "ref", ["--uu-tien-nguon", "ref"]),
    ("kieu_chay", "auto", ["--kieu-chay", "auto"]),
    ("chi_chuan_bi", True, ["--chi-chuan-bi"]),
]


def _co_lenh(opts: dict) -> list[str]:
    """Gọi thẳng chỗ thật trong worker — không chép lại logic sang test."""
    from autoedit.web.worker import co_lenh

    return co_lenh(opts)


@pytest.mark.parametrize("ten,gia_tri,co", TUY_CHON, ids=[t[0] for t in TUY_CHON])
def test_tung_tuy_chon_ra_toi_dong_lenh(ten, gia_tri, co):
    """Bật MỘT tuỳ chọn -> đúng cờ đó xuất hiện."""
    extra = _co_lenh({ten: gia_tri})
    for c in co:
        assert c in extra, f"tuỳ chọn «{ten}» rớt giữa đường: {extra}"


def test_bat_HET_tuy_chon_thi_ra_HET_co():
    """Bật tất cả cùng lúc — không tuỳ chọn nào nuốt tuỳ chọn nào."""
    extra = _co_lenh({t: v for t, v, _ in TUY_CHON})
    for _, _, co in TUY_CHON:
        for c in co:
            assert c in extra, f"thiếu {c} khi bật hết: {extra}"


def test_khong_bat_gi_thi_khong_ra_co_lac():
    """opts rỗng -> KHÔNG cờ nào. Cờ mọc ra từ hư không nghĩa là chương chạy
    bằng thứ người dùng không khai."""
    extra = _co_lenh({})
    assert extra == [], f"cờ mọc ra từ opts rỗng: {extra}"


def test_JobRequest_nhan_du_moi_tuy_chon_form_gui():
    """Form gửi khoá lạ thì Pydantic bỏ im lặng — đối chiếu tận nơi."""
    from autoedit.web.server import JobRequest

    co = set(JobRequest.model_fields)
    for ten, _, _ in TUY_CHON:
        assert ten in co, f"JobRequest không có trường «{ten}»"


# ---------------------------------------------------------------- ma trận
# (kieu_chay, avd_s, mo_dau_tap_s) -> chương này người duyệt?
MA_TRAN = [
    ("manual", 360, 0,    True,  "manual: mọi chương đều duyệt"),
    ("manual", 360, 9999, True,  "manual: kể cả chương cuối"),
    ("manual", 0,   0,    True,  "manual: không cần mốc AVD"),
    ("auto",   360, 0,    False, "auto: mọi chương tự chạy"),
    ("auto",   0,   0,    False, "auto: không cần mốc AVD"),
    ("avd",    360, 0,    True,  "avd: chương TRƯỚC mốc -> duyệt"),
    ("avd",    360, 359,  True,  "avd: sát trước mốc -> duyệt"),
    ("avd",    360, 360,  False, "avd: ĐÚNG mốc -> tự chạy"),
    ("avd",    360, 400,  False, "avd: sau mốc -> tự chạy"),
    ("avd",    0,   0,    True,  "avd: chưa khai mốc -> duyệt hết (an toàn)"),
    ("",       360, 0,    True,  "rỗng: giữ công thức cũ"),
    ("",       360, 400,  False, "rỗng: giữ công thức cũ"),
]


@pytest.mark.parametrize("kieu,avd,mo_dau,mong,vi_sao", MA_TRAN,
                         ids=[m[4][:28] for m in MA_TRAN])
def test_ma_tran_kieu_chay(kieu, avd, mo_dau, mong, vi_sao):
    assert tinh_dong_kiem(kieu, avd, mo_dau) is mong, vi_sao


# Kiểu chạy × độ dày khay -> chương có thật sự tự chạy không.
# Cổng Auto chỉ được đụng chương ĐANG ĐỊNH tự chạy; chương người duyệt thì
# khay mỏng hay dày cũng vẫn là người duyệt.
KHAY = [
    ("auto",   1.0, False, "auto + khay đầy -> tự chạy"),
    ("auto",   0.6, False, "auto + đúng ngưỡng -> tự chạy"),
    ("auto",   0.5, True,  "auto + khay mỏng -> ĐẨY sang đồng kiểm"),
    ("auto",   0.0, True,  "auto + khay rỗng -> ĐẨY sang đồng kiểm"),
    ("manual", 0.0, True,  "manual + khay rỗng -> vẫn là người duyệt"),
    ("manual", 1.0, True,  "manual + khay đầy -> vẫn là người duyệt"),
]


@pytest.mark.parametrize("kieu,phu,mong,vi_sao", KHAY, ids=[k[3][:30] for k in KHAY])
def test_ma_tran_kieu_chay_x_do_day_khay(kieu, phu, mong, vi_sao):
    n = 10
    uv = [[{"id": "x"}]] * round(n * phu) + [[]] * (n - round(n * phu))
    dong_kiem = tinh_dong_kiem(kieu, 0, 0)
    if not dong_kiem and not du_khay_cho_auto(uv):
        dong_kiem = True
    assert dong_kiem is mong, vi_sao


def test_moi_co_worker_sinh_ra_deu_CO_THAT_tren_CLI():
    """Worker gửi cờ mà `make` không hiểu -> job chết ngay dòng đầu, và lỗi chỉ
    hiện trong log. Đối chiếu với `--help` thật của CLI."""
    import os
    import subprocess
    import sys

    env = {**os.environ, "PYTHONPATH": ".", "PYTHONIOENCODING": "utf-8",
           "PYTHONUTF8": "1"}
    r = subprocess.run([sys.executable, "-m", "autoedit.cli", "make", "--help"],
                       capture_output=True, text=True, env=env, timeout=180)
    assert r.returncode == 0, r.stderr[-400:]
    tro_giup = r.stdout
    co = [c for c in _co_lenh({t: v for t, v, _ in TUY_CHON}) if c.startswith("--")]
    thieu = [c for c in co if c not in tro_giup]
    assert not thieu, f"worker gửi cờ mà `make` không có: {thieu}"


def test_uu_tien_nguon_mac_dinh_ref_co_tac_dung_that(tmp_path, monkeypatch):
    """Form KHÔNG có ô chọn `uu_tien_nguon` — luôn là mặc định "ref" của
    JobRequest. Nếu giá trị đó không được `tra()` hiểu thì mặc định là vô nghĩa
    và không ai biết."""
    from autoedit.sotra import db as sdb
    from autoedit.sotra.tag7 import tag_tu_tieu_de
    from autoedit.sotra.tra import tra

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    conn = sdb.mo()
    try:
        for i in range(6):
            ten = f"kabul market crowd {i}"
            sdb.them_clip(conn, {"id": f"ref:LI103-r:{i}", "nguon": "ref", "tap": "LI103",
                                 "tieu_de": ten, "path_local": "ref 1.mp4",
                                 **tag_tu_tieu_de(ten)})
            sdb.them_clip(conn, {"id": f"pexels:{i}", "nguon": "pexels",
                                 "tieu_de": ten, **tag_tu_tieu_de(ten)})
        conn.commit()
        ra = tra(conn, {"L0": [], "L1": ["market"], "L2": [], "L3": []},
                 so=4, uu_tien_nguon="ref", tap="LI103")
        assert ra, "tra() trả rỗng — không kết luận được gì"
        assert ra[0]["nguon"] == "ref", \
            f"ưu tiên «ref» không có tác dụng: {[c['nguon'] for c in ra]}"
    finally:
        conn.close()


def test_JobRequest_mac_dinh_khop_voi_thu_form_KHONG_gui():
    """Trường form không gửi thì mặc định của JobRequest là thứ CHẠY THẬT —
    nên mặc định đó phải là giá trị hợp lệ, không phải chỗ trống bỏ quên."""
    from autoedit.offline.runner import KIEU_CHAY_HOP_LE
    from autoedit.sotra.db import NGUON_HOP_LE
    from autoedit.web.server import JobRequest

    m = JobRequest(folder="x", dia_danh="tibet")
    assert m.uu_tien_nguon in NGUON_HOP_LE, m.uu_tien_nguon
    assert m.phuong_an in ("stock", "ai", "tu_quay"), m.phuong_an
    assert m.align_backend in ("auto", "srt", "whisper"), m.align_backend
    assert m.chi_chuan_bi is True          # form luôn gửi true, mặc định phải khớp
    assert m.kieu_chay == "" or m.kieu_chay in KIEU_CHAY_HOP_LE


def test_CHI_MOT_nguong_auto_trong_ca_he():
    """Rà cuối 08/09 bắt được: `server.api_offline_phan_tich` giữ rào riêng
    `co_hinh < tong_k * 0.5` trong khi cổng ở runner là 60%. Hai con số cho
    CÙNG một khái niệm, ở hai chỗ — và vì cổng runner chặn trước, nhánh 50%
    thành code chết mà vẫn đọc như thể đang bảo vệ cái gì đó (BH4).
    """
    import re
    from pathlib import Path

    from autoedit.offline.runner import NGUONG_AUTO

    src = Path("autoedit/web/server.py").read_text(encoding="utf-8")
    so_la = re.findall(r"co_hinh\s*<\s*tong_k\s*\*\s*([0-9.]+)", src)
    assert not so_la, f"máy chủ còn ngưỡng auto riêng: {so_la} (runner={NGUONG_AUTO})"
    assert "du_khay_cho_auto" in src, "máy chủ phải dùng chung hàm cổng của runner"
