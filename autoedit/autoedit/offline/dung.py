r"""Đổ ỨNG VIÊN + chọn mặc định cho các khối — pha 2 của Offline.

Ứng viên tra từ Library (sotra.tra — 4 lớp giao nhau, suất REF giữ chỗ).
Chọn mặc định theo bộ luật nghiệm thu ở prototype V5:
  - luật 60s: cùng clip không xuất hiện 2 lần trong cửa sổ
  - chốt neo: mỗi CHOT_NEO_S phải có >=1 khối lớp trực chỉ
  - cấm 3 khối liền cùng lớp không khí (trôi thành slideshow)
"Thắng ở đây" chỉ là ĐỀ XUẤT — điểm chất lượng thật chờ phản biện ngoài
(người thay/khóa sổ/retention) ghi vào su_kien.
"""

from __future__ import annotations

CUA_SO_LAP_S = 60.0
CHOT_NEO_S = 30.0


def do_ung_vien(conn, khoi: list, lop, chu_the_tap: list[str],
                uu_tien_nguon: str = "", so_moi_khoi: int = 12,
                bo_nguon: tuple = (), geo_tap: str = "", tap: str = "") -> list[list[dict]]:
    """Mỗi khối một danh sách ứng viên (đã xếp lớp/điểm) từ Library.

    bo_nguon (user chốt 06/09): chương AUTO sau mốc AVD ít người xem tới —
    không đốt license Envato vào đó, chỉ dùng pexels/pixabay/ref/kho.
    """
    from autoedit.sotra.tra import tra

    ra = []
    for i, k in enumerate(khoi):
        o = lop[i]
        uv = tra(conn, {"L0": chu_the_tap, "L1": o.truc_chi,
                        "L2": o.ngu_canh, "L3": o.khong_khi},
                 so=so_moi_khoi + (6 if bo_nguon else 0),
                 uu_tien_nguon=uu_tien_nguon, can_neo=bool(o.neo), seed=i,
                 geo_tap=geo_tap, tap=tap)
        if bo_nguon:
            uv = [c for c in uv if c["nguon"] not in bo_nguon]
        # LUẬT "clip ngắn hơn phần nói thì loại" (06/09) — USER ĐẬP BỎ 07/09:
        # "vô tình làm lãng phí rất nhiều source. Tôi vẫn chấp nhận cho source
        # đó vào. Tôi sẽ tùy chỉnh bằng cách tạo một khối nhỏ trong khối lớn
        # vừa với source bằng cách add shot." Clip ngắn không gây hỏng draft:
        # thay_mau đã có sẵn đường xuống cấp (chậm tới 0.8x rồi freeze đuôi).
        #
        # SUẤT GIỮ CHỖ REF phải sống sót khâu gọn khay: `tra()` trả ref Ở CUỐI
        # danh sách nên `[:so_moi_khoi]` chặt đúng phần đuôi. Đo trên C1 07/09:
        # 72 cảnh ref được cấp cho 36 khối, 59 MẤT VÌ CẮT, chỉ 4 cảnh vào khay.
        ref_uv = [c for c in uv if c["nguon"] == "ref"]
        khac = [c for c in uv if c["nguon"] != "ref"]
        uv = khac[:max(0, so_moi_khoi - len(ref_uv))] + ref_uv
        ra.append([{"id": c["id"], "nguon": c["nguon"], "tieu_de": c["tieu_de"],
                    "lop": c["lop"], "diem": c["diem"],
                    "url_anh": c.get("url_anh", ""), "url_video": c.get("url_video", ""),
                    "geo": c.get("geo", ""), "dai_s": c.get("dai_s", 0),
                    # t0/t1 để UI gắn #t= — không có thì hover ref tải cả file 1GB
                    "t0": c.get("t0", 0), "t1": c.get("t1", 0)}
                   for c in uv])
    return ra


