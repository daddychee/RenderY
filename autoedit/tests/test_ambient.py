"""Test thư viện ambient C1 (M1) — import manifest theo niche + variants + fail-open.

Khuôn theo test_sfx.py (WAV thật nhỏ + normalize_audio chạy ffmpeg thật).
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pytest
import yaml

from autoedit.ambient.library import (
    RECORDS_FILE,
    ambient_root,
    import_from_manifest,
    library_status,
    list_variants,
    niche_dir,
)


def _wav(path: Path, sec: float = 0.3) -> None:
    rate = 48000
    frames = bytearray()
    for i in range(int(sec * rate)):
        frames += struct.pack("<h", int(6000 * math.sin(2 * math.pi * 220 * i / rate)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(bytes(frames))


def _manifest(path: Path, entries: list[dict]) -> Path:
    path.write_text(yaml.safe_dump({"ambient": entries}, allow_unicode=True), encoding="utf-8")
    return path


@pytest.fixture
def niche(tmp_path):
    """Folder niche kiểu thật: file thô + manifest nằm TRONG folder (như F:\\...\\space)."""
    d = tmp_path / "ambient" / "space"
    d.mkdir(parents=True)
    _wav(d / "deep space.wav")
    _wav(d / "u u vu tru.wav")
    _wav(d / "gio bao.wav")
    return d


def test_import_in_place(niche):
    """Nguồn trong folder niche: chuẩn hóa thành <kind>_<n>.wav, thô dọn vào raw/,
    manifest input đổi thành raw/*.done.yaml, records ghi ambient_library.yaml."""
    man = _manifest(niche / "ambient_manifest.yaml", [
        {"file": "deep space.wav", "kind": "space", "artlist_url": "editor:SP1 - 001", "title": "deep space"},
        {"file": "u u vu tru.wav", "kind": "space", "artlist_url": "https://artlist.io/x", "title": "ù ù"},
        {"file": "gio bao.wav", "kind": "mountain_desert", "title": "gió bão"},
    ])
    res = import_from_manifest(man, niche, niche)
    assert len(res.imported) == 3 and not res.failed
    assert [p.name for p in list_variants("space", niche)] == ["space.wav", "space_2.wav"]
    assert [p.name for p in list_variants("mountain_desert", niche)] == ["mountain_desert.wav"]
    # thứ tự manifest = thứ tự biến thể: editor đứng đầu
    rec = yaml.safe_load((niche / RECORDS_FILE).read_text(encoding="utf-8"))["ambient"]
    assert rec[0]["file"] == "space.wav" and rec[0]["artlist_url"] == "editor:SP1 - 001"
    assert rec[0]["source_file"] == "deep space.wav"  # truy vết file gốc
    # dọn thô + manifest
    assert (niche / "raw" / "deep space.wav").is_file()
    assert not (niche / "deep space.wav").exists()
    assert (niche / "raw" / "ambient_manifest.done.yaml").is_file()
    assert not (niche / "ambient_manifest.yaml").exists()
    assert library_status(niche) == {"mountain_desert": 1, "space": 2}


def test_import_external_source_untouched(tmp_path, niche):
    """Nguồn NGOÀI folder niche (vd materials draft editor): copy-đọc, KHÔNG move."""
    ext = tmp_path / "materials"
    ext.mkdir()
    _wav(ext / "Dark Space.wav")
    man = _manifest(tmp_path / "m.yaml", [{"file": "Dark Space.wav", "kind": "space", "title": "ds"}])
    res = import_from_manifest(man, ext, niche)
    assert res.imported == ["space <- Dark Space.wav"]
    assert (ext / "Dark Space.wav").is_file()          # nguồn còn nguyên
    assert (tmp_path / "m.yaml").is_file()             # manifest ngoài không bị dọn


def test_import_rejects_bad_kind_and_missing_file(niche):
    man = _manifest(niche / "ambient_manifest.yaml", [
        {"file": "deep space.wav", "kind": "vu_tru", "title": "x"},   # kind ngoài enum
        {"file": "khong_co.wav", "kind": "space", "title": "y"},      # thiếu file
    ])
    res = import_from_manifest(man, niche, niche)
    assert res.imported == []
    assert any("không hợp lệ" in r[1] for r in res.failed)
    assert any("không thấy file" in r[1] for r in res.failed)
    # không nhập được gì -> manifest GIỮ NGUYÊN cho user sửa
    assert (niche / "ambient_manifest.yaml").is_file()


def test_import_appends_variant_numbers(niche):
    m1 = _manifest(niche / "ambient_manifest.yaml",
                   [{"file": "deep space.wav", "kind": "space", "title": "a"}])
    import_from_manifest(m1, niche, niche)
    m2 = _manifest(niche / "ambient_manifest.yaml",
                   [{"file": "u u vu tru.wav", "kind": "space", "title": "b"}])
    import_from_manifest(m2, niche, niche)
    assert [p.name for p in list_variants("space", niche)] == ["space.wav", "space_2.wav"]
    # records cộng dồn 2 lần nhập
    rec = yaml.safe_load((niche / RECORDS_FILE).read_text(encoding="utf-8"))["ambient"]
    assert len(rec) == 2


def test_subject_rules_yaml_kinds_and_import(niche):
    """Kind loài per-niche (sheet SFX editor 2026-07-13): subject_rules.yaml trong
    folder niche khai kind mới -> load_subject_rules đọc được, niche_kinds nối vào
    AMBIENT_KINDS, import chấp nhận kind mới; kind bịa vẫn bị chặn."""
    from autoedit.ambient.library import AMBIENT_KINDS, load_subject_rules, niche_kinds

    # chưa có yaml -> None (built-in), kinds = AMBIENT_KINDS nguyên bản
    assert load_subject_rules(niche) is None
    assert niche_kinds(niche) == AMBIENT_KINDS

    (niche / "subject_rules.yaml").write_text(yaml.safe_dump({"rules": [
        {"kind": "whale_sperm", "keywords": ["sperm whale", "cá nhà táng"]},
        {"kind": "ocean", "keywords": ["seagull"]},   # kind sẵn có — không nối đôi
    ]}, allow_unicode=True), encoding="utf-8")
    rules = load_subject_rules(niche)
    assert rules == (("whale_sperm", ("sperm whale", "cá nhà táng")),
                     ("ocean", ("seagull",)))
    kinds = niche_kinds(niche)
    assert "whale_sperm" in kinds and kinds.count("ocean") == 1

    man = _manifest(niche / "ambient_manifest.yaml", [
        {"file": "deep space.wav", "kind": "whale_sperm", "title": "click cá nhà táng"},
        {"file": "u u vu tru.wav", "kind": "vu_tru", "title": "kind bịa vẫn chặn"},
    ])
    res = import_from_manifest(man, niche, niche)
    assert res.imported == ["whale_sperm <- deep space.wav"]
    assert [p.name for p in list_variants("whale_sperm", niche)] == ["whale_sperm.wav"]
    assert any("không hợp lệ" in r[1] for r in res.failed)
    assert library_status(niche)["whale_sperm"] == 1


def test_dual_kind_same_source_file(niche):
    """Regression: 1 file thô -> 2 kind trong CÙNG manifest (vd gió rừng dùng cho cả
    sky_cloud lẫn nature_forest_field). Bug trước-fix: kind 1 dọn thô vào raw/ ngay
    trong vòng lặp -> kind 2 'không thấy file'."""
    man = _manifest(niche / "ambient_manifest.yaml", [
        {"file": "gio bao.wav", "kind": "nature_forest_field", "title": "a"},  # đứng TRƯỚC
        {"file": "gio bao.wav", "kind": "sky_cloud", "title": "b"},            # cùng file
    ])
    res = import_from_manifest(man, niche, niche)
    assert not res.failed and len(res.imported) == 2
    assert library_status(niche) == {"nature_forest_field": 1, "sky_cloud": 1}
    assert (niche / "raw" / "gio bao.wav").is_file()  # thô vẫn được dọn, đúng 1 bản


def test_list_variants_strict_and_ordered(tmp_path):
    d = tmp_path / "space"
    d.mkdir()
    for name in ("urban_street.wav", "urban_street_2.wav", "urban_street_10.wav",
                 "urban_landmark.wav", "urban_street_2.mp3"):
        _wav(d / name)
    v = [p.name for p in list_variants("urban_street", d)]
    # khớp chặt: không dính urban_landmark / .mp3; thứ tự SỐ không phải alphabet
    assert v == ["urban_street.wav", "urban_street_2.wav", "urban_street_10.wav"]


def test_fail_open_missing_niche(tmp_path):
    """Niche chưa có kho -> [] / {} — tầng ambient tắt, không nổ."""
    ghost = tmp_path / "ambient" / "deepsea"
    assert list_variants("space", ghost) == []
    assert library_status(ghost) == {}


def test_ambient_root_derives_from_library_root(monkeypatch, tmp_path):
    """Root = <library_root cha>/ambient (machine.json) — 0 config mới."""
    import autoedit.library.profile as profile

    monkeypatch.setattr(profile, "resolve_library_root",
                        lambda override=None: tmp_path / "AutoEdit" / "library")
    assert ambient_root() == tmp_path / "AutoEdit" / "ambient"
    assert niche_dir("space") == tmp_path / "AutoEdit" / "ambient" / "space"
    # override tường minh thắng
    assert ambient_root(tmp_path / "khac") == tmp_path / "khac"

# ===================== C đợt 3b (M0): kind chủ thể + drone ====================
def test_subject_and_drone_kinds_import(tmp_path):
    from autoedit.ambient.library import AMBIENT_KINDS, SUBJECT_KINDS

    assert set(SUBJECT_KINDS) <= set(AMBIENT_KINDS) and "drone" in AMBIENT_KINDS
    niche = tmp_path / "space"
    niche.mkdir()
    _wav(niche / "raw_fire.wav")
    _wav(niche / "raw_drone.wav")
    m = _manifest(niche / "m.yaml", [
        {"file": "raw_fire.wav", "kind": "fire", "title": "lửa"},
        {"file": "raw_drone.wav", "kind": "drone", "title": "nền"},
    ])
    res = import_from_manifest(m, niche, niche)
    assert not res.failed and len(res.imported) == 2
    assert [p.name for p in list_variants("fire", niche)] == ["fire.wav"]
    assert [p.name for p in list_variants("drone", niche)] == ["drone.wav"]
