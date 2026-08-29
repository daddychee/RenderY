"""Test Draft Packager + machine profile (M1) — không cần CapCut thật."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoedit.packager.machine import (
    DONOR_CONTENT_KEYS,
    MachineProfile,
    find_default_donor,
    register_machine,
    set_draft_out_root,
)
from autoedit.packager.packager import (
    CAPCUT_PLACEHOLDER,
    NATIVE_CHECK_FLAG,
    PYCAPCUT_CHECK_FLAG,
    PackageError,
    package_draft,
    verify_draft,
)


@pytest.fixture
def fake_capcut(tmp_path: Path) -> dict:
    """Folder CapCut giả với 1 donor draft đủ trường (mô phỏng draft thật)."""
    root = tmp_path / "com.lveditor.draft"
    donor = root / "0428"
    donor.mkdir(parents=True)

    donor_content = {
        "platform": {"os": "mac", "app_version": "8.1.1", "device_id": "abc"},
        "last_modified_platform": {"os": "mac", "app_version": "8.8.0"},
        "new_version": "173.0.0",
        "version": 360000,
        "draft_type": "video",
        "function_assistant_info": {},
        "mixed_track_mode_on": False,
        "smart_ads_info": {},
        "uneven_animation_template_info": {},
        "duration": 1000000,
        "materials": {"videos": [], "audios": []},
        "tracks": [],
    }
    donor_meta = {
        "draft_fold_path": str(donor),
        "draft_root_path": str(root),
        "draft_name": "0428",
        "draft_id": "OLD-ID",
        "draft_cover": "draft_cover.jpg",
        "tm_draft_create": 1,
        "tm_draft_modified": 1,
        "tm_duration": 1000000,
        "cloud_draft_sync": False,
    }
    (donor / "draft_info.json").write_text(json.dumps(donor_content))
    (donor / "draft_meta_info.json").write_text(json.dumps(donor_meta))
    (donor / "draft_cover.jpg").write_bytes(b"fake-jpg")

    # 1 asset thật trên disk cho content test
    asset = tmp_path / "assets" / "video1.mp4"
    asset.parent.mkdir()
    asset.write_bytes(b"fake-video")

    return {"root": root, "donor": donor, "asset": asset, "tmp": tmp_path}


@pytest.fixture
def profile(fake_capcut, tmp_path) -> MachineProfile:
    return register_machine(fake_capcut["donor"], profile_path=tmp_path / "machine.json")


def _content_with_asset(asset: Path) -> dict:
    return {
        "duration": 5000000,
        "materials": {"videos": [{"path": str(asset), "check_flag": PYCAPCUT_CHECK_FLAG}],
                      "audios": []},
        "tracks": [],
    }


def _resolve_placeholder(p: str, draft_dir: Path) -> Path:
    """Path placeholder -> path thật trong folder draft (như CapCut resolve)."""
    assert p.startswith(CAPCUT_PLACEHOLDER + "/"), f"không phải placeholder: {p}"
    return draft_dir / p[len(CAPCUT_PLACEHOLDER) + 1:]


# --------------------------- machine profile --------------------------------
def test_register_machine_extracts_overrides(profile, fake_capcut):
    assert set(profile.content_overrides.keys()) == set(DONOR_CONTENT_KEYS)
    assert profile.content_overrides["new_version"] == "173.0.0"
    assert profile.capcut_root == str(fake_capcut["root"])
    assert profile.capcut_app_version == "8.1.1"
    assert profile.meta_template["draft_name"] == "0428"


def test_register_machine_rejects_donor_missing_platform(tmp_path):
    bad = tmp_path / "bad_donor"
    bad.mkdir()
    (bad / "draft_info.json").write_text(json.dumps({"version": 1}))
    (bad / "draft_meta_info.json").write_text(json.dumps({}))
    with pytest.raises(ValueError, match="thiếu trường bắt buộc"):
        register_machine(bad, profile_path=tmp_path / "machine.json")


def test_profile_roundtrip(profile, tmp_path):
    path = tmp_path / "machine.json"
    loaded = MachineProfile.load(path)
    assert loaded.model_dump() == profile.model_dump()


def test_find_default_donor_picks_latest(fake_capcut):
    assert find_default_donor(fake_capcut["root"]) == fake_capcut["donor"]


# --------------------------- package_draft ----------------------------------
def test_package_draft_writes_valid_folder(profile, fake_capcut):
    content = _content_with_asset(fake_capcut["asset"])
    draft_dir = package_draft(content, "TEST_DRAFT", profile)

    assert draft_dir == fake_capcut["root"] / "TEST_DRAFT"
    info = json.loads((draft_dir / "draft_info.json").read_text())
    copy = json.loads((draft_dir / "draft_content.json").read_text())
    meta = json.loads((draft_dir / "draft_meta_info.json").read_text())

    # bản sao giống hệt
    assert info == copy
    # 9 trường donor được đè vào content
    for k in DONOR_CONTENT_KEYS:
        assert info[k] == profile.content_overrides[k]
    # meta: fold_path tuyệt đối đúng folder, id mới, duration khớp content
    assert meta["draft_fold_path"] == str(draft_dir)
    assert meta["draft_root_path"] == str(fake_capcut["root"])
    assert meta["draft_name"] == "TEST_DRAFT"
    assert meta["draft_id"] != "OLD-ID"
    assert meta["tm_duration"] == content["duration"]
    # cover copy từ donor
    assert (draft_dir / "draft_cover.jpg").is_file()
    # verify không kêu
    verify_draft(draft_dir)


def test_package_draft_embeds_media_inside_draft(profile, fake_capcut):
    """CapCut sandbox: media phải nằm TRONG folder draft, không trỏ ra ngoài (13/06).
    Path ghi dạng placeholder (PORTABLE 13/07) — resolve về draft phải ra file thật."""
    content = _content_with_asset(fake_capcut["asset"])
    draft_dir = package_draft(content, "TEST_EMBED", profile)
    info = json.loads((draft_dir / "draft_info.json").read_text())
    for kind in ("videos", "audios"):
        for m in info["materials"][kind]:
            p = _resolve_placeholder(m["path"], draft_dir)
            assert p.is_file(), f"{p} không tồn tại"
    assert (draft_dir / "materials").is_dir()


def test_package_draft_portable_cross_machine(profile, fake_capcut):
    """Regression bàn giao máy khác (13/07): path tuyệt đối máy gốc + check_flag 63487
    -> CapCut máy khác báo "Không thể tải xuống tài liệu", KHÔNG cho relink (§B4).
    Draft sinh ra không được chứa path tuyệt đối của máy này trong CONTENT."""
    content = _content_with_asset(fake_capcut["asset"])
    draft_dir = package_draft(content, "TEST_PORTABLE", profile)

    esc = json.dumps(str(draft_dir))[1:-1]  # dạng escaped nằm trong file JSON
    fwd = str(draft_dir).replace("\\", "/")
    for name in ("draft_info.json", "draft_content.json"):
        raw = (draft_dir / name).read_text()
        assert esc not in raw and fwd not in raw, f"{name} còn path tuyệt đối máy gốc"

    info = json.loads((draft_dir / "draft_info.json").read_text())
    m = info["materials"]["videos"][0]
    assert m["path"] == f"{CAPCUT_PLACEHOLDER}/materials/video1.mp4"
    assert m["check_flag"] == NATIVE_CHECK_FLAG
    # sổ đăng ký meta: file_Path tương đối kiểu native + local_material_id khớp sổ
    meta = json.loads((draft_dir / "draft_meta_info.json").read_text())
    entries = [e for b in meta["draft_materials"] for e in b.get("value", [])]
    assert entries[0]["file_Path"] == "./materials/video1.mp4"
    assert m["local_material_id"] == entries[0]["id"]
    # dict của caller giữ path tuyệt đối -> re-package (overwrite) vẫn chạy
    assert content["materials"]["videos"][0]["path"].startswith(str(draft_dir))
    package_draft(content, "TEST_PORTABLE", profile, overwrite=True)


def test_package_draft_out_root(profile, fake_capcut, tmp_path):
    """set-draft-root: draft ghi vào draft_out_root (tự tạo folder), cover vẫn lấy
    từ donor ở capcut_root."""
    out = tmp_path / "CapCut Drafts"  # chưa tồn tại — package tự mkdir
    profile.draft_out_root = str(out)
    content = _content_with_asset(fake_capcut["asset"])
    draft_dir = package_draft(content, "TEST_OUTROOT", profile)

    assert draft_dir == out / "TEST_OUTROOT"
    meta = json.loads((draft_dir / "draft_meta_info.json").read_text())
    assert meta["draft_fold_path"] == str(draft_dir)
    assert meta["draft_root_path"] == str(out)
    assert (draft_dir / "draft_cover.jpg").is_file()  # cover từ donor capcut_root
    verify_draft(draft_dir)


def test_set_draft_out_root_persists(profile, tmp_path):
    set_draft_out_root(tmp_path / "out", profile_path=tmp_path / "machine.json")
    loaded = MachineProfile.load(tmp_path / "machine.json")
    assert loaded.draft_out_root == str(tmp_path / "out")
    assert loaded.out_root() == tmp_path / "out"


def test_resolve_data_root_priority(profile, tmp_path, monkeypatch):
    """G1 kho chung: override > env AUTOEDIT_DATA_ROOT > machine.json > ~/AutoEdit."""
    from autoedit.packager.machine import (
        DATA_ROOT_ENV, DEFAULT_DATA_ROOT, resolve_data_root, set_data_root)

    pp = tmp_path / "machine.json"
    monkeypatch.delenv(DATA_ROOT_ENV, raising=False)
    # 4. chưa set -> mặc định cũ (máy chưa G1 không đổi hành vi)
    assert resolve_data_root(profile_path=pp) == DEFAULT_DATA_ROOT
    # 3. machine.json (set-data-root)
    set_data_root(tmp_path / "share", profile_path=pp)
    assert resolve_data_root(profile_path=pp) == tmp_path / "share"
    assert MachineProfile.load(pp).data_root == str(tmp_path / "share")
    # 2. env thắng machine.json
    monkeypatch.setenv(DATA_ROOT_ENV, str(tmp_path / "env_root"))
    assert resolve_data_root(profile_path=pp) == tmp_path / "env_root"
    # 1. override thắng tất
    assert resolve_data_root(tmp_path / "ov", profile_path=pp) == tmp_path / "ov"
    # profile hỏng/thiếu -> fail-open về mặc định, không nổ
    monkeypatch.delenv(DATA_ROOT_ENV, raising=False)
    assert resolve_data_root(profile_path=tmp_path / "khong_ton_tai.json") == DEFAULT_DATA_ROOT


def test_resolve_db_url_priority(profile, tmp_path, monkeypatch):
    """G2 sổ Postgres: override > env AUTOEDIT_DB_URL > machine.json > rỗng (= SQLite G1)."""
    from autoedit.packager.machine import DB_URL_ENV, resolve_db_url, set_db_url

    pp = tmp_path / "machine.json"
    monkeypatch.delenv(DB_URL_ENV, raising=False)
    # 4. chưa set -> rỗng (máy chưa G2 chạy SQLite y nguyên)
    assert resolve_db_url(profile_path=pp) == ""
    # 3. machine.json (set-db-url)
    set_db_url("postgresql://a:b@goc:5432/autoedit", profile_path=pp)
    assert resolve_db_url(profile_path=pp) == "postgresql://a:b@goc:5432/autoedit"
    assert MachineProfile.load(pp).db_url == "postgresql://a:b@goc:5432/autoedit"
    # đường lui G2: set rỗng = xóa -> về SQLite
    set_db_url("", profile_path=pp)
    assert resolve_db_url(profile_path=pp) == ""
    set_db_url("postgresql://a:b@goc:5432/autoedit", profile_path=pp)
    # 2. env thắng machine.json
    monkeypatch.setenv(DB_URL_ENV, "postgresql://env@env/x")
    assert resolve_db_url(profile_path=pp) == "postgresql://env@env/x"
    # 1. override thắng tất
    assert resolve_db_url("postgresql://ov@ov/y", profile_path=pp) == "postgresql://ov@ov/y"
    # profile hỏng/thiếu -> fail-open về rỗng, không nổ
    monkeypatch.delenv(DB_URL_ENV, raising=False)
    assert resolve_db_url(profile_path=tmp_path / "khong_ton_tai.json") == ""


def test_package_draft_does_not_mutate_input(profile, fake_capcut):
    content = _content_with_asset(fake_capcut["asset"])
    package_draft(content, "TEST_MUTATE", profile)
    assert "platform" not in content  # caller giữ nguyên dict gốc


def test_package_draft_rejects_missing_asset(profile, fake_capcut):
    content = _content_with_asset(fake_capcut["tmp"] / "khong_ton_tai.mp4")
    with pytest.raises(PackageError, match="không tồn tại"):
        package_draft(content, "TEST_MISSING", profile)
    # không được tạo folder rác khi fail
    assert not (fake_capcut["root"] / "TEST_MISSING").exists()


def test_package_draft_rejects_relative_asset(profile):
    content = {"duration": 0, "materials": {"videos": [{"path": "relative.mp4"}], "audios": []}, "tracks": []}
    with pytest.raises(PackageError, match="không tuyệt đối"):
        package_draft(content, "TEST_REL", profile)


def test_package_draft_rejects_non_ascii_name(profile, fake_capcut):
    content = _content_with_asset(fake_capcut["asset"])
    with pytest.raises(PackageError, match="ASCII"):
        package_draft(content, "bản nháp 1", profile)


def test_package_draft_no_silent_overwrite(profile, fake_capcut):
    content = _content_with_asset(fake_capcut["asset"])
    package_draft(content, "TEST_DUP", profile)
    with pytest.raises(PackageError, match="đã tồn tại"):
        package_draft(content, "TEST_DUP", profile)
    # với overwrite=True thì được
    package_draft(content, "TEST_DUP", profile, overwrite=True)
