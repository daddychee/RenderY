r"""Bàn kịch bản — QUY TRÌNH kiểm một đoạn. Không chạm mạng (tiêm đồ giả).

THỨ TỰ CÓ CHỦ Ý — Python tìm, Python tải, LLM chỉ ĐỌC rồi kết luận:

    1. LLM sinh truy vấn (việc nó giỏi: rút ý chính thành câu tra)
    2. PYTHON tra (Serper) rồi LOẠI mọi tên miền ngoài danh sách uy tín
    3. PYTHON tải trang, lấy chữ
    4. LLM đọc CHỮ ĐÃ TẢI, chọn trích đoạn làm bằng chứng
    5. PYTHON kiểm lại: trích đoạn có THẬT trong trang không

LLM không bao giờ tự đưa URL. Đây là chỗ nó bịa nhiều nhất: URL trông rất thật,
mở ra là 404 hoặc nội dung khác hẳn. Nó chỉ được chọn trong số trang Python đã
tải, và mọi trích dẫn đều bị soi lại.

Bản chụp lưu tại chỗ kiểm: kênh sức khoẻ cần bằng chứng khi bị khiếu nại, mà
link chết sau 6-12 tháng là chuyện thường.
"""

from __future__ import annotations

import pytest

from autoedit.factcheck.kiem import kiem_doan

DOAN = ("The Women's Health Initiative found women drinking two or more "
        "artificially sweetened drinks a day had about 23 percent higher risk of stroke.")

TRANG_THAT = ("Among 81,714 postmenopausal women, those consuming two or more "
              "artificially sweetened beverages per day had a higher risk of "
              "all stroke (aHR 1.23).")


class TimGia:
    """Serper giả — trả đúng thứ ta dựng sẵn, đếm số lượt gọi."""

    def __init__(self, ket_qua):
        self.ket_qua = ket_qua
        self.da_goi: list[str] = []

    def __call__(self, truy_van, so=6):
        self.da_goi.append(truy_van)
        return self.ket_qua


class TaiGia:
    def __init__(self, trang: dict[str, tuple[int, str]]):
        self.trang = trang
        self.da_tai: list[str] = []

    def __call__(self, url):
        self.da_tai.append(url)
        return self.trang.get(url, (404, ""))


class LlmGia:
    def __init__(self, dung=True, nguon=None, ly_do="", truy_van=None):
        self._dung, self._nguon, self._ly_do = dung, nguon or [], ly_do
        self._truy_van = truy_van or ["WHI artificially sweetened beverages stroke risk"]
        self.trang_nhan: list[str] = []

    def truy_van(self, doan):
        return self._truy_van

    def ket_luan(self, doan, trang):
        self.trang_nhan = [t["url"] for t in trang]
        return {"dung": self._dung, "ly_do": self._ly_do, "nguon": self._nguon}


def _bo(ket_qua_tim, trang, llm):
    return TimGia(ket_qua_tim), TaiGia(trang), llm


# --------------------------------------------------------------------------- #
def test_loai_nguon_ngoai_danh_sach_TRUOC_khi_tai():
    """Không tải trang của reddit/blog: vừa tốn thời gian vừa mở đường cho LLM
    trích dẫn thứ không được phép."""
    tim, tai, llm = _bo(
        [{"url": "https://www.reddit.com/r/x", "ten": "reddit"},
         {"url": "https://blog.banthuoc.example/x", "ten": "blog"},
         {"url": "https://pubmed.ncbi.nlm.nih.gov/30789285/", "ten": "WHI"}],
        {"https://pubmed.ncbi.nlm.nih.gov/30789285/": (200, TRANG_THAT)},
        LlmGia(nguon=[{"url": "https://pubmed.ncbi.nlm.nih.gov/30789285/",
                       "trich": "higher risk of all stroke (aHR 1.23)"}]))
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert tai.da_tai == ["https://pubmed.ncbi.nlm.nih.gov/30789285/"]
    assert kq.ket == "dung"


