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
    # relocate theo DẢI HÌNH (08/09): mỗi MIẾNG hình một file — khoảng thở có
    # thể chứa nhiều miếng, miếng có thể trải qua nhiều khối voice
    from autoedit.offline import hinh as mhinh

    for i, k in enumerate(mhinh.dam_bao(hd)):
        ung = (k.get("uv") or [])
        thu_tu = ([ung[k["chon"]]] if 0 <= k.get("chon", -1) < len(ung) else []) + \
                 [u for j, u in enumerate(ung) if j != k.get("chon")]
        dat = None
        for u in thu_tu:
            cid = u["id"]
            nguon = cid.split(":")[0]
            c = _clip_db(conn, cid) or {}
            dich = assets / f"h{i:02d}_{sdb.slug(u.get('tieu_de', ''), 24)}{'.png' if nguon == 'aigen' else '.mp4'}"
            try:
                if nguon == "ref" and c.get("path_local"):
                    dem = 0.3
                    cat_clip(Path(c["path_local"]), max(0.0, float(c["t0"]) - 0),
                             min(float(c["t1"]) - float(c["t0"]) + dem, k["dur"] + 2.0),
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
                    sach = c.get("path_local") or ""
                    if sach and Path(sach).is_file():
                        # BẢN SẠCH đã tải (online) — cắt đoạn dùng cho nhẹ assets
                        t0s = float(c.get("t0") or 0)
                        dai = (float(c.get("t1") or 0) - t0s) if float(c.get("t1") or 0) > t0s                             else k["dur"] + 2.0
                        cat_clip(Path(sach), t0s, dai + 0.3, dich)
                    else:
                        if not c.get("url_video"):
                            raise RuntimeError("thiếu preview")
                        _tai(c["url_video"], dich)       # preview watermark TẠM
                        warns.append(f"miếng {i + 1}: Envato preview WATERMARK — "
                                     "phiên Envato sống rồi bấm Online lại là sạch")
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
            warns.append(f"miếng {i + 1}: KHÔNG lấy được nguồn nào — timeline hở, editor đắp")
        else:
            ra[i] = dat
        log(f"thay-mau: miếng {i + 1}/{len(mhinh.dam_bao(hd))} -> {dat.name if dat else 'HỞ'}")
    return ra, dung_id, warns


def _cat_voice(project_dir: Path, hd: dict, log) -> dict[int, Path]:
    """Cắt master theo DẢI KHỐI (voice), index = khối — độc lập dải hình."""
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


def _tai_nhac(project_dir: Path, hd: dict, log) -> Path | None:
    """Preview 128kbps của track đã chọn -> assets_offline/. Bản sạch thay sau
    khi có tài khoản Epidemic trong két (đúng khuôn Envato preview/bản sạch)."""
    n = hd.get("nhac") or {}
    url = n.get("url_nghe") or ""
    if not url:
        return None
    f = project_dir / "assets_offline" / f"nhac_{(n.get('id') or 'x').split(':')[-1]}.mp3"
    if f.is_file() and f.stat().st_size > 0:
        return f
    try:
        import urllib.request

        f.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        f.write_bytes(urllib.request.urlopen(req, timeout=120).read())
        log(f"thay-mau: nhạc «{n.get('tieu_de')}» {f.stat().st_size // 1024}KB")
        return f
    except Exception as exc:  # noqa: BLE001 — nhạc hỏng KHÔNG giết draft
        log(f"thay-mau: tải nhạc LỖI ({str(exc)[:80]}) — draft không nhạc")
        return None


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

    from autoedit.offline import hinh as mhinh

    # ---- TRACK VIDEO: theo DẢI HÌNH (miếng cắt tự do, 08/09) ----
    # KHÍT MÉP microsecond: t0 của miếng sau = HẾT của miếng trước. Làm tròn
    # từng miếng riêng lẻ sinh chồng lấn 10ms -> pycapcut SegmentOverlap
    # (bắt thật 08/09 khi chẻ 2 miếng vào khoảng thở 8.5s).
    ds_hinh = mhinh.dam_bao(hd)
    mep_us = [round(ds_hinh[0]["t0"] * SEC)] if ds_hinh else []
    for h in ds_hinh:
        mep_us.append(mep_us[-1] + round(h["dur"] * SEC))
    for i, h in enumerate(ds_hinh):
        f = video.get(i)
        if f is None:
            continue
        t0_us, dai_us = mep_us[i], mep_us[i + 1] - mep_us[i]
        m = VideoMaterial(str(f))
        if f.suffix.lower() == ".png":                 # ảnh AI -> tĩnh
            script.add_segment(VideoSegment(m, Timerange(t0_us, dai_us),
                                            source_timerange=Timerange(0, dai_us)),
                               "video_l1")
            continue
        avail = m.duration - SAFETY_US
        if avail >= round(dai_us * SPEED):
            script.add_segment(VideoSegment(m, Timerange(t0_us, dai_us), speed=SPEED),
                               "video_l1")
        else:
            toc = avail / dai_us
            if toc < SPEED_MIN and (dai_us - round(avail / SPEED)) >= SEC // 2:
                dv = round(avail / SPEED)              # sàn 0.8: 0.9x + freeze
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

    # ---- TRACK VOICE: theo DẢI KHỐI, mốc timeline riêng (bất biến) ----
    for i, (t0, t1, _tt) in enumerate(mhinh.moc_timeline(hd["khoi"])):
        vf = voice.get(i)
        if vf is None:
            continue
        k = hd["khoi"][i]
        tho_that = max(0.0, (k.get("tho") or 0) + min(0.0, k.get("tho_them") or 0))
        am = AudioMaterial(str(vf))
        script.add_segment(AudioSegment(
            am, Timerange(round(t0 * SEC),
                          min(am.duration - SAFETY_US,
                              round(((t1 - t0) + tho_that) * SEC)))), "voice")

    # ---- TRACK NHẠC (user chốt 06/09): ducking theo voice + fade chương ----
    nhac_f = _tai_nhac(project_dir, hd, log)
    if nhac_f is not None:
        from autoedit.offline.nhac_mix import (FADE_RA_S, FADE_VAO_S, cat_lap,
                                               duong_am_luong)

        script.add_track(TrackType.audio, "nhac")
        nm = AudioMaterial(str(nhac_f))
        dai_nhac = nm.duration / SEC
        tong = mhinh.tong_dai(hd["khoi"])
        kf = duong_am_luong(hd["khoi"])
        mieng_nhac = cat_lap(dai_nhac, tong)
        for j, (bat_dau, dai) in enumerate(mieng_nhac):
            seg = AudioSegment(nm, Timerange(round(bat_dau * SEC), round(dai * SEC)),
                               source_timerange=Timerange(0, round(dai * SEC)),
                               volume=1.0)
            # keyframe ducking RƠI TRONG miếng này (mốc tương đối theo miếng)
            for t, v in kf:
                if bat_dau - 0.01 <= t <= bat_dau + dai + 0.01:
                    seg.add_keyframe(max(0, round((t - bat_dau) * SEC)), v)
            # fade chương chỉ ở miếng ĐẦU (vào) và miếng CUỐI (ra)
            vao = round(FADE_VAO_S * SEC) if j == 0 else 0
            ra_ = round(FADE_RA_S * SEC) if j == len(mieng_nhac) - 1 else 0
            if vao or ra_:
                seg.add_fade(vao, ra_)
            script.add_segment(seg, "nhac")
        log(f"thay-mau: nhạc {len(mieng_nhac)} miếng · {len(kf)} keyframe ducking")

    # overwrite: thay máu là thao tác LẶP LẠI theo thiết kế (sửa đường dây ->
    # thay máu lại) — draft cùng tên phải được đè, không bắt user xoá tay
    draft = package_draft(json.loads(script.dumps()), ten_draft, profile, overwrite=True)
    # (6) user chốt 06/09: "team copy folder về máy cá nhân — source và license
    # nằm trong đó". Media đã tự chứa trong materials/ (placeholder tương đối);
    # ghi thêm GIAY_PHEP.txt: mỗi clip Envato dùng trong tập — item URL, file,
    # ngày license — đối soát được với My Downloads.
    try:
        from autoedit.sotra import db as _sdb2

        c2 = _sdb2.mo()
        try:
            dong = ["clip_id	url_item	ten_file	ngay"]
            thay = set()
            for i in dung_id.values() if isinstance(dung_id, dict) else []:
                u = str(i)
                if not u.startswith("envato:") or u in thay:
                    continue
                thay.add(u)
                goc = u.split("#")[0]
                r = c2.execute(
                    "SELECT url_item, ten_file, ngay FROM giay_phep "
                    "WHERE clip_id=? ORDER BY gp DESC LIMIT 1", (goc,)).fetchone()
                if r:
                    dong.append(f"{u}	{r['url_item']}	{r['ten_file']}	{r['ngay']}")
                else:
                    dong.append(f"{u}	(chưa có bản licensed — đang dùng preview)		")
            if len(dong) > 1:
                (Path(draft) / "GIAY_PHEP.txt").write_text(
                    "\n".join(dong), encoding="utf-8")
                log(f"online: GIAY_PHEP.txt — {len(dong) - 1} clip Envato")
        finally:
            c2.close()
    except Exception as exc:  # noqa: BLE001 — sổ hỏng không giết draft
        log(f"online: ghi GIAY_PHEP lỗi ({str(exc)[:70]})")
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
        # BẢN ONLINE (user chốt 06/09 — thuật ngữ dựng phim: offline duyệt xong
        # thì conform bản online với media sạch): tải bản sạch Envato cho các
        # shot ĐANG CHỌN trước khi ráp. Fail-open — thiếu phiên/hỏng clip nào
        # thì clip đó dùng preview, draft vẫn ra.
        try:
            from autoedit.offline import hinh as _mh
            from autoedit.sourcer import tai_sach

            can = [h["uv"][h["chon"]]["id"] for h in _mh.dam_bao(hd)
                   if 0 <= h.get("chon", -1) < len(h.get("uv") or [])
                   and h["uv"][h["chon"]].get("nguon") == "envato"]
            if can:
                ghi(f"online: {len(set(tai_sach._uuid_goc(x) for x in can))} clip "
                    "Envato cần bản sạch — tải 1 luồng giãn 2-5s")
                tai_sach.tai_nhieu(c, can, log=ghi)
        except Exception as exc:  # noqa: BLE001
            ghi(f"online: tải bản sạch LỖI ({str(exc)[:80]}) — dùng preview")
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
    from autoedit.offline import hinh as _mh
    kq = {"draft": str(draft), "mieng_co_hinh": len(video),
          "tong_mieng": len(_mh.dam_bao(hd)), "tong_khoi_voice": len(hd["khoi"]),
          "canh_bao": warns}
    (project_dir / "thay_mau.json").write_text(
        json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    return kq
