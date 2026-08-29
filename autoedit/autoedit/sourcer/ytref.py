"""Nguồn footage từ VIDEO MẪU YouTube (đối thủ) — tải theo link, cắt tại ĐIỂM NHÔ.

User đưa link YouTube video đối thủ; tool tải về, đọc heatmap Most Replayed, cắt các
đoạn khán giả xem lại nhiều nhất thành clip 3-10s (bỏ tiếng) để dùng làm B-roll.

Khác mọi nguồn khác ở chỗ: đây là footage KHÔNG CÓ QUYỀN. Nên mỗi clip mang
`asset_key` dạng `ytref:<VIDEO_ID>@t=<start>-<end>` — truy ngược được clip nào cắt
từ video nào, giây nào; và `ViralLedger` (gate C8) áp trần tỉ trọng 8%/15%.

Tái dùng nguyên:
- `library.ytpeaks` — dò đỉnh (thuật toán bê từ tool ME của user), rút ID, fail-open.
- `sourcer.viral.ViralLedger` — trần tỉ trọng + luật cấm 2 cảnh liền kề cùng nguồn.
Module này chỉ thêm phần TẢI + CẮT + ghi sổ, không dò đỉnh lại.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from autoedit.library.ytpeaks import Peak, YTVideoInfo, fetch_video_info, _id_from_url
from autoedit.project import ffprobe_duration

MAX_CLIP = 10.0    # giây — clip thường không quá 10s (y tool ME của user)
MIN_CLIP = 3.0
LEAD_IN = 1.0      # lấy thêm 1s sau apex: "khoảnh khắc đỉnh" nằm trong bin, không đúng mép
DOWNLOAD_TIMEOUT = 900   # 15 phút/video — video dài + mạng chậm
_MAX_HEIGHT = 1080       # không tải 4K: nặng, timeline vốn 1920x1080


class YtRefError(RuntimeError):
    """Lỗi tải/cắt video mẫu — caller quyết định bỏ qua nguồn này hay dừng."""


@dataclass
class YtClip:
    """1 clip đã cắt từ video mẫu, kèm đủ dấu vết truy ngược nguồn gốc."""

    path: Path
    video_id: str
    start: float
    end: float
    peak_type: str          # primary / secondary / minor
    title: str = ""
    channel: str = ""

    @property
    def asset_key(self) -> str:
        """Khoá truy ngược: nguồn + ID + mốc thời gian gốc trong video đối thủ."""
        return f"ytref:{self.video_id}@t={self.start:.1f}-{self.end:.1f}"

    @property
    def duration(self) -> float:
        return self.end - self.start

    def as_candidate(self) -> dict:
        """Về đúng shape candidate của StockClient để runner dùng chung."""
        return {
            "asset_key": self.asset_key,
            "url": str(self.path),          # file local, không phải URL mạng
            "media_type": "video",
            "duration": self.duration,
            "width": 0, "height": 0,        # runner probe lại khi cần
            "description": f"{self.title} — {self.channel}".strip(" —"),
            "source": "ytref",
            "video_id": self.video_id,
            "peak_type": self.peak_type,
        }


def parse_links(text: str) -> list[str]:
    """Đọc file links: mỗi dòng 1 URL YouTube, bỏ dòng trống và dòng ghi chú (#)."""
    out: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if _id_from_url(line) or len(line) == 11:
            out.append(line)
    return out


def video_ids(links: list[str]) -> list[str]:
    """URL/ID -> list ID 11 ký tự, khử trùng lặp, giữ thứ tự."""
    seen: set[str] = set()
    out: list[str] = []
    for link in links:
        vid = _id_from_url(link) or (link if len(link) == 11 else None)
        if vid and vid not in seen:
            seen.add(vid)
            out.append(vid)
    return out


def plan_cuts(info: YTVideoInfo, budget_ratio: float) -> list[tuple[float, float, str]]:
    """Từ điểm nhô -> danh sách (start, end, peak_type) trong TRẦN ngân sách.

    Đỉnh mạnh trước (primary rồi secondary), dừng khi chạm trần. Trần tính theo
    THỜI LƯỢNG NGUỒN — cùng cách đo của gate C8 (cộng dồn trọn duration mỗi clip).
    """
    if not info.peaks or info.duration <= 0:
        return []
    budget = info.duration * budget_ratio
    order = {"primary": 0, "secondary": 1, "minor": 2}
    cuts: list[tuple[float, float, str]] = []
    used = 0.0
    for pk in sorted(info.peaks, key=lambda p: (order.get(p.type, 3), -p.value)):
        start = max(0.0, pk.foot_time)
        # Kéo tới hết bin đỉnh + LEAD_IN, kẹp trong [MIN_CLIP, MAX_CLIP]
        want_end = max(pk.apex_end or pk.apex_time, pk.apex_time) + LEAD_IN
        dur = min(max(want_end - start, MIN_CLIP), MAX_CLIP)
        end = min(start + dur, info.duration)
        dur = end - start
        if dur < MIN_CLIP:
            continue  # sát cuối video, không đủ dài
        if used + dur > budget:
            continue  # clip này vượt trần -> thử đỉnh sau (có thể ngắn hơn, lọt)
        cuts.append((start, end, pk.type))
        used += dur
    return sorted(cuts, key=lambda c: c[0])


def download_video(video_id: str, dest_dir: Path, timeout: int = DOWNLOAD_TIMEOUT) -> Path:
    """Tải video YouTube về dest_dir. Trả path file. Raise YtRefError nếu hỏng."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(dest_dir.glob(f"{video_id}.*"))
    for p in existing:
        if p.suffix.lower() != ".part" and ffprobe_duration(p) is not None:
            return p  # đã tải rồi (resume-safe: chạy lại không tải lại)

    out_tmpl = str(dest_dir / f"{video_id}.%(ext)s")
    cmd = [
        sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-warnings",
        "-f", f"bestvideo[height<={_MAX_HEIGHT}]+bestaudio/best[height<={_MAX_HEIGHT}]",
        "--merge-output-format", "mp4",
        "-o", out_tmpl, f"https://www.youtube.com/watch?v={video_id}",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise YtRefError(f"Tải {video_id} quá {timeout}s — bỏ qua nguồn này")
    if r.returncode != 0:
        raise YtRefError(f"yt-dlp lỗi ({video_id}): {r.stderr.strip()[:200]}")

    for p in sorted(dest_dir.glob(f"{video_id}.*")):
        if p.suffix.lower() != ".part" and ffprobe_duration(p) is not None:
            return p
    raise YtRefError(f"Tải xong nhưng không thấy file dùng được: {video_id}")


def cut_clip(src: Path, start: float, end: float, dest: Path) -> Path:
    """Cắt [start, end) thành clip KHÔNG TIẾNG (-an) — voice riêng đã có, tiếng gốc thừa."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(src),
        "-an",  # bỏ tiếng (y tool ME)
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        str(dest),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or ffprobe_duration(dest) is None:
        dest.unlink(missing_ok=True)
        raise YtRefError(f"Cắt clip hỏng ({src.name} {start:.1f}-{end:.1f}s): "
                         f"{r.stderr.strip()[:160]}")
    return dest


def harvest(video_id: str, work_dir: Path, budget_ratio: float,
            include_minor: bool = False) -> tuple[list[YtClip], str]:
    """Tải 1 video mẫu + cắt clip tại điểm nhô. Trả (clips, warning).

    FAIL-OPEN toàn tầng (§3c của padoma): lỗi mạng / video chưa có Most Replayed /
    cắt hỏng -> trả clip rỗng + warning, KHÔNG raise. Một video mẫu hỏng không được
    giết cả lượt dựng.
    """
    info = fetch_video_info(video_id, include_minor=include_minor)
    if info.error:
        return [], f"{video_id}: {info.error}"
    if not info.heatmap_available:
        return [], f"{video_id}: chưa có Most Replayed (video ít view?) — bỏ qua"

    cuts = plan_cuts(info, budget_ratio)
    if not cuts:
        return [], f"{video_id}: không có đỉnh nào lọt trần {budget_ratio:.0%}"

    try:
        src = download_video(video_id, work_dir / "src")
    except YtRefError as exc:
        return [], str(exc)

    clips: list[YtClip] = []
    warns: list[str] = []
    for start, end, ptype in cuts:
        dest = work_dir / "clips" / f"ytref_{video_id}_{start:07.1f}.mp4"
        try:
            if not dest.exists():
                cut_clip(src, start, end, dest)
        except YtRefError as exc:
            warns.append(str(exc))
            continue
        clips.append(YtClip(path=dest, video_id=video_id, start=start, end=end,
                            peak_type=ptype, title=info.title, channel=info.channel))
    return clips, "; ".join(warns)


def write_ledger(clips: list[YtClip], dest: Path) -> Path:
    """Ghi sổ nguồn gốc JSON — bằng chứng truy ngược khi bị hỏi bản quyền."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    rows = [{
        "asset_key": c.asset_key, "file": c.path.name, "video_id": c.video_id,
        "url": f"https://www.youtube.com/watch?v={c.video_id}&t={int(c.start)}s",
        "start": round(c.start, 2), "end": round(c.end, 2),
        "duration": round(c.duration, 2), "peak_type": c.peak_type,
        "title": c.title, "channel": c.channel,
    } for c in clips]
    dest.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def source_mix(asset_keys: list[str], durations: list[float]) -> dict:
    """Tỉ trọng theo NHÓM NGUỒN để user nhìn 1 dòng biết ngay % footage cắt.

    Nhóm: stock (pexels/pixabay, free) · sub (envato/vecteezy/artlist, đã trả tiền)
    · ytref (CẮT, không có quyền) · local (kho riêng) · other.
    """
    group_of = {"pexels": "stock", "pixabay": "stock",
                "envato": "sub", "vecteezy": "sub", "artlist": "sub",
                "ytref": "ytref", "local": "local"}
    total = sum(durations) or 1.0
    secs: dict[str, float] = {}
    count: dict[str, int] = {}
    for key, dur in zip(asset_keys, durations):
        prefix = key.split(":", 1)[0] if ":" in key else "other"
        g = group_of.get(prefix, "other")
        secs[g] = secs.get(g, 0.0) + dur
        count[g] = count.get(g, 0) + 1
    return {g: {"seconds": round(s, 1), "ratio": round(s / total, 4), "clips": count[g]}
            for g, s in sorted(secs.items(), key=lambda kv: -kv[1])}