def chon_mac_dinh(khoi: list, ung_vien: list[list[dict]], than: float = 0.0,
                  noi_tiep: list | None = None) -> list[int]:
    """Chỉ số ứng viên mặc định mỗi khối (-1 = không có) theo 3 luật trên.

    `than` > 0 bật CHẢY TIẾP (user chốt 07/09 tối): khối ngắn hơn chuẩn kênh thì
    khối kế dùng TIẾP chính clip đó, ngay sau đoạn vừa dùng — người xem thấy một
    shot dài đúng nhịp kênh thay vì hai shot vụn.

    Phân biệt rõ với LẶP (clip quay lại sau vài chục giây — vẫn cấm bởi luật
    60s): chảy tiếp là hai khối LIỀN KỀ, nguồn còn đủ dài. Vì sao cần (SEQUENCE
    3b): luật 60s vô tình ép ĐỔI HÌNH MỖI HƠI THỞ — người đọc thở 2,2s/lần thì
    video cắt 2,2s/lần, bất kể kênh ref giữ shot 4,7s. Đo trên C2: 43 shot
    median 3,24s (lệch -32%) -> 32 shot median 4,71s (lệch 0%).

    `noi_tiep` (nếu truyền) được điền True ở khối chảy tiếp.
    """
    dung_luc: dict[str, float] = {}
    cha_dung = 0.0            # thời lượng shot hiện tại đã kéo dài bao nhiêu
    con_nguon = 0.0           # nguồn của clip đang dùng còn lại bao nhiêu giây
    dang = -1                 # vị trí ứng viên đang dùng ở khối trước
    lop_gan: list[str] = []
    neo_cuoi = -999.0
    chon: list[int] = []
    for i, k in enumerate(khoi):
        uv = ung_vien[i]
        if noi_tiep is not None:
            noi_tiep.append(False)
        if not uv:
            chon.append(-1)
            dang, cha_dung, con_nguon = -1, 0.0, 0.0
            continue
        dai_khoi = float(k.v1 - k.v0) + max(0.0, float(getattr(k, "tho", 0) or 0))
        # ---- CHẢY TIẾP: giữ nguyên clip của khối trước nếu còn hợp lệ ----
        if (than > 0 and dang >= 0 and chon and chon[-1] >= 0
                and cha_dung + dai_khoi <= than * 1.3
                and con_nguon >= dai_khoi):
            truoc = ung_vien[i - 1][chon[-1]]
            vi_tri = next((j for j, u in enumerate(uv) if u["id"] == truoc["id"]), None)
            if vi_tri is None:
                # Clip đang chiếu THƯỜNG KHÔNG nằm trong khay khối kế (đo trên
                # C2: chỉ 8/39 chỗ có) vì mỗi khối tra Library bằng từ khóa
                # riêng. Chảy tiếp là quyết định về TIMELINE chứ không phải về
                # khay, nên đưa nó vào đầu khay khối này — editor nhìn thấy
                # đúng clip đang chiếu và đổi được nếu muốn.
                uv.insert(0, truoc)
                vi_tri = 0
            chon.append(vi_tri)
            if noi_tiep is not None:
                noi_tiep[-1] = True
            cha_dung += dai_khoi
            con_nguon -= dai_khoi
            lop_gan.append(truoc.get("lop", "L3"))
            continue
        can_l1 = (k.v0 - neo_cuoi) >= CHOT_NEO_S
        ba_l3 = len(lop_gan) >= 2 and lop_gan[-1] == "L3" and lop_gan[-2] == "L3"
        c = -1
        for khat_khe in (True, False):          # vòng 1 đủ luật, vòng 2 nới
            for j, u in enumerate(uv):
                gan = dung_luc.get(u["id"])
                if gan is not None and k.v0 - gan < CUA_SO_LAP_S:
                    continue                     # luật 60s là CỨNG cả 2 vòng
                if khat_khe and (can_l1 or ba_l3) and u["lop"] != "L1":
                    continue
                c = j
                break
            if c >= 0:
                break
        if c < 0:
            c = 0
        chon.append(c)
        u = uv[c]
        dang = c
        cha_dung = dai_khoi
        # `dai_s` rỗng ở HẦU HẾT clip kho (đo C2: 39/39) — nếu coi rỗng là "hết
        # nguồn" thì chảy tiếp không bao giờ chạy. Lạc quan ở đây, KIỂM THẬT lúc
        # ráp: thay_mau đo độ dài file thật, hụt thì tự chuyển sang clip riêng.
        dai_nguon = float(u.get("dai_s") or 0) or (than * 2 if than > 0 else 0.0)
        con_nguon = max(0.0, dai_nguon - dai_khoi)
        dung_luc[u["id"]] = k.v0
        lop_gan.append(u["lop"])
        if u["lop"] == "L1":
            neo_cuoi = k.v0
    return chon


