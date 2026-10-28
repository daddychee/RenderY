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
from autoedit.treatment import drama as mdrama
from autoedit.treatment import tai_san as mtai_san
from autoedit.treatment.kho import DongVuaDoi, Kho, KhoaBiGiu

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
from autoedit.treatment.dich import GIAY_VIDEO, VIEC_SINH_PROMPT

CO_CHU = {"EWS": "extreme wide shot", "WS": "wide shot", "MS": "medium shot",
          "MCU": "medium close-up", "CU": "close-up", "ECU": "extreme close-up",
          "AERIAL": "aerial shot"}
# Bộ mã hợp lệ suy ra từ chính bảng dịch: thêm một cỡ cảnh mà quên khai bản
# dịch thì nó lọt vào dữ liệu rồi biến mất ở prompt, không ai thấy.
CO_HOP_LE = tuple(CO_CHU)

# Góc máy: mã -> câu tiếng Anh ĐÃ ĐO (trang ⑬, 27/09). eye/low 3/3 · high 2/3 ·
# top/POV 3/3 và bird 2/3 khi đoạn sau viết theo khung · OTS 1/3. Dữ liệu cũ ghi
# chữ tự do ("eye level, straight-on") thì đi nguyên — không migrate.
# CÙNG BẢNG với `GOC_CHU` bên trang, canh bằng test tĩnh.
GOC_CHU = {
    "eye": "eye level",
    "low": "low angle, camera below the subject looking up",
    "high": "high angle, camera above the subject looking down",
    "bird": "bird's-eye view, from high above at a steep downward angle",
    "top": "top-down shot, camera directly overhead looking straight down",
    "ots": "over-the-shoulder shot, from behind a second person's shoulder in the foreground",
    "pov": "POV shot, first-person view from the subject's own eyes, the subject not visible",
}

# Động tác máy: CHỈ những thứ Seedance i2v đo ra chạy (trang ⑬, 38 clip 15 s).
# push/pull/tilt/track/truck 3/3 · pan 2/3 · whip/crash chạy nhưng sai nhịp ·
# arc/orbit vòng lỏng. KHÔNG có handheld, boom, dolly zoom: 0/2 cả hai cách nói —
# bày nút máy không làm được là bán nút chết. Câu máy đứng ĐẦU prompt video và tả
# hệ quả trên khung: ở giữa thì pan/truck đứng yên 0/1, lên đầu thì truck 3/3.
CD_CHU = {
    "static": "The camera holds perfectly still.",
    "push_in": "The camera pushes in slowly and steadily toward the subject.",
    "pull_out": "The camera pulls out slowly and steadily away from the subject.",
    "tilt_up": "The camera tilts slowly upward.",
    "tilt_down": "The camera tilts slowly downward.",
    "track": "The camera tracks the subject, following its movement.",
    "truck_left": "The camera trucks to the left: it slides sideways on a rail, the scene drifting rightward across the frame with parallax.",
    "truck_right": "The camera trucks to the right: it slides sideways on a rail, the scene drifting leftward across the frame with parallax.",
    "pan_left": "The camera pans slowly to the left, the whole scene sweeping rightward across the frame.",
    "pan_right": "The camera pans slowly to the right, the whole scene sweeping leftward across the frame.",
    "whip_pan": "A fast whip pan to the right with heavy motion blur, snapping to a new framing.",
    "crash_zoom": "A sudden, very fast zoom in on the subject.",
    "arc": "The camera arcs slowly around the subject.",
    "orbit": "The camera orbits around the subject.",
}

# Drama (user chốt 28/10): mỗi SHOT của clip Grok mang đúng bộ mã cỡ/góc/máy của
# narration, ghép bằng đúng bảng chữ trên. Bỏ `orbit`: Grok xoay vòng hỏng 2/2
# (đo của Padoma, grok-phim.md mục 1).
CD_DRAMA = {k: v for k, v in CD_CHU.items() if k != "orbit"}
KHOA_SHOT = {"t", "co", "goc", "cd", "lap", "cau"}


def khung_shot(s: dict) -> str:
    """Câu khung một shot drama: "{cỡ}, {góc}: {lap}. {máy}" — cùng dạng câu KHUNG
    narration đã đo (`_khung`); mốc giây do `prompt_clip` đặt trước nó."""
    dau = ", ".join(x for x in (CO_CHU.get(s.get("co") or "", ""), GOC_CHU.get(s.get("goc") or "", "")) if x)
    lap = str(s.get("lap") or "").strip().rstrip(".")
    cau = f"{dau}: {lap}" if dau and lap else (dau or lap)
    return " ".join(x for x in (f"{cau}." if cau else "", CD_DRAMA.get(s.get("cd") or "", "")) if x)


