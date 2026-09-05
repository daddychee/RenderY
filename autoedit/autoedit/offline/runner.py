r"""Chạy PHÂN TÍCH Offline cho 1 project (chương) -> `offline.json`.

Chuỗi: voice master + transcript (align sẵn) -> cắt khối theo hơi thở
(khoi.py) -> gán 4 lớp (lop4.py, GLM tiêm được) -> chia đồng kiểm/auto theo
AVD -> đổ ứng viên Library + chọn mặc định (dung.py) -> offline.json.

Fail-open từng tầng phụ: GLM chết -> khối trừu tượng (người vẫn duyệt pha 1);
Library rỗng -> ứng viên rỗng (khay trống, hút thêm sau). Ranh khối là tầng
CỨNG duy nhất — hỏng là báo lỗi thẳng, không đoán.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from autoedit.offline import dung, khoi as mkhoi, lop4

TEN_HOP_DONG = "offline.json"


def _words(project_dir: Path) -> list[dict]:
    d = json.loads((project_dir / "transcript.json").read_text(encoding="utf-8"))
    if isinstance(d, dict):
        d = d.get("words") or d.get("transcript") or []
    return d


def _framing(kenh_ref: str) -> dict:
    """Hồ sơ Framing (bộ outlier/kênh) — thiếu thì số 0, khối không gợi ý chẻ."""
    if not kenh_ref:
        return {}
    try:
        from autoedit.kenh.do_kenh import slug_tu_link
        from autoedit.kenh.hoso import HoSoKenh

        hs = HoSoKenh.doc(slug_tu_link(kenh_ref))
        if hs is None:
            return {}
        return {"ten": hs.ten, "than": hs.than_trung_vi, "hold": hs.than_ty_le_hold,
                "hook": hs.hook_trung_vi}
    except Exception:  # noqa: BLE001
        return {}


def phan_tich(project_dir: Path, avd_s: float = 0.0, mo_dau_tap_s: float = 0.0,
              kenh_ref: str = "", uu_tien_nguon: str = "", dia_danh: str = "",
              llm=None, conn=None, log=None) -> dict:
    """Sinh offline.json. `avd_s`: mốc AVD của TẬP; `mo_dau_tap_s`: chương này
    bắt đầu ở giây bao nhiêu của tập (đồng kiểm nếu chương CHẠM mốc AVD).
    `llm`/`conn` tiêm được để test không mạng."""
    def ghi(m):
        if log:
            log(m)

    project_dir = Path(project_dir)
    master = project_dir / "media" / "voice_master.wav"
    if not master.is_file():
        raise RuntimeError("thiếu media/voice_master.wav — chạy align/cut trước")
    words = _words(project_dir)
    if not words:
        raise RuntimeError("transcript rỗng — chạy align trước")

    from autoedit.cutter import silence as sil
    from autoedit.project import ffprobe_duration

    het = ffprobe_duration(master) or max(w.get("end", 0) for w in words)
    fr = _framing(kenh_ref)
    silences = sil.detect_silences(master)
    ds_khoi, offset = mkhoi.cat_khoi(silences, words, het,
                                     than_framing=float(fr.get("than") or 0))
    ghi(f"offline: {len(ds_khoi)} khối theo hơi thở · offset {offset}s")

    # 4 lớp — fail-open
    try:
        lo = lop4.gan_lop([k.loi for k in ds_khoi], dia_danh=dia_danh, llm=llm)
        chu_the = lo.chu_the_tap
        lop_ds = lo.khoi
    except Exception as exc:  # noqa: BLE001
        ghi(f"offline: 4 lớp LỖI ({str(exc)[:90]}) — khối trừu tượng, duyệt pha 1 vẫn chạy")
        chu_the = []
        lop_ds = [lop4.LopKhoi(khoi=i, truu_tuong=True) for i in range(len(ds_khoi))]

    # đồng kiểm theo AVD: chương thuộc đồng kiểm nếu BẮT ĐẦU trước mốc AVD
    dong_kiem = (avd_s <= 0) or (mo_dau_tap_s < avd_s)

    # ứng viên Library — fail-open
    ung_vien: list[list[dict]] = [[] for _ in ds_khoi]
    chon = [-1] * len(ds_khoi)
    try:
        from autoedit.sotra import db as sdb

        c = conn or sdb.mo()
        try:
            ung_vien = dung.do_ung_vien(c, ds_khoi, lop_ds, chu_the,
                                        uu_tien_nguon=uu_tien_nguon)
            chon = dung.chon_mac_dinh(ds_khoi, ung_vien)
        finally:
            if conn is None:
                c.close()
    except Exception as exc:  # noqa: BLE001
        ghi(f"offline: Library LỖI ({str(exc)[:90]}) — khay trống, hút thêm sau")

    lap = dung.kiem_lap(ds_khoi, ung_vien, chon)
    hd = {
        "phien_ban": 1,
        "ngay": datetime.now(timezone.utc).isoformat(),
        "offset": offset, "tong_voice": round(het - offset, 2),
        "avd_s": avd_s, "dong_kiem": dong_kiem,
        "framing": fr, "uu_tien_nguon": uu_tien_nguon,
        "chu_the_tap": chu_the,
        "trang_thai": "pha1",
        "khoi": [{
            **asdict(k),
            "L1": lop_ds[i].truc_chi, "L2": lop_ds[i].ngu_canh,
            "L3": lop_ds[i].khong_khi, "neo": lop_ds[i].neo,
            "mood": lop_ds[i].mood, "truu_tuong": lop_ds[i].truu_tuong,
            "uv": ung_vien[i], "chon": chon[i],
            "khoa": False, "nguoi_sua": False,
        } for i, k in enumerate(ds_khoi)],
        "canh_bao": ([f"{len(lap)} khối vi phạm luật 60s"] if lap else []),
    }
    (project_dir / TEN_HOP_DONG).write_text(
        json.dumps(hd, ensure_ascii=False, indent=1), encoding="utf-8")
    ghi(f"offline: hợp đồng ghi xong — {len(ds_khoi)} khối · "
        f"{'ĐỒNG KIỂM' if dong_kiem else 'AUTO'} · {len(lap)} lỗi lặp")
    return hd


def doc(project_dir: Path) -> dict | None:
    f = Path(project_dir) / TEN_HOP_DONG
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None


def luu(project_dir: Path, hd: dict) -> None:
    """Màn Offline PUT bản người chỉnh — ghi đè nguyên hợp đồng (server validate)."""
    (Path(project_dir) / TEN_HOP_DONG).write_text(
        json.dumps(hd, ensure_ascii=False, indent=1), encoding="utf-8")


def xuat_kiem_mp4(project_dir: Path, dich: Path, dai_s: float = 15.0) -> Path:
    """MP4 kiểm ranh: timeline khối + playhead NUNG vào hình (audio+hình chung
    container -> sync tuyệt đối, miễn nhiễm trễ Remote Desktop — 06/09)."""
    import subprocess
    import tempfile

    from PIL import Image, ImageDraw, ImageFont

    hd = doc(project_dir)
    if hd is None:
        raise RuntimeError("chưa có offline.json — chạy phân tích trước")
    OFF, PXS, H = hd["offset"], 120, 480
    W = int(dai_s * PXS)
    im = Image.new("RGB", (W, H), (15, 18, 22))
    dr = ImageDraw.Draw(im)
    try:
        f_to = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 34)
        f_nho = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
    except Exception:  # noqa: BLE001
        f_to = f_nho = ImageFont.load_default()
    y0, y1 = 140, 360
    for i, k in enumerate(hd["khoi"]):
        if k["v0"] > dai_s:
            break
        dr.rounded_rectangle([k["v0"] * PXS + 2, y0, min(k["v1"], dai_s) * PXS - 2, y1],
                             10, fill=(34, 48, 63), outline=(51, 71, 92), width=2)
        dr.text((k["v0"] * PXS + 14, y0 + 12), f"{i + 1:02d}", font=f_to,
                fill=(233, 236, 239))
        nghi = k["tho"] + max(0.0, k["tho_them"])
        if nghi > 0.05 and k["v1"] < dai_s:
            ta, tb = k["v1"] * PXS, min(k["v1"] + nghi, dai_s) * PXS
            dr.rounded_rectangle([ta + 2, y0, tb - 2, y1], 10,
                                 fill=(233, 236, 239), outline=(180, 190, 200), width=2)
            dr.text(((ta + tb) / 2 - 30, (y0 + y1) / 2 - 14), f"THỞ {nghi:.1f}s",
                    font=f_nho, fill=(30, 36, 44))
    tmp = Path(tempfile.mkdtemp(prefix="kiem_"))
    strip, ph = tmp / "s.png", tmp / "p.png"
    im.save(strip)
    Image.new("RGBA", (6, H), (221, 80, 60, 255)).save(ph)
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(strip),
        "-loop", "1", "-i", str(ph),
        "-ss", f"{OFF:.2f}", "-t", f"{dai_s:.2f}",
        "-i", str(Path(project_dir) / "media" / "voice_master.wav"),
        "-filter_complex", f"[0][1]overlay=x='t*{PXS}':y=0,scale=1280:-2,format=yuv420p[v]",
        "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-t", f"{dai_s:.2f}", str(dich)],
        check=True, timeout=300)
    return dich
