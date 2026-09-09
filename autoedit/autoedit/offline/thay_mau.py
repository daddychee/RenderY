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
import urllib.error
import urllib.request
from pathlib import Path

from autoedit.offline import runner as orun

SEC = 1_000_000
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://elements.envato.com/"}
GIAN_NHIP = (2.0, 4.0)
SPEED = 0.9
SPEED_MIN = 0.8

# Nguồn ĐÃ MẤT HẲN — đánh `link_chet` để khay không trồi nó lên nữa.
_MA_CHET = (404, 410)
# Hết lượt / nhà cung cấp trục trặc — clip VẪN SỐNG, đánh dấu là giết oan.
_MA_TAM = (408, 425, 429, 500, 502, 503, 504)
_CAU_CHET = ("file rỗng", "thiếu preview", "API không trả file gốc",
             "nguồn không có đường lấy")


def la_nguon_chet(exc: BaseException) -> bool:
    """Lỗi này có nghĩa clip MẤT HẲN không? (quyết định đánh `link_chet`).

    Bản cũ kiểm `"không tồn tại" in str(exc)` — KHÔNG luồng nào ném chuỗi đó,
    nên nhánh đánh dấu gần như không bao giờ chạy: preview Envato chết trả
    `HTTPError` với `str(exc)` = "HTTP Error 404: Not Found". Kết quả là clip
    chết cứ được chọn lại mỗi lần dựng.

    Nguyên tắc: THÀ BỎ SÓT CÒN HƠN GIẾT OAN. Repo không có đường gỡ cờ
    `link_chet` (grep: không chỗ nào set ngược về 'song'), nên chỉ đánh khi
    chắc chắn mất hẳn; 429/5xx/mạng đứt để nguyên (user chốt: fail 1 lần bỏ qua).
    """
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in _MA_CHET
    if isinstance(exc, (urllib.error.URLError, TimeoutError, OSError)):
        return False                      # mạng đứt: clip vẫn sống
    return any(c in str(exc) for c in _CAU_CHET)


