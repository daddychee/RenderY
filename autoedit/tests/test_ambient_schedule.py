"""Test C1 M2 — lập lịch ô thở + chọn ambient + wire _add_ambient (MO_TA_C1 §3).

Lịch dùng chung ducking (test riêng khỏi trùng test_ducking); phần wire chạy pycapcut
thật với WAV nhỏ, scene_lookup tiêm tay để không đụng cache.db máy.
"""

from __future__ import annotations

import math
import sqlite3
import struct
import wave
from pathlib import Path

import pytest

from autoedit.ambient import schedule as amb
from autoedit.ambient.schedule import (
    NOISY_KINDS,
    AmbientSlot,
    breath_slots,
    choose_drone,
    choose_files,
    db_scene_lookup,
    db_subject_lookup,
    resolve_scene,
    subject_beat_slots,
    subject_kind,
)
from autoedit.packager.assembler import (
    _add_ambient,
    _add_drone,
    _add_hook_sfx,
    _add_subject_sfx,
    _beat_has_priority_visual,
)
from autoedit.project import Beat, BreathShot, Inputs, Project, ShotPick, StageRecord, StageStatus, VoiceSegment

SEC = 1_000_000


def _seg(seg_id, ts, te, beat_ids, breathing=0.0, micro=0.0) -> VoiceSegment:
    return VoiceSegment(
        segment_id=seg_id, path=f"segments/seg_{seg_id:03d}.wav",
        source_start=ts, source_end=te, timeline_start=ts, timeline_end=te,
        beat_ids=beat_ids, breathing_after=breathing, micro_pause_after=micro,
    )


def _project(tmp_path, **kw) -> Project:
    return Project(
        project_id="t", title="t", created_at="2026-07-10", project_dir=str(tmp_path),
        inputs=Inputs(script_path="s", voice_path="v", original_script_path="s",
                      original_voice_path="v", script_text="x"),
        niche="space", **kw,
    )


def _wav(path: Path, sec: float = 8.0) -> None:
    rate = 48000
    frames = bytearray()
    for i in range(int(sec * rate)):
        frames += struct.pack("<h", int(4000 * math.sin(2 * math.pi * 110 * i / rate)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(bytes(frames))


# ===================== lập lịch (pure) ========================================
def test_breath_slots_gaps_tail_and_beat_id():
    segs = [_seg(1, 0.0, 10.0, [0, 1], breathing=4.0),   # ô giữa 10-14 (beat 1 mang ô)
            _seg(2, 14.0, 20.0, [2], breathing=5.0)]     # ô kết video 20-25 (beat 2)
    slots = breath_slots(segs)
    assert [(s.start, s.end, s.beat_id) for s in slots] == [(10.0, 14.0, 1), (20.0, 25.0, 2)]


def test_breath_slots_short_gap_and_micro_skipped():
    # nghỉ 1.0s < MIN_BREATH bị merge (vi nghỉ); ô 2.0s < AMB_MIN bị lọc
    segs = [_seg(1, 0.0, 4.0, [0]), _seg(2, 5.0, 8.0, [1], breathing=0.0),
            _seg(3, 10.0, 15.0, [2])]                    # gap 8-10 = 2.0s
    assert breath_slots(segs) == []


def test_breath_slots_empty_segments():
    assert breath_slots([]) == []


# ===================== phân giải loại cảnh ====================================
def test_resolve_scene_breath_shot_first_then_pick():
    lookup = {"local:LIB/breath.mp4": "space", "local:LIB/pick.mp4": "sky_cloud"}.get
    look = lambda k: lookup(k) or ""  # noqa: E731
    project = _project(Path("."), breath_shots=[
        BreathShot(beat_id=1, asset_path="assets/b1.mp4", asset_key="local:LIB/breath.mp4"),
    ], shots=[
        ShotPick(beat_id=1, asset_path="a.mp4", asset_key="local:LIB/pick.mp4", source="local"),
        ShotPick(beat_id=2, asset_path="b.mp4", asset_key="pexels:9", source="pexels"),
    ])
    # beat 1: miếng shot thở ĐẦU thắng pick
    assert resolve_scene(AmbientSlot(0, 3, beat_id=1), project, look) == "space"
    # beat 2: không shot thở -> pick; stock không tag -> "" (mù)
    assert resolve_scene(AmbientSlot(0, 3, beat_id=2), project, look) == ""
    # beat không có gì
    assert resolve_scene(AmbientSlot(0, 3, beat_id=7), project, look) == ""


def test_db_scene_lookup_local_only():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE library_assets (path TEXT, scene_type TEXT)")
    conn.execute("INSERT INTO library_assets VALUES ('F:/lib/x.mp4', 'space')")
    look = db_scene_lookup(conn)
    assert look("local:F:/lib/x.mp4") == "space"
    assert look("local:F:/lib/missing.mp4") == ""   # không có dòng db
    assert look("pexels:123") == ""                 # stock không tra


# ===================== chọn file ==============================================
def test_choose_files_rotation_and_fallback(tmp_path):
    lib = tmp_path / "space"
    lib.mkdir()
    for n in ("space.wav", "space_2.wav", "default.wav"):
        _wav(lib / n, sec=0.3)
    slots = [AmbientSlot(0, 4, scene_type="space"), AmbientSlot(10, 14, scene_type="space"),
             AmbientSlot(20, 24, scene_type="space"),
             AmbientSlot(30, 34, scene_type="underwater"),   # kho thiếu -> default
             AmbientSlot(40, 44, scene_type="")]             # mù tag -> default
    choose_files(slots, lib)
    # 3 slot space xoay vòng 2 biến thể; 2 slot rơi về default (chỉ 1 biến thể)
    assert [s.file.name for s in slots] == [
        "space.wav", "space_2.wav", "space.wav", "default.wav", "default.wav"]
    assert "thiếu 'underwater'" in slots[3].note and "mù tag" in slots[4].note


def test_choose_files_empty_library_skips(tmp_path):
    lib = tmp_path / "space"
    lib.mkdir()
    slots = [AmbientSlot(0, 4, scene_type="space")]
    choose_files(slots, lib)
    assert slots[0].file is None and "bỏ" in slots[0].note


# ===================== wire _add_ambient ======================================
@pytest.fixture
def script():
    from pycapcut import ScriptFile
    return ScriptFile(1920, 1080, fps=30)


def _record() -> StageRecord:
    return StageRecord(status=StageStatus.RUNNING)


def test_add_ambient_places_segments(tmp_path, script):
    lib = tmp_path / "amb" / "space"
    lib.mkdir(parents=True)
    for n in ("space.wav", "default.wav"):
        _wav(lib / n, sec=8.0)
    project = _project(
        tmp_path,
        segments=[_seg(1, 0.0, 10.0, [0, 1], breathing=4.0), _seg(2, 14.0, 20.0, [2], breathing=5.0)],
        breath_shots=[BreathShot(beat_id=1, asset_path="assets/b1.mp4", asset_key="local:LIB/b.mp4")],
        shots=[ShotPick(beat_id=2, asset_path="x.mp4", asset_key="pexels:9", source="pexels")],
    )
    rec = _record()
    _add_ambient(script, project, rec, niche_path=lib,
                 scene_lookup=lambda k: "space" if k == "local:LIB/b.mp4" else "")
    track = script.tracks["ambient"]
    assert len(track.segments) == 2
    s1, s2 = track.segments
    # ô 1: 10-14s, scene space; ô 2 (kết video): 20-25s, mù tag -> default
    assert (s1.target_timerange.start, s1.target_timerange.duration) == (10 * SEC, 4 * SEC)
    assert (s2.target_timerange.start, s2.target_timerange.duration) == (20 * SEC, 5 * SEC)
    assert s1.volume == amb.AMBIENT_VOL and s2.volume == amb.AMBIENT_VOL
    assert s1.source_timerange.start == 0                      # cắt từ đầu file
    assert s1.fade is not None and s1.fade.in_duration == SEC  # fade 1.0s 2 mép
    log = project.ambient_log
    assert [a["file"] for a in log] == ["space.wav", "default.wav"]
    assert log[0]["scene_type"] == "space" and log[1]["scene_type"] == ""
    assert any("ambient C1: 2/2" in w for w in rec.warnings)


def test_add_ambient_fail_open(tmp_path, script):
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0)]
    # (a) không niche -> tắt
    p1 = _project(tmp_path, segments=segs)
    p1.niche = None
    _add_ambient(script, p1, _record(), niche_path=tmp_path / "x")
    assert "ambient" not in script.tracks and p1.ambient_log == []
    # (b) kho niche chưa tồn tại -> tắt
    p2 = _project(tmp_path, segments=segs)
    _add_ambient(script, p2, _record(), niche_path=tmp_path / "chua_co")
    assert "ambient" not in script.tracks and p2.ambient_log == []
    # (c) kho rỗng -> không đặt gì nhưng log ghi lý do bỏ (editor thấy trên report)
    empty = tmp_path / "amb2" / "space"
    empty.mkdir(parents=True)
    p3 = _project(tmp_path, segments=segs)
    _add_ambient(script, p3, _record(), niche_path=empty, scene_lookup=lambda k: "")
    assert "ambient" not in script.tracks
    assert len(p3.ambient_log) == 1 and p3.ambient_log[0]["file"] is None


