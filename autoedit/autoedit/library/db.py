"""SỔ dữ liệu — asset thư viện + usage log P7 + search cache + stock tags.

2 lưng (G2, MO_TA_VAN_HANH_G2_DB_SERVER §3): mặc định SQLite <data_root>/cache.db
(G1, máy chưa cấu hình không đổi gì); đặt db_url (`set-db-url` / env AUTOEDIT_DB_URL)
-> Postgres qua shim PgConnection — nhiều máy ghi đồng thời an toàn. Mọi hàm nhận
conn để test bằng db tạm; test truyền db_path tường minh LUÔN được SQLite.
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from autoedit.packager.machine import resolve_data_root, resolve_db_url

DEFAULT_DB_PATH = resolve_data_root() / "cache.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS library_assets (
    id INTEGER PRIMARY KEY,
    niche TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,          -- đường dẫn tuyệt đối
    category TEXT NOT NULL,             -- folder con cấp 1: signature / entity / <chủ-đề>
    folder_path TEXT NOT NULL DEFAULT '',  -- TOÀN BỘ đường dẫn folder con (giữ nghĩa editor đặt), searchable
    media_type TEXT NOT NULL,           -- video | image
    mtime REAL NOT NULL,                -- để skip file chưa đổi khi re-index
    subject TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    shot_size TEXT NOT NULL DEFAULT '',
    mood TEXT NOT NULL DEFAULT '',      -- 1-2 từ vocab nhạc, nối ', ' (spec TAG_GLM §3a)
    scene_type TEXT NOT NULL DEFAULT '',   -- enum 14 loại cảnh (e1 ambient + c6 chữ ký)
    camera_angle TEXT NOT NULL DEFAULT '', -- c7: chỉ tag ở mẻ thử, có thể bỏ sau PB3
    dominant_color TEXT NOT NULL DEFAULT '',  -- '#rrggbb' — đo code thuần (b1 C2b)
    brightness REAL NOT NULL DEFAULT 0,       -- 0-1
    saturation REAL NOT NULL DEFAULT 0,       -- 0-1
    has_people INTEGER NOT NULL DEFAULT 0,
    tags TEXT NOT NULL DEFAULT '[]',    -- JSON list keyword
    duration REAL NOT NULL DEFAULT 0,   -- §3b code thuần: giây (video; ảnh = 0)
    width INTEGER NOT NULL DEFAULT 0,
    height INTEGER NOT NULL DEFAULT 0,
    fps REAL NOT NULL DEFAULT 0,
    source_video TEXT NOT NULL DEFAULT '',  -- ống nạp PB4: file nguồn gốc đã cắt ra clip này
    scene_start REAL NOT NULL DEFAULT 0,    -- giây bắt đầu trong file nguồn
    scene_index INTEGER NOT NULL DEFAULT 0, -- thứ tự cảnh trên timeline draft nguồn (0 = không từ draft)
    has_voice INTEGER NOT NULL DEFAULT -1,  -- -1 chưa biết (folder-index) | 0/1 từ ống nạp (d2 thở)
    source_class TEXT NOT NULL DEFAULT 'own',   -- c8: own | viral (luật bản quyền chỉ áp viral)
    source_duration REAL NOT NULL DEFAULT 0,    -- c8: tổng giây FILE NGUỒN (mẫu số trần 8% gói CHỌN)
    source_channel TEXT NOT NULL DEFAULT '',    -- VD4 ghi công: KÊNH của video nguồn (≠ asset_usage.channel = kênh sản xuất)
    peak_value REAL,                    -- ytref §3e: value đỉnh Most Replayed 0-1 (NULL = không cờ)
    peak_type TEXT,                     -- ytref §3e: primary | secondary (NULL = không cờ)
    approved INTEGER NOT NULL DEFAULT 0,  -- người duyệt (learning loop sau)
    indexed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assets_niche ON library_assets(niche);

-- P7: log asset đã dùng theo kênh -> phạt mềm khi chọn (KHÔNG chặn cứng)
CREATE TABLE IF NOT EXISTS asset_usage (
    id INTEGER PRIMARY KEY,
    channel TEXT NOT NULL,
    asset_key TEXT NOT NULL,       -- 'pexels:12345' | 'local:/path' | 'entity:url-hash'
    video_id TEXT NOT NULL,        -- project_id
    used_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usage_channel ON asset_usage(channel, asset_key);

-- 4.1: cache kết quả search (provider+query) -> đỡ rate limit, video sau tái dùng
CREATE TABLE IF NOT EXISTS search_cache (
    provider TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT NOT NULL,        -- JSON
    cached_at TEXT NOT NULL,
    PRIMARY KEY (provider, query)
);

-- M3b (C đợt 3b): vision tag cho footage STOCK/ENTITY đã pick — "editor xem footage
-- LÀ GÌ" cho phần ngoài kho. Key theo asset_key (pexels id/entity hash ổn định) nên
-- LƯU VĨNH VIỄN, video sau tái dùng miễn phí. CHỈ ambient/subject-SFX đọc (KHÔNG cho
-- phễu/ranker — tránh 2-tầng-cùng-quản). Nền cho C5 đợt 5 + vòng học editor-learn.
CREATE TABLE IF NOT EXISTS stock_tags (
    asset_key TEXT PRIMARY KEY,    -- 'pexels:12345' | 'entity-cache:<dir>' ...
    media_type TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    scene_type TEXT NOT NULL DEFAULT '',
    shot_size TEXT NOT NULL DEFAULT '',
    mood TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',   -- JSON list keyword
    model TEXT NOT NULL DEFAULT '',
    tagged_at TEXT NOT NULL
);
"""