def pd_ghep(pd: dict, sh: list[dict]) -> dict:
    """`pd` (chữ LLM viết cho từng shot) + `sh` (shot người dựng chốt) -> dạng
    `drama.prompt_clip` đọc. Lệch số shot = chữ viết cho bộ shot khác: coi như chưa có."""
    ds = pd.get("shots") or []
    if not pd or not sh or len(ds) != len(sh):
        return {}
    return dict(pd, shots=[dict(x if isinstance(x, dict) else {}, khung=khung_shot(s), cau=s.get("cau"))
                           for s, x in zip(sh, ds)])


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
        # Tập mới đi luật tài sản khuôn Padoma (`khuon` "2", user chốt 27/10:
        # cả narration lẫn drama, chỉ tập mới). `loai` "drama" = drama thoại.
        try:
            kho.tao_tap((than.get("ma") or "").strip(), (than.get("ten") or "").strip(),
                        loai=(than.get("loai") or "").strip(), khuon="2")
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
        kieu = kho.kieu_tap(tap)
        if kieu["khuon"] == "2" and hasattr(sinh_asset, "sinh_asset_2"):
            # Khuôn Padoma: LLM chỉ viết MÔ TẢ (+ giọng nhân vật); prompt ảnh là
            # khuôn câu cố định Python ghép (`tai_san.pr_mau`). Nhân vật drama
            # giữ cụm của kịch bản — kịch bản là nguồn, LLM không viết đè.
            try:
                ra = sinh_asset.sinh_asset_2(muc, _tong_chu(so, ""))
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(502, f"Sinh asset hỏng: {exc}") from exc
            kho_so = kho.ds_so(tap)
            for x in kho_so:
                if x["ma"] != ma:
                    continue
                giu_cum = (kieu["loai"] == "drama" and x["loai"] == "nhan_vat"
                           and (x.get("chu") or "").strip())
                if not giu_cum:
                    x["chu"] = str(ra.get("chu") or "").strip()
                if x["loai"] == "nhan_vat" and str(ra.get("tieng") or "").strip():
                    x["tieng"] = str(ra["tieng"]).strip()
                x["pr"] = mtai_san.pr_mau(x["loai"], x["chu"])
                muc = x
            kho.luu_so(tap, kho_so)
            return {"ok": True, "chu": muc.get("chu", ""), "pr": muc.get("pr", ""),
                    "tieng": muc.get("tieng", "")}
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
        # Phải CÓ TRONG SỔ mới nhận. Đo 26/09: user tạo một bối cảnh mới rồi
        # tải ref lên ngay, trước khi lưu sổ. Máy chủ nhận 200 và ghi file,
        # nhưng mục đó chưa bao giờ được lưu — trang nạp lại sổ là nuốt mất nó.
        # File thành mồ côi, màn hình trống, user tưởng tải lên hỏng.
        if not any(x["ma"] == ma for x in kho.ds_so(tap)):
            raise HTTPException(
                404, "Asset này chưa có trong sổ — đặt tên và bấm Lưu trước, "
                     "rồi mới tải ref lên.")
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
        if kho.kieu_tap(tap)["khuon"] == "2" and muc[0]["loai"] in mtai_san.TI_LE:
            return _ref_khuon_2(tap, ma, muc[0])
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

    def _ref_khuon_2(tap: str, ma: str, muc: dict) -> dict:
        """Luật tài sản Padoma bằng GPT Image 2 (user chốt 27/10). Người: cận
        mặt 1:1 -> toàn thân 9:16 SỬA TỪ ảnh cận -> tấm gộp 4:3 (đây mới là ref);
        đồ vật nền trắng 1:1; nơi chốn 16:9 không người. Ảnh vẽ theo MÔ TẢ tiếng
        Anh — chưa có thì chặn, vẽ theo chữ Việt là ra ảnh sai."""
        loai, chu = muc["loai"], (muc.get("chu") or "").strip()
        if not chu or mdrama.la_tieng_viet(chu):
            raise HTTPException(400, "Asset này chưa có mô tả tiếng Anh — bấm “Sinh Asset” "
                                     "trước, ảnh vẽ theo mô tả đó.")
        pr = (muc.get("pr") or "").strip() or mtai_san.pr_mau(loai, chu)
        try:
            dich = kho.duong_ref(tap, ma, ".png")
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        m = {"model": mtai_san.MODEL_ANH}
        try:
            if loai == "nhan_vat":
                can, toan = dich.with_name(ma + "__can.png"), dich.with_name(ma + "__toan.png")
                ve_anh.gen_anh(pr, can, ti_le="1:1", **m)
                ve_anh.gen_anh(mtai_san.toan_than(chu), toan, ref=[can], ti_le="9:16", **m)
                tam = mtai_san.ghep_tam(can, toan, dich.with_name(ma + "__tam.png"))
                kho.xoa_ref(tap, ma)
                tam.replace(dich)
            else:
                ve_anh.gen_anh(pr, dich, ti_le=mtai_san.TI_LE[loai], **m)
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Vẽ ref hỏng: {exc}") from exc
        for d in kho.DUOI_REF:          # đổi đuôi thì đừng để lại bản cũ
            if d != ".png":
                kho.duong_ref(tap, ma, d).unlink(missing_ok=True)
        return {"ok": True}

    # ------------------------------------------------------------ drama
    @app.post("/api/tap/{tap}/drama")
    def dan_drama(tap: str, request: Request, than: dict = Body(...)):
        """Dán CẢ `kich-ban.md` (skill /bien-kich-grok, khuôn Padoma) vào tập
        drama. Kịch bản lỗi khuôn thì KHÔNG ghi gì (giao ước với skill). Dán lại
        khớp clip theo mã P: giữ ảnh/video, độ dài đã chọn, prompt sửa tay."""
        ai = _ghi_duoc(request)
        if kho.kieu_tap(tap)["loai"] != "drama":
            raise HTTPException(400, "Tập này không phải tập drama — tạo tập mới loại Drama thoại.")
        r = mdrama.tach_tap(than.get("text") or "")
        if r["loi"]:
            raise HTTPException(400, "Kịch bản chưa đúng khuôn, chưa nạp gì:\n" + "\n".join(r["loi"][:20])
                                + (f"\n… và {len(r['loi']) - 20} lỗi nữa" if len(r["loi"]) > 20 else ""))
        # Gác khoá TRƯỚC khi ghi chương nào: ghi được nửa tập rồi mới vướng là
        # tập lệch nửa cũ nửa mới.
        for ch in r["chuong"]:
            giu = kho.ai_giu(tap, ch["ma"])
            if giu and giu != ai:
                raise HTTPException(409, f"{giu} đang sửa chương {ch['ma']} — đợi xong rồi dán lại.")
        so = kho.ds_so(tap)
        theo_ma = {x["ma"]: x for x in so}
        for m in r["so"]:
            o = theo_ma.get(m["ma"])
            if o is None:
                o = dict(m, pr="", tb="")
                so.append(o)
            o.update(ten=m["ten"], loai=m["loai"], yc=m["yc"])
            if m["loai"] == "nhan_vat":
                # Cụm của kịch bản là nguồn nhận dạng. Giọng tiếng Anh đã chốt
                # thì giữ — đổi giọng giữa phim là lộ ngay.
                o["chu"] = m["chu"]
                o["pr"] = mtai_san.pr_mau("nhan_vat", m["chu"])
                if not (o.get("tieng") or "").strip() or mdrama.la_tieng_viet(o.get("tieng")):
                    o["tieng"] = m["tieng"]
        kho.luu_so(tap, so)
        cu = {c["ma"]: kho.doc(tap, c["ma"])["dong"] for c in kho.ds_chuong(tap)}
        ma_kb = {m["ma"] for m in r["so"]}
        pm_cu = {c.get("pm") for ds in cu.values() for d in ds for c in mdong.doc_canh(d) if c.get("pm")}
        truoc = {c["pm"]: c for ds in cu.values() for d in ds for c in mdong.doc_canh(d) if c.get("pm")}
        pm_moi, doi, mat = set(), [], []
        for ch in r["chuong"]:
            kho.tao_chuong(tap, ch["ma"])
            ds = mdrama.ghep_lai(cu, ch["dong"], ma_kb)
            for c in (c for d in ds for c in d["canh"]):
                pm_moi.add(c["pm"])
                o = truoc.get(c["pm"])
                if o is not None and o.get("t", "") != c["t"]:
                    doi.append(c["pm"])
                if o is not None and o.get("pd") and not c.get("pd"):
                    mat.append(c["pm"])
            try:
                kho.luu(tap, ch["ma"], ds, ch["outline"], ai)
            except KhoaBiGiu as exc:
                raise HTTPException(409, str(exc)) from exc
        # `doi`/`mat_prompt`: trang báo clip nào đổi chữ, clip nào phải viết lại prompt.
        return {"ok": True, "chuong": len(r["chuong"]), "clip": len(pm_moi),
                "bo": len(pm_cu - pm_moi), "nhac": r["nhac"][:30], "doi": doi, "mat_prompt": mat}

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

    # Bảng chọn model — đứng TRƯỚC `/api/tap/{tap}/{chuong}` kẻo "mo-hinh" bị
    # nuốt làm mã chương (cùng bẫy với `/txt` ngay trên).
    @app.get("/api/tap/{tap}/mo-hinh")
    def doc_mo_hinh(tap: str):
        """Bảng chọn model: danh sách nhà đang mở + đang chọn của tập + credit +
        giây từng model video. Nhà không có bảng (ModelArk) thì danh sách rỗng."""
        from autoedit.treatment.dich import doc_ket_viec

        # Model Owner cấp trong két — để nút "theo két" nói rõ đang rơi về đâu.
        ket = {"anh": (doc_ket_viec("gen_canh") or {}).get("model") or "",
               "video": (doc_ket_viec("gen_video") or {}).get("model") or ""}
        return {"chon": kho.mo_hinh_tap(tap), "ket": ket,
                "danh_sach": getattr(ve_video, "danh_sach", None) or [],
                "credit": getattr(ve_video, "credit", None),
                "giay": getattr(ve_video, "giay_theo_model", None) or {},
                "giay_mac_dinh": _giay_clip(tap)}

    @app.put("/api/tap/{tap}/mo-hinh")
    def dat_mo_hinh(tap: str, request: Request, than: dict = Body(...)):
        _ghi_duoc(request)
        kho.dat_mo_hinh_tap(tap, than.get("anh") or "", than.get("video") or "")
        return {"ok": True, "chon": kho.mo_hinh_tap(tap)}

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
                if c.get("pm"):          # clip drama: số từ, mốc shot, câu khung do PYTHON tính — trang chỉ hiện
                    sh, g = mdrama.doc_sh(c.get("sh")), _giay_clip(tap, c)
                    c["tu"] = mdrama.so_tu(c.get("t"))
                    c["ns"] = len(sh)
                    c["day"] = mdrama.so_shot_qua_day(c["ns"], g)
                    c["moc"] = [list(x) for x in mdrama.moc_shot(sh, c.get("t"), g)]
                    c["thoai"] = mdrama.loi_thoai(c.get("t"))
                    c["dau_shot"] = [khung_shot(s) for s in sh]
        return ra

    @app.put("/api/tap/{tap}/{chuong}")
    def luu(tap: str, chuong: str, request: Request, than: dict = Body(...)):
        ai = _ghi_duoc(request)
        try:
            giu = kho.luu_tu_trang(tap, chuong, than.get("dong") or [],
                                   than.get("outline") or "", ai,
                                   hop_rieng=bool(than.get("hop_rieng")))
        except KhoaBiGiu as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"ok": True, "giu_ban_moi": giu}

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

    def _va_canh(tap: str, chuong: str, ma: str, va, ai: str) -> dict:
        """Kết quả MÁY làm ghi qua đây: vá đúng một cảnh trên bản mới nhất,
        không cần khoá chương (đo 28/09: 409 ở chỗ này làm mất một clip đã trả
        tiền, và ghi cả chương thì đè bản sửa của người khác)."""
        try:
            return kho.sua_canh(tap, chuong, ma, va, ai)
        except KeyError as exc:
            raise HTTPException(404, f"Không có cảnh mã '{ma}' trong chương {chuong}.") from exc

    def _sua_dong(tap: str, chuong: str, i: int, dau: list, lam, ai: str) -> None:
        """Breakdown / cú bổ trợ ghi qua đây: áp kết quả LLM lên bản MỚI NHẤT của
        phân cảnh; phân cảnh đổi trong lúc chờ thì 409, không đè."""
        try:
            kho.sua_dong(tap, chuong, i, dau, lam, ai)
        except (KhoaBiGiu, DongVuaDoi) as exc:
            raise HTTPException(409, str(exc)) from exc

    def _tim_canh(tap: str, chuong: str, ma: str):
        """(danh sách dòng, chỉ số dòng, chỉ số cảnh, cảnh) theo MÃ RIÊNG."""
        d = kho.doc(tap, chuong)["dong"]
        for i, dg in enumerate(d):
            for j, c in enumerate(mdong.doc_canh(dg)):
                if c.get("id") == ma:
                    return d, i, j, c
        raise HTTPException(404, f"Không có cảnh mã '{ma}' trong chương {chuong}.")

    def _khung(c: dict) -> str:
        """Câu KHUNG — "{cỡ}, {góc}: {cái gì lấp khung}." — đứng ĐẦU prompt.

        Đo 27/09 (trang ⑬): cỡ cảnh vào bằng ba chữ "Close-up, eye level."
        trước 134 chữ thì WS/MS/ECU ra 9 tấm một cỡ, 0/9. Câu này đứng đầu
        kèm "cái gì lấp khung" thì EWS/WS 3/3; khi đoạn sau viết theo khung thì
        CU/ECU/top/POV 3/3. Thứ ở đầu prompt được nghe to nhất.

        `co` và `goc` DỊCH RA CHỮ đã đo; `goc` cũ là chữ tự do thì đi nguyên.
        Chưa có cột nào thì trả rỗng — prompt bắt đầu thẳng bằng `pa`.
        """
        co = CO_CHU.get((c.get("co") or "").upper(), "")
        g = (c.get("goc") or "").strip()
        dau = ", ".join(x for x in (co, GOC_CHU.get(g, g)) if x)
        if not dau:
            return ""
        dau = dau[:1].upper() + dau[1:]
        lap = (c.get("lap") or "").strip()
        return f"{dau}: {lap}." if lap else f"{dau}."

    def _mo_hinh(tap: str, c: dict | None, loai: str) -> str:
        """Model HIỆU LỰC: cảnh đè (`mda`/`mdv`) > tập > "" (= theo két, nhà tự
        lấy). Owner 27/09: chọn model ngay trong UI, đè được theo cảnh."""
        khoa = "mda" if loai == "anh" else "mdv"
        m = ((c or {}).get(khoa) or "").strip()
        return m or (kho.mo_hinh_tap(tap).get(loai) or "").strip()

    def _giay_clip(tap: str | None = None, c: dict | None = None) -> int:
        """Độ dài clip theo model video HIỆU LỰC — lệnh LLM, prompt video và
        trang cùng đọc một chỗ. Model không có trong bảng thì theo nhà; nhà
        không báo thì 15 như cũ. Clip drama mang độ dài người dựng chọn (`gi`)."""
        if c and str(c.get("gi") or "").isdigit():
            return int(c["gi"])
        m = _mo_hinh(tap, c, "video") if tap else ""
        bang = getattr(ve_video, "giay_theo_model", None) or {}
        if m and m in bang:
            return int(bang[m])
        return int(getattr(ve_video, "giay", None) or GIAY_VIDEO)

    @app.get("/api/cau-hinh/video")
    def cau_hinh_video(tap: str = ""):
        return {"giay": _giay_clip(tap or None)}

    def _mo_ta_ts(so: list[dict], c: dict) -> str:
        """Khối mô tả tài sản chêm vào prompt — CHỈ cho tài sản CHƯA có ref.

        Đo thật 26/09, bốn lượt vẽ trên cùng một cảnh (thang máy Liên Xô, cỡ CU,
        đã có ref):

          A  pa đầy đủ + khối mô tả 77 từ + ref  -> khuôn hình vẫn RỘNG
          B  bỏ khối mô tả, giữ ref              -> danh tính GIỮ NGUYÊN (đúng
                                                    bóng đèn, sơn, sàn, bảng nút),
                                                    khuôn hình chặt lại
          D  giữ khối mô tả, BỎ ref              -> thang máy KHÁC HẲN, ra ảnh
                                                    dựng 3D thay vì ảnh chụp

        Tức là ảnh ref neo danh tính, khối chữ KHÔNG neo được — nó chỉ giành chỗ
        với khuôn hình, và nhắc lại thứ `pa` đã tả nên nhà AI cân về phía bối
        cảnh thay vì chủ thể. Asset CHƯA có ref thì giữ nguyên đường cũ: lúc đó
        chữ là thứ duy nhất neo được nó.

        CÙNG LUẬT với `moTaTaiSan()` bên trang, canh bằng test tĩnh.
        """
        tra = {x["ma"]: x for x in so}
        ta = [tra[m] for m in (c.get("ts") or [])
              if m in tra and tra[m].get("chu") and not tra[m].get("ref")]
        mo_ta = "".join(f"{x['ten']}: {x['chu']}\n" for x in ta)
        return mo_ta + "\n" if mo_ta else ""

    def _prompt_anh(tap: str, c: dict) -> str:
        """ĐÚNG cái người dùng thấy trong hộp: nội dung EN + mô tả tài sản +
        đoạn tông. Gửi mỗi `pa` thì ảnh mất tông, khác hẳn bản họ duyệt."""
        tay = (c.get("pat") or "").strip()
        if tay:
            return tay      # sửa tay thì THẤY GÌ GỬI NẤY, không ghép thêm chữ nào
        so = _so_day_du(tap)
        mo_ta = _mo_ta_ts(so, c)
        tong = _tong_chu(so, c.get("tong") or "")
        # Không còn "16:9 ratio." mở đầu: cỡ khung đi bằng tham số `size`, và
        # mọi cấu hình đo ra chạy ở trang ⑬ đều không có nó — câu KHUNG phải là
        # thứ đầu tiên nhà AI đọc.
        kh = _khung(c)
        return f"{kh + ' ' if kh else ''}{c['pa']}\n\n{_loi_ref(tap, c)}{mo_ta}{tong}".strip()

    def _loi_ref(tap: str, c: dict) -> str:
        """Tập khuôn 2: đánh số ĐÚNG danh sách ảnh sẽ gửi (`_ref_ve`) kèm lời dặn
        lấy gì, bỏ gì. Đứng SAU câu khung + `pa` — câu đầu là câu nhà AI nghe to
        nhất (đo 27/09). CÙNG LUẬT với `loiRef()` bên trang."""
        if kho.kieu_tap(tap)["khuon"] != "2":
            return ""
        loai = {x["ma"]: x["loai"] for x in kho.ds_so(tap)}
        ds = [loai.get(t.stem, "dao_cu") for t in _ref_ve(tap, c)]
        return (" ".join(mtai_san.LOI_REF.get(x, mtai_san.LOI_REF["dao_cu"]).format(i=i)
                         for i, x in enumerate(ds, 1)) + "\n\n") if ds else ""

    def _prompt_video(tap: str, c: dict) -> str:
        """ĐÚNG cái người dùng thấy ở ô "Prompt video" trong hộp cảnh.

        CÙNG LUẬT với `promptVideo()` bên trang, từng nhánh một. Đây chính là
        chỗ đã sinh ra lỗi nặng nhất của cả đợt: prompt ẢNH có hai bản dựng ở
        hai tầng rồi trôi khỏi nhau, người dùng duyệt một đằng máy gửi một nẻo.
        Lần này viết kèm phép đo so từng chữ ngay từ đầu.
        """
        tay = (c.get("pvt") or "").strip()
        if tay:
            return tay
        if c.get("pm"):
            return _prompt_drama(tap, c)
        so = _so_day_du(tap)
        mo_ta = _mo_ta_ts(so, c)
        cd = (c.get("cd") or "").strip()
        # Câu MÁY đứng ĐẦU (đo ⑬ mục 7: ở giữa thì pan/truck đứng yên, lên đầu
        # thì truck 3/3). Mã mới -> câu đã đo; `cd` cũ là chữ tự do -> "Camera:
        # <cd>." vẫn đứng đầu; không có -> câu chung như trước.
        may = CD_CHU.get(cd) or (f"Camera: {cd}." if cd else "Simple camera motion only.")
        kh = _khung(c)
        dau = (f"{may} {kh + ' ' if kh else ''}Continue this camera move for the full "
               f"{_giay_clip(tap, c)} seconds.")
        sfx = (c.get("sfx") or "").strip()
        return (f"{dau}\n{c['pv']}\nOne continuous shot, no cuts.\n\n"
                f"{mo_ta}{_tong_chu(so, c.get('tong') or '')}"
                + (f" Sound: {sfx}." if sfx else "") + " No background music.")

    def _prompt_drama(tap: str, c: dict) -> str:
        """Prompt Grok của một clip drama: phần LLM viết (`pd`) + câu thoại
        NGUYÊN VĂN + mốc giây theo `gi` đang chọn — Python ghép (`drama.py`).
        Ảnh đánh số theo `ts` — đúng danh sách sẽ gửi, vì `_video_drama` chặn
        khi asset nào trong `ts` chưa có ảnh: thấy gì gửi nấy."""
        pd = pd_ghep(mdrama.doc_pd(c.get("pd")), mdrama.doc_sh(c.get("sh")))
        # Shot viết cho chữ cũ mà câu thoại đã đổi thì trỏ câu không còn: coi như
        # chưa có prompt, không để IndexError làm 500 mọi đường dựng prompt.
        if not pd or mdrama.kiem_pd(pd, c.get("t") or ""):
            return ""
        so = kho.ds_so(tap)
        tra = {x["ma"]: x for x in so}
        anh = [{"loai": tra[m]["loai"], "ten": tra[m]["ten"], "chu": tra[m].get("chu", "")}
               for m in (c.get("ts") or []) if m in tra]
        tieng = {x["ten"].split(" · ")[0]: x["tieng"] for x in so
                 if x["loai"] == "nhan_vat" and (x.get("tieng") or "").strip()
                 and not mdrama.la_tieng_viet(x["tieng"])}
        return mdrama.prompt_clip(pd, c.get("t") or "", anh, tieng, _giay_clip(tap, c))

    def _noi_chon(cs: list[dict], tra: dict) -> str:
        noi = next((tra[m] for c in cs for m in (c.get("ts") or [])
                    if m in tra and tra[m]["loai"] == "boi_canh"), None)
        return "NƠI CHỐN: " + (f"{noi['ten']} — {noi.get('chu') or noi.get('yc') or ''}" if noi else "(chưa gán)")

    def _khoi_clip(c: dict, tra: dict) -> list[str]:
        """Khối MỘT clip trong thân lượt LLM. Câu thoại đánh số [k]: LLM chỉ trỏ
        số, Python chèn câu nguyên văn."""
        khung = [tra[m]["ten"].split(" · ")[0] for m in (c.get("ts") or [])
                 if m in tra and tra[m]["loai"] == "nhan_vat"]
        dong = [f"### {c['pm']} ({_giay_clip(None, c)} giây) · trong khung: {', '.join(khung) or '(không ai)'}"]
        dong += [d for d in (c.get("t") or "").splitlines()
                 if d.split(":", 1)[0].strip().lower() not in ("thoại", "lời nghĩ")]
        for k, lt in enumerate(mdrama.loi_thoai(c.get("t"))):
            dong.append(f"[{k}] " + ("Lời nghĩ " if lt["nghi"] else "") + lt["ten"]
                        + (f" ({lt['cach']})" if lt["cach"] else "") + f": \"{lt['cau']}\"")
        return dong + [""]

    def _than_drama(dg: dict, cs: list[dict], tra: dict) -> tuple[str, list[str]]:
        """Thân lượt LLM viết PHẦN CHUNG của một cảnh drama — thấy mọi clip để hiểu
        cảnh. Trả (thân, người cần giọng)."""
        nguoi: dict[str, dict] = {}
        for c in cs:
            for m in c.get("ts") or []:
                if m in tra and tra[m]["loai"] == "nhan_vat":
                    nguoi.setdefault(tra[m]["ten"].split(" · ")[0], tra[m])
        goc = {x["ten"].split(" · ")[0].lower(): x for x in tra.values() if x["loai"] == "nhan_vat"}
        for c in cs:
            for lt in mdrama.loi_thoai(c.get("t")):
                x = goc.get(lt["ten"].lower())
                if x is not None:
                    nguoi.setdefault(x["ten"].split(" · ")[0], x)
        can = [t for t, x in nguoi.items()
               if not (x.get("tieng") or "").strip() or mdrama.la_tieng_viet(x["tieng"])]
        dong = [f"CẢNH: {dg.get('en', '')}", dg.get("vi", ""), _noi_chon(cs, tra), "NGƯỜI:"]
        dong += [f"- {t}: {x.get('chu', '')} | giọng: {x.get('tieng') or '(chưa có)'}" for t, x in nguoi.items()]
        dong += [f"CẦN CÂU GIỌNG: {', '.join(can) or '(không)'}", "", "CLIP:"]
        for c in cs:
            dong += _khoi_clip(c, tra)
        return "\n".join(dong), can

    def _than_clip(dg: dict, cs: list[dict], c: dict, tra: dict, chung: dict) -> str:
        """Thân lượt LLM viết MỘT clip: phần chung đã chốt của cảnh + chỉ clip này
        + các shot người dựng đã chốt (khung bằng chữ của bảng, ý, câu nói)."""
        nv = [tra[m] for m in (c.get("ts") or []) if m in tra and tra[m]["loai"] == "nhan_vat"]
        dong = [f"CẢNH: {dg.get('en', '')}", dg.get("vi", ""), _noi_chon(cs, tra),
                f"TRỤC CẢNH: {chung.get('truc') or '(chưa có)'}", "TRONG KHUNG:"]
        dong += [f"- {x['ten'].split(' · ')[0]}: {x.get('chu', '')}" for x in nv] or ["(không ai)"]
        lt = mdrama.loi_thoai(c.get("t"))
        shot = ["SHOT ĐÃ CHỐT (viết đúng từng shot, đúng thứ tự):"]
        for k, s in enumerate(mdrama.doc_sh(c.get("sh")), 1):
            khung = ", ".join(x for x in (CO_CHU.get(s.get("co") or "", ""), GOC_CHU.get(s.get("goc") or "", "")) if x)
            may = CD_DRAMA.get(s.get("cd") or "", "")
            noi = ", ".join(f"[{i}] {lt[i]['ten']}" for i in mdrama.chi_so(s) if 0 <= i < len(lt)) or "không ai nói"
            shot.append(f"- Shot {k} · {khung}" + (f" · {may}" if may else "") + f" · ý: {s.get('t') or ''} · nói: {noi}")
        return "\n".join(dong + [""] + _khoi_clip(c, tra) + shot)

    def _canh_drama(tap: str, chuong: str, i: int, viec: str = "drama_clip") -> tuple[dict, list[dict], dict]:
        if ky_thuat is None or not hasattr(ky_thuat, viec):
            raise HTTPException(503, "Chưa bật bộ sinh prompt.")
        d = kho.doc(tap, chuong)["dong"]
        if not 0 <= i < len(d):
            raise HTTPException(404, "Không có cảnh này.")
        cs = [c for c in mdong.doc_canh(d[i]) if c.get("pm") and c.get("id")]
        if not cs:
            raise HTTPException(400, "Dòng này không có clip drama nào.")
        return d[i], cs, {x["ma"]: x for x in kho.ds_so(tap)}

    def _phan_chung(tap: str, dg: dict, cs: list[dict], tra: dict) -> dict:
        """Lượt PHẦN CHUNG của cảnh (ánh sáng, trục, nền — khuôn Padoma: giống
        nhau giữa các clip, lệch là lộ khi dựng) + câu giọng người còn thiếu."""
        than, can = _than_drama(dg, cs, tra)
        try:
            chung = ky_thuat.drama_canh(than) or {}
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Viết prompt hỏng: {exc}") from exc
        tg = chung.get("tieng") if isinstance(chung.get("tieng"), dict) else {}
        # Giọng: chỉ điền người còn thiếu giọng tiếng Anh, cho MỌI bộ đồ của
        # người đó — viết một lần, các cảnh sau dùng lại nguyên câu.
        moi = {t: str(v).strip() for t, v in tg.items() if t in can and str(v).strip()
               and not mdrama.la_tieng_viet(str(v))}
        if moi:
            so = kho.ds_so(tap)
            for x in so:
                t = x["ten"].split(" · ")[0]
                if x["loai"] == "nhan_vat" and t in moi and (
                        not (x.get("tieng") or "").strip() or mdrama.la_tieng_viet(x["tieng"])):
                    x["tieng"] = moi[t]
            kho.luu_so(tap, so)
        return {k: str(chung.get(k) or "") for k in ("look", "truc", "nen")}

    def _viet_clip(tap: str, chuong: str, dg: dict, cs: list[dict], chon: list[dict], tra: dict,
                   chung: dict, ai: str) -> dict:
        """Mỗi clip một lượt LLM, chạy SONG SONG (kiểm thử 28/10: một lượt cả cảnh
        5 clip quá 180 s 2/2 lần); phần chung giữ y nguyên ở mọi clip. LLM chỉ viết
        chữ cho các shot ĐÃ CHỐT. Clip nào lệch số shot hay câu vị trí / câu khung
        nhắc người NGOÀI KHUNG (Grok vẽ thêm người đó) thì KHÔNG lưu clip đó, báo
        rõ; clip đúng vẫn lưu."""
        import json as _json
        from concurrent.futures import ThreadPoolExecutor

        def mot(c):
            try:
                return ky_thuat.drama_clip(_than_clip(dg, cs, c, tra, chung)) or {}
            except Exception as exc:  # noqa: BLE001 — hỏng một clip không bỏ cả cảnh
                return exc

        with ThreadPoolExecutor(max_workers=min(len(chon), 6)) as ex:
            ra = list(ex.map(mot, chon))
        ten_nv = {x["ten"].split(" · ")[0] for x in tra.values() if x["loai"] == "nhan_vat"}
        viet, loi = 0, []
        for c, x in zip(chon, ra):
            if isinstance(x, Exception):
                loi.append(f"{c['pm']}: viết prompt hỏng: {x}")
                continue
            sh = mdrama.doc_sh(c.get("sh"))
            ds = [s for s in (x.get("shots") or []) if isinstance(s, dict)]
            if len(ds) != len(sh):
                loi.append(f"{c['pm']}: LLM viết {len(ds)} shot, clip đã chốt {len(sh)} shot")
                continue
            pd = dict(chung, truc_canh=chung["truc"], truc=str(x.get("truc") or ""))
            pd.update({k: str(x.get(k) or "") for k in ("y", "size", "giu")},
                      shots=[{k: str(s.get(k) or "") for k in ("cach", "mat", "am")} for s in ds])
            lap = [str(s.get("lap") or "").strip() for s in ds]
            ngoai = sorted(ten_nv - {tra[m]["ten"].split(" · ")[0] for m in (c.get("ts") or [])
                                     if m in tra and tra[m]["loai"] == "nhan_vat"})
            sai = mdrama.kiem_pd(pd_ghep(pd, [dict(s, lap=l) for s, l in zip(sh, lap)]), c.get("t")) + [
                f"câu vị trí nhắc {n} — người này không có trong clip"
                for n in mdrama.nhac_ten(pd["truc"], ngoai)] + [
                f"shot {k}: câu khung nhắc {n} — người này không có trong clip"
                for k, l in enumerate(lap, 1) for n in mdrama.nhac_ten(l, ngoai)]
            if sai:
                loi += [f"{c['pm']}: {s}" for s in sai]
                continue
            chu = _json.dumps(pd, ensure_ascii=False)

            def va(y, chu=chu, lap=lap):
                # `lap` vá vào shot của bản MỚI NHẤT: người dựng đổi mã trong 30–90 s
                # chờ LLM thì mã của họ còn nguyên (dấu vết sẽ báo prompt cũ).
                hien = mdrama.doc_sh(y.get("sh"))
                if len(hien) == len(lap):
                    for s, l in zip(hien, lap):
                        s["lap"] = l
                    y["sh"] = _json.dumps(hien, ensure_ascii=False)
                y["pd"] = chu
            _va_canh(tap, chuong, c["id"], va, ai)
            kho.ghi_vet(tap, c["id"], "prompt", _dau_pd(c))
            viet += 1
        return {"ok": True, "viet": viet, "loi": loi}

    def _co_shot(cs: list[dict]) -> tuple[list[dict], list[str]]:
        """Clip đã Breakdown (shot hợp lệ với chữ hiện tại) / lỗi cho clip chưa."""
        co, loi = [], []
        for c in cs:
            if mdrama.kiem_pd({"shots": mdrama.doc_sh(c.get("sh"))}, c.get("t") or ""):
                loi.append(f"{c['pm']}: chưa Breakdown — bấm Breakdown trước đã")
            else:
                co.append(c)
        return co, loi

    def _breakdown_clip(tap: str, chuong: str, dg: dict, cs: list[dict], chon: list[dict], tra: dict,
                        ai: str) -> dict:
        """Mỗi clip một lượt LLM song song: chia shot theo `Hình:` + đặt mã cỡ/góc/máy
        (bảng của narration). Mã lạ về mặc định như Create Prompt narration (MS · eye),
        máy lạ bỏ trống. Chia thoại sai hay quá số shot của độ dài: không lưu clip đó.
        Shot mới thì prompt viết theo shot cũ hết nghĩa — bỏ `pd`."""
        import json as _json
        from concurrent.futures import ThreadPoolExecutor

        def mot(c):
            try:
                return ky_thuat.drama_breakdown(_than_bd(dg, cs, c, tra)) or {}
            except Exception as exc:  # noqa: BLE001 — hỏng một clip không bỏ cả cảnh
                return exc

        with ThreadPoolExecutor(max_workers=min(len(chon), 6)) as ex:
            ra = list(ex.map(mot, chon))
        so, loi = 0, []
        for c, x in zip(chon, ra):
            if isinstance(x, Exception):
                loi.append(f"{c['pm']}: breakdown hỏng: {x}")
                continue
            sh = []
            for s in (s for s in (x.get("shots") or []) if isinstance(s, dict)):
                co, goc, cd = (str(s.get(k) or "").strip() for k in ("co", "goc", "cd"))
                sh.append({"t": str(s.get("t") or "").strip(), "co": co.upper() if co.upper() in CO_CHU else "MS",
                           "goc": goc if goc in GOC_CHU else "eye", "cd": cd if cd in CD_DRAMA else "",
                           "lap": "", "cau": s.get("cau")})
            g = _giay_clip(tap, c)
            sai = mdrama.kiem_pd({"shots": sh}, c.get("t") or "")
            if mdrama.so_shot_qua_day(len(sh), g):
                sai.append(f"{len(sh)} shot không vừa clip {g} giây (mỗi shot ít nhất 2,5 giây)")
            if sai:
                loi += [f"{c['pm']}: {s}" for s in sai]
                continue
            for s in sh:
                s["cau"] = mdrama.chi_so(s)
            chu = _json.dumps(sh, ensure_ascii=False)

            def va(y, chu=chu):
                y["sh"] = chu
                y.pop("pd", None)
            _va_canh(tap, chuong, c["id"], va, ai)
            so += 1
        return {"ok": True, "so_clip": so, "loi": loi}

    def _than_bd(dg: dict, cs: list[dict], c: dict, tra: dict) -> str:
        return "\n".join([f"CẢNH: {dg.get('en', '')}", dg.get("vi", ""), _noi_chon(cs, tra), ""]
                         + _khoi_clip(c, tra))

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/breakdown")
    def breakdown_clip(tap: str, chuong: str, ma: str, request: Request):
        """Breakdown lại MỘT clip drama — clip khác giữ shot, prompt, video."""
        ai = _ghi_duoc(request)
        _, i, _, c = _tim_canh(tap, chuong, ma)
        if not c.get("pm"):
            raise HTTPException(400, "Đây không phải clip drama.")
        dg, cs, tra = _canh_drama(tap, chuong, i, "drama_breakdown")
        return _breakdown_clip(tap, chuong, dg, cs, [c], tra, ai)

    @app.post("/api/tap/{tap}/{chuong}/dong/{i}/prompt-drama")
    def prompt_drama(tap: str, chuong: str, i: int, request: Request):
        """Viết prompt MỌI clip ĐÃ BREAKDOWN của một cảnh drama: phần chung một
        lượt, rồi mỗi clip một lượt song song. Không clip nào có shot thì không gọi LLM."""
        ai = _ghi_duoc(request)
        dg, cs, tra = _canh_drama(tap, chuong, i)
        co, loi = _co_shot(cs)
        if not co:
            return {"ok": True, "viet": 0, "loi": loi}
        r = _viet_clip(tap, chuong, dg, cs, co, tra, _phan_chung(tap, dg, cs, tra), ai)
        return dict(r, loi=loi + r["loi"])

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/prompt-drama")
    def prompt_drama_clip(tap: str, chuong: str, ma: str, request: Request):
        """Viết lại prompt MỘT clip, dùng lại phần chung đã có của cảnh — clip khác
        không bị đụng, video của chúng không thành cũ oan. Cảnh chưa có phần chung
        thì viết phần chung trước."""
        ai = _ghi_duoc(request)
        _, i, _, c = _tim_canh(tap, chuong, ma)
        if not c.get("pm"):
            raise HTTPException(400, "Đây không phải clip drama.")
        dg, cs, tra = _canh_drama(tap, chuong, i)
        if not _co_shot([c])[0]:
            raise HTTPException(400, "Clip chưa Breakdown — bấm Breakdown trước đã.")
        cu = [x for x in (mdrama.doc_pd(y.get("pd")) for y in cs) if x.get("truc_canh")]
        chung = ({"look": str(cu[0].get("look") or ""), "truc": cu[0]["truc_canh"],
                  "nen": str(cu[0].get("nen") or "")} if cu else _phan_chung(tap, dg, cs, tra))
        return _viet_clip(tap, chuong, dg, cs, [c], tra, chung, ai)

    def _ref_ve(tap: str, c: dict) -> list:
        """Ảnh ref đi KÈM lượt vẽ: khung master trường đoạn trước, ref asset
        sau. Một chỗ duy nhất — lượt vẽ và dấu vết "cũ" cùng đọc từ đây."""
        ma_ref = ([c["td"]] if (c.get("td") or "").strip() else []) \
            + (c.get("ts") or [])
        return [t for t in (kho.ref_dang_co(tap, m) for m in ma_ref)
                if t is not None]

    def _bam(*phan) -> str:
        import hashlib
        import json as _json

        return hashlib.sha1(_json.dumps(phan, ensure_ascii=False, default=str)
                            .encode("utf-8")).hexdigest()[:16]

    def _mtime(t) -> int:
        try:
            return int(t.stat().st_mtime)
        except OSError:
            return 0

    def _dau_prompt(tap: str, en: str, c: dict, so: list) -> str:
        return _bam(en, c.get("t"), c.get("co") or "MS", c.get("goc") or "eye",
                    [(x.get("ma"), x.get("chu")) for x in so], _giay_clip(tap, c))

    def _dau_anh(tap: str, c: dict) -> str:
        return _bam(_prompt_anh(tap, dict(c, pa=c.get("pa") or "")),
                    [(t.name, _mtime(t)) for t in _ref_ve(tap, c)], _mo_hinh(tap, c, "anh"))

    def _dau_pd(c: dict) -> str:
        # Clip drama: LLM viết `pd` từ chữ clip + asset trong khung + cỡ/góc/thoại
        # từng shot — đổi là prompt cũ (như narration: chữ viết theo khung). Máy
        # (`cd`) và `lap` thì không: Python ghép thẳng vào câu khung.
        return _bam(c.get("t"), c.get("ts"), [(s.get("t"), s.get("co"), s.get("goc"), s.get("cau"))
                                              for s in mdrama.doc_sh(c.get("sh"))])

    def _dau_video(tap: str, c: dict) -> str:
        if c.get("pm"):
            # Clip drama không có ảnh cảnh: dấu là prompt + GIỜ SỬA các tấm tham chiếu
            # (vẽ lại tấm là video cũ) + chữ clip (đổi Hình mà prompt chưa viết lại).
            return _bam(_prompt_video(tap, c), [(t.name, _mtime(t)) for t in _ref_ve(tap, c)],
                        c.get("t"))
        # Ảnh nguồn tính theo GIỜ SỬA FILE: vẽ lại ảnh là video dựng từ ảnh cũ thành cũ.
        return _bam(_prompt_video(tap, dict(c, pv=c.get("pv") or "")),
                    _mtime(kho.duong_anh(tap, c["id"])), _giay_clip(tap, c),
                    _mo_hinh(tap, c, "video"))

    def _ve_mot_canh(tap: str, chuong: str, d: list, i: int, j: int, ai: str) -> None:
        c = mdong.doc_canh(d[i])[j]
        # Người đã tự viết tay thì thôi bắt đi qua LLM — đi vòng qua LLM CHÍNH LÀ
        # mục đích của ô sửa tay.
        if not ((c.get("pa") or "").strip() or (c.get("pat") or "").strip()):
            raise HTTPException(
                400, "Cảnh này chưa có prompt tiếng Anh — bấm Create Prompt trước, "
                     "hoặc tự sửa thẳng vào ô Prompt ảnh. Gửi chữ Việt cho "
                     "Seedream là ra ảnh sai.")
        # Ảnh ref của asset đã gán đi KÈM lượt vẽ. Asset chưa vẽ ref thì bỏ
        # qua, không chặn — gán rồi mà chưa kịp vẽ ref là chuyện thường giữa
        # chừng, lúc đó rơi về đúng hành vi cũ: chỉ có chữ.
        # Khung master của trường đoạn đi ĐẦU, ref asset theo sau — đúng
        # thứ tự đã đo 26/09 (9 lượt): [master, ref, ref] giữ được ba nhận
        # dạng cùng lúc. Trường đoạn chưa vẽ master thì bỏ qua như asset chưa
        # có ref: không chặn, rơi về đúng hành vi cũ.
        ref = _ref_ve(tap, c)
        m = _mo_hinh(tap, c, "anh")
        dau = _dau_anh(tap, c)
        ve_anh.gen_anh(_prompt_anh(tap, c), kho.duong_anh(tap, c["id"]), ref=ref,
                       **({"model": m} if m else {}))
        kho.ghi_vet(tap, c["id"], "anh", dau)
        # ảnh đổi thì con dấu duyệt cũ hết nghĩa — vá trên bản MỚI NHẤT
        _va_canh(tap, chuong, c["id"], lambda x: x.pop("duyet", None), ai)

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
        # KHUNG là của người dựng. Chưa chọn thì máy đặt MS · eye level (ghi
        # xuống để nút sáng trên hộp cảnh), KHÔNG để LLM đoán — đo 27/09: LLM
        # chọn thì chép danh sách ví dụ theo thứ tự (static 48%, eye level 53%).
        if not (cs[j].get("co") or "").strip():
            cs[j]["co"] = "MS"
        if not (cs[j].get("goc") or "").strip():
            cs[j]["goc"] = "eye"
        muc = [{"id": ma, "voice": d[i].get("en", ""), "canh": c["t"],
                "thu_tu": f"{j + 1}/{len(cs)}", "khung": _khung(cs[j]).rstrip("."),
                "giay": _giay_clip(tap, cs[j])}]
        dau = _dau_prompt(tap, d[i].get("en", ""), cs[j], so)
        try:
            ra = ky_thuat.ky_thuat(muc, so)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Sinh prompt hỏng: {exc}") from exc
        x = next((y for y in ra if str(y.get("id")) == ma), None)
        if x is None and len(ra) == 1:
            x = ra[0]
        if x is None:
            raise HTTPException(502, "LLM không trả về cảnh nào khớp mã.")

        # LLM chỉ còn viết CHỮ theo khung: `lap`, `pa`, `pv`, `sfx`. `co`/`goc`/
        # `cd` là của người dựng — LLM có trả cũng LỜ ĐI, không ghi đè.
        # KHÔNG đụng `ts`: người dùng chọn asset, không phải LLM (user chốt
        # 25/09 — "Không để LLM tự nhớ"). Bớt một chỗ nó bịa mã, và bấm Create
        # Prompt lần hai không xoá lựa chọn có chủ đích của người dùng.
        # Vá trên bản MỚI NHẤT (đo 28/09: ghi cả chương đọc từ trước lượt LLM
        # là xoá bản sửa của người khác trong 30-60 s chờ).
        def va(y):
            for khoa, mac in (("co", "MS"), ("goc", "eye")):
                if not (y.get(khoa) or "").strip():
                    y[khoa] = mac
            for khoa in ("lap", "pa", "pv", "sfx"):
                if (x.get(khoa) or "").strip():
                    y[khoa] = str(x[khoa]).strip()

        _va_canh(tap, chuong, ma, va, ai)
        kho.ghi_vet(tap, ma, "prompt", dau)
        return {"ok": True, "gan_asset": len(c.get("ts") or [])}

    @app.post("/api/tap/{tap}/{chuong}/dong/{i}/breakdown")
    def breakdown_dong(tap: str, chuong: str, i: int, request: Request):
        """Owner 27/09: người viết DIRECTION vắn tắt cho phân cảnh, LLM viết lại
        chi tiết + đặt góc · cỡ · máy, ghi THẲNG vào cảnh của dòng — không bảng
        duyệt ("sai thì tôi tự sửa như sửa prompt"). Đo ⑮ trên chương H.

        Cảnh cũ cùng vị trí giữ `id` (ảnh/video đã vẽ không mất dấu), giữ ts/td/
        tong/mda/mdv; bỏ prompt cũ (viết theo `t` cũ) và con dấu duyệt.

        Dòng drama (cảnh Cxxx, user chốt 28/10): mỗi clip chia shot theo `Hình:` +
        mã cỡ/góc/máy cùng bảng, cùng nút — `_breakdown_clip`.
        """
        ai = _ghi_duoc(request)
        d = kho.doc(tap, chuong)["dong"]
        if 0 <= i < len(d) and any(c.get("pm") for c in mdong.doc_canh(d[i])):
            dg, cs, tra = _canh_drama(tap, chuong, i, "drama_breakdown")
            return _breakdown_clip(tap, chuong, dg, cs, cs, tra, ai)
        if ky_thuat is None or not hasattr(ky_thuat, "breakdown"):
            raise HTTPException(503, "Chưa bật bộ sinh prompt.")
        d = kho.doc(tap, chuong)["dong"]
        if not 0 <= i < len(d):
            raise HTTPException(404, "Không có phân cảnh này.")
        cs = mdong.doc_canh(d[i])
        dau = kho.dau_dong(d[i])
        y = [(c.get("t") or "").strip() for c in cs if (c.get("t") or "").strip()]
        if not y:
            raise HTTPException(400, "Phân cảnh chưa có direction — viết trước đã.")
        voice = d[i].get("en") or ""
        giay = max(1, round(len(voice.split()) / TU_MOI_GIAY))
        so = [t for t in kho.ds_so(tap) if t.get("loai") in ("nhan_vat", "dao_cu", "boi_canh")]
        try:
            ra = ky_thuat.breakdown(voice, y, giay, so)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Breakdown hỏng: {exc}") from exc
        # ÉP 1:1 theo vị trí (Owner: mỗi ý một cú): cú k viết lại cảnh có ý k.
        # LLM trả thừa thì bỏ phần thừa; trả thiếu thì cảnh còn lại GIỮ NGUYÊN
        # — không mất ý nào của người dựng, không đẻ thêm cảnh.
        ra = list(ra or [])

        def lam(cs):
            co_y = [k for k, c in enumerate(cs) if (c.get("t") or "").strip()]
            moi = [dict(c) for c in cs]
            for k, r in zip(co_y, ra):
                t = str((r or {}).get("t") or "").strip()
                if not t:
                    continue
                c = moi[k]
                for khoa in ("lap", "pa", "pv", "sfx", "pat", "pvt", "duyet"):
                    c.pop(khoa, None)
                c["t"] = t
                for khoa, bang in (("co", CO_CHU), ("goc", GOC_CHU), ("cd", CD_CHU)):
                    v = str(r.get(khoa) or "").strip()
                    v = v.upper() if khoa == "co" else v
                    if v in bang:
                        c[khoa] = v
                    else:
                        c.pop(khoa, None)      # mã lạ thì bỏ, đừng gửi chữ tự do xuống prompt
            return moi

        doi = sum(1 for _, r in zip(y, ra) if str((r or {}).get("t") or "").strip())
        if not doi:
            raise HTTPException(502, "LLM không trả về cú máy nào.")
        # Ghi lên bản MỚI NHẤT của phân cảnh (đo 28/09: Opus 30-60 s/dòng, ghi
        # cả chương đọc từ trước là xoá mọi thứ người khác sửa trong lúc chờ).
        _sua_dong(tap, chuong, i, dau, lam, ai)
        return {"ok": True, "so_cu": doi, "so_y": len(y)}

    @app.post("/api/tap/{tap}/{chuong}/dong/{i}/bo-tro")
    def bo_tro_dong(tap: str, chuong: str, i: int, request: Request):
        """Đợt 2 (Owner 27/09): chen cú BỔ TRỢ vào giữa các cú chính đã breakdown.
        Chỉ thêm khi voice còn chỗ (~3 s/cú); cú chính giữ nguyên, cú mới có id mới."""
        ai = _ghi_duoc(request)
        if ky_thuat is None or not hasattr(ky_thuat, "bo_tro"):
            raise HTTPException(503, "Chưa bật bộ sinh prompt.")
        d = kho.doc(tap, chuong)["dong"]
        if not 0 <= i < len(d):
            raise HTTPException(404, "Không có phân cảnh này.")
        dau = kho.dau_dong(d[i])
        cs = [c for c in mdong.doc_canh(d[i]) if (c.get("t") or "").strip()]
        if not cs:
            raise HTTPException(400, "Phân cảnh chưa có cú máy nào — breakdown trước đã.")
        voice = d[i].get("en") or ""
        giay = max(1, round(len(voice.split()) / TU_MOI_GIAY))
        toi_da = max(0, min(3, round(giay / GIAY_MOI_CU) - len(cs)))
        if not toi_da:
            return {"ok": True, "them": 0, "giay": giay, "so_cu": len(cs)}
        so = [t for t in kho.ds_so(tap) if t.get("loai") in ("nhan_vat", "dao_cu", "boi_canh")]
        try:
            ra = ky_thuat.bo_tro(voice, cs, giay, toi_da, so)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Sinh cú bổ trợ hỏng: {exc}") from exc
        them = []
        for r in (ra or [])[:toi_da]:
            t = str((r or {}).get("t") or "").strip()
            sau = r.get("sau")
            if not t or not isinstance(sau, int) or not 0 <= sau <= len(cs):
                continue
            c = {"t": t}
            for khoa, bang in (("co", CO_CHU), ("goc", GOC_CHU), ("cd", CD_CHU)):
                v = str(r.get(khoa) or "").strip()
                v = v.upper() if khoa == "co" else v
                if v in bang:
                    c[khoa] = v
            them.append((sau, c))
        def lam(moi):
            moi = [c for c in moi if (c.get("t") or "").strip()]
            # chen từ SAU ra TRƯỚC để chỉ số `sau` của các cú còn lại không trôi
            for sau, c in sorted(them, key=lambda x: -x[0]):
                moi.insert(sau, dict(c))
            return moi

        if them:
            _sua_dong(tap, chuong, i, dau, lam, ai)
        return {"ok": True, "them": len(them), "giay": giay, "so_cu": len(cs) + len(them)}

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
        return {"ok": True}

    # Trường NGƯỜI sửa trong hộp cảnh. `duyet`/`vid`/`pa`/`pv`/`sfx` chỉ máy chủ
    # viết — trang tự đặt `duyet` là lách cổng tiền video.
    TRUONG_TAY = ("t", "lap", "pat", "pvt", "co", "goc", "cd", "ts", "td", "tong",
                  "mda", "mdv", "gi", "sh")

    def _sai_sh(chu: str, c: dict) -> str:
        """Shot hộp cảnh gửi lên — kiểm ở BIÊN TIN CẬY: khoá, mã trong bảng, thoại
        mỗi câu đúng một lần, đúng thứ tự, một shot một người nói."""
        import json as _json

        if not c.get("pm"):
            return "Chỉ clip drama mới có shot."
        try:
            sh = _json.loads(chu)
        except ValueError:
            return "`sh` không phải JSON."
        if not isinstance(sh, list) or not sh or not all(isinstance(s, dict) for s in sh):
            return "`sh` phải là danh sách shot."
        for k, s in enumerate(sh, 1):
            if set(s) - KHOA_SHOT:
                return f"shot {k}: khoá lạ {', '.join(sorted(set(s) - KHOA_SHOT))}."
            for khoa, bang in (("co", CO_CHU), ("goc", GOC_CHU), ("cd", CD_DRAMA)):
                if s.get(khoa) and s[khoa] not in bang:
                    return f"shot {k}: mã {khoa} '{s[khoa]}' không có trong bảng."
            if not all(isinstance(s.get(x, ""), str) for x in ("t", "lap")):
                return f"shot {k}: `t`/`lap` phải là chữ."
        return "; ".join(mdrama.kiem_pd({"shots": sh}, c.get("t") or ""))

    @app.patch("/api/tap/{tap}/{chuong}/canh/{ma}")
    def sua_mot_canh(tap: str, chuong: str, ma: str, request: Request,
                     than: dict = Body(...)):
        """Hộp cảnh ghi RIÊNG một cảnh, chỉ ĐÚNG trường vừa đổi, không cần khoá
        chương (28/09: hai người hai cảnh cùng chương thì người sau phải chờ).
        Rỗng = xoá khoá. Trả `v` để trang giữ số bản mới."""
        ai = _ghi_duoc(request)
        truong = than.get("truong")
        if not isinstance(truong, dict) or not truong:
            raise HTTPException(400, "Thiếu `truong`.")
        la = [k for k in truong if k not in TRUONG_TAY]
        if la:
            raise HTTPException(400, f"Không sửa được {', '.join(la)} từ hộp cảnh.")
        for k, gt in truong.items():
            if k == "ts":
                hop_le = isinstance(gt, list) and all(isinstance(x, str) for x in gt)
            else:
                hop_le = isinstance(gt, str)
            if not hop_le:
                raise HTTPException(400, f"`{k}` sai kiểu.")
        # Độ dài clip drama — chỉ mức Grok nhận (user chốt 27/10: chọn trên treatment).
        if "gi" in truong and truong["gi"].strip() and truong["gi"].strip() not in map(str, mdrama.GIAY_CHON):
            raise HTTPException(400, f"Độ dài {truong['gi']} giây không có — chỉ "
                                     f"{'/'.join(map(str, mdrama.GIAY_CHON))} giây.")
        if "sh" in truong and truong["sh"].strip():
            sai = _sai_sh(truong["sh"], _tim_canh(tap, chuong, ma)[3])
            if sai:
                raise HTTPException(400, sai)

        def va(c):
            for k, gt in truong.items():
                gt = [x.strip() for x in gt if x.strip()] if k == "ts" else gt.strip()
                if gt:
                    c[k] = gt
                else:
                    c.pop(k, None)

        c = _va_canh(tap, chuong, ma, va, ai)
        return {"ok": True, "v": c.get("v", "")}

    @app.get("/api/tap/{tap}/{chuong}/cu")
    def cu_chuong(tap: str, chuong: str):
        """Cảnh nào có kết quả CŨ: đầu vào hôm nay khác dấu đã ghi lúc chạy.
        Chưa từng ghi dấu -> không cũ (dữ liệu trước tính năng, đừng kêu oan)."""
        vet = kho.doc_vet(tap)
        tra = {x["ma"]: x for x in kho.ds_so(tap)}
        ra = {}
        for dg in kho.doc(tap, chuong)["dong"]:
            for c in mdong.doc_canh(dg):
                ma = c.get("id")
                if not ma:
                    continue
                v = {"prompt": False, "anh": False, "video": False}
                if vet.get((ma, "prompt")) and (c.get("pa") or "").strip():
                    so = [tra[m] for m in (c.get("ts") or []) if m in tra]
                    v["prompt"] = vet[(ma, "prompt")] != _dau_prompt(tap, dg.get("en", ""), c, so)
                elif vet.get((ma, "prompt")) and c.get("pm") and c.get("pd"):
                    v["prompt"] = vet[(ma, "prompt")] != _dau_pd(c)
                co_chu = (c.get("pa") or "").strip() or (c.get("pat") or "").strip()
                if vet.get((ma, "anh")) and co_chu and kho.duong_anh(tap, ma).exists():
                    v["anh"] = vet[(ma, "anh")] != _dau_anh(tap, c)
                co_pv = (c.get("pv") or "").strip() or (c.get("pvt") or "").strip() or c.get("pm")
                if vet.get((ma, "video")) and co_pv and kho.duong_video(tap, ma).exists():
                    v["video"] = vet[(ma, "video")] != _dau_video(tap, c)
                ra[ma] = v
        return ra

    @app.get("/api/tap/{tap}/{chuong}/canh/{ma}/prompt")
    def xem_prompt(tap: str, chuong: str, ma: str):
        """Bảng vẽ hiện ĐÚNG chuỗi sẽ gửi đi — gọi chính hàm ghép lúc gửi, không
        chép luật sang trang lần thứ ba. Chưa có chữ để ghép thì trả rỗng, cùng
        điều kiện mà nút vẽ/dựng dùng để chặn."""
        _, _, _, c = _tim_canh(tap, chuong, ma)
        co_anh = (c.get("pa") or "").strip() or (c.get("pat") or "").strip()
        co_vid = ((c.get("pv") or "").strip() or (c.get("pvt") or "").strip()
                  or (c.get("pd") or "").strip())
        return {"anh": _prompt_anh(tap, dict(c, pa=c.get("pa") or "")) if co_anh else "",
                "video": _prompt_video(tap, dict(c, pv=c.get("pv") or "")) if co_vid else ""}

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
        _tim_canh(tap, chuong, ma)
        if not kho.duong_anh(tap, ma).exists():
            raise HTTPException(400, "Cảnh này chưa có ảnh để duyệt.")
        _va_canh(tap, chuong, ma, lambda x: x.update(duyet="1"), ai)
        return {"ok": True}

    # ------------------------------------------------------------ video
    # GIAY_VIDEO: một nguồn ở `dich.py` — trang và lệnh LLM cùng đọc từ đó.

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
        if c.get("pm"):
            return _video_drama(tap, chuong, ma, c, ai)
        if not kho.duong_anh(tap, ma).exists():
            raise HTTPException(400, "Cảnh này chưa có ảnh — vẽ ảnh trước đã.")
        if not c.get("duyet"):
            raise HTTPException(
                400, "Ảnh của cảnh này chưa được duyệt. Tiền video chỉ đốt sau "
                     "cổng duyệt — xem ảnh rồi bấm Duyệt ảnh đã.")
        if not ((c.get("pv") or "").strip() or (c.get("pvt") or "").strip()):
            raise HTTPException(
                400, "Cảnh này chưa có prompt video — bấm Create Prompt trước, "
                     "hoặc tự sửa thẳng vào ô Prompt video.")

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
            m = _mo_hinh(tap, c, "video")
            dau = _dau_video(tap, c)
            tid = ve_video.bat_dau(_prompt_video(tap, c), dau_vao, _giay_clip(tap, c),
                                   False, **({"model": m} if m else {}))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Dựng video hỏng: {exc}") from exc
        kho.ghi_vet(tap, ma, "video_cho", dau)
        # Task ĐÃ trả tiền: mã phải xuống kho bất kể ai đang giữ chương.
        _va_canh(tap, chuong, ma, lambda x: x.update(vid=str(tid)), ai)
        return {"ok": True, "vid": str(tid)}

    def _video_drama(tap: str, chuong: str, ma: str, c: dict, ai: str) -> dict:
        """Clip drama: Grok dựng từ ẢNH THAM CHIẾU (nơi chốn, tấm nhân vật theo
        Khung, đồ vật), KHÔNG khung đầu, KHÔNG cổng duyệt ảnh (không có ảnh cảnh).
        Cổng tiền ở đây là đủ tấm: thiếu tấm nhân vật thì Grok tự bịa mặt mà vẫn
        trừ 108 credit — chặn trước khi gửi."""
        if not hasattr(ve_video, "bat_dau_ref"):
            raise HTTPException(503, "Bộ dựng video chưa có đường ảnh tham chiếu (Grok).")
        p = _prompt_video(tap, c)
        if not p:
            raise HTTPException(400, "Clip này chưa có prompt — bấm “Viết prompt cảnh” trước, "
                                     "hoặc tự sửa thẳng vào ô Prompt video.")
        tra = {x["ma"]: x for x in kho.ds_so(tap)}
        thieu = [tra[m]["ten"] if m in tra else m for m in (c.get("ts") or [])
                 if kho.ref_dang_co(tap, m) is None]
        if thieu:
            raise HTTPException(400, f"Chưa có ảnh tham chiếu cho: {', '.join(thieu)} — vẽ ở màn "
                                     "Asset trước. Gửi thiếu tấm là Grok tự bịa mặt mà vẫn mất tiền.")
        ref = _ref_ve(tap, c)
        if len(ref) > mdrama.ANH_TOI_DA:
            raise HTTPException(400, f"{len(ref)} ảnh tham chiếu, Grok chỉ nhận tốt tới "
                                     f"{mdrama.ANH_TOI_DA} — bớt asset của clip này.")
        dau = _dau_video(tap, c)
        try:
            tid = ve_video.bat_dau_ref(p, ref, _giay_clip(tap, c), model=mdrama.MODEL_VIDEO)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Dựng video hỏng: {exc}") from exc
        kho.ghi_vet(tap, ma, "video_cho", dau)
        # Task ĐÃ trả tiền: mã phải xuống kho bất kể ai đang giữ chương.
        _va_canh(tap, chuong, ma, lambda x: x.update(vid=str(tid)), ai)
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
            _va_canh(tap, chuong, ma, lambda x: x.pop("vid", None), ai)

        if tt == "succeeded":
            try:
                ve_video.tai_ve(r.get("video_url") or "",
                                kho.duong_video(tap, ma))
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(502, f"Tải video về hỏng: {exc}") from exc
            _quen_ma()
            cho = kho.doc_vet(tap).get((ma, "video_cho"))
            if cho:
                kho.ghi_vet(tap, ma, "video", cho)
                kho.xoa_vet(tap, ma, "video_cho")
            return {"trang_thai": "xong"}
        if tt in ("failed", "cancelled"):
            kho.xoa_vet(tap, ma, "video_cho")
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