def test_add_ambient_short_file_truncates(tmp_path, script):
    lib = tmp_path / "amb" / "space"
    lib.mkdir(parents=True)
    _wav(lib / "default.wav", sec=2.0)   # file 2s < ô 4s
    project = _project(tmp_path, segments=[_seg(1, 0.0, 10.0, [0], breathing=4.0)])
    _add_ambient(script, project, _record(), niche_path=lib, scene_lookup=lambda k: "")
    seg = script.tracks["ambient"].segments[0]
    assert seg.target_timerange.duration < 4 * SEC          # phủ được tới đâu hay tới đó
    assert "file ngắn" in project.ambient_log[0]["note"]


# ===================== C đợt 3b — S2 chủ thể ==================================
def _beat(bid, t0, t1, concept="", graphic=False) -> Beat:
    b = Beat(beat_id=bid, chapter=1, text="t", start_word=0, end_word=1,
             start=t0, end=t1, energy="low", mood="calm",
             visual_level="literal", visual_concept=concept, shot_size="wide")
    b.timeline_start, b.timeline_end = t0, t1
    if graphic:
        b.graphic_asset = "chart.mp4"
    return b


def _pick(bid, key, source="pexels", path="x.mp4") -> ShotPick:
    return ShotPick(beat_id=bid, asset_path=path, asset_key=key, source=source)


def test_subject_kind_word_boundary():
    assert subject_kind("Boiling sun surface with flares") == "fire"  # lửa THẬT (boiling)
    assert subject_kind("sunset over the city") == ""          # 'sunset' KHÔNG ăn 'sun'
    assert subject_kind("rocket launch pad at night") == "rocket"
    assert subject_kind("spiral galaxy stars") == ""
    assert subject_kind("") == ""


def test_subject_kind_sun_needs_close_shot():
    """Tai V7 (user 2026-07-10): tiếng lửa cho mặt trời CHỈ khi quay cận cảnh (editor
    gốc làm vậy); có lửa thật trên hình (lava/flame) thì cỡ nào cũng kêu."""
    assert subject_kind("bright sun in the sky", "wide") == ""
    assert subject_kind("bright sun in the sky", "close_up") == "fire"
    assert subject_kind("sun granulation detail", "extreme_close_up") == "fire"
    assert subject_kind("burning flame in the dark", "wide") == "fire"  # lửa cháy thật — kêu luôn
    # V8 b42: "volcanic rock formations" aerial (nham thạch NGUỘI) dính tag lava
    assert subject_kind("volcanic lava rock formations", "aerial") == ""
    assert subject_kind("glowing lava flow", "close_up") == "fire"


