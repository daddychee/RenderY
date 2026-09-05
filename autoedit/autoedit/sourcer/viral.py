"""C8 gói CHỌN — gate PHÁP LÝ khi phễu chọn footage viral (MO_TA_VAN_HANH_C8_CHON.md).

Luật 3: cấm 2 cảnh scene_index LIỀN KỀ của cùng 1 nguồn trong 1 video mình, DÙ ĐẶT XA
NHAU trên timeline (user chốt 2026-07-08). Luật 5: trần 8% thời lượng nguồn — cộng dồn
TRỌN duration clip mỗi lần pick (bảo thủ: clip chỉ chiếu 1 phần vẫn tính trọn).
REF (user chốt 2026-07-11): nguồn khai --ref (video mẫu của bài) trần 15% thay 8%.

Gate CỨNG cùng loại geo-gate PA2 — KHÔNG phải veto chất lượng (filter-overload-guard
nguyên vẹn). Ledger sống trọn 1 lần run_source; asset class 'own'/Pexels miễn mọi gate.
"""

from __future__ import annotations

VIRAL_CAP_RATIO = 0.08  # luật 5: trần % thời lượng 1 nguồn trong 1 video mình
# REF (user chốt 2026-07-11): nguồn MẪU CỦA BÀI (người dựng khai --ref, máy không suy
# từ tên file) được trần riêng — editor đã khoanh đúng đề tài nên chấp nhận footprint
# lớn hơn; luật kề + rải mềm vẫn áp nguyên.
REF_CAP_RATIO = 0.15
# LẶP FOOTAGE (editor Hải + user chốt 05/09: "một số footage bị lặp lại, chỉ cách
# nhau vài frame — trong 45-60s không được dùng lại footage đã dùng"): cùng NGUỒN
# (source_video) không được xuất hiện 2 lần trong cửa sổ 60s timeline. Áp MỌI
# class có source_video (luật kề cũ chỉ áp viral nên own/local/ref lọt).
CUA_SO_LAP_S = 60.0


