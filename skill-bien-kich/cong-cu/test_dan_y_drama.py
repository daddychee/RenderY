"""Test dan_y_drama.py. Chạy: py -3 cong-cu/test_dan_y_drama.py (unittest, không cần pytest)."""
import contextlib
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import dan_y_drama as dy  # noqa: E402
from kiem_drama import gop  # noqa: E402

MOC = "\n".join(f"| N{k:02d} | {(k - 1) * 2}–{k * 2} | Ngày {1 + k // 4} | Đoạn {k} | Việc mốc {k}. | — | KB{k} |" for k in range(1, 11))
DAN_Y = f"""# Phim thử
Loại phim: drama_thoai
Seedance: 100%
Thể loại: drama-da-den · Độ dài: 20 phút · Tỉ lệ: 16:9

## Tựa và thumbnail
Tựa: The Maid Who Saved Him
Thumbnail: Nia mặc đồng phục, giơ tay chắn
Phim mẫu: X · Thủ pháp giữ: Y · Khác phim mẫu ở: Z
Trả tựa ở: N02

## Logline
Nia cứu bà lão.

## Bí mật khán giả biết trước
Bà là mẹ tỷ phú; khán giả biết ở N01; vỡ ở N09.

## Nhân vật và bối cảnh
| Tên (dùng ở Khung) | Vai | Tuổi, ngoại hình một câu | Giọng (tuổi, độ trầm, chất giọng) |
|---|---|---|---|
| Nia | nữ chính | 24, NGOAIHINH | nữ 24, ấm |
| Damon | nam chính | 35, cao | nam 35, trầm |

### Nơi
| Nơi (tên dùng ở tiêu đề cảnh) | Một câu tả |
|---|---|
| Shop | tiệm kính |

## Cụm cố định
| Mã | Tên | Cụm tiếng Anh (nguyên văn) | Ghi chú |
|---|---|---|---|
| NV01 | Nia (she) | Beautiful Black woman about 24, CUMTIENGANH | |
| NV02 | Damon (he) | Handsome Black man in his early thirties, grey suit | |

## Kẻ ác từng vòng
| Kẻ ác | Vào ở | Bị xử ở | Bị xử thế nào (tăng bậc) |
|---|---|---|---|
| Gerald | N01 | N05 | bị đuổi |

## Mở phim (0–4 phút)
| Giây | Ai làm gì | Câu thoại hay lời nghĩ chính |
|---|---|---|
| 0:00–0:30 | Nia chắn cú tát | "Not again." |

## Bảng mốc
| Mốc | Phút | Ngày | Đoạn khung | Việc (tối đa 2 câu) | Ức trả ở | Mã kho |
|---|---|---|---|---|---|---|
{MOC}

## Gieo và gặt
| Mã | Loại | Điều | Gieo ở (bằng gì) | Gặt ở |
|---|---|---|---|---|
| G01 | lật | Bà nói quên ví | N01, thoại bà | N03 |
| G02 | dẫn sai | Khán giả đoán A; thật là B | N02, lời nghĩ | N04 |
| G03 | dẫn sai | Đoán C; thật là D | N06 | N08 |
| G04 | vết | Nia rách khóe môi trái | N03 | tới N07 |
| G05 | biết | Damon biết vụ cược | N02 | N09 |
| G06 | phi lý | Bà chọn vợ cho cháu | N06, thoại | — |
| G07 | vật | Huy hiệu D.H. | N04 | N08, N10 |
| G08 | vết | Damon bầm tay phải | N01 | tới N03 |

## Phần
| Phần | Tên | Mốc | Phút |
|---|---|---|---|
| 1 | Bà lão | N01–N05 | 10 |
| 2 | Huy hiệu | N06–N10 | 10 |
"""

CLIP = """### {ma} · clip
Máy: Seedance 10s
Khung: {khung}
Hình: {hinh}
Thoại: Nia (khẽ): "Hi there."
"""
GG1 = "G01 P001, G02 P002, G04 P002, G05 P001, G07 P002, G08 P001"


