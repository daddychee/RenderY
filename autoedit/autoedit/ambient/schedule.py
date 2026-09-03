"""C1 + C đợt 3b — lập lịch ô thở, ambient khớp cảnh/CHỦ THỂ, drone nền, tiếng chủ thể
trong voice (MO_TA_VAN_HANH_C1_AMBIENT §3 + MO_TA_VAN_HANH_SFX_HOAN_THIEN §2-3).

Lịch ô thở DÙNG CHUNG `ducking.merge_voice_intervals` — 1 nguồn sự thật với F8, ambient
và nhạc-nở không bao giờ lệch nhau (rà chồng chéo §6). Tầng này chỉ ĐỌC breath_shots/
shots/beats; mù tag -> kind `default`; thiếu file -> bỏ ô (fail-open mọi nấc).
"""

from __future__ import annotations

import re
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from autoedit.ambient.library import list_variants
from autoedit.packager import ducking

# Cổng TAI V4 chốt 2026-07-10: 0.4 bị nhạc-nở nuốt -> user chốt 0dB, KHÔNG hạ ambient.
# (Số editor 0.2-0.4 ở PB10 không áp thẳng được: nhạc nền của họ chỉ 0.05-0.1.)
AMBIENT_VOL = 1.0   # 0dB — user chốt cổng tai; nghe dày thì chỉnh tầng khác, không hạ số này
AMB_MIN = 3.0       # ô ngắn hơn: fade chưa kịp nghe đã hết -> bỏ (chốt V4)
AMB_FADE = 1.0      # giây fade in/out — fade-out kết thúc ĐÚNG lúc voice vào lại (chốt V4)

# 🔸 S1 drone nền (MO_TA_SFX §3) — tai user chốt ở cổng TAI V5
DRONE_VOL = 0.15     # quy TƯƠNG QUAN PB10 (drone editor ≈ nhạc nền họ), KHÔNG bê số tuyệt đối
# 🔸 Deepsea: bed "ục ục dưới nước" — theo SHEET editor CHỈ đặt trên CẢNH DƯỚI NƯỚC,
# KHÔNG loop cả bài (user sửa nhận định 2026-07-13; đo 23 draft xác nhận: 383 đoạn,
# median 40s/đoạn, gap thật 4s-630s tại cảnh mặt biển/bản đồ). Vol 0.32-0.56 của họ
# ≈ ngang SFX-voiced 0.5 -> quy tương quan 0.25. Chờ cổng tai video kiểm.
DRONE_VOL_BY_NICHE: dict[str, float] = {"deepsea": 0.25}
DRONE_SCENE_BY_NICHE: dict[str, tuple[str, ...]] = {"deepsea": ("underwater",)}
BED_MIN = 6.0        # run bed ngắn nhất — editor hiếm khi đặt đoạn <7s (đo 2026-07-13)
DRONE_FADE_IN = 2.0
DRONE_FADE_OUT = 3.0
SEAM_FADE = 0.3      # mép nối khi loop file drone — chống click


def drone_vol(niche: str | None) -> float:
    return DRONE_VOL_BY_NICHE.get(niche or "", DRONE_VOL)


def drone_scenes(niche: str | None) -> tuple[str, ...]:
    """Niche có gate cảnh -> bed chỉ đặt trên các scene_type này; () = loop cả bài."""
    return DRONE_SCENE_BY_NICHE.get(niche or "", ())


def bed_intervals(project, scene_lookup: Callable[[str], str],
                  scenes: tuple[str, ...]) -> list[tuple[float, float]]:
    """Các khoảng timeline đang chiếu cảnh thuộc `scenes` — bed S1 chỉ đặt ở đây.

    Đơn vị = BEAT trọn (voice + thở sau nó, tới timeline_start beat kế): shot thở 3.0
    LIÊN TỤC CHỦ THỂ clip liền trước nên cảnh trong ô thở ≈ cảnh pick. Beat liền nhau
    cùng cảnh gộp 1 run; run < BED_MIN bỏ (editor không đặt đoạn quá ngắn). Beat mù
    tag/graphic/thiếu timeline -> không bed (fail-open từng beat)."""
    picks = {p.beat_id: p for p in project.shots}
    beats = sorted((b for b in project.beats if b.timeline_start is not None),
                   key=lambda b: b.timeline_start)
    if not beats or not project.segments:
        return []
    last = project.segments[-1]
    total_end = last.timeline_end + last.breathing_after
    ivals = []
    for b, nxt in zip(beats, list(beats[1:]) + [None]):
        p = picks.get(b.beat_id)
        if p is None or not p.asset_key:
            continue
        if scene_lookup(p.asset_key) in scenes:
            ivals.append((b.timeline_start, nxt.timeline_start if nxt else total_end))
    merged: list[list[float]] = []
    for s, e in ivals:
        if merged and s - merged[-1][1] <= 0.05:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged if e - s >= BED_MIN]

