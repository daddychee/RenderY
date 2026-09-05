"""Stage 6 — Assemble: ráp project.json thành draft CapCut 3 track (Phase 0).

Track: video_l1 (phủ kín theo coverage windows) + voice (segments M4) + music.
Pure function từ project.json (7.1): chạy lại sinh draft đè (overwrite).
Bài học CapCut: transcode chuẩn hóa (6.6), target ngắn hơn source >=3 frame (6.8),
asset path tuyệt đối tồn tại trước khi ghi (6.4 — verify trong package_draft).
"""

from __future__ import annotations

import json
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# MUSIC SYNC M1: hằng XFADE + hàm chương-timeline dời sang music/plan.py (stage music
# cần CÙNG số/logic — 2 bản sẽ lệch nhau). Alias tên cũ cho mọi chỗ gọi nội bộ.
from autoedit.music.plan import (
    MUSIC_XFADE,
    chapters_with_time as _chapters_with_time,
)
from autoedit.packager import coverage as cov
from autoedit.packager import ducking
from autoedit.packager.machine import MachineProfile
from autoedit.packager.packager import package_draft
from autoedit.packager.transcode import (
    cover_scale,
    ffprobe_dims,
    has_audio_stream,
    is_video,
    normalize_audio,
    normalize_image,
    normalize_video,
)
from autoedit.project import (
    Project,
    Stage,
    StageRecord,
    StageStatus,
    ffprobe_duration,
)

SEC = 1_000_000  # CapCut microsecond
SAFETY_US = 3 * SEC // 30  # 6.8: 3 frame @30fps
MUSIC_VOLUME = 0.2  # Phase 0: volume thấp cố định; ducking keyframe là Phase 1
# Tốc độ phát footage video trên track L1 (user chốt 2026-07-15: mọi footage chậm 10%).
# Chỉ video — ảnh/chart/slug giữ nguyên. Override từng lần chạy: `--footage-speed` (1.0 = gốc).
FOOTAGE_SPEED = 0.9
# SÀN TỐC ĐỘ (editor Hải + user chốt 05/09): mốc an toàn 0.8-1.2 — footage stock
# fps thấp mà slow dưới 0.8 là giật hình/drop frame (đo thật: clip 9s bị kéo 17s
# = 0.53x). Clip thiếu nguồn -> KHÔNG slow sâu nữa: chạy hết nguồn ở footage_speed
# rồi ĐÓNG BĂNG khung cuối (freeze frame) phủ nốt ô — thủ pháp dựng chuẩn, không giật.
SPEED_MIN = 0.8
FREEZE_TOI_THIEU_US = SEC // 2   # phần thiếu < 0.5s thì slow nhẹ thêm chút còn hơn chèn freeze


def run_assemble(
    project: Project,
    profile: MachineProfile,
    music_path: Optional[Path] = None,
    sfx_dir: Optional[Path] = None,
    sfx_fallback: Optional[Path] = None,
    music_lib: Optional[Path] = None,
    footage_speed: Optional[float] = None,
    credit: bool = False,
) -> Project:
    if footage_speed is None:
        footage_speed = FOOTAGE_SPEED
    src_stage = project.stages.get(Stage.SOURCE)
    if src_stage is None or src_stage.status != StageStatus.DONE:
        raise RuntimeError("Stage source chưa xong — chạy `autoedit source` trước.")

    project_dir = Path(project.project_dir)
    record = StageRecord.running()
    project.stages[Stage.ASSEMBLE] = record
    project.save()

    try:
        # Shot thở: chẻ cửa sổ theo picks THẬT (pick hụt ô nào -> ô đó giữ hành vi cũ;
        # 2.0: mỗi ô 1-3 miếng theo dur từng record, thứ tự list = thứ tự đặt)
        breath_specs: dict[int, list[float]] = {}
        for b in project.breath_shots:
            if b.asset_path:
                breath_specs.setdefault(b.beat_id, []).append(b.dur)
        windows = cov.apply_j_cuts(cov.split_breath_shots(
            cov.coverage_windows(project.beats, project.segments), breath_specs))
        # NHIP-M4: chẻ Δ theo lưới beat BÀI EDITOR (vùng không voice -> nhịp quyết 100%
        # mép cắt). Nhịp đo sẵn lúc `insert --music` (bài ngoài kho, không có record để
        # tra). Không có nhịp/tier C -> Δ giữ 1 cửa sổ như M3 (fail-open).
        # M4c: seed + mốc dời về cov.insert_grids — source pick footage gọi CÙNG hàm
        # nên số ô/mốc hai tầng tự khớp (không còn bản sao logic trong assembler).
        ins_grids = cov.insert_grids(project)
        if ins_grids:
            windows = cov.split_insert_windows(windows, ins_grids)
        total_end = project.segments[-1].timeline_end + project.segments[-1].breathing_after

        # MUSIC SYNC M3 (chỉ khi music-sync bật): M-CHANGE chọn điểm đổi nhạc = mép cắt
        # gần ranh giới chương, rồi M-ACCENT snap các mép còn lại về accent (sau J-cut,
        # trước invariant + đặt footage — MO_TA_MUSIC_SYNC §3 thứ tự đã rà)
        boundaries, targets = None, None
        if project.music_plan and music_lib is not None and music_path is None:
            from autoedit.music import plan as mplan
            from autoedit.music.library import _load_index
            chs = mplan.chapters_with_time(project)
            if chs:
                edges = [w.start for w in windows[1:]]
                boundaries, anchored = mplan.music_boundaries(chs, edges)
                m_index = _load_index(Path(music_lib))
                targets = mplan.timeline_accents(project, m_index, boundaries)
                hook_end = chs[1]["timeline_start"] if len(chs) > 1 else total_end
                exempt = {round(b, 2) for b, a in zip(boundaries, anchored) if a}
                st = cov.snap_to_accents(windows, targets, hook_end,
                                         tol=mplan.SNAP_TOL, lead=mplan.SNAP_LEAD,
                                         cap_ratio=mplan.SNAP_CAP, exempt=exempt)
                if st["snapped"]:
                    sh = st["shift_ms"]
                    record.warnings.append(
                        f"M-ACCENT: snap {st['snapped']}/{st['edges']} mép về accent−"
                        f"{mplan.SNAP_LEAD * 1000:.0f}ms (hook {st['hook']} · vào-ô-thở "
                        f"{st['breath']} · body {st['body']}), dịch "
                        f"{min(sh)}..{max(sh)}ms")
                n_anch = sum(anchored)
                if n_anch:
                    record.warnings.append(
                        f"M-CHANGE: {n_anch}/{len(chs) - 1} điểm đổi nhạc chương neo vào "
                        f"mép cắt (±{mplan.M_CHANGE_WIN:.0f}s, xfade "
                        f"{mplan.change_xfade_for(project.niche)}s niche {project.niche})")
                # NHIP-M1: mép GIỮA các miếng shot thở (ô beat_cut) dời về beat THẬT trên
                # boundary M-CHANGE vừa chốt — SAU snap (mép vào/ra ô đã yên vị), TRƯỚC
                # invariant + đặt footage. Số miếng giữ nguyên (bẫy ① NAM CHÂM).
                grid_ids = {b.beat_id for b in project.breath_shots
                            if b.beat_cut and b.asset_path}
                if grid_ids:
                    from autoedit.cutter.pause import load_breath_dna
                    beat_pts = mplan.timeline_beats(project, m_index, boundaries)
                    rst = cov.retime_breath_grid(
                        windows, beat_pts, grid_ids,
                        min_piece=float(load_breath_dna(project.niche).get("min_piece", 1.5)))
                    seen_k: dict[int, int] = {}
                    for b in project.breath_shots:  # dur mới -> project.json (SFX first_piece_end đọc)
                        nd = rst["durs"].get(b.beat_id)
                        if nd and b.asset_path:
                            k = seen_k.get(b.beat_id, 0)
                            if k < len(nd):
                                b.dur = nd[k]
                            seen_k[b.beat_id] = k + 1
                    record.warnings.append(
                        f"NHIP-M1: lưới beat ô thở — retime {rst['retimed']}/{len(grid_ids)} ô"
                        + (f", {rst['kept']} ô giữ mép cũ (lưới thiếu mốc)" if rst["kept"] else ""))

        errors = cov.check_coverage_invariants(windows, total_end)
        if errors:
            raise RuntimeError("Coverage không phủ kín: " + "; ".join(errors))

        placed_shots: list[float] = []
        content = _build_content(
            project, windows, music_path, record, project_dir, sfx_dir, sfx_fallback,
            music_lib, placed_shots=placed_shots, music_boundaries=boundaries,
            music_accents=targets, footage_speed=footage_speed, credit=credit,
        )
        # NHIP-M2: Δ đoạn chèn không có shot máy đặt (slug) -> loại khỏi MẪU SỐ phút,
        # không thì cpm/pstdev pha loãng -> báo động giả (BAN_GIAO §7c.3)
        insert_total = sum(w.end - w.start for w in windows if w.insert)
        _warn_pacing_dna(project, record, placed_shots, total_end - insert_total)
        # RA_SOAT 7.1: KHÔNG đè draft cũ — CapCut cache draft_id trong root_meta,
        # đè làm draft không mở được (bài học 12/06). Luôn sinh tên mới _V2, _V3...
        # Version = MAX hiện có + 1, KHÔNG điền lỗ trống (xóa _V4 cũ xong bản mới lại
        # thành _V4 "trẻ hơn V6" — bẫy đã cắn 2 lần, MO_TA_SHOT_THO §6.3).
        base_name = project.project_id.replace("-", "_").upper()[:46]
        root = profile.out_root()  # folder XUẤT draft (set-draft-root), fallback capcut_root
        draft_name = base_name if not (root / base_name).exists() else (
            f"{base_name}_V{_next_version(root, base_name)}")
        draft_dir = package_draft(content, draft_name, profile)
    except Exception as exc:
        record.status = StageStatus.FAILED
        record.error = str(exc)
        project.save()
        raise

    project.draft_path = str(draft_dir)

    # SỔ NGUỒN GỐC (RenderY): xuất cạnh draft để đi cùng khi copy sang máy editor.
    # Lưới an toàn — sổ hỏng KHÔNG được giết draft đã dựng xong.
    try:
        from autoedit.packager.sourcebook import write_sourcebook

        write_sourcebook(project, draft_dir)
    except Exception as exc:
        record.warnings.append(f"⚠ Không ghi được sổ nguồn footage ({exc}) — "
                               "draft vẫn dùng được, tra nguồn trong project.json")

    # ĐO LẠI SAU DỰNG (user duyệt 05/09): draft tự chấm nhịp của chính nó —
    # so với hồ sơ hiệu lực, chênh >50% cảnh báo to (bug ép-nhịp-chết-im-lặng
    # kiểu LI095 04/09 sẽ hiện ngay ở đây thay vì đợi người mở CapCut).
    try:
        from autoedit.nhip.do_draft import do_nhip_draft, doi_chieu_hs

        record.warnings.append(doi_chieu_hs(project, do_nhip_draft(draft_dir)))
    except Exception as exc:  # noqa: BLE001 — thước hỏng không được giết draft
        record.warnings.append(f"đo lại sau dựng: bỏ qua ({str(exc)[:120]})")

    record.status = StageStatus.DONE
    record.completed_at = datetime.now(timezone.utc).isoformat()
    project.save()
    return project