def test_llm_chi_duoc_chon_trong_so_trang_da_tai():
    """Chống bịa URL: LLM nhả một link nó tự nghĩ ra -> loại thẳng."""
    tim, tai, llm = _bo(
        [{"url": "https://www.cdc.gov/stroke/facts.htm", "ten": "CDC"}],
        {"https://www.cdc.gov/stroke/facts.htm": (200, TRANG_THAT)},
        LlmGia(nguon=[{"url": "https://www.nejm.org/doi/bia-ra-day", "trich": "x"}]))
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert kq.ket == "sai"
    assert [n.url for n in kq.nguon] == []


def test_trich_doan_khop_du_khac_khoang_trang_va_hoa_thuong():
    tim, tai, llm = _bo(
        [{"url": "https://www.cdc.gov/x", "ten": "CDC"}],
        {"https://www.cdc.gov/x": (200, TRANG_THAT)},
        LlmGia(nguon=[{"url": "https://www.cdc.gov/x",
                       "trich": "HIGHER   risk of all\nstroke (aHR 1.23)"}]))
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert kq.nguon[0].khop is True and kq.ket == "dung"


def test_trich_doan_khong_co_trong_trang_thi_khong_duoc_dong_dau_dung():
    """LLM 'nhớ' ra một câu không có trong trang — ca bịa tinh vi nhất."""
    tim, tai, llm = _bo(
        [{"url": "https://www.cdc.gov/x", "ten": "CDC"}],
        {"https://www.cdc.gov/x": (200, TRANG_THAT)},
        LlmGia(nguon=[{"url": "https://www.cdc.gov/x",
                       "trich": "risk of stroke doubled in every age group"}]))
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert kq.nguon[0].khop is False
    assert kq.ket == "sai"


def test_link_chet_khong_tinh_la_bang_chung():
    tim, tai, llm = _bo(
        [{"url": "https://www.cdc.gov/x", "ten": "CDC"}],
        {"https://www.cdc.gov/x": (404, "")},
        LlmGia(nguon=[{"url": "https://www.cdc.gov/x", "trich": "x"}]))
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert kq.ket == "sai"


def test_khong_co_nguon_uy_tin_nao_thi_khong_goi_llm_ket_luan():
    """Tra ra toàn rác: dừng sớm, không đốt lượt LLM."""
    tim, tai, llm = _bo(
        [{"url": "https://www.reddit.com/r/x", "ten": "reddit"}], {}, LlmGia())
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert kq.ket == "sai" and "không tìm được nguồn" in kq.ly_do.lower()
    assert llm.trang_nhan == [], "không gọi LLM khi chẳng có gì để đọc"


def test_tran_so_trang_tai_ve():
    """Mỗi lượt kiểm là tiền + thời gian: chặn trần, không tải cả trang kết quả."""
    nhieu = [{"url": f"https://www.cdc.gov/{i}", "ten": str(i)} for i in range(20)]
    tim, tai, llm = _bo(nhieu,
                        {f"https://www.cdc.gov/{i}": (200, TRANG_THAT) for i in range(20)},
                        LlmGia(nguon=[]))
    kiem_doan(DOAN, tim=tim, tai=tai, llm=llm, tran_trang=4)
    assert len(tai.da_tai) == 4


def test_luu_ban_chup_cho_nguon_lam_bang_chung(tmp_path):
    """Bằng chứng tại thời điểm kiểm — link chết sau 6-12 tháng là chuyện thường."""
    tim, tai, llm = _bo(
        [{"url": "https://www.cdc.gov/x", "ten": "CDC"}],
        {"https://www.cdc.gov/x": (200, TRANG_THAT)},
        LlmGia(nguon=[{"url": "https://www.cdc.gov/x",
                       "trich": "higher risk of all stroke (aHR 1.23)"}]))
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm, thu_muc_chup=tmp_path)
    n = kq.nguon[0]
    assert n.ban_chup and (tmp_path / n.ban_chup).is_file()
    assert TRANG_THAT in (tmp_path / n.ban_chup).read_text(encoding="utf-8")
    assert n.luc, "phải ghi thời điểm kiểm"


