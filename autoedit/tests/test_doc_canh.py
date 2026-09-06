# -*- coding: utf-8 -*-
"""Đọc nội dung cảnh ref bằng GLM — test tiêm hàm gọi, KHÔNG chạm mạng."""
from pathlib import Path

from autoedit.sotra.doc_canh import DocRa, _go_json, doc_lo, doc_nhieu


def test_go_json_boc_rao_markdown():
    assert _go_json('```json\n{"canh":[{"i":1}]}\n```')["canh"][0]["i"] == 1
    assert _go_json('Đây:\n{"canh":[]} xong')["canh"] == []


def test_doc_nhieu_chia_dung_lo():
    thay = []

    def goi(phan):
        thay.append(len(phan))
        return [DocRa(i=j + 1) for j in range(len(phan))]

    ra = doc_nhieu([(Path("a.jpg"), "")] * 26, lo=12, goi=goi)
    assert thay == [12, 12, 2] and len(ra) == 26


def test_lo_hong_khong_giet_ca_tap():
    """Một lô lỗi mạng thì các lô khác vẫn phải chạy — 638 cảnh không được
    mất trắng vì một lần gọi hỏng."""
    def goi(phan):
        if len(phan) == 12:
            raise RuntimeError("mạng hỏng")
        return [DocRa(i=j + 1, subject="ok") for j in range(len(phan))]

    log = []
    ra = doc_nhieu([(Path("a.jpg"), "")] * 15, lo=12, goi=goi, log=log.append)
    assert len(ra) == 15
    assert [r.subject for r in ra[:12]] == [""] * 12   # lô hỏng -> rỗng
    assert ra[12].subject == "ok"                       # lô sau vẫn chạy
    assert any("hỏng" in m for m in log)


def _anh(tmp_path, n):
    """Ảnh thật (byte bất kỳ) — doc_lo đọc file để mã hoá base64."""
    ra = []
    for i in range(n):
        f = tmp_path / f"{i}.jpg"
        f.write_bytes(bytes([255, 216, 255, 217]))
        ra.append((f, ""))
    return ra


def test_glm_bo_sot_anh_khong_lam_lech_chi_so(monkeypatch, tmp_path):
    """GLM trả thiếu ảnh 2 thì ảnh 3 KHÔNG được tụt lên vị trí 2 — lệch một
    nấc là cả kho gán nhầm nội dung."""
    import autoedit.sotra.doc_canh as m

    monkeypatch.setattr(m, "_khoa", lambda: "k")

    class _R:
        def raise_for_status(self): pass

        def json(self):
            return {"choices": [{"message": {"content":
                '{"canh":[{"i":1,"subject":"a"},{"i":3,"subject":"c"}]}'}}]}

    import requests
    monkeypatch.setattr(requests, "post", lambda *a, **k: _R())
    ra = doc_lo(_anh(tmp_path, 3))
    assert [r.subject for r in ra] == ["a", "", "c"]


def test_khop_kep_trong_0_3(monkeypatch, tmp_path):
    import requests

    import autoedit.sotra.doc_canh as m
    monkeypatch.setattr(m, "_khoa", lambda: "k")

    class _R:
        def raise_for_status(self): pass

        def json(self):
            return {"choices": [{"message": {"content":
                '{"canh":[{"i":1,"khop":9},{"i":2,"khop":-4}]}'}}]}

    monkeypatch.setattr(requests, "post", lambda *a, **k: _R())
    ra = doc_lo(_anh(tmp_path, 2))
    assert [r.khop for r in ra] == [3, 0]
