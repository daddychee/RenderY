r"""Danh sách NGUỒN UY TÍN — xếp hạng theo tên miền. Hàm thuần, không mạng.

Hai mảng nội dung của kênh (user chốt 15/09): **điều tra báo chí** và **học thuật
sức khoẻ**. Ba hạng:

  1 — BẰNG CHỨNG GỐC, được trích làm chứng cứ: bài bình duyệt, cơ quan chính phủ,
      hồ sơ toà/SEC, số liệu tổ chức quốc tế.
  2 — Báo uy tín, dùng khi không có nguồn gốc.
  3 — CHỈ để định hướng (Wikipedia, trang bệnh viện phổ thông): tra ngược tìm bài
      gốc rồi trích bài gốc. KHÔNG đủ để đóng dấu ĐÚNG.
  None — chặn, hoặc không biết. **Fail-closed**: tên miền lạ không được làm bằng
      chứng. Thà bắt người kiểm tay còn hơn đóng dấu ĐÚNG cho một blog.

Vì sao chặn cứng vài nhóm: trang bán thực phẩm chức năng và press-release luôn có
"nghiên cứu cho thấy" — đó chính là thứ kênh sức khoẻ dễ dẫm phải nhất.
"""

from __future__ import annotations

from urllib.parse import urlsplit

# --------------------------------------------------------------- hạng 1
HANG_1 = {
    # học thuật — bình duyệt / dữ liệu gốc
    "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "europepmc.org",
    "cochranelibrary.com", "nejm.org", "thelancet.com", "jamanetwork.com",
    "bmj.com", "nature.com", "science.org", "sciencedirect.com",
    "clinicaltrials.gov", "doi.org", "crossref.org", "openalex.org",
    # Nhà xuất bản bình duyệt lớn — THÊM 16/09 sau khi đo thật một lượt tra:
    # bài gốc WHI nằm ở `ahajournals.org` (tạp chí Stroke) mà danh sách cũ loại
    # thẳng, tức tool tự vứt bằng chứng tốt nhất rồi báo "không đủ căn cứ".
    "ahajournals.org", "academic.oup.com", "onlinelibrary.wiley.com",
    "link.springer.com", "springer.com", "cambridge.org", "tandfonline.com",
    "journals.plos.org", "plos.org", "frontiersin.org", "annals.org",
    "diabetesjournals.org", "ajcn.nutrition.org", "nutrition.org",
    "cell.com", "jhu.edu", "acpjournals.org",
    # cơ quan nhà nước / quốc tế
    "who.int", "un.org", "worldbank.org", "oecd.org", "europa.eu",
    "efsa.europa.eu", "nhs.uk", "fda.gov", "cdc.gov", "nih.gov",
    "nhlbi.nih.gov", "nia.nih.gov", "cancer.gov", "medlineplus.gov",
    # hồ sơ chính thức — phục vụ điều tra báo chí
    "sec.gov", "courtlistener.com", "justice.gov", "gao.gov",
}
# Đuôi tên miền hạng 1 (cơ quan nhà nước/đại học ở mọi nước).
DUOI_HANG_1 = (".gov", ".gov.uk", ".gov.au", ".edu", ".int")

# --------------------------------------------------------------- hạng 2
HANG_2 = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "ft.com",
    "theguardian.com", "nytimes.com", "washingtonpost.com", "economist.com",
    "propublica.org", "icij.org", "occrp.org", "bellingcat.com",
    "npr.org", "pbs.org", "nature.com.au",
}

# --------------------------------------------------------------- hạng 3
HANG_3 = {
    "wikipedia.org", "wikimedia.org", "britannica.com",
    "mayoclinic.org", "clevelandclinic.org", "health.harvard.edu",
    "hopkinsmedicine.org", "heart.org", "diabetes.org", "alz.org",
    "healthline.com", "webmd.com", "medicalnewstoday.com",
}

# --------------------------------------------------------------- chặn
CHAN = {
    "reddit.com", "youtube.com", "youtu.be", "facebook.com", "x.com",
    "twitter.com", "tiktok.com", "quora.com", "medium.com", "substack.com",
    "prnewswire.com", "businesswire.com", "globenewswire.com", "einpresswire.com",
    "pinterest.com", "linkedin.com",
    # Trang tin khoa học + tổng đài thông cáo: đăng lại press release của trường.
    # Trích nó là trích THÔNG CÁO, không phải trích nghiên cứu (đo 16/09: cả hai
    # đều lọt top kết quả cho câu hỏi y khoa).
    "sciencedaily.com", "eurekalert.org", "newswise.com", "phys.org",
}


def _mien(url: str) -> str:
    m = (urlsplit(url).hostname or "").lower()
    return m[4:] if m.startswith("www.") else m


def _thuoc(mien: str, bo: set[str]) -> bool:
    """Khớp cả tên miền con: `kho.dulieu.cdc.gov` vẫn là `cdc.gov`."""
    return any(mien == d or mien.endswith("." + d) for d in bo)


def hang(url: str) -> int | None:
    """1 / 2 / 3, hoặc None khi bị chặn hay không nằm trong danh sách."""
    m = _mien(url)
    if not m or _thuoc(m, CHAN):
        return None
    # Tên miền KHAI ĐÍCH DANH thắng luật đuôi chung: `health.harvard.edu` là
    # trang phổ thông (hạng 3) chứ không phải bài bình duyệt, dù đuôi là .edu.
    if _thuoc(m, HANG_1):
        return 1
    if _thuoc(m, HANG_2):
        return 2
    if _thuoc(m, HANG_3):
        return 3
    if m.endswith(DUOI_HANG_1):
        return 1
    return None


def mo_ta_hang(h: int | None) -> str:
    return {
        1: "Hạng 1 — bằng chứng gốc (bình duyệt / cơ quan nhà nước / hồ sơ chính thức)",
        2: "Hạng 2 — báo uy tín",
        3: "Hạng 3 — chỉ để định hướng, không đủ làm bằng chứng",
    }.get(h, "Không nằm trong danh sách nguồn uy tín — không dùng làm bằng chứng")