# S2 tiếng chủ thể — volume theo NGỮ CẢNH VOICE. Ambient LOẠI CẢNH trong ô thở vẫn
# AMBIENT_VOL 0dB (verdict V4 riêng — pad dài dễ bị nhạc-nở 0.5 nuốt, khác tiếng chủ thể
# giàu transient).
#
# 📌 USER CHỐT 2026-07-18 (sau cổng TAI RD-89 V10): NÂNG -15/-10dB -> -8/-5dB. Nâng CẢ
# HAI mức, GIỮ NGUYÊN khoảng cách 3dB giữa chúng — nếu chỉ nâng mức trong-voice lên -8dB
# thì nó VƯỢT mức khoảng-thở (0.40 > 0.32), thành ra SFX đè voice to hơn lúc không có
# voice: ngược logic, giọng đọc bị lấn.
# 📌 LỆCH SO VỚI BẢN GỐC: số cũ -15/-10dB do user đặt 2026-07-10 và PB13 đo 3 draft editor
# XÁC NHẬN (SFX đè voice median -11..-15.6dB, SFX khoảng nghỉ -10..-11.6dB —
# scripts_phan_tich_pb13_sfx_vol_voice.py). Số mới CAO HƠN editor thật ~7dB: đây là TAI
# USER đè số đo (cùng tiền lệ DS5-083 "số đo editor = điểm xuất phát, cổng tai đè").
# Muốn quay lại số editor: SUBJECT_VOL=0.18 / SUBJECT_BREATH_VOL=0.32.
SUBJECT_VOL = 0.40         # -8dB — tiếng chủ thể TRONG voice
SUBJECT_BREATH_VOL = 0.56  # -5dB — tiếng chủ thể THẮNG Ô THỞ (không voice)
SUBJ_MAX = 10.0      # 🔸 trần giây 1 tiếng
# Trần SUBJ_CAP=6/video + không-2-beat-kề + ≤2-lần/kind ĐÃ BỎ (Milestone C, user chốt
# 2026-07-13: "không có mật độ — thấy footage phù hợp là để sfx phù hợp với footage đó",
# học sheet editor deepsea). Chống loạn còn lại: từ vựng match hẹp (subject_rules per-niche,
# không bare sea/ocean/whale) + ảnh/đồ họa/beat ngắn skip + xoay vòng biến thể.
# Tai chê ở cổng kiểm -> thêm knob lại, không đoán trước.

# S3 whoosh auto ĐÃ BỎ TRỌN (PB12 2026-07-10): đo 3 draft editor — 0/88 whoosh nằm quanh
# mốc vào ô thở (0% cả 3 draft), 40-70% đi cùng TEXT hiện lên (đúng lời user: "chapter 2:
# the moon" lên hình -> whoosh theo). Whoosh đúng kiểu editor = bám TEXT — overlay-SFX
# hiện có đã làm; phần thiếu = chapter-title card + whoosh/swell (backlog, kho swell ×8 chờ).

# S3-HOOK (MO_TA_VAN_HANH_HOOK_SFX, 2026-07-13): hit/whoosh/click tại CUT trong HOOK.
# 📌 KHÔNG lật PB12: PB12 đo SPACE (whoosh bám text); 23 draft DEEPSEA đo ra bám CUT
# (48% ±0.25s, text 3% — PHAN_TICH_HOOK_SFX_EDITOR_DEEPSEA) -> luật per-niche.
# 📌 space BẬT 2026-07-14 (user chốt): MƯỢN số deepsea 🔸 vì 2 niche gần giống —
# đo lại theo QUY_TRINH_LAY_MAU_SFX_NICHE_MOI.md khi space có số riêng thì thay.
HOOK_SFX_NICHES: tuple[str, ...] = ("deepsea", "space", "life-in", "investigate")
# 📌 investigate BẬT 03/09 (V2 Đợt 1b, user duyệt hướng SFX-tại-bùng): MƯỢN số
#    deepsea như space/life-in — đo lại riêng khi niche có số.
# 📌 life-in BẬT 2026-07-15 (user chốt): đối chiếu 48 draft editor — hook có nhấn
# (whoosh/impact bám cut). MƯỢN số deepsea (PM 1.44) như space; đo lại riêng khi có số.
HOOK_SFX_PM = 1.44         # 📌 CỔNG TAI V4 DS5-083 (2026-07-14): user chê whoosh+impact
                           # dày đặc khó chịu → CÒN 30% số đo editor (median 23 draft
                           # 4.8/ph — số gốc giữ ở PHAN_TICH). Áp CẢ 2 niche (space mượn).
