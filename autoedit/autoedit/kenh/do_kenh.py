r"""Đo KÊNH ref → HoSoKenh: tải (yt-dlp) → đo nhịp (nhip/do) → đo nhạc (ffmpeg).

Đường đi: link YouTube (kênh @handle hoặc video lẻ) → tải tối đa SO_VIDEO bản
360p (đủ cho dò điểm cắt — 03/09 đo Fern 28' ở 360p vẫn hội tụ 2 thước) → đo
từng video → chỉ video HỘI TỤ 2 thước mới vào hồ sơ (video đánh lừa thước như
đồ hoạ nhấp nháy bị loại, đúng luật nhip/do.py) → gộp median → cache.

yt-dlp cần JS runtime cho YouTube — deno đặt BỀN tại C:\OutlierY\tools\deno
(bài học 05/09: bản cũ nằm ở scratchpad phiên làm việc, bay mất khi hết phiên).
Video tải về thư mục tạm và XOÁ ngay sau khi đo — chỉ giữ hoso.json vài KB.
"""

from __future__ import annotations

import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

from autoedit.kenh.hoso import HoSoKenh
from autoedit.nhip.do import DoNhipError, do_video

SO_VIDEO = 5          # mặc định (user 05/09: "đo nhiều video thì số hiệu chỉnh
                      # chuẩn hơn"); trần 8 — YouTube từng chặn IP ở ~9 lượt tải
SO_VIDEO_TRAN = 8
DAI_TOI_THIEU_S = 240  # bỏ video <4 phút (shorts/trailer — không đại diện nhịp dựng)
DENO_DIR = r"C:\OutlierY\tools\deno"
# Lớp cookies NGỦ ĐÔNG (user hỏi 05/09 sau trận 403): bình thường KHÔNG cần —
# 403 hàng loạt hôm đó do yt-dlp cũ 2 tháng, update là khỏi. Nhưng ngày nào
# YouTube chặn IP máy chủ thật thì chỉ cần export cookies từ browser đã đăng
# nhập (account PHỤ — account bị soi có thể dính cờ) bỏ vào đây là chạy tiếp,
# không phải sửa code. File không tồn tại = bỏ qua.
COOKIES_FILE = Path(r"C:\OutlierY\tools\yt_cookies.txt")


class DoKenhError(RuntimeError):
    """Không đo được kênh — thông điệp tiếng Việt, in thẳng cho editor."""


def slug_tu_ten(ten: str) -> str:
    """Tên phong cách editor đặt ("Fern chậm rãi") -> slug thư mục cache
    ("fern-cham-rai") — bỏ dấu tiếng Việt, chỉ giữ chữ/số/gạch."""
    import unicodedata

    khong_dau = unicodedata.normalize("NFD", ten)
    khong_dau = "".join(c for c in khong_dau if unicodedata.category(c) != "Mn")
    khong_dau = khong_dau.replace("đ", "d").replace("Đ", "D")
    sach = re.sub(r"[^\w.-]+", "-", khong_dau).strip("-").lower()[:60]
    if not sach:
        raise DoKenhError(f"tên phong cách không hợp lệ: {ten!r}")
    return sach


def slug_tu_link(link: str) -> str:
    """Link kênh/video → slug cache. '@fern-tv' → 'fern-tv'; video lẻ → 'video-<id>'."""
    link = (link or "").strip().rstrip("/")
    m = re.search(r"@([\w.-]+)", link)
    if m:
        return m.group(1).lower()
    m = re.search(r"(?:watch\?v=|youtu\.be/)([\w-]{6,})", link)
    if m:
        # lowercase NHẤT QUÁN mọi nhánh — dropdown UI gửi lại slug làm kenh_ref,
        # nhánh fallback vốn lowercase, lệch case là trượt cache (Windows FS
        # không phân biệt hoa thường nên cache cũ không vỡ).
        return f"video-{m.group(1)}".lower()
    m = re.search(r"/channel/(UC[\w-]+)", link)
    if m:
        return m.group(1).lower()
    # đường cùng: lọc ký tự an toàn làm tên thư mục
    sach = re.sub(r"[^\w.-]+", "-", link.split("//")[-1])[:60].strip("-").lower()
    if not sach:
        raise DoKenhError(f"link không nhận dạng được: {link!r}")
    return sach


