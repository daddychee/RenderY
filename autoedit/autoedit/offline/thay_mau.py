r"""THAY MÁU — thi hành offline.json ĐÃ KHÓA SỔ thành draft CapCut (Đợt 5).

Preview -> bản thật, truy ngược mọi thứ qua ID CHÍNH TẮC trong Library:
  ref:*    -> cắt từ file NAS theo t0/t1 (+đệm cắt sạch), KHÔNG tải gì
  kho:*    -> copy file local đã có
  pexels/pixabay:* -> API chính thức trả file gốc (key sẵn), tải rón rén
  aigen:*  -> ảnh đã chốt -> i2v Seedance 5s (đắt, CHỈ chạy ở đây); i2v lỗi
              -> dùng ảnh + Ken Burns (fail-open)
  envato:* -> cần tài khoản trong két (user sẽ đưa) — chưa có: rơi về ứng viên
              DỰ BỊ non-envato của khối; hết dự bị -> preview watermark TẠM +
              warning to (editor thay khi có két; timeline không bao giờ hở)

Voice: cắt master theo từng khối (offset+v0 .. v1+thở), đặt lên timeline với
gap = tho_them (im lặng THẬT — đúng định nghĩa +/-1s). Video: sàn tốc độ 0.8
+ freeze khung cuối (luật 05/09). Sản phẩm là DRAFT CAPCUT — không render MP4.
"""

from __future__ import annotations

import json
import os
import random
import subprocess
import time
import urllib.request
from pathlib import Path

from autoedit.offline import runner as orun

SEC = 1_000_000
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://elements.envato.com/"}
GIAN_NHIP = (2.0, 4.0)
SPEED = 0.9
SPEED_MIN = 0.8


def _tai(url: str, dich: Path, timeout: float = 300.0) -> Path:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        dich.write_bytes(r.read())
    return dich


def _clip_db(conn, cid: str) -> dict | None:
    r = conn.execute("SELECT * FROM clip WHERE id=?", (cid,)).fetchone()
    return dict(r) if r else None


def _pexels_goc(cid: str) -> str:
    """API Pexels trả link file gốc 1080p+ (không watermark, key sẵn)."""
    key = os.getenv("PEXELS_API_KEY", "").strip()
    vid = cid.split(":")[1]
    req = urllib.request.Request(f"https://api.pexels.com/videos/videos/{vid}",
                                headers={"Authorization": key})
    d = json.loads(urllib.request.urlopen(req, timeout=60).read())
    files = sorted((f for f in d.get("video_files", []) if f.get("height")),
                   key=lambda f: -f["height"])
    hd = next((f for f in files if f["height"] <= 1440), files[0] if files else None)
    return (hd or {}).get("link", "")


def _pixabay_goc(cid: str) -> str:
    key = os.getenv("PIXABAY_API_KEY", "").strip()
    vid = cid.split(":")[1]
    d = json.loads(urllib.request.urlopen(
        f"https://pixabay.com/api/videos/?key={key}&id={vid}", timeout=60).read())
    hits = d.get("hits") or [{}]
    vids = hits[0].get("videos", {})
    return (vids.get("large") or vids.get("medium") or {}).get("url", "")


def _i2v(client, anh: Path, prompt: str, dich: Path, log) -> Path | None:
    """Seedance image-to-video 5s — đắt, chỉ chạy cho ảnh ĐÃ CHỐT."""
    try:
        task = client.gen_video_i2v(prompt, anh, giay=5)
        return client.cho_video(task, dich)
    except Exception as exc:  # noqa: BLE001 — fail-open về ảnh + Ken Burns
        log(f"thay-mau: i2v LỖI ({str(exc)[:80]}) — dùng ảnh + Ken Burns")
        return None


