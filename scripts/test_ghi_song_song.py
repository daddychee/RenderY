"""Test ghi SONG SONG 2 máy vào PostgreSQL — cổng số G2-M4.

Chạy ĐỒNG THỜI trên 2 máy (thứ tự bắt đầu không quan trọng, script tự chờ nhau):
    máy gốc :  uv run python <path>\test_ghi_song_song.py --tag goc
    máy editor: uv run python <path>\test_ghi_song_song.py --tag editor

- Dùng db `autoedit_test` (KHÔNG đụng sổ thật `autoedit`) — DSN tự suy từ machine.json
  db_url của chính máy đang chạy, chỉ đổi dbname. Bảng riêng `m4_test`, xong tự dọn.
- Ghi qua ĐÚNG shim PgConnection của tool (db.connect(db_url=...)) — test cả lớp đệm.
- 3 pha: ① barrier chờ đủ 2 máy qua chính PG ② mỗi máy 200 INSERT khóa riêng
  ③ 100 UPSERT cả 2 máy vào CÙNG 1 khóa (tranh chấp row-lock). Cuối: mỗi máy tự
  verify thấy đủ dòng của máy kia + shared row không hỏng.
"""

from __future__ import annotations

import argparse
import sys
import time

from autoedit.library import db
from autoedit.packager.machine import resolve_db_url

N_OWN = 200
N_SHARED = 100
BARRIER_TIMEOUT_S = 300


def test_dsn() -> str:
    dsn = resolve_db_url()
    if not dsn:
        sys.exit("Máy này chưa set-db-url — chạy set-db-url trước (M4).")
    if "dbname=autoedit" not in dsn:
        sys.exit(f"db_url không có dbname=autoedit — không suy được DSN test.")
    return dsn.replace("dbname=autoedit", "dbname=autoedit_test")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, choices=["goc", "editor"])
    ap.add_argument("--cleanup", action="store_true", help="chỉ dọn bảng m4_test rồi thoát")
    args = ap.parse_args()
    tag, other = args.tag, ("editor" if args.tag == "goc" else "goc")

    conn = db.connect(db_url=test_dsn())
    conn.execute(
        "CREATE TABLE IF NOT EXISTS m4_test ("
        "k TEXT PRIMARY KEY, v TEXT NOT NULL, tag TEXT NOT NULL, ts DOUBLE PRECISION NOT NULL)"
    )
    if args.cleanup:
        conn.execute("DROP TABLE m4_test")
        print("Đã dọn bảng m4_test.")
        return

    errors = 0

    # ① barrier: khai báo sẵn sàng rồi chờ máy kia (đồng bộ qua chính PG)
    conn.execute(
        "INSERT INTO m4_test (k, v, tag, ts) VALUES (?, ?, ?, ?) "
        "ON CONFLICT (k) DO UPDATE SET ts = EXCLUDED.ts",
        (f"ready:{tag}", "1", tag, time.time()),
    )
    print(f"[{tag}] sẵn sàng — chờ máy '{other}' (tối đa {BARRIER_TIMEOUT_S}s)...")
    t0 = time.time()
    while True:
        row = conn.execute("SELECT 1 AS ok FROM m4_test WHERE k = ?", (f"ready:{other}",)).fetchone()
        if row:
            break
        if time.time() - t0 > BARRIER_TIMEOUT_S:
            sys.exit(f"[{tag}] HẾT GIỜ chờ máy '{other}' — máy kia đã chạy script chưa?")
        time.sleep(2)
    print(f"[{tag}] cả 2 máy sẵn sàng — BẮT ĐẦU ghi song song.")

    # ② 200 insert khóa riêng, xen kẽ đọc
    t1 = time.time()
    for i in range(N_OWN):
        try:
            conn.execute(
                "INSERT INTO m4_test (k, v, tag, ts) VALUES (?, ?, ?, ?) "
                "ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v, ts = EXCLUDED.ts",
                (f"{tag}:{i:04d}", f"v{i}", tag, time.time()),
            )
            if i % 20 == 0:
                conn.execute("SELECT count(*) AS n FROM m4_test").fetchone()
        except Exception as e:  # noqa: BLE001 — đếm mọi lỗi ghi, đó là mục tiêu test
            errors += 1
            print(f"[{tag}] LỖI pha 2 i={i}: {e}")

    # ③ 100 upsert cả 2 máy vào CÙNG khóa 'shared' (tranh chấp row-lock)
    for i in range(N_SHARED):
        try:
            conn.execute(
                "INSERT INTO m4_test (k, v, tag, ts) VALUES ('shared', ?, ?, ?) "
                "ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v, tag = EXCLUDED.tag, ts = EXCLUDED.ts",
                (f"{tag}-{i}", tag, time.time()),
            )
        except Exception as e:  # noqa: BLE001
            errors += 1
            print(f"[{tag}] LỖI pha 3 i={i}: {e}")
    dt = time.time() - t1

    # đánh dấu xong + chờ máy kia xong rồi verify chéo
    conn.execute(
        "INSERT INTO m4_test (k, v, tag, ts) VALUES (?, ?, ?, ?) "
        "ON CONFLICT (k) DO UPDATE SET ts = EXCLUDED.ts",
        (f"done:{tag}", "1", tag, time.time()),
    )
    t0 = time.time()
    while not conn.execute("SELECT 1 AS ok FROM m4_test WHERE k = ?", (f"done:{other}",)).fetchone():
        if time.time() - t0 > BARRIER_TIMEOUT_S:
            sys.exit(f"[{tag}] HẾT GIỜ chờ '{other}' ghi xong.")
        time.sleep(2)

    n_own = conn.execute("SELECT count(*) AS n FROM m4_test WHERE tag = ? AND k LIKE ?", (tag, f"{tag}:%")).fetchone()["n"]
    n_other = conn.execute("SELECT count(*) AS n FROM m4_test WHERE k LIKE ?", (f"{other}:%",)).fetchone()["n"]
    shared = conn.execute("SELECT v, tag FROM m4_test WHERE k = 'shared'").fetchone()
    conn.close()

    ok = errors == 0 and n_own == N_OWN and n_other == N_OWN and shared is not None
    print(f"[{tag}] KẾT QUẢ: lỗi={errors} · dòng mình={n_own}/{N_OWN} · dòng máy kia={n_other}/{N_OWN}"
          f" · shared cuối='{shared['v'] if shared else None}' (máy {shared['tag'] if shared else '?'})"
          f" · {N_OWN + N_SHARED} lệnh ghi hết {dt:.1f}s")
    print(f"[{tag}] {'✅ ĐẠT' if ok else '❌ TRƯỢT'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
