r"""Hai luật user chốt 09/09 sau khi bản chặn Export lọt lỗi.

**1. Soát thấy clip chết thì DỪNG NGAY, không quét hết.**
Người dựng phải thay clip rồi bấm lại, nên biết một miếng hỏng là đủ để chặn.
Quét hết 46 miếng chỉ tốn thời gian mà kết quả không đổi — vẫn là "chặn".
(Vẫn trả về miếng tìm được để UI tô đỏ và nhảy tới.)

**2. Timeline chưa duyệt thì KHÔNG tải video nào.**
`_xep_tai_ban_sach` đang chạy ngay khi người dựng chọn clip (server.py:1099 và
:1296) — tức mỗi lần bấm thử một clip là xếp hàng tải bản sạch Envato.

Đo thật 09/09 trên production:
  - 25 chương đã khoá sổ  ->  77 miếng envato
  - **8 chương CHƯA duyệt -> 17 miếng envato đang tải sớm**
  - bản sạch đã tải: **104 file, 44,5 GB** (trung bình 428 MB/clip)

Người dựng đổi clip vài lần trong lúc dò là tải vài GB cho những clip cuối cùng
không dùng. Chỉ tải khi chương đã KHOÁ SỔ (`trang_thai == "khoa"`).
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from autoedit.offline import thay_mau as mtm


def _kho():
    from autoedit.sotra import db as sdb

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(sdb._SCHEMA)
    return conn


def _them(conn, cid, trang_thai="song", sach=True):
    """`sach=True`: clip envato ĐÃ có bản sạch — trạng thái bình thường.

    Từ 10/09 `soat_truoc_pha` chặn cả clip envato thiếu bản sạch (Export ra sẽ
    dính preview WATERMARK — user chốt chặn hẳn). Test ở file này kiểm đường
    LINK CHẾT nên clip phải sạch, không thì miếng nào cũng bị bắt vì watermark
    trước khi tới miếng chết thật.
    """
    f = ""
    if sach:
        g = Path(tempfile.mkdtemp()) / f"{cid.replace(':', '_')}.mp4"
        g.write_bytes(bytes(200_000))
        f = str(g)
    conn.execute(
        "INSERT INTO clip(id, nguon, tieu_de, trang_thai, path_local) "
        "VALUES(?,'envato',?,?,?)",
        (cid, f"clip {cid}", trang_thai, f))
    conn.commit()


def _hd(*ids, trang_thai="khoa"):
    return {"trang_thai": trang_thai,
            "khoi": [{"v0": 0.0, "v1": 2.0, "loi": "x"}],
            "hinh": [{"t0": float(i * 2), "dur": 2.0, "khoi_goc": 0, "chon": 0,
                      "uv": [{"id": c, "nguon": "envato", "tieu_de": f"clip {c}"}]}
                     for i, c in enumerate(ids)]}


# ═══════════ 1. DỪNG NGAY khi gặp clip chết ═══════════

def test_gap_clip_chet_thi_DUNG_khong_quet_tiep():
    """Miếng 1 hỏng thì không đọc tới miếng 2, 3..."""
    conn = _kho()
    _them(conn, "envato:0")
    _them(conn, "envato:1", "link_chet")
    _them(conn, "envato:2", "link_chet")
    xau = mtm.soat_truoc_pha(conn, _hd("envato:0", "envato:1", "envato:2"))
    assert len(xau) == 1, f"phải dừng ở miếng hỏng đầu tiên, được {xau}"
    assert xau[0]["mieng"] == 1


def test_dung_som_van_du_thong_tin_cho_UI():
    """Dừng sớm không được làm mất id/tiêu đề — UI cần để tô đỏ và báo tên."""
    conn = _kho()
    _them(conn, "envato:chet", "link_chet")
    xau = mtm.soat_truoc_pha(conn, _hd("envato:chet"))
    assert xau[0]["id"] == "envato:chet"
    assert "clip envato:chet" in xau[0]["tieu_de"]


def test_dung_som_KHONG_doc_them_dong_DB_nao():
    """Đo thật số lần truy vấn: 46 miếng mà hỏng ở miếng 2 thì chỉ 2 lượt đọc."""
    conn = _kho()
    _them(conn, "envato:0")
    _them(conn, "envato:1", "link_chet")
    for i in range(2, 46):
        _them(conn, f"envato:{i}")
    dem = {"n": 0}
    goc = conn.execute

    class _Dem:
        def execute(self, *a, **k):
            dem["n"] += 1
            return goc(*a, **k)

        def __getattr__(self, t):
            return getattr(conn, t)

    xau = mtm.soat_truoc_pha(_Dem(), _hd(*[f"envato:{i}" for i in range(46)]))
    assert len(xau) == 1
    assert dem["n"] <= 3, f"quét quá nhiều: {dem['n']} lượt đọc DB cho 46 miếng"


def test_khay_sach_van_quet_HET():
    """Không hỏng gì thì phải soi hết — dừng sớm chỉ áp cho ca GẶP LỖI."""
    conn = _kho()
    for i in range(5):
        _them(conn, f"envato:{i}")
    assert mtm.soat_truoc_pha(conn, _hd(*[f"envato:{i}" for i in range(5)])) == []


# ═══════════ 2. CHƯA DUYỆT thì KHÔNG tải ═══════════

def test_chua_khoa_so_thi_KHONG_tai_gi(monkeypatch):
    """Đang dò clip mà đã tải là đốt băng thông cho clip sẽ bị bỏ.

    Đo 09/09: 8 chương chưa duyệt đang giữ 17 miếng envato; kho bản sạch đã
    44,5 GB / 104 file (428 MB mỗi clip).
    """
    from autoedit.web import server as sv

    goi = []
    monkeypatch.setattr(sv, "_tai_nen_hang", set())
    monkeypatch.setattr(sv, "_tai_nen_worker", {"chay": False})
    monkeypatch.setattr("autoedit.sourcer.tai_sach.tai_nhieu",
                        lambda *a, **k: goi.append(a))
    sv._xep_tai_ban_sach(_hd("envato:x", trang_thai="pha2"))
    assert not sv._tai_nen_hang, (
        f"chương chưa duyệt mà đã xếp hàng tải: {sv._tai_nen_hang}")


@pytest.mark.parametrize("tt", ["", "pha1", "pha2", "dong_kiem"])
def test_moi_trang_thai_CHUA_khoa_deu_khong_tai(monkeypatch, tt):
    from autoedit.web import server as sv

    monkeypatch.setattr(sv, "_tai_nen_hang", set())
    monkeypatch.setattr(sv, "_tai_nen_worker", {"chay": False})
    sv._xep_tai_ban_sach(_hd("envato:x", trang_thai=tt))
    assert not sv._tai_nen_hang, f"trạng thái {tt!r} vẫn tải"


def test_KHOA_SO_phai_bat_dau_tai(tmp_path, monkeypatch):
    """Chặn tải sớm mà quên gọi lúc khoá sổ = Export mới tải, người dựng chờ dài.

    Bản sạch 428 MB/clip; một chương 40 miếng envato là hàng chục phút.
    """
    import json

    from fastapi.testclient import TestClient

    from autoedit.sourcer import tai_sach
    from autoedit.web import server as sv

    d = tmp_path / "c1-20260101-000000"
    d.mkdir(parents=True)
    (d / "offline.json").write_text(
        json.dumps(_hd("envato:x", trang_thai="pha2")), encoding="utf-8")
    monkeypatch.setattr(sv, "_pdir_offline", lambda pid: d)
    monkeypatch.setattr(sv, "_require_auth", lambda r: None)
    monkeypatch.setattr(sv, "_gac_quyen_sua", lambda *a, **k: None)
    monkeypatch.setattr(sv, "_tai_nen_hang", set())
    monkeypatch.setattr(sv, "_tai_nen_worker", {"chay": False})
    monkeypatch.setattr(tai_sach, "thu_muc_sach", lambda: tmp_path)
    monkeypatch.setattr(tai_sach, "tai_nhieu", lambda *a, **k: None)

    r = TestClient(sv.app).post(f"/api/offline/{d.name}/khoa-so", json={})
    assert r.status_code == 200, r.text
    assert sv._tai_nen_hang, "khoá sổ xong mà không xếp hàng tải bản sạch"


def test_da_khoa_so_thi_VAN_tai_nhu_cu(monkeypatch, tmp_path):
    """Không được chặn nhầm: khoá sổ rồi là đúng lúc tải."""
    from autoedit.sourcer import tai_sach
    from autoedit.web import server as sv

    monkeypatch.setattr(sv, "_tai_nen_hang", set())
    monkeypatch.setattr(sv, "_tai_nen_worker", {"chay": False})
    monkeypatch.setattr(tai_sach, "thu_muc_sach", lambda: tmp_path)
    monkeypatch.setattr(tai_sach, "tai_nhieu", lambda *a, **k: None)
    sv._xep_tai_ban_sach(_hd("envato:x", trang_thai="khoa"))
    assert sv._tai_nen_hang, "chương đã khoá sổ mà không tải -> Export sẽ chờ lâu"
