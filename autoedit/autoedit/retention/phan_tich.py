r"""Phân tích đường retention tập CŨ -> điều chỉnh hồ sơ nhịp tập MỚI.

Phase 1 chỉ làm mức ĐO ĐƯỢC + luật bảo thủ (không hứa AI hiểu nội dung):

  giu_30s      — còn bao nhiêu % khán giả sau 30 giây (chất lượng hook).
  decay_pm     — thân video mất bao nhiêu ĐIỂM %/phút (60s -> 90% thời lượng).
  diem_tut     — các mốc tụt CỤC BỘ mạnh bất thường (>= 1.8x median + >= 1.5 điểm
                 trong 30s) — báo vị trí cho editor soát nội dung, KHÔNG tự sửa.

Luật điều chỉnh hồ sơ (áp trong cutter, trước lap_ke_hoach):
  giu_30s < 0.55          -> hook_kieu = "no" (nổ — đánh dày ngay giây đầu)
  decay_pm > 2.5 điểm/phút -> bung_chu_ky_s x0.75 (sàn 180s) — bùng dày hơn

Số liệu + báo cáo ghi retention.json tại FOLDER TẬP (server ghi lúc nộp job,
mọi chương của tập cùng đọc). Không có file -> [] , nhịp chạy như cũ.
"""

from __future__ import annotations

import json
from pathlib import Path

TEN_FILE = "retention.json"
NGUONG_HOOK_YEU = 0.55       # giữ <55% sau 30s = hook thua benchmark faceless
NGUONG_DECAY_CAO = 2.5       # điểm %/phút
SAN_CHU_KY_S = 180.0


def phan_tich(duong_cong: list[tuple[float, float]], dai_s: float) -> dict:
    """[(x_frac, pct)] + thời lượng (giây) -> số liệu + đề xuất điều chỉnh."""
    if dai_s <= 60:
        raise ValueError("thời lượng tập cũ phải > 60s")
    ts = [x * dai_s for x, _ in duong_cong]
    ps = [p for _, p in duong_cong]

    def tai(t: float) -> float:
        for i in range(1, len(ts)):
            if ts[i] >= t:
                w = (t - ts[i - 1]) / max(1e-9, ts[i] - ts[i - 1])
                return ps[i - 1] + w * (ps[i] - ps[i - 1])
        return ps[-1]

    giu_30s = tai(30.0)
    t_a, t_b = 60.0, dai_s * 0.9
    decay_pm = max(0.0, (tai(t_a) - tai(t_b)) * 100 / max(1e-9, (t_b - t_a) / 60))

    # tụt cục bộ: độ mất trong cửa sổ 30s tại từng mốc (sau hook)
    tut: list[tuple[float, float]] = []       # (t, mất điểm %)
    mat = [(t, (tai(t) - tai(t + 30)) * 100)
           for t in range(60, int(dai_s) - 30, 15)]
    if mat:
        cac_mat = sorted(m for _, m in mat)
        median = cac_mat[len(cac_mat) // 2]
        for t, m in mat:
            if m >= max(1.5, median * 1.8):
                if tut and t - tut[-1][0] < 45:   # gom mốc dính nhau, giữ mốc mạnh
                    if m > tut[-1][1]:
                        tut[-1] = (float(t), m)
                else:
                    tut.append((float(t), m))
    tut = sorted(tut, key=lambda x: -x[1])[:3]

    dieu_chinh: dict = {}
    bao_cao = [f"retention tập cũ: sau 30s giữ {giu_30s:.0%} · thân mất "
               f"{decay_pm:.1f} điểm%/phút · cuối còn {ps[-1]:.0%}"]
    if giu_30s < NGUONG_HOOK_YEU:
        dieu_chinh["hook_kieu"] = "no"
        bao_cao.append(f"hook giữ {giu_30s:.0%} < {NGUONG_HOOK_YEU:.0%} -> tập này "
                       "ép hook kiểu NỔ (đánh dày ngay giây đầu)")
    if decay_pm > NGUONG_DECAY_CAO:
        dieu_chinh["bung_he_so_chu_ky"] = 0.75
        bao_cao.append(f"thân mất {decay_pm:.1f} điểm%/phút > {NGUONG_DECAY_CAO} "
                       "-> rút chu kỳ bùng còn 75% (bùng dày hơn giữ chân)")
    for t, m in sorted(tut):
        bao_cao.append(f"⚠ tụt mạnh quanh {int(t) // 60}:{int(t) % 60:02d} "
                       f"(-{m:.1f} điểm trong 30s) — soát nội dung đoạn tương ứng")
    return {"dai_s": dai_s, "giu_30s": round(giu_30s, 3),
            "decay_pm": round(decay_pm, 2), "cuoi": round(ps[-1], 3),
            "diem_tut": [[round(t, 1), round(m, 1)] for t, m in sorted(tut)],
            "dieu_chinh": dieu_chinh, "bao_cao": bao_cao}


def phan_tich_anh(anh: Path, dai_s: float,
                 tooltip_giay: list[tuple[float, float]] | None = None) -> dict:
    """Ảnh chụp + thời lượng -> kết quả phan_tich (tiện cho server gọi 1 phát).

    tooltip_giay: [(giây, giá_trị_%)] editor đọc trực tiếp trên YouTube Studio
    (di chuột qua đường cong) — dùng khi OCR không đọc được nhãn trục (ảnh
    thiếu/crop mất nhãn). Quy đổi giây -> x_frac bằng dai_s rồi giao cho
    doc_duong_cong (đơn vị %/x_frac y hệt cách OCR neo bằng nhãn trục)."""
    from autoedit.retention.doc_anh import doc_duong_cong

    tooltip = ([(g / dai_s, p) for g, p in tooltip_giay] if tooltip_giay else None)
    return phan_tich(doc_duong_cong(Path(anh), tooltip=tooltip), dai_s)


def ap_vao_ho_so(project, hs) -> list[str]:
    """Đọc retention.json ở FOLDER TẬP (cha của folder chương) -> chỉnh hs tại chỗ.

    Fail-open: không file / file hỏng -> [] hoặc 1 dòng cảnh báo, nhịp chạy như cũ.
    """
    try:
        goc = Path(project.inputs.original_script_path).parent.parent
        f = goc / TEN_FILE
        if not f.is_file():
            return []
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"retention: bỏ qua ({exc})"]
    dc = d.get("dieu_chinh") or {}
    ra = [f"retention (tập cũ {int(d.get('dai_s', 0)) // 60} phút): áp vào nhịp"]
    if dc.get("hook_kieu"):
        hs.hook_kieu = dc["hook_kieu"]
    if dc.get("bung_he_so_chu_ky"):
        hs.bung_chu_ky_s = max(SAN_CHU_KY_S, hs.bung_chu_ky_s * dc["bung_he_so_chu_ky"])
    ra += [ln for ln in d.get("bao_cao", [])[1:]]     # dòng 1 là tổng quan, khỏi lặp
    return ra if (dc or len(ra) > 1) else []
