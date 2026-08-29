"""Tầng 3 — NÃO chấm kind tiếng cho cảnh bảng luật MÙ CHỮ (2026-07-18).

Ràng buộc quan trọng nhất: tầng này CHỈ được đụng ca bảng luật KHÔNG quyết được.
Ca bảng luật đã quyết mà bị NÃO lật = mất ổn định + mất mọi thứ đã qua cổng tai.
"""

from __future__ import annotations

from autoedit.ambient.subject_llm import _Pick, _Picks, scene_line, score_unmatched


class FakeClient:
    """client.complete(system, user, model) -> (obj, usage). Ghi lại prompt để soi."""

    def __init__(self, picks, boom=False):
        self.picks, self.boom, self.seen = picks, boom, []

    def complete(self, system, user, output_model):
        self.seen.append(user)
        if self.boom:
            raise RuntimeError("mạng đứt")
        return _Picks(picks=[_Pick(id=i, kind=k) for i, k in self.picks]), None


def test_scores_only_given_scenes():
    c = FakeClient([(1, "urban_street"), (2, "")])
    got = score_unmatched(
        [{"id": 1, "subject": "Omani village", "tags": "town road", "shot_size": "wide"},
         {"id": 2, "subject": "abstract pattern", "tags": "", "shot_size": ""}],
        ["urban_street", "wind"], c)
    assert got == {1: "urban_street", 2: ""}
    assert "urban_street, wind" in c.seen[0]      # kho được liệt kê cho NÃO
    assert "Omani village" in c.seen[0]


def test_rejects_kind_outside_library():
    """NÃO bịa kind không có file -> BỎ (máy giữ ràng buộc, NÃO chỉ quyết nghĩa)."""
    c = FakeClient([(1, "helicopter"), (2, "wind")])
    got = score_unmatched(
        [{"id": 1, "subject": "a", "shot_size": "aerial"},
         {"id": 2, "subject": "b", "shot_size": "aerial"}], ["wind"], c)
    assert got == {2: "wind"}                     # id 1 bị loại vì kind lạ


def test_rejects_id_outside_batch():
    """NÃO trả id không có trong mẻ -> BỎ (chống lệch beat)."""
    c = FakeClient([(1, "wind"), (999, "wind")])
    got = score_unmatched([{"id": 1, "subject": "a", "shot_size": "aerial"}], ["wind"], c)
    assert got == {1: "wind"}


def test_fail_open_on_error():
    """Lỗi mạng/parse -> {} : bảng luật giữ nguyên quyết định, KHÔNG chặn assemble."""
    assert score_unmatched([{"id": 1, "subject": "a"}], ["wind"], FakeClient([], boom=True)) == {}


def test_no_scenes_or_no_kinds_skips_call():
    c = FakeClient([(1, "wind")])
    assert score_unmatched([], ["wind"], c) == {}
    assert score_unmatched([{"id": 1, "subject": "a"}], [], c) == {}
    assert c.seen == []                           # không gọi NÃO vô ích


def test_technical_kinds_never_offered(tmp_path):
    """Hồi quy chạy thật RD-89 (2026-07-18): cho NÃO chọn MỌI kind có file thì nó vơ cả
    kind KỸ THUẬT/UI — "opening soda can"->click, người mặc đồ->default. Chặn phía MÁY."""
    from autoedit.ambient.subject_llm import NON_SUBJECT_KINDS, kinds_with_files

    lib = tmp_path / "life-in"
    lib.mkdir()
    for n in ("wind.wav", "default.wav", "click.wav", "ocean.wav"):
        (lib / n).write_bytes(b"RIFF0000WAVEfmt ")
    got = kinds_with_files(lib)
    assert "default" not in got and "click" not in got
    assert {"default", "click", "whoosh", "drone"} <= NON_SUBJECT_KINDS


