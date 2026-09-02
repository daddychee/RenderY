"""Test Stage 4 Source (M5) — fake clients, không gọi mạng."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from autoedit.library import db
from autoedit.project import (
    Beat,
    Project,
    SearchQueries,
    Stage,
    StageStatus,
    Word,
    create_project,
)
from autoedit.sourcer import usage
from autoedit.sourcer.local import find_local_candidates
from autoedit.sourcer.runner import run_source


@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "cache.db")


def _beat(beat_id, route="stock", **kw) -> Beat:
    return Beat(
        beat_id=beat_id, chapter=1, text=f"b{beat_id}", start_word=0, end_word=1,
        start=float(beat_id), end=float(beat_id) + 2.0, energy="medium", mood="m",
        sourcing_route=route, visual_level="literal",
        visual_concept=kw.get("concept", "man walking street"), shot_size="medium",
        search_queries=SearchQueries(
            specific=kw.get("specific", ["man walking street"]),
            broad=["city walk"], thematic=kw.get("thematic", ["urban life"]),
        ),
        entity_queries=kw.get("entity_queries", []),
    )


class FakeStock:
    """Pexels giả: trả ứng viên định sẵn, 'tải' = ghi file giả."""

    def __init__(self, candidates: list[dict] | None = None):
        self.candidates = candidates if candidates is not None else [
            {"asset_key": f"pexels:{i}", "url": f"http://x/{i}.mp4", "media_type": "video",
             "duration": 10.0, "description": f"clip {i}", "source": "pexels"}
            for i in range(5)
        ]
        self.downloads: list[str] = []

    def search_tiered(self, queries) -> list[dict]:
        return list(self.candidates)

    def download(self, candidate, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"fake-video")
        self.downloads.append(candidate["asset_key"])
        return dest


class FakeEntity:
    def __init__(self, results=None):
        self.results = results or [
            {"asset_key": "entity:abc123", "url": "http://news/trump.jpg",
             "media_type": "image", "description": "Trump announcement",
             "origin": "reuters.com", "preferred": True, "source": "entity"},
        ]

    def search_images(self, query, n=5):
        return list(self.results)

    def download(self, candidate, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20000)  # JPEG magic = ảnh hợp lệ
        return dest


def test_pexels_rate_limit_degrades_not_crash(monkeypatch):
    """429 kéo dài -> _cached_get trả rỗng + đánh dấu rate_limited, KHÔNG raise (video dài
    không bị 1 lần rate-limit giết cả stage source)."""
    from autoedit.sourcer import pexels

    monkeypatch.setattr(pexels.time, "sleep", lambda *_: None)  # khỏi chờ backoff

    class Resp429:
        status_code = 429
        def raise_for_status(self):
            raise AssertionError("không được raise khi 429 — phải xử lý mềm")

    monkeypatch.setattr(pexels.requests, "get", lambda *a, **k: Resp429())
    client = pexels.PexelsClient("fake-key", conn=None)
    assert client._cached_get("any query") == {}      # rỗng, không raise
    assert client.rate_limited is True
    # đã rate-limit -> query sau bỏ qua mạng luôn (trả rỗng tức thì)
    monkeypatch.setattr(pexels.requests, "get",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("không được gọi mạng nữa")))
    assert client._cached_get("another") == {}
    assert client.search_tiered(SearchQueries(specific=["x"], broad=[], thematic=[])) == []


def test_looks_like_image_rejects_html(tmp_path):
    """Magic bytes: ảnh thật -> True; trang HTML lưu nhầm .jpg -> False (bug 19/06)."""
    from autoedit.sourcer.entity import looks_like_image

    jpg = tmp_path / "real.jpg"
    jpg.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 50)        # JPEG magic
    png = tmp_path / "real.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)       # PNG magic
    html = tmp_path / "fake.jpg"
    html.write_bytes(b"<!DOCTYPE html><html>error page</html>" * 500)  # HTML nặng >10KB
    tiny = tmp_path / "tiny.jpg"
    tiny.write_bytes(b"xx")

    assert looks_like_image(jpg) is True
    assert looks_like_image(png) is True
    assert looks_like_image(html) is False     # chặn HTML dù nặng
    assert looks_like_image(tiny) is False
    assert looks_like_image(tmp_path / "khong-ton-tai.jpg") is False


def test_collect_pexels_keys_parses_many_forms():
    from autoedit.sourcer.pexels import collect_pexels_keys

    env = {
        "PEXELS_API_KEY": "k1, k2  k3",   # nhiều key ngăn phẩy/khoảng trắng
        "PEXELS_API_KEY_2": "k4",
        "PEXELS_API_KEY_3": "k2",          # trùng -> bỏ
    }
    assert collect_pexels_keys(env) == ["k1", "k2", "k3", "k4"]
    assert collect_pexels_keys({"PEXELS_API_KEY": "solo"}) == ["solo"]
    assert collect_pexels_keys({}) == []


def test_pexels_rotates_to_next_key_on_429(monkeypatch):
    """Key đầu 429 -> xoay sang key 2 (còn hạn mức) -> lấy được kết quả, KHÔNG rate_limited."""
    from autoedit.sourcer import pexels

    monkeypatch.setattr(pexels.time, "sleep", lambda *_: None)

    class Resp:
        def __init__(self, code, payload=None):
            self.status_code = code
            self._payload = payload or {}
        def json(self):
            return self._payload
        def raise_for_status(self):
            raise AssertionError("không nên gọi raise_for_status")

    def fake_get(url, headers, params, timeout):
        # key đầu (k1) hết hạn mức; key 2 (k2) còn
        if headers["Authorization"] == "k1":
            return Resp(429)
        return Resp(200, {"videos": []})

    monkeypatch.setattr(pexels.requests, "get", fake_get)
    client = pexels.PexelsClient(["k1", "k2"], conn=None)
    assert client._cached_get("q") == {"videos": []}
    assert client.rate_limited is False
    assert 0 in client.exhausted and client.key_idx == 1   # đã xoay sang k2


@pytest.fixture
def project(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("a b", encoding="utf-8")
    voice = tmp_path / "voice.mp3"
    voice.write_bytes(b"fake")
    p = create_project(script, voice, out_dir=tmp_path / "projects", channel="kenh-test")
    p.transcript = [Word(text="a", start=0.0, end=1.0)]
    for st in (Stage.ALIGN, Stage.DIRECT, Stage.CUT):
        p.stages[st].status = StageStatus.DONE
    return p


def _run(p, conn, tmp_path, stock=None, entity=None, niche="", brain=None, gate=None):
    return run_source(p, conn, stock or FakeStock(), entity, niche=niche,
                      library_root=tmp_path / "library", brain=brain, gate=gate)


# ----------------------------- route stock -----------------------------------
def test_stock_route_downloads_and_records(project, conn, tmp_path):
    project.beats = [_beat(0), _beat(1)]
    project.save()
    stock = FakeStock()
    _run(project, conn, tmp_path, stock)

    saved = Project.load(project.project_dir)
    assert saved.stages[Stage.SOURCE].status == StageStatus.DONE
    assert saved.stages[Stage.RANK].status == StageStatus.DONE
    s0, s1 = saved.shots
    assert s0.status == "ok" and s0.source == "pexels"
    assert (Path(saved.project_dir) / s0.asset_path).is_file()
    # không lặp clip trong cùng video (luật cứng P7)
    assert s0.asset_key != s1.asset_key
    assert len(s0.alternates) == 3
    # C4 (lật có chủ đích hành vi cũ "không --niche -> không ghi"): fallback channel —
    # vá bug niche rơi làm local/signature/shot thở tắt im lặng khi skill gọi source trần.
    assert saved.niche == "kenh-test"
    assert any("fallback từ channel" in w for w in saved.stages[Stage.SOURCE].warnings)


def test_stock_route_soft_penalty_prefers_unused(project, conn, tmp_path):
    """P7: asset đã dùng cho kênh này tụt hạng, KHÔNG bị cấm."""
    usage.log_usage(conn, "kenh-test", "pexels:0", "video-cu")
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].asset_key == "pexels:1"  # pexels:0 bị phạt mềm xuống dưới


def test_stock_route_local_library_wins(project, conn, tmp_path):
    """P6: footage local đã người duyệt đứng trước stock."""
    lib_file = tmp_path / "lib" / "walk.mp4"
    lib_file.parent.mkdir()
    lib_file.write_bytes(b"local-video")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(lib_file), category="signature", media_type="video",
        mtime=1.0, subject="man walking street", description="local man walking",
        shot_size="medium", mood="neutral", has_people=True, tags=["man", "walking"],
    ))
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, niche="n1")
    saved = Project.load(project.project_dir)
    assert saved.shots[0].source == "local"
    assert (Path(saved.project_dir) / saved.shots[0].asset_path).read_bytes() == b"local-video"
    assert saved.niche == "n1"          # DNA d1: assemble đọc dna.json theo đây


def test_local_pick_carries_source_channel(project, conn, tmp_path):
    """VD4 ghi công: kênh nguồn chảy DB -> ứng viên (_row_to_candidate) -> ShotPick ->
    project.json — assemble --credit đọc từ đây, KHÔNG mở sổ (NT1)."""
    lib_file = tmp_path / "lib" / "walk.mp4"
    lib_file.parent.mkdir()
    lib_file.write_bytes(b"local-video")
    rec = db.AssetRecord(
        niche="n1", path=str(lib_file), category="signature", media_type="video",
        mtime=1.0, subject="man walking street", description="local man walking",
        shot_size="medium", mood="neutral", has_people=True, tags=["man", "walking"])
    rec.source_channel = "Kurzgesagt"
    db.upsert_asset(conn, rec)
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, niche="n1")
    saved = Project.load(project.project_dir)
    assert saved.shots[0].source == "local"
    assert saved.shots[0].source_channel == "Kurzgesagt"


def test_stock_route_exhausted_needs_human(project, conn, tmp_path):
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, stock=FakeStock(candidates=[]))
    saved = Project.load(project.project_dir)
    assert saved.shots[0].status == "needs_human"
    assert any("cần người chọn" in w for w in saved.stages[Stage.SOURCE].warnings)


# ----------------------------- SÀN NICHE (bug DS3-084) ------------------------
def test_floor_fills_needs_human_from_kho(project, conn, tmp_path):
    """Bug DS3-084 (40 beat needs_human/1 bài, user chốt tool tự điền hết): phễu +
    stock trắng tay -> sàn niche tự đắp từ kho own. Query gốc 'man walking street'
    không khớp asset nào; nấc 2 rút về đuôi danh từ 'street' thì khớp."""
    f = tmp_path / "lib" / "street.mp4"
    f.parent.mkdir()
    f.write_bytes(b"floor-video")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="rainy street night", description="empty rainy street",
        shot_size="wide", mood="moody", has_people=False, tags=["street", "rain"],
    ))
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, stock=FakeStock(candidates=[]), niche="n1")
    saved = Project.load(project.project_dir)
    s = saved.shots[0]
    assert s.status == "ok" and s.source == "floor"
    assert (Path(saved.project_dir) / s.asset_path).read_bytes() == b"floor-video"
    assert "SÀN NICHE nấc 2" in s.note
    warns = saved.stages[Stage.SOURCE].warnings
    assert any("SÀN NICHE tự đắp 1 beat" in w for w in warns)
    assert not any("cần người chọn" in w for w in warns)  # hết needs_human


def test_floor_world_lock_niche_skips_people(project, conn, tmp_path):
    """Niche trong WORLD_LOCK (deepsea): sàn GẠT HẲN cảnh có người (WRONG-vs-BLAND
    — nền niche không người), kể cả khi cảnh có người đứng trước theo thứ tự kho."""
    quiet = tmp_path / "lib" / "deep.mp4"
    quiet.parent.mkdir()
    quiet.write_bytes(b"no-people")
    people = tmp_path / "lib" / "diver.mp4"
    people.write_bytes(b"people")
    # upsert people SAU -> indexed_at mới hơn -> đứng ĐẦU kết quả tìm kho
    db.upsert_asset(conn, db.AssetRecord(
        niche="deepsea", path=str(quiet), category="nap", media_type="video",
        mtime=1.0, subject="shark in dark water", description="d",
        shot_size="wide", mood="dark", has_people=False, tags=["shark"],
    ))
    db.upsert_asset(conn, db.AssetRecord(
        niche="deepsea", path=str(people), category="nap", media_type="video",
        mtime=1.0, subject="diver with shark", description="d",
        shot_size="wide", mood="dark", has_people=True, tags=["shark", "diver"],
    ))
    project.beats = [_beat(0, specific=["sand tiger shark"])]
    project.save()
    _run(project, conn, tmp_path, stock=FakeStock(candidates=[]), niche="deepsea")
    saved = Project.load(project.project_dir)
    s = saved.shots[0]
    assert s.status == "ok" and s.source == "floor"
    assert (Path(saved.project_dir) / s.asset_path).read_bytes() == b"no-people"


def test_floor_kho_empty_keeps_needs_human(project, conn, tmp_path):
    """Kho niche rỗng thật -> sàn trả None, beat giữ needs_human (slug assembler gánh)."""
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, stock=FakeStock(candidates=[]), niche="n-rong")
    saved = Project.load(project.project_dir)
    assert saved.shots[0].status == "needs_human"


# ----------------------------- route entity ----------------------------------
def test_entity_route_downloads_real_photo_with_flag(project, conn, tmp_path):
    project.beats = [_beat(0, route="entity", entity_queries=["trump gold card announcement"])]
    project.save()
    _run(project, conn, tmp_path, entity=FakeEntity(), niche="n1")
    saved = Project.load(project.project_dir)
    s = saved.shots[0]
    assert s.status == "ok" and s.source == "entity" and s.licensing_flag
    # cache entity được ghi vào library để video sau tái dùng
    cache = list((tmp_path / "library" / "n1" / "entity").rglob("*.jpg"))
    assert len(cache) == 1


def test_entity_route_reuses_cache_without_search(project, conn, tmp_path):
    cache_dir = tmp_path / "library" / "n1" / "entity" / "trump-gold-card-announcement"
    cache_dir.mkdir(parents=True)
    (cache_dir / "cached.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20000)  # JPEG magic

    class BoomEntity(FakeEntity):
        def search_images(self, query, n=5):
            raise AssertionError("không được gọi search khi đã có cache")

    project.beats = [_beat(0, route="entity", entity_queries=["trump gold card announcement"])]
    project.save()
    _run(project, conn, tmp_path, entity=BoomEntity(), niche="n1")
    saved = Project.load(project.project_dir)
    assert saved.shots[0].status == "ok"
    assert "cache" in saved.shots[0].note


def test_entity_route_missing_key_needs_human(project, conn, tmp_path):
    project.beats = [_beat(0, route="entity", entity_queries=["trump gold card"])]
    project.save()
    _run(project, conn, tmp_path, entity=None)
    saved = Project.load(project.project_dir)
    s = saved.shots[0]
    assert s.status == "needs_human" and s.licensing_flag
    assert "GOOGLE_CSE_KEY" in s.note


# ----------------------------- route graphic ---------------------------------
def test_graphic_route_placeholder_with_background(project, conn, tmp_path):
    project.beats = [_beat(0, route="graphic", thematic=["dark texture background"])]
    project.save()
    _run(project, conn, tmp_path)
    saved = Project.load(project.project_dir)
    s = saved.shots[0]
    assert s.status == "graphic"
    assert "EDITOR LÀM GRAPHIC" in s.note
    assert s.asset_path  # nền lót đã tải


def test_stock_download_failure_falls_to_next_candidate(project, conn, tmp_path):
    """4.7: tải hỏng -> thử ứng viên kế, không giết stage."""

    class FlakyStock(FakeStock):
        def download(self, candidate, dest):
            if candidate["asset_key"] == "pexels:0":
                raise RuntimeError("403 Forbidden")
            return super().download(candidate, dest)

    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, stock=FlakyStock())
    saved = Project.load(project.project_dir)
    assert saved.shots[0].status == "ok" and saved.shots[0].asset_key == "pexels:1"
    assert any("tải hỏng" in w for w in saved.stages[Stage.SOURCE].warnings)


def test_entity_download_failure_falls_to_next_image(project, conn, tmp_path):
    class FlakyEntity(FakeEntity):
        def __init__(self):
            super().__init__(results=[
                {"asset_key": "entity:bad", "url": "http://x/bad.jpg", "media_type": "image",
                 "description": "bad", "origin": "wikimedia.org", "preferred": True, "source": "entity"},
                {"asset_key": "entity:good", "url": "http://x/good.jpg", "media_type": "image",
                 "description": "good", "origin": "reuters.com", "preferred": True, "source": "entity"},
            ])

        def download(self, candidate, dest):
            if candidate["asset_key"] == "entity:bad":
                raise RuntimeError("Tải ảnh hỏng sau 3 lần")
            return super().download(candidate, dest)

    project.beats = [_beat(0, route="entity", entity_queries=["x"])]
    project.save()
    _run(project, conn, tmp_path, entity=FlakyEntity(), niche="n1")
    saved = Project.load(project.project_dir)
    assert saved.shots[0].status == "ok" and saved.shots[0].asset_key == "entity:good"


# ----------------------------- phễu c5 (F5) ----------------------------------
class FakeRankBrain:
    """NÃO giả cho phễu: chấm theo bảng soạn sẵn (mặc định ok 5/5); đếm call, giữ prompt."""

    def __init__(self, scores=None, vetoes=None):
        self.scores = scores or {}   # asset_key -> (nghia, mood)
        self.vetoes = vetoes or {}   # asset_key -> veto_type
        self.calls = 0
        self.prompts: list[str] = []
        self.model = "fake-brain"

    def complete(self, system, user, output_model, context=None):
        from autoedit.director.client import Usage
        from autoedit.ranker.prompts import alias_of
        from autoedit.ranker.schema import BeatRankResponse, CandidateVerdict

        self.calls += 1
        self.prompts.append(user)
        # TOC-1: prompt nay in id NGẮN — fake trả đúng alias như NÃO thật, funnel dịch về key
        ids = [ln.split(". id: ")[1].strip()
               for ln in user.splitlines() if ". id: " in ln]
        rev = {alias_of(k): k for k in set(self.scores) | set(self.vetoes)}
        verdicts = []
        for a in ids:
            k = rev.get(a, a)
            if k in self.vetoes:
                verdicts.append(CandidateVerdict(
                    id=a, verdict="veto", veto_type=self.vetoes[k],
                    diem_nghia=0, diem_mood=0, ly_do="sai nghĩa"))
            else:
                n, m = self.scores.get(k, (5, 5))
                verdicts.append(CandidateVerdict(
                    id=a, verdict="ok", diem_nghia=n, diem_mood=m, ly_do=f"hợp: {k}"))
        return BeatRankResponse(verdicts=verdicts), Usage(input_tokens=10, output_tokens=5)


def test_funnel_picks_by_brain_score_and_logs(project, conn, tmp_path):
    """Phễu thay chọn-thô: NÃO chấm cao nhất thắng (không phải ứng viên đầu);
    rank_log + kill-log + cost ghi vào project.json; note = lý do NÃO."""
    project.beats = [_beat(0)]
    project.save()
    brain = FakeRankBrain(scores={"pexels:3": (9, 8)})
    _run(project, conn, tmp_path, brain=brain)

    saved = Project.load(project.project_dir)
    assert saved.shots[0].asset_key == "pexels:3"          # chọn theo điểm, không theo thứ tự
    assert saved.shots[0].note == "hợp: pexels:3"          # editor đọc hiểu ngay
    assert brain.calls == 1                                 # đúng 1 call/beat
    assert len(saved.rank_log) == 1
    kl = saved.rank_log[0]["kill_log"]
    assert kl["thu"] == 5 and kl["con_lai"] == 5
    assert any("phễu c5" in w for w in saved.stages[Stage.RANK].warnings)
    assert any(c.stage == "rank" for c in saved.cost_log)   # token NÃO có ghi sổ


def test_perf_counters_recorded_toc4(project, conn, tmp_path):
    """TOC-4: source tự đo — started_at + perf (rank_calls/downloads/stage_s) vào
    project.json để NHAT_KY_TOC_DO không phải bấm giờ tay."""
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, brain=FakeRankBrain())
    saved = Project.load(project.project_dir)
    rec = saved.stages[Stage.SOURCE]
    assert rec.started_at and rec.completed_at
    assert rec.perf["rank_calls"] == 1
    assert rec.perf["downloads"] >= 1
    assert rec.perf["stage_s"] >= 0
    assert any(c.stage == "rank" for c in saved.cost_log)  # .model đi qua proxy nguyên


def test_funnel_serious_veto_falls_to_next(project, conn, tmp_path):
    """Veto thực-thể-sai loại hẳn ứng viên top; needs_human khi cả pool bị veto nghiêm trọng."""
    project.beats = [_beat(0)]
    project.save()
    brain = FakeRankBrain(scores={"pexels:0": (9, 9)}, vetoes={"pexels:0": "thuc_the_sai"})
    _run(project, conn, tmp_path, brain=brain)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].status == "ok" and saved.shots[0].asset_key != "pexels:0"
    assert saved.rank_log[0]["kill_log"]["veto_nghia"] == 1

    # cả pool veto nghiêm trọng -> needs_human mềm
    project2 = Project.load(project.project_dir)
    project2.beats = [_beat(0)]
    brain2 = FakeRankBrain(vetoes={f"pexels:{i}": "chu_de_khac_han" for i in range(5)})
    run_source(project2, conn, FakeStock(), None, library_root=tmp_path / "lib2", brain=brain2)
    saved2 = Project.load(project2.project_dir)
    assert saved2.shots[0].status == "needs_human"


def test_funnel_download_failure_falls_to_next_ranked(project, conn, tmp_path):
    """4.7 giữ nguyên trong phễu: top điểm tải hỏng -> lấy điểm kế tiếp."""

    class FlakyStock(FakeStock):
        def download(self, candidate, dest):
            if candidate["asset_key"] == "pexels:3":
                raise RuntimeError("403 Forbidden")
            return super().download(candidate, dest)

    project.beats = [_beat(0)]
    project.save()
    brain = FakeRankBrain(scores={"pexels:3": (9, 9), "pexels:1": (8, 8)})
    _run(project, conn, tmp_path, stock=FlakyStock(), brain=brain)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].asset_key == "pexels:1"
    assert any("tải hỏng" in w for w in saved.stages[Stage.SOURCE].warnings)


def test_funnel_hook_gathers_signature_first(project, conn, tmp_path):
    """Luật c6: beat HOOK gom signature/ trước, xếp đầu danh sách; beat thường thì KHÔNG."""
    sig = tmp_path / "sig" / "drone.mp4"
    sig.parent.mkdir()
    sig.write_bytes(b"sig-video")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(sig), category="signature", media_type="video",
        mtime=1.0, subject="drone reveal", description="signature drone",
        shot_size="aerial", mood="epic", has_people=False, tags=["drone"],
    ))
    project.outline = {"chapters": [{"chapter_id": 1, "central_subject": "Hà Nội"},
                                    {"chapter_id": 2, "central_subject": "ẩm thực"}]}
    project.beats = [_beat(0), _beat(1)]          # chapter=1 = hook (chương đầu outline)
    project.beats[1].chapter = 2                  # beat thường, visual_anchor=True
    project.save()
    brain = FakeRankBrain()
    _run(project, conn, tmp_path, brain=brain, niche="n1")

    # beat hook: ứng viên signature ĐỨNG ĐẦU prompt + central_subject có mặt
    # (TOC-1: prompt in id NGẮN — nhận diện signature qua alias của asset_key)
    from autoedit.ranker.prompts import alias_of
    sig_id = alias_of(f"local:{sig}")
    assert sig_id in brain.prompts[0]
    first_key = next(ln for ln in brain.prompts[0].splitlines() if ". id: " in ln)
    assert sig_id in first_key
    assert "central_subject: Hà Nội" in brain.prompts[0]
    # beat thường (không hook, có anchor): KHÔNG gom signature
    assert sig_id not in brain.prompts[1]
    # mạch c3: prompt beat 2 mang footage beat 1 + cờ mở chương (chapter 1 -> 2)
    assert "PREVIOUS beat" in brain.prompts[1]
    assert "OPENS A NEW CHAPTER" in brain.prompts[1]


def test_funnel_filler_slot_gathers_signature(project, conn, tmp_path):
    """SLOT CHÊM (visual_anchor=False) cũng gom signature/ dù không phải hook."""
    sig = tmp_path / "sig2" / "b-roll.mp4"
    sig.parent.mkdir()
    sig.write_bytes(b"sig")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(sig), category="signature", media_type="video",
        mtime=1.0, subject="b-roll city", description="signature b-roll",
        shot_size="wide", mood="calm", has_people=False, tags=[],
    ))
    project.outline = {"chapters": [{"chapter_id": 9, "central_subject": "x"}]}  # hook = ch 9
    project.beats = [_beat(0)]                    # chapter=1, KHÔNG phải hook
    project.beats[0].visual_anchor = False        # slot chêm
    project.save()
    brain = FakeRankBrain()
    _run(project, conn, tmp_path, brain=brain, niche="n1")
    from autoedit.ranker.prompts import alias_of
    assert alias_of(f"local:{sig}") in brain.prompts[0]  # TOC-1: prompt in id ngắn


def test_local_candidates_carry_shot_size(conn, tmp_path):
    """c7: tag shot_size từ DB phải theo ứng viên vào phễu (trước đây bị đánh rơi)."""
    f = tmp_path / "walk.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="street", media_type="video",
        mtime=1.0, subject="man walking street", description="d",
        shot_size="medium", mood="neutral", has_people=True, tags=[],
    ))
    out = find_local_candidates(conn, "n1", SearchQueries(specific=["man walking street"]))
    assert out and out[0]["shot_size"] == "medium" and out[0]["mood"] == "neutral"


def test_local_candidates_carry_duration(conn, tmp_path):
    """PB7: duration từ DB (ống nạp PB4) phải theo ứng viên vào phễu — trước đây bị
    đánh rơi -> cửa clip-quá-ngắn + điểm khớp-độ-dài mù với footage local."""
    f = tmp_path / "nebula.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="spiral nebula deep space", description="d",
        shot_size="wide", mood="mysterious", has_people=False, tags=[], duration=7.2,
    ))
    out = find_local_candidates(conn, "n1", SearchQueries(specific=["spiral nebula"]))
    assert out and out[0]["duration"] == 7.2


def test_local_candidates_no_duration_key_when_unknown(conn, tmp_path):
    """PB7 bẫy loại-oan: asset cũ (trước migrate PB4) duration=0 -> KHÔNG gắn key,
    nếu truyền 0 thẳng thì cửa kỹ thuật phễu loại oan mọi asset cũ (0 < mọi beat_dur)."""
    f = tmp_path / "old.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="street", media_type="video",
        mtime=1.0, subject="old asset walking", description="d",
        shot_size="wide", mood="calm", has_people=False, tags=[],
    ))
    out = find_local_candidates(conn, "n1", SearchQueries(specific=["old asset"]))
    assert out and "duration" not in out[0]


def test_local_candidates_exclude_used_before_limit(conn, tmp_path):
    """Bug DS3-084 (26 beat needs_human oan): search_assets cắt TOP-limit theo thứ tự
    DB cố định TRƯỚC, luật P7 đã-dùng lọc SAU -> video dài lặp query, 5 dòng đầu bị
    dùng hết là mọi beat sau trắng tay dù kho còn cả nghìn asset. Fix: used_keys
    truyền xuống, lọc TRƯỚC nhát cắt limit."""
    paths = []
    for i in range(8):
        f = tmp_path / f"shark{i}.mp4"
        f.write_bytes(b"v")
        db.upsert_asset(conn, db.AssetRecord(
            niche="n1", path=str(f), category="nap", media_type="video",
            mtime=1.0, subject="shark swimming deep", description="d",
            shot_size="wide", mood="dark", has_people=False, tags=["shark"],
        ))
        paths.append(str(f))
    q = SearchQueries(local=["shark swimming"])
    top5 = [c["path"] for c in find_local_candidates(conn, "n1", q)]
    assert len(top5) == 5  # limit/query = 5, thứ tự cố định
    used = {f"local:{p}" for p in top5}
    out = find_local_candidates(conn, "n1", q, used_keys=used)
    # trước fix: [] (trắng tay oan); sau fix: đúng 3 asset còn lại chưa dùng
    assert {c["path"] for c in out} == set(paths) - set(top5)


def test_signature_candidates_exclude_used_before_limit(conn, tmp_path):
    """Anh em cùng pattern bug DS3-084: signature_assets cũng cắt LIMIT trước —
    beat hook sau nhận trắng khi top-5 signature đã dùng."""
    from autoedit.sourcer.local import find_signature_candidates
    paths = []
    for i in range(7):
        f = tmp_path / f"sig{i}.mp4"
        f.write_bytes(b"v")
        db.upsert_asset(conn, db.AssetRecord(
            niche="n1", path=str(f), category="signature", media_type="video",
            mtime=1.0, subject="hero shot", description="d",
            shot_size="wide", mood="epic", has_people=False, tags=[],
        ))
        paths.append(str(f))
    top5 = [c["path"] for c in find_signature_candidates(conn, "n1")]
    assert len(top5) == 5
    used = {f"local:{p}" for p in top5}
    out = find_signature_candidates(conn, "n1", used_keys=used)
    assert {c["path"] for c in out} == set(paths) - set(top5)


# ----------------------------- C6 drop-list từ chuyển động (PB8) -------------
def test_strip_motion_terms_words_and_phrases():
    from autoedit.sourcer.local import _strip_motion_terms

    assert _strip_motion_terms("spiral galaxy rotating") == "spiral galaxy"
    assert _strip_motion_terms("stars timelapse") == "stars"
    assert _strip_motion_terms("universe zoom out") == "universe"   # cụm 2 từ
    assert _strip_motion_terms("astronaut floating") == "astronaut"
    assert _strip_motion_terms("night sky") == "night sky"          # không dính -> no-op
    # bỏ hết sạch token -> giữ NGUYÊN query gốc (không match bừa cả kho)
    assert _strip_motion_terms("zoom out") == "zoom out"
    # từ sự kiện CÓ NGHĨA không bị đụng (drop-list chỉ camera/thời-gian)
    assert _strip_motion_terms("supernova explosion") == "supernova explosion"


def test_local_candidates_motion_word_no_longer_blocks(conn, tmp_path):
    """PB8 2b: kho có 'spiral galaxy' nhưng GLM tag frame TĨNH không bao giờ có
    'rotating' -> query từng AND-trượt oan 0 khớp. C6 bỏ từ chuyển động -> vào pool."""
    f = tmp_path / "galaxy.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="spiral galaxy deep space", description="d",
        shot_size="wide", mood="epic", has_people=False, tags=["galaxy", "stars"],
    ))
    out = find_local_candidates(
        conn, "n1", SearchQueries(specific=["spiral galaxy rotating"]))
    assert out and out[0]["asset_key"] == f"local:{f}"


# ----------------------------- D3 trần tổng local (C đợt 2) ------------------
def test_local_total_cap_and_per_query_limit_d3(conn, tmp_path):
    """D3: trần TỔNG 10 tách khỏi limit per-query 5 — query đầu (8 khớp) chỉ chiếm 5
    suất, query sau vẫn còn chỗ; tổng kẹp tại LOCAL_TOTAL_CAP."""
    for i in range(8):
        f = tmp_path / f"alpha{i}.mp4"
        f.write_bytes(b"v")
        db.upsert_asset(conn, db.AssetRecord(
            niche="n1", path=str(f), category="nap", media_type="video", mtime=1.0,
            subject="alpha scene galaxy", description="d", shot_size="wide",
            mood="epic", has_people=False, tags=[]))
    for i in range(8):
        f = tmp_path / f"beta{i}.mp4"
        f.write_bytes(b"v")
        db.upsert_asset(conn, db.AssetRecord(
            niche="n1", path=str(f), category="nap", media_type="video", mtime=1.0,
            subject="beta scene nebula", description="d", shot_size="wide",
            mood="epic", has_people=False, tags=[]))
    q = SearchQueries(specific=["beta scene"], broad=[], thematic=[],
                      local=["alpha scene"])
    out = find_local_candidates(conn, "n1", q)
    assert len(out) == 10                                   # trần tổng D3
    n_alpha = sum(1 for c in out if "alpha" in c["path"])
    assert n_alpha == 5                                     # per-query giữ 5
    assert sum(1 for c in out if "beta" in c["path"]) == 5  # query sau vẫn có suất


# ----------------------------- C8 gói CHỌN: gate pháp lý viral ---------------
def _viral_cand(idx, dur=6.0, src="E:/src.mp4"):
    return {"source_class": "viral", "source_video": src, "scene_index": idx,
            "source_duration": 600.0, "duration": dur}


def test_viral_ledger_adjacency_far_apart_still_banned():
    """c8 luật 3 (user chốt 2026-07-08): cảnh 5 đã pick -> cảnh 4/6 cùng nguồn bị cấm
    DÙ ĐẶT XA NHAU trên timeline; cách 2 cảnh thì qua; own/Pexels miễn mọi gate."""
    from autoedit.sourcer.viral import ViralLedger

    lg = ViralLedger()
    assert lg.blocks({"source": "local"}) == ""          # own không có source_class
    assert lg.blocks(_viral_cand(5)) == ""
    lg.add(_viral_cand(5))
    assert lg.blocks(_viral_cand(4)) and lg.blocks(_viral_cand(6))
    assert lg.blocks(_viral_cand(5))                     # trùng cảnh
    assert lg.blocks(_viral_cand(7)) == ""               # cách 2 -> qua
    assert lg.blocks(_viral_cand(6, src="E:/other.mp4")) == ""  # nguồn khác không vạ lây


def test_viral_ledger_peak_exempts_adjacency_not_cap():
    """ytref (user chốt 2026-07-11): cảnh ĐIỂM NHÔ miễn luật kề ±1 — trio 3 cảnh
    build-up sát đỉnh lấy được CẢ; trùng chính nó + trần 8% vẫn áp; cảnh THƯỜNG
    kề cảnh điểm nhô đã pick vẫn bị cấm như cũ."""
    from autoedit.sourcer.viral import ViralLedger

    def pk(i):
        return _viral_cand(i) | {"peak_value": 0.9, "peak_type": "primary"}

    lg = ViralLedger()
    lg.add(pk(5))
    assert lg.blocks(pk(6)) == ""                        # kề nhưng điểm nhô -> qua
    lg.add(pk(6))
    assert lg.blocks(pk(7)) == ""                        # cả trio 5-6-7 vào được
    lg.add(pk(7))
    assert "trùng" in lg.blocks(pk(6))                   # trùng chính nó vẫn chặn
    assert "kề" in lg.blocks(_viral_cand(8))             # cảnh thường kề 7 vẫn cấm
    for i in (10, 12, 14, 16, 18):                       # 3×6 + 5×6 = 48s = trần 8%
        lg.add(pk(i))
    assert "8%" in lg.blocks(pk(30))                     # trần 8% KHÔNG miễn


def test_viral_ledger_counts_peak_picks():
    """ytref §3h: ledger đếm pick mang cờ điểm nhô (dòng 'viral c8 · pick điểm nhô: N'
    trong report); pick viral thường + own KHÔNG đếm."""
    from autoedit.sourcer.viral import ViralLedger

    lg = ViralLedger()
    lg.add(_viral_cand(1) | {"peak_value": 0.9, "peak_type": "primary"})
    lg.add(_viral_cand(3))                               # viral thường
    lg.add({"source": "local"})                          # own — add() bỏ qua từ đầu
    assert lg.peak_picks == 1


def test_viral_ledger_8pct_cap_accumulates():
    """c8 luật 5: trần 8% × source_duration (600s -> 48s), cộng dồn TRỌN duration clip;
    thiếu source_duration -> chặn luôn (fail-safe mẫu số)."""
    from autoedit.sourcer.viral import ViralLedger

    lg = ViralLedger()
    for i in (1, 3, 5, 7, 9, 11, 13, 15):                # 8 clip × 6s = 48s = đúng trần
        assert lg.blocks(_viral_cand(i)) == ""
        lg.add(_viral_cand(i))
    assert lg.seconds["E:/src.mp4"] == pytest.approx(48.0)
    assert "8%" in lg.blocks(_viral_cand(30))
    assert "source_duration" in lg.blocks(
        {"source_class": "viral", "source_video": "x", "scene_index": 1, "duration": 3.0})


def test_viral_ledger_gate_filters_counts_and_spreads():
    """gate(): lọc cứng + đếm blocked (report) + sort rải mềm — nguồn ít-dùng lên trước,
    own giữ nguyên (key=0, sort ổn định). KHÔNG phải cửa loại chất lượng."""
    from autoedit.sourcer.viral import ViralLedger

    lg = ViralLedger()
    lg.add(_viral_cand(5))                               # src.mp4 đã dùng 6s
    own = {"asset_key": "local:/own.mp4"}
    fresh = _viral_cand(2, src="E:/fresh.mp4")
    used_src = _viral_cand(9)                            # cùng src.mp4, không kề -> qua gate
    adjacent = _viral_cand(6)                            # kề cảnh 5 -> chết
    out = lg.gate([own, used_src, adjacent, fresh])
    assert adjacent not in out and lg.blocked == 1
    assert out.index(fresh) < out.index(used_src)        # rải: nguồn chưa dùng lên trước
    assert out[0] is own                                 # own key=0 giữ đầu (sort ổn định)


def test_local_candidates_carry_viral_provenance(conn, tmp_path):
    """c8: ứng viên viral mang source_class/source_video/scene_index/source_duration
    cho ledger gate; asset own KHÔNG có key (ledger coi là miễn gate)."""
    f = tmp_path / "viral_clip.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="galaxy viral pan", description="d",
        shot_size="wide", mood="epic", has_people=False, tags=[], duration=6.0,
        source_video="E:/src.mp4", scene_index=41, source_class="viral",
        source_duration=724.0, peak_value=0.9, peak_type="primary"))
    out = find_local_candidates(conn, "n1", SearchQueries(specific=["galaxy viral"]))
    assert out and out[0]["source_class"] == "viral"
    assert out[0]["scene_index"] == 41 and out[0]["source_duration"] == 724.0
    assert out[0]["source_video"] == "E:/src.mp4"
    # ytref: 2 cột điểm nhô KHÔNG rơi (vết PB7) — ledger miễn-kề + M3 bonus đọc
    assert out[0]["peak_value"] == 0.9 and out[0]["peak_type"] == "primary"


# ----------------------------- REF nguồn mẫu của bài (user 2026-07-11) -------
def test_viral_ledger_ref_cap_15pct():
    """REF: nguồn khai --ref trần 15% (600s -> 90s) thay 8% (48s); prefix so
    KHÔNG phân hoa-thường (path Windows); nguồn ngoài ref giữ nguyên 8%."""
    from autoedit.sourcer.viral import ViralLedger

    lg = ViralLedger(ref_sources=["E:/SRC.mp4"])          # khai HOA, cand ghi thường
    for i in (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29):  # 15×6s=90s=trần 15%
        assert lg.blocks(_viral_cand(i)) == ""
        lg.add(_viral_cand(i))
    assert "15%" in lg.blocks(_viral_cand(40))            # quá 90s -> chặn, báo đúng 15%
    lg2 = ViralLedger(ref_sources=["E:/SRC.mp4"])
    for i in (1, 3, 5, 7, 9, 11, 13, 15):                 # nguồn KHÁC: 48s = trần 8% cũ
        lg2.add(_viral_cand(i, src="E:/other.mp4"))
    assert "8%" in lg2.blocks(_viral_cand(30, src="E:/other.mp4"))


def test_find_ref_candidates_or_match(conn, tmp_path):
    """REF: match NỚI trúng ≥1 từ query CHỈ trong tập nguồn --ref; asset ngoài ref
    không vào lưới này; beat không trúng từ nào (ẩn dụ chủ đích) -> không chèn."""
    from autoedit.sourcer.local import find_ref_candidates

    def _seed(name, subject, src):
        f = tmp_path / name
        f.write_bytes(b"v")
        db.upsert_asset(conn, db.AssetRecord(
            niche="space", path=str(f), category="nap", media_type="video",
            mtime=1.0, subject=subject, description="d", shot_size="wide",
            mood="epic", has_people=False, tags=[], duration=6.0,
            source_video=src, scene_index=1, source_class="viral",
            source_duration=600.0))

    _seed("ref1.mp4", "spacecraft assembly cleanroom", "F:/VIDEO MAU/SP1/a.mp4")
    _seed("ref2.mp4", "lunar surface craters", "F:/VIDEO MAU/SP1/b.mp4")
    _seed("ngoai.mp4", "spacecraft assembly factory", "E:/khac/c.mp4")
    prefixes = ("f:/video mau/sp1",)
    # AND-match kho chung trượt query này ('blueprints' không có) — OR-match ref vẫn vớt
    q = SearchQueries(specific=["assembly blueprints table"])
    out = find_ref_candidates(conn, "space", prefixes, q)
    assert [c["description"] for c in out] == ["spacecraft assembly cleanroom"]
    assert out[0]["source_class"] == "viral"              # nhãn ledger không rơi (vết PB7)
    # beat ẩn dụ: không từ nào trúng -> pool sạch, không nhiễu
    assert find_ref_candidates(conn, "space", prefixes,
                               SearchQueries(specific=["grandmother kitchen recipe"])) == []


def test_gather_marks_ref_and_diem_may_bonus(project, conn, tmp_path):
    """REF glue: _gather_candidates đánh dấu is_ref MỌI đường vào pool (local AND-match
    lẫn chèn OR-match) theo prefix ledger; _diem_may cộng đúng REF_BONUS."""
    from autoedit.ranker.funnel import REF_BONUS, _diem_may
    from autoedit.sourcer.runner import _gather_candidates
    from autoedit.sourcer.viral import ViralLedger

    f = tmp_path / "refclip.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="space", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="man walking street", description="d", shot_size="wide",
        mood="epic", has_people=False, tags=[], duration=6.0,
        source_video="F:/VIDEO MAU/SP1/a.mp4", scene_index=1, source_class="viral",
        source_duration=600.0))
    ledger = ViralLedger(ref_sources=["F:/VIDEO MAU/SP1"])
    cands, _ = _gather_candidates(_beat(0), conn, FakeStock(), "space", set(),
                                  signature_first=False, ledger=ledger)
    ref = [c for c in cands if c.get("is_ref")]
    assert len(ref) == 1 and ref[0]["source_video"] == "F:/VIDEO MAU/SP1/a.mp4"
    assert all(not c.get("is_ref") for c in cands if c["asset_key"].startswith("pexels:"))
    assert _diem_may(ref[0], 5.0, "", 1) - _diem_may(dict(ref[0], is_ref=False), 5.0, "", 1) \
        == pytest.approx(REF_BONUS)


def _seed_ref(conn, tmp_path, name, src, subject="man walking street"):
    """Asset viral thuộc mẻ mẫu --ref (khuôn test REF theo chương VD2)."""
    f = tmp_path / name
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="space", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject=subject, description=subject, shot_size="wide",
        mood="epic", has_people=False, tags=[], duration=6.0,
        source_video=src, scene_index=1, source_class="viral",
        source_duration=600.0))


def test_ref_chapter_scan_map_and_counts(conn, tmp_path):
    """VD2 REF theo chương: segment 'Chapter N'/'CHUONG N'/'ch N' NGAY DƯỚI prefix --ref
    -> map chương; file ở gốc + folder con tên thường -> chung; prefix trả về có dấu
    phân cách cuối ('chapter 1/' KHÔNG nuốt 'chapter 10/'); folder mẫu phẳng -> map rỗng."""
    from autoedit.sourcer.local import ref_chapter_scan

    root = "F:/VIDEO MAU/AMZ/"
    _seed_ref(conn, tmp_path, "s0.mp4", root + "goc.mp4")             # file ngay gốc -> chung
    _seed_ref(conn, tmp_path, "s1.mp4", root + "Chapter 1/a.mp4")
    _seed_ref(conn, tmp_path, "s2.mp4", root + "CHUONG 2/b.mp4")
    _seed_ref(conn, tmp_path, "s3.mp4", root + "ch 3/c.mp4")
    _seed_ref(conn, tmp_path, "s4.mp4", root + "Chapter 10/d.mp4")
    _seed_ref(conn, tmp_path, "s5.mp4", root + "food market/e.mp4")   # tên thường -> chung
    mapping, counts = ref_chapter_scan(conn, "space", ("f:/video mau/amz/",))
    assert sorted(mapping) == [1, 2, 3, 10]
    assert mapping[1] == ("f:/video mau/amz/chapter 1/",)
    assert counts == {1: 1, 2: 1, 3: 1, 10: 1, "chung": 2}
    # separator cuối prefix: cảnh Chapter 10 KHÔNG dính vào chương 1
    assert not (root.lower() + "chapter 10/d.mp4").startswith(mapping[1])
    # folder mẫu phẳng (không folder chương) -> map rỗng = hành xử REF y cũ
    _seed_ref(conn, tmp_path, "s6.mp4", "F:/VIDEO MAU/FLAT/x.mp4")
    assert ref_chapter_scan(conn, "space", ("f:/video mau/flat/",)) == ({}, {"chung": 1})


def test_find_ref_candidates_exclude_prefixes(conn, tmp_path):
    """VD2: exclude_prefixes chặn suất CHÈN của cảnh chương KHÁC — cảnh đúng chương +
    mẫu chung vẫn vào lưới vớt."""
    from autoedit.sourcer.local import find_ref_candidates

    root = "F:/VIDEO MAU/AMZ2/"
    _seed_ref(conn, tmp_path, "e1.mp4", root + "Chapter 1/a.mp4", "old town market street")
    _seed_ref(conn, tmp_path, "e2.mp4", root + "Chapter 2/b.mp4", "night market food stalls")
    _seed_ref(conn, tmp_path, "e3.mp4", root + "goc.mp4", "market square people")
    q = SearchQueries(specific=["market crowds"])
    out = find_ref_candidates(conn, "space", ("f:/video mau/amz2/",), q,
                              exclude_prefixes=("f:/video mau/amz2/chapter 2/",))
    assert sorted(c["source_video"] for c in out) == \
        [root + "Chapter 1/a.mp4", root + "goc.mp4"]


def test_gather_ref_chapter_soft_scope(project, conn, tmp_path):
    """VD2 MỀM (user chốt 2026-07-18): beat chương 1 — cảnh mẫu Chapter 2 VẪN nằm trong
    pool qua đường search thường (không cửa loại) nhưng KHÔNG nhãn is_ref (mất bonus);
    cảnh Chapter 1 + mẫu chung giữ nhãn."""
    from autoedit.sourcer.local import ref_chapter_scan
    from autoedit.sourcer.runner import _gather_candidates
    from autoedit.sourcer.viral import ViralLedger

    root = "F:/VIDEO MAU/AMZ3/"
    _seed_ref(conn, tmp_path, "g1.mp4", root + "Chapter 1/a.mp4")
    _seed_ref(conn, tmp_path, "g2.mp4", root + "Chapter 2/b.mp4")
    _seed_ref(conn, tmp_path, "g3.mp4", root + "goc.mp4")
    ledger = ViralLedger(ref_sources=[root])
    ledger.ref_chapter_prefixes, _ = ref_chapter_scan(conn, "space", ledger.ref_prefixes)
    beat = _beat(0)   # chapter=1
    cands, _ = _gather_candidates(beat, conn, FakeStock(), "space", set(),
                                  signature_first=False, ledger=ledger)
    by_src = {c.get("source_video", ""): c for c in cands}
    assert root + "Chapter 2/b.mp4" in by_src        # mềm: vẫn trong pool (search thường)
    assert not by_src[root + "Chapter 2/b.mp4"].get("is_ref")
    assert by_src[root + "Chapter 1/a.mp4"].get("is_ref")
    assert by_src[root + "goc.mp4"].get("is_ref")


# ----------------------------- entity filter (dùng chung provider) -----------
def test_filter_and_rank_images_blocklist_and_preference():
    from autoedit.sourcer.entity import filter_and_rank_images

    raw = [
        {"url": "https://www.gettyimages.com/x.jpg", "origin": "gettyimages.com", "description": "stock"},
        {"url": "https://cdn.site.com/a.jpg", "origin": "randomblog.com", "description": "blog"},
        {"url": "https://media.reuters.com/b.jpg", "origin": "reuters.com", "description": "news"},
    ]
    out = filter_and_rank_images(raw, n=5)
    # getty bị loại tuyệt đối; reuters (preferred) lên đầu dù đứng sau trong input
    assert [o["origin"] for o in out] == ["reuters.com", "randomblog.com"]
    assert all(o["asset_key"].startswith("entity:") for o in out)
    assert out[0]["preferred"] and not out[1]["preferred"]


# ----------------------------- F5 shot_count: nhiều footage/beat -------------
def test_shot_count_target_clamps():
    from autoedit.packager.coverage import MIN_SHOT_DUR
    from autoedit.sourcer.runner import _shot_count_target

    # beat đủ dài (3s), LLM xin 3 -> 3
    b = _beat(0); b.start, b.end, b.shot_count = 0.0, 3.0, 3
    assert _shot_count_target(b) == 3
    # beat ngắn (1s) -> sàn kẹp: floor(1.0/0.7)=1
    b2 = _beat(1); b2.start, b2.end, b2.shot_count = 0.0, 1.0, 3
    assert _shot_count_target(b2) == max(1, int(1.0 / MIN_SHOT_DUR))
    # shot_count=1 -> 1 (mặc định)
    b3 = _beat(2); b3.start, b3.end = 0.0, 5.0
    assert _shot_count_target(b3) == 1


def test_shot_count_forced_one_for_special_layout():
    from autoedit.project import InfoCard
    from autoedit.sourcer.runner import _shot_count_target

    b = _beat(0); b.start, b.end, b.shot_count = 0.0, 6.0, 3
    b.info_card = InfoCard(title="x", bullets=["a", "b"], approved=True)
    assert _shot_count_target(b) == 1  # beat có info-card -> giữ 1 shot (layout riêng)


def test_funnel_multi_shot_picks_n_distinct(project, conn, tmp_path):
    """beat shot_count=3, pool đủ -> clip chính + 2 extra_shots KHÁC nhau; cả 3 vào used_in_video."""
    beat = _beat(0)
    beat.start, beat.end, beat.shot_count = 0.0, 3.0, 3   # 3s đủ cho 3 shot (sàn 0.7)
    project.beats = [beat]
    project.save()
    brain = FakeRankBrain(scores={"pexels:2": (9, 9), "pexels:1": (8, 8), "pexels:0": (7, 7)})
    _run(project, conn, tmp_path, brain=brain)

    saved = Project.load(project.project_dir)
    s = saved.shots[0]
    assert s.asset_key == "pexels:2"                       # clip chính = điểm cao nhất
    assert len(s.extra_shots) == 2
    keys = [s.asset_key] + [e.asset_key for e in s.extra_shots]
    assert keys == ["pexels:2", "pexels:1", "pexels:0"]    # theo thứ tự điểm
    assert len(set(keys)) == 3                             # 3 clip KHÁC nhau
    assert all((Path(saved.project_dir) / e.asset_path).is_file() for e in s.extra_shots)
    # bug đè file: N clip CÙNG beat có cùng visual_concept -> tên file phải KHÁC nhau
    # (không clip sau ghi đè clip trước) -> asset_path phân biệt
    paths = [s.asset_path] + [e.asset_path for e in s.extra_shots]
    assert len(set(paths)) == 3


def test_funnel_multi_shot_capped_by_pool(project, conn, tmp_path):
    """shot_count=3 nhưng pool chỉ 2 clip -> 2 shot (pha 2: kho quyết số cuối)."""
    beat = _beat(0)
    beat.start, beat.end, beat.shot_count = 0.0, 3.0, 3
    project.beats = [beat]
    project.save()
    stock = FakeStock(candidates=[
        {"asset_key": f"pexels:{i}", "url": f"http://x/{i}.mp4", "media_type": "video",
         "duration": 10.0, "description": f"clip {i}", "source": "pexels"}
        for i in range(2)
    ])
    _run(project, conn, tmp_path, stock=stock, brain=FakeRankBrain())
    saved = Project.load(project.project_dir)
    assert len(saved.shots[0].extra_shots) == 1            # 2 shot: 1 chính + 1 extra


def test_funnel_single_shot_no_extras(project, conn, tmp_path):
    """shot_count=1 (mặc định) -> không extra_shots (hành vi cũ y hệt)."""
    project.beats = [_beat(0)]   # shot_count mặc định 1
    project.save()
    _run(project, conn, tmp_path, brain=FakeRankBrain())
    saved = Project.load(project.project_dir)
    assert saved.shots[0].extra_shots == []


# ----------------------------- Lớp 2: sàn phân giải ảnh entity ----------------
def _make_png(path: Path, w: int, h: int) -> Path:
    from PIL import Image

    Image.new("RGB", (w, h), (120, 90, 60)).save(path)
    return path


def test_image_width_measures_and_fails_open(tmp_path):
    from autoedit.sourcer.entity import image_width

    big = _make_png(tmp_path / "big.png", 1920, 1080)
    assert image_width(big) == 1920
    # file rác không decode được -> 0 (caller fail-open, không loại oan)
    junk = tmp_path / "junk.jpg"
    junk.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 5000)
    assert image_width(junk) == 0
    assert image_width(tmp_path / "khong-ton-tai.png") == 0


def test_filter_ranks_drops_small_and_prefers_large():
    from autoedit.sourcer.entity import MIN_IMAGE_WIDTH, filter_and_rank_images

    raw = [
        {"url": "http://a/x.jpg", "origin": "blog.com", "description": "nhỏ", "width": 250},
        {"url": "http://b/y.jpg", "origin": "blog.com", "description": "vừa", "width": MIN_IMAGE_WIDTH},
        {"url": "http://c/z.jpg", "origin": "blog.com", "description": "to", "width": 3000},
        {"url": "http://d/w.jpg", "origin": "reuters.com", "description": "báo", "width": 1400},
    ]
    out = filter_and_rank_images(raw, n=5)
    keys = [o["description"] for o in out]
    assert "nhỏ" not in keys                       # 250px < sàn -> loại
    assert keys[0] == "báo"                         # preferred (reuters) lên đầu
    assert keys[1:] == ["to", "vừa"]                # cùng hạng: ảnh to hơn trước


def test_filter_keeps_when_width_unknown():
    """Metadata thiếu width (0) -> KHÔNG loại (backstop sau-tải mới quyết)."""
    from autoedit.sourcer.entity import filter_and_rank_images

    raw = [{"url": "http://a/x.jpg", "origin": "blog.com", "description": "?", "width": 0}]
    assert len(filter_and_rank_images(raw, n=5)) == 1


def test_download_rejects_low_res_image(tmp_path, monkeypatch):
    """Backstop: metadata qua được nhưng pixel thật < sàn -> raise để caller thử ảnh khác."""
    import io

    from autoedit.sourcer import entity
    from PIL import Image

    def fake_get(url, stream, timeout, headers):
        import os

        buf = io.BytesIO()
        w = 2000 if "big" in url else 600      # 'big' = nét; 600px = mờ (<1280 sàn)
        h = w * 2 // 3
        # nhiễu để PNG > 10KB (vượt cửa 'file quá nhỏ' → mới tới được cửa phân giải)
        Image.frombytes("RGB", (w, h), os.urandom(w * h * 3)).save(buf, format="PNG")
        body = buf.getvalue()

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def raise_for_status(self): pass
            def iter_content(self, chunk_size): yield body
        return Resp()

    monkeypatch.setattr(entity.requests, "get", fake_get)
    monkeypatch.setattr(entity.time, "sleep", lambda *_: None)

    with pytest.raises(RuntimeError, match="phân giải thấp"):
        entity._download_image("http://x/small.png", tmp_path / "small.png")
    ok = entity._download_image("http://x/big.png", tmp_path / "big.png")
    assert entity.image_width(ok) == 2000


def test_serper_search_filters_small_images(conn):
    """Serper trả imageWidth -> ảnh nhỏ bị lọc ở tầng metadata (khỏi tải)."""
    import json

    from autoedit.sourcer.entity import SerperEntityClient

    payload = {"images": [
        {"imageUrl": "http://a/tiny.jpg", "domain": "wiki.org", "title": "tiny", "imageWidth": 330},
        {"imageUrl": "http://b/hd.jpg", "domain": "news.com", "title": "hd", "imageWidth": 1920},
    ]}
    conn.execute("INSERT INTO search_cache (provider, query, response, cached_at) "
                 "VALUES ('serper', 'cairo', ?, 'now')", (json.dumps(payload),))
    conn.commit()
    client = SerperEntityClient.__new__(SerperEntityClient)
    client.key, client.conn = "fake", conn
    out = client.search_images("cairo")
    assert [o["description"] for o in out] == ["hd"]   # chỉ ảnh 1920px lọt


# ----------------------------- guard + local find ----------------------------
def test_source_requires_cut(project, conn, tmp_path):
    project.stages[Stage.CUT].status = StageStatus.PENDING
    project.beats = [_beat(0)]
    project.save()
    with pytest.raises(RuntimeError, match="cut"):
        _run(project, conn, tmp_path)


def test_find_local_candidates_specific_only(conn, tmp_path):
    """Local CHỈ match tier specific. Broad/thematic generic bị BỎ QUA để không kéo
    footage sai địa danh (bug Alaska ra Hà Giang). Khán giả > tái dùng siêu dữ liệu."""
    f = tmp_path / "x.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="vietnam", media_type="video", mtime=1.0,
        subject="night market", description="vietnam night market neon",
        shot_size="medium", mood="vibrant", has_people=True, tags=["night market"],
    ))
    # khớp QUA broad -> KHÔNG còn trả (hành vi mới)
    q_broad = SearchQueries(specific=["khong khop gi"], broad=["night market"], thematic=[])
    assert find_local_candidates(conn, "n1", q_broad) == []
    # khớp qua specific -> trả
    q_spec = SearchQueries(specific=["night market"], broad=[], thematic=[])
    out = find_local_candidates(conn, "n1", q_spec)
    assert len(out) == 1 and out[0]["source"] == "local"
    assert find_local_candidates(conn, "", q_spec) == []


def test_find_local_rejects_wrong_place(conn, tmp_path):
    """Địa danh đúng ở mức TINH: video Hà Nội (specific có 'hanoi') KHÔNG kéo clip Hà Giang
    — chữ 'hanoi' AND-match loại clip Hà Giang. Nhưng video Hà Giang thì khớp đúng."""
    f = tmp_path / "hg.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="vietnam", media_type="video", mtime=1.0,
        subject="mountain valley village ha giang", description="ha giang terraced fields",
        shot_size="wide", mood="serene", has_people=False, tags=["mountain", "valley"],
        folder_path="vietnam/ha giang",
    ))
    # video Hà Nội: specific 'hanoi...' -> clip Hà Giang không có 'hanoi' -> loại (broad bị bỏ)
    q_hanoi = SearchQueries(specific=["hanoi old quarter street"], broad=["remote valley"], thematic=[])
    assert find_local_candidates(conn, "n1", q_hanoi) == []
    # video Hà Giang: specific khớp đúng nơi
    q_hg = SearchQueries(specific=["ha giang mountain valley"], broad=[], thematic=[])
    assert len(find_local_candidates(conn, "n1", q_hg)) == 1


def test_geo_gate_vetoes_wrong_country(conn, tmp_path):
    """PA2: clip có QUỐC GIA không xuất hiện trong script -> veto (video Mỹ ra Hà Giang)."""
    f = tmp_path / "hg.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="vietnam", media_type="video", mtime=1.0,
        subject="rice terrace aerial", description="green rice terrace",
        shot_size="wide", mood="serene", has_people=False, tags=["rice", "terrace"],
        folder_path="Khu Vực Châu Á (Asia)/VIETNAM/HA GIANG",
    ))
    q = SearchQueries(specific=["rice terrace aerial"], broad=[], thematic=[])
    # script Alaska (không có 'vietnam') -> veto
    assert find_local_candidates(conn, "n1", q, script_text="Alaska bush rice terrace") == []
    # script có 'Vietnam' -> qua
    assert len(find_local_candidates(conn, "n1", q, script_text="Vietnam rice terrace life")) == 1
    # không truyền script_text -> KHÔNG gate (backward compat)
    assert len(find_local_candidates(conn, "n1", q)) == 1


def test_find_local_candidates_local_tier_c4(conn, tmp_path):
    """C4: tier `local` (NÃO viết theo vocab tag kho) được match TRƯỚC specific —
    query specific kiểu Pexels mang từ chuyển động AND-trượt (bài học PB8) nhưng
    tier local vẫn tìm thấy clip. Không có tier local -> hành vi cũ y nguyên."""
    f = tmp_path / "gal.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="nap", media_type="video", mtime=1.0,
        subject="spiral galaxy", description="deep space spiral galaxy",
        shot_size="wide", mood="epic", has_people=False, tags=["galaxy", "space"],
    ))
    q = SearchQueries(specific=["spiral galaxy rotating"], broad=[], thematic=[],
                      local=["spiral galaxy"])
    out = find_local_candidates(conn, "n1", q)
    assert len(out) == 1 and out[0]["source"] == "local"
    # C6 (đổi CÓ CHỦ ĐÍCH 2026-07-09, trước đây assert == [] tài liệu hóa bug PB8):
    # thiếu tier local, query specific mang từ chuyển động GIỜ VẪN khớp nhờ drop-list
    q_old = SearchQueries(specific=["spiral galaxy rotating"], broad=[], thematic=[])
    assert len(find_local_candidates(conn, "n1", q_old)) == 1


def test_find_local_local_tier_still_geo_gated_c4(conn, tmp_path):
    """C4: nới tier local KHÔNG nới geo-gate PA2 — clip sai quốc gia so script vẫn bị loại."""
    f = tmp_path / "hg.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="vietnam", media_type="video", mtime=1.0,
        subject="rice terrace aerial", description="green terrace", shot_size="wide",
        mood="serene", has_people=False, tags=["rice terrace"],
        folder_path="Khu Vực Châu Á (Asia)/VIETNAM/HA GIANG",
    ))
    q = SearchQueries(specific=[], broad=[], thematic=[], local=["rice terrace"])
    assert find_local_candidates(conn, "n1", q, script_text="Alaska bush aerial") == []
    assert len(find_local_candidates(conn, "n1", q, script_text="Vietnam rice fields")) == 1


def test_run_source_reports_local_first_stats_c4(project, conn, tmp_path):
    """C4: mỗi run tự báo 'local-first (C4): X/Y beat ... kho thắng Z pick' vào record."""
    lib_file = tmp_path / "lib" / "walk.mp4"
    lib_file.parent.mkdir()
    lib_file.write_bytes(b"local-video")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(lib_file), category="doi-thuong", media_type="video",
        mtime=1.0, subject="man walking street", description="local man walking",
        shot_size="medium", mood="neutral", has_people=True, tags=["man", "walking"],
    ))
    project.beats = [_beat(0), _beat(1, specific=["khong khop gi ca"])]
    project.save()
    _run(project, conn, tmp_path, niche="n1")
    saved = Project.load(project.project_dir)
    lines = [w for w in saved.stages[Stage.SOURCE].warnings if "local-first (C4)" in w]
    assert len(lines) == 1
    assert "1/2 beat" in lines[0] and "kho thắng 1 pick" in lines[0]


def test_geo_gate_allows_place_agnostic(conn, tmp_path):
    """Clip ngoài cây địa lý (signature/người-già) = place-agnostic -> luôn qua dù script khác nước."""
    f = tmp_path / "eld.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path=str(f), category="signature", media_type="video", mtime=1.0,
        subject="elderly couple walking", description="old couple park",
        shot_size="medium", mood="warm", has_people=True, tags=["elderly"],
        folder_path="signature/NGHỈ HƯU/NGƯỜI GIÀ TRAVEL",
    ))
    q = SearchQueries(specific=["elderly couple walking"], broad=[], thematic=[])
    assert len(find_local_candidates(conn, "n1", q, script_text="Alaska freedom cheap land")) == 1


# ------------------- PA-1 (2026-07-07): phễu batch 1 call/chunk ----------------
class FakeBatchRankBrain:
    """NÃO giả nhận CẢ batch lẫn per-beat (đếm riêng); chấm mọi ứng viên theo bảng."""

    def __init__(self, scores=None):
        self.scores = scores or {}
        self.batch_calls = 0
        self.single_calls = 0
        self.model = "fake-batch-brain"

    def complete(self, system, user, output_model, context=None):
        from autoedit.director.client import Usage
        from autoedit.ranker.prompts import alias_of
        from autoedit.ranker.schema import (BatchRankResponse, BeatRankResponse,
                                            BeatVerdicts, CandidateVerdict)

        rev = {alias_of(k): k for k in self.scores}  # TOC-1: prompt in id ngắn

        def verdicts_for(ids):
            out = []
            for a in ids:
                k = rev.get(a, a)
                n, m = self.scores.get(k, (5, 5))
                out.append(CandidateVerdict(id=a, verdict="ok", diem_nghia=n,
                                            diem_mood=m, ly_do=f"hợp: {k}"))
            return out

        if output_model is BatchRankResponse:
            self.batch_calls += 1
            beats, cur_id, cur_ids = [], None, []
            for ln in user.splitlines():
                if "=== BEAT #" in ln:
                    if cur_id is not None:
                        beats.append(BeatVerdicts(beat_id=cur_id, verdicts=verdicts_for(cur_ids)))
                    cur_id, cur_ids = int(ln.split("#")[1].split(" ")[0]), []
                elif ". id: " in ln:
                    cur_ids.append(ln.split(". id: ")[1].strip())
            if cur_id is not None:
                beats.append(BeatVerdicts(beat_id=cur_id, verdicts=verdicts_for(cur_ids)))
            return BatchRankResponse(beats=beats), Usage(input_tokens=300, output_tokens=120)
        self.single_calls += 1
        ids = [ln.split(". id: ")[1].strip()
               for ln in user.splitlines() if ". id: " in ln]
        return BeatRankResponse(verdicts=verdicts_for(ids)), Usage(input_tokens=10, output_tokens=5)


def test_funnel_batch_one_call_and_no_repeat_in_chunk(project, conn, tmp_path):
    """PA-1: 3 beat stock cùng chương -> ĐÚNG 1 call NÃO batch; cùng 1 asset điểm cao nhất
    cho cả 3 beat -> P7 máy gác: 3 shot ra 3 asset KHÁC nhau (không tin LLM tự tránh)."""
    project.beats = [_beat(0), _beat(1), _beat(2)]
    project.save()
    brain = FakeBatchRankBrain(scores={"pexels:2": (9, 9), "pexels:3": (8, 8), "pexels:4": (7, 7)})
    _run(project, conn, tmp_path, brain=brain)

    saved = Project.load(project.project_dir)
    assert brain.batch_calls == 1 and brain.single_calls == 0   # 1 call cho cả chunk
    keys = [s.asset_key for s in saved.shots]
    assert keys[0] == "pexels:2"                    # điểm cao nhất thắng beat đầu
    assert len(set(keys)) == 3                      # P7: không beat nào lặp asset
    assert all(s.status == "ok" for s in saved.shots)
    assert len(saved.rank_log) == 3                 # kill-log per-beat giữ nguyên
    # token batch ghi 1 lần (beat đầu tiêu thụ) — tổng cost không đội
    toks = [r["input_tokens"] for r in saved.rank_log]
    assert sum(toks) == 300


def test_prenorm_writes_norm_files_toc3(project, conn, tmp_path, monkeypatch):
    """TOC-3: pick video -> file norm nằm sẵn ở media/norm/<tên> (đúng path assemble
    tìm, transcode mtime-skip ăn ngay); perf + warning tổng kết có mặt."""
    import autoedit.packager.transcode as tc

    monkeypatch.setenv("AUTOEDIT_PRENORM", "1")   # conftest tắt mặc định cho cả suite

    def fake_norm_video(src, dst, crop_16x9=True):
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(b"norm")
        return dst

    monkeypatch.setattr(tc, "normalize_video", fake_norm_video)
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, brain=FakeRankBrain())

    saved = Project.load(project.project_dir)
    name = Path(saved.shots[0].asset_path).name
    norm = Path(project.project_dir) / "media" / "norm" / name
    assert norm.is_file() and norm.read_bytes() == b"norm"
    assert not list(norm.parent.glob("part_*"))   # ghi tmp -> replace, không để rác
    rec = saved.stages[Stage.SOURCE]
    assert rec.perf.get("prenorm_n", 0) >= 1
    assert any("normalize nền" in w for w in rec.warnings)


def test_prenorm_error_fail_open_toc3(project, conn, tmp_path, monkeypatch):
    """TOC-3 fail-open: ffmpeg chết -> đếm lỗi + KHÔNG file norm + stage vẫn DONE
    (assemble tự normalize lại như cũ, không mất gì)."""
    import autoedit.packager.transcode as tc

    monkeypatch.setenv("AUTOEDIT_PRENORM", "1")

    def boom(src, dst, crop_16x9=True):
        raise RuntimeError("ffmpeg die")

    monkeypatch.setattr(tc, "normalize_video", boom)
    project.beats = [_beat(0)]
    project.save()
    _run(project, conn, tmp_path, brain=FakeRankBrain())

    saved = Project.load(project.project_dir)
    rec = saved.stages[Stage.SOURCE]
    assert rec.status == StageStatus.DONE
    assert rec.perf.get("prenorm_err", 0) >= 1
    assert not (Path(project.project_dir) / "media" / "norm" / "x").parent.exists() or \
        not list((Path(project.project_dir) / "media" / "norm").glob("*.mp4"))


def test_timed_stock_reuses_valid_dest_toc3b(tmp_path, monkeypatch):
    """TOC-3b: file đích đã nằm sẵn + ffprobe đọc được -> KHÔNG tải lại (warm-up/resume);
    file cụt (ffprobe None) -> tải lại như cũ, không bao giờ nhận file rác."""
    import autoedit.sourcer.runner as runner_mod
    from autoedit.sourcer.runner import _Perf, _TimedStock

    perf = {}
    stock = FakeStock()
    timed = _TimedStock(stock, _Perf(perf))
    dest = tmp_path / "b000_x.mp4"
    dest.write_bytes(b"warmup-da-tai")

    monkeypatch.setattr(runner_mod, "ffprobe_duration", lambda p: 5.0)
    out = timed.download({"asset_key": "pexels:1", "url": "http://x/1.mp4",
                          "media_type": "video"}, dest)
    assert out == dest and stock.downloads == []          # tái dùng, không gọi inner
    assert perf["dl_reuse"] == 1

    monkeypatch.setattr(runner_mod, "ffprobe_duration", lambda p: None)  # file cụt
    timed.download({"asset_key": "pexels:1", "url": "http://x/1.mp4",
                    "media_type": "video"}, dest)
    assert stock.downloads == ["pexels:1"]                # tải lại thật


def test_prefetch_plan_picks_top_stock_toc3b(tmp_path):
    """TOC-3b: kế hoạch warm-up = top điểm NÃO thuần/beat; bỏ local (không url),
    bỏ veto, bỏ đã-dùng; PA-3 (map {}) không đoán."""
    from autoedit.ranker.schema import CandidateVerdict
    from autoedit.sourcer.runner import _prefetch_plan, _stock_dest

    b = _beat(7)
    cands = [
        {"asset_key": "local:F:/x.mp4", "source": "local", "path": "F:/x.mp4",
         "media_type": "video", "description": "kho"},
        {"asset_key": "pexels:9", "source": "pexels", "url": "http://x/9.mp4",
         "media_type": "video", "description": "top"},
        {"asset_key": "pexels:8", "source": "pexels", "url": "http://x/8.mp4",
         "media_type": "video", "description": "nhì"},
    ]
    def v(k, n, m, verdict="ok"):
        return CandidateVerdict(id=k, verdict=verdict, diem_nghia=n, diem_mood=m,
                                ly_do="x", veto_type="" if verdict == "ok" else "khac")
    verdicts = {"local:F:/x.mp4": v("a", 10, 10),          # điểm cao nhất nhưng là local
                "pexels:9": v("b", 9, 9), "pexels:8": v("c", 5, 5)}
    gathered = {7: (cands, None)}

    plan = _prefetch_plan([b], gathered, {7: verdicts}, set(), None, tmp_path)
    assert [(c["asset_key"], d) for c, d in plan] == \
        [("pexels:9", _stock_dest(cands[1], b, tmp_path))]

    # top stock đã dùng -> lấy ứng viên kế; verdict veto không bao giờ warm-up
    verdicts["pexels:8"] = v("c", 5, 5, verdict="veto")
    plan = _prefetch_plan([b], gathered, {7: verdicts}, {"pexels:9"}, None, tmp_path)
    assert plan == []
    # PA-3 pool ≤1: map {} -> không đoán
    assert _prefetch_plan([b], gathered, {7: {}}, set(), None, tmp_path) == []


def test_dl_parallel_e2e_same_picks_toc3b(project, conn, tmp_path, monkeypatch):
    """TOC-3b bật thật (thread warm-up chạy): pick vẫn theo điểm + P7 không lặp —
    warm-up chỉ làm ấm file, không được đổi kết quả chọn."""
    import autoedit.sourcer.runner as runner_mod

    monkeypatch.setenv("AUTOEDIT_DL_PARALLEL", "4")   # conftest tắt mặc định
    # file FakeStock là bytes giả — cho ffprobe giả đọc được để nhánh tái-dùng sống
    monkeypatch.setattr(runner_mod, "ffprobe_duration",
                        lambda p: 5.0 if Path(p).is_file() else None)
    project.beats = [_beat(0), _beat(1), _beat(2)]
    project.save()
    brain = FakeBatchRankBrain(scores={"pexels:2": (9, 9), "pexels:3": (8, 8)})
    _run(project, conn, tmp_path, brain=brain)

    saved = Project.load(project.project_dir)
    keys = [s.asset_key for s in saved.shots]
    assert keys[0] == "pexels:2" and len(set(keys)) == 3
    assert all(s.status == "ok" for s in saved.shots)


def test_plan_chunks_matches_old_prefetch_rules():
    """TOC-2: chia chunk tĩnh phải Y LUẬT _prefetch_batch cũ — cùng chương, liền nhau,
    cap RANK_BATCH_SIZE, chunk 1 beat bỏ (per-beat xử)."""
    from autoedit.sourcer.runner import RANK_BATCH_SIZE, _plan_chunks

    beats = [_beat(i) for i in range(12)]                    # 12 stock cùng chương
    plan = _plan_chunks(beats)
    assert [len(c) for c in plan] == [RANK_BATCH_SIZE, 2]    # cap 10 + đuôi 2

    beats = [_beat(0), _beat(1), _beat(2, route="entity"), _beat(3), _beat(4)]
    plan = _plan_chunks(beats)                               # entity chẻ đôi
    assert [[b.beat_id for b in c] for c in plan] == [[0, 1], [3, 4]]

    beats = [_beat(0), _beat(1), _beat(2, route="entity"), _beat(3)]  # đuôi 1 beat -> bỏ
    assert [[b.beat_id for b in c] for c in _plan_chunks(beats)] == [[0, 1]]

    b_ch2 = _beat(2)
    b_ch2.chapter = 2                                        # đổi chương cũng chẻ
    assert [[b.beat_id for b in c] for c in _plan_chunks([_beat(0), _beat(1), b_ch2])] \
        == [[0, 1]]


def test_rank_lookahead_two_chunks_two_calls(project, conn, tmp_path):
    """TOC-2: 2 chương -> 2 chunk -> đúng 2 call batch (0 per-beat), pick vẫn theo điểm,
    P7 không lặp asset giữa các beat — hành vi chọn Y HỆT đường tuần tự cũ."""
    b3, b4 = _beat(3), _beat(4)
    b3.chapter = 2
    b4.chapter = 2
    project.beats = [_beat(0), _beat(1), b3, b4]
    project.save()
    brain = FakeBatchRankBrain(scores={"pexels:2": (9, 9), "pexels:3": (8, 8)})
    _run(project, conn, tmp_path, brain=brain)

    saved = Project.load(project.project_dir)
    assert brain.batch_calls == 2 and brain.single_calls == 0
    keys = [s.asset_key for s in saved.shots]
    assert keys[0] == "pexels:2" and len(set(keys)) == 4     # điểm cao thắng + không lặp
    assert all(s.status == "ok" for s in saved.shots)
    perf = saved.stages[Stage.SOURCE].perf
    assert perf["rank_calls"] == 2 and perf["rank_wait_s"] >= 0


def test_rank_lookahead_batch_error_falls_back_per_beat(project, conn, tmp_path):
    """TOC-2 giữ lưới cũ: future batch chết -> warning 'rơi về 1 call/beat' + per-beat
    gánh, không beat nào trắng."""
    class BoomBatchBrain(FakeBatchRankBrain):
        def complete(self, system, user, output_model, context=None):
            from autoedit.ranker.schema import BatchRankResponse
            if output_model is BatchRankResponse:
                self.batch_calls += 1
                raise RuntimeError("boom")
            return super().complete(system, user, output_model, context)

    project.beats = [_beat(0), _beat(1), _beat(2)]
    project.save()
    brain = BoomBatchBrain()
    _run(project, conn, tmp_path, brain=brain)
    saved = Project.load(project.project_dir)
    assert brain.batch_calls == 1 and brain.single_calls == 3
    assert all(s.status == "ok" for s in saved.shots)
    assert any("rơi về 1 call/beat" in w for w in saved.stages[Stage.SOURCE].warnings)


def test_rank_parallel_env_one_still_correct(project, conn, tmp_path, monkeypatch):
    """Knob AUTOEDIT_RANK_PARALLEL=1 (tắt lookahead khi subscription nghẽn) — kết quả
    chọn không đổi."""
    monkeypatch.setenv("AUTOEDIT_RANK_PARALLEL", "1")
    project.beats = [_beat(0), _beat(1), _beat(2)]
    project.save()
    brain = FakeBatchRankBrain(scores={"pexels:2": (9, 9)})
    _run(project, conn, tmp_path, brain=brain)
    saved = Project.load(project.project_dir)
    assert brain.batch_calls == 1
    assert saved.shots[0].asset_key == "pexels:2"
    assert len({s.asset_key for s in saved.shots}) == 3


# ----------------------- V3: video_subject tới prompt phễu --------------------
def test_funnel_receives_video_subject_from_outline(project, conn, tmp_path):
    """V3 (bài học b11 Mars-vs-Moon): outline.video_subject phải chảy tới prompt NÃO
    phễu qua run_source (wiring — họ bug 'niche rơi' C4). Project cũ không có key ->
    fail-open, các test funnel cũ (outline None) chứng minh sẵn."""
    project.beats = [_beat(0)]
    project.outline = {"video_subject": "the Moon and its far side", "chapters": []}
    project.save()
    brain = FakeRankBrain()
    _run(project, conn, tmp_path, brain=brain)
    assert brain.prompts, "NÃO phễu phải được gọi"
    assert any(
        "VIDEO SUBJECT (outer scope for entity vetoes): the Moon and its far side" in p
        for p in brain.prompts
    )


# ----------------------- C5 vision gate (C đợt 5) -----------------------------
class FakeGate:
    """Mắt C5 giả: phán theo claim (description ứng viên) -> (subject, mood); đếm call.
    Khớp chữ ký VisionGate.check — runner chỉ gọi qua _gate_check."""

    def __init__(self, verdicts=None, error=None, only_beat=None):
        self.verdicts = verdicts or {}   # claim -> (subject_match, mood_match)
        self.error = error
        self.only_beat = only_beat       # chỉ áp verdicts cho beat này (beat khác gật hết)
        self.calls: list[str] = []

    def check(self, media_path, beat, *, central_subject="", video_subject="",
              claim="", images=None):
        from autoedit.ranker.visiongate import GateVerdict

        self.calls.append(claim)
        if self.error is not None:
            raise self.error
        if self.only_beat is not None and beat.beat_id != self.only_beat:
            s, m = "yes", "yes"
        else:
            s, m = self.verdicts.get(claim, ("yes", "yes"))
        return GateVerdict(subject_match=s, mood_match=m,
                           seen=f"thấy: {claim}", reason="test")


@pytest.fixture
def gate_all_sources(monkeypatch):
    """Test HÀNH VI gate dùng pool FakeStock (source=pexels) — mở scope để soi được.
    Scope mặc định local-only (user 2026-07-10) có test riêng bên dưới."""
    monkeypatch.setattr("autoedit.sourcer.runner.GATE_SOURCES", ("pexels", "local"))

def test_c5_gate_pass_keeps_pick_and_logs(project, conn, tmp_path, gate_all_sources):
    """Gate gật -> pick y hệt không-gate; chỉ soi LEAD (1 call/beat); log action=pass."""
    project.beats = [_beat(0)]
    project.save()
    gate = FakeGate()
    _run(project, conn, tmp_path, brain=FakeRankBrain(scores={"pexels:3": (9, 8)}), gate=gate)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].asset_key == "pexels:3"           # y hệt test không-gate
    assert gate.calls == ["clip 3"]                          # đúng 1 lượt soi = lead
    vg = saved.rank_log[0]["vision_gate"]
    assert len(vg) == 1 and vg[0]["action"] == "pass"
    assert any("C5 vision gate: soi 1" in w for w in saved.stages[Stage.RANK].warnings)


def test_c5_gate_demote_swaps_to_next_ranked(project, conn, tmp_path, gate_all_sources):
    """Ca b60/b68: mắt chê chủ thể lead -> lấy ứng viên điểm kế (cũng được soi)."""
    project.beats = [_beat(0)]
    project.save()
    gate = FakeGate(verdicts={"clip 3": ("no", "yes")})
    _run(project, conn, tmp_path,
         brain=FakeRankBrain(scores={"pexels:3": (9, 9), "pexels:1": (8, 8)}), gate=gate)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].asset_key == "pexels:1"
    assert gate.calls == ["clip 3", "clip 1"]
    actions = {g["asset_key"]: g["action"] for g in saved.rank_log[0]["vision_gate"]}
    assert actions == {"pexels:3": "demote", "pexels:1": "pass"}
    assert any("C5 chê pexels:3" in w for w in saved.stages[Stage.SOURCE].warnings)
    # pexels:3 KHÔNG bị ghi sổ P7 -> beat sau vẫn dùng được (gate chê theo TỪNG beat)
    project2 = Project.load(project.project_dir)
    project2.beats = [_beat(0), _beat(1)]
    project2.save()
    gate2 = FakeGate(verdicts={"clip 3": ("no", "yes")}, only_beat=0)
    _run(project2, conn, tmp_path,
         brain=FakeRankBrain(scores={"pexels:3": (9, 9), "pexels:1": (8, 8)}), gate=gate2)
    saved2 = Project.load(project2.project_dir)
    assert saved2.shots[0].asset_key == "pexels:1"
    assert saved2.shots[1].asset_key == "pexels:3"          # beat 1 chê xong beat 2 vẫn lấy


def test_c5_gate_two_fails_keeps_best_with_warning(project, conn, tmp_path, gate_all_sources):
    """User chốt V123 §3c: chê cả 2 -> GIỮ bản điểm phễu CAO NHẤT + warning soát tay;
    budget 2 verdict/beat — ứng viên #3 không được soi thêm."""
    project.beats = [_beat(0)]
    project.save()
    gate = FakeGate(verdicts={"clip 3": ("no", "yes"), "clip 1": ("no", "yes")})
    _run(project, conn, tmp_path,
         brain=FakeRankBrain(scores={"pexels:3": (9, 9), "pexels:1": (8, 8)}), gate=gate)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].asset_key == "pexels:3"           # điểm cao nhất, KHÔNG needs_human
    assert saved.shots[0].status == "ok"
    assert gate.calls == ["clip 3", "clip 1"]                # đúng budget 2
    actions = {g["asset_key"]: g["action"] for g in saved.rank_log[0]["vision_gate"]}
    assert actions["pexels:3"] == "giu_du_nghi_sai" and actions["pexels:1"] == "demote"
    assert any("SOÁT TAY" in w for w in saved.stages[Stage.SOURCE].warnings)


