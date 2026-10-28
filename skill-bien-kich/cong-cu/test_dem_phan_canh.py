"""Test dem_phan_canh.py, dan_y.py ở phim `Clip: 30s` (Spec 55, `phan-canh-30s.md`). Chạy: py -3 cong-cu/test_dem_phan_canh.py"""
import sys
import unittest
from pathlib import Path

CC = Path(__file__).resolve().parent
sys.path.insert(0, str(CC))
import dan_y as dy  # noqa: E402
import dem_phan_canh as dp  # noqa: E402

NHIP = """# Thử 30
Thể loại: fantasy-drama · Dài: 2 phút · Lời bình: không · Thoại: ít · Clip: 30s

## Ba hồi
- Hồi 1 (N01–N03, ~100%): mở.

## Bảng nhịp
| Mã | % | Loại | Cảnh | Sự kiện | Vì nhịp | Cảm xúc khán giả | Mức |
|---|---|---|---|---|---|---|---|
| N01 | 0 | Móc | 2 | Sói đuổi cô bé tới hang | – | sợ | 4 |
| N02 | 25 | Diễn biến | 4 | Cô bé về làng, mẹ giận | N01 | lo | 4 |
| N03 | 75 | Diễn biến | 2 | Mẹ băng tay cho cô | N02 | thương | 2 |

## Bảng phân clip
Ngân sách hồi 1: 4,5 × 2 × 100% = 9; bảng: 8.
| Nhịp | Mức | Việc | Clip theo loại | Điểm chạm và thủ pháp | Lý do vượt trần |
|---|---|---|---|---|---|
| N01 | 4 | sói đuổi | việc 2 15s | | |
| N02 | 4 | về làng; mẹ mắng | nối+việc 1, việc+sau đỉnh 1 | | |
| N03 | 2 | mẹ băng tay | việc 1 | | |
"""

SHOT_30 = ('0–3s trung rộng: sân làng, NV01 bên trái, NV02 bên phải → 3–6s cận NV02: "Con đi đâu cả đêm?" → 6–9s cận tay NV01 → '
           '9–12s cận NV01 cúi đầu → 12–15s cận mặt NV02 → 15–19s trung: NV02 kéo NV01 vào nhà → 19–23s cận NV01: "Con xin lỗi mẹ." → '
           '23–27s đặc tả tay → 27–30s trung rộng, *lùi ra*: hai mẹ con')


def canh(so: int, giay: int, nhip: int, muc_dich: str, noi: str, hanh: str, cach: str = "9 shot hard cut",
         co_mat: str = "NV01, NV02") -> str:
    return (f"## P{so:02d} · cảnh {so} · {giay}s · N{nhip:02d}\n"
            f"- Mục đích kể chuyện: {muc_dich}  |  Bối cảnh, thời điểm: {noi} nơi, sáng  |  Có mặt: {co_mat}\n"
            f"- Cách dựng: {cach}\n- Hành động theo nhịp: {hanh}\n\n")


MOC = "0–2s trung rộng: rừng, sói đuổi → 2–4s cận chân → 4–6s cận mặt → 6–9s cận sói → 9–12s cận tay → 12–15s toàn cảnh hang"


def hoi(*them: str) -> str:
    cac = list(them) or [
        canh(1, 15, 1, "việc · sói đuổi cô bé trong rừng", "DD01", MOC, "8 shot hard cut", "NV01"),
        canh(2, 15, 1, "việc · cô bé lết tới hang", "DD01", MOC, "8 shot hard cut", "NV01"),
        canh(3, 30, 2, "nối + việc · cô bé về tới làng → mẹ hỏi cô đi đâu", "DD02", SHOT_30.replace("trung rộng: sân", "toàn cảnh: sân", 1)),
        canh(4, 30, 2, "việc + sau đỉnh · mẹ mắng cô → cô khóc xin lỗi", "DD02", SHOT_30),
        canh(5, 30, 3, "việc · mẹ băng tay trái cho cô", "DD02", SHOT_30),
    ]
    return "# Hồi 1: Mở\n\n" + "".join(cac)


def dem(vb: str, nhip: str = NHIP) -> tuple[list[str], list[str]]:
    _, so, dong = dp.dem(vb, nhip=nhip)
    return so, dong


