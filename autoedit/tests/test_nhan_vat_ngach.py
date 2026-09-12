r"""NHÂN VẬT CỦA NGÁCH — khoá logic từng ngách trước khi dựng (user chốt 12/09).

Vì sao có file này. Đo thật trên SH010 (Senior Health, 116 khối): đọc hình 116
miếng tool đang chọn thì chỉ **8 miếng** có người già da trắng, 77 miếng KHÔNG
CÓ NGƯỜI NÀO, 29 miếng người trẻ/trung niên. Nguyên nhân không phải xếp hạng
kém — mà không chỗ nào trong tool biết "ngách này quay AI".

User mô phỏng lại cách một editor làm:
  1. AI      — ngách quyết định người trong khung (Senior Health: già 60+, Mỹ
               hoặc da trắng). Đây là HẰNG SỐ của ngách, không đổi theo câu.
  2. OBJECT  — vật thể nhắc trong câu (cốc nước, bệnh tim).
  3. cảnh cận— câu nào không tả được bằng 1+2 thì dùng cảnh cận.

Chốt: nhân vật khai Ở RENDERY (cùng khuôn QĐ13 với cờ địa danh — danh bạ nền là
sổ của CRM, RenderY thêm cột vào đó là lấn sân), sửa được qua `.env` +
trang Cài đặt, và **chưa khai thì không cho nộp tập**.

Ngách gắn địa lý (LIFE IN · LIVING IN · TRAVEL DOCUMENTARY) KHỎI khai: nhân vật
của chúng là "người dân địa danh đó", mà cửa geo hiện có đã làm đúng việc ấy —
khai thêm là hai luật cho một khái niệm (BH4).
"""

from __future__ import annotations

import json
import sqlite3

import pytest

NGACH_THAT = [                      # sao y danh bạ nền 12/09
    ("N-COOKING", "COOKING", "khai_thac"),
    ("N-LIFE-IN", "LIFE IN", "mo_rong"),
    ("N-LIVING-IN", "LIVING IN", "khai_thac"),
    ("N-SENIOR-HEALTH", "SENIOR HEALTH", "khai_thac"),
    ("N-TRAVEL-DOCUMENTA", "TRAVEL DOCUMENTARY", "khai_thac"),
]


@pytest.fixture
def danh_ba(tmp_path, monkeypatch):
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
    return f


# ------------------------------------------------------------------ khai báo

def test_senior_health_da_khai_gia_60_va_da_trang(danh_ba):
    """Đúng lời user 12/09: "Senior là người già 60+, Mỹ hoặc da trắng"."""
    from autoedit import ngach

    nv = ngach.nhan_vat("SENIOR HEALTH")
    assert nv["tuoi"] == ["older"]
    assert nv["chung_toc"] == ["white"]


def test_nhan_ca_MA_lan_TEN(danh_ba):
    from autoedit import ngach

    assert ngach.nhan_vat("N-SENIOR-HEALTH") == ngach.nhan_vat("senior health")


def test_ngach_chua_khai_thi_tra_RONG(danh_ba):
    from autoedit import ngach

    assert ngach.nhan_vat("COOKING") == {}


def test_ngach_gan_dia_ly_KHOI_khai(danh_ba):
    """Nhân vật của LIFE IN là "người dân nơi đó" — cửa geo đã làm việc ấy."""
    from autoedit import ngach

    for x in ("LIFE IN", "LIVING IN", "TRAVEL DOCUMENTARY"):
        assert ngach.da_khai_nhan_vat(x) is True, x


def test_ngach_khong_gan_dia_ly_ma_chua_khai_thi_CHUA_KHAI(danh_ba):
    from autoedit import ngach

    assert ngach.da_khai_nhan_vat("COOKING") is False
    assert ngach.da_khai_nhan_vat("SENIOR HEALTH") is True


def test_env_de_duoc_khai_bao(danh_ba, monkeypatch):
    """Khai thêm ngách mới KHÔNG phải sửa code — y khuôn RENDERY_NGACH_GEO."""
    from autoedit import ngach

    monkeypatch.setenv("RENDERY_NGACH_NHAN_VAT", json.dumps(
        {"N-COOKING": {"tuoi": ["young", "middle"]}}))
    assert ngach.nhan_vat("COOKING") == {"tuoi": ["young", "middle"]}
    assert ngach.da_khai_nhan_vat("COOKING") is True
    # khai ở env KHÔNG được xoá mất bản mặc định của ngách khác
    assert ngach.nhan_vat("SENIOR HEALTH")["tuoi"] == ["older"]