@dataclass
class AssetRecord:
    niche: str
    path: str
    category: str
    media_type: str
    mtime: float
    subject: str
    description: str
    shot_size: str
    mood: str
    has_people: bool
    tags: list[str]
    folder_path: str = ""
    scene_type: str = ""
    camera_angle: str = ""
    dominant_color: str = ""
    brightness: float = 0.0
    saturation: float = 0.0
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    source_video: str = ""
    scene_start: float = 0.0
    scene_index: int = 0
    has_voice: int = -1  # -1 chưa biết | 0/1 từ ống nạp
    source_class: str = "own"  # c8: own | viral
    source_duration: float = 0.0  # c8: tổng giây file nguồn
    source_channel: str = ""  # VD4 ghi công: kênh của video nguồn
    peak_value: float | None = None  # ytref §3e: value đỉnh 0-1 (None = không cờ)
    peak_type: str | None = None     # ytref §3e: primary | secondary


def connect(db_path: Path | None = None, db_url: str | None = None):
    """Mở SỔ. Không tham số -> resolver G2: db_url đặt (env AUTOEDIT_DB_URL /
    machine.json) -> Postgres; rỗng -> SQLite <data_root>/cache.db (G1 y nguyên).

    db_path tường minh -> LUÔN SQLite tại path đó, KHÔNG nhìn resolver — 531 test
    cũ + script di trú giữ nguyên lưng SQLite kể cả trên máy đã flip Postgres.
    db_url tường minh -> LUÔN Postgres (test parity, kiểm kết nối)."""
    if db_url:
        return _connect_pg(db_url)
    if db_path is None:
        url = resolve_db_url()
        if url:
            return _connect_pg(url)
        db_path = DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # timeout 30s: G1 sổ có thể nằm trên ổ mạng dùng chung — máy khác đang ghi thì
    # CHỜ khóa thay vì nổ ngay "database is locked" (mặc định sqlite chỉ chờ 5s)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    # SQLite lower() chỉ hạ chữ ASCII -> "TƯ TRỊ" không khớp query "tư trị".
    # Đè bằng str.lower() của Python (Unicode) để search tiếng Việt hoạt động.
    conn.create_function("lower", 1, lambda s: s.lower() if isinstance(s, str) else s)
    conn.executescript(_SCHEMA)
    _migrate(conn)
    return conn


# ============================ G2 — lưng Postgres ==============================
# Lớp đệm 2 lưng: callsite giữ nguyên cú pháp sqlite3 (placeholder ?, row theo
# tên, conn.commit() tường minh) — shim dịch cho psycopg. SQL trong codebase chỉ
# được dùng cú pháp CẢ 2 lưng hiểu: INSERT..ON CONFLICT (không INSERT OR REPLACE),
# lower() 2 vế quanh LIKE, tie-break id tường minh sau ORDER BY hòa điểm.


