r"""Nút "⟳ Đổ lại khay" KHÔNG được làm mất hình (user duyệt 11/09).

Đo thật trên 14 chương LI106 (bản nháp, không ghi): bấm nút thì **31 miếng
đang có hình thành trống** — timeline thủng. Ba nguyên nhân:

| Miếng | Vì sao |
|---|---|
| 10 | khối ĐẦU: `(i or -1)` ra -1 khi `khoi_goc == 0` -> bị bỏ qua |
| 10 | miếng CHẢY TIẾP: bị xoá lựa chọn rồi `_chon_lai_ho_may` bỏ qua |
| 11 | miếng anh em trong khối NGƯỜI sửa: bị xoá theo, không ai chọn lại |

Và chế độ GIỮ HÌNH (user chốt "Hải B" 11/09): chương đã KHOÁ SỔ là chương
người đã duyệt — chỉ bổ sung khay (để ref nạp muộn như ref 3/4/5 LI106 hiện
ra), KHÔNG chọn lại khối nào. Máy chọn lại 10–32 khối/chương là phá công đã duyệt.
"""

from __future__ import annotations

import pytest

from autoedit.offline import dung
from autoedit.sotra import db as sdb
from autoedit.sotra.tag7 import tag_tu_tieu_de


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    for i in range(4):
        ten = f"kabul market crowd {i}"
        sdb.them_clip(c, {"id": f"ref:LI103-r:{i}", "nguon": "ref", "tap": "LI103",
                          "tieu_de": ten, "path_local": "ref 1.mp4",
                          "t0": 0.0, "t1": 8.0, **tag_tu_tieu_de(ten)})
    c.commit()
    yield c
    c.close()


def _cu(ten):
    """Clip đang nằm trên timeline — KHÔNG có trong kết quả tra mới."""
    return {"id": f"ref:LI103-cu:{ten}", "nguon": "ref", "tieu_de": ten,
            "lop": "L1", "diem": 9.0, "t0": 0.0, "t1": 8.0}


def _khoi(v0, v1, clip=None, **them):
    return {"v0": v0, "v1": v1, "tho": 0.5, "L1": ["market"], "L2": [], "L3": [],
            "uv": [clip] if clip else [], "chon": 0 if clip else -1, **them}


def _mieng(kg, clip, **them):
    return {"khoi_goc": kg, "uv": [clip], "chon": 0, **them}


def _id(x):
    uv, c = x.get("uv") or [], x.get("chon", -1)
    return uv[c]["id"] if 0 <= c < len(uv) else None


# ───────────── chế độ thường (QĐ6: máy chọn lại khối máy) ─────────────

def test_mieng_KHOI_DAU_duoc_chon_lai_nhu_moi_khoi_may(conn):
    a, b = _cu("a"), _cu("b")
    hd = {"ma_tap": "LI103", "khoi": [_khoi(0, 3, a), _khoi(3, 6, b)],
          "hinh": [_mieng(0, a), _mieng(1, b)]}
    dung.do_lai_khay(hd, conn)
    k0, k1 = hd["khoi"]
    h0, h1 = hd["hinh"]
    assert _id(h0) is not None, "miếng khối đầu mất hình"
    assert _id(h0) == _id(k0)          # dội đúng lựa chọn mới của khối 0
    assert _id(h1) == _id(k1)          # khối máy khác vẫn như cũ (không hồi quy)


def test_mieng_CHAY_TIEP_khong_mat_hinh(conn):
    a, b = _cu("a"), _cu("b")
    hd = {"ma_tap": "LI103", "khoi": [_khoi(0, 3, a), _khoi(3, 6, b)],
          "hinh": [_mieng(0, a), _mieng(1, a, noi_tiep=True)]}
    dung.do_lai_khay(hd, conn)
    assert _id(hd["hinh"][1]) == a["id"], "miếng chảy tiếp: không đụng -> giữ hình cũ"


def test_mieng_anh_em_trong_khoi_NGUOI_SUA_giu_hinh(conn):
    x, y = _cu("x"), _cu("y")
    k = _khoi(0, 6, x)
    k["uv"] = [x, y]
    hd = {"ma_tap": "LI103", "khoi": [k],
          "hinh": [_mieng(0, x, nguoi_sua=True), {"khoi_goc": 0, "uv": [x, y], "chon": 1}]}
    dung.do_lai_khay(hd, conn)
    assert _id(hd["hinh"][0]) == x["id"]
    assert _id(hd["hinh"][1]) == y["id"], "miếng anh em bị xoá hình theo"


