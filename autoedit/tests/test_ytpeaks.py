"""Test ytpeaks (YTREF M1) — dò đỉnh heatmap giả lập + THẬT (fixture, không mạng),
rút YouTube ID, urls.txt, đối chiếu duration, fetch fail-open."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoedit.library import ytpeaks
from autoedit.library.ytpeaks import (
    _detect,
    _id_from_url,
    duration_mismatch,
    extract_youtube_id,
    fetch_video_info,
    load_urls_txt,
    resolve_youtube_id,
)

FIXTURE = Path(__file__).parent / "data" / "ytref_TY9dnrbQano.json"


def _heatmap(vals: list[float], bin_s: float = 10.0) -> list[dict]:
    return [{"start_time": i * bin_s, "end_time": (i + 1) * bin_s, "value": v}
            for i, v in enumerate(vals)]


# ----------------------------- _detect (heatmap giả lập) ----------------------
def test_detect_single_peak_foot_and_apex():
    peaks = _detect(_heatmap([0.1, 0.1, 0.3, 0.6, 1.0, 0.5, 0.2, 0.1, 0.1]))
    assert len(peaks) == 1
    p = peaks[0]
    # chân = điểm bắt đầu dốc lên (index 1), đỉnh = index 4
    assert (p.foot_time, p.apex_time, p.type) == (10.0, 40.0, "primary")
    assert p.foot_time < p.apex_time
    assert p.apex_end == 50.0   # end_time BIN đỉnh — ingest neo cắt giữa bin (fix 2026-07-11)


def test_detect_boundary_spike_no_rising_slope_dropped():
    # t=0 luôn =1.0 trên heatmap thật — dốc xuống từ biên không có chân -> bỏ sạch
    assert _detect(_heatmap([1.0, 0.9, 0.3, 0.3, 0.3, 0.3])) == []


def test_detect_flat_and_too_short():
    assert _detect(_heatmap([0.5, 0.5, 0.5, 0.5, 0.5])) == []
    assert _detect(_heatmap([0.1, 0.9])) == []


def test_detect_nms_suppresses_peak_within_20s():
    # bin 6s: apex 12s (0.8) và 24s (1.0) cách 12s < MIN_GAP -> giữ đỉnh cao hơn
    peaks = _detect(_heatmap(
        [0.1, 0.4, 0.8, 0.5, 1.0, 0.3, 0.1, 0.2, 0.9, 0.4, 0.1], bin_s=6.0))
    assert [p.value for p in peaks] == [1.0, 0.9]
    assert [p.apex_time for p in peaks] == [24.0, 48.0]


def test_detect_classification_thresholds():
    # đỉnh cách nhau 30s (thoát NMS): 1.0 / 0.7 / 0.4 so đỉnh cao nhất
    peaks = _detect(_heatmap([0.1, 1.0, 0.1, 0.7, 0.1, 0.4, 0.1], bin_s=30.0))
    assert [p.type for p in peaks] == ["primary", "secondary", "minor"]


# ----------------------------- _detect (heatmap THẬT M0) ----------------------
def test_detect_real_heatmap_matches_m0_smoke():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    peaks = _detect(data["heatmap"])
    # số M0 đã kiểm mắt trên YouTube: đỉnh thật 13:04 (784s) value 1.00
    top = peaks[0]
    assert top.type == "primary" and top.value == 1.0
    assert abs(top.apex_time - 784.3) < 1.0
    assert top.foot_time < top.apex_time
    # bin thật ~9.12s (911s/100) — apex_end phải là mép PHẢI bin, không rỗng
    assert 8.0 < top.apex_end - top.apex_time < 16.0
    # 5 đỉnh primary/secondary như smoke; minor phần còn lại
    assert len([p for p in peaks if p.type != "minor"]) == 5


# ----------------------------- fetch_video_info -------------------------------
def test_fetch_fail_open_on_error(monkeypatch):
    def boom(url):
        raise RuntimeError("yt-dlp lỗi: network down")
    monkeypatch.setattr(ytpeaks, "_dump_json", boom)
    info = fetch_video_info("TY9dnrbQano")
    assert info.error and info.peaks == [] and not info.heatmap_available
    assert info.video_id == "TY9dnrbQano"


def test_fetch_full_info_from_fixture(monkeypatch):
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    monkeypatch.setattr(ytpeaks, "_dump_json", lambda url: data)
    info = fetch_video_info("TY9dnrbQano")
    assert info.title == "What China Found on The Moon"
    assert info.duration == 911.0
    assert [c["title"] for c in info.chapters] == [
        "Intro", "The Moon", "The Far Side", "The Cube", "Lava", "Water"]
    assert info.heatmap_available
    # mặc định BỎ minor (y tool ME)
    assert len(info.peaks) == 5
    assert all(p.type in ("primary", "secondary") for p in info.peaks)


def test_fetch_reads_channel_uploader_fallback(monkeypatch):
    """VD4 ghi công: yt-dlp --dump-json có sẵn channel/uploader — trước 2026-07-17
    code fetch mà bỏ qua field này (segment→kênh đứt ở mắt xích cuối)."""
    monkeypatch.setattr(ytpeaks, "_dump_json",
                        lambda url: {"title": "T", "duration": 10, "channel": "Kurzgesagt"})
    assert fetch_video_info("TY9dnrbQano").channel == "Kurzgesagt"
    monkeypatch.setattr(ytpeaks, "_dump_json",
                        lambda url: {"title": "T", "duration": 10, "uploader": "Astrum"})
    assert fetch_video_info("TY9dnrbQano").channel == "Astrum"
    monkeypatch.setattr(ytpeaks, "_dump_json", lambda url: {"title": "T", "duration": 10})
    assert fetch_video_info("TY9dnrbQano").channel == ""


def test_fetch_no_heatmap_no_chapters_keeps_title(monkeypatch):
    # 2/3 video M0 không có heatmap/chapters -> fail-open chỉ-tiêu-đề là bắt buộc (§3i)
    monkeypatch.setattr(ytpeaks, "_dump_json",
                        lambda url: {"title": "Moon Doc", "duration": 600,
                                     "chapters": None, "heatmap": None})
    info = fetch_video_info("bdygcDw-NM8")
    assert info.title == "Moon Doc" and info.duration == 600.0
    assert info.chapters == [] and info.peaks == [] and not info.heatmap_available
    assert info.error == ""


# ----------------------------- rút ID (§3b) -----------------------------------
def test_extract_id_ytdown_pattern():
    name = "Whats-Actually-on-the-Fa_Media_bdygcDw_NM8_001_1080p.mp4"
    assert extract_youtube_id(name) == "bdygcDw_NM8"


def test_extract_id_standalone_token():
    assert extract_youtube_id("Moon doc [TY9dnrbQano].mp4") == "TY9dnrbQano"
    # nhiều token đứng riêng -> lấy token CUỐI (ID thường sát đuôi tên)
    assert extract_youtube_id("abcdefghijk TY9dnrbQano.mp4") == "TY9dnrbQano"


def test_extract_id_none_for_plain_names():
    assert extract_youtube_id("SP1 - 003 final.mp4") is None
    # run dài ký tự hợp lệ dính liền không phải token đứng riêng
    assert extract_youtube_id("clip_scene_00_long_name.mp4") is None


def test_id_from_url_variants():
    assert _id_from_url("https://www.youtube.com/watch?v=TY9dnrbQano&t=5s") == "TY9dnrbQano"
    assert _id_from_url("https://youtu.be/bdygcDw-NM8") == "bdygcDw-NM8"
    assert _id_from_url("https://www.youtube.com/shorts/TY9dnrbQano") == "TY9dnrbQano"
    assert _id_from_url("TY9dnrbQano") == "TY9dnrbQano"
    assert _id_from_url("https://example.com/x") is None


def test_urls_txt_and_resolve(tmp_path):
    (tmp_path / "urls.txt").write_text(
        "moon.mp4 = https://www.youtube.com/watch?v=TY9dnrbQano\n"
        "far side.mp4 = https://youtu.be/bdygcDw-NM8\n"
        "dòng hỏng không có dấu bằng\n"
        "bad.mp4 = https://example.com/x\n", encoding="utf-8")
    assert load_urls_txt(tmp_path) == {
        "moon.mp4": "TY9dnrbQano", "far side.mp4": "bdygcDw-NM8"}
    # tên file không chứa ID -> tra urls.txt cạnh file
    assert resolve_youtube_id(tmp_path / "moon.mp4") == "TY9dnrbQano"
    # tên file chứa ID -> khỏi cần urls.txt
    assert resolve_youtube_id(tmp_path / "x [TY9dnrbQano].mp4") == "TY9dnrbQano"
    assert resolve_youtube_id(tmp_path / "khongcoid.mp4") is None


def test_resolve_without_urls_txt(tmp_path):
    assert resolve_youtube_id(tmp_path / "khongcoid.mp4") is None
    # trade-off spec §3b đã chấp nhận: chuỗi thường ĐÚNG 11 ký tự đứng riêng vẫn bị
    # rút nhầm thành ID ("khong-co-id") — tầng đối chiếu duration §3d chặn hạ nguồn
    assert extract_youtube_id("khong-co-id.mp4") == "khong-co-id"


# ----------------------------- đối chiếu duration (§3d) -----------------------
def test_duration_mismatch():
    assert not duration_mismatch(910.5, 911.0)   # lệch 0,05% — ok
    assert duration_mismatch(880.0, 911.0)       # lệch 3,4% — file bị cắt đầu/đuôi
    assert duration_mismatch(0.0, 911.0)         # thiếu số đối chiếu -> bảo thủ
    assert duration_mismatch(911.0, 0.0)