HOOK_SFX_VOL = 0.2         # 🔸 quy tương quan PB10 (editor 0.56 × 0.18/0.5) — chờ cổng tai V4
HOOK_SFX_GAP = 3.0         # giây cách tối thiểu giữa 2 tiếng bất kỳ trong hook
HOOK_SFX_MAX_S = 4.0       # trần giây 1 one-shot (hit đuôi dài cắt + fade-out)
HOOK_CLICK_CAP = 4         # trần click/video (editor ~1.3 click/hook, đỉnh ~4)
HOOK_WHOOSH_LEAD = 0.08    # whoosh vào TRƯỚC cut 80ms (13% tiếng editor lead 0-200ms;
                           # cùng triết lý SNAP_LEAD của M-SNAP)
_HOOK_ACCENT_TOL = 0.35    # cut cách accent target ≤ tol -> coi là cut-accent (impact)


def nhan_sfx_slots(cuts: list[tuple[float, bool]],
                   vung: list[tuple[float, float]],
                   busy: list[float] | tuple[float, ...] = (),
                   accents: list[float] | tuple[float, ...] = (),
                   ) -> list[HookSfxSlot]:
    """S3 trên NHIỀU CỬA SỔ NHẤN — V2 Đợt 1b (user duyệt hướng 03/09).

    Vùng nhấn = chương H trọn (hook thật) + cửa sổ BEAT BÙNG ở chương thân/kết
    (nhip/ep.py quyết — đợt bùng là hook thu nhỏ). KHÔNG lật PB12: đây vẫn là
    tiếng bám CUT trong vùng mật độ cao (số 23 draft DEEPSEA), không phải whoosh
    rải tự do khắp thân — cái đó đã đo 0/88 và bỏ.

    Tái dùng NGUYÊN hook_sfx_slots (PM 1.44 · gap 3s · các luật đã qua cổng tai
    V4) bằng cách dịch mốc mỗi vùng về 0 rồi dịch slot trả về — không đụng một
    hằng số nào đã hiệu chỉnh.
    """
    ra: list[HookSfxSlot] = []
    for t0, t1 in vung:
        if t1 <= t0:
            continue
        cuts_v = [(t - t0, anh) for t, anh in cuts if t0 <= t <= t1]
        if not cuts_v:
            continue
        busy_v = [b - t0 for b in busy if t0 - HOOK_SFX_GAP <= b <= t1 + HOOK_SFX_GAP]
        acc_v = [a - t0 for a in accents if t0 <= a <= t1]
        slots_v = hook_sfx_slots(cuts_v, t1 - t0, busy=busy_v, accents=acc_v)
        if not slots_v and cuts_v:
            # Vùng bùng NGẮN (7-10s): ngân sách PM 1.44/phút làm tròn về 0 —
            # vùng câm lặng, mất luôn ý nghĩa "đánh dấu đợt bùng". Luật tối
            # thiểu: MỘT whoosh tại cut đầu vùng (vẫn giữ gap với tiếng đã có).
            t_dau = cuts_v[0][0] - HOOK_WHOOSH_LEAD
            if all(abs(t_dau - b) >= HOOK_SFX_GAP for b in busy_v):
                slots_v = [HookSfxSlot(t=t_dau, kind="whoosh",
                                       note="tối thiểu 1 tiếng/vùng bùng")]
        for slot in slots_v:
            slot.t += t0
            ra.append(slot)
        # tiếng vừa đặt trong vùng này thành busy của vùng sau (giữ gap toàn cục)
        busy = list(busy) + [x.t for x in ra]
    ra.sort(key=lambda x: x.t)
    return ra


def hook_sfx_niches() -> tuple[str, ...]:
    return HOOK_SFX_NICHES


@dataclass
class HookSfxSlot:
    t: float               # mốc đặt trên timeline (whoosh đã trừ lead)
    kind: str              # impact | whoosh | click
    note: str = ""
    file: Optional[Path] = None