def test_c5_gate_mood_no_is_warning_only(project, conn, tmp_path, gate_all_sources):
    """filter-overload-guard: mood 'no' KHÔNG đổi pick — chỉ warning cho editor."""
    project.beats = [_beat(0)]
    project.save()
    gate = FakeGate(verdicts={"clip 3": ("yes", "no")})
    _run(project, conn, tmp_path, brain=FakeRankBrain(scores={"pexels:3": (9, 8)}), gate=gate)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].asset_key == "pexels:3"           # pick nguyên
    vg = saved.rank_log[0]["vision_gate"]
    assert vg[0]["action"] == "mood_warning"
    assert any("C5 mood nghi lệch" in w for w in saved.stages[Stage.SOURCE].warnings)


def test_c5_gate_only_candidate_rejected_still_picked(project, conn, tmp_path, gate_all_sources):
    """Pool 1 ứng viên (auto-pick PA-3) bị chê -> không có ai thay: vớt lại + SOÁT TAY,
    KHÔNG rơi needs_human (gate không bao giờ làm beat trống thêm)."""
    project.beats = [_beat(0)]
    project.save()
    stock = FakeStock([{"asset_key": "pexels:9", "url": "http://x/9.mp4",
                        "media_type": "video", "duration": 10.0,
                        "description": "clip 9", "source": "pexels"}])
    gate = FakeGate(verdicts={"clip 9": ("no", "yes")})
    _run(project, conn, tmp_path, stock=stock, brain=FakeRankBrain(), gate=gate)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].status == "ok" and saved.shots[0].asset_key == "pexels:9"
    vg = saved.rank_log[0]["vision_gate"]
    assert vg[0]["action"] == "giu_du_nghi_sai"
    assert any("không còn ứng viên thay" in w for w in saved.stages[Stage.SOURCE].warnings)


