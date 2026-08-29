"""G2-M2: di tru SO tu SQLite -> PostgreSQL (MO_TA_VAN_HANH_G2_DB_SERVER §4 M2).

Chay luc KHONG job. Sau khi chay, so that VAN LA SQLite — PG chi la ban sao (M3 moi flip).

    cd autoedit
    uv run python "..\\scripts\\migrate_g2.py" --pg-url "host=... dbname=autoedit user=autoedit password=..."

Cac buoc:
  1. PRE-FLIGHT: quet kieu du lieu tung cot + NUL byte trong text (PG tu choi \\x00) — co ban -> dung, chua ghi gi.
  2. COPY 4 bang GIU NGUYEN id (IDENTITY BY DEFAULT cho phep) + setval sequence ve max(id).
  3. VERIFY: dem 100% tung bang + so mau ngau nhien 500 dong/bang (seed 89, tung cot)
     + truy van chon loc that (count/videos_for_niche/signature/search) 2 lung so ket qua.

Exit 0 = MOI cong dat. Target phai TRONG (dung --wipe de xoa ban sao cu truoc khi copy lai).
--verify-only: chi chay buoc 3 (kiem lai cong ma khong copy).
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from collections import Counter
from pathlib import Path

from autoedit.library import db as dbmod

# (cot, kind) — kind: text / real / int, hau to '?' = nullable. Khop _SCHEMA db.py.
TABLES: dict[str, dict] = {
    "library_assets": {
        "cols": [
            ("id", "int"), ("niche", "text"), ("path", "text"), ("category", "text"),
            ("folder_path", "text"), ("media_type", "text"), ("mtime", "real"),
            ("subject", "text"), ("description", "text"), ("shot_size", "text"),
            ("mood", "text"), ("scene_type", "text"), ("camera_angle", "text"),
            ("dominant_color", "text"), ("brightness", "real"), ("saturation", "real"),
            ("has_people", "int"), ("tags", "text"), ("duration", "real"),
            ("width", "int"), ("height", "int"), ("fps", "real"),
            ("source_video", "text"), ("scene_start", "real"), ("scene_index", "int"),
            ("has_voice", "int"), ("source_class", "text"), ("source_duration", "real"),
            ("peak_value", "real?"), ("peak_type", "text?"),
            ("approved", "int"), ("indexed_at", "text"),
        ],
        "key": ["id"], "id_seq": True,
    },
    "asset_usage": {
        "cols": [("id", "int"), ("channel", "text"), ("asset_key", "text"),
                 ("video_id", "text"), ("used_at", "text")],
        "key": ["id"], "id_seq": True,
    },
    "search_cache": {
        "cols": [("provider", "text"), ("query", "text"),
                 ("response", "text"), ("cached_at", "text")],
        "key": ["provider", "query"], "id_seq": False,
    },
    "stock_tags": {
        "cols": [("asset_key", "text"), ("media_type", "text"), ("subject", "text"),
                 ("description", "text"), ("scene_type", "text"), ("shot_size", "text"),
                 ("mood", "text"), ("tags", "text"), ("model", "text"), ("tagged_at", "text")],
        "key": ["asset_key"], "id_seq": False,
    },
}
SAMPLE_N = 500
BATCH = 1000


def _kind_ok(v, kind: str) -> bool:
    if kind.endswith("?"):
        if v is None:
            return True
        kind = kind[:-1]
    if kind == "text":
        return isinstance(v, str) and "\x00" not in v
    if kind == "real":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, int) and not isinstance(v, bool)  # int


def preflight(src) -> list[str]:
    """Quet TOAN BO dong nguon, tra danh sach loi (rong = sach)."""
    errs: list[str] = []
    for table, spec in TABLES.items():
        names = [c for c, _ in spec["cols"]]
        for i, row in enumerate(src.execute(f"SELECT {', '.join(names)} FROM {table}")):
            for (col, kind) in spec["cols"]:
                if not _kind_ok(row[col], kind):
                    errs.append(f"{table} dong#{i} cot {col}: kieu la {type(row[col]).__name__}")
                    if len(errs) >= 20:
                        return errs
    return errs


def copy_tables(src, dst) -> None:
    for table, spec in TABLES.items():
        names = [c for c, _ in spec["cols"]]
        ins = (f"INSERT INTO {table} ({', '.join(names)}) "
               f"VALUES ({', '.join('?' * len(names))})")
        batch: list[tuple] = []
        n = 0
        for row in src.execute(f"SELECT {', '.join(names)} FROM {table}"):
            batch.append(tuple(row[c] for c in names))
            if len(batch) >= BATCH:
                dst.executemany(ins, batch)
                n += len(batch)
                batch = []
        if batch:
            dst.executemany(ins, batch)
            n += len(batch)
        print(f"  copy {table}: {n} dong")
        if spec["id_seq"]:
            mx = src.execute(f"SELECT MAX(id) AS m FROM {table}").fetchone()["m"]
            if mx is not None:
                dst.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), ?)", (mx,))
                print(f"  setval {table}.id -> {mx}")


def _fetch_one(conn, table: str, names: list[str], key: list[str], kv: tuple):
    where = " AND ".join(f"{k} = ?" for k in key)
    return conn.execute(f"SELECT {', '.join(names)} FROM {table} WHERE {where}", kv).fetchone()


def verify(src, dst) -> bool:
    ok = True
    # 1. Dem 100% tung bang
    for table in TABLES:
        a = src.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        b = dst.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        mark = "PASS" if a == b else "FAIL"
        ok &= a == b
        print(f"  [dem] {table}: sqlite={a} pg={b} -> {mark}")
    # 2. So mau ngau nhien 500 dong/bang, tung cot
    rng = random.Random(89)
    for table, spec in TABLES.items():
        names = [c for c, _ in spec["cols"]]
        key = spec["key"]
        keys = [tuple(r[k] for k in key)
                for r in src.execute(f"SELECT {', '.join(key)} FROM {table}")]
        sample = rng.sample(keys, min(SAMPLE_N, len(keys)))
        bad = 0
        for kv in sample:
            ra = _fetch_one(src, table, names, key, kv)
            rb = _fetch_one(dst, table, names, key, kv)
            if rb is None:
                bad += 1
                print(f"    LECH {table} {kv}: THIEU ben pg")
                continue
            for c in names:
                if ra[c] != rb[c]:
                    bad += 1
                    print(f"    LECH {table} {kv} cot {c}: sqlite={ra[c]!r} pg={rb[c]!r}")
                    break
        mark = "PASS" if bad == 0 else "FAIL"
        ok &= bad == 0
        print(f"  [mau] {table}: {len(sample)} dong so tung cot, lech {bad} -> {mark}")
    # 3. Truy van chon loc that 2 lung (thu tu da co tie-break id DESC tu M1)
    niches = [r["niche"] for r in src.execute(
        "SELECT DISTINCT niche FROM library_assets ORDER BY niche")]
    for niche in niches:
        checks = {
            "count_assets": (dbmod.count_assets(src, niche), dbmod.count_assets(dst, niche)),
            "videos_for_niche": ([r["path"] for r in dbmod.videos_for_niche(src, niche)],
                                 [r["path"] for r in dbmod.videos_for_niche(dst, niche)]),
            "signature_assets": ([r["path"] for r in dbmod.signature_assets(src, niche)],
                                 [r["path"] for r in dbmod.signature_assets(dst, niche)]),
        }
        # search_assets voi 2 tag pho bien nhat cua niche (tu du lieu that)
        words: Counter = Counter()
        for r in src.execute(
                "SELECT subject FROM library_assets WHERE niche = ? LIMIT 300", (niche,)):
            for w in str(r["subject"]).lower().split():
                if len(w) >= 4:
                    words[w] += 1
        for w, _ in words.most_common(2):
            checks[f"search '{w}'"] = (
                [r["path"] for r in dbmod.search_assets(src, niche, w)],
                [r["path"] for r in dbmod.search_assets(dst, niche, w)])
        for name, (a, b) in checks.items():
            mark = "PASS" if a == b else "FAIL"
            ok &= a == b
            size = len(a) if isinstance(a, list) else a
            print(f"  [query] {niche} / {name} ({size}): {mark}")
            if a != b and isinstance(a, list):
                for i, (x, y) in enumerate(zip(a, b)):
                    if x != y:
                        print(f"    lech dau tien tai #{i}: sqlite={x!r} pg={y!r}")
                        break
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pg-url", required=True, help="DSN keyword psycopg toi db autoedit")
    ap.add_argument("--sqlite", default=r"F:\AutoEdit\cache.db")
    ap.add_argument("--wipe", action="store_true", help="TRUNCATE ban sao PG cu truoc khi copy")
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()

    src = dbmod.connect(db_path=Path(args.sqlite))  # path tuong minh = LUON SQLite
    dst = dbmod.connect(db_url=args.pg_url)
    t0 = time.time()
    try:
        if not args.verify_only:
            print("== PRE-FLIGHT: quet kieu du lieu + NUL byte ==")
            errs = preflight(src)
            if errs:
                print("\n".join("  " + e for e in errs))
                print("FAIL pre-flight — chua ghi gi vao PG.")
                return 1
            print("  sach.")
            counts = {t: dst.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"]
                      for t in TABLES}
            if any(counts.values()):
                if not args.wipe:
                    print(f"FAIL: PG khong trong {counts} — dung --wipe de copy lai tu dau.")
                    return 1
                dst.execute("TRUNCATE " + ", ".join(TABLES) + " RESTART IDENTITY")
                print(f"  da wipe ban sao cu {counts}")
            print("== COPY ==")
            copy_tables(src, dst)
        print("== VERIFY ==")
        ok = verify(src, dst)
        print(f"== {'DAT' if ok else 'FAIL'} — {time.time() - t0:.1f}s ==")
        return 0 if ok else 2
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    sys.exit(main())