class PgConnection:
    """Bọc psycopg Connection cho giống sqlite3.Connection ở đúng phần codebase
    dùng: execute/executemany/executescript/commit/close + row truy cập theo tên
    (dict_row). autocommit=True: sqlite3 commit theo conn.commit() tường minh —
    PG commit từng lệnh nên commit() thành no-op, ghi-rồi-đọc-lại vẫn đúng và
    lỗi 1 lệnh không làm "độc" transaction treo các lệnh sau."""

    backend = "postgres"

    def __init__(self, url: str) -> None:
        import psycopg
        from psycopg.rows import dict_row

        self._conn = psycopg.connect(url, autocommit=True, row_factory=dict_row,
                                     connect_timeout=10)

    def execute(self, sql: str, params=()):
        return self._conn.execute(_to_pg(sql), params)

    def executemany(self, sql: str, seq) -> None:
        with self._conn.cursor() as cur:
            cur.executemany(_to_pg(sql), seq)

    def executescript(self, script: str) -> None:
        self._conn.execute(script)  # psycopg chạy được nhiều lệnh cách ';' 1 lần

    def commit(self) -> None:  # giữ chỗ cho callsite conn.commit() — autocommit rồi
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        self._conn.close()


def _to_pg(sql: str) -> str:
    """Placeholder sqlite '?' -> psycopg '%s'. Mọi giá trị trong codebase đi qua
    params — SQL không có '?' hay '%' literal trong chuỗi nên thay thẳng an toàn."""
    return sql.replace("?", "%s")


def _pg_schema() -> str:
    """_SCHEMA (nguồn duy nhất, không nuôi 2 bản) dịch sang phương ngữ Postgres:
    id tự tăng (INTEGER PRIMARY KEY của SQLite = rowid tự tăng, PG thì không) +
    REAL -> DOUBLE PRECISION (REAL của PG là float 4 byte ~7 chữ số — mtime epoch
    ~1.7e9 mất sạch phần lẻ, needs_index so 1e-6 sẽ bắt tag lại oan CẢ KHO)."""
    s = _SCHEMA.replace("INTEGER PRIMARY KEY",
                        "BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY")
    return re.sub(r"\bREAL\b", "DOUBLE PRECISION", s)


def _connect_pg(url: str) -> PgConnection:
    conn = PgConnection(url)
    conn.executescript(_pg_schema())
    _migrate(conn)
    return conn


def backup_cache_db(db_path: Path | None = None, keep: int = 10) -> Path | None:
    """Chụp bản sao cache.db vào <data_root>/backup/ TRƯỚC mẻ ghi lớn (nạp/tag).

    Lá chắn G1: sổ dùng chung trên ổ mạng — SQLite qua SMB có rủi ro hỏng file khi
    ghi đụng nhau; hỏng thì khôi phục bản backup, mất nhiều nhất mẻ đang dở.
    Trả path bản backup (None nếu db chưa tồn tại). Giữ `keep` bản mới nhất.
    """
    src = db_path or DEFAULT_DB_PATH
    if not src.is_file():
        return None
    bdir = src.parent / "backup"
    bdir.mkdir(parents=True, exist_ok=True)
    dst = bdir / f"cache-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    shutil.copy2(src, dst)
    for old in sorted(bdir.glob("cache-*.db"))[:-keep]:
        old.unlink()
    return dst


