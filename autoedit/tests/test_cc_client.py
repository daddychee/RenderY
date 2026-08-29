"""Test ClaudeCodeDirectorClient — backend đạo diễn qua Claude Code CLI.

Giả lập subprocess.run (KHÔNG gọi `claude` thật): kiểm parse structured_output +
usage, và ĐẢM BẢO xoá ANTHROPIC_API_KEY khỏi env con (ép subscription, không metered).
"""

from __future__ import annotations

import json
import subprocess

import pytest

from autoedit.director import cc_client
from autoedit.director.cc_client import ClaudeCodeDirectorClient
from autoedit.director.schema import Outline

# 1 Outline hợp lệ (đủ field bắt buộc của ChapterPlan) để trả qua structured_output
GOOD_OUTLINE = {
    "tone": "warm",
    "motifs": ["đường về"],
    "chapters": [
        {
            "chapter_id": 0, "title": "Hook", "start_word": 0, "end_word": 11,
            "mood": "warm_inviting", "energy": "medium",
            "music_hint": "ấm, 80bpm", "summary": "mở bài",
            "central_subject": "người nghỉ hưu ở nước ngoài",
        }
    ],
}


def _fake_stdout(structured: dict, in_tok=100, out_tok=50) -> str:
    return json.dumps({
        "type": "result", "subtype": "success", "is_error": False,
        "result": json.dumps(structured),
        "structured_output": structured,
        "usage": {
            "input_tokens": in_tok, "output_tokens": out_tok,
            "cache_read_input_tokens": 10, "cache_creation_input_tokens": 20,
        },
        "total_cost_usd": 0.01,
    })


def test_complete_parses_structured_output_and_usage(monkeypatch):
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["kw"] = kw
        return subprocess.CompletedProcess(cmd, 0, stdout=_fake_stdout(GOOD_OUTLINE), stderr="")

    monkeypatch.setattr(cc_client.subprocess, "run", fake_run)

    client = ClaudeCodeDirectorClient(model="sonnet")
    parsed, usage = client.complete("SYS luật đạo diễn", "USER chia chương", Outline,
                                    context="TOÀN VĂN script")

    # trả về object đã validate
    assert isinstance(parsed, Outline)
    assert parsed.chapters[0].central_subject == "người nghỉ hưu ở nước ngoài"
    # usage lấy đúng từ JSON
    assert usage.input_tokens == 100 and usage.output_tokens == 50
    assert usage.cache_read_input_tokens == 10 and usage.cache_creation_input_tokens == 20

    # cmd đúng flag sống còn (cmd[0..] = node cli.js HOẶC claude, tuỳ cách cài)
    cmd = captured["cmd"]
    assert "claude" in " ".join(cmd).lower()
    assert "-p" in cmd
    assert "--json-schema" in cmd
    assert "--tools" in cmd and cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--output-format") + 1] == "json"
    # prompt gộp system + context + user, đẩy qua stdin
    assert "SYS luật đạo diễn" in captured["kw"]["input"]
    assert "TOÀN VĂN script" in captured["kw"]["input"]
    assert "USER chia chương" in captured["kw"]["input"]


def test_complete_strips_api_key_from_child_env(monkeypatch):
    """ANTHROPIC_API_KEY trong env cha KHÔNG được lọt vào env con (tránh metered)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-be-removed")
    seen_env = {}

    def fake_run(cmd, **kw):
        seen_env.update(kw["env"])
        return subprocess.CompletedProcess(cmd, 0, stdout=_fake_stdout(GOOD_OUTLINE), stderr="")

    monkeypatch.setattr(cc_client.subprocess, "run", fake_run)
    ClaudeCodeDirectorClient().complete("s", "u", Outline)
    assert "ANTHROPIC_API_KEY" not in seen_env


def test_complete_raises_on_error_result(monkeypatch):
    def fake_run(cmd, **kw):
        out = json.dumps({"is_error": True, "subtype": "error_max_turns", "result": "boom"})
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")

    monkeypatch.setattr(cc_client.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="claude -p báo lỗi"):
        ClaudeCodeDirectorClient().complete("s", "u", Outline)


def test_complete_raises_on_nonzero_exit(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="crash")

    monkeypatch.setattr(cc_client.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="exit 1"):
        ClaudeCodeDirectorClient().complete("s", "u", Outline)


def test_complete_grounded_not_supported():
    with pytest.raises(NotImplementedError, match="web-grounded"):
        ClaudeCodeDirectorClient().complete_grounded("s", "u", Outline)
