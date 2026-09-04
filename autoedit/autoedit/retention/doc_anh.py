r"""Đọc ĐƯỜNG CONG retention từ ẢNH CHỤP biểu đồ YouTube Studio.

User 04/09: "Không thể xuất CSV retention, chỉ có ảnh" — nên đo thẳng trên ảnh
bằng pixel (Python đo, không nhờ LLM đoán số):

  1. Tìm các ĐƯỜNG KẺ NGANG xám nhạt CÁCH ĐỀU NHAU (gridline % trục tung) —
     KHÔNG giả định trên-cùng=100%/dưới-cùng=0% (bug 04/09, ảnh thật Trịnh Ngọc
     Hải: trục là 0/40/80/120%, đỉnh biểu đồ 120% không phải 100%, và có khi
     KHÔNG vẽ đủ 4 vạch — retention không vượt 100% nên YouTube bỏ vạch 120%
     mờ nhất). Chỉ cần ≥3 gridline CÁCH ĐỀU để suy khoảng-cách-trên-mỗi-điểm-%,
     rồi quy đổi y->% bằng phép tuyến tính — không cần biết vạch nào là bao
     nhiêu %, không cần vạch trên/dưới cùng phải đúng đỉnh/đáy trục.
  2. Tách đường màu XANH NGỌC ("Video này") khỏi nền: xanh dương trội hẳn đỏ —
     ngưỡng LỎNG (b-r≥20, bão hoà≥15) vì nén JPG nhoè màu đường mảnh về gần
     trắng (đo thật: tâm đường chỉ còn b-r≈30-50, không phải màu gốc ~150).
  3. Mỗi cột x lấy CỤM pixel xanh TRÊN CÙNG (không phải median mọi pixel xanh
     trong cột — dải "thông thường" mờ nhạt bên dưới đường chính cũng lọt
     ngưỡng lỏng, median gộp 2 cụm cho ra vị trí sai hẳn giữa hai đường).

Trục hoành ảnh không tự đọc được (nhãn 28:25 là chữ) — thời lượng tập cũ do
editor nhập khi nộp job; x_frac × thời lượng = giây thật.

Ảnh không đo được (thiếu gridline, thiếu đường xanh) thì NỔ AnhKhongDoDuoc với
lý do rõ — thà bắt nộp lại ảnh còn hơn im lặng chỉnh nhịp theo số rác.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np


class AnhKhongDoDuoc(ValueError):
    """Ảnh chụp không đo được — thông điệp tiếng Việt, in thẳng cho editor."""


def _duong_manh(tyle: np.ndarray) -> list[int]:
    """Hàng NGANG MẢNH (đường kẻ 1-3px), loại VÙNG NỀN dày (nhiều hàng xám liền
    kề — vd thanh video-bar mờ ở mép ảnh chụp, bug 04/09 dày ~19px từng lọt
    nhầm). Đòi CẢ hai bên (trên/dưới, cách 6px) đều không xám mới nhận là mảnh
    — một bên đủ (`or`) từng bắt nhầm biên của dải dày."""
    la_hang_xam = tyle > 0.5
    n = len(la_hang_xam)
    manh = np.zeros(n, dtype=bool)
    for y in np.where(la_hang_xam)[0]:
        tren = tyle[max(0, y - 6)] <= 0.5
        duoi = tyle[min(n - 1, y + 6)] <= 0.5
        manh[y] = tren and duoi
    hang = np.where(manh)[0]
    duong: list[int] = []
    for y in hang:
        if duong and y - duong[-1] <= 3:
            duong[-1] = int(y)           # gộp vệt liền kề, lấy mép dưới
        else:
            duong.append(int(y))
    return duong


def _gridlines(a: np.ndarray) -> tuple[float, float, int, int, list[int]]:
    """Tìm thước quy đổi y->% và bề ngang khung: (y_0pct, px_per_pct, x_left, x_right).

    KHÔNG giả định gridline trên-cùng=100%/dưới-cùng=0% (bug 04/09: trục có thể
    là 0/40/80/120%, và ảnh có khi KHÔNG vẽ đủ vạch trên cùng — retention không
    vượt 100% nên YouTube bỏ vạch mờ nhất). Chỉ cần ≥3 gridline CÁCH ĐỀU nhau
    (dung sai 15%) để suy khoảng-cách-mỗi-điểm-% bằng hồi quy tuyến tính đơn
    giản trên toạ độ y của chúng — không cần biết vạch nào ứng bao nhiêu %,
    chỉ cần chúng LÀ MỘT HỌ trục cách đều (loại được đường lẻ không liên quan,
    như viền hộp tooltip — đo thật: khoảng cách gấp ~3 lần 3 vạch còn lại).
    """
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    xam = ((np.abs(r - g) < 14) & (np.abs(g - b) < 14)
           & (r >= 190) & (r <= 248))
    tyle = xam.mean(axis=1)
    duong = _duong_manh(tyle)
    if len(duong) < 2:
        raise AnhKhongDoDuoc(
            "không thấy đường kẻ ngang của biểu đồ — chụp đủ khung retention, "
            "không lẫn nền trang")
    # tìm cụm ≥3 đường CÁCH ĐỀU dài nhất (khoảng cách giữa các cặp liên tiếp
    # lệch nhau <15%) — loại đường lẻ (vd viền tooltip) không cùng họ trục %.
    khoang = [duong[i + 1] - duong[i] for i in range(len(duong) - 1)]
    tot_nhat: list[int] = duong[:2]
    i = 0
    while i < len(khoang):
        j = i
        while (j + 1 < len(khoang)
               and abs(khoang[j + 1] - khoang[i]) <= 0.15 * khoang[i]):
            j += 1
        if j - i + 1 > len(tot_nhat) - 1:
            tot_nhat = duong[i:j + 2]
        i = j + 1
    if len(tot_nhat) < 3:
        raise AnhKhongDoDuoc(
            f"chỉ thấy {len(tot_nhat)} đường kẻ cách đều nhau — cần ≥3 vạch "
            "trục (vd 0/40/80%) để đo tỉ lệ, chụp đủ khung hơn")
    ys = np.array(tot_nhat, dtype=float)
    bac = np.arange(len(ys))                      # 0,1,2.. theo THỨ TỰ (không cần biết %)
    # hồi quy y theo bậc -> độ dốc px/bậc (khoảng cách THÔ, chưa hiệu chuẩn %)
    do_doc = float(np.polyfit(bac, ys, 1)[0])
    if do_doc <= 0:
        raise AnhKhongDoDuoc("đường kẻ trục không theo thứ tự hợp lệ")
    y_0pct = float(duong[-1])                       # gridline DƯỚI CÙNG thấy được = 0% thật
    # KHÔNG đoán mỗi bậc là bao nhiêu % (có thể 20/25/33.3/40 tuỳ YouTube, đoán
    # sai làm co giãn cả đường cong — đo thật 04/09: giả định cứng 40%/bậc gây
    # lệch tới 17 điểm% trên ảnh test 0/33/66/100%). Trả khoảng cách THÔ
    # (do_doc = px giữa 2 gridline liên tiếp); doc_duong_cong() hiệu chuẩn
    # CHÍNH XÁC bằng neo tại đỉnh 100% đầu video (quy luật YouTube — retention
    # LUÔN bắt đầu 100%, không cần đoán số bậc gridline).
    px_per_gridline = do_doc
    # bề ngang khung: đoạn LIÊN TỤC dài nhất mà đường 0% thực sự kẻ (tránh lề/
    # chữ số trục hoành cũng lọt ngưỡng xám nằm rời rạc ngoài đoạn kẻ liền mạch).
    y_hang = int(round(y_0pct)) if int(round(y_0pct)) < a.shape[0] else a.shape[0] - 1
    cot_xam = np.where(xam[y_hang])[0]
    if len(cot_xam) == 0:
        raise AnhKhongDoDuoc("đường kẻ 0% quá mờ/đứt đoạn — chụp lại rõ hơn")
    ngat = np.where(np.diff(cot_xam) > 3)[0]
    bien = [0, *(ngat + 1).tolist(), len(cot_xam)]
    doan = max(((bien[i], bien[i + 1]) for i in range(len(bien) - 1)),
              key=lambda ab: cot_xam[ab[1] - 1] - cot_xam[ab[0]])
    x_l, x_r = int(cot_xam[doan[0]]), int(cot_xam[doan[1] - 1])
    return y_0pct, px_per_gridline, x_l, x_r, tot_nhat


def _doc_nhan_truc(a: np.ndarray, x_r: int) -> dict[int, float]:
    """OCR nhãn % cạnh gridline bên phải khung -> {y_pixel: gia_tri_%}.

    User chốt 04/09 (ảnh Trịnh Ngọc Hải thứ 2: điểm đầu 119% — chứng minh
    'retention luôn bắt đầu 100%' SAI, YouTube cho phép vượt 100% khi có tua
    lại) — không còn neo cứng đầu=100%, đọc THẲNG số % in cạnh trục bằng OCR.
    Trả rỗng nếu không có pytesseract/tesseract hoặc không đọc được gì —
    caller tự rơi về phương án cũ (fail-open, không giết luồng đo)."""
    try:
        import os as _os

        import pytesseract
        from PIL import Image

        # Windows không tự thêm Tesseract vào PATH sau khi cài qua winget —
        # trỏ thẳng đường dẫn cài mặc định; máy khác không có thì giữ nguyên
        # mặc định (tìm trong PATH), lỗi rơi vào except bên dưới (fail-open).
        duong_mac_dinh = "C:/Program Files/Tesseract-OCR/tesseract.exe"
        if _os.path.isfile(duong_mac_dinh):
            pytesseract.pytesseract.tesseract_cmd = duong_mac_dinh
    except Exception:  # noqa: BLE001 — thiếu thư viện/binary tesseract
        return {}
    h, w = a.shape[:2]
    # dải hẹp bên phải khung, đủ rộng để chứa nhãn "120%" mà không dính đường xanh
    x0 = max(0, min(w - 1, x_r + 2))
    crop = Image.fromarray(a[:, x0:min(w, x0 + 90)])
    try:
        # psm 6: khối văn bản NHIỀU DÒNG — đúng khuôn 4 nhãn "0%/40%/80%/120%"
        # xếp dọc cạnh trục (psm 7 giả định MỘT dòng, đo thật: trả rỗng hoàn
        # toàn với crop nhiều dòng dù cùng nội dung psm 6 đọc đúng cả 4 nhãn).
        data = pytesseract.image_to_data(crop, config="--psm 6 -c tessedit_char_whitelist=0123456789%",
                                         output_type=pytesseract.Output.DICT)
    except Exception:  # noqa: BLE001 — tesseract lỗi/không cài đúng
        return {}
    ra: dict[int, float] = {}
    for i, txt in enumerate(data.get("text", [])):
        so = "".join(c for c in txt if c.isdigit())
        if not so or int(data["conf"][i]) < 40:
            continue
        y_giua = data["top"][i] + data["height"][i] / 2
        ra[int(round(y_giua))] = float(so)
    return ra


def doc_duong_cong(anh: Path, so_diem: int = 200) -> list[tuple[float, float]]:
    """Ảnh chụp -> [(x_frac 0..1, retention 0..1)] đã resample đều so_diem điểm."""
    from PIL import Image

    a = np.asarray(Image.open(anh).convert("RGB"))
    y_0pct, px_per_gridline, x_l, x_r, cac_gridline = _gridlines(a)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    # ngưỡng LỎNG (b-r>=20) — đo thật 04/09: nén JPG nhoè đường mảnh, tâm đường
    # chỉ còn b-r~30-50 (không phải màu gốc đậm ~150 của thước cũ b-r>30 g-r>15
    # ĐỒNG THỜI, quá chặt nên chỉ bắt được 88/7213 pixel hơi-xanh thật của bài).
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    xanh = (b - r >= 20) & (sat >= 15) & (b >= 130)
    # trần quét: 4 gridline liên tiếp NGƯỢC lên trên gridline 0% — dư dả cho mọi
    # khuôn trục YouTube (0/33/66/100 hay 0/40/80/120), không cần biết đúng %.
    y_top_vung = max(0, int(round(y_0pct - 4 * px_per_gridline)))
    xanh[:y_top_vung] = False
    xanh[int(round(y_0pct)) + 3:] = False
    xanh[:, :x_l] = False
    xanh[:, x_r + 1:] = False

    cot_co = np.where(xanh.any(axis=0))[0]
    if len(cot_co) < (x_r - x_l) * 0.35:
        raise AnhKhongDoDuoc(
            f"đường retention màu xanh chỉ phủ {len(cot_co)} cột "
            f"({100 * len(cot_co) // max(1, x_r - x_l)}% bề ngang) — cần ảnh rõ "
            "hơn, không che khuất đường 'Video này'")
    x0, x1 = int(cot_co.min()), int(cot_co.max())
    ys = np.arange(a.shape[0])
    y_bruta: list[tuple[int, float]] = []          # (x, y_pixel) CHƯA hiệu chuẩn %
    for x in cot_co:
        yy = ys[xanh[:, x]]
        # CỤM TRÊN CÙNG — không phải median mọi pixel xanh trong cột: dải
        # "thông thường" (band mờ dưới đường "Video này") cũng lọt ngưỡng lỏng,
        # median gộp cả hai cụm cho vị trí sai lệch hẳn giữa 2 đường (đo thật
        # 04/09: cột gần t=0 median ra ~50% dù đường thật ở 95% — 2 cụm cách
        # nhau ~50px, median rơi giữa khoảng trống).
        cum_tren = yy[yy <= yy.min() + 6]
        y_bruta.append((int(x), float(np.median(cum_tren))))
    # HIỆU CHUẨN %: ưu tiên OCR đọc nhãn số cạnh gridline (chính xác tuyệt đối,
    # đúng mọi khuôn trục 0/33/66/100 hay 0/40/80/120) — user chốt 04/09 sau khi
    # phát hiện điểm đầu có thể VƯỢT 100% (YouTube cho phép khi có tua lại; ảnh
    # thật Trịnh Ngọc Hải thứ 2: đầu video 119%), nên KHÔNG còn neo cứng "đầu
    # luôn 100%". OCR đọc được ít nhất 2 nhãn khớp 2 gridline khác nhau -> suy
    # px_per_pct chính xác bằng chênh lệch giá trị/khoảng cách pixel giữa
    # chúng. Không đọc được (thiếu tesseract, ảnh không có nhãn như ảnh gốc
    # Hải bị crop hẹp) -> rơi về neo "đầu ~100%" cũ, kèm cảnh báo qua log caller.
    nhan = _doc_nhan_truc(a, x_r)
    px_per_pct = None
    for y_g in cac_gridline:
        gan = [(y_n, v) for y_n, v in nhan.items() if abs(y_n - y_g) <= 8]
        if gan:
            y_khop, gia_tri = min(gan, key=lambda t: abs(t[0] - y_g))
            for y_g2 in cac_gridline:
                if y_g2 == y_g:
                    continue
                gan2 = [(y_n, v) for y_n, v in nhan.items() if abs(y_n - y_g2) <= 8]
                if gan2:
                    y_khop2, gia_tri2 = min(gan2, key=lambda t: abs(t[0] - y_g2))
                    if gia_tri != gia_tri2:
                        px_per_pct = abs(y_khop - y_khop2) / abs(gia_tri - gia_tri2)
                        y_0pct_that, pct_0 = y_khop, gia_tri
                        break
        if px_per_pct:
            break
    if px_per_pct:
        # dịch quy chiếu về gridline y_0pct_that (giá trị pct_0 đọc được từ OCR,
        # KHÔNG giả định là 0) — mọi điểm quy đổi qua đúng mốc đã xác nhận này.
        y_0pct, offset_pct = y_0pct_that, pct_0
    else:
        # fallback: neo đầu ~100% (đường cũ, kém chính xác hơn với ảnh vượt 100%
        # nhưng vẫn đúng hình dạng đường cong — chỉ sai biên trên/dưới)
        y_dinh_dau = y_bruta[0][1]
        px_per_pct = max(1e-6, (y_0pct - y_dinh_dau) / 100.0)
        offset_pct = 0.0
    ra: list[tuple[float, float]] = []
    for x, y in y_bruta:
        pct = offset_pct / 100.0 + (y_0pct - y) / px_per_pct / 100.0
        # KHONG kep tran 1.0 — retention hop le co the VUOT 100% khi nguoi xem
        # tua lai (bug 04/09: anh that Trinh Ngoc Hai thu 2, dau video 119%,
        # kep tran se cat mat du lieu that). San 0.0 van giu (khong am duoc).
        ra.append(((x - x0) / max(1, x1 - x0), max(0.0, pct)))
    # kiểm chân lý: retention chạm 100% Ở ĐÂU ĐÓ rất gần đầu (giây đầu tiên) —
    # KHÔNG đòi cột đầu tiên đo được phải cao (bug 04/09, báo bởi Trịnh Ngọc Hải:
    # video hook yếu tụt thật xuống ~70% chỉ trong vài giây, đây là DỮ LIỆU THẬT
    # chứ không phải ảnh bị cắt — ép ngưỡng 80% từ chối đúng ca cần đo nhất).
    # Ảnh THỰC SỰ cắt mất đầu thì đỉnh cao nhất trong 10% đầu vẫn thấp hẳn dưới
    # mốc chuẩn 95% (YouTube luôn vẽ đúng 100% tại t=0, kể cả khi tụt ngay sau đó).
    dinh_dau = max(p for x, p in ra if x <= 0.10)
    if dinh_dau < 0.90:
        raise AnhKhongDoDuoc(
            f"đỉnh cao nhất trong 10% đầu chỉ {dinh_dau:.0%} — retention luôn "
            "chạm 100% ngay tại 0:00; ảnh có lẽ bị cắt mất đoạn mở đầu hoặc "
            "chụp thiếu góc trên bên trái")
    # resample đều: nội suy tuyến tính trên lưới so_diem điểm
    xs = np.array([p[0] for p in ra])
    ps = np.array([p[1] for p in ra])
    luoi = np.linspace(0.0, 1.0, so_diem)
    return list(zip(luoi.tolist(), np.interp(luoi, xs, ps).tolist()))
