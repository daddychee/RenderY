"""Đường dẫn dùng chung cho công cụ của thư mục biên kịch: đọc `.env` cạnh thư mục (không in giá trị nào).
Chép một lần từ `skill lam phim/cong-cu/cau_hinh.py` (28/09, Spec 40 bước 5a-1), bỏ phần phim mẫu."""

import os
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent          # thư mục "skill bien kich"


def _env(ten: str, mac_dinh: str = "") -> str:
    if os.environ.get(ten):
        return os.environ[ten]
    f = GOC / ".env"
    if f.exists():
        for dong in f.read_text(encoding="utf-8").splitlines():
            if dong.startswith(ten + "="):
                return dong.split("=", 1)[1].strip().strip('"')
    return mac_dinh


def thu_muc_phim() -> Path:
    return Path(_env("THU_MUC_PHIM", r"F:\gen_video_data\phim"))
