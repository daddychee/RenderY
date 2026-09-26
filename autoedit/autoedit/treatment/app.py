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


# Tông MỒI cho tập chưa lập sổ. Đây là GIÁ TRỊ KHỞI ĐIỂM, không phải chỗ chốt:
# Owner sửa trong sổ của tập thì bản sửa thắng.
#
# Trước 25/09 chỗ này có HAI mục tên "dưới nước" / "trên cạn". User bắt đúng:
# đó là BỐI CẢNH chứ không phải tông. Ruột hai mục chỉ khác nhau đúng câu ánh
# sáng dưới nước — mà ánh sáng là thuộc tính của bối cảnh, thuộc về sổ Asset.
# Mood thật thì y hệt nhau, nên tập này thực chất chỉ có MỘT tông bị chẻ nhầm.
#
# `tb` (thiết bị) tách thành ô riêng, không chôn trong `chu`: chôn thì người
# dùng không biết là phải điền — đúng chỗ user báo thiếu (prompt video không hề
# có ống kính / máy quay).
TONG_MAC_DINH = [
    {"ma": "mood", "loai": "tong", "ten": "Tối & bí ẩn", "pr": "",
     "chu": "Photorealistic. Mood and tone: dark and mysterious, "
            "restrained contrast, no harsh shadows. "
            "Consistent mood, tone, and graphic style across all shots.",
     "tb": ""},
]


# Mã cỡ cảnh -> chữ nhà AI hiểu. `CO_HOP_LE` là bộ mã hợp lệ LLM được phép
# trả về; bảng này là bản dịch ra ngôn ngữ của prompt.
CO_CHU = {"WS": "wide shot", "MS": "medium shot", "CU": "close-up",
          "ECU": "extreme close-up", "AERIAL": "aerial shot"}
# Bộ mã hợp lệ suy ra từ chính bảng dịch: thêm một cỡ cảnh mà quên khai bản
# dịch thì nó lọt vào dữ liệu rồi biến mất ở prompt, không ai thấy.
CO_HOP_LE = tuple(CO_CHU)


def khung_cuoi(video: Path, dich: Path) -> Path:
    """Trích KHUNG CUỐI của một clip ra file ảnh.

    `-sseof -0.2` = tua từ CUỐI ngược lại 0,2 giây rồi lấy một khung. Lấy đúng
    khung cuối cùng thì hay trúng chỗ bộ giải mã chưa có dữ liệu; lùi một nhịp
    ngắn là chắc ăn mà mắt không phân biệt được.

    ffmpeg gọi từ PATH — máy chủ này có sẵn (8.1.2 ở C:/OutlierY/tools/ffmpeg).
    """
    import subprocess

    dich.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-sseof", "-0.2",
         "-i", str(video), "-frames:v", "1", "-y", str(dich)],
        capture_output=True, text=True, errors="replace")
    if not dich.exists():
        raise RuntimeError("không trích được khung cuối: " + (r.stderr or "")[:200])
    return dich


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


