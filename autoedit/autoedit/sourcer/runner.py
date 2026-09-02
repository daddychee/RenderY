"""Stage 4 — Source: route từng beat -> ứng viên -> chọn -> tải.

Thang fallback P8 (route stock): local niche -> Pexels 3 tier -> needs_human.
Route entity: Google CSE (thiếu key -> needs_human + hướng dẫn).
Route graphic: placeholder + tải nền theo tier thematic nếu có.
Chọn: có `brain` -> KHUNG PHỄU c5 (F5, MO_TA_VAN_HANH_PHEU_C5.md — NÃO chấm + điểm máy
+ sàn 3 + kill-log; PA-1 2026-07-07: chấm BATCH ~10 beat cùng chương/1 call, fallback
1 call/beat khi batch hỏng — MO_TA_VAN_HANH_PHEU_BATCH.md). Không brain -> heuristic
Phase 0 cũ (local thắng, relevance + phạt mềm P7 + ưu tiên clip dài >= 1.2x beat — 4.4).
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from autoedit.library.profile import DEFAULT_LIBRARY_ROOT
from autoedit.packager.coverage import MIN_SHOT_DUR
from autoedit.project import (
    Beat,
    CostEntry,
    ExtraShot,
    Project,
    SearchQueries,
    ShotPick,
    Stage,
    StageRecord,
    StageStatus,
    ffprobe_duration,
    slugify,
)
from autoedit.ranker.funnel import (
    MOOD_W,
    NGHIA_W,
    RankBrain,
    rank_batch,
    rank_beat,
    rank_beat_prescored,
)
from autoedit.ranker.visiongate import GATE_BUDGET, GATE_SOURCES
from autoedit.sourcer import usage
from autoedit.sourcer.breath import pick_breath_shots
from autoedit.sourcer.colorcheck import check_project_colors
from autoedit.sourcer.entity import (
    MIN_IMAGE_WIDTH,
    EntityClient,
    entity_cache_dir,
    image_width,
    looks_like_image,
)
from autoedit.sourcer.local import (
    BOOST_INJECT_CAP,
    REF_INJECT_CAP,
    _strip_motion_terms,
    find_boost_candidates,
    find_local_candidates,
    find_ref_candidates,
    find_signature_candidates,
    ref_chapter_scan,
)
from autoedit.sourcer.viral import ViralLedger
from autoedit.sourcer.pexels import StockClient

PREFER_DURATION_RATIO = 1.2  # 4.4: ưu tiên clip dài hơn beat
RANK_BATCH_SIZE = 10  # PA-1 (2026-07-07): gom tối đa N beat stock/local cùng chương / 1 call NÃO
# TOC-2 (2026-07-15): số call NÃO batch bay SONG SONG (lookahead). Đo 3 bài: 43-57 call
# nối đuôi = 50-80% thời gian source. Gather vẫn main thread (sqlite/used_in_video);
# luật cứng P7 + gate C8 vốn re-check TẠI PICK nên lookahead không thủng luật; giá phải
# trả duy nhất = prev_pick_note ranh chunk cũ đi 1-2 chunk (mạch c3 trong chunk giữ nguyên).
# env AUTOEDIT_RANK_PARALLEL đè (=1 -> tuần tự như cũ, tắt nhanh khi subscription nghẽn).
RANK_PARALLEL = 3
# TOC-3 (2026-07-15): normalize footage NỀN ngay trong source (CPU rảnh lúc chờ NÃO/tải)
# -> assemble mtime-skip ăn sẵn (transcode.py idempotent), assemble 20' rơi còn vài phút.
# env AUTOEDIT_PRENORM=0 tắt (test suite tắt qua conftest — fake video không phải media).
PRENORM_WORKERS = 2
# TOC-3b (2026-07-15, user chốt "làm luôn" — .env có 10 key Pexels): tải Pexels SONG SONG
# kiểu WARM-UP — chunk vừa có verdict NÃO thì tải trước ứng viên top-điểm của từng beat
# vào ĐÚNG file đích; vòng pick giữ nguyên thứ tự/luật cũ, gặp file nằm sẵn (ffprobe
# hợp lệ) thì khỏi tải. PICK KHÔNG ĐỔI — trượt dự đoán chỉ phí 1 file mồ côi trong
# assets/. env AUTOEDIT_DL_PARALLEL đè (0 = tắt warm-up; test suite tắt qua conftest).
DL_PARALLEL = 4
PREFETCH_PER_BEAT = 1  # top điểm NÃO thuần/beat (thiếu điểm máy ±2.5 — xấp xỉ đủ tốt)


class _Prenorm:
    """Hàng đợi normalize nền — ghi CHÍNH XÁC path assemble sẽ tìm (media/norm/<tên>).

    An toàn crash: ffmpeg ghi ra file part_* rồi os.replace sang tên thật — không bao
    giờ để file norm CỤT mang mtime hợp lệ (assemble mtime-skip sẽ nuốt file cụt nếu
    ghi thẳng). Lỗi bất kỳ -> đếm + bỏ qua, assemble tự normalize lại như cũ (fail-open).
    """

    def __init__(self, project_dir: Path, perf: _Perf):
        self.project_dir = project_dir
        self.norm_dir = project_dir / "media" / "norm"
        self.perf = perf
        self.seen: set[str] = set()
        self.pool = ThreadPoolExecutor(max_workers=PRENORM_WORKERS,
                                       thread_name_prefix="prenorm")

    def submit(self, asset_rel: "str | None") -> None:
        if not asset_rel or asset_rel in self.seen:
            return
        self.seen.add(asset_rel)
        self.pool.submit(self._one, asset_rel)

    def _one(self, asset_rel: str) -> None:
        from autoedit.packager.transcode import is_video, normalize_image, normalize_video

        src = self.project_dir / asset_rel
        t0 = time.perf_counter()
        tmp = None
        try:
            # nhánh video/ảnh + tên đích Y HỆT assembler (video: <tên>; ảnh: <stem>.jpg)
            if is_video(src):
                dst, fn = self.norm_dir / src.name, normalize_video
            else:
                dst, fn = self.norm_dir / f"{src.stem}.jpg", normalize_image
            if dst.is_file() and dst.stat().st_mtime >= src.stat().st_mtime:
                return  # đã có bản norm mới hơn (resume)
            tmp = dst.with_name("part_" + dst.name)  # giữ ĐUÔI thật — ffmpeg đoán muxer theo đuôi
            tmp.unlink(missing_ok=True)              # rác run trước: xóa kẻo replace bản cụt
            fn(src, tmp)
            os.replace(tmp, dst)
            self.perf.add("prenorm_s", time.perf_counter() - t0, "prenorm_n")
        except Exception:
            self.perf.add("prenorm_err_s", time.perf_counter() - t0, "prenorm_err")
            if tmp is not None:
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass

    def drain(self, record) -> None:
        """Chờ hàng đợi cạn cuối stage (đa số đã xong trong lúc source chạy) + tổng kết."""
        self.pool.shutdown(wait=True)
        n = self.perf.perf.get("prenorm_n", 0)
        err = self.perf.perf.get("prenorm_err", 0)
        if n or err:
            record.warnings.append(
                f"TOC-3 normalize nền: {n} asset xong ngay trong source"
                + (f", {err} lỗi (assemble tự normalize lại — không mất gì)" if err else ""))


# ---- TOC-4 (2026-07-15): đo tốc độ tự động — record.perf thay bấm giờ tay ------------
class _Perf:
    """Cộng dồn số đo vào record.perf — thread-safe (TOC-2 gọi NÃO từ worker thread)."""

    def __init__(self, perf: dict):
        self.perf = perf
        self.lock = threading.Lock()

    def add(self, key: str, dt: float, n_key: str | None = None) -> None:
        with self.lock:
            self.perf[key] = round(self.perf.get(key, 0.0) + dt, 3)
            if n_key:
                self.perf[n_key] = self.perf.get(n_key, 0) + 1


class _TimedStock:
    """Proxy StockClient đo search/download — interface + thuộc tính đi qua nguyên.

    TOC-3b: download có KHÓA THEO ĐÍCH (warm-up nền + vòng pick có thể cùng muốn 1 file)
    + tái dùng file đích đã nằm sẵn và ffprobe đọc được (warm-up đã tải / resume run cũ).
    File cụt/hỏng -> ffprobe None -> tải lại như cũ, không bao giờ nhận file rác."""

    def __init__(self, inner, perf: _Perf):
        self._inner, self._perf = inner, perf
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _dest_lock(self, dest) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(str(dest), threading.Lock())

    def search_tiered(self, queries):
        t0 = time.perf_counter()
        try:
            return self._inner.search_tiered(queries)
        finally:
            self._perf.add("pexels_search_s", time.perf_counter() - t0)

    def download(self, candidate, dest):
        with self._dest_lock(dest):
            if dest.is_file() and ffprobe_duration(dest) is not None:
                self._perf.add("dl_reuse_s", 0.0, "dl_reuse")  # warm-up/resume đã tải
                return dest
            t0 = time.perf_counter()
            try:
                return self._inner.download(candidate, dest)
            finally:
                self._perf.add("download_s", time.perf_counter() - t0, "downloads")

    def __getattr__(self, name):  # rate_limited / keys / conn... đi thẳng inner
        return getattr(self._inner, name)


class _DlPool:
    """TOC-3b: hàng đợi tải warm-up — lỗi nuốt êm (warm-up là TỐI ƯU, vòng pick inline
    tự tải lại + tự fallback ứng viên kế như cũ)."""

    def __init__(self, workers: int):
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="dl")

    def submit(self, fn, *args) -> None:
        self.pool.submit(self._safe, fn, *args)

    @staticmethod
    def _safe(fn, *args) -> None:
        try:
            fn(*args)
        except Exception:  # noqa: BLE001 — đường inline gánh, không được giết worker
            pass


class _TimedBrain:
    """Proxy RankBrain đo từng call NÃO (compute — wall song song đo riêng rank_wait_s)."""

    def __init__(self, inner, perf: _Perf):
        self._inner, self._perf = inner, perf

    def complete(self, system, user, output_model, context=None):
        t0 = time.perf_counter()
        try:
            return self._inner.complete(system, user, output_model, context=context)
        finally:
            self._perf.add("rank_call_s", time.perf_counter() - t0, "rank_calls")

    def __getattr__(self, name):  # .model cho cost_log
        return getattr(self._inner, name)


def run_source(
    project: Project,
    conn: sqlite3.Connection,
    stock: StockClient,
    entity: Optional[EntityClient],
    niche: str = "",
    library_root: Path = DEFAULT_LIBRARY_ROOT,
    on_progress=None,
    brain: Optional[RankBrain] = None,   # F5: có brain -> phễu c5; None -> heuristic cũ
    gate=None,   # C5 đợt 5: VisionGate soi lead-pick (CLI tiêm; None/không brain = tắt)
    ref_sources: tuple[str, ...] | list[str] = (),  # REF: prefix nguồn mẫu của bài (khai --ref)
    boosts: tuple[str, ...] | list[str] = (),  # BOOST: "X@scope" per-video (khai --boost)
) -> Project:
    """on_progress(done, total, beat): gọi TRƯỚC khi xử lý mỗi beat cho CLI in tiến độ."""
    cut = project.stages.get(Stage.CUT)
    if cut is None or cut.status != StageStatus.DONE or not project.beats:
        raise RuntimeError("Stage cut chưa xong — chạy `autoedit cut` trước.")

    project_dir = Path(project.project_dir)
    assets_dir = project_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    channel = project.inputs.channel or ""
    script_text = project.inputs.script_text or ""   # PA2 geo-gate: lọc local sai quốc gia

    record = StageRecord.running()
    project.stages[Stage.SOURCE] = record
    # TOC-4: đo tự động — bọc stock + brain, số đo dồn vào record.perf (NHAT_KY_TOC_DO)
    _t0_stage = time.perf_counter()
    _perf = _Perf(record.perf)
    stock = _TimedStock(stock, _perf)
    if brain is not None:
        brain = _TimedBrain(brain, _perf)
    # C4 vá bug niche rơi (anh em bug B2 quên-consumer): lệnh `source` đứng riêng không
    # --niche -> local/signature/shot thở TẮT IM LẶNG (skill /dung-video Pha 2 gọi đúng
    # kiểu này). Fallback channel Ở ĐÂY = chokepoint duy nhất cho mọi đường gọi.
    if not niche and channel:
        niche = channel
        record.warnings.append(f"niche kho local = '{niche}' (fallback từ channel — C4)")
    project.rank_log = []   # chạy lại source -> xóa log phễu cũ (tránh lệch với shots mới)
    project.niche = niche or None   # truy vết kho local (DNA d1: assemble đọc dna.json theo đây)
    project.save()

    shots: list[ShotPick] = []
    used_in_video: set[str] = set()  # luật cứng duy nhất P7
    local_stats: dict[int, bool] = {}  # C4 đo local-first: beat_id -> pool có ứng viên KHO?
    # C8 gói CHỌN: gate pháp lý viral (liền kề + trần 8%; nguồn khai --ref trần 15%)
    ledger = ViralLedger(ref_sources=ref_sources)

    # NGUỒN REF VIDEO (02/09): video có sẵn + .srt user đặt THẲNG trong thư mục chương.
    # Đọc từ thư mục kịch bản GỐC trên NAS (project chỉ giữ bản sao script/voice).
    refs, matcher = [], None
    try:
        from autoedit.sourcer import refvideo as _rv

        goc = Path(project.inputs.original_script_path or "").parent
        refs, rv_canh_bao = _rv.doc_ref(goc)
        for w in rv_canh_bao:
            record.warnings.append(f"ref video — {w}")
        if refs:
            from autoedit.sourcer.refembed import Matcher

            matcher = Matcher()
            if not matcher.san_sang:
                record.warnings.append(
                    "ref video: thiếu sentence-transformers -> TẮT nguồn này "
                    "(pip install sentence-transformers)")
                refs = []
            else:
                n_seg = sum(len(r.segments) for r in refs)
                record.warnings.append(
                    f"ref video: {len(refs)} video ({n_seg} đoạn transcript) — "
                    f"khớp ngữ nghĩa, trần tỉ trọng như mọi nguồn mượn")
    except Exception as exc:      # fail-open: hỏng nguồn ref KHÔNG giết cả stage
        record.warnings.append(f"ref video: bỏ qua ({exc})")
        refs, matcher = [], None

    if ledger.ref_prefixes:
        record.warnings.append(
            f"REF ưu tiên nguồn mẫu của bài: {len(ledger.ref_prefixes)} prefix — "
            f"chèn ≤{REF_INJECT_CAP} cảnh/beat (match nới) + bonus phễu + trần 15%")
        # REF THEO CHƯƠNG (VD2, user chốt 2026-07-18 MỀM): folder con "Chapter N" trong
        # folder --ref = mẫu riêng chương N — scope CHÈN + bonus theo beat.chapter tại
        # _gather_candidates; trần 15% vẫn cả mẻ. Map rỗng = ref phẳng y cũ.
        # M4d HINH THO (user chốt 2026-07-21): folder `HINH THO` dưới --ref = footage
        # dành riêng Δ/mini-hook — tước CHÈN+bonus mọi beat (ref_excludes); Δ tiêu thụ
        # ở pick_insert_footage (tự scan lại — đường phẫu thuật không qua runner).
        from autoedit.sourcer.local import ref_hinhtho_scan
        ht = ref_hinhtho_scan(conn, niche, ledger.ref_prefixes)
        if ht["all"]:
            ledger.ref_hinhtho_prefixes = ht["all"]
            c = ht["counts"]
            record.warnings.append(
                "HINH THO (M4d): "
                + ", ".join(f"ch{n}={c.get(n, 0)}" for n in sorted(ht["by_chapter"]))
                + (f", mini-hook={c.get('minihook', 0)}" if ht["minihook"] else "")
                + f", chung={c.get('chung', 0)} cảnh — dành riêng Δ/mini-hook, "
                  "beat thường mất chèn+bonus (search thường vẫn chấm)")
        ch_map, ch_counts = ref_chapter_scan(conn, niche, ledger.ref_prefixes)
        if ch_map:
            ledger.ref_chapter_prefixes = ch_map
            record.warnings.append(
                "REF theo chương (mềm): "
                + ", ".join(f"ch{n}={ch_counts.get(n, 0)}" for n in sorted(ch_map))
                + f", chung={ch_counts.get('chung', 0)} cảnh — cảnh sai chương mất "
                  "CHÈN+bonus (search thường vẫn chấm), trần 15% giữ cả mẻ")
            outline_ids = {c.get("chapter_id")
                           for c in (project.outline or {}).get("chapters", [])}
            bad = sorted(set(ch_map) - outline_ids)
            if bad:
                record.warnings.append(
                    f"REF theo chương: folder chương {bad} không khớp chapter_id nào của "
                    "outline — cảnh trong đó không được chèn/bonus ở beat nào (editor "
                    "đánh số lệch?)")
    # BOOST (user 2026-07-17): sở thích khán giả — per-video (--boost) + niche
    # (audience_bias niche_profile.yaml). Merge Ở ĐÂY = chokepoint duy nhất mọi đường
    # gọi (bug B2 quên-consumer: `run` gọi thẳng run_source, merge ở CLI là đường run mù)
    boost_specs = _parse_boosts(list(boosts) + _audience_bias(niche, library_root), record)
    if boost_specs:
        record.warnings.append(
            "BOOST khán giả: " + ", ".join(f"'{t}'@{sc}" for t, sc in boost_specs)
            + f" — chèn ≤{BOOST_INJECT_CAP} cảnh KHO/beat + bonus phễu (nghĩa vẫn trên hết)")

    # F5: ngữ cảnh phễu — central_subject theo chương + mạch c3 (footage beat N−1)
    chapters = (project.outline or {}).get("chapters", [])
    central_by_ch = {c.get("chapter_id"): c.get("central_subject") or "" for c in chapters}
    hook_ch = chapters[0].get("chapter_id") if chapters else None
    # V3: phạm vi chủ thể VIDEO — vòng ngoài veto thực thể (project cũ thiếu key -> "")
    video_subject = (project.outline or {}).get("video_subject", "") or ""
    ctx = ({"results": [], "prev_pick_note": "", "prev_shot_size": "", "batch_cache": {},
            "video_subject": video_subject, "gate": gate, "gate_errors": 0,
            "gate_streak": 0}
           if brain else None)
    prev_chapter = None

    # TOC-2: chia sẵn chunk batch (tĩnh) + executor lookahead. n_par=1 = tuần tự như cũ.
    rank_exec = None
    rank_pending: dict[int, dict] = {}   # chunk_idx -> {"future","gathered","first"}
    rank_next = 0                        # chunk kế tiếp CHƯA submit
    chunk_idx_of: dict[int, int] = {}
    rank_chunks: list[list[Beat]] = []
    if ctx is not None:
        n_par = max(1, int(os.environ.get("AUTOEDIT_RANK_PARALLEL", RANK_PARALLEL)))
        rank_chunks = _plan_chunks(project.beats)
        chunk_idx_of = {b.beat_id: ci for ci, ch in enumerate(rank_chunks) for b in ch}
        idx_of = {b.beat_id: j for j, b in enumerate(project.beats)}
        # chapter_open của beat đầu chunk — tĩnh theo thứ tự beats (khớp prev_chapter cũ)
        chunk_prev_ch = [
            project.beats[idx_of[ch[0].beat_id] - 1].chapter
            if idx_of[ch[0].beat_id] > 0 else None
            for ch in rank_chunks
        ]
        if rank_chunks:
            rank_exec = ThreadPoolExecutor(max_workers=n_par, thread_name_prefix="rank")

    # TOC-3: normalize nền (mọi đường — có brain hay heuristic đều lợi)
    prenorm = (_Prenorm(project_dir, _perf)
               if os.environ.get("AUTOEDIT_PRENORM", "1") != "0" else None)
    # TOC-3b: tải warm-up song song (chỉ đường phễu — cần verdict để biết tải gì trước)
    dl_pool = None
    if ctx is not None:
        n_dl = max(0, int(os.environ.get("AUTOEDIT_DL_PARALLEL", DL_PARALLEL)))
        if n_dl > 0:
            dl_pool = _DlPool(n_dl)

    try:
        total = len(project.beats)
        for i, beat in enumerate(project.beats, start=1):
            if on_progress:
                on_progress(i, total, beat)
            # BOOST scope tính PER-BEAT tại call site (không qua ctx — né staleness
            # lookahead TOC-2, P5 đã rà); đường heuristic không ctx vẫn ăn chèn
            bterms = _boost_terms_for(boost_specs, beat.chapter, hook_ch)
            if ctx is not None:
                ctx["central_subject"] = central_by_ch.get(beat.chapter, "")
                ctx["chapter_open"] = prev_chapter is not None and beat.chapter != prev_chapter
                # luật c6: HOOK hoặc SLOT CHÊM -> gom signature/ trước
                ctx["signature_first"] = (beat.chapter == hook_ch) or not beat.visual_anchor
                # PA-1 + TOC-2: giữ n_par call NÃO bay trước; đến lượt chunk nào thì
                # chờ kết quả chunk đó (thường đã xong từ lâu) rồi đổ vào batch_cache
                if rank_exec is not None:
                    rank_next = _pump_rank(
                        rank_exec, rank_chunks, chunk_prev_ch, rank_pending, rank_next,
                        n_par, ctx, conn, stock, niche, used_in_video, script_text,
                        hook_ch, central_by_ch, brain, local_stats, ledger, boost_specs,
                        refs=refs, matcher=matcher)
                    ci = chunk_idx_of.get(beat.beat_id)
                    if ci is not None and beat.beat_id not in ctx["batch_cache"]:
                        entry = rank_pending.pop(ci, None)
                        _resolve_rank(entry, ctx, record, _perf)
                        # TOC-3b: verdict vừa về -> tải TRƯỚC top-pick các beat của chunk
                        # (song song, nuốt lỗi) trong lúc vòng pick tiêu thụ tuần tự
                        if dl_pool is not None and entry is not None:
                            maps_by_bid = {
                                bid: ctx["batch_cache"][bid][1]
                                for bid in entry["gathered"] if bid in ctx["batch_cache"]
                            }
                            for c, dest in _prefetch_plan(
                                    entry["beats"], entry["gathered"], maps_by_bid,
                                    used_in_video, ledger, assets_dir):
                                dl_pool.submit(stock.download, c, dest)
            if beat.sourcing_route == "entity":
                pick = _source_entity(beat, entity, conn, niche, library_root,
                                      assets_dir, project_dir, record)
            elif beat.sourcing_route == "graphic":
                pick = _source_graphic(beat, conn, stock, niche, used_in_video,
                                       channel, assets_dir, project_dir, script_text)
            else:  # stock | local_library
                pick = _source_stock(beat, conn, stock, niche, used_in_video,
                                     channel, assets_dir, project_dir, record, script_text,
                                     brain=brain, ctx=ctx, local_stats=local_stats,
                                     ledger=ledger, boost_terms=bterms,
                                     refs=refs, matcher=matcher)
            if pick.status == "needs_human":  # SÀN NICHE: mọi route đầu hàng -> tự đắp
                floor = _floor_pick(beat, conn, niche, used_in_video, channel, stock,
                                    assets_dir, project_dir, record,
                                    script_text=script_text, why=pick.note,
                                    boost_terms=bterms)
                if floor is not None:
                    pick = floor
            prev_chapter = beat.chapter
            # mạch c3 cho route ngoài phễu (route stock tự cập nhật trong _source_stock)
            if ctx is not None and beat.sourcing_route in ("entity", "graphic") and pick.asset_key:
                ctx["prev_pick_note"] = pick.note or beat.visual_concept
                ctx["prev_shot_size"] = ""
            if pick.asset_key:
                used_in_video.add(pick.asset_key)
                if channel and pick.status in ("ok", "graphic"):
                    usage.log_usage(conn, channel, pick.asset_key, project.project_id)
            # P1.5b: chart nửa màn -> render thêm chart làm PiP (footage là pick ở trên).
            # P2B: chart BỔ SUNG (supplementary) chỉ render khi đã DUYỆT (approved).
            gs = beat.graphic_spec
            # half = footage nửa trái + chart PiP nửa phải -> route PHẢI có footage (không graphic,
            # vì route=graphic là chart đầy màn rồi -> 2 chart đè nhau). Bug 15/06.
            if (gs is not None and gs.layout == "half" and getattr(gs, "approved", True)
                    and beat.sourcing_route != "graphic"):
                beat.graphic_asset = _render_half_chart(beat, assets_dir, project_dir, record)
            # P2B Req6: thẻ chữ bổ sung -> render khi đã duyệt
            if beat.info_card is not None and beat.info_card.approved:
                beat.info_card_asset = _render_info_card(beat, assets_dir, project_dir, record)
            shots.append(pick)
            # TOC-3: footage vừa nằm xuống assets/ -> normalize nền luôn. KHÔNG đụng
            # chart PiP/info-card (assemble normalize crop_16x9=False riêng — crop
            # nhầm card dọc là VỠ layout); chart đầy màn cũng bỏ (assemble tự lo).
            if (prenorm is not None and pick.asset_path
                    and pick.source not in ("chart", "none")):
                prenorm.submit(pick.asset_path)
                for ex in pick.extra_shots:
                    prenorm.submit(ex.asset_path)
        project.shots = shots
        # Shot thở (MO_TA_VAN_HANH_SHOT_THO §2d): chọn SAU khi mọi beat có clip —
        # chủ thể clip liền trước đã biết, used_in_video đầy đủ (không cắt sang clip hàng xóm)
        project.breath_shots = pick_breath_shots(project, conn, used_in_video,
                                                 assets_dir, record)
        if prenorm is not None:  # TOC-3: shot thở cũng vào norm nền
            for b in project.breath_shots:
                prenorm.submit(b.asset_path)
        # M4c: footage THẬT cho Δ — chọn SAU mọi pick beat/thở (used_in_video đầy đủ,
        # kho không giành clip của beat). Fail-open cả tầng: lỗi -> Δ giữ slug như M4b.
        if any(i.footage_clips or i.footage_queries for i in project.inserts):
            try:
                from autoedit.sourcer.insert_fill import pick_insert_footage
                pick_insert_footage(project, conn, used_in_video, record, channel)
                if prenorm is not None:  # pick Δ (kho lẫn editor) vào norm nền
                    for ins in project.inserts:
                        for p in ins.footage_picks:
                            if p.path:
                                prenorm.submit(p.path)
            except Exception as exc:
                record.warnings.append(f"M4c footage Δ lỗi ({exc}) — Δ giữ slug")
        # C3: so màu nội bộ chương — CHỈ cảnh báo, fail-open (không giết stage)
        try:
            check_project_colors(project, record)
        except Exception as exc:
            record.warnings.append(f"so màu C3 lỗi ({exc}) — bỏ qua")
        # M3b: vision-tag pick stock/entity (SAU khi picks chốt — không lật phễu/ranker);
        # tag lưu vĩnh viễn stock_tags, video sau cache hit. Fail-open cả tầng.
        try:
            from autoedit.library.stock_tags import tag_project_stock
            st = tag_project_stock(project, Path(project.project_dir), conn)
            if st["tagged"] or st["failed"]:
                record.warnings.append(
                    f"vision tag stock M3b: {st['tagged']} mới + {st['cached']} cache"
                    + (f", {len(st['failed'])} lỗi (mù tag như cũ)" if st["failed"] else "")
                )
        except Exception as exc:
            record.warnings.append(f"vision tag stock M3b lỗi ({exc}) — pick stock mù tag như cũ")
        if prenorm is not None:  # TOC-3: chờ cạn CUỐI CÙNG — tối đa thời gian chồng lấn
            prenorm.drain(record)
    except Exception as exc:
        record.status = StageStatus.FAILED
        record.error = str(exc)
        project.save()
        raise
    finally:
        if rank_exec is not None:  # TOC-2: không rò thread khi stage chết giữa chừng
            rank_exec.shutdown(wait=False, cancel_futures=True)
        if prenorm is not None:    # TOC-3: nt — ffmpeg đang chạy tự xong, .part vô hại
            prenorm.pool.shutdown(wait=False, cancel_futures=True)
        if dl_pool is not None:    # TOC-3b: warm-up dở dang = file mồ côi, không ai đọc
            dl_pool.pool.shutdown(wait=False, cancel_futures=True)

    n_human = sum(1 for s in shots if s.status == "needs_human")
    if n_human:
        record.warnings.append(f"{n_human} beat cần người chọn footage (xem shots)")
    n_floor = sum(1 for s in shots if s.source == "floor")
    if n_floor:
        record.warnings.append(
            f"SÀN NICHE tự đắp {n_floor} beat (phễu/route trắng tay) — nguồn 'floor' "
            "trên report, editor soát/swap các beat này trước")
    if boost_specs:  # BOOST tầng ĐO: editor kiểm X có vào bài thật không (số 🔸 chỉnh theo đây)
        n_lead = sum(1 for s in shots if s.boost_hit)
        n_extra = sum(1 for s in shots for ex in s.extra_shots if ex.boost_hit)
        record.warnings.append(
            f"BOOST tầng ĐO: {n_lead}/{len(shots)} beat lead match sở thích khán giả"
            + (f" + {n_extra} extra-shot" if n_extra else "")
            + " — 0/thấp bất thường: term chưa theo từ vựng tag kho hoặc kho thiếu cảnh X")
    if local_stats:  # C4: mỗi run tự trả lời "đã local-first thật chưa" (tín hiệu DNA c4 §5)
        wins = sum(1 for s in shots if s.source == "local" and s.status == "ok")
        record.warnings.append(
            f"local-first (C4): {sum(local_stats.values())}/{len(local_stats)} beat stock/local"
            f" có ứng viên KHO trong pool · kho thắng {wins} pick"
        )
    if ledger.picked or ledger.blocked:  # C8: minh bạch viral cho editor/user kiểm luật
        record.warnings.append(
            f"viral c8: {sum(len(v) for v in ledger.picked.values())} cảnh từ "
            f"{len(ledger.picked)} nguồn ({ledger.summary() or '—'}) · gate chặn "
            f"{ledger.blocked} lượt ứng viên (liền kề/trần 8%) · pick điểm nhô: "
            f"{ledger.peak_picks} (ytref §3h)"
        )
    if getattr(stock, "rate_limited", False):
        n_keys = len(getattr(stock, "keys", [""]))
        record.warnings.append(
            f"⚠ TẤT CẢ {n_keys} key Pexels đều hết hạn mức (rate limit) giữa chừng — các beat "
            "stock sau đó không tải được, để needs_human. Footage thư viện local F: vẫn dùng "
            "bình thường. Cách lấp: thêm key Pexels vào .env, hoặc chạy lại `source` sau ~1 giờ "
            "(hạn mức reset), hoặc editor tự thay."
        )
    record.perf["stage_s"] = round(time.perf_counter() - _t0_stage, 1)  # TOC-4
    record.status = StageStatus.DONE
    record.completed_at = datetime.now(timezone.utc).isoformat()
    if ctx is not None:  # F5: phễu c5 — ghi rank_log + kill-log tổng + token NÃO
        results = ctx["results"]
        project.rank_log = [r.model_dump(mode="json") for r in results]
        tot = {k: sum(r.kill_log.get(k, 0) for r in results)
               for k in ("thu", "hong_ky_thuat", "veto_nghia", "tra_lai_san")}
        thu = tot["thu"] or 1  # tránh chia 0 khi mọi beat đều entity/graphic
        rank_warns = [
            f"phễu c5 ({len(results)} beat): thu {tot['thu']} ứng viên · chết kỹ thuật "
            f"{tot['hong_ky_thuat']} ({100 * tot['hong_ky_thuat'] // thu}%) · veto nghĩa "
            f"{tot['veto_nghia']} ({100 * tot['veto_nghia'] // thu}%) · trả lại sàn "
            f"{tot['tra_lai_san']} — cửa nào giết nhiều bất thường thì nới ĐỊNH NGHĨA cửa đó"
        ]
        # C5 vision gate (đợt 5): tổng kết cho user phán trúng/oan (chi tiết ở report)
        gate_entries = [g for r in results for g in r.vision_gate]
        if gate_entries or ctx.get("gate_errors"):
            n_act = {a: sum(1 for g in gate_entries if g["action"] == a)
                     for a in ("pass", "demote", "giu_du_nghi_sai", "mood_warning")}
            rank_warns.append(
                f"C5 vision gate: soi {len(gate_entries)} lượt · pass {n_act['pass']} · "
                f"demote {n_act['demote']} · giữ-dù-nghi {n_act['giu_du_nghi_sai']} · "
                f"mood-warning {n_act['mood_warning']} · lỗi fail-open {ctx.get('gate_errors', 0)}"
            )
        project.stages[Stage.RANK] = StageRecord(
            status=StageStatus.DONE, completed_at=record.completed_at,
            warnings=rank_warns,
        )
        in_tok = sum(r.input_tokens for r in results)
        out_tok = sum(r.output_tokens for r in results)
        if in_tok or out_tok:
            project.cost_log.append(CostEntry(
                stage="rank", model=getattr(brain, "model", "claude-code"),
                input_tokens=in_tok, output_tokens=out_tok, usd=0.0,  # subscription
                at=record.completed_at,
            ))
    else:
        # Phase 0: rank = heuristic ngay trong source
        project.stages[Stage.RANK] = StageRecord(
            status=StageStatus.DONE,
            completed_at=record.completed_at,
            warnings=["Phase 0: chọn heuristic (local thắng, relevance, phạt mềm P7) — phễu c5 cần brain"],
        )
    project.save()
    return project


# ----------------------------------------------------------------------------
def _plan_chunks(beats) -> list[list]:
    """TOC-2: chia sẵn TOÀN BỘ chunk batch — tĩnh, chỉ phụ thuộc route/chương (biết
    trước khi chạy). CÙNG LUẬT với _prefetch_batch cũ (PA-1): beat stock/local LIỀN
    NHAU cùng chương, tối đa RANK_BATCH_SIZE; chunk <2 beat bỏ (1 call/beat cũ xử)."""
    chunks: list[list] = []
    cur: list = []
    for b in beats:
        stockish = b.sourcing_route in ("stock", "local_library")
        if stockish and (not cur or (b.chapter == cur[-1].chapter
                                     and len(cur) < RANK_BATCH_SIZE)):
            cur.append(b)
            continue
        if len(cur) >= 2:
            chunks.append(cur)
        cur = [b] if stockish else []
    if len(cur) >= 2:
        chunks.append(cur)
    return chunks


# ---- BOOST (user chốt 2026-07-17): sở thích khán giả niche ---------------------
# MO_TA_VAN_HANH_BOOST.md. 2 nguồn khai (NGƯỜI khai, máy không suy): --boost per-video
# + audience_bias niche_profile.yaml. Chèn + bonus = ĐIỂM RANK, không cửa loại
# (filter-overload-guard); nghĩa/veto/world-lock vẫn trên hết.
def _parse_boosts(specs, record=None) -> list[tuple[str, str]]:
    """'X@scope' -> (term thường-hóa + bỏ từ chuyển động C6, scope). scope: all (mặc
    định) | hook | ch<N>; scope lạ = all + warning (không im lặng bỏ — thà nới)."""
    out: list[tuple[str, str]] = []
    for s in specs:
        raw = str(s).strip()
        if not raw:
            continue
        term, _, scope = raw.partition("@")
        term = _strip_motion_terms(term.strip().lower()).strip()
        scope = scope.strip().lower() or "all"
        if scope not in ("all", "hook") and not re.fullmatch(r"ch\d+", scope):
            if record is not None:
                record.warnings.append(f"BOOST '{raw}': scope '{scope}' lạ — coi như 'all'")
            scope = "all"
        if term and (term, scope) not in out:
            out.append((term, scope))
    return out


def _audience_bias(niche: str, library_root) -> list[str]:
    """audience_bias từ niche_profile.yaml (field Stage-4, nay mới nối dây) — fail-open:
    thiếu niche/profile/lỗi đọc = [] (boost là tối ưu, không giết stage). Lọc dòng
    TODO của scaffold init_niche."""
    if not niche:
        return []
    try:
        from autoedit.library.profile import NicheProfile, niche_dir
        prof = NicheProfile.load(niche_dir(niche, root=library_root))
        return [t for t in prof.audience_bias
                if str(t).strip() and not str(t).strip().lower().startswith("todo")]
    except Exception:
        return []


def _boost_terms_for(specs, chapter, hook_ch) -> tuple[str, ...]:
    """Term hiệu lực tại beat theo scope — tính PER-BEAT tại call site (không qua ctx,
    né staleness lookahead TOC-2)."""
    return tuple(
        t for t, sc in specs
        if sc == "all" or (sc == "hook" and chapter == hook_ch) or sc == f"ch{chapter}"
    )


def _matches_boost(c: dict, boost_terms) -> bool:
    """Ứng viên match term X? AND từng từ của term trên subject+tags (cùng luật
    AND-match của search_assets — term viết theo từ vựng tag kho)."""
    blob = f"{c.get('description', '')} {c.get('tags', '')}".lower()
    return any(all(w in blob for w in t.split()) for t in boost_terms if t.strip())


def _pump_rank(exec_, chunks, chunk_prev_ch, pending, next_idx, n_par, ctx, conn, stock,
               niche, used_in_video, script_text, hook_ch, central_by_ch, brain,
               local_stats, ledger, boost_specs=(), refs=(), matcher=None) -> int:
    """TOC-2: giữ tối đa n_par call NÃO batch bay trước (lookahead). Gather ứng viên ở
    MAIN thread (sqlite conn + used_in_video không thread-safe); worker CHỈ chạy
    rank_batch (thuần + subprocess claude). Trả next_idx mới.

    Staleness chấp nhận (P5 đã rà): used_in_video/ledger lúc gather cũ đi ≤ n_par chunk
    — ứng viên vừa bị beat trước lấy sẽ bị SKIP tại pick (P7 + ledger.blocks re-check,
    cơ chế CÓ SẴN từ PA-1); prev_pick_note ranh chunk cũ đi 1-2 chunk (mạch c3 TRONG
    chunk không đổi — NÃO tự chain như cũ)."""
    while next_idx < len(chunks) and len(pending) < n_par:
        chunk = chunks[next_idx]
        first = chunk[0]
        items: list[tuple] = []
        gathered: dict[int, tuple] = {}
        for b in chunk:
            sig_first = (b.chapter == hook_ch) or not b.visual_anchor
            cands, queries = _gather_candidates(b, conn, stock, niche, used_in_video,
                                                sig_first, script_text,
                                                local_stats=local_stats, ledger=ledger,
                                                boost_terms=_boost_terms_for(
                                                    boost_specs, b.chapter, hook_ch),
                                                refs=refs, matcher=matcher)
            items.append((b, cands))
            gathered[b.beat_id] = (cands, queries)
        prev_ch = chunk_prev_ch[next_idx]
        fut = exec_.submit(
            rank_batch, items, brain,
            central_subject=central_by_ch.get(first.chapter, ""),
            prev_pick_note=ctx.get("prev_pick_note", ""),
            chapter_open_first=(prev_ch is not None and first.chapter != prev_ch),
            video_subject=ctx.get("video_subject", ""),
        )
        pending[next_idx] = {"future": fut, "gathered": gathered, "first": first.beat_id,
                             "beats": chunk}  # TOC-3b: warm-up cần beat để tính tên đích
        next_idx += 1
    return next_idx


def _resolve_rank(entry, ctx, record, perf) -> None:
    """TOC-2: chờ + tiêu thụ 1 future chunk — đổ verdict vào batch_cache (giữ nguyên
    khuôn PA-1). Call lỗi → warning + KHÔNG cache (đường 1 call/beat cũ tự chạy)."""
    if entry is None:
        return
    t0 = time.perf_counter()
    try:
        maps, tok, warns = entry["future"].result()
    except Exception as exc:  # batch là TỐI ƯU — hỏng thì về đường cũ, không giết stage
        record.warnings.append(
            f"batch NÃO lỗi ở chunk từ beat {entry['first']} ({exc}) — rơi về 1 call/beat")
        return
    finally:
        perf.add("rank_wait_s", time.perf_counter() - t0)  # wall thật NGỒI CHỜ NÃO
    record.warnings.extend(warns)
    for bid, (cands, queries) in entry["gathered"].items():
        ctx["batch_cache"][bid] = (cands, maps.get(bid), queries)
    if tok != (0, 0):
        ctx["batch_usage"] = tok  # ghi vào BeatRankResult đầu tiên tiêu thụ (tổng đúng)


def _gather_candidates(beat, conn, stock, niche, used_in_video, signature_first,
                       script_text="", local_stats=None,
                       ledger=None, boost_terms=(),
                       refs=(), matcher=None) -> tuple[list[dict], SearchQueries]:
    """B1 THU cho 1 beat (dùng chung đường per-beat lẫn batch PA-1).

    `refs`/`matcher`: video có sẵn của user + transcript (nguồn refvideo, 02/09).
    Rỗng = không có ref -> chương chạy y như trước.
    """
    queries = SearchQueries.model_validate(
        beat.search_queries if isinstance(beat.search_queries, dict)
        else beat.search_queries.model_dump()
    )
    # luật c6: beat HOOK/CHÊM gom signature/ trước, xếp LÊN ĐẦU (chỉ đường phễu)
    candidates: list[dict] = []
    if signature_first:
        candidates += find_signature_candidates(conn, niche, used_keys=used_in_video)
    # P6: local trước (geo-gate PA2: lọc clip sai quốc gia so với script)
    # used_keys = P7-trước-limit (bug DS3-084): lọc đã-dùng TRƯỚC nhát cắt top-5/query
    local_cands = find_local_candidates(conn, niche, queries, script_text=script_text,
                                        used_keys=used_in_video)
    if ledger is not None:  # C8: gate pháp lý viral (liền kề + trần 8%/15% ref) + sort rải mềm
        local_cands = ledger.gate(local_cands)
    if local_stats is not None:  # C4: keyed theo beat_id — re-gather (batch lỗi) không đếm đôi
        local_stats[beat.beat_id] = bool(local_cands)
    candidates += local_cands
    # REF (user 2026-07-11): CHÈN cảnh nguồn mẫu của bài (match nới, sau local chặt,
    # trước Pexels) — ledger vẫn gác pháp lý, phễu vẫn chấm nghĩa như mọi ứng viên
    if ledger is not None and ledger.ref_prefixes:
        candidates += ledger.gate(find_ref_candidates(
            conn, niche, ledger.ref_prefixes, queries, script_text=script_text,
            used_keys=used_in_video,
            exclude_prefixes=ledger.ref_excludes(beat.chapter)))
    # BOOST: chèn cảnh KHO match sở thích khán giả (sau ref, trước Pexels) — ledger
    # vẫn gác pháp lý (chèn ≠ miễn); phễu vẫn chấm nghĩa như mọi ứng viên
    if boost_terms:
        extra = find_boost_candidates(conn, niche, boost_terms,
                                      script_text=script_text, used_keys=used_in_video)
        candidates += ledger.gate(extra) if ledger is not None else extra
    # REF VIDEO của user: đặt TRƯỚC stock để khi điểm ngang nhau thì thắng —
    # user đưa video vào là muốn dùng nó. Ledger vẫn gác trần tỉ trọng như ytref.
    if refs:
        from autoedit.sourcer import refvideo as _rv

        rc = _rv.tim_ung_vien(beat, refs, matcher, used_keys=used_in_video)
        candidates += ledger.gate(rc) if ledger is not None else rc
    candidates += stock.search_tiered(queries)
    seen: set[str] = set(used_in_video)  # luật cứng P7 + khử trùng signature/local
    uniq: list[dict] = []
    for c in candidates:
        if c["asset_key"] not in seen:
            seen.add(c["asset_key"])
            uniq.append(c)
    if ledger is not None and ledger.ref_prefixes:
        # đánh dấu 1 CHỖ DUY NHẤT cho REF_BONUS phễu — phủ cả ứng viên vào bằng đường
        # local AND-match lẫn đường chèn (không phụ thuộc đường vào pool). REF theo
        # chương (VD2 mềm): cảnh chương KHÁC beat này không nhận nhãn -> không bonus.
        excl = ledger.ref_excludes(beat.chapter)
        for c in uniq:
            src = str(c.get("source_video", "")).lower()
            if src.startswith(ledger.ref_prefixes) and not (excl and src.startswith(excl)):
                c["is_ref"] = True
    if boost_terms:
        # BOOST nhãn cùng khuôn 1-chỗ-duy-nhất (gắn trên bản chèn sẽ RƠI theo dedup —
        # vết PB7); CHỈ nguồn kho local: cảnh X kho phải ĐÈ cảnh X Pexels (user chốt
        # 2026-07-17 — editor thật né Pexels)
        for c in uniq:
            if c.get("source") == "local" and _matches_boost(c, boost_terms):
                c["is_boost"] = True
    return uniq, queries


# ---- SÀN NICHE (bug DS3-084, 2026-07-14) -------------------------------------
# 40 beat needs_human/1 bài trong khi kho own 8.981 asset — user chốt: tool PHẢI tự
# điền hết. Lưới vớt heuristic KHÔNG-NÃO chạy khi mọi route đã đầu hàng, đúng mẫu
# user duyệt ở retrofit world-lock (NÃO veto footage generic-in-world cho beat
# filler thuần nền -> heuristic Phase 0 lấy top kho free). Thang 3 nấc, nấc nào có
# hàng thì dừng: ① query gốc (đường find_local_candidates chuẩn: geo-gate + C6 +
# used-exclusion) ② rút query về ĐUÔI danh từ ('sand tiger embryo'->'tiger embryo'
# ->'embryo') ③ từ vựng chủ thể kho (vocab_for_niche). CHỈ kho own — viral bị gạt
# (sàn không đụng pháp lý c8); niche WORLD_LOCK gạt cảnh có người (WRONG-vs-BLAND:
# nền niche KHÔNG người), niche khác chỉ ưu tiên không-người. Pick mang
# source="floor" + warning để editor soát/swap trên report.
FLOOR_VOCAB_TOP = 10  # nấc ③: thử top-N từ chủ thể kho


def _floor_ladder(queries) -> list[SearchQueries]:
    """Nấc ①+② của thang sàn — nấc ③ (vocab kho) build lúc chạy vì cần conn."""
    base = [q for q in list(queries.local) + list(queries.specific) if q.strip()]
    tails: list[str] = []
    for q in base:
        words = q.split()
        for k in range(1, len(words)):  # tiếng Anh: danh từ chính nằm CUỐI cụm
            t = " ".join(words[k:])
            if t and t not in tails and t not in base:
                tails.append(t)
    out = []
    if base:
        out.append(SearchQueries(local=base))
    if tails:
        out.append(SearchQueries(local=tails))
    return out


def _floor_has_people(conn, path: str) -> bool:
    row = conn.execute(
        "SELECT has_people FROM library_assets WHERE path = ?", (path,)).fetchone()
    return bool(row and row["has_people"])


def _floor_pick(beat, conn, niche, used_in_video, channel, stock,
                assets_dir, project_dir, record, script_text="", why="",
                boost_terms=()) -> ShotPick | None:
    """Trả ShotPick source='floor' hoặc None (kho cạn thật -> giữ needs_human, slug
    của assembler gánh). KHÔNG bao giờ raise — sàn là lưới an toàn, không giết stage."""
    from autoedit.director.live import WORLD_LOCK
    from autoedit.library import db as libdb

    if not niche:
        return None
    try:
        queries = SearchQueries.model_validate(
            beat.search_queries if isinstance(beat.search_queries, dict)
            else beat.search_queries.model_dump())
        ladder = _floor_ladder(queries)
        vocab = [w for w, _ in (libdb.vocab_for_niche(conn, niche).get("subject_words")
                                or [])[:FLOOR_VOCAB_TOP]]
        if vocab:
            ladder.append(SearchQueries(local=vocab))
        world_locked = (niche or "").strip().lower() in WORLD_LOCK
        beat_dur = beat.end - beat.start
        for rung, q in enumerate(ladder, start=1):
            # own_only/no_people lọc TRONG SQL trước cap (bug anh em P7-trước-limit:
            # top kho deepsea theo indexed_at = toàn viral, lọc sau cap là trắng oan)
            cands = find_local_candidates(conn, niche, q, script_text=script_text,
                                          used_keys=used_in_video, own_only=True,
                                          no_people=world_locked)
            if not cands:
                continue
            cands = usage.soft_penalty_sort(conn, channel, cands)          # P7 mềm lịch sử
            cands.sort(key=lambda c: c.get("duration", 1e9) < beat_dur * PREFER_DURATION_RATIO)
            if not world_locked:  # niche thường: ưu tiên không-người, không gạt hẳn
                cands.sort(key=lambda c: _floor_has_people(conn, c["path"]))
            if boost_terms:
                # BOOST: sàn = đúng nghĩa đen "đoạn không kiếm được footage" — editor
                # thật đổ cảnh X vào đây (user 2026-07-17); sort cuối = khóa chính
                cands.sort(key=lambda c: not _matches_boost(c, boost_terms))
            for chosen in cands:
                try:
                    asset_path = _materialize(chosen, beat, stock, assets_dir, project_dir)
                except (RuntimeError, OSError):
                    continue
                record.warnings.append(
                    f"beat {beat.beat_id}: SÀN NICHE tự đắp (nấc {rung}) "
                    f"{chosen.get('description', '')!r} — {why or 'phễu trắng'}; editor swap nếu cần")
                return ShotPick(
                    beat_id=beat.beat_id, status="ok", source="floor",
                    asset_path=asset_path, asset_key=chosen["asset_key"],
                    source_channel=chosen.get("source_channel", ""),
                    boost_hit=bool(boost_terms and _matches_boost(chosen, boost_terms)),
                    note=f"SÀN NICHE nấc {rung} (lý do gốc: {why or 'phễu trắng'}): "
                         f"{chosen.get('description', '')}",
                )
    except Exception as exc:  # noqa: BLE001 — sàn fail-open
        record.warnings.append(f"beat {beat.beat_id}: sàn niche lỗi ({exc}) — giữ needs_human")
    return None


def _source_stock(beat, conn, stock, niche, used_in_video, channel,
                  assets_dir, project_dir, record, script_text="",
                  brain=None, ctx=None, local_stats=None, ledger=None,
                  boost_terms=(), refs=(), matcher=None) -> ShotPick:
    # PA-1: chunk đã chấm batch -> dùng lại ứng viên + verdict cache, không gather/call lại
    cached = (ctx or {}).get("batch_cache", {}).pop(beat.beat_id, None) if ctx else None
    if cached is not None:
        candidates, prescored, queries = cached
    else:
        sig_first = bool(ctx is not None and ctx.get("signature_first"))
        candidates, queries = _gather_candidates(
            beat, conn, stock, niche, used_in_video, sig_first, script_text,
            local_stats=local_stats, ledger=ledger, boost_terms=boost_terms,
            refs=refs, matcher=matcher)
        prescored = None

    if brain is not None:
        try:
            return _pick_by_funnel(beat, candidates, brain, ctx, conn, channel,
                                   stock, assets_dir, project_dir, record, queries,
                                   used_in_video, prescored=prescored, ledger=ledger)
        except (ValueError, RuntimeError) as exc:
            # LLM lỗi ở MỘT beat KHÔNG được giết cả stage: 02/09 GLM trả verdicts[7]
            # rỗng -> hỏng lượt chấm -> chết job sau 8 phút, mất luôn 19 beat đã chấm
            # xong. Rơi xuống heuristic ngay dưới: chọn kém tinh hơn nhưng CÓ footage,
            # và ghi rõ beat nào để người còn biết mà xem lại.
            record.warnings.append(
                f"beat {beat.beat_id}: phễu c5 lỗi ({str(exc)[:120]}) — "
                f"dùng heuristic cho beat này")

    # ---- đường heuristic Phase 0 (không brain) ------------------------------
    # 4.4: ưu tiên clip đủ dài (sort ổn định — relevance bảo toàn trong nhóm)
    beat_dur = beat.end - beat.start
    candidates.sort(
        key=lambda c: c.get("duration", 1e9) < beat_dur * PREFER_DURATION_RATIO
    )
    candidates = usage.soft_penalty_sort(conn, channel, candidates)  # P7

    # 4.7: download hỏng -> thử ứng viên kế tiếp, KHÔNG giết cả stage
    for idx, chosen in enumerate(candidates):
        if ledger is not None and ledger.blocks(chosen):
            continue  # C8: gate pháp lý viral — re-check tại pick (beat trước có thể vừa lấy)
        try:
            asset_path = _materialize(chosen, beat, stock, assets_dir, project_dir)
        except (RuntimeError, OSError) as exc:
            record.warnings.append(
                f"beat {beat.beat_id}: tải hỏng ứng viên {chosen['asset_key']} — thử tiếp ({exc})"
            )
            continue
        if ledger is not None:
            ledger.add(chosen)
        return ShotPick(
            beat_id=beat.beat_id, status="ok", source=chosen["source"],
            asset_path=asset_path, asset_key=chosen["asset_key"],
            source_channel=chosen.get("source_channel", ""),
            boost_hit=bool(chosen.get("is_boost")),
            note=chosen.get("description", ""),
            peak=bool(chosen.get("peak_value")),  # ytref §3h: report đánh dấu ⭐
            alternates=[c.get("url") or c.get("path", "") for c in candidates[idx + 1:idx + 4]],
        )
    return ShotPick(
        beat_id=beat.beat_id, status="needs_human", source="none",
        note=f"Hết thang fallback cho queries {queries.specific + queries.broad}",
    )


def _shot_count_target(beat) -> int:
    """N mong muốn (pha 1 = ý định LLM) đã kẹp theo SÀN thời lượng (beat ngắn → ít shot).
    Pha 2 (pool quyết) làm ở vòng tải. Beat có info-card/chart-half → giữ 1 shot (layout riêng)."""
    if beat.info_card is not None or (
        beat.graphic_spec is not None and getattr(beat.graphic_spec, "layout", "") == "half"
    ):
        return 1
    by_floor = max(1, int((beat.end - beat.start) / MIN_SHOT_DUR))
    return max(1, min(beat.shot_count, by_floor))


def _gate_warn(result, record, msg: str) -> None:
    """Warning C5 vào CẢ rank_log (result) lẫn stage source (record) — record đã extend
    result.warnings TRƯỚC vòng pick nên append sau đó phải đi cả 2 tay."""
    result.warnings.append(msg)
    record.warnings.append(msg)


def _gate_check(gate, chosen, asset_path, beat, ctx, project_dir, record):
    """C5: hỏi mắt vision 1 câu cho lead-pick. Mọi lỗi -> None (fail-open — gate là tối
    ưu, không giết stage); 3 lỗi LIÊN TIẾP thì TẮT gate cả run (GLM sập không kéo lê
    cả video; soi được lại thì reset đếm — V11 lần 1 chết oan vì đếm lỗi TỔNG:
    3 hắt hơi thoáng qua đầu run tắt gate của cả 92 beat sau)."""
    try:
        v = gate.check(Path(project_dir) / asset_path, beat,
                       central_subject=ctx.get("central_subject", ""),
                       video_subject=ctx.get("video_subject", ""),
                       claim=chosen.get("description", ""))
        ctx["gate_streak"] = 0
        ctx["gate_errors"] = ctx.get("gate_errors", 0)  # giữ tổng cho dòng tổng kết RANK
        return v
    except Exception as exc:  # noqa: BLE001
        ctx["gate_errors"] = ctx.get("gate_errors", 0) + 1
        ctx["gate_streak"] = ctx.get("gate_streak", 0) + 1
        record.warnings.append(
            f"beat {beat.beat_id}: C5 gate lỗi ({str(exc)[:120]}) — nhận pick không soi")
        if ctx["gate_streak"] >= 3:
            ctx["gate"] = None
            record.warnings.append(
                "C5 gate TẮT sau 3 lỗi liên tiếp — các beat sau nhận pick không soi")
        return None


def _pick_by_funnel(beat, candidates, brain, ctx, conn, channel,
                    stock, assets_dir, project_dir, record, queries, used_in_video,
                    prescored=None, ledger=None) -> ShotPick:
    """Đường phễu c5 (F5): NÃO chấm (per-beat HOẶC verdict batch PA-1 có sẵn) -> tải TOP-N
    clip khác nhau theo điểm (giữ 4.7). N = min(shot_count LLM, sàn thời lượng, pool).
    Clip chính = ShotPick, còn lại = extra_shots."""
    times_used = (lambda k: usage.times_used(conn, channel, k)) if channel else None
    if prescored is not None:  # PA-1: verdict từ call batch ({} = pool ≤1, tự auto-pick PA-3)
        result = rank_beat_prescored(
            beat, candidates, prescored,
            prev_shot_size=ctx.get("prev_shot_size", ""), times_used=times_used,
        )
        batch_tok = ctx.pop("batch_usage", None)  # token cả chunk ghi vào beat ĐẦU tiêu thụ
        if batch_tok:
            result.input_tokens, result.output_tokens = batch_tok
    else:
        result = rank_beat(
            beat, candidates, brain,
            central_subject=ctx.get("central_subject", ""),
            prev_pick_note=ctx.get("prev_pick_note", ""),
            prev_shot_size=ctx.get("prev_shot_size", ""),
            chapter_open=ctx.get("chapter_open", False),
            video_subject=ctx.get("video_subject", ""),
            times_used=times_used,
        )
    ctx["results"].append(result)
    record.warnings.extend(result.warnings)

    n_want = _shot_count_target(beat)
    by_key = {c["asset_key"]: c for c in candidates}
    picked: list[tuple[dict, str, str]] = []  # (candidate, asset_path, ly_do)
    gate = ctx.get("gate")   # C5 đợt 5: mắt vision soi lead-pick (None = tắt, hành vi cũ)
    gate_calls = 0
    gate_stash = None        # (chosen, asset_path, ly_do) — lead điểm CAO NHẤT bị chê lần 1
    last_idx = -1
    for idx, rc in enumerate(result.ranked):
        if len(picked) >= n_want:
            break
        if rc.asset_key in used_in_video:
            continue  # P7 trong chunk PA-1: pool gather TRƯỚC, beat trước có thể vừa lấy
        chosen = by_key[rc.asset_key]
        # C8: gate pháp lý viral RE-CHECK tại pick — cùng lý do với P7 dòng trên
        # (chunk PA-1 gather 1 lần, beat trước có thể vừa lấy cảnh hàng xóm/đầy trần 8%)
        if ledger is not None and ledger.blocks(chosen):
            continue
        # 4.7: download hỏng -> thử ứng viên điểm kế tiếp, KHÔNG giết cả stage
        try:
            asset_path = _materialize(chosen, beat, stock, assets_dir, project_dir)
        except (RuntimeError, OSError) as exc:
            record.warnings.append(
                f"beat {beat.beat_id}: tải hỏng ứng viên {rc.asset_key} — thử tiếp ({exc})"
            )
            continue
        ly_do = rc.ly_do or chosen.get("description", "")
        # --- C5 vision gate: CHỈ soi ứng viên sắp thành shot CHÍNH (nguyên tắc top-pick
        # V123 §3c) và CHỈ nguồn trong GATE_SOURCES (user 2026-07-10: kho local — nơi
        # tag máy tự sinh hay nói dối); extra_shots/alternates KHÔNG soi. Budget 2
        # verdict/beat. Không phải cửa loại thứ 3: demote 1 lần, cùng chê giữ điểm cao
        # nhất + warning. -----------------------------------------------------------
        if (not picked and gate is not None and gate_calls < GATE_BUDGET
                and chosen.get("source") in GATE_SOURCES):
            v = _gate_check(gate, chosen, asset_path, beat, ctx, project_dir, record)
            if v is not None:
                gate_calls += 1
                entry = {"asset_key": rc.asset_key, "subject_match": v.subject_match,
                         "mood_match": v.mood_match, "seen": v.seen, "action": "pass"}
                result.vision_gate.append(entry)
                if v.subject_match == "no":
                    entry["action"] = "demote"
                    if gate_calls < GATE_BUDGET:  # lần 1: gạt, thử ứng viên điểm kế
                        gate_stash = (chosen, asset_path, ly_do)
                        _gate_warn(result, record,
                                   f"beat {beat.beat_id}: C5 chê {rc.asset_key} "
                                   f"(mắt thấy: {v.seen}) — thử ứng viên kế")
                        continue
                    # lần 2 cũng chê -> user chốt: lấy bản điểm phễu CAO NHẤT + soát tay
                    chosen, asset_path, ly_do = gate_stash
                    for e in result.vision_gate:
                        if e["asset_key"] == chosen["asset_key"]:
                            e["action"] = "giu_du_nghi_sai"
                    _gate_warn(result, record,
                               f"beat {beat.beat_id}: C5 chê cả 2 top-pick — giữ "
                               f"{chosen['asset_key']} (điểm phễu cao nhất), editor SOÁT TAY")
                elif v.mood_match == "no":
                    entry["action"] = "mood_warning"
                    _gate_warn(result, record,
                               f"beat {beat.beat_id}: C5 mood nghi lệch {rc.asset_key} "
                               f"(mắt thấy: {v.seen}) — giữ pick, editor liếc qua")
        picked.append((chosen, asset_path, ly_do))
        used_in_video.add(chosen["asset_key"])  # P7: cả N clip không lặp ở beat sau
        if ledger is not None:
            ledger.add(chosen)  # C8: ghi sổ SAU khi tải thành công
        last_idx = idx

    # C5: lead bị chê rồi hết ứng viên (tải hỏng/P7/ledger chặn nốt) -> vớt lại bản
    # điểm cao nhất thay vì rơi needs_human (gate không bao giờ làm beat trống thêm)
    if not picked and gate_stash is not None:
        chosen, asset_path, ly_do = gate_stash
        picked.append((chosen, asset_path, ly_do))
        used_in_video.add(chosen["asset_key"])
        if ledger is not None:
            ledger.add(chosen)
        for e in result.vision_gate:
            if e["asset_key"] == chosen["asset_key"]:
                e["action"] = "giu_du_nghi_sai"
        _gate_warn(result, record,
                   f"beat {beat.beat_id}: C5 chê pick nhưng không còn ứng viên thay — giữ "
                   f"{chosen['asset_key']}, editor SOÁT TAY")

    if not picked:
        return ShotPick(
            beat_id=beat.beat_id, status="needs_human", source="none",
            note=f"Phễu không còn ứng viên cho queries {queries.specific + queries.broad}",
        )

    # mạch c3 cho beat sau: hàng xóm N−1 = clip CUỐI của beat này
    last_cand = picked[-1][0]
    ctx["prev_pick_note"] = last_cand.get("description") or beat.visual_concept
    ctx["prev_shot_size"] = last_cand.get("shot_size", "")
    if len(picked) > 1:
        record.warnings.append(
            f"beat {beat.beat_id}: {len(picked)} shot nối tiếp (shot_count={beat.shot_count})"
        )

    lead, lead_path, lead_ly_do = picked[0]
    return ShotPick(
        beat_id=beat.beat_id, status="ok", source=lead["source"],
        asset_path=lead_path, asset_key=lead["asset_key"], note=lead_ly_do,
        source_channel=lead.get("source_channel", ""),
        boost_hit=bool(lead.get("is_boost")),
        peak=bool(lead.get("peak_value")),  # ytref §3h: report đánh dấu ⭐
        extra_shots=[
            ExtraShot(asset_path=p, asset_key=c["asset_key"],
                      source=c["source"], note=ly,
                      source_channel=c.get("source_channel", ""),
                      boost_hit=bool(c.get("is_boost")))
            for c, p, ly in picked[1:]
        ],
        alternates=[
            (by_key[r.asset_key].get("url") or by_key[r.asset_key].get("path", ""))
            for r in result.ranked[last_idx + 1:last_idx + 4]
        ],
    )


def _source_entity(beat, entity, conn, niche, library_root,
                   assets_dir, project_dir, record) -> ShotPick:
    if entity is None:
        return ShotPick(
            beat_id=beat.beat_id, status="needs_human", source="none",
            licensing_flag=True,
            note="Thiếu GOOGLE_CSE_KEY/GOOGLE_CSE_CX — tìm tay ảnh thật cho: "
            + "; ".join(beat.entity_queries),
        )
    for q in beat.entity_queries:
        # cache theo thực thể: đã tải lần nào thì tái dùng, không tốn query (4.1)
        cache_dir = entity_cache_dir(niche or "default", q, library_root)
        # CHỈ nhận ảnh THẬT trong cache — bỏ file HTML-lưu-nhầm-.jpg lần trước (bug 19/06)
        # + Lớp 2: bỏ ảnh cache MỜ dưới sàn (đo lỗi → 0 → fail-open giữ lại, không loại oan)
        cached = [
            c for c in sorted(cache_dir.glob("*.*"))
            if looks_like_image(c) and (image_width(c) or MIN_IMAGE_WIDTH) >= MIN_IMAGE_WIDTH
        ] if cache_dir.is_dir() else []
        if cached:
            asset_path = _copy_to_assets(cached[0], beat, assets_dir, project_dir)
            return ShotPick(
                beat_id=beat.beat_id, status="ok", source="entity",
                asset_path=asset_path, asset_key=f"entity-cache:{cache_dir.name}",
                licensing_flag=True, note=f"cache entity '{q}'",
                alternates=[str(p) for p in cached[1:4]],
            )
        results = entity.search_images(q)
        # 4.7: ảnh tải hỏng (403/404/quá nhỏ) -> thử ảnh kế, không giết stage
        for idx, chosen in enumerate(results):
            cache_dir.mkdir(parents=True, exist_ok=True)
            ext = Path(chosen["url"].split("?")[0]).suffix.lower() or ".jpg"
            if ext == ".svg":      # ffmpeg/CapCut không đọc SVG -> bỏ, thử ảnh kế
                continue
            try:
                cached_file = entity.download(
                    chosen, cache_dir / f"{chosen['asset_key'].split(':')[1]}{ext}"
                )
            except (RuntimeError, OSError) as exc:
                record.warnings.append(
                    f"beat {beat.beat_id}: ảnh entity tải hỏng {chosen['origin']} — thử tiếp ({exc})"
                )
                continue
            asset_path = _copy_to_assets(cached_file, beat, assets_dir, project_dir)
            return ShotPick(
                beat_id=beat.beat_id, status="ok", source="entity",
                asset_path=asset_path, asset_key=chosen["asset_key"],
                licensing_flag=True,
                note=f"{chosen.get('description', '')} ({chosen.get('origin', '')})",
                alternates=[r["url"] for r in results[idx + 1:idx + 4]],
            )
    return ShotPick(
        beat_id=beat.beat_id, status="needs_human", source="none", licensing_flag=True,
        note="CSE không có kết quả sạch cho: " + "; ".join(beat.entity_queries),
    )


def _render_half_chart(beat, assets_dir, project_dir, record):
    """Render chart half-layout làm asset PiP. Trả path tương đối; lỗi -> None + warning."""
    from autoedit.packager.charts import render_chart
    from autoedit.project import slugify

    dur = max(beat.end - beat.start + 1.0, 3.0)
    out = assets_dir / f"b{beat.beat_id:03d}_chartpip_{slugify(beat.graphic_spec.title)[:26]}.mp4"
    try:
        render_chart(beat.graphic_spec, dur, out)
    except Exception as exc:
        record.warnings.append(f"beat {beat.beat_id}: render chart PiP lỗi ({exc}) — bỏ chart")
        return None
    return str(out.relative_to(project_dir))


def _render_info_card(beat, assets_dir, project_dir, record):
    """Render thẻ chữ bổ sung (P2B Req6) làm asset nửa phải. Lỗi -> None + warning."""
    from autoedit.packager.infocard import render_info_card

    dur = max(beat.end - beat.start + 1.0, 4.0)
    out = assets_dir / f"b{beat.beat_id:03d}_infocard.mp4"
    try:
        render_info_card(beat.info_card, dur, out)
    except Exception as exc:
        record.warnings.append(f"beat {beat.beat_id}: render info-card lỗi ({exc}) — bỏ")
        return None
    return str(out.relative_to(project_dir))


def _source_graphic(beat, conn, stock, niche, used_in_video, channel,
                    assets_dir, project_dir, script_text="") -> ShotPick:
    """Beat có graphic_spec -> RENDER biểu đồ động (P1.5); không thì placeholder + nền."""
    if beat.graphic_spec is not None:
        from autoedit.packager.charts import render_chart
        from autoedit.project import slugify

        dur = max(beat.end - beat.start + 1.0, 3.0)  # phủ beat + chừa margin
        out = assets_dir / f"b{beat.beat_id:03d}_chart_{slugify(beat.graphic_spec.title)[:30]}.mp4"
        try:
            render_chart(beat.graphic_spec, dur, out)
        except Exception as exc:  # render hỏng -> rơi về placeholder, không giết stage
            return ShotPick(
                beat_id=beat.beat_id, status="graphic", source="none",
                note=f"RENDER CHART LỖI ({exc}) — editor làm graphic: {beat.visual_concept}",
            )
        return ShotPick(
            beat_id=beat.beat_id, status="graphic", source="chart",
            asset_path=str(out.relative_to(project_dir)),
            asset_key=f"chart:{beat.beat_id}",
            note=f"Biểu đồ {beat.graphic_spec.chart_type} tự sinh: {beat.graphic_spec.title}",
        )

    queries = SearchQueries.model_validate(
        beat.search_queries if isinstance(beat.search_queries, dict)
        else beat.search_queries.model_dump()
    )
    note = f"EDITOR LÀM GRAPHIC: {beat.visual_concept}"
    bg = SearchQueries(specific=[], broad=[], thematic=queries.thematic)
    candidates = [c for c in (find_local_candidates(conn, niche, bg, script_text=script_text,
                                                    used_keys=used_in_video)
                              + stock.search_tiered(bg))
                  if c["asset_key"] not in used_in_video]
    for chosen in usage.soft_penalty_sort(conn, channel, candidates):
        try:
            asset_path = _materialize(chosen, beat, stock, assets_dir, project_dir)
        except (RuntimeError, OSError):
            continue  # nền lót là phụ — hỏng thì thử cái khác, hết thì thôi
        return ShotPick(
            beat_id=beat.beat_id, status="graphic", source=chosen["source"],
            asset_path=asset_path, asset_key=chosen["asset_key"],
            note=note + " (đã tải nền lót)",
        )
    return ShotPick(beat_id=beat.beat_id, status="graphic", source="none", note=note)


# ----------------------------------------------------------------------------
def _stock_dest(candidate: dict, beat: Beat, assets_dir: Path) -> Path:
    """Tên file đích cho ứng viên stock — TÁCH RIÊNG vì warm-up TOC-3b phải tính
    ĐÚNG tên vòng pick sẽ dùng (lệch tên = tải trước vô ích).

    Tên theo concept của beat (PRD: b012_vietnam-beach.mp4) — description của Pexels
    là URL trang, không dùng làm slug. THÊM hash asset_key (F5 shot_count): nhiều clip
    CÙNG beat có cùng concept -> phải khác tên, không clip sau ĐÈ clip trước."""
    slug = slugify(beat.visual_concept)[:34]
    uid = hashlib.sha1(candidate["asset_key"].encode()).hexdigest()[:6]
    ext = ".mp4" if candidate["media_type"] == "video" else ".jpg"
    return assets_dir / f"b{beat.beat_id:03d}_{slug}_{uid}{ext}"


def _prefetch_plan(chunk, gathered, maps_by_bid, used_in_video, ledger,
                   assets_dir) -> list[tuple]:
    """TOC-3b: chọn ứng viên đáng tải TRƯỚC cho chunk vừa có verdict — top điểm NÃO
    thuần mỗi beat (thiếu điểm máy ±2.5 nên chỉ XẤP XỈ top-1 phễu; trượt = phí 1 file,
    PICK THẬT vẫn do phễu quyết y cũ). Chỉ ứng viên có url (local/REF = copy, khỏi tải);
    né used/ledger tại thời điểm lập kế hoạch (staleness vô hại — chỉ đỡ tải phí)."""
    plan: list[tuple] = []
    for b in chunk:
        verdicts = maps_by_bid.get(b.beat_id)
        if not verdicts:
            continue  # PA-3 pool ≤1 / NÃO quên — không đoán
        cands, _q = gathered[b.beat_id]
        by_key = {c["asset_key"]: c for c in cands}
        ranked = sorted(
            ((k, v) for k, v in verdicts.items() if k in by_key and v.verdict == "ok"),
            key=lambda kv: -(kv[1].diem_nghia * NGHIA_W + kv[1].diem_mood * MOOD_W))
        n = 0
        for k, v in ranked:
            if n >= PREFETCH_PER_BEAT:
                break
            c = by_key[k]
            if not c.get("url") or k in used_in_video:
                continue
            if ledger is not None and ledger.blocks(c):
                continue
            plan.append((c, _stock_dest(c, b, assets_dir)))
            n += 1
    return plan


def _materialize(candidate: dict, beat: Beat, stock, assets_dir: Path, project_dir: Path) -> str:
    """Đưa ứng viên thành file trong assets/ — local: copy; stock: download
    (TOC-3b: warm-up đã tải sẵn thì _TimedStock.download tự tái dùng)."""
    if candidate["source"] == "local":
        return _copy_to_assets(Path(candidate["path"]), beat, assets_dir, project_dir)
    dest = _stock_dest(candidate, beat, assets_dir)
    # REF VIDEO: file đã nằm sẵn trên đĩa — "tải" ở đây là CẮT bằng ffmpeg.
    # Phân nhánh phải ở ĐÂY (đường DUY NHẤT mọi ứng viên đi qua), không phải trong
    # MultiStockClient: chỉ có 1 nguồn stock thì `stock` là PexelsClient trực tiếp,
    # MultiStockClient bị bỏ qua và nhánh refvideo không bao giờ chạy — đo thật
    # 02/09: 8 beat chọn ref, cả 8 đều "Tải hỏng sau 3 lần" vì Pexels đi tải một
    # đường dẫn file local.
    if candidate["source"] == "refvideo":
        from autoedit.sourcer.refvideo import cat_clip

        cat_clip(Path(candidate["url"]),
                 float(candidate.get("src_in") or 0.0),
                 float(candidate.get("duration") or 0.0), dest)
        return str(dest.relative_to(project_dir))
    stock.download(candidate, dest)
    return str(dest.relative_to(project_dir))


def _copy_to_assets(src: Path, beat: Beat, assets_dir: Path, project_dir: Path) -> str:
    dest = assets_dir / f"b{beat.beat_id:03d}_{slugify(src.stem)[:40]}{src.suffix.lower()}"
    shutil.copy2(src, dest)
    return str(dest.relative_to(project_dir))