def relocate(project_dir: Path, hd: dict, conn, log, ark=None) -> tuple[dict, list[str]]:
    """Mỗi khối -> file thật trong assets_offline/. Trả (map khối->path, warnings)."""
    from autoedit.sotra import db as sdb
    from autoedit.sourcer.refvideo import cat_clip

    assets = project_dir / "assets_offline"
    assets.mkdir(exist_ok=True)
    ra: dict[int, Path] = {}
    dung_id: dict[int, str] = {}          # clip THẬT được dùng (dự bị tính là nó)
    warns: list[str] = []
    for i, k in enumerate(hd["khoi"]):
        ung = (k.get("uv") or [])
        thu_tu = ([ung[k["chon"]]] if 0 <= k.get("chon", -1) < len(ung) else []) + \
                 [u for j, u in enumerate(ung) if j != k.get("chon")]
        dat = None
        for u in thu_tu:
            cid = u["id"]
            nguon = cid.split(":")[0]
            c = _clip_db(conn, cid) or {}
            dich = assets / f"k{i:02d}_{sdb.slug(u.get('tieu_de', ''), 24)}{'.png' if nguon == 'aigen' else '.mp4'}"
            try:
                if nguon == "ref" and c.get("path_local"):
                    dem = 0.3
                    cat_clip(Path(c["path_local"]), max(0.0, float(c["t0"]) - 0),
                             min(float(c["t1"]) - float(c["t0"]) + dem,
                                 (k["v1"] - k["v0"]) + (k.get("tho") or 0) + 2.0),
                             dich)
                elif nguon == "kho" and c.get("path_local") and Path(c["path_local"]).is_file():
                    import shutil
                    shutil.copy2(c["path_local"], dich)
                elif nguon == "aigen" and c.get("path_local"):
                    anh = Path(c["path_local"])
                    if ark is not None:
                        v = _i2v(ark, anh, u.get("tieu_de", ""), dich.with_suffix(".mp4"), log)
                        if v is not None:
                            dat = v
                            dung_id[i] = cid
                            break
                    import shutil
                    shutil.copy2(anh, dich)          # ảnh -> Ken Burns lo phần động
                elif nguon == "pexels":
                    url = _pexels_goc(cid)
                    if not url:
                        raise RuntimeError("API không trả file gốc")
                    _tai(url, dich)
                    time.sleep(random.uniform(*GIAN_NHIP))
                elif nguon == "pixabay":
                    url = _pixabay_goc(cid)
                    if not url:
                        raise RuntimeError("API không trả file gốc")
                    _tai(url, dich)
                    time.sleep(random.uniform(*GIAN_NHIP))
                elif nguon == "envato":
                    # CHỜ KÉT (user đưa tài khoản sau): thử dự bị trước đã
                    if any(x["id"].split(":")[0] != "envato" for x in thu_tu):
                        raise RuntimeError("chờ két Envato — thử dự bị")
                    if not c.get("url_video"):
                        raise RuntimeError("thiếu preview")
                    _tai(c["url_video"], dich)       # preview watermark TẠM
                    warns.append(f"khối {i + 1}: Envato preview WATERMARK tạm — "
                                 "thay bản sạch khi có két")
                    time.sleep(random.uniform(*GIAN_NHIP))
                else:
                    raise RuntimeError("nguồn không có đường lấy")
                if dich.is_file() and dich.stat().st_size > 5_000:
                    dat = dich
                    dung_id[i] = cid
                    break
                raise RuntimeError("file rỗng")
            except Exception as exc:  # noqa: BLE001 — thử ứng viên kế
                log(f"thay-mau: khối {i + 1} «{cid[:40]}» {str(exc)[:70]} — thử dự bị")
                if "không tồn tại" in str(exc) or "file rỗng" in str(exc):
                    conn.execute("UPDATE clip SET trang_thai='link_chet' WHERE id=?", (cid,))
                continue
        if dat is None:
            warns.append(f"khối {i + 1}: KHÔNG lấy được nguồn nào — timeline hở, editor đắp")
        else:
            ra[i] = dat
        log(f"thay-mau: khối {i + 1}/{len(hd['khoi'])} -> {dat.name if dat else 'HỞ'}")
    return ra, dung_id, warns


def _cat_voice(project_dir: Path, hd: dict, log) -> dict[int, Path]:
    """Cắt master theo khối (offset+v0 .. v1+thở tự nhiên) — lời + ngắt gốc."""
    ra = {}
    seg_dir = project_dir / "assets_offline"
    off = hd["offset"]
    for i, k in enumerate(hd["khoi"]):
        f = seg_dir / f"voice_k{i:02d}.wav"
        dai = (k["v1"] - k["v0"]) + max(0.0, (k.get("tho") or 0) + min(0.0, k.get("tho_them") or 0))
        r = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{off + k['v0']:.3f}",
             "-t", f"{max(dai, 0.3):.3f}",
             "-i", str(project_dir / "media" / "voice_master.wav"), str(f)],
            capture_output=True, timeout=120)
        if r.returncode == 0 and f.is_file():
            ra[i] = f
    log(f"thay-mau: cắt {len(ra)} voice segment")
    return ra