def _tai_video(link: str, dich: Path, so_video: int = SO_VIDEO,
               log=None) -> list[Path]:
    """Tải tối đa so_video bản 360p về `dich`. Trả danh sách file đã tải.

    Kênh -> lấy video MỚI NHẤT (tab /videos, bỏ shorts qua lọc thời lượng).
    Chạy yt-dlp qua subprocess (không import API) để PATH deno tiêm được sạch.
    """
    def ghi(m):
        if log:
            log(m)

    env = dict(os.environ)
    env["PATH"] = DENO_DIR + os.pathsep + env.get("PATH", "")
    la_video_le = bool(re.search(r"watch\?v=|youtu\.be/", link))
    url = link if la_video_le else link.rstrip("/") + "/videos"
    # sys.executable -m yt_dlp: LUÔN bản trong venv — gọi "yt-dlp" trần qua PATH
    # từng vớ phải bản GLOBAL cũ 2 tháng (trận 403 hàng loạt 05/09: venv đã
    # update mà production vẫn chết vì subprocess chạy con global)
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--no-warnings", "--quiet", "--no-playlist" if la_video_le else "--yes-playlist",
        "-f", "bv*[height<=360]+ba/b[height<=360]/b",
        "--merge-output-format", "mp4",
        "--match-filter", f"duration >= {DAI_TOI_THIEU_S}",
        "--playlist-items", f"1:{so_video * 2}",   # dư gấp đôi vì match-filter loại bớt
        "--max-downloads", str(so_video),
        "-o", str(dich / "%(id)s.%(ext)s"),
    ]
    if COOKIES_FILE.is_file():
        cmd += ["--cookies", str(COOKIES_FILE)]
        ghi("kenh: dùng cookies tại " + str(COOKIES_FILE))
    cmd.append(url)
    ghi(f"kenh: tải tối đa {so_video} video 360p từ {url}")
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                       env=env, timeout=1800)
    files = sorted(dich.glob("*.mp4"))
    # yt-dlp exit 101 = dừng vì --max-downloads (thành công); các mã khác + 0 file = lỗi thật
    if not files:
        duoi = (r.stderr or r.stdout or "")[-400:]
        goi_y = ""
        if "403" in duoi or "Forbidden" in duoi:
            goi_y = (" · GỢI Ý 403: yt-dlp cũ (update trong venv) hoặc YouTube "
                     f"chặn IP — export cookies browser vào {COOKIES_FILE}")
        raise DoKenhError(f"không tải được video nào từ {link} — {duoi}{goi_y}")
    return files


