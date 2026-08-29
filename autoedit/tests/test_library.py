"""Test thư viện niche (M3.5 + PB2) — db/profile/indexer với FakeTagger, không API/ffmpeg."""

from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from autoedit.library import db
from autoedit.library.indexer import index_niche
from autoedit.library.profile import NicheProfile, init_niche
from autoedit.library.vision import (
    AssetTags,
    GLMVisionTagger,
    measure_colors,
    media_type_of,
)


# ----------------------------- profile ---------------------------------------
def test_init_niche_scaffold_and_profile_roundtrip(tmp_path):
    d = init_niche("retirement-abroad", root=tmp_path)
    assert (d / "signature").is_dir() and (d / "entity").is_dir()
    profile = NicheProfile.load(d)
    assert profile.niche == "retirement-abroad"

    profile.safe_pool = ["retirement abroad", "expat lifestyle"]
    profile.save(d)
    assert NicheProfile.load(d).safe_pool == ["retirement abroad", "expat lifestyle"]


def test_init_niche_does_not_overwrite_profile(tmp_path):
    d = init_niche("n1", root=tmp_path)
    p = NicheProfile.load(d)
    p.banned = ["alcohol"]
    p.save(d)
    init_niche("n1", root=tmp_path)  # chạy lại không được đè
    assert NicheProfile.load(d).banned == ["alcohol"]


# ----------------------------- db --------------------------------------------
@pytest.fixture
def conn(tmp_path):
    return db.connect(tmp_path / "cache.db")


def _rec(path: str, **kw) -> db.AssetRecord:
    return db.AssetRecord(
        niche=kw.get("niche", "n1"), path=path, category=kw.get("category", "signature"),
        media_type="video", mtime=kw.get("mtime", 1.0),
        subject=kw.get("subject", "old couple beach"),
        description=kw.get("description", "elderly couple walking on a sunny beach"),
        shot_size="wide", mood=kw.get("mood", "warm"),
        scene_type=kw.get("scene_type", "nature_water"),
        has_people=True, tags=kw.get("tags", ["beach", "retirement", "couple"]),
    )


def test_search_returns_matching_file(conn):
    db.upsert_asset(conn, _rec("/lib/a.mp4"))
    db.upsert_asset(conn, _rec("/lib/b.mp4", subject="city traffic night",
                               description="busy street at night", tags=["city", "night"]))
    rows = db.search_assets(conn, "n1", "beach couple")
    assert [r["path"] for r in rows] == ["/lib/a.mp4"]
    # AND logic: từ không khớp -> rỗng
    assert db.search_assets(conn, "n1", "beach night") == []
    # khác niche -> rỗng
    assert db.search_assets(conn, "n2", "beach") == []


def test_upsert_updates_by_path(conn):
    db.upsert_asset(conn, _rec("/lib/a.mp4", mtime=1.0))
    db.upsert_asset(conn, _rec("/lib/a.mp4", mtime=2.0, subject="updated subject"))
    assert db.count_assets(conn, "n1") == 1
    assert db.search_assets(conn, "n1", "updated")[0]["mtime"] == 2.0


def test_needs_index_by_mtime(conn):
    assert db.needs_index(conn, "/lib/x.mp4", 1.0)  # chưa có
    db.upsert_asset(conn, _rec("/lib/x.mp4", mtime=1.0))
    assert not db.needs_index(conn, "/lib/x.mp4", 1.0)  # không đổi
    assert db.needs_index(conn, "/lib/x.mp4", 99.0)     # file đổi


def test_vocab_for_niche_counts_and_empty(conn):
    """C4: từ vựng kho — đếm scene_type/tags/từ subject (lowercase, bỏ stopword);
    kho rỗng -> total=0 (live.py sẽ bỏ khối, fail-open)."""
    db.upsert_asset(conn, _rec("/lib/g1.mp4", subject="Spiral Galaxy in the night",
                               tags=["space", "Stars"], scene_type="space"))
    db.upsert_asset(conn, _rec("/lib/g2.mp4", subject="galaxy cluster",
                               tags=["space", "cosmos"], scene_type="space"))
    v = db.vocab_for_niche(conn, "n1")
    assert v["total"] == 2 and v["videos"] == 2 and v["images"] == 0
    assert ("space", 2) in v["scene_types"]
    tags = dict(v["tags"])
    assert tags["space"] == 2 and tags["stars"] == 1     # tag hạ lowercase để gộp đếm
    subj = dict(v["subject_words"])
    assert subj["galaxy"] == 2 and "in" not in subj and "the" not in subj  # bỏ stopword
    assert db.vocab_for_niche(conn, "niche-khong-co")["total"] == 0


def test_tag_instruction_no_guess_and_source_title():
    """2a+2b (§C6-DIEU-TRA): luật không-đoán-thiên-thể LUÔN có; block tiêu đề nguồn
    chỉ xuất hiện khi có source_title (GLM từng tag Pluto = 'moon' từ 1 frame tĩnh)."""
    from autoedit.library.vision import _tag_instruction

    base = _tag_instruction("video", "", want_angle=False)
    assert "guessing a name" in base                 # 2b luôn bật
    assert "source video titled" not in base         # không title -> không block 2a
    t = _tag_instruction("video", "", want_angle=False, source_title="NASA - PLUTO")
    assert '"NASA - PLUTO"' in t and "do NOT tag a DIFFERENT specific one" in t


def test_tag_instruction_section_hint_and_topic():
    """ytref §3i-2/§3i-3: block chapter + block --topic cùng bậc tin cậy source_title;
    không hint -> prompt Y CŨ (mọi đường nạp khác không đổi hành vi)."""
    from autoedit.library.vision import _tag_instruction

    t = _tag_instruction("video", "", want_angle=False, source_title="X",
                         section_hint="The Cube", topic="the Moon, lunar exploration")
    assert 'chapter titled: "The Cube"' in t
    assert 'is about: "the Moon, lunar exploration"' in t
    old = _tag_instruction("video", "", want_angle=False, source_title="X")
    assert "chapter titled" not in old and "batch of source footage" not in old
    # hint rỗng = chuỗi y hệt trước ytref (regression 2 tầng prompt)
    assert _tag_instruction("video", "", False, "X", "", "") == old


# ----------------------------- indexer ---------------------------------------
class FakeTagger:
    def __init__(self):
        self.calls: list[str] = []
        self.contexts: list[str] = []  # folder_context nhận được mỗi lần tag
        self.source_titles: list[str] = []  # 2a: tiêu đề video nguồn nhận được
        self.section_hints: list[str] = []  # ytref §3i-2: chapter nhận được
        self.topics: list[str] = []         # ytref §3i-3: --topic nhận được

    def tag(self, media_path: Path, folder_context: str = "",
            images: list[bytes] | None = None, source_title: str = "",
            section_hint: str = "", topic: str = "") -> AssetTags:
        self.calls.append(media_path.name)
        self.contexts.append(folder_context)
        self.source_titles.append(source_title)
        self.section_hints.append(section_hint)
        self.topics.append(topic)
        if "broken" in media_path.name:
            raise RuntimeError("decode error")
        return AssetTags(
            subject=f"subject {media_path.stem}", description=f"desc {media_path.stem}",
            shot_size="medium", scene_type="urban_street", mood=["peaceful", "dreamy"],
            has_people=False, tags=[media_path.stem, "fake"],
        )


def _make_niche(tmp_path) -> Path:
    d = init_niche("n1", root=tmp_path)
    (d / "signature" / "sig1.mp4").write_bytes(b"v")
    (d / "vietnam").mkdir()
    (d / "vietnam" / "hanoi.jpg").write_bytes(b"i")
    (d / "vietnam" / "broken.mp4").write_bytes(b"x")
    (d / "entity" / "trump.jpg").write_bytes(b"e")     # phải bị bỏ qua
    (d / "niche_profile.yaml").touch(exist_ok=True)    # đã có từ init
    (d / "README.txt").write_text("not media")          # không phải media
    return d


def test_index_niche_tags_and_skips(tmp_path, conn):
    d = _make_niche(tmp_path)
    tagger = FakeTagger()
    result = index_niche(conn, "n1", d, tagger)

    assert sorted(Path(p).name for p in result.indexed) == ["hanoi.jpg", "sig1.mp4"]
    assert [Path(p).name for p, _ in result.failed] == ["broken.mp4"]
    assert "trump.jpg" not in tagger.calls  # entity/ bỏ qua
    # bài kiểm tra M3.5: search tag trả về đúng file
    rows = db.search_assets(conn, "n1", "hanoi")
    assert len(rows) == 1 and rows[0]["path"].endswith("hanoi.jpg")
    assert rows[0]["category"] == "vietnam"

    # re-index: file không đổi -> skip hết, không gọi vision
    tagger2 = FakeTagger()
    result2 = index_niche(conn, "n1", d, tagger2)
    assert result2.indexed == [] and result2.skipped == 2
    assert tagger2.calls == ["broken.mp4"]  # chỉ file lỗi (chưa vào db) bị thử lại


def test_index_detects_moved_files_without_retagging(tmp_path, conn):
    """Đổi tên folder/cut file: giữ tag vision (không tốn tiền), cập nhật path+category."""
    import os
    import shutil

    d = init_niche("n1", root=tmp_path)
    src = d / "Việt Nam"
    src.mkdir()
    (src / "hanoi.mp4").write_bytes(b"v")
    index_niche(conn, "n1", d, FakeTagger())
    old = db.search_assets(conn, "n1", "hanoi")[0]
    assert old["category"] == "Việt Nam"

    # đổi tên folder có dấu -> ascii, giữ nguyên mtime (như mv thật)
    dst = d / "vietnam"
    mt = (src / "hanoi.mp4").stat().st_mtime
    shutil.move(str(src), str(dst))
    os.utime(dst / "hanoi.mp4", (mt, mt))

    tagger = FakeTagger()
    result = index_niche(conn, "n1", d, tagger)
    assert result.moved == 1 and result.pruned == 0
    assert tagger.calls == []  # không gọi vision lại
    row = db.search_assets(conn, "n1", "hanoi")[0]
    assert row["category"] == "vietnam" and Path(row["path"]).name == "hanoi.mp4"
    assert Path(row["path"]).parent.name == "vietnam"  # đã đổi sang folder mới
    assert db.count_assets(conn, "n1") == 1  # không nhân đôi


def test_deep_folder_becomes_searchable_tag(tmp_path, conn):
    """Folder sâu (editor đặt tên) -> full folder_path lưu + tìm được + đưa vào vision."""
    d = init_niche("n1", root=tmp_path)
    deep = d / "Khu Vực Châu Á (Asia)" / "CAMBODIA" / "KHU TƯ TRỊ CAMBODIA"
    deep.mkdir(parents=True)
    (deep / "0710 (1)-12.mp4").write_bytes(b"v")

    tagger = FakeTagger()
    index_niche(conn, "n1", d, tagger)

    # vision nhận context folder người-đọc-được (bắc cầu ngôn ngữ địa danh)
    assert tagger.contexts == ["Khu Vực Châu Á (Asia) / CAMBODIA / KHU TƯ TRỊ CAMBODIA"]

    # tìm bằng tên folder sâu (dù file đặt tên vô nghĩa '0710 (1)-12')
    rows = db.search_assets(conn, "n1", "cambodia")
    assert len(rows) == 1
    assert rows[0]["category"] == "Khu Vực Châu Á (Asia)"        # cấp 1 (tương thích cũ)
    assert "KHU TƯ TRỊ CAMBODIA" in rows[0]["folder_path"]       # full path lưu
    # tìm bằng cụm sâu nhất cũng ra
    assert len(db.search_assets(conn, "n1", "tư trị")) == 1