def dung_draft(project_dir: Path, hd: dict, video: dict, voice: dict,
               ten_draft: str, profile, log) -> Path:
    """Ráp draft CapCut: video sàn 0.8 + freeze; voice đặt gap = tho_them dương."""
    from pycapcut import (AudioMaterial, AudioSegment, ScriptFile, Timerange,
                          TrackType, VideoMaterial, VideoSegment)

    from autoedit.packager.assembler import SAFETY_US, _freeze_frame
    from autoedit.packager.packager import package_draft
    from autoedit.project import ffprobe_duration

    script = ScriptFile(1920, 1080, fps=30)
    script.add_track(TrackType.video, "video_l1")
    script.add_track(TrackType.audio, "voice")

    cursor = 0.0
    for i, k in enumerate(hd["khoi"]):
        noi = k["v1"] - k["v0"]
        tho = max(0.0, (k.get("tho") or 0) + min(0.0, k.get("tho_them") or 0))
        them = max(0.0, k.get("tho_them") or 0)
        o_dai = noi + tho + them                       # hình phủ TRỌN cả thở
        t0_us, dai_us = round(cursor * SEC), round(o_dai * SEC)
        f = video.get(i)
        if f is not None:
            if f.suffix.lower() == ".png":             # ảnh AI -> tĩnh (Ken Burns đợt sau)
                m = VideoMaterial(str(f))
                script.add_segment(VideoSegment(m, Timerange(t0_us, dai_us),
                                                source_timerange=Timerange(0, dai_us)),
                                   "video_l1")
            else:
                m = VideoMaterial(str(f))
                avail = m.duration - SAFETY_US
                if avail >= round(dai_us * SPEED):
                    script.add_segment(VideoSegment(m, Timerange(t0_us, dai_us), speed=SPEED),
                                       "video_l1")
                else:
                    toc = avail / dai_us
                    if toc < SPEED_MIN and (dai_us - round(avail / SPEED)) >= SEC // 2:
                        dv = round(avail / SPEED)      # sàn 0.8: chạy 0.9x + freeze
                        script.add_segment(VideoSegment(m, Timerange(t0_us, dv), speed=SPEED),
                                           "video_l1")
                        fz = _freeze_frame(f, f.parent)
                        if fz is not None:
                            script.add_segment(VideoSegment(
                                VideoMaterial(str(fz)), Timerange(t0_us + dv, dai_us - dv),
                                source_timerange=Timerange(0, dai_us - dv)), "video_l1")
                    else:
                        script.add_segment(VideoSegment(m, Timerange(t0_us, dai_us),
                                                        source_timerange=Timerange(0, avail),
                                                        speed=toc), "video_l1")
        vf = voice.get(i)
        if vf is not None:
            am = AudioMaterial(str(vf))
            script.add_segment(AudioSegment(
                am, Timerange(t0_us, min(am.duration - SAFETY_US,
                                         round((noi + tho) * SEC)))), "voice")
        cursor += o_dai
    draft = package_draft(json.loads(script.dumps()), ten_draft, profile)
    log(f"thay-mau: draft {draft}")
    return draft


def thay_mau(project_dir: Path, profile=None, conn=None, ark=None, log=None) -> dict:
    """Chạy trọn: relocate -> cắt voice -> draft CapCut. Chỉ chương KHÓA SỔ."""
    def ghi(m):
        if log:
            log(m)

    project_dir = Path(project_dir)
    hd = orun.doc(project_dir)
    if hd is None:
        raise RuntimeError("chưa có offline.json")
    if hd.get("trang_thai") != "khoa":
        raise RuntimeError("chương chưa KHÓA SỔ — duyệt xong bấm Khóa sổ trước")

    from autoedit.sotra import db as sdb

    c = conn or sdb.mo()
    try:
        video, dung_id, warns = relocate(project_dir, hd, c, ghi, ark=ark)
        # phản biện: ghi sổ theo clip THẬT được dùng (dự bị tính là dự bị —
        # test 07/09 bắt bug ghi nhầm theo clip 'được chọn' đã chết)
        for i, k in enumerate(hd["khoi"]):
            if i in dung_id:
                sdb.ghi_su_kien(c, dung_id[i], "len_final",
                                tap=project_dir.name, vi_tri=k["v0"])
        c.commit()
    finally:
        if conn is None:
            c.close()
    voice = _cat_voice(project_dir, hd, ghi)
    if profile is None:
        from autoedit.packager.machine import MachineProfile

        profile = MachineProfile.load()
    ten = f"OFF_{project_dir.name}"
    draft = dung_draft(project_dir, hd, video, voice, ten, profile, ghi)
    kq = {"draft": str(draft), "khoi_co_hinh": len(video),
          "tong_khoi": len(hd["khoi"]), "canh_bao": warns}
    (project_dir / "thay_mau.json").write_text(
        json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    return kq
