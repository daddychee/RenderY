"""Stage 3 — Cut: master WAV -> snap ranh giới vào lặng -> cắt segment -> ghi project.

Pure function từ project.json: chạy lại đè sạch segments cũ, không nhân đôi (7.1).
"""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from autoedit.cutter import pause as pz
from autoedit.cutter import silence as sil
from autoedit.cutter import timeline as tl
from autoedit.project import (
    Project,
    Stage,
    StageRecord,
    StageStatus,
    VoiceSegment,
    ffprobe_duration,
)

FADE_SEC = 0.008          # 3.2: fade 8ms hai đầu chống click
DURATION_TOLERANCE = 0.05  # verify ffprobe ±50ms
TAIL_PAD = 0.30           # 3.1: đệm sau từ cuối segment (giữ âm đuôi/decay)
LEAD_PAD = 0.25           # 3.1: đệm dự phòng khi không đo được khởi âm
ONSET_GUARD = 0.12        # 3.1: lùi trước khởi âm ĐO ĐƯỢC từ audio
# NGẮT NHỊP TRONG VOICE (user chốt 05/09: "tôi sẽ cho user ngắt nhịp trong voice —
# nhận tín hiệu đó là hình thở"): khoảng nghỉ >= ngưỡng giữa 2 beat, ĐO SẠCH TIẾNG,
# được chuyển thành breathing_after ĐÚNG độ dài ngắt — thay vì bị cắt bỏ ở ranh run
# (đo LI100: 305s nguồn bị vứt, timeline chỉ chèn lại 181s thở máy).
NGUONG_NGAT_S = 1.0       # ngắt chủ động của người đọc thường >= 1s
TIENG_CHO_PHEP = 0.25     # vùng nghỉ chứa > 0.25s KHÔNG-im-lặng = có tiếng thật


def _tieng_trong_vung(
    z0: float, z1: float, silences: list[tuple[float, float]]
) -> float:
    """Số giây CÓ TIẾNG trong [z0, z1] = độ dài vùng trừ phần phủ bởi silence.

    Dùng để (a) chỉ nhận ngắt-nhịp SẠCH làm hình thở, (b) phát hiện align sót từ
    tại ranh run — vùng "nghỉ theo transcript" mà có tiếng thì cấm vứt (bug 05/09:
    câu 5s mất 2-3s voice)."""
    dai = max(0.0, z1 - z0)
    im = sum(max(0.0, min(e, z1) - max(s, z0)) for s, e in silences)
    return max(0.0, dai - im)


def _onset_in_zone(
    zone_start: float, zone_end: float, silences: list[tuple[float, float]]
) -> float | None:
    """Khởi âm thật của từ sau vùng nghỉ = silence_end CUỐI CÙNG trong vùng.

    Cho phép lố zone_end 0.2s vì chính zone_end (timestamp align) có thể trễ.
    """
    candidates = [
        e for s, e in silences if zone_start - 0.05 <= e <= zone_end + 0.2
    ]
    return max(candidates) if candidates else None


