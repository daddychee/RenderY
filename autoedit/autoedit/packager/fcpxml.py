r"""Xuất timeline sang FCPXML — mở được bằng DaVinci Resolve và Final Cut Pro.

LƯU Ý: Premiere KHÔNG đọc .fcpxml (định dạng FCPX). Bản cho Premiere là FCP7 XML
(.xml) do xmeml.py xuất — hai file đi cạnh nhau trong thư mục giao.

Vì sao dịch TỪ DRAFT CAPCUT chứ không dựng lại từ project.json: draft là kết quả
CUỐI, đã qua mọi xử lý (kéo ô thở, đổi tốc độ, chèn thẻ thông tin, đặt SFX, khớp
mép beat từng micro-giây). Dựng song song một đường thứ hai từ dữ liệu thô là tự
tạo ra hai bản timeline lệch nhau — sửa một chỗ, quên chỗ kia.

Giới hạn ĐÃ BIẾT, ghi ra đây để không ai tưởng bản Premiere là bản sao y:
  - Chữ (track text) chuyển thành marker đúng vị trí + thời lượng, KHÔNG phải title
    có kiểu dáng. Style chữ CapCut là định dạng riêng, dịch sang sẽ sai font/màu —
    thà nói rõ "chỗ này có chữ" để editor tự đặt.
  - Keyframe (Ken Burns) không mang sang: FCPXML tả được, nhưng đường cong CapCut
    khác đường cong Premiere nên chuyển động sẽ khác — clip giữ nguyên khung tĩnh.
  - Hiệu ứng chuyển cảnh, chỉnh màu: không dùng trong draft nên không dịch.

FCPXML 1.8 (không phải 1.9+) vì đây là bản Resolve/FCP đọc ổn định nhất tính tới 2026.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from xml.dom import minidom

# CapCut đo thời gian bằng MICRO-giây trong JSON.
MICRO = 1_000_000


class FcpxmlError(RuntimeError):
    """Không dịch được draft sang FCPXML."""


def _tick(giay: float, fps: int) -> str:
    """Giây -> chuỗi thời gian FCPXML ('126126/30000s').

    FCPXML đòi thời gian là PHÂN SỐ hữu tỉ theo nhịp khung hình, không phải số thực.
    Làm tròn về đúng biên khung: lệch nửa khung là Premiere kêu media offline hoặc
    xê dịch cả timeline.
    """
    # 30 fps thật là 30000/1001 ở NTSC, nhưng draft ghi fps nguyên -> dùng mẫu 1/fps.
    return _khung(round(giay * fps), fps)


def _khung(so_khung: int, fps: int) -> str:
    """Số khung -> chuỗi thời gian FCPXML. Đơn vị làm việc THẬT của timeline."""
    return f"{int(so_khung) * 100}/{fps * 100}s"


def _duong_dan_that(path: str, thu_muc_draft: Path) -> Optional[Path]:
    """CapCut ghi đường dẫn dạng `##_draftpath_placeholder_<GUID>_##/materials/x.mp4`.

    Placeholder đó là cách CapCut cho draft di chuyển được giữa các máy. Muốn
    Premiere mở được thì phải trả lại đường dẫn THẬT trên đĩa.
    """
    if not path:
        return None
    p = path.replace("\\", "/")
    if "_##/" in p:
        p = p.split("_##/", 1)[1]
        that = thu_muc_draft / p
        return that if that.is_file() else that   # trả cả khi thiếu -> báo ở kiểm tra
    ra = Path(path)
    return ra


def _uri(p: Path) -> str:
    """Đường dẫn tuyệt đối -> file:// URI (Premiere cần URI, không nhận đường Windows)."""
    return Path(p).resolve().as_uri()


def doc_draft(thu_muc_draft: Path) -> dict:
    f = Path(thu_muc_draft) / "draft_content.json"
    if not f.is_file():
        raise FcpxmlError(f"Không thấy draft_content.json trong {thu_muc_draft}")
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FcpxmlError(f"Đọc draft hỏng: {exc}") from exc


def _gom_material(draft: dict) -> dict:
    """material_id -> (loại, dict). Một chỗ tra, khỏi lặp 3 vòng lặp."""
    ra = {}
    for loai in ("videos", "audios", "texts"):
        for x in draft.get("materials", {}).get(loai) or []:
            if x.get("id"):
                ra[x["id"]] = (loai, x)
    return ra


def _toc_do(draft: dict, seg: dict) -> float:
    """Tốc độ phát của 1 đoạn. CapCut để trong material 'speed' tham chiếu chéo."""
    sp = {x["id"]: x for x in draft.get("materials", {}).get("speeds") or []}
    for r in seg.get("extra_material_refs") or []:
        if r in sp:
            return float(sp[r].get("speed") or 1.0)
    return float(seg.get("speed") or 1.0)