def test_subject_kind_per_niche_rules_phrase():
    """Kind loài deepsea (sheet SFX editor 2026-07-13): rules per-niche THAY built-in,
    match được CỤM TỪ — 'sperm whale' không dính 'humpback whale'; bare 'whale' cố ý
    KHÔNG match (tránh loạn tiếng — filter-overload)."""
    rules = (
        ("whale_sperm", ("sperm whale", "sperm whales")),
        ("whale_humpback", ("humpback whale", "humpback")),
        ("whale_orca", ("orca", "orcas", "killer whale")),
        ("attack", ("attack", "attacking", "hunting")),
        ("splash", ("breach", "breaching", "splash")),
    )
    assert subject_kind("a sperm whale diving into the abyss", rules=rules) == "whale_sperm"
    assert subject_kind("humpback whale song underwater", rules=rules) == "whale_humpback"
    assert subject_kind("pod of orcas swimming", rules=rules) == "whale_orca"
    # loài TRƯỚC hành động: orca đang săn -> tiếng orca (không phải whoosh attack)
    assert subject_kind("killer whale attacking a seal", rules=rules) == "whale_orca"
    assert subject_kind("shark hunting prey at night", rules=rules) == "attack"
    assert subject_kind("whale breaching the surface", rules=rules) == "splash"
    assert subject_kind("a lone whale in deep water", rules=rules) == ""  # bare 'whale' im
    # rules per-niche THAY TRỌN built-in: rocket không còn match
    assert subject_kind("rocket launch pad", rules=rules) == ""
    # rules=None -> built-in giữ nguyên (space không đổi hành vi)
    assert subject_kind("rocket launch pad") == "rocket"


# Bảng rút gọn từ subject_rules.yaml life-in THẬT (các kind dính 5 ca user chê)
_LIFEIN = (
    ("camel", ("camel", "camels")),
    ("market", ("market", "souk", "bazaar", "vendor")),
    ("urban_street", ("street", "city", "cityscape", "town", "road", "shop", "traffic")),
    ("wind", ("desert", "dune", "sand", "canyon", "cliff", "mountain", "arid")),
    ("ocean", ("beach", "shore", "coast", "harbor", "bay")),
    ("people_activity", ("crowd", "festival", "ceremony", "procession")),
)


@pytest.mark.parametrize("subj, tags_desc, cu, moi", [
    # 5 ca user CHÊ ở cổng TAI RD-89 đợt 2 (2026-07-18) — tag THẬT lấy từ sổ
    ("lemons", 'lemons fruit yellow food produce market fresh. A pile of lemons.',
     "market", ""),                       # b061 quả chanh KHÔNG kêu tiếng chợ
    ("sunset beach", 'beach sunset waves sand ocean. Waves rolling onto a sandy beach.',
     "wind", "ocean"),                    # b099 sóng biển: gió -> tiếng biển
    ("Sultan Qaboos Grand Mosque", 'mosque Oman Muscat architecture sunset garden cityscape',
     "urban_street", ""),                 # b008 lâu đài/đền KHÔNG kêu tiếng phố
    ("man walking desert", 'desert walking solitude dirt road palm trees landscape',
     "urban_street", "wind"),             # b019 người giữa sa mạc: tiếng xe -> gió
    # b033 cận mặt người: subject "Omani men" mù chữ -> tag `desert` cứu -> VẪN wind.
    # GIỮ NGUYÊN có chủ đích: wind KHÔNG ồn, người Oman đứng giữa sa mạc mà nghe gió là
    # hợp lý — user chê ca này ở bản CŨ khi nó nằm giữa loạt sai khác. Đo cả RD-89 chỉ
    # 1 ca cận-cảnh-người dạng này -> không đẻ luật riêng cho 1 ca (P2). Tầng LLM (tùy
    # chọn) mới là chỗ dọn nốt phần đuôi này.
    ("Omani men", 'Oman culture traditional clothing men beards desert',
     "wind", "wind"),
])
def test_subject_beats_background_tags(subj, tags_desc, cu, moi):
    """📌 CHỦ THỂ ĐÈ PHÔNG NỀN (cổng TAI RD-89 đợt 2). `tags` liệt kê mọi thứ GLM nhìn
    thấy, không phân biệt chủ thể với phông nền -> chanh-trong-chợ kêu tiếng chợ.
    `cu` = kind sai mà bản trước phát ra; `moi` = kind đúng ("" = im)."""
    full = f"{subj} {tags_desc}"
    assert subject_kind(full, "", rules=_LIFEIN) == cu          # tái hiện bug
    assert subject_kind(full, "", rules=_LIFEIN, subject=subj) == moi


def test_noisy_kind_needs_named_subject():
    """Kind ỒN (user chốt: ưu tiên tiếng dễ nghe) phải ĐÍCH DANH trong subject mới kêu;
    kind dễ nghe vẫn được tag bối cảnh cứu khi subject mù chữ."""
    # subject mù chữ + tag phố -> IM (urban_street thuộc NOISY_KINDS)
    assert subject_kind("residential neighborhood city road", "",
                        rules=_LIFEIN, subject="residential neighborhood") == ""
    # nhưng subject GỌI TÊN thì kêu bình thường
    assert subject_kind("busy city street", "", rules=_LIFEIN,
                        subject="busy city street") == "urban_street"
    # kind DỄ NGHE (ocean) vẫn được bối cảnh cứu — không đòi bằng chứng cao
    assert subject_kind("aerial landscape with coast", "",
                        rules=_LIFEIN, subject="aerial landscape") == "ocean"
    assert "urban_street" in NOISY_KINDS and "ocean" not in NOISY_KINDS


def test_subject_none_keeps_old_behavior():
    """subject=None -> hành vi CŨ y nguyên (caller/test cũ không bị lật ngầm)."""
    assert subject_kind("lemons at the market", "", rules=_LIFEIN) == "market"


