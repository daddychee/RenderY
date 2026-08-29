"""Machine profile — cơ chế `register-machine` (RA_SOAT_LOGIC 6.1, 6.2).

Mỗi máy editor đăng ký 1 lần: đọc một draft THẬT do CapCut trên máy đó tạo
("donor") để lấy đúng platform block, version, root path. Draft do tool sinh
sẽ được đè các trường này theo profile → CapCut nhận draft như draft nội bộ.

Profile lưu ở ~/.autoedit/machine.json — theo MÁY, không theo repo.
"""

from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

# Các trường top-level của draft_info.json phải copy từ donor.
# Đã kiểm chứng 11/06/2026: platform + last_modified_platform + new_version
# + 5 trường donor có mà pycapcut không sinh (thiếu → CapCut từ chối/lỗi path).
DONOR_CONTENT_KEYS = [
    "platform",
    "last_modified_platform",
    "new_version",
    "version",
    "draft_type",
    "function_assistant_info",
    "mixed_track_mode_on",
    "smart_ads_info",
    "uneven_animation_template_info",
]

def _default_capcut_root() -> Path:
    """Folder chứa mọi draft CapCut, theo OS (A1: Windows dùng %LOCALAPPDATA%)."""
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    return Path("~/Movies/CapCut/User Data/Projects/com.lveditor.draft").expanduser()


DEFAULT_CAPCUT_ROOT = _default_capcut_root()

PROFILE_PATH = Path("~/.autoedit/machine.json").expanduser()


class MachineProfile(BaseModel):
    """Hồ sơ CapCut của một máy editor, trích từ donor draft."""

    donor_name: str
    capcut_root: str  # draft_root_path — folder chứa mọi draft trên máy này
    capcut_app_version: str = ""  # để re-test khi CapCut update (6.3)
    library_root: str = ""  # thư viện footage theo máy (rỗng = ~/AutoEdit/library); đặt bằng `set-library-root`
    draft_out_root: str = ""  # folder XUẤT draft mới (rỗng = capcut_root); đặt bằng `set-draft-root`
    data_root: str = ""  # G1 kho chung: gốc cache.db + music/ + sfx/ (rỗng = ~/AutoEdit); đặt bằng `set-data-root`
    db_url: str = ""  # G2 sổ Postgres: postgresql://user:pass@host/db (rỗng = SQLite G1); đặt bằng `set-db-url`
    registered_at: str = ""
    # 9 trường top-level đè vào draft_info.json khi sinh draft
    content_overrides: dict = Field(default_factory=dict)
    # Nguyên bản draft_meta_info.json của donor — template cho meta draft mới
    meta_template: dict = Field(default_factory=dict)

    def out_root(self) -> Path:
        """Folder xuất draft mới — draft_out_root nếu đã đặt, không thì capcut_root."""
        return Path(self.draft_out_root or self.capcut_root)

    def save(self, path: Path = PROFILE_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, path: Path = PROFILE_PATH) -> "MachineProfile":
        if not path.is_file():
            raise FileNotFoundError(
                f"Chưa có machine profile ({path}). Chạy `autoedit register-machine` trước."
            )
        return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _read_donor_content(donor_dir: Path) -> dict:
    """Đọc draft_info.json của donor (fallback draft_content.json)."""
    for name in ("draft_info.json", "draft_content.json"):
        f = donor_dir / name
        if f.is_file():
            return json.loads(f.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        f"Donor không có draft_info.json/draft_content.json: {donor_dir}"
    )


def register_machine(
    donor_dir: Path | str,
    profile_path: Path = PROFILE_PATH,
) -> MachineProfile:
    """Đọc donor draft → trích profile máy → lưu. Trả về profile."""
    donor_dir = Path(donor_dir).expanduser().resolve()
    content = _read_donor_content(donor_dir)
    meta_file = donor_dir / "draft_meta_info.json"
    if not meta_file.is_file():
        raise FileNotFoundError(f"Donor thiếu draft_meta_info.json: {donor_dir}")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))

    overrides = {k: content[k] for k in DONOR_CONTENT_KEYS if k in content}
    missing = [k for k in ("platform", "last_modified_platform", "new_version") if k not in overrides]
    if missing:
        raise ValueError(
            f"Donor thiếu trường bắt buộc {missing} — không phải draft CapCut thật? ({donor_dir})"
        )

    # Root = folder cha của donor; ưu tiên giá trị donor tự khai nếu có
    capcut_root = meta.get("draft_root_path") or str(donor_dir.parent)

    profile = MachineProfile(
        donor_name=donor_dir.name,
        capcut_root=capcut_root,
        capcut_app_version=overrides.get("platform", {}).get("app_version", ""),
        registered_at=datetime.now(timezone.utc).isoformat(),
        content_overrides=overrides,
        meta_template=meta,
    )
    profile.save(profile_path)
    return profile


