"""Test M4c — footage THẬT trong Δ (thay slug M2/M4b) + sửa tồn đọng M3 #1.

Nguồn LAI (user chốt 2026-07-21): clip folder editor dùng TRƯỚC (HOLD=cảnh rộng,
RUN=cận — e2 §5), thiếu thì KHO đắp bù theo prompt editor (NÃO dịch query lúc khai);
ô không có gì giữ slug (fail-open). Picks ghi theo INDEX ô — lưới hai tầng
source/assemble cùng `cov.insert_grids` nên index tự khớp.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autoedit.library import db
from autoedit.music import plan as mplan
from autoedit.packager import coverage as cov
from autoedit.project import (
    Beat, Inputs, InsertClip, InsertSpec, MusicPlanEntry, Project, SearchQueries,
    StageRecord, VoiceSegment,
)
from autoedit.sourcer import insert_fill as ifill


def _beat(beat_id: int, chapter: int, ts: float, te: float) -> Beat:
    return Beat(
        beat_id=beat_id, chapter=chapter, text=f"beat {beat_id}.", start_word=0,
        end_word=1, start=ts, end=te, timeline_start=ts, timeline_end=te,
        energy="medium", mood="m", visual_level="literal", visual_concept="c",
        shot_size="medium", search_queries=SearchQueries(specific=["q"]),
    )


def _seg(seg_id, ts, te, beat_ids, breathing=0.0, insert=0.0) -> VoiceSegment:
    return VoiceSegment(
        segment_id=seg_id, path=f"segments/seg_{seg_id:03d}.wav",
        source_start=ts, source_end=te, timeline_start=ts, timeline_end=te,
        beat_ids=beat_ids, breathing_after=breathing, insert_after=insert,
    )


def _project(beats, segs, inserts=(), niche="life-in") -> Project:
    return Project.model_construct(
        project_id="t", project_dir="/tmp/t", beats=list(beats), segments=list(segs),
        inserts=list(inserts), music_plan=[], niche=niche,
        inputs=Inputs.model_construct(script_text="life in oman is beautiful",
                                      ref_sources=[]),
        outline={"chapters": [{"chapter_id": 1, "mood": "m", "energy": "medium"},
                              {"chapter_id": 2, "mood": "m", "energy": "medium"}]},
    )


def _spec(**kw) -> InsertSpec:
    """Δ 20s sau beat 0, nhịp 3 bar 2,0s (madmom) -> lưới công thức unit 2,0s."""
    downs = [round(0.0 + 2.0 * i, 2) for i in range(40)]
    beats = [round(i * 2.0 / 3, 4) for i in range(120)]
    base = dict(after_beat=0, dur=20.0, music="/m/ed.mp3", music_beats=beats,
                music_beat_strength=[0.5] * len(beats), music_tier="A",
                music_downbeats=downs, music_meter=3, shuffle_seed=7)
    base.update(kw)
    return InsertSpec(**base)


def _delta_project(spec) -> Project:
    beats = [_beat(0, 1, 0.0, 10.0), _beat(1, 2, 34.0, 40.0)]
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0, insert=20.0),
            _seg(2, 34.0, 40.0, [1])]
    return _project(beats, segs, [spec])


# ===================== luật HOLD dùng chung ==================================
def test_hold_flags_shared_rule():
    # <4 ô: không HOLD (Δ ngắn chưa đủ pattern); ≥4 ô: dur ≥1,5× trung vị là HOLD
    assert cov.insert_hold_flags([2.0, 4.0, 2.0]) == [False, False, False]
    flags = cov.insert_hold_flags([2.0, 2.0, 2.0, 4.0, 2.0, 2.0, 4.0, 2.0])
    assert flags == [False, False, False, True, False, False, True, False]


def test_insert_grids_matches_assembler_seed():
    """Lưới từ helper == gọi tay insert_grid_cuts với seed crc32 (đúng logic assembler
    cũ) — 2 tầng source/assemble cùng 1 nguồn mốc, không trôi lệch."""
    import zlib

    spec = _spec(shuffle_seed=0)
    p = _delta_project(spec)
    grids = cov.insert_grids(p)
    assert 0 in grids
    seed = zlib.crc32(b"0:ed.mp3")
    manual = cov.insert_grid_cuts(14.0, 34.0, spec.music_beats,
                                  spec.music_beat_strength,
                                  downbeats=spec.music_downbeats, meter=3,
                                  seed=seed, pace="medium")
    assert grids[0] == manual


# ===================== dịch prompt -> query kho ==============================
def test_insert_footage_queries_validation():
    q = ifill.InsertFootageQueries(queries=["  Majestic  Nature ", "women", "women",
                                            "a b c d e f g", ""])
    # lowercase + gộp space + bỏ rỗng/quá dài + dedup giữ thứ tự
    assert q.queries == ["majestic nature", "women"]
    with pytest.raises(Exception):
        ifill.InsertFootageQueries(queries=["", "one two three four five six"])


def test_queries_from_prompt_uses_client():
    class FakeClient:
        def complete(self, system, user, output_model):
            assert "thiên nhiên" in user and "canyon" in system  # vocab lồng vào system
            return output_model(queries=["majestic nature", "desert women"]), None

    out = ifill.queries_from_prompt("thiên nhiên hùng vĩ và hình ảnh phụ nữ",
                                    "canyon, desert, oasis", FakeClient())
    assert out == ["majestic nature", "desert women"]


# ===================== ingest folder editor ==================================
def test_ingest_insert_footage_copies_and_tags(tmp_path):
    folder = tmp_path / "editor"
    folder.mkdir()
    (folder / "b_can.mp4").write_bytes(b"x")
    (folder / "a_rong.mp4").write_bytes(b"y")
    (folder / "note.txt").write_text("bỏ qua")  # không phải media
    proj = tmp_path / "proj"
    proj.mkdir()

    class FakeTagger:
        def tag(self, path, folder_context="", **kw):
            class T:
                shot_size = "wide" if "rong" in path.name else "close_up"
            return T()

    clips, warns = ifill.ingest_insert_footage(folder, proj, FakeTagger())
    assert [c.shot_size for c in clips] == ["wide", "close_up"]  # sort theo tên
    for c in clips:
        assert (proj / c.path).is_file()
        assert c.path.startswith("media/insert/")
        # prefix crc8 chống đè trùng tên (họ bug F6)
        assert (proj / c.path).name.split("_")[0] != ""
    assert warns == []


def test_ingest_tag_fail_open(tmp_path):
    folder = tmp_path / "e"
    folder.mkdir()
    (folder / "clip.mp4").write_bytes(b"x")
    proj = tmp_path / "p"
    proj.mkdir()

    class BoomTagger:
        def tag(self, *a, **kw):
            raise RuntimeError("glm chết")

    clips, warns = ifill.ingest_insert_footage(folder, proj, BoomTagger())
    assert clips[0].shot_size == "" and len(warns) == 1  # trung tính, vẫn dùng được
    clips2, w2 = ifill.ingest_insert_footage(folder, proj, None)  # không key GLM
    assert clips2[0].shot_size == "" and w2 == []


# ===================== pick: editor trước, HOLD=rộng RUN=cận =================
def test_pick_editor_clips_hold_gets_wide():
    spec = _spec(footage_clips=[
        InsertClip(path="media/insert/w1.mp4", shot_size="wide", duration=10.0),
        InsertClip(path="media/insert/c1.mp4", shot_size="close_up", duration=10.0),
        InsertClip(path="media/insert/c2.mp4", shot_size="close_up", duration=10.0),
    ])
    p = _delta_project(spec)
    record = StageRecord()
    ifill.pick_insert_footage(p, None, set(), record)
    picks = spec.footage_picks
    durs = ifill._cell_durs(p, spec)
    holds = cov.insert_hold_flags(durs)
    assert len(picks) == len(durs) >= 4
    # ô HOLD đầu tiên nhận clip RỘNG duy nhất; clip cận vào ô RUN
    first_hold = holds.index(True)
    assert picks[first_hold].path == "media/insert/w1.mp4"
    assert picks[first_hold].hold is True
    placed = [x for x in picks if x.path]
    assert len(placed) == 3 and all(x.source == "editor" for x in placed)
    # ô còn lại giữ slug (không prompt -> kho tắt) + warning nói rõ
    assert sum(1 for x in picks if not x.path) == len(durs) - 3
    assert any("kho đắp bù TẮT" in w for w in record.warnings)


def test_pick_library_fills_rest_and_logs_usage(tmp_path):
    conn = db.connect(tmp_path / "cache.db")
    for i in range(20):
        db.upsert_asset(conn, db.AssetRecord(
            niche="life-in", path=f"/lib/nat_{i:02d}.mp4", category="", media_type="video",
            mtime=1.0, subject="majestic nature canyon",
            description="sweeping desert canyon at dawn",
            shot_size="wide" if i % 2 == 0 else "close_up",
            mood="epic", has_people=False, tags=["nature", "canyon"], duration=12.0,
        ))
    spec = _spec(footage_clips=[
        InsertClip(path="media/insert/c1.mp4", shot_size="close_up", duration=10.0)],
        footage_queries=["majestic nature"])
    p = _delta_project(spec)
    record = StageRecord()
    used: set[str] = set()
    ifill.pick_insert_footage(p, conn, used, record, channel="CH1")
    picks = spec.footage_picks
    durs = ifill._cell_durs(p, spec)
    holds = cov.insert_hold_flags(durs)
    assert all(x.path for x in picks)                      # kho đắp kín, 0 slug
    for x, h in zip(picks, holds):
        if h and x.source == "library":
            assert x.shot_size == "wide"                   # HOLD kho cũng cảnh rộng
    lib = [x for x in picks if x.source == "library"]
    assert lib and all(x.asset_key.startswith("local:") for x in lib)
    assert all(x.asset_key in used for x in lib)           # P7: đã đánh dấu dùng
    assert len({x.path for x in picks}) == len(picks)      # không lặp clip trong Δ
    n = conn.execute("SELECT COUNT(*) AS n FROM asset_usage").fetchone()["n"]
    assert n == len(lib)                                   # usage CHỈ đếm kho


def test_pick_fail_open_without_timeline():
    # Khai Δ khi CHƯA cut lần nào (không có segment) -> không mép -> giữ slug + warning
    spec = _spec(footage_clips=[InsertClip(path="media/insert/x.mp4", duration=5.0)])
    p = _project([_beat(0, 1, 0.0, 10.0)], [], [spec])
    record = StageRecord()
    ifill.pick_insert_footage(p, None, set(), record)
    assert spec.footage_picks == []
    assert any("chưa có timeline" in w for w in record.warnings)


def test_no_grid_tier_c_single_cell():
    # Bài tier C (không lưới): Δ = 1 ô phủ trọn — 1 clip editor đắp cả Δ (y M3)
    spec = _spec(music_tier="C", music_downbeats=[], music_beats=[],
                 footage_clips=[InsertClip(path="media/insert/x.mp4", duration=30.0)])
    p = _delta_project(spec)
    ifill.pick_insert_footage(p, None, set(), StageRecord())
    assert len(spec.footage_picks) == 1
    assert spec.footage_picks[0].path == "media/insert/x.mp4"


# ===================== M4d: cổng LOCATION cho kho đắp bù =====================
def test_foreign_location_blocks_wrong_country():
    script = "life in oman is beautiful"
    blob = "lifeinomanisbeautiful"
    # tên nước trong TÊN VIDEO NGUỒN (đúng ca V13: Walking-Tour-Vietnam trong bài Oman)
    row = {"source_video": r"F:\x\K-Walking-Tour-Vietnam-O.mp4", "subject": "street"}
    assert ifill.foreign_location(row, blob) == "vietnam"
    assert ifill.foreign_location(
        {"source_video": r"F:\x\Bosnia-Is-Like-This.mp4"}, blob) == "bosnia"
    # nước CÓ trong script -> qua (video Oman dùng mọi cảnh Oman)
    assert ifill.foreign_location(
        {"source_video": r"F:\x\Life-in-Oman-on-Masirah.mp4"}, blob) == ""
    # không nhãn nước -> qua (fail-open, không đẻ cửa loại cho clip không nhãn)
    assert ifill.foreign_location({"subject": "camel in desert"}, blob) == ""
    # chống khớp oan: "oman"⊄"romance", "viet nam"⊄"soviet name" (token, không substring)
    assert ifill.foreign_location({"subject": "romance movie set"}, "xyz") == ""
    assert ifill.foreign_location({"subject": "soviet name history"}, "xyz") == ""
    assert ifill.foreign_location({"subject": "viet nam street"}, "xyz") == "viet nam"


def test_library_pool_applies_location_gate(tmp_path):
    conn = db.connect(tmp_path / "cache.db")
    for name, src in [("ok.mp4", r"F:\v\Life-in-Oman-Documentary.mp4"),
                      ("bad.mp4", r"F:\v\Djibouti-Ep-1-Horn-of-Africa.mp4")]:
        db.upsert_asset(conn, db.AssetRecord(
            niche="life-in", path=f"/lib/{name}", category="", media_type="video",
            mtime=1.0, subject="majestic nature", description="", shot_size="wide",
            mood="epic", has_people=False, tags=["nature"], duration=12.0,
            source_video=src))
    pool, blocked = ifill._library_pool(conn, "life-in", ["majestic nature"], set(),
                                        script_blob="lifeinoman")
    assert [Path(r["path"]).name for r in pool] == ["ok.mp4"]
    assert blocked and "djibouti" in blocked[0]


# ===================== M4d: HINH THO trong folder --ref ======================
_REF = "f:\\life in\\video mau\\rd89\\"


def _ht_db(tmp_path):
    from pathlib import PurePath  # noqa: F401 — path chuỗi thuần, không đụng đĩa
    conn = db.connect(tmp_path / "cache.db")
    rows = [
        # (path kho, source_video, shot_size, scene_index)
        ("/lib/ht1a.mp4", _REF + "HINH THO\\chapter 1\\OMAN-DOC.mp4", "wide", 0),
        ("/lib/ht1b.mp4", _REF + "HINH THO\\chapter 1\\OMAN-DOC.mp4", "close_up", 1),
        ("/lib/ht1c.mp4", _REF + "HINH THO\\chapter 1\\OMAN-DOC.mp4", "close_up", 2),
        ("/lib/ht5.mp4", _REF + "HINH THO\\chapter 5\\OTHER.mp4", "wide", 0),
        ("/lib/mh.mp4", _REF + "HINH THO\\Mini Hook\\HOOK.mp4", "wide", 0),
        ("/lib/chung.mp4", _REF + "HINH THO\\extra.mp4", "medium", 0),
        ("/lib/ref_ch1.mp4", _REF + "CHAPTER 1\\SRC.mp4", "wide", 0),
    ]
    for path, src, size, idx in rows:
        db.upsert_asset(conn, db.AssetRecord(
            niche="life-in", path=path, category="", media_type="video", mtime=1.0,
            subject="oman scenery", description="", shot_size=size, mood="epic",
            has_people=False, tags=["oman"], duration=12.0, source_video=src,
            scene_index=idx))
    return conn


def test_ref_hinhtho_scan_parses_tree(tmp_path):
    from autoedit.sourcer.local import ref_chapter_scan, ref_hinhtho_scan
    conn = _ht_db(tmp_path)
    scan = ref_hinhtho_scan(conn, "life-in", (_REF,))
    assert scan["by_chapter"].keys() == {1, 5}
    assert scan["counts"] == {1: 3, 5: 1, "minihook": 1, "chung": 1}
    # file ở GỐC HINH THO = chung (đếm được) nhưng không có prefix con — pool match
    # bằng root trừ chương/minihook, không cần prefix riêng
    assert scan["minihook"]
    # ref_chapter_scan: cảnh HINH THO đếm RIÊNG, không phồng số "chung" của REF chèn
    ch_map, counts = ref_chapter_scan(conn, "life-in", (_REF,))
    assert 1 in ch_map and counts["hinh_tho"] == 6 and counts.get("chung") is None


def test_ref_excludes_covers_hinhtho():
    from autoedit.sourcer.viral import ViralLedger
    led = ViralLedger(ref_sources=[_REF])
    led.ref_chapter_prefixes = {1: (_REF + "chapter 1\\",)}
    led.ref_hinhtho_prefixes = (_REF + "hinh tho\\",)
    # beat chương 1: KHÔNG loại chapter 1, LUÔN loại HINH THO (dành riêng Δ/mini-hook)
    assert led.ref_excludes(1) == (_REF + "hinh tho\\",)
    assert set(led.ref_excludes(2)) == {_REF + "chapter 1\\", _REF + "hinh tho\\"}


def test_pick_hinhtho_before_prompt_kho(tmp_path):
    """Ưu tiên ①editor ②HINH THO đúng chương+chung ③kho prompt: Δ chương 1 ăn 3 clip
    ch1 + 1 chung; KHÔNG đụng ch5/Mini Hook; ô còn lại mới tới kho theo query."""
    conn = _ht_db(tmp_path)
    for i in range(20):
        db.upsert_asset(conn, db.AssetRecord(
            niche="life-in", path=f"/lib/gen_{i:02d}.mp4", category="",
            media_type="video", mtime=1.0, subject="majestic nature canyon",
            description="", shot_size="wide" if i % 2 == 0 else "close_up",
            mood="epic", has_people=False, tags=["nature"], duration=12.0))
    spec = _spec(footage_queries=["majestic nature"])
    p = _delta_project(spec)          # Δ sau beat 0 (chương 1)
    p.inputs.ref_sources = [_REF]
    record = StageRecord()
    used: set[str] = set()
    ifill.pick_insert_footage(p, conn, used, record)
    picks = spec.footage_picks
    ht = [x for x in picks if x.source == "hinh_tho"]
    lib = [x for x in picks if x.source == "library"]
    assert {x.path for x in ht} == {"/lib/ht1a.mp4", "/lib/ht1b.mp4",
                                    "/lib/ht1c.mp4", "/lib/chung.mp4"}
    assert all(x.path not in ("/lib/ht5.mp4", "/lib/mh.mp4") for x in picks)
    assert len(lib) == len(picks) - 4 and len(lib) > 0   # kho chỉ đắp phần còn lại
    assert any("HINH THO 4" in w for w in record.warnings)


def test_prompt_kho_khong_vot_lai_vung_dat_cho(tmp_path):
    """Hồi quy V14 lần đầu: Δ ch2 khai prompt — search chữ match cả cảnh HINH THO
    chapter 1/5/Mini Hook (subject 'oman scenery') nhưng vùng ĐẶT CHỖ cho chỗ khác
    phải bị loại khỏi pool ③; chỉ 'chung' được dùng (qua tầng ②)."""
    conn = _ht_db(tmp_path)
    beats = [_beat(0, 1, 0.0, 10.0), _beat(1, 2, 34.0, 40.0), _beat(2, 2, 44.0, 50.0)]
    segs = [_seg(1, 0.0, 10.0, [0], breathing=4.0),
            _seg(2, 34.0, 40.0, [1], insert=20.0), _seg(3, 44.0, 50.0, [2])]
    spec = _spec(after_beat=1, footage_queries=["oman scenery"])
    p = _project(beats, segs, [spec])
    p.inputs.ref_sources = [_REF]
    ifill.pick_insert_footage(p, conn, set(), StageRecord())
    paths = {x.path for x in spec.footage_picks if x.path}
    assert "/lib/chung.mp4" in paths                       # chung: mọi Δ dùng được
    assert not paths & {"/lib/ht1a.mp4", "/lib/ht1b.mp4", "/lib/ht1c.mp4",
                        "/lib/ht5.mp4", "/lib/mh.mp4"}     # vùng đặt chỗ không rò qua ③


def test_pick_hinhtho_even_scene_first(tmp_path):
    """Chống kề bản quyền: trong pool HINH THO cùng nguồn, scene CHẴN xếp trước LẺ."""
    from autoedit.sourcer.local import ref_hinhtho_scan
    conn = _ht_db(tmp_path)
    scan = ref_hinhtho_scan(conn, "life-in", (_REF,))
    pool = ifill._hinhtho_pool(conn, "life-in", scan, 1, set())
    ch1 = [r for r in pool if "chapter 1" in str(r["source_video"]).lower()]
    assert [r["scene_index"] for r in ch1] == [0, 2, 1]   # chẵn (0,2) trước lẻ (1)


# ===================== schema cũ load được (tương thích ngược) ===============
def test_old_insertspec_schema_loads():
    old = {"after_beat": 3, "dur": 20.0, "music": "/m/x.mp3"}  # M4b: chưa có field M4c
    spec = InsertSpec(**old)
    assert spec.footage_clips == [] and spec.footage_picks == []
    assert spec.footage_prompt == "" and spec.footage_queries == []


# ===================== tồn đọng M3 #1: accent/beat biết span Δ ===============
def _accent_project(with_insert_music: bool):
    spec = _spec() if with_insert_music else _spec(music="")
    p = _delta_project(spec)
    p.music_plan = [MusicPlanEntry(chapter_id=1, file="a.mp3", start_offset=0.0,
                                   beat_tier="B"),
                    MusicPlanEntry(chapter_id=2, file="b.mp3", start_offset=0.0,
                                   beat_tier="B")]
    return p


def test_timeline_accents_stop_at_insert_span():
    """Chương mang Δ-nhạc: accent bài KẾ HOẠCH dừng ở mép Δ (bài đã bị thay từ đó
    tới hết chương — phát tiếp mốc của nó là snap theo nhạc KHÔNG còn kêu)."""
    # 20.5/30.7 chọn LỆCH lưới downbeat editor (14+chẵn) để phân biệt được nguồn mốc
    rows = [{"file": "a.mp3", "beat_tier": "B", "accents": [1.0, 20.5, 30.7]},
            {"file": "b.mp3", "beat_tier": "B", "accents": []}]
    p = _accent_project(with_insert_music=True)
    out = mplan.timeline_accents(p, rows)
    assert 1.0 in out
    assert all(not (14.0 <= t < 34.0) or t in
               [round(14.0 + d, 4) for d in p.inserts[0].music_downbeats]
               for t in out)
    # accent bài cũ tại 20,5/30,7 (rơi trong span Δ) phải BIẾN MẤT
    assert 20.5 not in out and 30.7 not in out
    # downbeat bài editor xuất hiện trong span Δ (14 + 0, 2, 4, ...)
    assert 14.0 in out and 16.0 in out


def test_timeline_accents_regression_without_insert_music():
    """Hồi quy bằng 0: Δ KHÔNG nhạc editor -> kết quả y đường cũ (span không chẻ)."""
    rows = [{"file": "a.mp3", "beat_tier": "B", "accents": [1.0, 20.0, 30.0]},
            {"file": "b.mp3", "beat_tier": "B", "accents": []}]
    p = _accent_project(with_insert_music=False)
    # ch1 [0, 34): P=0 -> 1.0, 20.0, 30.0 đều giữ (34.0 = timeline_start ch2)
    assert mplan.timeline_accents(p, rows) == [1.0, 20.0, 30.0]


def test_timeline_beats_insert_span_uses_editor_measurements():
    # 20.5 chọn LỆCH lưới beat editor (14 + i·2/3) để phân biệt được nguồn mốc
    rows = [{"file": "a.mp3", "beat_tier": "B",
             "beat_times": [1.0, 20.5], "beat_strength": [0.9, 0.8]},
            {"file": "b.mp3", "beat_tier": "B", "beat_times": [], "beat_strength": []}]
    p = _accent_project(with_insert_music=True)
    out = mplan.timeline_beats(p, rows)
    assert (1.0, 0.9) in out
    assert all(t != 20.5 for t, _ in out)          # beat bài cũ trong span Δ biến mất
    # beat bài editor: 14 + i*(2/3), strength 0.5 đo lúc khai
    assert (round(14.0 + 2.0 / 3, 4), 0.5) in out
