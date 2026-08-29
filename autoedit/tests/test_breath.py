"""Test shot thở (sourcer/breath.py) — chọn máy thuần MO_TA_VAN_HANH_SHOT_THO §2c + §7 (3.0)."""

from __future__ import annotations

from pathlib import Path

from autoedit.library import db
from autoedit.project import (
    Beat,
    SearchQueries,
    ShotPick,
    StageRecord,
    create_project,
)
from autoedit.sourcer.breath import (
    _anchor_tags,
    _generic_tokens,
    _mood_set,
    _pieces,
    _score,
    _subject_tokens,
    pick_breath_shots,
)


def _beat(beat_id, start, end, breathing=0.0, chapter=1, mood="epic", size="wide",
          concept="c") -> Beat:
    return Beat(
        beat_id=beat_id, chapter=chapter, text=f"b{beat_id}.", start_word=0, end_word=1,
        start=start, end=end, timeline_start=start, timeline_end=end,
        energy="medium", mood=mood, visual_level="literal", visual_concept=concept,
        shot_size=size, search_queries=SearchQueries(specific=["q"]),
        breathing_after=breathing,
    )


def _cand(key, mood="", size="", dur=10.0, subject=""):
    return {"asset_key": key, "path": f"/x/{key}.mp4", "media_type": "video",
            "mood": mood, "shot_size": size, "duration": dur, "source": "local",
            "_tokens": _subject_tokens(subject)}


# ---------------- _mood_set: vocab đóng + synonyms, từ lạ fail-open ----------------
def test_mood_set_vocab_and_synonyms():
    assert _mood_set("epic, mysterious") == {"epic", "mysterious"}
    assert _mood_set("grand") == {"epic"}          # synonym dịch được
    assert _mood_set("xyz_la") == set()            # từ lạ -> rỗng, không nổ


def test_mood_set_compound_director_mood():
    """Regression DS5-083: director trả mood ghép 'awe_urgent_cautionary' — trước fix
    cả chuỗi không split được -> mood câm toàn video (note toàn 'mood —')."""
    assert _mood_set("awe_urgent_cautionary") == {"tense"}   # urgent -> tense
    assert _mood_set("tense_dramatic") == {"tense"}


# ---------------- _subject_tokens + _generic_tokens (3.0) ---------------------------
def test_subject_tokens_split_and_stopwords():
    got = _subject_tokens("tiger shark gliding above the sea grass", "sperm whale")
    assert {"tiger", "shark", "whale", "sperm", "grass"} <= got
    assert "the" not in got and "of" not in got     # stopword + từ <3 ký tự bỏ


def test_generic_tokens_df_demote_and_small_pool_guard():
    sets = ([{"underwater", f"u{i}"} for i in range(40)]
            + [{"shark", f"s{i}"} for i in range(3)]
            + [{f"x{i}"} for i in range(7)])
    generic = _generic_tokens(sets)                 # underwater 40/50 = 80% > 25%
    assert "underwater" in generic and "shark" not in generic
    assert _generic_tokens(sets[:10]) == set()      # pool nhỏ -> không demote


# ---------------- _score: CHỦ THỂ chủ đạo (3.0), khác cỡ cảnh, mood phụ trợ --------
def test_score_subject_continuity_wins():
    """Regression DS5-083 b045: clip liền trước = sói tuyết, máy cũ pick asteroid
    aerial (mood câm + bonus wide/aerial). Luật mới: cùng chủ thể THẮNG tuyệt đối."""
    anchor = _subject_tokens("gray wolves moving across a snowy yellowstone landscape")
    wolf = _score(_cand("a", size="medium", dur=4.0, subject="gray wolves running snowy ridge"),
                  3.0, anchor, set(), "wide", None, set())
    asteroid = _score(_cand("b", size="aerial", dur=11.0, subject="asteroid surface flyover"),
                      3.0, anchor, set(), "wide", None, set())
    assert wolf > asteroid


def test_score_generic_token_not_counted():
    anchor = {"underwater", "shark"}
    generic = {"underwater"}
    only_generic = _score(_cand("a", dur=2.0, subject="underwater view"),
                          3.0, anchor, set(), "", None, generic)
    real_subject = _score(_cand("b", dur=2.0, subject="shark hunting"),
                          3.0, anchor, set(), "", None, generic)
    assert only_generic == 0.0 and real_subject == 3.0