def _may_ve(cd: dict, video: bool = False):
    """Chọn NHÀ theo `base_url` trong két: seedvis.com -> SeedvisClient (Nano
    Banana / Omni Flash / Veo), còn lại ModelArk như cũ. User chốt 27/09: đấu
    nối Seedvis, không dùng Seedance nữa. Model trong két là của việc đó (ảnh
    hay video); để trống thì lấy mặc định của nhà."""
    if "seedvis.com" in (cd.get("base_url") or ""):
        from autoedit.aigen.seedvis import SeedvisClient

        m = (cd.get("model") or "").strip() or None
        return SeedvisClient(api_key=cd.get("key", ""), base_url=cd.get("base_url") or "",
                             model_video=m if video else None, model_anh=None if video else m)
    from autoedit.aigen.client import ArkClient

    return ArkClient(api_key=cd.get("key", ""))


class _VeAnh:
    """Seedream qua ArkClient, khoá lấy từ KÉT bằng SLUG CỦA TREATMENT.

    KHÔNG để ArkClient tự đi tìm: nó đi qua `web/ket_v3` ghi cứng
    `SLUG = "rendery"` nên cấp phát của Treatment không bao giờ thấy — đúng lỗi
    đã phải sửa một lần cho `dich.py` ngày 23/09 (cấp phát đúng rồi mà app vẫn
    báo "chưa cấp"). Truyền khoá vào tận tay.
    """

    def gen_anh(self, prompt, dich, ref=None, model=None, ti_le=None):
        from autoedit.treatment.dich import doc_ket_viec

        cd = doc_ket_viec("gen_canh") or {}
        if not cd.get("key"):
            raise RuntimeError(
                "Chưa có khoá vẽ ảnh — Owner cấp ở General › API Keys › "
                "Theo app › Treatment › gen_canh.")
        # `ti_le` chỉ Seedvis nhận (tài sản khuôn Padoma: 1:1 / 9:16 / 16:9).
        return _may_ve(cd).gen_anh(prompt, dich, ref=ref, **({"model": model} if model else {}),
                                   **({"ti_le": ti_le} if ti_le else {}))


