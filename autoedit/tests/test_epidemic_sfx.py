"""Test nạp SFX Epidemic Sound -> kho ambient per-niche.

Khuôn theo test_ambient.py (WAV thật nhỏ + normalize_audio chạy ffmpeg thật).
Client MCP bị fake — KHÔNG gọi mạng thật trong test.

3 test hồi quy tái hiện bẫy ĐO THẬT 2026-07-18 (P5 cổng hồi quy):
- term phải LỒNG trong query (gọi phẳng -> server lặng lẽ trả list mặc định)
- key tài khoản free: search OK nhưng download FORBIDDEN
- assetUrl hết hạn ~60s -> tải lỗi phải xóa file cụt, không để ffmpeg nuốt
"""

from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path

import pytest
import yaml

from autoedit.ambient.epidemic import EpidemicClient, EpidemicError, SoundEffect
from autoedit.ambient.epidemic_fetch import fetch_to_niche, parse_plan, title_matches
from autoedit.ambient.library import RECORDS_FILE, list_variants


def _wav(path: Path, sec: float = 0.3) -> None:
    rate = 48000
    frames = bytearray()
    for i in range(int(sec * rate)):
        frames += struct.pack("<h", int(6000 * math.sin(2 * math.pi * 220 * i / rate)))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(bytes(frames))


class FakeClient:
    """Client giả: search trả n kết quả, download ghi WAV thật ra đích."""

    def __init__(self, per_term: int = 2, fail_download: str | None = None):
        self.per_term = per_term
        self.fail_download = fail_download
        self.searched: list[tuple[str, int]] = []

    def search(self, term, limit=10, min_s=None, max_s=None):
        self.searched.append((term, limit))
        return [SoundEffect(id=f"id-{term}-{i}", title=f"Animals, {term.title()} 0{i}",
                            duration_s=5.0 + i)
                for i in range(min(self.per_term, limit))]

    def download(self, effect, dest, filetype="MP3"):
        if self.fail_download and self.fail_download in effect.title:
            raise EpidemicError(f"Tải '{effect.title}' lỗi: link hết hạn")
        _wav(dest)
        return dest


@pytest.fixture
def niche(tmp_path):
    d = tmp_path / "ambient" / "life-in"
    d.mkdir(parents=True)
    return d


# --- parse_plan --------------------------------------------------------------

def test_parse_plan_ba_dang_cu_phap():
    plans = parse_plan(["camel", "wind=desert wind", "market=busy market:5"])
    assert (plans[0].kind, plans[0].term, plans[0].limit) == ("camel", "camel", 3)
    assert (plans[1].kind, plans[1].term, plans[1].limit) == ("wind", "desert wind", 3)
    assert (plans[2].kind, plans[2].term, plans[2].limit) == ("market", "busy market", 5)


def test_parse_plan_term_co_dau_hai_cham_khong_phai_so():
    """"a=b:c" — ':c' không phải số thì thuộc TERM, không nuốt thành limit."""
    (plan,) = parse_plan(["wind=storm:heavy"])
    assert plan.term == "storm:heavy" and plan.limit == 3


# --- fetch_to_niche: happy path ---------------------------------------------

def test_fetch_nap_vao_kho_va_chuan_hoa_wav(niche):
    client = FakeClient(per_term=2)
    res = fetch_to_niche(parse_plan(["water=water splash"]), niche, client=client)

    assert len(res.downloaded) == 2 and not res.failed
    assert len(res.imported) == 2 and not res.import_failed
    # đặt tên biến thể do library lo: water.wav, water_2.wav
    assert [p.name for p in list_variants("water", niche)] == ["water.wav", "water_2.wav"]
    # chuẩn hóa C4: WAV PCM 48k
    with wave.open(str(niche / "water.wav")) as w:
        assert w.getframerate() == 48000 and w.getsampwidth() == 2


def test_fetch_ghi_link_epidemic_de_truy_license(niche):
    fetch_to_niche(parse_plan(["fire"]), niche, client=FakeClient(per_term=1))
    recs = yaml.safe_load((niche / RECORDS_FILE).read_text(encoding="utf-8"))["ambient"]
    assert recs[0]["artlist_url"].startswith("https://www.epidemicsound.com/sound-effects/")
    assert recs[0]["kind"] == "fire"


