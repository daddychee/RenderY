"""M3b (C đợt 3b) — vision-tag footage STOCK/ENTITY đã pick (MO_TA_SFX_HOAN_THIEN §4a).

Kho local có mắt vision từ ingest; pick stock mù -> subject-SFX chỉ phủ ~20% beat
(tai V6: "3 tiếng là ít"). Tag frame THẬT của từng pick bằng GLMVisionTagger sẵn có,
LƯU VĨNH VIỄN cache.db::stock_tags theo asset_key -> video sau tái dùng miễn phí;
đồng thời là nền C5 đợt 5 + vòng học editor-learn (project.json giữ asset_key từng beat).

Rà chồng chéo: chạy SAU khi picks chốt -> không lật được quyết định phễu/ranker;
chỉ ambient/subject-SFX tiêu thụ. Fail-open từng asset lẫn cả tầng.
"""

from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

# Key KHÔNG tag: local đã có vision trong library_assets; chart là đồ họa máy render.
_SKIP_PREFIXES = ("local:", "chart:")
THREADS_PER_KEY = 3  # PB3-B2: >3 luồng/key bigmodel cắt kết nối


def stock_keys_to_tag(project) -> dict[str, str]:
    """asset_key -> asset_path (tương đối project_dir) của các pick CHÍNH stock/entity,
    dedup (1 asset dùng nhiều beat chỉ tag 1 lần)."""
    out: dict[str, str] = {}
    for s in project.shots:
        k = s.asset_key
        if not k or k.startswith(_SKIP_PREFIXES) or not s.asset_path:
            continue
        out.setdefault(k, s.asset_path)
    return out


def lookup_row(conn: sqlite3.Connection, asset_key: str):
    """Dòng stock_tags theo asset_key; bảng chưa có (db cũ) -> None (fail-open)."""
    try:
        return conn.execute(
            "SELECT * FROM stock_tags WHERE asset_key = ?", (asset_key,)
        ).fetchone()
    except sqlite3.OperationalError:
        return None


def tag_project_stock(project, project_dir: Path, conn: sqlite3.Connection,
                      tagger_factory=None) -> dict:
    """Tag các pick stock CHƯA có trong bảng. Trả {"tagged", "cached", "failed": [(key, lý do)]}.

    tagger_factory(api_key) -> tagger (tiêm được cho test); mặc định GLMVisionTagger
    multi-key. Vision chạy song song ≤THREADS_PER_KEY/key; ghi db ở luồng chính
    (sqlite conn không thread-safe).
    """
    todo = stock_keys_to_tag(project)
    cached = 0
    for k in list(todo):
        if lookup_row(conn, k) is not None:
            cached += 1
            todo.pop(k)
    result = {"tagged": 0, "cached": cached, "failed": []}
    if not todo:
        return result

    if tagger_factory is None:
        from autoedit.library.vision import GLMVisionTagger
        tagger_factory = lambda key: GLMVisionTagger(api_key=key)  # noqa: E731
        from autoedit.library.vision import glm_api_keys
        keys = glm_api_keys()
    else:
        keys = [""]
    if not keys:
        raise RuntimeError("Thiếu GLM_API_KEY trong .env — không tag stock được")
    taggers = [tagger_factory(k) for k in keys]

    def _one(idx_key_rel):
        i, (key, rel) = idx_key_rel
        path = Path(project_dir) / rel
        if not path.is_file():
            raise FileNotFoundError(f"không thấy file {rel}")
        return key, taggers[i % len(taggers)].tag(path)

    rows = []
    with ThreadPoolExecutor(max_workers=min(THREADS_PER_KEY * len(taggers), len(todo))) as ex:
        futs = {ex.submit(_one, item): item[1][0] for item in enumerate(todo.items())}
        for fut, key in futs.items():
            try:
                k, tags = fut.result()
                rows.append((k, tags))
            except Exception as exc:  # noqa: BLE001 — 1 asset hỏng không giết mẻ
                result["failed"].append((key, str(exc)[:160]))

    from autoedit.library.vision import media_type_of
    now = datetime.now(timezone.utc).isoformat()
    for k, t in rows:
        mtype = media_type_of(Path(project_dir) / todo[k]) or ""
        conn.execute(
            # G2: ON CONFLICT thay INSERT OR REPLACE — chạy cả 2 lưng
            """INSERT INTO stock_tags
               (asset_key, media_type, subject, description, scene_type, shot_size,
                mood, tags, model, tagged_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(asset_key) DO UPDATE SET
                 media_type=excluded.media_type, subject=excluded.subject,
                 description=excluded.description, scene_type=excluded.scene_type,
                 shot_size=excluded.shot_size, mood=excluded.mood,
                 tags=excluded.tags, model=excluded.model, tagged_at=excluded.tagged_at""",
            (k, mtype, t.subject, t.description, t.scene_type, t.shot_size,
             ", ".join(t.mood), json.dumps(t.tags, ensure_ascii=False),
             getattr(taggers[0], "model", ""), now),
        )
        result["tagged"] += 1
    conn.commit()
    return result
