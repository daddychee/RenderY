r"""TRA 4 LỚP — hàm truy xuất cho Đường Dây (đợt 4 gọi; đợt 1 nghiệm thu logic).

Mô hình tập-giao (user chốt 06/09): L0 chủ thể tập là CỬA BẮT BUỘC, các lớp
còn lại cộng điểm L1 trực chỉ > L2 ngữ cảnh > L3 không khí; nguồn ref/kho được
ưu tiên nhẹ theo switch; luật 60s do caller lo (cần vị trí timeline).
Đây là bản đã nghiệm thu ở prototype V5 — giờ đọc từ db thay JSON.
"""

from __future__ import annotations

import re

from autoedit.sotra import db as sdb

DIEM = {"L1": 10.0, "L2": 6.0, "L3": 3.0}
DIEM_NEO = 2.0
# 6.0 chứ không phải 2.5: phải THẮNG được `PHAT_NGUON` (tối đa 4.0), nếu không
# `--uu-tien-nguon pexels` gõ vào mà pexels vẫn nằm dưới envato — người dùng
# bảo ưu tiên thì luật chung phải nhường.
DIEM_UU_TIEN_NGUON = 6.0
# VIỆC F (user chốt 09/09): pexels/pixabay xấu hơn -> ĐẨY XUỐNG, KHÔNG loại.
# Thứ tự mong muốn: ref -> envato -> pexels -> pixabay.
#
# Mức 3.0/4.0 là số ĐO trên 996 miếng production 10/09, không phải ước:
#   khoảng cách điểm trong một khay: trung vị 13.0, p25 7.0
#   mô phỏng trong nhóm `cham` (ref có luật `suat_ref` riêng, không đụng):
#     phạt 2/3 -> 6/31 khay đổi thứ tự      phạt 5/6 -> 14/31 (envato -0.42)
#     phạt 3/4 -> 8/31 (envato -0.25)       phạt 8/9 -> 16/31 (envato -0.57)
# Chọn 3/4: đủ lật khi điểm sát nhau (p25=7), không đủ để đẩy stock văng khỏi
# khay. Nặng hơn thì bắt đầu kéo tụt cả envato/kho mà stock vẫn không xuống
# thêm — vì 10/31 khay có stock thì stock là TOÀN BỘ nhóm cham, không có gì
# để so. Đó là trần tự nhiên, đừng nâng mức phạt để đuổi theo nó.
PHAT_NGUON = {"pexels": 3.0, "pixabay": 4.0}
# VẤN ĐỀ 3 (user duyệt 10/09): clip đã LÊN FINAL ở chương khác CÙNG TẬP thì đẩy
# xuống, mỗi chương −20, trần 5 chương. Đo mô phỏng `chon_mac_dinh` qua 14/11/7
# chương thật (than=4.73): phạt 6 -> trùng còn 12%/15%/7%; phạt 20 -> 0.6%/0%/0%,
# điểm gốc clip được chọn −4% (30.8 -> 29.7), ref vẫn 100% final (không trôi
# sang stock). `chon_mac_dinh` chỉ nhớ 60s TRONG một chương — đây là bộ nhớ
# GIỮA các chương. Caller đếm từ `offline.json` chương anh em (dung.py).
PHAT_DA_DUNG = 20.0
TRAN_DA_DUNG = 5
# SÀN REF + MỖI NGUỒN STOCK MỘT Ô (user chốt 12/09: "mỗi chương phải có đủ ref,
# và 2 nguồn stock"). Đo SH010 trước khi sửa: 116 khối thì kho có sẵn hàng cho
# 97 khối, mà khay chỉ cho 2 khối đạt — 95 khối mất vì luật cắt khay, không
# phải vì thiếu dữ liệu. Envato trước đây không có suất giữ chỗ nào (chỉ
# pexels/pixabay, vì suất cũ gắn với `PHAT_NGUON`).
SAN_REF = 3
NGUON_STOCK = ("envato", "pexels", "pixabay")
# LỚP NGHĨA (đợt 3, 06/09) — topic của beat khớp lớp L1/L2 của khối voice.
# Nặng hơn lớp Hình vì đây mới là "video này NÓI VỀ gì", còn pixel chỉ tả vật.
DIEM_NGHIA_L1 = 12.0
DIEM_NGHIA_L2 = 7.0
PHAT_AN_DU = 5.0        # beat ẩn dụ: máy KHÔNG tự chọn, editor tra tay vẫn thấy
DUNG_LOP_NGHIA = True   # CÔNG TẮC: False = quay về cách cũ tức thì