def test_score_mood_now_secondary():
    prev = {"epic"}
    hit = _score(_cand("a", mood="epic", size="wide", dur=10), 3.0, set(), prev, "wide", None, set())
    miss = _score(_cand("b", mood="sad", size="wide", dur=10), 3.0, set(), prev, "wide", None, set())
    assert hit > miss and hit - miss == 0.5         # phụ trợ, không còn chủ đạo 2.0


def test_score_prefers_different_shot_size_but_accepts_same():
    diff = _score(_cand("a", size="close_up", dur=10), 3.0, set(), set(), "wide", None, set())
    same = _score(_cand("b", size="wide", dur=10), 3.0, set(), set(), "wide", None, set())
    assert diff > same and same > 0    # trùng cỡ cảnh KHÔNG bị âm/loại (chấp nhận)


def test_score_duration_and_no_wide_bonus():
    du = _score(_cand("a", dur=5.0), 3.0, set(), set(), "", None, set())   # đủ dài
    ng = _score(_cand("b", dur=2.0), 3.0, set(), set(), "", None, set())   # ngắn -> slow-mo
    assert du - ng == 1.5
    # 3.0: BỎ bonus wide/aerial (proxy "đắt" cũ chính là nguồn nhặt sai chủ thể)
    assert _score(_cand("c", size="aerial", dur=5.0), 3.0, set(), set(), "", None, set()) == du


# ---------------- _anchor_tags: local tra db, stock rơi về nghĩa beat ---------------
def test_anchor_tags_local_and_fallback(tmp_path):
    conn = db.connect(tmp_path / "cache.db")
    db.upsert_asset(conn, db.AssetRecord(
        niche="deepsea", path="/x/p.mp4", category="", media_type="video", mtime=1.0,
        subject="orca pod hunting", description="", shot_size="close_up",
        mood="peaceful", has_people=False, tags=["orca", "deep sea"], duration=8.0,
    ))
    pick = ShotPick(beat_id=0, asset_path="assets/p.mp4", asset_key="local:/x/p.mp4")
    beat = _beat(0, 0.0, 2.0, mood="grand", size="medium",
                 concept="gray wolves moving across snowy yellowstone")
    tokens, moods, size = _anchor_tags(pick, conn, beat)
    assert tokens == {"orca", "pod", "hunting", "deep", "sea"}
    assert moods == {"peaceful"} and size == "close_up"
    # clip stock không tag -> visual_concept beat = proxy chủ thể + mood/size beat
    stock = ShotPick(beat_id=0, asset_path="assets/s.mp4", asset_key="pexels:9")
    tokens, moods, size = _anchor_tags(stock, conn, beat)
    assert tokens == {"gray", "wolves", "moving", "across", "snowy", "yellowstone"}
    assert moods == {"epic"} and size == "medium"   # grand -> epic


# ---------------- pick_breath_shots end-to-end (sqlite thật + copy file) ------------
def test_pick_breath_shots_end_to_end(tmp_path):
    conn = db.connect(tmp_path / "cache.db")
    lib = tmp_path / "lib"
    lib.mkdir()
    # 3 asset: best (cùng mood KHÁC cỡ) · cùng mood TRÙNG cỡ · khác mood
    assets = [
        ("best.mp4", "epic", "close_up"),
        ("same_size.mp4", "epic", "wide"),
        ("off_mood.mp4", "sad", "close_up"),
        ("prev.mp4", "epic", "wide"),      # clip beat đã dùng (prev)
    ]
    for name, mood, size in assets:
        f = lib / name
        f.write_bytes(b"fake")
        db.upsert_asset(conn, db.AssetRecord(
            niche="space", path=str(f), category="", media_type="video", mtime=1.0,
            subject=name, description="", shot_size=size, mood=mood,
            has_people=False, tags=[], duration=8.0,
        ))

    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.txt"; voice.write_text("x")  # chỉ cần file tồn tại
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.niche = "space"
    # b0 mang ô 3s (>=2.5 đạt ngưỡng) + b1 không; prev clip của b0 = prev.mp4 (local)
    p.beats = [_beat(0, 0.0, 4.0, breathing=3.0), _beat(1, 7.0, 9.0)]
    prev_key = f"local:{lib / 'prev.mp4'}"
    p.shots = [
        ShotPick(beat_id=0, status="ok", source="local",
                 asset_path="assets/prev.mp4", asset_key=prev_key),
        ShotPick(beat_id=1, status="ok", source="pexels",
                 asset_path="assets/b1.mp4", asset_key="pexels:1"),
    ]
    assets_dir = Path(p.project_dir) / "assets"
    assets_dir.mkdir()
    record = StageRecord()

    got = pick_breath_shots(p, conn, {prev_key, "pexels:1"}, assets_dir, record)
    assert len(got) == 1 and got[0].beat_id == 0
    # cùng mood epic + KHÁC cỡ wide->close_up thắng; prev bị P7 loại dù điểm cao
    assert got[0].asset_key == f"local:{lib / 'best.mp4'}"
    assert "epic" in got[0].note and "wide→close_up" in got[0].note
    assert got[0].dur == 2.5                       # footage = ô 3.0 - hold 0.5, k=1
    copied = Path(p.project_dir) / got[0].asset_path
    assert copied.is_file() and copied.name.startswith("b000_breath1_")