def test_c5_gate_fail_open_and_disable_after_3_errors(project, conn, tmp_path, gate_all_sources):
    """GLM lỗi -> nhận pick không soi (fail-open); lỗi thứ 3 TẮT gate cả run —
    các beat sau không call nữa (GLM sập không kéo lê cả video)."""
    project.beats = [_beat(i) for i in range(5)]
    project.save()
    gate = FakeGate(error=RuntimeError("GLM sập"))
    _run(project, conn, tmp_path, brain=FakeRankBrain(), gate=gate)
    saved = Project.load(project.project_dir)
    assert all(s.status == "ok" for s in saved.shots)        # hành vi cũ nguyên vẹn
    assert len(gate.calls) == 3                               # tắt sau lỗi thứ 3
    assert any("C5 gate TẮT sau 3 lỗi" in w for w in saved.stages[Stage.SOURCE].warnings)
    assert all(not r["vision_gate"] for r in saved.rank_log)  # không verdict nào ghi log


def test_c5_gate_error_streak_resets_on_success(project, conn, tmp_path, gate_all_sources):
    """V11 lần 1 chết oan vì đếm lỗi TỔNG: 3 hắt hơi thoáng qua tắt gate 92 beat sau.
    Luật mới: 3 lỗi LIÊN TIẾP mới tắt — xen kẽ thành công thì reset, gate sống cả run."""

    class FlakyGate(FakeGate):
        def __init__(self, error_beats):
            super().__init__()
            self.error_beats = set(error_beats)

        def check(self, media_path, beat, **kw):
            if beat.beat_id in self.error_beats:
                self.calls.append(f"err:{beat.beat_id}")
                raise RuntimeError("GLM hắt hơi")
            return super().check(media_path, beat, **kw)

    # 5 beat = vừa khít pool FakeStock 5 ứng viên (P7 mỗi beat ăn 1 — beat 6 sẽ trống pool)
    project.beats = [_beat(i) for i in range(5)]
    project.save()
    gate = FlakyGate(error_beats={0, 1, 3})  # streak tối đa 2 — không bao giờ chạm 3
    _run(project, conn, tmp_path, brain=FakeRankBrain(), gate=gate)
    saved = Project.load(project.project_dir)
    assert len(gate.calls) == 5                              # gate SỐNG cả run, không tắt
    assert not any("C5 gate TẮT" in w for w in saved.stages[Stage.SOURCE].warnings)
    soi = [g for r in saved.rank_log for g in r["vision_gate"]]
    assert len(soi) == 2                                     # beat 2 + beat 4 soi được
    assert any("lỗi fail-open 3" in w for w in saved.stages[Stage.RANK].warnings)