def _migrate(conn) -> None:
    """Thêm cột mới cho db cũ — ALTER an toàn, idempotent. Chạy CẢ 2 lưng
    (liệt kê cột: PRAGMA là phương ngữ SQLite, PG dùng information_schema)."""
    new_cols = {
        "folder_path": "TEXT NOT NULL DEFAULT ''",
        "scene_type": "TEXT NOT NULL DEFAULT ''",
        "camera_angle": "TEXT NOT NULL DEFAULT ''",
        "dominant_color": "TEXT NOT NULL DEFAULT ''",
        "brightness": "REAL NOT NULL DEFAULT 0",
        "saturation": "REAL NOT NULL DEFAULT 0",
        "duration": "REAL NOT NULL DEFAULT 0",
        "width": "INTEGER NOT NULL DEFAULT 0",
        "height": "INTEGER NOT NULL DEFAULT 0",
        "fps": "REAL NOT NULL DEFAULT 0",
        "source_video": "TEXT NOT NULL DEFAULT ''",
        "scene_start": "REAL NOT NULL DEFAULT 0",
        "scene_index": "INTEGER NOT NULL DEFAULT 0",
        "has_voice": "INTEGER NOT NULL DEFAULT -1",
        "source_class": "TEXT NOT NULL DEFAULT 'own'",
        "source_duration": "REAL NOT NULL DEFAULT 0",
        "source_channel": "TEXT NOT NULL DEFAULT ''",

        "peak_value": "REAL",   # ytref §3e: asset cũ NULL = không cờ, KHÔNG re-tag
        "peak_type": "TEXT",
    }
    is_pg = getattr(conn, "backend", "") == "postgres"
    if is_pg:
        cols = {r["column_name"] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns"
            " WHERE table_name = 'library_assets'")}
    else:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(library_assets)")}
    changed = False
    for name, ddl in new_cols.items():
        if name not in cols:
            if is_pg:
                ddl = re.sub(r"\bREAL\b", "DOUBLE PRECISION", ddl)  # như _pg_schema
            conn.execute(f"ALTER TABLE library_assets ADD COLUMN {name} {ddl}")
            changed = True
    if changed:
        conn.commit()


