"""Test nguồn video mẫu YouTube (RenderY) — thuần logic, không gọi mạng/ffmpeg.

Đây là nguồn DUY NHẤT không có quyền sử dụng, nên test khoá chặt 2 thứ:
trần tỉ trọng (không được vượt) và sổ nguồn gốc (phải truy ngược được clip nào
cắt từ video nào, giây nào).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from autoedit.library.ytpeaks import Peak, YTVideoInfo
from autoedit.sourcer.ytref import (
    MAX_CLIP,
    MIN_CLIP,
    YtClip,
    parse_links,
    plan_cuts,
    source_mix,
    video_ids,
    write_ledger,
)


def _info(peaks, duration=600.0, heatmap=True) -> YTVideoInfo:
    return YTVideoInfo(video_id="vid12345678", title="T", channel="C",
                       duration=duration, heatmap_available=heatmap, peaks=peaks)


def _peak(foot, apex, value=1.0, ptype="primary", apex_end=0.0) -> Peak:
    return Peak(foot_time=foot, apex_time=apex, value=value, type=ptype, apex_end=apex_end)


# ------------------------------ parse link ----------------------------------
def test_parse_links_bo_dong_trong_va_ghi_chu():
    text = ("# video đối thủ\n"
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ\n"
            "\n"
            "   https://youtu.be/abcdefghijk   \n"
            "# ghi chú cuối\n")
    assert parse_links(text) == ["https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                                 "https://youtu.be/abcdefghijk"]


def test_video_ids_rut_id_va_khu_trung():
    got = video_ids([
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",       # trùng -> bỏ
        "https://www.youtube.com/shorts/abcdefghijk",
    ])
    assert got == ["dQw4w9WgXcQ", "abcdefghijk"]


def test_video_ids_bo_link_rac():
    assert video_ids(["https://example.com/abc", "linh tinh"]) == []


# ------------------------------ plan_cuts -----------------------------------
def test_khong_co_dinh_thi_khong_cat():
    assert plan_cuts(_info([]), 0.15) == []


def test_duration_0_khong_no():
    assert plan_cuts(_info([_peak(10, 20)], duration=0.0), 0.15) == []


def test_clip_kep_trong_min_max():
    """Đỉnh rất rộng -> clip vẫn không quá MAX_CLIP; đỉnh hẹp -> tối thiểu MIN_CLIP."""
    cuts = plan_cuts(_info([_peak(10, 100), _peak(200, 200.2)]), 0.5)
    for start, end, _ in cuts:
        assert MIN_CLIP <= end - start <= MAX_CLIP


def test_ton_trong_tran_ti_trong():
    """TRẦN LÀ LUẬT CỨNG — tổng thời lượng cắt không được vượt budget."""
    peaks = [_peak(i * 30.0, i * 30.0 + 5.0) for i in range(20)]
    info = _info(peaks, duration=600.0)
    for budget in (0.08, 0.15, 0.20):
        cuts = plan_cuts(info, budget)
        assert sum(e - s for s, e, _ in cuts) <= info.duration * budget + 1e-6


def test_tran_0_thi_khong_cat_gi():
    assert plan_cuts(_info([_peak(10, 20)]), 0.0) == []


def test_uu_tien_dinh_manh_truoc():
    """Ngân sách chỉ đủ 1 clip -> phải là đỉnh primary, không phải secondary."""
    info = _info([_peak(300, 305, 0.6, "secondary"), _peak(10, 15, 1.0, "primary")],
                 duration=100.0)
    cuts = plan_cuts(info, 0.10)   # 10s ngân sách
    assert len(cuts) == 1
    assert cuts[0][2] == "primary"


def test_ket_qua_sap_theo_thoi_gian():
    info = _info([_peak(400, 405), _peak(10, 15), _peak(200, 205)], duration=600.0)
    cuts = plan_cuts(info, 0.5)
    assert [s for s, _, _ in cuts] == sorted(s for s, _, _ in cuts)


def test_dinh_sat_cuoi_video_bi_bo():
    """Không đủ MIN_CLIP trước khi hết video -> bỏ, đừng cắt clip cụt."""
    info = _info([_peak(99.0, 99.5)], duration=100.0)
    assert plan_cuts(info, 0.5) == []


def test_dung_apex_end_khi_co():
    """value đo trên CẢ BIN -> apex_end cho biết bin kết thúc ở đâu."""
    cuts = plan_cuts(_info([_peak(10, 12, apex_end=16.0)], duration=600.0), 0.5)
    assert len(cuts) == 1
    assert cuts[0][1] == pytest.approx(17.0)   # apex_end 16 + LEAD_IN 1


# ------------------------------ asset_key -----------------------------------
def test_asset_key_truy_nguoc_duoc():
    c = YtClip(path=Path("x.mp4"), video_id="dQw4w9WgXcQ",
               start=125.3, end=133.1, peak_type="primary")
    assert c.asset_key == "ytref:dQw4w9WgXcQ@t=125.3-133.1"
    assert c.duration == pytest.approx(7.8)


def test_candidate_dung_shape_stockclient():
    c = YtClip(path=Path("x.mp4"), video_id="vid12345678", start=1.0, end=5.0,
               peak_type="secondary", title="Tiêu đề", channel="Kênh")
    cand = c.as_candidate()
    assert cand["source"] == "ytref"
    assert cand["media_type"] == "video"
    assert cand["asset_key"].startswith("ytref:")
    assert cand["duration"] == pytest.approx(4.0)
    assert "Tiêu đề" in cand["description"]


# ------------------------------ sổ nguồn gốc --------------------------------
def test_so_ghi_du_dau_vet(tmp_path):
    clips = [YtClip(path=tmp_path / "a.mp4", video_id="dQw4w9WgXcQ", start=10.0,
                    end=17.0, peak_type="primary", title="Video A", channel="Kênh A")]
    dest = write_ledger(clips, tmp_path / "ytref_ledger.json")
    rows = json.loads(dest.read_text(encoding="utf-8"))

    assert len(rows) == 1
    r = rows[0]
    assert r["video_id"] == "dQw4w9WgXcQ"
    assert r["start"] == 10.0 and r["end"] == 17.0
    assert r["channel"] == "Kênh A"
    # URL nhảy đúng giây trong video gốc -> mở là kiểm chứng được ngay
    assert r["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s"


def test_so_rong_van_ghi_duoc(tmp_path):
    dest = write_ledger([], tmp_path / "sub" / "ledger.json")
    assert json.loads(dest.read_text(encoding="utf-8")) == []


# ------------------------------ tỉ trọng ------------------------------------
def test_mix_gom_theo_nhom_nguon():
    keys = ["pexels:1", "pixabay:2", "envato:3", "ytref:X@t=1-5", "local:kho/a.mp4"]
    mix = source_mix(keys, [10.0, 10.0, 20.0, 5.0, 5.0])
    assert mix["stock"]["clips"] == 2 and mix["stock"]["seconds"] == 20.0
    assert mix["sub"]["clips"] == 1
    assert mix["ytref"]["ratio"] == pytest.approx(0.1)   # 5/50
    assert mix["local"]["clips"] == 1


def test_mix_rong_khong_chia_0():
    assert source_mix([], []) == {}


def test_mix_nguon_la_vao_other():
    mix = source_mix(["khongro:1"], [10.0])
    assert mix["other"]["clips"] == 1
