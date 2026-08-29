"""Test sổ nguồn footage (RenderY) — xuất cạnh draft CapCut.

User chốt: mỗi clip ghi nguồn + ID. Lý do là nỗi lo với padoma — trộn footage cắt vào
kho rồi thì không phân biệt được nữa. Test khoá: phân nhóm đúng (nhất là phân biệt
`ytref:` với path Windows `C:\\...`), tỉ trọng chính xác, và cảnh báo khi vượt trần.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from autoedit.packager.sourcebook import (
    YTREF_WARN_RATIO,
    collect_rows,
    group_of,
    render_text,
    summarize,
    write_sourcebook,
)


def _shot(beat_id, asset_key, source="pexels", path="assets/a.mp4", **kw):
    return SimpleNamespace(beat_id=beat_id, asset_key=asset_key, source=source,
                           asset_path=path, source_channel=kw.get("channel", ""),
                           licensing_flag=kw.get("flag", False), peak=kw.get("peak", False))


def _beat(beat_id, start=0.0, end=5.0, chapter=1):
    return SimpleNamespace(beat_id=beat_id, start=start, end=end, chapter=chapter)


def _project(shots, beats, pid="test-video"):
    return SimpleNamespace(project_id=pid, shots=shots, beats=beats)


# ------------------------------ group_of ------------------------------------
def test_phan_nhom_theo_tien_to():
    assert group_of("pexels:123") == "stock"
    assert group_of("pixabay:9") == "stock"
    assert group_of("envato:abc") == "sub"
    assert group_of("vecteezy:x") == "sub"
    assert group_of("ytref:VID@t=1.0-5.0") == "ytref"
    assert group_of("local:kho/a.mp4") == "local"


def test_path_windows_khong_bi_nham_la_provider():
    """`C:\\kho\\a.mp4` có dấu ':' nhưng prefix 1 chữ cái -> là file local."""
    assert group_of(r"C:\kho\a.mp4") == "local"
    assert group_of(r"D:/footage/b.mov") == "local"


def test_khoa_rong_va_la_vao_other():
    assert group_of("") == "other"
    assert group_of("nguonla:1") == "other"


# ------------------------------ collect_rows --------------------------------
def test_bo_qua_beat_chua_co_footage():
    shots = [_shot(1, "pexels:1"), _shot(2, "", source="none", path=None)]
    rows = collect_rows(_project(shots, [_beat(1), _beat(2)]))
    assert [r["beat_id"] for r in rows] == [1]


def test_lay_duration_tu_beat():
    rows = collect_rows(_project([_shot(1, "pexels:1")], [_beat(1, 10.0, 17.5)]))
    assert rows[0]["duration"] == pytest.approx(7.5)


def test_beat_thieu_khong_no():
    """Shot trỏ beat không tồn tại -> duration 0, KHÔNG crash cả sổ."""
    rows = collect_rows(_project([_shot(9, "pexels:1")], []))
    assert rows[0]["duration"] == 0.0


def test_giu_co_phap_ly_va_diem_nho():
    rows = collect_rows(_project(
        [_shot(1, "ytref:V@t=1-5", source="ytref", flag=True, peak=True)], [_beat(1)]))
    assert rows[0]["licensing_flag"] is True and rows[0]["peak"] is True


# ------------------------------ summarize -----------------------------------
def test_ti_trong_dung():
    rows = collect_rows(_project(
        [_shot(1, "pexels:1"), _shot(2, "envato:2"), _shot(3, "ytref:V@t=1-5")],
        [_beat(1, 0, 10), _beat(2, 10, 20), _beat(3, 20, 25)]))
    s = summarize(rows)
    assert s["stock"]["seconds"] == 10.0
    assert s["sub"]["seconds"] == 10.0
    assert s["ytref"]["ratio"] == pytest.approx(0.2)   # 5 / 25
    assert sum(g["clips"] for g in s.values()) == 3


def test_sap_theo_thoi_luong_giam_dan():
    rows = collect_rows(_project(
        [_shot(1, "ytref:V@t=1-5"), _shot(2, "pexels:2")],
        [_beat(1, 0, 30), _beat(2, 30, 35)]))
    assert list(summarize(rows)) == ["ytref", "stock"]


def test_so_rong_khong_chia_0():
    assert summarize([]) == {}


# ------------------------------ render_text ---------------------------------
def test_canh_bao_khi_ytref_vuot_tran():
    rows = collect_rows(_project(
        [_shot(1, "ytref:V@t=1-5", source="ytref"), _shot(2, "pexels:2")],
        [_beat(1, 0, 50), _beat(2, 50, 60)]))          # ytref 50/60 = 83%
    txt = render_text(rows, summarize(rows), "vid")
    assert "VƯỢT TRẦN" in txt


def test_khong_canh_bao_khi_duoi_tran():
    rows = collect_rows(_project(
        [_shot(1, "ytref:V@t=1-5", source="ytref"), _shot(2, "pexels:2")],
        [_beat(1, 0, 5), _beat(2, 5, 100)]))           # ytref 5/100 = 5%
    txt = render_text(rows, summarize(rows), "vid")
    assert "VƯỢT TRẦN" not in txt
    assert "Footage cắt từ YouTube" in txt             # vẫn nêu tỉ lệ
    assert YTREF_WARN_RATIO == 0.15


def test_khong_co_ytref_thi_khong_nhac_toi():
    rows = collect_rows(_project([_shot(1, "pexels:1")], [_beat(1)]))
    assert "YouTube" not in render_text(rows, summarize(rows), "vid")


def test_liet_ke_clip_can_duyet_ban_quyen():
    rows = collect_rows(_project(
        [_shot(1, "entity:img1", source="entity", flag=True)], [_beat(1)]))
    txt = render_text(rows, summarize(rows), "vid")
    assert "cần người duyệt bản quyền" in txt and "entity:img1" in txt


# ------------------------------ write_sourcebook ----------------------------
def test_xuat_2_file_canh_draft(tmp_path):
    project = _project([_shot(1, "pexels:1"), _shot(2, "ytref:V@t=2.0-9.0", source="ytref")],
                       [_beat(1, 0, 10), _beat(2, 10, 17)])
    js, txt = write_sourcebook(project, tmp_path / "DRAFT")

    assert js.name == "nguon_footage.json" and txt.name == "nguon_footage.txt"
    data = json.loads(js.read_text(encoding="utf-8"))
    assert data["project_id"] == "test-video"
    assert len(data["clips"]) == 2
    assert data["summary"]["stock"]["clips"] == 1
    # asset_key giữ nguyên -> truy ngược được cắt từ video nào, giây nào
    assert any(c["asset_key"] == "ytref:V@t=2.0-9.0" for c in data["clips"])
    assert "SỔ NGUỒN FOOTAGE" in txt.read_text(encoding="utf-8")


def test_tao_thu_muc_neu_chua_co(tmp_path):
    project = _project([_shot(1, "pexels:1")], [_beat(1)])
    js, _ = write_sourcebook(project, tmp_path / "a" / "b" / "DRAFT")
    assert js.is_file()


def test_project_khong_co_clip_nao_van_xuat_duoc(tmp_path):
    js, txt = write_sourcebook(_project([], []), tmp_path / "DRAFT")
    assert json.loads(js.read_text(encoding="utf-8"))["clips"] == []
    assert "0 clip" in txt.read_text(encoding="utf-8")
