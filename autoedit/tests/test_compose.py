"""Test gom kết quả ra Compose Timeline (bước 4 — tích hợp CRM).

Đây là thứ nhân sự thật sự cầm về máy, nên test khoá: gom đủ 3 thứ (draft +
footage + sổ nguồn), tên thư mục theo TÊN CHƯƠNG nhân sự đặt (không phải
project_id máy sinh), và lỗi gom KHÔNG được làm mất phần đã dựng.
"""

from __future__ import annotations

import json

import pytest

from autoedit.web.compose import (
    ComposeError,
    compose_chapter,
    compose_job,
    write_readme,
)


def _project(root, pid, *, draft=True, footage=2, thieu=0, tong=5, warns=None):
    """Dựng 1 project giả đủ để gom."""
    pdir = root / "projects" / pid
    (pdir / "assets").mkdir(parents=True)
    for i in range(footage):
        (pdir / "assets" / f"clip_{i}.mp4").write_bytes(b"\x00" * 100)

    draft_dir = root / "drafts" / pid.upper()
    if draft:
        draft_dir.mkdir(parents=True)
        (draft_dir / "draft_content.json").write_text('{"duration":1}', encoding="utf-8")
        (draft_dir / "materials").mkdir()
        (draft_dir / "materials" / "a.mp4").write_bytes(b"\x00" * 50)
        (draft_dir / "nguon_footage.txt").write_text("SỔ NGUỒN", encoding="utf-8")
        (draft_dir / "nguon_footage.json").write_text("[]", encoding="utf-8")

    report = pdir / "report.html"
    report.write_text("<h1>report</h1>", encoding="utf-8")

    shots = [{"beat_id": i, "asset_path": None if i < thieu else f"assets/clip.mp4"}
             for i in range(tong)]
    (pdir / "project.json").write_text(json.dumps({
        "project_id": pid, "shots": shots,
        "draft_path": str(draft_dir) if draft else "",
        "report_path": str(report),
        "stages": {"source": {"warnings": warns or []}},
    }), encoding="utf-8")
    return pdir


# ------------------------------ 1 chương ------------------------------------
def test_gom_du_draft_footage_so_nguon(tmp_path):
    p = _project(tmp_path, "ch01-x", footage=3)
    dest = tmp_path / "out" / "ch01"
    info = compose_chapter(p, dest)

    assert (dest / "draft" / "draft_content.json").is_file()
    assert (dest / "draft" / "materials" / "a.mp4").is_file()
    assert len(list((dest / "footage").iterdir())) == 3
    assert (dest / "report.html").is_file()
    # sổ nguồn kéo lên cấp chương cho dễ thấy
    assert (dest / "nguon_footage.txt").read_text(encoding="utf-8") == "SỔ NGUỒN"
    assert info["footage"] == 3 and info["draft"] >= 2


def test_dem_dung_so_beat_thieu_clip(tmp_path):
    p = _project(tmp_path, "ch01-x", thieu=2, tong=5)
    info = compose_chapter(p, tmp_path / "out")
    assert info["thieu_clip"] == 2 and info["so_beat"] == 5


def test_chua_co_draft_van_gom_duoc_phan_con_lai(tmp_path):
    """Assemble lỗi -> vẫn giao footage + report, chỉ cảnh báo."""
    p = _project(tmp_path, "ch01-x", draft=False)
    dest = tmp_path / "out"
    info = compose_chapter(p, dest)
    assert not (dest / "draft").exists()
    assert (dest / "footage").is_dir()
    assert any("chưa có draft" in c for c in info["canh_bao"])


def test_giu_canh_bao_cua_stage(tmp_path):
    p = _project(tmp_path, "ch01-x", warns=["Timestamp vượt duration"])
    info = compose_chapter(p, tmp_path / "out")
    assert any("Timestamp" in c for c in info["canh_bao"])


def test_project_hong_bao_loi_ro(tmp_path):
    (tmp_path / "trong").mkdir()
    with pytest.raises(ComposeError, match="project.json"):
        compose_chapter(tmp_path / "trong", tmp_path / "out")


def test_project_json_khong_parse_duoc(tmp_path):
    p = tmp_path / "hong"
    p.mkdir()
    (p / "project.json").write_text("{khong phai json", encoding="utf-8")
    with pytest.raises(ComposeError):
        compose_chapter(p, tmp_path / "out")