def upsert_asset(conn: sqlite3.Connection, rec: AssetRecord) -> None:
    # Cột truy vết ống nạp (source_video/scene_start/scene_index/has_voice): re-index
    # THƯỜNG (không qua ống nạp) mang giá trị default -> CASE giữ giá trị cũ, không
    # âm thầm xóa provenance (P5 — index_niche và ingest_draft cùng ghi 1 dòng).
    conn.execute(
        """INSERT INTO library_assets
           (niche, path, category, folder_path, media_type, mtime, subject, description,
            shot_size, mood, scene_type, camera_angle, dominant_color, brightness,
            saturation, has_people, tags, duration, width, height, fps,
            source_video, scene_start, scene_index, has_voice,
            source_class, source_duration, source_channel, peak_value, peak_type, indexed_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(path) DO UPDATE SET
             category=excluded.category, folder_path=excluded.folder_path,
             mtime=excluded.mtime, subject=excluded.subject,
             description=excluded.description, shot_size=excluded.shot_size,
             mood=excluded.mood, scene_type=excluded.scene_type,
             camera_angle=excluded.camera_angle, dominant_color=excluded.dominant_color,
             brightness=excluded.brightness, saturation=excluded.saturation,
             has_people=excluded.has_people,
             tags=excluded.tags,
             duration=excluded.duration, width=excluded.width,
             height=excluded.height, fps=excluded.fps,
             source_video=CASE WHEN excluded.source_video=''
               THEN library_assets.source_video ELSE excluded.source_video END,
             scene_start=CASE WHEN excluded.source_video=''
               THEN library_assets.scene_start ELSE excluded.scene_start END,
             scene_index=CASE WHEN excluded.source_video=''
               THEN library_assets.scene_index ELSE excluded.scene_index END,
             has_voice=CASE WHEN excluded.has_voice=-1
               THEN library_assets.has_voice ELSE excluded.has_voice END,
             source_class=CASE WHEN excluded.source_video=''
               THEN library_assets.source_class ELSE excluded.source_class END,
             source_duration=CASE WHEN excluded.source_video=''
               THEN library_assets.source_duration ELSE excluded.source_duration END,
             source_channel=CASE WHEN excluded.source_channel=''
               THEN library_assets.source_channel ELSE excluded.source_channel END,
             peak_value=CASE WHEN excluded.source_video=''
               THEN library_assets.peak_value ELSE excluded.peak_value END,
             peak_type=CASE WHEN excluded.source_video=''
               THEN library_assets.peak_type ELSE excluded.peak_type END,
             indexed_at=excluded.indexed_at""",
        (
            rec.niche, rec.path, rec.category, rec.folder_path, rec.media_type, rec.mtime,
            rec.subject, rec.description, rec.shot_size, rec.mood,
            rec.scene_type, rec.camera_angle, rec.dominant_color, rec.brightness,
            rec.saturation, int(rec.has_people), json.dumps(rec.tags, ensure_ascii=False),
            rec.duration, rec.width, rec.height, rec.fps,
            rec.source_video, rec.scene_start, rec.scene_index, rec.has_voice,
            rec.source_class, rec.source_duration, rec.source_channel,
            rec.peak_value, rec.peak_type,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


def needs_index(conn: sqlite3.Connection, path: str, mtime: float) -> bool:
    """File mới hoặc đã đổi (mtime khác) thì cần tag lại — tiết kiệm vision call.

    Thêm luật spec TAG_GLM §5.1: dòng cũ THIẾU field bắt buộc mới (scene_type rỗng)
    cũng tag lại — asset tag trước Phase B tự nâng cấp schema.
    """
    row = conn.execute(
        "SELECT mtime, scene_type FROM library_assets WHERE path = ?", (path,)
    ).fetchone()
    return row is None or abs(row["mtime"] - mtime) > 1e-6 or not row["scene_type"]


# c8 gói CHỌN (2026-07-09): viral ĐÃ vào phễu thoại — gate pháp lý (liền kề + trần 8%)
# nằm ở sourcer/viral.py::ViralLedger, KHÔNG chặn ở db nữa. Ngoại lệ DUY NHẤT:
# videos_for_niche (pool shot thở) GIỮ chặn — 1209 clip viral nạp mới sẽ chiếm trọn
# pool 500 sort mới-nhất-trước, lật hành vi shot thở 2.0 đã duyệt (MO_TA C8_CHON §2.4).
_NO_VIRAL = " AND source_class != 'viral'"


def search_assets(conn: sqlite3.Connection, niche: str, query: str, limit: int = 20,
                  exclude_paths: set[str] | None = None,
                  own_only: bool = False, no_people: bool = False) -> list[dict]:
    """Tìm asset theo từ khóa — match LIKE trên subject/description/tags/category.

    Mọi từ trong query đều phải xuất hiện (AND) ở một trong các trường.

    exclude_paths (P7 asset đã dùng trong video): lọc TRƯỚC khi cắt limit — thứ tự
    ORDER BY cố định nên nếu lọc SAU, top-limit bị các beat trước dùng hết là query
    trắng tay dù kho còn cả nghìn asset (bug DS3-084: 26 beat needs_human oan).
    own_only/no_people (SÀN NICHE): cùng lý do — lọc PHẢI trước limit. Kho deepsea
    top-100 'shark' theo indexed_at DESC = 100% viral (mẻ viral nạp sau cùng), lọc
    sau cap là sàn trắng tay oan y hệt.
    """
    terms = [t.strip().lower() for t in query.split() if t.strip()]
    if not terms:
        return []
    sql = "SELECT * FROM library_assets WHERE niche = ?"
    params: list = [niche]
    if own_only:
        sql += _NO_VIRAL
    if no_people:
        sql += " AND COALESCE(has_people, 0) = 0"  # NULL = không rõ -> fail-open cho qua
    for t in terms:
        sql += (" AND (lower(subject) LIKE ? OR lower(description) LIKE ? OR lower(tags) LIKE ?"
                " OR lower(category) LIKE ? OR lower(folder_path) LIKE ?)")
        like = f"%{t}%"
        params += [like, like, like, like, like]
    # id DESC = tie-break tường minh (G2): hòa (approved, indexed_at) mỗi lưng tự
    # xếp một kiểu -> pick đổi sau flip Postgres; id giữ nghĩa mới-nạp-đứng-trước.
    sql += " ORDER BY approved DESC, indexed_at DESC, id DESC"
    if not exclude_paths:
        sql += " LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    else:  # duyệt cursor tới khi đủ limit dòng CHƯA dùng (không LIMIT trong SQL)
        rows = []
        for r in conn.execute(sql, params):
            if r["path"] in exclude_paths:
                continue
            rows.append(r)
            if len(rows) >= limit:
                break
    return [dict(r) | {"tags": json.loads(r["tags"])} for r in rows]


_VOCAB_STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "of", "with", "and", "or", "to", "from",
    "for", "by", "over", "under", "into", "out", "up", "down", "is", "are",
}


def vocab_for_niche(conn: sqlite3.Connection, niche: str, top_n: int = 30) -> dict:
    """Từ vựng THẬT của kho (C4 controlled vocabulary) — máy thuần, 0 token.

    Trả {"total", "videos", "images", "scene_types", "tags", "subject_words"} —
    3 list cuối là [(từ, đếm)] giảm dần, nguyên liệu cho khối TỪ VỰNG KHO trong
    direct_context.md (NÃO viết queries.local trúng từ kho thật sự nói).
    """
    from collections import Counter

    rows = conn.execute(
        "SELECT subject, tags, scene_type, media_type FROM library_assets WHERE niche = ?",
        (niche,),
    ).fetchall()
    scene: Counter = Counter()
    tag_c: Counter = Counter()
    subj_c: Counter = Counter()
    videos = 0
    for r in rows:
        if r["media_type"] == "video":
            videos += 1
        if r["scene_type"]:
            scene[r["scene_type"]] += 1
        for t in json.loads(r["tags"] or "[]"):
            t = str(t).strip().lower()
            if t:
                tag_c[t] += 1
        for w in str(r["subject"]).lower().split():
            w = w.strip(".,;:!?'\"()")
            if len(w) >= 3 and w not in _VOCAB_STOPWORDS:
                subj_c[w] += 1
    return {
        "total": len(rows),
        "videos": videos,
        "images": len(rows) - videos,
        "scene_types": scene.most_common(),
        "tags": tag_c.most_common(top_n),
        "subject_words": subj_c.most_common(top_n),
    }


def videos_for_niche(conn: sqlite3.Connection, niche: str, limit: int = 50_000) -> list[dict]:
    """Pool VIDEO của niche cho shot thở (MO_TA_SHOT_THO §2c) — chọn máy theo tag,
    không theo query. Thứ tự ổn định approved/indexed_at làm tie-break khi hòa điểm.

    3.0 (2026-07-13): lấy TRỌN kho (limit chỉ là phanh an toàn) — trần 500 cũ chỉ thấy
    500 clip mới-index-nhất, chủ thể nạp sớm không bao giờ vào pool (deepsea 7.940 clip
    own -> đói 94%), luật liên-tục-chủ-thể không có nguyên liệu."""
    rows = conn.execute(
        "SELECT * FROM library_assets WHERE niche = ? AND media_type = 'video'"
        + _NO_VIRAL + " ORDER BY approved DESC, indexed_at DESC, id DESC LIMIT ?",
        (niche, limit),
    ).fetchall()
    return [dict(r) | {"tags": json.loads(r["tags"])} for r in rows]


def signature_assets(conn: sqlite3.Connection, niche: str, limit: int = 5,
                     exclude_paths: set[str] | None = None) -> list[dict]:
    """Asset thư mục signature/ của niche (c6 — chữ ký, gom TRƯỚC cho beat hook/chêm).
    exclude_paths: cùng lý do search_assets — lọc đã-dùng TRƯỚC khi cắt limit."""
    sql = ("SELECT * FROM library_assets WHERE niche = ? AND category = 'signature' "
           "ORDER BY approved DESC, indexed_at DESC, id DESC")
    if not exclude_paths:
        rows = conn.execute(sql + " LIMIT ?", (niche, limit)).fetchall()
    else:
        rows = []
        for r in conn.execute(sql, (niche,)):
            if r["path"] in exclude_paths:
                continue
            rows.append(r)
            if len(rows) >= limit:
                break
    return [dict(r) | {"tags": json.loads(r["tags"])} for r in rows]


def paths_for_niche(conn: sqlite3.Connection, niche: str) -> dict[str, dict]:
    """Mọi asset của niche: path -> {mtime, ...} (phục vụ phát hiện file đã di chuyển)."""
    rows = conn.execute(
        "SELECT path, mtime FROM library_assets WHERE niche = ?", (niche,)
    ).fetchall()
    return {r["path"]: dict(r) for r in rows}


def move_asset(
    conn: sqlite3.Connection, old_path: str, new_path: str, category: str, folder_path: str = ""
) -> None:
    """File đổi chỗ: cập nhật path + category + folder_path, GIỮ tag vision (không tốn tiền tag lại)."""
    conn.execute(
        "UPDATE library_assets SET path = ?, category = ?, folder_path = ? WHERE path = ?",
        (new_path, category, folder_path, old_path),
    )
    conn.commit()


def delete_assets(conn: sqlite3.Connection, paths: list[str]) -> int:
    """Dọn dòng trỏ tới file không còn tồn tại."""
    if not paths:
        return 0
    conn.executemany("DELETE FROM library_assets WHERE path = ?", [(p,) for p in paths])
    conn.commit()
    return len(paths)


def count_assets(conn: sqlite3.Connection, niche: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) AS n FROM library_assets WHERE niche = ?", (niche,)
    ).fetchone()["n"]