def test_db_subject_lookup_joins_text():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE library_assets (path TEXT, subject TEXT, tags TEXT, "
                 "description TEXT, shot_size TEXT)")
    conn.execute("INSERT INTO library_assets VALUES ('F:/lib/sun.mp4', 'sun', "
                 "'[\"sun\", \"solar\"]', 'A boiling sun surface.', 'close_up')")
    look = db_subject_lookup(conn)
    text, shot, subj = look("local:F:/lib/sun.mp4")
    assert "boiling" in text and "solar" in text and shot == "close_up"
    assert subj == "sun"      # subject TÁCH RIÊNG — phân biệt chủ thể với phông nền
    assert look("local:F:/lib/missing.mp4") == ("", "", "")
    assert look("pexels:123") == ("", "", "")


def test_choose_files_subject_beats_scene(tmp_path):
    lib = tmp_path / "space"
    lib.mkdir()
    for n in ("fire.wav", "space.wav", "default.wav"):
        _wav(lib / n, sec=0.3)
    slots = [AmbientSlot(0, 4, scene_type="space", subject_kind="fire"),
             AmbientSlot(10, 14, scene_type="space", subject_kind="water")]  # kho không có water
    choose_files(slots, lib)
    assert slots[0].file.name == "fire.wav" and "chủ thể thắng 'space'" in slots[0].note
    assert slots[1].file.name == "space.wav" and "kho thiếu chủ thể 'water'" in slots[1].note


def test_subject_beat_slots_match_driven_no_caps():
    """Milestone C (user chốt 2026-07-13): BỎ trần SUBJ_CAP/không-kề/≤2-lần-kind —
    footage match là đặt (như editor). Vẫn giữ: đồ họa skip, beat ngắn skip, SUBJ_MAX.
    Hồi quy đảo chiều của test caps cũ: beat kề + kind lặp lần 3 GIỜ PHẢI CÓ tiếng."""
    texts = {
        "local:LIB/sun.mp4": "sun boiling surface",
        "local:LIB/lava.mp4": "burning lava flow",
        "local:LIB/meteor.mp4": "meteor collision crater",
        "local:LIB/flame.mp4": "fire and flame",
        "local:LIB/sun2.mp4": "burning sun",
        "local:LIB/rocket.mp4": "rocket launch pad",
        "local:LIB/rocket2.mp4": "rocket in flight",
    }
    project = _project(Path("."), beats=[
        _beat(1, 0.0, 5.0),                       # fire
        _beat(2, 5.0, 12.0),                      # LIỀN KỀ beat 1 — giờ VẪN đặt (fire)
        _beat(4, 12.0, 18.0),                     # explosion
        _beat(6, 20.0, 26.0),                     # fire lần 2
        _beat(8, 28.0, 34.0),                     # fire lần 3 — giờ VẪN đặt (hết trần kind)
        _beat(10, 36.0, 42.0, graphic=True),      # đồ họa -> vẫn skip
        _beat(12, 43.0, 45.0),                    # ngắn <AMB_MIN -> vẫn skip
        _beat(14, 46.0, 60.0),                    # rocket, cắt SUBJ_MAX
    ], shots=[
        _pick(1, "local:LIB/sun.mp4", "local"), _pick(2, "local:LIB/lava.mp4", "local"),
        _pick(4, "local:LIB/meteor.mp4", "local"), _pick(6, "local:LIB/flame.mp4", "local"),
        _pick(8, "local:LIB/sun2.mp4", "local"), _pick(10, "local:LIB/rocket.mp4", "local"),
        _pick(12, "local:LIB/rocket.mp4", "local"), _pick(14, "local:LIB/rocket2.mp4", "local"),
    ])
    slots = subject_beat_slots(project, lambda k: (texts.get(k, ""), ""),
                               skip_beat=_beat_has_priority_visual)
    assert [(s.beat_id, s.kind, s.source) for s in slots] == [
        (1, "fire", "kho"), (2, "fire", "kho"), (4, "explosion", "kho"),
        (6, "fire", "kho"), (8, "fire", "kho"), (14, "rocket", "kho")]
    assert slots[-1].end - slots[-1].start == pytest.approx(amb.SUBJ_MAX)  # beat 14s cắt 10s


def test_subject_llm_only_fills_blind_beats():
    """TẦNG 3 chỉ điền beat bảng luật MÙ CHỮ — KHÔNG lật ca bảng luật đã quyết.
    (Lật được = mất ổn định + mất mọi thứ đã qua cổng tai.) source='llm' để soi ở report."""
    rows = {                                   # (text, shot, subject)
        "local:LIB/a.mp4": ("rocket launch pad", "wide", "rocket launch pad"),  # luật QUYẾT
        "local:LIB/b.mp4": ("Omani village houses", "wide", "Omani village"),   # luật MÙ
    }
    project = _project(Path("."), beats=[_beat(1, 0.0, 6.0), _beat(2, 6.0, 12.0)],
                       shots=[_pick(1, "local:LIB/a.mp4", "local"),
                              _pick(2, "local:LIB/b.mp4", "local")])

    class Cl:
        def __init__(self): self.asked = []
        def complete(self, system, user, model):
            from autoedit.ambient.subject_llm import _Pick, _Picks
            self.asked.append(user)
            # NÃO cố tình trả CẢ beat 1 (đã có kind) — phải bị bỏ qua vì không hỏi tới nó
            return _Picks(picks=[_Pick(id=1, kind="water"), _Pick(id=2, kind="water")]), None

    cl = Cl()
    slots = subject_beat_slots(project, lambda k: rows.get(k, ("", "", "")),
                               llm=(cl, ["water", "rocket"]))
    assert [(s.beat_id, s.kind, s.source) for s in slots] == [
        (1, "rocket", "kho"),      # bảng luật GIỮ NGUYÊN, NÃO không lật được
        (2, "water", "llm")]       # beat mù chữ được NÃO điền
    assert "Omani village" in cl.asked[0] and "rocket launch pad" not in cl.asked[0]


