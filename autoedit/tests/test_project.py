"""Test khung project.json (M0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.project import (
    PIPELINE_ORDER,
    Project,
    StageStatus,
    create_project,
    slugify,
)


@pytest.fixture
def sample_inputs(tmp_path: Path) -> tuple[Path, Path]:
    """1 script .txt + 1 file giả làm voice (đủ cho M0, không cần audio thật)."""
    script = tmp_path / "src" / "script.txt"
    script.parent.mkdir(parents=True)
    script.write_text("Vietnam is one of the cheapest countries.\n", encoding="utf-8")
    voice = tmp_path / "src" / "voice.mp3"
    voice.write_bytes(b"\x00\x01fake-audio")
    return script, voice


def test_create_project_makes_valid_project(tmp_path, sample_inputs):
    script, voice = sample_inputs
    project = create_project(script, voice, out_dir=tmp_path / "projects", title="Test Video")

    assert isinstance(project, Project)
    project_dir = Path(project.project_dir)
    assert project_dir.is_dir()
    assert (project_dir / "project.json").is_file()
    # inputs được copy vào trong project
    assert (project_dir / project.inputs.script_path).is_file()
    assert (project_dir / project.inputs.voice_path).is_file()


# --------------------------- .srt kèm voice (RenderY) -----------------------
def test_srt_duoc_copy_cung_ten_voice(tmp_path, sample_inputs):
    """.srt copy vào project và ĐỔI TÊN theo voice -> SrtAligner tự tìm thấy,
    project vẫn self-contained (resume được khi folder gốc đã xoá)."""
    script, voice = sample_inputs
    srt = voice.with_suffix(".srt")
    srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nxin chào\n", encoding="utf-8")

    project = create_project(script, voice, out_dir=tmp_path / "projects", srt=srt)

    dst_voice = Path(project.project_dir) / project.inputs.voice_path
    assert dst_voice.with_suffix(".srt").is_file()

    from autoedit.align.srt_file import SrtAligner
    assert SrtAligner().find_srt(dst_voice) == dst_voice.with_suffix(".srt")


def test_khong_co_srt_van_tao_duoc_project(tmp_path, sample_inputs):
    """.srt là tuỳ chọn — thiếu thì project vẫn tạo bình thường (dùng whisper)."""
    script, voice = sample_inputs
    project = create_project(script, voice, out_dir=tmp_path / "projects")
    dst_voice = Path(project.project_dir) / project.inputs.voice_path
    assert not dst_voice.with_suffix(".srt").exists()


def test_srt_sai_duong_dan_bao_loi_som(tmp_path, sample_inputs):
    """Chỉ .srt không tồn tại -> báo ngay, đừng để tới stage align mới chết."""
    script, voice = sample_inputs
    with pytest.raises(FileNotFoundError, match=r"\.srt"):
        create_project(script, voice, out_dir=tmp_path / "projects",
                       srt=tmp_path / "khong-co.srt")


def test_srt_ten_khac_voice_van_doi_ten_dung(tmp_path, sample_inputs):
    """User đặt tên .srt tự do (vd 'chuong 1.srt') -> vẫn về đúng tên voice."""
    script, voice = sample_inputs
    srt = voice.parent / "chuong 1.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nxin chào\n", encoding="utf-8")

    project = create_project(script, voice, out_dir=tmp_path / "projects", srt=srt)

    dst_voice = Path(project.project_dir) / project.inputs.voice_path
    assert dst_voice.with_suffix(".srt").is_file()
    assert not (dst_voice.parent / "chuong 1.srt").exists()


def test_script_text_loaded(tmp_path, sample_inputs):
    script, voice = sample_inputs
    project = create_project(script, voice, out_dir=tmp_path / "projects")
    assert "Vietnam" in project.inputs.script_text


def test_all_stages_pending_at_start(tmp_path, sample_inputs):
    """Resume khởi đầu đúng: mọi stage đều pending."""
    script, voice = sample_inputs
    project = create_project(script, voice, out_dir=tmp_path / "projects")
    assert len(project.stages) == len(PIPELINE_ORDER)
    assert set(project.stages.keys()) == set(PIPELINE_ORDER)
    assert all(rec.status == StageStatus.PENDING for rec in project.stages.values())


def test_save_load_roundtrip(tmp_path, sample_inputs):
    script, voice = sample_inputs
    project = create_project(script, voice, out_dir=tmp_path / "projects")
    loaded = Project.load(project.project_dir)
    assert loaded.model_dump(mode="json") == project.model_dump(mode="json")


def test_slugify_ascii():
    assert slugify("Việt Nam giá rẻ!") == "viet-nam-gia-re"
    assert slugify("  Hello, World  ") == "hello-world"
    assert slugify("") == "project"


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_project(tmp_path / "nope.txt", tmp_path / "nope.mp3", out_dir=tmp_path)


def test_docx_script_rejected(tmp_path):
    script = tmp_path / "script.docx"
    script.write_bytes(b"fake docx")
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"fake")
    with pytest.raises(ValueError, match="docx"):
        create_project(script, voice, out_dir=tmp_path / "projects")


def test_search_queries_local_optional_c4():
    """C4: tier `local` optional — project.json cũ (không có key) load nguyên, local=[]."""
    from autoedit.project import SearchQueries

    q = SearchQueries.model_validate({"specific": ["a b"], "broad": [], "thematic": []})
    assert q.local == []
    q2 = SearchQueries.model_validate(
        {"specific": [], "broad": [], "thematic": [], "local": ["spiral galaxy"]})
    assert q2.local == ["spiral galaxy"]