# ----------------------------------------------------------------------------
def _next_version(root: Path, base_name: str) -> int:
    """Suffix version kế = max(_V*) hiện có + 1 (min 2) — không điền lỗ trống."""
    versions = [2]
    for p in root.glob(f"{base_name}_V*"):
        tail = p.name[len(base_name) + 2:]
        if tail.isdigit():
            versions.append(int(tail) + 1)
    return max(versions)


def _warn_pacing_dna(project, record, shot_durs: list[float], total_end: float) -> None:
    """Mảnh B DNA d1 (MO_TA_VAN_HANH_DNA_D1 §2c): so pacing video vừa ráp với dna.json
    của niche -> 0-2 dòng record.warnings (report.html tự hiện). Validator PHỤ:
    thiếu niche/dna.json thì im lặng; lỗi gì cũng KHÔNG được chặn assemble."""
    if not project.niche:
        return
    try:
        from autoedit.library.dna import check_pacing, load_dna
        from autoedit.library.profile import niche_dir, resolve_library_root

        dna = load_dna(niche_dir(project.niche, root=resolve_library_root(None)))
        if dna:
            record.warnings.extend(check_pacing(shot_durs, total_end / 60, dna))
    except Exception as exc:
        record.warnings.append(f"pacing DNA: validator lỗi ({exc}) — bỏ qua, draft không ảnh hưởng")


def _build_content(project, windows, music_path, record, project_dir: Path,
                   sfx_dir=None, sfx_fallback=None, music_lib=None, music_boundaries=None,
                   placed_shots: Optional[list] = None,
                   music_accents: Optional[list] = None,
                   footage_speed: float = FOOTAGE_SPEED,
                   credit: bool = False) -> dict:
    from pycapcut import (
        AudioMaterial,
        AudioSegment,
        ScriptFile,
        Timerange,
        TrackType,
        VideoMaterial,
        VideoSegment,
    )

    script = ScriptFile(1920, 1080, fps=30)
    script.add_track(TrackType.video, "video_l1")
    script.add_track(TrackType.audio, "voice")
    script.add_track(TrackType.audio, "music", relative_index=1)

    # ---------------- voice: segments M4 đặt theo timeline -------------------
    for seg in project.segments:
        f = project_dir / seg.path
        dur_us = int((seg.source_end - seg.source_start) * SEC)
        material = AudioMaterial(str(f))
        dur_us = min(dur_us, material.duration - SAFETY_US)
        script.add_segment(
            AudioSegment(material, Timerange(int(seg.timeline_start * SEC), dur_us)),
            "voice",
        )

    # ---------------- video L1: coverage windows -----------------------------
    shots_by_beat = {s.beat_id: s for s in project.shots}
    breath_q: dict[int, list] = {}  # hàng đợi miếng theo beat — cửa sổ đi theo đúng thứ tự
    for b in project.breath_shots:
        if b.asset_path:
            breath_q.setdefault(b.beat_id, []).append(b)
    norm_dir = project_dir / "media" / "norm"
    kb_log: list[float] = []  # Ken Burns f2: mức zoom từng ảnh đã keyframe
    cuts_log: list[tuple[float, bool]] = []  # S3-HOOK: mọi mép miếng L1 = mốc cut
    credit_log: list[tuple[float, float, str]] = []  # VD4: (start, end, asset_rel) từng miếng L1
    holes: list[tuple[float, float, int]] = []  # ô trống L1 — PHẢI lấp slug (xem dưới)
    ins_holes: list[tuple[float, float, int]] = []  # NHIP-M2: Δ đoạn chèn — slug giữ chỗ
    # M4c: pick footage Δ từ source (index list = index ô lưới — cùng cov.insert_grids
    # nên thứ tự cửa sổ = thứ tự pick; đếm ins_seen để map). Δ vẫn NGOÀI placed_shots
    # (pacing) / cuts_log (S3) / credit_log — giữ nguyên các luật loại trừ của M2.
    ins_picks = {i.after_beat: i.footage_picks for i in project.inserts if i.footage_picks}
    ins_seen: dict[int, int] = {}
    ins_filled: dict[str, int] = {}
    for w in windows:
        if w.insert:
            idx = ins_seen.get(w.beat_id, 0)
            ins_seen[w.beat_id] = idx + 1
            picks = ins_picks.get(w.beat_id)
            pick = picks[idx] if picks and idx < len(picks) else None
            if pick is not None and pick.path:
                # đặt clip thật; hỏng/không chuyển mã được -> rơi xuống slug (fail-open)
                if _place_video_l1(script, record, project_dir, norm_dir, pick.path,
                                   w.start, w.end, w.beat_id, kb_log=kb_log,
                                   footage_speed=footage_speed):
                    ins_filled[pick.source or "?"] = ins_filled.get(pick.source or "?", 0) + 1
                    continue
            ins_holes.append((w.start, w.end, w.beat_id))
            continue
        if w.breath_shot:  # cửa sổ shot thở (MO_TA_SHOT_THO §2b/§6) — 1 clip/miếng
            bs = breath_q[w.beat_id].pop(0)  # split theo chính picks -> luôn đủ
            if _place_video_l1(script, record, project_dir, norm_dir, bs.asset_path,
                               w.start, w.end, w.beat_id, cuts_log=cuts_log,
                               footage_speed=footage_speed, credit_log=credit_log):
                if placed_shots is not None:
                    placed_shots.append(w.end - w.start)
            else:
                holes.append((w.start, w.end, w.beat_id))
            continue
        shot = shots_by_beat.get(w.beat_id)
        if shot is None or not shot.asset_path:
            record.warnings.append(
                f"beat {w.beat_id}: không có asset (needs_human) — timeline hở "
                f"{w.start:.1f}-{w.end:.1f}s, editor tự đắp"
            )
            holes.append((w.start, w.end, w.beat_id))
            continue
        # F5 shot_count: 1 clip chính + extra_shots -> chia cửa sổ thành N khoảng con
        # liền khít; mỗi clip phủ 1 khoảng. N=1 -> nguyên cửa sổ (hành vi cũ y hệt).
        # Chỉ chia phần THOẠI — shot cuối phủ trọn ô thở (d2: ô thở = 1 hình giữ).
        clips = [shot.asset_path] + [e.asset_path for e in shot.extra_shots]
        subs = cov.split_window(w.start, w.end, len(clips), tail=w.tail_dur)
        for asset_rel, (sub_start, sub_end) in zip(clips, subs):
            if _place_video_l1(script, record, project_dir, norm_dir,
                               asset_rel, sub_start, sub_end, w.beat_id,
                               kb_log=kb_log, cuts_log=cuts_log,
                               footage_speed=footage_speed, credit_log=credit_log):
                if placed_shots is not None:
                    placed_shots.append(sub_end - sub_start)
            else:
                holes.append((sub_start, sub_end, w.beat_id))

    # LẤP MỌI Ô TRỐNG bằng slug (bug DS3-084 _V2.._V4): main track CapCut có tính
    # NAM CHÂM — mở draft là mọi lỗ hở bị dồn sạch, footage sau lỗ trượt khỏi voice
    # (DS3-084: 27 lỗ needs_human = trượt tích lũy -187s, footage "hết" ở 18:36 trong
    # khi voice 21:30). Slug = ảnh tối "EDITOR ĐẮP FOOTAGE" giữ chỗ đúng khoảng —
    # sync sống, editor nhìn timeline thấy ngay ô cần đắp. Slug KHÔNG vào
    # placed_shots (pacing DNA) / cuts_log (S3-HOOK) / kb_log (không Ken Burns).
    if ins_filled:
        record.warnings.append(
            "M4c Δ footage thật: " + " · ".join(f"{src} {n} ô" for src, n in
                                                sorted(ins_filled.items())))
    for b, picks in ins_picks.items():
        if ins_seen.get(b, 0) != len(picks):
            record.warnings.append(
                f"M4c Δ sau beat {b}: số ô lưới ({ins_seen.get(b, 0)}) ≠ số pick "
                f"({len(picks)}) — spec Δ đổi sau source? chạy lại `autoedit source`; "
                "ô lệch giữ slug")
    if ins_holes:
        by_beat: dict[int, list] = {}
        for s, e, b in ins_holes:
            by_beat.setdefault(b, []).append((s, e))
        parts = []
        for b, ivs in by_beat.items():
            ivs.sort()
            tot = ivs[-1][1] - ivs[0][0]
            if len(ivs) > 1:   # NHIP-M4: Δ đã chẻ theo lưới beat bài editor
                ds = [f"{e - s:.1f}" for s, e in ivs]
                parts.append(f"sau beat {b}: {ivs[0][0]:.1f}-{ivs[-1][1]:.1f}s = "
                             f"{len(ivs)} hình theo nhịp ({'/'.join(ds)}s)")
            else:
                parts.append(f"sau beat {b}: {ivs[0][0]:.1f}-{ivs[0][1]:.1f}s (1 hình)")
        record.warnings.append(
            f"NHIP-M2/M4 đoạn chèn: {len(by_beat)} Δ tổng "
            f"{sum(i[-1][1] - i[0][0] for i in by_beat.values()):.1f}s "
            f"({'; '.join(parts)}) — slug giữ chỗ, editor đắp footage")
    if holes or ins_holes:
        _fill_holes_with_slug(script, record, norm_dir, holes + ins_holes)

    if kb_log:
        record.warnings.append(
            f"Ken Burns f2: {len(kb_log)} ảnh zoom 100%→"
            f"{'/'.join(f'{z:.0%}' for z in kb_log)} (keyframe scale)")

    # ---------------- music ---------------------------------------------------
    # Ưu tiên --music (1 file loop, override tay); không thì auto chọn theo chương từ thư viện
    if music_path is not None:
        music_path = Path(music_path).resolve()
        if music_path.suffix.lower() != ".wav":
            # mp3 VBR: duration header lệch số CapCut đo -> relink (bài học 12/06)
            music_path = normalize_audio(music_path, norm_dir / f"{music_path.stem}.wav")
        m = AudioMaterial(str(music_path))
        total_end = project.segments[-1].timeline_end + project.segments[-1].breathing_after
        want_us = int(total_end * SEC)
        chunk = m.duration - SAFETY_US  # 1 vòng nhạc
        cursor, n_loops = 0, 0
        while cursor < want_us:
            seg_us = min(chunk, want_us - cursor)
            script.add_segment(
                AudioSegment(m, Timerange(cursor, seg_us),
                             source_timerange=Timerange(0, seg_us), volume=MUSIC_VOLUME),
                "music",
            )
            cursor += seg_us
            n_loops += 1
        if n_loops > 1:
            record.warnings.append(
                f"nhạc ({m.duration / SEC:.0f}s) ngắn hơn video ({total_end:.0f}s) — loop {n_loops} vòng"
            )
    elif music_lib is not None:
        _add_music_by_chapter(script, project, record, project_dir, Path(music_lib),
                              boundaries=music_boundaries)
    else:
        record.warnings.append("không có nhạc — truyền --music hoặc --music-lib")
    _duck_music(script, project, record)  # F8: keyframe volume SAU khi nhạc đặt xong
    _add_ambient(script, project, record)  # C1+S2: ambient ô thở (chủ thể thắng cảnh)
    _add_drone(script, project, record)    # S1: drone nền suốt video
    _add_subject_sfx(script, project, record)  # S2: tiếng chủ thể trong voice
    # S3 whoosh auto ĐÃ BỎ (PB12: 0/88 whoosh editor nằm ở mốc vào ô thở; whoosh thật
    # bám TEXT hiện lên — overlay-SFX lo; backlog chapter-title card). Dọn log lần trước.
    project.whoosh_log = []

    # ---------------- chart PiP nửa màn (Phase 1 Nhóm B half) -----------------
    _add_pip_charts(script, project, record, project_dir)

    # ---------------- info-card nửa màn (Phase 2B Req 6) ----------------------
    _add_info_cards(script, project, record, project_dir)

    # ---------------- overlay: text (keyframe) + SFX (Phase 1 Nhóm A) ---------
    _add_overlays(script, project, record, project_dir, sfx_dir, sfx_fallback)

    # ---------------- chữ chạy theo voice từng cụm (Phase 2A Req 3) -----------
    _add_text_sequences(script, project, record, project_dir)

    # ---------------- ghi công kênh nguồn ở góc (VD4, --credit) ---------------
    if credit:
        _add_credit_overlays(script, project, record, credit_log)

    # ---------------- SFX khi biểu đồ mọc (Phase 2A Req 2) --------------------
    _add_chart_sfx(script, project, record, project_dir, sfx_dir, sfx_fallback)

    # ---------------- S3-HOOK: hit/whoosh/click tại cut trong hook ------------
    # Chạy CUỐI chuỗi audio: UI-SFX (overlay/chart) giữ chỗ trước, S3 né bằng gap.
    _add_hook_sfx(script, project, record, cuts_log, accents=music_accents)

    content = json.loads(script.dumps())
    # has_audio phải khớp thực tế (bài học 12/06: photo khai has_audio=true
    # khiến CapCut nghi file hỏng): ảnh = False, video probe stream thật
    for m in content["materials"]["videos"]:
        if m.get("type") == "photo":
            m["has_audio"] = False
        elif m.get("path"):
            m["has_audio"] = has_audio_stream(Path(m["path"]))
    return content


