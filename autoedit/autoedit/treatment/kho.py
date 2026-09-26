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
import re
import sqlite3
import time
from pathlib import Path
from typing import Optional

from autoedit.treatment.dong import doc_canh, ghi_canh
from autoedit.web.chapters import phan_tich_ten

SO_BAN_LUI = 12      # user chốt: giữ 12 bản gần nhất
KHOA_GIAY = 180      # nhả sau 3 phút không gõ


class KhoaBiGiu(RuntimeError):
    """Chương đang do người khác giữ — không được ghi đè."""


_SCHEMA = """
CREATE TABLE IF NOT EXISTS tap(
  ma TEXT PRIMARY KEY, ten TEXT NOT NULL, tao_luc REAL NOT NULL,
  tong TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS chuong(
  tap TEXT NOT NULL, ma TEXT NOT NULL, thu_tu INTEGER NOT NULL,
  dong TEXT NOT NULL DEFAULT '[]', outline TEXT NOT NULL DEFAULT '',
  sua_luc REAL, sua_boi TEXT,
  PRIMARY KEY (tap, ma));
CREATE TABLE IF NOT EXISTS ban_cu(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tap TEXT NOT NULL, chuong TEXT NOT NULL, luc REAL NOT NULL, boi TEXT,
  dong TEXT NOT NULL, outline TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS so(
  tap TEXT NOT NULL, ma TEXT NOT NULL, loai TEXT NOT NULL,
  ten TEXT NOT NULL DEFAULT '', chu TEXT NOT NULL DEFAULT '',
  pr TEXT NOT NULL DEFAULT '', tb TEXT NOT NULL DEFAULT '',
  yc TEXT NOT NULL DEFAULT '',
  thu_tu INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (tap, ma));
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
        # Cột thêm sau: `CREATE TABLE IF NOT EXISTS` không đụng bảng đã có, nên
        # kho cũ phải vá tại chỗ. Rẻ và chạy mỗi lần mở, không cần sổ phiên bản.
        co = {r["name"] for r in self.cn.execute("PRAGMA table_info(so)")}
        for ten in ("pr", "tb", "yc"):
            if co and ten not in co:
                self.cn.execute(
                    f"ALTER TABLE so ADD COLUMN {ten} TEXT NOT NULL DEFAULT ''")
        ct = {r["name"] for r in self.cn.execute("PRAGMA table_info(tap)")}
        if ct and "tong" not in ct:
            self.cn.execute("ALTER TABLE tap ADD COLUMN tong TEXT NOT NULL DEFAULT ''")
        self.cn.commit()
        self._va_ma_canh()

    def _va_ma_canh(self) -> None:
        """Đặt MÃ RIÊNG cho cảnh của dữ liệu cũ, một lần, lúc mở kho.

        Đo thật 24/09 trên bản sao kho production: bấm "Sinh ảnh" nhận 404, vì
        chương lưu TRƯỚC lúc có luật mã riêng nên cảnh không mang `id` và trang
        gọi `/canh//anh`. Mã chỉ được đặt khi chương được LƯU LẠI — mà người
        dùng có thể bấm sinh ảnh trước khi sửa gì.

        Ghi thẳng bằng UPDATE, KHÔNG qua `luu`: đây là vá dữ liệu, không phải
        người sửa — không được đẻ bản lùi, không được đụng `sua_luc`/`sua_boi`,
        và không được vướng khoá chương của ai.
        """
        try:
            rows = list(self.cn.execute("SELECT tap, ma, dong FROM chuong"))
        except sqlite3.Error:
            return
        for r in rows:
            try:
                ds = json.loads(r["dong"] or "[]")
            except (TypeError, ValueError):
                continue
            if not any(c.get("id") is None
                       for d in ds if isinstance(d, dict)
                       for c in (d.get("canh") or [])):
                continue
            moi = [ghi_canh(d, doc_canh(d)) if isinstance(d, dict) else d for d in ds]
            self.cn.execute("UPDATE chuong SET dong=? WHERE tap=? AND ma=?",
                            (json.dumps(moi, ensure_ascii=False), r["tap"], r["ma"]))
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
                self.cn.execute("SELECT ma, ten, tong FROM tap ORDER BY tao_luc DESC")]

    def tong_tap(self, tap: str) -> str:
        """Mã tông dùng cho CẢ TẬP. Cảnh nào không tự chọn thì ăn theo đây.

        Ở cấp tập chứ không phải cấp cảnh (user chốt 25/09): bắt chọn tay từng
        cảnh thì không ai chọn — đo thật trên SE001, 0/83 cảnh có `tong`, nên
        mọi ảnh sinh ra đều mất mood.
        """
        r = self.cn.execute("SELECT tong FROM tap WHERE ma=?", (tap,)).fetchone()
        return (r["tong"] if r else "") or ""

    def dat_tong_tap(self, tap: str, ma: str) -> None:
        self.cn.execute("UPDATE tap SET tong=? WHERE ma=?", (ma or "", tap))
        self.cn.commit()

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
            "SELECT ma, thu_tu, sua_luc, sua_boi, dong FROM chuong WHERE tap=? "
            "ORDER BY thu_tu, ma", (tap,))
        ra = []
        for r in rows:
            d = dict(r)
            # Số câu chạy LIỀN từ H đến E (user chốt 24/09) nên trang phải biết
            # mỗi chương dài bao nhiêu để đặt mốc đếm, kể cả khi chỉ mở một
            # chương. Đếm ở đây, KHÔNG trả cả kịch bản về: mở một chương mà phải
            # kéo cả tập thì chương nào cũng chờ.
            try:
                d["so_dong"] = len(json.loads(d.pop("dong") or "[]"))
            except (TypeError, ValueError):
                d["so_dong"] = 0
            d["ai_giu"] = self.ai_giu(tap, d["ma"])
            ra.append(d)
        return ra

    # ---------------------------------------------------------------- sổ
    # Ba thứ cùng một hình dạng (mã · tên · một đoạn chữ) nên dùng CHUNG một
    # bảng với cột `loai`, không đẻ ba bảng ba bộ endpoint:
    #   tong     — đoạn boilerplate ghép cuối prompt, `canh[i].tong` trỏ tới
    #   nhan_vat / dao_cu / boi_canh — mô tả tiếng Anh của tài sản
    #   nhan_su  — cụm màu 1..6 là ai (user chốt: "cụm màu để phân nhân sự")
    #   truong_doan — một NHÓM CÚ MÁY cùng không gian; `ref` của nó là khung
    #     MASTER mà mọi cú trong nhóm bám theo. KHÔNG phải loại đối tượng thứ
    #     tư: đối tượng chỉ có ba (người/vật/bối cảnh, user chốt 26/09), và nó
    #     không hiện trên màn Asset. Đi chung bảng vì nó cùng hình dạng (mã ·
    #     tên · một đoạn chữ · một ảnh) nên dùng lại được cả đường ref.
    LOAI_SO = ("tong", "nhan_vat", "dao_cu", "boi_canh", "nhan_su",
               "truong_doan")
    # Ảnh ref giữ THÀNH FILE cạnh kho, không giữ cái link (user chốt 24/09):
    # link Drive chết là mất cả sổ, và đợt 2 gọi API thì phải có BYTES mới đính
    # ref vào lượt gọi được.
    # CHỈ ẢNH (user chốt 24/09). Ref là bản mặt của nhân vật/đạo cụ để giữ nhất
    # quán — clip không phục vụ việc đó, mà mở cửa cho video là kho phình bằng
    # file nặng và đợt 2 phải xử hai kiểu đầu vào.
    DUOI_REF = (".png", ".jpg", ".jpeg", ".webp")
    REF_TOI_DA = 25 * 1024 * 1024        # 25MB: rộng gấp nhiều lần một bản ref 4K

    def duong_ref(self, tap: str, ma: str, duoi: str) -> Path:
        """Đường file ref. `ma` và `tap` đi THẲNG vào tên file nên phải chặn ở
        đây: không chặn là ghi đè được file bất kỳ trên ổ bằng `ma=../../...`."""
        for x in (tap, ma):
            if not x or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", x):
                raise ValueError(f"Mã '{x}' có ký tự không dùng được cho tên file.")
        if duoi.lower() not in self.DUOI_REF:
            raise ValueError(f"Đuôi '{duoi}' không nhận — chỉ "
                             f"{', '.join(self.DUOI_REF)}.")
        return self.duong.parent / "tai_san" / tap / (ma + duoi.lower())

    def duong_anh(self, tap: str, ma_canh: str) -> Path:
        """Ảnh sinh cho một cảnh. Neo vào MÃ RIÊNG của cảnh (`canh[i].id`) chứ
        không neo vào số thứ tự hiển thị: chèn một cảnh phía trên là mọi số sau
        đó dịch hết, ảnh sẽ trỏ sang cảnh khác mà không ai thấy gì bất thường.

        Ổ F, tạm thời (user chốt 24/09: "ảnh lưu trong ổ F tạm thời, tôi sẽ xem
        xét vị trí lưu sau"). Đổi chỗ sau này chỉ phải sửa đúng hàm này.
        """
        for x in (tap, ma_canh):
            if not x or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", x):
                raise ValueError(f"Mã '{x}' có ký tự không dùng được cho tên file.")
        return self.duong.parent / "anh" / tap / (ma_canh + ".png")

    def duong_video(self, tap: str, ma_canh: str) -> Path:
        """Clip của một cảnh. Neo vào MÃ RIÊNG như ảnh, cùng lý do."""
        for x in (tap, ma_canh):
            if not x or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", x):
                raise ValueError(f"Mã '{x}' có ký tự không dùng được cho tên file.")
        return self.duong.parent / "video" / tap / (ma_canh + ".mp4")

    def ref_dang_co(self, tap: str, ma: str) -> Optional[Path]:
        for d in self.DUOI_REF:
            try:
                t = self.duong_ref(tap, ma, d)
            except ValueError:
                return None
            if t.exists():
                return t
        return None

    def xoa_ref(self, tap: str, ma: str) -> bool:
        """Xoá HẾT đuôi: tải .png rồi tải .jpg cùng mã mà để lại cả hai thì lần
        sau lấy nhầm bản cũ."""
        xoa = False
        for d in self.DUOI_REF:
            try:
                t = self.duong_ref(tap, ma, d)
            except ValueError:
                return False
            if t.exists():
                t.unlink()
                xoa = True
        return xoa

    def ds_so(self, tap: str) -> list[dict]:
        ra = []
        for r in self.cn.execute(
                "SELECT ma, loai, ten, chu, pr, tb, yc FROM so WHERE tap=? "
                "ORDER BY thu_tu, ma", (tap,)):
            d = dict(r)
            # Sổ phải biết tài sản nào ĐÃ có ref — để đếm được việc còn dở.
            # Kèm TEM PHIÊN BẢN (mtime): vẽ lại ref thì đường ảnh phải đổi, không
            # thì trình duyệt giữ bản đã tải và người dùng tưởng nút hỏng (user
            # báo 26/09 — máy chủ ghi file mới rồi mà màn hình vẫn ảnh cũ).
            t = self.ref_dang_co(tap, d["ma"])
            d["ref"] = t is not None
            d["ref_v"] = int(t.stat().st_mtime) if t is not None else 0
            ra.append(d)
        return ra

    def luu_so(self, tap: str, so: list[dict]) -> None:
        """Ghi CẢ danh sách: sổ nhỏ và sửa thưa, nên bỏ một mục là nó biến mất
        thật chứ không để lại rác.

        Đổi lại: hai người sửa sổ cùng lúc thì người sau đè người trước. Chấp
        nhận — sổ không phải chỗ gõ cả buổi như kịch bản, và kịch bản mới là
        thứ có khoá chương.
        """
        sach = []
        for i, x in enumerate(so or []):
            loai = (x.get("loai") or "").strip()
            if loai not in self.LOAI_SO:
                raise ValueError(
                    f"Loại '{loai}' không có trong sổ — chỉ nhận "
                    f"{', '.join(self.LOAI_SO)}.")
            ma, ten = (x.get("ma") or "").strip(), (x.get("ten") or "").strip()
            if not ma or not ten:       # thiếu mã hoặc tên thì không tra được
                continue
            sach.append((tap, ma, loai, ten, (x.get("chu") or "").strip(),
                         (x.get("pr") or "").strip(),
                         (x.get("tb") or "").strip(),
                         (x.get("yc") or "").strip(), i))
        self.cn.execute("DELETE FROM so WHERE tap=?", (tap,))
        self.cn.executemany(
            "INSERT OR REPLACE INTO so(tap, ma, loai, ten, chu, pr, tb, yc, "
            "thu_tu) VALUES(?,?,?,?,?,?,?,?,?)", sach)
        self.cn.commit()

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
        # CHUẨN HOÁ ở BIÊN GHI, không trông vào trang tự làm đúng: đặt mã riêng
        # cho cảnh chưa có (ảnh neo vào mã), loại khoá lạ một tab hỏng đẩy lên,
        # và áp luật cảnh rỗng. Một chỗ duy nhất, mọi đường ghi đều qua đây.
        dong = [ghi_canh(d, doc_canh(d)) if isinstance(d, dict) else d
                for d in (dong or [])]
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