def hook_sfx_slots(cuts: list[tuple[float, bool]], hook_end: float,
                   busy: list[float] | tuple[float, ...] = (),
                   accents: list[float] | tuple[float, ...] = (),
                   pm: float = HOOK_SFX_PM, gap: float = HOOK_SFX_GAP,
                   click_cap: int = HOOK_CLICK_CAP,
                   lead: float = HOOK_WHOOSH_LEAD) -> list[HookSfxSlot]:
    """Lịch S3-HOOK (pure — MO_TA_HOOK_SFX §1). cuts = [(mốc cut, cut-vào-ẢNH?)];
    busy = mốc tiếng đã có trong hook (S2/C1/sfx-track — đếm vào mật độ + giữ gap).

    Thứ tự: (1) click TẠI cut vào ảnh (đặt cả khi đủ mật độ, trần click_cap);
    (2) impact TẠI cut trùng accent nhạc; (3) whoosh TRƯỚC cut thường `lead`s —
    (2)+(3) chỉ BÙ tới round(pm × phút hook). Mọi tiếng cách nhau ≥ gap."""
    if hook_end <= 0:
        return []
    cs = sorted((t, p) for t, p in cuts if 0.5 <= t < hook_end)
    taken = sorted(float(b) for b in busy)

    def ok(t: float) -> bool:
        return all(abs(t - b) >= gap for b in taken)

    slots: list[HookSfxSlot] = []

    def add(t: float, kind: str, note: str) -> None:
        slots.append(HookSfxSlot(t=round(t, 3), kind=kind, note=note))
        taken.append(t)

    for t, is_photo in cs:                       # (1) click bám ảnh
        if sum(1 for s in slots if s.kind == "click") >= click_cap:
            break
        if is_photo and ok(t):
            add(t, "click", "cut vào ảnh")

    deficit = round(pm * hook_end / 60.0) - len(taken)
    acc = sorted(float(a) for a in accents or ())

    def near_accent(t: float) -> bool:
        return any(abs(t - a) <= _HOOK_ACCENT_TOL for a in acc)

    for t, is_photo in cs:                       # (2) impact tại cut-accent
        if deficit <= 0:
            break
        if not is_photo and near_accent(t) and ok(t):
            add(t, "impact", "cut accent")
            deficit -= 1
    for t, is_photo in cs:                       # (3) whoosh trước cut thường
        if deficit <= 0:
            break
        t2 = max(0.0, t - lead)
        if not is_photo and not near_accent(t) and ok(t2):
            add(t2, "whoosh", f"cut −{lead * 1000:.0f}ms")
            deficit -= 1
    slots.sort(key=lambda s: s.t)
    return slots

# Bảng chủ thể -> kind tiếng (controlled vocab — khớp TỪ NGUYÊN, xét theo thứ tự).
# THỨ TỰ = cụ thể trước, generic sau (V7 kiểm tag thật: rocket phụt lửa phải ra ROCKET,
# không phải fire). 3 từ bẫy đã bỏ: "solar" (solar panels ≠ mặt trời — b08 V7),
# "impact" (impact craters là cảnh TĨNH — b20 V7), "water" trần (tai V7: biển đêm nghe
# tiếng nước RÓT — kind water của kho là tiếng rót/sôi, sóng biển tách kind `ocean`).
SUBJECT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("rocket", ("rocket", "launch", "missile", "liftoff", "thruster")),
    ("explosion", ("explosion", "explode", "meteor", "meteorite", "collision")),
    ("rumble", ("earthquake", "rumble", "collapse", "debris", "avalanche")),
    ("signal", ("satellite", "signal", "transmission", "radar", "antenna")),
    ("ocean", ("ocean", "sea", "wave", "waves")),
    ("water", ("rain", "waterfall", "pouring")),
    ("fire", ("sun", "fire", "burning", "boiling", "lava", "flame")),
)
# Tai V7 (user 2026-07-10): tiếng lửa cho MẶT TRỜI chỉ khi quay CẬN CẢNH (editor gốc
# làm vậy); có lửa THẬT đang cháy trên hình (fire/burning/boiling/flame) thì cỡ nào
# cũng kêu. "lava" KHÔNG nằm nhóm lửa-thật: V8 b42 "volcanic rock formations" aerial
# (nham thạch NGUỘI) dính tag lava — lava cũng đòi cận cảnh mới kêu.
_FIRE_REAL = frozenset(("fire", "burning", "boiling", "flame"))
_CLOSE_SHOTS = ("close_up", "extreme_close_up")


@dataclass
class AmbientSlot:
    """1 ô thở đủ dài trên timeline + kết quả chọn ambient (ghi ambient_log)."""

    start: float
    end: float
    beat_id: Optional[int] = None   # beat mang ô (breathing_after của nó)
    scene_type: str = ""            # loại cảnh footage đang chiếu ("" = mù tag)
    subject_kind: str = ""          # kind CHỦ THỂ trên hình (S2 — thắng scene_type)
    subject_end: Optional[float] = None  # mốc kết MIẾNG 1 — tiếng chủ thể dừng theo miếng (tai V5)
    used_kind: str = ""             # kind thực dùng sau chuỗi fallback (choose_files điền)
    file: Optional[Path] = None     # file wav thư viện đã chọn (None = bỏ ô)
    note: str = ""                  # lý do chọn/bỏ — report + editor kiểm tai

    @property
    def dur(self) -> float:
        return self.end - self.start