def test_fetch_dry_run_khong_dung_kho(niche):
    res = fetch_to_niche(parse_plan(["fire"]), niche, client=FakeClient(), dry_run=True)
    assert res.downloaded and not res.imported
    assert list_variants("fire", niche) == []


def test_fetch_target_bo_qua_kind_da_du(niche):
    _wav(niche / "fire.wav")
    _wav(niche / "fire_2.wav")
    client = FakeClient()
    res = fetch_to_niche(parse_plan(["fire"]), niche, client=client, target_per_kind=2)
    assert res.skipped and not res.downloaded
    assert client.searched == []  # không gọi API khi đã đủ


def test_fetch_kind_khong_hop_le_bao_loi_khong_ghi_kho(niche):
    res = fetch_to_niche(parse_plan(["khong_ton_tai"]), niche, client=FakeClient())
    assert res.failed and "không hợp lệ" in res.failed[0][1]
    assert not res.imported


def test_fetch_mot_file_loi_van_nap_cac_file_con_lai(niche):
    """Tải hỏng 1 file không được giết cả mẻ (khuôn fail-open như sourcer)."""
    client = FakeClient(per_term=2, fail_download="01")
    res = fetch_to_niche(parse_plan(["water"]), niche, client=client)
    assert len(res.failed) == 1 and len(res.imported) == 1


# --- hồi quy: 3 bẫy đo thật --------------------------------------------------

def test_hoi_quy_term_long_trong_query(monkeypatch):
    """BẪY 1: `term` phẳng ở cấp trên cùng -> server bỏ qua, mọi term ra cùng kết quả."""
    seen = {}

    def fake_tool(self, name, arguments):
        seen.update(arguments)
        return {"soundEffects": {"nodes": []}}

    monkeypatch.setattr(EpidemicClient, "_tool", fake_tool)
    EpidemicClient(key="k").search("camel", limit=4)
    assert seen["query"] == {"term": "camel"}, "term phải LỒNG trong query"
    assert "term" not in seen, "term KHÔNG được để phẳng ở cấp trên cùng"


def test_hoi_quy_key_free_bao_loi_ro_rang(monkeypatch):
    """BẪY 2: tài khoản free search được nhưng download FORBIDDEN — thông điệp phải
    chỉ đúng nguyên nhân (tài khoản), không để user đi sửa cú pháp."""
    def fake_post(self, payload):
        body = {"errors": [{"message": "You don't have permission to download this asset",
                            "extensions": {"code": "FORBIDDEN"}}], "data": None}
        env = {"jsonrpc": "2.0", "id": 2,
               "result": {"content": [{"type": "text", "text": json.dumps(body)}]}}
        return "sid", f"data: {json.dumps(env)}\n"

    monkeypatch.setattr(EpidemicClient, "_post", fake_post)
    client = EpidemicClient(key="k")
    client._sid = "sid"
    with pytest.raises(EpidemicError, match="TRẢ PHÍ"):
        client.download(SoundEffect("i", "t", 1.0), Path("x.mp3"))


def test_hoi_quy_tai_loi_xoa_file_cut(monkeypatch, tmp_path):
    """BẪY 3: link hết hạn ~60s — tải dở phải xóa file cụt, đừng để ffmpeg nuốt."""
    dest = tmp_path / "a.mp3"

    monkeypatch.setattr(EpidemicClient, "_tool",
                        lambda self, n, a: {"soundEffectDownload": {"assetUrl": "https://x/y"}})

    def boom(url, timeout=0):
        dest.write_bytes(b"\x00" * 10)   # file cụt đã rơi ra đĩa
        raise OSError("connection reset")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    client = EpidemicClient(key="k")
    with pytest.raises(EpidemicError):
        client.download(SoundEffect("i", "t", 1.0), dest)
    assert not dest.exists(), "file cụt phải bị xóa"


# --- lưới loài (title_matches) — ca THẬT từ dry-run 2026-07-18 -----------------

