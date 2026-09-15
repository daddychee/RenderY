r"""Kho lưu của bàn kịch bản — SQLite riêng, không dính `jobs.db`.

Vì sao SQLite chứ không phải file JSON cạnh chương: 2-3 người (có lúc hơn) làm
cùng lúc trên cùng một tập, cần khoá và cần biết ai đang giữ chương nào. Vì sao
không dùng chung DB với dây chuyền dựng: giai đoạn 1 không nối vào đâu — hỏng ở
đây không được chạm tới 9118.

Khoá đặt ở TẦNG GHI, không chỉ ẩn nút trên UI: người thứ hai mở tab cũ, bấm lưu,
là ghi đè mất công người thứ nhất. Cửa gác phải nằm chỗ dữ liệu đi qua.

Thứ tự chương H -> C1..Cn -> E lấy lại `phan_tich_ten` của `web/chapters.py` —
luật đã có, đã có test riêng; chép lại là đẻ ra hai luật lệch nhau.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

from autoedit.web.chapters import phan_tich_ten

SO_BAN_LUI = 12      # user chốt: giữ 12 bản gần nhất
KHOA_GIAY = 180      # nhả sau 3 phút không gõ


class KhoaBiGiu(RuntimeError):
    """Chương đang do người khác giữ — không được ghi đè."""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS tap(
  ma TEXT PRIMARY KEY, ten TEXT NOT NULL, tao_luc REAL NOT NULL);
CREATE TABLE IF NOT EXISTS chuong(
  tap TEXT NOT NULL, ma TEXT NOT NULL, thu_tu INTEGER NOT NULL,
  dong TEXT NOT NULL DEFAULT '[]', outline TEXT NOT NULL DEFAULT '',
  sua_luc REAL, sua_boi TEXT,
  PRIMARY KEY (tap, ma));
CREATE TABLE IF NOT EXISTS ban_cu(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tap TEXT NOT NULL, chuong TEXT NOT NULL, luc REAL NOT NULL, boi TEXT,
  dong TEXT NOT NULL, outline TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS khoa(
  tap TEXT NOT NULL, chuong TEXT NOT NULL, nguoi TEXT NOT NULL, den REAL NOT NULL,
  PRIMARY KEY (tap, chuong));
"""


