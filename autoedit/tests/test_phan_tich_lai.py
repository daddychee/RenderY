r"""PHÂN TÍCH LẠI CHƯƠNG ĐÃ CÓ HỢP ĐỒNG — phải có cửa chặn (user duyệt 12/09).

Vì sao cần: câu lệnh 4 lớp vừa sửa theo nhóm ngách (việc 3) chỉ chạy lúc PHÂN
TÍCH. `⟳ Đổ lại khay` dùng LỚP ĐÃ LƯU và không gọi LLM, nên chương cũ vẫn giữ
`neo=true` của prompt cũ. Mà nút "Phân tích chương này" chỉ hiện khi chương CHƯA
có hợp đồng -> SH010/SH019 không có đường nào hưởng bản sửa.

Vì sao phải chặn: phân tích lại ghi đè hợp đồng, mất sạch phần chỉnh tay ở pha 2.
Đo thật 12/09: SH010 c1–c5/e **0 chỗ chỉnh tay** (phân tích lại không mất gì),
nhưng SH010/h có **4 miếng** và SH019/h có **10 khối + 13 miếng** — mất là mất
công thật của người dựng.
"""

from __future__ import annotations

import json

import pytest


def _hd(nguoi_sua_khoi=0, nguoi_sua_mieng=0, nguoi_tao="bot"):
    khoi = [{"v0": 0, "v1": 3, "tho": 0.5, "L1": ["a"], "uv": [], "chon": -1}
            for _ in range(3)]
    hinh = [{"khoi_goc": i, "t0": i * 3.0, "dur": 3.0, "uv": [], "chon": -1}
            for i in range(3)]
    for i in range(nguoi_sua_khoi):
        khoi[i]["nguoi_sua"] = True
    for i in range(nguoi_sua_mieng):
        hinh[i]["nguoi_sua"] = True
    return {"ma_tap": "SH010", "dia_danh": "", "nguoi_tao": nguoi_tao,
            "trang_thai": "pha2", "khoi": khoi, "hinh": hinh}


@pytest.fixture()
def may_chu(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.offline import runner as orun
    from autoedit.sotra import db as sdb
    from autoedit.web import server

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    # KHÔNG chạy phân tích thật trong test (tốn LLM + ffmpeg)
    monkeypatch.setattr(orun, "phan_tich",
                        lambda d, **k: {"dong_kiem": True, "khoi": [], "hinh": []})
    d = tmp_path / "projects" / "c9-test"
    d.mkdir(parents=True)
    monkeypatch.setattr(server, "PROJECTS_DIR", d.parent)
    return TestClient(server.app, client=("127.0.0.1", 51000)), d


def _dau(user="bot", vai="manager"):
    return {"X-Forwarded-Host": "crm.local", "X-Remote-User": user,
            "X-Remote-Role": vai}


def _ghi(d, hd):
    (d / "offline.json").write_text(json.dumps(hd, ensure_ascii=False),
                                    encoding="utf-8")


# ─────────────────────────── cửa chặn ───────────────────────────

def test_chua_co_hop_dong_thi_phan_tich_nhu_cu(may_chu):
    tc, d = may_chu
    r = tc.post(f"/api/offline/{d.name}/phan-tich", json={}, headers=_dau())
    assert r.status_code == 200, r.text


def test_co_hop_dong_KHONG_chinh_tay_thi_cho_qua(may_chu):
    """SH010 c1–c5/e: 0 chỗ chỉnh tay -> phân tích lại không mất gì."""
    tc, d = may_chu
    _ghi(d, _hd())
    r = tc.post(f"/api/offline/{d.name}/phan-tich", json={}, headers=_dau())
    assert r.status_code == 200, r.text


def test_CO_chinh_tay_thi_CHAN_va_noi_ro_so_cho(may_chu):
    tc, d = may_chu
    _ghi(d, _hd(nguoi_sua_khoi=2, nguoi_sua_mieng=3))
    r = tc.post(f"/api/offline/{d.name}/phan-tich", json={}, headers=_dau())
    assert r.status_code == 409, r.text
    ct = r.json()["detail"]
    assert "2" in ct and "3" in ct, f"phải nói rõ mất bao nhiêu: {ct}"


def test_xac_nhan_thi_van_chay(may_chu):
    tc, d = may_chu
    _ghi(d, _hd(nguoi_sua_khoi=2, nguoi_sua_mieng=3))
    r = tc.post(f"/api/offline/{d.name}/phan-tich",
                json={"xoa_chinh_tay": True}, headers=_dau())
    assert r.status_code == 200, r.text


def test_khong_phai_chu_sequence_thi_KHONG_duoc_phan_tich_lai(may_chu):
    """Cùng luật với mọi đường sửa khác — chứ không phải cửa mới."""
    tc, d = may_chu
    _ghi(d, _hd(nguoi_tao="thanhdn"))
    r = tc.post(f"/api/offline/{d.name}/phan-tich", json={},
                headers=_dau("haint", "viewer"))
    assert r.status_code == 403, r.text


# ─────────────────────────── giao diện ───────────────────────────

def test_giao_dien_co_nut_phan_tich_lai():
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "ofPhanTichLai()" in h, "chưa có nút phân tích lại"
    assert "xoa_chinh_tay" in h, "nút chưa gửi cờ xác nhận"


def test_giao_dien_hoi_truoc_khi_xoa_cong_chinh_tay():
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    i = h.index("async function ofPhanTichLai")
    than = h[i:i + 1200]
    assert "confirm(" in than, "xoá công người dựng mà không hỏi"