def test_index_limit_stops_and_skips_prune(tmp_path, conn):
    """--limit: dừng sau N tag mới, KHÔNG prune (chạy thử/giới hạn ngân sách)."""
    d = init_niche("n1", root=tmp_path)
    for i in range(5):
        (d / "signature" / f"clip{i}.mp4").write_bytes(b"v")
    result = index_niche(conn, "n1", d, FakeTagger(), limit=2)
    assert len(result.indexed) == 2 and result.pruned == 0
    assert db.count_assets(conn, "n1") == 2
    # chạy tiếp không limit -> tag nốt phần còn lại (resume)
    result2 = index_niche(conn, "n1", d, FakeTagger())
    assert len(result2.indexed) == 3 and result2.skipped == 2
    assert db.count_assets(conn, "n1") == 5


def test_index_prunes_deleted_files(tmp_path, conn):
    d = init_niche("n1", root=tmp_path)
    (d / "signature" / "a.mp4").write_bytes(b"v")
    index_niche(conn, "n1", d, FakeTagger())
    assert db.count_assets(conn, "n1") == 1

    (d / "signature" / "a.mp4").unlink()
    result = index_niche(conn, "n1", d, FakeTagger())
    assert result.pruned == 1
    assert db.count_assets(conn, "n1") == 0


def test_media_type_of():
    assert media_type_of(Path("a.mp4")) == "video"
    assert media_type_of(Path("a.JPG")) == "image"
    assert media_type_of(Path("a.txt")) is None


def test_image_to_jpeg_downscales_large(tmp_path):
    """Ảnh lớn -> thu nhỏ ≤1280 + ra JPEG (tránh vượt trần 10MB API)."""
    from PIL import Image

    from autoedit.library.vision import image_to_jpeg

    big = tmp_path / "huge.png"
    Image.new("RGB", (5000, 3000), (120, 80, 40)).save(big)
    out = image_to_jpeg(big)
    assert out[:2] == b"\xff\xd8"          # magic bytes JPEG
    assert len(out) < 2_000_000            # nhỏ hơn nhiều so với 10MB
    from io import BytesIO
    w, h = Image.open(BytesIO(out)).size
    assert max(w, h) == 1280               # cạnh dài đã co về 1280


def test_image_to_jpeg_handles_mislabeled_and_alpha(tmp_path):
    """Ảnh RGBA (alpha) vẫn ra JPEG hợp lệ (PIL convert RGB)."""
    from io import BytesIO

    from PIL import Image

    from autoedit.library.vision import image_to_jpeg

    p = tmp_path / "rgba.png"
    Image.new("RGBA", (300, 200), (10, 20, 30, 128)).save(p)
    out = image_to_jpeg(p)
    assert Image.open(BytesIO(out)).mode == "RGB"


# ------------------- PB2: schema tag GLM (spec MO_TA_VAN_HANH_TAG_GLM) --------
def _tags(**kw) -> AssetTags:
    base = dict(subject="s", description="d", shot_size="wide",
                scene_type="nature_water", mood=["peaceful"],
                has_people=False, tags=["x"])
    return AssetTags(**(base | kw))


def test_asset_tags_mood_vocab_and_defaults():
    """mood BẮT BUỘC nằm trong vocabulary 19 từ của nhạc (chuẩn hóa lowercase);
    camera_angle mặc định unknown (chỉ tag ở mẻ thử)."""
    t = _tags(mood=[" Peaceful ", "dreamy"])
    assert t.mood == ["peaceful", "dreamy"]
    assert t.camera_angle == "unknown"
    # PB4: từ ngoài vocab nhưng có trong _MOOD_SYNONYMS nhạc -> phiên dịch, không bác
    assert _tags(mood=["appetizing"]).mood == ["happy"]
    assert _tags(mood=["warm", "cozy"]).mood == ["hopeful", "nostalgic"]
    assert _tags(mood=["peaceful", "calm"]).mood == ["peaceful"]  # dịch trùng -> dedup
    # Mẻ deepsea 2026-07-13: 12 từ tài liệu biển sâu vào map (educational/creepy áp đảo)
    assert _tags(mood=["educational", "creepy"]).mood == ["serious", "dark"]
    assert _tags(mood=["scientific"]).mood == ["serious"]
    # Mẻ life-in 2026-07-15: 21 từ documentary quốc gia/văn hóa (104/770 cảnh mẻ 1 fail)
    assert _tags(mood=["spiritual", "lively"]).mood == ["peaceful", "playful"]
    assert _tags(mood=["traditional", "cultural"]).mood == ["nostalgic"]  # dịch trùng
    assert _tags(mood=["opulent", "luxurious"]).mood == ["epic"]
    assert _tags(mood=["everyday"]).mood == ["peaceful"]
    assert _tags(mood=["busy", "vibrant"]).mood == ["playful"]
    # Mẻ 4 life-in: đuôi từ lạ vô hạn → từ lạ bị BỎ khi còn ≥1 mood hợp lệ
    # (1 từ lạ đánh rớt cả asset = asset vô hình với phễu); lạ toàn bộ vẫn bác
    assert _tags(mood=["peaceful", "craftsman"]).mood == ["peaceful"]
    assert _tags(mood=["desolate", "community"]).mood == ["dark"]  # desolate map được (sorted[0])
    with pytest.raises(ValidationError):
        _tags(mood=["flamboyant"])         # ngoài vocab + ngoài map -> retry ở tagger
    with pytest.raises(ValidationError):
        _tags(mood=[])                     # phải có ≥1
    with pytest.raises(ValidationError):
        _tags(mood=["peaceful", "dreamy", "epic"])  # tối đa 2
    with pytest.raises(ValidationError):
        _tags(scene_type="beach")          # scene_type ngoài enum 14 giá trị


def _jpg(rgb: tuple[int, int, int]) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (64, 64), rgb).save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def test_measure_colors_solid_frames():
    """Đo màu code thuần (b1 C2b, 0 token): đỏ tươi vs xám tối."""
    hexc, bright, sat = measure_colors([_jpg((255, 0, 0))])
    r, g, b = int(hexc[1:3], 16), int(hexc[3:5], 16), int(hexc[5:7], 16)
    assert r > 240 and g < 15 and b < 15   # JPEG lệch nhẹ cho phép
    assert bright > 0.9 and sat > 0.9
    _, bright2, sat2 = measure_colors([_jpg((40, 40, 40))])
    assert bright2 < 0.25 and sat2 < 0.1
    with pytest.raises(ValueError):
        measure_colors([])


class StubGLM(GLMVisionTagger):
    """GLM tagger với HTTP stub — test parse/retry không mạng."""

    def __init__(self, responses: list):
        super().__init__(api_key="test-key")
        self._responses = list(responses)
        self.posts = 0
        self.bodies: list[dict] = []

    def _post(self, body: dict) -> dict:
        self.posts += 1
        # snapshot: tagger MUTATE body giữa các attempt (feedback-retry PB4)
        self.bodies.append(json.loads(json.dumps(body)))
        r = self._responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


_VALID_TAG = {"subject": "s", "description": "d", "shot_size": "wide",
              "scene_type": "urban_street", "mood": ["peaceful"],
              "camera_angle": "unknown", "has_people": False, "tags": ["x"]}


def _glm_resp(content: str) -> dict:
    return {"choices": [{"message": {"content": content}}]}


def test_glm_tagger_parses_fenced_json():
    """GLM hay bọc code fence — _clean_json phải gỡ được, 1 call đủ."""
    fenced = "```json\n" + json.dumps(_VALID_TAG) + "\n```"
    t = StubGLM([_glm_resp(fenced)])
    tags = t.tag(Path("x.mp4"), images=[b"jpegbytes"])
    assert tags.scene_type == "urban_street" and tags.mood == ["peaceful"]
    assert t.posts == 1


def test_glm_tagger_retries_empty_then_ok(monkeypatch):
    """Content rỗng (bẫy thinking) -> retry, lần 2 ok."""
    monkeypatch.setattr("autoedit.library.vision.time.sleep", lambda s: None)
    t = StubGLM([_glm_resp(""), _glm_resp(json.dumps(_VALID_TAG))])
    tags = t.tag(Path("x.mp4"), images=[b"jpegbytes"])
    assert t.posts == 2 and tags.subject == "s"


def test_glm_tagger_schema_echo_retries_and_prompt_hardened(monkeypatch):
    """Bug PB3: GLM thỉnh thoảng CHÉP NGUYÊN SCHEMA thay vì instance (ngẫu nhiên theo
    call dù temperature=0). Retry phải cứu được + prompt phải giữ 2 lớp chống echo."""
    monkeypatch.setattr("autoedit.library.vision.time.sleep", lambda s: None)
    echo = json.dumps(AssetTags.model_json_schema(), ensure_ascii=False)
    t = StubGLM([_glm_resp(echo), _glm_resp(json.dumps(_VALID_TAG))])
    tags = t.tag(Path("x.mp4"), images=[b"jpegbytes"])
    assert t.posts == 2 and tags.subject == "s"
    system = t.bodies[0]["messages"][0]["content"]
    user_text = t.bodies[0]["messages"][1]["content"][-1]["text"]
    assert "sunset beach" in system            # lớp 1: example instance trong system
    assert "Do NOT output the schema" in user_text  # lớp 2: user text chống echo


def test_glm_tagger_feedback_retry_on_validation_error(monkeypatch):
    """Bug PB4: model 'khăng khăng' giá trị ngoài enum (mood 'appetizing' clip đồ ăn)
    -> retry mù fail đủ 4 lần. Lượt retry phải NHÉT LỖI validation vào prompt để
    model tự sửa; lỗi mạng thường thì KHÔNG nhét gì."""
    monkeypatch.setattr("autoedit.library.vision.time.sleep", lambda s: None)
    bad = json.dumps(_VALID_TAG | {"mood": ["flamboyant"]})  # ngoài vocab + ngoài map
    t = StubGLM([_glm_resp(bad), _glm_resp(json.dumps(_VALID_TAG))])
    tags = t.tag(Path("x.mp4"), images=[b"jpegbytes"])
    assert t.posts == 2 and tags.mood == ["peaceful"]
    text1 = t.bodies[0]["messages"][1]["content"][-1]["text"]
    text2 = t.bodies[1]["messages"][1]["content"][-1]["text"]
    assert "failed validation" not in text1
    assert "failed validation" in text2 and "flamboyant" in text2