def test_c5_gate_default_scope_skips_stock_picks(project, conn, tmp_path):
    """User chốt 2026-07-10 (đo tốc độ V11): mặc định gate CHỈ soi pick KHO LOCAL —
    pick Pexels đi thẳng, 0 call vision (~60 call + ~10 phút/video tiết kiệm)."""
    project.beats = [_beat(0)]
    project.save()
    gate = FakeGate(verdicts={"clip 3": ("no", "yes")})   # bảng có chê clip 3...
    _run(project, conn, tmp_path, brain=FakeRankBrain(scores={"pexels:3": (9, 8)}), gate=gate)
    saved = Project.load(project.project_dir)
    assert saved.shots[0].asset_key == "pexels:3"          # ...pick pexels vẫn đi thẳng
    assert gate.calls == []                                 # 0 lượt soi
    assert all(not r["vision_gate"] for r in saved.rank_log)


# ----------------------------- BOOST sở thích khán giả (user 2026-07-17) ------
def test_parse_boosts_scope_default_dedupe_and_unknown_scope():
    """'X' mặc định @all; @hook/@ch<N> giữ nguyên (không phân hoa-thường); scope lạ
    -> all + WARNING (không im lặng bỏ); từ chuyển động C6 strip; trùng khai khử."""
    from autoedit.project import StageRecord
    from autoedit.sourcer.runner import _parse_boosts

    rec = StageRecord.running()
    out = _parse_boosts(
        ["beautiful woman", "aurora@hook", "Lion@CH3", "woman floating@xyz",
         "beautiful woman", "  "], rec)
    assert out == [("beautiful woman", "all"), ("aurora", "hook"),
                   ("lion", "ch3"), ("woman", "all")]
    assert any("scope 'xyz' lạ" in w for w in rec.warnings)