def test_subject_llm_obeys_fire_close_shot_rule():
    """📌 Hồi quy VÒNG 3 (b063 jack-o'-lantern): quyết định NÃO PHẢI qua LUẬT AN TOÀN như
    đường bảng luật. NÃO gán `fire` cho cảnh medium không có lửa thật (tag `candlelight`)
    -> luật fire-cận-cảnh (tai V7) PHẢI chặn, đúng như nó chặn đường bảng luật.
    Lỗ hổng KIẾN TRÚC: NÃO lách được luật mà bảng luật vẫn phải tuân."""
    rows = {"local:LIB/p.mp4": ("halloween pumpkin candlelight spooky", "medium",
                                "jack-o'-lantern"),
            "local:LIB/f.mp4": ("bonfire burning at night", "medium", "bonfire")}

    class Cl:
        def complete(self, system, user, model):
            from autoedit.ambient.subject_llm import _Pick, _Picks
            return _Picks(picks=[_Pick(id=1, kind="fire"), _Pick(id=2, kind="fire")]), None

    project = _project(Path("."), beats=[_beat(1, 0.0, 6.0), _beat(2, 6.0, 12.0)],
                       shots=[_pick(1, "local:LIB/p.mp4", "local"),
                              _pick(2, "local:LIB/f.mp4", "local")])
    slots = subject_beat_slots(project, lambda k: rows.get(k, ("", "", "")),
                               llm=(Cl(), ["fire"]))
    # beat 1 (nến trong bí ngô, medium) bị luật chặn; beat 2 (lửa THẬT đang cháy) qua
    assert [(s.beat_id, s.kind) for s in slots] == [(2, "fire")]


def test_subject_llm_off_by_default():
    """llm=None (mặc định) -> beat mù chữ vẫn IM như trước, không gọi NÃO."""
    rows = {"local:LIB/b.mp4": ("Omani village houses", "", "Omani village")}
    project = _project(Path("."), beats=[_beat(2, 6.0, 12.0)],
                       shots=[_pick(2, "local:LIB/b.mp4", "local")])
    assert subject_beat_slots(project, lambda k: rows.get(k, ("", "", ""))) == []


def test_subject_beat_slots_skips_none_asset_path():
    """Regression DS3-084: beat needs_human có ShotPick nhưng asset_path=None (ảnh entity
    tải hỏng) → subject_beat_slots PHẢI bỏ qua, KHÔNG crash Path(None). Bug lộ ở video
    đầu tiên có needs_human (DS5-083 có 0 nên không gặp)."""
    texts = {"local:LIB/flame.mp4": "fire and flame"}
    project = _project(Path("."), beats=[
        _beat(1, 0.0, 5.0),      # có footage -> đặt
        _beat(2, 6.0, 12.0),     # needs_human, asset_path=None -> skip, không crash
    ], shots=[
        _pick(1, "local:LIB/flame.mp4", "local"),
        _pick(2, "", source="none", path=None),
    ])
    slots = subject_beat_slots(project, lambda k: (texts.get(k, ""), ""),
                               skip_beat=_beat_has_priority_visual)
    assert [(s.beat_id, s.kind) for s in slots] == [(1, "fire")]


def test_drone_vol_per_niche():
    """🔸 Bed ục ục deepsea to hơn drone space (đo 23 draft editor: vol 0.32-0.56)."""
    assert amb.drone_vol("space") == amb.DRONE_VOL
    assert amb.drone_vol(None) == amb.DRONE_VOL
    assert amb.drone_vol("deepsea") == pytest.approx(0.25)


def test_subject_beat_slots_concept_not_used():
    """Regression tai V5 (b22 mặt trăng nghe lửa, b56 dung nham nghe nước): stock không
    có tag vision -> KHÔNG tiếng, DÙ visual_concept có từ match — concept ≠ footage thật."""
    project = _project(Path("."), beats=[_beat(1, 0.0, 8.0, concept="rocket launch")],
                       shots=[_pick(1, "pexels:9")])
    assert subject_beat_slots(project, lambda k: ("", "")) == []


def test_subject_beat_slots_image_no_sfx():
    """Regression tai V7 (b12 ảnh Artemis kêu tiếng rocket): footage là ẢNH
    (entity/Ken Burns) đứng yên -> KHÔNG SFX, dù tag match."""
    project = _project(Path("."), beats=[_beat(1, 0.0, 8.0)],
                       shots=[_pick(1, "entity-cache:artemis", "entity", path="assets/b1.jpg")])
    assert subject_beat_slots(project, lambda k: ("rocket launch pad", "wide")) == []


def test_subject_beat_slots_multishot_clips_to_shot1():
    """Beat 2 shot: tiếng chủ thể match shot 1 phải dừng ở mép chia shot (split_window
    dùng chung với assembler — không tràn sang shot 2)."""
    from autoedit.project import ExtraShot

    pick = _pick(1, "local:LIB/rocket.mp4", "local")
    pick.extra_shots = [ExtraShot(asset_path="y.mp4")]
    project = _project(Path("."), beats=[_beat(1, 0.0, 8.0)], shots=[pick])
    slots = subject_beat_slots(project, lambda k: ("rocket launch", ""))
    assert len(slots) == 1 and slots[0].end == pytest.approx(4.0)  # shot 1 = nửa đầu beat


def test_add_subject_sfx_places(tmp_path, script):
    lib = tmp_path / "amb" / "space"
    lib.mkdir(parents=True)
    for n in ("fire.wav", "rocket.wav"):
        _wav(lib / n, sec=12.0)
    texts = {"local:LIB/sun.mp4": "sun boiling", "local:LIB/rk.mp4": "rocket launch pad"}
    project = _project(tmp_path, beats=[
        _beat(1, 0.0, 6.0), _beat(3, 8.0, 20.0),
    ], shots=[_pick(1, "local:LIB/sun.mp4", "local"), _pick(3, "local:LIB/rk.mp4", "local")])
    _add_subject_sfx(script, project, _record(), niche_path=lib,
                     subject_lookup=lambda k: (texts.get(k, ""), ""))
    s1, s2 = script.tracks["ambient"].segments
    assert (s1.target_timerange.start, s1.target_timerange.duration) == (0, 6 * SEC)
    assert (s2.target_timerange.start, s2.target_timerange.duration) == (8 * SEC, 10 * SEC)
    # -8dB trong voice (user chốt 2026-07-18, nâng từ -15dB PB13). Ghim SỐ TRẦN có chủ
    # đích: đổi mức nghe được là quyết định của TAI USER, phải bắt buộc sửa test kèm.
    assert s1.volume == amb.SUBJECT_VOL == 0.40
    assert [(a["kind"], a["source"], a["file"]) for a in project.subject_sfx_log] == [
        ("fire", "kho", "fire.wav"), ("rocket", "kho", "rocket.wav")]