def do_nhac_ffmpeg(video: Path, so_bucket: int = 12) -> dict:
    """Energy curve audio bằng ffmpeg THUẦN (librosa cố ý vắng trên máy chủ).

    RMS dB mỗi giây (astats reset theo khung 1s) → chia so_bucket theo thời
    gian, chuẩn hoá 0..1 trong video. Trả {curve, vi_tri_drop, do_dong}.
    """
    cmd = ["ffmpeg", "-hide_banner", "-i", str(video), "-vn",
           "-af", "aresample=8000,asetnsamples=n=8000,"
                  "astats=metadata=1:reset=1,"
                  "ametadata=mode=print:key=lavfi.astats.Overall.RMS_level:file=-",
           "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                       timeout=600)
    db: list[float] = []
    for dong in r.stdout.splitlines():
        m = re.search(r"RMS_level=(-?[\d.]+|-inf)", dong)
        if m:
            db.append(-90.0 if m.group(1) == "-inf" else float(m.group(1)))
    if len(db) < so_bucket:
        return {"curve": [], "vi_tri_drop": 0.0, "do_dong": 0.0}
    # bucket theo thời gian, mỗi bucket lấy trung bình dB
    n = len(db)
    buckets = [statistics.fmean(db[i * n // so_bucket:(i + 1) * n // so_bucket])
               for i in range(so_bucket)]
    lo, hi = min(buckets), max(buckets)
    curve = [round((b - lo) / (hi - lo), 3) if hi > lo else 0.5 for b in buckets]
    sx = sorted(db)
    do_dong = sx[int(0.9 * (n - 1))] - sx[int(0.1 * (n - 1))]
    return {"curve": curve,
            "vi_tri_drop": round(curve.index(max(curve)) / (so_bucket - 1), 3),
            "do_dong": round(do_dong, 1)}


def _hook_kieu(hook_tv: float, than_tv: float) -> str:
    """Suy kiểu hook từ tỉ lệ trung vị hook/thân — heuristic khớp 3 kiểu đã
    quan sát tháng 9 (Fern hook 0.72s vs thân 2.1s ≈ 0.34 → nổ; Harris leo)."""
    if than_tv <= 0 or hook_tv <= 0:
        return ""
    ty_le = hook_tv / than_tv
    if ty_le < 0.5:
        return "no"
    if ty_le < 0.85:
        return "leo"
    return "em"


def _median(vals: list[float]) -> float:
    return round(statistics.median(vals), 3) if vals else 0.0


def do_kenh(link: str, ten: str = "", so_video: int = SO_VIDEO,
            do_lai: bool = False, log=None, tai=None, goi_vision=None,
            ten_phong_cach: str = "", nguoi_tao: str = "",
            llm_mo_ta=None) -> HoSoKenh:
    """Link → HoSoKenh (cache theo kênh). `tai` tiêm được để test không mạng."""
    def ghi(m):
        if log:
            log(m)

    ten = ten or slug_tu_link(link)
    if not do_lai:
        cu = HoSoKenh.doc(ten)
        if cu is not None:
            ghi(f"kenh: «{ten}» đã đo {cu.ngay_do[:10]} ({cu.so_video_hoi_tu} video)"
                " — dùng cache, thêm --do-lai nếu muốn đo mới")
            return cu

    tai = tai or _tai_video
    tmp = Path(tempfile.mkdtemp(prefix=f"kenh_{ten}_"))
    try:
        files = tai(link, tmp, so_video=so_video, log=log)
        hooks, hooks_nhanh, thans, thans_nhanh, thans_hold = [], [], [], [], []
        chu_kys, drops, do_dongs = [], [], []
        curve_tong: list[list[float]] = []
        video_hoi_tu: list[Path] = []
        hoi_tu = 0
        for f in files:
            ghi(f"kenh: đo {f.name}...")
            try:
                kq = do_video(f)
            except DoNhipError as exc:
                ghi(f"kenh: {f.name} đo lỗi ({exc}) — bỏ")
                continue
            if not kq.hoi_tu():
                ghi(f"kenh: {f.name} hai thước KHÔNG hội tụ — bỏ (video đánh lừa thước)")
                continue
            hoi_tu += 1
            video_hoi_tu.append(f)
            h, t = kq.hook.get("select"), kq.than.get("select")
            if h:
                hooks.append(h.trung_vi)
                hooks_nhanh.append(h.ty_le_nhanh)
            if t:
                thans.append(t.trung_vi)
                thans_nhanh.append(t.ty_le_nhanh)
                thans_hold.append(t.ty_le_hold)
            if kq.chu_ky_bung_s:
                chu_kys.append(kq.chu_ky_bung_s)
            nh = do_nhac_ffmpeg(f)
            if nh["curve"]:
                curve_tong.append(nh["curve"])
                drops.append(nh["vi_tri_drop"])
                do_dongs.append(nh["do_dong"])
        if hoi_tu == 0:
            raise DoKenhError(
                f"không video nào của «{ten}» cho số đo tin được (2 thước không "
                "hội tụ) — thử kênh khác hoặc dán link video cụ thể ít đồ hoạ hơn")
        hs = HoSoKenh(
            ten=ten, ten_phong_cach=ten_phong_cach, nguoi_tao=nguoi_tao, link=link,
            nguon=[f.stem for f in files], so_video_hoi_tu=hoi_tu,
            hook_trung_vi=_median(hooks), hook_ty_le_nhanh=_median(hooks_nhanh),
            than_trung_vi=_median(thans), than_ty_le_nhanh=_median(thans_nhanh),
            than_ty_le_hold=_median(thans_hold),
            bung_chu_ky_s=_median(chu_kys),
            nhac_vi_tri_drop=_median(drops), nhac_do_dong=_median(do_dongs),
        )
        hs.hook_kieu = _hook_kieu(hs.hook_trung_vi, hs.than_trung_vi)
        if curve_tong:
            n = len(curve_tong[0])
            hs.nhac_energy_curve = [
                round(statistics.fmean(c[i] for c in curve_tong), 3) for i in range(n)]
        # Tầng 3 (Đợt B): tỷ trọng loại cảnh — GLM vision, fail-open (thiếu key/
        # API chết -> {} + log, hồ sơ vẫn có 2 tầng nhịp+nhạc). Đo TRƯỚC khi xoá
        # video tạm; goi_vision tiêm được cho test.
        from autoedit.kenh.loai_canh import do_loai_canh
        hs.loai_canh = do_loai_canh(video_hoi_tu, goi=goi_vision, log=log)
        if hs.loai_canh:
            ghi("kenh: loại cảnh — " + " · ".join(
                f"{k} {v:.0%}" for k, v in hs.loai_canh.items() if v > 0))
        # MÔ TẢ ĐỌC ĐƯỢC (Framing Insight): LLM viết bản nhận diện 4 mặt (nhịp
        # độ · đường hình · âm nhạc · năng lượng) TỪ số đo — fail-open: thiếu
        # key/API chết thì mô tả trống, UI nhắc Đo lại để sinh.
        try:
            from autoedit.kenh.mo_ta import sinh_mo_ta
            hs.mo_ta = sinh_mo_ta(hs, llm=llm_mo_ta)
            ghi("kenh: mô tả phong cách đã sinh (Framing Insight)")
        except Exception as exc:  # noqa: BLE001
            ghi(f"kenh: sinh mô tả LỖI ({exc}) — hồ sơ vẫn giữ đủ số đo")
        hs.ghi()
        ghi(f"kenh: «{ten}» đo xong — {hoi_tu}/{len(files)} video hội tụ, hồ sơ đã cache")
        return hs
    finally:
        shutil.rmtree(tmp, ignore_errors=True)   # video tạm xoá sạch, chỉ giữ hoso.json