def tao_app(kho: Kho, dich=None, goi_y=None, ky_thuat=None,
            ve_anh=None, sinh_asset=None, ve_video=None) -> FastAPI:
    """Mọi bộ máy tiêm từ ngoài: test chạy DB tạm + đồ giả, không mạng."""
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
    def _so_day_du(tap: str) -> list[dict]:
        """Sổ như MỌI bên phải thấy: bản trong DB, chêm tông mặc định khi tập
        chưa có tông nào.

        Một hàm duy nhất, vì lỗi đo được 25/09 sinh ra đúng từ chỗ có hai:
        endpoint `/so` chêm mặc định nên TRANG thấy tông, còn `_prompt_anh` gọi
        thẳng `kho.ds_so()` nên MÁY CHỦ không thấy. Hộp cảnh hiện prompt có
        mood, Seedream nhận prompt trần — người duyệt một đằng, máy gửi một nẻo,
        và không có gì trên màn hình lộ ra điều đó.
        """
        ds = kho.ds_so(tap)
        if not any(x["loai"] == "tong" for x in ds):
            # BẢN SAO: dưới đây có gắn cờ `mac_dinh` vào từng mục, gắn thẳng
            # vào hằng số module là tập này bôi bẩn tập khác.
            ds = [dict(x) for x in TONG_MAC_DINH] + ds
        tong = [x for x in ds if x["loai"] == "tong"]
        mac = kho.tong_tap(tap)
        if not any(x["ma"] == mac for x in tong):
            mac = tong[0]["ma"] if tong else ""     # chưa chọn -> tông đầu sổ
        for x in tong:
            x["mac_dinh"] = x["ma"] == mac
        return ds

    def _tong_chu(so: list[dict], ma: str) -> str:
        """Đoạn tông của một cảnh. CÙNG LUẬT với `boiler()` trong trang, từng
        nhánh một: cảnh tự chọn thì theo cảnh, không thì theo tông MẶC ĐỊNH CỦA
        TẬP. Thiếu đường lui này thì cảnh nào quên chọn là prompt cụt — đo thật:
        0/83 cảnh có chọn."""
        tong = [y for y in so if y["loai"] == "tong"]
        x = next((y for y in tong if y["ma"] == ma), None)
        if x is None:
            x = next((y for y in tong if y.get("mac_dinh")), None)
        if x is None:
            return ""
        return " ".join(p for p in ((x.get("chu") or "").strip(),
                                    (x.get("tb") or "").strip()) if p)

    @app.get("/api/tap/{tap}/so")
    def doc_so(tap: str):
        """Sổ dùng chung cả tập. Sổ rỗng thì đưa sẵn HAI TÔNG mặc định user
        đang dùng: prompt nào cũng phải có đoạn tông ghép ở cuối, trả rỗng là
        prompt đầu tiên của mọi tập đều cụt. Chưa ghi xuống — sửa mới ghi."""
        return _so_day_du(tap)

    @app.put("/api/tap/{tap}/so")
    def luu_so(tap: str, request: Request, than: dict = Body(...)):
        _ghi_duoc(request)
        try:
            kho.luu_so(tap, than.get("so") or [])
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        # Chỉ đụng khi trang GỬI: lưu sổ mà không kèm `tong` là sửa nội dung
        # tông, không phải đổi tông mặc định — im lặng dọn lựa chọn cũ thì
        # người ta mất nó mà không biết vì sao.
        if "tong" in than:
            kho.dat_tong_tap(tap, (than.get("tong") or "").strip())
        return {"ok": True}

    @app.post("/api/tap/{tap}/so/goi-y")
    def goi_y_tai_san(tap: str, request: Request):
        """LLM đọc CẢ KỊCH BẢN TIẾNG ANH rồi gọi tên Asset + đề xuất Mood.

        Đọc kịch bản chứ không đọc mô tả cảnh (user chốt 25/09): nguồn sự thật
        là bản tiếng Anh, đi qua lớp dịch tiếng Việt của biên kịch là trôi tên
        riêng. Và chương chưa viết treatment thì quét theo cảnh là vô hình — đo
        thật trên SE001: C6 và E có 0 cảnh nhưng vẫn có kịch bản.

        MỘT lượt gọi: đo 25/09, cả tập là ~9.100 token. Bỏ được vòng chia lô và
        đoạn gộp trùng giữa các lô. Mood cũng hỏi trong chính lượt này — nó đã
        đọc hết rồi thì không việc gì phải trả tiền đọc lại.

        Đề xuất KHÔNG tự ghi vào sổ, người duyệt mới nhận (luật cứng #5).
        """
        _ghi_duoc(request)
        if goi_y is None:
            raise HTTPException(503, "Chưa bật bộ gợi ý.")
        dong: list[str] = []
        for c in kho.ds_chuong(tap):
            for d in kho.doc(tap, c["ma"])["dong"]:
                t = (d.get("en") or "").strip()
                if t:
                    dong.append(t)
        if not dong:
            raise HTTPException(
                400, "Tập này chưa có kịch bản tiếng Anh — dán kịch bản vào trước.")
        try:
            ra = goi_y.goi_y(chr(10).join(dong)) or {}
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Gợi ý hỏng: {exc}") from exc

        ds: list[dict] = []
        thay: dict[str, int] = {}
        for x in ra.get("tai_san") or []:
            if not isinstance(x, dict):
                continue
            if (x.get("loai") or "") not in ("nhan_vat", "dao_cu", "boi_canh"):
                continue
            ten = (x.get("ten") or "").strip()
            khoa = ten.lower()
            if not ten or khoa in thay:      # gộp trùng: một thứ một mục
                continue
            thay[khoa] = 1
            # `chu`/`pr` để TRỐNG: mô tả nhận dạng sinh ở bước sau, từ yêu cầu
            # của chính người dùng. LLM tự đoán ra một mô tả chung chung thì
            # người ta phải xoá đi gõ lại.
            ds.append({"ma": _ma_sach(ten, thay), "loai": x["loai"], "ten": ten,
                       "ly_do": (x.get("ly_do") or "").strip(),
                       "chu": "", "pr": "", "tb": "", "ref": False})

        md = ra.get("mood")
        mood: dict = {}
        if isinstance(md, dict) and ((md.get("ten") or "").strip()
                                     or (md.get("chu") or "").strip()):
            mood = {k: str(md.get(k) or "").strip()
                    for k in ("ten", "chu", "tb", "ly_do")}
        return {"goi_y": ds, "mood": mood, "quet": len(dong)}

    @app.post("/api/tap/{tap}/so/{ma}/sinh")
    def sinh_asset_api(tap: str, ma: str, request: Request):
        """Viết hồ sơ nhận dạng cho MỘT asset, từ YÊU CẦU người dùng đã gõ.

        Bước 2 của luồng user chốt 25/09. Bước 1 (`/so/goi-y`) chỉ gọi tên;
        mô tả sinh ở đây, sau khi người dùng đã nói họ muốn gì.
        """
        _ghi_duoc(request)
        if sinh_asset is None:
            raise HTTPException(503, "Chưa bật bộ sinh asset.")
        so = _so_day_du(tap)
        muc = next((x for x in so if x["ma"] == ma), None)
        if muc is None:
            raise HTTPException(404, f"Không có mã '{ma}' trong sổ.")
        if muc["loai"] not in ("nhan_vat", "dao_cu", "boi_canh"):
            raise HTTPException(
                400, "Mục này không phải asset — tông không có hồ sơ nhận dạng.")
        if not (muc.get("yc") or "").strip():
            raise HTTPException(
                400, "Chưa có yêu cầu cho asset này — viết vào ô “Yêu cầu” "
                     "trước. Để trống thì LLM lại tự đoán, đúng thứ vừa bỏ đi.")
        try:
            ra = sinh_asset.sinh_asset(muc, _tong_chu(so, ""))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Sinh asset hỏng: {exc}") from exc

        # Ghi ĐÈ LÊN BẢN TRONG KHO, không ghi bản `_so_day_du` (bản này có thể
        # đang mang tông mồi chưa hề nằm trong DB — lưu cả cụm là tự nhiên đẻ
        # ra một mục tông mà không ai thêm).
        kho_so = kho.ds_so(tap)
        for x in kho_so:
            if x["ma"] == ma:
                x["chu"], x["pr"] = ra.get("chu", ""), ra.get("pr", "")
        kho.luu_so(tap, kho_so)
        return {"ok": True, "chu": ra.get("chu", ""), "pr": ra.get("pr", "")}

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

    @app.post("/api/tap/{tap}/so/{ma}/ref-sinh")
    def sinh_ref(tap: str, ma: str, request: Request):
        """Vẽ ảnh ref cho một tài sản bằng chính `pr` (prompt tạo ref).

        Gửi ĐÚNG `pr`, KHÔNG ghép đoạn tông của cảnh: ref là bản mặt của nhân
        vật/đạo cụ — nền trắng, không mood. Ghép "dark & mysterious mood" vào là
        ref tối om, đem làm tham chiếu thì hỏng.

        Đường TẢI LÊN giữ nguyên: ai đã có ref đẹp sẵn thì vẫn dùng được.
        """
        _ghi_duoc(request)
        if ve_anh is None:
            raise HTTPException(503, "Chưa bật bộ vẽ ảnh.")
        muc = [x for x in kho.ds_so(tap) if x["ma"] == ma]
        if not muc:
            raise HTTPException(404, f"Không có tài sản mã '{ma}' trong sổ.")
        pr = (muc[0].get("pr") or "").strip()
        if not pr:
            raise HTTPException(
                400, "Tài sản này chưa có prompt tạo ref — viết vào ô "
                     "“Prompt tạo ref” trước, không thì Seedream vẽ ra thứ vô nghĩa.")
        try:
            dich = kho.duong_ref(tap, ma, ".png")
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        try:
            ve_anh.gen_anh(pr, dich)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Vẽ ref hỏng: {exc}") from exc
        for d in kho.DUOI_REF:          # đổi đuôi thì đừng để lại bản cũ
            if d != ".png":
                kho.duong_ref(tap, ma, d).unlink(missing_ok=True)
        return {"ok": True}

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
        """Gắn kèm cờ `anh` cho cảnh đã có ảnh trên đĩa.

        SUY RA TỪ ĐĨA, không lưu xuống kho: lưu là sớm muộn lệch với file thật
        (xoá file bằng tay, chép kho sang máy khác…). Giá trị lấy theo GIỜ SỬA
        FILE nên vừa làm cờ, vừa làm mã chống cache — vẽ lại ảnh cùng tên mà
        không đổi mã thì trình duyệt vẫn hiện tấm cũ.
        """
        ra = kho.doc(tap, chuong)
        for dg in ra["dong"]:
            for c in dg.get("canh") or []:
                ma = c.get("id")
                if not ma:
                    continue
                try:
                    t = kho.duong_anh(tap, ma)
                except ValueError:
                    continue
                if t.exists():
                    c["anh"] = str(int(t.stat().st_mtime))
                v = kho.duong_video(tap, ma)
                if v.exists():
                    c["video"] = str(int(v.stat().st_mtime))
        return ra

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

    # ------------------------------------------------------------- ảnh

    def _luu_canh(tap: str, chuong: str, d: list, ai: str) -> None:
        """Mọi đường ghi của phần ảnh đi qua đây. Không bắt `KhoaBiGiu` thì
        chương đang bị người khác giữ sẽ nổ 500 và trang chỉ hiện "HTTP 500"
        (đo thật 24/09) — trong khi mọi đường ghi khác đều trả 409 kèm tên."""
        try:
            kho.luu(tap, chuong, d, kho.doc(tap, chuong)["outline"], ai)
        except KhoaBiGiu as exc:
            raise HTTPException(409, str(exc)) from exc

    def _tim_canh(tap: str, chuong: str, ma: str):
        """(danh sách dòng, chỉ số dòng, chỉ số cảnh, cảnh) theo MÃ RIÊNG."""
        d = kho.doc(tap, chuong)["dong"]
        for i, dg in enumerate(d):
            for j, c in enumerate(mdong.doc_canh(dg)):
                if c.get("id") == ma:
                    return d, i, j, c
        raise HTTPException(404, f"Không có cảnh mã '{ma}' trong chương {chuong}.")

    def _may(c: dict) -> str:
        """Cỡ cảnh + góc máy thành MỘT mệnh đề tiếng Anh.

        Đo 25/09: 49/49 cảnh có prompt EN đều đã có đủ `co` và `goc` — LLM
        điền, người dùng nhìn thấy trên thẻ — mà prompt không mang chữ nào.
        Cùng họ lỗi với đoạn tông: dữ liệu có sẵn, không tới nơi cần tới.

        `co` phải DỊCH RA CHỮ: gửi "ECU" trần là gửi một mã nội bộ cho nhà AI
        đoán.
        """
        pn = [CO_CHU.get((c.get("co") or "").upper(), ""),
              (c.get("goc") or "").strip()]
        t = ", ".join(x for x in pn if x)
        return t[:1].upper() + t[1:] if t else ""

    def _prompt_anh(tap: str, c: dict) -> str:
        """ĐÚNG cái người dùng thấy trong hộp: nội dung EN + mô tả tài sản +
        đoạn tông. Gửi mỗi `pa` thì ảnh mất tông, khác hẳn bản họ duyệt."""
        so = _so_day_du(tap)
        tra = {x["ma"]: x for x in so}
        ta = [tra[m] for m in (c.get("ts") or []) if m in tra and tra[m].get("chu")]
        mo_ta = "".join(f"{x['ten']}: {x['chu']}\n" for x in ta)
        if mo_ta:
            mo_ta += "\n"
        tong = _tong_chu(so, c.get("tong") or "")
        may = _may(c)
        return f"16:9 ratio. {may + '. ' if may else ''}{c['pa']}\n\n{mo_ta}{tong}".strip()

    def _prompt_video(tap: str, c: dict) -> str:
        """ĐÚNG cái người dùng thấy ở ô "Prompt video" trong hộp cảnh.

        CÙNG LUẬT với `promptVideo()` bên trang, từng nhánh một. Đây chính là
        chỗ đã sinh ra lỗi nặng nhất của cả đợt: prompt ẢNH có hai bản dựng ở
        hai tầng rồi trôi khỏi nhau, người dùng duyệt một đằng máy gửi một nẻo.
        Lần này viết kèm phép đo so từng chữ ngay từ đầu.
        """
        so = _so_day_du(tap)
        tra = {x["ma"]: x for x in so}
        ta = [tra[m] for m in (c.get("ts") or []) if m in tra and tra[m].get("chu")]
        mo_ta = "".join(f"{x['ten']}: {x['chu']}\n" for x in ta)
        if mo_ta:
            mo_ta += "\n"
        may, cd = _may(c), (c.get("cd") or "").strip()
        dau = f"Camera: {cd}." if cd else "Simple camera motion only."
        if may:
            dau += f" {may}."
        sfx = (c.get("sfx") or "").strip()
        return (f"{c['pv']}\n{dau}\nOne continuous shot, no cuts.\n\n"
                f"{mo_ta}{_tong_chu(so, c.get('tong') or '')}"
                + (f" Sound: {sfx}." if sfx else "") + " No background music.")

    def _ve_mot_canh(tap: str, chuong: str, d: list, i: int, j: int, ai: str) -> None:
        c = mdong.doc_canh(d[i])[j]
        if not (c.get("pa") or "").strip():
            raise HTTPException(
                400, "Cảnh này chưa có prompt tiếng Anh — bấm Sinh prompt trước. "
                     "Gửi chữ Việt cho Seedream là ra ảnh sai.")
        # Ảnh ref của asset đã gán đi KÈM lượt vẽ. Asset chưa vẽ ref thì bỏ
        # qua, không chặn — gán rồi mà chưa kịp vẽ ref là chuyện thường giữa
        # chừng, lúc đó rơi về đúng hành vi cũ: chỉ có chữ.
        ref = [t for t in (kho.ref_dang_co(tap, m) for m in (c.get("ts") or []))
               if t is not None]
        ve_anh.gen_anh(_prompt_anh(tap, c), kho.duong_anh(tap, c["id"]), ref=ref)
        cs = mdong.doc_canh(d[i])
        cs[j].pop("duyet", None)      # ảnh đổi thì con dấu duyệt cũ hết nghĩa
        d[i] = mdong.ghi_canh(d[i], cs)

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/ky-thuat")
    def create_prompt(tap: str, chuong: str, ma: str, request: Request):
        """Dịch nội dung cảnh sang prompt TIẾNG ANH + điền cột kỹ thuật, cho
        ĐÚNG MỘT CẢNH (user chốt 25/09: "đưa Sinh prompt về từng cảnh luôn").

        Cùng lý do với ảnh: mỗi cảnh là một quyết định, không chạy hàng loạt.
        LLM KHÔNG đụng `t` và KHÔNG chọn `tong` — hai thứ đó user giữ quyền.
        """
        ai = _ghi_duoc(request)
        if ky_thuat is None:
            raise HTTPException(503, "Chưa bật bộ sinh prompt.")
        d, i, j, c = _tim_canh(tap, chuong, ma)
        if not (c.get("t") or "").strip():
            raise HTTPException(400, "Cảnh này chưa có nội dung — viết trước đã.")

        # Chỉ đưa asset CẢNH NÀY đang dùng, không đưa cả sổ: LLM không còn
        # việc chọn, nó chỉ cần biết chủ thể trông ra sao để tả cho khớp.
        tra = {x["ma"]: x for x in kho.ds_so(tap)}
        so = [tra[m] for m in (c.get("ts") or []) if m in tra]
        cs = mdong.doc_canh(d[i])
        muc = [{"id": ma, "voice": d[i].get("en", ""), "canh": c["t"],
                "thu_tu": f"{j + 1}/{len(cs)}"}]
        try:
            ra = ky_thuat.ky_thuat(muc, so)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Sinh prompt hỏng: {exc}") from exc
        x = next((y for y in ra if str(y.get("id")) == ma), None)
        if x is None and len(ra) == 1:
            x = ra[0]
        if x is None:
            raise HTTPException(502, "LLM không trả về cảnh nào khớp mã.")

        for khoa in ("pa", "pv", "goc", "cd", "sfx"):
            if (x.get(khoa) or "").strip():
                cs[j][khoa] = str(x[khoa]).strip()
        if (x.get("co") or "").upper() in CO_HOP_LE:
            cs[j]["co"] = x["co"].upper()
        # KHÔNG đụng `ts`: người dùng chọn asset, không phải LLM (user chốt
        # 25/09 — "Không để LLM tự nhớ"). Bớt một chỗ nó bịa mã, và bấm Create
        # Prompt lần hai không xoá lựa chọn có chủ đích của người dùng.
        d[i] = mdong.ghi_canh(d[i], cs)
        _luu_canh(tap, chuong, d, ai)
        return {"ok": True, "gan_asset": len(c.get("ts") or [])}

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/anh")
    def sinh_anh(tap: str, chuong: str, ma: str, request: Request):
        ai = _ghi_duoc(request)
        if ve_anh is None:
            raise HTTPException(503, "Chưa bật bộ vẽ ảnh.")
        d, i, j, _ = _tim_canh(tap, chuong, ma)
        try:
            _ve_mot_canh(tap, chuong, d, i, j, ai)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Vẽ ảnh hỏng: {exc}") from exc
        _luu_canh(tap, chuong, d, ai)
        return {"ok": True}

    @app.get("/api/tap/{tap}/{chuong}/canh/{ma}/anh")
    def xem_anh(tap: str, chuong: str, ma: str):
        try:
            t = kho.duong_anh(tap, ma)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        if not t.exists():
            raise HTTPException(404, "Cảnh này chưa có ảnh.")
        return FileResponse(t, headers={"Cache-Control": "no-store"})

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/duyet")
    def duyet_anh(tap: str, chuong: str, ma: str, request: Request):
        """Cổng duyệt. Luật của `aigen` (user chốt 03/09): tiền video chỉ đốt
        SAU cổng này — ảnh ~$0,03/tấm, video đắt gấp năm."""
        ai = _ghi_duoc(request)
        d, i, j, _ = _tim_canh(tap, chuong, ma)
        if not kho.duong_anh(tap, ma).exists():
            raise HTTPException(400, "Cảnh này chưa có ảnh để duyệt.")
        cs = mdong.doc_canh(d[i])
        cs[j]["duyet"] = "1"
        d[i] = mdong.ghi_canh(d[i], cs)
        _luu_canh(tap, chuong, d, ai)
        return {"ok": True}

    # ------------------------------------------------------------ video
    GIAY_VIDEO = 15     # trần nhà cung cấp, đo 26/09: 20s bị từ chối

    def _canh_truoc(d: list, i: int, j: int) -> dict | None:
        """Cảnh liền trước TRONG CHƯƠNG. Lùi trong cùng dòng, hết thì sang dòng
        trên. Không bắc cầu sang chương khác: nối hai chương là quyết định khác,
        và ranh giới chương thường cũng là ranh giới cảnh."""
        if j > 0:
            return mdong.doc_canh(d[i])[j - 1]
        for k in range(i - 1, -1, -1):
            cs = mdong.doc_canh(d[k])
            if cs:
                return cs[-1]
        return None

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/video")
    def sinh_video(tap: str, chuong: str, ma: str, request: Request,
                   than: dict = Body(default={})):
        """Tạo TASK dựng video, trả về NGAY kèm mã task.

        Không chờ cho xong: đo 26/09 một clip mất 70-150 giây. Giữ request treo
        suốt thời gian đó thì đóng tab hay rớt mạng là mất dấu một clip đã trả
        tiền — mà chính vì thế mã task phải được ghi xuống kho.
        """
        ai = _ghi_duoc(request)
        if ve_video is None:
            raise HTTPException(503, "Chưa bật bộ dựng video.")
        d, i, j, c = _tim_canh(tap, chuong, ma)
        if not kho.duong_anh(tap, ma).exists():
            raise HTTPException(400, "Cảnh này chưa có ảnh — vẽ ảnh trước đã.")
        if not c.get("duyet"):
            raise HTTPException(
                400, "Ảnh của cảnh này chưa được duyệt. Tiền video chỉ đốt sau "
                     "cổng duyệt — xem ảnh rồi bấm Duyệt ảnh đã.")
        if not (c.get("pv") or "").strip():
            raise HTTPException(
                400, "Cảnh này chưa có prompt video — bấm Create Prompt trước.")

        # NỐI: khung cuối clip cảnh trước thành khung đầu clip này (user chốt
        # 26/09). Đổi lại clip KHÔNG còn bắt đầu từ tấm ảnh đã duyệt của chính
        # cảnh này — nên chỉ làm khi người dùng bấm, không bao giờ tự động.
        dau_vao = kho.duong_anh(tap, ma)
        if than.get("noi"):
            tr = _canh_truoc(d, i, j)
            v = kho.duong_video(tap, tr["id"]) if tr and tr.get("id") else None
            if v is None or not v.exists():
                raise HTTPException(
                    400, "Cảnh trước chưa có video để nối — dựng cảnh trước đã.")
            try:
                dau_vao = khung_cuoi(v, kho.duong_anh(tap, ma).parent /
                                     ("noi_" + ma + ".png"))
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(502, f"Trích khung cuối hỏng: {exc}") from exc
        try:
            tid = ve_video.bat_dau(_prompt_video(tap, c), dau_vao,
                                   GIAY_VIDEO, False)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Dựng video hỏng: {exc}") from exc
        cs = mdong.doc_canh(d[i])
        cs[j]["vid"] = str(tid)
        d[i] = mdong.ghi_canh(d[i], cs)
        _luu_canh(tap, chuong, d, ai)
        return {"ok": True, "vid": str(tid)}

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/video-kiem")
    def kiem_video(tap: str, chuong: str, ma: str, request: Request):
        """Hỏi một lần xem task xong chưa; xong thì tải về và quên mã task.

        Hỏng cũng phải quên mã: giữ lại là trang treo mãi ở "đang dựng". Đo
        26/09 có task hỏng thật vì bộ lọc bản quyền âm thanh.
        """
        ai = _ghi_duoc(request)
        if ve_video is None:
            raise HTTPException(503, "Chưa bật bộ dựng video.")
        d, i, j, c = _tim_canh(tap, chuong, ma)
        tid = (c.get("vid") or "").strip()
        if not tid:
            return {"trang_thai":
                    "xong" if kho.duong_video(tap, ma).exists() else "chua"}
        try:
            r = ve_video.trang_thai(tid) or {}
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Hỏi trạng thái hỏng: {exc}") from exc
        tt = str(r.get("status") or "").lower()

        def _quen_ma():
            cs = mdong.doc_canh(d[i])
            cs[j].pop("vid", None)
            d[i] = mdong.ghi_canh(d[i], cs)
            _luu_canh(tap, chuong, d, ai)

        if tt == "succeeded":
            try:
                ve_video.tai_ve(r.get("video_url") or "",
                                kho.duong_video(tap, ma))
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(502, f"Tải video về hỏng: {exc}") from exc
            _quen_ma()
            return {"trang_thai": "xong"}
        if tt in ("failed", "cancelled"):
            _quen_ma()
            return {"trang_thai": "hong", "loi": r.get("loi") or tt}
        return {"trang_thai": "dang"}

    @app.get("/api/tap/{tap}/{chuong}/canh/{ma}/video")
    def xem_video(tap: str, chuong: str, ma: str):
        _ = chuong
        try:
            t = kho.duong_video(tap, ma)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        if not t.exists():
            raise HTTPException(404, "Cảnh này chưa có video.")
        return FileResponse(t, headers={"Cache-Control": "no-store"})

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