def test_glm_tagger_gives_up_after_4(monkeypatch):
    monkeypatch.setattr("autoedit.library.vision.time.sleep", lambda s: None)
    t = StubGLM([_glm_resp("not json at all")] * 4)
    with pytest.raises(RuntimeError, match="4 lần"):
        t.tag(Path("x.mp4"), images=[b"jpegbytes"])
    assert t.posts == 4


def test_glm_tagger_400_surfaces_body(monkeypatch):
    """PB4: 400 content-filter (bigmodel 1301) không retry được — lỗi phải mang BODY
    (lý do chặn) cho kill-log, không mù 'Bad Request'."""
    import urllib.error
    from io import BytesIO

    err = urllib.error.HTTPError("u", 400, "Bad Request", {},
                                 BytesIO(b'{"contentFilter":[{"level":2}]}'))
    t = StubGLM([err])
    with pytest.raises(RuntimeError, match="contentFilter"):
        t.tag(Path("x.mp4"), images=[b"jpegbytes"])
    assert t.posts == 1  # không retry 400


def test_db_migrate_old_schema_adds_new_columns(tmp_path):
    """DB tag trước Phase B: connect() tự ALTER thêm cột + dòng cũ thiếu scene_type
    bị coi là cần tag lại (luật spec §5.1) dù mtime không đổi."""
    old = tmp_path / "old.db"
    raw = sqlite3.connect(old)
    raw.execute("""CREATE TABLE library_assets (
        id INTEGER PRIMARY KEY, niche TEXT NOT NULL, path TEXT NOT NULL UNIQUE,
        category TEXT NOT NULL, media_type TEXT NOT NULL, mtime REAL NOT NULL,
        subject TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
        shot_size TEXT NOT NULL DEFAULT '', mood TEXT NOT NULL DEFAULT '',
        has_people INTEGER NOT NULL DEFAULT 0, tags TEXT NOT NULL DEFAULT '[]',
        approved INTEGER NOT NULL DEFAULT 0, indexed_at TEXT NOT NULL)""")
    raw.execute("INSERT INTO library_assets (niche, path, category, media_type, mtime,"
                " indexed_at) VALUES ('n1','/lib/old.mp4','signature','video',1.0,'t')")
    raw.commit()
    raw.close()

    conn = db.connect(old)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(library_assets)")}
    assert {"folder_path", "scene_type", "camera_angle",
            "dominant_color", "brightness", "saturation",
            "duration", "width", "height", "fps",                    # PB4 §3b
            "source_video", "scene_start", "scene_index", "has_voice"} <= cols
    assert db.needs_index(conn, "/lib/old.mp4", 1.0)  # thiếu scene_type -> tag lại


def test_needs_index_retags_when_scene_type_missing(conn):
    db.upsert_asset(conn, _rec("/lib/x.mp4", mtime=1.0, scene_type=""))
    assert db.needs_index(conn, "/lib/x.mp4", 1.0)      # mtime y nguyên vẫn cần tag
    db.upsert_asset(conn, _rec("/lib/x.mp4", mtime=1.0, scene_type="urban_street"))
    assert not db.needs_index(conn, "/lib/x.mp4", 1.0)


def test_indexer_measures_colors_and_writes_new_fields(tmp_path, conn):
    """Ảnh thật (JPEG xanh dương) -> indexer đo màu code thuần + ghi đủ field mới;
    mood list nối ', ' vào cột TEXT cũ."""
    from PIL import Image

    d = init_niche("n1", root=tmp_path)
    Image.new("RGB", (200, 200), (0, 0, 255)).save(d / "signature" / "blue.jpg", quality=95)
    result = index_niche(conn, "n1", d, FakeTagger())
    assert len(result.indexed) == 1 and result.failed == []

    row = db.search_assets(conn, "n1", "blue")[0]
    assert row["scene_type"] == "urban_street"
    assert row["camera_angle"] == "unknown"
    assert row["mood"] == "peaceful, dreamy"
    r, b = int(row["dominant_color"][1:3], 16), int(row["dominant_color"][5:7], 16)
    assert b > 240 and r < 15
    assert row["brightness"] > 0.9 and row["saturation"] > 0.9


def test_indexer_color_fail_open_on_fake_bytes(tmp_path, conn):
    """File không decode được (bytes giả): đo màu fail-open — vẫn tag, màu rỗng."""
    d = init_niche("n1", root=tmp_path)
    (d / "signature" / "fake.jpg").write_bytes(b"not-an-image")
    result = index_niche(conn, "n1", d, FakeTagger())
    assert len(result.indexed) == 1 and result.failed == []
    row = db.search_assets(conn, "n1", "fake")[0]
    assert row["dominant_color"] == "" and row["brightness"] == 0.0


# ------------------- PB4: đa luồng + multi-key + ống nạp draft ----------------
def test_glm_api_keys_from_env_dict():
    """GLM_API_KEY + _2..9: có bao nhiêu dùng bấy nhiêu, bỏ ô trống, giữ thứ tự."""
    from autoedit.library.vision import glm_api_keys

    assert glm_api_keys({"GLM_API_KEY": "a", "GLM_API_KEY_3": "c"}) == ["a", "c"]
    assert glm_api_keys({"GLM_API_KEY_2": "b"}) == ["b"]
    assert glm_api_keys({}) == []


def test_shrink_for_api_downscales_and_fails_open():
    """Bug PB3-B2: frame thu ≤960px trước khi gửi; bytes giả trả nguyên (fail-open)."""
    from PIL import Image

    from autoedit.library.vision import shrink_for_api

    small = shrink_for_api(_make_jpeg(2000, 1200))
    w, h = Image.open(io.BytesIO(small)).size
    assert max(w, h) == 960
    assert shrink_for_api(b"junk-bytes") == b"junk-bytes"


def _make_jpeg(w: int, h: int) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (w, h), (30, 60, 90)).save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_glm_tagger_sends_shrunken_frames():
    """GLMVisionTagger tự thu 960px — caller đưa frame gốc 1280 vẫn gửi bản nhẹ."""
    import base64

    from PIL import Image

    t = StubGLM([_glm_resp(json.dumps(_VALID_TAG))])
    t.tag(Path("x.mp4"), images=[_make_jpeg(1280, 720)])
    sent = t.bodies[0]["messages"][1]["content"][0]["image_url"]["url"]
    data = base64.b64decode(sent.split(",", 1)[1])
    assert max(Image.open(io.BytesIO(data)).size) == 960


def test_preview_images_one_frame_under_10s(monkeypatch):
    """Spec §3a (user chốt 2026-07-07): video <10s rút 1 frame giữa clip; ≥10s 2 frame."""
    from autoedit.library import vision

    got: list[int] = []
    monkeypatch.setattr(vision, "extract_frames",
                        lambda p, n=2: got.append(n) or [b"f"] * n)
    for dur, want in [(1.5, 1), (8.0, 1), (9.9, 1), (10.0, 2), (15.0, 2)]:
        monkeypatch.setattr(vision, "ffprobe_duration", lambda p, d=dur: d)
        assert len(vision.preview_images(Path("a.mp4"))) == want
    assert got == [1, 1, 1, 2, 2]


def test_index_niche_multi_taggers_round_robin(tmp_path, conn):
    """Multi-key PB3-B2: job i -> tagger i%n, tải chia đều, kết quả đủ hết."""
    d = init_niche("n1", root=tmp_path)
    for i in range(4):
        (d / "signature" / f"c{i}.mp4").write_bytes(b"v")
    t1, t2 = FakeTagger(), FakeTagger()
    result = index_niche(conn, "n1", d, [t1, t2])
    assert len(result.indexed) == 4 and result.failed == []
    assert len(t1.calls) == 2 and len(t2.calls) == 2
    assert db.count_assets(conn, "n1") == 4


def test_index_nap_folder_gets_no_context(tmp_path, conn):
    """Clip ống nạp nằm ở nap/<tên project> — tên project KHÔNG phải ground truth
    ngữ nghĩa -> folder_context rỗng (tránh 'SP1 - 003' lọt vào tags)."""
    d = init_niche("n1", root=tmp_path)
    nap = d / "nap" / "SP1 - 003"
    nap.mkdir(parents=True)
    (nap / "clip.mp4").write_bytes(b"v")
    tagger = FakeTagger()
    index_niche(conn, "n1", d, tagger)
    assert tagger.contexts == [""]
    row = db.search_assets(conn, "n1", "clip")[0]
    assert row["category"] == "nap" and row["folder_path"] == "nap/SP1 - 003"


def test_upsert_preserves_ingest_provenance(conn):
    """Re-index thường (không qua ống nạp) mang default -> KHÔNG được xóa cột truy
    vết ống nạp (source_video/scene_start/scene_index/has_voice) — P5."""
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path="/lib/nap/c.mp4", category="nap", media_type="video",
        mtime=1.0, subject="s", description="d", shot_size="wide", mood="calm",
        has_people=False, tags=[], source_video="E:/src.mp4", scene_start=12.5,
        scene_index=7, has_voice=1, duration=5.0))
    # re-tag qua đường index folder: extra để default
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path="/lib/nap/c.mp4", category="nap", media_type="video",
        mtime=2.0, subject="s2", description="d", shot_size="wide", mood="calm",
        has_people=False, tags=[], duration=5.1))
    row = conn.execute("SELECT * FROM library_assets WHERE path='/lib/nap/c.mp4'").fetchone()
    assert row["subject"] == "s2" and row["duration"] == 5.1     # field thường cập nhật
    assert row["source_video"] == "E:/src.mp4" and row["scene_start"] == 12.5
    assert row["scene_index"] == 7 and row["has_voice"] == 1     # truy vết giữ nguyên


# ----- ống nạp: đọc draft nguồn (fake draft_content.json, không cần CapCut) -----
_PH = "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"


def _seg(mat_id: str, src_start: float, src_dur: float, tgt_start: float,
         tgt_dur: float | None = None) -> dict:
    return {"material_id": mat_id,
            "source_timerange": {"start": int(src_start * 1e6), "duration": int(src_dur * 1e6)},
            "target_timerange": {"start": int(tgt_start * 1e6),
                                 "duration": int((tgt_dur if tgt_dur is not None else src_dur) * 1e6)}}


