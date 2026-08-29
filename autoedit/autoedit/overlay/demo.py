"""P1.1 — Derisk gate: draft tối thiểu có text overlay (keyframe) + SFX.

Mục tiêu: chứng minh CapCut máy thật MỞ ĐƯỢC text animation keyframe + SFX trước
khi xây overlay director/assembler (tránh lặp saga relink ở quy mô 100 text).
Nền: 1 video + 1 voice (đã chứng minh ở M1) — chỉ thêm 2 thứ MỚI để cô lập rủi ro.
"""

from __future__ import annotations

import json
from pathlib import Path

from pycapcut import (
    AudioMaterial,
    AudioSegment,
    ScriptFile,
    Timerange,
    TrackType,
    VideoMaterial,
    VideoSegment,
)

from autoedit.overlay.text import build_text_overlay
from autoedit.packager.packager import PackageError

SEC = 1_000_000
SAFETY_US = 3 * SEC // 30
REQUIRED = ["video1.mp4", "voice1.mp3", "sfx.mp3"]


def build_overlay_demo_content(assets_dir: Path) -> dict:
    """Nền video+voice ~6s; text '$2' pop ở giây 1.5 kèm SFX cùng lúc."""
    assets_dir = Path(assets_dir).expanduser().resolve()
    missing = [n for n in REQUIRED if not (assets_dir / n).is_file()]
    if missing:
        raise PackageError(f"Thiếu asset demo {missing} trong {assets_dir}")

    video = VideoMaterial(str(assets_dir / "video1.mp4"))
    voice = AudioMaterial(str(assets_dir / "voice1.mp3"))
    sfx = AudioMaterial(str(assets_dir / "sfx.mp3"))

    total = min(video.duration - SAFETY_US, 6 * SEC)
    pop_at = int(1.5 * SEC)

    script = ScriptFile(1920, 1080, fps=30)
    script.add_track(TrackType.video, "video_l1")
    script.add_track(TrackType.audio, "voice")
    script.add_track(TrackType.audio, "sfx", relative_index=1)
    script.add_track(TrackType.text, "text")

    script.add_segment(VideoSegment(video, Timerange(0, total)), "video_l1")
    script.add_segment(
        AudioSegment(voice, Timerange(0, min(voice.duration - SAFETY_US, total))), "voice"
    )
    # SFX đúng thời điểm text pop (mô phỏng cash-register khi hiện giá)
    script.add_segment(
        AudioSegment(sfx, Timerange(pop_at, min(sfx.duration - SAFETY_US, SEC // 2))), "sfx"
    )
    # ĐIỂM DERISK: text overlay keyframe pop
    script.add_segment(
        build_text_overlay("$2", pop_at, 2 * SEC, position="lower_third", anim="pop", size=18.0),
        "text",
    )
    return json.loads(script.dumps())
