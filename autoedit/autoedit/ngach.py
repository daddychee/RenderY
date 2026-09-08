r"""Ngách — đọc từ DANH BẠ NỀN của CRM OUTLIERY (user chốt 08/09/2026).

Vì sao cần: ô Niche trên form nộp tập đang nhập tay TỰ DO. Hậu quả đo được —
Library có CẢ `Life In` LẪN `life-in`, hai thư mục cho cùng một ngách. Ngách
phải chọn từ danh mục đã tạo, không gõ.

**Sổ ở đâu:** `D:\AI AGENT OUTLIERY\data\nen\danh_ba.db`, bảng `ngach`
(`ma`, `ten_chuan`, `trang_thai`, `ghi_chu`, `tao_luc`) — 13 ngách. CRM đọc nó
qua `nen.common.danh_ba`; **không có API HTTP nào**.

**QĐ12 — đọc THẲNG file, chế độ CHỈ ĐỌC.** Không import thư viện của CRM: đỡ
buộc hai tool vào nhau, và mở `mode=ro` thì RenderY không có đường nào ghi hỏng
dữ liệu của cả tổ chức. Đường dẫn khai ở `.env` (`RENDERY_DANH_BA`).

**QĐ13 — cờ "ngách này cần địa danh" đặt Ở ĐÂY, không đặt trong danh bạ.**
Danh bạ là của chung; RenderY thêm cột vào đó là lấn sân. Sửa được qua
`.env` (`RENDERY_NGACH_GEO`) và trang Cài đặt.

**QĐ14 — ba ngách cần địa danh:** LIFE IN · LIVING IN · TRAVEL DOCUMENTARY.
Các ngách khác (COOKING, SENIOR HEALTH, SCI-FI...) nội dung không gắn địa
điểm, ép khai địa danh chỉ làm khay ứng viên nghèo đi vô cớ.

**Fail-open có chủ ý:** CRM tắt / ổ D chưa gắn -> `liet_ke()` trả rỗng và
`hop_le()` trả True. Một app khác chết KHÔNG được kéo cả RenderY chết theo.
Nhưng khi đó `can_dia_danh()` trả True (đòi khai địa danh) — đang mù thì giữ
luật chặt, nới lỏng lúc mù là mở lại đúng bẫy "chợ Trung Quốc cho tập
Afghanistan".
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DUONG_MAC_DINH = r"D:\AI AGENT OUTLIERY\data\nen\danh_ba.db"

# QĐ14. Ghi bằng MÃ (bất biến) — tên chuẩn đổi được, mã thì không.
CAN_DIA_DANH_MAC_DINH = ("N-LIFE-IN", "N-LIVING-IN", "N-TRAVEL-DOCUMENTA")


def duong_danh_ba() -> Path:
    return Path(os.getenv("RENDERY_DANH_BA", "").strip() or DUONG_MAC_DINH)


def _mo() -> sqlite3.Connection:
    """Kết nối CHỈ ĐỌC. `mode=ro` là rào thật: mọi lệnh ghi ném OperationalError."""
    f = duong_danh_ba()
    if not f.is_file():
        raise FileNotFoundError(str(f))
    conn = sqlite3.connect(f"file:{f.as_posix()}?mode=ro", uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def doc_duoc() -> bool:
    """Có đọc được sổ không — UI cần biết để nói rõ khi danh sách rỗng."""
    try:
        conn = _mo()
    except Exception:  # noqa: BLE001
        return False
    try:
        conn.execute("SELECT 1 FROM ngach LIMIT 1").fetchone()
        return True
    except Exception:  # noqa: BLE001
        return False
    finally:
        conn.close()


def _bo_can_geo() -> set[str]:
    """Bộ ngách cần địa danh, khai ở `.env` thì đè mặc định. Nhận mã LẪN tên."""
    raw = os.getenv("RENDERY_NGACH_GEO", "").strip()
    nguon = [x for x in raw.split(",")] if raw else list(CAN_DIA_DANH_MAC_DINH)
    return {x.strip().upper() for x in nguon if x.strip()}


def liet_ke() -> list[dict]:
    """13 ngách + cờ `can_dia_danh`. Sổ hỏng/mất -> [] (fail-open)."""
    try:
        conn = _mo()
    except Exception:  # noqa: BLE001
        return []
    try:
        rows = conn.execute(
            "SELECT ma, ten_chuan, trang_thai FROM ngach ORDER BY ten_chuan").fetchall()
    except Exception:  # noqa: BLE001
        return []
    finally:
        conn.close()
    bo = _bo_can_geo()
    return [{"ma": r["ma"], "ten": r["ten_chuan"],
             "trang_thai": r["trang_thai"] or "",
             "can_dia_danh": bool({(r["ma"] or "").upper(),
                                   (r["ten_chuan"] or "").upper()} & bo)}
            for r in rows]


def _tim(x: str) -> dict | None:
    """Tra một ngách theo MÃ hoặc TÊN (không phân biệt hoa/thường)."""
    k = (x or "").strip().upper()
    if not k:
        return None
    for n in liet_ke():
        if k in (n["ma"].upper(), n["ten"].upper()):
            return n
    return None


def hop_le(x: str) -> bool:
    """Ngách này có THẬT trong danh bạ không?

    Rỗng -> False. Không đọc được sổ -> True: không có cơ sở để bác, mà chặn
    thì CRM tắt là cả team đứng việc.
    """
    if not (x or "").strip():
        return False
    if _tim(x) is not None:
        return True
    return not doc_duoc()


def can_dia_danh(x: str) -> bool:
    """Ngách này có bắt buộc khai địa danh không?

    Không tra ra (bỏ trống, gõ tay, hoặc sổ hỏng) -> True: giữ luật cũ. Đang mù
    mà nới lỏng là mở lại bẫy stock lệch vùng.
    """
    n = _tim(x)
    return True if n is None else bool(n["can_dia_danh"])
