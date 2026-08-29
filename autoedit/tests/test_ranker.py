"""Test khung phễu c5 (F5 milestone 1) — theo tiêu chí thành công MO_TA_VAN_HANH_PHEU_C5.md §5:
veto đúng 3 dạng c2 · sàn 3 tự nới · điểm MÁY không lật nghĩa · kill-log đếm đúng · NÃO 1 call/beat.
"""

from __future__ import annotations

import pytest

from autoedit.director.client import Usage
from autoedit.project import Beat
from autoedit.ranker.funnel import (
    MACHINE_MAX_SPREAD,
    NGHIA_W,
    PEAK_BONUS,
    POOL_FLOOR,
    rank_beat,
)
from autoedit.ranker.schema import BeatRankResponse, CandidateVerdict


# --------------------------------------------------------------------------- #
# Đồ nghề
# --------------------------------------------------------------------------- #
def make_beat(**over) -> Beat:
    base = dict(
        beat_id=1, chapter=1, text="Hà Nội có 36 phố phường cổ.",
        start_word=0, end_word=6, start=0.0, end=4.0,
        energy="medium", mood="nostalgic", visual_level="literal",
        visual_concept="hanoi old quarter street", shot_size="wide",
    )
    base.update(over)
    return Beat(**base)


def cand(key: str, **over) -> dict:
    c = {"asset_key": key, "source": "pexels", "media_type": "video",
         "description": f"clip {key}", "duration": 10.0}
    c.update(over)
    return c


class FakeBrain:
    """NÃO giả: trả verdicts soạn sẵn theo asset_key; đếm số call."""

    def __init__(self, verdicts: dict[str, CandidateVerdict]):
        self.verdicts = verdicts
        self.calls = 0

    def complete(self, system, user, output_model, context=None):
        self.calls += 1
        assert output_model is BeatRankResponse
        return BeatRankResponse(verdicts=list(self.verdicts.values())), Usage(
            input_tokens=100, output_tokens=50
        )


def ok(key, nghia=7, mood=7, ly_do="hợp nghĩa"):
    return CandidateVerdict(id=key, verdict="ok", diem_nghia=nghia, diem_mood=mood, ly_do=ly_do)


def veto(key, vtype, ly_do="sai"):
    return CandidateVerdict(id=key, verdict="veto", veto_type=vtype,
                            diem_nghia=0, diem_mood=0, ly_do=ly_do)


# --------------------------------------------------------------------------- #
# 1. Veto đúng 3 dạng c2 — nghiêm trọng bị loại hẳn, không bao giờ được chọn
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("vtype", ["chu_de_khac_han", "thuc_the_sai", "nguoc_tran_cu_the"])
def test_serious_veto_killed(vtype):
    brain = FakeBrain({
        "a": veto("a", vtype), "b": ok("b", nghia=6), "c": ok("c", nghia=5),
        "d": ok("d", nghia=4),
    })
    r = rank_beat(make_beat(), [cand("a"), cand("b"), cand("c"), cand("d")], brain)
    assert r.chosen_key == "b"
    assert all(rc.asset_key != "a" for rc in r.ranked)  # không được trả lại pool
    assert r.kill_log["veto_nghia"] == 1
    assert r.kill_log["tra_lai_san"] == 0  # pool còn 3 = đủ sàn, và veto nghiêm trọng không hồi


def test_all_serious_veto_needs_human():
    brain = FakeBrain({"a": veto("a", "thuc_the_sai"), "b": veto("b", "chu_de_khac_han")})
    r = rank_beat(make_beat(), [cand("a"), cand("b")], brain)
    assert r.needs_human and r.chosen_key is None
    assert r.kill_log["con_lai"] == 0


