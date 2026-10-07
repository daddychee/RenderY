r"""Kho BẢN TÁCH theo cảnh — tách một lần, dựng lại bao nhiêu lần cũng không tách lại.

User chốt 06/10/2026 (cách A): dựng thẳng video; cảnh cắt sai thì editor bấm điểm lên ảnh,
"Tách lại" -> dựng lại ĐÚNG cảnh đó. Nên bản tách phải sống theo CẢNH (không theo việc), có
điểm bấm tay, có cờ "không chắc", và tự bỏ khi ảnh cảnh bị vẽ lại (so dấu băm ảnh).

Đặt ở `<goc>/canh/<tập>/<mã cảnh>/`. `tach.json` ghi SAU CÙNG = dấu "bản tách đã đủ".
Mỏng: trang treatment chỉ gọi `thong_tin` (đọc json) — không kéo torch.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

_MAU = [(1.0, 0.35, 0.25), (0.25, 1.0, 0.4), (0.35, 0.5, 1.0)]


class KhoTach:
    def __init__(self, goc):
        self.goc = Path(goc)

    def thu_muc(self, nhan: str) -> Path:
        tap, _, ma = str(nhan).partition("/")
        for x in (tap, ma):
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", x or ""):
                raise ValueError(f"Nhãn cảnh '{nhan}' không dùng được làm thư mục.")
        return self.goc / "canh" / tap / ma

    def thong_tin(self, nhan: str) -> dict | None:
        p = self.thu_muc(nhan) / "tach.json"
        if not p.exists():
            return None
        j = json.loads(p.read_text(encoding="utf-8"))
        return {"co": j.get("co", []), "diem": j.get("diem"), "so_vat": len(j.get("vat", [])),
                "xem": str(self.thu_muc(nhan) / "xem.png"), "luc": j.get("luc")}

    def doc(self, nhan: str, bam: str):
        import numpy as np
        from PIL import Image

        from autoedit.collage.tach import KetQuaTach

        d = self.thu_muc(nhan)
        p = d / "tach.json"
        if not p.exists():
            return None
        j = json.loads(p.read_text(encoding="utf-8"))
        if j.get("bam") != bam:
            return None                                            # ảnh cảnh đã vẽ lại
        vat = [(np.asarray(Image.open(d / v["mask"])) > 127, float(v["z"])) for v in j["vat"]]
        nen = np.asarray(Image.open(d / "nen.png").convert("RGB"), np.float32) / 255
        return KetQuaTach(vat, nen, np.load(d / "z_nen.npy"), list(j.get("co", [])))

    def ghi(self, nhan: str, bam: str, kq, rgb, diem=None) -> None:
        import numpy as np
        from PIL import Image

        d = self.thu_muc(nhan)
        d.mkdir(parents=True, exist_ok=True)
        (d / "tach.json").unlink(missing_ok=True)                  # đang ghi dở = coi như chưa có
        vat = []
        for i, (m, z) in enumerate(kq.vat):
            Image.fromarray((np.asarray(m) * 255).astype(np.uint8)).save(d / f"vat_{i}.png")
            vat.append({"mask": f"vat_{i}.png", "z": float(z)})
        Image.fromarray((np.clip(kq.nen, 0, 1) * 255 + 0.5).astype(np.uint8)).save(d / "nen.png")
        np.save(d / "z_nen.npy", np.asarray(kq.z_nen, np.float32))
        # ảnh xem cho editor: vật tô màu trên ảnh gốc, cỡ nhỏ
        xem = np.asarray(rgb, np.float32).copy()
        for i, (m, _) in enumerate(kq.vat):
            xem[m] = xem[m] * 0.45 + np.float32(_MAU[i % len(_MAU)]) * 0.55
        im = Image.fromarray((np.clip(xem, 0, 1) * 255).astype(np.uint8))
        im.thumbnail((960, 960))
        im.save(d / "xem.png")
        (d / "tach.json").write_text(json.dumps(
            {"bam": bam, "vat": vat, "co": list(kq.co), "diem": diem, "luc": time.time()},
            ensure_ascii=False), encoding="utf-8")
