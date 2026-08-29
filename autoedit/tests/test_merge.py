"""Test gộp draft các chương thành draft tổng (RenderY R7).

Quy trình user là tuyến tính theo chương, mỗi chương ra 1 draft. Gộp = nối tiếp theo
thời gian. Chỗ dễ vỡ nhất: id material trùng giữa 2 draft (segment trỏ theo id), và
offset thời gian (sai là lệch tiếng-hình toàn bộ chương sau).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoedit.packager.merge import (
    draft_duration,
    merge_contents,
    merge_drafts,
    merge_sourcebooks,
    read_draft,
)
from autoedit.packager.packager import PackageError


def _content(dur_us: int, mat_id: str = "m1", seg_id: str = "s1",
             track_name: str = "video_l1", extra_ref: str = "e1") -> dict:
    return {
        "id": "OLD-ID",
        "duration": dur_us,
        "fps": 30,
        "canvas_config": {"width": 1920, "height": 1080},
        "materials": {
            "videos": [{"id": mat_id, "path": "##_ph_##/materials/a.mp4"}],
            "speeds": [{"id": extra_ref, "speed": 1.0}],
        },
        "tracks": [{
            "type": "video", "name": track_name,
            "segments": [{
                "id": seg_id, "material_id": mat_id,
                "extra_material_refs": [extra_ref],
                "target_timerange": {"start": 0, "duration": dur_us},
                "source_timerange": {"start": 0, "duration": dur_us},
            }],
        }],
    }


def _write_draft(root: Path, name: str, content: dict, media: str = "a.mp4") -> Path:
    d = root / name
    (d / "materials").mkdir(parents=True)
    (d / "materials" / media).write_bytes(b"x" * 100)
    (d / "draft_content.json").write_text(json.dumps(content), encoding="utf-8")
    (d / "draft_meta_info.json").write_text(
        json.dumps({"draft_name": name, "draft_id": "OLD"}), encoding="utf-8")
    return d


# ------------------------------ đọc / duration ------------------------------
def test_thieu_draft_content_bao_loi(tmp_path):
    (tmp_path / "rong").mkdir()
    with pytest.raises(PackageError, match="Không thấy draft_content"):
        read_draft(tmp_path / "rong")


def test_json_hong_bao_loi_ro(tmp_path):
    d = tmp_path / "hong"
    d.mkdir()
    (d / "draft_content.json").write_text("{khong phai json", encoding="utf-8")
    with pytest.raises(PackageError, match="hỏng"):
        read_draft(d)


def test_duration_suy_tu_segment_khi_thieu_truong():
    c = _content(5_000_000)
    del c["duration"]
    assert draft_duration(c) == 5_000_000


# ------------------------------ merge_contents ------------------------------
def test_chuong_sau_dich_dung_offset():
    """Sai offset = lệch tiếng-hình TOÀN BỘ chương sau — luật cứng nhất."""
    a, b = _content(10_000_000), _content(7_000_000)
    m = merge_contents([a, b])
    starts = [s["target_timerange"]["start"] for s in m["tracks"][0]["segments"]]
    assert starts == [0, 10_000_000]
    assert m["duration"] == 17_000_000


def test_ba_chuong_cong_don():
    m = merge_contents([_content(5_000_000), _content(3_000_000), _content(2_000_000)])
    starts = [s["target_timerange"]["start"] for s in m["tracks"][0]["segments"]]
    assert starts == [0, 5_000_000, 8_000_000]
    assert m["duration"] == 10_000_000


def test_source_timerange_KHONG_bi_dich():
    """Chỉ dịch target (vị trí trên timeline), source là mốc trong file gốc."""
    m = merge_contents([_content(10_000_000), _content(5_000_000)])
    for seg in m["tracks"][0]["segments"]:
        assert seg["source_timerange"]["start"] == 0


def test_id_material_trung_thi_doi_id_draft_sau():
    """Segment trỏ material theo id — trùng id giữa 2 chương là hỏng hình."""
    a = _content(1_000_000, mat_id="SAME", extra_ref="REF")
    b = _content(1_000_000, mat_id="SAME", extra_ref="REF")
    m = merge_contents([a, b])

    ids = [v["id"] for v in m["materials"]["videos"]]
    assert len(set(ids)) == 2                      # không còn trùng
    segs = m["tracks"][0]["segments"]
    assert {s["material_id"] for s in segs} == set(ids)   # mỗi segment trỏ đúng material
    refs = [s["extra_material_refs"][0] for s in segs]
    assert len(set(refs)) == 2
    assert set(refs) == {sp["id"] for sp in m["materials"]["speeds"]}


def test_id_khac_nhau_thi_giu_nguyen():
    a = _content(1_000_000, mat_id="A", extra_ref="RA")
    b = _content(1_000_000, mat_id="B", extra_ref="RB")
    m = merge_contents([a, b])
    assert {v["id"] for v in m["materials"]["videos"]} == {"A", "B"}


def test_track_gop_theo_ten():
    m = merge_contents([_content(1_000_000), _content(1_000_000)])
    assert len(m["tracks"]) == 1                   # cùng tên video_l1 -> 1 track
    assert len(m["tracks"][0]["segments"]) == 2


def test_track_chi_co_o_chuong_sau_duoc_them_moi():
    a = _content(1_000_000, track_name="video_l1")
    b = _content(1_000_000, track_name="text", mat_id="m2", extra_ref="e2")
    b["tracks"][0]["type"] = "text"
    m = merge_contents([a, b])
    assert {t["name"] for t in m["tracks"]} == {"video_l1", "text"}


def test_trung_ten_khac_type_thi_khong_gop_nham():
    a = _content(1_000_000, track_name="x")
    b = _content(1_000_000, track_name="x", mat_id="m2", extra_ref="e2")
    b["tracks"][0]["type"] = "audio"
    m = merge_contents([a, b])
    assert len(m["tracks"]) == 2


def test_segment_sap_theo_thoi_gian():
    m = merge_contents([_content(9_000_000), _content(1_000_000)])
    starts = [s["target_timerange"]["start"] for s in m["tracks"][0]["segments"]]
    assert starts == sorted(starts)


def test_draft_tong_co_id_moi():
    """C1: draft mới = timeline mới -> id mới, không mượn id draft nguồn."""
    m = merge_contents([_content(1_000_000), _content(1_000_000)])
    assert m["id"] != "OLD-ID" and len(m["id"]) == 36


def test_khong_sua_part_tai_cho():
    a, b = _content(1_000_000), _content(2_000_000)
    merge_contents([a, b])
    assert b["tracks"][0]["segments"][0]["target_timerange"]["start"] == 0
    assert a["id"] == "OLD-ID"


def test_rong_bao_loi():
    with pytest.raises(PackageError, match="Không có draft"):
        merge_contents([])


# ------------------------------ merge_drafts --------------------------------
def test_gop_2_draft_that(tmp_path):
    d1 = _write_draft(tmp_path, "CH01", _content(6_000_000, mat_id="A", extra_ref="RA"))
    d2 = _write_draft(tmp_path, "CH02", _content(4_000_000, mat_id="B", extra_ref="RB"))
    out = merge_drafts([d1, d2], tmp_path / "TONG")

    content = json.loads((out / "draft_content.json").read_text(encoding="utf-8"))
    assert content["duration"] == 10_000_000
    assert (out / "draft_info.json").is_file()
    assert (out / "materials" / "a.mp4").is_file()

    meta = json.loads((out / "draft_meta_info.json").read_text(encoding="utf-8"))
    assert meta["draft_name"] == "TONG" and meta["draft_id"] != "OLD"


def test_media_trung_ten_khac_noi_dung_thi_doi_ten(tmp_path):
    d1 = _write_draft(tmp_path, "CH01", _content(1_000_000, mat_id="A", extra_ref="RA"))
    c2 = _content(1_000_000, mat_id="B", extra_ref="RB")
    c2["materials"]["videos"][0]["path"] = "##_ph_##/materials/a.mp4"
    d2 = _write_draft(tmp_path, "CH02", c2)
    (d2 / "materials" / "a.mp4").write_bytes(b"y" * 500)   # khác kích thước

    out = merge_drafts([d1, d2], tmp_path / "TONG")
    assert (out / "materials" / "a.mp4").is_file()
    assert (out / "materials" / "a_1.mp4").is_file()
    content = json.loads((out / "draft_content.json").read_text(encoding="utf-8"))
    paths = [v["path"] for v in content["materials"]["videos"]]
    assert any(p.endswith("a_1.mp4") for p in paths)       # path đã sửa theo tên mới


def test_media_giong_het_thi_khong_nhan_ban(tmp_path):
    d1 = _write_draft(tmp_path, "CH01", _content(1_000_000, mat_id="A", extra_ref="RA"))
    d2 = _write_draft(tmp_path, "CH02", _content(1_000_000, mat_id="B", extra_ref="RB"))
    out = merge_drafts([d1, d2], tmp_path / "TONG")
    assert len(list((out / "materials").iterdir())) == 1


def test_can_it_nhat_2_draft(tmp_path):
    d1 = _write_draft(tmp_path, "CH01", _content(1_000_000))
    with pytest.raises(PackageError, match="ít nhất 2"):
        merge_drafts([d1], tmp_path / "TONG")


def test_khong_de_draft_da_co(tmp_path):
    """C5: CapCut cache draft_id theo folder — đè làm draft không mở được."""
    d1 = _write_draft(tmp_path, "CH01", _content(1_000_000, mat_id="A", extra_ref="RA"))
    d2 = _write_draft(tmp_path, "CH02", _content(1_000_000, mat_id="B", extra_ref="RB"))
    (tmp_path / "TONG").mkdir()
    with pytest.raises(PackageError, match="đã tồn tại"):
        merge_drafts([d1, d2], tmp_path / "TONG")
    merge_drafts([d1, d2], tmp_path / "TONG", overwrite=True)   # có cờ thì được


# ------------------------------ sổ nguồn ------------------------------------
def test_gop_so_nguon_va_danh_so_chuong(tmp_path):
    for i, name in enumerate(("CH01", "CH02"), start=1):
        d = _write_draft(tmp_path, name, _content(1_000_000))
        (d / "nguon_footage.json").write_text(json.dumps({"clips": [
            {"beat_id": i, "asset_key": f"pexels:{i}", "group": "stock",
             "duration": 5.0, "licensing_flag": False, "peak": False, "chapter": 0}]}),
            encoding="utf-8")
    out = tmp_path / "TONG"
    out.mkdir()
    txt = merge_sourcebooks([tmp_path / "CH01", tmp_path / "CH02"], out)

    assert txt is not None
    data = json.loads((out / "nguon_footage.json").read_text(encoding="utf-8"))
    assert [c["chapter"] for c in data["clips"]] == [1, 2]   # đánh số theo thứ tự gộp
    assert data["summary"]["stock"]["clips"] == 2


def test_khong_chuong_nao_co_so_thi_tra_none(tmp_path):
    d1 = _write_draft(tmp_path, "CH01", _content(1_000_000))
    d2 = _write_draft(tmp_path, "CH02", _content(1_000_000))
    out = tmp_path / "TONG"
    out.mkdir()
    assert merge_sourcebooks([d1, d2], out) is None
