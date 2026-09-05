r"""KHAI QUẬT kho cũ — quét projects/ đã dựng, ghi vào Sổ Tra MỘT LẦN.

Kỳ vọng đã hiệu chỉnh qua phản biện (06/09): đây KHÔNG phải kho vàng —
98% ứng viên thua phễu thua rõ rệt, và "thắng phễu" chưa qua vòng phản biện
nào. Giá trị thật: (a) catalog 3.9k clip đang nằm sẵn trên đĩa trước khi bị
dọn; (b) sự kiện `len_final` từ shots — clip nào từng LÊN TIMELINE tập nào
(nhãn "đã dùng" chống lặp giữa tập); (c) nền cho vòng phản biện cắm điểm sau.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from autoedit.sotra import db as sdb
from autoedit.sotra.tag7 import tag_tu_tieu_de


def _ten_tap(p: dict) -> str:
    """Suy mã tập (LI100...) từ đường dẫn script gốc — không có thì id project."""
    goc = (p.get("inputs") or {}).get("original_script_path") or ""
    m = re.search(r"(?:^|[\\/])([A-Z]{2,4}\d{2,4})(?:_[\w-]+)?(?:[\\/])", goc)
    return m.group(1) if m else (p.get("project_id") or "")


def khai_quat(conn, projects_dir: Path, log=None) -> dict:
    """Quét mọi project.json: assets trên đĩa -> clip nguồn 'kho'; shots -> su_kien."""
    def ghi(m):
        if log:
            log(m)

    kq = {"clip_moi": 0, "su_kien": 0, "project": 0}
    for f in sorted(Path(projects_dir).glob("*/project.json")):
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        pdir = f.parent
        tap = _ten_tap(p)
        assets = {a.name: a for a in (pdir / "assets").glob("*.*")} if (pdir / "assets").is_dir() else {}
        if not assets:
            continue
        kq["project"] += 1
        # 1) mọi file asset -> 1 dòng clip nguồn 'kho' (tag từ slug tên file)
        for ten, duong in assets.items():
            # b012_vietnam-beach-sunset_ab12cd.mp4 -> "vietnam beach sunset"
            m = re.match(r"b\d{3}_(.+?)(?:_[0-9a-f]{6})?\.\w+$", ten)
            mo_ta = (m.group(1) if m else duong.stem).replace("-", " ")
            r = {"id": sdb.lam_id("kho", f"{pdir.name}:{ten}"), "nguon": "kho",
                 "tieu_de": mo_ta, "path_local": str(duong), "tap": tap,
                 **tag_tu_tieu_de(mo_ta)}
            kq["clip_moi"] += sdb.them_clip(conn, r)
        # 2) shots -> sự kiện LÊN FINAL (đã lên timeline thật của tập đó)
        for s in p.get("shots") or []:
            ap = s.get("asset_path") or ""
            ten = Path(ap).name if ap else ""
            if ten not in assets:
                continue
            cid = sdb.lam_id("kho", f"{pdir.name}:{ten}")
            sdb.ghi_su_kien(conn, cid, "len_final", tap=tap,
                            chi_tiet=f"beat {s.get('beat_id')} · {s.get('source', '')}")
            kq["su_kien"] += 1
        conn.commit()
        ghi(f"sotra: khai quật {pdir.name} ({tap}): {len(assets)} asset")
    return kq
