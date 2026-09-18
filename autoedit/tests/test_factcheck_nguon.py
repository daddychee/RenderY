"""Bàn kịch bản — XẾP HẠNG NGUỒN + luật kết luận fact-check.

User chốt 15/09: LLM trả **hai** kết quả thôi — ĐÚNG (kèm citation chống lưng)
hoặc SAI/CHƯA KẾT LUẬN. Nội dung là điều tra báo chí + học thuật sức khoẻ.

LUẬT CỨNG (tôi nêu, user chốt): **dấu ✅ chỉ được đóng khi có ít nhất MỘT nguồn
mà PYTHON đã kiểm** — link sống, domain nằm trong danh sách uy tín, và trích đoạn
CÓ THẬT trong trang. LLM nói đúng mà không nguồn nào kiểm được thì rơi xuống ❌.
Không có luật này thì dấu ✅ là do LLM tự khen nó — nguy hiểm hơn không có tool,
vì team sẽ thôi tự đọc nguồn. Kênh sức khoẻ cho người trên 60 là vùng YouTube
soi kỹ nhất.

Hai luật riêng cho y khoa (đã trình 15/09): ưu tiên BÀI GỐC hơn báo đưa tin về
bài; và "gây ra" mà nguồn chỉ là nghiên cứu quan sát thì KHÔNG phải bằng chứng
nhân quả — đó là lỗi hay gặp nhất của thể loại này.
"""

from __future__ import annotations

from autoedit.factcheck.nguon import CHAN, hang, mo_ta_hang
from autoedit.factcheck.kiem import Nguon, chu_ky, ket_luan


# ------------------------------ xếp hạng ------------------------------------
def test_hang_1_la_bang_chung_goc():
    for u in ("https://pubmed.ncbi.nlm.nih.gov/30789285/",
              "https://www.nejm.org/doi/full/10.1056/NEJMoa1806640",
              "https://www.thelancet.com/journals/lancet/article/PIIS0140",
              "https://www.cdc.gov/stroke/facts.htm",
              "https://www.nhlbi.nih.gov/science/womens-health-initiative-whi",
              "https://www.who.int/news-room/fact-sheets/detail/stroke",
              "https://clinicaltrials.gov/study/NCT00000611",
              "https://www.sec.gov/edgar/browse/?CIK=320193",
              "https://www.europepmc.org/article/MED/30789285"):
        assert hang(u) == 1, u


def test_hang_2_la_bao_uy_tin():
    for u in ("https://www.reuters.com/business/healthcare/x",
              "https://apnews.com/article/abc",
              "https://www.bbc.com/news/health-123",
              "https://www.propublica.org/article/x",
              "https://www.theguardian.com/science/2024/jan/01/x"):
        assert hang(u) == 2, u


def test_hang_3_chi_de_dinh_huong():
    """Wikipedia / Mayo / Harvard Health: tra ngược tìm bài gốc, KHÔNG trích làm
    bằng chứng cuối."""
    for u in ("https://en.wikipedia.org/wiki/Stroke",
              "https://www.mayoclinic.org/diseases-conditions/stroke",
              "https://www.health.harvard.edu/heart-health/x"):
        assert hang(u) == 3, u


def test_nguon_bi_chan():
    """Trang bán thực phẩm chức năng, content farm, diễn đàn — chặn thẳng."""
    for u in ("https://www.reddit.com/r/nutrition/comments/x",
              "https://www.youtube.com/watch?v=x",
              "https://blog.supplementshop.com/diet-soda-truth",
              "https://www.prnewswire.com/news-releases/x"):
        assert hang(u) is None, u
    assert "reddit.com" in CHAN


def test_domain_la_bi_tu_choi_chu_khong_doan_bua():
    """Không biết thì KHÔNG cho làm bằng chứng — fail-closed."""
    assert hang("https://trangnaolado.example/x") is None


def test_ten_mien_con_van_tinh_dung_hang():
    assert hang("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123/") == 1
    assert hang("https://kho.dulieu.cdc.gov/x") == 1


def test_mo_ta_hang_cho_nguoi_doc():
    assert "gốc" in mo_ta_hang(1).lower()
    assert mo_ta_hang(None) and "không" in mo_ta_hang(None).lower()