# --------------------------------------------------------------------------- #
# 2. Sàn 3 tự nới — veto lý-do-thường được trả lại với điểm trừ nặng
# --------------------------------------------------------------------------- #
def test_floor_revives_non_serious_vetoes():
    brain = FakeBrain({
        "a": ok("a", nghia=8),
        "b": veto("b", "khac", ly_do="mood lệch"),   # KHÔNG thuộc 3 dạng
        "c": veto("c", "khac", ly_do="nhạt"),
    })
    r = rank_beat(make_beat(), [cand("a"), cand("b"), cand("c")], brain)
    assert r.chosen_key == "a"                        # ứng viên ok vẫn thắng tuyệt đối
    assert r.kill_log["tra_lai_san"] == 2
    assert r.kill_log["con_lai"] == 3                 # pool đầy lại đủ sàn
    demoted = [rc for rc in r.ranked if rc.demoted]
    assert len(demoted) == 2
    assert all(rc.diem_tong < min(x.diem_tong for x in r.ranked if not x.demoted)
               for rc in demoted)                     # trừ nặng: luôn xếp sau hàng ok


def test_floor_not_triggered_when_pool_full():
    brain = FakeBrain({
        "a": ok("a"), "b": ok("b"), "c": ok("c"),
        "d": veto("d", "khac"),
    })
    r = rank_beat(make_beat(), [cand("a"), cand("b"), cand("c"), cand("d")], brain)
    assert r.kill_log["tra_lai_san"] == 0
    assert all(rc.asset_key != "d" for rc in r.ranked)


def test_all_vetoed_non_serious_picks_best_demoted():
    brain = FakeBrain({
        "a": veto("a", "khac"), "b": veto("b", "khac"),
    })
    # NÃO chấm điểm 0 khi veto -> hòa; sort ổn định giữ thứ tự relevance -> "a"
    r = rank_beat(make_beat(), [cand("a"), cand("b")], brain)
    assert r.chosen_key == "a" and not r.needs_human
    assert any("tự-hạ-cấp" in w for w in r.warnings)  # cảnh báo nên soát tay


# --------------------------------------------------------------------------- #
# 3. Điểm MÁY không lật được nghĩa
# --------------------------------------------------------------------------- #
def test_machine_spread_below_one_nghia_point():
    assert MACHINE_MAX_SPREAD < NGHIA_W  # bất biến thiết kế — đổi trọng số phải giữ


def test_machine_score_cannot_flip_nghia():
    # "worse": nghĩa thấp hơn 1 điểm nhưng ăn TRỌN điểm máy (khác cỡ cảnh, dài, chưa dùng,
    #          CỜ ĐIỂM NHÔ ytref §3h — spread mới 2.5 vẫn phải thua 1 điểm nghĩa)
    # "better": nghĩa cao hơn nhưng điểm máy TỆ NHẤT (trùng cỡ cảnh, ngắn vừa, đã dùng)
    brain = FakeBrain({
        "better": ok("better", nghia=8, mood=5),
        "worse": ok("worse", nghia=7, mood=5),
    })
    beat = make_beat()
    r = rank_beat(
        beat,
        [cand("worse", shot_size="close_up", duration=30.0, peak_value=0.9),
         cand("better", shot_size="wide", duration=4.5)],
        brain,
        prev_shot_size="wide",
        times_used=lambda k: 3 if k == "better" else 0,
    )
    assert r.chosen_key == "better"


# --------------------------------------------------------------------------- #
# 3b. PEAK_BONUS ytref §3h — cờ điểm nhô cộng điểm máy, chảy CẢ 2 đường rank (P5)
# --------------------------------------------------------------------------- #
def test_peak_bonus_per_beat_path():
    # 2 ứng viên NÃO chấm HỆT nhau -> cờ điểm nhô quyết thắng thua (đường rank_beat)
    brain = FakeBrain({"peak": ok("peak"), "plain": ok("plain")})
    r = rank_beat(make_beat(),
                  [cand("plain"), cand("peak", peak_value=0.85)], brain)
    assert r.chosen_key == "peak"
    by = {rc.asset_key: rc for rc in r.ranked}
    assert by["peak"].diem_may - by["plain"].diem_may == pytest.approx(PEAK_BONUS)