def test_interior_kinds_never_offered(tmp_path):
    """Hồi quy 2 VÒNG chạy thật: "Oman gate" -> car_interior lọt CẢ SAU KHI prompt dặn
    luật vật-đứng-yên. Kind nội thất/đặc thù chỉ đúng khi thấy đích danh — mà thấy đích
    danh thì bảng luật đã bắt, không rơi xuống tầng này. Chặn CỨNG, không nhờ prompt."""
    from autoedit.ambient.subject_llm import kinds_with_files

    lib = tmp_path / "life-in"
    lib.mkdir()
    # kind phải KHAI trong subject_rules.yaml mới được coi là kind của niche (niche_kinds)
    (lib / "subject_rules.yaml").write_text(
        "rules:\n"
        "  - kind: car_interior\n    keywords: [car interior]\n"
        "  - kind: subway\n    keywords: [subway]\n"
        "  - kind: wind\n    keywords: [desert]\n"
        "  - kind: camel\n    keywords: [camel]\n", encoding="utf-8")
    for n in ("car_interior.wav", "subway.wav", "wind.wav", "camel.wav"):
        (lib / n).write_bytes(b"RIFF0000WAVEfmt ")
    got = kinds_with_files(lib)
    assert "car_interior" not in got and "subway" not in got   # nội thất: chặn CỨNG
    assert {"wind", "camel"} <= set(got)                       # ngoài trời/loài: vẫn chọn được


def test_spatial_kind_blocked_on_narrow_shot():
    """Hồi quy VÒNG 3 — user chê đúng 3/19 ca NÃO, CẢ BA đều cảnh HẸP gán tiếng KHÔNG GIAN:
    b039 "woman on phone"(medium)->market · b063 "jack-o'-lantern"(medium)->fire(*) ·
    b074 "opening soda can"(close_up)->splash. 15 ca cảnh RỘNG user duyệt hết.
    Khung hình hẹp chỉ có 1 người/1 vật — tiếng phải từ CHÍNH chủ thể, không phải không
    gian quanh nó. (*) fire không thuộc SPATIAL_KINDS, chặn bằng prompt (luật 6)."""
    c = FakeClient([(39, "market"), (74, "splash"), (114, "wind")])
    got = score_unmatched([
        {"id": 39, "subject": "woman on phone", "shot_size": "medium"},
        {"id": 74, "subject": "opening soda can", "shot_size": "close_up"},
        {"id": 114, "subject": "Omani village", "shot_size": "aerial"},
    ], ["market", "splash", "wind"], c)
    assert 39 not in got and 74 not in got     # cảnh HẸP + tiếng không gian -> loại
    assert got == {114: "wind"}                # cảnh RỘNG giữ nguyên


def test_missing_shot_size_treated_as_narrow():
    """Mù cỡ cảnh -> coi như HẸP: thà siết còn hơn gán tiếng không gian cho cảnh không rõ."""
    c = FakeClient([(1, "wind"), (2, "camel")])
    got = score_unmatched([{"id": 1, "subject": "a"}, {"id": 2, "subject": "b"}],
                          ["wind", "camel"], c)
    assert got == {2: "camel"}                 # camel (tiếng chủ thể) qua, wind bị chặn


def test_prompt_tells_brain_to_prefer_silence():
    """Hồi quy: NÃO gán tiếng cho vật ĐỨNG YÊN không phát ra tiếng đó ("Oman gate"->
    car_interior, "cannon fort"->ocean). Prompt phải nói rõ luật vật-đứng-yên + thà im."""
    c = FakeClient([(1, "")])
    score_unmatched([{"id": 1, "subject": "Oman gate"}], ["wind"], c)
    from autoedit.ambient.subject_llm import _SYSTEM
    assert "ĐỪNG CỐ ĐIỀN CHO ĐỦ" in _SYSTEM
    assert "đứng yên" in _SYSTEM and "THÀ IM CÒN HƠN SAI" in _SYSTEM


def test_scene_line_puts_subject_first():
    line = scene_line(7, "lemons", "market fruit", "close_up")
    assert line.startswith("[7] chủ thể: lemons")
    assert "bối cảnh: market fruit" in line       # tag rõ ràng là BỐI CẢNH, không phải chủ thể