# ---------------- _pieces: k theo ngưỡng + seed định trước + guard clip dài ---------
def test_pieces_k_thresholds_and_determinism():
    from autoedit.cutter.pause import BREATH_POOLED as bdna

    assert _pieces(4.0, "p:0", 20.0, bdna) == [4.0]
    a = _pieces(7.5, "p:8", 20.0, bdna)
    assert a == _pieces(7.5, "p:8", 20.0, bdna)    # seed -> chạy lại y kết quả
    assert len(a) in (1, 2) and round(sum(a), 2) == 7.5
    b = _pieces(9.0, "p:63", 20.0, bdna)
    assert len(b) in (1, 2, 3) and round(sum(b), 2) == 9.0
    assert all(x >= bdna["min_piece"] for x in b)
    assert b == sorted(b, reverse=True)            # miếng đầu dài nhất


def test_pieces_guard_no_long_clip_bumps_k():
    """k=1 mà pool không clip nào >= footage-0.5 -> nâng k=2 (né slow-mo giãn xấu)."""
    from autoedit.cutter.pause import BREATH_POOLED

    durs = _pieces(7.5, "p:0", 6.0, BREATH_POOLED)   # clip dài nhất 6.0 < 7.0
    assert len(durs) == 2 and round(sum(durs), 2) == 7.5 and durs[0] > durs[1]
    # ô nông không bị guard đụng (k=1 là lựa chọn duy nhất)
    assert _pieces(4.0, "p:0", 2.0, BREATH_POOLED) == [4.0]


def test_pick_breath_shots_multi_piece_subject_anchor_fixed(tmp_path):
    """Ô sâu (footage 7.5, pool toàn clip 6s -> guard ép k=2): miếng 1 = cùng chủ thể
    orca thắng (không còn bonus aerial); miếng 2 neo chủ thể GIỮ NGUYÊN ô — c4 khớp tag
    của MIẾNG 1 (breaching splash) nhưng không khớp neo -> KHÔNG được chọn (trước 3.0
    chuỗi-nối sẽ trôi sang c4)."""
    conn = db.connect(tmp_path / "cache.db")
    lib = tmp_path / "lib"
    lib.mkdir()
    clips = [
        ("c1.mp4", "seal colony resting", "epic", "close_up", 6.0),
        ("c2.mp4", "orca breaching splash", "epic", "aerial", 6.0),
        ("c3.mp4", "kelp forest swaying", "sad", "medium", 6.0),
        ("c4.mp4", "breaching splash wave", "epic", "medium", 2.0),
        ("prev.mp4", "orca pod", "epic", "wide", 6.0),
    ]
    for name, subject, mood, size, dur in clips:
        f = lib / name
        f.write_bytes(b"fake")
        db.upsert_asset(conn, db.AssetRecord(
            niche="space", path=str(f), category="", media_type="video", mtime=1.0,
            subject=subject, description="", shot_size=size, mood=mood,
            has_people=False, tags=[], duration=dur,
        ))
    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.txt"; voice.write_text("x")
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.niche = "space"
    p.beats = [_beat(0, 0.0, 4.0, breathing=8.0), _beat(1, 12.0, 14.0)]
    prev_key = f"local:{lib / 'prev.mp4'}"
    p.shots = [ShotPick(beat_id=0, status="ok", source="local",
                        asset_path="assets/prev.mp4", asset_key=prev_key)]
    assets_dir = Path(p.project_dir) / "assets"
    assets_dir.mkdir()
    record = StageRecord()

    got = pick_breath_shots(p, conn, {prev_key}, assets_dir, record)
    assert [g.dur for g in got] == [4.35, 3.15]            # 7.5 chia 0.58/0.42
    assert got[0].asset_key.endswith("c2.mp4")             # chủ thể orca nối tiếp
    assert "orca" in got[0].note
    assert got[1].asset_key.endswith("c1.mp4")             # neo cố định -> c4 thua
    assert got[0].asset_key != got[1].asset_key            # P7 xuyên miếng
    names = [Path(g.asset_path).name for g in got]
    assert names[0].startswith("b000_breath1_") and names[1].startswith("b000_breath2_")