# ---------------- VD4 ghi công: kênh nguồn footage (MO_TA_GHI_CONG_KENH) -----------
def source_video_folders(conn: sqlite3.Connection, niche: str | None = None) -> list[dict]:
    """Gom asset theo FOLDER nguồn (thư mục cha của source_video) — nguyên liệu cho
    `channel-audit`: user nhìn là biết folder nào chưa điền kênh. Trả list dict
    {folder, niche, assets, channels} sort theo niche rồi folder."""
    sql = ("SELECT niche, source_video, source_channel, COUNT(*) AS n FROM library_assets"
           " WHERE source_video != ''")
    params: list = []
    if niche:
        sql += " AND niche = ?"
        params.append(niche)
    sql += " GROUP BY niche, source_video, source_channel"
    groups: dict[tuple[str, str], dict] = {}
    for r in conn.execute(sql, params):
        folder = str(Path(r["source_video"]).parent)
        g = groups.setdefault((r["niche"], folder), {
            "folder": folder, "niche": r["niche"], "assets": 0, "channels": set()})
        g["assets"] += r["n"]
        g["channels"].add(r["source_channel"] or "")
    out = [g | {"channels": sorted(g["channels"])} for g in groups.values()]
    return sorted(out, key=lambda g: (g["niche"], g["folder"].lower()))