def test_add_subject_sfx_fail_open(tmp_path, script):
    project = _project(tmp_path, beats=[_beat(1, 0.0, 6.0, concept="fire")],
                       shots=[_pick(1, "pexels:1")])
    _add_subject_sfx(script, project, _record(), niche_path=tmp_path / "chua_co",
                     subject_lookup=lambda k: ("", ""))
    assert "ambient" not in script.tracks and project.subject_sfx_log == []


# ===================== C đợt 3b — S1 drone nền ================================
def test_choose_drone_deterministic(tmp_path):
    lib = tmp_path / "space"
    lib.mkdir()
    for n in ("drone.wav", "drone_2.wav"):
        _wav(lib / n, sec=0.3)
    a, b = choose_drone(lib, "proj-x"), choose_drone(lib, "proj-x")
    assert a == b and a.name in ("drone.wav", "drone_2.wav")
    assert choose_drone(lib / "khong_co", "proj-x") is None


def test_add_drone_loops_and_fades(tmp_path, script):
    lib = tmp_path / "amb" / "space"
    lib.mkdir(parents=True)
    _wav(lib / "drone.wav", sec=8.0)
    # video 22s (voice 18 + thở kết 4) / file 8s -> 3 đoạn nối
    project = _project(tmp_path, segments=[_seg(1, 0.0, 18.0, [0], breathing=4.0)])
    _add_drone(script, project, _record(), niche_path=lib)
    segs = script.tracks["drone"].segments
    assert len(segs) == 3 and project.drone_log["loops"] == 3
    assert sum(s.target_timerange.duration for s in segs) == 22 * SEC
    assert all(s.volume == amb.DRONE_VOL for s in segs)
    seam = round(amb.SEAM_FADE * SEC)
    assert segs[0].fade.in_duration == 2 * SEC and segs[0].fade.out_duration == seam
    assert segs[1].fade.in_duration == seam and segs[1].fade.out_duration == seam
    assert segs[2].fade.out_duration == 3 * SEC
    assert project.drone_log["file"] == "drone.wav"


def test_add_drone_fail_open(tmp_path, script):
    # kho có ambient khác nhưng KHÔNG có kind drone -> tầng tắt
    lib = tmp_path / "amb" / "space"
    lib.mkdir(parents=True)
    _wav(lib / "space.wav", sec=0.3)
    project = _project(tmp_path, segments=[_seg(1, 0.0, 10.0, [0])])
    _add_drone(script, project, _record(), niche_path=lib)
    assert "drone" not in script.tracks and project.drone_log == {}


# ============ SFX-LOAI-C sửa: bed gate theo CẢNH (sheet editor 2026-07-13) ==========
def test_bed_intervals_merge_and_min():
    """Bed chỉ trên beat cảnh underwater: beat liền nhau gộp 1 run, run < BED_MIN bỏ,
    beat mù tag/không pick = gap (fail-open từng beat)."""
    project = _project(
        Path("."),
        segments=[_seg(1, 0.0, 40.0, [1, 2, 3, 4, 5], breathing=4.0)],
        beats=[_beat(1, 0.0, 8.0), _beat(2, 8.0, 16.0), _beat(3, 16.0, 24.0),
               _beat(4, 24.0, 30.0), _beat(5, 30.0, 40.0)],
        shots=[_pick(1, "local:a", "local"), _pick(2, "local:b", "local"),
               _pick(3, "local:c", "local"), _pick(4, "local:d", "local"),
               _pick(5, "local:e", "local")],
    )
    scene = {"local:a": "underwater", "local:b": "underwater",
             "local:c": "nature_water", "local:d": "underwater"}
    look = lambda k: scene.get(k, "")  # noqa: E731 — local:e mù tag
    # b1+b2 gộp [0,16]; b3 cảnh khác; b4 [24,30] = 6.0s đúng sàn BED_MIN; b5 mù
    assert amb.bed_intervals(project, look, ("underwater",)) == [(0.0, 16.0), (24.0, 30.0)]
    # run < BED_MIN bị bỏ: chỉ b4 match, dời timeline_start -> span [25,30) = 5s
    project.beats[3].timeline_start = 25.0
    scene2 = {"local:d": "underwater"}
    assert amb.bed_intervals(project, lambda k: scene2.get(k, ""), ("underwater",)) == []
    # beat CUỐI match -> run ăn tới hết video (breathing kết)
    scene3 = {"local:e": "underwater"}
    assert amb.bed_intervals(project, lambda k: scene3.get(k, ""), ("underwater",)) == [(30.0, 44.0)]