# ------------------------------ kết luận ------------------------------------
def _ng(url, song=True, khop=True):
    return Nguon(url=url, ten="x", trich="y", song=song, khop=khop)


def test_dung_khi_co_nguon_hang_1_kiem_duoc():
    kq, ly = ket_luan(True, [_ng("https://pubmed.ncbi.nlm.nih.gov/1/")])
    assert kq == "dung" and "1 nguồn" in ly


def test_llm_noi_dung_nhung_khong_nguon_nao_kiem_duoc_thi_KHONG_dung():
    """Ca nguy hiểm nhất: LLM khẳng định nhưng link chết/bịa."""
    kq, ly = ket_luan(True, [_ng("https://pubmed.ncbi.nlm.nih.gov/1/", song=False)])
    assert kq == "sai"
    assert "không kiểm được" in ly or "link chết" in ly


def test_trich_doan_khong_co_that_trong_trang_thi_khong_tinh():
    kq, _ = ket_luan(True, [_ng("https://www.cdc.gov/x", khop=False)])
    assert kq == "sai"


def test_nguon_hang_3_khong_du_de_dong_dau_dung():
    """Wikipedia sống, trích đoạn khớp — vẫn KHÔNG đủ làm bằng chứng cuối."""
    kq, ly = ket_luan(True, [_ng("https://en.wikipedia.org/wiki/Stroke")])
    assert kq == "sai" and "hạng 3" in ly


def test_llm_noi_sai_thi_giu_nguyen_sai_du_co_nguon():
    kq, ly = ket_luan(False, [_ng("https://www.cdc.gov/x")], ly_do="Nguồn nói ngược lại.")
    assert kq == "sai" and "ngược" in ly


def test_khong_co_nguon_nao():
    kq, ly = ket_luan(True, [])
    assert kq == "sai" and "không tìm được nguồn" in ly.lower()


# ------------------------------ neo đoạn ------------------------------------
def test_chu_ky_bo_qua_khac_biet_khoang_trang():
    """Neo citation theo NỘI DUNG, không theo số dòng: chẻ/gộp dòng không đổi
    một chữ nào nên kết luận phải giữ nguyên (user chốt 15/09)."""
    a = "The strongest evidence comes from the WHI."
    b = "The strongest evidence comes\nfrom the   WHI."
    assert chu_ky(a) == chu_ky(b)


def test_chu_ky_doi_khi_sua_chu():
    assert chu_ky("23 percent higher risk") != chu_ky("33 percent higher risk")


# ---- bổ sung sau khi ĐO THẬT một lượt tra (16/09) --------------------------
def test_nha_xuat_ban_binh_duyet_lon_phai_la_hang_1():
    """Đo thật trên câu WHI/nước ngọt ăn kiêng: Serper trả về ĐÚNG bài gốc ở
    `ahajournals.org` (tạp chí Stroke) mà danh sách cũ loại thẳng — tức là tool
    tự vứt bằng chứng tốt nhất rồi báo 'không đủ căn cứ'."""
    for u in ("https://www.ahajournals.org/doi/10.1161/STROKEAHA.118.023100",
              "https://academic.oup.com/aje/article/188/1/1",
              "https://onlinelibrary.wiley.com/doi/10.1111/x",
              "https://link.springer.com/article/10.1007/x",
              "https://www.cambridge.org/core/journals/x",
              "https://journals.plos.org/plosone/article?id=10.1371/x",
              "https://www.frontiersin.org/articles/10.3389/x",
              "https://www.annals.org/doi/10.7326/x",
              "https://diabetesjournals.org/care/article/x"):
        assert hang(u) == 1, u


def test_trang_tin_khoa_hoc_va_thong_cao_khong_phai_bang_chung():
    """sciencedaily/eurekalert chỉ đăng lại thông cáo của trường — trích nó là
    trích thông cáo, không phải trích nghiên cứu."""
    for u in ("https://www.sciencedaily.com/releases/2019/02/x.htm",
              "https://www.eurekalert.org/news-releases/123"):
        assert hang(u) is None, u