class _VeVideo:
    """Seedance qua ArkClient, khoá lấy từ KÉT bằng slug của Treatment.

    Dùng chung cấp phát `gen_canh` với bộ vẽ ảnh: một khoá ARK chạy cả Seedream
    lẫn Seedance. Tách việc riêng chỉ để đo tiền tách bạch thì làm sau.
    """

    def _may(self):
        from autoedit.treatment.dich import doc_ket_viec

        # Việc riêng `gen_video` (ảnh và video là hai model khác nhau ở Seedvis);
        # chưa cấp thì dùng chung `gen_canh` như trước.
        cd = doc_ket_viec("gen_video") or {}
        if not cd.get("key"):
            # `model` của gen_canh là model ẢNH — không đem sang video. Bỏ để
            # nhà tự lấy model video mặc định.
            cd = {k: v for k, v in (doc_ket_viec("gen_canh") or {}).items() if k != "model"}
        if not cd.get("key"):
            raise RuntimeError(
                "Chưa có khoá dựng video — Owner cấp ở General › API Keys › "
                "Theo app › Treatment › gen_canh.")
        return _may_ve(cd, video=True)

    @property
    def giay(self):
        """Độ dài clip của NHÀ đang dùng: Seedvis 8, ModelArk 15."""
        try:
            return int(getattr(self._may(), "giay", GIAY_VIDEO) or GIAY_VIDEO)
        except Exception:  # noqa: BLE001 — chưa cấp khoá thì vẫn ghép prompt được
            return GIAY_VIDEO

    @property
    def giay_theo_model(self):
        """Độ dài theo từng model video (UI cần để bày và để cảnh đè)."""
        try:
            from autoedit.aigen.seedvis import GIAY_THEO_MODEL
            return dict(GIAY_THEO_MODEL) if "seedvis" in type(self._may()).__name__.lower() else {}
        except Exception:  # noqa: BLE001
            return {}

    @property
    def danh_sach(self):
        """Model đang mở ở nhà đang nối — cho bảng chọn. ModelArk: không có bảng."""
        try:
            m = self._may()
            return m.ds_model() if hasattr(m, "ds_model") else []
        except Exception:  # noqa: BLE001
            return []

    @property
    def credit(self):
        try:
            m = self._may()
            return m.tai_khoan().get("credit") if hasattr(m, "tai_khoan") else None
        except Exception:  # noqa: BLE001
            return None

    def bat_dau(self, prompt, anh, giay, am, model=None):
        kw = {"model": model} if model else {}
        return self._may().gen_video_i2v(prompt, anh, giay=giay, am=am, **kw)

    def bat_dau_ref(self, prompt, anh, giay, model=None):
        """Drama: dựng từ ảnh tham chiếu (Grok `multi-image-to-video`)."""
        m = self._may()
        if not hasattr(m, "gen_video_ref"):
            raise RuntimeError("Nhà video đang cấp không có đường ảnh tham chiếu — "
                               "drama cần Seedvis (Owner cấp ở General › API Keys › gen_video).")
        return m.gen_video_ref(prompt, anh, giay=giay, **({"model": model} if model else {}))

    def trang_thai(self, tid):
        return self._may().trang_thai_video(tid)

    def tai_ve(self, url, dich):
        return self._may().tai_video(url, dich)