class Phim30(unittest.TestCase):
    def test_mau_sach(self):
        so, dong = dem(hoi())
        self.assertEqual([d for d in dong if d.startswith("LỖI")], [], dong)
        for chu in ("shot đầu", "shot quá", "shot (cảnh 30s", "thoại","bảng phân clip lệch", "lệch ngân sách", "nhân vật ở Có mặt", "khối"):
            self.assertFalse([d for d in dong if chu in d], (chu, dong))
        self.assertTrue(any("Hồi 1: 8 đơn vị / ngân sách 9" in s for s in so), so)
        self.assertTrue(any("3 cảnh 30s, 2 cảnh 10/15s" in s for s in so), so)
        self.assertTrue(any("20%" in d for d in dong), dong)        # 30s trên 120s là 25%: cảnh báo cảnh 15s xen

    def test_chi_bang(self):
        so, dong = dem("", NHIP)
        self.assertIn("8 đơn vị 15 giây", so[0])
        self.assertFalse([d for d in dong if d.startswith("LỖI")], dong)

    def test_khong_ep_cat_giua(self):
        """Spec 71 K.4: cảnh 30s không buộc ranh giới shot ở 13–17s, không đòi ghi 'cắt giữa'."""
        h = "0–3s trung rộng: sân → 3–7s cận → 7–12s cận → 12–18s trung → 18–24s cận → 24–30s trung"
        _, dong = dem(hoi(canh(1, 30, 3, "việc · mẹ băng tay", "DD02", h, "6 shot hard cut")))
        self.assertFalse([d for d in dong if "13–17s" in d or "cắt giữa" in d], dong)
        self.assertFalse([d for d in dong if d.startswith("LỖI P01")], dong)

    def test_shot_dau_dai_va_thoai(self):
        h = ('0–6s trung rộng: sân "Một hai ba bốn năm sáu bảy tám chín mười mười một mười hai mười ba." → 6–10s cận → 10–15s cận → '
             '15–22s trung → 22–30s cận')
        _, dong = dem(hoi(canh(1, 30, 3, "việc · mẹ băng tay", "DD02", h)))
        noi = " | ".join(dong)
        for chu in ("shot đầu 6s", "shot quá 6s", "5 shot", "quá 12 từ"):
            self.assertIn(chu, noi)

    def test_hai_noi_trong_canh_30(self):
        _, dong = dem(hoi(canh(1, 30, 3, "nối · cô bé chạy về", "DD01 → DD02", SHOT_30)))
        self.assertTrue(any(d.startswith("LỖI") and "cảnh 30s một nơi" in d for d in dong), dong)

    def test_lon_lat_theo_don_vi(self):
        lon = canh(1, 30, 2, "lớn 1/1 nhận ra · mẹ nhận ra vết cắn", "DD02", SHOT_30)
        _, dong = dem(hoi(lon))
        self.assertFalse([d for d in dong if "khoảnh khắc lớn" in d], dong)
        lat = [canh(k, 30, 3, f"lật {k}/2 · nấc {k}", "DD02", SHOT_30) for k in (1, 2)]
        _, dong = dem(hoi(*lat))
        self.assertFalse([d for d in dong if "cú lật lớn nhất" in d and d.startswith("LỖI")], dong)
        _, dong = dem(hoi(canh(1, 30, 3, "lật 1/1 · nấc", "DD02", SHOT_30)))
        self.assertTrue(any(d.startswith("LỖI") and "2 đơn vị" in d for d in dong), dong)

    def test_tran_hai_dong_moi_canh(self):
        khoi = ("## Thiết kế trận T1: Sân · cỡ xô xát · P01–P02\n- Lý do đảo thế: x\n"
                "| Cảnh | Bậc | Câu hỏi kịch tính | Đổi thế | Cú đỉnh | Cuối cảnh |\n|---|---|---|---|---|---|\n"
                "| P01 0–15 | chạm đầu | ? | sói vồ | | còn 0 người phụ đứng |\n| P01 15–30 | leo thang | ? | cô né | | còn 0 người phụ đứng |\n"
                "| P02 | đảo thế | ? | cô ném đá | | còn 0 người phụ đứng |\n")
        vb = "# Hồi 1: Mở\n\n" + khoi + "".join(canh(k, 30, 3, f"việc · đổi thế {k}", "DD02", SHOT_30) for k in (1, 2))
        so, dong = dem(vb)
        self.assertTrue(any("4 đơn vị việc (3–4)" in s for s in so), so)
        thieu = [d for d in dong if "một dòng ở bảng khối" in d]
        self.assertEqual(len(thieu), 1, dong)
        self.assertIn("P02", thieu[0])
        self.assertEqual(len([d for d in dong if "shot (cảnh trận 30s: 10–16)" in d]), 2, dong)     # 9 shot: ít cho cảnh trận
        shot_tran = " → ".join(f"{2 * i}–{2 * i + 2}s cận: đòn {i}" for i in range(15))
        vb = "# Hồi 1: Mở\n\n" + khoi + "".join(canh(k, 30, 3, f"việc · đổi thế {k}", "DD02", shot_tran) for k in (1, 2))
        self.assertFalse([d for d in dem(vb)[1] if "shot (cảnh" in d], dem(vb)[1])

    def test_dan_y_phut(self):
        d = dy.doc_nhip(NHIP)
        self.assertEqual(d["clip"], 30)
        self.assertAlmostEqual(dy.phut_nhip(d, [1, 2, 3]), 8 / 4.5)


class Phim15(unittest.TestCase):
    """Vắng `Clip:` là phim 15s: hai loại trong một cảnh là LỖI, lớn 1/1 là LỖI như cũ, phút = Cảnh / 6."""

    NHIP15 = NHIP.replace(" · Clip: 30s", "")

    def test_hai_loai_loi(self):
        _, dong = dem(hoi(canh(1, 15, 3, "việc + sau đỉnh · a → b", "DD02", MOC)), self.NHIP15)
        self.assertTrue(any(d.startswith("LỖI") and "chỉ ở phim Clip: 30s" in d for d in dong), dong)

    def test_lon_mot_clip(self):
        _, dong = dem(hoi(canh(1, 30, 2, "lớn 1/1 nhận ra · mẹ nhận ra", "DD02", SHOT_30)), self.NHIP15)
        self.assertTrue(any("chỉ có 1 clip (luật: 2)" in d for d in dong), dong)
        self.assertFalse([d for d in dong if "13–17s" in d or "Phim 30s" in d], dong)

    def test_dan_y_phut(self):
        d = dy.doc_nhip(self.NHIP15)
        self.assertEqual(d["clip"], 15)
        self.assertAlmostEqual(dy.phut_nhip(d, [1, 2, 3]), 8 / 6)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
