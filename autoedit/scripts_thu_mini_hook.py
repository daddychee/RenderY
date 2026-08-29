"""THỬ MINI-HOOK ĐỘC LẬP — dựng 1 draft CapCut CHỈ có mini-hook để user duyệt mắt/tai.

KHÔNG đụng pipeline (cut/source/assemble giữ nguyên). Mục đích DUY NHẤT: xem cắt có
đúng nhịp nhạc chưa, trước khi nối vào đường chính (user chốt 2026-07-19).

Cách chạy:
    python scripts_thu_mini_hook.py --music "<file nhạc>" --footage <folder> [--dur 20]

  --music    file nhạc (mp3/wav). Beat đo bằng librosa như music/analyze.py.
  --footage  folder chứa clip; lấy N clip đầu (sắp theo tên). Sau này pipeline sẽ
             thay bằng "N clip điểm cao nhất trong bài" (user chốt: tái dùng footage đẹp).
  --dur      độ dài mini-hook, mặc định 20s.

Draft xuất ra draft_out_root (E:\\CapCut Drafts) — portable, mở được trên máy editor.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SEC = 1_000_000


def _beat_times(music: Path) -> tuple[list[float], list[float], float]:
    """Beat + ĐỘ MẠNH tại từng beat + BPM. Dùng ĐÚNG cách music/analyze.py.

    Độ mạnh cần cho beat_grid: cắt vào beat YẾU kề beat mạnh bị tai nghe là TRỄ một
    nhịp (bug b08/b09 user bắt 2026-07-19).
    """
    import librosa
    import numpy as np

    y, sr = librosa.load(str(music), sr=22050, mono=True, duration=120)
    env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beats = librosa.beat.beat_track(onset_envelope=env, sr=sr, units="time")
    times = librosa.times_like(env, sr=sr)
    envn = env / env.max() if env.max() > 0 else env
    strength = [float(envn[int(np.argmin(np.abs(times - b)))]) for b in beats]
    return [float(b) for b in beats], strength, float(np.atleast_1d(tempo)[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--music", required=True, type=Path)
    ap.add_argument("--footage", required=True, type=Path)
    ap.add_argument("--dur", type=float, default=20.0)
    ap.add_argument("--name", default="MINIHOOK_TEST")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    from pycapcut import (
        AudioMaterial,
        AudioSegment,
        ScriptFile,
        Timerange,
        TrackType,
        VideoMaterial,
        VideoSegment,
    )

    from autoedit.music.minihook import grid_windows
    from autoedit.packager.machine import MachineProfile
    from autoedit.packager.packager import package_draft
    from autoedit.packager.transcode import normalize_video

    if not args.music.is_file():
        print(f"LỖI: không thấy file nhạc {args.music}")
        return 1

    beats, strength, bpm = _beat_times(args.music)
    windows = grid_windows(args.dur, beats, beat_strength=strength)
    print(f"Nhạc: {args.music.name}  |  {bpm:.1f} BPM  |  beat đầu {beats[0]:.3f}s")
    print(f"Mini-hook {args.dur}s -> {len(windows)} shot:")
    for i, (s, e) in enumerate(windows):
        if i:
            k = min(range(len(beats)), key=lambda j: abs(s - beats[j]))
            lech, manh = abs(s - beats[k]) * 1000, strength[k]
            # beat kề bên có mạnh hơn không? (mạnh hơn = có thể vẫn trễ/sớm 1 nhịp)
            ke = [strength[j] for j in (k - 1, k + 1) if 0 <= j < len(beats)]
            co = "" if not ke or manh >= max(ke) else "  ⚠ beat kề MẠNH HƠN"
            print(f"  shot {i+1:2d}  {s:6.3f} -> {e:6.3f}  ({e-s:.2f}s)"
                  f"  lệch {lech:4.1f}ms  mạnh {manh:.2f}{co}")
        else:
            print(f"  shot  1  {s:6.3f} -> {e:6.3f}  ({e-s:.2f}s)  (mở màn)")

    # --- footage: lấy N clip đầu trong folder --------------------------------
    exts = {".mp4", ".mov", ".mkv", ".webm", ".jpg", ".jpeg", ".png"}
    clips = sorted(p for p in args.footage.rglob("*") if p.suffix.lower() in exts)
    if not clips:
        print(f"LỖI: folder {args.footage} không có clip nào")
        return 1
    print(f"\nFootage: {len(clips)} file trong kho, dùng {len(windows)} clip đầu")

    # --- dựng draft -----------------------------------------------------------
    script = ScriptFile(1920, 1080, fps=30)
    script.add_track(TrackType.video, "video_l1")
    script.add_track(TrackType.audio, "music", relative_index=1)

    norm_dir = Path(__file__).resolve().parent / "_minihook_norm"
    norm_dir.mkdir(exist_ok=True)

    for i, (s, e) in enumerate(windows):
        src = clips[i % len(clips)]
        try:
            asset = normalize_video(src, norm_dir / f"{i:02d}_{src.stem}.mp4")
        except Exception as exc:
            print(f"  ! shot {i+1}: {src.name} hỏng ({exc}) — BỎ QUA")
            continue
        material = VideoMaterial(str(asset))
        # round KHÔNG int: 4.18*SEC = 4179999.9999 -> lệch 1µs -> SegmentOverlap
        start_us = round(s * SEC)
        want_us = round(e * SEC) - start_us
        avail = material.duration - 100_000
        if avail >= want_us:
            seg = VideoSegment(material, Timerange(start_us, want_us),
                               source_timerange=Timerange(0, want_us))
        else:  # clip ngắn hơn ô -> giãn cho đầy (KHÔNG để hở: bug NAM CHÂM)
            seg = VideoSegment(material, Timerange(start_us, want_us),
                               speed=avail / want_us)
        script.add_segment(seg, "video_l1")

    total_us = round(args.dur * SEC)
    m = AudioMaterial(str(args.music))
    script.add_segment(
        AudioSegment(m, Timerange(0, min(total_us, m.duration - 100_000)),
                     source_timerange=Timerange(0, min(total_us, m.duration - 100_000)),
                     volume=1.0),
        "music",
    )

    profile = MachineProfile.load()
    content = json.loads(script.dumps())          # dumps() trả CHUỖI (như assembler.py:326)
    out = package_draft(content, args.name, profile, overwrite=args.overwrite)
    print(f"\n✅ Draft: {out}")
    print("   Mở CapCut -> xem mini-hook cắt có đúng nhịp chưa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