def breath_slots(segments, min_len: float = AMB_MIN) -> list[AmbientSlot]:
    """Ô thở ≥ min_len: khoảng trống giữa các đoạn voice (vi nghỉ đã bị merge như F8)
    + ô thở kết video. beat_id = beat CUỐI của segment đứng ngay trước ô.

    NHIP-M2: Δ đoạn chèn (insert_after, nằm CUỐI gap ngay trước voice kế) KHÔNG nhận
    ambient — nhạc là chủ đạo trong Δ (M3); 1 clip ambient không loop phủ Δ dài sẽ im
    lặng nửa ô (BAN_GIAO §7c.4). Cắt ô ambient tại mép vào Δ."""
    if not segments:
        return []
    voice = ducking.merge_voice_intervals(segments)
    total_end = segments[-1].timeline_end + segments[-1].breathing_after
    # mép vào Δ theo timeline_start của segment SAU Δ (cùng float với cursor cut)
    ins_before = {round(b.timeline_start, 4): a.insert_after
                  for a, b in zip(segments, segments[1:])
                  if getattr(a, "insert_after", 0.0) > 0}
    gaps = [(b, a2 - ins_before.get(round(a2, 4), 0.0))
            for (_, b), (a2, _) in zip(voice, voice[1:])]
    if total_end - voice[-1][1] > 0:
        gaps.append((voice[-1][1], total_end))
    return [AmbientSlot(start=g0, end=g1, beat_id=_beat_at(segments, g0))
            for g0, g1 in gaps if g1 - g0 >= min_len]


def _beat_at(segments, t: float) -> Optional[int]:
    """Beat mang ô bắt đầu tại t = beat cuối của segment có timeline_end <= t gần nhất."""
    best = None
    for s in segments:
        if s.timeline_end <= t + 1e-6 and s.beat_ids:
            best = s.beat_ids[-1]
    return best


def resolve_scene(slot: AmbientSlot, project,
                  scene_lookup: Callable[[str], str]) -> str:
    """Loại cảnh footage đang chiếu trong ô: miếng shot thở ĐẦU của beat (MO_TA §3.2)
    -> không có thì pick của beat (giữ hình) -> "" (mù tag, sẽ rơi về default)."""
    for b in project.breath_shots:
        if b.beat_id == slot.beat_id and b.asset_path:
            return scene_lookup(b.asset_key)
    pick = next((s for s in project.shots if s.beat_id == slot.beat_id), None)
    return scene_lookup(pick.asset_key) if pick is not None else ""


def db_scene_lookup(conn) -> Callable[[str], str]:
    """asset_key -> scene_type qua cache.db: local tra library_assets; stock/entity tra
    stock_tags (M3b — vision tag pick, lưu vĩnh viễn). Không có dòng/bảng -> "" (fail-open)."""
    def look(asset_key: str) -> str:
        if asset_key.startswith("local:"):
            row = conn.execute(
                "SELECT scene_type FROM library_assets WHERE path = ?",
                (asset_key[len("local:"):],),
            ).fetchone()
        else:
            from autoedit.library.stock_tags import lookup_row
            row = lookup_row(conn, asset_key)
        return (row["scene_type"] or "") if row else ""
    return look


def choose_files(slots: list[AmbientSlot], niche_path: Path,
                 exclude_files: "frozenset[str] | None" = None) -> None:
    """Gắn file cho từng slot, ưu tiên CHỦ THỂ > loại cảnh > default (S2 nâng C1 —
    MO_TA_SFX §2 mức 1, sửa NGAY TẠI ĐÂY, không có tầng thứ 2 đè); biến thể xoay vòng
    theo kind; thiếu nốt -> bỏ ô + note. 1 ambient / 1 ô (MO_TA §3.4).

    exclude_files: tên file bị loại (cờ --no-epidemic). Loại hết 1 kind thì rơi tiếp
    xuống chain như kho vốn thiếu kind đó — không đẻ nhánh xử lý riêng."""
    rotation: dict[str, int] = {}
    for slot in slots:
        scene = slot.scene_type or "default"
        chain = [k for k in dict.fromkeys((slot.subject_kind, scene, "default")) if k]
        used, variants = None, []
        for k in chain:
            v = list_variants(k, niche_path, exclude_files)
            if v:
                used, variants = k, v
                break
        if not variants:
            slot.note = f"bỏ: kho không có '{chain[0]}' lẫn 'default'"
            continue
        i = rotation.get(used, 0)
        rotation[used] = i + 1
        slot.file = variants[i % len(variants)]
        slot.used_kind = used
        if slot.subject_kind and used == slot.subject_kind:
            via = f" (chủ thể thắng '{slot.scene_type or 'mù tag'}')"
        elif not slot.scene_type and used == "default":
            via = " (mù tag -> default)"
        elif used != scene:
            via = f" (kho thiếu '{scene}' -> default)"
        else:
            via = ""
        if slot.subject_kind and used != slot.subject_kind:
            via += f" · kho thiếu chủ thể '{slot.subject_kind}'"
        slot.note = f"{used}{via}"


