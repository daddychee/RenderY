r"""Ba bộ phận CHẠM RA NGOÀI của fact-check: tra Serper · tải trang · LLM đọc.

Tách khỏi `kiem.py` để phần LUẬT (cái quyết định dấu ✅/❌) là hàm thuần, test
được không cần mạng. Ở đây chỉ có I/O.

Khoá lấy từ KÉT OUTLIERY như bộ dịch (một cửa khoá, `docs/APPS.md` bước 5):
Serper nằm ở việc `tim_tu_lieu`, GLM ở `cham_footage`.

Không cài thêm gói bóc HTML (bs4/trafilatura đều KHÔNG có trong venv này, và
thang Ponytail: đủ dùng thì đừng thêm). Bóc chữ bằng regex — đây là việc tìm
một câu trong trang, không phải dựng lại bố cục.
"""

from __future__ import annotations

import html
import json
import os
import re
import urllib.error
import urllib.request

import requests

SERPER_URL = "https://google.serper.dev/search"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) RenderY-KichBan/0.1"


def _khoa(viec: str, nha: str = "") -> str:
    """Khoá của một việc trong két; `nha` để chọn đúng nhà cung cấp khi việc đó
    có nhiều khoá (tim_tu_lieu đang giữ cả serpapi lẫn serper)."""
    try:                     # két là TUỲ CHỌN — đứng riêng thì rơi về biến môi trường
        from autoedit.web.ket_v3 import doc_ket

        ds = (doc_ket().get(viec) or {}).get("khoa") or []
    except Exception:  # noqa: BLE001
        ds = []
    for k in ds:
        if not nha or nha in (k.get("nha") or "").lower():
            if k.get("key"):
                return k["key"]
    return ""


# ------------------------------------------------------------------ tra
def tim_serper(truy_van: str, so: int = 8, cai_dat: dict | None = None) -> list[dict]:
    """Google qua Serper.dev -> [{url, ten, mo_ta}]. Không có khoá -> rỗng.

    Thứ tự khoá: tab ⚙ trong app -> két OUTLIERY -> biến môi trường. Ô trong app
    là BẮT BUỘC phải có: đóng gói xong, máy chủ chạy Treatment ở thư mục riêng nên
    không import được `autoedit` -> mất luôn khoá Serper của két, mà mất kênh này
    thì mảng điều tra báo chí chết lặng, chỉ còn Europe PMC lo phần học thuật.
    """
    key = ((cai_dat or {}).get("serper_key") or _khoa("tim_tu_lieu", "serper")
           or os.getenv("SERPER_API_KEY", ""))
    if not key or not truy_van.strip():
        return []
    try:
        r = requests.post(SERPER_URL, timeout=25,
                          json={"q": truy_van, "num": so},
                          headers={"X-API-KEY": key, "Content-Type": "application/json",
                                   "User-Agent": _UA})
        if r.status_code != 200:
            return []
        kq = r.json()
    except Exception:  # noqa: BLE001 — mất một kênh, không được giết lượt kiểm
        return []
    return [{"url": m.get("link", ""), "ten": m.get("title", ""),
             "mo_ta": m.get("snippet", "")}
            for m in (kq.get("organic") or []) if m.get("link")]


EPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def tim_europepmc(truy_van: str, so: int = 4) -> list[dict]:
    """Tra Europe PMC — API MỞ, không khoá, không bị chặn bot, trả thẳng TÓM TẮT.

    Vì sao phải có kênh này (đo 16/09): Serper tìm ra đúng bài gốc nhưng
    `ahajournals.org` và cả `nhlbi.nih.gov` đều trả **403** cho mọi lượt tải tự
    động — cào không lấy được chữ, tool đành báo "không đủ căn cứ" dù bằng chứng
    nằm ngay đó. Đây là cửa chính cho mảng học thuật sức khoẻ; Serper lo phần
    điều tra báo chí và tin tức.

    Trả [{url, ten, text}] — có `text` sẵn nên `kiem_doan` không cào lại.
    """
    import requests

    if not truy_van.strip():
        return []
    try:
        r = requests.get(EPMC_URL, timeout=25, headers={"User-Agent": _UA}, params={
            "query": truy_van, "format": "json", "resultType": "core",
            # KHÔNG sắp theo lượt trích dẫn: đo 16/09 thì nó đẩy mấy bản báo cáo
            # thống kê thường niên lên đầu, còn bài đúng chủ đề rơi mất. Để mặc
            # định (độ liên quan).
            "pageSize": so})
        ds = (r.json().get("resultList") or {}).get("result") or []
    except Exception:  # noqa: BLE001 — hỏng thì chỉ mất một kênh, còn Serper
        return []

    ra = []
    for m in ds:
        tom = (m.get("abstractText") or "").strip()
        if not tom:
            continue                       # không có tóm tắt thì không soi được
        pmid, doi = m.get("pmid") or "", m.get("doi") or ""
        url = (f"https://europepmc.org/article/MED/{pmid}" if pmid
               else f"https://doi.org/{doi}" if doi else "")
        if not url:
            continue
        nam = m.get("pubYear") or ""
        tap_chi = ((m.get("journalInfo") or {}).get("journal") or {}).get("title") or ""
        ra.append({
            "url": url,
            "ten": f"{m.get('title', '')} — {tap_chi} {nam}".strip(" —"),
            "text": _THE.sub(" ", tom) + (f"\n\nDOI: {doi}" if doi else ""),
        })
    return ra


def tim_gop(truy_van: str, so: int = 8, cai_dat: dict | None = None) -> list[dict]:
    """Europe PMC TRƯỚC (bài gốc, lấy được chữ), rồi mới tới Serper."""
    return tim_europepmc(truy_van, so=4) + tim_serper(truy_van, so=so, cai_dat=cai_dat)