def test_add_drone_scene_gated(tmp_path, script):
    """Deepsea: bed đặt theo RUN cảnh underwater, mỗi run fade vào/ra riêng, vol 0.25;
    khoảng cảnh mặt biển KHÔNG có bed (user sửa nhận định 2026-07-13)."""
    lib = tmp_path / "amb" / "deepsea"
    lib.mkdir(parents=True)
    _wav(lib / "drone.wav", sec=8.0)
    project = _project(
        tmp_path,
        segments=[_seg(1, 0.0, 30.0, [1, 2, 3], breathing=0.0)],
        beats=[_beat(1, 0.0, 10.0), _beat(2, 10.0, 20.0), _beat(3, 20.0, 30.0)],
        shots=[_pick(1, "local:uw1", "local"), _pick(2, "local:surface", "local"),
               _pick(3, "local:uw2", "local")],
    )
    project.niche = "deepsea"
    scene = {"local:uw1": "underwater", "local:surface": "ocean_surface",
             "local:uw2": "underwater"}
    _add_drone(script, project, _record(), niche_path=lib,
               scene_lookup=lambda k: scene.get(k, ""))
    segs = script.tracks["drone"].segments
    # run 1 [0,10] file ~7.9s (8s - SAFETY_US) -> 2 đoạn; run 2 [20,30] -> 2 đoạn; [10,20] TRỐNG
    from autoedit.packager.assembler import SAFETY_US
    f_us = 8 * SEC - SAFETY_US
    assert [(s.target_timerange.start, s.target_timerange.duration) for s in segs] == [
        (0, f_us), (f_us, 10 * SEC - f_us), (20 * SEC, f_us), (20 * SEC + f_us, 10 * SEC - f_us)]
    assert all(s.volume == 0.25 for s in segs)
    seam = round(amb.SEAM_FADE * SEC)
    assert segs[0].fade.in_duration == 2 * SEC and segs[1].fade.out_duration <= 3 * SEC
    assert segs[2].fade.in_duration == 2 * SEC and segs[2].fade.out_duration == seam
    assert project.drone_log["runs"] == 2 and project.drone_log["covered_s"] == 20.0
    assert project.drone_log["gate"] == "underwater" and project.drone_log["loops"] == 4


def test_add_drone_gated_blind_db_off(tmp_path, script):
    """Gate cảnh mà mù tag toàn bộ -> KHÔNG bed (đè cảnh mặt biển tệ hơn không bed);
    space không gate -> loop cả bài y cũ (regression giữ nguyên)."""
    lib = tmp_path / "amb" / "deepsea"
    lib.mkdir(parents=True)
    _wav(lib / "drone.wav", sec=8.0)
    project = _project(tmp_path, segments=[_seg(1, 0.0, 10.0, [1])],
                       beats=[_beat(1, 0.0, 10.0)], shots=[_pick(1, "local:x", "local")])
    project.niche = "deepsea"
    rec = _record()
    _add_drone(script, project, rec, niche_path=lib, scene_lookup=lambda k: "")
    assert "drone" not in script.tracks and project.drone_log == {}
    assert any("không beat nào chiếu cảnh underwater" in w for w in rec.warnings)


def test_add_subject_sfx_clips_head_against_breath_ambient(tmp_path, script):
    """Regression V5-b11: hệ tọa độ kép lệch ~50ms — ô thở C1 (mốc SEGMENT) lấn đầu
    tiếng chủ thể của beat đứng ngay sau ô (mốc WORD) -> phải XÉN ĐẦU, không bỏ cả tiếng."""
    lib = tmp_path / "amb" / "space"
    lib.mkdir(parents=True)
    for n in ("default.wav", "rocket.wav"):
        _wav(lib / n, sec=8.0)
    project = _project(
        tmp_path,
        segments=[_seg(1, 0.0, 10.0, [1], breathing=4.0), _seg(2, 14.0, 22.0, [3])],
        beats=[_beat(3, 13.95, 20.0)],                            # lấn ô thở 10-14 50ms
        shots=[_pick(3, "local:LIB/rk.mp4", "local")],
    )
    _add_ambient(script, project, _record(), niche_path=lib, scene_lookup=lambda k: "")
    _add_subject_sfx(script, project, _record(), niche_path=lib,
                     subject_lookup=lambda k: ("rocket launch" if k == "local:LIB/rk.mp4" else "", ""))
    subj = [x for x in script.tracks["ambient"].segments if x.volume == amb.SUBJECT_VOL]
    assert len(subj) == 1
    assert subj[0].target_timerange.start == 14 * SEC            # xén về đúng mép ô thở
    assert "xén đầu né ô thở" in project.subject_sfx_log[0]["note"]
    assert project.subject_sfx_log[0]["file"] == "rocket.wav"


def test_add_ambient_subject_cut_to_piece(tmp_path, script):
    """Regression tai V5 (b20 fire tràn sang footage tên lửa, b46 signal tràn qua mốc
    tàu thăm dò): ô thở nhiều miếng — tiếng CHỦ THỂ (match miếng 1) phải DỪNG ở mốc kết
    miếng 1; tiếng loại-cảnh vẫn phủ trọn ô."""
    lib = tmp_path / "amb" / "space"
    lib.mkdir(parents=True)
    for n in ("fire.wav", "space.wav", "default.wav"):
        _wav(lib / n, sec=8.0)
    project = _project(
        tmp_path,
        segments=[_seg(1, 0.0, 10.0, [1], breathing=6.0)],   # ô thở 10-16
        breath_shots=[
            BreathShot(beat_id=1, asset_path="assets/p1.mp4", asset_key="local:LIB/sun.mp4", dur=2.5),
            BreathShot(beat_id=1, asset_path="assets/p2.mp4", asset_key="local:LIB/moon.mp4", dur=3.5),
        ],
    )
    _add_ambient(script, project, _record(), niche_path=lib,
                 scene_lookup=lambda k: "space",
                 subject_lookup=lambda k: ("boiling sun" if k == "local:LIB/sun.mp4" else "", ""))
    seg = script.tracks["ambient"].segments[0]
    assert (seg.target_timerange.start, seg.target_timerange.duration) == (10 * SEC, round(2.5 * SEC))
    assert "cắt theo miếng 1 (2.5s/6.0s)" in project.ambient_log[0]["note"]
    # PB13/user 2026-07-10: tiếng CHỦ THỂ thắng ô thở -> -10dB (loại CẢNH vẫn 0dB — V4)
    assert seg.volume == amb.SUBJECT_BREATH_VOL == 0.56  # -5dB (user chốt 2026-07-18)


# S3 whoosh auto ĐÃ BỎ (PB12 2026-07-10): 0/88 whoosh editor nằm ở mốc vào ô thở —
# test whoosh gỡ cùng code; whoosh đúng kiểu editor bám TEXT (overlay-SFX hiện có).