class ViralLedger:
    """Trạng thái viral-đã-lấy của 1 video đang dựng (phễu thoại — shot thở đóng với viral)."""

    def __init__(self, ref_sources: tuple[str, ...] | list[str] = ()) -> None:
        self.picked: dict[str, set[int]] = {}  # source_video -> scene_index đã dùng
        # luật cửa sổ 60s: source_video -> mốc beat (giây voice) lần dùng gần nhất.
        # beat_hien_tai do _gather_candidates đặt trước mỗi lượt gate/re-check.
        self.moc_lap: dict[str, float] = {}
        self.beat_hien_tai: float = 0.0
        self.seconds: dict[str, float] = {}    # source_video -> giây đã lấy (trọn clip)
        self.blocked = 0                       # đếm ứng viên bị gate chặn (report)
        self.peak_picks = 0                    # ytref §3h: đếm pick mang cờ điểm nhô (report)
        # prefix folder/file nguồn mẫu, so lower-case (path Windows không phân hoa-thường)
        self.ref_prefixes: tuple[str, ...] = tuple(str(s).lower() for s in ref_sources if str(s).strip())
        # REF THEO CHƯƠNG (VD2, user chốt 2026-07-18 MỀM): chương -> prefix folder con
        # "Chapter N" (runner đổ từ ref_chapter_scan). Chỉ scope CHÈN + bonus is_ref;
        # trần 15% vẫn CẢ mẻ — _cap_ratio cố ý KHÔNG đọc map này. Rỗng = ref phẳng y cũ.
        self.ref_chapter_prefixes: dict[int, tuple[str, ...]] = {}
        # M4d HINH THO (user chốt 2026-07-21): folder `HINH THO` dưới --ref = footage
        # dành RIÊNG cho Δ/mini-hook — tước CHÈN + bonus ở MỌI beat thường (mềm: search
        # thường vẫn vớt được, trần 15% vẫn cả mẻ — không đẻ cửa loại).
        self.ref_hinhtho_prefixes: tuple[str, ...] = ()

    def ref_excludes(self, chapter: int) -> tuple[str, ...]:
        """Prefix các chương KHÁC `chapter` + toàn bộ HINH THO — cảnh trong đó mất CHÈN
        + REF_BONUS ở beat này (vẫn vào pool được qua search thường + vẫn ăn trần 15%)."""
        return tuple(p for ch, ps in self.ref_chapter_prefixes.items()
                     if ch != chapter for p in ps) + self.ref_hinhtho_prefixes

    def _cap_ratio(self, src: str) -> float:
        """Trần theo nguồn: 15% nếu là nguồn mẫu của bài (khai --ref), còn lại 8%."""
        if self.ref_prefixes and src.lower().startswith(self.ref_prefixes):
            return REF_CAP_RATIO
        return VIRAL_CAP_RATIO

    def blocks(self, cand: dict) -> str:
        """'' nếu qua; lý do (ghi log) nếu gate chặn. Chỉ áp class viral."""
        src_lap = cand.get("source_video", "")
        if src_lap:
            gan = self.moc_lap.get(src_lap)
            if gan is not None and abs(self.beat_hien_tai - gan) < CUA_SO_LAP_S:
                return (f"nguồn «{src_lap}» vừa dùng {abs(self.beat_hien_tai - gan):.0f}s"
                        f" trước — luật 60s chống lặp")
        if cand.get("source_class") != "viral":
            return ""
        src = cand.get("source_video", "")
        idx = int(cand.get("scene_index") or 0)
        used = self.picked.get(src, set())
        if idx in used:
            return f"cảnh {idx} trùng cảnh đã dùng của nguồn"
        # ytref (user chốt 2026-07-11): cảnh ĐIỂM NHÔ miễn luật kề — chuỗi 3 cảnh
        # build-up sát đỉnh được lấy CẢ (đặt khác vị trí khi dựng); trần 8% + rải
        # nguồn vẫn áp nguyên. Cảnh THƯỜNG kề cảnh đã dùng vẫn cấm như cũ.
        if not cand.get("peak_value") and ((idx - 1) in used or (idx + 1) in used):
            return f"cảnh {idx} kề cảnh đã dùng của nguồn"
        ratio = self._cap_ratio(src)
        cap = ratio * float(cand.get("source_duration") or 0)
        if cap <= 0:
            return "thiếu source_duration (mẫu số trần %) — không dùng"
        if self.seconds.get(src, 0.0) + float(cand.get("duration") or 0) > cap:
            return f"vượt trần {ratio:.0%} nguồn ({self.seconds.get(src, 0.0):.0f}s/{cap:.0f}s)"
        return ""

    def add(self, cand: dict) -> None:
        """Ghi sổ SAU khi pick thật (đã tải/copy thành công)."""
        src_lap = cand.get("source_video", "")
        if src_lap:
            self.moc_lap[src_lap] = self.beat_hien_tai
        if cand.get("source_class") != "viral":
            return
        src = cand.get("source_video", "")
        self.picked.setdefault(src, set()).add(int(cand.get("scene_index") or 0))
        self.seconds[src] = self.seconds.get(src, 0.0) + float(cand.get("duration") or 0)
        if cand.get("peak_value"):
            self.peak_picks += 1

    def gate(self, cands: list[dict]) -> list[dict]:
        """Lọc gate cứng + sort rải mềm (luật 5: nguồn ít-dùng lên trước — sort ổn định,
        own giữ nguyên chỗ tương đối vì key=0). KHÔNG phải cửa loại chất lượng."""
        out = []
        for c in cands:
            if self.blocks(c):
                self.blocked += 1
            else:
                out.append(c)
        out.sort(key=lambda c: self.seconds.get(c.get("source_video", ""), 0.0)
                 if c.get("source_class") == "viral" else 0.0)
        return out

    def summary(self) -> str:
        """1 dòng cho report: nguồn nào lấy bao nhiêu giây/cảnh."""
        if not self.picked:
            return ""
        from pathlib import Path
        parts = [f"{Path(src).stem[:30]}: {len(idxs)} cảnh/{self.seconds.get(src, 0):.0f}s"
                 for src, idxs in self.picked.items()]
        return " · ".join(parts)