def _fake_draft(tmp_path: Path) -> Path:
    """Draft nguồn thu nhỏ mô phỏng SP1 - 003: placeholder path, file thiếu, cache
    CapCut, cảnh ngắn, cảnh trùng, voice track nhiều segment + music track."""
    draft = tmp_path / "SP1 - TEST"
    (draft / "materials").mkdir(parents=True)
    for name in ("a.mp4", "b.mp4", "pic.jpg"):
        (draft / "materials" / name).write_bytes(b"x")
    content = {
        "materials": {"videos": [
            {"id": "A", "type": "video", "path": f"{_PH}/materials/a.mp4"},
            {"id": "B", "type": "video", "path": f"{_PH}/materials/b.mp4"},
            {"id": "P", "type": "photo", "path": f"{_PH}/materials/pic.jpg"},
            {"id": "M", "type": "video", "path": f"{_PH}/materials/GONE.mp4"},   # file thiếu
            {"id": "C", "type": "photo",  # nền đen tải về — bỏ
             "path": "C:/Users/x/AppData/Local/CapCut/User Data/Cache/onlineMaterial/k.image"},
        ]},
        "tracks": [
            {"type": "video", "segments": [
                _seg("B", 100.0, 4.0, 6.0),          # cảnh 2 theo timeline
                _seg("A", 26.0, 9.4, 0.0),           # cảnh 1
                _seg("A", 26.0, 9.4, 50.0),          # trùng khúc -> bỏ
                _seg("A", 40.0, 0.4, 20.0),          # <1s -> bỏ
                _seg("M", 0.0, 5.0, 30.0),           # file thiếu -> bỏ
                _seg("C", 0.0, 3.0, 40.0),           # cache -> bỏ
            ]},
            {"type": "video", "segments": [_seg("P", 0.0, 3.0, 12.0)]},  # overlay ảnh
            {"type": "text", "segments": [{"material_id": "T"}]},
            # voice = track audio NHIỀU segment nhất (3 khúc: 0-5s, 5.5-9s, 13-14s)
            {"type": "audio", "segments": [
                {"target_timerange": {"start": 0, "duration": int(5e6)}},
                {"target_timerange": {"start": int(5.5e6), "duration": int(3.5e6)}},
                {"target_timerange": {"start": int(13e6), "duration": int(1e6)}},
            ]},
            {"type": "audio", "segments": [  # nhạc: 1 khúc dài
                {"target_timerange": {"start": 0, "duration": int(60e6)}},
            ]},
        ],
    }
    (draft / "draft_content.json").write_text(
        json.dumps(content, ensure_ascii=False), encoding="utf-8")
    return draft


def test_read_draft_scenes_filters_resolves_and_orders(tmp_path):
    from autoedit.library.ingest import read_draft_scenes

    draft = _fake_draft(tmp_path)
    scenes, stats = read_draft_scenes(draft)
    assert [s.source.name for s in scenes] == ["a.mp4", "b.mp4", "pic.jpg"]  # theo timeline
    # §3g ytref: index theo TỪNG nguồn (mỗi file 1 cảnh -> đều là 1)
    assert [s.index for s in scenes] == [1, 1, 1]
    assert stats["missing_file"] == 1 and stats["cache_material"] == 1
    assert stats["too_short"] == 1 and stats["duplicate"] == 1
    a = scenes[0]
    assert a.source == draft / "materials" / "a.mp4"   # placeholder resolve về draft
    assert a.start == 26.0 and a.duration == 9.4 and a.media_type == "video"
    # voice: cảnh 1 (tgt 0-9.4s) phủ bởi voice 0-5 + 5.5-9 -> 1; cảnh 2 (6-10s) phủ 3/4 -> 1;
    # ảnh (12-15s) chỉ dính 13-14 = 1/3 >= 25% -> 1... kiểm bằng số thật:
    assert [s.has_voice for s in scenes] == [1, 1, 1]


def test_resolve_material_dead_absolute_path_falls_back_to_materials(tmp_path):
    """Mẻ deepsea 2026-07-12: draft dời máy — path tuyệt đối chết `D:/CapCut Drafts/...`
    nhưng file có thật trong <draft>/materials/ -> fallback; không có thật -> missing y cũ."""
    from autoedit.library.ingest import _resolve_material_path

    draft = tmp_path / "DS TEST"
    (draft / "materials").mkdir(parents=True)
    (draft / "materials" / "ca quay.mp4").write_bytes(b"x")
    got = _resolve_material_path("D:/CapCut Drafts/DS050_PORTABLE/materials/ca quay.mp4", draft)
    assert got == draft / "materials" / "ca quay.mp4"
    # path chết + không có bản local -> trả nguyên path chết (missing_file y cũ)
    gone = _resolve_material_path("D:/CapCut Drafts/OLD/materials/GONE.mp4", draft)
    assert gone == Path("D:/CapCut Drafts/OLD/materials/GONE.mp4")
    # path placeholder + path sống không bị đụng
    ph = _resolve_material_path(f"{_PH}/materials/ca quay.mp4", draft)
    assert ph == draft / "materials" / "ca quay.mp4"


def test_read_draft_scenes_no_audio_track_means_unknown_voice(tmp_path):
    from autoedit.library.ingest import read_draft_scenes

    draft = _fake_draft(tmp_path)
    content = json.loads((draft / "draft_content.json").read_text(encoding="utf-8"))
    content["tracks"] = [t for t in content["tracks"] if t["type"] != "audio"]
    (draft / "draft_content.json").write_text(json.dumps(content), encoding="utf-8")
    scenes, _ = read_draft_scenes(draft)
    assert {s.has_voice for s in scenes} == {-1}   # không track audio -> chưa biết


def test_cut_scene_video_applies_c4_and_is_idempotent(tmp_path, monkeypatch):
    """Lệnh cắt: -ss TRƯỚC -i (seek nhanh + chính xác khi re-encode), C4 H.264 CFR
    30fps yuv420p, -an bỏ audio nguồn. Có file rồi -> không gọi ffmpeg lại."""
    from autoedit.library import ingest

    calls: list[list[str]] = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        Path(cmd[-1]).write_bytes(b"out")

        class R:
            returncode = 0
            stderr = ""
        return R()

    monkeypatch.setattr(ingest.subprocess, "run", fake_run)
    scene = ingest.DraftScene(source=tmp_path / "src video.mp4", media_type="video",
                              start=26.0, duration=9.4, index=1, has_voice=1)
    clip, is_new = ingest.cut_scene(scene, tmp_path / "out")
    assert is_new and clip.name == "src video__000026000_0009400.mp4"
    cmd = calls[0]
    assert cmd.index("-ss") < cmd.index("-i")
    assert "-an" in cmd and "yuv420p" in cmd and "30" in cmd and "libx264" in cmd
    clip2, is_new2 = ingest.cut_scene(scene, tmp_path / "out")
    assert clip2 == clip and not is_new2 and len(calls) == 1


def test_ingest_draft_end_to_end_and_resume(tmp_path, conn, monkeypatch):
    """Ống nạp trọn vòng với FakeTagger + cắt giả: cảnh -> clip nap/<draft>/ -> db
    kèm cột §3b; chạy lại = resume (không cắt lại, không tag lại)."""
    from PIL import Image

    from autoedit.library import ingest

    draft = _fake_draft(tmp_path)
    d = init_niche("n1", root=tmp_path)

    def fake_cut(scene, out_dir, zoom=0.0):
        p = out_dir / ingest.scene_clip_name(scene, zoom)
        new = not p.is_file()
        if new:
            p.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (640, 360), (9, 9, 9)).save(p, format="JPEG")
        return p, new

    monkeypatch.setattr(ingest, "cut_scene", fake_cut)
    tagger = FakeTagger()
    r = ingest.ingest_draft(conn, "n1", d, draft, [tagger])
    assert r.scenes == 3 and r.cut_new == 3 and len(r.indexed) == 3 and r.failed == []
    assert tagger.contexts == ["", "", ""]          # tên project không làm context
    # 2a (§C6-DIEU-TRA): tiêu đề FILE video nguồn đi kênh riêng source_title
    assert all(t for t in tagger.source_titles) and "a" in tagger.source_titles

    rows = {Path(x["path"]).name: x for x in conn.execute(
        "SELECT * FROM library_assets WHERE niche='n1'").fetchall()}
    first = rows["a__000026000_0009400.mp4"]
    assert first["category"] == "nap" and first["folder_path"] == "nap/SP1 - TEST"
    assert first["source_video"].endswith("a.mp4")
    assert first["scene_start"] == 26.0 and first["scene_index"] == 1
    assert first["has_voice"] == 1
    assert first["width"] == 640 and first["height"] == 360   # §3b đo từ clip (PIL)

    r2 = ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()])
    assert r2.cut_new == 0 and r2.cut_reused == 3
    assert r2.indexed == [] and r2.skipped_db == 3            # resume: 0 tiền

    # limit: chỉ xử lý N cảnh đầu
    conn.execute("DELETE FROM library_assets")
    conn.commit()
    r3 = ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()], limit=2)
    assert len(r3.indexed) == 2


# ----- c8: gói NẠP viral (MO_TA_VAN_HANH_C8_NAP.md) -----
def _viral_draft(tmp_path: Path) -> Path:
    """Draft tách cảnh từ 1 video viral: nguồn 600s, 1 cảnh 20s (bóp 6s giữa),
    1 cảnh 4s (giữ nguyên), 1 cảnh 1.5s (sàn 2s bỏ — sàn 1s cũ cho qua)."""
    draft = tmp_path / "VIRAL - TEST"
    (draft / "materials").mkdir(parents=True)
    (draft / "materials" / "v.mp4").write_bytes(b"x")
    content = {
        "materials": {"videos": [
            {"id": "V", "type": "video", "duration": int(600e6),
             "path": f"{_PH}/materials/v.mp4"},
        ]},
        "tracks": [{"type": "video", "segments": [
            _seg("V", 100.0, 20.0, 0.0),    # >10s -> bóp còn 6s khúc giữa (107..113)
            _seg("V", 300.0, 4.0, 20.0),    # 2-10s -> giữ nguyên
            _seg("V", 500.0, 1.5, 24.0),    # <2s -> sàn c8 luật 6 bỏ trước vision
        ]}],
    }
    (draft / "draft_content.json").write_text(
        json.dumps(content, ensure_ascii=False), encoding="utf-8")
    return draft


def test_scene_floor_2s_drops_before_vision(tmp_path):
    """c8 luật 6 (user chốt 2026-07-08): cảnh <2s bỏ tại ống nạp TRƯỚC khi cắt/tag —
    tái hiện bug-trước-fix: sàn 1.0s cũ cho cảnh 1.5s đi qua tốn tiền vision."""
    from autoedit.library.ingest import MIN_SCENE_S, read_draft_scenes

    assert MIN_SCENE_S == 2.0
    scenes, stats = read_draft_scenes(_viral_draft(tmp_path))
    assert stats["too_short"] == 1                       # cảnh 1.5s bị đếm + bỏ
    assert [s.duration for s in scenes] == [20.0, 4.0]   # không cảnh nào <2s lọt
    assert all(s.source_duration == 600.0 for s in scenes)


def test_cut_scene_zoom_bakes_crop_and_names_clip(tmp_path, monkeypatch):
    """c8 luật 4: zoom>1 chèn -vf crop tâm + scale về ~cỡ gốc, tên clip mang _z112
    (đổi % zoom -> tên mới -> cắt+tag lại, không tái dùng clip zoom cũ)."""
    from autoedit.library import ingest

    calls: list[list[str]] = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        Path(cmd[-1]).write_bytes(b"out")

        class R:
            returncode = 0
            stderr = ""
        return R()

    monkeypatch.setattr(ingest.subprocess, "run", fake_run)
    scene = ingest.DraftScene(source=tmp_path / "v.mp4", media_type="video",
                              start=107.0, duration=6.0, index=1, has_voice=-1)
    clip, _ = ingest.cut_scene(scene, tmp_path / "out", zoom=1.12)
    assert clip.name == "v__000107000_0006000_z112.mp4"
    vf = calls[0][calls[0].index("-vf") + 1]
    assert vf.startswith("crop=trunc(iw/1.12/2)*2") and "scale=trunc(iw*1.12/2)*2" in vf
    assert "-an" in calls[0]                        # luật 2: tách âm vẫn nguyên
    # zoom=0 (own): KHÔNG chèn -vf, tên không suffix — hành vi cũ nguyên vẹn
    clip2, _ = ingest.cut_scene(scene, tmp_path / "out")
    assert clip2.name == "v__000107000_0006000.mp4" and "-vf" not in calls[1]