def _ve_video_mac_dinh(kho: Kho):
    _ = kho
    return _VeVideo()


def _ve_anh_mac_dinh(kho: Kho):
    _ = kho
    return _VeAnh()


# ── BREAKDOWN direction -> cú máy (Owner 27/09) ─────────────────────────────
# Đo trên chương H thật (trang ⑮, 12 lượt Opus): 54/54 mã đúng bảng, static
# 19% / eye 20% (LLM tự chọn không direction: 48% / 53%), ràng buộc của người
# dựng giữ 12/12. Luật 2 đổi sau đó theo Owner: MỖI Ý = MỘT CÚ (đo lại trên
# H: 4/7/4/3 ý -> 4/7/4/3 cú). Máy chủ vẫn ép 1:1 theo vị trí, không tin LLM.
_LENH_BREAKDOWN = (
    "Bạn là trợ lý đạo diễn. Người dựng đưa cho bạn MỘT DÒNG voice (tiếng Anh) và "
    "DIRECTION của họ cho dòng đó (tiếng Việt, viết vắn tắt, có thể chỉ vài chữ mỗi ý). "
    "Việc của bạn: BREAKDOWN direction đó thành các CÚ MÁY dựng được — viết lại mô tả "
    "cho rõ, và đặt góc máy · cỡ cảnh · chuyển động máy phù hợp với nghĩa của từng cú.\n\n"
    "LUẬT:\n"
    "1. TRUNG THÀNH với direction: mỗi ý người dựng đã ghi phải thành ít nhất một cú máy, "
    "đúng thứ tự. KHÔNG bịa thêm nhân vật, đồ vật, địa điểm ngoài voice + direction + "
    "danh sách asset. Ràng buộc người dựng ghi (ví dụ \"không show trọn vẹn tàu\") là luật.\n"
    "2. MỖI Ý = ĐÚNG MỘT CÚ MÁY, cùng thứ tự: direction có K ý thì trả về đúng K cú, "
    "cú thứ k viết lại ý thứ k. Không gộp, không tách, không thêm cú.\n"
    "3. Mô tả `t`: tiếng Việt, 1–2 câu, CỤ THỂ: chủ thể + hành động + môi trường ngay "
    "trong câu (dưới nước thì nói dưới nước). Không tả màu sắc, không tả tông phim.\n"
    "4. Góc máy `goc`, cỡ `co`, chuyển động `cd` CHỈ lấy trong ba bảng dưới, ghi đúng MÃ. "
    "Chọn theo nghĩa của cú máy (nhỏ bé/bị theo dõi → high angle; sức nặng → low angle; "
    "chi tiết → CU/ECU; bao quát → WS/EWS), KHÔNG chọn theo thứ tự bảng. Hai cú liền "
    "nhau không cùng cỡ; không quá 1/3 số cú là static.\n"
    "5. `ly_do`: một câu ngắn vì sao chọn góc/cỡ/máy đó.\n\n"
    "BẢNG CỠ (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in CO_CHU.items()) + "\n"
    "BẢNG GÓC (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in GOC_CHU.items()) + "\n"
    "BẢNG CHUYỂN ĐỘNG (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in CD_CHU.items()) + "\n\n"
    "Trả về JSON: {\"canh\": [{\"t\": \"...\", \"co\": \"MS\", \"goc\": \"eye\", "
    "\"cd\": \"push_in\", \"ly_do\": \"...\"}]}")