def test_peak_bonus_batch_path():
    # cùng verdict qua đường batch PA-1 (rank_beat_prescored) — bonus phải chảy Y HỆT
    from autoedit.ranker.funnel import rank_beat_prescored
    verdicts = {"peak": ok("peak"), "plain": ok("plain")}
    r = rank_beat_prescored(make_beat(),
                            [cand("plain"), cand("peak", peak_value=0.85)], verdicts)
    assert r.chosen_key == "peak"
    by = {rc.asset_key: rc for rc in r.ranked}
    assert by["peak"].diem_may - by["plain"].diem_may == pytest.approx(PEAK_BONUS)


# --------------------------------------------------------------------------- #
# 4. Cửa kỹ thuật + kill-log đếm đúng
# --------------------------------------------------------------------------- #
def test_technical_gate_and_kill_log():
    brain = FakeBrain({"c": ok("c")})
    r = rank_beat(
        make_beat(),  # beat 4s -> video < 2s là quá ngắn (slow-mo quá 2x)
        [cand("a", watermark=True), cand("b", duration=1.5), cand("c")],
        brain,
    )
    assert r.kill_log == {"thu": 3, "hong_ky_thuat": 2, "veto_nghia": 0,
                          "tra_lai_san": 0, "con_lai": 1}
    assert r.chosen_key == "c"


def test_technical_gate_counts_breathing_and_micro():
    """Hình thở 3.0: clip phải phủ beat + thở + giãn máy khi ô DƯỚI ngưỡng shot thở —
    beat 4s + thở 2.3s (<2.5) -> need 6.3: clip 2.9s loại (<3.15), clip 6s đậu.
    Giãn máy cũng tính: beat 4s + micro 0.7 -> need 4.7: clip 2.3 loại (<2.35)."""
    brain = FakeBrain({"long": ok("long")})
    r = rank_beat(make_beat(breathing_after=2.3),
                  [cand("short", duration=2.9), cand("long", duration=6.0)], brain)
    assert r.kill_log["hong_ky_thuat"] == 1 and r.chosen_key == "long"
    brain2 = FakeBrain({"long": ok("long")})
    r2 = rank_beat(make_beat(micro_pause_after=0.7),
                   [cand("short", duration=2.3), cand("long", duration=6.0)], brain2)
    assert r2.kill_log["hong_ky_thuat"] == 1 and r2.chosen_key == "long"


def test_need_dur_breath_shot_frees_beat_clip():
    """REGRESSION shot thở (MO_TA_SHOT_THO §3): ô >= 2.5s có shot thở riêng gánh phần
    sau HOLD -> clip beat chỉ cần phủ thoại + 0.5. Beat 4s + thở 5s: clip 4s TRƯỚC ĐÂY
    bị giết oan (4 < 9×0.5), giờ phải SỐNG; clip 6s vẫn hơn đúng DURATION_BONUS."""
    beat = make_beat(breathing_after=5.0)
    brain = FakeBrain({"short": ok("short"), "long": ok("long")})
    r = rank_beat(beat, [cand("short", duration=4.0), cand("long", duration=6.0)], brain)
    assert r.kill_log["hong_ky_thuat"] == 0
    short = next(rc for rc in r.ranked if rc.asset_key == "short")
    long_ = next(rc for rc in r.ranked if rc.asset_key == "long")
    # need 4.5 -> chỉ clip >= 5.4 (1.2x) ăn bonus độ dài; 4.0 thiếu nhưng KHÔNG chết
    assert long_.diem_may - short.diem_may == pytest.approx(0.5)


def test_image_without_duration_passes_technical_gate():
    brain = FakeBrain({"img": ok("img")})
    r = rank_beat(make_beat(), [cand("img", media_type="image", duration=None)], brain)
    assert r.chosen_key == "img"
    assert r.kill_log["hong_ky_thuat"] == 0


def test_empty_pool_after_technical_gate_needs_human():
    brain = FakeBrain({})
    r = rank_beat(make_beat(), [cand("a", watermark=True)], brain)
    assert r.needs_human and brain.calls == 0  # không phí call NÃO khi pool trống


