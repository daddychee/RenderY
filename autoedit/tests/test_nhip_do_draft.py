"""ĐO LẠI SAU DỰNG (user duyệt 05/09) — draft tự chấm nhịp, so hồ sơ hiệu lực.

Sinh ra từ audit 3 video 04/09: LI095 ép nhịp CHẾT im lặng (bug frozen) mà
không ai biết — hook 6.26s/1% thay vì đích 1.0s/70%. Thước này phải bắt được
đúng ca đó: chênh >50% -> cảnh báo LỆCH TO.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from autoedit.nhip.do_draft import do_nhip_draft, doi_chieu_hs
from autoedit.nhip.hieu_luc import nap_hieu_luc


def _draft(tmp_path, durs_s):
    """draft_content.json tối giản: 1 track video nền với các segment durs_s."""
    c = {"tracks": [
        {"type": "audio", "segments": [{"target_timerange": {"duration": 1}}]},
        {"type": "video", "segments": [
            {"target_timerange": {"start": 0, "duration": int(d * 1e6)}} for d in durs_s]},
    ]}
    (tmp_path / "draft_content.json").write_text(json.dumps(c), encoding="utf-8")
    return tmp_path


def _project(title="H", channel="life-in"):
    return SimpleNamespace(title=title, inputs=SimpleNamespace(
        channel=channel, kenh_ref="", original_script_path="/khong/ton/tai/x.txt"))


# ------------------------------------------------------------ do_nhip_draft
def test_do_dung_thong_ke():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        tk = do_nhip_draft(_draft(Path(d), [1.0, 1.5, 2.0, 6.0]))
    assert tk["so_shot"] == 4
    assert tk["trung_vi"] == 1.75
    assert tk["ty_le_nhanh"] == 0.75      # 3/4 shot ≤2s
    assert tk["ty_le_hold"] == 0.25       # 1/4 shot ≥5s


def test_draft_rong_nem_loi(tmp_path):
    (tmp_path / "draft_content.json").write_text(
        json.dumps({"tracks": [{"type": "video", "segments": []}]}), encoding="utf-8")
    with pytest.raises(Exception):
        do_nhip_draft(tmp_path)


# ------------------------------------------------------------ doi_chieu
def test_doi_chieu_ca_khoe_li098_khong_bao_oan():
    """LI098 thật 04/09: trung vị 1.53s (+53% — gap HỆ THỐNG sàn 0.7s/slow-mo)
    nhưng tỷ lệ nhanh 75% VƯỢT đích 70% -> video đạt, KHÔNG được réo oan
    (réo mỗi video là editor nhờn cảnh báo — ngưỡng hiệu chuẩn bằng số thật)."""
    dong = doi_chieu_hs(_project(), {"so_shot": 711, "trung_vi": 1.53,
                                     "ty_le_nhanh": 0.75, "ty_le_hold": 0.15})
    assert "LỆCH TO" not in dong
    assert "hook" in dong and "1.53s" in dong


def test_doi_chieu_bat_dung_ca_li095():
    """Ca thật LI095 04/09: hook 6.26s vs đích 1.0s (chênh +526%) — ép nhịp
    chết im lặng phải bị thước này réo tên."""
    dong = doi_chieu_hs(_project(), {"so_shot": 306, "trung_vi": 6.26,
                                     "ty_le_nhanh": 0.01, "ty_le_hold": 0.65})
    assert "LỆCH TO" in dong
    # 06/09 niche không còn đổi nhịp: đích hook = mặc định 1.2s -> +422% (vẫn réo to)
    assert "+422%" in dong or "422" in dong


def test_doi_chieu_chuong_than_dung_dich_than():
    dong = doi_chieu_hs(_project(title="C3"), {"so_shot": 50, "trung_vi": 3.4,
                                               "ty_le_nhanh": 0.3, "ty_le_hold": 0.3})
    assert "[than]" in dong
    assert "3.0s" in dong                  # đích thân MẶC ĐỊNH (06/09: niche không đổi nhịp)


# ------------------------------------------------------------ nap_hieu_luc
def test_hieu_luc_niche_khong_anh_huong_nhip():
    """User chốt 06/09: chọn kênh/niche KHÔNG được đổi logic dựng — nền luôn là
    hồ sơ trung tính, kể cả khi channel='life-in' (preset life-in từng đè 3.5s)."""
    hs, logs = nap_hieu_luc(_project())
    assert hs.ten == "_mac_dinh"
    assert hs.than_trung_vi == 3.0
    assert logs == []                      # không tầng nào áp -> im lặng


def test_hieu_luc_kenh_de_niche(tmp_path, monkeypatch):
    import autoedit.kenh.hoso as mh
    monkeypatch.setattr(mh, "resolve_data_root", lambda *a, **k: tmp_path)
    from autoedit.kenh.hoso import HoSoKenh
    HoSoKenh(ten="fern-tv", than_trung_vi=2.1, than_ty_le_nhanh=0.5,
             than_ty_le_hold=0.1, so_video_hoi_tu=2).ghi()
    p = _project()
    p.inputs.kenh_ref = "https://www.youtube.com/@fern-tv"
    hs, logs = nap_hieu_luc(p)
    assert hs.than_trung_vi == 2.1         # kênh đè niche (3.5)
    assert any("fern-tv" in x for x in logs)


def test_hieu_luc_kenh_chua_do_bao_ro():
    p = _project()
    p.inputs.kenh_ref = "https://www.youtube.com/@kenh-chua-do-bao-gio"
    hs, logs = nap_hieu_luc(p)
    assert hs.ten == "_mac_dinh"           # rơi về mặc định (06/09: hết tầng niche)
    assert any("chưa có hồ sơ" in x for x in logs)