TU_MOI_GIAY = 2.6      # cùng con số với trang (`TU_MOI_GIAY`) để ước giây voice
GIAY_MOI_CU = 3.0      # mỗi cú cần ~3 giây voice; thiếu chỗ thì KHÔNG thêm cú bổ trợ

# Cú BỔ TRỢ (Owner 27/09, đợt 2): chen insert / cutaway / establishing vào giữa
# các cú chính đã breakdown. Đo trên H đã breakdown (8 lượt Opus): 8/8 mã + vị
# trí hợp lệ, 4/4 lượt không đủ chỗ trả rỗng đúng. `%d` = tối đa · giây · số cú.
_LENH_BO_TRO = (
    "Bạn là trợ lý đạo diễn. Phân cảnh dưới đây ĐÃ được breakdown thành các cú máy "
    "chính (mỗi cú = một ý của người dựng). Việc của bạn: đề xuất thêm CÚ BỔ TRỢ — insert "
    "chi tiết, cutaway, phản ứng, establishing — chen vào giữa các cú chính để mạch dựng "
    "giàu hơn, KHÔNG thay đổi cú chính nào.\n\n"
    "LUẬT:\n"
    "1. Cú bổ trợ phải phục vụ cú chính bên cạnh nó: chi tiết của chính thứ đang thấy, "
    "phản ứng của người đang có mặt, hoặc toàn cảnh của đúng không gian đó. KHÔNG bịa "
    "nhân vật, đồ vật, địa điểm ngoài voice + cú chính + danh sách asset. KHÔNG lặp lại "
    "nội dung một cú chính đã có.\n"
    "2. Số cú bổ trợ: tối đa %d (voice ~%d giây, hiện có %d cú, mỗi cú cần ~3 giây). "
    "Không đủ chỗ thì trả về danh sách rỗng — thà ít còn hơn nhồi.\n"
    "3. `sau`: số thứ tự cú chính mà cú bổ trợ đứng NGAY SAU (0 = đứng trước cú 1).\n"
    "4. Mô tả `t`: tiếng Việt, 1–2 câu, cụ thể: chủ thể + hành động + môi trường. Không tả "
    "màu, không tả tông.\n"
    "5. `co`/`goc`/`cd` CHỈ lấy mã trong ba bảng dưới; chọn theo nghĩa; cỡ phải KHÁC cú "
    "chính đứng liền trước và liền sau nó.\n"
    "6. `ly_do`: một câu vì sao cú này bổ trợ cho cú chính nào.\n\n"
    "BẢNG CỠ: " + "; ".join(f"{k}: {v}" for k, v in CO_CHU.items()) + "\n"
    "BẢNG GÓC: " + "; ".join(f"{k}: {v}" for k, v in GOC_CHU.items()) + "\n"
    "BẢNG CHUYỂN ĐỘNG: " + "; ".join(f"{k}: {v}" for k, v in CD_CHU.items()) + "\n\n"
    "Trả về JSON: {\"them\": [{\"sau\": 1, \"t\": \"...\", \"co\": \"CU\", \"goc\": \"eye\", "
    "\"cd\": \"static\", \"ly_do\": \"...\"}]}")


