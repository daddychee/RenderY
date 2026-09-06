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


# --------------------------------------------- nạp ref: cắt theo CẢNH QUAY
def _gia_lap_ref(monkeypatch, canh, docs=None):
    """Giả lập scene-detect + trích ảnh + đọc hình (không chạm ffmpeg/mạng)."""
    import autoedit.sotra.hut as h
    from autoedit.sotra.canh import Canh
    from autoedit.sotra.doc_canh import DocRa

    monkeypatch.setattr("autoedit.sotra.canh.cat_canh",
                        lambda v, **k: [Canh(*c) for c in canh])
    monkeypatch.setattr("autoedit.sotra.doc_canh.trich_anh",
                        lambda v, t0, t1, dich, **k: dich)
    monkeypatch.setattr("autoedit.sotra.doc_canh.doc_nhieu",
                        lambda al, **k: docs or [DocRa(i=j + 1) for j in range(len(al))])
    return h


def test_nap_ref_cat_theo_canh_khong_theo_cau(conn, tmp_path, monkeypatch):
    """Đổi 06/09: đơn vị ref là CÚ MÁY, không phải câu phụ đề. Phụ đề chỉ làm
    `loi_quanh` — 11% cảnh không có câu nào chồng vẫn phải vào kho."""
    from autoedit.sotra.doc_canh import DocRa

    h = _gia_lap_ref(monkeypatch, [(0.0, 5.0, False), (5.0, 9.0, True)],
                     docs=[DocRa(i=1, subject="worker lifting box",
                                 vat_the="bananas, box, pallet", shot="medium",
                                 mood="tense", khop=2),
                           DocRa(i=2, subject="street at night", vat_the="cars, lights")])
    (tmp_path / "r.srt").write_text(
        "1\n00:00:01,000 --> 00:00:03,000\nnarco cocaine shipment\n\n", encoding="utf-8")
    (tmp_path / "r.mp4").write_bytes(b"v")

    assert h.nap_ref_tap(conn, tmp_path, tap="LI100", quoc_gia="ecuador") == 2
    c = {r["id"]: r for r in conn.execute("SELECT * FROM clip")}
    a = c["ref:LI100-r:0.00-5.00"]
    assert a["subject"] == "worker lifting box" and a["tag_nguon"] == "vision"
    assert a["loi_quanh"] == "narco cocaine shipment"   # phụ đề = ngữ cảnh
    assert a["geo"] == "ecuador"                         # gắn cứng cấp tập
    assert a["frame_dau"], "mỗi cảnh phải có ảnh đại diện"
    b = c["ref:LI100-r:5.00-9.00"]
    assert b["loi_quanh"] == "", "cảnh không có câu chồng vẫn phải vào kho"
    assert b["may_dong"] == 1


def test_tra_duoc_bang_vat_the(conn, tmp_path, monkeypatch):
    """`vat_the` phải nằm trong FTS — đó là lý do thêm trục này: tra "bananas"
    phải ra thùng Burberry giấu ma túy (v1 chỉ ghi "box" nên tra không ra)."""
    from autoedit.sotra.doc_canh import DocRa

    h = _gia_lap_ref(monkeypatch, [(0.0, 4.0, False)],
                     docs=[DocRa(i=1, subject="hand holding box",
                                 vat_the="hand, burberry box, bananas, plastic wrap")])
    (tmp_path / "r.mp4").write_bytes(b"v")
    h.nap_ref_tap(conn, tmp_path, tap="LI100", quoc_gia="ecuador")
    assert sdb.tim(conn, q="bananas"), "tra vật thể trong hình phải ra cảnh"


def test_bo_phu_de_cua_phim_khac(conn, tmp_path, monkeypatch):
    """Gặp thật 06/09: `ref 2.srt` trùng MD5 với `ref 1.srt` nhưng video 23'
    vs 52' — dùng bừa thì 228 cảnh bị gán lời phim khác."""
    h = _gia_lap_ref(monkeypatch, [(0.0, 4.0, False)])
    (tmp_path / "r.srt").write_text(
        "1\n00:50:00,000 --> 00:50:05,000\nloi phim khac\n\n", encoding="utf-8")
    (tmp_path / "r.mp4").write_bytes(b"v")
    log = []
    h.nap_ref_tap(conn, tmp_path, tap="LI100", log=log.append)
    r = conn.execute("SELECT loi_quanh FROM clip").fetchone()
    assert r["loi_quanh"] == "", "phụ đề lệch phải bị bỏ, không gán bừa"
    assert any("phim khác" in m for m in log)


def test_doc_hinh_hong_van_nap_duoc(conn, tmp_path, monkeypatch):
    """GLM chết thì kho vẫn phải có cảnh (tạm lấy từ khóa từ lời)."""
    h = _gia_lap_ref(monkeypatch, [(0.0, 4.0, False)])
    (tmp_path / "r.srt").write_text(
        "1\n00:00:01,000 --> 00:00:03,000\npolice patrol street\n\n", encoding="utf-8")
    (tmp_path / "r.mp4").write_bytes(b"v")
    assert h.nap_ref_tap(conn, tmp_path, tap="LI100") == 1
    assert conn.execute("SELECT tag_nguon FROM clip").fetchone()[0] == "tieu_de"


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


def test_ung_vien_mang_t0_t1_cho_hover_ref(conn, tmp_path):
    """ref là file 52'/1GB: ứng viên PHẢI mang t0/t1 để UI gắn #t= — thiếu thì
    trình duyệt tải từ byte 0 dò tới giây cần xem (đo 06/09: hover khúc 4s =
    tải 1.076.201.806 byte, 5.9s; có #t= còn 512KB/0.012s)."""
    from autoedit.offline.dung import do_ung_vien
    from autoedit.sotra.db import them_clip

    them_clip(conn, {"id": "ref:LI100-r1:120-124", "nguon": "ref",
                     "tieu_de": "police patrol street", "path_local": "/x/r1.mp4",
                     "t0": 120.0, "t1": 124.0, "dai_s": 4.0,
                     "subject": "police patrol", "setting": "street"})
    conn.commit()

    class _O:
        truc_chi = ["police patrol"]; ngu_canh = ["street"]; khong_khi = []; neo = ""
    uv = do_ung_vien(conn, [{"loi": "x"}], [_O()], ["police"])
    r = [c for c in uv[0] if c["id"].startswith("ref:")]
    assert r, "ref phải lọt vào ứng viên"
    assert r[0]["t0"] == 120.0 and r[0]["t1"] == 124.0