def soat_truoc_pha(conn, hd: dict) -> list[dict]:
    """Miếng nào ĐANG CHỌN clip đã chết? Trả [{mieng, id, tieu_de}] để UI tô đỏ.

    User chốt 09/09: *"Sau khi ấn export timeline, tool check 1 lượt. Nếu không
    có link chết thì export. Nếu có thì báo đã có video hỏng."*

    Vì sao kiểm TRƯỚC: `thay_mau` vốn có đường lùi (hết ứng viên thì để hở, ghi
    warning), nhưng warning chỉ hiện SAU KHI ráp — người dựng chờ vài phút mới
    biết miếng của mình hỏng. Soát trước tốn chưa tới một giây (đọc DB, không
    chạm mạng) và chỉ đúng miếng cần thay.

    CHỈ soát miếng ĐANG CHỌN: dự bị hỏng không cản gì vì nó chỉ được dùng khi
    cái đang chọn hỏng — chặn vì dự bị là chặn oan.

    Fail-open: soát là bước phụ. DB khoá/hỏng thì cho Export chạy tiếp, đường
    lùi trong lúc ráp vẫn đỡ được — chặn oan tệ hơn bỏ sót.
    """
    from autoedit.offline import hinh as _mh

    try:
        from autoedit.offline.dung import clip_hong

        xau = []
        for i, h in enumerate(_mh.dam_bao(hd)):
            uv, c = h.get("uv") or [], h.get("chon", -1)
            if not (0 <= c < len(uv)):
                continue          # chưa chọn: việc của placeholder, không phải Export
            u = uv[c]
            # `tha_giu_cu=False`: mục đang chọn gần như luôn mang cờ `giu_cu`
            # (do `_thay` đặt lúc vá khay). Thả cờ ở đây là soát rỗng vĩnh viễn.
            if clip_hong(conn, u, tha_giu_cu=False):
                # DỪNG NGAY (user chốt 09/09): kết quả không đổi dù quét tiếp —
                # vẫn là "chặn", người dựng vẫn phải thay rồi bấm lại. Soi hết
                # 46 miếng chỉ tốn thời gian. Vẫn trả miếng tìm được để UI tô
                # đỏ và nhảy tới đúng chỗ.
                return [{"mieng": i, "id": u.get("id", ""),
                         "tieu_de": (u.get("tieu_de") or "")[:80]}]
        return xau
    except Exception as exc:  # noqa: BLE001 — soát hỏng KHÔNG được giết Export
        # In ra: fail-open câm là bẫy gỡ rối (mất 20 phút truy 09/09 vì lỗi
        # SQLite xuyên luồng bị nuốt sạch, endpoint cứ lặng lẽ cho qua).
        print(f"[soat-truoc-pha] bỏ qua vì lỗi: {type(exc).__name__}: {exc}", flush=True)
        return []


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

    truoc_file: Path | None = None      # asset của miếng liền trước
    truoc_dung = 0.0                     # đã tiêu bao nhiêu giây của asset đó
    truoc_id: str | None = None          # clip của miếng trước — miếng CHẢY TIẾP
    # dùng lại chính nó, sổ nguồn gốc phải ghi tên nó chứ không bỏ trống
    for i, k in enumerate(mhinh.dam_bao(hd)):
        # ---- MIẾNG CHẢY TIẾP (3b): cắt TIẾP asset của miếng trước, đúng chỗ nó
        # dừng. Nếu cắt lại từ giây 0 thì người xem thấy hình NHẢY VỀ ĐẦU —
        # còn xấu hơn cắt sang clip khác.
        if k.get("noi_tiep"):
            if con_du_nguon(truoc_file, truoc_dung, k["dur"]):
                dich = assets / f"h{i:02d}_noi.mp4"
                try:
                    cat_clip(truoc_file, truoc_dung, k["dur"] + 0.3, dich)
                    if dich.is_file() and dich.stat().st_size > 5_000:
                        ra[i] = dich
                        if truoc_id:
                            dung_id[i] = truoc_id
                        truoc_dung += k["dur"] * SPEED
                        log(f"thay-mau: miếng {i + 1} chảy tiếp «{truoc_file.name[:28]}»"
                            f" từ {truoc_dung - k['dur'] * SPEED:.1f}s")
                        continue
                except Exception as exc:  # noqa: BLE001 — hụt thì chọn clip riêng
                    log(f"thay-mau: miếng {i + 1} chảy tiếp lỗi ({str(exc)[:60]})")
            else:
                log(f"thay-mau: miếng {i + 1} nguồn cạn — chuyển sang clip riêng")
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
                if la_nguon_chet(exc):
                    conn.execute("UPDATE clip SET trang_thai='link_chet' WHERE id=?", (cid,))
                    conn.commit()      # commit TẠI CHỖ: khâu sau ném lỗi thì
                    #                    dấu đã đánh vẫn còn, không phải dò lại
                continue
        if dat is None:
            # Link để in lên ô giữ chỗ: ưu tiên clip ĐANG CHỌN — đó là clip
            # người dựng đã duyệt, tải tay bản đó mới đúng ý. Khay rỗng (ca c8
            # thật) thì không có link nào, ô in lời dặn chung.
            u0 = thu_tu[0] if thu_tu else None
            if u0:
                cr = _clip_db(conn, u0["id"]) or {}
                k["ho_link"] = cr.get("url_trang") or cr.get("url_video") or ""
                k["ho_ten"] = u0.get("tieu_de") or ""
            warns.append(f"miếng {i + 1}: KHÔNG lấy được nguồn nào — ô giữ chỗ"
                         + (" kèm link tải tay" if k.get("ho_link") else ""))
        else:
            ra[i] = dat
            truoc_file, truoc_dung = dat, k["dur"] * SPEED
            truoc_id = dung_id.get(i)
        log(f"thay-mau: miếng {i + 1}/{len(mhinh.dam_bao(hd))} -> {dat.name if dat else 'HỞ'}")
    return ra, dung_id, warns


def be_dong(chu: str, moi_dong: int) -> list[str]:
    """Bẻ chuỗi thành các dòng <= `moi_dong` ký tự, KHÔNG mất ký tự nào.

    Cắt cứng theo độ dài chứ không theo khoảng trắng: link không có khoảng
    trắng nào, mà `wrap=True` của matplotlib chỉ bẻ ở khoảng trắng — nên link
    dài bị vẽ TRÀN cả hai mép ảnh (nhìn ảnh thật 10/09 mới thấy: mất
    `https://...` ở đầu, mất ID ở đuôi -> người dựng không tải được).
    Đo trong kho thật: link dài nhất 226 ký tự.
    """
    return [chu[i:i + moi_dong] for i in range(0, len(chu), moi_dong)]