# Breakdown clip DRAMA (user chốt 28/10): clip Grok = nhiều shot cắt cứng; shot
# lấy từ `Hình:` của biên kịch (skill Padoma viết sẵn "shot 1 … Shot 2 …"), mã
# cỡ/góc/máy cùng ba bảng narration. Python kiểm thoại + số shot theo độ dài.
_LENH_BREAKDOWN_DRAMA = (
    "Bạn là trợ lý đạo diễn phim DRAMA CÓ THOẠI dựng bằng Grok Imagine 1.5 — một clip là nhiều shot "
    "cắt cứng. Bạn nhận MỘT CLIP: mã, số giây, ai trong khung, chữ của biên kịch (tiếng Việt; `Hình:` "
    "tả từng shot), câu thoại đánh số [0], [1]… Việc của bạn: BREAKDOWN clip thành các SHOT và đặt "
    "cỡ cảnh · góc máy · chuyển động máy cho từng shot.\n\n"
    "LUẬT:\n"
    "1. Theo `Hình:`: mỗi \"shot n\" của biên kịch là MỘT shot, đúng thứ tự. `Hình:` không chia shot thì "
    "mỗi lượt người nói một shot.\n"
    "2. Mỗi shot ít nhất 2,5 giây: clip 6 giây tối đa 2 shot, 10 giây tối đa 4, 15 giây tối đa 6 — "
    "nhiều hơn thì gộp các shot liền nhau.\n"
    "3. `cau`: mảng số câu thoại shot đó nói; shot không ai nói thì []. MỌI câu có mặt đúng một lần, "
    "đúng thứ tự; một shot chỉ một người nói.\n"
    "4. `t`: tiếng Việt, 1–2 câu, giữ ý của `Hình:` cho shot đó (ai, làm gì, ở đâu trong khung). Không "
    "bịa người ngoài khung.\n"
    "5. `co`/`goc`/`cd` CHỈ lấy MÃ trong ba bảng dưới. Theo chữ máy của biên kịch trước: cận → CU, cực "
    "cận → ECU, trung cận → MCU, trung → MS, toàn/rộng → WS, qua vai → ots, góc thấp → low, góc cao → high, "
    "đẩy vào → push_in, lùi ra → pull_out, bám theo → track, máy ngước → tilt_up, máy cúi → tilt_down. "
    "Biên kịch không nói thì chọn theo nghĩa; hai shot liền nhau không cùng cỡ; máy không có ý đồ thì static.\n"
    "6. Máy làm cỡ đổi trong shot (đẩy vào, lùi ra): `co` là cỡ LÚC BẮT ĐẦU shot — đẩy vào tới cận → "
    "MCU + push_in, lùi ra tới toàn → MS + pull_out. Ghi cỡ cuối thì Grok mở ngay ở cỡ đó và gần như "
    "không đẩy.\n"
    "7. `ly_do`: một câu vì sao chọn mã đó.\n\n"
    "BẢNG CỠ (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in CO_CHU.items()) + "\n"
    "BẢNG GÓC (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in GOC_CHU.items()) + "\n"
    "BẢNG CHUYỂN ĐỘNG (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in CD_DRAMA.items()) + "\n\n"
    "Trả về JSON: {\"shots\": [{\"t\": \"...\", \"co\": \"CU\", \"goc\": \"ots\", \"cd\": \"static\", "
    "\"cau\": [0], \"ly_do\": \"...\"}]}")