def test_boost_terms_for_scope_per_beat():
    from autoedit.sourcer.runner import _boost_terms_for

    specs = [("woman", "all"), ("aurora", "hook"), ("lion", "ch3")]
    assert _boost_terms_for(specs, chapter=1, hook_ch=1) == ("woman", "aurora")
    assert _boost_terms_for(specs, chapter=3, hook_ch=1) == ("woman", "lion")
    assert _boost_terms_for(specs, chapter=2, hook_ch=1) == ("woman",)
    assert _boost_terms_for([], chapter=1, hook_ch=1) == ()


def test_find_boost_candidates_geo_gate_and_used_before_limit(conn, tmp_path):
    """BOOST chèn CHỈ KHO + 3 cửa như find_local/find_ref (P5 đã rà): geo-gate PA2
    chặn X sai quốc gia (vết bug 'video Hà Nội ra cảnh Hà Giang'); loại đã-dùng
    TRƯỚC limit (vết DS3-084); tags lên ứng viên (chống vết PB7 cột-rơi)."""
    from autoedit.sourcer.local import find_boost_candidates

    def _seed(name, subject, folder=""):
        f = tmp_path / name
        f.write_bytes(b"v")
        db.upsert_asset(conn, db.AssetRecord(
            niche="lifein", path=str(f), category="nap", folder_path=folder,
            media_type="video", mtime=1.0, subject=subject, description="d",
            shot_size="medium", mood="calm", has_people=True,
            tags=["woman", "street"], duration=6.0))
        return str(f)

    p_fr = _seed("fr.mp4", "elegant woman walking",
                 "Khu Vực Europe (English)/FRANCE/paris")
    p_jp = _seed("jp.mp4", "elegant woman walking",
                 "Khu Vực Asia (English)/JAPAN/tokyo")
    p_any = _seed("any.mp4", "woman crossing street")  # phi-địa-lý -> luôn qua geo
    script = "Life in France, the streets of Paris"
    out = find_boost_candidates(conn, "lifein", ("woman",), script_text=script)
    paths = {c["path"] for c in out}
    assert p_fr in paths and p_any in paths
    assert p_jp not in paths                       # geo-gate PA2 chặn sai nước
    assert all(c.get("tags") for c in out)         # tags mang theo ứng viên
    out2 = find_boost_candidates(conn, "lifein", ("woman",), script_text=script,
                                 used_keys={f"local:{p_fr}"})
    assert p_fr not in {c["path"] for c in out2}   # P7 lọc TRƯỚC limit
    assert find_boost_candidates(conn, "lifein", ()) == []


