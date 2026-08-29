"""Draft Packager — đóng gói draft content thành folder CapCut mở được.

Cơ chế đã kiểm chứng 11/06/2026 (PADOMA_TEST_V2, CapCut Mac 8.1.1):
- File nội dung tên `draft_info.json`, ghi thêm bản sao `draft_content.json`
- Đè 9 trường top-level từ donor (xem machine.DONOR_CONTENT_KEYS)
- `draft_meta_info.json` theo template donor, với `draft_fold_path` =
  đường dẫn tuyệt đối THẬT của folder draft (rỗng → lỗi "unusual path")
- Mọi asset path trong draft phải tuyệt đối và tồn tại trước khi ghi
- PORTABLE (kiểm chứng 13/07/2026, SP1-014 mở tốt trên 2 máy — MO_TA_VAN_HANH_PORTABLE.md):
  sau khi embed media, path trong CONTENT đổi về placeholder toàn cục của CapCut
  `##_draftpath_placeholder_<GUID>_##/materials/<tên>` + check_flag video nâng lên
  native 62978047 → copy nguyên folder draft sang máy editor khác là mở được,
  KHÔNG relink. (Path tuyệt đối máy gốc + 63487 → CapCut coi là "cloud material
  thiếu", báo "Không thể tải xuống tài liệu" và không cho relink — AutoClone §B4.)
"""

from __future__ import annotations

import json
import re
import shutil
import time
import uuid
from pathlib import Path

from autoedit.packager.machine import MachineProfile

_ASCII_NAME = re.compile(r"^[A-Za-z0-9_\-]+$")

# Placeholder "folder draft này" của CapCut — GUID là HẰNG SỐ TOÀN CỤC (quét 401 file
# draft Mac + Windows editor 13/07/2026: tất cả cùng đúng 1 GUID này).
CAPCUT_PLACEHOLDER = "##_draftpath_placeholder_0E685133-18CE-45ED-8CB8-2904A212EC80_##"
# check_flag video: native "verified-local" vs mặc định pycapcut thiếu bit cao.
NATIVE_CHECK_FLAG = 62978047  # 0xF7FF | 0x3C00000
PYCAPCUT_CHECK_FLAG = 63487  # 0xF7FF


class PackageError(ValueError):
    """Lỗi đóng gói draft — báo rõ nguyên nhân cho người dùng."""


def _collect_asset_paths(content: dict) -> list[str]:
    """Gom mọi path asset trong materials (videos/audios/ảnh dùng chung 'videos')."""
    paths: list[str] = []
    materials = content.get("materials", {})
    for key in ("videos", "audios"):
        for m in materials.get(key, []) or []:
            p = m.get("path", "")
            if p:
                paths.append(p)
    return paths


def verify_assets(content: dict) -> None:
    """Asset path phải tuyệt đối và tồn tại (RA_SOAT_LOGIC 6.4). Lỗi → dừng sớm."""
    problems = []
    for p in _collect_asset_paths(content):
        path = Path(p)
        if not path.is_absolute():
            problems.append(f"path không tuyệt đối: {p}")
        elif not path.is_file():
            problems.append(f"file không tồn tại: {p}")
    if problems:
        raise PackageError(
            "Asset chưa sẵn sàng, không ghi draft:\n  - " + "\n  - ".join(problems)
        )


