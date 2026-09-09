r"""Việc B — bấm Export thì KIỂM MỘT LƯỢT, có clip chết thì CHẶN + tô đỏ.

User chốt 09/09: *"Sau khi ấn export timeline, tool check 1 lượt. Nếu không có
link chết thì export. Nếu có thì báo đã có video hỏng. Cần thay thế. Lúc này
timeline đánh dấu đỏ vào các video đã hết hạn/chết"*.

Vì sao cần: `thay_mau` có sẵn đường lùi (hết ứng viên thì để hở, có warning),
nhưng warning chỉ hiện SAU KHI ráp xong — người dựng chờ vài phút mới biết
miếng của mình hỏng. Kiểm TRƯỚC tốn vài giây và trả về đúng danh sách miếng để
tô đỏ, người dựng thay ngay rồi bấm lại.

Đo thật 09/09 trên 33 chương production: **9 miếng đang chọn clip `link_chet`**.

PHẠM VI (chốt khi bàn): chỉ kiểm miếng ĐANG CHỌN (~30-90/chương), KHÔNG kiểm cả
khay (13.270 ô toàn hệ thống). Dùng `dung.clip_hong` của việc C — một luật, một
chỗ, không viết lại.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from autoedit.offline import thay_mau as mtm


class _KhongDong:
    """Bọc connection, nuốt `close()` — `sqlite3.Connection.close` chỉ đọc nên
    không gán đè được, mà test cần dùng tiếp sau khi server đã đóng."""

    def __init__(self, conn):
        self._c = conn

    def close(self):
        pass

    def __getattr__(self, ten):
        return getattr(self._c, ten)


def _kho(f: Path | None = None):
    """DB nhỏ đúng schema thật.

    `f` (dùng cho test qua TestClient): SQLite **in-memory không qua được luồng
    khác**, mà FastAPI chạy endpoint sync trong threadpool — nên test endpoint
    phải dùng DB FILE, không thì `soat_truoc_pha` nuốt `ProgrammingError` và
    lặng lẽ cho Export qua (bắt được 09/09).
    """
    from autoedit.sotra import db as sdb

    conn = sqlite3.connect(str(f) if f else ":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(sdb._SCHEMA)
    return conn


def _them(conn, cid, nguon="envato", trang_thai="song"):
    conn.execute(
        "INSERT INTO clip(id, nguon, tieu_de, trang_thai) VALUES(?,?,?,?)",
        (cid, nguon, f"clip {cid}", trang_thai))
    conn.commit()


def _hd(*chon_ids):
    """Hợp đồng nhỏ: mỗi miếng một ứng viên đang chọn."""
    return {"khoi": [{"v0": 0.0, "v1": 2.0, "loi": "x"}],
            "hinh": [{"t0": float(i * 2), "dur": 2.0, "khoi_goc": 0, "chon": 0,
                      "uv": [{"id": cid, "nguon": "envato", "tieu_de": f"clip {cid}"}]}
                     for i, cid in enumerate(chon_ids)]}


# ───────────────────────── phần đo: hàm kiểm ─────────────────────────

def test_khay_sach_thi_KHONG_bao_gi():
    conn = _kho()
    _them(conn, "envato:a")
    _them(conn, "envato:b")
    assert mtm.soat_truoc_pha(conn, _hd("envato:a", "envato:b")) == []


def test_bat_dung_MIENG_nao_hong():
    """Trả CHỈ SỐ miếng — UI cần đúng số để tô đỏ đúng chỗ."""
    conn = _kho()
    _them(conn, "envato:a")
    _them(conn, "envato:chet", trang_thai="link_chet")
    _them(conn, "envato:c")
    xau = mtm.soat_truoc_pha(conn, _hd("envato:a", "envato:chet", "envato:c"))
    assert [x["mieng"] for x in xau] == [1], f"phải chỉ đúng miếng 1, được {xau}"


def test_bao_kem_TEN_clip_de_nguoi_dung_biet_thay_gi():
    conn = _kho()
    _them(conn, "envato:chet", trang_thai="link_chet")
    xau = mtm.soat_truoc_pha(conn, _hd("envato:chet"))
    assert xau[0]["id"] == "envato:chet"
    assert "clip envato:chet" in xau[0]["tieu_de"]


def test_clip_KHONG_CO_trong_kho_cung_bi_bat():
    conn = _kho()
    xau = mtm.soat_truoc_pha(conn, _hd("envato:bien_mat"))
    assert len(xau) == 1


def test_mieng_CHUA_CHON_gi_thi_bo_qua():
    """Miếng chưa chọn là việc của placeholder (việc A), không phải của Export."""
    conn = _kho()
    hd = {"khoi": [{"v0": 0.0, "v1": 2.0, "loi": "x"}],
          "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "chon": -1, "uv": []}]}
    assert mtm.soat_truoc_pha(conn, hd) == []


def test_KHONG_kiem_ung_vien_du_bi():
    """Chỉ soát miếng ĐANG CHỌN — dự bị hỏng không cản Export.

    Dự bị chỉ dùng khi cái đang chọn hỏng; chặn vì dự bị là chặn oan.
    """
    conn = _kho()
    _them(conn, "envato:ok")
    _them(conn, "envato:du_bi_chet", trang_thai="link_chet")
    hd = {"khoi": [{"v0": 0.0, "v1": 2.0, "loi": "x"}],
          "hinh": [{"t0": 0.0, "dur": 2.0, "khoi_goc": 0, "chon": 0,
                    "uv": [{"id": "envato:ok", "nguon": "envato", "tieu_de": "ok"},
                           {"id": "envato:du_bi_chet", "nguon": "envato", "tieu_de": "x"}]}]}
    assert mtm.soat_truoc_pha(conn, hd) == []


def test_nhieu_mieng_hong_bao_HET(sorted_ok=True):
    conn = _kho()
    for i in range(5):
        _them(conn, f"envato:{i}", trang_thai="link_chet" if i % 2 else "song")
    xau = mtm.soat_truoc_pha(conn, _hd(*[f"envato:{i}" for i in range(5)]))
    assert [x["mieng"] for x in xau] == [1, 3]


def test_moi_nguon_deu_bi_soat():
    """Không riêng envato — pexels/pixabay/ref chết cũng phải chặn."""
    conn = _kho()
    for ng in ("pexels", "pixabay", "ref"):
        _them(conn, f"{ng}:chet", nguon=ng, trang_thai="link_chet")
    hd = {"khoi": [{"v0": 0.0, "v1": 2.0, "loi": "x"}],
          "hinh": [{"t0": float(i * 2), "dur": 2.0, "khoi_goc": 0, "chon": 0,
                    "uv": [{"id": f"{ng}:chet", "nguon": ng, "tieu_de": ng,
                            "t0": 1.0, "t1": 5.0}]}
                   for i, ng in enumerate(("pexels", "pixabay", "ref"))]}
    assert len(mtm.soat_truoc_pha(conn, hd)) == 3


# ───────────────────────── phần cổng: server chặn ─────────────────────────

def test_endpoint_CHAN_va_tra_danh_sach(tmp_path, monkeypatch):
    """POST thay-mau khi có clip chết -> 409 + danh sách miếng, KHÔNG chạy ráp."""
    from fastapi.testclient import TestClient

    from autoedit.web import server as sv

    d = tmp_path / "c1-20260101-000000"
    (d / "assets_offline").mkdir(parents=True)
    (d / "project.json").write_text(json.dumps(
        {"project_id": d.name, "inputs": {}}), encoding="utf-8")
    (d / "offline.json").write_text(json.dumps(
        {**_hd("envato:chet"), "trang_thai": "khoa"}), encoding="utf-8")

    conn = _kho(tmp_path / "kho.db")
    _them(conn, "envato:chet", trang_thai="link_chet")
    # server đóng connection sau khi soát; test còn dùng tiếp -> bọc để nuốt close
    monkeypatch.setattr("autoedit.sotra.db.mo", lambda *a, **k: _KhongDong(conn))
    monkeypatch.setattr(sv, "_pdir_offline", lambda pid: d)
    monkeypatch.setattr(sv, "_require_auth", lambda r: None)

    da_chay = []
    monkeypatch.setattr("autoedit.offline.thay_mau.thay_mau",
                        lambda *a, **k: da_chay.append(1))

    r = TestClient(sv.app).post(f"/api/offline/{d.name}/thay-mau", json={})
    assert r.status_code == 409, f"phải chặn, được {r.status_code}: {r.text[:200]}"
    body = r.json()
    ds = body.get("detail") if isinstance(body.get("detail"), dict) else body
    assert ds.get("hong"), f"thiếu danh sách miếng hỏng: {body}"
    assert ds["hong"][0]["mieng"] == 0
    assert not da_chay, "đã chặn mà vẫn chạy ráp draft"


def test_endpoint_khay_sach_thi_CHO_QUA(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.web import server as sv

    d = tmp_path / "c2-20260101-000000"
    (d / "assets_offline").mkdir(parents=True)
    (d / "project.json").write_text(json.dumps(
        {"project_id": d.name, "inputs": {}}), encoding="utf-8")
    (d / "offline.json").write_text(json.dumps(
        {**_hd("envato:ok"), "trang_thai": "khoa"}), encoding="utf-8")

    conn = _kho(tmp_path / "kho.db")
    _them(conn, "envato:ok")
    # server đóng connection sau khi soát; test còn dùng tiếp -> bọc để nuốt close
    monkeypatch.setattr("autoedit.sotra.db.mo", lambda *a, **k: _KhongDong(conn))
    monkeypatch.setattr(sv, "_pdir_offline", lambda pid: d)
    monkeypatch.setattr(sv, "_require_auth", lambda r: None)
    monkeypatch.setattr("autoedit.offline.thay_mau.thay_mau",
                        lambda *a, **k: {"draft": str(d / "draft"), "mieng_co_hinh": 1,
                                         "tong_mieng": 1, "canh_bao": []})

    r = TestClient(sv.app).post(f"/api/offline/{d.name}/thay-mau", json={})
    assert r.status_code == 200, f"khay sạch mà bị chặn: {r.text[:200]}"


def test_soat_hong_KHONG_duoc_giet_export(tmp_path, monkeypatch):
    """Soát là bước PHỤ. DB hỏng thì cho Export chạy, không chặn oan."""
    conn = _kho()

    def _no(*a, **k):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr("autoedit.offline.dung.clip_hong", _no)
    assert mtm.soat_truoc_pha(conn, _hd("envato:x")) == []


# ───────────────────────── phần giao diện ─────────────────────────

def test_UI_co_bien_giu_danh_sach_hong():
    """Chỉ kiểm DÂY NỐI có tồn tại. Việc tô đỏ có ĂN THẬT hay không do
    `test_to_do_trinh_duyet.py` kiểm bằng Chrome — bản cũ của test này chỉ tìm
    chuỗi `.of-mieng.hong` trong file nên báo xanh trong khi user nhìn màn hình
    KHÔNG thấy viền đỏ nào (CSS bị luật `.tho` đứng sau đè)."""
    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "OF_HONG" in h, "thiếu biến giữ danh sách miếng hỏng"
    assert "OF_HONG.has(j) ? ' hong'" in h, "khai biến nhưng không gắn lớp vào miếng"
    assert "OF_HONG.delete" in h, "không gỡ dấu đỏ khi người dựng đổi clip"


def test_UI_moi_onclick_deu_co_ham_that():
    """Bài học 08/09: gọi `toast()` không tồn tại — hỏng âm thầm."""
    import re

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    # `if`/`return`... là TỪ KHOÁ JS, không phải lời gọi hàm (`onclick="if(...)"`)
    TU_KHOA = {"if", "for", "while", "switch", "return", "typeof", "delete"}
    goi = set(re.findall(r'onclick="(\w+)\(', h)) - TU_KHOA
    co = set(re.findall(r"function\s+(\w+)\s*\(", h))
    co |= set(re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(", h))
    thieu = goi - co
    assert not thieu, f"onclick gọi hàm không tồn tại: {sorted(thieu)}"
