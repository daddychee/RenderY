# -*- coding: utf-8 -*-
"""API hồ sơ ngách — đọc / lưu (QĐ18, 18/09/2026).

Số clip hiện trên chip từ khoá phải đếm ĐÚNG CỤM. Đo trên kho thật 18/09:
`dem_tim("vending machine")` = **177** vì nó nối các từ bằng OR nên ăn cả clip
"machine" chung chung; đếm đúng cụm = **0**. Hồ sơ mà hiện 177 là nói dối đúng
chỗ người ta dựa vào để quyết có phải đi hút hay không.
"""
from __future__ import annotations

import sqlite3

import pytest

from autoedit import ngach_ho_so as hs
from autoedit.sotra import db as sdb

NGACH_THAT = [
    ("N-003", "X FILE", "khai_thac"),
    ("N-SENIOR-HEALTH", "SENIOR HEALTH", "khai_thac"),
    ("N-COOKING", "COOKING", "khai_thac"),
]


# ------------------------------------------------- đếm đúng cụm (sotra/db.py)

@pytest.fixture
def kho_clip(tmp_path):
    conn = sdb.mo(tmp_path / "so_tra.db")
    for i, (tid, tieu) in enumerate([
            ("pexels:1", "vending machine in tokyo"),
            ("pexels:2", "washing machine close up"),
            ("pexels:3", "old sewing machine")]):
        sdb.them_clip(conn, {"id": tid, "nguon": "pexels", "tieu_de": tieu})
    conn.commit()
    return conn


def test_dem_cum_KHONG_an_theo_tung_tu(kho_clip):
    assert sdb.dem_tim(kho_clip, "vending machine") == 3, "lối OR: ăn cả 3"
    assert sdb.dem_cum(kho_clip, "vending machine") == 1


def test_dem_cum_tu_don_giong_dem_tim(kho_clip):
    assert sdb.dem_cum(kho_clip, "machine") == 3


def test_dem_cum_rong_tra_0(kho_clip):
    assert sdb.dem_cum(kho_clip, "") == 0
    assert sdb.dem_cum(kho_clip, "   ") == 0


def test_dem_cum_ky_tu_la_khong_no(kho_clip):
    """Từ khoá đi từ HTTP vào — dấu nháy trong FTS5 là cú pháp, không phải chữ."""
    assert sdb.dem_cum(kho_clip, 'may "OR" *') == 0


# ---------------------------------------------------------------------- API

