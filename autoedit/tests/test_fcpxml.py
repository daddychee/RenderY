"""Xuất timeline sang FCPXML cho Premiere Pro / DaVinci Resolve.

Dịch TỪ DRAFT CAPCUT (kết quả cuối, đã qua mọi xử lý) chứ không dựng lại từ dữ liệu
thô — hai đường dựng song song là hai timeline lệch nhau.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from fractions import Fraction

import pytest

from autoedit.packager.fcpxml import (
    FcpxmlError,
    draft_sang_fcpxml,
    xuat_fcpxml,
)

MICRO = 1_000_000


def _giay(s: str) -> float:
    return float(Fraction(s.rstrip("s")))


def _mk_draft(tmp_path, *, doan=None, fps=30, them_track=None):
    """Draft CapCut tối thiểu nhưng ĐÚNG cấu trúc thật (đo từ draft LI104/C9)."""
    d = tmp_path / "draft"
    (d / "materials").mkdir(parents=True)
    doan = doan if doan is not None else [(0.0, 4.0, 0.0, 1.0), (4.0, 3.0, 0.0, 1.0)]

    videos, speeds, segs = [], [], []
    for i, (bd, keo, src_bd, toc) in enumerate(doan):
        f = d / "materials" / f"v{i}.mp4"
        f.write_bytes(b"fake")
        mid, sid = f"m{i}", f"s{i}"
        videos.append({"id": mid, "type": "video", "duration": int(30 * MICRO),
                       "width": 1920, "height": 1080,
                       "path": f"##_draftpath_placeholder_X_##/materials/v{i}.mp4"})
        speeds.append({"id": sid, "type": "speed", "speed": toc, "mode": 0})
        segs.append({
            "material_id": mid, "extra_material_refs": [sid], "volume": 1.0,
            "target_timerange": {"start": int(bd * MICRO), "duration": int(keo * MICRO)},
            "source_timerange": {"start": int(src_bd * MICRO),
                                 "duration": int(keo * toc * MICRO)},
        })

    tracks = [{"type": "video", "attribute": 0, "flag": 0, "segments": segs}]
    if them_track:
        tracks.extend(them_track)
    tong = max((b + k for b, k, _, _ in doan), default=0)
    (d / "draft_content.json").write_text(json.dumps({
        "fps": fps, "duration": int(tong * MICRO),
        "canvas_config": {"width": 1920, "height": 1080, "ratio": "original"},
        "materials": {"videos": videos, "audios": [], "texts": [], "speeds": speeds},
        "tracks": tracks,
    }), encoding="utf-8")
    return d


# ------------------------------- cơ bản --------------------------------------
def test_sinh_ra_xml_hop_le(tmp_path):
    xml, _ = draft_sang_fcpxml(_mk_draft(tmp_path))
    r = ET.fromstring(xml)
    assert r.tag == "fcpxml"
    assert r.get("version") == "1.8"      # bản Premiere đọc ổn định nhất
    assert r.find(".//sequence") is not None


def test_moi_doan_thanh_mot_clip(tmp_path):
    xml, _ = draft_sang_fcpxml(_mk_draft(tmp_path))
    assert len(ET.fromstring(xml).findall(".//spine/asset-clip")) == 2


def test_giu_dung_moc_thoi_gian(tmp_path):
    xml, _ = draft_sang_fcpxml(_mk_draft(tmp_path))
    clips = ET.fromstring(xml).findall(".//spine/asset-clip")
    assert _giay(clips[0].get("offset")) == pytest.approx(0.0)
    assert _giay(clips[0].get("duration")) == pytest.approx(4.0, abs=0.02)
    assert _giay(clips[1].get("offset")) == pytest.approx(4.0, abs=0.02)


def test_clip_nen_lien_mach_khong_ho(tmp_path):
    """Trong spine FCPXML, khe hở là LỖ ĐEN trên timeline còn chồng lấn thì Premiere
    tự đẩy, xô lệch mọi thứ phía sau. Làm tròn từng clip riêng lẻ sinh ra cả hai
    (đo thật trên draft C9: ±1 khung ở 24/25 mối nối)."""
    # mốc lẻ, cố tình không rơi đúng biên khung 30fps
    doan = [(0.0, 1.017, 0, 1.0), (1.017, 2.049, 0, 1.0), (3.066, 0.983, 0, 1.0)]
    xml, _ = draft_sang_fcpxml(_mk_draft(tmp_path, doan=doan))
    clips = ET.fromstring(xml).findall(".//spine/asset-clip")
    moc = [(_giay(c.get("offset")), _giay(c.get("duration"))) for c in clips]
    for i in range(len(moc) - 1):
        assert moc[i][0] + moc[i][1] == pytest.approx(moc[i + 1][0]), \
            f"clip {i} và {i + 1} hở/chồng nhau"


def test_moc_khong_troi_qua_nhieu_clip(tmp_path):
    """Bám mép mà cộng dồn sai số thì clip cuối lệch cả giây so với draft."""
    doan = [(i * 1.017, 1.017, 0, 1.0) for i in range(40)]
    xml, _ = draft_sang_fcpxml(_mk_draft(tmp_path, doan=doan))
    cuoi = ET.fromstring(xml).findall(".//spine/asset-clip")[-1]
    assert _giay(cuoi.get("offset")) == pytest.approx(39 * 1.017, abs=0.034)  # <1 khung


# ------------------------------ tốc độ ---------------------------------------
def test_doi_toc_do_thanh_timemap(tmp_path):
    """footage_speed 0.9 (chậm 10%) là mặc định của tool — mất là timeline sai nhịp."""
    xml, _ = draft_sang_fcpxml(_mk_draft(tmp_path, doan=[(0.0, 5.0, 0.0, 0.9)]))
    tm = ET.fromstring(xml).find(".//asset-clip/timeMap")
    assert tm is not None
    pts = tm.findall("timept")
    assert len(pts) == 2
    assert _giay(pts[1].get("value")) == pytest.approx(5.0 * 0.9, abs=0.05)


def test_toc_do_binh_thuong_khong_them_timemap(tmp_path):
    xml, _ = draft_sang_fcpxml(_mk_draft(tmp_path, doan=[(0.0, 5.0, 0.0, 1.0)]))
    assert ET.fromstring(xml).find(".//timeMap") is None


# ------------------------------ đường dẫn ------------------------------------
def test_go_placeholder_duong_dan_capcut(tmp_path):
    """CapCut ghi `##_draftpath_placeholder_<GUID>_##/materials/x.mp4`. Không gỡ thì
    Premiere báo media offline toàn bộ."""
    xml, _ = draft_sang_fcpxml(_mk_draft(tmp_path))
    src = ET.fromstring(xml).find(".//asset").get("src")
    assert "_draftpath_placeholder_" not in src   # đúng chuỗi CapCut, không phải chữ rời
    assert "##" not in src
    assert src.startswith("file:")
    assert src.endswith("v0.mp4")


def test_bao_khi_thieu_file_media(tmp_path):
    d = _mk_draft(tmp_path)
    (d / "materials" / "v0.mp4").unlink()
    _, canh_bao = draft_sang_fcpxml(d)
    assert any("offline" in c for c in canh_bao)


# ------------------------------ nhiều lớp ------------------------------------
def _track_audio(bd, keo, mid="a0"):
    return {"type": "audio", "attribute": 0, "flag": 0, "segments": [{
        "material_id": mid, "extra_material_refs": [], "volume": 1.0,
        "target_timerange": {"start": int(bd * MICRO), "duration": int(keo * MICRO)},
        "source_timerange": {"start": 0, "duration": int(keo * MICRO)}}]}


def test_lop_audio_thanh_lane_am(tmp_path):
    """Voice/SFX phải nằm DƯỚI lớp video (lane âm) — sai lane là che mất hình."""
    d = _mk_draft(tmp_path, them_track=[_track_audio(0.0, 3.0)])
    draft = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    (d / "materials" / "voice.wav").write_bytes(b"fake")
    draft["materials"]["audios"] = [{
        "id": "a0", "type": "extract_music", "duration": int(3 * MICRO),
        "path": "##_draftpath_placeholder_X_##/materials/voice.wav"}]
    (d / "draft_content.json").write_text(json.dumps(draft), encoding="utf-8")

    xml, _ = draft_sang_fcpxml(d)
    lanes = [c.get("lane") for c in ET.fromstring(xml).findall(".//asset-clip")
             if c.get("lane")]
    assert "-1" in lanes


def test_draft_thieu_file_bao_loi_ro(tmp_path):
    with pytest.raises(FcpxmlError, match="draft_content.json"):
        draft_sang_fcpxml(tmp_path / "khong-co")


def test_draft_khong_co_track_video(tmp_path):
    d = tmp_path / "draft"
    d.mkdir()
    (d / "draft_content.json").write_text(json.dumps({
        "fps": 30, "duration": 0, "materials": {}, "tracks": []}), encoding="utf-8")
    with pytest.raises(FcpxmlError, match="track video"):
        draft_sang_fcpxml(d)


def test_xuat_ra_file(tmp_path):
    d = _mk_draft(tmp_path)
    out = tmp_path / "C9.fcpxml"
    xuat_fcpxml(d, out, ten_seq="C9")
    assert out.is_file()
    txt = out.read_text(encoding="utf-8")
    assert txt.startswith("<?xml")
    assert "<!DOCTYPE fcpxml>" in txt        # Premiere nhận diện chắc hơn
    assert ET.fromstring(txt).find(".//project").get("name") == "C9"
