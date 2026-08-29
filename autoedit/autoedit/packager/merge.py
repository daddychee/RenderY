"""Gộp nhiều draft CapCut (từng chương) thành MỘT draft tổng — RenderY R7.

Quy trình của user là tuyến tính theo chương: ren voice chương 1 -> tool dựng chương 1,
trong lúc đó user ren voice chương 2... Mỗi chương ra một draft riêng. Cuối cùng cần
một draft tổng mở ra là có cả phim đúng thứ tự.

Gộp = nối tiếp theo THỜI GIAN:
- Draft thứ N dịch mọi `target_timerange.start` thêm offset = tổng duration các draft trước.
- Materials gộp lại; id trùng giữa 2 draft thì ĐỔI id của draft sau (kèm mọi tham chiếu),
  vì `material_id` / `extra_material_refs` / `keyframe_refs` trỏ theo id.
- Track gộp THEO TÊN (`video_l1` vào `video_l1`), track chỉ có ở draft sau thì thêm mới.
- File media copy vào `materials/` của draft tổng; trùng tên khác nội dung thì thêm hậu tố.

Giữ nguyên các luật CapCut đã trả giá (xem CLAUDE_PADOMA_GOC.md §4):
- C1: `content["id"]` của draft tổng là id MỚI (draft mới = timeline mới), nhưng KHÔNG
  bao giờ sửa id của draft nguồn tại chỗ.
- C2: path media giữ dạng placeholder `##_draftpath_placeholder_<GUID>_##/materials/...`.
- C5: không đè draft đã có — caller tự đặt tên mới.
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from autoedit.packager.packager import PackageError

# Nhóm materials là list các dict có "id" — gộp được. Khoá khác (dict/số) giữ của draft ĐẦU.
_MERGEABLE = ("videos", "audios", "texts", "speeds", "material_animations",
              "canvases", "sound_channel_mappings", "vocal_separations",
              "beats", "placeholders", "stickers", "effects", "transitions",
              "audio_fades", "video_effects", "masks", "hsl", "loudnesses")


def _uid() -> str:
    return uuid.uuid4().hex


def read_draft(draft_dir: Path) -> dict:
    """Đọc draft_content.json. Raise PackageError nếu thiếu/hỏng."""
    p = Path(draft_dir) / "draft_content.json"
    if not p.is_file():
        raise PackageError(f"Không thấy draft_content.json trong {draft_dir}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PackageError(f"draft_content.json hỏng ({draft_dir.name}): {exc}") from exc


def draft_duration(content: dict) -> int:
    """Duration (µs) — ưu tiên trường `duration`, không có thì suy từ segment cuối."""
    dur = int(content.get("duration") or 0)
    if dur > 0:
        return dur
    end = 0
    for track in content.get("tracks", []):
        for seg in track.get("segments", []):
            tr = seg.get("target_timerange") or {}
            end = max(end, int(tr.get("start", 0)) + int(tr.get("duration", 0)))
    return end


def _material_ids(content: dict) -> set[str]:
    out: set[str] = set()
    for key in _MERGEABLE:
        for m in content.get("materials", {}).get(key) or []:
            if isinstance(m, dict) and m.get("id"):
                out.add(m["id"])
    return out


def _remap_ids(content: dict, mapping: dict[str, str]) -> None:
    """Đổi id material + MỌI tham chiếu tới chúng, tại chỗ."""
    if not mapping:
        return
    for key in _MERGEABLE:
        for m in content.get("materials", {}).get(key) or []:
            if isinstance(m, dict) and m.get("id") in mapping:
                m["id"] = mapping[m["id"]]
    for track in content.get("tracks", []):
        for seg in track.get("segments", []):
            if seg.get("material_id") in mapping:
                seg["material_id"] = mapping[seg["material_id"]]
            for field in ("extra_material_refs", "keyframe_refs"):
                refs = seg.get(field)
                if isinstance(refs, list):
                    seg[field] = [mapping.get(r, r) for r in refs]


def _shift_segments(content: dict, offset_us: int) -> None:
    """Dịch mọi segment sang phải `offset_us` — chỉ đụng target, KHÔNG đụng source."""
    if offset_us <= 0:
        return
    for track in content.get("tracks", []):
        for seg in track.get("segments", []):
            tr = seg.get("target_timerange")
            if isinstance(tr, dict):
                tr["start"] = int(tr.get("start", 0)) + offset_us


def _copy_media(src_dir: Path, dst_dir: Path, content: dict) -> None:
    """Copy materials/ của draft nguồn sang draft tổng, đổi tên khi trùng khác nội dung."""
    src_mat = Path(src_dir) / "materials"
    dst_mat = Path(dst_dir) / "materials"
    if not src_mat.is_dir():
        return
    dst_mat.mkdir(parents=True, exist_ok=True)
    rename: dict[str, str] = {}
    for f in sorted(src_mat.iterdir()):
        if not f.is_file():
            continue
        target = dst_mat / f.name
        if target.exists():
            if target.stat().st_size == f.stat().st_size:
                continue                       # cùng file (clip dùng lại giữa các chương)
            stem, suf, n = f.stem, f.suffix, 1
            while (dst_mat / f"{stem}_{n}{suf}").exists():
                n += 1
            target = dst_mat / f"{stem}_{n}{suf}"
            rename[f.name] = target.name
        shutil.copy2(f, target)

    if rename:  # file bị đổi tên -> sửa path trong materials cho khớp
        for key in _MERGEABLE:
            for m in content.get("materials", {}).get(key) or []:
                if not isinstance(m, dict):
                    continue
                for field in ("path", "media_path"):
                    val = m.get(field) or ""
                    name = val.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                    if name in rename:
                        m[field] = val[: len(val) - len(name)] + rename[name]


def merge_contents(parts: list[dict]) -> dict:
    """Gộp nội dung draft (đã copy media). Trả content mới, KHÔNG sửa parts tại chỗ."""
    if not parts:
        raise PackageError("Không có draft nào để gộp")
    import copy

    merged = copy.deepcopy(parts[0])
    merged["id"] = str(uuid.uuid4()).upper()   # C1: draft mới = timeline mới
    used_ids = _material_ids(merged)
    offset = draft_duration(merged)

    for part in parts[1:]:
        cur = copy.deepcopy(part)
        # id trùng -> đổi id của draft SAU (draft đầu giữ nguyên, ít xáo trộn nhất)
        clash = _material_ids(cur) & used_ids
        _remap_ids(cur, {old: _uid() for old in clash})
        used_ids |= _material_ids(cur)

        _shift_segments(cur, offset)

        for key in _MERGEABLE:
            items = cur.get("materials", {}).get(key)
            if items:
                merged.setdefault("materials", {}).setdefault(key, []).extend(items)

        # Track gộp THEO TÊN; track lạ thì thêm mới (giữ nguyên thứ tự xuất hiện)
        by_name = {t.get("name"): t for t in merged.get("tracks", []) if t.get("name")}
        for track in cur.get("tracks", []):
            target = by_name.get(track.get("name"))
            if target is not None and target.get("type") == track.get("type"):
                target.setdefault("segments", []).extend(track.get("segments", []))
            else:
                merged.setdefault("tracks", []).append(track)
                if track.get("name"):
                    by_name[track["name"]] = track

        offset += draft_duration(part)

    merged["duration"] = offset
    for track in merged.get("tracks", []):
        track.get("segments", []).sort(
            key=lambda s: int((s.get("target_timerange") or {}).get("start", 0)))
    return merged


def merge_drafts(draft_dirs: list[Path], out_dir: Path, overwrite: bool = False) -> Path:
    """Gộp các draft chương -> draft tổng tại `out_dir`. Trả đường dẫn draft tổng."""
    dirs = [Path(d) for d in draft_dirs]
    if len(dirs) < 2:
        raise PackageError("Cần ít nhất 2 draft để gộp")
    out_dir = Path(out_dir)
    if out_dir.exists() and not overwrite:
        # C5: CapCut cache draft_id theo folder — đè draft cũ làm nó không mở được
        raise PackageError(f"Draft đích đã tồn tại: {out_dir} (dùng --overwrite nếu chắc)")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    parts: list[dict] = []
    for d in dirs:
        content = read_draft(d)
        _copy_media(d, out_dir, content)   # copy TRƯỚC khi gộp (có thể đổi tên file)
        parts.append(content)

    merged = merge_contents(parts)
    (out_dir / "draft_content.json").write_text(
        json.dumps(merged, ensure_ascii=False), encoding="utf-8")
    (out_dir / "draft_info.json").write_text(
        json.dumps(merged, ensure_ascii=False), encoding="utf-8")

    # draft_meta_info.json: lấy của draft đầu, sửa tên/đường dẫn/duration cho khớp
    meta_src = dirs[0] / "draft_meta_info.json"
    if meta_src.is_file():
        meta = json.loads(meta_src.read_text(encoding="utf-8"))
        meta["draft_name"] = out_dir.name
        meta["draft_fold_path"] = str(out_dir).replace("\\", "/")
        meta["draft_root_path"] = str(out_dir.parent).replace("\\", "/")
        meta["draft_id"] = str(uuid.uuid4()).upper()   # draft mới = id mới
        meta["tm_duration"] = merged["duration"]
        (out_dir / "draft_meta_info.json").write_text(
            json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    cover = dirs[0] / "draft_cover.jpg"
    if cover.is_file():
        shutil.copy2(cover, out_dir / "draft_cover.jpg")
    return out_dir


def merge_sourcebooks(draft_dirs: list[Path], out_dir: Path) -> Path | None:
    """Gộp sổ nguồn footage của các chương -> sổ tổng. None nếu không chương nào có sổ."""
    from autoedit.packager.sourcebook import render_text, summarize

    rows: list[dict] = []
    for i, d in enumerate(draft_dirs, start=1):
        p = Path(d) / "nguon_footage.json"
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        for c in data.get("clips", []):
            c = dict(c)
            c["chapter"] = i          # chương = thứ tự draft, không phải chapter trong part
            rows.append(c)
    if not rows:
        return None

    out_dir = Path(out_dir)
    summary = summarize(rows)
    (out_dir / "nguon_footage.json").write_text(json.dumps(
        {"project_id": out_dir.name, "summary": summary, "clips": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")
    txt = out_dir / "nguon_footage.txt"
    txt.write_text(render_text(rows, summary, out_dir.name), encoding="utf-8")
    return txt