def kiem_lap(khoi: list, ung_vien: list[list[dict]], chon: list[int]) -> list[int]:
    """Chỉ số các khối vi phạm 60s (UI tô đỏ; rào kiểm sau phân tích)."""
    xau = set()
    for i, k in enumerate(khoi):
        if chon[i] < 0:
            continue
        uid = ung_vien[i][chon[i]]["id"]
        for j in range(i):
            if chon[j] < 0:
                continue
            if (ung_vien[j][chon[j]]["id"] == uid
                    and abs(k.v0 - khoi[j].v0) < CUA_SO_LAP_S):
                xau.update((i, j))
    return sorted(xau)


def do_lai_khay(hd: dict, conn, so_moi_khoi: int = 12,
                may_doi: list | None = None) -> int:
    """Tra lại Library cho MỌI khối, bổ sung khay — GIỮ NGUYÊN lựa chọn của người.

    Vì sao cần (07/09 khuya): hợp đồng sinh TRƯỚC một bản vá nguồn (vd bản vá
    suất giữ chỗ ref) thì khay của nó thiếu hẳn một nguồn, mà nút "Phân tích"
    chỉ hiện khi chương CHƯA có hợp đồng. Phân tích lại thì mất sạch phần đã
    chỉnh ở pha 2 — đúng thứ không được phép làm với công của người.

    Dùng LỚP NGHĨA ĐÃ LƯU trong hợp đồng nên KHÔNG gọi LLM.

    Luật (QĐ6, user chốt 08/09): chỉ lựa chọn của NGƯỜI được ghim lại; lựa chọn
    của MÁY được chọn LẠI theo khay mới. Khối chưa ai chọn (`chon == -1`) vẫn
    để trống — người vẫn quyết.

    Vì sao phải phân biệt (đo thật 08/09, chương H/LI103): khay sinh trước cửa
    geo cho 9 khối máy chọn ra clip lệch địa danh ("Sixth street in New York
    City" cho câu về Afghanistan). Bấm nút này rồi dựng lại thì draft RA Y HỆT,
    vì bản cũ ghim mọi lựa chọn đang có — kể cả lựa chọn máy đặt theo luật cũ.
    Người dùng bấm mà tưởng đã chữa; xoá tay `chon` của máy rồi chạy mới đổi
    được 0/9 -> 9/9 khớp geo.

    Chọn lại bằng chính `chon_mac_dinh` (BH4: một khái niệm, một hàm) nên vẫn
    theo luật 60s + chảy tiếp. Lưu ý thật thà: hàm đó tính như thể nó cầm trịch
    cả chương, trong khi khối của người giữ lựa chọn riêng — nên sổ 60s của nó
    lệch ở những khối đó. Vi phạm còn lại do `kiem_lap` soi ra và UI tô đỏ,
    không giấu đi.

    `may_doi` (nếu truyền) nhận chỉ số các khối MÁY đã bị chọn lại — UI phải
    nói ra con số này, đổi ngầm dưới tay người dùng là đúng họ nhà lỗi BH5.

    Trả số khối được bổ sung.
    """
    from autoedit.sotra.tra import tra

    doi = 0
    ds_khoi = hd.get("khoi") or []
    may_da_chon = [False] * len(ds_khoi)      # khối MÁY đã chọn -> chọn lại
    id_may_cu: list = [None] * len(ds_khoi)   # để biết khối nào THẬT SỰ đổi
    # Người dựng sửa ở MIẾNG HÌNH; khối không mang cờ nào (đo chương H 08/09:
    # khoi 0/14 cờ, hinh 6/15). Xét cờ ở khối thì mọi khối đều thành "máy".
    nguoi_o_mieng = {h.get("khoi_goc") for h in (hd.get("hinh") or [])
                     if h.get("nguoi_sua")}
    for i, k in enumerate(ds_khoi):
        cu = list(k.get("uv") or [])
        c = k.get("chon", -1)
        co_chon = 0 <= c < len(cu)
        cua_nguoi = bool(k.get("nguoi_sua")) or i in nguoi_o_mieng
        may_da_chon[i] = co_chon and not cua_nguoi
        if may_da_chon[i]:
            id_may_cu[i] = cu[c]["id"]
        dang_chon = cu[c] if (co_chon and cua_nguoi) else None
        try:
            moi = tra(conn, {"L0": hd.get("chu_the_tap") or [],
                             "L1": k.get("L1") or [], "L2": k.get("L2") or [],
                             "L3": k.get("L3") or []},
                      so=so_moi_khoi, uu_tien_nguon=hd.get("uu_tien_nguon") or "",
                      can_neo=bool(k.get("neo")), seed=i,
                      geo_tap=hd.get("dia_danh") or "", tap=hd.get("ma_tap") or "")
        except Exception:  # noqa: BLE001 — một khối hỏng không giết cả chương
            continue
        if not moi:
            continue
        gon = [{"id": c2["id"], "nguon": c2["nguon"], "tieu_de": c2["tieu_de"],
                "lop": c2["lop"], "diem": c2["diem"],
                "url_anh": c2.get("url_anh", ""), "url_video": c2.get("url_video", ""),
                "geo": c2.get("geo", ""), "dai_s": c2.get("dai_s", 0),
                "t0": c2.get("t0", 0), "t1": c2.get("t1", 0)} for c2 in moi]
        if dang_chon is not None:
            vi = next((j for j, u in enumerate(gon)
                       if u["id"] == dang_chon["id"]), None)
            if vi is None:                    # clip người chọn không còn trong
                gon.insert(0, dang_chon)      # kết quả tra -> giữ chỗ đầu khay
                vi = 0
            k["chon"] = vi
        else:
            k["chon"] = -1                    # chưa ai chọn: KHÔNG chọn hộ
        k["uv"] = gon
        doi += 1
        # DẢI HÌNH cũng phải đổ (pha 2 và bước ráp draft đọc khay của MIẾNG,
        # không phải của khối) — chỉ đổ khối thì người vẫn không thấy gì.
        for h in hd.get("hinh") or []:
            if h.get("khoi_goc") != i:
                continue
            c_h = h.get("chon", -1)
            uv_h = h.get("uv") or []
            chon_h = (uv_h[c_h] if (0 <= c_h < len(uv_h) and h.get("nguoi_sua"))
                      else None)
            moi_h = list(gon)
            if chon_h is not None:
                vi = next((j for j, u in enumerate(moi_h)
                           if u["id"] == chon_h["id"]), None)
                if vi is None:
                    moi_h.insert(0, chon_h)
                    vi = 0
                h["chon"] = vi
            else:
                h["chon"] = -1
            h["uv"] = moi_h

    if any(may_da_chon):
        _chon_lai_ho_may(hd, ds_khoi, may_da_chon, id_may_cu, may_doi)
    return doi