def test_viral_ingest_squeezes_labels_and_own_untouched(tmp_path, conn, monkeypatch):
    """c8 luật 1+5: viral cảnh >10s bóp 6s KHÚC GIỮA (start dịch +7), db mang
    source_class='viral' + source_duration; nạp own không bóp, nhãn 'own'."""
    from PIL import Image

    from autoedit.library import ingest

    draft = _viral_draft(tmp_path)
    d = init_niche("n1", root=tmp_path)
    zooms: list[float] = []

    def fake_cut(scene, out_dir, zoom=0.0):
        zooms.append(zoom)
        p = out_dir / ingest.scene_clip_name(scene, zoom)
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (640, 360), (9, 9, 9)).save(p, format="JPEG")
        return p, True

    monkeypatch.setattr(ingest, "cut_scene", fake_cut)
    r = ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()], source_class="viral")
    assert r.stats["squeezed_6s"] == 1 and set(zooms) == {ingest.VIRAL_ZOOM}
    rows = {Path(x["path"]).name: x for x in conn.execute(
        "SELECT * FROM library_assets WHERE niche='n1'").fetchall()}
    sq = rows["v__000107000_0006000_z112.mp4"]      # 100 + (20-6)/2 = 107, dur 6
    assert sq["scene_start"] == 107.0
    assert sq["source_class"] == "viral" and sq["source_duration"] == 600.0
    assert sq["scene_index"] == 1
    keep = rows["v__000300000_0004000_z112.mp4"]    # ≤10s giữ nguyên độ dài
    assert keep["source_class"] == "viral" and keep["scene_start"] == 300.0

    # nạp own trên draft khác: không bóp, không zoom, nhãn own (hành vi cũ)
    conn.execute("DELETE FROM library_assets")
    conn.commit()
    zooms.clear()
    r2 = ingest.ingest_draft(conn, "n1", d, _fake_draft(tmp_path), [FakeTagger()])
    assert "squeezed_6s" not in r2.stats and set(zooms) == {0.0}
    row = conn.execute("SELECT source_class FROM library_assets").fetchone()
    assert row["source_class"] == "own"


# ----- VD4: ghi công kênh nguồn (MO_TA_VAN_HANH_GHI_CONG_KENH.md) -----
# dùng chung helper _fake_cut_jpeg(monkeypatch) của khối TCF phía dưới
def test_ingest_channel_flag_and_retag_preserves(tmp_path, conn, monkeypatch):
    """--channel đóng dấu kênh cả mẻ; chạy LẠI (retag) KHÔNG --channel phải GIỮ kênh —
    tái hiện footgun-trước-fix: nếu theo khuôn CASE source_video thì mỗi lần resume/
    retag không khai kênh là backfill mất trắng."""
    from autoedit.library import ingest

    draft = _fake_draft(tmp_path)
    d = init_niche("n1", root=tmp_path)
    _fake_cut_jpeg(monkeypatch)

    ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()], channel="Kênh Công Ty")
    chans = {r["source_channel"] for r in conn.execute(
        "SELECT source_channel FROM library_assets WHERE niche='n1'")}
    assert chans == {"Kênh Công Ty"}

    ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()], retag=True)
    chans = {r["source_channel"] for r in conn.execute(
        "SELECT source_channel FROM library_assets WHERE niche='n1'")}
    assert chans == {"Kênh Công Ty"}  # luật preserve: rỗng không đè


def test_viral_ingest_auto_channel_from_youtube(tmp_path, conn, monkeypatch):
    """Mẻ viral có YouTube ID: kênh tự điền từ yt-dlp TỪNG file nguồn;
    --channel explicit vẫn thắng kênh YouTube (cùng luật --topic)."""
    from autoedit.library import ingest
    from autoedit.library.ytpeaks import YTVideoInfo

    draft = _viral_draft(tmp_path)
    d = init_niche("n1", root=tmp_path)
    _fake_cut_jpeg(monkeypatch)
    monkeypatch.setattr(ingest, "youtube_infos_for", lambda scenes: (
        {str(s.source): YTVideoInfo(video_id="TY9dnrbQano", title="T",
                                    channel="Kurzgesagt", duration=600.0)
         for s in scenes}, []))

    ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()], source_class="viral")
    chans = {r["source_channel"] for r in conn.execute(
        "SELECT source_channel FROM library_assets WHERE niche='n1'")}
    assert chans == {"Kurzgesagt"}

    ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()], source_class="viral",
                        retag=True, channel="Editor Khai")
    chans = {r["source_channel"] for r in conn.execute(
        "SELECT source_channel FROM library_assets WHERE niche='n1'")}
    assert chans == {"Editor Khai"}


def test_viral_pool_open_except_breath(conn):
    """c8 gói CHỌN (2026-07-09, thay fail-safe NẠP): viral VÀO search_assets (phễu —
    gate pháp lý chuyển sang ViralLedger ở sourcer) + vocab_for_niche (NÃO học từ vựng
    viral vì giờ dùng được). Ngoại lệ DUY NHẤT: videos_for_niche (pool shot thở) VẪN
    chặn — 1209 clip nạp mới sort mới-nhất-trước sẽ chiếm trọn pool 500."""
    def rec(path, cls):
        return db.AssetRecord(
            niche="n1", path=path, category="nap", media_type="video", mtime=1.0,
            subject="glowing nebula", description="d", shot_size="wide", mood="epic",
            has_people=False, tags=["nebula"], scene_type="nature_landscape",
            source_video="E:/src.mp4", source_class=cls, source_duration=600.0)

    db.upsert_asset(conn, rec("/lib/own.mp4", "own"))
    db.upsert_asset(conn, rec("/lib/viral.mp4", "viral"))
    assert {r["path"] for r in db.search_assets(conn, "n1", "nebula")} == \
        {"/lib/own.mp4", "/lib/viral.mp4"}
    assert db.vocab_for_niche(conn, "n1")["total"] == 2
    assert [r["path"] for r in db.videos_for_niche(conn, "n1")] == ["/lib/own.mp4"]


def test_reindex_never_flips_viral_to_own(conn):
    """c8 chống lật nhãn (P5 — tầng nguy hiểm nhất): index_niche quét lại folder nap/
    upsert với default source_video=''/'own' -> KHÔNG được đè viral thành own
    (lách gate pháp lý âm thầm)."""
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path="/lib/nap/v.mp4", category="nap", media_type="video",
        mtime=1.0, subject="s", description="d", shot_size="wide", mood="calm",
        has_people=False, tags=[], source_video="E:/viral.mp4", scene_start=107.0,
        scene_index=3, has_voice=-1, source_class="viral", source_duration=600.0))
    # re-index thường: extra toàn default
    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path="/lib/nap/v.mp4", category="nap", media_type="video",
        mtime=2.0, subject="s2", description="d", shot_size="wide", mood="calm",
        has_people=False, tags=[]))
    row = conn.execute("SELECT * FROM library_assets WHERE path='/lib/nap/v.mp4'").fetchone()
    assert row["subject"] == "s2"                          # field thường vẫn cập nhật
    assert row["source_class"] == "viral" and row["source_duration"] == 600.0
    assert row["source_video"] == "E:/viral.mp4" and row["scene_index"] == 3


# ------------ ytref: điểm nhô + bối cảnh (MO_TA_YTREF §3a-3g + §3i) ------------
def _yt_scene(src: str, start: float, dur: float, mt: str = "video"):
    from autoedit.library.ingest import DraftScene
    return DraftScene(source=Path(src), media_type=mt, start=start, duration=dur,
                      index=1, has_voice=-1, source_duration=600.0)


def test_viral_rules_trio_runup_flag_and_anchor():
    """§3a/§3e/§3f (📌 điều chỉnh 1+2, 2026-07-11): điểm nhô = TRIO 3 cảnh từ-đỉnh-
    về-trước (cảnh chứa đỉnh + 2 cảnh liền trước build-up, hở >3s dừng); cảnh SAU
    đỉnh không cờ; bóp 6s SÁT ĐỈNH (chứa đỉnh: giữa bin, build-up: 6s cuối);
    >20s BỎ trừ có cờ."""
    from autoedit.library import ingest
    from autoedit.library.ytpeaks import Peak, YTVideoInfo

    src = str(Path("F:/moon/doc [TY9dnrbQano].mp4"))  # key = str(Path) y production
    info = YTVideoInfo(video_id="TY9dnrbQano", title="t", duration=600.0,
                       heatmap_available=True,
                       # P1: bin [110,116] giữa 113, cửa sổ [109,117]
                       # P2: bin [202,208] giữa 205, cửa sổ [201,209]
                       peaks=[Peak(100.0, 110.0, 1.0, "primary", apex_end=116.0),
                              Peak(195.0, 202.0, 0.7, "secondary", apex_end=208.0)])
    scenes = [_yt_scene(src, 84.0, 6.0),     # trước trio (trio đã đủ 3) -> KHÔNG cờ
              _yt_scene(src, 90.0, 6.0),     # trio k-2: cờ DÙ không giao cửa sổ đỉnh
              _yt_scene(src, 96.0, 14.0),    # trio k-1 >10s -> 6s CUỐI dẫn vào đỉnh [104,110]
              _yt_scene(src, 110.0, 18.0),   # k (chứa giữa-bin 113) -> [110,116]
              _yt_scene(src, 128.0, 4.0),    # SAU đỉnh -> KHÔNG cờ
              _yt_scene(src, 140.0, 25.0),   # >20s không cờ -> BỎ (too_long)
              _yt_scene(src, 190.0, 25.0),   # k của P2; cảnh trước hở 58s>3s -> trio 1 mình;
              #                                >20s CÓ cờ -> GIỮ, neo [202,208]
              _yt_scene(src, 400.0, 12.0)]   # không cờ -> 6s khúc giữa 403 (y cũ)
    stats, warns = {}, []
    kept = ingest.apply_viral_rules(scenes, stats, {src: info}, warns)

    assert stats["too_long"] == 1 and stats["squeezed_6s"] == 4
    assert (stats["peak_scenes"], stats["peak_total"], stats["peak_videos"]) == (4, 2, 1)
    by_start = {s.start: s for s in kept}
    assert set(by_start) == {84.0, 90.0, 104.0, 110.0, 128.0, 202.0, 403.0}
    assert by_start[90.0].peak_type == "primary" and by_start[90.0].duration == 6.0
    runup = by_start[104.0]                  # 96+14 -> 6s cuối sát đỉnh, vẫn mang cờ
    assert runup.duration == 6.0 and runup.peak_value == 1.0
    anchored = by_start[110.0]               # chứa đỉnh: tail=min(113+3,128) -> [110,116]
    assert anchored.duration == 6.0 and anchored.peak_type == "primary"
    long_peak = by_start[202.0]              # P2 trio 1 mình (đứt chuỗi), neo trọn bin
    assert long_peak.duration == 6.0 and long_peak.peak_type == "secondary"
    # trước-trio và SAU đỉnh không cờ (user: chỉ lấy TỪ ĐỈNH VỀ TRƯỚC)
    assert by_start[84.0].peak_type == "" and by_start[128.0].peak_type == ""
    assert by_start[403.0].duration == 6.0 and by_start[403.0].peak_type == ""
    assert warns == []