def run_cut(project: Project) -> Project:
    direct = project.stages.get(Stage.DIRECT)
    if direct is None or direct.status != StageStatus.DONE or not project.beats:
        raise RuntimeError("Stage direct chưa xong hoặc beats rỗng — chạy `autoedit direct` trước.")

    project_dir = Path(project.project_dir)
    record = StageRecord.running()
    project.stages[Stage.CUT] = record
    project.save()

    try:
        master = _ensure_master_wav(project, project_dir)

        # 1) Kế hoạch run + biên cắt theo KHỞI ÂM ĐO TỪ AUDIO (3.1).
        # Bài học 11/06 (user nghe mất 1/3 từ "Meanwhile" cả khi đệm 250ms): align
        # có thể trễ tới ~0.5s sau khoảng nghỉ dài. Đệm tĩnh không đủ — phải ĐO:
        # trong vùng nghỉ giữa 2 từ (theo transcript), silence_end cuối cùng chính
        # là khởi âm thật của từ kế -> segment sau bắt đầu trước đó ONSET_GUARD.
        # Không đo được -> lấy TRỌN khoảng nghỉ vào segment sau (im lặng thừa vô
        # hại, mất từ là chí mạng). Segment được hở nhau trong source, cấm đè.

        # 0) Giãn nghỉ máy (hình thở 3.0 — DNA nhịp nghỉ) — ghi đè TOÀN BỘ field mỗi
        # lần chạy (reset 0 rồi điền) để chạy lại cut không cộng dồn.
        # SHOT THỞ 2.0: breathing reset về số NÃO gốc trước — budget micro tính theo
        # base, kéo sâu ô làm SAU (bẫy idempotent, MO_TA_SHOT_THO §6.2A).
        pz.reset_breathing_to_base(project.beats)
        micro = pz.plan_micro_pauses(project.beats, dna=pz.load_pause_dna(project.niche))
        by_id = {b.beat_id: b for b in project.beats}
        n_sent = sum(1 for bid in micro if pz._ends_sentence(by_id[bid].text))
        n_clause = sum(1 for bid in micro if not pz._ends_sentence(by_id[bid].text)
                       and pz._ends_clause(by_id[bid].text))
        for b in project.beats:
            b.micro_pause_after = micro.get(b.beat_id, 0.0)
        if micro:
            record.warnings.append(
                f"giãn nghỉ máy (DNA): {len(micro)} điểm ({n_sent} kết câu + {n_clause} "
                f"kết mệnh đề + {len(micro) - n_sent - n_clause} câu đinh), chèn tổng "
                f"+{sum(micro.values()):.1f}s (δ {min(micro.values()):.2f}-{max(micro.values()):.2f}s)"
            )

        # SHOT THỞ 2.0: kéo sâu ô đạt ngưỡng lên tầm editor (footage 4-10s)
        depth = pz.plan_breath_depth(project.beats, dna=pz.load_breath_dna(project.niche))
        if depth:
            added = sum(depth[bid] - by_id[bid].breathing_after for bid in depth)
            for bid, sec in depth.items():
                by_id[bid].breathing_after = sec
            record.warnings.append(
                f"kéo sâu ô thở (DNA lớp hình thở): {len(depth)} ô -> "
                f"{min(depth.values()):.1f}-{max(depth.values()):.1f}s, video dài thêm +{added:.1f}s"
            )

        # NGẮT NHỊP TRONG VOICE -> HÌNH THỞ (user 05/09): khoảng nghỉ >=1s giữa
        # 2 beat mà đo SẠCH TIẾNG = người đọc ngắt chủ động -> breathing_after
        # ĐÚNG BẰNG độ dài ngắt (ranh run cắt khoảng lặng khỏi voice, timeline
        # chèn lại y nguyên -> tổng thời lượng giữ, sourcer tự cấp shot thở).
        # Đặt SAU depth DNA: độ ngắt của người đọc thắng số máy (chỉ nâng, không hạ).
        silences = sil.detect_silences(master)
        ngat = []
        for a, b in zip(project.beats, project.beats[1:]):
            gap = b.start - a.end
            if (gap >= NGUONG_NGAT_S and gap > a.breathing_after
                    and _tieng_trong_vung(a.end, b.start, silences) <= TIENG_CHO_PHEP):
                a.breathing_after = round(gap, 2)
                ngat.append(gap)
        if ngat:
            record.warnings.append(
                f"ngắt nhịp trong voice -> hình thở: {len(ngat)} chỗ "
                f"({min(ngat):.1f}-{max(ngat):.1f}s) — giữ đúng độ dài ngắt của người đọc")

        # NHIP-M2 đoạn chèn: Δ editor khai (lệnh `insert`) — tiêu thụ Ở ĐÂY, chỗ sinh
        # timeline duy nhất (BAN_GIAO_NHIP_NHAC §7b). Validate lại phòng project.json
        # sửa tay: beat phải tồn tại + không phải beat cuối (total_end dựa segment cuối).
        beat_ids = {b.beat_id for b in project.beats}
        for ins in project.inserts:
            if ins.after_beat not in beat_ids:
                raise RuntimeError(
                    f"đoạn chèn sau beat {ins.after_beat}: beat không tồn tại — "
                    "sửa bằng `autoedit insert --remove` rồi khai lại")
            if ins.after_beat == project.beats[-1].beat_id:
                raise RuntimeError(
                    f"đoạn chèn sau beat {ins.after_beat} là beat CUỐI video — không hỗ trợ "
                    "(outro không có voice sau; kéo dài đuôi là việc của editor trong CapCut)")
            if ins.dur <= 0:
                raise RuntimeError(f"đoạn chèn sau beat {ins.after_beat}: dur {ins.dur} phải > 0")
        insert_map = {i.after_beat: i.dur for i in project.inserts}
        if insert_map:
            record.warnings.append(
                f"đoạn chèn (NHIP-M2): {len(insert_map)} chỗ, tổng +{sum(insert_map.values()):.1f}s — "
                + ", ".join(f"sau beat {b}: {d:.1f}s" for b, d in sorted(insert_map.items())))

        plans = tl.plan_segments(project.beats, inserts=insert_map)
        master_dur = ffprobe_duration(master) or project.beats[-1].end
        # (silences đã đo ở khối ngắt-nhịp phía trên — cùng master, không đo lại)

        first_onset = _onset_in_zone(0.0, plans[0].source_start, silences)
        plans[0].source_start = max(
            0.0,
            (first_onset - ONSET_GUARD) if first_onset is not None
            else plans[0].source_start - LEAD_PAD,
        )
        plans[-1].source_end = min(master_dur, plans[-1].source_end + TAIL_PAD)

        for i, (a, b) in enumerate(zip(plans, plans[1:])):
            word_end, word_start = a.source_end, b.source_start  # theo transcript
            gap = word_start - word_end
            tail = word_end + min(TAIL_PAD, max(gap, 0.0) * 0.4)
            onset = _onset_in_zone(word_end, word_start, silences)
            tieng = _tieng_trong_vung(word_end, word_start, silences)
            if tieng > TIENG_CHO_PHEP:
                # Vùng "nghỉ theo transcript" mà CÓ TIẾNG = align sót từ (bug 05/09:
                # câu 5s mất 2-3s voice — LI100 vứt 305s nguồn tại 125 ranh). CẤM
                # vứt: lấy trọn vùng vào segment sau — im lặng thừa vô hại,
                # mất từ là chí mạng.
                lead = tail
                record.warnings.append(
                    f"ranh segment {i + 1}->{i + 2}: vùng nghỉ {word_end:.2f}-"
                    f"{word_start:.2f}s có {tieng:.1f}s TIẾNG (align nghi sót từ) — "
                    "giữ trọn vào segment sau, không vứt voice")
            elif onset is not None and onset > tail:
                lead = max(tail, onset - ONSET_GUARD)
            else:
                lead = tail  # không đo được khởi âm -> trọn khoảng nghỉ vào segment sau
                if gap > 0.5:
                    record.warnings.append(
                        f"ranh giới segment {i + 1}->{i + 2}: không đo được khởi âm trong "
                        f"vùng nghỉ {word_end:.2f}-{word_start:.2f}s — lấy trọn khoảng nghỉ, "
                        "nghe kiểm tra mép file"
                    )
            a.source_end = tail
            b.source_start = lead

        tl.apply_timeline(plans)
        beat_timeline = tl.map_beats_to_timeline(project.beats, plans)

        # 2) Cắt từng segment từ master (3.4), fade 2 đầu (3.2), verify ffprobe
        seg_dir = project_dir / "segments"
        if seg_dir.exists():
            shutil.rmtree(seg_dir)  # chạy lại = đè sạch, pure function từ project.json
        seg_dir.mkdir(parents=True)

        segments: list[VoiceSegment] = []
        for i, plan in enumerate(plans, start=1):
            out = seg_dir / f"seg_{i:03d}.wav"
            _cut_segment(master, plan.source_start, plan.source_end, out)
            _verify_segment(out, plan.duration)
            segments.append(
                VoiceSegment(
                    segment_id=i,
                    path=str(out.relative_to(project_dir)),
                    source_start=plan.source_start,
                    source_end=plan.source_end,
                    timeline_start=plan.timeline_start,
                    timeline_end=plan.timeline_end,
                    beat_ids=plan.beat_ids,
                    breathing_after=plan.breathing_after,
                    micro_pause_after=plan.micro_pause_after,
                    insert_after=plan.insert_after,
                )
            )
    except Exception as exc:
        record.status = StageStatus.FAILED
        record.error = str(exc)
        project.save()
        raise

    # 3) Ghi kết quả: segments + timeline từng beat
    project.segments = segments
    for b in project.beats:
        ts, te = beat_timeline[b.beat_id]
        b.timeline_start, b.timeline_end = round(ts, 4), round(te, 4)
    # MUSIC SYNC M1: timeline vừa đổi -> music_plan cũ (nếu có) sai vị trí chương — xóa
    from autoedit.music.plan import mark_music_stale
    stale_msg = mark_music_stale(project)
    if stale_msg:
        record.warnings.append(stale_msg)
    # NHỊP (V2 Đợt 1c): ép phân bố shot theo hồ sơ niche — timeline vừa điền xong
    # là lúc duy nhất biết thoại từng beat dài bao nhiêu. Fail-open: nhịp lỗi thì
    # ghi cảnh báo, KHÔNG giết cut (video đều còn hơn không có video).
    try:
        from autoedit.nhip.ep import ap_dung as _nhip_ap_dung

        # Hồ sơ HIỆU LỰC: niche -> kênh ref -> retention — logic tách vào
        # nhip/hieu_luc.py (05/09) vì "đo lại sau dựng" của assembler cũng cần
        # đúng hồ sơ này để so; 2 nơi chép tay thì sớm muộn lệch nhau.
        from autoedit.nhip.hieu_luc import nap_hieu_luc as _nap_hl

        hs, _hl_log = _nap_hl(project)
        record.warnings.extend(_hl_log)
        record.warnings.extend(_nhip_ap_dung(project, hs))
    except Exception as exc:  # noqa: BLE001
        record.warnings.append(f"nhịp: bỏ qua ép ({exc})")
    record.status = StageStatus.DONE
    record.completed_at = datetime.now(timezone.utc).isoformat()
    project.save()

    _write_index(project, seg_dir)
    return project