def _tokens(cum) -> set:
    if isinstance(cum, str):
        cum = [cum]
    return {w for c in (cum or []) for w in re.findall(r"[a-z]{4,}", str(c).lower())}


def tra(conn, lop: dict, so: int = 12, uu_tien_nguon: str = "",
        can_neo: bool = True, suat_ref: int = 2, seed: int = 0,
        geo_tap: str = "", tap: str = "",
        da_dung: dict[str, int] | None = None) -> list[dict]:
    """lop = {"L0": [...], "L1": [...], "L2": [...], "L3": [...]} -> ứng viên xếp
    hạng, mỗi cái kèm `lop` (tầng trúng) + `diem`. Khay chia nhóm theo `lop`.

    suat_ref: REF luôn được GIỮ CHỖ (bài học V5: điểm chữ Envato đè chết ref).
    da_dung: {clip_id: số CHƯƠNG khác trong tập đã lên final} -> trừ PHAT_DA_DUNG."""
    l0, l1 = _tokens(lop.get("L0")), _tokens(lop.get("L1"))
    l2, l3 = _tokens(lop.get("L2")), _tokens(lop.get("L3"))
    # kéo ứng viên qua FTS bằng TOÀN BỘ từ của các lớp (OR) — rẻ hơn quét cả bảng
    moi_tu = l1 | l2 | l3 | l0
    if not moi_tu:
        return []
    fts = " OR ".join(f'"{t}"' for t in sorted(moi_tu))
    rows = conn.execute(
        "SELECT c.* FROM clip_fts f JOIN clip c ON c.id=f.id "
        "WHERE clip_fts MATCH ? AND c.trang_thai='song' LIMIT 800", (fts,)).fetchall()
    # REF lấy RIÊNG, không qua FTS (bài học V5: ref ít + từ khóa lệch ngôn ngữ
    # -> FTS bỏ rơi; suất giữ chỗ phải đến từ quét thẳng bảng, ref mỗi tập ít).
    #
    # LỌC THEO TẬP ngay trong câu này (bug bắt 07/09 khi chạy chương H LI103):
    # bản cũ `LIMIT 600` không lọc tập và không sắp xếp -> lấy 600 dòng ĐẦU
    # BẢNG, mà đầu bảng là tập nạp TRƯỚC. Đo thật: 600 dòng đó toàn LI100, nên
    # 1.995 cảnh ref của LI103 (1.768 khớp từ khoá) không bao giờ được xét; rồi
    # rào "ref tập khác không sang tập này" loại nốt LI100 -> KHAY REF RỖNG.
    # Suất giữ chỗ chỉ đúng khi kho có MỘT tập; có tập thứ hai là hỏng.
    #
    # KHÔNG CÒN `LIMIT` khi đã lọc tập (user duyệt 10/09). `LIMIT 600` không
    # ORDER BY = 600 dòng ĐẦU theo rowid, chạy bao nhiêu lần cũng đúng 600 dòng
    # đó: LI106 có 2.123 ref mà 1.523 (72%) chưa từng được xét, 100% ref lên
    # final nằm trong 600 dòng đó -> chính là "kho nhiều mà không dùng". Đo bỏ
    # LIMIT: điểm khớp +12%, +4..22s/tập chạy nền. Không đặt trần mới: LI103 đã
    # 2.401, kho nạp +4.498/ngày — trần nào rồi cũng thành `LIMIT 600` thứ hai.
    da_co = {r["id"] for r in rows}
    if tap:
        cau, tham = ("SELECT * FROM clip WHERE nguon='ref' AND trang_thai='song' "
                     "AND tap=?", (tap,))
    else:
        cau, tham = ("SELECT * FROM clip WHERE nguon='ref' AND trang_thai='song' "
                     "LIMIT 600", ())
    rows = list(rows) + [r for r in conn.execute(cau, tham)
                         if r["id"] not in da_co]
    # LỚP NGHĨA: topic + cờ ẩn dụ của beat, tra một lượt cho cả mẻ (rẻ)
    nghia: dict[str, tuple] = {}
    if DUNG_LOP_NGHIA:
        bids = {r["beat_id"] for r in rows if (r["beat_id"] or "")}
        if bids:
            dau = ",".join("?" * len(bids))
            nghia = {b: (t, m) for b, t, m in conn.execute(
                f"SELECT id, topic, metaphor FROM beat WHERE id IN ({dau})",
                list(bids))}

    cham, refs = [], []
    for r in rows:
        c = dict(r)
        # vat_the + loi_quanh PHẢI vào điểm (user bắt 06/09: cùng một câu mà
        # khay ref ra cảnh chẳng liên quan): vat_the là vật NHÌN THẤY trong
        # hình (giàu nghĩa nhất của ref), loi_quanh là lời quanh cảnh — thiếu
        # cả hai thì mọi ref 0 điểm, suất giữ chỗ lấy đại 2 cảnh đầu bảng.
        chu = " ".join(str(c.get(k) or "")
                       for k in ("tieu_de", "vat_the", "loi_quanh") + sdb.TRUC)
        tt = _tokens([chu])
        la_ref = c["nguon"] in ("ref",)
        # RÀO CỨNG THEO TẬP (user chốt 06/09: "city ở Ecuador không thể chảy
        # vào Nepal; person ở châu Phi không thể chảy vào Mỹ"):
        # 1. ref của tập KHÁC không bao giờ sang tập này
        if la_ref and tap and (c.get("tap") or "") != tap:
            continue
        # 2. HÌNH PHẢI KHỚP NGỮ NGHĨA (user chốt 07/09): tập khai địa danh thì
        #    clip KHÔNG KHỚP bị loại — cả geo lệch LẪN geo trống. Trước đây geo
        #    trống đi qua như "trung tính", mà 72% kho envato không có geo nên
        #    rào gần như vô hiệu: núi Bolivia và ruộng bậc thang Inca chảy vào
        #    tập Afghanistan. User: "nếu không có ref và stock cũng không có
        #    đúng thì video final không thể tồn tại" — khối trống là THÔNG TIN
        #    thật cho editor, không phải chỗ để lấp bừa.
        #    Tiêu đề có nhắc địa danh mà cột geo rỗng (clip nạp trước khi từ
        #    điển được mở rộng) thì đọc lại từ tiêu đề, khỏi phải nạp lại kho.
        gt = _tokens([geo_tap]) if geo_tap else set()
        gc = _tokens([(c.get("geo") or "").replace(">", " ")])
        if gt and not gc:
            from autoedit.sotra.tag7 import tag_tu_tieu_de
            gc = _tokens([(tag_tu_tieu_de(c.get("tieu_de") or "").get("geo") or "")
                          .replace(">", " ")])
        if gt and not (gt & gc):
            continue
        co_neo = bool(c.get("geo")) or c["nguon"] in ("ref", "kho")
        # CỬA L0: thuộc thế giới video (neo địa lý HOẶC trúng chủ thể tập)
        if can_neo and not (co_neo or la_ref or (tt & l0)):
            continue
        s1, s2, s3 = len(tt & l1), len(tt & l2), len(tt & l3)
        # LỚP NGHĨA — tính RIÊNG, không trộn vào chuỗi chữ của lớp Hình
        n1 = n2 = 0
        an_du = 0
        tp, an_du = nghia.get(c.get("beat_id") or "", ("", 0))
        if tp:
            tn = _tokens([tp])
            n1, n2 = len(tn & l1), len(tn & l2)
        if not (s1 or s2 or s3 or n1 or n2) and not la_ref:
            continue
        tang = ("L1" if (s1 or n1) else ("L2" if (s2 or n2) else "L3"))
        d = s1 * DIEM["L1"] + s2 * DIEM["L2"] + s3 * DIEM["L3"]
        d += n1 * DIEM_NGHIA_L1 + n2 * DIEM_NGHIA_L2
        if an_du:
            d -= PHAT_AN_DU          # ẩn dụ: đè xuống, không loại
        if tp:
            c["topic_beat"] = tp
            c["an_du"] = int(an_du)
        d += DIEM_NEO if co_neo else 0
        d -= PHAT_NGUON.get(c["nguon"], 0.0)     # việc F: đẩy xuống, KHÔNG loại
        if da_dung:                               # vấn đề 3: đã lên final chương khác
            d -= PHAT_DA_DUNG * min(da_dung.get(c["id"], 0), TRAN_DA_DUNG)
        if uu_tien_nguon and c["nguon"] == uu_tien_nguon:
            d += DIEM_UU_TIEN_NGUON
        # 3. kho b-roll của TẬP KHÁC mà không rõ geo: đè xuống đáy khay —
        #    tra tay vẫn thấy, máy không bao giờ tự chọn
        if c["nguon"] == "kho" and tap and (c.get("tap") or "") != tap and not gc:
            d -= 6.0
        c["lop"], c["diem"] = tang, round(d, 1)
        (refs if la_ref else cham).append(c)

    cham.sort(key=lambda c: -c["diem"])
    # ref đồng điểm: RẢI theo seed (mỗi khối một seed) — không thì cả tập bị
    # đề xuất đúng 2 cảnh đầu bảng cho mọi câu (triệu chứng user thấy 06/09)
    refs.sort(key=lambda c: (-c["diem"], hash((c["id"], seed)) % 9973))

    # GIỮ CHỖ TRƯỚC, XẾP ĐIỂM SAU. Bản cũ xếp điểm trước rồi mới vá suất giữ
    # chỗ, nên nguồn điểm thấp bị vòng giỏ tầng (tối đa 6/tầng) cắt mất trước
    # khi tới lượt vá — đúng chỗ 95/116 khối SH010 rơi.
    ra: list[dict] = []
    da: set = set()

    def _nhan(c) -> None:
        if len(ra) < so and c["id"] not in da:
            da.add(c["id"])
            ra.append(c)

    # Sàn ref đếm theo THẺ HIỂN THỊ: `gop_ban_trung` gộp cùng nguồn + cùng tiêu
    # đề về MỘT thẻ, mà ref cắt theo cảnh nên tên lặp nhiều ("woman speaking"
    # ×3). Đo SH010 sau khi thêm sàn: 22 khối vẫn thiếu ref, **22/22 rơi vì gộp**
    # chứ không phải kho thiếu. Giữ chỗ theo tiêu đề KHÁC NHAU; hết tên khác thì
    # thôi, không bịa.
    can, ten_da = max(suat_ref, SAN_REF), set()
    for c in refs:
        if len(ten_da) >= can:
            break
        t = (c.get("tieu_de") or "").strip().lower()
        if t and t in ten_da:
            continue
        ten_da.add(t or c["id"])
        _nhan(c)
    for ng in NGUON_STOCK:                          # mỗi nguồn stock 1 ô
        t = next((c for c in cham if c["nguon"] == ng and c["id"] not in da), None)
        if t is not None:
            _nhan(t)
    # phần còn lại theo điểm — vẫn cân nhóm 6/tầng để khay đủ 4 tầng lựa chọn
    gio = {"L1": 0, "L2": 0, "L3": 0}
    for c in cham:
        if len(ra) >= so:
            break
        if c["id"] in da or gio[c["lop"]] >= 6:
            continue
        gio[c["lop"]] += 1
        _nhan(c)
    # `suat_ref` là SÀN chứ không phải TRẦN (user chốt 07/09: "cái gì nhiều hơn
    # thì ưu tiên đổ vào"): stock cạn thì ref đổ tiếp cho đầy khay. Life In sống
    # bằng ref chính là nhánh này — cửa geo đã loại sạch stock từ trước.
    for c in refs:
        if len(ra) >= so:
            break
        _nhan(c)
    ra.sort(key=lambda c: -c["diem"])
    # GỘP BẢN TRÙNG (user chốt 09/09): cùng nguồn + cùng tiêu đề về một thẻ,
    # bản còn lại nằm ở `ban_khac` nên vẫn chọn được. Đo 64% khay production có
    # bản trùng — người dựng phải lướt qua 13 thẻ y hệt. Gộp SAU khi xếp điểm
    # để bản đại diện là bản điểm cao nhất.
    return sdb.gop_ban_trung(ra)
