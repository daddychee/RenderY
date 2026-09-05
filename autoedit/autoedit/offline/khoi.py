r"""Cắt KHỐI theo hơi thở người đọc — pha 1 của Offline. Hàm thuần, test được.

Quy tắc GIAO 2 BẰNG CHỨNG (nghiệm thu bằng RMS 06/09 trên LI100 — 11/16 ranh
silence-only bị từ kế đè 0.06-0.33s):
  - ranh CỨNG: im lặng đo được >= NGAT_CUNG_S
  - bắt đầu thở = max(silence_start, mốc KẾT của từ cuối)   -> không ăn voice cũ
  - kết thúc thở = min(silence_end,  mốc BẮT ĐẦU từ kế)     -> dứt đúng lúc voice lên
  - kẹp xong < THO_TOI_THIEU_S thì không đáng là thở (nhập vào khối nói)
  - ranh MỀM (NGAT_MEM_S..NGAT_CUNG_S): điểm chẻ hợp lệ cho "sinh phương án"
Trục thời gian QUY 0 tại khởi âm đầu tiên (offset giữ riêng để phát audio).
"""

from __future__ import annotations

from dataclasses import dataclass, field

NGAT_CUNG_S = 0.5      # im lặng >= mức này là ranh khối (user chốt 06/09)
NGAT_MEM_S = 0.3       # 0.3-0.5s: ranh mềm — sinh phương án bật/tắt
THO_TOI_THIEU_S = 0.3  # kẹp giao xong ngắn hơn -> không phải thở
LE_TU_S = 0.45         # lề dò mốc từ quanh ranh (align lệch tới ~0.4s sau nghỉ)


@dataclass
class Khoi:
    """1 khối nói + khoảng thở NGAY SAU nó (thở là khối trắng riêng trên UI)."""

    v0: float                 # bắt đầu nói (trục quy 0)
    v1: float                 # kết thúc nói = bắt đầu khối trắng
    tho: float = 0.0          # độ dài khối trắng TỰ NHIÊN (đo từ voice)
    tho_them: float = 0.0     # người chỉnh: + chèn im lặng thật, − thu (sàn giữ 0.2s)
    loi: str = ""
    ranh_mem: list[float] = field(default_factory=list)   # điểm chẻ hợp lệ trong khối
    goi_y_che: bool = False   # khối dài quá chuẩn Framing -> gợi ý (người quyết)


def _tu_truoc(words: list[dict], t: float) -> float:
    ket = [w.get("end", 0.0) for w in words if w.get("end", 0.0) <= t + LE_TU_S]
    return max(ket) if ket else 0.0


def _tu_ke(words: list[dict], t: float, tran: float) -> float:
    bat = [w.get("start", 0.0) for w in words if w.get("start", 0.0) >= t - LE_TU_S]
    return min(bat) if bat else tran


def cat_khoi(silences: list[tuple[float, float]], words: list[dict],
             het: float, than_framing: float = 0.0) -> tuple[list[Khoi], float]:
    """(silences từ cutter.silence, words từ align, mốc hết) -> ([Khoi], offset).

    silences/words theo trục FILE; Khoi trả về theo trục QUY 0 (offset = khởi âm
    đầu). than_framing > 0 thì đánh dấu goi_y_che cho khối dài > 1.6x chuẩn.
    """
    cung = [(s, min(e, het)) for s, e in silences
            if s < het and (min(e, het) - s) >= NGAT_CUNG_S]
    mem = [s for s, e in silences
           if s < het and NGAT_MEM_S <= (min(e, het) - s) < NGAT_CUNG_S]

    # khởi âm đầu: hết khoảng im mở đầu, kẹp bằng từ đầu tiên
    dau = cung[0][1] if cung and cung[0][0] < 0.3 else 0.0
    dau = min(dau, _tu_ke(words, dau, het)) if words else dau

    khoi: list[Khoi] = []
    truoc = dau
    for s, e in cung:
        if s <= truoc + 0.2:
            truoc = max(truoc, min(e, _tu_ke(words, e, het)))
            continue
        tho_bat = max(s, _tu_truoc(words, s))
        tho_ket = min(e, _tu_ke(words, e, het))
        if tho_ket - tho_bat < THO_TOI_THIEU_S:
            continue
        khoi.append(Khoi(v0=round(truoc, 2), v1=round(tho_bat, 2),
                         tho=round(tho_ket - tho_bat, 2)))
        truoc = tho_ket
        if truoc >= het:
            break
    if truoc < het - 1.0:
        khoi.append(Khoi(v0=round(truoc, 2), v1=round(het, 2)))

    # quy 0 + lời + ranh mềm + gợi ý chẻ
    for k in khoi:
        ws = [w for w in words
              if w.get("start", 0.0) >= k.v0 - 0.6 and w.get("end", 0.0) <= k.v1 + 0.3]
        k.loi = " ".join(w.get("text", w.get("word", "")) for w in ws).strip()[:200]
        k.ranh_mem = [round(x - dau, 2) for x in mem if k.v0 + 0.8 < x < k.v1 - 0.8]
        k.v0, k.v1 = round(k.v0 - dau, 2), round(k.v1 - dau, 2)
        if than_framing > 0:
            k.goi_y_che = (k.v1 - k.v0) > than_framing * 1.6
    return khoi, round(dau, 2)


def tong_thoi_luong(khoi: list[Khoi]) -> float:
    """Tổng timeline = voice + thở tự nhiên + thở người chỉnh (voice bất biến)."""
    return round(sum((k.v1 - k.v0) + max(0.0, k.tho + k.tho_them) for k in khoi), 2)


def chinh_tho(k: Khoi, delta: float) -> Khoi:
    """+/-1s = thao tác ÂM THANH thật (user chốt 06/09): + chèn im lặng kể cả nơi
    chưa nghỉ; − được ăn vào ngắt tự nhiên nhưng luôn giữ sàn 0.2s (không bao
    giờ chạm vào lời). Mutate + trả lại chính khối."""
    san = -(max(k.tho - 0.2, 0.0))
    k.tho_them = round(max(san, k.tho_them + delta), 2)
    return k
