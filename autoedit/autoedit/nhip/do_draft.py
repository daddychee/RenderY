r"""ĐO LẠI SAU DỰNG — draft vừa ráp xong tự chấm nhịp của chính nó.

Bối cảnh (user duyệt 05/09, sau audit 3 video 04/09): ép nhịp DỰ BÁO trên kế
hoạch shot_count nhưng draft thật lệch ~50% (LI098 dự báo 1.02s/96% ≤2s, đo
thật 1.53s/75% — assembler kẹp sàn 0.7s, clip nguồn ngắn giữ nguyên + kéo
slow-mo). Tệ hơn: LI095 ép nhịp CHẾT im lặng (bug frozen) mà không ai biết vì
"dự báo" in ra không ai kiểm lại — hook 6.26s/1% thay vì 1.0s/70%.

Thước này khép vòng: assemble xong đọc NGAY draft_content.json (số tuyệt đối,
không cần render/ffmpeg) → so với hồ sơ nhịp hiệu lực → in một dòng chênh lệch
vào warnings. Chênh to = có tầng nào đó chết/kẹp — thấy liền, không đợi 1 ngày
sau mở CapCut mới biết (đúng tinh thần BAN_GIAO_M4: số không thay được mắt
người, nhưng số LỆCH TO thì báo được máy hỏng).
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

NHANH_S = 2.0    # cùng mốc nhip/do.py
HOLD_S = 5.0


def do_nhip_draft(draft_dir: Path) -> dict:
    """Đọc draft_content.json -> {so_shot, trung_vi, ty_le_nhanh, ty_le_hold}.

    Đo track video NỀN (track video đầu tiên có segment — đúng track mà
    render_xemthu/nhip vẫn dùng). Ném lỗi nếu draft thiếu/rỗng — caller fail-open.
    """
    f = Path(draft_dir) / "draft_content.json"
    c = json.loads(f.read_text(encoding="utf-8"))
    nen = next(t for t in c["tracks"] if t["type"] == "video" and t["segments"])
    durs = [s["target_timerange"]["duration"] / 1e6 for s in nen["segments"]]
    if not durs:
        raise ValueError("track nền không có segment nào")
    return {
        "so_shot": len(durs),
        "trung_vi": round(statistics.median(durs), 2),
        "ty_le_nhanh": round(sum(1 for x in durs if x <= NHANH_S) / len(durs), 3),
        "ty_le_hold": round(sum(1 for x in durs if x >= HOLD_S) / len(durs), 3),
    }


def doi_chieu_hs(project, tk: dict) -> str:
    """1 dòng warning: nhịp ĐO THẬT vs ĐÍCH hồ sơ hiệu lực — kèm mức chênh."""
    from autoedit.nhip.ep import vai_tro_chuong
    from autoedit.nhip.hieu_luc import nap_hieu_luc

    hs, _ = nap_hieu_luc(project)
    vai = vai_tro_chuong(getattr(project, "title", ""))
    if vai == "hook":
        dich_tv, dich_nhanh = hs.hook_trung_vi, hs.hook_ty_le_nhanh
    else:
        dich_tv, dich_nhanh = hs.than_trung_vi, hs.than_ty_le_nhanh
    chenh = (tk["trung_vi"] - dich_tv) / dich_tv if dich_tv > 0 else 0.0
    dong = (f"ĐO LẠI SAU DỰNG [{vai}]: {tk['so_shot']} shot · trung vị "
            f"{tk['trung_vi']}s (đích {dich_tv}s, chênh {chenh:+.0%}) · "
            f"≤2s {tk['ty_le_nhanh']:.0%} (đích {dich_nhanh:.0%}) · "
            f"≥5s {tk['ty_le_hold']:.0%}")
    # Ngưỡng réo: đo thật 05/09 trên draft khỏe (LI098) trung vị vẫn cao hơn
    # đích ~50% MỘT CÁCH HỆ THỐNG (assembler kẹp sàn 0.7s + clip ngắn slow-mo
    # giữ nguyên shot) — réo ở 50% thì video nào cũng réo, editor nhờn cảnh
    # báo. Chỉ réo khi chênh >150% (ca chết hẳn như LI095 +526%) HOẶC tỷ lệ
    # nhanh chưa được NỬA đích (LI095: 1% vs đích 70%).
    if chenh > 1.5 or (dich_nhanh > 0 and tk["ty_le_nhanh"] < dich_nhanh / 2):
        dong += " — ⚠ LỆCH TO: kiểm ép nhịp có chạy không (xem warnings stage cut)"
    return dong