def phan1(gg: str | None = GG1, hinh: str = "Shot 1 trung rộng quầy, Nia đứng bên trái.", khung: str = "Nia") -> str:
    ghi = "## Ghi chú nối\n- Mã cuối: P002\n" + (f"- Gieo, gặt: {gg}\n" if gg is not None else "")
    return ("# Phần 1 · Bà lão · 10 phút\n\n## C001 · Shop · sáng · N01\nCó mặt: Nia, Damon\n\n"
            + CLIP.format(ma="P001", khung=khung, hinh=hinh) + "\n" + CLIP.format(ma="P002", khung="Nia", hinh="Nia cười.") + "\n" + ghi)


def doi(vb: str, cu: str, moi: str) -> str:
    assert cu in vb, cu
    return vb.replace(cu, moi, 1)


def kiem(vb: str) -> tuple[list[str], list[str]]:
    loi, nhac, _ = dy.kiem_dan_y(vb)
    return [x for _, x in loi], [x for _, x in nhac]


class KiemDanY(unittest.TestCase):
    def co(self, vb: str, chu: str, nhac: bool = False):
        loi, n = kiem(vb)
        ds = n if nhac else loi
        self.assertTrue(any(chu in x for x in ds), f"không thấy '{chu}' trong {ds}")

    def test_mau_sach(self):
        self.assertEqual(kiem(DAN_Y), ([], []))

    def test_thieu_muc(self):
        self.co(doi(DAN_Y, "## Mở phim (0–4 phút)", "## Mo dau"), "thiếu mục '## Mở phim'")
        self.co(doi(DAN_Y, "### Nơi", "### Chỗ"), "thiếu mục '### Nơi'")
        self.co(doi(DAN_Y, "Ngày", "Ngay"), "thiếu cột 'Ngày'")
        self.co(doi(DAN_Y, "Trả tựa ở: N02", ""), "thiếu dòng 'Trả tựa ở")

    def test_tra_tua_qua_4_phut(self):
        self.co(doi(DAN_Y, "Trả tựa ở: N02", "Trả tựa ở: N04"), "4 phút đầu")
        self.assertEqual(kiem(doi(DAN_Y, "Trả tựa ở: N02", "Trả tựa ở: N03"))[0], [])  # N03 bắt đầu phút 4

    def test_hai_moc_cach_qua_5_phut(self):
        self.co(doi(DAN_Y, "| N04 | 6–8 |", "| N04 | 11–12 |"), "N03 → N04 cách 7 phút")

    def test_phan_dai_va_phim_ngan(self):
        vb = doi(DAN_Y, "| N01–N05 | 10 |", "| N01–N05 | 13 |")
        self.co(vb, "Phần 1: 13 phút")
        self.assertEqual(kiem(doi(vb, "Độ dài: 20 phút", "Độ dài: 8 phút"))[0], [])

    def test_phan_khong_dan_sai(self):
        vb = doi(DAN_Y, "| G03 | dẫn sai |", "| G03 | lật |")
        self.co(vb, "Phần 2: không có dòng 'dẫn sai'")
        self.assertEqual(kiem(doi(vb, "Độ dài: 20 phút", "Độ dài: 9 phút"))[0], [])

    def test_moc_khong_thuoc_phan(self):
        self.co(doi(DAN_Y, "| N06–N10 | 10 |", "| N06–N09 | 10 |"), "N10 không thuộc phần nào")

    def test_gieo_gat(self):
        self.co(doi(DAN_Y, "| N01, thoại bà | N03 |", "| N03, thoại bà | N02 |"), "G01: gặt ở N02 trước gieo ở N03")
        self.co(doi(DAN_Y, "| G07 | vật |", "| G07 | twist |"), "loại 'twist' lạ")
        self.co(doi(DAN_Y, "khóe môi trái", "khóe môi"), "G04: vết thiếu trái hay phải")
        self.co(doi(DAN_Y, "| N03 | tới N07 |", "| N03 | N07 |"), "G04: vết ghi Gặt ở 'tới Nxx'")
        self.assertEqual(kiem(doi(DAN_Y, "khóe môi trái", "ướt cả người"))[0], [])
        self.co(doi(DAN_Y, "| N08, N10 |", "| N08, N12 |"), "G07: mốc N12 không có ở Bảng mốc")
        self.co(doi(DAN_Y, "| N04 | N08, N10 |", "| thoại, N04 | N08, N10 |"), "phải bắt đầu bằng mã mốc")
        self.co(doi(DAN_Y, "| N08, N10 |", "| sau cùng |"), "Gặt ở 'sau cùng' sai dạng")

    def test_cum_co_dinh(self):
        self.co(doi(DAN_Y, "Beautiful Black woman about 24, ", "Beautiful Black woman, "), "NV01 Nia: cụm thiếu tuổi")
        self.co(doi(DAN_Y, "grey suit", "grey suit, dark circles"), "dark circles", nhac=True)

    def test_nhac(self):
        self.co(doi(DAN_Y, "Việc mốc 3.", 'Một. Hai: "A. B." Ba!'), "N03: Việc 3 câu", nhac=True)
        self.assertEqual(dy.so_cau('Gerald nói: "Đi. Ngay." Nia đi.'), 2)
        self.assertEqual(dy.so_cau('Nợ 48.000 đô, gọi "nhét vòng" rồi đi'), 1)
        self.co(doi(DAN_Y, "Nia cứu bà lão.", "chữ " * 7000), "token", nhac=True)
        self.assertEqual(kiem(doi(DAN_Y, "CUMTIENGANH", "x" * 30000))[1], [])  # Cụm cố định không tính