def test_gather_marks_is_boost_chokepoint_kho_only(conn, tmp_path):
    """BOOST glue: nhãn is_boost gắn tại chokepoint SAU dedup — ứng viên vào bằng
    đường local AND-match vẫn ăn nhãn (gắn trên bản chèn thì RƠI theo dedup — vết
    PB7/REF); Pexels match chữ X KHÔNG ăn (kho phải đè Pexels — user chốt);
    _diem_may cộng đúng BOOST_BONUS và CỘNG DỒN với REF_BONUS."""
    from autoedit.ranker.funnel import BOOST_BONUS, REF_BONUS, _diem_may
    from autoedit.sourcer.runner import _gather_candidates

    f = tmp_path / "womanstreet.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="space", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="man walking street", description="d", shot_size="medium",
        mood="calm", has_people=True, tags=["woman", "street"], duration=6.0))
    stock = FakeStock([{"asset_key": "pexels:9", "url": "http://x/9.mp4",
                        "media_type": "video", "duration": 10.0,
                        "description": "beautiful woman street", "source": "pexels"}])
    # query beat 'man walking street' AND-match -> asset vào pool bằng đường LOCAL,
    # bản chèn boost bị dedup gạt — nhãn phải sống nhờ chokepoint
    cands, _ = _gather_candidates(_beat(0), conn, stock, "space", set(),
                                  signature_first=False, boost_terms=("woman",))
    local = next(c for c in cands if c["asset_key"] == f"local:{f}")
    pex = next(c for c in cands if c["asset_key"] == "pexels:9")
    assert local.get("is_boost") is True
    assert not pex.get("is_boost")
    base = {k: v for k, v in local.items() if k != "is_boost"}
    assert _diem_may(local, 5.0, "", 1) - _diem_may(base, 5.0, "", 1) \
        == pytest.approx(BOOST_BONUS)
    assert _diem_may(dict(local, is_ref=True), 5.0, "", 1) - _diem_may(base, 5.0, "", 1) \
        == pytest.approx(BOOST_BONUS + REF_BONUS)   # cộng dồn REF (user chấp nhận P5)