class _VeAnh:
    """Seedream qua ArkClient, khoá lấy từ KÉT bằng SLUG CỦA TREATMENT.

    KHÔNG để ArkClient tự đi tìm: nó đi qua `web/ket_v3` ghi cứng
    `SLUG = "rendery"` nên cấp phát của Treatment không bao giờ thấy — đúng lỗi
    đã phải sửa một lần cho `dich.py` ngày 23/09 (cấp phát đúng rồi mà app vẫn
    báo "chưa cấp"). Truyền khoá vào tận tay.
    """

    def gen_anh(self, prompt, dich, ref=None):
        from autoedit.aigen.client import ArkClient
        from autoedit.treatment.dich import doc_ket_viec

        khoa = (doc_ket_viec("gen_canh") or {}).get("key", "")
        if not khoa:
            raise RuntimeError(
                "Chưa có khoá vẽ ảnh — Owner cấp ở General › API Keys › "
                "Theo app › Treatment › gen_canh.")
        return ArkClient(api_key=khoa).gen_anh(prompt, dich, ref=ref)


class _VeVideo:
    """Seedance qua ArkClient, khoá lấy từ KÉT bằng slug của Treatment.

    Dùng chung cấp phát `gen_canh` với bộ vẽ ảnh: một khoá ARK chạy cả Seedream
    lẫn Seedance. Tách việc riêng chỉ để đo tiền tách bạch thì làm sau.
    """

    def _ark(self):
        from autoedit.aigen.client import ArkClient
        from autoedit.treatment.dich import doc_ket_viec

        khoa = (doc_ket_viec("gen_canh") or {}).get("key", "")
        if not khoa:
            raise RuntimeError(
                "Chưa có khoá dựng video — Owner cấp ở General › API Keys › "
                "Theo app › Treatment › gen_canh.")
        return ArkClient(api_key=khoa)

    def bat_dau(self, prompt, anh, giay, am):
        return self._ark().gen_video_i2v(prompt, anh, giay=giay, am=am)

    def trang_thai(self, tid):
        return self._ark().trang_thai_video(tid)

    def tai_ve(self, url, dich):
        return self._ark().tai_video(url, dich)


def _ve_video_mac_dinh(kho: Kho):
    _ = kho
    return _VeVideo()


def _ve_anh_mac_dinh(kho: Kho):
    _ = kho
    return _VeAnh()


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


class _SinhAsset:
    """Đọc KÉT mỗi lượt, dùng chung cấp phát `dich` như bộ gợi ý."""

    def sinh_asset(self, muc, tong):
        from autoedit.treatment.dich import LLM

        return LLM().sinh_asset(muc, tong)


def _sinh_asset_mac_dinh(kho: Kho):
    _ = kho
    return _SinhAsset()


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
                   ky_thuat=_ky_thuat_mac_dinh(kho),
                   ve_anh=_ve_anh_mac_dinh(kho),
                   sinh_asset=_sinh_asset_mac_dinh(kho),
                   ve_video=_ve_video_mac_dinh(kho))


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
