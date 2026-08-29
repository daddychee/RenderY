"""Test S4/M5 editor-learn — DNA scan (PB10/PB11/PB13) + mót file COPY-only.

Regression 3 draft SP1 (cổng M5): số scan phải ra ĐÚNG số đã công bố ở
PB10_AM_THANH_3_DRAFT_EDITOR.md §5/§7 — chỉ chạy trên máy có E:\\PROJECT NHAN BAN.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest
import yaml

from autoedit.editor_learn import dna as dnamod
from autoedit.editor_learn.mine import (
    HOLD_DIR,
    SFX_STAGING,
    SFX_STAGING_MANIFEST,
    classify,
    mine_draft,
    norm_name,
)

PLACE = "##_draftpath_placeholder_TEST-GUID_##/materials/"


def _seg(mid: str, start: float, dur: float, vol: float = 1.0) -> dict:
    return {"material_id": mid,
            "target_timerange": {"start": int(start * 1e6), "duration": int(dur * 1e6)},
            "volume": vol}


@pytest.fixture
def draft(tmp_path) -> Path:
    """Draft giả: voice 2 khúc (0-40, 60-100), nhạc + bed đặt cả bài, whoosh ×2
    (1 sát cut + ôm cut, 1 xa cut), SFX chủ thể trong voice, pop trong ô nghỉ."""
    root = tmp_path / "DRAFT X"
    mats = root / "materials"
    mats.mkdir(parents=True)
    audios = []

    def mat(mid: str, name: str, dur_s: float, touch: bool = True) -> None:
        if touch:
            (mats / name).write_bytes(b"fake-audio")
        audios.append({"id": mid, "name": name, "path": PLACE + name,
                       "duration": int(dur_s * 1e6)})

    mat("m_voice", "voice.mp3", 100)
    mat("m_music", "lắng đọng.mp3", 180)
    mat("m_bed", "ù ù vũ trụ.mp3", 200)
    mat("m_wh", "Swoosh.mp3", 1.7)
    mat("m_rocket", "rocket ignition.mp3", 8)
    mat("m_pop", "Pop-up tap.mp3", 1)
    mat("m_myst", "mystery texture 01.mp3", 5)
    mat("m_ghost", "ghost.mp3", 3, touch=False)   # material mất file media

    content = {
        "id": "test-draft", "duration": int(100 * 1e6),
        "materials": {"audios": audios},
        "tracks": [
            {"type": "audio", "segments": [_seg("m_voice", 0, 40), _seg("m_voice", 60, 40)]},
            {"type": "audio", "segments": [_seg("m_music", 0, 120, 0.08),
                                           _seg("m_bed", 0, 200, 0.10)]},
            {"type": "audio", "segments": [
                _seg("m_wh", 19.8, 1.7, 0.3),    # sát cut 20 (0.2s) + cut 20 nằm trong
                _seg("m_wh", 50.0, 1.2, 0.4),    # xa cut (45 cách 5s) — novoice
                _seg("m_rocket", 10, 8, 0.2),    # trọn trong voice -> voiced
                _seg("m_pop", 45, 1, 0.44),      # trong ô nghỉ 40-60 -> novoice
                _seg("m_myst", 30, 5, 0.5),      # voiced
                _seg("m_ghost", 90, 2, 0.6),     # voiced (DNA vẫn đo, mine báo missing)
            ]},
            {"type": "video", "segments": [_seg("v", 0, 20), _seg("v", 20, 25),
                                           _seg("v", 45, 25), _seg("v", 70, 30)]},
        ],
    }
    (root / "draft_content.json").write_text(
        json.dumps(content, ensure_ascii=False), encoding="utf-8")
    return root


# ---------------- DNA (PB13 + PB11) ----------------

def test_dna_scan(draft):
    d = dnamod.scan_draft(draft)
    assert d.draft == "DRAFT X"
    assert d.voice_span == (0.0, 100.0) and d.n_voice_tracks == 1
    assert sorted(d.music_vols) == [0.08, 0.10]
    assert sorted(d.sfx_vols["voiced"]) == [0.2, 0.5, 0.6]
    assert d.sfx_vols["novoice"] == [0.44]
    # whoosh tách khỏi nhóm SFX (PB13 in "bỏ whoosh")
    assert d.whoosh_ctx_vols["voiced"] == [0.3]
    assert d.whoosh_ctx_vols["novoice"] == [0.4]
    # PB11: cut = start segment track video chính (bỏ t=0)
    assert d.cuts_n == 3
    assert d.whoosh_n == 2
    assert d.whoosh_near_cut == 1
    assert d.cuts_inside_whoosh == 1
    assert sorted(round(x, 1) for x in d.whoosh_durs) == [1.2, 1.7]


def test_dna_empty_draft(tmp_path):
    (tmp_path / "draft_content.json").write_text(
        json.dumps({"duration": 0, "materials": {"audios": []}, "tracks": []}),
        encoding="utf-8")
    d = dnamod.scan_draft(tmp_path)
    assert d.whoosh_n == 0 and d.music_vols == [] and d.n_voice_tracks == 0


def test_profile_accumulate_idempotent(draft, tmp_path):
    prof_path = tmp_path / "editor_dna.json"
    d = dnamod.scan_draft(draft)
    dnamod.update_profile(prof_path, d)
    profile = dnamod.update_profile(prof_path, d)     # học lại cùng draft
    assert len(profile["drafts"]) == 1                # thay entry, không cộng đôi
    d2 = dnamod.scan_draft(draft)
    d2.draft = "DRAFT Y"
    d2.sfx_vols = {"voiced": [0.3], "novoice": [], "mixed": []}
    d2.music_vols = [0.12]
    profile = dnamod.update_profile(prof_path, d2)
    pooled = dnamod.pooled_stats(profile)
    assert pooled["n_drafts"] == 2
    assert pooled["voiced"]["n"] == 4                 # [0.2,0.5,0.6] + [0.3]
    assert pooled["voiced"]["median"] == pytest.approx(0.4)
    assert pooled["music"]["n"] == 3


# ---------------- Mót file (COPY-only) ----------------

def _tree(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*")}


def test_mine_classify_copy_manifest(draft, tmp_path):
    niche = tmp_path / "ambient" / "space"
    sfx_root = tmp_path / "sfx"
    music_root = tmp_path / "music_editor"
    before = _tree(draft)

    res = mine_draft(draft, niche, sfx_root, music_root)

    assert _tree(draft) == before                     # COPY-only: draft không đổi 1 file
    assert res.voice == ["voice.mp3"]
    assert res.missing == ["ghost.mp3"]
    assert sorted(res.ambient) == [("rocket", "rocket ignition.mp3"),
                                   ("space", "ù ù vũ trụ.mp3")]
    assert sorted(res.sfx) == [("pop", "Pop-up tap.mp3"), ("whoosh", "Swoosh.mp3")]
    assert res.music == ["lắng đọng.mp3"]
    assert res.hold == ["mystery texture 01.mp3"]
    # file nằm đúng chỗ
    assert (niche / "ù ù vũ trụ.mp3").is_file()
    assert (sfx_root / SFX_STAGING / "Swoosh.mp3").is_file()
    assert (music_root / "DRAFT X" / "lắng đọng.mp3").is_file()
    assert (niche / "raw" / HOLD_DIR / "mystery texture 01.mp3").is_file()
    # manifest đúng schema import + provenance editor:<draft>
    amb = yaml.safe_load((niche / "ambient_manifest.yaml").read_text(encoding="utf-8"))["ambient"]
    assert {(e["kind"], e["file"]) for e in amb} == {("rocket", "rocket ignition.mp3"),
                                                     ("space", "ù ù vũ trụ.mp3")}
    assert all(e["artlist_url"] == "editor:DRAFT X" for e in amb)
    sfx = yaml.safe_load((sfx_root / SFX_STAGING / SFX_STAGING_MANIFEST)
                         .read_text(encoding="utf-8"))["sfx"]
    assert {(e["kind"], e["file"]) for e in sfx} == {("pop", "Pop-up tap.mp3"),
                                                     ("whoosh", "Swoosh.mp3")}


def test_mine_rerun_all_known(draft, tmp_path):
    """Chạy lại cùng draft: mọi thứ đã trong kho -> 0 đề xuất mới, manifest không phình."""
    niche = tmp_path / "ambient" / "space"
    sfx_root = tmp_path / "sfx"
    music_root = tmp_path / "music_editor"
    mine_draft(draft, niche, sfx_root, music_root)
    res2 = mine_draft(draft, niche, sfx_root, music_root)
    assert res2.ambient == [] and res2.sfx == [] and res2.music == [] and res2.hold == []
    assert len(res2.known) == 6                       # 2 ambient + 2 sfx + 1 nhạc + 1 hold
    amb = yaml.safe_load((niche / "ambient_manifest.yaml").read_text(encoding="utf-8"))["ambient"]
    assert len(amb) == 2


def test_mine_dry_run_writes_nothing(draft, tmp_path):
    niche = tmp_path / "ambient" / "space"
    sfx_root = tmp_path / "sfx"
    music_root = tmp_path / "music_editor"
    res = mine_draft(draft, niche, sfx_root, music_root, dry_run=True)
    assert len(res.ambient) == 2 and len(res.sfx) == 2      # vẫn báo cáo đủ
    assert not niche.exists() and not sfx_root.exists() and not music_root.exists()


def test_mine_kind_name_collision_guard(tmp_path):
    """File editor tên trùng khuôn <kind>.wav -> đổi 'editor - <tên>' khi copy,
    list_variants của thư viện không nuốt file thô chưa chuẩn hóa."""
    from autoedit.ambient.library import list_variants

    root = tmp_path / "D2"
    (root / "materials").mkdir(parents=True)
    (root / "materials" / "fire.wav").write_bytes(b"x")
    (root / "materials" / "voice.mp3").write_bytes(b"x")
    content = {"duration": int(30 * 1e6),
               "materials": {"audios": [
                   {"id": "m1", "name": "fire.wav", "path": PLACE + "fire.wav",
                    "duration": int(5 * 1e6)},
                   {"id": "mv", "name": "voice.mp3", "path": PLACE + "voice.mp3",
                    "duration": int(30 * 1e6)}]},
               "tracks": [{"type": "audio", "segments": [_seg("mv", 0, 30)]},
                          {"type": "audio", "segments": [_seg("m1", 0, 5, 0.3)]}]}
    (root / "draft_content.json").write_text(json.dumps(content), encoding="utf-8")
    niche = tmp_path / "ambient" / "space"
    res = mine_draft(root, niche, tmp_path / "sfx", tmp_path / "music_editor")
    assert res.ambient == [("fire", "editor - fire.wav")]
    assert (niche / "editor - fire.wav").is_file()
    assert list_variants("fire", niche) == []
    # chạy lại: dedup qua title manifest (tên gốc fire.wav)
    res2 = mine_draft(root, niche, tmp_path / "sfx", tmp_path / "music_editor")
    assert res2.ambient == [] and res2.known == ["fire.wav"]


def test_classify_rules():
    from autoedit.editor_learn.mine import AudioUse

    def c(name, file_dur=3.0, max_seg=3.0, in_voice=False):
        return classify(AudioUse(name=name, path=None, file_dur_s=file_dur,
                                 max_seg_s=max_seg, in_voice_track=in_voice))

    assert c("hook.mp3") == ("voice", "")                          # hint tên
    assert c("x.mp3", in_voice=True) == ("voice", "")              # nằm track voice
    assert c("wind noise_whoosh 03.mp3", 1.2) == ("sfx", "whoosh")
    assert c("Long Heavy Whoosh Slow Buildup.aac", 9.0) == ("sfx", "swell")   # whoosh dài
    assert c("sôi sục mặt trời.mp3", 60, 60) == ("ambient", "fire")           # VN subject
    assert c("Rumble slow impact earth.mp3") == ("ambient", "rumble")         # subject trước sfx
    assert c("Data analysis (data display on screen).mp3") == ("sfx", "ding")
    assert c("The sound of the wind roaring low in a devastated space.mp3") \
        == ("ambient", "mountain_desert")                          # roaring thắng space/wind
    assert c("Crowd_Wall Street_01 (morning).mp3") == ("ambient", "people_activity")
    # bug SP1-012: "city" trong tên địa danh cướp tiếng côn trùng đêm về urban_street
    assert c("【Japanese nature sound 】Autumn Insect 2-Gentle Night Insect Chorus-"
             "Chuo City, Yamanashi Prefecture(1137829).mp3") \
        == ("ambient", "nature_forest_field")
    # "nature" KHÔNG phải keyword nature_forest_field — gió vẫn phải về sky_cloud
    assert c("Wind sound effects (nature, breeze, building style, etc.) 14.mp3") \
        == ("ambient", "sky_cloud")
    assert c("sâu lắng ambient.mp3", 150, 150) == ("ambient", "default")
    assert c("căng dần.mp3", 150, 150) == ("music", "")            # cả bài, không keyword
    assert c("tiếng lạ gì đó.mp3") == ("hold", "")
    assert c("Rockets, missiles, space shuttles, etc.") == ("ambient", "rocket")   # số nhiều
    assert c("Hugh! A really realistic fireworks rocket sound 3b") \
        == ("ambient", "explosion")                                # precedent mót tay
    assert c("Earth rumbling low frequency(1078575)") == ("ambient", "rumble")
    assert norm_name("Pop-up_tap_decision sound_09(806023).mp3") == "pop up tap decision sound 09(806023)"
    # 2 SFX kho CapCut chỉ khác id trong ngoặc — không được trùng danh tính (dedup oan)
    assert norm_name("Whoosh sound effect.(1424899)") != norm_name("Whoosh sound effect.(1424901)")
    assert norm_name("Whoosh sound effect.(1424899).mp3") == norm_name("Whoosh sound effect.(1424899)")


def test_classify_with_niche_rules():
    """Kind loài per-niche (subject_rules.yaml deepsea): classify nhận rules -> tên file
    editor (VN + EN, kể cả tách bằng _-) route đúng kind; không rules -> hold như cũ."""
    from autoedit.editor_learn.mine import AudioUse

    rules = (("whale_sperm", ("sperm whale", "cá nhà táng")),
             ("whale_humpback", ("humpback",)),
             ("splash", ("splash", "rơi xuống nước")))

    def c(name, rules=rules):
        return classify(AudioUse(name=name, path=None, file_dur_s=3.0,
                                 max_seg_s=3.0, in_voice_track=False), rules)

    assert c("cá nhà táng2.mp3") == ("ambient", "whale_sperm")
    # norm_name đổi _- thành space -> cụm 'sperm whale' vẫn khớp tên file Elevenlabs
    assert c("ANMLAqua-sperm_whale_clicking-Elevenlabs.mp3") == ("ambient", "whale_sperm")
    assert c("Rơi xuống nước mạnh.aac") == ("ambient", "splash")
    # whoosh hint vẫn XÉT TRƯỚC rules (whoosh attack tương lai -> sfx staging, người sort)
    assert c("Alien Monster Whoosh 01.aac") == ("sfx", "whoosh")
    # không rules (space) -> hành vi cũ: không match gì -> hold
    assert c("cá nhà táng2.mp3", rules=None) == ("hold", "")


def test_mine_capcut_cache_hash_names(tmp_path):
    """File SFX kho CapCut: đĩa tên hash md5, material tên có nghĩa -> copy mang tên
    material (+ đuôi từ file đĩa), dedup theo tên material khi chạy lại."""
    root = tmp_path / "D3"
    (root / "materials").mkdir(parents=True)
    (root / "materials" / "ab12cd34ef.mp3").write_bytes(b"x")
    (root / "materials" / "voice.mp3").write_bytes(b"x")
    content = {"duration": int(30 * 1e6), "materials": {"audios": [
        {"id": "m1", "name": "Buon (Whoosh movie) 7(1503716)",
         "path": PLACE + "ab12cd34ef.mp3", "duration": int(1.2 * 1e6)},
        {"id": "mv", "name": "voice.mp3", "path": PLACE + "voice.mp3",
         "duration": int(30 * 1e6)}]},
        "tracks": [{"type": "audio", "segments": [_seg("mv", 0, 30)]},
                   {"type": "audio", "segments": [_seg("m1", 3, 1.2, 0.3)]}]}
    (root / "draft_content.json").write_text(
        json.dumps(content, ensure_ascii=False), encoding="utf-8")
    sfx_root = tmp_path / "sfx"
    res = mine_draft(root, tmp_path / "amb" / "space", sfx_root, tmp_path / "music_editor")
    assert res.sfx == [("whoosh", "Buon (Whoosh movie) 7(1503716).mp3")]
    assert (sfx_root / SFX_STAGING / "Buon (Whoosh movie) 7(1503716).mp3").is_file()
    res2 = mine_draft(root, tmp_path / "amb" / "space", sfx_root, tmp_path / "music_editor")
    assert res2.sfx == [] and res2.known == ["Buon (Whoosh movie) 7(1503716)"]


# ---------------- Regression 3 draft SP1 (cổng M5 — số PB10/PB11/PB13) ----------------

SP1_ROOT = Path(r"E:\PROJECT NHAN BAN\SPACE 1")
SP1_EXPECT = {
    # PB13 (PB10 doc §7): nhạc median · SFX đè voice (n, median, bỏ whoosh) · SFX không voice
    # PB11 (PB10 doc §5): whoosh n · dur median · vol median · cut n · sát cut ≤0.5s · cut trong whoosh
    "SP1 - 001": {"music": 0.10, "voiced": (45, 0.25), "novoice": (1, 1.00),
                  "wh": 40, "dur": 1.70, "vol": 0.32, "cuts": 120, "near": 10, "inside": 17},
    "SP1 - 003": {"music": 0.09, "voiced": (33, 0.28), "novoice": (1, 0.26),
                  "wh": 25, "dur": 3.47, "vol": 0.18, "cuts": 232, "near": 5, "inside": 12},
    "SP1 - 004": {"music": 0.06, "voiced": (33, 0.17), "novoice": (12, 0.32),
                  "wh": 23, "dur": 2.13, "vol": 0.20, "cuts": 263, "near": 7, "inside": 4},
}


@pytest.mark.skipif(not SP1_ROOT.is_dir(), reason="3 draft editor SP1 chỉ có trên máy chính")
@pytest.mark.parametrize("name", sorted(SP1_EXPECT))
def test_regression_sp1_dna(name):
    exp = SP1_EXPECT[name]
    d = dnamod.scan_draft(SP1_ROOT / name)
    assert round(statistics.median(d.music_vols), 2) == exp["music"]
    assert (len(d.sfx_vols["voiced"]),
            round(statistics.median(d.sfx_vols["voiced"]), 2)) == exp["voiced"]
    assert (len(d.sfx_vols["novoice"]),
            round(statistics.median(d.sfx_vols["novoice"]), 2)) == exp["novoice"]
    assert d.whoosh_n == exp["wh"]
    assert round(statistics.median(d.whoosh_durs), 2) == exp["dur"]
    assert round(statistics.median(d.whoosh_vols), 2) == exp["vol"]
    assert d.cuts_n == exp["cuts"]
    assert d.whoosh_near_cut == exp["near"]
    assert d.cuts_inside_whoosh == exp["inside"]