@pytest.mark.parametrize("title,kind,term,ok", [
    # ĐÚNG loài — phải nhận
    ("Birds, Sea, Penguin Vocalization, Close, Short", "penguin", "penguin call", True),
    ("Birds, Bird Of Prey, Vulture, Black Headed Threatened", "vulture", "vulture bird call", True),
    ("Birds, Sea, Seagulls, Call, Group", "seagull", "seagull", True),      # số nhiều
    ("Machines, Escalator, Indoor, Rhythmic", "escalator", "escalator moving", True),
    ("Vehicles, Misc, Snowmobile, Pass By, Engine", "snowmobile", "snowmobile engine", True),
    # LỆCH loài — phải loại (nạp mù thì penguin.wav kêu tiếng vịt = RD-89)
    ("Birds, Fowl, Goose, Call, Movement", "penguin", "penguin call", False),
    ("Toys, Misc, Duck, Duck Call, Cartoony 01", "penguin", "penguin call", False),
    ("Birds, Fowl, Currawong Call", "vulture", "vulture bird call", False),
    ("Birds, Fowl, Duck, Mallard, Quack", "vulture", "vulture bird call", False),
])
def test_luoi_loai_ca_that(title, kind, term, ok):
    assert title_matches(title, kind, term) is ok


def test_luoi_loai_chan_truoc_khi_tai(niche):
    """Kết quả lệch loài bị loại TRƯỚC khi tốn băng thông tải."""
    class Lech(FakeClient):
        def search(self, term, limit=10, min_s=None, max_s=None):
            return [SoundEffect("i1", "Birds, Sea, Penguin Vocalization", 4.2),
                    SoundEffect("i2", "Birds, Fowl, Goose, Call", 4.5)]

    res = fetch_to_niche(parse_plan(["water=penguin call"]), niche, client=Lech())
    assert len(res.downloaded) == 1 and "Penguin" in res.downloaded[0]
    assert len(res.rejected) == 1 and "Goose" in res.rejected[0]
    assert len(list_variants("water", niche)) == 1


def test_loose_tat_luoi_loai(niche):
    class Lech(FakeClient):
        def search(self, term, limit=10, min_s=None, max_s=None):
            return [SoundEffect("i2", "Birds, Fowl, Goose, Call", 4.5)]

    res = fetch_to_niche(parse_plan(["water=penguin call"]), niche,
                         client=Lech(), strict=False)
    assert len(res.downloaded) == 1 and not res.rejected


# --- cờ --no-epidemic: editor bật/tắt mỗi lần dựng --------------------------

def test_epidemic_files_doc_dung_nguon(niche):
    """Nhận diện file Epidemic qua artlist_url trong records."""
    from autoedit.ambient.library import epidemic_files

    fetch_to_niche(parse_plan(["fire"]), niche, client=FakeClient(per_term=1))
    _wav(niche / "fire_2.wav")  # file kho CŨ (không có trong records)
    assert epidemic_files(niche) == frozenset({"fire.wav"})


def test_no_epidemic_bo_qua_file_epidemic(niche):
    """Tắt -> list_variants không trả file Epidemic, file kho cũ VẪN dùng."""
    from autoedit.ambient.library import epidemic_files, list_variants

    fetch_to_niche(parse_plan(["fire"]), niche, client=FakeClient(per_term=1))
    _wav(niche / "fire_2.wav")
    skip = epidemic_files(niche)
    assert [p.name for p in list_variants("fire", niche)] == ["fire.wav", "fire_2.wav"]
    assert [p.name for p in list_variants("fire", niche, skip)] == ["fire_2.wav"]


def test_no_epidemic_khong_lam_kho_trong_khi_chi_co_epidemic(niche):
    """Kind CHỈ có file Epidemic -> tắt thì kind đó rỗng (tầng tự im, không crash)."""
    from autoedit.ambient.library import epidemic_files, list_variants

    fetch_to_niche(parse_plan(["fire"]), niche, client=FakeClient(per_term=2))
    assert list_variants("fire", niche, epidemic_files(niche)) == []


def test_epidemic_skip_bat_thi_khong_doc_records(niche, monkeypatch):
    """BẬT (`--epidemic`) -> trả None, KHÔNG tốn công đọc yaml."""
    from autoedit.packager import assembler

    class P:
        use_epidemic_sfx = True

    def no_call(*a, **k):
        raise AssertionError("bật thì không được đọc records")

    monkeypatch.setattr("autoedit.ambient.library.epidemic_files", no_call)
    assert assembler._epidemic_skip(P(), niche) is None


