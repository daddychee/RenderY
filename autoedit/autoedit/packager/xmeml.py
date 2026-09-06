r"""Xuất timeline sang FCP7 XML (xmeml) — định dạng Premiere Pro import được.

Vì sao cần file này khi đã có fcpxml.py: Premiere KHÔNG đọc .fcpxml (định dạng
Final Cut Pro X). Premiere chỉ import "Final Cut Pro XML" đời cũ — xmeml, đuôi
.xml. Resolve đọc được cả hai. Vậy nên mỗi draft giao kèm cả hai bản:
  .xml     -> Premiere (và Resolve)
  .fcpxml  -> Resolve / Final Cut Pro

Cũng như fcpxml.py: dịch TỪ DRAFT CAPCUT (kết quả cuối, đã qua mọi xử lý), không
dựng lại từ project.json — hai đường dựng song song là hai timeline lệch nhau.

xmeml hợp draft của mình hơn FCPXML: danh sách track PHẲNG (V1..Vn, A1..An) khớp
thẳng 8 track CapCut, không phải ép về mô hình 1 spine + connected clip. Nhờ vậy
bản này mang sang được những thứ bản .fcpxml phải bỏ:
  - Ken Burns (keyframe scale trên ảnh) -> keyframe Scale của Basic Motion
  - Vị trí/scale PiP (chart nửa màn, info card) -> Scale + Center của Basic Motion
  - Ducking nhạc (keyframe volume) -> keyframe Level của Audio Levels

Giới hạn ĐÃ BIẾT (ghi ra để không ai tưởng bản Premiere là bản sao y):
  - Chữ (track text) thành MARKER trên sequence, KHÔNG phải title có kiểu dáng.
    Style chữ CapCut là định dạng riêng, dịch sang sẽ sai font/màu — thà nói rõ
    "chỗ này có chữ" để editor tự đặt bằng Essential Graphics.
  - Đường cong keyframe: CapCut nội suy tuyến tính, Premiere cũng đặt tuyến tính
    — khớp. Nhưng nếu sau này draft dùng curve khác thì bản Premiere vẫn tuyến tính.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from xml.dom import minidom

from autoedit.packager.fcpxml import (
    MICRO,
    FcpxmlError,
    _duong_dan_that,
    _gom_material,
    _toc_do,
    _uri,
    doc_draft,
)


class XmemlError(RuntimeError):
    """Không dịch được draft sang xmeml."""


def _el(cha, tag: str, text=None):
    """xmeml để giá trị trong TEXT của element (khác fcpxml dùng attribute)."""
    e = ET.SubElement(cha, tag)
    if text is not None:
        e.text = str(text)
    return e


def _rate(cha, fps: int):
    r = _el(cha, "rate")
    _el(r, "timebase", fps)
    _el(r, "ntsc", "FALSE")   # draft ghi fps nguyên (30), không phải 29.97 NTSC
    return r


def _chu_cua(mat: dict) -> str:
    """Nội dung chữ của material text — CapCut gói trong JSON con."""
    try:
        return (json.loads(mat.get("content") or "{}").get("text") or "")[:60]
    except (json.JSONDecodeError, AttributeError):
        return (mat.get("content") or "")[:60]


def _fit_canvas(mat: dict, w: int, h: int) -> float:
    """Hệ số CapCut co media VỪA khung (contain) trước khi áp scale của user.

    CapCut: scale 1.0 = đã fit vừa canvas. Premiere: scale 100 = kích thước GỐC
    (pixel-to-pixel). Không nhân hệ số này thì ảnh dọc 4000px tràn màn trong
    Premiere dù CapCut hiển thị đúng. Footage đã normalize 1920x1080 -> hệ số 1.
    """
    mw, mh = int(mat.get("width") or 0), int(mat.get("height") or 0)
    if mw <= 0 or mh <= 0:
        return 1.0
    return min(w / mw, h / mh)


def _keyframes_cua(seg: dict, property_type: str) -> list[tuple[int, float]]:
    """[(time_offset_µs, value)] của 1 thuộc tính. time_offset theo MIỀN NGUỒN
    (từ đầu FILE, không phải từ đầu clip) — xem bài học ducking trong assembler."""
    for kf in seg.get("common_keyframes") or []:
        if kf.get("property_type") != property_type:
            continue
        ra = []
        for k in kf.get("keyframe_list") or []:
            vals = k.get("values") or []
            if vals:
                ra.append((int(k.get("time_offset") or 0), float(vals[0])))
        return sorted(ra)
    return []


def draft_sang_xmeml(thu_muc_draft: Path, ten_seq: str = "") -> tuple[str, list[str]]:
    """Dịch 1 draft CapCut -> (chuỗi FCP7 XML, danh sách cảnh báo)."""
    thu_muc_draft = Path(thu_muc_draft)
    try:
        draft = doc_draft(thu_muc_draft)
    except FcpxmlError as exc:
        raise XmemlError(str(exc)) from exc
    fps = int(draft.get("fps") or 30)
    cv = draft.get("canvas_config") or {}
    w, h = int(cv.get("width") or 1920), int(cv.get("height") or 1080)
    tong = float(draft.get("duration") or 0) / MICRO
    mats = _gom_material(draft)
    canh_bao: list[str] = []

    def khung(giay: float) -> int:
        return round(giay * fps)

    tracks = draft.get("tracks") or []
    nen_idx = next((i for i, t in enumerate(tracks)
                    if t.get("type") == "video" and t.get("segments")), None)
    if nen_idx is None:
        raise XmemlError("Draft không có track video nào có đoạn")

    xmeml = ET.Element("xmeml", version="4")
    seq = ET.SubElement(xmeml, "sequence", id="sequence-1")
    _el(seq, "name", ten_seq or thu_muc_draft.name)
    _el(seq, "duration", khung(tong))
    _rate(seq, fps)
    tc = _el(seq, "timecode")
    _rate(tc, fps)
    _el(tc, "string", "00:00:00:00")
    _el(tc, "frame", 0)
    _el(tc, "displayformat", "NDF")
    media = _el(seq, "media")
    video = _el(media, "video")
    fmt = _el(video, "format")
    sc = _el(fmt, "samplecharacteristics")
    _rate(sc, fps)
    _el(sc, "width", w)
    _el(sc, "height", h)
    _el(sc, "anamorphic", "FALSE")
    _el(sc, "pixelaspectratio", "square")
    _el(sc, "fielddominance", "none")

    # ------------------------------------------------------------------ file
    # Mỗi file media chỉ định nghĩa ĐẦY ĐỦ một lần; các clip sau tham chiếu id
    # rỗng — Premiere đòi vậy, lặp định nghĩa là nó hiểu thành file khác.
    file_id: dict[str, str] = {}
    da_dinh_nghia: set[str] = set()
    thieu: list[str] = []

    def them_file(cha, mid: str, loai: str, mat: dict):
        fid = file_id.setdefault(mid, f"file-{len(file_id) + 1}")
        if fid in da_dinh_nghia:
            ET.SubElement(cha, "file", id=fid)
            return
        da_dinh_nghia.add(fid)
        that = _duong_dan_that(mat.get("path") or "", thu_muc_draft)
        if that is not None and not that.is_file():
            thieu.append(that.name)
        f = ET.SubElement(cha, "file", id=fid)
        _el(f, "name", that.name if that else mid)
        if that is not None:
            _el(f, "pathurl", _uri(that))
        _rate(f, fps)
        _el(f, "duration", max(1, khung(float(mat.get("duration") or 0) / MICRO)))
        m = _el(f, "media")
        if loai == "videos":
            v = _el(m, "video")
            vc = _el(v, "samplecharacteristics")
            _rate(vc, fps)
            _el(vc, "width", int(mat.get("width") or w))
            _el(vc, "height", int(mat.get("height") or h))
        else:
            a = _el(m, "audio")
            ac = _el(a, "samplecharacteristics")
            _el(ac, "depth", 16)
            _el(ac, "samplerate", 48000)
            _el(a, "channelcount", 2)

    # -------------------------------------------------------------- clipitem
    so_clip = 0

    def them_clip(track_el, seg, khung_bat_dau: Optional[int] = None) -> Optional[int]:
        """1 đoạn CapCut -> 1 <clipitem>. Trả khung KẾT để lớp nền bám mép nhau.

        `khung_bat_dau` ép clip bắt đầu ĐÚNG khung chỉ định (lớp nền): làm tròn
        từng clip độc lập thì mối nối lệch ±1 khung — hở là đen màn, chồng là
        Premiere xô lệch cả timeline. Độ dài lấy theo MỐC KẾT của draft chứ không
        làm tròn riêng độ dài — sai số không cộng dồn qua ~25 clip (y hệt fcpxml).
        """
        nonlocal so_clip
        mid = seg.get("material_id")
        if mid not in mats:
            return None
        loai, mat = mats[mid]
        if loai == "texts":
            return None
        tgt = seg.get("target_timerange") or {}
        src = seg.get("source_timerange") or {}
        offset = float(tgt.get("start") or 0) / MICRO
        keo = float(tgt.get("duration") or 0) / MICRO
        src_bd = float(src.get("start") or 0) / MICRO
        src_keo = float(src.get("duration") or 0) / MICRO
        toc = _toc_do(draft, seg)
        if src_keo <= 0:
            src_keo = keo * toc

        k_off = khung(offset) if khung_bat_dau is None else khung_bat_dau
        k_keo = max(1, khung(offset + keo) - k_off)
        k_in = khung(src_bd)
        k_out = max(k_in + 1, khung(src_bd + src_keo))

        so_clip += 1
        clip = ET.SubElement(track_el, "clipitem", id=f"clipitem-{so_clip}")
        that = _duong_dan_that(mat.get("path") or "", thu_muc_draft)
        _el(clip, "name", that.stem if that else mid)
        _el(clip, "enabled", "TRUE")
        _el(clip, "duration", max(1, khung(float(mat.get("duration") or 0) / MICRO)))
        _rate(clip, fps)
        _el(clip, "start", k_off)
        _el(clip, "end", k_off + k_keo)
        _el(clip, "in", k_in)
        _el(clip, "out", k_out)
        them_file(clip, mid, loai, mat)

        if loai == "videos":
            _loc_hinh(clip, seg, mat, toc, k_in, k_out)
        else:
            st = _el(clip, "sourcetrack")
            _el(st, "mediatype", "audio")
            _el(st, "trackindex", 1)
            _loc_tieng(clip, seg, k_in, k_out)
        return k_off + k_keo

    def _loc_hinh(clip, seg, mat, toc: float, k_in: int, k_out: int):
        """Filter hình: Basic Motion (scale/vị trí + Ken Burns), Time Remap (tốc độ)."""
        cs = seg.get("clip") or {}
        scale = float(((cs.get("scale") or {}).get("x")) or 1.0)
        tx = float(((cs.get("transform") or {}).get("x")) or 0.0)
        ty = float(((cs.get("transform") or {}).get("y")) or 0.0)
        kb = _keyframes_cua(seg, "UNIFORM_SCALE")
        fit = _fit_canvas(mat, w, h)

        can_motion = kb or abs(scale - 1.0) > 1e-6 or abs(tx) > 1e-6 \
            or abs(ty) > 1e-6 or abs(fit - 1.0) > 1e-6
        if can_motion:
            ef = _el(_el(clip, "filter"), "effect")
            _el(ef, "name", "Basic Motion")
            _el(ef, "effectid", "basic")
            _el(ef, "effectcategory", "motion")
            _el(ef, "effecttype", "motion")
            _el(ef, "mediatype", "video")
            p = _el(ef, "parameter")
            _el(p, "parameterid", "scale")
            _el(p, "name", "Scale")
            _el(p, "valuemin", 0)
            _el(p, "valuemax", 1000)
            if kb:
                # Ken Burns: giá trị CapCut (1.0 = fit khung) -> % Premiere (100 = gốc).
                # time_offset theo miền nguồn = đúng miền của in/out -> đổi thẳng ra khung.
                _el(p, "value", round(kb[0][1] * fit * 100, 2))
                for t_us, v in kb:
                    kf = _el(p, "keyframe")
                    _el(kf, "when", min(max(khung(t_us / MICRO), k_in), k_out))
                    _el(kf, "value", round(v * fit * 100, 2))
            else:
                _el(p, "value", round(scale * fit * 100, 2))
            if abs(tx) > 1e-6 or abs(ty) > 1e-6:
                # CapCut transform: 1.0 = nửa cạnh canvas, y HƯỚNG LÊN dương.
                # Premiere center: 1.0 = cả cạnh canvas, y hướng XUỐNG dương.
                p = _el(ef, "parameter")
                _el(p, "parameterid", "center")
                _el(p, "name", "Center")
                v = _el(p, "value")
                _el(v, "horiz", round(tx / 2, 4))
                _el(v, "vert", round(-ty / 2, 4))
        if abs(toc - 1.0) > 1e-6:
            # Tốc độ hằng -> Time Remap %, đúng cách Premiere tự ghi khi export xmeml.
            ef = _el(_el(clip, "filter"), "effect")
            _el(ef, "name", "Time Remap")
            _el(ef, "effectid", "timeremap")
            _el(ef, "effectcategory", "motion")
            _el(ef, "effecttype", "motion")
            _el(ef, "mediatype", "video")
            p = _el(ef, "parameter")
            _el(p, "parameterid", "variablespeed")
            _el(p, "name", "variablespeed")
            _el(p, "valuemin", 0)
            _el(p, "valuemax", 1)
            _el(p, "value", 0)
            p = _el(ef, "parameter")
            _el(p, "parameterid", "speed")
            _el(p, "name", "speed")
            _el(p, "valuemin", -100000)
            _el(p, "valuemax", 100000)
            _el(p, "value", round(toc * 100, 2))

    def _loc_tieng(clip, seg, k_in: int, k_out: int):
        """Filter tiếng: Audio Levels — volume tĩnh + keyframe ducking."""
        vol = float(seg.get("volume") if seg.get("volume") is not None else 1.0)
        kfs = _keyframes_cua(seg, "KFTypeVolume")
        if not kfs and abs(vol - 1.0) <= 1e-6:
            return
        ef = _el(_el(clip, "filter"), "effect")
        _el(ef, "name", "Audio Levels")
        _el(ef, "effectid", "audiolevels")
        _el(ef, "effectcategory", "audiolevels")
        _el(ef, "effecttype", "audiolevels")
        _el(ef, "mediatype", "audio")
        p = _el(ef, "parameter")
        _el(p, "parameterid", "level")
        _el(p, "name", "Level")
        _el(p, "valuemin", 0)
        _el(p, "valuemax", 15.849)
        _el(p, "value", round(kfs[0][1] if kfs else vol, 4))
        # time_offset ducking ghi theo miền NGUỒN (từ đầu bài nhạc, bài học F8) —
        # trùng miền in/out của xmeml nên đổi thẳng ra khung, KHÔNG trừ src_start.
        for t_us, v in kfs:
            kf = _el(p, "keyframe")
            _el(kf, "when", min(max(khung(t_us / MICRO), k_in), k_out))
            _el(kf, "value", round(v, 4))

    # Lớp nền = V1: clip sau bắt đầu ĐÚNG chỗ clip trước kết thúc.
    tr = _el(video, "track")
    ket_truoc: Optional[int] = None
    for seg in tracks[nen_idx].get("segments") or []:
        ra = them_clip(tr, seg, khung_bat_dau=ket_truoc)
        if ra is not None:
            ket_truoc = ra
    if ket_truoc is None:
        raise XmemlError("Không dựng được clip nào — kiểm tra đường dẫn media của draft")

    # Các track video còn lại -> V2, V3... (lớp phủ neo theo mốc riêng, khỏi bám mép)
    for i, t in enumerate(tracks):
        if i == nen_idx or t.get("type") != "video" or not t.get("segments"):
            continue
        tr = _el(video, "track")
        for seg in t["segments"]:
            them_clip(tr, seg)

    # Audio: mỗi track CapCut -> 1 track A đúng thứ tự (voice, music, sfx...)
    audio = _el(media, "audio")
    _el(audio, "numOutputChannels", 2)
    for t in tracks:
        if t.get("type") != "audio" or not t.get("segments"):
            continue
        tr = _el(audio, "track")
        for seg in t["segments"]:
            them_clip(tr, seg)

    # Chữ -> marker trên SEQUENCE (Premiere import marker sequence từ xmeml).
    so_text = 0
    for t in tracks:
        if t.get("type") != "text":
            continue
        for seg in t.get("segments") or []:
            tgt = seg.get("target_timerange") or {}
            bd = float(tgt.get("start") or 0) / MICRO
            keo = float(tgt.get("duration") or 0) / MICRO
            _, mat = mats.get(seg.get("material_id"), ("", {}))
            chu = _chu_cua(mat)
            mk = _el(seq, "marker")
            _el(mk, "comment", "")
            _el(mk, "name", f"CHỮ: {chu}" if chu else "CHỮ")
            _el(mk, "in", khung(bd))
            _el(mk, "out", max(khung(bd) + 1, khung(bd + keo)))
            so_text += 1

    if thieu:
        canh_bao.append(f"{len(thieu)} file media không thấy trên đĩa "
                        f"(vd {thieu[0]}) — Premiere sẽ báo offline")
    if so_text:
        canh_bao.append(f"{so_text} đoạn chữ chuyển thành MARKER trên sequence "
                        f"(không phải title có kiểu dáng) — xem marker để biết đặt chữ ở đâu")

    tho = ET.tostring(xmeml, encoding="utf-8")
    dep = minidom.parseString(tho).toprettyxml(indent="  ", encoding="utf-8")
    xml = dep.decode("utf-8")
    # DOCTYPE để Premiere nhận diện đây là FCP7 XML, không đoán mò theo đuôi file
    xml = xml.replace('<?xml version="1.0" encoding="utf-8"?>',
                      '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>', 1)
    return xml, canh_bao


def xuat_xmeml(thu_muc_draft: Path, dich: Path, ten_seq: str = "") -> list[str]:
    """Dịch draft -> ghi file .xml (FCP7 XML). Trả danh sách cảnh báo."""
    xml, canh_bao = draft_sang_xmeml(thu_muc_draft, ten_seq)
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    dich.write_text(xml, encoding="utf-8")
    return canh_bao