def anh_giu_cho(thu_muc: Path, link: str = "", tieu_de: str = "") -> tuple[Path, str]:
    """Ảnh 1920x1080 giữ chỗ cho miếng KHÔNG lấy được nguồn nào. Trả (file, chữ).

    Vì sao PHẢI có: main track CapCut là track NAM CHÂM. Draft hở thì lúc MỞ,
    CapCut dồn mọi segment phía sau lên và ghi đè `draft_content.json` — voice
    nằm track khác nên đứng yên, hình nửa sau chương lệch tiếng tích luỹ. Đo
    thật 10/09 trên `OFF_c8-20260831-064152`: hở 5.170s tại giây 67.020.

    USER CHỐT 09/09: có link thì in LINK + câu dặn tải tay — người dựng nhìn ô
    là biết tải ở đâu, không phải mò ngược sổ nguồn.

    Trả cả phần chữ vì matplotlib không cho đọc ngược chữ ra khỏi ảnh; caller
    (và test) cần biết đã dặn gì.
    """
    import hashlib

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if link:
        chu = ["Tool đang cập nhật, vui lòng tải bằng tay theo link",
               link, (tieu_de or "")[:70]]
    else:
        chu = ["EDITOR: ĐẮP FOOTAGE Ở ĐÂY",
               "(không tìm được clip nào cho ô này — máy giữ chỗ để CapCut không dồn timeline)",
               (tieu_de or "")[:70]]
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    # tên theo BĂM của chữ: mỗi link một ảnh, cùng link thì dùng lại — 35 miếng
    # hở mà render 35 lượt matplotlib là phí (mỗi lượt ~0.4s).
    ma = hashlib.sha1("\n".join(chu).encode("utf-8")).hexdigest()[:10]
    out = thu_muc / f"_giu_cho_{ma}.jpg"
    if out.is_file():
        return out, "\n".join(chu)

    plt.rcParams["font.family"] = "DejaVu Sans"      # có dấu tiếng Việt
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor="#14181d")
    # 82 ký tự/dòng ở cỡ 26 — ĐO THẬT trên CẢ 5315 link trong kho (10/09):
    # 0 dòng vượt 1728px (90% khung), và 4606/5315 link (87%) vừa trọn MỘT
    # dòng. Ngưỡng 80 chỉ được 256 link một dòng, ngưỡng 86 làm 3 dòng tràn.
    dong2 = be_dong(chu[1], 82)
    khoi = [(chu[0], 40 if link else 46, "#e0a33a" if link else "#96a0ab", "bold", "normal")]
    khoi += [(d, 26, "#7fb3d5" if link else "#5c656f", "normal", "normal") for d in dong2]
    if chu[2]:
        khoi.append((chu[2], 22, "#5c656f", "normal", "italic"))
    # Xếp GIỮA theo tổng chiều cao thật: link 226 ký tự thành 3 dòng, còn khay
    # rỗng chỉ 2 dòng. Toạ độ cứng thì ca này lệch lên đỉnh, ca kia đè nhau.
    # Khoảng cách tỉ lệ cỡ chữ (dòng cỡ 40 cần chỗ hơn dòng cỡ 26).
    khoang = [co / 1080 * 3.5 for _t, co, *_ in khoi]
    y = 0.5 + sum(khoang) / 2 - khoang[0] / 2
    for (t, co, mau, dam, nghieng), kc in zip(khoi, khoang):
        fig.text(0.5, y, t, color=mau, ha="center", va="center", fontsize=co,
                 fontweight=dam, style=nghieng)
        y -= kc
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out, "\n".join(chu[:1] + dong2 + chu[2:])


def con_du_nguon(f: Path | None, da_dung: float, can: float) -> bool:
    """Asset của miếng trước còn đủ để chảy tiếp thêm `can` giây không?

    Chốt an toàn của luật CHẢY TIẾP (SEQUENCE 3b): lúc CHỌN thì lạc quan (hầu
    hết clip kho không ghi `dai_s` — đo C2: 39/39 rỗng), nhưng lúc RÁP phải đo
    file thật. Hụt thì miếng đó quay về chọn clip riêng, không kéo hình cụt.
    """
    if f is None or not Path(f).is_file():
        return False
    return (_dai_video(Path(f)) - da_dung) >= can