def test_epidemic_skip_tat_thi_tra_danh_sach(niche):
    from autoedit.packager import assembler

    fetch_to_niche(parse_plan(["fire"]), niche, client=FakeClient(per_term=1))

    class P:
        use_epidemic_sfx = False

    assert assembler._epidemic_skip(P(), niche) == frozenset({"fire.wav"})


def test_project_json_cu_van_load_duoc_va_mac_dinh_tat(tmp_path):
    """project.json CŨ (không có key use_epidemic_sfx) phải load được và MẶC ĐỊNH TẮT.

    📌 ĐẢO KỲ VỌNG 2026-07-18 (user chốt mặc định TẮT): trước đây test này khẳng định
    "mặc định BẬT" để thêm field không lật ngầm draft cũ. Nay luật đổi — project CŨ dựng
    lại phải theo luật MỚI (tắt), nên chỗ chặn thật nằm ở `assembler._epidemic_skip`
    (`getattr(..., False)`): sửa mỗi project.py là VÔ ÍCH, draft cũ vẫn bật qua đó."""
    from autoedit.project import Project

    cu = {"project_id": "x", "project_dir": str(tmp_path), "name": "n", "title": "t",
          "created_at": "2026-07-18T00:00:00",
          "inputs": {"script_path": "s.txt", "voice_path": "v.mp3",
                     "original_script_path": "s.txt", "original_voice_path": "v.mp3",
                     "script_text": "xin chao", "voice_duration_sec": 1.0}}
    (tmp_path / "project.json").write_text(json.dumps(cu), encoding="utf-8")
    assert Project.load(tmp_path).use_epidemic_sfx is False
    # Chốt chặn THẬT: project cũ (thiếu field hẳn) đi qua assembler cũng phải TẮT
    from autoedit.packager import assembler

    class Cu:                       # object KHÔNG có field -> đi nhánh getattr mặc định
        pass

    assert assembler._epidemic_skip(Cu(), tmp_path) is not None


def test_hoi_quy_title_dai_trung_dau_khong_de_nhau():
    """BẪY 6 (dính thật market_8/9 + boat_9/10 2026-07-18): 2 SFX KHÁC nhau có title
    dài trùng 60 ký tự đầu -> cùng tên file thô -> file sau ĐÈ file trước trong folder
    tạm -> kho nhận 2 bản y hệt (md5 trùng). Slug phải gắn id để phân biệt."""
    a = SoundEffect("aaaaaaaa-1111", "Ambience, Market, Farmers Market, Vendors Shouting, People Talking 01", 5.0)
    b = SoundEffect("bbbbbbbb-2222", "Ambience, Market, Farmers Market, Vendors Shouting, People Talking 02", 5.0)
    assert a.slug != b.slug


def test_hai_sfx_title_trung_dau_nap_thanh_2_file_khac_nhau(niche):
    """Đầu-cuối: 2 title trùng 60 ký tự đầu phải ra 2 file kho có nội dung KHÁC nhau."""
    class TrungTitle(FakeClient):
        def search(self, term, limit=10, min_s=None, max_s=None):
            long = "Ambience, Market, Farmers Market, Vendors Shouting, People Talking"
            return [SoundEffect("aaaaaaaa-1", f"{long} 01", 5.0),
                    SoundEffect("bbbbbbbb-2", f"{long} 02", 5.0)]

        def download(self, effect, dest, filetype="MP3"):
            # độ dài khác nhau -> nội dung khác nhau, đè nhau là lộ ngay
            _wav(dest, sec=0.3 if effect.id.startswith("a") else 0.5)
            return dest

    res = fetch_to_niche(parse_plan(["water=farmers market"]), niche,
                         client=TrungTitle(), strict=False)
    assert len(res.imported) == 2
    files = list_variants("water", niche)
    assert len(files) == 2
    assert files[0].read_bytes() != files[1].read_bytes(), "2 SFX khác nhau bị đè thành 1"


def test_key_thieu_bao_cach_tao_lai(monkeypatch):
    """Key hết hạn 30 ngày — lỗi phải chỉ chỗ tạo lại, không chết câm."""
    monkeypatch.delenv("EPIDEMIC_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: None)
    with pytest.raises(EpidemicError, match="account/api-keys"):
        EpidemicClient()
