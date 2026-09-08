"""F5 xong lựa chọn quay về mặc định (user báo 08/09) — và chỉ THỈNH THOẢNG.

`api_offline_doc` gọi `lam_tuoi_ref` NGAY LÚC ĐỌC hợp đồng rồi ghi đè file.
Hàm đó dựng lại danh sách `uv` (bỏ mục ref hỏng, thêm mục tươi) nhưng KHÔNG
dời `chon` theo. Mục hỏng nằm TRƯỚC mục đang chọn thì mọi chỉ số sau nó tụt
một bậc — `chon` trỏ sang clip khác. Người dựng thấy "F5 là về mặc định".

Chỉ thỉnh thoảng vì phải có đủ hai điều kiện: khay của miếng đó CÓ mục ref
hỏng, và mục hỏng nằm TRƯỚC mục đang chọn.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def conn(tmp_path, monkeypatch):
    from autoedit.sotra import db as sdb
    from autoedit.sotra.tag7 import tag_tu_tieu_de

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    c = sdb.mo()
    for i in range(6):
        ten = f"kabul market crowd {i}"
        sdb.them_clip(c, {"id": f"ref:LI103-r:{i}", "nguon": "ref", "tap": "LI103",
                          "tieu_de": ten, "path_local": "ref 1.mp4",
                          "t0": i * 10, "t1": i * 10 + 4, **tag_tu_tieu_de(ten)})
    c.commit()
    yield c
    c.close()


def _hd(chon: int) -> dict:
    """Khay: [ref HỎNG (thiếu t1), ref tốt, ref tốt] — mục hỏng đứng TRƯỚC."""
    def uv(i, t1):
        return {"id": f"ref:LI103-r:{i}", "nguon": "ref", "tieu_de": f"c{i}",
                "lop": "L1", "diem": 9.0, "t0": i * 10, "t1": t1}

    khay = [uv(0, 0), uv(1, 14), uv(2, 24)]      # mục 0 thiếu t1 -> "hỏng"
    return {"ma_tap": "LI103", "dia_danh": "", "chu_the_tap": [],
            "khoi": [{"v0": 0, "v1": 3, "L1": ["market"], "L2": [], "L3": [],
                      "uv": list(khay), "chon": chon}],
            "hinh": [{"t0": 0.0, "dur": 3.0, "khoi_goc": 0, "uv": list(khay),
                      "chon": chon, "noi_tiep": False, "nguoi_sua": True}]}


def test_lam_tuoi_GIU_dung_clip_dang_chon(conn):
    """Người chọn mục thứ 3 (chỉ số 2). Sau khi làm tươi, `chon` phải vẫn trỏ
    ĐÚNG clip đó — không phải chỉ số cũ trên danh sách mới."""
    from autoedit.offline import dung

    hd = _hd(chon=2)
    truoc = hd["hinh"][0]["uv"][2]["id"]
    dung.lam_tuoi_ref(hd, conn)

    for cho, ten in ((hd["khoi"][0], "khối"), (hd["hinh"][0], "miếng")):
        uv, c = cho["uv"], cho["chon"]
        assert 0 <= c < len(uv), f"{ten}: chon={c} rơi ra ngoài khay {len(uv)}"
        assert uv[c]["id"] == truoc, (
            f"{ten}: F5 xong đổi clip — chọn «{truoc}» nhưng thành «{uv[c]['id']}»")


def test_lam_tuoi_giu_lua_chon_o_moi_vi_tri(conn):
    """Quét mọi vị trí chọn: không vị trí nào được đổi clip sau khi làm tươi."""
    from autoedit.offline import dung

    for chon in (1, 2):
        hd = _hd(chon=chon)
        truoc = hd["hinh"][0]["uv"][chon]["id"]
        dung.lam_tuoi_ref(hd, conn)
        h = hd["hinh"][0]
        assert h["uv"][h["chon"]]["id"] == truoc, f"vị trí {chon} bị đổi clip"


def test_lam_tuoi_khong_doi_gi_thi_khong_ghi_lai(conn):
    """Khay sạch -> trả False -> `api_offline_doc` không ghi đè file. Ghi lại
    mỗi lần đọc là mở cửa cho đúng loại race mà lỗi này sinh ra."""
    from autoedit.offline import dung

    hd = _hd(chon=1)
    for cho in (hd["khoi"][0], hd["hinh"][0]):
        cho["uv"] = [u for u in cho["uv"] if u["t1"]]      # bỏ mục hỏng
        cho["chon"] = 1
    assert dung.lam_tuoi_ref(hd, conn) is False


# ---------------------------------------------------------------------------
# LỖI THẬT của team (08/09): "đổi hình xong F5 lại về mặc định", mà user thử
# thì KHÔNG bị.
#
# Đo trên hợp đồng thật: 5/9 chương có `nguoi_tao = 'bot'` — cả tập LI103 nộp
# dưới tên đó. Luật "chỉ người NỘP TẬP được sửa" (user chốt 07/09) vì thế khoá
# cửa với mọi người trừ admin. User là admin nên qua được; đồng nghiệp thì
# không.
#
# Luật ĐÚNG, cách hỏng thì SAI: giao diện cho đổi hình, hiện lên màn hình, rồi
# 700ms sau autosave mới ăn 403 — toast chớp một cái rồi trôi, F5 là mất. Phải
# biết ngay lúc MỞ chương là mình chỉ được xem.

@pytest.fixture
def may_chu_quyen(tmp_path, monkeypatch):
    import json

    from fastapi.testclient import TestClient

    from autoedit.sotra import db as sdb
    from autoedit.web import server

    monkeypatch.setattr(sdb, "resolve_data_root", lambda *a, **k: tmp_path)
    monkeypatch.setenv("RENDERY_TRUST_PROXY", "1")
    d = tmp_path / "projects" / "c4-test"
    d.mkdir(parents=True)
    hd = _hd(chon=1)
    hd["nguoi_tao"] = "bot"
    (d / "offline.json").write_text(json.dumps(hd, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(server, "PROJECTS_DIR", d.parent)
    # header danh tính chỉ được tin khi client là LOOPBACK (_trust_proxy)
    return TestClient(server.app, client=("127.0.0.1", 51000)), d.name


def _dau(user: str, vai: str = "manager") -> dict:
    return {"X-Forwarded-Host": "crm.local", "X-Remote-User": user,
            "X-Remote-Role": vai}


def test_doc_hop_dong_noi_ro_duoc_sua_hay_khong(may_chu_quyen):
    """Người không phải chủ sequence phải biết NGAY lúc mở là chỉ xem."""
    tc, pid = may_chu_quyen
    r = tc.get(f"/api/offline/{pid}", headers=_dau("thanhdn"))
    assert r.status_code == 200, r.text
    assert r.json()["duoc_sua"] is False, "không báo trước, người dựng sửa rồi mất công"


def test_chu_sequence_va_admin_van_sua_duoc(may_chu_quyen):
    tc, pid = may_chu_quyen
    assert tc.get(f"/api/offline/{pid}", headers=_dau("bot")).json()["duoc_sua"] is True
    assert tc.get(f"/api/offline/{pid}",
                  headers=_dau("ai_do", "admin")).json()["duoc_sua"] is True


def test_chay_truc_tiep_khong_qua_CRM_thi_mo(may_chu_quyen):
    """Ngoài CRM không có SSO — y khuôn `_gac_quyen_sua`, mở."""
    tc, pid = may_chu_quyen
    assert tc.get(f"/api/offline/{pid}").json()["duoc_sua"] is True


def test_giao_dien_khoa_ngay_luc_MO_chuong():
    """UI phải đọc `duoc_sua` lúc nạp, và chặn đổi hình khi chỉ xem — chứ không
    đợi autosave ăn 403 rồi mới biết."""
    from pathlib import Path

    h = Path("autoedit/web/static/index.html").read_text(encoding="utf-8")
    assert "duoc_sua" in h, "UI chưa đọc cờ quyền lúc nạp hợp đồng"
    i = h.index("d.onclick = () => {")
    assert "OF_KHOA_SUA" in h[i:i + 400], "click đổi hình chưa chặn khi chỉ xem"