# ===================== S2 — tiếng CHỦ THỂ trên hình ===========================
# 📌 KIND ỒN — user chốt cổng TAI RD-89 đợt 2 (2026-07-18): "ưu tiên sfx khán giả DỄ
# NGHE (thiên nhiên, động vật) hơn sfx KHÓ CHỊU như urban_street". Đây KHÔNG phải cửa
# loại — chỉ là NGƯỠNG BẰNG CHỨNG cao hơn: kind ồn phải đích danh trong `subject` mới
# kêu, không được suy từ tag bối cảnh (RD-89: urban_street 51/120 lượt = 42% thời lượng
# nghe tiếng xe, phần lớn suy từ tag `city`/`town`/`road`/`shop` của cảnh KHÔNG có xe).
# Thêm kind vào đây = "tiếng này làm phiền tai, đòi bằng chứng chắc"; tiếng thiên nhiên
# KHÔNG bao giờ vào danh sách này (sai cũng dễ nghe).
NOISY_KINDS: frozenset[str] = frozenset({
    "urban_street", "market", "subway", "plane", "racecar", "stadium",
    "motorboat", "snowmobile", "escalator",
})


def _hit(text_lower: str, keys) -> bool:
    """Khớp TỪ/CỤM TỪ nguyên (word-boundary): 'sunset' không ăn 'sun'; 'sperm whale'
    phân biệt được 'humpback whale' (kind loài — sheet SFX editor 2026-07-13)."""
    return any(re.search(rf"\b{re.escape(k)}\b", text_lower) for k in keys)


def subject_kind(text: str, shot_size: str = "",
                 rules: tuple[tuple[str, tuple[str, ...]], ...] | None = None,
                 subject: str | None = None) -> str:
    """Chủ thể trên hình -> kind tiếng. rules = bảng per-niche (subject_rules.yaml,
    ambient/library.load_subject_rules) — None -> SUBJECT_RULES built-in (space).
    "" = không match. Text = tag vision (subject/tags/description).
    Luật mặt-trời-cận (tai V7): fire match KHÔNG QUA lửa thật trên hình
    -> đòi shot cận, không thì im (áp cho mọi bảng — lava/hydrothermal cũng vậy).

    📌 LUẬT CHỦ THỂ-VS-PHÔNG NỀN (cổng TAI RD-89 đợt 2, user chốt 2026-07-18):
    `subject` (nếu truyền) = chủ thể THẬT, quyết định trước. `tags`/`description` chỉ là
    BỐI CẢNH — GLM liệt kê mọi thứ nhìn thấy, không phân biệt chủ thể với phông nền, nên
    "quả chanh trong chợ" có tag `market` và kêu tiếng chợ. Đo thật 5/5 ca user chê đều
    khớp nhầm qua `tags`, `subject` thì ĐÚNG cả 5. Xem NOISY_KINDS cho phần chỉ-tin-subject.
    subject=None -> hành vi CŨ y nguyên (test/caller cũ không đổi)."""
    if subject is not None:
        k = _kind_of(subject, shot_size, rules)
        if k:
            return k
        # subject mù chữ -> cho bối cảnh cứu, TRỪ kind ồn (phải đích danh mới kêu)
        k = _kind_of(text, shot_size, rules)
        return "" if k in NOISY_KINDS else k
    return _kind_of(text, shot_size, rules)


def _kind_of(text: str, shot_size: str,
             rules: tuple[tuple[str, tuple[str, ...]], ...] | None) -> str:
    t = text.lower()
    for kind, keys in (rules if rules is not None else SUBJECT_RULES):
        if _hit(t, keys):
            if kind == "fire" and not _hit(t, _FIRE_REAL) and shot_size not in _CLOSE_SHOTS:
                return ""  # nguồn nóng nhưng KHÔNG cận cảnh -> im (editor gốc làm vậy)
            return kind
    return ""