class Doc(unittest.TestCase):
    def setUp(self):
        self.d = dy.doc_dan_y(DAN_Y)

    def ma(self, ra: list[str], dau: str) -> list[str]:
        return [x.split("|")[1].strip() for x in ra if re.match(rf"\| {dau}\d\d ", x)]

    def test_phan_1(self):
        ra = dy.cat_phan(self.d, 1)
        vb = "\n".join(ra)
        self.assertTrue(ra[0] == "# Phim thử" and "Seedance: 100%" in vb)
        for chu in ("## Tựa và thumbnail", "## Logline", "## Bí mật", "### Nơi", "## Kẻ ác", "## Mở phim", "| 1 | Bà lão |"):
            self.assertIn(chu, vb)
        self.assertNotIn("NGOAIHINH", vb)                  # bỏ cột ngoại hình
        self.assertNotIn("CUMTIENGANH", vb)                # không Cụm cố định
        self.assertIn("| Nia | nữ chính | nữ 24, ấm |", vb)
        self.assertEqual(self.ma(ra, "N"), [f"N{k:02d}" for k in range(1, 7)])          # N01–N05 và một mốc sau
        self.assertEqual(self.ma(ra, "G"), ["G01", "G02", "G04", "G05", "G07", "G08"])
        self.assertNotIn("| 2 | Huy hiệu |", vb)

    def test_phan_2_vet_con_hieu_luc(self):
        ra = dy.cat_phan(self.d, 2)
        vb = "\n".join(ra)
        self.assertNotIn("## Mở phim", vb)
        self.assertEqual(self.ma(ra, "N"), [f"N{k:02d}" for k in range(5, 11)])          # một mốc trước, N06–N10
        # G04 vết gieo N03 tới N07: còn hiệu lực; G08 vết tới N03 đã hết; G01, G02 gieo, gặt ở phần 1
        self.assertEqual(self.ma(ra, "G"), ["G03", "G04", "G05", "G06", "G07"])

    def test_biet_mang_sang(self):
        d = dy.doc_dan_y(doi(DAN_Y, "| N02 | N09 |", "| N02 | — |"))   # biết từ N02, không mốc gặt
        self.assertIn("G05", self.ma(dy.cat_phan(d, 2), "G"))

    def test_phan_khong_co(self):
        self.assertIsNone(dy.cat_phan(self.d, 9))


