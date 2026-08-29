"""Điểm nhô (Most Replayed) video YouTube — spec MO_TA_VAN_HANH_YTREF_DIEM_NHO §3b-3d.

Thuật toán dò đỉnh BÊ NGUYÊN từ tool ME OutlierY của user (đã chạy thật):
`TOOL CẮT SIÊU DỮ LIỆU\\ME OutlierY WIN\\me\\peaks.py` — local maxima CÓ dốc lên
(chân foot + đỉnh apex), non-max suppression ≥20s, phân loại primary ≥85% /
secondary 55-84% / minor <55% (mặc định BỎ minor — y tool).

Mở rộng cho ống nạp ytref:
- `fetch_video_info` trả kèm title THẬT + chapters (tag bối cảnh §3i) — FAIL-OPEN
  toàn tầng: lỗi mạng / video chưa có Most Replayed / YouTube đổi format -> peaks
  rỗng + `.error`, mẻ nạp vẫn chạy trọn như viral thường.
- `resolve_youtube_id`: rút ID 11 ký tự từ tên file (khuôn YTDown trước, token đứng
  riêng sau), fallback cuối `urls.txt` cạnh file nguồn (§3b).
- `duration_mismatch`: đối chiếu duration file tải vs YouTube — lệch >3% = mốc trượt,
  caller KHÔNG gắn cờ điểm nhô (gắn sai còn hại hơn không gắn — §3d).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

MIN_GAP = 20.0  # giây — khoảng cách tối thiểu giữa 2 đỉnh (non-max suppression, y tool ME)
DUR_TOL = 0.03  # §3d: duration file tải lệch >3% so YouTube -> không gắn cờ điểm nhô


@dataclass
class Peak:
    foot_time: float
    apex_time: float   # start_time của BIN đỉnh (heatmap 100 bin, mỗi bin ~duration/100)
    value: float
    type: str  # primary / secondary / minor
    apex_end: float = 0.0  # end_time bin đỉnh — value đo trên CẢ BIN nên "khoảnh khắc
    #                        đỉnh" nằm trong [apex_time, apex_end]; 0 = không rõ (coi = apex_time)


@dataclass
class YTVideoInfo:
    """Kết quả 1 call yt-dlp cho 1 video — đủ cho cờ điểm nhô (§3e) + tag bối cảnh (§3i)."""

    video_id: str
    title: str = ""
    channel: str = ""  # VD4 ghi công: tên kênh nguồn (yt-dlp channel/uploader)
    duration: float = 0.0
    chapters: list[dict] = field(default_factory=list)  # [{title,start_time,end_time}]
    heatmap_available: bool = False
    peaks: list[Peak] = field(default_factory=list)
    error: str = ""  # fail-open: lý do khi không lấy được (in warning, không raise)


def _dump_json(url: str, timeout: int = 90) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--dump-json", "--no-playlist",
         "--no-warnings", url],
        capture_output=True, text=True, timeout=timeout, encoding="utf-8",
    )
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp lỗi: {(r.stderr or '').strip()[:200]}")
    return json.loads(r.stdout)


def _detect(heatmap: list[dict]) -> list[Peak]:
    """heatmap: [{start_time,end_time,value}] -> Peak đã phân loại (NGUYÊN tool ME).

    Bỏ điểm biên (t=0 luôn =1.0, không phải điểm nhô thật); chỉ nhận local maxima
    CÓ dốc lên (foot < apex); giãn cách đỉnh >= MIN_GAP; phân loại theo đỉnh thật.
    """
    n = len(heatmap)
    if n < 3:
        return []
    vals = [h["value"] for h in heatmap]
    cand: list[tuple[int, int, float]] = []  # (apex_idx, foot_idx, value)
    for i in range(1, n - 1):
        if vals[i] >= vals[i - 1] and vals[i] >= vals[i + 1]:
            foot = i
            for j in range(i - 1, -1, -1):  # đi ngược tìm chân (còn dốc lên)
                if vals[j] < vals[j + 1]:
                    foot = j
                else:
                    break
            if foot == i:  # không có dốc lên -> bỏ (spike biên)
                continue
            cand.append((i, foot, vals[i]))
    if not cand:
        return []
    cand.sort(key=lambda x: -x[2])
    chosen: list[tuple[int, int, float]] = []
    for apex, foot, v in cand:  # non-max suppression theo thời gian
        at = heatmap[apex]["start_time"]
        if all(abs(at - heatmap[a]["start_time"]) >= MIN_GAP for a, _, _ in chosen):
            chosen.append((apex, foot, v))
    vmax = max(v for _, _, v in chosen) or 1.0
    peaks = []
    for apex, foot, v in chosen:
        ratio = v / vmax
        typ = "primary" if ratio >= 0.85 else "secondary" if ratio >= 0.55 else "minor"
        peaks.append(Peak(float(heatmap[foot]["start_time"]),
                          float(heatmap[apex]["start_time"]), float(v), typ,
                          apex_end=float(heatmap[apex].get("end_time") or 0)))
    peaks.sort(key=lambda p: -p.value)
    return peaks


def fetch_video_info(video_id: str, include_minor: bool = False) -> YTVideoInfo:
    """1 call yt-dlp --dump-json -> đỉnh + title + chapters. KHÔNG raise (§3c fail-open)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        data = _dump_json(url)
    except Exception as e:  # mạng/timeout/format đổi/JSON hỏng — mẻ nạp vẫn chạy
        return YTVideoInfo(video_id=video_id, error=str(e)[:200])
    info = YTVideoInfo(
        video_id=video_id,
        title=data.get("title") or "",
        channel=data.get("channel") or data.get("uploader") or "",
        duration=float(data.get("duration") or 0),
        chapters=[{"title": c.get("title", ""),
                   "start_time": float(c.get("start_time") or 0),
                   "end_time": float(c.get("end_time") or 0)}
                  for c in (data.get("chapters") or [])],
    )
    hm = data.get("heatmap")
    if not hm:  # video ít view chưa có Most Replayed — vẫn dùng được title/chapters
        return info
    info.heatmap_available = True
    info.peaks = [p for p in _detect(hm) if include_minor or p.type != "minor"]
    return info