def test_viral_rules_duration_mismatch_drops_flags():
    """§3d chống mốc trượt: file lệch YouTube >3% -> KHÔNG gắn cờ video đó + warning;
    hệ quả >20s mất ngoại lệ điểm nhô -> bỏ."""
    from autoedit.library import ingest
    from autoedit.library.ytpeaks import Peak, YTVideoInfo

    src = str(Path("F:/moon/doc [TY9dnrbQano].mp4"))
    info = YTVideoInfo(video_id="TY9dnrbQano", title="t", duration=700.0,  # file 600s
                       heatmap_available=True,
                       peaks=[Peak(105.0, 110.0, 1.0, "primary")])
    scenes = [_yt_scene(src, 100.0, 18.0), _yt_scene(src, 199.0, 25.0)]
    stats, warns = {}, []
    kept = ingest.apply_viral_rules(scenes, stats, {src: info}, warns)
    assert len(warns) == 1 and "KHÔNG gắn cờ" in warns[0]
    assert stats["peak_videos"] == 0 and stats["peak_scenes"] == 0
    assert stats["too_long"] == 1                      # 25s hết ngoại lệ -> bỏ
    assert [s.start for s in kept] == [106.0]          # 18s bóp khúc giữa như thường


def test_scene_index_per_source_interleaved(tmp_path):
    """§3g: index = thứ tự source_start TRONG TỪNG nguồn (ledger check kề ±1 theo
    nguồn) — 2 nguồn trộn xen kẽ trên timeline không làm index nhảy."""
    from autoedit.library.ingest import read_draft_scenes

    draft = tmp_path / "MIX"
    (draft / "materials").mkdir(parents=True)
    for name in ("a.mp4", "b.mp4"):
        (draft / "materials" / name).write_bytes(b"x")
    content = {"materials": {"videos": [
        {"id": "A", "type": "video", "path": f"{_PH}/materials/a.mp4"},
        {"id": "B", "type": "video", "path": f"{_PH}/materials/b.mp4"}]},
        "tracks": [{"type": "video", "segments": [
            _seg("A", 50.0, 3.0, 0.0), _seg("B", 10.0, 3.0, 3.0),
            _seg("A", 20.0, 3.0, 6.0), _seg("B", 90.0, 3.0, 9.0)]}]}
    (draft / "draft_content.json").write_text(json.dumps(content), encoding="utf-8")
    scenes, _ = read_draft_scenes(draft)
    # list giữ thứ tự TIMELINE (dna cần); index theo nguồn
    assert [(s.source.name, s.start, s.index) for s in scenes] == [
        ("a.mp4", 50.0, 2), ("b.mp4", 10.0, 1), ("a.mp4", 20.0, 1), ("b.mp4", 90.0, 2)]


def test_ingest_ytref_flags_db_title_and_section(tmp_path, conn, monkeypatch):
    """Ống nạp ytref trọn vòng (yt-dlp fake): cờ vào 2 cột db (§3e, không rơi —
    vết PB7), cảnh không cờ NULL; tag nhận title THẬT (§3i-1) + chapter đúng ĐOẠN
    theo điểm giữa miếng cắt SAU bóp (§3i-2)."""
    from PIL import Image

    from autoedit.library import ingest
    from autoedit.library.ytpeaks import Peak, YTVideoInfo

    draft = tmp_path / "MOON THAM KHAO"
    (draft / "materials").mkdir(parents=True)
    (draft / "materials" / "doc [TY9dnrbQano].mp4").write_bytes(b"x")
    content = {"materials": {"videos": [
        {"id": "V", "type": "video", "duration": int(600e6),
         "path": f"{_PH}/materials/doc [TY9dnrbQano].mp4"}]},
        "tracks": [{"type": "video", "segments": [
            _seg("V", 100.0, 18.0, 0.0),   # cờ -> 6s neo apex 112 -> start 109, mid 112
            _seg("V", 50.0, 4.0, 18.0),    # không cờ, mid 52
        ]}]}
    (draft / "draft_content.json").write_text(json.dumps(content), encoding="utf-8")
    d = init_niche("n1", root=tmp_path)

    def fake_fetch(video_id):
        assert video_id == "TY9dnrbQano"   # ID rút từ tên file, không cần urls.txt
        return YTVideoInfo(
            video_id=video_id, title="What China Found on The Moon", duration=600.0,
            heatmap_available=True,
            chapters=[{"title": "The Moon", "start_time": 0.0, "end_time": 110.0},
                      {"title": "The Cube", "start_time": 110.0, "end_time": 400.0}],
            peaks=[Peak(105.0, 112.0, 1.0, "primary")])

    def fake_cut(scene, out_dir, zoom=0.0):
        p = out_dir / ingest.scene_clip_name(scene, zoom)
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 64), (9, 9, 9)).save(p, format="JPEG")
        return p, True

    monkeypatch.setattr(ingest.ytpeaks, "fetch_video_info", fake_fetch)
    monkeypatch.setattr(ingest, "cut_scene", fake_cut)
    tagger = FakeTagger()
    r = ingest.ingest_draft(conn, "n1", d, draft, [tagger], source_class="viral")
    assert r.stats["peak_scenes"] == 1 and r.stats["warnings"] == []

    rows = {row["scene_start"]: row for row in conn.execute(
        "SELECT * FROM library_assets WHERE niche='n1'").fetchall()}
    flagged = rows[109.0]                  # neo đỉnh: min(max(112-3, 100), 112) = 109
    assert flagged["peak_value"] == 1.0 and flagged["peak_type"] == "primary"
    plain = rows[50.0]
    assert plain["peak_value"] is None and plain["peak_type"] is None
    assert set(tagger.source_titles) == {"What China Found on The Moon"}
    assert sorted(tagger.section_hints) == ["The Cube", "The Moon"]


def test_viral_without_id_warns_and_proceeds(tmp_path, conn, monkeypatch):
    """§3b fail-open: nguồn không rút được ID -> warning 'thiếu bối cảnh + điểm nhô',
    KHÔNG gọi yt-dlp, mẻ nạp vẫn chạy trọn như viral thường."""
    from PIL import Image

    from autoedit.library import ingest

    def no_fetch(video_id):
        raise AssertionError("không có ID thì không được gọi yt-dlp")

    def fake_cut(scene, out_dir, zoom=0.0):
        p = out_dir / ingest.scene_clip_name(scene, zoom)
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 64), (9, 9, 9)).save(p, format="JPEG")
        return p, True

    monkeypatch.setattr(ingest.ytpeaks, "fetch_video_info", no_fetch)
    monkeypatch.setattr(ingest, "cut_scene", fake_cut)
    r = ingest.ingest_draft(conn, "n1", init_niche("n1", root=tmp_path),
                            _viral_draft(tmp_path), [FakeTagger()], source_class="viral")
    assert any("không tìm ra YouTube ID" in w for w in r.stats["warnings"])
    assert r.stats["peak_scenes"] == 0 and len(r.indexed) == 2   # 20s bóp giữa + 4s


def test_ingest_topic_reaches_tagger(tmp_path, conn, monkeypatch):
    """§3i-3: --topic chảy tới vision cho MỌI cảnh; đường không ytref section_hint
    rỗng = prompt y cũ."""
    from PIL import Image

    from autoedit.library import ingest

    def fake_cut(scene, out_dir, zoom=0.0):
        p = out_dir / ingest.scene_clip_name(scene, zoom)
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 64), (9, 9, 9)).save(p, format="JPEG")
        return p, True

    monkeypatch.setattr(ingest, "cut_scene", fake_cut)
    tagger = FakeTagger()
    ingest.ingest_draft(conn, "n1", init_niche("n1", root=tmp_path),
                        _fake_draft(tmp_path), [tagger], topic="the Moon")
    assert set(tagger.topics) == {"the Moon"} and set(tagger.section_hints) == {""}


# ------- spec TOPIC_CHAPTER_FILE: file bối cảnh editor đặt trong folder draft -------
def _context_file(draft: Path, text: str) -> None:
    (draft / "topic + chapter video.txt").write_text(text, encoding="utf-8")


def _fake_cut_jpeg(monkeypatch):
    from PIL import Image

    from autoedit.library import ingest

    def fake_cut(scene, out_dir, zoom=0.0):
        p = out_dir / ingest.scene_clip_name(scene, zoom)
        if p.exists():           # y bản thật: clip có sẵn -> tái dùng, KHÔNG ghi lại
            return p, False
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 64), (9, 9, 9)).save(p, format="JPEG")
        return p, True

    monkeypatch.setattr(ingest, "cut_scene", fake_cut)


def _own_ctx_draft(tmp_path: Path) -> Path:
    """2 cảnh mà giây NGUỒN và giây TIMELINE khác hẳn nhau — bắt bẫy hệ quy chiếu."""
    draft = tmp_path / "SP1 - CTX"
    (draft / "materials").mkdir(parents=True)
    for name in ("a.mp4", "b.mp4"):
        (draft / "materials" / name).write_bytes(b"x")
    content = {"materials": {"videos": [
        {"id": "A", "type": "video", "path": f"{_PH}/materials/a.mp4"},
        {"id": "B", "type": "video", "path": f"{_PH}/materials/b.mp4"}]},
        "tracks": [{"type": "video", "segments": [
            _seg("A", 100.0, 4.0, 0.0),    # timeline 0-4 (mid 2s) | mid nguồn 102s
            _seg("B", 50.0, 4.0, 10.0),    # timeline 10-14 (mid 12s) | mid nguồn 52s
        ]}]}
    (draft / "draft_content.json").write_text(json.dumps(content), encoding="utf-8")
    return draft


def test_read_draft_context_parses_topic_and_chapters(tmp_path):
    """TCF §2: dòng trước chapter đầu = tiêu đề (gộp); chapter M:SS / H:MM:SS format
    YouTube, end_time nối đuôi (cuối = None); dòng hỏng sau chapter đầu bỏ đúng dòng."""
    from autoedit.library.ingest import read_draft_context

    d = tmp_path / "SP1 - X"
    d.mkdir()
    _context_file(d, "Vì sao Mặt Trăng khóa thủy triều\n(phần 2 tiêu đề)\n\n"
                     "00:00 Mở đầu\n02:15 Tidal locking\ndòng hỏng không timestamp\n"
                     "1:05:40 Mặt xa\n")
    ctx = read_draft_context(d)
    assert ctx.topic == "Vì sao Mặt Trăng khóa thủy triều (phần 2 tiêu đề)"
    assert [(c["start_time"], c["end_time"], c["title"]) for c in ctx.chapters] == [
        (0.0, 135.0, "Mở đầu"), (135.0, 3940.0, "Tidal locking"),
        (3940.0, None, "Mặt xa")]