# ------------------------------ cả job --------------------------------------
def _inbox_job(root, ten, chuong):
    d = root / "_INBOX" / ten
    for c in chuong:
        cd = d / c
        cd.mkdir(parents=True)
        (cd / "script.txt").write_text("x", encoding="utf-8")
        (cd / "voice.mp3").write_bytes(b"\x00")
    return d


def test_gom_nhieu_chuong_dat_ten_theo_INBOX(tmp_path):
    """Thư mục kết quả mang TÊN CHƯƠNG nhân sự đặt, không phải project_id máy sinh."""
    job = _inbox_job(tmp_path, "LI070-Han-Quoc", ["ch01", "ch02"])
    p1 = _project(tmp_path, "li070-20260830-01")
    p2 = _project(tmp_path, "li070-20260830-02")

    dest = compose_job(job, [p1, p2], tmp_path / "Compose Timeline")

    assert dest.name == "LI070-Han-Quoc"
    assert sorted(d.name for d in dest.iterdir() if d.is_dir()) == ["ch01", "ch02"]
    assert (dest / "ch01" / "draft").is_dir()
    assert (dest / "DOC_TRUOC.txt").is_file()


def test_dung_lai_lan_2_khong_lan_ket_qua_cu(tmp_path):
    job = _inbox_job(tmp_path, "LI070", ["ch01"])
    p1 = _project(tmp_path, "p1")
    out = tmp_path / "Compose Timeline"

    dest = compose_job(job, [p1], out)
    (dest / "ch01" / "rac_cu.txt").write_text("cũ", encoding="utf-8")
    compose_job(job, [p1], out)

    assert not (dest / "ch01" / "rac_cu.txt").exists()


def test_1_chuong_hong_khong_chan_chuong_khac(tmp_path):
    job = _inbox_job(tmp_path, "LI070", ["ch01", "ch02"])
    p1 = _project(tmp_path, "p1")
    hong = tmp_path / "projects" / "hong"
    hong.mkdir(parents=True)                       # thiếu project.json

    dest = compose_job(job, [hong, p1], tmp_path / "out")
    doc = (dest / "DOC_TRUOC.txt").read_text(encoding="utf-8")
    assert (dest / "ch02" / "draft").is_dir()      # chương lành vẫn giao
    assert "project.json" in doc                   # chương hỏng được nêu rõ


def test_it_project_hon_so_chuong_van_chay(tmp_path):
    """Job dừng giữa chừng -> chỉ có project của chương đã xong."""
    job = _inbox_job(tmp_path, "LI070", ["ch01", "ch02", "ch03"])
    dest = compose_job(job, [_project(tmp_path, "p1")], tmp_path / "out")
    assert [d.name for d in dest.iterdir() if d.is_dir()] == ["ch01"]


# ------------------------------ DOC_TRUOC -----------------------------------
def test_doc_truoc_co_huong_dan_va_trang_thai(tmp_path):
    p = write_readme(tmp_path / "out", "/nas/_INBOX/LI070", [
        {"ten": "ch01", "thieu_clip": 0, "so_beat": 8, "footage": 12, "canh_bao": []},
        {"ten": "ch02", "thieu_clip": 3, "so_beat": 9, "footage": 6,
         "canh_bao": ["source: hết hạn mức Pexels"]},
    ])
    txt = p.read_text(encoding="utf-8")

    assert "LI070" in txt
    assert "Copy CẢ THƯ MỤC" in txt
    assert "ch01" in txt and "OK" in txt
    assert "THIẾU 3/9 clip" in txt
    assert "hết hạn mức Pexels" in txt
    # nêu rõ tổng số chỗ thiếu + cách nhận ra trong CapCut
    assert "Còn 3 chỗ chưa có footage" in txt
    assert "ĐẮP FOOTAGE Ở ĐÂY" in txt


def test_doc_truoc_khong_thieu_gi_thi_khong_canh_bao(tmp_path):
    p = write_readme(tmp_path / "out", "/nas/LI070", [
        {"ten": "ch01", "thieu_clip": 0, "so_beat": 5, "footage": 9, "canh_bao": []}])
    assert "chưa có footage" not in p.read_text(encoding="utf-8")