def test_gather_boost_injects_when_queries_miss(conn, tmp_path):
    """BOOST chèn: beat query trượt kho (AND-match 0 khớp) nhưng kho có cảnh X ->
    vẫn vào pool qua đường chèn — đúng kịch bản 'đoạn khó kiếm footage' của editor
    thật. Không khai boost -> không chèn (đối chứng)."""
    from autoedit.sourcer.runner import _gather_candidates

    f = tmp_path / "woman2.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="space", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="elegant woman paris cafe", description="d",
        shot_size="medium", mood="calm", has_people=True, tags=["woman"],
        duration=6.0))
    cands, _ = _gather_candidates(_beat(0, specific=["quantum blueprints"]), conn,
                                  FakeStock(), "space", set(),
                                  signature_first=False, boost_terms=("woman",))
    assert any(c["asset_key"] == f"local:{f}" and c.get("is_boost") for c in cands)
    cands2, _ = _gather_candidates(_beat(1, specific=["quantum blueprints"]), conn,
                                   FakeStock(), "space", set(), signature_first=False)
    assert not any(c["asset_key"] == f"local:{f}" for c in cands2)


def test_boost_inject_respects_ledger_gate(conn, tmp_path):
    """Chèn ≠ miễn pháp lý (cùng luật chèn REF): ứng viên viral vượt trần 8% bị
    ledger.gate chặn ngay ở đường chèn boost."""
    from autoedit.sourcer.runner import _gather_candidates
    from autoedit.sourcer.viral import ViralLedger

    f = tmp_path / "viralwoman.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="space", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="woman dancing", description="d", shot_size="medium",
        mood="calm", has_people=True, tags=["woman"], duration=50.0,
        source_video="F:/VIRAL/x.mp4", scene_index=1, source_class="viral",
        source_duration=100.0))   # 50s > trần 8% của nguồn 100s
    cands, _ = _gather_candidates(_beat(0, specific=["quantum blueprints"]), conn,
                                  FakeStock(), "space", set(),
                                  signature_first=False, ledger=ViralLedger(),
                                  boost_terms=("woman",))
    assert not any(c["asset_key"] == f"local:{f}" for c in cands)