# ----------------------------------------------------------------------------
def _ensure_master_wav(project: Project, project_dir: Path) -> Path:
    """WAV 48kHz master (RA_SOAT 0.5/3.4) — convert 1 lần, các lần sau dùng lại."""
    master = project_dir / "media" / "voice_master.wav"
    if master.is_file():
        return master
    master.parent.mkdir(parents=True, exist_ok=True)
    src = project_dir / project.inputs.voice_path
    result = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-ar", "48000", "-c:a", "pcm_s16le", str(master)],
        capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg convert master thất bại: {result.stderr[-300:]}")
    src_dur, dst_dur = ffprobe_duration(src), ffprobe_duration(master)
    if src_dur and dst_dur and abs(src_dur - dst_dur) > 0.1:
        raise RuntimeError(f"Master WAV lệch duration: gốc {src_dur:.2f}s vs master {dst_dur:.2f}s")
    project.voice_master_path = str(master.relative_to(project_dir))
    return master


def _cut_segment(master: Path, start: float, end: float, out: Path) -> None:
    dur = end - start
    fade_out_start = max(dur - FADE_SEC, 0)
    result = subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-ss", f"{start:.4f}", "-to", f"{end:.4f}", "-i", str(master),
         "-af", f"afade=t=in:d={FADE_SEC},afade=t=out:st={fade_out_start:.4f}:d={FADE_SEC}",
         "-c:a", "pcm_s16le", str(out)],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg cắt {out.name} thất bại: {result.stderr[-300:]}")


