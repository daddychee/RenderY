r"""Hồ Sơ Kênh — 3 tầng học từ kênh ref, KHÔNG luật cứng (user chốt 05/09).

User: "cả 3 mặt đều học được từ việc nghiên cứu kênh ref" — mỗi phương án dựng
(PA1 toàn stock · PA2 AI bù · PA3 tự quay) gắn 1 kênh YouTube ref do editor
chọn; tool đo kênh đó ra hồ sơ 3 tầng thay cho việc khai số tay:

  Tầng 1 NHỊP   — nhip/do.py (2 thước hội tụ, đã kiểm chứng Fern/WUFO 03/09).
  Tầng 2 NHẠC   — ffmpeg thuần (RMS/giây → energy curve): librosa CỐ Ý không
                  cài trên máy chủ (10 test music_rhythm fail là vì vậy) nên
                  tầng này không được phụ thuộc nó.
  Tầng 3 LOẠI CẢNH — GLM vision chấm khung hình tại điểm cắt (Đợt B).

CACHE THEO KÊNH (user chốt 05/09): 1 kênh chỉ tải/đo MỘT lần — né bẫy YouTube
chặn IP sau ~9 lượt tải (đã dính thật khi đo nghiên cứu tháng 9). Cache tại
`<data_root>/kenh/<slug>/hoso.json`; đo lại phải chủ động `--do-lai`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from autoedit.packager.machine import resolve_data_root


def thu_muc_kenh(ten: str) -> Path:
    return resolve_data_root() / "kenh" / ten


@dataclass
class HoSoKenh:
    """Kết quả đo 1 kênh ref — nguồn sự thật cho 3 chỗ áp: ép nhịp, nhạc, nguồn."""

    ten: str                                  # slug kênh (fern-tv, johnnyharris...)
    nguon: list[str] = field(default_factory=list)   # link/id các video đã đo
    ngay_do: str = ""
    so_video_hoi_tu: int = 0                  # chỉ video 2 thước hội tụ mới được tính

    # ---- tầng 1: NHỊP (median qua các video hội tụ; đơn vị giây / tỉ lệ 0..1) ----
    hook_trung_vi: float = 0.0
    hook_ty_le_nhanh: float = 0.0
    hook_kieu: str = ""                       # no | leo | em — suy từ hook/thân
    than_trung_vi: float = 0.0
    than_ty_le_nhanh: float = 0.0
    than_ty_le_hold: float = 0.0
    bung_chu_ky_s: float = 0.0                # 0 = không đo được chu kỳ

    # ---- tầng 2: NHẠC (ffmpeg thuần) ----
    nhac_energy_curve: list[float] = field(default_factory=list)  # 12 bucket 0..1
    nhac_vi_tri_drop: float = 0.0             # bucket mạnh nhất nằm ở đâu (0..1)
    nhac_do_dong: float = 0.0                 # dải động dB (p90-p10) — nhạc phẳng hay sóng

    # ---- tầng 3: LOẠI CẢNH (Đợt B — GLM vision; rỗng = chưa đo) ----
    loai_canh: dict = field(default_factory=dict)  # {tu_quay, b_roll, do_hoa, ai_render}: 0..1

    # ------------------------------------------------------------------ io
    @staticmethod
    def duong(ten: str) -> Path:
        return thu_muc_kenh(ten) / "hoso.json"

    @classmethod
    def doc(cls, ten: str) -> "HoSoKenh | None":
        f = cls.duong(ten)
        if not f.is_file():
            return None
        d = json.loads(f.read_text(encoding="utf-8"))
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def ghi(self) -> Path:
        f = self.duong(self.ten)
        f.parent.mkdir(parents=True, exist_ok=True)
        if not self.ngay_do:
            self.ngay_do = datetime.now(timezone.utc).isoformat()
        f.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=1),
                     encoding="utf-8")
        return f

    # ------------------------------------------------------- áp vào HoSoNhip
    def ap_vao_nhip(self, hs) -> tuple["object", list[str]]:
        """Trả (HoSoNhip MỚI, log) — hồ sơ nhịp là frozen dataclass, KHÔNG gán
        đè tại chỗ được (bug 05/09: test kênh lộ FrozenInstanceError; cùng lỗi
        đó nằm im trong retention/ap_vao_ho_so production, bị fail-open nuốt).

        Chỉ đè trường có số (0 = không đo được thì giữ số hồ sơ niche)."""
        from dataclasses import replace

        doi: dict = {}
        ra: list[str] = []
        if self.than_trung_vi > 0:
            doi.update(than_trung_vi=self.than_trung_vi,
                       than_ty_le_nhanh=self.than_ty_le_nhanh,
                       than_ty_le_hold=self.than_ty_le_hold)
            ra.append(f"thân {self.than_trung_vi:.1f}s (nhanh {self.than_ty_le_nhanh:.0%}"
                      f" · hold {self.than_ty_le_hold:.0%})")
        if self.hook_trung_vi > 0:
            doi.update(hook_trung_vi=self.hook_trung_vi,
                       hook_ty_le_nhanh=self.hook_ty_le_nhanh)
            ra.append(f"hook {self.hook_trung_vi:.1f}s kiểu {self.hook_kieu or '?'}")
        if self.hook_kieu:
            doi["hook_kieu"] = self.hook_kieu
        if self.bung_chu_ky_s > 0:
            doi["bung_chu_ky_s"] = self.bung_chu_ky_s
            ra.append(f"chu kỳ bùng {self.bung_chu_ky_s / 60:.1f} phút")
        if ra:
            ra = [f"nhịp học từ kênh «{self.ten}» ({self.so_video_hoi_tu} video): "
                  + " · ".join(ra)]
        return (replace(hs, **doi) if doi else hs), ra