def test_read_draft_context_real_editor_format(tmp_path):
    """REGRESSION format THẬT editor đặt ở SP1-012 (2026-07-11): dòng nhãn
    'Topic video:' / 'chapter' phải bị bỏ, tiêu đề sạch; 7 chapter CHAPTER N — ..."""
    from autoedit.library.ingest import read_draft_context

    d = tmp_path / "SP1 - 012"
    d.mkdir()
    _context_file(d, "Topic video:\n"
                     "What's Behind the Moon Is More Terrifying Than the Void Itself\n"
                     "chapter\n"
                     "01:02 CHAPTER 1 — Four people just passed the face we never see\n"
                     "04:44 CHAPTER 2 — The half that was built wrong\n"
                     "07:44 CHAPTER 3 — We only saw it recently\n"
                     "10:35 CHAPTER 4 — The scar that breaks the ruler\n"
                     "14:02 CHAPTER 5 — The thing buried under the floor\n"
                     "17:31 CHAPTER 6 — A world we called dead is still moving\n"
                     "20:49 CHAPTER 7 — The quietest sky in the solar system\n")
    ctx = read_draft_context(d)
    assert ctx.topic == "What's Behind the Moon Is More Terrifying Than the Void Itself"
    assert len(ctx.chapters) == 7
    assert ctx.chapters[0]["start_time"] == 62.0
    assert ctx.chapters[-1]["title"].endswith("quietest sky in the solar system")
    assert ctx.chapters[-1]["end_time"] is None
    # tiêu đề bắt đầu bằng chữ "Chapter..." KHÔNG bị strip oan (prefix cần dấu ':')
    e = tmp_path / "SP1 - E"
    e.mkdir()
    _context_file(e, "Chapter of the Moon story\n00:00 A\n01:00 B\n")
    assert read_draft_context(e).topic == "Chapter of the Moon story"


def test_read_draft_context_insufficient_or_missing(tmp_path):
    """TCF §2: 1 chapter = cả video -> KHÔNG chia đoạn (chỉ giữ tiêu đề — đúng ý user
    'không đủ thì chỉ lấy tiêu đề'); không có file -> rỗng im lặng (fail-open)."""
    from autoedit.library.ingest import read_draft_context

    d = tmp_path / "SP1 - Y"
    d.mkdir()
    _context_file(d, "Bí ẩn đảo Síp\n00:00 Cả video\n")
    ctx = read_draft_context(d)
    assert ctx.topic == "Bí ẩn đảo Síp" and ctx.chapters == []
    e = tmp_path / "SP1 - Z"
    e.mkdir()
    empty = read_draft_context(e)
    assert empty.topic == "" and empty.chapters == []


def test_ingest_own_context_maps_by_timeline(tmp_path, conn, monkeypatch):
    """TCF §3a/§3b: own — tiêu đề file vào TOPIC (stem GIỮ làm source_title, không đè);
    chapter map theo TIMELINE draft (target_start). Map nhầm theo giây NGUỒN thì cả 2
    cảnh đều rơi vào 'Phần hai' (mid nguồn 102/52 >= 10s) — test bắt đúng bẫy đó."""
    from autoedit.library import ingest

    _fake_cut_jpeg(monkeypatch)
    tagger = FakeTagger()
    draft = _own_ctx_draft(tmp_path)
    _context_file(draft, "Mặt tối Mặt Trăng\n00:00 Mở đầu\n00:10 Phần hai\n")
    r = ingest.ingest_draft(conn, "n1", init_niche("n1", root=tmp_path), draft, [tagger])
    assert set(tagger.topics) == {"Mặt tối Mặt Trăng"}
    assert set(tagger.source_titles) == {"a", "b"}          # stem giữ nguyên
    by_clip = dict(zip(tagger.calls, tagger.section_hints))
    assert by_clip[next(k for k in by_clip if k.startswith("a__"))] == "Mở đầu"
    assert by_clip[next(k for k in by_clip if k.startswith("b__"))] == "Phần hai"
    assert r.stats["warnings"] == []


def test_ingest_cli_topic_overrides_context_file(tmp_path, conn, monkeypatch):
    """TCF §3c: --topic CLI ĐÈ tiêu đề file (explicit thắng) + warning khi cả 2 khác."""
    from autoedit.library import ingest

    _fake_cut_jpeg(monkeypatch)
    tagger = FakeTagger()
    draft = _own_ctx_draft(tmp_path)
    _context_file(draft, "Tiêu đề trong file\n")
    r = ingest.ingest_draft(conn, "n1", init_niche("n1", root=tmp_path), draft,
                            [tagger], topic="CLI chốt")
    assert set(tagger.topics) == {"CLI chốt"}
    assert any("đè" in w for w in r.stats["warnings"])


def test_ingest_own_without_topic_warns(tmp_path, conn, monkeypatch):
    """TCF §3c: own không file + không --topic -> warning nhắc (luật vận hành mới),
    mẻ nạp vẫn chạy trọn tag mù chủ đề như cũ."""
    from autoedit.library import ingest

    _fake_cut_jpeg(monkeypatch)
    tagger = FakeTagger()
    r = ingest.ingest_draft(conn, "n1", init_niche("n1", root=tmp_path),
                            _own_ctx_draft(tmp_path), [tagger])
    assert any("thiếu chủ đề" in w for w in r.stats["warnings"])
    assert len(tagger.calls) == 2 and set(tagger.topics) == {""}


def test_ingest_viral_context_fallback_source_frame(tmp_path, conn, monkeypatch):
    """TCF §3c: viral KHÔNG rút được ID -> file txt lấp topic + chapter, map theo giây
    FILE NGUỒN (scene.start — khác hệ quy chiếu own): cảnh bóp 6s mid nguồn 110s ->
    'Chương A' (60-240), cảnh 4s mid 302s -> 'Chương B'."""
    from autoedit.library import ingest

    def no_fetch(video_id):
        raise AssertionError("không có ID thì không được gọi yt-dlp")

    monkeypatch.setattr(ingest.ytpeaks, "fetch_video_info", no_fetch)
    _fake_cut_jpeg(monkeypatch)
    tagger = FakeTagger()
    draft = _viral_draft(tmp_path)
    _context_file(draft, "Video nguồn ABC\n01:00 Chương A\n04:00 Chương B\n")
    ingest.ingest_draft(conn, "n1", init_niche("n1", root=tmp_path), draft,
                        [tagger], source_class="viral")
    assert set(tagger.topics) == {"Video nguồn ABC"}
    assert sorted(tagger.section_hints) == ["Chương A", "Chương B"]


def test_ingest_retag_forces_existing_assets(tmp_path, conn, monkeypatch):
    """TCF M2: chạy lại thường -> skip hết (needs_index); --retag -> tag lại TOÀN BỘ
    (clip tái dùng không cắt lại, upsert đè tag cũ)."""
    from autoedit.library import ingest

    _fake_cut_jpeg(monkeypatch)
    d = init_niche("n1", root=tmp_path)
    draft = _own_ctx_draft(tmp_path)
    r1 = ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()], topic="t")
    assert len(r1.indexed) == 2
    r2 = ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()], topic="t")
    assert r2.skipped_db == 2 and len(r2.indexed) == 0        # resume thường: skip
    tagger = FakeTagger()
    r3 = ingest.ingest_draft(conn, "n1", d, draft, [tagger], topic="t", retag=True)
    assert r3.skipped_db == 0 and len(r3.indexed) == 2        # ép tag lại
    assert r3.cut_new == 0 and r3.cut_reused == 2             # clip KHÔNG cắt lại
    assert len(tagger.calls) == 2


def test_ingest_viral_youtube_beats_context_file(tmp_path, conn, monkeypatch):
    """TCF §3c: viral tra ĐƯỢC YouTube -> title/chapter YouTube thắng, file chỉ còn
    góp topic (cùng vai --topic mẻ MOON M2); chapter mồi trong file KHÔNG được dùng."""
    from PIL import Image

    from autoedit.library import ingest
    from autoedit.library.ytpeaks import YTVideoInfo

    draft = tmp_path / "MOON THAM KHAO"
    (draft / "materials").mkdir(parents=True)
    (draft / "materials" / "doc [TY9dnrbQano].mp4").write_bytes(b"x")
    content = {"materials": {"videos": [
        {"id": "V", "type": "video", "duration": int(600e6),
         "path": f"{_PH}/materials/doc [TY9dnrbQano].mp4"}]},
        "tracks": [{"type": "video", "segments": [_seg("V", 100.0, 4.0, 0.0)]}]}
    (draft / "draft_content.json").write_text(json.dumps(content), encoding="utf-8")
    _context_file(draft, "Topic từ file\n00:00 Chapter mồi 1\n03:00 Chapter mồi 2\n")

    def fake_fetch(video_id):
        return YTVideoInfo(
            video_id=video_id, title="Tiêu đề YouTube", duration=600.0,
            chapters=[{"title": "YT Chương", "start_time": 0.0, "end_time": 300.0}])

    monkeypatch.setattr(ingest.ytpeaks, "fetch_video_info", fake_fetch)
    _fake_cut_jpeg(monkeypatch)
    tagger = FakeTagger()
    ingest.ingest_draft(conn, "n1", init_niche("n1", root=tmp_path), draft,
                        [tagger], source_class="viral")
    assert tagger.source_titles == ["Tiêu đề YouTube"]
    assert tagger.section_hints == ["YT Chương"]            # không phải "Chapter mồi 1"
    assert tagger.topics == ["Topic từ file"]


def test_db_peak_columns_migrate_and_preserve(tmp_path, conn):
    """§3e: db cũ migrate thêm 2 cột (dòng cũ NULL, KHÔNG re-tag); re-index thường
    không xóa cờ (cùng khuôn chống-lật c8)."""
    p = tmp_path / "old.db"
    c1 = db.connect(p)
    c1.execute("ALTER TABLE library_assets DROP COLUMN peak_value")
    c1.execute("ALTER TABLE library_assets DROP COLUMN peak_type")
    c1.commit()
    c1.close()
    c2 = db.connect(p)   # _migrate thêm lại 2 cột
    cols = {r["name"] for r in c2.execute("PRAGMA table_info(library_assets)")}
    assert {"peak_value", "peak_type"} <= cols
    c2.close()

    db.upsert_asset(conn, db.AssetRecord(
        niche="n1", path="/lib/nap/pk.mp4", category="nap", media_type="video",
        mtime=1.0, subject="s", description="d", shot_size="wide", mood="calm",
        has_people=False, tags=[], source_video="E:/v.mp4", scene_start=109.0,
        source_class="viral", source_duration=600.0,
        peak_value=0.9, peak_type="primary"))
    db.upsert_asset(conn, db.AssetRecord(   # re-index thường: extra toàn default
        niche="n1", path="/lib/nap/pk.mp4", category="nap", media_type="video",
        mtime=2.0, subject="s2", description="d", shot_size="wide", mood="calm",
        has_people=False, tags=[]))
    row = conn.execute("SELECT * FROM library_assets WHERE path='/lib/nap/pk.mp4'").fetchone()
    assert row["peak_value"] == 0.9 and row["peak_type"] == "primary"
    db.upsert_asset(conn, _rec("/lib/plain.mp4"))
    plain = conn.execute("SELECT * FROM library_assets WHERE path='/lib/plain.mp4'").fetchone()
    assert plain["peak_value"] is None and plain["peak_type"] is None


