"""Demo draft — bài kiểm tra M1 (tái hiện PADOMA_TEST_V2 bằng code sạch).

Sinh draft 3 track (video, voice, nhạc + text) từ folder asset mẫu.
Đây cũng là bài test chạy lại sau mỗi lần CapCut update (RA_SOAT_LOGIC 6.3).
"""

from __future__ import annotations

import json
from pathlib import Path

from pycapcut import (
    AudioMaterial,
    AudioSegment,
    ScriptFile,
    TextSegment,
    Timerange,
    TrackType,
    VideoMaterial,
    VideoSegment,
)

from autoedit.packager.packager import PackageError

SEC = 1_000_000  # CapCut tính bằng microsecond

# Asset mẫu bắt buộc trong folder assets (trùng bộ capcut_test/assets)
REQUIRED_ASSETS = ["video1.mp4", "video2.mp4", "voice1.mp3", "voice2.mp3", "music.mp3"]

# Cắt target ngắn hơn duration vật lý ≥3 frame @30fps (RA_SOAT_LOGIC 6.8)
SAFETY_US = 3 * SEC // 30


def _clamped(material_duration: int, want_us: int) -> int:
    """Không bao giờ dùng quá duration vật lý trừ biên an toàn 3 frame."""
    return min(want_us, max(material_duration - SAFETY_US, 0))


def build_demo_content(assets_dir: Path) -> dict:
    """Ráp draft content demo bằng pycapcut, trả về dict (chưa đóng gói)."""
    assets_dir = Path(assets_dir).expanduser().resolve()
    missing = [n for n in REQUIRED_ASSETS if not (assets_dir / n).is_file()]
    if missing:
        raise PackageError(
            f"Folder assets thiếu file mẫu {missing} (tìm trong {assets_dir})"
        )

    video1 = VideoMaterial(str(assets_dir / "video1.mp4"))
    video2 = VideoMaterial(str(assets_dir / "video2.mp4"))
    voice1 = AudioMaterial(str(assets_dir / "voice1.mp3"))
    voice2 = AudioMaterial(str(assets_dir / "voice2.mp3"))
    music = AudioMaterial(str(assets_dir / "music.mp3"))

    # Timeline demo ~10s: 2 shot video nối nhau, voice khớp shot, nhạc phủ nền
    shot1 = _clamped(video1.duration, 5 * SEC)
    shot2 = _clamped(video2.duration, 5 * SEC)
    v1 = _clamped(voice1.duration, shot1)
    v2 = _clamped(voice2.duration, shot2)
    total = shot1 + shot2

    script = ScriptFile(1920, 1080, fps=30)
    script.add_track(TrackType.video, "video_l1")
    script.add_track(TrackType.audio, "voice")
    script.add_track(TrackType.audio, "music", relative_index=1)
    script.add_track(TrackType.text, "text")

    script.add_segment(VideoSegment(video1, Timerange(0, shot1)), "video_l1")
    script.add_segment(VideoSegment(video2, Timerange(shot1, shot2)), "video_l1")
    script.add_segment(AudioSegment(voice1, Timerange(0, v1)), "voice")
    script.add_segment(AudioSegment(voice2, Timerange(shot1, v2)), "voice")
    script.add_segment(
        AudioSegment(music, Timerange(0, _clamped(music.duration, total)), volume=0.3),
        "music",
    )
    script.add_segment(
        TextSegment("PADOMA AUTOEDIT DEMO", Timerange(0, total)), "text"
    )

    return json.loads(script.dumps())