# --------------------------------------------------------------------------- #
# 5. NÃO đúng 1 call/beat + bỏ sót -> trung tính, không loại
# --------------------------------------------------------------------------- #
def test_one_brain_call_per_beat_and_usage_logged():
    brain = FakeBrain({"a": ok("a"), "b": ok("b")})
    r = rank_beat(make_beat(), [cand("a"), cand("b")], brain)
    assert brain.calls == 1
    assert r.input_tokens == 100 and r.output_tokens == 50


def test_missing_verdict_gets_neutral_score_not_killed():
    brain = FakeBrain({"a": ok("a", nghia=3, mood=3)})  # NÃO quên "b"
    r = rank_beat(make_beat(), [cand("a"), cand("b")], brain)
    b = next(rc for rc in r.ranked if rc.asset_key == "b")
    assert b.diem_nghia == 5 and b.verdict == "ok"
    assert r.chosen_key == "b"  # trung tính 5/5 thắng 3/3
    assert any("bỏ sót" in w for w in r.warnings)


def test_ranked_sorted_desc_and_reason_surfaced():
    brain = FakeBrain({
        "a": ok("a", nghia=4), "b": ok("b", nghia=9, ly_do="đúng phố cổ Hà Nội"),
        "c": ok("c", nghia=6),
    })
    r = rank_beat(make_beat(), [cand("a"), cand("b"), cand("c")], brain)
    assert [rc.asset_key for rc in r.ranked] == ["b", "c", "a"]
    assert r.chosen_ly_do == "đúng phố cổ Hà Nội"
    assert r.kill_log["thu"] == 3 and r.kill_log["con_lai"] == 3
    assert POOL_FLOOR == 3  # đóng băng c5


# --------------------------------------------------------------------------- #
# 6. PA-1+3 (2026-07-07): batch 1 call/chunk + auto-pick pool 1 + fallback
# --------------------------------------------------------------------------- #
from autoedit.ranker.funnel import rank_batch, rank_beat_prescored  # noqa: E402
from autoedit.ranker.schema import BatchRankResponse, BeatVerdicts  # noqa: E402


class FakeBatchBrain:
    """NÃO giả batch: chấm theo bảng (asset_key -> (nghia, mood)) cho MỌI beat trong prompt;
    biết 'quên' beat theo yêu cầu (test fallback)."""

    def __init__(self, scores=None, forget_beats=()):
        self.scores = scores or {}
        self.forget = set(forget_beats)
        self.calls = 0

    def complete(self, system, user, output_model, context=None):
        from autoedit.ranker.prompts import alias_of

        self.calls += 1
        assert output_model is BatchRankResponse
        rev = {alias_of(k): k for k in self.scores
               if not isinstance(k, tuple)}  # TOC-1: prompt in id ngắn
        rev.update({alias_of(k): k for (_, k) in [t for t in self.scores if isinstance(t, tuple)]})
        beats = []
        cur_id, cur_ids = None, []
        for ln in user.splitlines():
            if "=== BEAT #" in ln:
                if cur_id is not None:
                    beats.append((cur_id, cur_ids))
                cur_id, cur_ids = int(ln.split("#")[1].split(" ")[0]), []
            elif ". id: " in ln:
                cur_ids.append(ln.split(". id: ")[1].strip())
        if cur_id is not None:
            beats.append((cur_id, cur_ids))
        out = []
        for bid, ids in beats:
            if bid in self.forget:
                continue
            keys = [rev.get(a, a) for a in ids]
            n_m = [self.scores.get((bid, k)) or self.scores.get(k) or (5, 5) for k in keys]
            out.append(BeatVerdicts(beat_id=bid, verdicts=[
                CandidateVerdict(id=a, verdict="ok", diem_nghia=n, diem_mood=m,
                                 ly_do=f"hợp: {k}")
                for a, k, (n, m) in zip(ids, keys, n_m)]))
        return BatchRankResponse(beats=out), Usage(input_tokens=200, output_tokens=90)


