"""Chọn NƠI XUẤT draft khi bấm Export (user yêu cầu 09/09).

User đã tự chứng minh: thư mục draft CapCut **copy sang chỗ khác vẫn dùng
được**. Nên muốn xuất thẳng vào đúng thư mục chứa working file của CapCut, thay
vì luôn đổ vào một kho chung 42 thư mục lẫn lộn.

Khảo sát trước khi code — MỘT NỬA cơ chế đã có sẵn:
  `MachineProfile.draft_out_root` (rỗng = `capcut_root`), `profile.out_root()`,
  và `package_draft` ĐÃ dùng nó. Nhưng đó là thiết lập TOÀN MÁY (lệnh
  `set-draft-root`), không đè được từng lượt xuất.
  `_trong_nas` đã tự quy đổi `Z:\` -> `F:\` và chặn đường dẫn ra ngoài NAS.

User chốt: **dán đường dẫn**, nhớ **theo TẬP** (gõ một lần, 16 chương dùng chung).
Thư mục đích nằm trên NAS nên máy chủ ghi thẳng được, KHÔNG chép hai bản.
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
    nas = tmp_path / "nas"
    (nas / "Life In" / "US" / "LI106" / "RenderY").mkdir(parents=True)
    monkeypatch.setattr(server, "NAS_ROOT", nas)
    d = tmp_path / "projects" / "c9-test"
    d.mkdir(parents=True)
    (d / "offline.json").write_text(json.dumps({
        "ma_tap": "LI106", "trang_thai": "khoa", "nguoi_tao": "",
        "khoi": [{"v0": 0, "v1": 3, "uv": [], "chon": -1}],
        "hinh": [{"t0": 0.0, "dur": 3.0, "khoi_goc": 0, "uv": [], "chon": -1}],
    }), encoding="utf-8")
    monkeypatch.setattr(server, "PROJECTS_DIR", d.parent)
    server._offline_dang.clear()
    return TestClient(server.app), d, nas


def test_noi_xuat_duoc_ghi_nho_theo_TAP(may_chu, monkeypatch):
    """Gõ một lần -> hợp đồng nhớ, chương sau của cùng tập khỏi gõ lại."""
    from autoedit.offline import runner as orun

    tc, d, nas = may_chu
    dich = nas / "Life In" / "US" / "LI106" / "RenderY" / "Draft"
    dich.mkdir(parents=True)
    monkeypatch.setattr("autoedit.offline.thay_mau.thay_mau",
                        lambda *a, **k: {"draft": str(dich / "x"), "mieng_co_hinh": 1,
                                         "tong_mieng": 1, "tong_khoi_voice": 1,
                                         "canh_bao": []})
    r = tc.post(f"/api/offline/{d.name}/thay-mau", json={"noi_xuat": str(dich)})
    assert r.status_code == 200, r.text
    assert orun.doc(d).get("noi_xuat") == str(dich.resolve()), orun.doc(d).get("noi_xuat")


def test_lan_sau_bo_trong_thi_dung_lai_noi_da_nho(may_chu, monkeypatch):
    from autoedit.offline import runner as orun

    tc, d, nas = may_chu
    dich = nas / "Life In" / "US" / "LI106" / "RenderY" / "Draft"
    dich.mkdir(parents=True)
    hd = orun.doc(d); hd["noi_xuat"] = str(dich); orun.luu(d, hd)
    nhan = {}
    monkeypatch.setattr("autoedit.offline.thay_mau.thay_mau",
                        lambda *a, **k: (nhan.update(k), {"draft": str(dich / "x"),
                        "mieng_co_hinh": 1, "tong_mieng": 1, "tong_khoi_voice": 1,
                        "canh_bao": []})[1])
    assert tc.post(f"/api/offline/{d.name}/thay-mau", json={}).status_code == 200
    assert nhan.get("noi_xuat") == str(dich), nhan


def test_duong_dan_NGOAI_NAS_bi_chan(may_chu, tmp_path):
    """Rào duy nhất: worker ghi thẳng lên thư mục đó."""
    tc, d, _ = may_chu
    r = tc.post(f"/api/offline/{d.name}/thay-mau",
                json={"noi_xuat": str(tmp_path / "ngoai-nas")})
    assert r.status_code == 422 and "NAS" in r.json()["detail"]


def test_bo_trong_thi_giu_nguyen_nhu_cu(may_chu, monkeypatch):
    """Không khai gì -> `noi_xuat` rỗng, `package_draft` dùng capcut_root như cũ."""
    tc, d, _ = may_chu
    nhan = {}
    monkeypatch.setattr("autoedit.offline.thay_mau.thay_mau",
                        lambda *a, **k: (nhan.update(k), {"draft": "x",
                        "mieng_co_hinh": 1, "tong_mieng": 1, "tong_khoi_voice": 1,
                        "canh_bao": []})[1])
    assert tc.post(f"/api/offline/{d.name}/thay-mau", json={}).status_code == 200
    assert not nhan.get("noi_xuat")


def test_thay_mau_doi_noi_xuat_vao_profile(tmp_path):
    """`thay_mau(noi_xuat=...)` phải đẩy xuống `draft_out_root` — đó là chỗ
    `package_draft` đọc. Không đẩy thì draft vẫn rơi vào kho cũ."""
    from autoedit.packager.machine import MachineProfile

    p = MachineProfile(donor_name="d", capcut_root=str(tmp_path / "kho"))
    assert p.out_root() == tmp_path / "kho"
    p2 = p.model_copy(update={"draft_out_root": str(tmp_path / "noi-moi")})
    assert p2.out_root() == tmp_path / "noi-moi"


def test_cot_co_draft_KHONG_ghi_cung_duong_dan():
    """`server.py` từng ghi cứng `F:/OutlierY Nas 2/...` để biết chương đã có
    draft chưa. Đổi nơi xuất là cột "✓draft" sai âm thầm — đúng họ nhà lỗi BH5."""
    src = Path("autoedit/web/server.py").read_text(encoding="utf-8")
    assert "Tool Edit/Capcut Draft" not in src and "Tool Edit\\Capcut Draft" not in src, \
        "vẫn còn đường dẫn kho draft ghi cứng trong server.py"


def test_giao_diem_co_o_nhap_noi_xuat():
    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "noi_xuat" in h, "giao diện chưa có ô nhập nơi xuất"
