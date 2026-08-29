"""C3 — so màu NỘI BỘ chương, CHỈ CẢNH BÁO (C đợt 1, MO_TA_VAN_HANH_C_DOT_1.md §C3).

Foundation b1 §4: 1 footage lệch màu giết cả đoạn — lỗi là LỆCH TƯƠNG ĐỐI so với
xung quanh, không phải footage "xấu". Đo màu mọi footage ĐÃ CHỌN (PIL/ffmpeg thuần,
0 token) rồi so với TRUNG VỊ chương; lệch nổi bật -> dòng warning cho editor soi.

KHÔNG trừ điểm, KHÔNG veto, KHÔNG đổi pick (filter-overload-guard: không đẻ cửa loại).
Đường lên quyền trừ điểm để C đợt 5 (C2b/C5) sau khi video kiểm cho số ngưỡng thật.
"""

from __future__ import annotations

import colorsys
import math
from pathlib import Path

# Ngưỡng cảnh báo (warning-only — video kiểm tinh chỉnh dần). 2 điều kiện ĐỒNG THỜI:
# (1) lệch tuyệt đối đủ lớn; (2) lệch bất thường SO VỚI ĐỘ TẢN TỰ NHIÊN của chương
# (robust z theo MAD). Đo thật V123 (110 footage space): chỉ ngưỡng tuyệt đối -> 53
# cảnh báo oan vì space vốn xen kẽ cảnh xám (bề mặt trăng) và render rực (tinh vân);
# MAD encode đúng b1 "lệch TƯƠNG ĐỐI so với xung quanh" — chương đa dạng tự nhiên thì
# im, chương đồng nhất mà 1 clip bật hẳn thì bắn đúng nó.
DV_WARN = 0.25        # lệch độ sáng so trung vị chương
DS_WARN = 0.30        # lệch độ bão hòa so trung vị chương
ROBUST_Z = 3.5        # |x − med| / MAD — cutoff outlier robust kinh điển
MAD_FLOOR = 0.02      # chặn MAD~0 ở chương siêu đồng nhất (chia 0 / nhạy quá đà)
HUE_WARN_DEG = 60.0   # lệch tông màu (chỉ xét khi footage LẪN nền chương đủ màu)
MIN_COLORED_SAT = 0.25   # "đủ màu" — hue của màu xám gần như nhiễu
MIN_CHAPTER_ITEMS = 3    # chương < 3 footage đo được -> không đủ "xung quanh" để so
MIN_HUE_CONCENTRATION = 0.5  # chương không có tông chủ đạo (vector hue tản mác) -> bỏ xét hue


