"""Xuất timeline: máy chủ CÓ trạng thái nhưng không lộ ra đúng khoá (09/09).

Nhân sự báo "xuất timeline bị lỗi". Đo trên log production: **không có lỗi
nào** — cả hai lượt xuất C3 đều chạy xong, draft `OFF_c3-20260907-050623` ra
với 182 material. Thứ tự lượt gọi trong tiến trình: `200, 409, 409, 409, 409,
200, 409` — tức người dùng bấm Export, không thấy gì, bấm lại 4 lần.

Gốc: nút Export CÓ vòng hỏi mỗi 8s, nhưng nó đọc `d.tt` — trạng thái của khoá
PHÂN TÍCH (`project_id`) — trong khi lượt Online lưu ở khoá KHÁC
(`project_id:thaymau`). Đọc nhầm khoá nên vòng hỏi không bao giờ thấy gì, màn
hình im lặng, và hộp thoại 409 lại mở đầu bằng chữ "Lỗi" (BH5: im lặng còn tệ
hơn báo lỗi — ở đây là im lặng CỘNG một chữ "Lỗi" đặt sai chỗ).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def may_chu(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.sotra import db as sdb
    from autoedit.web import server

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.setattr(server, "ROOT", tmp_path)
    d = tmp_path / "projects" / "c3-test"
    d.mkdir(parents=True)
    (d / "offline.json").write_text(json.dumps({
        "ma_tap": "LI103", "trang_thai": "khoa", "nguoi_tao": "",
        "khoi": [{"v0": 0, "v1": 3, "uv": [], "chon": -1}],
        "hinh": [{"t0": 0.0, "dur": 3.0, "khoi_goc": 0, "uv": [], "chon": -1}],
    }), encoding="utf-8")
    monkeypatch.setattr(server, "PROJECTS_DIR", d.parent)
    server._offline_dang.clear()
    return TestClient(server.app), d.name


def test_doc_hop_dong_lo_ra_trang_thai_luot_ONLINE(may_chu):
    """Vòng hỏi của nút Export phải có chỗ mà nhìn."""
    tc, pid = may_chu
    r = tc.get(f"/api/offline/{pid}")
    assert r.status_code == 200, r.text
    assert "tt_online" in r.json(), "hợp đồng không lộ trạng thái lượt Online"


def test_dang_chay_thi_tt_online_bao_dang(may_chu):
    from autoedit.web import server

    tc, pid = may_chu
    server._offline_dang[f"{pid}:thaymau"] = {"tt": "dang", "ghi_chu": "miếng 12/46"}
    d = tc.get(f"/api/offline/{pid}").json()
    assert d["tt_online"]["tt"] == "dang"
    assert "12/46" in d["tt_online"]["ghi_chu"], "không thấy tiến độ"


def test_bam_lai_khi_dang_chay_KHONG_phai_loi(may_chu):
    """409 phải nói ĐANG CHẠY TỚI ĐÂU, đừng để người dùng tưởng hỏng."""
    from autoedit.web import server

    tc, pid = may_chu
    server._offline_dang[f"{pid}:thaymau"] = {"tt": "dang", "ghi_chu": "miếng 12/46"}
    r = tc.post(f"/api/offline/{pid}/thay-mau")
    assert r.status_code == 409
    chi = r.json()["detail"]
    assert "12/46" in chi, f"409 không kèm tiến độ: {chi!r}"
    assert not chi.lower().startswith("lỗi"), "câu 409 vẫn mở đầu bằng «Lỗi»"


def test_tien_do_tung_mieng_duoc_ghi_vao_trang_thai(may_chu, monkeypatch):
    """`thay_mau` in ra "miếng n/m" qua log — trạng thái phải bám theo, nếu
    không thì vòng hỏi có nhìn cũng chỉ thấy một câu đứng yên."""
    import time

    from autoedit.web import server

    tc, pid = may_chu
    thay = []

    def gia(d, log=None, **k):
        for i in (1, 2, 3):
            log(f"thay-mau: miếng {i}/3 -> h{i:02d}.mp4")
            thay.append(dict(server._offline_dang.get(f"{pid}:thaymau", {})))
        return {"draft": str(d / "OFF_x"), "mieng_co_hinh": 3, "tong_mieng": 3,
                "tong_khoi_voice": 1, "canh_bao": []}

    monkeypatch.setattr("autoedit.offline.thay_mau.thay_mau", gia)
    assert tc.post(f"/api/offline/{pid}/thay-mau").status_code == 200
    het = time.time() + 15
    while time.time() < het and server._offline_dang.get(f"{pid}:thaymau", {}).get("tt") == "dang":
        time.sleep(0.2)
    assert any("2/3" in (x.get("ghi_chu") or "") for x in thay), \
        f"trạng thái không bám theo tiến độ: {thay}"
    assert server._offline_dang[f"{pid}:thaymau"]["tt"] == "xong"


def test_giao_dien_doc_dung_khoa_va_khoa_nut():
    """UI phải đọc `tt_online` (không phải `d.tt`) và VÔ HIỆU nút khi đang chạy
    — để người dùng khỏi bấm rồi nhận hộp thoại."""
    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "tt_online" in h, "UI vẫn hỏi nhầm khoá"
    i = h.index("/thay-mau'")
    quanh = h[max(0, i - 900):i + 1500]
    assert "disabled" in quanh, "nút Export không bị khoá trong lúc chạy"
