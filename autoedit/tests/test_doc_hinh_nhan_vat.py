r"""ĐỌC HÌNH để biết NHÂN VẬT — tuổi · chủng tộc · vật thể · cỡ cảnh.

Vì sao cần (đo 12/09): kho 17.039 clip thì 8.524 clip stock **chưa bao giờ được
đọc hình** — `subject` của chúng chỉ là tiêu đề người bán bị xé chữ:

    tieu_de: "Man Counts Money at Glass Table in Office"
    subject: "counts,money,glass,table"        <- không ai xem hình này

Nên tiêu đề nói dối là cả dây chuyền tin theo: `Sunrise at Andes Mountains...
foggy morning` thắng câu "đột quỵ không rải đều trong ngày" nhờ chữ `morning`.

Đã kiểm vision đọc được thật (10 clip, 12/09): 5/5 clip tiêu đề "Senior" ->
`tuoi=older`, 5/5 clip "Family" -> `young`/`mixed`, không cái nào nhầm. Đọc 551
clip khay SH010 mất 8 phút ở 3 luồng, 3 lỗi, và LƯU VĨNH VIỄN nên tập sau gần
như miễn phí.

Nguyên tắc: một clip đọc MỘT LẦN (`doc_nguoi=1`), lỗi một clip không giết cả lô,
và `vat_the` của ref (đã do `doc_canh` ghi) KHÔNG bị ghi đè.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def kho(tmp_path):
    from autoedit.sotra import db as sdb

    conn = sdb.mo(tmp_path / "so_tra.db")
    yield conn
    conn.close()


def _them(conn, cid, **kw):
    from autoedit.sotra import db as sdb

    r = {"id": cid, "nguon": kw.pop("nguon", "envato"),
         "tieu_de": kw.pop("tieu_de", cid), "url_anh": kw.pop("url_anh", "http://x/a.jpg")}
    r.update(kw)
    sdb.them_clip(conn, r)
    return cid


# ------------------------------------------------------------------ cột mới

def test_kho_co_cot_tuoi_chung_toc_doc_nguoi(kho):
    cot = {r[1] for r in kho.execute("PRAGMA table_info(clip)")}
    assert {"tuoi", "chung_toc", "doc_nguoi"} <= cot


# ------------------------------------------------------------------ điền

def test_dien_du_bon_truong(kho):
    from autoedit.sotra import doc_hinh

    _them(kho, "envato:a")
    n = doc_hinh.bo_sung(kho, ["envato:a"], doc=lambda r: {
        "ai": "older woman", "tuoi": "older", "chung_toc": "white",
        "object": "water glass, pill bottle", "co_canh": "close"})
    assert n == 1
    r = kho.execute("SELECT tuoi, chung_toc, vat_the, shot, doc_nguoi, people "
                    "FROM clip WHERE id='envato:a'").fetchone()
    assert r["tuoi"] == "older" and r["chung_toc"] == "white"
    assert "water glass" in r["vat_the"] and r["shot"] == "close"
    assert r["doc_nguoi"] == 1
    assert "older woman" in (r["people"] or "")


def test_doc_MOT_LAN_moi_clip(kho):
    from autoedit.sotra import doc_hinh

    _them(kho, "envato:a")
    goi = []
    d = lambda r: (goi.append(r["id"]), {"tuoi": "older", "chung_toc": "white"})[1]
    doc_hinh.bo_sung(kho, ["envato:a"], doc=d)
    doc_hinh.bo_sung(kho, ["envato:a"], doc=d)
    assert goi == ["envato:a"], "lần hai phải bỏ qua — tiền thật, 1,1s/clip"


def test_mot_clip_loi_KHONG_giet_ca_lo(kho):
    from autoedit.sotra import doc_hinh

    _them(kho, "envato:a")
    _them(kho, "envato:b")

    def d(r):
        if r["id"] == "envato:a":
            raise RuntimeError("403 Forbidden")
        return {"tuoi": "older", "chung_toc": "white"}

    n = doc_hinh.bo_sung(kho, ["envato:a", "envato:b"], doc=d)
    assert n == 1
    assert kho.execute("SELECT doc_nguoi FROM clip WHERE id='envato:a'"
                       ).fetchone()[0] == 0, "clip lỗi phải đọc lại được lần sau"
    assert kho.execute("SELECT tuoi FROM clip WHERE id='envato:b'"
                       ).fetchone()[0] == "older"


def test_KHONG_ghi_de_vat_the_cua_ref(kho):
    """`doc_canh` đã liệt kê vật thể của ref rất kỹ (7.322 clip). Ghi đè là phá
    dữ liệu đắt tiền đã có."""
    from autoedit.sotra import doc_hinh

    _them(kho, "ref:v:1", nguon="ref", url_anh="", path_local="",
          vat_the="boat, river, buildings, sky")
    doc_hinh.bo_sung(kho, ["ref:v:1"], doc=lambda r: {
        "tuoi": "older", "chung_toc": "white", "object": "xxx"})
    r = kho.execute("SELECT vat_the, tuoi FROM clip WHERE id='ref:v:1'").fetchone()
    assert r["vat_the"] == "boat, river, buildings, sky"
    assert r["tuoi"] == "older", "tuổi vẫn phải được ghi"


# ------------------------------------------------------------------ chuẩn hoá

@pytest.mark.parametrize("tho, chuan", [
    ("older", "older"), ("elderly", "older"), ("SENIOR", "older"), ("old", "older"),
    ("young adult", "young"), ("", ""), ("chả biết", ""),
])
def test_chuan_hoa_tuoi(tho, chuan):
    from autoedit.sotra import doc_hinh

    assert doc_hinh.chuan_tuoi(tho) == chuan


def test_gia_tri_la_KHONG_ghi_bua(kho):
    """Model trả chữ lạ thì để TRỐNG, không bịa `older` — ghi sai một lần là
    cửa nhân vật sai suốt (clip lưu vĩnh viễn)."""
    from autoedit.sotra import doc_hinh

    _them(kho, "envato:a")
    doc_hinh.bo_sung(kho, ["envato:a"], doc=lambda r: {
        "tuoi": "khoảng 4 người", "chung_toc": "cam", "co_canh": "toàn cảnh"})
    r = kho.execute("SELECT tuoi, chung_toc, shot, doc_nguoi FROM clip "
                    "WHERE id='envato:a'").fetchone()
    assert r["tuoi"] == "" and r["chung_toc"] == "" and not r["shot"]
    assert r["doc_nguoi"] == 1, "đã đọc rồi thì đừng đọc lại"


# ------------------------------------------------------------------ FTS

def test_vat_the_moi_vao_FTS(kho):
    """Đọc hình xong phải TRA RA ĐƯỢC bằng vật thể mới — không thì đọc để đấy."""
    from autoedit.sotra import doc_hinh

    _them(kho, "envato:a", tieu_de="Man at Table")
    doc_hinh.bo_sung(kho, ["envato:a"], doc=lambda r: {
        "tuoi": "older", "chung_toc": "white", "object": "sphygmomanometer"})
    hit = kho.execute("SELECT id FROM clip_fts WHERE clip_fts MATCH "
                      "'sphygmomanometer'").fetchall()
    assert [r[0] for r in hit] == ["envato:a"]


# ------------------------------------------------- tải ảnh phải có User-Agent
# Chạy thật 13/09: đọc 692 clip vừa hút -> envato 322/322 ĐƯỢC, pexels 0/191 và
# pixabay 0/179 ăn **403 Forbidden**. CDN của hai trang đó chặn urllib trần;
# `hut.py` từ đầu đã gửi UA giả trình duyệt (`_get`), còn `doc_hinh` thì không.
# Envato không chặn nên hỏng CHỈ MỘT PHẦN — kiểu lỗi dễ tưởng là "xong rồi".

def test_tai_anh_gui_User_Agent():
    from autoedit.sotra import doc_hinh

    da_goi = {}

    def mo_gia(req, timeout=None):
        da_goi["ua"] = req.get_header("User-agent")
        raise RuntimeError("dừng ở đây — chỉ cần biết header")

    import urllib.request
    that = urllib.request.urlopen
    urllib.request.urlopen = mo_gia
    try:
        with pytest.raises(RuntimeError):
            doc_hinh.anh_cua({"url_anh": "https://images.pexels.com/x.jpeg"})
    finally:
        urllib.request.urlopen = that
    assert da_goi.get("ua"), "thiếu User-Agent -> pexels/pixabay trả 403"
    assert "Mozilla" in da_goi["ua"]