def test_source_stock_heuristic_pick_carries_boost_hit(conn, tmp_path):
    """Đường heuristic (không NÃO): chèn boost vẫn ăn + pick mang boost_hit ->
    tầng ĐO đếm được từ project.json."""
    from autoedit.project import StageRecord
    from autoedit.sourcer.runner import _source_stock

    f = tmp_path / "woman3.mp4"
    f.write_bytes(b"v")
    db.upsert_asset(conn, db.AssetRecord(
        niche="space", path=str(f), category="nap", media_type="video",
        mtime=1.0, subject="elegant woman cafe", description="d",
        shot_size="medium", mood="calm", has_people=True, tags=["woman"],
        duration=6.0))
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    pick = _source_stock(_beat(0, specific=["quantum blueprints"]), conn,
                         FakeStock([]), "space", set(), "", assets_dir, tmp_path,
                         StageRecord.running(), boost_terms=("woman",))
    assert pick.status == "ok" and pick.asset_key == f"local:{f}"
    assert pick.boost_hit is True


def test_floor_pick_prefers_boost_match(conn, tmp_path):
    """SÀN NICHE + BOOST: sàn = đúng nghĩa đen 'đoạn không kiếm được footage' —
    cảnh X thắng cả ưu-tiên-không-người (sort X là khóa chính); pick mang boost_hit.
    Đối chứng: không khai boost -> hành vi cũ (không-người thắng)."""
    from autoedit.project import StageRecord
    from autoedit.sourcer.runner import _floor_pick

    def _seed(name, subject, has_people, tags):
        f = tmp_path / name
        f.write_bytes(b"v")
        db.upsert_asset(conn, db.AssetRecord(
            niche="lifein", path=str(f), category="nap", media_type="video",
            mtime=1.0, subject=subject, description="d", shot_size="medium",
            mood="calm", has_people=has_people, tags=tags, duration=6.0))
        return str(f)

    p_plain = _seed("plain.mp4", "quiet street rain", False, [])
    p_woman = _seed("woman4.mp4", "woman walking street", True, ["woman"])
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    pick = _floor_pick(_beat(0, specific=["street"]), conn, "lifein", set(), "",
                       FakeStock([]), assets_dir, tmp_path, StageRecord.running(),
                       boost_terms=("woman",))
    assert pick is not None and pick.asset_key == f"local:{p_woman}"
    assert pick.boost_hit is True
    pick2 = _floor_pick(_beat(1, specific=["street"]), conn, "lifein", set(), "",
                        FakeStock([]), assets_dir, tmp_path, StageRecord.running())
    assert pick2 is not None and pick2.asset_key == f"local:{p_plain}"
    assert pick2.boost_hit is False


def test_audience_bias_loaded_todo_filtered_fail_open(tmp_path):
    """audience_bias (niche_profile.yaml, field Stage-4 nay mới nối dây): đọc được,
    lọc dòng TODO scaffold; thiếu profile/niche -> [] fail-open (không giết stage)."""
    from autoedit.library.profile import NicheProfile
    from autoedit.sourcer.runner import _audience_bias

    d = tmp_path / "lifein"
    d.mkdir()
    NicheProfile(niche="lifein",
                 audience_bias=["beautiful woman", "TODO: điền sau"]).save(d)
    assert _audience_bias("lifein", tmp_path) == ["beautiful woman"]
    assert _audience_bias("khongco", tmp_path) == []
    assert _audience_bias("", tmp_path) == []


def test_phieu_c5_loi_thi_roi_ve_heuristic_khong_giet_stage():
    """02/09: GLM trả verdicts[7] rỗng -> hỏng 1 lượt chấm -> CHẾT cả job sau 8 phút,
    mất luôn 19 beat đã chấm xong. Một beat hỏng chỉ được mất beat đó."""
    import inspect

    from autoedit.sourcer import runner

    src = inspect.getsource(runner._source_stock)
    i = src.index("_pick_by_funnel(")
    truoc = src[:i]
    assert "try:" in truoc, "_pick_by_funnel phải nằm trong try — LLM lỗi là chết stage"
    sau = src[i:]
    assert "except (ValueError, RuntimeError)" in sau
    assert "heuristic" in sau.lower(), "phải nói rõ beat nào rơi về heuristic"