def db_subject_lookup(conn) -> Callable[[str], tuple[str, str, str]]:
    """asset_key -> (chuỗi subject+tags+description, shot_size, subject RIÊNG) — 'mắt
    editor' nhìn footage LÀ GÌ + quay cỡ nào. Local tra library_assets (vision ingest);
    stock/entity tra stock_tags (M3b). Không có dòng/bảng -> ("", "", "") (fail-open).

    📌 Trả THÊM `subject` tách riêng (2026-07-18): gộp phẳng 3 trường làm MẤT thông tin
    trường nào là trường nào, mà đó đúng là thứ phân biệt chủ thể với phông nền
    (xem subject_kind). Giữ nguyên phần tử [0]/[1] để caller cũ không phải đổi."""
    def look(asset_key: str) -> tuple[str, str, str]:
        if asset_key.startswith("local:"):
            row = conn.execute(
                "SELECT subject, tags, description, shot_size FROM library_assets WHERE path = ?",
                (asset_key[len("local:"):],),
            ).fetchone()
        else:
            from autoedit.library.stock_tags import lookup_row
            row = lookup_row(conn, asset_key)
        if not row:
            return ("", "", "")
        text = " ".join(str(row[k] or "") for k in ("subject", "tags", "description"))
        return (text, str(row["shot_size"] or ""), str(row["subject"] or ""))
    return look


def _kind_from_lookup(asset_key: str, subject_lookup, rules) -> str:
    """Gọi lookup + subject_kind ĐÚNG tham số. KHÔNG unpack `*` được nữa: lookup trả
    3-tuple (text, shot, subject), unpack mù sẽ đẩy `subject` vào chỗ `rules`."""
    got = subject_lookup(asset_key)
    text, shot = got[0], got[1]
    subj = got[2] if len(got) > 2 else None   # lookup cũ (test) trả 2-tuple -> hành vi cũ
    return subject_kind(text, shot, rules=rules, subject=subj)


def resolve_slot_subject(slot: AmbientSlot, project,
                         subject_lookup: Callable[[str], tuple[str, str, str]],
                         rules=None) -> str:
    """Kind chủ thể của Ô THỞ — cùng thứ tự ưu tiên resolve_scene (miếng shot thở đầu
    -> pick giữ hình); chỉ tag kho (vision thật), KHÔNG dùng concept cho ô thở."""
    for b in project.breath_shots:
        if b.beat_id == slot.beat_id and b.asset_path:
            return _kind_from_lookup(b.asset_key, subject_lookup, rules)
    pick = next((s for s in project.shots if s.beat_id == slot.beat_id), None)
    return _kind_from_lookup(pick.asset_key, subject_lookup, rules) if pick is not None else ""


def first_piece_end(slot: AmbientSlot, project) -> Optional[float]:
    """Mốc kết MIẾNG shot thở ĐẦU của ô — tiếng chủ thể bám miếng nó match, KHÔNG tràn
    sang miếng sau (tai V5 2026-07-10: b20 fire tràn sang footage tên lửa, b46 signal
    tràn qua mốc tàu thăm dò). dur=0 (record v1, miếng phủ trọn ô) -> None (không cắt)."""
    for b in project.breath_shots:
        if b.beat_id == slot.beat_id and b.asset_path:
            return slot.start + b.dur if b.dur > 0 else None
    return None


@dataclass
class SubjectSlot:
    """1 tiếng chủ thể TRONG voice (S2 mức 2) — ghi subject_sfx_log."""

    start: float
    end: float
    beat_id: int
    kind: str
    source: str = ""                # "kho" (vision tag) | "concept" (NÃO tả hình — proxy)
    file: Optional[Path] = None
    note: str = ""


