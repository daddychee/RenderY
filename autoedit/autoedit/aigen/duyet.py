r"""Phiên duyệt ảnh aigen — dữ liệu cho cổng duyệt (editor nộp job tự duyệt).

Flow (user chốt 03/09): beat thiếu hình gom theo MOTIF → Seedream sinh 2 phương
án ảnh/motif → job đỗ, EDITOR duyệt trên UI (chọn/loại/ghi chú regen) → chốt →
Seedance i2v CHỈ ảnh đã chọn. Tiền video đốt sau cổng, không trước.

Lưu JSON cạnh project (không DB — cùng triết lý project.json là hàng đợi bền):
    projects/<id>/aigen_duyet.json     — phiên
    projects/<id>/aigen/<file>.png     — ảnh phương án
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

TEN_FILE = "aigen_duyet.json"
THU_MUC_ANH = "aigen"


@dataclass
class PhuongAn:
    """1 ảnh ứng viên của motif."""

    file: str                       # tên file trong projects/<id>/aigen/
    chon: bool | None = None        # None=chưa quyết · True=chốt · False=loại
    ghi_chu: str = ""               # editor ghi -> dùng làm feedback khi regen


@dataclass
class Motif:
    """1 cảnh chủ — gen MỘT lần, gán NHIỀU beat (giãn cách ≥60s, user chốt)."""

    ma: str                         # m1, m2...
    mo_ta: str                      # người đọc: "Cờ cầu nguyện trên đèo gió"
    prompt: str                     # prompt đã gửi Seedream (regen dùng lại + ghi chú)
    beat_ids: list[int] = field(default_factory=list)
    phuong_an: list[PhuongAn] = field(default_factory=list)

    @property
    def anh_chot(self) -> PhuongAn | None:
        return next((p for p in self.phuong_an if p.chon), None)


@dataclass
class PhienDuyet:
    project_id: str
    trang_thai: str = "cho_duyet"   # cho_duyet | da_chot | da_gen_video
    motif: list[Motif] = field(default_factory=list)

    # ------------------------------------------------------------- io
    @staticmethod
    def duong(project_dir: Path) -> Path:
        return Path(project_dir) / TEN_FILE

    @classmethod
    def doc(cls, project_dir: Path) -> "PhienDuyet | None":
        f = cls.duong(project_dir)
        if not f.is_file():
            return None
        d = json.loads(f.read_text(encoding="utf-8"))
        return cls(project_id=d["project_id"], trang_thai=d.get("trang_thai", "cho_duyet"),
                   motif=[Motif(ma=m["ma"], mo_ta=m["mo_ta"], prompt=m["prompt"],
                                beat_ids=list(m.get("beat_ids", [])),
                                phuong_an=[PhuongAn(**p) for p in m.get("phuong_an", [])])
                          for m in d.get("motif", [])])

    def ghi(self, project_dir: Path) -> Path:
        f = self.duong(project_dir)
        f.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=1),
                     encoding="utf-8")
        return f

    # ------------------------------------------------------------- nghiệp vụ
    def chon(self, ma_motif: str, file: str, chon: bool | None,
             ghi_chu: str = "") -> bool:
        """Editor quyết 1 phương án. Chốt 1 ảnh thì tự bỏ chốt ảnh khác cùng motif
        (mỗi motif đúng MỘT ảnh thắng — 1 motif 1 video)."""
        for m in self.motif:
            if m.ma != ma_motif:
                continue
            for p in m.phuong_an:
                if p.file == file:
                    p.chon = chon
                    if ghi_chu:
                        p.ghi_chu = ghi_chu
                elif chon:               # chốt ảnh này -> ảnh khác thôi chốt
                    p.chon = False if p.chon else p.chon
            return True
        return False

    def du_de_chot(self) -> tuple[bool, str]:
        """Chốt phiên được chưa? Mỗi motif phải có đúng 1 ảnh chọn HOẶC bị loại
        toàn bộ (editor quyết motif này khỏi cần AI — beat rơi về needs_human)."""
        thieu = [m.ma for m in self.motif
                 if m.anh_chot is None and any(p.chon is None for p in m.phuong_an)]
        if thieu:
            return False, f"motif chưa quyết: {', '.join(thieu)}"
        return True, ""