def test_llm_hong_thi_bao_loi_ro_chu_khong_nuot():
    class LlmHong(LlmGia):
        def ket_luan(self, doan, trang):
            raise RuntimeError("GLM hết hạn mức")

    tim, tai, llm = _bo(
        [{"url": "https://www.cdc.gov/x", "ten": "CDC"}],
        {"https://www.cdc.gov/x": (200, TRANG_THAT)}, LlmHong())
    with pytest.raises(RuntimeError, match="hết hạn mức"):
        kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)


def test_truy_van_duoc_ghi_lai_de_nguoi_kiem_tay():
    tim, tai, llm = _bo(
        [{"url": "https://www.cdc.gov/x", "ten": "CDC"}],
        {"https://www.cdc.gov/x": (200, TRANG_THAT)}, LlmGia(nguon=[]))
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert kq.truy_van == "WHI artificially sweetened beverages stroke risk"
    assert tim.da_goi == [kq.truy_van]


# ---- sau khi ĐO THẬT 16/09: nhà xuất bản chặn bot -------------------------
def test_nguon_da_co_san_chu_thi_khong_tai_lai():
    """Đo thật: `ahajournals.org` (bài gốc) và `nhlbi.nih.gov` đều trả **403** cho
    mọi lượt tải tự động. Đường đúng cho mảng học thuật là API mở (Europe PMC)
    trả thẳng tóm tắt — có chữ sẵn thì không cào trang nữa, vừa nhanh vừa không
    đụng lớp chặn bot của nhà xuất bản.
    """
    tim = TimGia([{"url": "https://europepmc.org/article/MED/30802187",
                   "ten": "WHI", "text": TRANG_THAT}])
    tai = TaiGia({})          # nếu gọi tới đây là sai
    llm = LlmGia(nguon=[{"url": "https://europepmc.org/article/MED/30802187",
                         "trich": "higher risk of all stroke (aHR 1.23)"}])
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert tai.da_tai == [], "có chữ sẵn thì đừng tải lại"
    assert kq.ket == "dung"


def test_van_tai_nhung_nguon_chua_co_chu():
    tim = TimGia([{"url": "https://europepmc.org/article/MED/1", "ten": "A", "text": TRANG_THAT},
                  {"url": "https://www.cdc.gov/x", "ten": "B"}])
    tai = TaiGia({"https://www.cdc.gov/x": (200, TRANG_THAT)})
    kiem_doan(DOAN, tim=tim, tai=tai, llm=LlmGia(nguon=[]))
    assert tai.da_tai == ["https://www.cdc.gov/x"]


def test_nguon_trung_url_chi_hien_mot_lan():
    """Đo thật 16/09: GLM trả hai mục cùng một URL (hai trích đoạn khác nhau) ->
    thẻ hiện nguồn đó hai lần, người đọc tưởng có hai bằng chứng độc lập."""
    tim, tai, llm = _bo(
        [{"url": "https://www.cdc.gov/x", "ten": "CDC"}],
        {"https://www.cdc.gov/x": (200, TRANG_THAT)},
        LlmGia(nguon=[{"url": "https://www.cdc.gov/x", "trich": "higher risk of all stroke"},
                      {"url": "https://www.cdc.gov/x", "trich": "81,714 postmenopausal women"}]))
    kq = kiem_doan(DOAN, tim=tim, tai=tai, llm=llm)
    assert len(kq.nguon) == 1
    assert "higher risk of all stroke" in kq.nguon[0].trich
    assert "81,714" in kq.nguon[0].trich, "gộp cả hai trích đoạn, không vứt cái thứ hai"