def test_pool_one_autopick_no_brain_call():
    """PA-3: pool 1 sau cửa kỹ thuật -> chọn luôn, KHÔNG call NÃO."""
    brain = FakeBrain({"a": ok("a")})
    r = rank_beat(make_beat(), [cand("a")], brain)
    assert brain.calls == 0 and r.chosen_key == "a"
    assert "auto-pick" in r.chosen_ly_do
    assert not any("bỏ sót" in w for w in r.warnings)   # auto-pick không phải NÃO quên


def test_rank_batch_one_call_and_prescored_equals_per_beat():
    """PA-1 bất biến: batch vs per-beat CÙNG verdict -> CÙNG kết quả chọn/xếp hạng."""
    b1, b2 = make_beat(beat_id=1), make_beat(beat_id=2)
    cands1 = [cand("a"), cand("b"), cand("c")]
    cands2 = [cand("x"), cand("y"), cand("z")]
    scores = {"a": (4, 5), "b": (9, 8), "c": (6, 5), "x": (7, 7), "y": (3, 3), "z": (8, 6)}
    batch_brain = FakeBatchBrain(scores=scores)
    maps, tok, warns = rank_batch([(b1, cands1), (b2, cands2)], batch_brain)
    assert batch_brain.calls == 1 and tok == (200, 90) and warns == []

    r1 = rank_beat_prescored(b1, cands1, maps[1])
    r2 = rank_beat_prescored(b2, cands2, maps[2])
    # đối chứng: đường per-beat với cùng điểm
    p1 = rank_beat(b1, cands1, FakeBrain({k: ok(k, *scores[k]) for k in ("a", "b", "c")}))
    p2 = rank_beat(b2, cands2, FakeBrain({k: ok(k, *scores[k]) for k in ("x", "y", "z")}))
    assert r1.chosen_key == p1.chosen_key == "b"
    assert r2.chosen_key == p2.chosen_key == "z"
    assert [rc.asset_key for rc in r1.ranked] == [rc.asset_key for rc in p1.ranked]
    assert r1.kill_log == p1.kill_log


def test_rank_batch_skips_small_pools_and_flags_forgotten():
    """PA-3 trong batch: beat pool ≤1 không gửi NÃO (map {}); beat bị NÃO quên -> map None."""
    b1 = make_beat(beat_id=1)          # pool 1 -> auto
    b2 = make_beat(beat_id=2)          # NÃO sẽ quên
    b3 = make_beat(beat_id=3)
    maps, tok, warns = rank_batch(
        [(b1, [cand("solo")]), (b2, [cand("m"), cand("n")]), (b3, [cand("p"), cand("q")])],
        FakeBatchBrain(forget_beats={2}),
    )
    assert maps[1] == {}                       # không gửi -> prescored tự auto-pick
    assert maps[2] is None                     # quên -> caller rơi về 1 call/beat
    assert isinstance(maps[3], dict) and maps[3]
    assert any("quên beat 2" in w for w in warns)
    r1 = rank_beat_prescored(b1, [cand("solo")], maps[1])
    assert r1.chosen_key == "solo" and "auto-pick" in r1.chosen_ly_do


# --------------------------------------------------------------------------- #
# V3 (2026-07-09): video_subject = phạm vi chủ thể video — vòng ngoài veto thực thể
# --------------------------------------------------------------------------- #
def test_prompts_video_subject_line_and_veto_wording():
    """Có video_subject -> dòng VIDEO SUBJECT trong prompt (cả 1-beat lẫn batch);
    không có -> prompt Y NHƯ CŨ (project cũ fail-open). RANK_SYSTEM đã mở rộng
    thuc_the_sai sang sai-thiên-thể + 'khớp hành động không gỡ tội' (bài học b11)."""
    from autoedit.ranker.prompts import (
        RANK_SYSTEM,
        build_batch_rank_prompt,
        build_rank_prompt,
    )

    beat = make_beat()
    cands = [cand("pexels:1"), cand("pexels:2")]
    scope = "the Moon and its far side"

    p1 = build_rank_prompt(beat, cands, video_subject=scope)
    assert f"VIDEO SUBJECT (outer scope for entity vetoes): {scope}" in p1
    assert "VIDEO SUBJECT" not in build_rank_prompt(beat, cands)  # thiếu -> như cũ

    pb = build_batch_rank_prompt([(beat, cands)], video_subject=scope)
    assert f"VIDEO SUBJECT (outer scope for entity vetoes): {scope}" in pb
    assert "VIDEO SUBJECT" not in build_batch_rank_prompt([(beat, cands)])

    # luật veto mở rộng nằm trong system prompt (dùng chung cả 2 chế độ)
    assert "wrong PLANET" in RANK_SYSTEM
    assert "does NOT redeem a wrong entity" in RANK_SYSTEM