def package_draft(
    content: dict,
    draft_name: str,
    profile: MachineProfile,
    overwrite: bool = False,
) -> Path:
    """Ghi draft folder hoàn chỉnh vào capcut_root của máy. Trả về path folder.

    Args:
        content: dict draft content (từ pycapcut ScriptFile.dumps() hoặc tự ráp).
        draft_name: tên draft — bắt buộc ASCII slug (RA_SOAT_LOGIC 6.7).
        profile: machine profile từ register-machine.
        overwrite: cho phép đè draft trùng tên.
    """
    if not _ASCII_NAME.match(draft_name):
        raise PackageError(
            f"Tên draft phải ASCII (chữ/số/_-), không dấu, không khoảng trắng: {draft_name!r}"
        )

    verify_assets(content)

    donor_root = Path(profile.capcut_root)  # nơi donor sống — cover lấy từ đây
    root = profile.out_root()
    if profile.draft_out_root:
        root.mkdir(parents=True, exist_ok=True)  # folder xuất do user đặt — tự tạo
    elif not root.is_dir():
        raise PackageError(
            f"capcut_root không tồn tại: {root} — máy này đã cài CapCut chưa? "
            "Chạy lại `autoedit register-machine`."
        )
    draft_dir = root / draft_name
    if draft_dir.exists() and not overwrite:
        raise PackageError(f"Draft đã tồn tại: {draft_dir} (dùng --overwrite để đè).")

    # --- draft_info.json: content + 9 trường donor ---------------------------
    content = dict(content)  # không sửa dict gốc của caller
    # NHÚNG media vào trong folder draft: CapCut bị sandbox (chỉ đọc được file
    # user tự chọn hoặc trong ~/Movies/CapCut). Media ở ~/Documents -> bắt relink.
    # Copy vào <draft>/materials/ -> CapCut luôn có quyền (bài học 13/06 + RA_SOAT 6.4).
    _embed_media(content, draft_dir)
    content.update(profile.content_overrides)
    content["id"] = str(uuid.uuid4()).upper()
    now_sec = int(time.time())
    content["create_time"] = now_sec
    content["update_time"] = now_sec

    # --- draft_meta_info.json: template donor + identity draft mới -----------
    meta = dict(profile.meta_template)
    now_us = now_sec * 1_000_000
    meta.update(
        {
            "draft_fold_path": str(draft_dir),  # tuyệt đối — rỗng là "unusual path"
            "draft_root_path": str(root),
            "draft_name": draft_name,
            "draft_id": str(uuid.uuid4()).upper(),
            "tm_draft_create": now_us,
            "tm_draft_modified": now_us,
            "tm_duration": int(content.get("duration", 0)),
            "draft_removable_storage_device": "",
        }
    )
    # Sổ đăng ký media: PHẢI là media của draft này — kế thừa sổ của donor làm
    # CapCut bắt relink (bài học 12/06, draft SAMPLE_GOLD_CARD đầu tiên)
    meta["draft_materials"] = _build_draft_materials(content, meta, now_sec, now_us, draft_dir)
    # local_material_id phải KHỚP id trong sổ (pycapcut điền hex ngẫu nhiên không
    # khớp -> CapCut coi là import dở dang, đòi relink — bài học 12/06 lần 2)
    _link_materials_to_registry(content, meta["draft_materials"])

    # Cover: copy từ donor nếu có, không thì bỏ tham chiếu
    donor_cover = donor_root / profile.donor_name / str(meta.get("draft_cover") or "")
    has_cover = bool(meta.get("draft_cover")) and donor_cover.is_file()
    if not has_cover:
        meta["draft_cover"] = ""

    # PORTABLE: path nội bộ draft trong CONTENT -> placeholder (copy sang máy khác
    # vẫn mở); meta GIỮ fold_path tuyệt đối (stale trên máy khác vô hại — đã kiểm).
    # _to_portable trả bản MỚI: content của caller giữ path tuyệt đối (re-package được).
    content = _to_portable(content, draft_dir)

    # --- ghi xuống disk -------------------------------------------------------
    draft_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(content, ensure_ascii=False)
    (draft_dir / "draft_info.json").write_text(payload, encoding="utf-8")
    (draft_dir / "draft_content.json").write_text(payload, encoding="utf-8")  # bản sao cho chắc
    (draft_dir / "draft_meta_info.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    if has_cover:
        shutil.copy2(donor_cover, draft_dir / meta["draft_cover"])

    verify_draft(draft_dir)
    return draft_dir


def _embed_media(content: dict, draft_dir: Path) -> None:
    """Copy mọi media material vào <draft>/materials/ và đổi path thành nội bộ draft.

    CapCut sandbox chỉ đọc được vùng của nó (~/Movies/CapCut) -> media ngoài đó
    (vd ~/Documents) bị bắt relink. Draft tự chứa cũng mang được sang máy editor khác.
    """
    mat_dir = draft_dir / "materials"
    mat_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}  # src path -> path nội bộ draft (dedupe clip tái dùng)
    for kind in ("videos", "audios"):
        for m in content.get("materials", {}).get(kind, []) or []:
            src = m.get("path", "")
            if not src:
                continue
            if src not in copied:
                dst = mat_dir / Path(src).name
                # tránh trùng tên giữa 2 nguồn khác nhau
                stem, suf, n = dst.stem, dst.suffix, 1
                while dst.exists() and str(dst) not in copied.values():
                    dst = mat_dir / f"{stem}_{n}{suf}"
                    n += 1
                shutil.copy2(src, dst)
                copied[src] = str(dst)
            m["path"] = copied[src]


def _to_portable(content: dict, draft_dir: Path) -> dict:
    """Bản CONTENT portable: path nội bộ draft -> placeholder CapCut, check_flag native.

    Trả CÂY MỚI — không đụng dict của caller. Combo placeholder + 62978047 là đúng
    dạng draft native (DS3_003: 265/267 video placeholder, flag 62978047) và đã đạt
    cổng mắt 2 máy với SP1-014 (13/07/2026). KHÔNG đổi content["id"] (C1 — id không
    phải path nên walk không chạm).
    """
    prefix_bs = str(draft_dir).rstrip("\\/")
    variants = (prefix_bs.lower(), prefix_bs.replace("\\", "/").lower())

    def swap(s: str) -> str:
        low = s.lower()
        for var in variants:
            i = low.find(var)
            if i >= 0:
                return (s[:i] + CAPCUT_PLACEHOLDER + s[i + len(var):]).replace("\\", "/")
        return s

    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, str):
            return swap(node)
        return node

    portable = walk(content)
    for m in (portable.get("materials") or {}).get("videos") or []:
        if isinstance(m, dict) and m.get("check_flag") == PYCAPCUT_CHECK_FLAG:
            m["check_flag"] = NATIVE_CHECK_FLAG
    return portable