KEN_BURNS_ZOOM = (1.20, 1.30)  # f2 v1 (user chốt 2026-07-09): ảnh đầu 100% -> cuối 120-130%


def _ken_burns_zoom(name: str) -> float:
    """Mức zoom cuối deterministic theo tên ảnh (crc32 — cùng khuôn seed shot thở 2.0):
    đa dạng giữa các ảnh, dựng lại ra đúng số cũ."""
    lo, hi = KEN_BURNS_ZOOM
    steps = round((hi - lo) * 100)
    return lo + (zlib.crc32(name.encode("utf-8")) % (steps + 1)) / 100


def _freeze_frame(asset: Path, norm_dir: Path) -> Path | None:
    """Khung CUỐI của clip -> JPEG (freeze frame phủ phần ô thiếu nguồn — sàn
    tốc độ 05/09). None nếu ffmpeg không rút được (caller ghi warning, ô hở đuôi)."""
    import subprocess

    dich = norm_dir / f"freeze_{asset.stem}.jpg"
    if dich.is_file():
        return dich
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-sseof", "-0.2", "-i", str(asset),
         "-frames:v", "1", "-q:v", "3", str(dich)],
        capture_output=True, timeout=60)
    return dich if r.returncode == 0 and dich.is_file() else None


def _place_video_l1(script, record, project_dir: Path, norm_dir: Path,
                    asset_rel: str, start: float, end: float, beat_id: int,
                    kb_log: Optional[list] = None,
                    cuts_log: Optional[list] = None,
                    footage_speed: float = FOOTAGE_SPEED,
                    credit_log: Optional[list] = None) -> bool:
    """Đặt 1 clip vào track video_l1 phủ khoảng [start, end]. Dùng cho cả beat 1-shot lẫn
    từng khoảng con của beat multi-shot. Asset hỏng -> BỎ QUA (chừa hở cho editor), không giết draft.
    Trả True nếu ĐÃ đặt (pacing validator đếm shot thật theo đây)."""
    from pycapcut import ClipSettings, KeyframeProperty, Timerange, VideoMaterial, VideoSegment

    asset = project_dir / asset_rel
    # Chuẩn hóa: 1 asset HỎNG (svg/corrupt) KHÔNG được giết cả draft -> bỏ qua, chừa
    # chỗ cho editor (như needs_human). Bài học 15/06: entity tải về .svg ffmpeg ko đọc.
    try:
        if is_video(asset):
            asset = normalize_video(asset, norm_dir / asset.name)  # 6.6
        else:
            asset = normalize_image(asset, norm_dir / f"{asset.stem}.jpg")
    except Exception as exc:
        record.warnings.append(
            f"beat {beat_id}: asset {asset.name} hỏng/không chuyển mã được ({exc}) — "
            f"BỎ QUA, timeline hở {start:.1f}-{end:.1f}s, editor tự đắp"
        )
        return False
    material = VideoMaterial(str(asset))
    # Mốc microsecond phải LÀM TRÒN (round), KHÔNG cắt cụt (int): 4.18*SEC =
    # 4179999.9999 -> int = 4179999, lệch 1us so với mép trước (4180000) -> SegmentOverlap.
    # Tính want từ 2 mép ĐÃ round -> khoảng con kề nhau khít (kể cả mép chia shot_count).
    start_us = round(start * SEC)
    want_us = round(end * SEC) - start_us
    # PHỦ KÍN ô (PRD 3.2): KHÔNG bao giờ để hở. Clip ngắn -> kéo giãn (slow-mo) cho đầy;
    # ảnh giữ nguyên cả ô (Ken Burns là Phase 1).
    speed = None
    cover = 1.0
    clip = None
    if material.material_type == "photo":
        source = Timerange(0, want_us)
        # V1: ảnh KHÔNG crop file (giữ nội dung tài liệu/poster) — phủ khung 16:9 bằng
        # scale. Ảnh 16:9 -> cover=1.0, hành vi y như cũ; probe lỗi -> 1.0 (fail-open).
        dims = ffprobe_dims(asset)
        cover = cover_scale(*dims) if dims else 1.0
        if cover > 1.0 and want_us <= 2 * ducking.EDGE_GUARD_US:
            # ảnh quá ngắn cho Ken Burns -> scale TĨNH (không trộn với keyframe — F8)
            clip = ClipSettings(scale_x=cover, scale_y=cover)
    else:
        avail = material.duration - SAFETY_US
        if avail >= round(want_us * footage_speed):
            # Clip đủ nguồn cho ô ở footage_speed: CHỈ truyền speed, source để pycapcut
            # tự tính (= target*speed, từ 0). KHÔNG truyền cả source lẫn speed — pycapcut
            # sẽ tính lại target = round(source/speed), lệch 1µs với mép beat -> SegmentOverlap.
            source = None
            speed = footage_speed
        else:
            speed = avail / want_us           # <1 = slow-mo sâu hơn footage_speed
            thieu_us = want_us - round(avail / footage_speed)
            if speed < SPEED_MIN and thieu_us >= FREEZE_TOI_THIEU_US:
                # SÀN 0.8 (user 05/09): thay vì slow sâu, chạy clip trọn nguồn ở
                # footage_speed rồi freeze khung cuối phủ nốt — không giật hình.
                dur_v_us = want_us - thieu_us
                seg_v = VideoSegment(material, Timerange(start_us, dur_v_us),
                                     speed=footage_speed)
                script.add_segment(seg_v, "video_l1")
                freeze = _freeze_frame(asset, norm_dir)
                if freeze is not None:
                    m_f = VideoMaterial(str(freeze))
                    script.add_segment(
                        VideoSegment(m_f, Timerange(start_us + dur_v_us, thieu_us),
                                     source_timerange=Timerange(0, thieu_us)),
                        "video_l1")
                record.warnings.append(
                    f"beat {beat_id}: clip ngắn ({material.duration / SEC:.1f}s cho ô "
                    f"{(end - start):.1f}s) — chạy {footage_speed}x + freeze khung cuối "
                    f"{thieu_us / SEC:.1f}s (sàn tốc độ {SPEED_MIN}, không slow sâu nữa); "
                    "editor nên swap clip dài hơn"
                    + ("" if freeze is not None else " — RÚT FRAME LỖI, ô hở đuôi"))
                if cuts_log is not None:
                    cuts_log.append((start, False))
                    cuts_log.append((start + dur_v_us / SEC, True))
                if credit_log is not None:
                    credit_log.append((start, end, asset_rel))
                return True
            # tới đây: hoặc thiếu < 0.5s (slow nhẹ quá sàn một chút, chấp nhận),
            # hoặc speed >= SPEED_MIN (slow trong mốc an toàn 0.8-1.2)
            source = Timerange(0, avail)     # clip ngắn -> dùng trọn, giãn cho đầy ô
            record.warnings.append(
                f"beat {beat_id}: clip ngắn ({material.duration / SEC:.1f}s không đủ "
                f"{(end - start):.1f}s × {footage_speed}) — kéo giãn slow-mo {speed:.2f}x "
                "cho phủ kín; editor nên swap clip dài hơn"
            )
    # Giữ NGUYÊN vị trí footage (full-frame): card phủ nửa phải, footage hiện nửa trái.
    seg = VideoSegment(
        material,
        Timerange(start_us, want_us),  # target LUÔN = ô đầy đủ
        source_timerange=source,
        speed=speed,
        clip_settings=clip,
    )
    # Ken Burns f2 v1 (user chốt 2026-07-09): ảnh không đứng yên — zoom-in về tâm
    # cover -> cover x 120-130% (V1: khởi động từ mức PHỦ khung thay 100% — ảnh 16:9
    # thì cover=1.0, y như cũ). Chỉ ẢNH (video có chuyển động thật). Ảnh source_start=0
    # nên không dính bẫy time_offset theo-file-nguồn của ducking F8.
    if material.material_type == "photo" and want_us > 2 * ducking.EDGE_GUARD_US:
        zoom = _ken_burns_zoom(asset.name)
        seg.add_keyframe(KeyframeProperty.uniform_scale, 0, cover)
        seg.add_keyframe(KeyframeProperty.uniform_scale,
                         want_us - ducking.EDGE_GUARD_US, round(cover * zoom, 4))
        if kb_log is not None:
            kb_log.append(zoom)
    script.add_segment(seg, "video_l1")
    if cuts_log is not None:  # S3-HOOK: mốc cut + cut-vào-ẢNH (click bám ảnh)
        cuts_log.append((start, material.material_type == "photo"))
    if credit_log is not None:  # VD4 ghi công: miếng nào từ asset nào (slug/card không qua đây)
        credit_log.append((start, end, asset_rel))
    return True


def _slug_image(norm_dir: Path, hold: bool = False) -> Path:
    """Ảnh slug 1920x1080 nền tối — render 1 lần/project/biến thể.

    A′ (e2 §5): ô HOLD (hình giữ lâu trong Δ) có ảnh RIÊNG dặn editor đặt cảnh
    RỘNG/nhiều chi tiết (craft: mắt cần thời gian đọc hình dài; hình ngắn = cận/chi
    tiết). Máy không biết editor sẽ đắp gì -> truyền luật cho người, đúng chỗ."""
    out = norm_dir / ("_editor_slug_hold.jpg" if hold else "_editor_slug.jpg")
    if out.exists():
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "DejaVu Sans"  # hỗ trợ dấu tiếng Việt (như charts)
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor="#14181d")
    if hold:
        fig.text(0.5, 0.54, "EDITOR: HOLD — CẢNH RỘNG / NHIỀU CHI TIẾT", color="#c9a227",
                 ha="center", va="center", fontsize=44, fontweight="bold")
        fig.text(0.5, 0.44, "(hình giữ lâu làm điểm nhấn — đặt cảnh đáng ngắm, mắt cần thời gian đọc)",
                 color="#8a7a3f", ha="center", va="center", fontsize=24)
    else:
        fig.text(0.5, 0.54, "EDITOR: ĐẮP FOOTAGE Ở ĐÂY", color="#96a0ab",
                 ha="center", va="center", fontsize=52, fontweight="bold")
        fig.text(0.5, 0.44, "(ô needs_human — máy giữ chỗ để CapCut không dồn timeline)",
                 color="#5c656f", ha="center", va="center", fontsize=24)
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out