# ------------------- rút YouTube ID từ tên file / urls.txt (§3b) -------------------

_YTDOWN_RE = re.compile(r"_Media_([A-Za-z0-9_-]{11})_\d+_")  # khuôn tool YTDown
# token 11 ký tự hợp lệ ĐỨNG RIÊNG (2 đầu là ký tự ngoài bảng ID hoặc biên chuỗi)
_TOKEN_RE = re.compile(r"(?:^|[^A-Za-z0-9_-])([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])")
_URL_ID_RE = re.compile(
    r"(?:[?&]v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])")


def extract_youtube_id(filename: str) -> str | None:
    """ID 11 ký tự từ tên file: khuôn YTDown trước, token đứng riêng sau (lấy token
    CUỐI — ID thường nằm sát đuôi tên). Không thấy -> None (caller fallback urls.txt).
    ID rút nhầm từ chữ thường 11 ký tự sẽ bị chặn ở tầng đối chiếu duration §3d."""
    m = _YTDOWN_RE.search(filename)
    if m:
        return m.group(1)
    tokens = _TOKEN_RE.findall(filename)
    return tokens[-1] if tokens else None


def _id_from_url(url: str) -> str | None:
    m = _URL_ID_RE.search(url)
    if m:
        return m.group(1)
    return url if re.fullmatch(r"[A-Za-z0-9_-]{11}", url) else None


def load_urls_txt(folder: Path) -> dict[str, str]:
    """`urls.txt` cạnh file nguồn (mỗi dòng `<tên file> = <url>`) -> {tên file: ID}.
    Dòng hỏng bỏ qua — file do editor gõ tay."""
    f = folder / "urls.txt"
    if not f.is_file():
        return {}
    out: dict[str, str] = {}
    for line in f.read_text(encoding="utf-8-sig").splitlines():
        name, sep, url = line.partition("=")
        if not sep:
            continue
        vid = _id_from_url(url.strip())
        if vid:
            out[name.strip()] = vid
    return out


def resolve_youtube_id(source: Path) -> str | None:
    """ID YouTube của 1 file nguồn: tên file trước, urls.txt cạnh file sau (§3b).
    None = nạp như viral thường + warning 'thiếu bối cảnh + điểm nhô' (caller lo)."""
    vid = extract_youtube_id(source.name)
    if vid:
        return vid
    return load_urls_txt(source.parent).get(source.name)


def duration_mismatch(file_dur: float, yt_dur: float) -> bool:
    """True = mốc trượt (lệch >3% hoặc thiếu số đối chiếu) -> KHÔNG gắn cờ điểm nhô."""
    if file_dur <= 0 or yt_dur <= 0:
        return True
    return abs(file_dur - yt_dur) / yt_dur > DUR_TOL


if __name__ == "__main__":  # smoke tay: python -m autoedit.library.ytpeaks <url|id>
    vid = _id_from_url(sys.argv[1]) or sys.argv[1]
    inf = fetch_video_info(vid)
    print(f"video   : {inf.video_id}\ntitle   : {inf.title}\nduration: {inf.duration:.1f}s")
    print(f"heatmap : {'có' if inf.heatmap_available else 'KHÔNG'}"
          + (f"  (lỗi: {inf.error})" if inf.error else ""))
    print(f"chapters: {len(inf.chapters)}")
    for c in inf.chapters:
        print(f"  {c['start_time']:7.1f}s  {c['title']}")
    print(f"đỉnh    : {len(inf.peaks)}")
    for p in inf.peaks:
        print(f"  {p.type:9s} foot {p.foot_time:7.1f}s  apex {p.apex_time:7.1f}s"
              f"  ({int(p.apex_time // 60)}:{p.apex_time % 60:04.1f})  value {p.value:.2f}")
