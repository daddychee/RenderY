"""Test M2 L2b sâu (F9) — direct-context (mảnh 1) + direct-ingest (mảnh 3), không API.

Cổng M2 (MO_TA_VAN_HANH_L2B_SAU.md §6): xuất đúng format từ đánh số; ingest CHẶN
draft hở coverage / thở sai chỗ; draft sạch → beats + timestamp khớp Y đường cũ.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_director import GOOD_OUTLINE, SCRIPT_12, WORDS, FakeClient, _draft, _drafts

from autoedit.director import live
from autoedit.director.runner import run_direct
from autoedit.project import Project, Stage, StageStatus, Word, create_project


def _mk_project(tmp_path, name, words):
    script = tmp_path / f"script_{name}.txt"
    script.write_text(SCRIPT_12, encoding="utf-8")
    voice = tmp_path / f"voice_{name}.mp3"
    voice.write_bytes(b"fake")
    p = create_project(script, voice, out_dir=tmp_path / name)
    p.transcript = words
    p.stages[Stage.ALIGN].status = StageStatus.DONE
    p.save()
    return p


@pytest.fixture
def project(tmp_path):
    return _mk_project(tmp_path, "projects", WORDS)


def _write_draft(project, chapters, outline=GOOD_OUTLINE) -> Path:
    """chapters: list[(chapter_id, list[BeatDraft])] -> director_draft.json."""
    data = {
        "outline": outline.model_dump(mode="json"),
        "chapters": [
            {"chapter_id": cid, "beats": [b.model_dump(mode="json") for b in beats]}
            for cid, beats in chapters
        ],
    }
    path = Path(project.project_dir) / live.DRAFT_FILE
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


# ===================== mảnh 1: direct-context =================================
def test_direct_context_numbered_words_and_constraint_table(project):
    ctx = live.build_direct_context(project)
    # transcript đánh số [i]word 0-based — đúng "hệ tọa độ" NT4
    assert "[0]w0" in ctx and "[11]w11" in ctx
    assert "0..11" in ctx and "6.0s thoại" in ctx
    # bảng ràng buộc in TỪ HẰNG SỐ code (đổi hằng là bảng đổi theo, không chép tay)
    for token in ("1.5–10s", "1.5–6s", "≥0.3s", "≤4 từ", "≤2 chart", "≤20 ký tự", "≤24", "≥0.7s"):
        assert token in ctx, f"bảng ràng buộc thiếu: {token}"
    assert live.DRAFT_FILE in ctx  # chỉ dẫn output cho phiên sống
    # C4/b1: đường sâu cũng mang luật mood-chạm-tone (cùng luật với beats_system direct cũ)
    assert "THÁI ĐỘ cả video" in ctx and "CHẠM tone" in ctx
    path = live.write_direct_context(project)
    assert path.name == live.CONTEXT_FILE and path.exists()


def test_direct_context_cong_cu_hinh_block(project):
    """Bug 3 bài đường sâu 0 info_card (DS5-083/DS3-084/SP1-017): direct_context chỉ in
    TRẦN card mà không dạy khi-nào-dùng → block CÔNG CỤ HÌNH phải có mặt MỌI video sâu
    (không phụ thuộc niche/kho — khác vocab/dna fail-open)."""
    ctx = live.build_direct_context(project)
    assert "CÔNG CỤ HÌNH" in ctx
    for token in ("info_card", "graphic_spec", "text_sequence",
                  "NÊN có ≥1 `info_card` HOẶC `graphic_spec`"):
        assert token in ctx, f"block công cụ hình thiếu: {token}"
    # block đứng TRƯỚC transcript (agent đọc luật trước khi gặp 27KB chữ)
    assert ctx.index("CÔNG CỤ HÌNH") < ctx.index("## TRANSCRIPT")


def test_direct_context_requires_align(project):
    project.stages[Stage.ALIGN].status = StageStatus.PENDING
    with pytest.raises(RuntimeError, match="align"):
        live.build_direct_context(project)


def test_direct_context_vocab_block_fail_open(project, tmp_path, monkeypatch):
    """C4: niche + kho có asset -> khối TỪ VỰNG KHO; không niche / kho rỗng / db lỗi ->
    KHÔNG khối, context y như cũ (fail-open)."""
    from autoedit.library import db as libdb

    monkeypatch.setenv("AUTOEDIT_LIBRARY_ROOT", str(tmp_path))  # cách ly dna.json thật của máy
    conn = libdb.connect(tmp_path / "cache.db")
    assert "TỪ VỰNG KHO" not in live.build_direct_context(project)                       # không niche
    assert "TỪ VỰNG KHO" not in live.build_direct_context(project, niche="space", conn=conn)  # kho rỗng
    libdb.upsert_asset(conn, libdb.AssetRecord(
        niche="space", path="/lib/g.mp4", category="nap", media_type="video", mtime=1.0,
        subject="spiral galaxy", description="deep space", shot_size="wide", mood="epic",
        scene_type="space", has_people=False, tags=["galaxy", "stars"]))
    ctx = live.build_direct_context(project, niche="space", conn=conn)
    assert "TỪ VỰNG KHO LOCAL (niche 'space'" in ctx
    assert "galaxy×1" in ctx and "search_queries.local" in ctx   # từ vựng + chỉ dẫn điền tier local
    assert ctx.index("TỪ VỰNG KHO") < ctx.index("## OUTPUT")     # khối đứng trước OUTPUT
    conn.close()
    assert "TỪ VỰNG KHO" not in live.build_direct_context(project, niche="space", conn=conn)  # db lỗi -> fail-open


def test_direct_context_boost_block_fail_open(project, tmp_path, monkeypatch):
    """BOOST M2 (VD3): inputs.boosts / audience_bias niche -> khối SỞ THÍCH KHÁN GIẢ
    (NÃO đan X vào concept — tầng mạnh nhất, bonus phễu không cứu nổi concept generic,
    bài học b018 REF); không khai gì -> KHÔNG khối (fail-open, context y như cũ)."""
    from autoedit.library.profile import NicheProfile

    monkeypatch.setenv("AUTOEDIT_LIBRARY_ROOT", str(tmp_path))  # cách ly YAML thật của máy
    assert "SỞ THÍCH KHÁN GIẢ" not in live.build_direct_context(project)
    # per-video: inputs.boosts (khai --boost tại direct-context)
    project.inputs.boosts = ["beautiful woman", "aurora@hook"]
    ctx = live.build_direct_context(project)
    assert "SỞ THÍCH KHÁN GIẢ" in ctx
    assert "'beautiful woman' (cả bài)" in ctx and "'aurora' (hook)" in ctx
    assert "NEO theo bối cảnh chương" in ctx          # luật đan-X-đúng-bối-cảnh
    assert ctx.index("SỞ THÍCH KHÁN GIẢ") < ctx.index("## OUTPUT")
    # per-niche: audience_bias YAML — không cần khai per-video, scope @ch<N> hiểu đúng
    project.inputs.boosts = []
    d = tmp_path / "lifein"
    d.mkdir()
    NicheProfile(niche="lifein", audience_bias=["elegant woman@ch2"]).save(d)
    ctx2 = live.build_direct_context(project, niche="lifein")
    assert "'elegant woman' (chương 2)" in ctx2


def test_direct_old_path_library_context_includes_boost(project, tmp_path, monkeypatch):
    """D2 cho BOOST: đường direct CŨ ăn cùng khối sở-thích với đường sâu qua
    library_context (boost_block gọi chung 1 hàm — không có nguồn luật thứ 2)."""
    monkeypatch.setenv("AUTOEDIT_LIBRARY_ROOT", str(tmp_path))
    project.inputs.boosts = ["beautiful woman"]
    block = live.boost_block(project, "")
    assert "SỞ THÍCH KHÁN GIẢ" in block and "'beautiful woman' (cả bài)" in block
    project.inputs.boosts = []
    assert live.boost_block(project, "") == ""


def test_direct_context_dna_block_fail_open(project, tmp_path, monkeypatch):
    """DNA-D1 Mảnh A (§6): có dna.json -> khối CHỮ KÝ PACING (4 dòng số + câu cấm hình
    thở §6b, đứng sau TỪ VỰNG KHO); không niche / không dna.json / JSON hỏng -> KHÔNG
    khối (fail-open 3 nấc)."""
    from autoedit.library import db as libdb

    monkeypatch.setenv("AUTOEDIT_LIBRARY_ROOT", str(tmp_path))
    assert "CHỮ KÝ PACING" not in live.build_direct_context(project)                 # không niche
    assert "CHỮ KÝ PACING" not in live.build_direct_context(project, niche="space")  # không dna.json
    niche_d = tmp_path / "space"
    niche_d.mkdir()
    (niche_d / "dna.json").write_text("hỏng{", encoding="utf-8")
    assert "CHỮ KÝ PACING" not in live.build_direct_context(project, niche="space")  # JSON hỏng
    (niche_d / "dna.json").write_text(json.dumps({
        "drafts": 3, "timeline_min": 82.6,
        "pacing": {"shots": 643, "cuts_per_min": 9.4,
                   "shot_len": {"median": 6.2, "std": 3.09},
                   "holds": {"share": 0.67, "median_s": 7.47},
                   "hook45": {"median": 4.8}},
    }), encoding="utf-8")
    conn = libdb.connect(tmp_path / "cache.db")
    libdb.upsert_asset(conn, libdb.AssetRecord(
        niche="space", path="/lib/g.mp4", category="nap", media_type="video", mtime=1.0,
        subject="spiral galaxy", description="deep space", shot_size="wide", mood="epic",
        scene_type="space", has_people=False, tags=["galaxy", "stars"]))
    ctx = live.build_direct_context(project, niche="space", conn=conn)
    assert "CHỮ KÝ PACING NICHE 'space'" in ctx and "3 draft" in ctx
    assert "9.4 cut/phút" in ctx and "[4.7; 18.8]" in ctx       # kèm ngưỡng validator Mảnh B sẽ soi
    assert "trung vị 6.2s" in ctx and "67% số shot" in ctx
    assert "4.8s — cắt NHANH hơn thân" in ctx                   # hook < thân -> chữ NHANH (in động)
    assert "KHÔNG chỉnh hình thở theo khối này" in ctx          # §6b: cấm rõ, không in số ô thở
    # thứ tự khối: TỪ VỰNG KHO -> CHỮ KÝ PACING -> OUTPUT
    assert ctx.index("TỪ VỰNG KHO") < ctx.index("CHỮ KÝ PACING") < ctx.index("## OUTPUT")


# ===================== luật "bán thuốc" (user chốt 2026-07-13) ================
def test_direct_context_has_ban_thuoc_block(project):
    """Đường sâu không ăn prompts.py — khối luật kể-chuyện-bằng-hình phải TỰ SINH
    trong direct_context.md (hồi quy: DS5-083 b014 Jenga vì đường sâu mù luật)."""
    ctx = live.build_direct_context(project)
    assert "bán thuốc" in ctx and "VOICE kể ẩn dụ — HÌNH kể câu chuyện" in ctx
    assert "Jenga" in ctx  # phản-ví-dụ thật giữ trong luật
    # đứng sau bảng ràng buộc, trước OUTPUT
    assert ctx.index("BẢNG RÀNG BUỘC CỨNG") < ctx.index("bán thuốc") < ctx.index("## OUTPUT")


def test_world_lock_block_deepsea_locks_world():
    """World-lock deepsea: khối luật giữ mọi hình dưới nước, cấm route entity cho
    người/y khoa, cấm central_subject mời nhà nghiên cứu đất liền vào (DS3-084 b17-24
    miệng người, b213-217 siêu âm)."""
    b = live.world_lock_block("deepsea")
    assert b  # có khối
    assert "DƯỚI NƯỚC" in b and "vanishing twin" in b  # phản-ví-dụ thật giữ trong luật
    assert "KHÔNG route `entity`" in b  # đóng cửa entity ảnh người
    assert "researchers who study them" in b  # cấm central_subject mời người
    assert "WRONG-vs-BLAND" in b  # nền-đúng-thế-giới thắng specific-sai-thế-giới


def test_world_lock_block_fail_open_non_locked_niche():
    """Fail-open: niche không khai trong WORLD_LOCK (space/travel) hay rỗng -> '' —
    không ép thế giới sai (filter-overload-guard: chỉ khóa niche đã khai)."""
    assert live.world_lock_block("space") == ""
    assert live.world_lock_block("travel") == ""
    assert live.world_lock_block("") == ""
    assert live.world_lock_block("  DeepSea  ") != ""  # chuẩn hóa hoa/thường/space


def test_direct_context_world_lock_injection(tmp_path):
    """deepsea chèn khối world-lock (sau bán-thuốc, trước OUTPUT); space không chèn."""
    p = _mk_project(tmp_path, "ds", WORDS)
    ctx = live.build_direct_context(p, niche="deepsea")
    assert "LUẬT GIỮ THẾ GIỚI HÌNH" in ctx
    # bán-thuốc VẪN còn (world-lock thêm chứ không thay)
    assert "bán thuốc" in ctx
    assert ctx.index("bán thuốc") < ctx.index("LUẬT GIỮ THẾ GIỚI HÌNH") < ctx.index("## OUTPUT")
    # niche không khóa: không chèn
    ctx_space = live.build_direct_context(p, niche="space")
    assert "LUẬT GIỮ THẾ GIỚI HÌNH" not in ctx_space
    assert "bán thuốc" in ctx_space  # bán-thuốc luôn có mọi niche


def test_ban_thuoc_warnings_flags_off_world_concept():
    """Hồi quy DS5-083: concept Jenga trong chương cá mập -> cảnh báo; concept dính
    chủ thể (kể cả số nhiều 'sharks' vs 'shark') -> im; route entity/graphic miễn."""
    from types import SimpleNamespace as NS

    outline = {
        "video_subject": "sharks and the ocean ecosystem",
        "chapters": [{"chapter_id": 1,
                      "central_subject": "sharks holding the ocean food web"}],
    }
    beats = [
        NS(beat_id=14, chapter=1, sourcing_route="stock",
           visual_concept="tall wooden jenga block tower standing intact on a table"),
        NS(beat_id=13, chapter=1, sourcing_route="stock",
           visual_concept="shark cruising above dense reef fish"),   # 'shark' khớp 'sharks'
        NS(beat_id=30, chapter=1, sourcing_route="entity",
           visual_concept="portrait of a famous chef"),              # entity miễn
        NS(beat_id=31, chapter=1, sourcing_route="graphic",
           visual_concept="bar chart of catch numbers"),             # graphic miễn
    ]
    warns = live.ban_thuoc_warnings(outline, beats)
    assert len(warns) == 1 and "b014" in warns[0] and "jenga" in warns[0]


def test_ban_thuoc_warnings_fail_open_without_anchor():
    """Không outline / chương không central_subject + video_subject rỗng -> im lặng
    (fail-open — không phải cửa loại, theo filter-overload-guard)."""
    from types import SimpleNamespace as NS

    beats = [NS(beat_id=1, chapter=1, sourcing_route="stock", visual_concept="jenga tower")]
    assert live.ban_thuoc_warnings({}, beats) == []
    assert live.ban_thuoc_warnings(
        {"video_subject": "", "chapters": [{"chapter_id": 1, "central_subject": ""}]},
        beats) == []


# ===================== mảnh 3: direct-ingest — CHẶN ===========================
def test_ingest_blocks_coverage_gap_and_writes_nothing(project):
    ch1 = [_draft(0, 2), _draft(4, 5).model_copy(update={"breathing_after_sec": 2.0})]
    ch2 = [_draft(6, 8), _draft(9, 11)]
    _write_draft(project, [(1, ch1), (2, ch2)])  # gap: thiếu từ 3
    _, errors = live.run_direct_ingest(project)
    assert any("gap" in e for e in errors)
    # KHÔNG ghi gì: beats rỗng, stage direct không DONE, không có beats.json
    saved = Project.load(project.project_dir)
    assert saved.beats == []
    direct = saved.stages.get(Stage.DIRECT)
    assert direct is None or direct.status != StageStatus.DONE
    assert not (Path(project.project_dir) / "beats.json").exists()


def test_ingest_blocks_chapter_mismatch(project):
    ch1 = list(_drafts((0, 2), (3, 5)).beats)
    ch2 = list(_drafts((6, 8), (9, 11)).beats)
    _write_draft(project, [(2, ch2), (1, ch1)])  # sai thứ tự outline
    _, errors = live.run_direct_ingest(project)
    assert any("khớp outline" in e for e in errors)


def test_ingest_schema_error_and_missing_file(project):
    path = Path(project.project_dir) / live.DRAFT_FILE
    path.write_text('{"outline": {}, "chapters": []}', encoding="utf-8")
    _, errors = live.run_direct_ingest(project)
    assert errors and all(e.startswith("schema") for e in errors)
    path.unlink()
    with pytest.raises(RuntimeError, match="direct_context"):
        live.run_direct_ingest(project)


def test_ingest_blocks_misplaced_breathing_with_hints(tmp_path):
    """Vá #2 (rà chồng chéo 2026-07-04): thở chỗ voice KHÔNG nghỉ = LỖI kèm gợi ý
    từ có nghỉ thật — thay vì enforce_breathing_pauses xóa âm thầm sau khi validator
    khác vừa ÉP hook phải có thở."""
    # 12 từ 0.5s; nghỉ thật DUY NHẤT 0.7s sau từ [5] (hết chương 1)
    words = [Word(text=f"w{i}", start=i * 0.5, end=i * 0.5 + 0.5) for i in range(6)]
    words += [Word(text=f"w{i}", start=3.7 + (i - 6) * 0.5, end=3.7 + (i - 6) * 0.5 + 0.5)
              for i in range(6, 12)]
    p = _mk_project(tmp_path, "pause_proj", words)

    bad_ch1 = [
        _draft(0, 2).model_copy(update={"breathing_after_sec": 2.0}),  # sau [2]: gap 0
        _draft(3, 5),
    ]
    ch2 = list(_drafts((6, 8), (9, 11)).beats)
    _write_draft(p, [(1, bad_ch1), (2, ch2)])
    _, errors = live.run_direct_ingest(p)
    assert any("does NOT pause" in e and "[2]w2" in e for e in errors)
    assert any("[5]w5" in e for e in errors)  # gợi ý đúng chỗ nghỉ thật gần đó

    # phiên "sửa theo gợi ý": chuyển thở về beat kết thúc từ [5] → pass, thở SỐNG SÓT
    good_ch1 = [_draft(0, 2), _draft(3, 5).model_copy(update={"breathing_after_sec": 2.0})]
    _write_draft(p, [(1, good_ch1), (2, ch2)])
    p, errors = live.run_direct_ingest(p)
    assert errors == []
    saved = Project.load(p.project_dir)
    hook_beats = [b for b in saved.beats if b.chapter == 1]
    assert any(b.breathing_after == 2.0 for b in hook_beats)  # hook giữ được thở


# ===================== mảnh 3: draft sạch khớp Y đường cũ =====================
def test_ingest_clean_draft_matches_old_direct_path(tmp_path):
    """Cùng outline + drafts: beats (timestamp, text, merge, thở...) phải Y HỆT
    đường run_direct cũ xử lý — pipeline sau không biết beats đến từ đường nào."""
    p_old = _mk_project(tmp_path, "old_path", WORDS)
    p_new = _mk_project(tmp_path, "new_path", WORDS)

    ch1, ch2 = _drafts((0, 2), (3, 5)), _drafts((6, 8), (9, 11))
    client = FakeClient([GOOD_OUTLINE, ch1, ch2])
    # transcript giả 6 giây -> sẽ bị gộp 1 chương; test so 2 ĐƯỜNG với cùng
    # outline 2 chương nên tắt gộp (xem NGUONG_MOT_CHUONG_GIAY).
    run_direct(p_old, client, gop_chuong_ngan=False)

    _write_draft(p_new, [(1, list(ch1.beats)), (2, list(ch2.beats))])
    p_new, errors = live.run_direct_ingest(p_new)
    assert errors == []  # WORDS không có chỗ nghỉ nào → placement check hạ về đường cũ

    s_old = Project.load(p_old.project_dir)
    s_new = Project.load(p_new.project_dir)
    assert s_new.stages[Stage.DIRECT].status == StageStatus.DONE
    assert [b.model_dump(mode="json") for b in s_new.beats] == [
        b.model_dump(mode="json") for b in s_old.beats
    ]
    assert s_new.outline == s_old.outline
    # beats.json review cũng được ghi như đường cũ; ingest không tốn API
    review = json.loads(
        (Path(p_new.project_dir) / "beats.json").read_text(encoding="utf-8")
    )
    assert len(review["beats"]) == len(s_new.beats)
    assert s_new.cost_log == []


# ===================== D2: direct cũ ăn khối kho (C4 + DNA) ===================
def test_run_direct_pass2_gets_vocab_and_dna_blocks(tmp_path, monkeypatch):
    """D2 (2026-07-09): đường run_direct cũ (fallback) phải chở CÙNG khối TỪ VỰNG KHO
    (C4) + CHỮ KÝ PACING (DNA Mảnh A) với đường sâu — CHỈ ở pass 2 (nơi quyết
    queries.local + độ dài beat/shot_count), pass outline KHÔNG. Niche lấy từ
    inputs.channel; không channel -> prompt y như cũ (fail-open)."""
    from autoedit.library import db as libdb

    monkeypatch.setenv("AUTOEDIT_LIBRARY_ROOT", str(tmp_path))  # cách ly dna.json thật
    real_connect = libdb.connect
    monkeypatch.setattr(  # cách ly cache.db thật của máy (vocab_block gọi db.connect())
        libdb, "connect", lambda db_path=None: real_connect(tmp_path / "cache.db"))

    # không channel -> không khối nào (fail-open, prompt y như trước D2)
    p0 = _mk_project(tmp_path, "no_channel", WORDS)
    c0 = FakeClient([GOOD_OUTLINE, _drafts((0, 2), (3, 5)), _drafts((6, 8), (9, 11))])
    run_direct(p0, c0)
    assert all("TỪ VỰNG KHO" not in s and "CHỮ KÝ PACING" not in s for s in c0.systems)

    # kho + dna.json giả trong tmp (cùng bộ số với test đường sâu ở trên)
    conn = libdb.connect()
    libdb.upsert_asset(conn, libdb.AssetRecord(
        niche="space", path="/lib/g.mp4", category="nap", media_type="video", mtime=1.0,
        subject="spiral galaxy", description="deep space", shot_size="wide", mood="epic",
        scene_type="space", has_people=False, tags=["galaxy", "stars"]))
    conn.close()
    niche_d = tmp_path / "space"
    niche_d.mkdir()
    (niche_d / "dna.json").write_text(json.dumps({
        "drafts": 3, "timeline_min": 82.6,
        "pacing": {"shots": 643, "cuts_per_min": 9.4,
                   "shot_len": {"median": 6.2, "std": 3.09},
                   "holds": {"share": 0.67, "median_s": 7.47},
                   "hook45": {"median": 4.8}},
    }), encoding="utf-8")

    p = _mk_project(tmp_path, "with_channel", WORDS)
    p.inputs.channel = "space"
    p.save()
    client = FakeClient([GOOD_OUTLINE, _drafts((0, 2), (3, 5)), _drafts((6, 8), (9, 11))])
    run_direct(p, client)
    # systems[0] = pass outline: KHÔNG khối; systems[1..] = pass 2: đủ CẢ 2 khối
    assert "TỪ VỰNG KHO" not in client.systems[0]
    assert "CHỮ KÝ PACING" not in client.systems[0]
    for s in client.systems[1:]:
        assert "TỪ VỰNG KHO LOCAL (niche 'space'" in s and "search_queries.local" in s
        assert "CHỮ KÝ PACING NICHE 'space'" in s and "9.4 cut/phút" in s
    assert client.systems[1] == client.systems[2]  # ổn định giữa các chương
