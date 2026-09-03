r"""Sau khi editor CHỐT phiên duyệt: gen video -> vào timeline -> dựng lại.

Chuỗi (user chốt 03/09 — tiền video chỉ đốt SAU cổng duyệt):
  1. Mỗi motif có ảnh chốt -> Seedance i2v (720p, 5s) -> projects/<id>/aigen/<ma>.mp4
  2. TÁI DÙNG: mỗi beat trong motif.beat_ids nhận MỘT BẢN SAO clip vào assets/
     (tên theo khuôn b{beat}_..., sổ nguồn nhóm aigen) — giãn cách ≥60s do
     director gán beat_ids lo từ trước, đây chỉ thi hành.
  3. Đặt lại stage assemble+report -> pending, chạy `run` để dựng lại draft —
     đúng khuôn "rerun music+assemble" đã dùng cho DS3-084 (14/07), không đường mới.

Chạy BLOCKING — caller tự bọc thread. Lỗi giữa chừng: phiên ghi trạng thái +
loi, KHÔNG ném lên (job dựng cũ vẫn nguyên, editor còn draft slug để làm tay).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from autoedit.aigen.client import ArkClient
from autoedit.aigen.duyet import THU_MUC_ANH, PhienDuyet

GIAY_CLIP = 5
DUOI_PROMPT = " --resolution 720p --duration 5"


def chay_sau_chot(project_dir: Path, log=None) -> str:
    """Trả thông điệp kết quả (cũng ghi vào phiên). log = callable(str) tuỳ chọn."""
    def ghi_log(msg: str) -> None:
        if log:
            log(msg)

    pdir = Path(project_dir)
    phien = PhienDuyet.doc(pdir)
    if phien is None or phien.trang_thai != "da_chot":
        return "phiên chưa ở trạng thái da_chot — bỏ qua"

    c = ArkClient()
    anh_dir = pdir / THU_MUC_ANH
    clips: dict[str, Path] = {}
    for m in phien.motif:
        chot = m.anh_chot
        if chot is None:
            continue          # editor loại motif -> beat giữ slug, làm tay
        ghi_log(f"aigen: gen video motif {m.ma} từ {chot.file}...")
        tid = c.gen_video_i2v(m.prompt + DUOI_PROMPT, anh_dir / chot.file,
                              giay=GIAY_CLIP)
        clips[m.ma] = c.cho_video(tid, anh_dir / f"{m.ma}.mp4")
        ghi_log(f"aigen: motif {m.ma} xong ({clips[m.ma].stat().st_size // 1024} KB)")

    if not clips:
        phien.trang_thai = "da_gen_video"
        phien.ghi(pdir)
        return "không motif nào có ảnh chốt — không gen gì"

    # ---- vào shots: mỗi beat của motif nhận một bản sao clip ----
    pj = pdir / "project.json"
    d = json.loads(pj.read_text(encoding="utf-8"))
    assets = pdir / "assets"
    assets.mkdir(exist_ok=True)
    shots_theo_beat = {s.get("beat_id"): s for s in d.get("shots", [])}
    thay = 0
    for m in phien.motif:
        clip = clips.get(m.ma)
        if clip is None:
            continue
        for bid in m.beat_ids:
            dich = assets / f"b{bid:03d}_aigen-{m.ma}{clip.suffix}"
            shutil.copy2(clip, dich)
            s = shots_theo_beat.get(bid)
            duong = str(dich.relative_to(pdir))
            if s is None:
                d.setdefault("shots", []).append({
                    "beat_id": bid, "asset_path": duong,
                    "asset_key": f"aigen:{m.ma}", "status": "ok",
                    "source": "aigen", "note": f"AI gen — motif {m.ma}"})
            else:
                s["asset_path"] = duong
                s["asset_key"] = f"aigen:{m.ma}"
                s["status"] = "ok"
                s["source"] = "aigen"
                s["note"] = f"AI gen — motif {m.ma} (thay {s.get('note', '')[:40]})"
            thay += 1

    # ---- đặt lại assemble/report -> dựng lại draft (khuôn rerun DS3-084) ----
    for st in ("assemble", "report"):
        if st in d.get("stages", {}):
            d["stages"][st]["status"] = "pending"
            d["stages"][st]["error"] = None
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    ghi_log("aigen: dựng lại assemble...")
    r = subprocess.run(
        [sys.executable, "-m", "autoedit.cli", "run", str(pdir)],
        cwd=str(Path(__file__).resolve().parents[2]),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=1800,
        env={**__import__("os").environ,
             "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
             "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    if r.returncode != 0:
        msg = f"gen video OK ({len(clips)} clip, {thay} beat) nhưng dựng lại LỖI: {r.stdout[-300:]}"
        phien.trang_thai = "da_gen_video"
        phien.ghi(pdir)
        return msg

    phien.trang_thai = "da_gen_video"
    phien.ghi(pdir)
    return (f"xong: {len(clips)} clip Seedance, {thay} vị trí beat, "
            f"draft đã dựng lại — mở CapCut xem bản mới")
