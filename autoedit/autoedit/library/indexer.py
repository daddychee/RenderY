"""Indexer — walk folder niche, tag asset mới/đổi bằng vision, lưu cache.db.

PB4: tag chạy SONG SONG (bài học PB3-B2): ≤3 luồng/key, nhiều tagger round-robin
(multi-key), so le khởi động đợt đầu. SQLite chỉ ghi ở MAIN thread (conn không
thread-safe) — worker chỉ rút frame + đo màu + gọi vision. Máy tag `tag_jobs`
dùng chung cho index folder (file rời) và ống nạp draft (ingest.py).
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence

from autoedit.library import db
from autoedit.library.vision import VisionTagger, measure_colors, media_type_of, preview_images
from autoedit.project import ffprobe_duration

WORKERS_PER_KEY = 3  # PB3-B2: >3 luồng/key -> bigmodel cắt kết nối (SSLEOF)

# Folder chứa clip do ống nạp cắt ra — tên folder = tên project nguồn, KHÔNG phải
# ground truth ngữ nghĩa -> không đưa làm folder_context cho vision (tránh "SP1 - 003"
# lọt vào tags). Vẫn nằm trong _candidates để move/prune hoạt động bình thường.
INGEST_DIR = "nap"


@dataclass
class IndexResult:
    indexed: list[str]
    skipped: int          # đã có trong db, file không đổi
    failed: list[tuple[str, str]]  # (path, lỗi)
    moved: int = 0        # file đổi chỗ — cập nhật path, không tag lại
    pruned: int = 0       # dòng db trỏ file đã xóa — dọn


@dataclass
class TagJob:
    """1 file cần tag + metadata ghi db. extra = cột ống nạp (§3b) đè lên default."""

    path: Path
    mtime: float
    category: str
    folder_path: str
    folder_context: str
    source_title: str = ""   # 2a: tiêu đề video NGUỒN (ống nạp) — gợi ý chủ đề cho vision
    section_hint: str = ""   # ytref §3i-2: YouTube chapter chứa cảnh — chỉ đường có chapters
    topic: str = ""          # ytref §3i-3: chủ đề editor khai (--topic) — mọi mẻ own/viral
    extra: dict = field(default_factory=dict)


def _candidates(niche_dir: Path) -> list[Path]:
    """Mọi media trong folder niche, trừ entity/ (cache của M5, tự quản)."""
    out = []
    for path in sorted(niche_dir.rglob("*")):
        if not path.is_file() or media_type_of(path) is None:
            continue
        rel = path.relative_to(niche_dir)
        if rel.parts and rel.parts[0] == "entity":
            continue
        out.append(path)
    return out


def _probe_meta(path: Path, mtype: str) -> tuple[float, int, int, float]:
    """(duration s, width, height, fps) — §3b code thuần 0 token; fail-open về 0."""
    try:
        if mtype == "image":
            from PIL import Image

            with Image.open(path) as im:
                return 0.0, im.width, im.height, 0.0
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
             "stream=width,height,r_frame_rate", "-of", "json", str(path)],
            capture_output=True, text=True, timeout=30)
        info = (json.loads(out.stdout).get("streams") or [{}])[0]
        num, _, den = str(info.get("r_frame_rate", "0/1")).partition("/")
        fps = round(float(num) / float(den or 1), 2) if float(den or 1) else 0.0
        return (round(ffprobe_duration(path) or 0.0, 3),
                int(info.get("width") or 0), int(info.get("height") or 0), fps)
    except Exception:
        return 0.0, 0, 0, 0.0


def tag_jobs(
    conn: sqlite3.Connection,
    niche: str,
    jobs: Sequence[TagJob],
    taggers: Sequence[VisionTagger],
    on_progress: Optional[Callable[[int, int, Path], None]] = None,
    stagger_s: float = 0.0,
) -> tuple[list[str], list[tuple[str, str]]]:
    """Tag song song -> upsert db. Trả (indexed, failed).

    - job i -> tagger i % n (round-robin key, tải chia đều)
    - luồng = min(số job, WORKERS_PER_KEY × số tagger)
    - đợt đầu so le `stagger_s`/job (tránh loạt TLS handshake + upload cùng lúc —
      tagger MẠNG đặt 2.0, tagger fake/test để 0)
    - on_progress(i, tổng, path) gọi ở main thread KHI job xong (không phải trước tag)
    """
    if not jobs:
        return [], []
    if not taggers:
        raise ValueError("tag_jobs cần ≥1 tagger")
    workers = max(1, min(len(jobs), WORKERS_PER_KEY * len(taggers)))

    def work(job: TagJob, tagger: VisionTagger, stagger: float) -> db.AssetRecord:
        time.sleep(stagger)
        mtype = media_type_of(job.path) or ""
        # frame rút 1 LẦN dùng chung vision + đo màu; đo màu fail-open (cùng họ
        # image_width F5-M3): frame hỏng -> tagger tự rút lại, màu để rỗng.
        try:
            images: list[bytes] | None = preview_images(job.path)
            dominant, brightness, saturation = measure_colors(images)
        except Exception:
            images, dominant, brightness, saturation = None, "", 0.0, 0.0
        tags = tagger.tag(job.path, job.folder_context, images=images,
                          source_title=job.source_title,
                          section_hint=job.section_hint, topic=job.topic)
        duration, width, height, fps = _probe_meta(job.path, mtype)
        return db.AssetRecord(
            niche=niche, path=str(job.path), category=job.category,
            folder_path=job.folder_path, media_type=mtype, mtime=job.mtime,
            subject=tags.subject, description=tags.description,
            shot_size=tags.shot_size, mood=", ".join(tags.mood),
            scene_type=tags.scene_type, camera_angle=tags.camera_angle,
            dominant_color=dominant, brightness=brightness, saturation=saturation,
            has_people=tags.has_people, tags=tags.tags,
            duration=duration, width=width, height=height, fps=fps,
            **job.extra,
        )

    indexed: list[str] = []
    failed: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, j, taggers[i % len(taggers)],
                          i * stagger_s if i < workers else 0.0): j
                for i, j in enumerate(jobs)}
        for i, fut in enumerate(as_completed(futs), start=1):
            job = futs[fut]
            try:
                db.upsert_asset(conn, fut.result())  # ghi sqlite ở MAIN thread
                indexed.append(str(job.path))
            except Exception as exc:  # decode hỏng / vision bỏ cuộc -> ghi log, đi tiếp
                failed.append((str(job.path), str(exc)))
            if on_progress:
                on_progress(i, len(jobs), job.path)
    return indexed, failed


def index_niche(
    conn: sqlite3.Connection,
    niche: str,
    niche_dir: Path,
    tagger: VisionTagger | Sequence[VisionTagger],
    on_progress: Optional[Callable[[int, int, Path], None]] = None,
    limit: Optional[int] = None,
    stagger_s: float = 0.0,
) -> IndexResult:
    """Index media trong folder niche. `tagger` nhận 1 tagger hoặc list (multi-key).

    limit: dừng sau khi tag MỚI `limit` file (để chạy thử/giới hạn ngân sách); None = hết.
    Khi có limit, KHÔNG prune dòng chết (tránh xóa nhầm phần chưa quét tới).
    """
    taggers = list(tagger) if isinstance(tagger, (list, tuple)) else [tagger]
    result = IndexResult(indexed=[], skipped=0, failed=[])
    candidates = _candidates(niche_dir)

    # File đã di chuyển/đổi tên folder: dòng db cũ trỏ path chết. Nhận diện lại
    # theo (tên file + mtime) để giữ tag vision — không tốn tiền tag lại.
    known = db.paths_for_niche(conn, niche)
    current_paths = {str(p) for p in candidates}
    dead = {p: row for p, row in known.items() if p not in current_paths}
    dead_by_fingerprint: dict[tuple[str, float], list[str]] = {}
    for p, row in dead.items():
        dead_by_fingerprint.setdefault((Path(p).name, round(row["mtime"], 3)), []).append(p)

    jobs: list[TagJob] = []
    for path in candidates:
        # stat/relative có thể vỡ nếu file BIẾN MẤT giữa chừng (người sắp xếp lại
        # folder khi index đang chạy) -> 1 file hỏng KHÔNG giết cả batch.
        try:
            rel = path.relative_to(niche_dir)
            folder_parts = rel.parts[:-1]  # mọi folder con (trừ tên file)
            category = folder_parts[0] if folder_parts else "uncategorized"
            # full path folder con, POSIX-style để ổn định giữa Win/Mac trong db (searchable)
            folder_path = "/".join(folder_parts)
            # context người-đọc-được đưa cho vision (bắc cầu ngôn ngữ địa danh);
            # folder ống nạp = tên project nguồn, không phải ground truth -> bỏ context
            folder_context = "" if category == INGEST_DIR else " / ".join(folder_parts)
            mtime = path.stat().st_mtime
            if not db.needs_index(conn, str(path), mtime):
                result.skipped += 1
                continue
            fingerprint = (path.name, round(mtime, 3))
            if dead_by_fingerprint.get(fingerprint):
                old_path = dead_by_fingerprint[fingerprint].pop(0)
                db.move_asset(conn, old_path, str(path), category, folder_path)
                dead.pop(old_path, None)
                result.moved += 1
                continue
            jobs.append(TagJob(path=path, mtime=mtime, category=category,
                               folder_path=folder_path, folder_context=folder_context))
        except Exception as exc:
            result.failed.append((str(path), str(exc)))
            continue

    if limit is not None:
        jobs = jobs[:limit]
    indexed, failed = tag_jobs(conn, niche, jobs, taggers,
                               on_progress=on_progress, stagger_s=stagger_s)
    result.indexed.extend(indexed)
    result.failed.extend(failed)
    if limit is not None:
        return result  # chạy thử / giới hạn ngân sách: dừng, KHÔNG prune

    # Dọn dòng chết còn lại (file đã xóa hẳn khỏi thư viện)
    result.pruned = db.delete_assets(conn, list(dead.keys()))
    return result