class Phan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self.tmp.name) / "kich-ban"
        self.kb.mkdir()
        (self.kb / "00-dan-y.md").write_text(DAN_Y, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def chay(self, *arg) -> tuple[int, str]:
        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            kq = dy.main([str(a) for a in arg])
        return kq, b.getvalue()

    def ghi(self, ten: str, vb: str) -> Path:
        (f := self.kb / ten).write_text(vb, encoding="utf-8")
        return f

    def test_dau_chep_phan_dau(self):
        self.ghi("phan-01.md", "# Cũ\nrác\n\n" + phan1())
        kq, ra = self.chay("dau", self.kb)
        vb = (self.kb / "phan-01.md").read_text(encoding="utf-8")
        self.assertEqual(kq, 0, ra)
        self.assertTrue(vb.startswith("# Phim thử\nLoại phim: drama_thoai"))
        self.assertIn("## Cụm cố định", vb)
        self.assertIn("### Nơi", vb)
        for chu in ("rác", "Tựa và thumbnail", "Gieo và gặt", "## Logline"):
            self.assertNotIn(chu, vb)
        self.assertIn("# Phần 1 · Bà lão", vb)

    def test_dau_thieu_file(self):
        self.assertEqual(self.chay("dau", self.kb)[0], 1)

    def dau_phan1(self, **kw) -> Path:
        self.ghi("phan-01.md", phan1(**kw))
        self.chay("dau", self.kb)
        return self.kb / "phan-01.md"

    def test_phan_sach(self):
        kq, ra = self.chay("phan", self.dau_phan1())
        self.assertEqual(kq, 0, ra)
        self.assertNotIn("NHẮC:", ra)

    def test_gieo_gat(self):
        kq, ra = self.chay("phan", self.dau_phan1(gg=GG1.replace(", G07 P002", "")))
        self.assertIn("G07 (vật", ra)
        kq, ra = self.chay("phan", self.dau_phan1(gg=GG1.replace("G07 P002", "G07 P099")))
        self.assertIn("G07 trỏ P099", ra)
        kq, ra = self.chay("phan", self.dau_phan1(gg=None))
        self.assertIn("thiếu dòng '- Gieo, gặt:", ra)
        kq, ra = self.chay("phan", self.dau_phan1(gg=GG1 + ", G99 P001"))
        self.assertIn("G99 không có ở bảng", ra)
        self.assertEqual(kq, 1)

    def test_vet_o_hinh(self):
        for hinh, nhac in (("Nia rách khóe môi, cười.", True), ("Nia rách khóe môi trái.", False), ("Nia ngồi băng ghế.", False), ("Mép túi vải rách toạc, máu rút khỏi mặt Gerald.", False),
                           ("Damon bên trái khung. Nia bầm má.", True)):
            ra = self.chay("phan", self.dau_phan1(hinh=hinh))[1]
            self.assertEqual("NHẮC:" in ra and "trái hay phải" in ra, nhac, hinh)

    def test_nhip_dien_va_dinh_vi(self):
        canh = "".join(CLIP.format(ma=f"P{k:03d}", khung="Nia", hinh="Nia nói.").replace('"Hi there."', '"' + "word " * 25 + '"')
                       for k in range(1, 4))
        vb = "# Phần 1 · Bà lão · 10 phút\n\n## C001 · Shop · sáng · N01\nCó mặt: Nia\n\n" + canh
        nhac = dy.kiem_nhip(vb)
        self.assertTrue(any("không nhịp diễn" in x for x in nhac), nhac)
        self.assertTrue(any("không có shot định vị" in x for x in nhac), nhac)
        self.assertFalse(any("giây có lời" in x for x in nhac), nhac)     # dưới 20 clip không đo %
        day = "## C002 · Shop · trưa · N02\nCó mặt: Nia\n\n" + "".join(
            CLIP.format(ma=f"P{k:03d}", khung="Nia", hinh="Shot 1 toàn quầy.").replace('"Hi there."', '"' + "word " * 25 + '"')
            for k in range(4, 25))
        self.assertTrue(any("gần toàn lời" in x for x in dy.kiem_nhip(vb + day)))

    def test_ten_khung_khong_co_cum(self):
        kq, ra = self.chay("phan", self.dau_phan1(khung="Nia, Otis"))
        self.assertEqual(kq, 1)
        self.assertIn("'Otis' ở Có mặt/Khung không có", ra)

    def test_phan_sau_va_ban_gop(self):
        p1 = self.dau_phan1()
        gg2 = "G03 P003, G06 P003, G07 P004, G05 P004"
        p2 = self.ghi("phan-02.md", "# Phần 2 · Huy hiệu · 10 phút\n\n## C002 · Shop · tối · N06\nCó mặt: Nia, Damon\n\n"
                      + CLIP.format(ma="P003", khung="Nia", hinh="Nia đi.") + "\n" + CLIP.format(ma="P004", khung="Damon", hinh="Damon nhìn.")
                      + f"\n## Ghi chú nối\n- Gieo, gặt: {gg2}\n")
        kq, ra = self.chay("phan", p2)
        self.assertEqual(kq, 0, ra)
        self.assertIn("Cụm cố định: 2 dòng NV", ra)                   # phần đầu lấy của phan-01.md
        kb = Path(self.tmp.name) / "kich-ban.md"
        kb.write_text(gop([p1.read_text(encoding="utf-8"), p2.read_text(encoding="utf-8")]), encoding="utf-8")
        kq, ra = self.chay("phan", kb)
        self.assertEqual(kq, 0, ra)
        self.assertIn("Gieo, gặt: 10 mã đủ clip", ra)
        self.ghi("00-dan-y.md", doi(DAN_Y, "| Nia | nữ chính |", "| Nia | nữ chính mới |"))
        self.assertIn("phần đầu khác dàn ý", self.chay("phan", kb)[1])

    def test_danh_ma_sau_khi_chen_tran(self):
        p1 = self.ghi("phan-01.md", "# Phần 1 · A · 10 phút\n\n## C001 · Shop · sáng · N01\n" + CLIP.format(ma="P001", khung="Nia", hinh="x")
                      + "\n## Thiết kế trận T1: Tiệm · cỡ xô xát · P002-b–P002-c\n| Cảnh | Bậc |\n|---|---|\n| P02-b | chạm đầu |\n"
                      + "## C001-b · Shop · sáng · N02\n" + CLIP.format(ma="P002-b", khung="Nia", hinh="x")
                      + CLIP.format(ma="P002-c", khung="Nia", hinh="x") + CLIP.format(ma="P002", khung="Nia", hinh="x")
                      + "\n## Ghi chú nối\n- Mã cuối: P002 · C001-b · N02\n- Gieo, gặt: G01 P002, G02 P002-b\n")
        p2 = self.ghi("phan-02.md", "# Phần 2 · B · 10 phút\n\n## C002 · Shop · tối · N06\n" + CLIP.format(ma="P003", khung="Nia", hinh="P0030 P003x")
                      + "\n## Ghi chú nối\n- Mã cuối: P003 · C002 · N06\n")
        kq, ra = self.chay("danh-ma", self.kb)
        self.assertEqual(kq, 0, ra)
        self.assertIn("phan-01 P001 C001, phan-02 P005 C003", ra)
        v1, v2 = p1.read_text(encoding="utf-8"), p2.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^#{2,3} ([PC]\d+)", v1, re.M), ["C001", "P001", "C002", "P002", "P003", "P004"])
        self.assertIn("cỡ xô xát · P002–P003\n", v1)
        self.assertIn("| P002 | chạm đầu |", v1)                         # P02-b cùng mã với P002-b
        self.assertIn("Mã cuối: P004 · C002 · N02", v1)
        self.assertIn("Gieo, gặt: G01 P004, G02 P002", v1)
        self.assertIn("## C003 · Shop", v2)
        self.assertIn("Hình: P0030 P003x", v2)                              # chữ không phải mã giữ nguyên
        self.assertIn("Mã cuối: P005 · C003", v2)
        self.assertEqual(self.chay("danh-ma", self.kb)[1].count("0/2 file"), 1)   # chạy lại không đổi gì

    def test_danh_ma_trung_khong_ghi(self):
        vb = "# Phần 1 · A · 10 phút\n\n## C001 · Shop · sáng · N01\n" + CLIP.format(ma="P001", khung="Nia", hinh="x") * 2
        f = self.ghi("phan-01.md", vb)
        kq, ra = self.chay("danh-ma", self.kb)
        self.assertEqual(kq, 1)
        self.assertIn("mã P001 trùng", ra)
        self.assertEqual(f.read_text(encoding="utf-8"), vb)

    def test_lenh_kiem_doc(self):
        kq, ra = self.chay("kiem", self.kb)
        self.assertEqual(kq, 0, ra)
        self.assertIn("10 mốc, 2 phần, 8 dòng", ra)
        kq, ra = self.chay("doc", self.kb, 2)
        self.assertEqual(kq, 0)
        self.assertIn("<!-- dan_y_drama doc phần 2", ra)
        self.assertEqual(self.chay("doc", self.kb, 5)[0], 1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
