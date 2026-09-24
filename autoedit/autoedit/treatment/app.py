r"""Bàn kịch bản — tầng web, chạy CỔNG RIÊNG (mặc định 9121).

Vì sao không nhét vào app 9118 (user lo 15/09: *"code luôn trên production bây
giờ sẽ ảnh hưởng tới công việc của team"*): app này khởi động/khởi động lại bao
nhiêu lần cũng không cắt UI của người đang dựng, và lỗi import ở đây không giết
tiến trình kia. Khi nào chạy ổn định thì gắn một dòng link vào nav của 9118.

Danh tính: header `X-Remote-User` do cổng CRM đặt — cùng quy ước với 9118 để đặt
sau cùng một cổng gác là chạy ngay. Không có header thì CHỈ ĐỌC (401 khi ghi):
2-3 người làm cùng lúc, không biết ai là ai thì không khoá được gì.

Chạy:  python -m autoedit.treatment.app --port 9121
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from fastapi import Body, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from autoedit.treatment import dong as mdong
from autoedit.treatment.kho import Kho, KhoaBiGiu

TRANG = Path(__file__).parent / "static" / "treatment.html"

# Số dòng mỗi lượt gọi LLM. 8 là chỗ đo được: 17-18 dòng/lượt vẫn qua,
# 20 dòng thì JSON cụt (SE001/C6, 23/09). Để rộng gấp đôi mức an toàn.
CO_LO = 8


def _loopback(request: Request) -> bool:
    host = (request.client.host if request.client else "") or ""
    return host in ("127.0.0.1", "::1", "localhost")


def _tin_header(request: Request) -> bool:
    """Có được tin `X-Remote-User` không?

    Luật cụm OUTLIERY (docs/bao-mat-internet.md, GD1 — 4 app từng tin header vô
    điều kiện, curl một cái là thành Owner): chỉ tin khi BẬT CỜ và client là
    loopback, vì cổng CRM proxy từ 127.0.0.1 và đã vứt header người ngoài gửi lên.

    Chưa đặt cờ thì giữ đường cũ (tin header) để chạy tay trên máy mình không
    vướng — bật cờ khi đặt sau proxy thật.
    """
    if os.getenv("KICHBAN_TRUST_PROXY", "").strip() != "1":
        return True
    return _loopback(request)


COOKIE_AI = "kichban_ai"


def chuan_ten(ten: str) -> str:
    """Chuẩn hoá tên người dùng — CÙNG KHUÔN với tên CRM gửi xuống
    ('Nguyễn Văn A' -> 'nguyenvana'): bỏ dấu, hạ chữ, chỉ giữ chữ-số-._-

    Tên này là KHOÁ CHƯƠNG. Không chuẩn hoá thì 'Hải' và 'hai' thành hai người,
    và dấu '/' lọt vào là hỏng cả đường dẫn lẫn câu SQL của khoá.
    """
    t = unicodedata.normalize("NFD", (ten or "").strip().lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"[^a-z0-9._-]", "", t)[:32]


def _nguoi(request: Request) -> str:
    """Danh tính, theo thứ tự: CRM (nếu tin được) -> tên tự khai trong cookie.

    Tên tự khai là đường CHƯA NỐI CRM (user chốt 15/09: cho một cổng riêng dùng
    ngay). Nó ĐỦ để khoá chương khỏi giẫm chân nhau, nhưng KHÔNG phải xác thực —
    trong mạng nội bộ ai cũng khai được tên bất kỳ. Nối vào cổng CRM thì header
    thắng, không ai mượn được tên người khác nữa.
    """
    if _tin_header(request):
        ten = (request.headers.get("x-remote-user") or "").strip()
        if ten:
            return ten
    return chuan_ten(request.cookies.get(COOKIE_AI) or "")


HANH_DONG_SUA = "sua"


def _co_hanh_dong(request: Request) -> set[str]:
    """Cờ hành động do GATEWAY tính và tiêm (`X-Remote-Actions`, Permissions v2).

    App CHỈ TIN CỜ, KHÔNG tự tính lại quyền theo level (luật ghim #2 của cụm):
    Owner tick lẻ cho một người ở trang Permissions thì phải chảy sang ngay lượt
    sau, mà tick lẻ chỉ hiện ra ở cờ này. Thiếu header -> rỗng -> fail-closed.
    """
    if not _tin_header(request):
        return set()
    return {x.strip() for x in (request.headers.get("x-remote-actions") or "").split(",")
            if x.strip()}


def _xem_duoc(request: Request) -> str:
    """Ai cũng xem được (đã qua cửa `vao` của gateway) — trả tên để ghi sổ."""
    return _nguoi(request)


def _ghi_duoc(request: Request) -> str:
    """Cửa gác GHI: L2 chỉ xem, Manager/Owner mới thêm sửa (user chốt 23/09).

    Đặt ở TẦNG GHI chứ không phải ở chỗ ẩn nút: người xem mở tab cũ bấm lưu thì
    vẫn phải bị chặn.
    """
    ai = _nguoi(request)
    if not ai:
        raise HTTPException(401, "Chưa đăng nhập — cổng CRM chưa gửi X-Remote-User.")
    if HANH_DONG_SUA not in _co_hanh_dong(request):
        raise HTTPException(403, "Bạn đang ở chế độ chỉ xem. Quyền thêm/sửa dành cho "
                                 "Manager trở lên — Owner cấp ở General › Permissions.")
    return ai


def _ban_trang() -> str:
    """Số hiệu bản của trang = giờ sửa file HTML.

    Vì sao cần (đo thật 24/09): bản vá lên máy chủ tối hôm trước, nhưng tab của
    người dùng mở từ trước đó vẫn chạy JS CŨ — 14:39 hôm sau vẫn ghi ra chữ
    dính. Trang nạp JS đúng một lần lúc mở, tool này thì team để tab cả ngày.
    Lấy theo giờ sửa file nên không ai phải nhớ tăng số bằng tay.
    """
    try:
        return str(int(TRANG.stat().st_mtime))
    except OSError:
        return "0"


# Hai tông user đang dùng (24/09). Đây là GIÁ TRỊ KHỞI ĐIỂM, không phải chỗ
# chốt: Owner sửa trong sổ của tập thì bản sửa thắng. Ghi cứng đoạn này trong
# code nghĩa là mỗi lần đổi mood phải sửa code — nên nó chỉ đứng ở đây làm mồi.
TONG_MAC_DINH = [
    {"ma": "nuoc", "loai": "tong", "ten": "dưới nước",
     "pr": "",
     "chu": "Photorealistic. Mood and tone: Dark & mysterious mood, "
            "dim natural underwater lighting, no harsh shadows, "
            "strictly no artificial light. "
            "Consistent mood, tone, and graphic style across all shots."},
    {"ma": "can", "loai": "tong", "ten": "trên cạn",
     "pr": "",
     "chu": "Photorealistic. Mood and tone: Dark & mysterious mood. "
            "Consistent mood, tone, and graphic style across all shots."},
]


def _ma_sach(ten: str, da_co: dict) -> str:
    """Tên tiếng Việt -> mã dùng được làm TÊN FILE ref.

    `duong_ref` chỉ nhận [A-Za-z0-9_-]; tên có dấu và dấu cách mà đưa thẳng vào
    là tải ref lên nhận 400 — lỗi chỉ lòi ra lúc người dùng bấm, không phải lúc
    sinh đề xuất.
    """
    t = unicodedata.normalize("NFD", ten.strip().lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn").replace("đ", "d")
    t = re.sub(r"[^a-z0-9]+", "_", t).strip("_")[:40] or "ts"
    goc, n = t, 2
    while t in da_co:
        t = f"{goc}_{n}"
        n += 1
    da_co[t] = 1
    return t


def tao_app(kho: Kho, dich=None, goi_y=None, ky_thuat=None) -> FastAPI:
    """`kho`, `dich`, `goi_y`, `ky_thuat` tiêm từ ngoài: test chạy DB tạm + đồ giả, không mạng."""
    app = FastAPI(title="Bàn kịch bản RenderY")

    # ------------------------------------------------------------- trang
    @app.get("/", response_class=HTMLResponse)
    def trang():
        # no-store: lần tải lại nào cũng phải ra bản mới nhất. Không đặt thì
        # trình duyệt giữ lại bản cũ và người dùng bấm tải lại vẫn thấy y nguyên.
        return HTMLResponse(TRANG.read_text(encoding="utf-8"),
                            headers={"Cache-Control": "no-store"})

    @app.get("/health")
    def health():
        return {"ok": True, "kho": str(kho.duong)}

    @app.post("/api/toi")
    def khai_ten(request: Request, response: Response, than: dict = Body(...)):
        """Tự khai tên khi CHƯA nối cổng CRM. Không mật khẩu: đây là chỗ để hai
        người biết nhau đang giữ chương nào, không phải cửa bảo mật."""
        ten = chuan_ten(than.get("nguoi") or "")
        if not ten:
            raise HTTPException(400, "Tên trống hoặc chỉ có ký tự lạ.")
        response.set_cookie(COOKIE_AI, ten, max_age=60 * 60 * 24 * 30,
                            httponly=False, samesite="lax")
        return {"nguoi": ten}

    @app.get("/api/suc-khoe")
    def suc_khoe():
        """Sức khoẻ SÂU theo khuôn của cụm (`nen/common/suc_khoe.py`): gateway đọc
        `trang_thai` + `mo_dun` để vẽ bảng giám sát.

        Thiếu khoá là **cảnh báo**, không phải lỗi: tool vẫn nhập/chia dòng/copy
        được, chỉ mất phần dịch và kiểm chứng. Báo đỏ oan thì lần sau không ai
        nhìn bảng nữa — chỉ kho hỏng mới là đỏ, vì lúc đó mất chữ của người viết.
        """
        mo_dun = []
        try:
            n = len(kho.ds_tap())
            mo_dun.append({"ten": "kho", "trang_thai": "ok",
                           "chi_tiet": f"{n} tập · {kho.duong}"})
        except Exception as exc:  # noqa: BLE001
            mo_dun.append({"ten": "kho", "trang_thai": "loi", "chi_tiet": str(exc)[:120]})

        from autoedit.treatment.dich import LLM

        try:
            m = LLM()
            co_khoa, ten_model = bool(m.key and m.url), m.model
        except Exception:  # noqa: BLE001
            co_khoa, ten_model = False, "?"
        mo_dun.append({
            "ten": "khoa_llm",
            "trang_thai": "ok" if co_khoa else "canh_bao",
            "chi_tiet": (f"model {ten_model}" if co_khoa
                         else "chưa cấp — General › API Keys › Theo app › Treatment")})

        muc = ("loi" if any(m["trang_thai"] == "loi" for m in mo_dun)
               else "canh_bao" if any(m["trang_thai"] == "canh_bao" for m in mo_dun)
               else "ok")
        return {"trang_thai": muc, "mo_dun": mo_dun}

    @app.get("/api/toi")
    def toi(request: Request):
        """Trang cần biết MÌNH là ai để biết chương nào là khoá của mình, chương
        nào của người khác. Không có header thì trả rỗng — trang tự chuyển sang
        chế độ chỉ xem thay vì để người ta gõ cả buổi rồi 401 lúc lưu."""
        return {"nguoi": _nguoi(request),
                "sua_duoc": HANH_DONG_SUA in _co_hanh_dong(request),
                "ban": _ban_trang()}

    # --------------------------------------------------------------- tập
    @app.get("/api/tap")
    def ds_tap():
        return kho.ds_tap()

    @app.post("/api/tap")
    def tao_tap(request: Request, than: dict = Body(...)):
        _ghi_duoc(request)
        try:
            kho.tao_tap((than.get("ma") or "").strip(), (than.get("ten") or "").strip())
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True}

    @app.get("/api/tap/{tap}")
    def ds_chuong(tap: str):
        return kho.ds_chuong(tap)

    @app.post("/api/tap/{tap}/chuong")
    def tao_chuong(tap: str, request: Request, than: dict = Body(...)):
        _ghi_duoc(request)
        try:
            return {"ma": kho.tao_chuong(tap, (than.get("ma") or "").strip())}
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    # ----------------------------------------------------------------- sổ
    @app.get("/api/tap/{tap}/so")
    def doc_so(tap: str):
        """Sổ dùng chung cả tập. Sổ rỗng thì đưa sẵn HAI TÔNG mặc định user
        đang dùng: prompt nào cũng phải có đoạn tông ghép ở cuối, trả rỗng là
        prompt đầu tiên của mọi tập đều cụt. Chưa ghi xuống — sửa mới ghi."""
        ds = kho.ds_so(tap)
        if not any(x["loai"] == "tong" for x in ds):
            ds = TONG_MAC_DINH + ds
        return ds

    @app.put("/api/tap/{tap}/so")
    def luu_so(tap: str, request: Request, than: dict = Body(...)):
        _ghi_duoc(request)
        try:
            kho.luu_so(tap, than.get("so") or [])
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True}

    CO_LO_CANH = 25        # cảnh mỗi lượt gọi — JSON dài là cụt (bài học 23/09)

    @app.post("/api/tap/{tap}/so/goi-y")
    def goi_y_tai_san(tap: str, request: Request):
        """Quét CẢ TẬP rồi gọi tên đủ nhân vật / đạo cụ / bối cảnh.

        Đúng bước 2 trong quy trình tay của user, nhưng khác hai chỗ — và cả
        hai là lý do tool tồn tại: chat quét một lần rồi quên, còn đây quét cả
        tập và GỘP TRÙNG; và đề xuất KHÔNG tự ghi vào sổ, người duyệt mới nhận
        (luật cứng #5: không tự quyết hộ user).
        """
        _ghi_duoc(request)
        if goi_y is None:
            raise HTTPException(503, "Chưa bật bộ gợi ý.")
        canh: list[str] = []
        for c in kho.ds_chuong(tap):
            for d in kho.doc(tap, c["ma"])["dong"]:
                canh += [x["t"] for x in mdong.doc_canh(d)]
        if not canh:
            raise HTTPException(400, "Tập này chưa có cảnh nào — viết treatment trước.")

        ra: list[dict] = []
        thay: dict[str, int] = {}
        loi = ""
        for k in range(0, len(canh), CO_LO_CANH):
            try:
                phan = goi_y.goi_y(canh[k:k + CO_LO_CANH])
            except Exception as exc:  # noqa: BLE001 — giữ phần đã quét
                loi = str(exc)
                break
            for x in phan or []:
                if (x.get("loai") or "") not in ("nhan_vat", "dao_cu", "boi_canh"):
                    continue
                ten = (x.get("ten") or "").strip()
                khoa = ten.lower()
                if not ten or khoa in thay:
                    continue
                thay[khoa] = 1
                ra.append({"ma": _ma_sach(ten, thay), "loai": x["loai"], "ten": ten,
                           "chu": (x.get("chu") or "").strip(),
                           "pr": (x.get("pr") or "").strip(), "ref": False})
        if loi and not ra:
            raise HTTPException(502, f"Gợi ý hỏng: {loi}")
        return {"goi_y": ra, "quet": len(canh), "loi": loi}

    # ------------------------------------------------------------ ref
    @app.post("/api/tap/{tap}/so/{ma}/ref")
    async def tai_ref(tap: str, ma: str, request: Request, tep: UploadFile = File(...)):
        """Nhận file ref của một tài sản. Đọc THEO KHÚC và đếm dọc đường: đọc
        cả file vào bộ nhớ rồi mới kiểm cỡ là mở cửa cho một lần tải 10GB."""
        _ghi_duoc(request)
        duoi = Path(tep.filename or "").suffix.lower()
        try:
            dich = kho.duong_ref(tap, ma, duoi)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

        dich.parent.mkdir(parents=True, exist_ok=True)
        tam = dich.with_suffix(dich.suffix + ".dang-tai")
        n = 0
        try:
            with tam.open("wb") as f:
                while True:
                    khuc = await tep.read(1 << 20)
                    if not khuc:
                        break
                    n += len(khuc)
                    if n > kho.REF_TOI_DA:
                        raise HTTPException(
                            413, f"File quá {kho.REF_TOI_DA // (1024 * 1024)}MB.")
                    f.write(khuc)
        except HTTPException:
            tam.unlink(missing_ok=True)
            raise
        if not n:
            tam.unlink(missing_ok=True)
            raise HTTPException(400, "File rỗng.")
        kho.xoa_ref(tap, ma)          # đổi đuôi thì đừng để lại bản cũ
        tam.replace(dich)
        return {"ok": True, "cỡ": n}

    @app.get("/api/tap/{tap}/so/{ma}/ref")
    def xem_ref(tap: str, ma: str):
        t = kho.ref_dang_co(tap, ma)
        if t is None:
            raise HTTPException(404, "Tài sản này chưa có ref.")
        return FileResponse(t, headers={"Cache-Control": "no-store"})

    @app.delete("/api/tap/{tap}/so/{ma}/ref")
    def xoa_ref(tap: str, ma: str, request: Request):
        _ghi_duoc(request)
        if not kho.xoa_ref(tap, ma):
            raise HTTPException(404, "Tài sản này chưa có ref.")
        return {"ok": True}

    # Khai TRƯỚC `/{tap}/{chuong}`: FastAPI khớp theo THỨ TỰ KHAI BÁO, để sau thì
    # "txt" bị nuốt làm mã chương và trả JSON chương rỗng thay vì bản .txt cả tập
    # (test `test_txt_toan_bo_ghep_dung_thu_tu_chuong` bắt đúng ca này).
    @app.get("/api/tap/{tap}/txt", response_class=PlainTextResponse)
    def txt_tap(tap: str, cot: str = "en"):
        """Cả tập, ghép theo thứ tự timeline H -> C1..Cn -> E, chương cách nhau
        một dòng trống. Voice ren theo CHƯƠNG nên bản này chỉ để soát lại."""
        phan = [mdong.xuat(kho.doc(tap, c["ma"])["dong"], cot)
                for c in kho.ds_chuong(tap)]
        return "\n".join(p for p in phan if p)

    # ------------------------------------------------------------ chương
    @app.get("/api/tap/{tap}/{chuong}")
    def doc(tap: str, chuong: str):
        return kho.doc(tap, chuong)

    @app.put("/api/tap/{tap}/{chuong}")
    def luu(tap: str, chuong: str, request: Request, than: dict = Body(...)):
        ai = _ghi_duoc(request)
        try:
            kho.luu(tap, chuong, than.get("dong") or [], than.get("outline") or "", ai)
        except KhoaBiGiu as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"ok": True}

    @app.post("/api/tap/{tap}/{chuong}/nap")
    def nap(tap: str, chuong: str, request: Request, than: dict = Body(...)):
        """Dán nguyên kịch bản vào -> danh sách dòng (dòng trống = ranh đoạn)."""
        ai = _ghi_duoc(request)
        d = mdong.nap(than.get("text") or "")
        try:
            kho.luu(tap, chuong, d, kho.doc(tap, chuong)["outline"], ai)
        except KhoaBiGiu as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"dong": d}

    # -------------------------------------------------------------- khoá
    @app.post("/api/tap/{tap}/{chuong}/giu")
    def giu(tap: str, chuong: str, request: Request):
        ai = _ghi_duoc(request)
        if not kho.giu(tap, chuong, ai):
            raise HTTPException(409, f"{kho.ai_giu(tap, chuong)} đang sửa chương này.")
        return {"ok": True}

    @app.post("/api/tap/{tap}/{chuong}/nha")
    def nha(tap: str, chuong: str, request: Request):
        kho.nha(tap, chuong, _ghi_duoc(request))
        return {"ok": True}

    # ------------------------------------------------------------- .txt
    @app.get("/api/tap/{tap}/{chuong}/txt", response_class=PlainTextResponse)
    def txt_chuong(tap: str, chuong: str, cot: str = "en"):
        return mdong.xuat(kho.doc(tap, chuong)["dong"], cot)

    # -------------------------------------------------------------- dịch
    @app.post("/api/tap/{tap}/{chuong}/dich")
    def dich_chuong(tap: str, chuong: str, request: Request):
        """Dịch các dòng CÒN THIẾU, chia LÔ nhỏ và lưu sau mỗi lô.

        Vì sao chia lô (đo thật 23/09 trên SE001): gửi cả chương 20 dòng thì
        Claude trả JSON CỤT — `Expecting ',' delimiter` — và mất trắng cả chương;
        chương 9-17 dòng thì qua. Lô nhỏ thì mỗi lượt JSON ngắn, và lô nào hỏng
        cũng KHÔNG cuốn theo phần đã dịch xong: bấm lại là nó dịch tiếp chỗ thiếu.

        Không đụng dòng người đã sửa tay, không dịch lại dòng đã có.
        """
        ai = _ghi_duoc(request)
        if dich is None:
            raise HTTPException(503, "Chưa bật bộ dịch.")
        d = kho.doc(tap, chuong)["dong"]
        can = [i for i, x in enumerate(d) if not (x.get("vi") or "").strip()
               and (x.get("en") or "").strip()]
        if not can:
            return {"dich": 0}

        xong, loi = 0, ""
        for k in range(0, len(can), CO_LO):
            phan = can[k:k + CO_LO]
            try:
                ra = dich.dich([d[i]["en"] for i in phan])
            except Exception as exc:  # noqa: BLE001 — giữ phần đã dịch, báo rõ
                loi = str(exc)
                break
            for i, v in zip(phan, ra):
                d[i]["vi"] = v
            xong += len(phan)
            try:
                kho.luu(tap, chuong, d, kho.doc(tap, chuong)["outline"], ai)
            except KhoaBiGiu as exc:
                raise HTTPException(409, str(exc)) from exc

        if loi and not xong:
            raise HTTPException(502, f"Dịch hỏng: {loi}")
        return {"dich": xong, "con_thieu": len(can) - xong,
                "loi": f"Dừng ở dòng {xong + 1}: {loi}" if loi else ""}

    # ---------------------------------------------------------- kỹ thuật
    CO_HOP_LE = ("WS", "MS", "CU", "ECU", "AERIAL")
    CO_LO_KT = 8        # mỗi mục trả 7 trường -> JSON dài gấp mấy lần bản dịch

    @app.post("/api/tap/{tap}/{chuong}/ky-thuat")
    def dien_ky_thuat(tap: str, chuong: str, request: Request):
        """Dịch nội dung cảnh sang prompt TIẾNG ANH và điền cột kỹ thuật.

        Chỉ đụng cảnh CÒN THIẾU (chưa có `pa`) — cùng luật với bản dịch: bấm lại
        là chạy tiếp chỗ dở, không đè lên chữ người đã sửa tay.

        LLM KHÔNG đụng `t` và KHÔNG chọn `tong`: hai thứ đó user giữ quyền.
        """
        ai = _ghi_duoc(request)
        if ky_thuat is None:
            raise HTTPException(503, "Chưa bật bộ sinh kỹ thuật.")
        d = kho.doc(tap, chuong)["dong"]
        ma_ts = {x["ma"] for x in kho.ds_so(tap)
                 if x["loai"] in ("nhan_vat", "dao_cu", "boi_canh")}
        so = [x for x in kho.ds_so(tap) if x["ma"] in ma_ts]

        can = []                        # (chỉ số dòng, chỉ số cảnh)
        for i, dg in enumerate(d):
            for j, c in enumerate(mdong.doc_canh(dg)):
                if not (c.get("pa") or "").strip():
                    can.append((i, j))
        if not can:
            return {"xong": 0, "con_thieu": 0, "loi": ""}

        xong, loi = 0, ""
        for k in range(0, len(can), CO_LO_KT):
            phan = can[k:k + CO_LO_KT]
            muc = []
            for i, j in phan:
                cs = mdong.doc_canh(d[i])
                muc.append({"id": f"{i}.{j}", "voice": d[i].get("en", ""),
                            "canh": cs[j]["t"], "thu_tu": f"{j + 1}/{len(cs)}"})
            try:
                ra = ky_thuat.ky_thuat(muc, so)
            except Exception as exc:  # noqa: BLE001 — giữ phần đã xong
                loi = str(exc)
                break
            # Khớp theo MÃ, không theo vị trí. ĐO THẬT 24/09 trên C1:
            # claude-sonnet-5 gửi 8 trả 7 — khớp theo vị trí thì cảnh 2 nhận
            # prompt của cảnh 3, sai câm không ai thấy. Khớp theo mã thì mục nó
            # nuốt chỉ làm cảnh đó để trống, bấm lại là chạy tiếp.
            theo_ma = {str(x.get("id")): x for x in ra if x.get("id") is not None}
            lam = [(i, j) for i, j in phan if f"{i}.{j}" in theo_ma]
            if not lam:
                loi = (f"trả {len(ra)} mục nhưng không mục nào mang mã cảnh "
                       "hợp lệ — không khớp được vào đâu")
                break
            for i, j in lam:
                x = theo_ma[f"{i}.{j}"]
                cs = mdong.doc_canh(d[i])
                c = cs[j]
                for khoa in ("pa", "pv", "goc", "cd", "sfx"):
                    if (x.get(khoa) or "").strip():
                        c[khoa] = str(x[khoa]).strip()
                if (x.get("co") or "").upper() in CO_HOP_LE:
                    c["co"] = x["co"].upper()
                ts = [m for m in (x.get("ts") or [])
                      if isinstance(m, str) and m in ma_ts]
                if ts:
                    c["ts"] = ts
                d[i] = mdong.ghi_canh(d[i], cs)
            xong += len(lam)
            try:                        # lưu sau MỖI lô, lô sau ngã không mất
                kho.luu(tap, chuong, d, kho.doc(tap, chuong)["outline"], ai)
            except KhoaBiGiu as exc:
                raise HTTPException(409, str(exc)) from exc

        if loi and not xong:
            raise HTTPException(502, f"Sinh kỹ thuật hỏng: {loi}")
        return {"xong": xong, "con_thieu": len(can) - xong,
                "loi": f"Dừng ở cảnh {xong + 1}: {loi}" if loi else ""}

    # ------------------------------------------------------------ bản lùi
    @app.get("/api/tap/{tap}/{chuong}/ban-cu")
    def ban_cu(tap: str, chuong: str):
        return kho.ban_cu(tap, chuong)

    @app.post("/api/tap/{tap}/{chuong}/lui")
    def lui(tap: str, chuong: str, request: Request, than: dict = Body(...)):
        ai = _ghi_duoc(request)
        try:
            kho.lui(tap, chuong, int(than.get("id") or 0), ai)
        except KhoaBiGiu as exc:
            raise HTTPException(409, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"ok": True}

    return app


def _kho_mac_dinh() -> Kho:
    goc = os.getenv("KICHBAN_DB") or (Path.home() / ".rendery" / "kichban.db")
    return Kho(goc)


class _Dich:
    """Đọc KÉT mỗi lượt dịch: Owner đổi khoá/model/nhà ở General là ăn ngay,
    không phải khởi động lại máy chủ."""

    def dich(self, cau):
        from autoedit.treatment.dich import LLM

        return LLM().dich(cau)


class _KyThuat:
    """Đọc KÉT mỗi lượt — Owner đổi khoá/model ở General là ăn ngay."""

    def ky_thuat(self, muc, tai_san):
        from autoedit.treatment.dich import LLM

        return LLM().ky_thuat(muc, tai_san)


def _ky_thuat_mac_dinh(kho: Kho):
    _ = kho
    return _KyThuat()


class _GoiY:
    """Đọc KÉT mỗi lượt như bộ dịch — Owner đổi khoá/model ở General là ăn ngay.

    Dùng CHUNG cấp phát `dich` của app: thêm một việc riêng trong apps.json chỉ
    để đo tiền tách bạch thì làm sau, không chặn đường chạy hôm nay.
    """

    def goi_y(self, canh):
        from autoedit.treatment.dich import LLM

        return LLM().goi_y(canh)


def _goi_y_mac_dinh(kho: Kho):
    _ = kho
    return _GoiY()


def _dich_mac_dinh(kho: Kho):
    _ = kho
    return _Dich()


def tao_app_mac_dinh() -> FastAPI:
    """Chỗ bám cho uvicorn: `autoedit.treatment.app:tao_app_mac_dinh --factory`.

    FACTORY chứ không phải biến `APP` sẵn ở module: biến sẵn nghĩa là chỉ IMPORT
    thôi đã mở SQLite, và cả suite test sẽ đẻ ra DB thật trong thư mục nhà.
    """
    kho = _kho_mac_dinh()
    return tao_app(kho, dich=_dich_mac_dinh(kho),
                   goi_y=_goi_y_mac_dinh(kho),
                   ky_thuat=_ky_thuat_mac_dinh(kho))


def main() -> None:
    import argparse

    import uvicorn

    ap = argparse.ArgumentParser(description="Bàn kịch bản RenderY")
    ap.add_argument("--host", default="127.0.0.1")
    # 9101-9120 + 9190 đã bị cụm OutlierY chiếm (đo 15/09: 9119 = app "thumby",
    # 9120 cũng đang nghe). Bind trùng thì uvicorn chết lặng ở cuối log.
    ap.add_argument("--port", type=int, default=9121)
    a = ap.parse_args()

    uvicorn.run(tao_app_mac_dinh(), host=a.host, port=a.port)


if __name__ == "__main__":
    main()