def _chon_lai_ho_may(hd: dict, ds_khoi: list, may_da_chon: list,
                     id_may_cu: list, may_doi: list | None = None) -> None:
    """Đặt lại lựa chọn cho các khối MÁY đã chọn, rồi dội xuống dải hình."""
    from types import SimpleNamespace

    # `chon_mac_dinh` đọc khối bằng THUỘC TÍNH (k.v0/k.v1/k.tho) vì lúc phân
    # tích nó nhận dataclass; ở đây hợp đồng đã là dict nên phải bọc lại.
    ns = [SimpleNamespace(v0=float(k.get("v0") or 0), v1=float(k.get("v1") or 0),
                          tho=float(k.get("tho") or 0)) for k in ds_khoi]
    # ID người đang giữ — `chon_mac_dinh` được phép CHÈN clip vào đầu khay
    # (chảy tiếp) nên mọi chỉ số cũ đều có thể lệch; ghim lại theo ID sau.
    giu = {i: k["uv"][k["chon"]]["id"] for i, k in enumerate(ds_khoi)
           if 0 <= k.get("chon", -1) < len(k.get("uv") or [])}
    moi = chon_mac_dinh(ns, [k.get("uv") or [] for k in ds_khoi],
                        than=float((hd.get("framing") or {}).get("than") or 0))
    for i, k in enumerate(ds_khoi):
        if may_da_chon[i] and moi[i] >= 0:
            k["chon"] = moi[i]
            if may_doi is not None and k["uv"][moi[i]]["id"] != id_may_cu[i]:
                may_doi.append(i)
        elif i in giu:
            vi = next((j for j, u in enumerate(k.get("uv") or [])
                       if u["id"] == giu[i]), None)
            k["chon"] = vi if vi is not None else -1

    for h in hd.get("hinh") or []:
        i = h.get("khoi_goc")
        if h.get("nguoi_sua") or h.get("noi_tiep") or not (0 <= (i or -1) < len(ds_khoi)):
            continue                     # người chọn / miếng chảy tiếp: không đụng
        if not may_da_chon[i]:
            continue
        k = ds_khoi[i]
        if not (0 <= k.get("chon", -1) < len(k.get("uv") or [])):
            continue
        cid = k["uv"][k["chon"]]["id"]
        h["uv"] = list(k["uv"])
        h["chon"] = next((j for j, u in enumerate(h["uv"]) if u["id"] == cid), -1)