def _than_bo_tro(voice: str, canh: list[dict], giay: int, tai_san: list[dict]) -> str:
    chinh = "\n".join(f"{k + 1}) [{c.get('co') or '?'} · {c.get('goc') or '?'} · {c.get('cd') or '?'}] "
                      f"{(c.get('t') or '').strip()}" for k, c in enumerate(canh))
    so = "\n".join(f"- {t.get('ten', '')}" for t in tai_san) or "(tập chưa lập sổ asset)"
    return f"VOICE (~{giay} giây): {voice}\n\nCÚ CHÍNH ĐÃ CÓ:\n{chinh}\n\nASSET CỦA TẬP:\n{so}"


def _than_breakdown(voice: str, y: list[str], giay: int, tai_san: list[dict]) -> str:
    loai = {"nhan_vat": "người", "dao_cu": "vật", "boi_canh": "bối cảnh"}
    so = "\n".join(f"- {t.get('ten', '')} ({loai.get(t.get('loai'), t.get('loai'))})"
                   for t in tai_san) or "(tập chưa lập sổ asset)"
    dr = "\n".join(f"{k + 1}) {t}" for k, t in enumerate(y))
    return (f"VOICE (tiếng Anh, ~{giay} giây): {voice}\n\nDIRECTION của người dựng "
            f"({len(y)} ý, giữ thứ tự):\n{dr}\n\nASSET CỦA TẬP (chỉ dùng thứ đã có):\n{so}")


class _KyThuat:
    """Đọc KÉT mỗi lượt — Owner đổi khoá/model ở General là ăn ngay."""

    def ky_thuat(self, muc, tai_san):
        from autoedit.treatment.dich import LLM

        return LLM(VIEC_SINH_PROMPT).ky_thuat(muc, tai_san)

    def breakdown(self, voice, y, giay, tai_san):
        from autoedit.treatment.dich import LLM

        ra = LLM(VIEC_SINH_PROMPT).goi(_LENH_BREAKDOWN, _than_breakdown(voice, y, giay, tai_san))
        return list(ra.get("canh") or []) if isinstance(ra, dict) else []

    def bo_tro(self, voice, canh, giay, toi_da, tai_san):
        from autoedit.treatment.dich import LLM

        ra = LLM(VIEC_SINH_PROMPT).goi(_LENH_BO_TRO % (toi_da, giay, len(canh)),
                                       _than_bo_tro(voice, canh, giay, tai_san))
        return list(ra.get("them") or []) if isinstance(ra, dict) else []

    def drama_breakdown(self, than):
        from autoedit.treatment.dich import LLM

        ra = LLM(VIEC_SINH_PROMPT).goi(_LENH_BREAKDOWN_DRAMA, than)
        return ra if isinstance(ra, dict) else {}

    def drama_canh(self, than):
        from autoedit.treatment.dich import LENH_DRAMA_CANH, LLM

        ra = LLM(VIEC_SINH_PROMPT).goi(LENH_DRAMA_CANH, than)
        return ra if isinstance(ra, dict) else {}

    def drama_clip(self, than):
        from autoedit.treatment.dich import LENH_DRAMA_CLIP, LLM

        ra = LLM(VIEC_SINH_PROMPT).goi(LENH_DRAMA_CLIP, than)
        return ra if isinstance(ra, dict) else {}


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

    def sinh_asset_2(self, muc, tong):
        from autoedit.treatment.dich import LLM

        return LLM().sinh_asset_2(muc, tong)


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