def test_env_rac_KHONG_lam_chet_viec(danh_ba, monkeypatch):
    """`.env` gõ sai là chuyện thường. Nổ ở đây = cả team không nộp được tập."""
    from autoedit import ngach

    monkeypatch.setenv("RENDERY_NGACH_NHAN_VAT", "{day khong phai json")
    assert ngach.nhan_vat("SENIOR HEALTH")["tuoi"] == ["older"]


def test_so_hong_thi_MO_khong_chan(tmp_path, monkeypatch):
    """CRM tắt / ổ D chưa gắn -> không có cơ sở để bác. Chặn thì cả team đứng
    việc (cùng lý lẽ với `hop_le`)."""
    from autoedit import ngach

    monkeypatch.setenv("RENDERY_DANH_BA", str(tmp_path / "khong-co.db"))
    assert ngach.da_khai_nhan_vat("bất kỳ") is True


# ------------------------------------------------------- cổng nộp tập

@pytest.fixture
def may_chu(danh_ba, tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from autoedit.web import queue as q, server

    monkeypatch.setattr(server, "ROOT", tmp_path)
    nas = tmp_path / "nas"
    tap = nas / "SH300"
    (tap / "RenderY").mkdir(parents=True)
    for ten in ("H", "C1", "E"):
        (tap / "RenderY" / f"{ten}.mp3").write_bytes(b"x" * 64)
        (tap / "RenderY" / f"{ten}.txt").write_text("xin chao", encoding="utf-8")
    monkeypatch.setattr(server, "_trong_nas", lambda p: tap)
    q.connect(tmp_path / "jobs.db").close()
    return TestClient(server.app), str(tap)


def test_nop_tap_ngach_CHUA_KHAI_nhan_vat_bi_chan(may_chu):
    """Đây chính là "khoá logic từng ngách trước khi dựng"."""
    tc, folder = may_chu
    r = tc.post("/api/jobs", json={"folder": folder, "niche": "COOKING",
                                   "dia_danh": ""})
    assert r.status_code == 422, r.text
    assert "nhân vật" in r.json()["detail"].lower()


def test_nop_tap_ngach_DA_KHAI_thi_qua(may_chu):
    tc, folder = may_chu
    r = tc.post("/api/jobs", json={"folder": folder, "niche": "SENIOR HEALTH",
                                   "dia_danh": ""})
    assert r.status_code == 200, r.text


def test_api_ngach_bao_ngach_nao_da_khai(may_chu):
    """Form nộp tập phải NÓI RÕ ngách nào chưa khai, không để người bấm rồi mới
    ăn 422 (cùng lý lẽ với cờ `can_dia_danh` đã có trên API này)."""
    tc, _ = may_chu
    d = tc.get("/api/ngach").json()
    theo_ten = {x["ten"]: x for x in d["ngach"]}
    assert theo_ten["SENIOR HEALTH"]["da_khai_nhan_vat"] is True
    assert theo_ten["COOKING"]["da_khai_nhan_vat"] is False
    assert theo_ten["LIFE IN"]["da_khai_nhan_vat"] is True


# ------------------------------------------------------- giao diện
# Mockup đối chiếu: scratchpad/ui_nhan_vat.html (luật user: UI phải có mockup
# đặt cạnh code). Ở đây chỉ soi CHUỖI — JS chạy thật thì kiểm bằng Chrome
# (bài học BH28 11/09: 7/7 test chuỗi xanh mà cả file JS chết).

def _trang() -> str:
    from pathlib import Path

    import autoedit.web.server as sv

    return (Path(sv.__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


def test_form_noi_ro_ngach_chua_khai():
    s = _trang()
    assert "chưa khai nhân vật" in s
    assert "da_khai_nhan_vat" in s
    assert "ns-nhan-vat" in s


def test_khay_co_nhan_tang():
    """Editor phải THẤY vì sao một thẻ được máy lấy hay không."""
    s = _trang()
    assert ".of-uv .tang{" in s and ".of-uv .tA{" in s and ".of-uv.mo{" in s
    assert "u.tang" in s


def test_the_tang_TRU_chi_lam_MO_chu_khong_an():
    """Kho còn nghèo (64/548 clip khay SH010 đạt cửa người) — bịt mắt người dựng
    là hỏng việc. Phải là `mo`, không phải `hidden`/`display:none`."""
    s = _trang()
    i = s.index("d.className = 'of-uv'")
    doan = s[i:i + 240]
    assert "' mo'" in doan and "display:none" not in doan