def test_subject_rules_specific_before_generic():
    """Regression V7 (kiểm tag vision thật trước cổng tai): rocket phụt lửa -> ROCKET
    (không phải fire); 'solar panels' không phải mặt trời; 'impact craters' tĩnh không nổ."""
    assert subject_kind("rocket ascending with fiery exhaust flame") == "rocket"
    assert subject_kind("spacecraft with solar panels orbiting") == ""
    assert subject_kind("grey cratered surface with impact craters") == ""
    assert subject_kind("meteor collision with planet") == "explosion"
    # tai V7 (b04): biển -> kind `ocean` (sóng nhẹ), KHÔNG rơi vào water (tiếng rót/sôi)
    assert subject_kind("full moon over dark ocean waves") == "ocean"
    assert subject_kind("pouring rain on window") == "water"


# ============ S3-HOOK: hit/whoosh/click tại cut trong hook (MO_TA_HOOK_SFX) ==========
def test_hook_sfx_slots_density_gap_and_kinds():
    """Hook 250s, cut mỗi 4s: bù đúng round(1.44 × 250/60) = 6 tiếng (📌 cổng tai V4
    2026-07-14: còn 30% số đo editor 4.8); cut trùng accent -> impact, cut thường ->
    whoosh TRƯỚC cut 80ms; mọi tiếng cách nhau ≥ HOOK_SFX_GAP."""
    cuts = [(4.0 * k, False) for k in range(1, 60)]
    slots = amb.hook_sfx_slots(cuts, 250.0, busy=[], accents=[8.0])
    assert len(slots) == round(amb.HOOK_SFX_PM * 250 / 60) == 6
    assert [(s.kind, s.t) for s in slots] == [
        ("whoosh", 3.92), ("impact", 8.0), ("whoosh", 11.92),
        ("whoosh", 15.92), ("whoosh", 19.92), ("whoosh", 23.92)]
    ts = [s.t for s in slots]
    assert all(b - a >= amb.HOOK_SFX_GAP for a, b in zip(ts, ts[1:]))
    # hồi quy cổng tai V4: hook 60s giờ chỉ BÙ 1 tiếng (trước fix: 5 — dày đặc)
    assert len(amb.hook_sfx_slots(cuts, 60.0, busy=[], accents=[8.0])) == 1


def test_hook_sfx_slots_click_photo_cap_and_busy():
    """Click bám cut VÀO ẢNH: trần HOOK_CLICK_CAP; vẫn đặt khi mật độ ĐÃ ĐỦ
    (hành vi editor: click đi với khoảnh khắc ảnh, không tính thay thế hit)."""
    photo_cuts = [(t, True) for t in (10.0, 20.0, 30.0, 40.0, 50.0, 55.0)]
    slots = amb.hook_sfx_slots(photo_cuts, 60.0, busy=[])
    assert [s.kind for s in slots] == ["click"] * amb.HOOK_CLICK_CAP
    # busy dày (6 tiếng ≥ đích 1) -> deficit ≤ 0, KHÔNG impact/whoosh, click vẫn vào
    busy = [5.0, 15.0, 25.0, 35.0, 45.0, 55.0]
    slots = amb.hook_sfx_slots([(10.0, True), (26.5, False)], 60.0, busy=busy)
    assert [s.kind for s in slots] == ["click"] and slots[0].t == 10.0


def test_hook_sfx_slots_bounds():
    """Fail-open biên: hook rỗng -> []; cut <0.5s đầu video / ngoài hook bị bỏ."""
    assert amb.hook_sfx_slots([(5.0, False)], 0.0) == []
    assert amb.hook_sfx_slots([(0.2, False), (70.0, False)], 60.0) == []


def test_add_hook_sfx_places(tmp_path, script):
    """Wire: deepsea + kho đủ 3 kind -> click bám ảnh + impact tại cut-accent trên
    track sfx, vol HOOK_SFX_VOL, log t/kind/file; hook = tới timeline_start chương 2."""
    lib = tmp_path / "amb" / "deepsea"
    lib.mkdir(parents=True)
    for n in ("impact.wav", "whoosh.wav", "click.wav"):
        _wav(lib / n, sec=2.0)
    b1, b2 = _beat(1, 0.0, 90.0), _beat(2, 90.0, 100.0)
    b2.chapter = 2
    project = _project(tmp_path, beats=[b1, b2],
                       segments=[_seg(1, 0.0, 100.0, [1, 2])])
    project.niche = "deepsea"
    project.outline = {"chapters": [{"chapter_id": 1}, {"chapter_id": 2}]}
    cuts = [(4.0, False), (8.0, False), (12.0, True), (20.0, False), (95.0, False)]
    _add_hook_sfx(script, project, _record(), cuts, accents=[8.0], niche_path=lib)
    segs = script.tracks["sfx"].segments
    # hook 90s -> đích round(1.44*1.5)=2: click@12 (bám ảnh) + impact@8 (accent, bù 1);
    # cut 4/20 thường KHÔNG whoosh (deficit hết — cổng tai V4); cut 95s ngoài hook
    assert [(s.target_timerange.start, s.volume) for s in segs] == [
        (8 * SEC, amb.HOOK_SFX_VOL), (12 * SEC, amb.HOOK_SFX_VOL)]
    assert [(e["kind"], e["file"]) for e in project.hook_sfx_log] == [
        ("impact", "impact.wav"), ("click", "click.wav")]


def test_add_hook_sfx_gate_niche_off(tmp_path, script):
    """Niche chưa có số đo (travel) -> tầng TẮT dù kho có file. Space BẬT 2026-07-14
    (mượn số deepsea 🔸 — user chốt); travel vẫn chờ đo."""
    lib = tmp_path / "amb" / "travel"
    lib.mkdir(parents=True)
    _wav(lib / "impact.wav", sec=2.0)
    project = _project(tmp_path, beats=[_beat(1, 0.0, 10.0)])
    project.niche = "travel"
    project.outline = {"chapters": [{"chapter_id": 1}]}
    _add_hook_sfx(script, project, _record(), [(4.0, False)], niche_path=lib)
    assert "sfx" not in script.tracks and project.hook_sfx_log == []
    assert "space" in amb.hook_sfx_niches()  # hồi quy: space không bị rơi khỏi gate
