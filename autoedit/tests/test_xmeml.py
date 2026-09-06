"""Xuất timeline sang FCP7 XML (xmeml) — định dạng Premiere Pro import được.

Dịch TỪ DRAFT CAPCUT (kết quả cuối) như fcpxml, nhưng mang thêm được Ken Burns,
vị trí PiP và ducking — những thứ mô hình 1-spine của FCPXML phải bỏ.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import pytest

from autoedit.packager.xmeml import (
    XmemlError,
    draft_sang_xmeml,
    xuat_xmeml,
)

MICRO = 1_000_000
FPS = 30


def _mk_draft(tmp_path, *, doan=None, fps=FPS, them_track=None,
              them_videos=None, texts=None):
    """Draft CapCut tối thiểu nhưng ĐÚNG cấu trúc thật (mirror test_fcpxml)."""
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
    videos.extend(them_videos or [])

    tracks = [{"type": "video", "attribute": 0, "flag": 0, "segments": segs}]
    if them_track:
        tracks.extend(them_track)
    tong = max((b + k for b, k, _, _ in doan), default=0)
    (d / "draft_content.json").write_text(json.dumps({
        "fps": fps, "duration": int(tong * MICRO),
        "canvas_config": {"width": 1920, "height": 1080, "ratio": "original"},
        "materials": {"videos": videos, "audios": [], "texts": texts or [],
                      "speeds": speeds},
        "tracks": tracks,
    }), encoding="utf-8")
    return d


def _clips_v1(xml: str):
    return ET.fromstring(xml).findall(".//video/track[1]/clipitem")


def _n(el, tag) -> int:
    return int(el.find(tag).text)


# ------------------------------- cơ bản --------------------------------------
def test_sinh_ra_xml_hop_le(tmp_path):
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path))
    r = ET.fromstring(xml)
    assert r.tag == "xmeml"
    assert r.get("version") == "4"
    assert r.find("sequence") is not None
    assert r.find(".//sequence/rate/timebase").text == str(FPS)


def test_moi_doan_thanh_mot_clipitem(tmp_path):
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path))
    assert len(_clips_v1(xml)) == 2


def test_giu_dung_moc_thoi_gian(tmp_path):
    """xmeml đo bằng KHUNG nguyên — 4.0s @30fps là khung 120, không xê dịch."""
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path))
    clips = _clips_v1(xml)
    assert _n(clips[0], "start") == 0
    assert _n(clips[0], "end") == 120
    assert _n(clips[1], "start") == 120
    assert _n(clips[1], "end") == 210


def test_lop_nen_lien_mach_khong_ho(tmp_path):
    """Mối nối hở là đen màn, chồng là Premiere xô lệch cả timeline (mirror
    bài học fcpxml: ±1 khung ở 24/25 mối nối nếu làm tròn từng clip riêng)."""
    doan = [(0.0, 1.017, 0, 1.0), (1.017, 2.049, 0, 1.0), (3.066, 0.983, 0, 1.0)]
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path, doan=doan))
    clips = _clips_v1(xml)
    for i in range(len(clips) - 1):
        assert _n(clips[i], "end") == _n(clips[i + 1], "start"), \
            f"clip {i} và {i + 1} hở/chồng nhau"


def test_moc_khong_troi_qua_nhieu_clip(tmp_path):
    """Bám mép mà cộng dồn sai số thì clip cuối lệch cả giây so với draft."""
    doan = [(i * 1.017, 1.017, 0, 1.0) for i in range(40)]
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path, doan=doan))
    cuoi = _clips_v1(xml)[-1]
    assert _n(cuoi, "start") == pytest.approx(39 * 1.017 * FPS, abs=1)


# ------------------------------ tốc độ ---------------------------------------
def test_doi_toc_do_thanh_time_remap(tmp_path):
    """footage_speed 0.9 là mặc định của tool — mất là timeline sai nhịp."""
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path, doan=[(0.0, 5.0, 0.0, 0.9)]))
    ef = next(e for e in ET.fromstring(xml).findall(".//clipitem/filter/effect")
              if e.find("effectid").text == "timeremap")
    speed = next(p for p in ef.findall("parameter")
                 if p.find("parameterid").text == "speed")
    assert float(speed.find("value").text) == pytest.approx(90.0)


def test_toc_do_binh_thuong_khong_them_time_remap(tmp_path):
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path, doan=[(0.0, 5.0, 0.0, 1.0)]))
    assert all(e.find("effectid").text != "timeremap"
               for e in ET.fromstring(xml).findall(".//effect"))


def test_toc_do_giu_dung_khoang_nguon(tmp_path):
    """in/out theo miền NGUỒN: 5s timeline @0.9 chỉ ăn 4.5s nguồn."""
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path, doan=[(0.0, 5.0, 2.0, 0.9)]))
    c = _clips_v1(xml)[0]
    assert _n(c, "in") == round(2.0 * FPS)
    assert _n(c, "out") == round((2.0 + 4.5) * FPS)
    assert _n(c, "end") - _n(c, "start") == 150


# ------------------------------ đường dẫn ------------------------------------
def test_go_placeholder_duong_dan_capcut(tmp_path):
    xml, _ = draft_sang_xmeml(_mk_draft(tmp_path))
    src = ET.fromstring(xml).find(".//file/pathurl").text
    assert "_draftpath_placeholder_" not in src
    assert "##" not in src
    assert src.startswith("file:")
    assert src.endswith("v0.mp4")


def test_bao_khi_thieu_file_media(tmp_path):
    d = _mk_draft(tmp_path)
    (d / "materials" / "v0.mp4").unlink()
    _, canh_bao = draft_sang_xmeml(d)
    assert any("offline" in c for c in canh_bao)


def test_file_chi_dinh_nghia_mot_lan(tmp_path):
    """2 clip cùng 1 file: định nghĩa đầy đủ 1 lần, lần sau tham chiếu id rỗng —
    Premiere đòi vậy, lặp định nghĩa là nó hiểu thành file khác."""
    d = _mk_draft(tmp_path, doan=[(0.0, 2.0, 0.0, 1.0)])
    draft = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    seg2 = json.loads(json.dumps(draft["tracks"][0]["segments"][0]))
    seg2["target_timerange"] = {"start": int(2 * MICRO), "duration": int(2 * MICRO)}
    draft["tracks"][0]["segments"].append(seg2)
    (d / "draft_content.json").write_text(json.dumps(draft), encoding="utf-8")

    xml, _ = draft_sang_xmeml(d)
    files = ET.fromstring(xml).findall(".//clipitem/file")
    assert len(files) == 2
    day_du = [f for f in files if f.find("pathurl") is not None]
    assert len(day_du) == 1


# ------------------------------ audio ----------------------------------------
def _track_audio(bd, keo, mid="a0", volume=1.0, src_bd=0.0, keyframes=None):
    seg = {
        "material_id": mid, "extra_material_refs": [], "volume": volume,
        "target_timerange": {"start": int(bd * MICRO), "duration": int(keo * MICRO)},
        "source_timerange": {"start": int(src_bd * MICRO),
                             "duration": int(keo * MICRO)}}
    if keyframes:
        seg["common_keyframes"] = [{
            "id": "kf0", "material_id": "", "property_type": "KFTypeVolume",
            "keyframe_list": [{"curveType": "Line", "id": f"k{i}",
                               "time_offset": int(t * MICRO), "values": [v]}
                              for i, (t, v) in enumerate(keyframes)]}]
    return {"type": "audio", "attribute": 0, "flag": 0, "segments": [seg]}


def _them_audio_material(d, mid="a0", ten="voice.wav", keo=30.0):
    draft = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    (d / "materials" / ten).write_bytes(b"fake")
    draft["materials"]["audios"].append({
        "id": mid, "type": "extract_music", "duration": int(keo * MICRO),
        "path": f"##_draftpath_placeholder_X_##/materials/{ten}"})
    (d / "draft_content.json").write_text(json.dumps(draft), encoding="utf-8")


def test_track_audio_nam_trong_phan_audio(tmp_path):
    """Voice/music phải vào <audio> (track A), không lẫn sang <video>."""
    d = _mk_draft(tmp_path, them_track=[_track_audio(0.0, 3.0)])
    _them_audio_material(d)
    xml, _ = draft_sang_xmeml(d)
    r = ET.fromstring(xml)
    assert len(r.findall(".//audio/track/clipitem")) == 1
    assert len(r.findall(".//video/track")) == 1


def test_volume_tinh_thanh_audio_levels(tmp_path):
    """MUSIC_VOLUME nép dưới voice — mất volume là nhạc đè lời."""
    d = _mk_draft(tmp_path, them_track=[_track_audio(0.0, 3.0, volume=0.6)])
    _them_audio_material(d)
    xml, _ = draft_sang_xmeml(d)
    level = next(p for p in ET.fromstring(xml).findall(".//audio//parameter")
                 if p.find("parameterid").text == "level")
    assert float(level.find("value").text) == pytest.approx(0.6)


def test_ducking_keyframe_theo_mien_nguon(tmp_path):
    """CapCut ghi time_offset ducking theo miền NGUỒN (từ đầu bài nhạc, bài học
    F8) — trùng miền in/out của xmeml nên `when` = offset đổi thẳng ra khung."""
    d = _mk_draft(tmp_path, them_track=[
        _track_audio(0.0, 10.0, src_bd=30.0,
                     keyframes=[(30.0, 1.0), (32.0, 0.25), (38.0, 1.0)])])
    _them_audio_material(d, keo=120.0)
    xml, _ = draft_sang_xmeml(d)
    level = next(p for p in ET.fromstring(xml).findall(".//audio//parameter")
                 if p.find("parameterid").text == "level")
    kfs = [(int(k.find("when").text), float(k.find("value").text))
           for k in level.findall("keyframe")]
    assert kfs == [(900, 1.0), (960, 0.25), (1140, 1.0)]
    c = ET.fromstring(xml).find(".//audio/track/clipitem")
    assert _n(c, "in") <= 900 and 1140 <= _n(c, "out")


# --------------------------- Ken Burns + PiP ---------------------------------
def _seg_video(mid, bd, keo, clip=None, keyframes=None):
    seg = {
        "material_id": mid, "extra_material_refs": [], "volume": 1.0,
        "target_timerange": {"start": int(bd * MICRO), "duration": int(keo * MICRO)},
        "source_timerange": {"start": 0, "duration": int(keo * MICRO)}}
    if clip:
        seg["clip"] = clip
    if keyframes:
        seg["common_keyframes"] = [{
            "id": "kf0", "material_id": "", "property_type": "UNIFORM_SCALE",
            "keyframe_list": [{"curveType": "Line", "id": f"k{i}",
                               "time_offset": int(t * MICRO), "values": [v]}
                              for i, (t, v) in enumerate(keyframes)]}]
    return seg


def test_ken_burns_thanh_keyframe_scale(tmp_path):
    """Ken Burns trên ảnh — thứ bản .fcpxml phải bỏ, bản .xml phải giữ."""
    d = _mk_draft(tmp_path)
    draft = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    (d / "materials" / "anh.jpg").write_bytes(b"fake")
    draft["materials"]["videos"].append({
        "id": "p0", "type": "photo", "duration": int(5 * MICRO),
        "width": 1920, "height": 1080,
        "path": "##_draftpath_placeholder_X_##/materials/anh.jpg"})
    draft["tracks"][0]["segments"] = [
        _seg_video("p0", 0.0, 5.0, keyframes=[(0.0, 1.0), (4.9, 1.25)])]
    (d / "draft_content.json").write_text(json.dumps(draft), encoding="utf-8")

    xml, _ = draft_sang_xmeml(d)
    scale = next(p for p in ET.fromstring(xml).findall(".//video//parameter")
                 if p.find("parameterid").text == "scale")
    kfs = [(int(k.find("when").text), float(k.find("value").text))
           for k in scale.findall("keyframe")]
    assert kfs == [(0, 100.0), (147, 125.0)]


def test_anh_doc_nhan_he_so_fit_khung(tmp_path):
    """CapCut scale 1.0 = fit vừa canvas; Premiere scale 100 = pixel gốc. Ảnh dọc
    1080x1920 không nhân hệ số fit (0.5625) là tràn màn trong Premiere."""
    d = _mk_draft(tmp_path)
    draft = json.loads((d / "draft_content.json").read_text(encoding="utf-8"))
    (d / "materials" / "doc.jpg").write_bytes(b"fake")
    draft["materials"]["videos"].append({
        "id": "p0", "type": "photo", "duration": int(3 * MICRO),
        "width": 1080, "height": 1920,
        "path": "##_draftpath_placeholder_X_##/materials/doc.jpg"})
    draft["tracks"][0]["segments"] = [_seg_video("p0", 0.0, 3.0)]
    (d / "draft_content.json").write_text(json.dumps(draft), encoding="utf-8")

    xml, _ = draft_sang_xmeml(d)
    scale = next(p for p in ET.fromstring(xml).findall(".//video//parameter")
                 if p.find("parameterid").text == "scale")
    assert float(scale.find("value").text) == pytest.approx(56.25)


def test_pip_thanh_scale_va_center(tmp_path):
    """Chart PiP nửa màn (scale 0.5, transform_x 0.42): CapCut đo bằng NỬA cạnh
    canvas, Premiere đo bằng CẢ cạnh -> horiz = 0.21. Sai là chart bay khỏi màn."""
    pip = {"type": "video", "attribute": 0, "flag": 0, "segments": [
        _seg_video("c0", 1.0, 3.0, clip={
            "alpha": 1.0, "rotation": 0.0,
            "scale": {"x": 0.5, "y": 0.5},
            "transform": {"x": 0.42, "y": 0.0}})]}
    d = _mk_draft(tmp_path, them_track=[pip], them_videos=[{
        "id": "c0", "type": "video", "duration": int(10 * MICRO),
        "width": 1920, "height": 1080,
        "path": "##_draftpath_placeholder_X_##/materials/chart.mp4"}])
    (d / "materials" / "chart.mp4").write_bytes(b"fake")

    xml, _ = draft_sang_xmeml(d)
    v2 = ET.fromstring(xml).findall(".//video/track")[1]
    scale = next(p for p in v2.findall(".//parameter")
                 if p.find("parameterid").text == "scale")
    assert float(scale.find("value").text) == pytest.approx(50.0)
    center = next(p for p in v2.findall(".//parameter")
                  if p.find("parameterid").text == "center")
    assert float(center.find("value/horiz").text) == pytest.approx(0.21)
    assert float(center.find("value/vert").text) == pytest.approx(0.0)


# ------------------------------- chữ -----------------------------------------
def test_chu_thanh_marker_tren_sequence(tmp_path):
    text_track = {"type": "text", "attribute": 0, "flag": 0, "segments": [{
        "material_id": "t0", "extra_material_refs": [],
        "target_timerange": {"start": int(2 * MICRO), "duration": int(3 * MICRO)}}]}
    d = _mk_draft(tmp_path, them_track=[text_track], texts=[{
        "id": "t0", "type": "text",
        "content": json.dumps({"text": "GDP tăng 8%"})}])
    xml, canh_bao = draft_sang_xmeml(d)
    mk = ET.fromstring(xml).find(".//sequence/marker")
    assert mk is not None
    assert "GDP tăng 8%" in mk.find("name").text
    assert _n(mk, "in") == 60
    assert _n(mk, "out") == 150
    assert any("MARKER" in c for c in canh_bao)


# ------------------------------- lỗi -----------------------------------------
def test_draft_thieu_file_bao_loi_ro(tmp_path):
    with pytest.raises(XmemlError, match="draft_content.json"):
        draft_sang_xmeml(tmp_path / "khong-co")


def test_draft_khong_co_track_video(tmp_path):
    d = tmp_path / "draft"
    d.mkdir()
    (d / "draft_content.json").write_text(json.dumps({
        "fps": 30, "duration": 0, "materials": {}, "tracks": []}), encoding="utf-8")
    with pytest.raises(XmemlError, match="track video"):
        draft_sang_xmeml(d)


def test_xuat_ra_file(tmp_path):
    d = _mk_draft(tmp_path)
    out = tmp_path / "C9.xml"
    xuat_xmeml(d, out, ten_seq="C9")
    assert out.is_file()
    txt = out.read_text(encoding="utf-8")
    assert txt.startswith("<?xml")
    assert "<!DOCTYPE xmeml>" in txt
    assert ET.fromstring(txt).find(".//sequence/name").text == "C9"