class Kho:
    def __init__(self, duong: Path | str) -> None:
        self.duong = Path(duong)
        self.duong.parent.mkdir(parents=True, exist_ok=True)
        self.cn = sqlite3.connect(self.duong, check_same_thread=False)
        self.cn.row_factory = sqlite3.Row
        self.cn.executescript(_SCHEMA)
        self.cn.commit()

    # ------------------------------------------------------------------ tập
    def tao_tap(self, ma: str, ten: str) -> None:
        if self.cn.execute("SELECT 1 FROM tap WHERE ma=?", (ma,)).fetchone():
            raise ValueError(f"Tập '{ma}' đã có rồi.")
        self.cn.execute("INSERT INTO tap(ma, ten, tao_luc) VALUES(?,?,?)",
                        (ma, ten, time.time()))
        self.cn.commit()

    def ds_tap(self) -> list[dict]:
        return [dict(r) for r in
                self.cn.execute("SELECT ma, ten FROM tap ORDER BY tao_luc DESC")]

    # --------------------------------------------------------------- chương
    def tao_chuong(self, tap: str, ma: str) -> str:
        """Chỉ nhận đúng H / C<số> / E. Tên khác bị từ chối ngay thay vì đoán —
        dựng nhầm thứ tự chương thì phải dựng lại cả tập."""
        kq = phan_tich_ten(ma)          # None khi sai quy ước — không unpack thẳng
        if kq is None:
            raise ValueError(
                f"Tên chương '{ma}' sai quy ước. Chỉ nhận H, C1, C2… hoặc E.")
        chuan, thu_tu, _ = kq
        self.cn.execute(
            "INSERT OR IGNORE INTO chuong(tap, ma, thu_tu) VALUES(?,?,?)",
            (tap, chuan, thu_tu))
        self.cn.commit()
        return chuan

    def ds_chuong(self, tap: str) -> list[dict]:
        """H -> C1..Cn -> E. Sắp theo TÊN là sai cả hai đầu ('E' trước 'H',
        'C10' trước 'C2')."""
        rows = self.cn.execute(
            "SELECT ma, thu_tu, sua_luc, sua_boi FROM chuong WHERE tap=? "
            "ORDER BY thu_tu, ma", (tap,))
        ra = []
        for r in rows:
            d = dict(r)
            d["ai_giu"] = self.ai_giu(tap, d["ma"])
            ra.append(d)
        return ra

    # ------------------------------------------------------------- lưu / đọc
    def doc(self, tap: str, chuong: str) -> dict:
        r = self.cn.execute(
            "SELECT dong, outline, sua_luc, sua_boi FROM chuong WHERE tap=? AND ma=?",
            (tap, chuong)).fetchone()
        if r is None:
            return {"dong": [], "outline": "", "sua_luc": None, "sua_boi": None}
        d = dict(r)
        d["dong"] = json.loads(d["dong"] or "[]")
        d["ai_giu"] = self.ai_giu(tap, chuong)
        return d

    def luu(self, tap: str, chuong: str, dong: list[dict], outline: str,
            nguoi: str) -> None:
        giu = self.ai_giu(tap, chuong)
        if giu and giu != nguoi:
            raise KhoaBiGiu(f"{giu} đang sửa chương {chuong}.")
        cu = self.doc(tap, chuong)
        self.cn.execute(
            "INSERT INTO ban_cu(tap, chuong, luc, boi, dong, outline) VALUES(?,?,?,?,?,?)",
            (tap, chuong, time.time(), nguoi,
             json.dumps(dong, ensure_ascii=False), outline))
        self.cn.execute(
            "INSERT INTO chuong(tap, ma, thu_tu, dong, outline, sua_luc, sua_boi) "
            "VALUES(?,?,?,?,?,?,?) ON CONFLICT(tap, ma) DO UPDATE SET "
            "dong=excluded.dong, outline=excluded.outline, "
            "sua_luc=excluded.sua_luc, sua_boi=excluded.sua_boi",
            (tap, chuong, (phan_tich_ten(chuong) or ("", 0, ""))[1],
             json.dumps(dong, ensure_ascii=False), outline, time.time(), nguoi))
        self._don_ban_cu(tap, chuong)
        self.cn.commit()
        _ = cu

    def _don_ban_cu(self, tap: str, chuong: str) -> None:
        self.cn.execute(
            "DELETE FROM ban_cu WHERE tap=? AND chuong=? AND id NOT IN "
            "(SELECT id FROM ban_cu WHERE tap=? AND chuong=? ORDER BY id DESC LIMIT ?)",
            (tap, chuong, tap, chuong, SO_BAN_LUI))

    def ban_cu(self, tap: str, chuong: str) -> list[dict]:
        """Mới nhất đứng đầu."""
        rows = self.cn.execute(
            "SELECT id, luc, boi, dong, outline FROM ban_cu WHERE tap=? AND chuong=? "
            "ORDER BY id DESC", (tap, chuong))
        ra = []
        for r in rows:
            d = dict(r)
            d["dong"] = json.loads(d["dong"])
            ra.append(d)
        return ra

    def lui(self, tap: str, chuong: str, ban_id: int, nguoi: str) -> None:
        r = self.cn.execute("SELECT dong, outline FROM ban_cu WHERE id=?",
                            (ban_id,)).fetchone()
        if r is None:
            raise ValueError(f"Không có bản lùi id={ban_id}.")
        self.luu(tap, chuong, json.loads(r["dong"]), r["outline"], nguoi)

    # ----------------------------------------------------------------- khoá
    def ai_giu(self, tap: str, chuong: str) -> Optional[str]:
        r = self.cn.execute(
            "SELECT nguoi, den FROM khoa WHERE tap=? AND chuong=?",
            (tap, chuong)).fetchone()
        if r is None or r["den"] <= time.time():
            return None
        return r["nguoi"]

    def giu(self, tap: str, chuong: str, nguoi: str, giay: int = KHOA_GIAY) -> bool:
        """Giành/gia hạn khoá. Người đang giữ gia hạn được; người khác thì không,
        cho tới khi khoá hết hạn (không gõ `giay` giây)."""
        dang = self.ai_giu(tap, chuong)
        if dang and dang != nguoi:
            return False
        self.cn.execute(
            "INSERT INTO khoa(tap, chuong, nguoi, den) VALUES(?,?,?,?) "
            "ON CONFLICT(tap, chuong) DO UPDATE SET nguoi=excluded.nguoi, den=excluded.den",
            (tap, chuong, nguoi, time.time() + giay))
        self.cn.commit()
        return True

    def nha(self, tap: str, chuong: str, nguoi: str) -> None:
        self.cn.execute("DELETE FROM khoa WHERE tap=? AND chuong=? AND nguoi=?",
                        (tap, chuong, nguoi))
        self.cn.commit()