def _hue_sat_of(hexcolor: str) -> tuple[float, float]:
    """(hue độ 0-360, saturation 0-1) của màu '#rrggbb' — sat làm cổng tin-hue."""
    r, g, b = (int(hexcolor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, s, _ = colorsys.rgb_to_hsv(r, g, b)
    return h * 360.0, s


def _hue_dist(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _median(vals: list[float]) -> float:
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def find_color_outliers(items: list[dict]) -> list[str]:
    """Thuần số, không I/O — mỗi item: {beat_id, chapter, label, v, s, h, hs}.

    v/s = độ sáng/bão hòa trung bình frame; h = hue màu chủ đạo; hs = saturation
    của chính màu chủ đạo (cổng tin-hue). Trả list dòng cảnh báo tiếng Việt.
    """
    warns: list[str] = []
    chapters = sorted({it["chapter"] for it in items})
    for ch in chapters:
        group = [it for it in items if it["chapter"] == ch]
        if len(group) < MIN_CHAPTER_ITEMS:
            continue
        med_v = _median([it["v"] for it in group])
        med_s = _median([it["s"] for it in group])
        mad_v = max(_median([abs(it["v"] - med_v) for it in group]), MAD_FLOOR)
        mad_s = max(_median([abs(it["s"] - med_s) for it in group]), MAD_FLOOR)
        colored = [it for it in group if it["hs"] >= MIN_COLORED_SAT]

        def _hue_ref_excluding(item) -> float | None:
            """Tông chủ đạo từ các footage đủ màu KHÁC (leave-one-out) — outlier
            không tự kéo tụt độ tập trung tông để thoát cảnh báo."""
            others = [o for o in colored if o is not item]
            if len(others) < MIN_CHAPTER_ITEMS - 1:
                return None
            x = sum(math.cos(math.radians(o["h"])) for o in others)
            y = sum(math.sin(math.radians(o["h"])) for o in others)
            if math.hypot(x, y) / len(others) < MIN_HUE_CONCENTRATION:
                return None  # chương không có tông chủ đạo -> không xét hue
            return math.degrees(math.atan2(y, x)) % 360.0

        for it in group:
            reasons = []
            dv = it["v"] - med_v
            if abs(dv) >= DV_WARN and abs(dv) / mad_v >= ROBUST_Z:
                reasons.append(f"{'sáng' if dv > 0 else 'tối'} hơn hẳn chương "
                               f"({it['v']:.2f}, trung vị {med_v:.2f})")
            ds = it["s"] - med_s
            if abs(ds) >= DS_WARN and abs(ds) / mad_s >= ROBUST_Z:
                reasons.append(f"màu {'rực' if ds > 0 else 'xám'} hơn hẳn chương "
                               f"({it['s']:.2f}, trung vị {med_s:.2f})")
            if it["hs"] >= MIN_COLORED_SAT:
                hue_ref = _hue_ref_excluding(it)
                if hue_ref is not None and _hue_dist(it["h"], hue_ref) >= HUE_WARN_DEG:
                    reasons.append(f"lệch tông màu chương ({it['h']:.0f}° vs {hue_ref:.0f}°)")
            if reasons:
                warns.append(f"so màu C3 (chương {ch}): b{it['beat_id']:03d} "
                             f"{it['label']} {'; '.join(reasons)} — soi lại")
    return warns


def check_project_colors(project, record) -> None:
    """Gọi cuối run_source (SAU mọi pick) — fail-open: lỗi đo màu không giết stage.

    Đo trực tiếp file trong assets/ cho MỌI nguồn (local/viral/pexels/entity) —
    1 điều kiện đo thống nhất, không trộn số cũ trong db. Bỏ asset mình render
    (chart/PiP/info-card có status/graphic riêng, không nằm trong picks "ok").
    """
    from autoedit.library.vision import measure_colors, preview_images

    chapter_of = {b.beat_id: b.chapter for b in project.beats}
    pdir = Path(project.project_dir)
    entries: list[tuple[int, str]] = []
    for s in project.shots:
        if s.status != "ok" or not s.asset_path:
            continue
        entries.append((s.beat_id, s.asset_path))
        entries.extend((s.beat_id, ex.asset_path) for ex in s.extra_shots if ex.asset_path)
    entries.extend((bs.beat_id, bs.asset_path)
                   for bs in project.breath_shots if bs.asset_path)

    items: list[dict] = []
    skipped = 0
    for beat_id, rel in entries:
        try:
            hexc, v, sat = measure_colors(preview_images(pdir / rel))
        except Exception:
            skipped += 1  # file lạ/ffmpeg hụt frame — cảnh báo màu không đáng giết stage
            continue
        h, hs = _hue_sat_of(hexc)
        items.append({"beat_id": beat_id, "chapter": chapter_of.get(beat_id, 0),
                      "label": Path(rel).name, "v": v, "s": sat, "h": h, "hs": hs})

    warns = find_color_outliers(items)
    record.warnings.extend(warns)
    n_ch = len({it["chapter"] for it in items})
    skip_note = f" · đo hụt {skipped}" if skipped else ""
    record.warnings.append(
        f"so màu C3: đo {len(items)} footage / {n_ch} chương — {len(warns)} cảnh báo{skip_note}")