# ----------------------------------------------------------------- tải
_BO_HAN = re.compile(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>")
_THE = re.compile(r"(?s)<[^>]+>")


def tai_trang(url: str, tran_ky_tu: int = 400_000) -> tuple[int, str]:
    """(mã HTTP, chữ trong trang). Hỏng/không mở được -> (0, '').

    Dùng `requests` chứ KHÔNG dùng urllib. Đo 16/09 trên chính máy chủ này:
    urllib chết `SSL: CERTIFICATE_VERIFY_FAILED (self-signed certificate in
    certificate chain)` với mọi trang https — máy nằm sau lớp chặn TLS — nên cả
    5 nguồn đều về HTTP=0 và tool báo "không tìm được nguồn uy tín" dù Serper
    trả đúng bài gốc. `requests` đi kho chứng chỉ riêng nên qua được.
    """
    import requests

    try:
        r = requests.get(url, timeout=25, allow_redirects=True, headers={
            "User-Agent": _UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"})
    except Exception:  # noqa: BLE001 — mọi lỗi mạng đều là "không mở được"
        return 0, ""
    loai = (r.headers.get("Content-Type") or "").lower()
    if r.status_code >= 400:
        return r.status_code, ""
    if "html" not in loai and "text" not in loai:
        return r.status_code, ""      # PDF/ảnh: không soi trích đoạn được
    chu = _THE.sub(" ", _BO_HAN.sub(" ", r.text[:tran_ky_tu]))
    return r.status_code, re.sub(r"[ \t\xa0]+", " ", html.unescape(chu))


_DOI = re.compile(r"(10\.\d{4,9}/[^\s?&#\"']+)", re.I)
_PMID = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)|europepmc\.org/article/MED/(\d+)", re.I)


def tai_thong_minh(url: str) -> tuple[int, str]:
    """Tải trang; bị chặn thì vòng qua Europe PMC bằng DOI/PMID trong chính URL.

    Đo 16/09: `ahajournals.org` (bài gốc WHI) và `nhlbi.nih.gov` trả **403** cho
    mọi lượt tải tự động. Không đi cửa sau lớp chặn bot — đi cửa chính thức: bài
    nào có DOI thì Europe PMC có tóm tắt, lấy ở đó, và vẫn ghi nguồn là URL gốc
    người đọc bấm được.
    """
    ma, chu = tai_trang(url)
    if ma == 200 and chu:
        return ma, chu

    m = _PMID.search(url)
    pmid = (m.group(1) or m.group(2)) if m else ""
    truy = f"EXT_ID:{pmid}" if pmid else ""
    if not truy:
        d = _DOI.search(url)
        if not d:
            return ma, chu
        truy = f'DOI:"{d.group(1).rstrip(".")}"'

    ds = tim_europepmc(truy, so=1)
    return (200, ds[0]["text"]) if ds else (ma, chu)


# ------------------------------------------------------------------ LLM
_CAU_TRUY_VAN = """Bạn giúp NHÀ BÁO ĐIỀU TRA kiểm chứng một đoạn kịch bản video.

Đọc đoạn dưới đây và viết MỘT câu tra cứu tiếng Anh để tìm nguồn gốc kiểm chứng
được (bài nghiên cứu, cơ quan y tế, báo lớn). Giữ tên riêng, tên nghiên cứu, con
số. Không thêm dấu ngoặc kép, không thêm lời nào khác.

Trả về JSON: {"truy_van": ["câu tra cứu"]}"""

_CAU_KET_LUAN = """Bạn kiểm chứng MỘT đoạn kịch bản video, cho kênh nội dung sức
khoẻ / điều tra. Bạn được đưa NGUYÊN VĂN nội dung của vài trang nguồn uy tín.

Luật:
- CHỈ dùng nội dung các trang được đưa. TUYỆT ĐỐI không nhắc tới URL nào khác,
  không dựa vào trí nhớ của bạn.
- `trich` phải là đoạn COPY NGUYÊN VĂN từ trang đó (10-40 từ). Nó sẽ được máy dò
  lại trong trang; chép sai một chữ là hỏng.
- `dung: true` khi trang nguồn chống lưng cho NỘI DUNG và CON SỐ của đoạn.
- Con số trong đoạn lệch con số trong nguồn -> `dung: false`, nêu số đúng.
- Đoạn chỉ TƯỜNG THUẬT kết quả nghiên cứu ("nghiên cứu thấy nhóm X có nguy cơ cao
  hơn 23%", "gắn với", "liên quan tới") mà nguồn đúng như vậy -> `dung: true`.
  Nếu đó là nghiên cứu quan sát thì THÊM MỘT CÂU NHẮC trong `ly_do`, ĐỪNG bác.
- Chỉ `dung: false` vì nhân quả khi đoạn KHẲNG ĐỊNH nguyên nhân: "gây ra", "làm
  cho", "dẫn đến", "khiến bạn bị" — trong khi nguồn chỉ là quan sát/tương quan.
- `ly_do` viết TIẾNG VIỆT, một câu, nói cho người viết kịch bản biết phải làm gì.

Trả về JSON:
{"dung": true/false, "ly_do": "...", "nguon": [{"url": "...", "trich": "..."}]}"""


class LlmKiem:
    """GLM đọc trang và kết luận. Cùng khuôn gọi với `dich.DichGLM`."""

    def __init__(self, key: str = "", model: str = "", cai_dat: dict | None = None) -> None:
        from autoedit.treatment.dich import DichGLM

        goc = DichGLM(key=key, model=model, cai_dat=cai_dat)   # chung đường lấy khoá
        self.key, self.url, self.model = goc.key, goc.url, goc.model

    def _goi(self, he: str, than: str) -> dict:
        """Dùng CHUNG một đường gọi với bộ dịch — một chỗ sửa, không để hai nơi
        lệch nhau (urllib/requests, tham số riêng từng nhà, câu báo lỗi)."""
        from autoedit.treatment.dich import DichGLM

        m = DichGLM(key=self.key, model=self.model)
        m.url = self.url
        return m.goi(he, than)

    def truy_van(self, doan: str) -> list[str]:
        ra = self._goi(_CAU_TRUY_VAN, doan).get("truy_van") or []
        return [str(x) for x in ra][:1]

    def ket_luan(self, doan: str, trang: list[dict]) -> dict:
        # Cắt mỗi trang còn ~6000 ký tự: đủ để tìm câu bằng chứng, không thổi
        # phồng token (5 trang x 400KB là đốt tiền vô ích).
        than = "ĐOẠN CẦN KIỂM:\n" + doan + "\n\n"
        for i, t in enumerate(trang, 1):
            than += (f"--- TRANG {i} ---\nURL: {t['url']}\nTIÊU ĐỀ: {t.get('ten','')}\n"
                     f"{t['text'][:6000]}\n\n")
        return self._goi(_CAU_KET_LUAN, than)
