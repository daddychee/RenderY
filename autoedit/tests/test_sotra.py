# -*- coding: utf-8 -*-
"""Sổ Tra (Đợt 1 Đường Dây) — db + tag 7 trục + tra 4 lớp + khai quật + API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoedit.sotra import db as sdb
from autoedit.sotra.tag7 import tag_tu_tieu_de
from autoedit.sotra.tra import tra


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    yield c
    c.close()


def _clip(i, ten, nguon="envato", **them):
    return {"id": sdb.lam_id(nguon, str(i)), "nguon": nguon, "tieu_de": ten,
            **tag_tu_tieu_de(ten), **them}


# ------------------------------------------------------------ đặt tên
def test_lam_id_chinh_tac():
    assert sdb.lam_id("envato", "78a15f44-x") == "envato:78a15f44-x"
    assert sdb.lam_id("ref", "LI100-ref1", "124-131") == "ref:LI100-ref1:124-131"
    with pytest.raises(ValueError):
        sdb.lam_id("youtube", "x")          # nguồn lạ bị chặn


def test_ten_frame_cho_nguoi_doc():
    t = sdb.ten_frame("envato:78a15f44-db0c", "Woman Buying Vegetables!", "dau")
    assert t == "envato_78a15f44_woman-buying-vegetables.dau.jpg"


# ------------------------------------------------------------ tag 7 trục
def test_tag7_boc_du_truc():
    t = tag_tu_tieu_de("Aerial View of Quito Old Town Market at Sunset, Woman Buying Vegetables")
    assert t["geo"] == "ecuador>andes>quito"
    assert "market" in t["setting"]
    assert "woman" in t["people"]
    assert t["shot"] == "aerial"
    assert "sunset" in t["mood"]
    assert "buying" in t["action"]
    assert "vegetables" in t["subject"]


def test_tag7_geo_cu_the_thang_chung():
    # có cả 'ecuador' lẫn 'otavalo' -> lấy cái CỤ THỂ hơn
    assert tag_tu_tieu_de("Otavalo Market Ecuador")["geo"] == "ecuador>andes>otavalo"


# ------------------------------------------------------------ db + tìm
def test_them_va_tim_fts(conn):
    sdb.them_clip(conn, _clip(1, "Woman Buying Vegetables at Quito Market"))
    sdb.them_clip(conn, _clip(2, "Snow Capped Volcano in the Andes"))
    conn.commit()
    kq = sdb.tim(conn, q="market")
    assert len(kq) == 1 and "Quito" in kq[0]["tieu_de"]
    assert sdb.dem_theo_nguon(conn) == {"envato": 2}


def test_alias_tieng_viet_tra_ra(conn):
    sdb.them_clip(conn, _clip(1, "Fresh Vegetables at Street Market"))
    conn.commit()
    assert sdb.tim(conn, q="chợ")            # chợ -> market
    assert sdb.tim(conn, q="tủ lạnh") == []  # refrigerator: kho không có -> rỗng sạch


def test_nhan_da_dung_chong_lap_giua_tap(conn):
    sdb.them_clip(conn, _clip(1, "Quito Street Morning"))
    sdb.ghi_su_kien(conn, "envato:1", "len_final", tap="LI100")
    conn.commit()
    kq = sdb.tim(conn, q="quito")
    assert kq[0].get("da_dung") == "LI100"


def test_loai_tru_khong_hien(conn):
    sdb.them_clip(conn, _clip(1, "Quito Street", trang_thai="loai_tru"))
    conn.commit()
    assert sdb.tim(conn, q="quito") == []


# ------------------------------------------------------------ tra 4 lớp
def test_tra_4_lop_giao_nhau(conn):
    """Cửa L0 bắt buộc; L1 xếp trên L2 trên L3; REF luôn có suất giữ chỗ."""
    sdb.them_clip(conn, _clip(1, "Refrigerator Full of Food in Ecuador Kitchen"))
    sdb.them_clip(conn, _clip(2, "Grocery Shopping at Quito Supermarket"))
    sdb.them_clip(conn, _clip(3, "Quito Street Daily Life Morning"))
    sdb.them_clip(conn, _clip(4, "New York Refrigerator Store"))   # KHÔNG neo, không L0
    sdb.them_clip(conn, {"id": sdb.lam_id("ref", "LI100-r1", "5-9"), "nguon": "ref",
                         "tieu_de": "gia đình nấu ăn", "path_local": "x.mp4",
                         **tag_tu_tieu_de("family cooking")})
    conn.commit()
    lop = {"L0": ["ecuador", "daily life", "cost"], "L1": ["refrigerator food"],
           "L2": ["grocery supermarket"], "L3": ["quito street morning"]}
    kq = tra(conn, lop, so=10)
    lops = [(c["id"], c["lop"]) for c in kq]
    assert lops[0] == ("envato:1", "L1")               # trực chỉ đứng đầu
    assert ("envato:4", "L1") not in lops              # trượt cửa L0 (không neo)
    assert any(c["nguon"] == "ref" for c in kq)        # suất REF giữ chỗ
    thu_tu = [c["lop"] for c in kq if c["nguon"] != "ref"]
    assert thu_tu == sorted(thu_tu)                    # L1 < L2 < L3 theo thứ tự chữ


def test_tra_uu_tien_nguon(conn):
    sdb.them_clip(conn, _clip(1, "Quito Market Stall", nguon="pexels"))
    sdb.them_clip(conn, _clip(2, "Quito Market Vendor", nguon="envato"))
    conn.commit()
    lop = {"L0": ["ecuador"], "L1": ["market"], "L2": [], "L3": []}
    kq = tra(conn, lop, uu_tien_nguon="pexels")
    assert kq[0]["nguon"] == "pexels"


# ------------------------------------------------------------ khai quật
def test_khai_quat_kho_cu(conn, tmp_path):
    from autoedit.sotra.khai_quat import khai_quat

    pdir = tmp_path / "projects" / "h-test-1"
    (pdir / "assets").mkdir(parents=True)
    (pdir / "assets" / "b012_quito-market-stall_ab12cd.mp4").write_bytes(b"v")
    (pdir / "assets" / "b013_andes-volcano-peak_ef34ab.mp4").write_bytes(b"v")
    (pdir / "project.json").write_text(json.dumps({
        "project_id": "h-test-1",
        "inputs": {"original_script_path": r"F:\NAS\Life In\US\LI100\RenderY\H\s.txt"},
        "shots": [{"beat_id": 12, "source": "pexels",
                   "asset_path": "assets/b012_quito-market-stall_ab12cd.mp4"}],
    }), encoding="utf-8")

    kq = khai_quat(conn, tmp_path / "projects")
    assert kq == {"clip_moi": 2, "su_kien": 1, "project": 1}
    kq_tim = sdb.tim(conn, q="market")
    assert kq_tim and kq_tim[0]["da_dung"] == "LI100"   # tên tập suy từ path gốc
    # id chính tắc nguồn kho
    assert kq_tim[0]["id"] == "kho:h-test-1:b012_quito-market-stall_ab12cd.mp4"


# ------------------------------------------------------------ nạp ref từ srt
def test_nap_ref_tap(conn, tmp_path):
    from autoedit.sotra.hut import nap_ref_tap

    (tmp_path / "ref 1.srt").write_text(
        "1\n00:00:05,000 --> 00:00:11,000\nfamily cooking dinner at home\n\n"
        "2\n00:00:12,000 --> 00:00:13,000\nqua ngan\n\n", encoding="utf-8")
    (tmp_path / "ref 1.mp4").write_bytes(b"v")
    moi = nap_ref_tap(conn, tmp_path, tap="LI100")
    assert moi == 1                                     # câu 1s bị bỏ
    r = sdb.tim(conn, q="cooking")[0]
    assert r["id"] == "ref:LI100-ref 1:5-11"
    assert r["t0"] == 5.0 and r["t1"] == 11.0


# ------------------------------------------------------------ API
def test_api_sotra(tmp_path, monkeypatch):
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    from fastapi.testclient import TestClient

    from autoedit.web import server

    c = sdb.mo()
    sdb.them_clip(c, _clip(1, "Quito Market Morning"))
    c.commit()
    c.close()
    tc = TestClient(server.app)
    r = tc.get("/api/sotra?q=market")
    assert r.status_code == 200
    assert len(r.json()["clips"]) == 1
    # quyền hút qua CRM: viewer chặn, manager qua (dùng _duoc_nghien_cuu_kenh
    # trực tiếp — TestClient không giả được client loopback cho trust proxy)
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")

    class _Req:
        headers = {"x-forwarded-host": "crm.local", "x-remote-role": "viewer"}
        query_params = {}
        client = type("C", (), {"host": "127.0.0.1"})()

    assert server._duoc_nghien_cuu_kenh(_Req()) is False
    r2 = tc.get("/api/sotra/clip?id=envato:1")
    assert r2.status_code == 200 and r2.json()["clip"]["tieu_de"] == "Quito Market Morning"
    assert tc.get("/api/sotra/clip?id=envato:khong-co").status_code == 404