@pytest.fixture
def may_chu(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.web import queue as q, server

    f = tmp_path / "danh_ba.db"
    c = sqlite3.connect(f)
    c.execute("CREATE TABLE ngach(ma TEXT PRIMARY KEY, ten_chuan TEXT, "
              "trang_thai TEXT, ghi_chu TEXT, tao_luc TEXT)")
    c.executemany("INSERT INTO ngach(ma, ten_chuan, trang_thai) VALUES(?,?,?)",
                  NGACH_THAT)
    c.commit()
    c.close()
    monkeypatch.setenv("RENDERY_DANH_BA", str(f))
    monkeypatch.delenv("RENDERY_NGACH_NHAN_VAT", raising=False)

    # pool Radary giả
    r = tmp_path / "radary.db"
    rc = sqlite3.connect(r)
    rc.executescript("""
        CREATE TABLE workspaces(id INTEGER PRIMARY KEY, name TEXT, market TEXT, ngach TEXT);
        CREATE TABLE channels(id INTEGER PRIMARY KEY, workspace_id INT, title TEXT);
        CREATE TABLE videos(id INTEGER PRIMARY KEY, workspace_id INT, title TEXT,
                            tier INT, pub_ts INT);
    """)
    rc.execute("INSERT INTO workspaces VALUES(53,'X FILE — US','TT-US','N-003')")
    rc.execute("INSERT INTO channels VALUES(1,53,'Kênh A')")
    rc.execute("INSERT INTO videos VALUES(1,53,'How Duct Tape Is Made',3,9)")
    rc.commit()
    rc.close()
    monkeypatch.setenv("RENDERY_RADARY", str(r))

    # kho hồ sơ + Sổ Tra riêng
    monkeypatch.setattr(hs, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    conn = sdb.mo()
    sdb.them_clip(conn, {"id": "pexels:9", "nguon": "pexels", "tieu_de": "duct tape roll"})
    conn.commit()
    conn.close()

    monkeypatch.setattr(server, "ROOT", tmp_path)
    nas = tmp_path / "nas" / "XF001"
    (nas / "RenderY").mkdir(parents=True)
    for ten in ("H", "C1", "E"):
        (nas / "RenderY" / f"{ten}.mp3").write_bytes(b"x" * 64)
        (nas / "RenderY" / f"{ten}.txt").write_text("xin chao", encoding="utf-8")
    monkeypatch.setattr(server, "_trong_nas", lambda p: nas)
    q.connect(tmp_path / "jobs.db").close()
    return TestClient(server.app), str(nas)


def test_GET_chua_co_ho_so_tra_null_kem_POOL(may_chu):
    tc, _ = may_chu
    d = tc.get("/api/ngach/N-003/ho-so").json()
    assert d["ho_so"] is None
    assert d["ngach"]["ten"] == "X FILE"
    assert d["pool"]["video"] == 1 and d["pool"]["kenh"] == 1
    assert d["pool"]["doc_duoc"] is True


def test_GET_ngach_khong_co_trong_danh_ba_thi_404(may_chu):
    tc, _ = may_chu
    # Chốt route CÓ THẬT trước — không thì 404 dưới đây chỉ là "chưa có route",
    # một cái xanh rỗng (đã dính đúng bẫy này lúc chạy pha đỏ 18/09).
    assert tc.get("/api/ngach/N-003/ho-so").status_code == 200
    assert tc.get("/api/ngach/N-BIA-RA/ho-so").status_code == 404


def test_GET_ma_bay_khong_doc_file_ngoai(may_chu):
    tc, _ = may_chu
    assert tc.get("/api/ngach/N-003/ho-so").status_code == 200
    assert tc.get("/api/ngach/..%2F..%2Fetc/ho-so").status_code in (404, 422)


def test_PUT_luu_roi_GET_thay_lai(may_chu):
    tc, _ = may_chu
    r = tc.put("/api/ngach/N-003/ho-so", json={
        "loc_nguoi": False, "vat_the": ["Duct Tape", "battery"]})
    assert r.status_code == 200, r.text
    d = tc.get("/api/ngach/N-003/ho-so").json()
    assert d["ho_so"]["vat_the"] == ["duct tape", "battery"]
    assert d["ho_so"]["loc_nguoi"] is False


def test_GET_kem_SO_CLIP_trong_kho_theo_tung_tu_khoa(may_chu):
    tc, _ = may_chu
    tc.put("/api/ngach/N-003/ho-so",
           json={"loc_nguoi": False, "vat_the": ["duct tape", "vending machine"]})
    kho = {x["tu"]: x["clip"] for x in tc.get("/api/ngach/N-003/ho-so").json()["kho"]}
    assert kho == {"duct tape": 1, "vending machine": 0}


def test_PUT_nguoi_duyet_lay_tu_PHIEN_khong_lay_tu_body(may_chu):
    """Ai duyệt là chữ ký — không để phía gọi tự khai hộ người khác."""
    tc, _ = may_chu
    tc.put("/api/ngach/N-003/ho-so",
           json={"loc_nguoi": False, "vat_the": ["x"], "nguoi_duyet": "sep_to"},
           headers={"X-Remote-User": "haint", "X-Remote-Role": "manager"})
    assert tc.get("/api/ngach/N-003/ho-so").json()["ho_so"]["nguoi_duyet"] != "sep_to"


def test_PUT_khai_nhan_vat_thi_tra_dung_bo_loc(may_chu):
    tc, _ = may_chu
    tc.put("/api/ngach/N-COOKING/ho-so", json={
        "loc_nguoi": True, "nhan_vat": {"tuoi": ["adult"], "chung_toc": ["asian"]}})
    from autoedit import ngach

    assert ngach.nhan_vat("COOKING") == {"tuoi": ["adult"], "chung_toc": ["asian"]}


def test_KHAI_KHONG_LOC_NGUOI_roi_thi_NOP_TAP_QUA_CONG(may_chu):
    """Payoff của cả QĐ18: X FILE nộp được tập mà không phải bịa ra nhân vật."""
    tc, folder = may_chu
    r = tc.post("/api/jobs", json={"folder": folder, "niche": "X FILE"})
    assert r.status_code == 422 and "NHÂN VẬT" in r.json()["detail"]

    tc.put("/api/ngach/N-003/ho-so", json={"loc_nguoi": False, "vat_the": ["duct tape"]})
    r = tc.post("/api/jobs", json={"folder": folder, "niche": "X FILE"})
    assert r.status_code == 200, r.text


def test_api_ngach_kem_co_ho_so_cho_man_hinh(may_chu):
    tc, _ = may_chu
    tc.put("/api/ngach/N-003/ho-so", json={"loc_nguoi": False, "vat_the": ["x"]})
    theo = {x["ma"]: x for x in tc.get("/api/ngach").json()["ngach"]}
    assert theo["N-003"]["co_ho_so"] is True
    assert theo["N-COOKING"]["co_ho_so"] is False


# --------------------------------------------- POST /sinh — máy ĐỀ XUẤT thôi

class _LLMGia:
    def __init__(self, tra=None, no=None):
        self.tra, self.no = tra, no

    def complete(self, system, user, output_model, context=None):
        if self.no:
            raise self.no
        return output_model(**(self.tra or {})), {}


@pytest.fixture
def llm_gia(monkeypatch):
    from autoedit import ngach_sinh as ns

    hop = {"llm": _LLMGia({"vat_the": ["duct tape", "forklift"]})}
    monkeypatch.setattr(ns, "_llm", lambda: hop["llm"])
    return hop


def test_POST_sinh_tra_DE_XUAT_va_KHONG_luu(may_chu, llm_gia):
    """Máy đề xuất, người chốt — sinh xong mà tự lưu là cướp quyền duyệt."""
    tc, _ = may_chu
    r = tc.post("/api/ngach/N-003/sinh")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["de_xuat"]["vat_the"] == ["duct tape", "forklift"]
    assert d["de_xuat"]["loc_nguoi"] is False
    assert tc.get("/api/ngach/N-003/ho-so").json()["ho_so"] is None, "đã tự lưu"


def test_POST_sinh_kem_SO_CLIP_trong_kho_cho_tung_tu(may_chu, llm_gia):
    """Đề xuất mà không nói kho có gì thì người duyệt không biết phải đi hút."""
    tc, _ = may_chu
    kho = {x["tu"]: x["clip"] for x in tc.post("/api/ngach/N-003/sinh").json()["kho"]}
    assert kho == {"duct tape": 1, "forklift": 0}


def test_POST_sinh_kem_SO_DO_nguoi(may_chu, llm_gia):
    tc, _ = may_chu
    d = tc.post("/api/ngach/N-003/sinh").json()["de_xuat"]
    assert d["do_nguoi"]["tong"] == 1


def test_POST_sinh_pool_rong_thi_422_noi_ro(may_chu, llm_gia):
    tc, _ = may_chu
    r = tc.post("/api/ngach/N-COOKING/sinh")
    assert r.status_code == 422 and "pool" in r.json()["detail"].lower()


def test_POST_sinh_LLM_chet_thi_502_chu_khong_500(may_chu, llm_gia):
    tc, _ = may_chu
    llm_gia["llm"] = _LLMGia(no=RuntimeError("GLM 500"))
    r = tc.post("/api/ngach/N-003/sinh")
    assert r.status_code == 502, r.status_code


# ------------------------------------------------------------------- quyền

@pytest.fixture
def qua_crm(monkeypatch):
    """Giả lập đi qua cổng CRM để header vai có hiệu lực."""
    from autoedit.web import server

    monkeypatch.setattr(server, "_trust_proxy", lambda r: True)
    return {"X-Remote-User": "haint", "X-Forwarded-Host": "crm.outliery"}


def test_viewer_KHONG_duoc_duyet_ho_so(may_chu, llm_gia, qua_crm):
    """Hồ sơ ngách đổi cách chọn hình của CẢ ngách — không để ai cũng sửa."""
    tc, _ = may_chu
    h = {**qua_crm, "X-Remote-Role": "viewer", "X-Remote-Level": "1"}
    assert tc.put("/api/ngach/N-003/ho-so",
                  json={"loc_nguoi": False, "vat_the": ["x"]},
                  headers=h).status_code == 403
    assert tc.post("/api/ngach/N-003/sinh", headers=h).status_code == 403


def test_manager_duyet_duoc(may_chu, llm_gia, qua_crm):
    tc, _ = may_chu
    h = {**qua_crm, "X-Remote-Role": "manager", "X-Remote-Level": "3"}
    assert tc.put("/api/ngach/N-003/ho-so",
                  json={"loc_nguoi": False, "vat_the": ["x"]},
                  headers=h).status_code == 200
    assert tc.post("/api/ngach/N-003/sinh", headers=h).status_code == 200


def test_viewer_VAN_XEM_duoc_ho_so(may_chu, qua_crm):
    """Chặn sửa, không chặn xem: người dựng cần biết ngách mình khai gì."""
    tc, _ = may_chu
    h = {**qua_crm, "X-Remote-Role": "viewer", "X-Remote-Level": "1"}
    r = tc.get("/api/ngach/N-003/ho-so", headers=h)
    assert r.status_code == 200 and r.json()["sua_duoc"] is False
