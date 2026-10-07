"""Hàng đợi dựng video Vox cho CẢ ĐỘI editor — một file SQLite riêng.

Không đụng `kichban.db` (đang có người dùng thật trên production). Một GPU, nhiều người:
chia lượt theo NGƯỜI — ai lâu chưa được phục vụ thì tới lượt; trong một người, gửi trước
làm trước. Thợ chết giữa chừng thì `khoi_phuc()` trả việc `dang` về `cho`.
"""

from __future__ import annotations

import os
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path

# Gốc dữ liệu VOX: hàng đợi, thư mục việc, bản tách theo ảnh.
GOC_MAC_DINH = Path(os.getenv("COLLAGE_GOC", r"F:\AutoEdit\collage"))

_BANG = """CREATE TABLE IF NOT EXISTS viec(
    id TEXT PRIMARY KEY, nguoi TEXT, model TEXT, giay REAL, cd TEXT, anh TEXT, nhan TEXT,
    trang_thai TEXT, tao REAL, bat_dau REAL, xong_luc REAL, ra TEXT, loi TEXT, diem TEXT DEFAULT '[]',
    chuoi TEXT DEFAULT '{}')"""


def ma_moi() -> str:
    return "vox-" + uuid.uuid4().hex[:12]


class HangDoi:
    def __init__(self, duong):
        self.duong = Path(duong)
        self.duong.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._noi()) as c, c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute(_BANG)
            # hàng đợi tạo trước P3 chưa có cột điểm bấm -> vá cột, không xoá dữ liệu
            cot = {r["name"] for r in c.execute("PRAGMA table_info(viec)")}
            if "diem" not in cot:
                c.execute("ALTER TABLE viec ADD COLUMN diem TEXT DEFAULT '[]'")
            if "chuoi" not in cot:                               # tool VOX riêng 07/10: chuỗi ảnh
                c.execute("ALTER TABLE viec ADD COLUMN chuoi TEXT DEFAULT '{}'")

    def _noi(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.duong, timeout=30, isolation_level=None)
        c.row_factory = sqlite3.Row
        return c

    # ------------------------------------------------------------ ghi
    def tao(self, nguoi: str, model: str, giay: float, cd: str, anh: str, nhan: str,
            id: str | None = None, diem: list | None = None, chuoi: dict | None = None) -> str:
        import json

        ma = id or ma_moi()
        with closing(self._noi()) as c:
            c.execute("INSERT INTO viec(id,nguoi,model,giay,cd,anh,nhan,trang_thai,tao,diem,chuoi) "
                      "VALUES(?,?,?,?,?,?,?,'cho',?,?,?)",
                      (ma, nguoi or "", model or "", float(giay), cd or "", anh or "", nhan or "", time.time(),
                       json.dumps(diem or [], ensure_ascii=False), json.dumps(chuoi or {}, ensure_ascii=False)))
        return ma

    def lay_tiep(self) -> dict | None:
        """Nhận việc kế tiếp theo lượt công bằng, đánh dấu `dang` — trong MỘT giao dịch."""
        with closing(self._noi()) as c:
            c.execute("BEGIN IMMEDIATE")
            try:
                thu_tu = self._thu_tu(c)
                if not thu_tu:
                    c.execute("COMMIT")
                    return None
                ma = thu_tu[0]
                c.execute("UPDATE viec SET trang_thai='dang', bat_dau=? WHERE id=?", (time.time(), ma))
                c.execute("COMMIT")
            except Exception:
                c.execute("ROLLBACK")
                raise
        return self.doc(ma)

    def xong(self, ma: str, ra: str) -> None:
        self._dat(ma, trang_thai="xong", ra=ra, xong_luc=time.time())

    def hong(self, ma: str, loi: str) -> None:
        self._dat(ma, trang_thai="hong", loi=loi, xong_luc=time.time())

    def khoi_phuc(self) -> int:
        """Thợ bật lại: việc đang dở (thợ cũ chết) quay về hàng chờ."""
        with closing(self._noi()) as c:
            return c.execute("UPDATE viec SET trang_thai='cho', bat_dau=NULL WHERE trang_thai='dang'").rowcount

    def _dat(self, ma: str, **cot) -> None:
        ten = ", ".join(f"{k}=?" for k in cot)
        with closing(self._noi()) as c:
            c.execute(f"UPDATE viec SET {ten} WHERE id=?", (*cot.values(), ma))

    # ------------------------------------------------------------ đọc
    def doc(self, ma: str) -> dict | None:
        with closing(self._noi()) as c:
            r = c.execute("SELECT * FROM viec WHERE id=?", (ma,)).fetchone()
        return dict(r) if r else None

    def cua(self, nguoi: str, gioi_han: int = 50) -> list[dict]:
        """Việc của MỘT người, mới nhất trước."""
        with closing(self._noi()) as c:
            return [dict(r) for r in c.execute("SELECT * FROM viec WHERE nguoi=? ORDER BY tao DESC LIMIT ?",
                                               (nguoi, gioi_han))]

    def thu_tu(self, ma: str) -> int:
        """Vị trí (1 = làm kế tiếp) của việc đang chờ; 0 nếu không còn chờ."""
        with closing(self._noi()) as c:
            ds = self._thu_tu(c)
        return ds.index(ma) + 1 if ma in ds else 0

    @staticmethod
    def _thu_tu(c: sqlite3.Connection) -> list[str]:
        """Mô phỏng thứ tự sẽ làm: mỗi lượt chọn NGƯỜI được phục vụ lâu nhất (chưa từng
        = ưu tiên), trong người đó lấy việc gửi sớm nhất."""
        cho = c.execute("SELECT id, nguoi FROM viec WHERE trang_thai='cho' ORDER BY rowid").fetchall()
        hang: dict[str, list[str]] = {}
        for r in cho:
            hang.setdefault(r["nguoi"], []).append(r["id"])
        lan_cuoi = {r["nguoi"]: r["m"] for r in c.execute(
            "SELECT nguoi, MAX(bat_dau) AS m FROM viec WHERE bat_dau IS NOT NULL GROUP BY nguoi")}
        vi_tri = {r["id"]: i for i, r in enumerate(cho)}
        ra, buoc = [], 0
        while hang:
            n = min(hang, key=lambda k: (lan_cuoi.get(k, float("-inf")), vi_tri[hang[k][0]]))
            ra.append(hang[n].pop(0))
            buoc += 1
            lan_cuoi[n] = time.time() + 1e6 + buoc                  # vừa được phục vụ -> xuống cuối lượt
            if not hang[n]:
                del hang[n]
        return ra