def _fill_holes_with_slug(script, record, norm_dir: Path, holes) -> None:
    """Lấp ô trống trên video_l1 bằng slug — main track CapCut là track NAM CHÂM,
    không cho lỗ hở: draft có lỗ thì CapCut lúc MỞ tự dồn mọi segment về trước và
    ghi đè draft_content.json, footage sau lỗ lệch voice tích lũy (bug DS3-084).
    Slug là ảnh nên không Ken Burns / không tính pacing DNA / không mốc cut S3."""
    from pycapcut import Timerange, VideoMaterial, VideoSegment

    try:
        img = _slug_image(norm_dir)
    except Exception as exc:  # slug là lưới an toàn — hỏng thì cảnh báo to, không giết draft
        record.warnings.append(
            f"⚠ SLUG LỖI ({exc}) — {len(holes)} lỗ hở KHÔNG lấp được: CapCut sẽ dồn "
            "track video mất sync, editor PHẢI tự chèn giữ chỗ trước khi kéo timeline")
        return
    # A′ (e2 §5): trong nhóm ô CÙNG beat ≥4 ô (= Δ đã chẻ lưới), ô dài ≥1,5× trung vị
    # là HOLD -> ảnh slug riêng dặn "cảnh rộng". Luật chung với source M4c (1 luật 2 nơi).
    from autoedit.packager.coverage import insert_hold_flags

    hold_keys: set[tuple[float, int]] = set()
    by_beat: dict[int, list[tuple[float, float]]] = {}
    for s, e, b in holes:
        by_beat.setdefault(b, []).append((s, e))
    for b, ivs in by_beat.items():
        flags = insert_hold_flags([e - s for s, e in ivs])
        hold_keys.update((s, b) for (s, e), f in zip(ivs, flags) if f)
    # NHIP-M4: MỖI ô một VideoMaterial RIÊNG. Trước đây 1 Δ = 1 slug nên không lộ;
    # lưới beat đẻ 11 slug thì dùng CHUNG 1 material -> CapCut hiển thị sai vị trí
    # (file JSON ghi đúng mốc nhưng UI dồn cả cụm xuống cuối video — user bắt 2026-07-20,
    # 4 bản draft liên tiếp). Material dùng lại giữa nhiều segment ảnh là ổ bug CapCut.
    for start, end, beat_id in holes:
        start_us = round(start * SEC)
        want_us = round(end * SEC) - start_us
        if want_us <= 0:
            continue
        use = img
        if (start, beat_id) in hold_keys:
            try:
                use = _slug_image(norm_dir, hold=True)
            except Exception:
                use = img                      # ảnh hold lỗi -> slug thường, không chết
        seg = VideoSegment(VideoMaterial(str(use)), Timerange(start_us, want_us),
                           source_timerange=Timerange(0, want_us))
        script.add_segment(seg, "video_l1")
    # sắp lại theo thời gian: pycapcut giữ nguyên thứ tự ADD, mà slug được add SAU
    # toàn bộ footage -> track có segment "đi lùi", CapCut đọc tuần tự thì dồn sạch.
    trk = script.tracks.get("video_l1")
    if trk is not None:
        trk.segments.sort(key=lambda s: s.target_timerange.start)
    record.warnings.append(
        f"slug: lấp {len(holes)} ô trống (beat {', '.join(str(b) for _, _, b in holes)}) "
        "— giữ sync vì main track CapCut không cho hở; editor swap footage tại các slug")


def _add_pip_charts(script, project, record, project_dir: Path) -> None:
    """Đặt chart NỬA MÀN (layout=half) lên track video `layer2` làm PiP.
    Footage beat vẫn chạy full-frame ở video_l1 phía dưới; chart 1920x1080 bị
    scale 0.5 -> 960x540 rồi dời sang phải (transform_x dương). Chỉ thêm track
    khi thực sự có chart (tránh track rỗng — bài học P1.3)."""
    from pycapcut import (
        ClipSettings,
        Timerange,
        TrackType,
        VideoMaterial,
        VideoSegment,
    )

    # KHÔNG đặt PiP nửa màn nếu beat đã là chart ĐẦY màn (route=graphic) — tránh 2 biểu
    # đồ đè nhau khi LLM để lỗi layout=half + route=graphic (bug 15/06).
    beats_pip = [
        b for b in project.beats
        if b.graphic_asset and b.timeline_start is not None
        and b.sourcing_route != "graphic"
    ]
    if not beats_pip:
        return
    _ensure_layer2(script)
    norm_dir = project_dir / "media" / "norm"
    n = 0
    for beat in beats_pip:
        asset = project_dir / beat.graphic_asset
        if not asset.exists():
            record.warnings.append(
                f"beat {beat.beat_id}: chart PiP {beat.graphic_asset} mất file — bỏ"
            )
            continue
        # crop_16x9=False: chart 1920x1080 tự render — tỉ lệ chủ đích, cấm cắt (V1)
        asset = normalize_video(asset, norm_dir / asset.name, crop_16x9=False)
        material = VideoMaterial(str(asset))
        want_us = int((beat.end - beat.start) * SEC)  # PiP phủ đúng ô beat
        src_us = min(want_us, material.duration - SAFETY_US)
        if src_us <= 0:
            continue
        script.add_segment(
            VideoSegment(
                material,
                Timerange(int(beat.timeline_start * SEC), src_us),
                source_timerange=Timerange(0, src_us),
                # scale 0.5 -> 960x540; transform_x sang phải, giữ tâm dọc
                clip_settings=ClipSettings(
                    scale_x=0.5, scale_y=0.5, transform_x=0.42, transform_y=0.0
                ),
            ),
            "layer2",
        )
        n += 1
    if n:
        record.warnings.append(f"chart PiP: {n} biểu đồ nửa màn đặt lên track layer2")




