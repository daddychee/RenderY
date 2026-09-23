r"""Fact-check một ĐOẠN kịch bản — luật gộp kết luận. Hàm thuần, không mạng.

Hai kết quả thôi (user chốt 15/09): **dung** hoặc **sai** (gộp cả "sai" lẫn "chưa
kết luận được"); thẻ ❌ mang theo MỘT DÒNG LÝ DO để người viết biết phải sửa câu
hay chỉ cần hạ giọng.

LUẬT CỨNG — chỗ quan trọng nhất của cả giai đoạn 2:

    dấu ✅ chỉ đóng khi có ≥1 nguồn HẠNG 1-2 mà PYTHON đã kiểm:
    link sống + trích đoạn CÓ THẬT trong trang.

LLM nói đúng mà không nguồn nào kiểm được thì rơi xuống ❌. Không có luật này,
dấu ✅ chỉ là lời LLM tự khen mình — tệ hơn không có tool, vì người viết sẽ thôi
tự đọc nguồn. Hạng 3 (Wikipedia, trang bệnh viện phổ thông) không bao giờ đủ:
nó để tra ngược ra bài gốc, rồi trích bài gốc.

NEO CITATION THEO NỘI DUNG, không theo số dòng. Chẻ/gộp dòng không đổi một chữ
nào nên kết luận phải giữ nguyên (user chốt 15/09); sửa chữ thì chữ ký đổi và
đoạn tự rơi về "cần kiểm lại".
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from autoedit.treatment.nguon import hang


@dataclass
class Nguon:
    """1 nguồn LLM đưa ra, kèm KẾT QUẢ KIỂM của Python."""

    url: str
    ten: str = ""
    trich: str = ""          # đoạn LLM nói là bằng chứng
    song: bool = False       # link trả 200
    khop: bool = False       # trích đoạn có thật trong trang
    luc: str = ""            # thời điểm kiểm
    ban_chup: str = ""       # tên file bản chụp (bằng chứng lúc kiểm)

    @property
    def hang(self) -> int | None:
        return hang(self.url)

    @property
    def dung_lam_bang_chung(self) -> bool:
        h = self.hang
        return bool(h and h <= 2 and self.song and self.khop)

    def ra_dict(self) -> dict:
        d = self.__dict__.copy()
        d["hang"] = self.hang
        d["bang_chung"] = self.dung_lam_bang_chung
        return d


def chu_ky(text: str) -> str:
    """Vân tay của đoạn — gộp mọi khoảng trắng về một dấu cách rồi băm.

    Gộp khoảng trắng chính là thứ làm cho CHẺ DÒNG không phá citation: chẻ chỉ
    thêm một chỗ xuống dòng, chữ y nguyên. Sửa một chữ thì vân tay đổi.
    """
    return hashlib.sha1(
        re.sub(r"\s+", " ", (text or "")).strip().encode("utf-8")).hexdigest()


def ket_luan(llm_dung: bool, nguon: list[Nguon], ly_do: str = "") -> tuple[str, str]:
    """(kết quả, lý do) — 'dung' | 'sai'."""
    if not llm_dung:
        return "sai", ly_do or "LLM kết luận không đúng hoặc chưa đủ căn cứ."
    if not nguon:
        return "sai", "Không tìm được nguồn nào trong danh sách uy tín."

    tot = [n for n in nguon if n.dung_lam_bang_chung]
    if tot:
        return "dung", (f"{len(tot)} nguồn hạng {min(n.hang for n in tot)} chống lưng · "
                        "Python đã kiểm link sống và trích đoạn có thật trong trang.")

    # Vì sao trượt — nói đúng lý do để người kiểm biết làm gì tiếp.
    if any(n.hang == 3 for n in nguon):
        return "sai", ("Chỉ có nguồn hạng 3 (bách khoa / trang phổ thông) — dùng để "
                       "tra ngược ra bài gốc, không đủ làm bằng chứng.")
    if any(not n.song for n in nguon):
        return "sai", "Nguồn LLM đưa ra không kiểm được (link chết hoặc không mở được)."
    if any(n.hang is None for n in nguon):
        return "sai", "Nguồn nằm ngoài danh sách uy tín — không dùng làm bằng chứng."
    return "sai", "Trích đoạn không tìm thấy trong trang nguồn."


def _gon(s: str) -> str:
    """Gộp khoảng trắng + hạ chữ — dùng để so trích đoạn với chữ trong trang.
    LLM hay trả lại câu đúng nghĩa nhưng khác cách xuống dòng/viết hoa."""
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def _co_trong(trich: str, trang: str) -> bool:
    """Trích đoạn có THẬT trong trang không.

    So nguyên câu trước; không thấy thì thử 8 từ đầu — trang web hay chèn ký tự
    lạ (nbsp, gạch nối mềm) giữa câu dài, mà 8 từ liền nhau đã đủ chắc để nói
    'câu này lấy từ đây'. Ngắn hơn thì dễ khớp bừa.
    """
    t, p = _gon(trich), _gon(trang)
    if not t or not p:
        return False
    if t in p:
        return True
    dau = " ".join(t.split()[:8])
    return len(dau.split()) >= 8 and dau in p


def kiem_doan(doan: str, tim, tai, llm, tran_trang: int = 5,
              thu_muc_chup=None) -> "KetQua":
    """Kiểm MỘT đoạn. `tim`/`tai`/`llm` tiêm từ ngoài (test không chạm mạng).

    Python tìm -> Python lọc theo danh sách uy tín -> Python tải -> LLM đọc chữ
    đã tải rồi chọn bằng chứng -> Python soi lại trích đoạn. LLM không bao giờ
    được tự đưa URL: nó chỉ chọn trong số trang đã tải (test khoá điều này).
    """
    from datetime import datetime, timezone

    truy_van = (llm.truy_van(doan) or [""])[0]
    ket_qua_tim = tim(truy_van) or []

    # LỌC TRƯỚC KHI TẢI: vừa nhanh vừa không mở đường cho LLM trích nguồn cấm.
    duoc = [m for m in ket_qua_tim if hang(m.get("url", "")) is not None][:tran_trang]

    trang: dict[str, dict] = {}
    for m in duoc:
        url = m["url"]
        # Nguồn đến từ API mở (Europe PMC) đã có sẵn tóm tắt -> không cào lại.
        # Đo 16/09: nhà xuất bản và cả nhlbi.nih.gov đều trả 403 cho lượt tải tự
        # động, nên đường API là đường DUY NHẤT lấy được chữ của bài gốc.
        chu = (m.get("text") or "").strip()
        if not chu:
            ma, chu = tai(url)
            if ma != 200 or not chu:
                continue
        trang[url] = {"url": url, "ten": m.get("ten", ""), "text": chu}

    if not trang:
        return KetQua(doan=doan, ket="sai", truy_van=truy_van,
                      ly_do="Không tìm được nguồn nào trong danh sách uy tín.")

    kq = llm.ket_luan(doan, list(trang.values())) or {}
    luc = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y %H:%M")

    nguon: list[Nguon] = []
    theo_url: dict[str, Nguon] = {}
    for m in kq.get("nguon") or []:
        url = (m.get("url") or "").strip()
        t = trang.get(url)
        if t is None:
            continue            # URL LLM tự nghĩ ra -> loại thẳng
        trich = (m.get("trich") or "").strip()
        # MỘT URL = MỘT NGUỒN. Đo 16/09: GLM trả hai mục cùng một bài (hai trích
        # đoạn) -> thẻ hiện hai dòng, người đọc tưởng có hai bằng chứng độc lập.
        cu = theo_url.get(url)
        if cu is not None:
            if trich and trich not in cu.trich:
                cu.trich = (cu.trich + " … " + trich).strip(" …")
                cu.khop = cu.khop or _co_trong(trich, t["text"])
            continue
        n = Nguon(url=url, ten=t["ten"], trich=trich,
                  song=True, khop=_co_trong(trich, t["text"]), luc=luc)
        theo_url[url] = n
        if n.dung_lam_bang_chung and thu_muc_chup is not None:
            n.ban_chup = _chup(thu_muc_chup, url, t["text"], luc)
        nguon.append(n)

    ket, ly_do = ket_luan(bool(kq.get("dung")), nguon, kq.get("ly_do", ""))
    return KetQua(doan=doan, ket=ket, ly_do=ly_do, nguon=nguon, truy_van=truy_van)


def _chup(thu_muc, url: str, chu: str, luc: str) -> str:
    """Lưu bản chụp trang tại thời điểm kiểm — bằng chứng khi bị khiếu nại, vì
    link chết sau 6-12 tháng là chuyện thường. Tên file theo băm URL."""
    from pathlib import Path

    d = Path(thu_muc)
    d.mkdir(parents=True, exist_ok=True)
    ten = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16] + ".txt"
    (d / ten).write_text(f"{url}\nKiểm lúc: {luc}\n{'-' * 60}\n{chu}",
                         encoding="utf-8")
    return ten


@dataclass
class KetQua:
    """Một lượt kiểm, đủ để hiện lên thẻ bên phải và lưu vào kho."""

    doan: str
    ket: str                      # dung | sai
    ly_do: str
    nguon: list[Nguon] = field(default_factory=list)
    truy_van: str = ""            # câu LLM đem đi tra — để người kiểm lại bằng tay

    def ra_dict(self) -> dict:
        return {"doan": self.doan, "chu_ky": chu_ky(self.doan), "ket": self.ket,
                "ly_do": self.ly_do, "truy_van": self.truy_van,
                "nguon": [n.ra_dict() for n in self.nguon]}
