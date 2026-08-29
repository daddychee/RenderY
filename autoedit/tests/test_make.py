"""Test tiện ích 1-lệnh `make` + launcher double-click cho nhân sự."""

from __future__ import annotations

import os
import stat

from autoedit import cli


def test_pick_input_by_extension_any_name(tmp_path):
    # tên bất kỳ, nhận theo đuôi (giống folder "voice test 3": text.rtf + voice test 3.mp3)
    (tmp_path / "text.rtf").write_text("x")
    (tmp_path / "voice test 3.mp3").write_bytes(b"x")
    s, sr = cli._pick_input(tmp_path, cli._TEXT_EXTS, "script")
    v, vr = cli._pick_input(tmp_path, cli._AUDIO_EXTS, "voice")
    assert s.name == "text.rtf" and sr == "ok"
    assert v.name == "voice test 3.mp3" and vr == "ok"


def test_pick_input_prefers_named_over_heuristic(tmp_path):
    (tmp_path / "script.txt").write_text("x")
    (tmp_path / "draft.txt").write_text("x")        # 2 file text -> ưu tiên 'script'
    s, sr = cli._pick_input(tmp_path, cli._TEXT_EXTS, "script")
    assert s.name == "script.txt" and sr == "ok"


def test_pick_input_many_audio_picks_largest(tmp_path):
    # 2 file audio không có tên 'voice' -> chọn file lớn nhất
    (tmp_path / "a.mp3").write_bytes(b"x")
    (tmp_path / "b.mp3").write_bytes(b"xx")         # b lớn hơn -> được chọn
    v, vr = cli._pick_input(tmp_path, cli._AUDIO_EXTS, "voice")
    assert v.name == "b.mp3" and vr == "ok"


def test_pick_input_many_scripts_prefers_txt_largest(tmp_path):
    # Nhiều file text -> ưu .txt, rồi chọn .txt lớn nhất
    (tmp_path / "notes.md").write_text("short")
    (tmp_path / "outline.txt").write_text("aa")
    (tmp_path / "main.txt").write_text("aabbcc")    # .txt lớn nhất -> được chọn
    s, sr = cli._pick_input(tmp_path, cli._TEXT_EXTS, "script")
    assert s.name == "main.txt" and sr == "ok"


def test_make_launcher_creates_executable(tmp_path):
    out = tmp_path / "Dung-NghiHuu.command"
    cli.make_launcher_cmd(channel="retirement-abroad", out=out)
    assert out.is_file()
    body = out.read_text()
    assert "retirement-abroad" in body          # kênh nhúng sẵn
    assert "autoedit make" in body              # gọi lệnh make
    assert "choose folder" in body              # hộp chọn folder (osascript)
    if os.name != "nt":                          # bit thực thi Unix — Windows (.bat) không áp dụng
        assert os.stat(out).st_mode & stat.S_IXUSR  # chạy được (executable)
