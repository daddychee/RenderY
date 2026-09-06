r"""Cơ sở dữ liệu Sổ Tra — SQLite + FTS5 tại <data_root>/so_tra/so_tra.db.

4 bảng (thiết kế chốt 06/09):
  clip      — mỗi dòng một KHÚC footage, mọi nguồn chung khuôn; từ khóa 7 trục
  su_kien   — sổ cái append-only: đề_xuất/được_chọn/người_thay/lên_final/...
  phien_hut — log lượt hút (đã phủ từ khóa nào, khỏi hút lại)
  alias     — đồng nghĩa → từ chuẩn (usd→dollar bills, chợ→market): team gõ
              tiếng Việt vẫn tra ra

FTS5 (bảng clip_fts) đánh chỉ mục tieu_de + 7 trục gộp — một ô tìm phủ tất cả.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from autoedit.packager.machine import resolve_data_root

NGUON_HOP_LE = ("envato", "pexels", "pixabay", "ref", "kho", "aigen")
# 7 trục từ khóa (chốt 06/09) — cột nào cũng text thường, cách nhau dấu phẩy
TRUC = ("subject", "action", "setting", "geo", "people", "shot", "mood")


def goc_so_tra() -> Path:
    return resolve_data_root() / "so_tra"


def duong_db() -> Path:
    return goc_so_tra() / "so_tra.db"


_SCHEMA = """
CREATE TABLE IF NOT EXISTS clip(
  id TEXT PRIMARY KEY,             -- nguon:ma[:khuc] — bất biến, cho MÁY
  nguon TEXT NOT NULL,             -- envato|pexels|pixabay|ref|kho
  tieu_de TEXT DEFAULT '',
  url_trang TEXT DEFAULT '',       -- trang gốc (mở để tải bản sạch)
  url_anh TEXT DEFAULT '',         -- thumbnail (hotlink được trong app)
  url_video TEXT DEFAULT '',       -- video preview 540p (hover-play)
  path_local TEXT DEFAULT '',      -- ref/kho: file trên đĩa (KHÔNG copy)
  t0 REAL DEFAULT 0, t1 REAL DEFAULT 0,   -- khúc trong video dài (ref)
  dai_s REAL DEFAULT 0,
  subject TEXT DEFAULT '', action TEXT DEFAULT '', setting TEXT DEFAULT '',
  geo TEXT DEFAULT '',             -- 3 cấp "ecuador>andes>otavalo"
  people TEXT DEFAULT '', shot TEXT DEFAULT '', mood TEXT DEFAULT '',
  tag_nguon TEXT DEFAULT 'tieu_de',    -- tieu_de|vision|nguoi (tầng đắt dần)
  frame_dau TEXT DEFAULT '', frame_cuoi TEXT DEFAULT '',   -- JPEG local (lazy)
  tu_khoa_hut TEXT DEFAULT '',
  tap TEXT DEFAULT '',             -- ref/kho: tập gốc
  trang_thai TEXT DEFAULT 'song',  -- song|link_chet|loai_tru
  ngay_them TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_clip_nguon ON clip(nguon);

CREATE VIRTUAL TABLE IF NOT EXISTS clip_fts USING fts5(
  id UNINDEXED, chu, tokenize='unicode61');
CREATE TABLE IF NOT EXISTS su_kien(
  sk INTEGER PRIMARY KEY AUTOINCREMENT,
  clip_id TEXT NOT NULL, tap TEXT DEFAULT '', vi_tri REAL DEFAULT 0,
  loai TEXT NOT NULL,              -- de_xuat|duoc_chon|nguoi_thay|nguoi_bo|
                                   -- len_final|editor_swap|retention_diem
  chi_tiet TEXT DEFAULT '', ts TEXT DEFAULT '');
CREATE INDEX IF NOT EXISTS idx_sk_clip ON su_kien(clip_id);
CREATE INDEX IF NOT EXISTS idx_sk_tap ON su_kien(tap);
CREATE TABLE IF NOT EXISTS phien_hut(
  ph INTEGER PRIMARY KEY AUTOINCREMENT,
  tu_khoa TEXT, nguon TEXT, so_moi INTEGER, so_trung INTEGER, ts TEXT);
CREATE TABLE IF NOT EXISTS alias(tu TEXT PRIMARY KEY, chuan TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS nhac(
  id TEXT PRIMARY KEY,             -- epidemic:<id> — bất biến, cho MÁY
  nguon TEXT NOT NULL DEFAULT 'epidemic',
  tieu_de TEXT DEFAULT '', nghe_si TEXT DEFAULT '',
  mood TEXT DEFAULT '',            -- đã quy về vocab NỘI BỘ (tense/calm/...)
  mood_goc TEXT DEFAULT '',        -- mood Epidemic nguyên bản, không mất tin
  genre TEXT DEFAULT '',
  bpm INTEGER DEFAULT 0,
  energy TEXT DEFAULT '',          -- low|medium|high
  dai_s REAL DEFAULT 0,
  co_loi INTEGER DEFAULT 0,        -- hasVocals: chặn mặc định (đè voice đọc)
  url_nghe TEXT DEFAULT '',        -- lqMp3Url 128kbps — TRỌN bài, công khai
  url_anh TEXT DEFAULT '', url_trang TEXT DEFAULT '',
  path_local TEXT DEFAULT '',      -- bản sạch sau khi tải qua két
  trang_thai TEXT DEFAULT 'preview',   -- preview|da_tai|loai_tru
  ngay_them TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS giay_phep(
  gp INTEGER PRIMARY KEY AUTOINCREMENT,
  clip_id TEXT NOT NULL,           -- envato:<uuid>
  url_item TEXT DEFAULT '',        -- trang item lúc tải (bằng chứng đối soát)
  ten_file TEXT DEFAULT '',        -- tên file Envato đặt (khớp My Downloads)
  bytes INTEGER DEFAULT 0,
  ngay TEXT DEFAULT '');
CREATE VIRTUAL TABLE IF NOT EXISTS nhac_fts USING fts5(
  id UNINDEXED, chu, tokenize='porter unicode61');
"""

# Bộ alias GỐC (Việt→Anh + đồng nghĩa hay gặp) — người bổ sung dần qua UI.
_ALIAS_GOC = {
    "chợ": "market", "cho": "market", "tủ lạnh": "refrigerator",
    "tu lanh": "refrigerator", "fridge": "refrigerator",
    "tiền": "dollar bills", "tien": "dollar bills", "usd": "dollar bills",
    "cash": "dollar bills", "money": "dollar bills",
    "núi": "mountain", "nui": "mountain", "núi tuyết": "snow mountain",
    "đường phố": "street", "duong pho": "street", "phố": "street",
    "rừng": "jungle", "rung": "jungle", "gia đình": "family",
    "gia dinh": "family", "bữa ăn": "meal", "bua an": "meal",
    "người bán": "vendor", "nguoi ban": "vendor", "xe buýt": "bus",
    "xe buyt": "bus", "quốc kỳ": "flag", "quoc ky": "flag",
    "thác": "waterfall", "thac": "waterfall", "biển": "coast", "bien": "coast",
}


def mo(path: Path | None = None) -> sqlite3.Connection:
    """Mở (tạo nếu chưa có) db — trả connection dùng chung, row_factory dict."""
    f = Path(path) if path else duong_db()
    f.parent.mkdir(parents=True, exist_ok=True)
    (f.parent / "frames").mkdir(exist_ok=True)
    (f.parent / "prev_cache").mkdir(exist_ok=True)
    (f.parent / "prev_giu").mkdir(exist_ok=True)
    conn = sqlite3.connect(str(f), timeout=15.0)
    # WAL (08/09, chuẩn bị 5 editor đồng thời): nhiều reader + 1 writer không
    # chặn nhau; journal 'delete' cũ khiến lượt hút nền khóa cả trang Library.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    # migration nhẹ: cột thêm sau đợt 1 (ALTER bỏ qua nếu đã có)
    try:
        conn.execute("ALTER TABLE clip ADD COLUMN tieu_de_goc TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    # ref cắt theo cảnh (06/09): vật thể nhìn thấy trong hình + độ khớp lời-hình
    for _cot, _kieu in (("vat_the", "TEXT DEFAULT ''"), ("khop", "INTEGER DEFAULT 0"),
                        ("loi_quanh", "TEXT DEFAULT ''"), ("may_dong", "INTEGER DEFAULT 0")):
        try:
            conn.execute(f"ALTER TABLE clip ADD COLUMN {_cot} {_kieu}")
        except sqlite3.OperationalError:
            pass
    if conn.execute("SELECT COUNT(*) FROM alias").fetchone()[0] == 0:
        conn.executemany("INSERT OR IGNORE INTO alias(tu, chuan) VALUES(?,?)",
                         list(_ALIAS_GOC.items()))
    conn.commit()
    return conn


# ------------------------------------------------------------ đặt tên
def lam_id(nguon: str, ma: str, khuc: str = "") -> str:
    """id chính tắc `nguon:ma[:khuc]` — bất biến, không phụ thuộc tiêu đề."""
    if nguon not in NGUON_HOP_LE:
        raise ValueError(f"nguồn lạ: {nguon!r} (nhận {'/'.join(NGUON_HOP_LE)})")
    ma = str(ma).strip()
    if not ma:
        raise ValueError("mã gốc rỗng")
    return f"{nguon}:{ma}" + (f":{khuc}" if khuc else "")


def slug(chu: str, dai: int = 30) -> str:
    """Slug tên file CHO NGƯỜI đọc — máy không bao giờ parse ngược."""
    khong_dau = unicodedata.normalize("NFD", chu or "")
    khong_dau = "".join(c for c in khong_dau if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", khong_dau.lower()).strip("-")[:dai] or "clip"


def ten_frame(clip_id: str, tieu_de: str, vai: str) -> str:
    """`{nguon}_{ma8}[_{khuc}]_{slug}.dau|cuoi.jpg` — nằm trong so_tra/frames/.

    KHÚC bắt buộc có trong tên: ref cắt theo cảnh thì mọi cảnh cùng một video
    chung `phan[1]`. Bỏ khúc đi thì 228 cảnh ghi đè nhau còn MỘT file — gặp thật
    06/09: GLM đọc 228 lần cùng một tấm hình, cả kho ra 4 subject giống nhau.
    """
    phan = clip_id.split(":")
    ma8 = re.sub(r"[^a-z0-9]", "", phan[1].lower())[:8] or "x"
    khuc = re.sub(r"[^a-z0-9]", "-", phan[2].lower())[:16] if len(phan) > 2 else ""
    return f"{phan[0]}_{ma8}{'_' + khuc if khuc else ''}_{slug(tieu_de)}.{vai}.jpg"


# ------------------------------------------------------------ ghi
def _chu_fts(r: dict) -> str:
    # vat_the PHẢI có trong FTS: đó là lý do thêm trục này (tra "bananas" phải
    # ra được thùng Burberry giấu ma túy). Bỏ sót = trục thành vô dụng.
    return " ".join(str(r.get(k) or "")
                    for k in ("tieu_de", "vat_the") + TRUC).replace(">", " ")


def them_clip(conn: sqlite3.Connection, r: dict) -> bool:
    """Upsert 1 clip. Trả True nếu MỚI. Trường lạ bị bỏ qua (fail-soft)."""
    cot = ["id", "nguon", "tieu_de", "url_trang", "url_anh", "url_video",
           "path_local", "t0", "t1", "dai_s", *TRUC, "tag_nguon",
           "frame_dau", "frame_cuoi", "tu_khoa_hut", "tap", "trang_thai",
           "vat_the", "khop", "loi_quanh", "may_dong"]
    d = {k: r.get(k, "") for k in cot}
    d["trang_thai"] = r.get("trang_thai") or "song"   # "" đè default SQL là bẫy
    for _so in ("khop", "may_dong"):                  # cột INTEGER: "" là bẫy
        d[_so] = int(r.get(_so) or 0)
    d["ngay_them"] = datetime.now(timezone.utc).isoformat()
    moi = conn.execute("SELECT 1 FROM clip WHERE id=?", (d["id"],)).fetchone() is None
    if moi:
        conn.execute(
            f"INSERT INTO clip({','.join(d)}) VALUES({','.join('?' * len(d))})",
            list(d.values()))
    else:
        # đã có: chỉ nâng cấp tag khi tầng mới ĐẮT hơn (tieu_de < vision < nguoi)
        bac = {"tieu_de": 0, "vision": 1, "nguoi": 2}
        cu = conn.execute("SELECT tag_nguon FROM clip WHERE id=?", (d["id"],)).fetchone()
        if bac.get(str(r.get("tag_nguon", "tieu_de")), 0) >= bac.get(cu[0], 0):
            conn.execute(
                "UPDATE clip SET " + ",".join(f"{k}=?" for k in cot[2:]) + " WHERE id=?",
                [d[k] for k in cot[2:]] + [d["id"]])
    conn.execute("DELETE FROM clip_fts WHERE id=?", (d["id"],))
    conn.execute("INSERT INTO clip_fts(id, chu) VALUES(?,?)", (d["id"], _chu_fts(d)))
    return moi


def ghi_su_kien(conn, clip_id: str, loai: str, tap: str = "",
                vi_tri: float = 0.0, chi_tiet: str = "") -> None:
    conn.execute(
        "INSERT INTO su_kien(clip_id, tap, vi_tri, loai, chi_tiet, ts) VALUES(?,?,?,?,?,?)",
        (clip_id, tap, vi_tri, loai, chi_tiet, datetime.now(timezone.utc).isoformat()))


def ghi_phien_hut(conn, tu_khoa: str, nguon: str, so_moi: int, so_trung: int) -> None:
    conn.execute("INSERT INTO phien_hut(tu_khoa, nguon, so_moi, so_trung, ts) VALUES(?,?,?,?,?)",
                 (tu_khoa, nguon, so_moi, so_trung, datetime.now(timezone.utc).isoformat()))


# ------------------------------------------------------------ đọc
def ap_alias(conn, chu: str) -> str:
    """Thay đồng nghĩa/tiếng Việt bằng từ chuẩn trước khi tra FTS."""
    ra = (chu or "").strip().lower()
    for tu, chuan in conn.execute("SELECT tu, chuan FROM alias"):
        if tu in ra:
            ra = ra.replace(tu, chuan)
    return ra


def tim(conn, q: str = "", nguon: str = "", chi_neo: bool = False,
        tap: str = "", limit: int = 60, offset: int = 0,
        meta: dict | None = None) -> list[dict]:
    """Ô tìm của trang Sổ Tra — FTS + lọc. Không q -> mới nhất trước."""
    dk, tham = ["c.trang_thai != 'loai_tru'"], []
    if nguon:
        dk.append("c.nguon=?")
        tham.append(nguon)
    if chi_neo:
        dk.append("(c.geo != '' OR c.nguon IN ('ref','kho'))")
    if tap:
        dk.append("(c.tap=? OR c.id IN (SELECT clip_id FROM su_kien WHERE tap=?))")
        tham += [tap, tap]
    q = ap_alias(conn, q)
    if q.strip():
        tokens = re.findall(r"[\w]+", q)
        fts = " OR ".join(f'"{t}"' for t in tokens)
        sql = (f"SELECT c.*, bm25(clip_fts) AS hang FROM clip_fts f "
               f"JOIN clip c ON c.id=f.id WHERE clip_fts MATCH ? AND {' AND '.join(dk)} "
               f"ORDER BY hang LIMIT ? OFFSET ?")
        rows = conn.execute(sql, [fts, *tham, limit, offset]).fetchall()
    else:
        sql = (f"SELECT c.* FROM clip c WHERE {' AND '.join(dk)} "
               f"ORDER BY c.ngay_them DESC LIMIT ? OFFSET ?")
        rows = conn.execute(sql, [*tham, limit, offset]).fetchall()
    # bug user bắt 06/09: UI ẩn "Xem thêm" khi trang trả <60 CLIP, nhưng gộp
    # trùng hiển thị làm 60 DÒNG thô co còn 15-40 clip -> nút ẩn oan từ trang
    # đầu, kho 871 mà mắt thấy <100. meta['het'] nói sự thật theo DÒNG THÔ.
    if meta is not None:
        meta["het"] = len(rows) < limit
    ra, nhom = [], {}
    for r in rows:
        d = dict(r)
        d.pop("hang", None)
        khoa = (d["nguon"], (d["tieu_de"] or "").strip().lower())
        if khoa in nhom:                      # gộp trùng hiển thị — dữ liệu giữ nguyên
            nhom[khoa]["so_ban"] = nhom[khoa].get("so_ban", 1) + 1
            continue
        d["so_ban"] = 1
        nhom[khoa] = d
        ra.append(d)
    # nhãn "đã dùng ở tập" — chống lặp giữa các tập ngay lúc chọn
    if ra:
        dau = {r["id"]: r for r in ra}
        for cid, tap_d in conn.execute(
                f"SELECT clip_id, GROUP_CONCAT(DISTINCT tap) FROM su_kien "
                f"WHERE loai IN ('len_final','duoc_chon') AND clip_id IN "
                f"({','.join('?' * len(dau))}) GROUP BY clip_id", list(dau)):
            dau[cid]["da_dung"] = ",".join(t for t in (tap_d or "").split(",") if t)
    return ra


def dem_theo_nguon(conn) -> dict:
    return {r[0]: r[1] for r in conn.execute(
        "SELECT nguon, COUNT(*) FROM clip WHERE trang_thai != 'loai_tru' GROUP BY nguon")}


def lich_su(conn, clip_id: str, limit: int = 20) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT tap, vi_tri, loai, chi_tiet, ts FROM su_kien WHERE clip_id=? "
        "ORDER BY sk DESC LIMIT ?", (clip_id, limit))]
