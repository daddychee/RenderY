r"""Giao GIẤY TỜ + LỐI MỞ vào thư mục tập trên NAS (user chốt 09/09/2026).

Hải bấm Export, draft RA THẬT — nhưng ở kho draft CapCut
(`...\Tool Edit\Capcut Draft\CapCut Drafts\OFF_<chương>`), còn thư mục tập
`...\LI106_Hai\RenderY\Compose Timeline\<chương>\` thì **rỗng hết 14 thư mục**.

Không phải hiểu nhầm: chính `DOC_TRUOC.txt` nằm trong đó hứa *"Copy cả thư mục
này về máy… mỗi chương có draft/, footage/, report.html, nguon_footage.txt"*.
Đường Offline không giao gì vào đó, nên tờ hướng dẫn hứa một đằng thực tế một nẻo.

**KHÔNG chép draft sang** (user chốt): đo trên LI106, 10 draft = **992MB**.
Chép sang là nhân đôi mỗi tập, và đẻ ra HAI bản có thể lệch nhau sau khi ai đó
sửa một bản. Chỉ giao thứ nhẹ và không trùng lặp:

  nguon_footage.txt / .json  — sổ nguồn gốc, thứ cần khi đối chiếu bản quyền
  GIAY_PHEP.txt              — chứng từ Envato (nếu có)
  MO_DRAFT.txt               — chỉ rõ mở draft NÀO trong CapCut

Fail-open: giao là thứ đi kèm. Hỏng thì mất giấy tờ, KHÔNG được mất draft đã
dựng xong — nên hàm trả `None` chứ không ném.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from autoedit.duong_dan import nhan_chuong_tu_script

TEN_LOI_MO = "MO_DRAFT.txt"
GIAY_TO = ("nguon_footage.txt", "nguon_footage.json", "GIAY_PHEP.txt")


def _script_goc(project_dir: Path) -> str:
    try:
        d = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return ""
    return (d.get("inputs") or {}).get("original_script_path") or ""


def _thu_muc_giao(goc_script: str, ten_chuong: str) -> Path | None:
    """`...\\LI106_Hai\\RenderY\\C9.txt` -> `...\\RenderY\\Compose Timeline\\C9`."""
    if not goc_script or not ten_chuong:
        return None
    p = Path(goc_script.replace("\\", "/"))
    for cha in p.parents:
        if cha.name.lower() == "rendery":
            return cha / "Compose Timeline" / ten_chuong
    return None


def giao_giay_to(project_dir: Path, draft_dir: Path) -> Path | None:
    """Chép giấy tờ + ghi lối mở vào thư mục chương. Trả thư mục đã giao, hoặc None."""
    try:
        project_dir, draft_dir = Path(project_dir), Path(draft_dir)
        goc = _script_goc(project_dir)
        ten = nhan_chuong_tu_script(goc)
        dich = _thu_muc_giao(goc, ten)
        if dich is None:
            return None
        dich.mkdir(parents=True, exist_ok=True)
        for f in GIAY_TO:
            nguon = draft_dir / f
            if nguon.is_file():
                shutil.copy2(nguon, dich / f)
        (dich / TEN_LOI_MO).write_text(
            f"CHƯƠNG {ten} — draft CapCut đã dựng xong\n"
            f"Xong lúc: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"MỞ Ở ĐÂU\n"
            f"  Tên draft : {draft_dir.name}\n"
            f"  Đường dẫn : {draft_dir}\n\n"
            f"  Mở CapCut là thấy draft tên «{draft_dir.name}» trong danh sách.\n"
            f"  KHÔNG chép draft về đây: nó nặng (một chương ~50-170MB) và chép\n"
            f"  sang là có hai bản, sửa một bản thì bản kia lệch.\n\n"
            f"GIẤY TỜ KÈM THEO\n"
            f"  nguon_footage.txt  — nguồn gốc từng clip (đối chiếu bản quyền)\n"
            f"  GIAY_PHEP.txt      — chứng từ Envato, nếu chương này có dùng\n",
            encoding="utf-8")
        return dich
    except Exception:  # noqa: BLE001 — mất giấy tờ chứ không được mất draft
        return None