def set_source_channel(conn: sqlite3.Connection, prefix: str, channel: str,
                       niche: str | None = None, dry_run: bool = False) -> int:
    """Backfill: gán kênh cho MỌI asset có source_video bắt đầu bằng `prefix`
    (không phân hoa-thường). So prefix ở PYTHON trên danh sách DISTINCT source_video
    rồi UPDATE theo GIÁ TRỊ CHÍNH XÁC — cố ý NÉ LIKE: trên Postgres dấu `\\` trong
    pattern LIKE là ký tự escape, prefix Windows sẽ match hụt (bug anh em REF, sửa
    2026-07-17). Trả số asset trúng; dry_run=True chỉ đếm, không ghi."""
    pfx = str(prefix).lower()
    if not pfx.strip():
        return 0
    sql = "SELECT DISTINCT source_video FROM library_assets WHERE source_video != ''"
    params: list = []
    if niche:
        sql += " AND niche = ?"
        params.append(niche)
    hits = [r["source_video"] for r in conn.execute(sql, params)
            if str(r["source_video"]).lower().startswith(pfx)]
    if not hits:
        return 0
    n = 0
    count_sql = "SELECT COUNT(*) AS n FROM library_assets WHERE source_video = ?"
    upd_sql = "UPDATE library_assets SET source_channel = ? WHERE source_video = ?"
    if niche:
        count_sql += " AND niche = ?"
        upd_sql += " AND niche = ?"
    for src in hits:
        p_count = (src, niche) if niche else (src,)
        n += conn.execute(count_sql, p_count).fetchone()["n"]
        if not dry_run:
            conn.execute(upd_sql, (channel, src, niche) if niche else (channel, src))
    if not dry_run:
        conn.commit()
    return n