def set_library_root(path: Path | str, profile_path: Path = PROFILE_PATH) -> MachineProfile:
    """Ghi library_root vào machine.json (cần đã register-machine trước)."""
    profile = MachineProfile.load(profile_path)
    profile.library_root = str(Path(path).expanduser())
    profile.save(profile_path)
    return profile


def set_draft_out_root(path: Path | str, profile_path: Path = PROFILE_PATH) -> MachineProfile:
    """Ghi draft_out_root vào machine.json (cần đã register-machine trước)."""
    profile = MachineProfile.load(profile_path)
    profile.draft_out_root = str(Path(path).expanduser())
    profile.save(profile_path)
    return profile


DATA_ROOT_ENV = "AUTOEDIT_DATA_ROOT"
DEFAULT_DATA_ROOT = Path("~/AutoEdit").expanduser()


def set_data_root(path: Path | str, profile_path: Path = PROFILE_PATH) -> MachineProfile:
    """Ghi data_root vào machine.json (cần đã register-machine trước)."""
    profile = MachineProfile.load(profile_path)
    profile.data_root = str(Path(path).expanduser())
    profile.save(profile_path)
    return profile


def resolve_data_root(override: str | Path | None = None,
                      profile_path: Path = PROFILE_PATH) -> Path:
    """Gốc dữ liệu chung (cache.db + music/ + sfx/), ưu tiên giảm dần:

    1. override tường minh
    2. biến môi trường AUTOEDIT_DATA_ROOT
    3. machine.json -> data_root (đặt bằng `set-data-root`, vd F:\\AutoEdit dùng chung LAN)
    4. mặc định ~/AutoEdit (hành vi cũ — máy chưa set không đổi gì)

    Cùng khuôn resolve_library_root (library/profile.py). Các module đọc giá trị này
    LÚC IMPORT (hằng MUSIC_ROOT/SFX_ROOT/DEFAULT_DB_PATH) — đổi set-data-root xong
    phải chạy process mới.
    """
    if override:
        return Path(override).expanduser()
    env = os.environ.get(DATA_ROOT_ENV, "").strip()
    if env:
        return Path(env).expanduser()
    try:
        prof = MachineProfile.load(profile_path)
        if prof.data_root:
            return Path(prof.data_root).expanduser()
    except Exception:
        # Chưa register-machine / profile lỗi -> rơi về mặc định, không chặn
        pass
    return DEFAULT_DATA_ROOT


DB_URL_ENV = "AUTOEDIT_DB_URL"


def set_db_url(url: str, profile_path: Path = PROFILE_PATH) -> MachineProfile:
    """Ghi db_url vào machine.json (G2; url rỗng = xóa — về SQLite G1)."""
    profile = MachineProfile.load(profile_path)
    profile.db_url = url.strip()
    profile.save(profile_path)
    return profile


def resolve_db_url(override: str | None = None,
                   profile_path: Path = PROFILE_PATH) -> str:
    """URL Postgres cho SỔ (G2), ưu tiên giảm dần — rỗng = SQLite tại data_root (G1):

    1. override tường minh
    2. biến môi trường AUTOEDIT_DB_URL
    3. machine.json -> db_url (đặt bằng `set-db-url`)
    4. rỗng — hành vi G1, máy chưa set không đổi gì

    Khác resolve_data_root: giá trị này đọc MỖI LẦN db.connect() (không phải hằng
    import) — xóa db_url là process mới về SQLite ngay, đúng đường lui G2.
    """
    if override:
        return override.strip()
    env = os.environ.get(DB_URL_ENV, "").strip()
    if env:
        return env
    try:
        prof = MachineProfile.load(profile_path)
        if prof.db_url:
            return prof.db_url.strip()
    except Exception:
        # Chưa register-machine / profile lỗi -> SQLite G1, không chặn
        pass
    return ""


def find_default_donor(capcut_root: Path = DEFAULT_CAPCUT_ROOT) -> Optional[Path]:
    """Tìm donor mặc định: draft sửa gần nhất trong folder CapCut có đủ file.

    Người dùng nên tự chỉ --donor một draft do chính CapCut tạo (vd 0428);
    hàm này chỉ là tiện ích khi không chỉ định.
    """
    if not capcut_root.is_dir():
        return None
    candidates = [
        d
        for d in capcut_root.iterdir()
        if d.is_dir()
        and (d / "draft_meta_info.json").is_file()
        and ((d / "draft_info.json").is_file() or (d / "draft_content.json").is_file())
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda d: (d / "draft_meta_info.json").stat().st_mtime)