def _lay_music(script, material, start_s, dur_s, track, xf, src_offset=0.0,
               volume=MUSIC_VOLUME) -> None:
    """Đặt 1 bài phủ [start_s, start_s+dur_s] trên 1 track (loop nếu ngắn) + fade in/out.
    src_offset: điểm bắt đầu TRONG bài (giây) — canh cao trào (M-N3); hết bài thì vòng về 0.
    volume: mức tĩnh (M-VOL M2: hook to hơn body theo niche — mặc định 0.2 như cũ)."""
    from pycapcut import AudioSegment, Timerange

    avail = material.duration - SAFETY_US
    if avail <= 0:
        return
    cursor = int(start_s * SEC)
    end = cursor + int(dur_s * SEC)
    xf_us = int(xf * SEC)
    src_cur = min(int(src_offset * SEC), max(0, avail - 1))   # offset nằm trong bài
    first = True
    while cursor < end:
        seg_us = min(avail - src_cur, end - cursor)
        if seg_us <= 0:                       # hết bài -> vòng lại đầu
            src_cur = 0
            continue
        seg = AudioSegment(material, Timerange(cursor, seg_us),
                           source_timerange=Timerange(src_cur, seg_us), volume=volume)
        is_last = cursor + seg_us >= end
        fin = xf_us if first else 0
        fout = min(xf_us, seg_us // 2) if is_last else 0
        if fin or fout:
            seg.add_fade(fin, fout)
        script.add_segment(seg, track)
        cursor += seg_us
        src_cur += seg_us
        first = False


def _add_music_by_chapter(script, project, record, project_dir: Path, music_lib: Path,
                          boundaries=None) -> None:
    """Auto chọn nhạc theo mood từng chương (THU_VIEN mục 5) + ghép 2 track crossfade.
    Đổi bài khi đổi chương; luân phiên track music/music2 để crossfade overlap được.
    MUSIC SYNC M1: có project.music_plan (stage music đã chọn + neo offset) -> dùng
    nguyên, KHÔNG chọn lại/KHÔNG đếm usage (stage music đếm rồi); không có -> tự chọn
    như cũ (đường cũ nguyên vẹn).
    M3 M-CHANGE: boundaries (điểm đổi nhạc đã neo vào mép cắt video) + xfade theo niche
    (deepsea gần-thẳng); offset điều chỉnh giữ BẤT BIẾN P = vị-trí-trong-bài tại boundary
    (accent vẫn rơi đúng điểm đổi, kể cả boundary dời/xfade ngắn lại)."""
    from pycapcut import AudioMaterial, TrackType

    from autoedit.music.library import TRACKS_DIR, _load_index, load_usage, save_usage
    from autoedit.music.select import select_music

    chapters = _chapters_with_time(project)
    if not chapters:
        record.warnings.append("thiếu outline chương — bỏ nhạc tự chọn")
        return
    sync = bool(project.music_plan)
    if sync:
        from autoedit.music.plan import change_xfade_for
        xf = change_xfade_for(project.niche)
    else:
        xf = MUSIC_XFADE
    bounds = boundaries if (sync and boundaries) else [c["timeline_start"] for c in chapters]
    if project.music_plan:
        pick_by_ch = {p.chapter_id: {"file": p.file, "start_offset": p.start_offset}
                      for p in project.music_plan}
        usage = None                                 # stage music đã đếm — không đếm đôi
    else:
        index = _load_index(music_lib)
        if not index:
            record.warnings.append(f"thư viện nhạc rỗng ({music_lib}) — draft thiếu nhạc")
            return
        usage = load_usage(music_lib)                # phạt mềm bài hay dùng (đa dạng giữa video)
        picks = select_music(chapters, index, usage=usage)
        if not picks:
            record.warnings.append("không chọn được nhạc hợp chương")
            return
        pick_by_ch = {p["chapter_id"]: p for p in picks}

    # "music" đã được tạo ở base setup; "music2" thêm khi cần (crossfade chương lẻ)
    norm_dir = project_dir / "media" / "norm"
    tracks_dir = Path(music_lib) / TRACKS_DIR
    total_end = project.segments[-1].timeline_end + project.segments[-1].breathing_after
    cache: dict[str, "object"] = {}
    selections: dict[str, str] = {}
    n = 0
    # Phủ LIỀN MẠCH: chương i kéo tới start chương i+1 (chương cuối tới hết video) — không
    # để hở ở khoảng hình thở giữa 2 chương. Chương sau bắt đầu sớm XFADE để crossfade.
    # NHIP-M3: chẻ chương mang Δ-có-nhạc-editor thành 2 nhịp nhạc (phương án B). Chương
    # không có Δ-nhạc -> đúng 1 span, tọa độ Y HỆT đường cũ. Track music/music2 luân
    # phiên theo CHỈ SỐ SPAN (không phải chỉ số chương) — span lẻ chèn giữa mà vẫn đếm
    # theo chương thì 2 đoạn liền nhau rơi cùng track -> crossfade đè -> SegmentOverlap.
    from autoedit.music.plan import bung_music_spans, music_spans
    ch_by_id = {c["chapter_id"]: c for c in chapters}
    spans = music_spans(project, chapters, bounds, total_end)
    # N2 (04/09): nhảy đoạn CHÍNH bài đang phát tại mốc bùng (lap_ke_hoach.
    # bung_beat_ids — mở/kết chương; hiệu lực thật chỉ ở chương KẾT, mở chương luôn
    # dính đầu span nên bị luật biên lọc) — fail-open, thiếu hồ sơ/index thì giữ
    # spans cũ, KHÔNG hỏng nhạc.
    try:
        from autoedit.nhip.hieu_luc import nap_hieu_luc as _nap_hl
        hs = _nap_hl(project)[0]   # 06/09: niche không đổi nhịp — 1 nguồn sự thật
        idx_by_file = {row["file"]: row for row in index}
        spans, bung_log = bung_music_spans(spans, project.beats, hs,
                                           getattr(project, "title", ""), idx_by_file)
        if bung_log:
            record.warnings.append("nhạc N2: " + " · ".join(bung_log))
    except Exception as exc:  # noqa: BLE001 — nhảy bùng không được giết stage nhạc
        record.warnings.append(f"nhạc N2: bỏ qua nâng bùng ({exc})")
    for i, sp in enumerate(spans):
        ch = ch_by_id[sp["chapter_id"]]
        if sp["is_insert"] and not sp.get("is_bung"):
            pick = {"file": sp["file"], "start_offset": sp["start_offset"]}
            src = Path(sp["file"])                    # bài editor: đường dẫn TUYỆT ĐỐI
        else:
            pick = pick_by_ch.get(ch["chapter_id"])
            if pick is None:
                continue
            src = tracks_dir / pick["file"]
            if sp.get("is_bung"):                     # bùng: GIỮ bài, đổi offset nhảy đoạn
                pick = {**pick, "start_offset": sp["start_offset"]}
        bnd = sp["seg_start"]
        # span đầu video vào từ 0; span sau vào sớm XFADE để crossfade (kể cả span Δ)
        seg_start = 0.0 if bnd <= 0 else max(0.0, bnd - xf)
        seg_end = sp["seg_end"]
        dur = seg_end - seg_start
        if dur <= 0.2:
            continue
        if not src.is_file():
            what = "nhạc editor" if sp["is_insert"] else "thiếu file"
            record.warnings.append(
                f"chương {ch['chapter_id']}: {what} {pick['file']} không thấy — bỏ")
            continue
        wav = cache.get(pick["file"])
        if wav is None:
            wav = src if src.suffix.lower() == ".wav" else \
                normalize_audio(src, norm_dir / f"music_{src.stem}.wav")
            cache[pick["file"]] = AudioMaterial(str(wav))
        track = "music" if i % 2 == 0 else "music2"
        if track == "music2" and "music2" not in script.tracks:
            from pycapcut import TrackType as _TT
            script.add_track(_TT.audio, "music2", relative_index=1)
        # M-VOL (M2): hook = chương ĐẦU timeline to hơn body theo niche — CHỈ khi
        # music-sync bật (có plan); không plan = 0.2 phẳng như cũ (đã qua tai V10)
        vol = ducking.hook_duck_for(project.niche) if (sync and i == 0) else MUSIC_VOLUME
        off = pick.get("start_offset", 0.0)
        if sync and not sp["is_insert"]:
            # bất biến P (M1): vị trí bài tại boundary = offset + min(XFADE, ts) —
            # giữ P với boundary/xfade mới để accent vẫn rơi đúng điểm đổi nhạc.
            # Span Δ KHÔNG áp P: bài editor bắt đầu từ đầu bài tại mép Δ, P của
            # music_plan là của bài CŨ — áp vào đây sẽ nhảy lung tung giữa bài lạ.
            pos_at_bound = off + min(MUSIC_XFADE, ch["timeline_start"])
            off = max(0.0, pos_at_bound - (bnd - seg_start))
        _lay_music(script, cache[pick["file"]], seg_start, dur, track, xf,
                   src_offset=off, volume=vol)
        # 1 chương giờ có thể 2 bài (M3) -> key theo span, không đè mất bài gốc
        key = f"{ch['chapter_id']}Δ" if sp["is_insert"] else str(ch["chapter_id"])
        selections[key] = pick["file"]
        if usage is not None and not sp["is_insert"]:
            usage[pick["file"]] = usage.get(pick["file"], 0) + 1   # ghi usage cho lần sau
        n += 1
    project.music_selections = selections
    if n and usage is not None:
        save_usage(music_lib, usage)
    if n:
        src = "theo music_plan (stage music)" if project.music_plan else "đổi bài theo mood"
        record.warnings.append(
            f"nhạc: {n} chương, {src} (crossfade {xf}s) — "
            + ", ".join(f"ch{k}:{Path(v).stem}" for k, v in selections.items())
        )


def _duck_music(script, project, record) -> None:
    """F8 ducking v1: voice -> nhạc nép (MUSIC_VOLUME), hình thở -> nhạc nở — keyframe
    volume chèn SAU khi nhạc đặt xong, không đụng logic chọn/đặt nhạc; fade/crossfade
    giữ nguyên (memory capcut-volume-keyframe). Clip nằm trọn trong voice: không cần
    keyframe (volume tĩnh của clip đã là mức nép)."""
    from autoedit.packager import ducking

    if not project.segments:
        return
    voice = ducking.merge_voice_intervals(project.segments)
    total_end = project.segments[-1].timeline_end + project.segments[-1].breathing_after
    env_body = ducking.build_envelope(voice, total_end, duck=MUSIC_VOLUME)
    # M-VOL (M2): music-sync bật -> envelope RIÊNG cho zone hook (nép cao hơn theo niche);
    # clip nhạc phân zone theo TRUNG ĐIỂM (hook seg phủ [0, đầu ch2]; body vào sớm XFADE)
    env_hook, hook_end, hook_duck = None, 0.0, MUSIC_VOLUME
    if project.music_plan:
        chs = _chapters_with_time(project)
        if chs:
            hook_end = chs[1]["timeline_start"] if len(chs) > 1 else total_end
            hook_duck = ducking.hook_duck_for(project.niche)
            env_hook = ducking.build_envelope(voice, total_end, duck=hook_duck)
    n = 0
    for name in ("music", "music2"):
        track = script.tracks.get(name)
        for seg in (track.segments if track else []):
            mid = (seg.target_timerange.start + seg.target_timerange.duration / 2) / SEC
            env, duck = (env_hook, hook_duck) if (env_hook is not None and mid < hook_end) \
                else (env_body, MUSIC_VOLUME)
            kfs = ducking.segment_keyframes(
                env, seg.target_timerange.start, seg.target_timerange.duration,
                duck=duck)
            # time_offset keyframe = thời gian trong BÀI NHẠC GỐC (source), KHÔNG phải
            # từ đầu clip — clip lấy nhạc giữa bài mà ghi offset từ 0 thì CapCut lờ
            # (bài học draft test v3 + đối chiếu REAL73, 2026-07-04)
            src0 = seg.source_timerange.start if seg.source_timerange else 0
            for off, vol in kfs:
                seg.add_keyframe(src0 + off, vol)
            n += 1 if kfs else 0
    if n:
        zone = f" | M-VOL hook nép {hook_duck} tới {hook_end:.0f}s" if env_hook is not None else ""
        record.warnings.append(
            f"ducking: nhạc nở {ducking.BREATH_VOL} ở khoảng thở, nép {MUSIC_VOLUME} khi "
            f"voice (ramp {ducking.RAMP}s) — keyframe trên {n} clip nhạc{zone}"
        )


def _epidemic_skip(project, niche_path: Path) -> "frozenset[str] | None":
    """Tên file SFX cần BỎ QUA khi `assemble --no-epidemic` (editor tắt mỗi lần dựng).

    Bật (mặc định) -> None, không đọc records, 0 chi phí. Tắt -> đọc ambient_library.yaml
    lấy file nguồn Epidemic. Kho VẪN GIỮ nguyên file — tắt chỉ là không chọn tới, bật lại
    có ngay (khác hẳn xóa/đổi folder)."""
    # 📌 Mặc định False (user chốt 2026-07-18 — đảo từ True): project.json CŨ dựng trước
    # ngày đó KHÔNG có field này, phải theo luật MỚI là tắt. Để True ở đây thì sửa
    # project.py vô ích — draft cũ dựng lại vẫn bật.
    if getattr(project, "use_epidemic_sfx", False):
        return None
    from autoedit.ambient.library import epidemic_files

    return epidemic_files(niche_path)


def _subject_llm(project, niche_path: Path):
    """(client NÃO, kind có file) cho TẦNG 3 — hoặc None khi tắt (mặc định).

    Bật bằng `assemble --sfx-llm`. Chỉ chấm beat bảng luật MÙ CHỮ (xem subject_llm.py).
    Fail-open: dựng client lỗi -> None -> chạy y như tắt, KHÔNG chặn assemble."""
    if not getattr(project, "sfx_llm", False):
        return None
    try:
        from autoedit.ambient.subject_llm import kinds_with_files
        from autoedit.director.cc_client import ClaudeCodeDirectorClient

        kinds = kinds_with_files(niche_path, _epidemic_skip(project, niche_path))
        if not kinds:
            return None
        return (ClaudeCodeDirectorClient(thinking=False), kinds)
    except Exception:
        return None


def _add_ambient(script, project, record, niche_path: Optional[Path] = None,
                 scene_lookup=None, subject_lookup=None) -> None:
    """C1 + S2 mức 1: mỗi ô thở ≥ AMB_MIN thêm 1 clip ambient — CHỦ THỂ trên hình thắng
    loại-cảnh (MO_TA_C1 §3 + MO_TA_SFX §2) — track `ambient` riêng, volume tĩnh + fade
    2 mép, cắt từ đầu file. Fail-open MỌI nấc: không niche / kho niche chưa có / db
    thiếu -> tầng tắt, draft y như trước C1. niche_path/*_lookup chỉ để test — mặc định
    suy từ machine.json + cache.db."""
    from pycapcut import AudioMaterial, AudioSegment, Timerange, TrackType

    from autoedit.ambient import schedule as amb
    from autoedit.ambient.library import load_subject_rules, niche_dir

    project.ambient_log = []
    if not project.segments or not project.niche:
        return
    npath = niche_path if niche_path is not None else niche_dir(project.niche)
    if not npath.is_dir():
        return  # kho ambient niche chưa gom -> tầng tắt (fail-open, MO_TA §3.3)

    slots = amb.breath_slots(project.segments)
    if not slots:
        return
    conn = None
    look, slook = scene_lookup, subject_lookup
    if look is None:
        try:  # mù db -> mù tag toàn bộ, mọi ô rơi về default — vẫn chạy
            from autoedit.library.db import connect
            conn = connect()
            look = amb.db_scene_lookup(conn)
            if slook is None:
                slook = amb.db_subject_lookup(conn)
        except Exception:
            look = lambda key: ""  # noqa: E731
    if slook is None:
        slook = lambda key: ("", "")  # noqa: E731 — test tiêm scene_lookup: không mở db thật
    rules = load_subject_rules(npath)  # bảng chủ thể per-niche (None -> built-in)
    try:
        for s in slots:
            s.scene_type = amb.resolve_scene(s, project, look)
            s.subject_kind = amb.resolve_slot_subject(s, project, slook, rules=rules)
            s.subject_end = amb.first_piece_end(s, project)
    finally:
        if conn is not None:
            conn.close()
    amb.choose_files(slots, npath, _epidemic_skip(project, npath))

    cache: dict[str, "object"] = {}
    placed = 0
    for s in slots:
        if s.file is None:
            continue
        m = cache.get(str(s.file))
        if m is None:
            m = cache[str(s.file)] = AudioMaterial(str(s.file))
        start_us = round(s.start * SEC)
        end_s = s.end
        # Tiếng CHỦ THỂ bám miếng nó match — dừng ở mốc kết miếng 1, không tràn sang
        # miếng sau (tai V5: b20 fire tràn qua footage tên lửa). Tiếng LOẠI CẢNH giữ
        # nguyên phủ trọn ô (các miếng thường cùng cảnh).
        is_subj = bool(s.used_kind and s.used_kind == s.subject_kind)
        if is_subj and s.subject_end and s.subject_end < end_s:
            end_s = s.subject_end
            s.note += f" · cắt theo miếng 1 ({end_s - s.start:.1f}s/{s.dur:.1f}s)"
        want_us = round(end_s * SEC) - start_us
        seg_us = min(want_us, m.duration - SAFETY_US)  # file ngắn hơn ô -> phủ được đến đâu hay đến đó
        if seg_us <= 0:
            s.file, s.note = None, f"bỏ: file ngắn bất thường ({s.note})"
            continue
        if seg_us < want_us:
            s.note += f" · file ngắn, phủ {seg_us / SEC:.1f}/{s.dur:.1f}s"
        if "ambient" not in script.tracks:
            script.add_track(TrackType.audio, "ambient", relative_index=3)
        fade_us = round(min(amb.AMB_FADE, seg_us / SEC / 2) * SEC)
        # Tiếng CHỦ THỂ thắng ô -> -5dB (user chốt 2026-07-18); loại CẢNH giữ 0dB (V4).
        vol = amb.SUBJECT_BREATH_VOL if is_subj else amb.AMBIENT_VOL
        seg = AudioSegment(m, Timerange(start_us, seg_us),
                           source_timerange=Timerange(0, seg_us), volume=vol)
        seg.add_fade(fade_us, fade_us)
        if _safe_add_segment(script, seg, "ambient"):
            placed += 1
        else:
            s.file, s.note = None, "bỏ: đè segment trước trên track ambient"
    project.ambient_log = [
        {"start": round(s.start, 3), "end": round(s.end, 3), "beat_id": s.beat_id,
         "scene_type": s.scene_type, "file": s.file.name if s.file else None,
         "note": s.note}
        for s in slots
    ]
    if placed:
        record.warnings.append(
            f"ambient C1: {placed}/{len(slots)} ô thở có tiếng môi trường "
            f"(vol cảnh {amb.AMBIENT_VOL} / chủ thể {amb.SUBJECT_BREATH_VOL} = -5dB, "
            f"fade {amb.AMB_FADE}s) — chi tiết trên report"
        )


def _add_drone(script, project, record, niche_path: Optional[Path] = None,
               scene_lookup=None) -> None:
    """S1: drone nền (lớp 2 của editor — PB10), track `drone` riêng. Niche có gate cảnh
    (deepsea: bed ục ục CHỈ trên cảnh underwater — sheet editor, user sửa nhận định
    2026-07-13) -> đặt theo run cảnh từ bed_intervals; niche khác loop SUỐT video.
    File ngắn hơn run -> loop nối đuôi (mép nối fade SEAM_FADE chống click); mỗi run
    fade vào 2s / ra 3s. Fail-open y C1: không niche / kho chưa có / kind drone rỗng
    -> tắt; gate mà MÙ DB cũng tắt (bed đè cảnh mặt biển tệ hơn không bed)."""
    from pycapcut import AudioMaterial, AudioSegment, Timerange, TrackType

    from autoedit.ambient import schedule as amb
    from autoedit.ambient.library import niche_dir

    project.drone_log = {}
    if not project.segments or not project.niche:
        return
    npath = niche_path if niche_path is not None else niche_dir(project.niche)
    if not npath.is_dir():
        return
    f = amb.choose_drone(npath, project.project_id, _epidemic_skip(project, npath))
    if f is None:
        return  # kho chưa có kind drone -> tầng tắt
    last = project.segments[-1]
    total_s = last.timeline_end + last.breathing_after
    scenes = amb.drone_scenes(project.niche)
    if scenes:
        look, conn = scene_lookup, None
        if look is None:
            try:
                from autoedit.library.db import connect
                conn = connect()
                look = amb.db_scene_lookup(conn)
            except Exception:
                look = None
        if look is None:
            record.warnings.append(
                f"drone nền S1: gate cảnh {'+'.join(scenes)} nhưng mù cache.db -> tầng tắt")
            return
        try:
            runs = amb.bed_intervals(project, look, scenes)
        finally:
            if conn is not None:
                conn.close()
        if not runs:
            record.warnings.append(
                f"drone nền S1: không beat nào chiếu cảnh {'+'.join(scenes)} -> không bed")
            return
    else:
        runs = [(0.0, total_s)]
    m = AudioMaterial(str(f))
    file_us = m.duration - SAFETY_US
    if file_us <= 0 or total_s <= 0:
        return
    if "drone" not in script.tracks:
        script.add_track(TrackType.audio, "drone", relative_index=4)
    vol = amb.drone_vol(project.niche)  # 🔸 per-niche (deepsea bed ục ục to hơn space)
    seam_us = round(amb.SEAM_FADE * SEC)
    loops = 0
    for run_s, run_e in runs:
        pos, end_us = round(run_s * SEC), round(run_e * SEC)
        while pos < end_us:
            dur = min(file_us, end_us - pos)
            fade_in = round(amb.DRONE_FADE_IN * SEC) if pos == round(run_s * SEC) else seam_us
            fade_out = round(amb.DRONE_FADE_OUT * SEC) if pos + dur >= end_us else seam_us
            seg = AudioSegment(m, Timerange(pos, dur), source_timerange=Timerange(0, dur),
                               volume=vol)
            seg.add_fade(min(fade_in, dur // 2), min(fade_out, dur // 2))
            if not _safe_add_segment(script, seg, "drone"):
                break
            pos += dur
            loops += 1
    covered = round(sum(e - s for s, e in runs), 1)
    project.drone_log = {"file": f.name, "volume": vol, "loops": loops,
                         "total_s": round(total_s, 1), "covered_s": covered,
                         "runs": len(runs), "gate": "+".join(scenes)}
    record.warnings.append(
        f"drone nền S1: {f.name} phủ {covered:.0f}/{total_s:.0f}s "
        f"({len(runs)} run cảnh, {loops} đoạn nối, vol {vol}"
        + (f", gate {'+'.join(scenes)})" if scenes else ")")
    )


def _add_subject_sfx(script, project, record, niche_path: Optional[Path] = None,
                     subject_lookup=None) -> None:
    """S2 mức 2: tiếng CHỦ THỂ khi footage đặc biệt lên hình, TRONG lúc voice nói
    (editor thật vẫn làm thế — user duyệt 2026-07-10, vol -8dB user chốt 2026-07-18). Đặt track `ambient`
    (vai môi trường; track sfx giữ vai UI/overlay). Trần chống loạn ở subject_beat_slots.
    Fail-open y C1."""
    from pycapcut import AudioMaterial, AudioSegment, Timerange, TrackType

    from autoedit.ambient import schedule as amb
    from autoedit.ambient.library import load_subject_rules, niche_dir

    project.subject_sfx_log = []
    if not project.beats or not project.niche:
        return
    npath = niche_path if niche_path is not None else niche_dir(project.niche)
    if not npath.is_dir():
        return
    conn = None
    look = subject_lookup
    if look is None:
        try:
            from autoedit.library.db import connect
            conn = connect()
            look = amb.db_subject_lookup(conn)
        except Exception:
            look = lambda key: ("", "", "")  # noqa: E731 — mù db -> không tiếng chủ thể
    try:
        slots = amb.subject_beat_slots(project, look, skip_beat=_beat_has_priority_visual,
                                       rules=load_subject_rules(npath),
                                       llm=_subject_llm(project, npath))
    finally:
        if conn is not None:
            conn.close()
    amb.choose_subject_files(slots, npath, _epidemic_skip(project, npath))

    cache: dict[str, "object"] = {}
    placed = 0
    for s in slots:
        if s.file is None:
            continue
        m = cache.get(str(s.file))
        if m is None:
            m = cache[str(s.file)] = AudioMaterial(str(s.file))
        start_us = round(s.start * SEC)
        want_us = round(s.end * SEC) - start_us
        # Hệ tọa độ kép lệch vài chục ms: ô thở C1 (mốc SEGMENT voice) có thể lấn ĐẦU
        # tiếng chủ thể (mốc WORD của beat — beat đứng ngay sau ô thở) -> xén đầu cho
        # né thay vì bỏ cả tiếng. Chỉ xén lấn nhỏ ≤1s; đè thật vẫn bỏ như cũ.
        track = script.tracks.get("ambient")
        if track is not None:
            for other in track.segments:
                o_end = other.target_timerange.start + other.target_timerange.duration
                lap = o_end - start_us
                if other.target_timerange.start <= start_us < o_end and lap <= SEC:
                    start_us, want_us = o_end, want_us - lap
                    s.start = start_us / SEC
                    s.note += " · xén đầu né ô thở"
                    break
        seg_us = min(want_us, m.duration - SAFETY_US)
        if seg_us <= 0:
            s.file, s.note = None, f"bỏ: file ngắn bất thường ({s.note})"
            continue
        if "ambient" not in script.tracks:
            script.add_track(TrackType.audio, "ambient", relative_index=3)
        fade_us = round(min(amb.AMB_FADE, seg_us / SEC / 2) * SEC)
        seg = AudioSegment(m, Timerange(start_us, seg_us),
                           source_timerange=Timerange(0, seg_us), volume=amb.SUBJECT_VOL)
        seg.add_fade(fade_us, fade_us)
        if _safe_add_segment(script, seg, "ambient"):
            placed += 1
        else:
            s.file, s.note = None, "bỏ: đè segment trên track ambient"
    project.subject_sfx_log = [
        {"start": round(s.start, 3), "end": round(s.end, 3), "beat_id": s.beat_id,
         "kind": s.kind, "source": s.source,
         "file": s.file.name if s.file else None, "note": s.note}
        for s in slots
    ]
    if placed:
        record.warnings.append(
            f"SFX chủ thể S2: {placed} tiếng trong voice (vol {amb.SUBJECT_VOL} = -8dB user chốt 2026-07-18)"
        )


def _add_hook_sfx(script, project, record, cuts, accents=None,
                  niche_path: Optional[Path] = None) -> None:
    """S3-HOOK: hit/whoosh/click tại CUT trong HOOK (MO_TA_VAN_HANH_HOOK_SFX §1 —
    23 draft editor deepsea: 4.8 tiếng/phút hook = 3× body, 48% bám cut ±0.25s).
    Chỉ niche có số đo (amb.HOOK_SFX_NICHES); đặt track `sfx` SAU overlay/chart-SFX
    (UI-SFX giữ chỗ — busy tính cả chúng lẫn S2/C1 trong hook). Fail-open y C1/S1/S2."""
    from pycapcut import AudioMaterial, AudioSegment, Timerange

    from autoedit.ambient import schedule as amb
    from autoedit.ambient.library import HOOK_SFX_KINDS, list_variants, niche_dir

    project.hook_sfx_log = []
    if project.niche not in amb.hook_sfx_niches() or not cuts:
        return
    npath = niche_path if niche_path is not None else niche_dir(project.niche)
    if not npath.is_dir():
        return
    skip = _epidemic_skip(project, npath)
    variants = {k: list_variants(k, npath, skip) for k in HOOK_SFX_KINDS}
    if not any(variants.values()):
        return  # kho niche chưa có tiếng hook -> tầng tắt
    # V2 Đợt 1b (user duyệt hướng 03/09): VÙNG NHẤN từ nhịp — chương H trọn
    # (trước đây flow từng-chương không có "mốc chương 2" nên tầng này TẮT hẳn)
    # + cửa sổ beat BÙNG ở chương thân/kết. Nhịp lỗi -> rơi về mốc chương cũ.
    vung: list[tuple[float, float]] = []
    try:
        from autoedit.nhip.ep import vung_nhan as _vung_nhan
        from autoedit.nhip.hieu_luc import nap_hieu_luc as _nap_hl

        vung = _vung_nhan(project.beats, _nap_hl(project)[0],   # 06/09: bỏ nap(niche)
                          title=getattr(project, "title", ""))
    except Exception as exc:  # noqa: BLE001
        record.warnings.append(f"S3 nhấn: nhịp lỗi ({exc}) — dùng mốc chương cũ")
    if not vung:
        chs = _chapters_with_time(project)
        if len(chs) < 2:
            record.warnings.append("HOOK SFX S3: không có vùng nhấn/mốc chương — tầng tắt")
            return
        vung = [(0.0, chs[1]["timeline_start"])]
    busy = [e["start"] for e in project.subject_sfx_log if e.get("file")]
    busy += [e["start"] for e in project.ambient_log if e.get("file")]
    sfx_track = script.tracks.get("sfx")
    if sfx_track is not None:
        busy += [s.target_timerange.start / SEC for s in sfx_track.segments]
    slots = amb.nhan_sfx_slots(cuts, vung, busy=busy, accents=accents or ())
    slots = [s for s in slots if variants.get(s.kind)]  # kind thiếu file -> bỏ loại đó
    if not slots:
        record.warnings.append(
            f"HOOK SFX S3: 0 slot trong hook ≤{hook_end:.0f}s (mật độ đủ/kho thiếu kind)")
        return
    _ensure_sfx_track(script)
    seed = zlib.crc32(project.project_id.encode("utf-8"))
    idx = dict.fromkeys(variants, 0)  # xoay vòng biến thể, seed theo project (dựng lại y cũ)
    cache: dict[str, object] = {}
    placed = 0
    for s in slots:
        vs = variants[s.kind]
        f = vs[(seed + idx[s.kind]) % len(vs)]
        idx[s.kind] += 1
        m = cache.get(str(f))
        if m is None:
            m = cache[str(f)] = AudioMaterial(str(f))
        seg_us = min(m.duration - SAFETY_US, round(amb.HOOK_SFX_MAX_S * SEC))
        if seg_us <= 0:
            s.note += " · bỏ: file ngắn bất thường"
            continue
        seg = AudioSegment(m, Timerange(round(s.t * SEC), seg_us),
                           source_timerange=Timerange(0, seg_us),
                           volume=amb.HOOK_SFX_VOL)
        if seg_us < m.duration - SAFETY_US:
            seg.add_fade(0, round(0.3 * SEC))  # cắt đuôi -> fade-out; KHÔNG fade-in (giữ attack)
        if _safe_add_segment(script, seg, "sfx"):
            s.file = f
            placed += 1
        else:
            s.note += " · bỏ: đè segment track sfx"
    project.hook_sfx_log = [
        {"t": s.t, "kind": s.kind, "file": s.file.name if s.file else None, "note": s.note}
        for s in slots
    ]
    if placed:
        kinds = {k: sum(1 for s in slots if s.kind == k and s.file) for k in HOOK_SFX_KINDS}
        mo_ta_vung = " + ".join(f"{t0:.0f}-{t1:.0f}s" for t0, t1 in vung[:4])
        record.warnings.append(
            f"SFX NHẤN S3: {placed} tiếng tại cut trong {len(vung)} vùng ({mo_ta_vung}) "
            f"(impact {kinds['impact']} · whoosh {kinds['whoosh']} · click {kinds['click']}, "
            f"vol {amb.HOOK_SFX_VOL} 🔸 · mật độ còn 30% số editor — cổng tai V4)"
        )


def _ensure_sfx_track(script) -> None:
    """Tạo track audio 'sfx' nếu CHƯA có (idempotent — overlay-SFX & chart-SFX dùng chung)."""
    from pycapcut import TrackType
    if "sfx" not in script.tracks:
        script.add_track(TrackType.audio, "sfx", relative_index=2)


def _ensure_layer2(script) -> None:
    """Tạo track video 'layer2' (trên video_l1) nếu chưa có — chart PiP & info-card dùng chung."""
    from pycapcut import TrackType
    if "layer2" not in script.tracks:
        script.add_track(TrackType.video, "layer2", relative_index=1)


def _beat_has_priority_visual(beat) -> bool:
    """Beat đã có thẻ card / biểu đồ = lớp hình ưu tiên -> BỎ overlay text + kinetic
    cho khỏi rối (user 14/06: ưu tiên card/chart hơn text)."""
    if beat.graphic_spec is not None or beat.graphic_asset:
        return True
    return beat.info_card is not None and beat.info_card.approved


def _add_info_cards(script, project, record, project_dir: Path) -> None:
    """Req 6: thẻ chữ nửa PHẢI (footage chạy nửa trái dưới). Card portrait 960x1080 +
    scale 0.5 -> hiển thị 960x1080 (full cao), transform_x đẩy phải. CHỈ đặt khi đã DUYỆT
    (info_card.approved) — chống số/nội dung sai lọt khi chưa người kiểm."""
    from pycapcut import ClipSettings, Timerange, VideoMaterial, VideoSegment

    beats_card = [
        b for b in project.beats
        if b.info_card_asset and b.timeline_start is not None
        and b.info_card is not None and b.info_card.approved
    ]
    if not beats_card:
        return
    _ensure_layer2(script)
    norm_dir = project_dir / "media" / "norm"
    n = 0
    for beat in beats_card:
        asset = project_dir / beat.info_card_asset
        if not asset.exists():
            record.warnings.append(f"beat {beat.beat_id}: info-card {beat.info_card_asset} mất file — bỏ")
            continue
        # crop_16x9=False: card DỌC 960x1080 chủ đích — crop 16:9 sẽ vỡ layout (V1)
        asset = normalize_video(asset, norm_dir / asset.name, crop_16x9=False)
        material = VideoMaterial(str(asset))
        want_us = int((beat.end - beat.start) * SEC)
        src_us = min(want_us, material.duration - SAFETY_US)
        if src_us <= 0:
            continue
        script.add_segment(
            VideoSegment(
                material,
                Timerange(int(beat.timeline_start * SEC), src_us),
                source_timerange=Timerange(0, src_us),
                # card portrait 960x1080: CapCut fit theo chiều cao -> scale 1.0 = 960x1080
                # (full nửa phải); transform_x 0.5 đẩy tâm sang phải (x=1440)
                clip_settings=ClipSettings(
                    scale_x=1.0, scale_y=1.0, transform_x=0.5, transform_y=0.0
                ),
            ),
            "layer2",
        )
        n += 1
    if n:
        record.warnings.append(f"info-card: {n} thẻ chữ nửa màn đặt lên layer2")


def _safe_add_segment(script, segment, track) -> bool:
    """Đặt segment, BỎ QUA nếu đè segment khác trên cùng track (CapCut cấm overlap).

    Lớp TRANG TRÍ (overlay text / SFX / kinetic) ở video DÀI có thể đè nhau khi 2 mốc
    gần nhau — 1 cái đè KHÔNG được giết cả assemble (như nguyên tắc 'asset hỏng không
    giết batch'). Trả True nếu đặt được, False nếu bỏ qua do overlap.
    """
    from pycapcut.exceptions import SegmentOverlap
    try:
        script.add_segment(segment, track)
        return True
    except SegmentOverlap:
        return False


def _add_sfx_clip(script, kind, start_us, max_dur_us, sfx_dir, sfx_fallback,
                  norm_dir: Path, sfx_cache: dict, sfx_rotation: dict, volume=0.7) -> bool:
    """Đặt 1 SFX (xoay vòng biến thể theo kind) lên track 'sfx'. True nếu đặt được.
    Track 'sfx' phải đã tồn tại (gọi _ensure_sfx_track trước)."""
    from pycapcut import AudioMaterial, AudioSegment, Timerange

    from autoedit.overlay.sfx import resolve_sfx_variants

    variants = resolve_sfx_variants(kind, sfx_dir, sfx_fallback)
    if not variants:
        return False
    idx = sfx_rotation.get(kind, 0)
    sfx_rotation[kind] = idx + 1
    sfx_src = variants[idx % len(variants)]
    key = str(sfx_src)
    if key not in sfx_cache:
        wav = sfx_src if sfx_src.suffix.lower() == ".wav" else \
            normalize_audio(sfx_src, norm_dir / f"sfx_{sfx_src.stem}.wav")
        sfx_cache[key] = AudioMaterial(str(wav))
    m = sfx_cache[key]
    dur = min(m.duration - SAFETY_US, max_dur_us)  # SFX ngắn -> dùng trọn (không loop)
    if dur <= 0:
        return False
    return _safe_add_segment(script, AudioSegment(m, Timerange(start_us, dur), volume=volume), "sfx")


def _chart_of_beat(beat):
    """(chart_type, start_giây) nếu beat CÓ chart hiển thị, không thì None. Mỗi beat 1 lần:
    half (graphic_asset PiP) ưu tiên, rồi full (graphic_spec + route=graphic)."""
    if beat.timeline_start is None:
        return None
    if beat.graphic_asset and beat.graphic_spec is not None:        # half PiP
        return beat.graphic_spec.chart_type, beat.timeline_start
    if beat.graphic_spec is not None and beat.sourcing_route == "graphic":  # full L1
        return beat.graphic_spec.chart_type, beat.timeline_start
    return None


def _add_chart_sfx(script, project, record, project_dir: Path, sfx_dir, sfx_fallback) -> None:
    """Req 2: SFX khi biểu đồ mọc. Tiếng grow (theo loại chart) đặt tại start, dài ~GROW_SEC;
    tiếng 'ding' chốt khi mọc xong. Chỉ thêm track khi thật sự có chart."""
    from autoedit.packager.charts import CHART_SETTLE_SFX, GROW_SEC, _CHART_SFX

    charts = [(b, _chart_of_beat(b)) for b in project.beats]
    charts = [(b, c) for b, c in charts if c is not None]
    if not charts:
        return
    _ensure_sfx_track(script)
    norm_dir = project_dir / "media" / "norm"
    sfx_cache: dict[str, "object"] = {}
    sfx_rotation: dict[str, int] = {}
    grow_us = int(GROW_SEC * SEC)
    n = 0
    for beat, (chart_type, start) in charts:
        start_us = int(start * SEC)
        kind = _CHART_SFX.get(chart_type, "chart_bar")
        if _add_sfx_clip(script, kind, start_us, grow_us, sfx_dir, sfx_fallback,
                         norm_dir, sfx_cache, sfx_rotation, volume=0.6):
            n += 1
        # tiếng chốt nhẹ khi mọc xong (cuối grow)
        _add_sfx_clip(script, CHART_SETTLE_SFX, start_us + grow_us, int(0.5 * SEC),
                      sfx_dir, sfx_fallback, norm_dir, sfx_cache, sfx_rotation, volume=0.5)
    if n:
        record.warnings.append(f"chart SFX: {n} biểu đồ có tiếng động khi mọc")


def _add_text_sequences(script, project, record, project_dir: Path) -> None:
    """Req 3: chữ chạy theo voice từng cụm — mỗi cụm 1 TextSegment slide-in, XẾP CHỒNG
    theo y, giữ tới hết beat, nền plate mờ cho nổi chữ. Chỉ thêm track text khi cần."""
    from pycapcut import TrackType

    from autoedit.overlay.text import build_text_overlay

    beats_ts = [
        b for b in project.beats
        if b.text_sequence and b.text_sequence.phrases and b.timeline_start is not None
        and not _beat_has_priority_visual(b)  # card/chart ưu tiên hơn kinetic text
    ]
    if not beats_ts:
        return
    words = project.transcript
    step = -0.30                                      # khoảng cách dòng (đủ rộng kẻo đè)
    n = 0
    for beat in beats_ts:
        seq = beat.text_sequence
        offset = beat.timeline_start - beat.start
        beat_end_tl = (
            beat.timeline_end if beat.timeline_end is not None
            else beat.timeline_start + (beat.end - beat.start)
        )
        phrases = seq.phrases[:4]
        base_y = -(len(phrases) - 1) / 2 * step       # CĂN GIỮA khối chữ quanh tâm màn
        for k, ph in enumerate(phrases):
            if not (0 <= ph.anchor_word < len(words)):
                continue
            ts = words[ph.anchor_word].start + offset
            start_us = int(max(0.0, ts) * SEC)
            end_us = int(beat_end_tl * SEC)          # giữ tới hết beat (xếp chồng)
            dur_us = end_us - start_us
            if dur_us <= 0:
                continue
            # các cụm CHỒNG THỜI GIAN (cùng hiện) -> mỗi index 1 track text riêng
            # (1 track CapCut cấm 2 segment đè nhau). Beat khác nhau cách thời gian nên
            # tái dùng được track kinetic{k}.
            track = f"kinetic{k}"
            if track not in script.tracks:
                script.add_track(TrackType.text, track)
            if _safe_add_segment(
                script,
                build_text_overlay(
                    ph.text, start_us, dur_us, position=seq.position, anim="slide_up",
                    size=seq.size, y_override=base_y + k * step,
                    bg_plate=(seq.background == "plate"),
                ),
                track,
            ):
                n += 1
    if n:
        record.warnings.append(f"text sequence: {n} cụm chữ chạy theo voice (Req 3)")


def _add_overlays(script, project, record, project_dir: Path, sfx_dir, sfx_fallback) -> None:
    """Đặt text overlay + SFX theo anchor_word. Timeline = source_từ + offset của beat
    (hệ tọa độ kép M4: trong 1 beat offset cố định = timeline_start - start)."""
    from pycapcut import TrackType

    from autoedit.overlay.text import build_text_overlay

    # CHỈ tạo track khi có overlay trên beat KHÔNG bị card/chart chiếm (tránh track rỗng)
    if not any(b.overlays and not _beat_has_priority_visual(b) for b in project.beats):
        return
    _ensure_sfx_track(script)            # dùng chung với chart-SFX
    script.add_track(TrackType.text, "text")

    words = project.transcript
    norm_dir = project_dir / "media" / "norm"
    total_end = (
        project.segments[-1].timeline_end + project.segments[-1].breathing_after
        if project.segments else 0
    )
    sfx_cache: dict[str, "object"] = {}
    sfx_rotation: dict[str, int] = {}  # xoay vòng biến thể theo kind (đỡ nghe lặp)
    n_text = n_sfx = n_skip = 0

    for beat in project.beats:
        if not beat.overlays or beat.timeline_start is None:
            continue
        if _beat_has_priority_visual(beat) or beat.text_sequence:
            continue  # đã có card/chart HOẶC kinetic text -> bỏ overlay (khỏi 2 lớp chữ)
        offset = beat.timeline_start - beat.start  # giây (offset run chứa beat)
        for ov in beat.overlays:
            if not (0 <= ov.anchor_word < len(words)):
                continue
            ts = words[ov.anchor_word].start + offset
            start_us = int(max(0.0, ts) * SEC)
            dur_us = int(min(ov.duration_sec, max(0.5, total_end - ts)) * SEC)
            if dur_us <= 0:
                continue
            if ov.anim == "typing":
                # GÕ MÁY (Req 1): hiệu ứng native CapCut + 1 SFX bàn phím trim đúng span gõ
                from autoedit.overlay.text import build_typing_overlay
                seg, type_total_us = build_typing_overlay(
                    ov.text, start_us, dur_us, position=ov.position, size=ov.size
                )
                if not _safe_add_segment(script, seg, "text"):
                    n_skip += 1     # đè overlay trước trên track text -> bỏ (không giết assemble)
                    continue
                n_text += 1
                if type_total_us > 0 and _add_sfx_clip(
                    script, ov.sfx_kind, start_us, type_total_us,
                    sfx_dir, sfx_fallback, norm_dir, sfx_cache, sfx_rotation, volume=0.5
                ):
                    n_sfx += 1
                continue
            if not _safe_add_segment(
                script,
                build_text_overlay(ov.text, start_us, dur_us, position=ov.position,
                                   anim=ov.anim, size=ov.size),
                "text",
            ):
                n_skip += 1
                continue
            n_text += 1
            if _add_sfx_clip(script, ov.sfx_kind, start_us, int(1.0 * SEC),
                             sfx_dir, sfx_fallback, norm_dir, sfx_cache, sfx_rotation,
                             volume=0.7):
                n_sfx += 1

    if n_text or n_skip:
        msg = f"overlay: {n_text} text + {n_sfx} SFX đã đặt lên draft"
        if n_skip:
            msg += f" ({n_skip} overlay bỏ do trùng thời gian trên track text — video dài)"
        record.warnings.append(msg)


# ---------------- VD4: ghi công kênh nguồn (MO_TA_VAN_HANH_GHI_CONG_KENH.md) ----------
# 4 góc = 4 cặp HƯỚNG (ngang, dọc); vị trí ngang tính ĐỘNG theo độ dài chữ — cổng mắt
# v1 2026-07-17 lộ bug: neo TÂM chữ tại x cố định ±0.72 làm tên dài tràn nửa chữ ra
# ngoài màn ("elaxation Channel"). v2: mép NGOÀI chữ luôn cách mép màn ~CREDIT_MARGIN,
# tên dài tự kéo vào trong. User chốt cùng cổng: size 4 (nhỏ 50%) + không viền/hiệu ứng.
_CREDIT_CORNERS = ((-1, 1), (1, 1), (-1, -1), (1, -1))
CREDIT_SIZE = 4.0
CREDIT_PREFIX = "Credit: "  # user chốt 2026-07-17 (thay vì in trơ tên kênh / "CRE:")
CREDIT_ALPHA = 0.5          # chữ mờ 50% (user chốt cùng ngày)
CREDIT_Y = 0.80        # độ cao góc (giữ v1 — user không chê dọc)
CREDIT_MARGIN = 0.03   # mép ngoài chữ cách mép màn (đơn vị nửa-khung chuẩn hóa)
# Bề rộng chữ ước lượng: px trên khung 1920 cho 1 (size × ký tự) — đo từ screenshot
# CapCut cổng mắt v1 (~5.4) + đệm an toàn; ước LỐ chỉ làm chữ lùi vào trong (an toàn),
# ước HỤT mới gây cắt chữ.
_CREDIT_PX_PER_SIZE_CHAR = 6.0


def _credit_channel_map(project) -> dict[str, str]:
    """asset_path (tương đối project) -> kênh nguồn, gom từ MỌI loại pick mang footage
    (shot chính + extra multi-shot + shot thở). Rỗng = không kênh -> không credit."""
    m: dict[str, str] = {}
    for s in project.shots:
        if s.asset_path and s.source_channel:
            m[s.asset_path] = s.source_channel
        for e in s.extra_shots:
            if e.asset_path and e.source_channel:
                m[e.asset_path] = e.source_channel
    for b in project.breath_shots:
        if b.asset_path and b.source_channel:
            m[b.asset_path] = b.source_channel
    return m


def _credit_pos(asset_rel: str, start: float, text: str,
                size: float = CREDIT_SIZE) -> tuple[float, float]:
    """Vị trí (x, y) cho credit 1 miếng: GÓC random giữa các miếng nhưng DETERMINISTIC
    (crc32 — cùng khuôn seed Ken Burns/shot thở: dựng lại ra đúng góc cũ); x tính từ
    độ dài chữ sao cho mép NGOÀI chữ ~CREDIT_MARGIN cách mép màn (transform_x neo TÂM
    hộp chữ — neo cứng là tên dài tràn màn, bug cổng mắt v1)."""
    sx, sy = _CREDIT_CORNERS[zlib.crc32(f"{asset_rel}:{round(start * 1000)}".encode("utf-8")) % 4]
    half = size * max(1, len(text)) * _CREDIT_PX_PER_SIZE_CHAR / 2 / 960  # nửa bề rộng, đơn vị nửa-khung
    return sx * max(0.0, 1.0 - CREDIT_MARGIN - half), sy * CREDIT_Y


def _add_credit_overlays(script, project, record, credit_log) -> None:
    """--credit (VD4): mỗi miếng footage L1 lấy từ asset CÓ kênh nguồn -> 1 text nhỏ
    tên kênh ở 1 trong 4 góc, span đúng bằng miếng. Track text riêng 'credit'
    (CapCut cấm 2 segment đè nhau 1 track); slug/chart/card không vào credit_log."""
    from pycapcut import TrackType

    from autoedit.overlay.text import build_text_overlay

    chan_of = _credit_channel_map(project)
    todo = [(start, end, rel, chan_of[rel])
            for start, end, rel in credit_log if chan_of.get(rel)]
    if not todo:
        record.warnings.append(
            "--credit bật nhưng 0 segment có kênh nguồn — kho chưa điền kênh "
            "(channel-set / library-ingest --channel) hoặc project source trước khi điền")
        return
    script.add_track(TrackType.text, "credit")
    n = 0
    for start, end, rel, chan in todo:
        start_us = round(start * SEC)
        dur_us = round(end * SEC) - start_us  # round 2 mép như L1 — kề nhau khít, không đè
        if dur_us <= 0:
            continue
        text = CREDIT_PREFIX + chan
        tx, ty = _credit_pos(rel, start, text)  # neo động tính trên CẢ tiền tố
        if _safe_add_segment(
            script,
            build_text_overlay(text, start_us, dur_us, anim="none", bordered=False,
                               alpha=CREDIT_ALPHA,
                               size=CREDIT_SIZE, y_override=ty, x_override=tx),
            "credit",
        ):
            n += 1
    record.warnings.append(
        f"ghi công (--credit): {n}/{len(credit_log)} miếng footage gắn tên kênh nguồn ở góc")
