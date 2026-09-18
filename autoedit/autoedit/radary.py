r"""Pool Radary — nguồn để dựng HỒ SƠ NGÁCH (QĐ18, user chốt 18/09/2026).

Vì sao cần: ngách mới (X FILE = `N-003`) không có cách nào khai "quay ai, quay
cái gì". Khai tay thì mỗi người gõ một kiểu — đúng thứ đã đẻ ra `Life In` và
`life-in`. Radary đã đi gom sẵn kênh + video outlier của từng ngách, nên lấy
TIÊU ĐỀ trong đó làm vốn từ cho hồ sơ là rẻ nhất: không phải nhập gì thêm.

**Sổ ở đâu:** `D:\AI AGENT OUTLIERY\data\radary\radary.db` — bảng `workspaces`
(`id`, `name`, `market`, `ngach`), `channels`, `videos`. Khai lại được ở `.env`
bằng `RENDERY_RADARY`.

**Đọc THẲNG file, chế độ CHỈ ĐỌC** — y lý lẽ QĐ12 với danh bạ CRM: không import
thư viện của app khác, và `mode=ro` thì RenderY không có đường nào ghi hỏng kho
của Radary.

**Khớp bằng MÃ.** Đo 18/09: cột `workspaces.ngach` chứa đúng mã danh bạ
(`N-003`, `N-SENIOR-HEALTH`) — không phải dò tên.

**GỘP mọi workspace cùng mã — đây là chỗ dễ sai nhất.** Một mã có nhiều
workspace theo thị trường: N-003 có ws 52 (`X FILE`, RỖNG) và ws 53
(`X FILE — US`, 36 kênh / 675 video). Cái rỗng có id NHỎ HƠN, nên ai đọc
"workspace đầu tiên của ngách" sẽ kết luận ngách này không có pool.

**Fail-open có chủ ý:** Radary tắt / ổ D chưa gắn / đổi cấu trúc bảng -> trả
rỗng kèm `doc_duoc=False`, KHÔNG ném. Một app khác chết không được kéo cả
RenderY chết theo.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DUONG_MAC_DINH = r"D:\AI AGENT OUTLIERY\data\radary\radary.db"

# Trần tiêu đề đưa cho LLM. Ngách to nhất (N-SPACE) có 10.450 video — nhồi hết
# vào prompt là vỡ cửa sổ ngữ cảnh. 2000 đủ ôm trọn ngách thường (X FILE 675)
# mà vẫn chặn được ngách khổng lồ. Trần cũ 600 cắt mất 75 tiêu đề của X FILE
# không vì lý do gì.
TRAN_TIEU_DE = 2000


def duong_radary() -> Path:
    return Path(os.getenv("RENDERY_RADARY", "").strip() or DUONG_MAC_DINH)


def _mo() -> sqlite3.Connection:
    """Kết nối CHỈ ĐỌC. `mode=ro` là rào thật: mọi lệnh ghi ném OperationalError."""
    f = duong_radary()
    if not f.is_file():
        raise FileNotFoundError(str(f))
    conn = sqlite3.connect(f"file:{f.as_posix()}?mode=ro", uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def doc_duoc() -> bool:
    """Có đọc được pool không — UI cần biết để nói rõ khi danh sách rỗng."""
    try:
        conn = _mo()
    except Exception:  # noqa: BLE001
        return False
    try:
        conn.execute("SELECT 1 FROM workspaces LIMIT 1").fetchone()
        return True
    except Exception:  # noqa: BLE001
        return False
    finally:
        conn.close()


def _lay_deu(hang, tran: int) -> list[str]:
    """Chia đều suất cho TỪNG KÊNH (vòng tròn), trong mỗi kênh giữ thứ tự tier.

    Vì sao không cắt "top N toàn cục": đo 18/09, cách đó làm LIFE IN chỉ còn
    **70/166 kênh** có mặt trong 600 tiêu đề, 5 kênh đăng dày nhất chiếm 171/600;
    SPACE mất 72/212 kênh. Vốn từ rút ra khi đó là vốn từ của mấy kênh đăng
    khoẻ nhất, không phải của ngách.
    """
    if tran <= 0:
        return []
    theo: dict[str, list[str]] = {}
    for ck, title in hang:
        theo.setdefault(ck, []).append(title)
    ra: list[str] = []
    vong = 0
    while len(ra) < tran:
        them = False
        for ds in theo.values():
            if vong < len(ds):
                ra.append(ds[vong])
                them = True
                if len(ra) >= tran:
                    break
        if not them:
            break
        vong += 1
    return ra


def pool(ma: str, tran: int = TRAN_TIEU_DE) -> dict:
    """Pool của một ngách theo MÃ — gộp mọi workspace mang mã đó.

    Trả `{"ma", "doc_duoc", "ws": [...], "kenh", "video", "tieu_de": [...]}`.
    `tran` chỉ cắt danh sách tiêu đề, KHÔNG cắt số đếm: màn hình phải nói đúng
    pool có bao nhiêu video, không phải bao nhiêu cái vừa đọc.
    """
    k = (ma or "").strip().upper()
    ra = {"ma": k, "doc_duoc": False, "ws": [], "kenh": 0, "video": 0, "tieu_de": []}
    try:
        conn = _mo()
    except Exception:  # noqa: BLE001
        return ra
    try:
        ws = conn.execute(
            "SELECT id, name, market FROM workspaces "
            "WHERE UPPER(COALESCE(ngach,'')) = ?", (k,)).fetchall()
        ra["doc_duoc"] = True
        if not k or not ws:
            return ra
        ids = [r["id"] for r in ws]
        cho = ",".join("?" * len(ids))
        ra["ws"] = [{"id": r["id"], "ten": r["name"] or "",
                     "market": r["market"] or ""} for r in ws]
        ra["kenh"] = int(conn.execute(
            f"SELECT COUNT(*) FROM channels WHERE workspace_id IN ({cho})",
            ids).fetchone()[0])
        ra["video"] = int(conn.execute(
            f"SELECT COUNT(*) FROM videos WHERE workspace_id IN ({cho})",
            ids).fetchone()[0])
        ra["tieu_de"] = _lay_deu(conn.execute(
            f"SELECT COALESCE(channel_yt_id,'') ck, title FROM videos "
            f"WHERE workspace_id IN ({cho}) AND COALESCE(title,'') <> '' "
            "ORDER BY tier DESC, pub_ts DESC", ids).fetchall(), max(0, int(tran)))
        return ra
    except Exception:  # noqa: BLE001
        # Radary đổi cấu trúc bảng -> câm lặng, không nổ giữa mặt user.
        return {**ra, "kenh": 0, "video": 0, "tieu_de": []}
    finally:
        conn.close()