def _dai_video(f: Path) -> float:
    """Độ dài video (giây); 0 nếu không đo được — caller coi như nguồn cạn."""
    try:
        from autoedit.project import ffprobe_duration

        return float(ffprobe_duration(f) or 0.0)
    except Exception:  # noqa: BLE001
        return 0.0


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
               ten_draft: str, profile, log, dung_id: dict | None = None) -> Path:
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
        t0_us, dai_us = mep_us[i], mep_us[i + 1] - mep_us[i]
        f = video.get(i)
        if f is None:
            # KHÔNG để hở: track nam châm CapCut sẽ dồn cả nửa sau chương lên
            # (đo thật OFF_c8: hở 5.170s). Lấp bằng ảnh giữ chỗ mang link.
            try:
                anh, _ = anh_giu_cho(project_dir / "assets_offline",
                                     h.get("ho_link") or "", h.get("ho_ten") or "")
                script.add_segment(VideoSegment(
                    VideoMaterial(str(anh)), Timerange(t0_us, dai_us),
                    source_timerange=Timerange(0, dai_us)), "video_l1")
            except Exception as exc:  # noqa: BLE001 — lưới an toàn, không giết draft
                log(f"thay-mau: miếng {i + 1} KHÔNG lấp được ô giữ chỗ "
                    f"({str(exc)[:60]}) — draft HỞ, CapCut sẽ dồn timeline")
            continue
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
            for i in (dung_id or {}).values():
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
    # SỔ NGUỒN GỐC đi CÙNG draft (chốt 29/08): editor mở draft ở máy khác vẫn
    # truy được nguồn + ID từng miếng. Cũng bọc try/except — mất sổ chứ không
    # được mất draft đã dựng xong.
    try:
        from autoedit.packager import sourcebook

        js, _ = sourcebook.viet_so_offline(hd, dung_id or {}, Path(draft),
                                           project_id=project_dir.name)
        so = json.loads(js.read_text(encoding="utf-8"))
        ti = " · ".join(f"{g} {st['ratio']:.0%}" for g, st in so["summary"].items())
        log(f"thay-mau: sổ nguồn gốc {len(so['clips'])} clip — {ti}")
    except Exception as exc:  # noqa: BLE001
        log(f"thay-mau: ghi sổ nguồn gốc lỗi ({str(exc)[:70]})")
    # GIAO vào thư mục tập trên NAS (user chốt 09/09). Draft ra thật nhưng nằm ở
    # kho draft CapCut, còn `Compose Timeline/<chương>/` thì rỗng — mà chính
    # `DOC_TRUOC.txt` trong đó lại hứa có draft/footage/report. Giao GIẤY TỜ +
    # LỐI MỞ, KHÔNG chép draft (đo LI106: 10 draft = 992MB, chép sang là nhân
    # đôi và đẻ ra hai bản lệch nhau).
    try:
        from autoedit.offline.giao import giao_giay_to

        dich = giao_giay_to(project_dir, Path(draft))
        log(f"thay-mau: giao giấy tờ -> {dich}" if dich
            else "thay-mau: không suy được thư mục giao — bỏ qua, draft vẫn nguyên")
    except Exception as exc:  # noqa: BLE001 — mất giấy tờ chứ không mất draft
        log(f"thay-mau: giao giấy tờ lỗi ({str(exc)[:70]})")
    log(f"thay-mau: draft {draft}")
    return draft


def thay_mau(project_dir: Path, profile=None, conn=None, ark=None, log=None,
             noi_xuat: str = "") -> dict:
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
        # duyệt theo MIẾNG HÌNH, không theo khối: `relocate` đánh số theo miếng
        # nên duyệt khối là so le (chương H 08/09: 15 miếng / 14 khối -> lệch từ
        # chỗ chẻ, miếng cuối không vào sổ lần nào)
        from autoedit.offline import hinh as _mh

        for i, h in enumerate(_mh.dam_bao(hd)):
            if i in dung_id:
                sdb.ghi_su_kien(c, dung_id[i], "len_final",
                                tap=project_dir.name, vi_tri=h["t0"])
        c.commit()
    finally:
        if conn is None:
            c.close()
    voice = _cat_voice(project_dir, hd, ghi)
    if profile is None:
        from autoedit.packager.machine import MachineProfile

        profile = MachineProfile.load()
    if noi_xuat:
        # NƠI XUẤT theo tập (user chốt 09/09): đè `draft_out_root` — đúng chỗ
        # `package_draft` đọc. Ghi THẲNG vào đó, không ghi rồi chép: chép là
        # nhân đôi dung lượng và đẻ ra hai bản lệch nhau.
        profile = profile.model_copy(update={"draft_out_root": str(noi_xuat)})
        log(f"thay-mau: nơi xuất theo tập -> {noi_xuat}")
    ten = f"OFF_{project_dir.name}"
    draft = dung_draft(project_dir, hd, video, voice, ten, profile, ghi,
                       dung_id=dung_id)
    from autoedit.offline import hinh as _mh
    kq = {"draft": str(draft), "mieng_co_hinh": len(video),
          "tong_mieng": len(_mh.dam_bao(hd)), "tong_khoi_voice": len(hd["khoi"]),
          "canh_bao": warns}
    (project_dir / "thay_mau.json").write_text(
        json.dumps(kq, ensure_ascii=False, indent=1), encoding="utf-8")
    return kq
