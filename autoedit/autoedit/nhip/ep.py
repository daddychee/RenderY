r"""ÉP phân bố độ dài shot theo hồ sơ nhịp — tầng dang dở từ 14/07 nay đóng lại.

Lịch sử: tempo map Tầng 1 (LLM khai `tempo_curve`) + Tầng 2 (`check_tempo_map`
CẢNH BÁO) code 14/07 thời padoma — nhưng không ai ÉP, nên LLM khai `fast_settle`
rồi vẫn chia đều: đo 02/09 hai chương CÙNG TẬP ra nhịp cụm 6,5× và 2,3× (chênh
gấp ba, ngẫu nhiên). File này là tầng ép.

ĐÒN BẨY: `beat.shot_count` — đọc mã trước khi chọn (Karpathy):
  - sourcer `_shot_count_target` = min(shot_count, floor(dur/MIN_SHOT_DUR=0.7))
  - assembler `split_window` chia beat thành N khoảng ĐỀU, khoảng cuối phủ ô thở
  → đặt shot_count = round(thoại/target) là ra độ dài shot mong muốn, KHÔNG cần
  gọi lại LLM, không chia lại beat, pool mỏng thì assembler tự xuống cấp mềm
  (đặt được bao nhiêu clip chia bấy nhiêu khoảng).

VAI TRÒ THEO QUY ƯỚC THƯ MỤC (H/C/E — user chốt 30/08): title project = tên
thư mục chương, nên "H" → hồ sơ hook, "E" → có bùng kết, còn lại → thân.
Chu kỳ bùng ~4 phút ≈ độ dài một chương → MỖI chương thân MỘT đợt bùng, đặt ở
MỞ chương (đo thật: đợt bùng hay trùng điểm chuyển ý; mở chương = điểm chuyển
trong video ghép).

LUẬT GIỮ NGUYÊN (không giẫm lên):
  - d2: beat có ô thở (breathing_after>0) = 1 HÌNH GIỮ → shot_count=1, không chia
  - MIN_SHOT_DUR=0.7 của sourcer vẫn là sàn cứng

BÀI HỌC BAN_GIAO_M4 (21/07, "3 lần script báo đúng — 3 lần user mở CapCut bác"):
file này chỉ LẬP KẾ HOẠCH và DỰ BÁO; nó không tự tuyên bố video "đúng nhịp" —
cổng cuối là mắt/tai user trên draft thật.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from autoedit.nhip.profile import HoSoNhip

MIN_SHOT_DUR = 0.7          # khớp sourcer/packager.coverage — sàn cứng của máy
TY_LE_MO_CHUONG = 0.15      # 15% thời lượng đầu chương thân = vùng bùng
TY_LE_KET = 0.20            # 20% cuối chương E = vùng bùng kết


def vai_tro_chuong(title: str) -> str:
    """'H' → hook · 'E' → ket · còn lại → than (quy ước thư mục H/C1../E)."""
    t = (title or "").strip().upper()
    if t == "H":
        return "hook"
    if t == "E":
        return "ket"
    return "than"


@dataclass
class KeHoachNhip:
    """Kế hoạch shot_count per-beat + dự báo phân bố để đối chiếu hồ sơ."""

    shot_count: dict[int, int] = field(default_factory=dict)
    bung_beat_ids: list[int] = field(default_factory=list)
    du_bao_trung_vi: float = 0.0
    du_bao_ty_le_nhanh: float = 0.0
    du_bao_ty_le_hold: float = 0.0
    canh_bao: list[str] = field(default_factory=list)


def _thoai(b) -> float:
    """Độ dài THOẠI của beat trên timeline (timeline_end KHÔNG gồm ô thở —
    map_beats_to_timeline trả b.end+offset, ô thở nằm sau)."""
    ts = getattr(b, "timeline_start", None)
    te = getattr(b, "timeline_end", None)
    if ts is not None and te is not None and te > ts:
        return te - ts
    return max(float(getattr(b, "end", 0)) - float(getattr(b, "start", 0)), 0.0)


def _muc_tieu_hook(hs: HoSoNhip, vi_tri: float) -> float:
    """Độ dài shot đích trong HOOK theo vị trí tương đối [0..1].

    Số từ đo thật 03/09:
      'no'  — Fern info: nổ ngay rồi THẢ SÂU (57→5 cắt/phút sau phút 4):
              2/3 đầu dày đặc, đuôi giãn ×1.6 cho người xem hạ cánh.
      'leo' — Fern điều tra (Hansa 9→19→29, đỉnh ~2:45): thưa → dày dần,
              đỉnh ở CUỐI hook.
      'em'  — WUFO: không nổ, dùng luôn nhịp thân.
    """
    if hs.hook_kieu == "no":
        return hs.hook_trung_vi * (1.6 if vi_tri > 0.66 else 1.0)
    if hs.hook_kieu == "leo":
        return hs.hook_trung_vi * (2.0 - vi_tri)      # 2.0x → 1.0x
    return hs.than_trung_vi


def lap_ke_hoach(beats: list, hs: HoSoNhip, title: str = "") -> KeHoachNhip:
    """Tính shot_count cho từng beat theo hồ sơ. THUẦN — không sửa beat nào."""
    kh = KeHoachNhip()
    if not beats:
        return kh
    vai = vai_tro_chuong(title)
    tong = sum(_thoai(b) for b in beats)
    if tong <= 0:
        kh.canh_bao.append("nhịp: beat chưa có timeline — bỏ qua ép")
        return kh

    du_bao: list[float] = []
    dau, cuoi = 0.0, 0.0
    for b in beats:
        d = _thoai(b)
        dau, cuoi = cuoi, cuoi + d
        vi_tri = (dau + d / 2) / tong

        # d2: ô thở = 1 hình giữ — KHÔNG chia, đây cũng chính là nguồn hold tự nhiên
        if float(getattr(b, "breathing_after", 0) or 0) > 0:
            kh.shot_count[b.beat_id] = 1
            du_bao.append(d + float(b.breathing_after))
            continue

        if vai == "hook":
            muc_tieu = _muc_tieu_hook(hs, vi_tri)
        elif vai == "ket" and hs.bung_ket and vi_tri >= 1 - TY_LE_KET:
            muc_tieu = hs.than_trung_vi / hs.bung_he_so     # bùng kết
            kh.bung_beat_ids.append(b.beat_id)
        elif vai != "hook" and vi_tri <= TY_LE_MO_CHUONG:
            muc_tieu = hs.than_trung_vi / hs.bung_he_so     # bùng mở chương
            kh.bung_beat_ids.append(b.beat_id)
        else:
            muc_tieu = hs.than_trung_vi

        n = max(1, round(d / max(muc_tieu, MIN_SHOT_DUR)))
        n = min(n, int(d / MIN_SHOT_DUR) or 1)              # sàn cứng của máy
        kh.shot_count[b.beat_id] = n
        du_bao.extend([d / n] * n)

    # ---- Dự báo để đối chiếu hồ sơ (chỉ MÔ TẢ — cổng cuối là mắt user) ----
    if du_bao:
        kh.du_bao_trung_vi = round(statistics.median(du_bao), 2)
        kh.du_bao_ty_le_nhanh = round(sum(1 for x in du_bao if x <= 2.0) / len(du_bao), 2)
        kh.du_bao_ty_le_hold = round(sum(1 for x in du_bao if x >= 5.0) / len(du_bao), 2)
        dich_tv = hs.hook_trung_vi if vai == "hook" else hs.than_trung_vi
        if kh.du_bao_trung_vi > dich_tv * 1.5:
            kh.canh_bao.append(
                f"nhịp: trung vị dự báo {kh.du_bao_trung_vi}s > đích {dich_tv}s ×1.5 "
                f"— beat quá dài so với hồ sơ, cân nhắc để LLM chia beat nhỏ hơn")
        dich_hold = hs.than_ty_le_hold if vai != "hook" else 0.1
        if kh.du_bao_ty_le_hold > dich_hold + 0.25:
            kh.canh_bao.append(
                f"nhịp: hold dự báo {kh.du_bao_ty_le_hold:.0%} vượt xa đích "
                f"{dich_hold:.0%} — nhiều ô thở/beat dài liên tiếp")
    return kh


def ap_dung(project, hs: HoSoNhip) -> list[str]:
    """Ghi kế hoạch vào project.beats (shot_count). Trả cảnh báo để cut ghi sổ.

    Chỉ NÂNG shot_count, không hạ dưới đề xuất LLM khi LLM muốn nhiều hơn — LLM
    đã đọc nội dung, biết beat nào cần montage; hồ sơ chỉ đảm bảo SÀN mật độ.
    Ngoại lệ: beat ô thở ép về 1 (luật d2 thắng mọi đề xuất).
    """
    kh = lap_ke_hoach(project.beats, hs, title=getattr(project, "title", ""))
    for b in project.beats:
        muon = kh.shot_count.get(b.beat_id)
        if muon is None:
            continue
        if float(getattr(b, "breathing_after", 0) or 0) > 0:
            b.shot_count = 1
        else:
            b.shot_count = max(int(getattr(b, "shot_count", 1) or 1), muon)
    ra = list(kh.canh_bao)
    ra.append(
        f"nhịp[{hs.ten}/{vai_tro_chuong(getattr(project, 'title', ''))}]: "
        f"dự báo trung vị {kh.du_bao_trung_vi}s · ≤2s {kh.du_bao_ty_le_nhanh:.0%} "
        f"· ≥5s {kh.du_bao_ty_le_hold:.0%} · {len(kh.bung_beat_ids)} beat bùng")
    return ra