def subject_beat_slots(project, subject_lookup: Callable[[str], tuple[str, str, str]],
                       skip_beat: Optional[Callable] = None,
                       rules=None, llm=None) -> list[SubjectSlot]:
    """Beat có chủ thể match -> 1 tiếng lúc chủ thể lên hình (đầu beat). CHỈ tin tag
    kho (vision thật) — nhánh visual_concept proxy BỎ sau tai V5 2026-07-10 (b22 mặt
    trăng nghe lửa, b56 dung nham nghe nước: concept NÃO ≠ footage stock thật; stock
    chờ C5 vision đợt 5). ẢNH (entity/Ken Burns) KHÔNG SFX — tai V7: ảnh đứng yên mà
    kêu tiếng rocket là sai. MATCH-DRIVEN không trần (Milestone C, user chốt 2026-07-13):
    footage match là đặt — như editor; beat đồ họa (skip_beat) + beat ngắn <AMB_MIN bỏ.
    Beat nhiều shot: tiếng cắt theo SHOT 1 (miếng nó match) — dùng chung split_window.

    llm = (client, kinds_có_file) — TẦNG 3 tùy chọn (assemble --sfx-llm): CHỈ chấm các
    beat bảng luật MÙ CHỮ ("Omani village", "residential neighborhood" — cảnh phố thật
    mà không từ nào lọt bảng). Bảng luật đã quyết -> KHÔNG hỏi NÃO. None = tắt."""
    from autoedit.library.vision import IMAGE_EXTS
    from autoedit.packager.coverage import split_window

    cands: list[tuple] = []          # (beat, pick, kind, text, shot, subj)
    for b in project.beats:
        if b.timeline_start is None or b.timeline_end is None:
            continue
        if b.timeline_end - b.timeline_start < AMB_MIN:
            continue
        if skip_beat is not None and skip_beat(b):
            continue
        pick = next((s for s in project.shots if s.beat_id == b.beat_id), None)
        if pick is None or not pick.asset_path:
            continue
        if Path(pick.asset_path).suffix.lower() in IMAGE_EXTS:
            continue  # ảnh đứng yên (entity/Ken Burns) — không SFX (tai V7)
        got = subject_lookup(pick.asset_key)
        text, shot = got[0], got[1]
        subj = got[2] if len(got) > 2 else None
        cands.append((b, pick, subject_kind(text, shot, rules=rules, subject=subj),
                      text, shot, subj or ""))

    llm_kind: dict[int, str] = {}
    if llm is not None:
        client, kinds = llm
        blind = [{"id": b.beat_id, "subject": subj, "tags": text[:300], "shot_size": shot}
                 for b, _p, k, text, shot, subj in cands if not k]
        if blind:
            from autoedit.ambient.subject_llm import score_unmatched
            llm_kind = score_unmatched(blind, kinds, client)

    out: list[SubjectSlot] = []
    for b, pick, kind, text, shot, _subj in cands:
        src = "kho"
        if not kind and b.beat_id in llm_kind:
            kind, src = llm_kind[b.beat_id], "llm"
            # 📌 Quyết định của NÃO PHẢI đi qua LUẬT AN TOÀN như đường bảng luật — nếu
            # không, NÃO lách được luật mà bảng luật vẫn phải tuân. Cắn thật: b063
            # "jack-o'-lantern" (medium, tag `candlelight`) -> fire, đúng thứ luật
            # fire-cận-cảnh (tai V7) vốn chặn. Đây là lỗ hổng KIẾN TRÚC, không phải 1 ca lẻ.
            if kind == "fire" and not _hit(text.lower(), _FIRE_REAL) \
                    and shot not in _CLOSE_SHOTS:
                kind = ""
        if not kind:
            continue
        end = min(b.timeline_end, b.timeline_start + SUBJ_MAX)
        n_shots = 1 + len(pick.extra_shots)
        if n_shots > 1:  # shot 1 = clip match; tiếng không tràn sang shot 2
            end = min(end, split_window(b.timeline_start, b.timeline_end, n_shots)[0][1])
        if end - b.timeline_start < AMB_MIN:
            continue
        out.append(SubjectSlot(start=b.timeline_start, end=end,
                               beat_id=b.beat_id, kind=kind, source=src))
    return out


def choose_subject_files(slots: list[SubjectSlot], niche_path: Path,
                         exclude_files: "frozenset[str] | None" = None) -> None:
    """Xoay vòng biến thể theo kind. KHÔNG rơi về default — tiếng chủ thể phải đúng
    chủ thể, thiếu thì thà im (drone nền + nhạc vẫn lo)."""
    rotation: dict[str, int] = {}
    for s in slots:
        variants = list_variants(s.kind, niche_path, exclude_files)
        if not variants:
            s.note = f"bỏ: kho không có '{s.kind}'"
            continue
        i = rotation.get(s.kind, 0)
        rotation[s.kind] = i + 1
        s.file = variants[i % len(variants)]
        s.note = f"{s.kind} ({s.source})"


# ===================== S1 — drone nền suốt video ==============================
def choose_drone(niche_path: Path, seed: str,
                 exclude_files: "frozenset[str] | None" = None) -> Optional[Path]:
    """1 drone / 1 video, deterministic crc32 theo seed (khuôn seed shot thở 2.0) —
    video khác nhau nghe khác nhau, chạy lại cùng project ra cùng file."""
    variants = list_variants("drone", niche_path, exclude_files)
    if not variants:
        return None
    return variants[zlib.crc32(seed.encode("utf-8")) % len(variants)]


