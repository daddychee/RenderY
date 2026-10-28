"""Test dan_y.py, doc_phan.py --phan, danh_lai_ma.py (dòng Gieo, gặt phần). Chạy: py -3 cong-cu/test_dan_y.py (unittest, không cần pytest)."""
import contextlib
import io
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CC = Path(__file__).resolve().parent
sys.path.insert(0, str(CC))
import dan_y as dy  # noqa: E402

NHIP = "\n".join(f"| N{k:02d} | {(k - 1) * 8} | Diễn biến | 10 | Sự kiện nhịp {k} (KB{k}) | {'–' if k == 1 else f'N{k - 1:02d}'} | lo | {2 + k % 3} |"
                 for k in range(1, 13))
NHIP_MD = f"""# Phim thử
Thể loại: fantasy-drama · Dài: 20 phút · Lời bình: không · Thoại: ít

## Tựa và thumbnail
Tựa: The Dragon Who Came Back
Thumbnail: con rồng dang cánh che cô bé
Phim mẫu: X · Thủ pháp giữ: Y · Khác phim mẫu ở: Z
Trả tựa ở: N02

## Logline
Cô bé cứu rồng.

## Ba hồi
- Hồi 1 (N01–N04, ~33%): mở.
- Hồi 2 (N05–N08, ~33%): giữa.
- Hồi 3 (N09–N12, ~34%): cuối.

## Bảng nhịp
| Mã | % | Loại | Cảnh | Sự kiện | Vì nhịp | Cảm xúc khán giả | Mức |
|---|---|---|---|---|---|---|---|
{NHIP}

## Gieo và gặt
| Mã | Loại | Điều | Gieo ở (bằng gì) | Gặt ở |
|---|---|---|---|---|
| G01 | lật | Sinh vật nhớ tiếng còi | N01, cô thổi còi | N03 |
| G02 | dẫn sai | Khán giả đoán A; thật là B | N02, lời nghĩ | N04 |
| G03 | dẫn sai | Đoán C; thật là D | N05 | N07 |
| G04 | vết | Rồng rách cánh trái | N03, cú cào | tới N06 |
| G05 | biết | Cô bé biết tên rồng | N02 | N10 |
| G06 | phi lý | Rồng chọn cô bé | N06, thoại | — |
| G07 | vật | Chiếc còi bạc | N04 | N08, N10 |
| G08 | dẫn sai | Đoán E; thật là F | N09 | N11 |
| G09 | vết | Cô bé bầm gối phải | N01 | tới N02 |

## Mô típ
| Mô típ | Loại | Gieo ở | Lặp ở | Trả ở |
|---|---|---|---|---|
| Tiếng còi | âm thanh | N01 | N04, N08 | N10 |

## Cụm cố định
| Mã | Tên | Cụm tiếng Anh (nguyên văn) | Ghi chú |
|---|---|---|---|
| NV01 | Mia (she) | a girl about 9 | từ N03 rách áo |
| Vật | Còi phần 1 | VATPHAN1 silver whistle | N01–N04 |
| Vật | Còi phần 3 | VATPHAN3 broken whistle | N10 |

## Phần
| Phần | Hồi | Nhịp | Phút | Clip |
|---|---|---|---|---|
| 1 | 1 | N01–N04 | 6,7 | 40 |
| 2 | 2 | N05–N08 | 6,7 | 40 |
| 3 | 3 | N09–N12 | 6,7 | 40 |
"""

GG1 = "G01 P01, G01 P03, G02 P02, G02 P04, G04 P03, G05 P02, G07 P04, G09 P01"


def canh(k: int, n: int, hinh: str = "Mia đứng bên suối.") -> str:
    return (f"## P{k:02d} · cảnh {k} · 15s · N{n:02d}\n- Mục đích kể chuyện: việc · cảnh {k}  |  Bối cảnh, thời điểm: DD01 suối, sáng  |  "
            f"Có mặt: NV01\n- Hành động theo nhịp: 0–15s trung: {hinh}\n\n")