def _build_draft_materials(content: dict, meta: dict, now_sec: int, now_us: int,
                           draft_dir: Path) -> list:
    """Sinh sổ đăng ký media (draft_meta_info.draft_materials) từ materials của draft.

    Cấu trúc theo draft thật (donor 0428): list block {type, value}; media nằm ở
    block type=0; metetype: video | photo | music; photo duration đăng ký 5s.
    file_Path ghi TƯƠNG ĐỐI `./materials/<tên>` — đúng quy ước draft native
    (DS3_003, SP1-014 sau khi CapCut mở) để sổ sống khi copy sang máy khác.
    """
    entries = []

    def add_entry(m: dict, metetype: str) -> None:
        path = m.get("path", "")
        if not path:
            return
        duration = 5_000_000 if metetype == "photo" else int(m.get("duration", 0))
        entries.append(
            {
                "ai_group_type": "",
                "create_time": now_sec,
                "duration": duration,
                "enter_from": 0,
                "extra_info": Path(path).name,
                "file_Path": "./" + Path(path).relative_to(draft_dir).as_posix(),
                "height": m.get("height", 0) or 0,
                "id": str(uuid.uuid4()),
                "import_time": now_sec,
                "import_time_ms": now_us,
                "item_source": 1,
                "md5": "",
                "metetype": metetype,
                "roughcut_time_range": {"duration": duration, "start": 0},
                "sub_time_range": {"duration": -1, "start": -1},
                "type": 0,
                "width": m.get("width", 0) or 0,
            }
        )

    seen: set[str] = set()
    for m in content.get("materials", {}).get("videos", []) or []:
        if m.get("path") and m["path"] not in seen:
            seen.add(m["path"])
            add_entry(m, "photo" if m.get("type") == "photo" else "video")
    for m in content.get("materials", {}).get("audios", []) or []:
        if m.get("path") and m["path"] not in seen:
            seen.add(m["path"])
            add_entry(m, "music")

    # Giữ khung block của donor (các type 1,2,3,6,7,8 rỗng), thay ruột type 0
    template_blocks = meta.get("draft_materials") or [{"type": 0, "value": []}]
    blocks = []
    placed = False
    for b in template_blocks:
        if isinstance(b, dict) and b.get("type") == 0:
            blocks.append({"type": 0, "value": entries})
            placed = True
        elif isinstance(b, dict):
            blocks.append({"type": b.get("type"), "value": []})
    if not placed:
        blocks.insert(0, {"type": 0, "value": entries})
    return blocks


def _link_materials_to_registry(content: dict, draft_materials: list) -> None:
    """Gán local_material_id của material = id entry sổ đăng ký (khớp theo TÊN file —
    file_Path sổ giờ tương đối, tên file duy nhất do _embed_media chống trùng).

    Quy luật quan sát từ draft thật (0428): local_material_id hoặc RỖNG hoặc
    KHỚP registry; audio local có music_id rỗng. Id lửng lơ -> CapCut đòi relink.
    """
    id_by_name = {
        e["extra_info"]: e["id"]
        for b in draft_materials
        for e in b.get("value", [])
    }
    for kind in ("videos", "audios"):
        for m in content.get("materials", {}).get(kind, []) or []:
            reg_id = id_by_name.get(Path(m.get("path", "")).name)
            if reg_id:
                m["local_material_id"] = reg_id
            if kind == "audios" and "music_id" in m:
                m["music_id"] = ""  # file local không phải nhạc thư viện CapCut


def verify_draft(draft_dir: Path) -> None:
    """Kiểm tra draft folder sau khi ghi — fail sớm còn hơn CapCut báo lỗi mù."""
    problems = []
    for name in ("draft_info.json", "draft_content.json", "draft_meta_info.json"):
        f = draft_dir / name
        if not f.is_file():
            problems.append(f"thiếu {name}")
            continue
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{name} không phải JSON hợp lệ: {exc}")
    if not problems:
        meta = json.loads((draft_dir / "draft_meta_info.json").read_text(encoding="utf-8"))
        if meta.get("draft_fold_path") != str(draft_dir):
            problems.append(
                f"draft_fold_path lệch: {meta.get('draft_fold_path')!r} != {str(draft_dir)!r}"
            )
    if problems:
        raise PackageError(f"Draft {draft_dir} không hợp lệ: " + "; ".join(problems))