def _lib_pool(tmp_path, conn, n=6):
    lib = tmp_path / "lib"
    lib.mkdir()
    keys = []
    for i in range(n):
        f = lib / f"c{i}.mp4"
        f.write_bytes(b"fake")
        db.upsert_asset(conn, db.AssetRecord(
            niche="space", path=str(f), category="", media_type="video", mtime=1.0,
            subject=f"clip {i}", description="", shot_size="wide", mood="epic",
            has_people=False, tags=[], duration=8.0,
        ))
        keys.append(f"local:{f}")
    return keys


def test_pick_breath_shots_luoi_beat_bo_tran_3_mieng(tmp_path, monkeypatch):
    """NHIP-M1 + regression BỎ TRẦN (user chốt 2026-07-19): music-sync bật, ô 10,5s
    @109 BPM -> 4 miếng trên lưới beat (đường DNA cũ trần 3), beat_cut=True, note có
    [lưới beat]. Vùng footage = [timeline_end + HOLD, timeline_end + breathing]."""
    conn = db.connect(tmp_path / "cache.db")
    _lib_pool(tmp_path, conn)
    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.txt"; voice.write_text("x")
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.niche = "space"
    p.beats = [_beat(0, 0.0, 4.0, breathing=10.5), _beat(1, 14.5, 16.0)]
    (Path(p.project_dir) / "assets").mkdir()
    # beat nhạc trên timeline: vùng footage = [4.5, 14.5); beat đầu 4.6, period 0,55
    pts = [(round(4.6 + i * 0.55, 4), 0.3) for i in range(18)]
    monkeypatch.setattr("autoedit.sourcer.breath._beat_map", lambda _p: pts)

    got = pick_breath_shots(p, conn, set(), Path(p.project_dir) / "assets", StageRecord())
    assert [g.dur for g in got] == [2.85, 2.75, 2.75, 1.65]   # 4 miếng — trần 3 đã bỏ
    assert all(g.beat_cut for g in got)
    assert "[lưới beat]" in got[0].note and "1/4" in got[0].note
    assert len({g.asset_key for g in got}) == 4                # P7 xuyên miếng vẫn giữ


def test_pick_breath_shots_khong_music_plan_giu_duong_dna(tmp_path, monkeypatch):
    """Music-sync tắt (_beat_map rỗng) -> _pieces DNA như cũ, beat_cut=False."""
    conn = db.connect(tmp_path / "cache.db")
    _lib_pool(tmp_path, conn)
    script = tmp_path / "s.txt"; script.write_text("a b")
    voice = tmp_path / "v.txt"; voice.write_text("x")
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.niche = "space"
    p.beats = [_beat(0, 0.0, 4.0, breathing=10.5), _beat(1, 14.5, 16.0)]
    (Path(p.project_dir) / "assets").mkdir()
    monkeypatch.setattr("autoedit.sourcer.breath._beat_map", lambda _p: [])

    got = pick_breath_shots(p, conn, set(), Path(p.project_dir) / "assets", StageRecord())
    assert 1 <= len(got) <= 3 and not any(g.beat_cut for g in got)  # trần DNA giữ
    assert round(sum(g.dur for g in got), 2) == 10.0


def test_pick_breath_shots_empty_pool_fail_open(tmp_path):
    """Niche trống -> không record nào + warning; assemble sẽ tự về hành vi cũ."""
    conn = db.connect(tmp_path / "cache.db")
    script = tmp_path / "s.txt"; script.write_text("a")
    voice = tmp_path / "v.txt"; voice.write_text("x")
    p = create_project(script, voice, out_dir=tmp_path / "projects")
    p.niche = "space"
    p.beats = [_beat(0, 0.0, 4.0, breathing=3.0), _beat(1, 7.0, 9.0)]
    record = StageRecord()
    assert pick_breath_shots(p, conn, set(), tmp_path / "assets", record) == []
    assert any("pool local rỗng" in w for w in record.warnings)