def hoi1(gg: str | None = GG1, hinh: str = "Mia đứng bên suối.") -> str:
    return ("# Hồi 1: Mở\n\n" + canh(1, 1, hinh) + canh(2, 2) + canh(3, 3) + canh(4, 4)
            + "## Bảng trạng thái liên tục\n| Nhân vật | Từ | Tới | Cụm tiếng Anh cố định |\n|---|---|---|---|\n| NV01 | P03 | hết phim | torn sleeve |\n"
            + "## Để viết hồi sau\n- Tóm tắt hồi: P01–P04 mở.\n" + (f"- Gieo, gặt phần 1: {gg}\n" if gg is not None else ""))


def doi(vb: str, cu: str, moi: str) -> str:
    assert cu in vb, cu
    return vb.replace(cu, moi, 1)


def kiem(vb: str) -> tuple[list[str], list[str]]:
    loi, nhac, _ = dy.kiem_nhip(vb)
    return [x for _, x in loi], [x for _, x in nhac]


class Kiem(unittest.TestCase):
    def co(self, vb: str, chu: str, nhac: bool = False):
        loi, n = kiem(vb)
        ds = n if nhac else loi
        self.assertTrue(any(chu in x for x in ds), f"không thấy '{chu}' trong {ds}")

    def test_mau_sach(self):
        self.assertEqual(kiem(NHIP_MD), ([], []))

    def test_thieu_muc(self):
        self.co(doi(NHIP_MD, "## Phần\n", "## Phan\n"), "thiếu mục '## Phần'")
        self.co(doi(NHIP_MD, "## Gieo và gặt", "## Gieo"), "thiếu mục '## Gieo và gặt'")
        self.co(doi(NHIP_MD, "Thumbnail: con", "Ảnh: con"), "thiếu dòng 'Thumbnail")
        self.co(doi(NHIP_MD, "Trả tựa ở: N02", ""), "thiếu dòng 'Trả tựa ở")
        self.co(doi(NHIP_MD, "| Phần | Hồi | Nhịp | Phút | Clip |", "| Phần | Hồi | Nhịp | Phút | Số |"), "thiếu cột 'Clip'")

    def test_tra_tua(self):
        self.co(doi(NHIP_MD, "Trả tựa ở: N02", "Trả tựa ở: N99"), "Trả tựa ở: phải là mã nhịp")
        self.co(doi(NHIP_MD, "Trả tựa ở: N02", "Trả tựa ở: sau"), "Trả tựa ở: phải là mã nhịp")

    def test_gieo_gat(self):
        self.co(doi(NHIP_MD, "| N01, cô thổi còi | N03 |", "| N03, cô thổi còi | N02 |"), "G01: gặt ở N02 trước gieo ở N03")
        self.co(doi(NHIP_MD, "| G07 | vật |", "| G07 | twist |"), "loại 'twist' lạ")
        self.co(doi(NHIP_MD, "cánh trái", "cánh"), "G04: vết thiếu trái hay phải")
        self.assertEqual(kiem(doi(NHIP_MD, "cánh trái", "ướt cả người"))[0], [])
        self.co(doi(NHIP_MD, "| N03, cú cào | tới N06 |", "| N03, cú cào | N06 |"), "G04: vết ghi Gặt ở 'tới Nxx'")
        self.co(doi(NHIP_MD, "| N08, N10 |", "| N08, N14 |"), "G07: nhịp N14 không có")
        self.co(doi(NHIP_MD, "| N04 | N08, N10 |", "| còi, N04 | N08, N10 |"), "phải bắt đầu bằng mã nhịp")
        self.co(doi(NHIP_MD, "| N08, N10 |", "| sau cùng |"), "Gặt ở 'sau cùng' sai dạng")

    def test_phan_thuoc(self):
        self.co(doi(NHIP_MD, "| N09–N12 |", "| N09–N11 |"), "N12 không thuộc phần nào")
        self.co(doi(NHIP_MD, "| N05–N08 |", "| N04–N08 |"), "N04 thuộc nhiều phần")
        self.co(doi(NHIP_MD, "| N01–N04 | 6,7 | 40 |", "| N01, N02, N04 | 6,7 | 40 |"), "các nhịp không liền")
        self.co(doi(NHIP_MD, "| N09–N12 |", "| N09–N13 |"), "nhịp N13 không có")

    def test_phan_trum_hoi(self):
        vb = doi(doi(NHIP_MD, "Hồi 1 (N01–N04", "Hồi 1 (N01–N03"), "Hồi 2 (N05–N08", "Hồi 2 (N04–N08")
        self.co(vb, "Phần 1 trùm hồi 1, 2")
        self.co(vb, "cột Hồi ghi 1, theo Ba hồi là 1, 2", nhac=True)
        vb = doi(doi(NHIP_MD, "Hồi 1 (N01–N04", "Hồi 1 (N01–N02"), "Hồi 2 (N05–N08", "Hồi 2 (N03–N08")
        self.assertFalse(any("trùm" in x for x in kiem(vb)[0]))      # hồi 1 dưới 5 phút

    def test_phan_phut_va_clip(self):
        vb = doi(NHIP_MD, "| N01 | 0 | Diễn biến | 10 |", "| N01 | 0 | Diễn biến | 30 |")
        self.co(vb, "Phần 1: 10,0 phút")
        self.co(vb, "Phần 1: cột Clip '40' lệch tổng cột Cảnh 60")
        self.assertFalse(any("phút" in x for x in kiem(doi(vb, "Dài: 20 phút", "Dài: 8 phút"))[0]))   # phim ngắn miễn
        self.co(doi(NHIP_MD, "| N05 | 32 | Diễn biến | 10 |", "| N05 | 32 | Diễn biến | mười |"), "cột Cảnh 'mười'")

    def test_nhac(self):
        self.co(doi(NHIP_MD, "| G08 | dẫn sai |", "| G08 | lật |"), "Phần 3: không có dòng 'dẫn sai'", nhac=True)
        self.co(doi(NHIP_MD, "Sự kiện nhịp 3 (KB3)", 'Một. Hai: "A. B." Ba!'), "N03: Sự kiện 3 câu", nhac=True)
        self.assertEqual(dy.cau_su_kien("Mia khóc (KB01, KB02). Rồng tới (nhắc: chiếc còi. Ở N01)"), 2)
        cu = NHIP_MD.replace("| Mã | % | Loại | Cảnh | Sự kiện | Vì nhịp | Cảm xúc khán giả | Mức |",
                             "| Mã | % | Loại | Cảnh | Sự kiện | Vì nhịp | Cảm xúc khán giả | Mức | Gieo | Trả ở |")
        self.co(cu, "còn cột Gieo, Trả ở", nhac=True)


