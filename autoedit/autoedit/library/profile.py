"""niche_profile.yaml — hồ sơ niche do NGƯỜI xây khi mở niche mới (PRD Stage 4, P6).

Cấu trúc thư viện:
~/AutoEdit/library/<niche>/
  niche_profile.yaml
  signature/        # footage chữ ký — hook bắt buộc 1-2 shot từ đây
  entity/           # ảnh thực thể đã tải (M5 route entity cache vào đây)
  <chủ-đề-con>/     # folder tự do: vietnam/, portugal/...
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

DEFAULT_LIBRARY_ROOT = Path("~/AutoEdit/library").expanduser()
PROFILE_FILENAME = "niche_profile.yaml"
LIBRARY_ROOT_ENV = "AUTOEDIT_LIBRARY_ROOT"


def resolve_library_root(override: str | Path | None = None) -> Path:
    """Library root hiệu lực, theo ưu tiên giảm dần:

    1. override tường minh (cờ --library-root)
    2. biến môi trường AUTOEDIT_LIBRARY_ROOT
    3. machine.json -> library_root (cấu hình theo máy, đặt bằng `set-library-root`)
    4. mặc định ~/AutoEdit/library

    Cho phép footage nằm ở ổ khác (vd F:\\FOOTAGE) mà không sửa code.
    """
    if override:
        return Path(override).expanduser()
    env = os.environ.get(LIBRARY_ROOT_ENV, "").strip()
    if env:
        return Path(env).expanduser()
    try:
        from autoedit.packager.machine import MachineProfile

        prof = MachineProfile.load()
        if prof.library_root:
            return Path(prof.library_root).expanduser()
    except Exception:
        # Chưa register-machine / profile lỗi -> rơi về mặc định, không chặn
        pass
    return DEFAULT_LIBRARY_ROOT


class NicheProfile(BaseModel):
    niche: str
    description: str = ""
    # Query an toàn của niche — tier thematic rút từ đây (P5)
    safe_pool: list[str] = Field(default_factory=list)
    # Loại footage khán giả kênh ưa — đổ vào slot visual_anchor=false (P4)
    audience_bias: list[str] = Field(default_factory=list)
    # Cấm kỵ của niche (vd kênh sức khỏe cấm cảnh rượu bia)
    banned: list[str] = Field(default_factory=list)

    def save(self, niche_dir: Path) -> Path:
        path = niche_dir / PROFILE_FILENAME
        path.write_text(
            yaml.safe_dump(self.model_dump(mode="json"), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, niche_dir: Path) -> "NicheProfile":
        path = niche_dir / PROFILE_FILENAME
        if not path.is_file():
            raise FileNotFoundError(
                f"Không thấy {PROFILE_FILENAME} trong {niche_dir} — chạy `autoedit library-init` trước."
            )
        return cls.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def niche_dir(niche: str, root: Path = DEFAULT_LIBRARY_ROOT) -> Path:
    return root / niche


def init_niche(niche: str, root: Path = DEFAULT_LIBRARY_ROOT) -> Path:
    """Scaffold folder niche + profile mẫu (người điền tiếp sau khi nghiên cứu kênh top)."""
    d = niche_dir(niche, root)
    for sub in ("signature", "entity"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    if not (d / PROFILE_FILENAME).is_file():
        NicheProfile(
            niche=niche,
            description="TODO: mô tả niche — xem 5-10 kênh top, liệt kê nhóm footage lặp lại",
            safe_pool=["TODO: query chủ đề an toàn, vd 'retirement abroad'"],
            audience_bias=["TODO: loại footage khán giả ưa, vd 'beach sunset aerial'"],
            banned=[],
        ).save(d)
    return d