# ------------------- PB5: thống kê DNA đợt 1 (dna.py, 0 token) ----------------
def test_read_timeline_shots_and_voice(tmp_path):
    """MỌI segment video (kể cả loại ống nạp bỏ) + voice = track nhiều segment nhất."""
    from autoedit.library.ingest import read_timeline

    shots, voice = read_timeline(_fake_draft(tmp_path))
    assert len(shots) == 7                       # 6 track chính + 1 overlay ảnh
    assert shots[0] == (0.0, 9.4)                # sort theo target start
    assert voice == [(0.0, 5.0), (5.5, 9.0), (13.0, 14.0)]


def test_compute_dna_end_to_end(tmp_path, conn, monkeypatch):
    """DNA từ fake draft + tag FakeTagger: pacing/thở/cỡ cảnh/chữ ký ra số kiểm được."""
    from PIL import Image

    from autoedit.library import ingest
    from autoedit.library.dna import compute_dna

    draft = _fake_draft(tmp_path)
    d = init_niche("n1", root=tmp_path)

    def fake_cut(scene, out_dir, zoom=0.0):
        p = out_dir / ingest.scene_clip_name(scene, zoom)
        p.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 64), (9, 9, 9)).save(p, format="JPEG")
        return p, True

    monkeypatch.setattr(ingest, "cut_scene", fake_cut)
    ingest.ingest_draft(conn, "n1", d, draft, [FakeTagger()])
    # regression ytref §3g: join dna theo (source_video, scene_start) — KHÔNG phụ
    # thuộc scheme scene_index, draft nạp trước fix (index timeline) vẫn khớp
    conn.execute("UPDATE library_assets SET scene_index = scene_index + 100")
    conn.commit()
    dna = compute_dna(conn, "n1", [draft])

    p = dna["pacing"]
    assert p["shots"] == 7 and dna["timeline_min"] == 1.0   # end = 50+9.4 = 59.4s
    assert p["holds"]["n"] == 3                  # 9.4 / 5 / 9.4 ≥ 5s
    # d2: voice 0-5, 5.5-9, 13-14 (end 59.4) -> ô thở ≥1s: 9→13 (4s) + 14→59.4 (45.4s)
    b = dna["breathing"]
    assert b["windows"] == 2 and b["len"]["max"] == 45.4 and b["len"]["min"] == 4.0
    # ảnh overlay (12-15s) đè ô thở 9-13 ≥0.5s + cảnh a (0-9.4) KHÔNG trong ô thở
    assert sum(b["scene_types"].values()) >= 1
    g = dna["shot_grammar"]
    assert sum(g["distribution"].values()) == pytest.approx(1.0, abs=0.02)
    assert dna["signature"]["top_scene_types"][0][0] == "urban_street"  # FakeTagger
    assert dna["signature"]["hook_opens_with"]                          # cảnh <45s có mặt


def test_compute_dna_excludes_mega_segments(conn, monkeypatch):
    """Luật user 2026-07-07 (PB9): shot >30s KHÔNG đếm vào pacing (mọi niche) — tái hiện
    bug: 1 khúc compilation 839s thổi std 3,1→32,9 làm validator Mảnh B kêu oan mọi video."""
    from autoedit.library import dna as dna_mod

    shots = [(0.0, 6.0), (6.0, 8.0), (14.0, 839.0)]   # 2 shot thật + 1 mega
    monkeypatch.setattr(dna_mod, "read_timeline", lambda d: (shots, []))
    monkeypatch.setattr(dna_mod, "read_draft_scenes", lambda d: ([], {}))
    p = dna_mod.compute_dna(conn, "n1", [Path("x")])["pacing"]
    assert p["shots"] == 2 and p["shot_len"]["max"] == 8.0    # 839s không đếm
    assert p["shot_len"]["std"] < 2                            # std không bị thổi
    assert p["mega_segments"] == {"n": 1, "total_s": 839.0}   # nhưng đếm riêng, không mất dấu
    # mật độ tính trên thời lượng ĐÃ TRỪ mega: 2 shot / (853-839)s
    assert p["cuts_per_min"] == round(2 / (14 / 60), 1)


def test_compute_dna_mega_stacked_tracks_density_fallback(conn, monkeypatch):
    """Regression life-in 2026-07-15: mega chồng NHIỀU track video → tổng mega
    (80.148s) > timeline (75.642s) → hiệu ÂM từng làm cuts_per_min = 0 (validator
    Mảnh B tự tắt oan cả niche). Fallback: mật độ trên TỔNG SHOT THẬT."""
    from autoedit.library import dna as dna_mod

    shots = [(0.0, 6.0), (0.0, 35.0), (0.0, 40.0)]   # 1 shot thật + 2 mega ĐÈ NHAU
    monkeypatch.setattr(dna_mod, "read_timeline", lambda d: (shots, []))
    monkeypatch.setattr(dna_mod, "read_draft_scenes", lambda d: ([], {}))
    p = dna_mod.compute_dna(conn, "n1", [Path("x")])["pacing"]
    assert p["mega_segments"]["total_s"] == 75.0      # 35+40 > timeline 40
    assert p["cuts_per_min"] == 10.0                  # 1 shot / 6s thật — KHÔNG rơi 0


def test_compute_dna_excludes_mega_breath_windows(conn, monkeypatch):
    """Luật user 2026-07-07: ô thở >60s (đoạn draft thiếu voice) BỎ QUA như shot — tái
    hiện bug PB9: gap 842s thổi mean ô thở 2,2→10,8s / std 80."""
    from autoedit.library import dna as dna_mod

    shots = [(0.0, 5.0), (5.0, 6.0), (11.0, 8.0), (19.0, 881.0 - 19.0)]
    voice = [(0.0, 5.0), (9.0, 19.0)]     # gap 5-9 (4s) + gap 19-881 (862s = mega)
    monkeypatch.setattr(dna_mod, "read_timeline", lambda d: (shots, voice))
    monkeypatch.setattr(dna_mod, "read_draft_scenes", lambda d: ([], {}))
    b = dna_mod.compute_dna(conn, "n1", [Path("x")])["breathing"]
    assert b["windows"] == 1 and b["len"]["max"] == 4.0        # 862s không đếm
    assert b["mega_windows"] == {"n": 1, "total_s": 862.0}     # đếm riêng, không mất dấu


# ---------- consumer DNA d1 đợt 1: dna.json + pacing validator (MO_TA DNA_D1) --
def test_dna_json_round_trip(tmp_path):
    from autoedit.library.dna import load_dna, save_dna

    dna = {"niche": "n1", "pacing": {"cuts_per_min": 8.3, "shot_len": {"std": 3.11}}}
    p = save_dna(dna, tmp_path / "n1", [Path("E:/SP1 - 003")])
    loaded = load_dna(tmp_path / "n1")
    assert p.name == "dna.json"
    assert loaded["pacing"] == dna["pacing"]
    assert loaded["measured_at"] and loaded["source_drafts"] == [str(Path("E:/SP1 - 003"))]


def test_load_dna_missing_or_corrupt_returns_none(tmp_path):
    """Fail-open §2c: không có / hỏng dna.json -> None, validator tự tắt, không nổ."""
    from autoedit.library.dna import load_dna

    assert load_dna(tmp_path) is None
    (tmp_path / "dna.json").write_text("{hỏng json", encoding="utf-8")
    assert load_dna(tmp_path) is None


_DNA = {"pacing": {"cuts_per_min": 8.3, "shot_len": {"std": 3.11}}}


def test_check_pacing_uniform_warns():
    """Tín hiệu (i): shot đều tăm tắp (std < ½ DNA) -> đúng 1 cảnh báo."""
    from autoedit.library.dna import check_pacing

    warns = check_pacing([5.0] * 10, 50 / 60, _DNA)   # 12 cut/phút: mật độ TRONG ngưỡng
    assert len(warns) == 1 and "đều tăm tắp" in warns[0]


def test_check_pacing_density_warns():
    """Tín hiệu (ii): cut/phút ngoài [½×, 2×] DNA -> đúng 1 cảnh báo."""
    from autoedit.library.dna import check_pacing

    warns = check_pacing([1.0, 8.0] * 12, 1.0, _DNA)  # std 3.5 ok; 24 cut/phút > 16.6
    assert len(warns) == 1 and "cut/phút" in warns[0] and "nhanh" in warns[0]


def test_check_pacing_clean_and_degenerate_silent():
    """Video hợp chuẩn -> 0 cảnh báo; DNA suy biến / thiếu shot -> im lặng, không nổ."""
    from autoedit.library.dna import check_pacing

    assert check_pacing([2.0, 9.0, 3.0, 8.0, 5.0, 6.0], 33 / 60, _DNA) == []
    assert check_pacing([5.0] * 10, 50 / 60, {"pacing": {}}) == []   # DNA rỗng
    assert check_pacing([], 1.0, _DNA) == []                          # không shot nào đặt được
    assert check_pacing([4.0], 10 / 60, _DNA) == []                   # 1 shot: std tự tắt (6 cut/phút trong ngưỡng)


def test_glm_api_url_default_intl_and_env_override(monkeypatch):
    """2026-07-10: mặc định server QUỐC TẾ api.z.ai (nhanh ~3x, ít đứt kết nối);
    env GLM_API_URL đè được để quay về server TQ mà không sửa code."""
    from autoedit.library import vision

    monkeypatch.delenv("GLM_API_URL", raising=False)
    assert vision.glm_api_url() == "https://api.z.ai/api/paas/v4/chat/completions"
    monkeypatch.setenv("GLM_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
    assert "bigmodel" in vision.glm_api_url()


def test_backup_cache_db_creates_and_prunes(tmp_path):
    """G1 kho chung: backup sổ trước mẻ nạp vào <data_root>/backup/, giữ `keep` bản mới nhất."""
    from autoedit.library.db import backup_cache_db

    src = tmp_path / "cache.db"
    assert backup_cache_db(src) is None  # db chưa tồn tại -> không nổ, không tạo gì
    assert not (tmp_path / "backup").exists()

    src.write_bytes(b"sqlite-fake" * 100)
    b1 = backup_cache_db(src, keep=3)
    assert b1 is not None and b1.is_file() and b1.parent == tmp_path / "backup"
    assert b1.read_bytes() == src.read_bytes()

    # 4 bản cũ giả (tên sort trước bản thật) -> gọi lần nữa với keep=3 phải prune
    for i in range(4):
        (tmp_path / "backup" / f"cache-2026010{i}-000000.db").write_bytes(b"old")
    b2 = backup_cache_db(src, keep=3)
    remaining = sorted((tmp_path / "backup").glob("cache-*.db"))
    assert len(remaining) == 3
    assert b2 in remaining  # bản vừa chụp luôn nằm trong nhóm giữ lại