def lam_tuoi_ref(hd: dict, conn) -> bool:
    """Thay ứng viên REF ĐỜI CŨ trong hợp đồng bằng bản cắt-theo-cảnh mới.

    Bug user bắt 06/09: sequence phân tích TRƯỚC đợt cắt-theo-cảnh nên uv còn
    mang khúc ref cũ — thiếu t0/t1 (UI phát cả file 52 phút) và clip đã bị
    loai_tru. Chạy lúc ĐỌC hợp đồng (fail-open), trả True nếu có đổi.

    Luật: chỉ đụng mục nguon='ref' hỏng (thiếu t1 hoặc clip không còn sống);
    mục đang ĐƯỢC CHỌN thì giữ chỗ nhưng vá lại t0/t1 từ DB nếu tra được.
    """
    from autoedit.sotra.tra import tra

    doi = False
    tuoi_theo_khoi: dict[int, list[dict]] = {}

    def _tuoi(i: int) -> list[dict]:
        if i not in tuoi_theo_khoi:
            k = (hd.get("khoi") or [{}])[i] if i < len(hd.get("khoi") or []) else {}
            uv = tra(conn, {"L0": hd.get("chu_the_tap") or [],
                            "L1": k.get("L1") or [], "L2": k.get("L2") or [],
                            "L3": k.get("L3") or []},
                     so=12, uu_tien_nguon="ref", can_neo=bool(k.get("neo")),
                     seed=i, geo_tap=hd.get("dia_danh") or "",
                     tap=hd.get("ma_tap") or "")
            tuoi_theo_khoi[i] = [
                {"id": c["id"], "nguon": c["nguon"], "tieu_de": c["tieu_de"],
                 "lop": c["lop"], "diem": c["diem"],
                 "url_anh": c.get("url_anh", ""), "url_video": c.get("url_video", ""),
                 "geo": c.get("geo", ""), "dai_s": c.get("dai_s", 0),
                 "t0": c.get("t0", 0), "t1": c.get("t1", 0)}
                for c in uv if c["nguon"] == "ref"]
        return tuoi_theo_khoi[i]

    def _hong(u: dict) -> bool:
        if u.get("nguon") != "ref" or u.get("giu_cu"):
            return False               # giu_cu: đời cũ đang được chọn, đã vá — yên
        if not (float(u.get("t1") or 0) > 0):
            return True
        r = conn.execute("SELECT trang_thai FROM clip WHERE id=?",
                         (u.get("id"),)).fetchone()
        return r is None or r[0] != "song"

    def _thay(ds: list[dict], i_khoi: int, chon: int) -> tuple[list[dict], bool]:
        if not any(_hong(u) for u in ds):
            return ds, False
        moi, giu_chon = [], ds[chon] if 0 <= chon < len(ds) else None
        for j, u in enumerate(ds):
            if not _hong(u):
                moi.append(u)
            elif j == chon and giu_chon is not None:
                # mục đang chọn: giữ chỗ, VÁ t0/t1 từ DB (clip loai_tru vẫn còn
                # dòng) + cờ giu_cu — thiếu cờ thì lần đọc nào cũng "hỏng" lại,
                # hợp đồng bị ghi lại vô hạn (test bắt được 06/09)
                r = conn.execute("SELECT t0, t1 FROM clip WHERE id=?",
                                 (u.get("id"),)).fetchone()
                if r is not None:
                    u["t0"], u["t1"] = r[0], r[1]
                u["giu_cu"] = 1
                moi.append(u)
        co = {u["id"] for u in moi}
        moi.extend(u for u in _tuoi(i_khoi) if u["id"] not in co)
        return moi, True

    for i, k in enumerate(hd.get("khoi") or []):
        ds, d1 = _thay(k.get("uv") or [], i, int(k.get("chon", -1)))
        if d1:
            k["uv"] = ds
            doi = True
    for h in hd.get("hinh") or []:
        i = int(h.get("khoi_goc") or 0)
        ds, d1 = _thay(h.get("uv") or [], min(i, max(0, len(hd.get("khoi") or []) - 1)),
                       int(h.get("chon", -1)))
        if d1:
            h["uv"] = ds
            doi = True
    return doi