def test_KHONG_MIENG_NAO_mat_hinh(conn):
    """Lưới an toàn: miếng đang có hình -> sau khi bấm vẫn phải có hình."""
    a, b, c = _cu("a"), _cu("b"), _cu("c")
    hd = {"ma_tap": "LI103",
          "khoi": [_khoi(0, 3, a), _khoi(3, 6, b), _khoi(6, 9, c, nguoi_sua=True)],
          "hinh": [_mieng(0, a), _mieng(1, a, noi_tiep=True), _mieng(1, b),
                   _mieng(2, c, nguoi_sua=True), _mieng(2, b)]}
    dung.do_lai_khay(hd, conn)
    trong = [i for i, h in enumerate(hd["hinh"]) if _id(h) is None]
    assert trong == []


# ───────────── chế độ GIỮ HÌNH (chương đã khoá sổ) ─────────────

def test_giu_chon_GIU_NGUYEN_moi_hinh_dang_dung(conn):
    a, b = _cu("a"), _cu("b")
    hd = {"ma_tap": "LI103", "khoi": [_khoi(0, 3, a), _khoi(3, 6, b)],
          "hinh": [_mieng(0, a), _mieng(1, b)]}
    may_doi: list = []
    dung.do_lai_khay(hd, conn, may_doi=may_doi, giu_chon=True)
    assert [_id(k) for k in hd["khoi"]] == [a["id"], b["id"]]
    assert [_id(h) for h in hd["hinh"]] == [a["id"], b["id"]]
    assert may_doi == []                               # không khối nào bị chọn lại


def test_giu_chon_VAN_bo_sung_khay(conn):
    a = _cu("a")
    hd = {"ma_tap": "LI103", "khoi": [_khoi(0, 3, a)], "hinh": [_mieng(0, a)]}
    dung.do_lai_khay(hd, conn, giu_chon=True)
    moi = {u["id"] for u in hd["hinh"][0]["uv"]}
    assert any(i.startswith("ref:LI103-r:") for i in moi), "khay miếng chưa có ref mới"
    assert any(u["id"].startswith("ref:LI103-r:") for u in hd["khoi"][0]["uv"])


# ───────────── máy chủ: chương KHOÁ SỔ thì bấm nút là giữ hình ─────────────

def _chuong(tmp_path, trang_thai):
    import json
    a, b = _cu("a"), _cu("b")
    d = tmp_path / "projects" / f"c9-{trang_thai}"
    d.mkdir(parents=True)
    hd = {"ma_tap": "LI103", "trang_thai": trang_thai,
          "khoi": [_khoi(0, 3, a), _khoi(3, 6, b)],
          "hinh": [_mieng(0, a, t0=0.0, dur=3.0), _mieng(1, b, t0=3.0, dur=3.0)]}
    (d / "offline.json").write_text(json.dumps(hd, ensure_ascii=False), encoding="utf-8")
    return d, a, b


def test_api_chuong_KHOA_SO_thi_giu_nguyen_hinh(conn, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.web import server

    d, a, b = _chuong(tmp_path, "khoa")
    monkeypatch.setattr(server, "PROJECTS_DIR", d.parent)
    r = TestClient(server.app).post(f"/api/offline/{d.name}/do-lai-khay")
    assert r.status_code == 200
    j = r.json()
    assert j["so_may_doi"] == 0
    assert [_id(h) for h in j["hop_dong"]["hinh"]] == [a["id"], b["id"]]


def test_api_chuong_CHUA_KHOA_van_chon_lai_khoi_may(conn, tmp_path, monkeypatch):
    """QĐ6 giữ nguyên cho chương đang dựng (c2 LI103 của Thành)."""
    from fastapi.testclient import TestClient

    from autoedit.web import server

    d, a, b = _chuong(tmp_path, "pha2")
    monkeypatch.setattr(server, "PROJECTS_DIR", d.parent)
    j = TestClient(server.app).post(f"/api/offline/{d.name}/do-lai-khay").json()
    assert j["so_may_doi"] == 2
    assert all(_id(h) for h in j["hop_dong"]["hinh"])     # không miếng nào trống
