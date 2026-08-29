"""Test C5 vision gate M1 (MO_TA_VAN_HANH_C5_VISION_GATE.md §6) — module visiongate:
parse verdict · chống schema-echo PB3 · feedback-retry PB4 · bỏ cuộc sau 4 · frame 960px
· prompt đủ ngữ cảnh beat. Logic demote/fail-open nằm ở M2 (vòng pick runner).
"""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import pytest

from autoedit.project import Beat
from autoedit.ranker.visiongate import GateVerdict, VisionGate


def make_beat(**over) -> Beat:
    base = dict(
        beat_id=1, chapter=1, text="Đài thiên văn ESO quan sát bầu trời đêm.",
        start_word=0, end_word=6, start=0.0, end=4.0,
        energy="medium", mood="contemplative", visual_level="literal",
        visual_concept="observatory telescope under starry sky", shot_size="wide",
    )
    base.update(over)
    return Beat(**base)


class StubGate(VisionGate):
    """Gate với HTTP stub — test parse/retry không mạng."""

    def __init__(self, responses: list):
        super().__init__(api_key="test-key")
        self._responses = list(responses)
        self.posts = 0
        self.bodies: list[dict] = []
        self.keys_used: list[str] = []

    def _post(self, body: dict, key: str | None = None) -> dict:
        self.posts += 1
        self.keys_used.append(key or self._keys[0])
        # snapshot: gate MUTATE body giữa các attempt (feedback-retry PB4)
        self.bodies.append(json.loads(json.dumps(body)))
        r = self._responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


_VALID = {"subject_match": "yes", "mood_match": "unsure",
          "seen": "Kính thiên văn dưới trời sao.", "reason": "Đúng chủ thể beat cần."}


def _resp(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


def test_gate_parses_fenced_json_one_call():
    fenced = "```json\n" + json.dumps(_VALID, ensure_ascii=False) + "\n```"
    g = StubGate([_resp(fenced)])
    v = g.check(Path("x.mp4"), make_beat(), images=[b"jpegbytes"])
    assert v.subject_match == "yes" and v.mood_match == "unsure"
    assert g.posts == 1


def test_gate_prompt_carries_beat_context_and_claim():
    g = StubGate([_resp(json.dumps(_VALID, ensure_ascii=False))])
    g.check(Path("x.mp4"), make_beat(), central_subject="Pluto",
            video_subject="the Solar System", claim="Full moon against dark sky",
            images=[b"jpegbytes"])
    text = g.bodies[0]["messages"][1]["content"][-1]["text"]
    assert "Đài thiên văn ESO" in text and "observatory telescope" in text
    assert "contemplative" in text
    assert "central_subject: Pluto" in text and "the Solar System" in text
    assert "TAGS CLAIM: Full moon" in text  # gate được đối chất chữ vs hình


def test_gate_schema_echo_retries_and_prompt_hardened(monkeypatch):
    """PB3: GLM thỉnh thoảng chép nguyên schema — retry cứu + prompt giữ 2 lớp chống echo."""
    monkeypatch.setattr("autoedit.ranker.visiongate.time.sleep", lambda s: None)
    echo = json.dumps(GateVerdict.model_json_schema(), ensure_ascii=False)
    g = StubGate([_resp(echo), _resp(json.dumps(_VALID, ensure_ascii=False))])
    v = g.check(Path("x.mp4"), make_beat(), images=[b"jpegbytes"])
    assert g.posts == 2 and v.subject_match == "yes"
    system = g.bodies[0]["messages"][0]["content"]
    assert "Example of a CORRECT output" in system            # lớp 1
    user_text = g.bodies[0]["messages"][1]["content"][-1]["text"]
    assert "Do NOT output the schema" in user_text            # lớp 2


def test_gate_feedback_retry_on_validation_error(monkeypatch):
    """PB4: giá trị ngoài enum -> lượt retry phải nhét lỗi validation vào prompt."""
    monkeypatch.setattr("autoedit.ranker.visiongate.time.sleep", lambda s: None)
    bad = json.dumps(_VALID | {"subject_match": "maybe"})
    g = StubGate([_resp(bad), _resp(json.dumps(_VALID, ensure_ascii=False))])
    v = g.check(Path("x.mp4"), make_beat(), images=[b"jpegbytes"])
    assert g.posts == 2 and v.subject_match == "yes"
    text2 = g.bodies[1]["messages"][1]["content"][-1]["text"]
    assert "failed validation" in text2 and "maybe" in text2


def test_gate_gives_up_after_4(monkeypatch):
    monkeypatch.setattr("autoedit.ranker.visiongate.time.sleep", lambda s: None)
    g = StubGate([_resp("not json at all")] * 4)
    with pytest.raises(RuntimeError, match="4 lần"):
        g.check(Path("x.mp4"), make_beat(), images=[b"jpegbytes"])
    assert g.posts == 4


def _make_jpeg(w: int, h: int) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (w, h), (30, 60, 90)).save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_gate_sends_shrunken_frame_960():
    """PB3-B2: frame gửi đi luôn thu 960px dù caller đưa bản 1280."""
    from PIL import Image

    g = StubGate([_resp(json.dumps(_VALID, ensure_ascii=False))])
    g.check(Path("x.mp4"), make_beat(), images=[_make_jpeg(1280, 720)])
    sent = g.bodies[0]["messages"][1]["content"][0]["image_url"]["url"]
    data = base64.b64decode(sent.split(",", 1)[1])
    assert max(Image.open(io.BytesIO(data)).size) == 960
    body = g.bodies[0]
    assert body["thinking"] == {"type": "disabled"}  # bẫy reasoning ăn max_tokens


def test_gate_frame_rejects_unknown_format(tmp_path):
    weird = tmp_path / "x.xyz"
    weird.write_bytes(b"?")
    with pytest.raises(ValueError, match="Không hỗ trợ"):
        VisionGate._frame(weird)


def test_gate_rotates_keys_on_429(monkeypatch):
    """V11 lần 1: gate chết vì tựa 1 key khi GLM hắt hơi — attempt sau phải sang key kế."""
    import urllib.error

    monkeypatch.setattr("autoedit.ranker.visiongate.time.sleep", lambda s: None)
    err = urllib.error.HTTPError("http://x", 429, "Too Many", None, None)
    g = StubGate([err, _resp(json.dumps(_VALID, ensure_ascii=False))])
    g._keys = ["k1", "k2", "k3"]
    v = g.check(Path("x.mp4"), make_beat(), images=[b"jpegbytes"])
    assert v.subject_match == "yes"
    assert g.keys_used == ["k1", "k2"]  # 429 ở k1 -> attempt 2 dùng k2