def _verify_segment(path: Path, expected_dur: float) -> None:
    actual = ffprobe_duration(path)
    if actual is None:
        raise RuntimeError(f"{path.name}: ffprobe không đọc được file vừa cắt")
    if abs(actual - expected_dur) > DURATION_TOLERANCE:
        raise RuntimeError(
            f"{path.name}: duration {actual:.3f}s lệch kế hoạch {expected_dur:.3f}s "
            f"(quá ±{DURATION_TOLERANCE * 1000:.0f}ms)"
        )


def _write_index(project: Project, seg_dir: Path) -> None:
    """INDEX.txt — người nghe đối chiếu (bài kiểm tra M4)."""
    by_id = {b.beat_id: b for b in project.beats}
    lines = [
        f"Project: {project.project_id}",
        f"Biên cắt: đuôi +{TAIL_PAD * 1000:.0f}ms; đầu = khởi âm ĐO từ audio -{ONSET_GUARD * 1000:.0f}ms "
        "(không đo được thì lấy trọn khoảng nghỉ)",
        "",
    ]
    for s in project.segments:
        first, last = by_id[s.beat_ids[0]], by_id[s.beat_ids[-1]]
        lines += [
            f"{Path(s.path).name}  [{s.source_end - s.source_start:.1f}s]",
            f"  source   : {s.source_start:.2f}s -> {s.source_end:.2f}s",
            f"  timeline : {s.timeline_start:.2f}s -> {s.timeline_end:.2f}s"
            + (f"  (+ hình thở {s.breathing_after:.1f}s sau đó)" if s.breathing_after else "")
            + (f"  (+ giãn nghỉ máy {s.micro_pause_after:.2f}s)" if s.micro_pause_after else "")
            + (f"  (+ ĐOẠN CHÈN {s.insert_after:.1f}s)" if s.insert_after else ""),
            f"  mở đầu   : \"{first.text[:60]}\"",
            f"  kết thúc : \"...{last.text[-60:]}\"",
            "",
        ]
    (seg_dir / "INDEX.txt").write_text("\n".join(lines), encoding="utf-8")