def draft_sang_fcpxml(thu_muc_draft: Path, ten_seq: str = "") -> tuple[str, list[str]]:
    """Dịch 1 draft CapCut -> (chuỗi XML, danh sách cảnh báo)."""
    thu_muc_draft = Path(thu_muc_draft)
    draft = doc_draft(thu_muc_draft)
    fps = int(draft.get("fps") or 30)
    cv = draft.get("canvas_config") or {}
    w, h = int(cv.get("width") or 1920), int(cv.get("height") or 1080)
    tong = float(draft.get("duration") or 0) / MICRO
    mats = _gom_material(draft)
    canh_bao: list[str] = []

    fcpxml = ET.Element("fcpxml", version="1.8")
    res = ET.SubElement(fcpxml, "resources")
    ET.SubElement(res, "format", id="r0", name=f"FFVideoFormat{h}p{fps}",
                  frameDuration=f"100/{fps * 100}s",
                  width=str(w), height=str(h))

    # ------------------------------------------------------ tài nguyên media
    asset_id: dict[str, str] = {}
    thieu: list[str] = []
    n = 0
    for mid, (loai, mat) in mats.items():
        if loai == "texts":
            continue
        that = _duong_dan_that(mat.get("path") or "", thu_muc_draft)
        if that is None:
            continue
        if not that.is_file():
            thieu.append(that.name)
        n += 1
        aid = f"r{n}"
        asset_id[mid] = aid
        keo = float(mat.get("duration") or 0) / MICRO
        co_hinh = "1" if loai == "videos" else "0"
        a = ET.SubElement(res, "asset", id=aid, name=that.stem,
                          src=_uri(that), start="0s",
                          duration=_tick(keo, fps),
                          hasVideo=co_hinh, hasAudio="1",
                          format="r0" if loai == "videos" else "")
        if loai != "videos":
            del a.attrib["format"]
    if thieu:
        canh_bao.append(f"{len(thieu)} file media không thấy trên đĩa "
                        f"(vd {thieu[0]}) — Premiere sẽ báo offline")

    # ------------------------------------------------------------- timeline
    lib = ET.SubElement(fcpxml, "library")
    ev = ET.SubElement(lib, "event", name="RenderY")
    proj = ET.SubElement(ev, "project", name=ten_seq or thu_muc_draft.name)
    seq = ET.SubElement(proj, "sequence", format="r0",
                        duration=_tick(tong, fps),
                        tcStart="0s", tcFormat="NDF")
    spine = ET.SubElement(seq, "spine")

    tracks = draft.get("tracks") or []
    # Track video ĐẦU TIÊN có đoạn = lớp nền -> vào spine. Còn lại thành lớp phủ
    # (connected clip) gắn vào clip nền, đúng mô hình FCPXML: spine là 1 mạch chính.
    nen_idx = next((i for i, t in enumerate(tracks)
                    if t.get("type") == "video" and t.get("segments")), None)
    if nen_idx is None:
        raise FcpxmlError("Draft không có track video nào có đoạn")

    def them_clip(cha, seg, lane: Optional[int] = None,
                  khung_bat_dau: Optional[int] = None):
        """`khung_bat_dau` ép clip bắt đầu ĐÚNG khung chỉ định (dùng cho lớp nền).

        Làm tròn từng clip độc lập thì clip này kết thúc lệch ±1 khung so với chỗ
        clip kia bắt đầu — trong spine FCPXML, khe hở là LỖ ĐEN trên timeline còn
        chồng lấn thì Premiere tự đẩy, xô lệch mọi thứ phía sau. Nên lớp nền phải
        bám mép nhau tuyệt đối, tính bằng KHUNG chứ không phải giây.
        """
        mid = seg.get("material_id")
        aid = asset_id.get(mid)
        if not aid:
            return None
        loai, mat = mats[mid]
        tgt = seg.get("target_timerange") or {}
        src = seg.get("source_timerange") or {}
        offset = float(tgt.get("start") or 0) / MICRO
        keo = float(tgt.get("duration") or 0) / MICRO
        bat_dau = float(src.get("start") or 0) / MICRO
        toc = _toc_do(draft, seg)

        k_off = round(offset * fps) if khung_bat_dau is None else khung_bat_dau
        # Độ dài lấy theo MỐC KẾT của draft, không phải làm tròn riêng độ dài: giữ
        # đúng điểm cắt tuyệt đối, sai số không cộng dồn qua 25 clip.
        k_het = round((offset + keo) * fps)
        k_keo = max(1, k_het - k_off)

        el = ET.SubElement(cha, "asset-clip",
                           ref=aid, name=Path(mat.get("path") or aid).stem,
                           offset=_khung(k_off, fps), start=_tick(bat_dau, fps),
                           duration=_khung(k_keo, fps))
        if lane is not None:
            el.set("lane", str(lane))
        if loai != "videos":
            el.set("audioRole", "dialogue")
        # Tốc độ: FCPXML tả bằng <timeMap>. Premiere đọc được và giữ đúng độ dài.
        if abs(toc - 1.0) > 1e-6:
            tm = ET.SubElement(el, "timeMap")
            ET.SubElement(tm, "timept", time="0s", value="0s",
                          interp="linear")
            ET.SubElement(tm, "timept", time=_tick(keo, fps),
                          value=_tick(keo * toc, fps), interp="linear")
        vol = seg.get("volume")
        if vol is not None and abs(float(vol) - 1.0) > 1e-6:
            el.set("audioVolume", f"{float(vol):.4f}")
        return el, k_off + k_keo

    # Lớp nền: clip sau bắt đầu ĐÚNG chỗ clip trước kết thúc -> không hở, không chồng.
    clip_nen: list = []
    ket_truoc: Optional[int] = None
    for seg in tracks[nen_idx].get("segments") or []:
        ra = them_clip(spine, seg, khung_bat_dau=ket_truoc)
        if ra is None:
            continue
        el, ket_truoc = ra
        clip_nen.append((float((seg.get("target_timerange") or {}).get("start") or 0) / MICRO, el))

    if not clip_nen:
        raise FcpxmlError("Không dựng được clip nào — kiểm tra đường dẫn media của draft")

    def clip_chua(giay: float):
        """Clip nền đang phủ mốc thời gian này (lớp phủ phải gắn vào nó)."""
        chon = clip_nen[0][1]
        for bd, el in clip_nen:
            if bd <= giay:
                chon = el
            else:
                break
        return chon

    # lớp phủ: mỗi track thành 1 lane. Video lane dương (nằm TRÊN), audio lane âm.
    lane_v, lane_a = 1, -1
    so_text = 0
    for i, t in enumerate(tracks):
        if i == nen_idx or not t.get("segments"):
            continue
        loai = t.get("type")
        if loai == "text":
            so_text += len(t["segments"])
            continue
        lane = lane_v if loai == "video" else lane_a
        for seg in t["segments"]:
            bd = float((seg.get("target_timerange") or {}).get("start") or 0) / MICRO
            them_clip(clip_chua(bd), seg, lane=lane)   # lớp phủ neo theo giây, khỏi bám mép
        if loai == "video":
            lane_v += 1
        else:
            lane_a -= 1

    # Chữ -> marker (xem docstring: cố dịch style sẽ ra sai font/màu).
    if so_text:
        for t in tracks:
            if t.get("type") != "text":
                continue
            for seg in t.get("segments") or []:
                tgt = seg.get("target_timerange") or {}
                bd = float(tgt.get("start") or 0) / MICRO
                keo = float(tgt.get("duration") or 0) / MICRO
                loai, mat = mats.get(seg.get("material_id"), ("", {}))
                chu = ""
                try:
                    chu = (json.loads(mat.get("content") or "{}").get("text") or "")[:60]
                except (json.JSONDecodeError, AttributeError):
                    chu = (mat.get("content") or "")[:60]
                el = clip_chua(bd)
                mk = ET.SubElement(el, "marker",
                                   start=_tick(bd, fps),
                                   duration=_tick(max(keo, 1 / fps), fps),
                                   value=f"CHỮ: {chu}" if chu else "CHỮ")
                mk.set("completed", "0")
        canh_bao.append(f"{so_text} đoạn chữ chuyển thành MARKER (không phải title có "
                        f"kiểu dáng) — xem marker để biết đặt chữ ở đâu")

    tho = ET.tostring(fcpxml, encoding="utf-8")
    dep = minidom.parseString(tho).toprettyxml(indent="  ", encoding="utf-8")
    xml = dep.decode("utf-8")
    # DOCTYPE để Premiere nhận diện chắc chắn
    xml = xml.replace('<?xml version="1.0" encoding="utf-8"?>',
                      '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>', 1)
    return xml, canh_bao


def xuat_fcpxml(thu_muc_draft: Path, dich: Path, ten_seq: str = "") -> list[str]:
    """Dịch draft -> ghi file .fcpxml. Trả danh sách cảnh báo."""
    xml, canh_bao = draft_sang_fcpxml(thu_muc_draft, ten_seq)
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    dich.write_text(xml, encoding="utf-8")
    return canh_bao