# --------------------------------------------------------------------------- #
# TOC-1 (2026-07-15): id NGẮN trong hội thoại NÃO — path 165 ký tự không vào
# prompt/verdict nữa (đo 3 bài: echo asset_key = 50-65% output token call rank)
# --------------------------------------------------------------------------- #
LONG_KEY = ("local:F:\\AutoEdit\\library\\deepsea\\nap\\Some-Very-Long-Draft-Name_Media_ABC\\"
            "Some-Very-Long-Draft-Name_Media_ABC__000411616_0006000_z112.mp4")


def test_prompt_uses_short_id_not_long_path():
    from autoedit.ranker.prompts import alias_of, build_batch_rank_prompt, build_rank_prompt

    beat = make_beat()
    # description tự đặt — cand() mặc định nhét key vào description làm nhiễu assert
    cands = [cand(LONG_KEY, description="deep sea anglerfish drifting"), cand("pexels:9")]
    p = build_rank_prompt(beat, cands)
    assert LONG_KEY not in p and f"id: {alias_of(LONG_KEY)}" in p
    pb = build_batch_rank_prompt([(beat, cands)])
    assert LONG_KEY not in pb and f"id: {alias_of(LONG_KEY)}" in pb


def test_alias_verdict_translated_back_to_asset_key():
    """NÃO trả id alias -> funnel dịch về asset_key thật; KHÔNG rơi nhánh 'bỏ sót'."""
    from autoedit.director.client import Usage as U
    from autoedit.ranker.prompts import alias_of

    class AliasBrain:  # NÃO thật sau TOC-1: chỉ echo mã ngắn, không biết asset_key
        def complete(self, system, user, output_model, context=None):
            v = [CandidateVerdict(id=alias_of(LONG_KEY), verdict="ok",
                                  diem_nghia=9, diem_mood=8, ly_do="đúng chủ thể"),
                 CandidateVerdict(id=alias_of("pexels:9"), verdict="ok",
                                  diem_nghia=4, diem_mood=4, ly_do="nhạt")]
            return BeatRankResponse(verdicts=v), U(input_tokens=1, output_tokens=1)

    r = rank_beat(make_beat(), [cand("pexels:9"), cand(LONG_KEY)], AliasBrain())
    assert r.chosen_key == LONG_KEY
    assert not any("bỏ sót" in w for w in r.warnings)


def test_batch_same_asset_same_alias_across_beats():
    """Cùng asset vào pool 2 beat -> CÙNG mã trong prompt batch (NÃO nhận ra asset lặp
    để né 'same asset win two beats' — tín hiệu này không được mất khi rút gọn id)."""
    from autoedit.ranker.prompts import alias_of, build_batch_rank_prompt

    b1, b2 = make_beat(beat_id=1), make_beat(beat_id=2)
    shared = cand("pexels:7")
    pb = build_batch_rank_prompt([(b1, [shared, cand("m")]), (b2, [shared, cand("n")])])
    assert pb.count(f"id: {alias_of('pexels:7')}") == 2


def test_alias_collision_falls_back_to_full_key(monkeypatch):
    from autoedit.ranker import prompts

    monkeypatch.setattr(prompts, "alias_of", lambda k: "aSAME")
    k2a, a2k = prompts.build_alias_maps([[{"asset_key": "k1"}, {"asset_key": "k2"}]])
    assert k2a["k1"] == "aSAME" and k2a["k2"] == "k2"   # ứng viên sau giữ key làm id
    assert a2k["aSAME"] == "k1" and a2k["k2"] == "k2"