class Lenh(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.phim = Path(self.tmp.name) / "phim-thu"
        self.kb = self.phim / "kich-ban"
        self.kb.mkdir(parents=True)
        self.ghi("00-nhip.md", NHIP_MD)

    def tearDown(self):
        self.tmp.cleanup()

    def ghi(self, ten: str, vb: str) -> Path:
        (f := self.kb / ten).write_text(vb, encoding="utf-8")
        return f

    def chay(self, *arg) -> tuple[int, str]:
        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            kq = dy.main([str(a) for a in arg])
        return kq, b.getvalue()

    def chay_ngoai(self, tep: str, *arg) -> tuple[int, str]:
        r = subprocess.run([sys.executable, str(CC / tep), *map(str, arg)], capture_output=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr

    def test_kiem(self):
        kq, ra = self.chay("kiem", self.kb)
        self.assertEqual(kq, 0, ra)
        self.assertIn("12 nhịp (20,0 phút theo cột Cảnh), 3 phần", ra)
        self.ghi("00-nhip.md", doi(NHIP_MD, "| G07 | vật |", "| G07 | twist |"))
        self.assertEqual(self.chay("kiem", self.kb / "00-nhip.md")[0], 1)

    def test_phan_sach(self):
        f = self.ghi("hoi-1.md", hoi1())
        kq, ra = self.chay("phan", f, "--phan", 1)
        self.assertEqual(kq, 0, ra)
        self.assertNotIn("NHẮC:", ra)
        self.assertIn("Gieo, gặt: 6/6 mã đủ cảnh", ra)
        self.assertEqual(self.chay("phan", "--phan", 1, f)[0], 0)          # thứ tự tham số tự do

    def test_phan_loi(self):
        f = self.ghi("hoi-1.md", hoi1(GG1.replace(", G07 P04", "")))
        self.assertIn("G07 (vật", self.chay("phan", f, "--phan", 1)[1])
        f = self.ghi("hoi-1.md", hoi1(GG1.replace("G07 P04", "G07 P09")))
        self.assertIn("G07 trỏ P09, các hồi không có", self.chay("phan", f, "--phan", 1)[1])
        f = self.ghi("hoi-1.md", hoi1(GG1 + ", G99 P01"))
        kq, ra = self.chay("phan", f, "--phan", 1)
        self.assertEqual(kq, 1)
        self.assertIn("G99 không có ở bảng", ra)
        f = self.ghi("hoi-1.md", hoi1(GG1 + ", G03"))
        self.assertIn("G03 thiếu mã cảnh", self.chay("phan", f, "--phan", 1)[1])
        f = self.ghi("hoi-1.md", hoi1(None))
        self.assertIn("thiếu dòng '- Gieo, gặt phần 1:", self.chay("phan", f, "--phan", 1)[1])
        self.assertIn("không có phần 7", self.chay("phan", f, "--phan", 7)[1])

    def test_phan_canh_khac_nhip(self):
        self.ghi("hoi-2.md", "# Hồi 2: Giữa\n\n" + canh(5, 5) + "## Để viết hồi sau\n- Tóm tắt hồi: x\n")
        f = self.ghi("hoi-1.md", hoi1(GG1.replace("G07 P04", "G07 P05")))
        self.assertIn("G07 trỏ P05, cảnh không mang nhịp của phần 1", self.chay("phan", f, "--phan", 1)[1])
        f = self.ghi("hoi-1.md", hoi1(GG1.replace("G07 P04", "G07 P004")))       # 3 chữ số
        self.assertEqual(self.chay("phan", f, "--phan", 1)[0], 0)

    def test_vet_khong_ben(self):
        for hinh, nhac in (("Mia rách khóe môi, cười.", True), ("Mia rách khóe môi trái.", False), ("a bandage on her arm", True),
                           ("a bandage on her left arm", False), ("hard cut to the river", False), ("mạch máu sáng tím", False),
                           ("băng bó gối", True), ("điện băng giữa tuyết", False)):
            ra = self.chay("phan", self.ghi("hoi-1.md", hoi1(hinh=hinh)), "--phan", 1)[1]
            self.assertEqual("trái hay phải" in ra, nhac, hinh)

    def test_doc_phan(self):
        self.ghi("hoi-1.md", hoi1())
        kq, ra = self.chay_ngoai("doc_phan.py", self.phim, "--phan", 2)
        self.assertEqual(kq, 0, ra)
        for chu in ("## Tựa và thumbnail", "Trả tựa ở: N02", "| 2 | 2 | N05–N08 |", "hoi-1.md (hồi trước; phần này mở hoi-2.md",
                    "## P04 · cảnh 4", "<!-- doc_phan phần 2:"):
            self.assertIn(chu, ra)
        self.assertNotIn("| 1 | 1 | N01–N04 |", ra)
        g = [x.split("|")[1].strip() for x in ra.splitlines() if x.startswith("| G")]
        # G03, G06, G07 gieo hay gặt ở N05–N08; G04 vết tới N06, G05 biết tới N10 còn hiệu lực; G09 vết hết ở N02
        self.assertEqual(g, ["G03", "G04", "G05", "G06", "G07"])
        n = [x.split("|")[1].strip() for x in ra.splitlines() if re.match(r"\| N\d\d ", x)]
        self.assertEqual(n, [f"N{k:02d}" for k in range(4, 10)])
        self.assertNotIn("VATPHAN1", ra)                  # vật chỉ ghi nhịp phần 1
        self.assertNotIn("VATPHAN3", ra)
        self.assertIn("| NV01 | Mia (she) |", ra)         # hàng nhân vật gốc luôn giữ
        self.assertNotIn("## P03 · cảnh 3", ra)           # --phan: chỉ một cảnh cuối
        kq, ra = self.chay_ngoai("doc_phan.py", self.phim, "--phan", 1)
        self.assertIn("Chưa có hồi nào viết trước phần này", ra)      # hoi-1.md đã có cảnh của phần 1: không in làm cảnh trước
        self.assertIn("VATPHAN1", ra)
        self.assertEqual(self.chay_ngoai("doc_phan.py", self.phim, "--phan", 9)[0], 1)
        kq, ra = self.chay_ngoai("doc_phan.py", self.phim, "--nhip", "N05-N08")
        self.assertEqual(kq, 0, ra)
        self.assertIn("## Hai cảnh cuối", ra)

    def test_danh_lai_ma_dong_gieo_gat(self):
        vb = ("# Hồi 1: Mở\n\n" + canh(1, 1) + canh(1, 1).replace("## P01 ·", "## P01-b ·") + canh(2, 2) + canh(3, 3) + canh(4, 4)
              + "## Để viết hồi sau\n- Gieo, gặt phần 1: G01 P01-b, G02 P002, G04 P03\n")
        f = self.ghi("hoi-1.md", vb)
        kq, ra = self.chay_ngoai("danh_lai_ma.py", self.phim)
        self.assertEqual(kq, 0, ra)
        moi = f.read_text(encoding="utf-8")
        self.assertIn("- Gieo, gặt phần 1: G01 P02, G02 P03, G04 P04", moi)
        self.assertEqual([x.split(" ·")[0] for x in moi.splitlines() if x.startswith("## P")], ["## P01", "## P02", "## P03", "## P04", "## P05"])


class TestNeoDoan(unittest.TestCase):
    """dem_phan_canh.py: clip đầu đoạn (đổi mã nơi; sau clip nối là clip kế) phải có shot định vị."""

    @staticmethod
    def _canh(so, loai, noi, hanh):
        return (f"## P{so:02d} · Cảnh {so} · {10 if loai == 'nối' else 15}s · N01\n"
                f"- Mục đích kể chuyện: {loai} · việc {so}  |  Bối cảnh, thời điểm: {noi} nơi, sáng  |  Có mặt: NV01\n"
                f"- Hành động theo nhịp: {hanh}\n")

    def test_neo(self):
        import dem_phan_canh as dp
        vb = "# Hồi 1: thử\n" + "".join([
            self._canh(1, "việc", "DD01", "0–5s cận: tay cô bé"),            # cảnh đầu file: không xét
            self._canh(2, "nối", "DD01 → DD02", "0–10s toàn cảnh đường rừng"),
            self._canh(3, "việc", "DD02", "0–5s cận: rồng non mở mắt"),       # sau clip nối, thiếu định vị
            self._canh(4, "việc", "DD02", "0–5s cận: mắt rồng"),
            self._canh(5, "nối", "DD02 → DD03", "0–10s toàn cảnh làng"),
            self._canh(6, "việc", "DD03", "0–4s trung rộng: sân làng, cô bé bên trái"),
        ])
        _, _, dong = dp.dem(vb)
        neo = [d for d in dong if "shot định vị" in d]
        self.assertEqual(len(neo), 1, dong)
        self.assertIn("P03", neo[0])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
