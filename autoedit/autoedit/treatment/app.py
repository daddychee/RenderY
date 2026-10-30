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

import functools
import itertools
import math
import os
import re
import threading
import time
import unicodedata
import zipfile
from pathlib import Path
from fastapi import Body, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, StreamingResponse

from autoedit.treatment import dong as mdong
from autoedit.treatment import drama as mdrama
from autoedit.treatment import tai_san as mtai_san
from autoedit.treatment.kho import DongVuaDoi, Kho, KhoaBiGiu

TRANG = Path(__file__).parent / "static" / "treatment.html"

# Số dòng mỗi lượt gọi LLM. 8 là chỗ đo được: 17-18 dòng/lượt vẫn qua,
# 20 dòng thì JSON cụt (SE001/C6, 23/09). Để rộng gấp đôi mức an toàn.
CO_LO = 8

# Storage (user chốt 29/10): gateway gom TRỌN body không phải SSE vào RAM rồi mới gửi
# (nen/common/proxy.py `aread`) -> một ZIP = một chương, trần 1,5 GB.
TRAN_ZIP = 1_500_000_000
# `tai_video` ghi bằng write_bytes, không atomic: file sửa chưa tới chừng này giây
# coi như đang ghi dở, không cho vào ZIP.
GIAY_GHI = 10


class _Ong:
    """File chỉ-ghi cho zipfile: không seek được thì zipfile tự ghi data descriptor,
    nên ZIP chảy ra từng mẩu mà không cần file tạm."""

    def __init__(self):
        self.b = []

    def write(self, x):
        self.b.append(bytes(x))
        return len(x)

    def flush(self):
        pass

    def lay(self) -> bytes:
        r = b"".join(self.b)
        self.b.clear()
        return r


def _luong_zip(ds: list[tuple[Path, str]]):
    """ZIP_STORED: MP4 đã nén sẵn, nén lại chỉ tốn CPU. Đo 30 video thật 157 MB: 0,87 s,
    RAM 3,2 MB."""
    o = _Ong()
    with zipfile.ZipFile(o, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for p, ten in ds:
            with open(p, "rb") as f, z.open(zipfile.ZipInfo.from_file(p, ten), "w", force_zip64=True) as w:
                while k := f.read(1 << 20):
                    w.write(k)
                    yield o.lay()
    yield o.lay()


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


_gio = time.monotonic       # đồng hồ của bộ nhớ đệm số dư (test thay được)


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
# Mỗi shot một video (user chốt 29/10, spec `docs/SPEC_DONG_NHAT_PHOI_CANH.md`): `sid` mã
# shot bất biến (tên file ảnh/video), `co_mat` người trong khung, `huong` người máy hướng
# tới (rỗng = Python suy), `gi` giây video của shot (rỗng = Python tính).
KHOA_SHOT = {"t", "co", "goc", "cd", "lap", "cau", "sid", "co_mat", "huong", "gi"}
_RE_SID = re.compile(r"s[0-9a-f]{6}")


def _sid_moi(da_co: set) -> str:
    import uuid

    while True:
        s = "s" + uuid.uuid4().hex[:6]
        if s not in da_co:
            return s


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


# Nút "Chạy tới duyệt ảnh" của một chương drama (user chốt 29/10). Ảnh 6 luồng: tài khoản
# Seedvis 16 luồng dùng chung cả team (ảnh + video Grok), chừa phần còn lại cho nút lẻ.
# LLM 2 cảnh một lúc, mỗi cảnh vẫn ≤6 clip song song như nút tay — 12 lượt, bằng hai người
# cùng bấm. Một loại việc hỏng LIỀN `PHANH` lần (hết quota LLM / hết credit) thì dừng loại
# đó: hỏng tiếp chỉ là dội lệnh vào nhà cung cấp.
LUONG_ANH_CHUONG = 6
LUONG_LLM_CHUONG = 2
PHANH = 3
PHUT_LLM_CANH = 3       # đo 29/10 P031: Breakdown 20 s + Viết prompt cảnh 1′54, làm tròn lên


def uoc_shot(t: str) -> int:
    """Số shot ƯỚC của clip chưa Breakdown: số "shot N" khác nhau ở dòng `Hình:` (đo DM002
    29/10: khớp 23/25 clip đã Breakdown); dòng Hình không đánh số thì một shot."""
    hinh = " ".join(d for d in (t or "").splitlines() if d.strip().lower().startswith("hình"))
    return len(set(re.findall(r"shot\s*(\d+)", hinh, re.I))) or 1


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

    # ------------------------------------------------------------ đang chạy
    # User chốt 29/10: "ấn nút generate all hoặc bất kỳ nút nào thì cũng phải có thanh trạng thái
    # ... người dùng dễ đè việc của nhau". Nút gen bấm tay vào sổ `_DANG` suốt request: mọi tab
    # hỏi `/dang-chay` thấy chung; đụng việc đang chạy thì 409 thay vì chạy lần hai (credit hai
    # lần, kết quả sau đè kết quả trước). Trong bộ nhớ như `_VIEC`: restart giết luôn request
    # đang chạy, sổ mất theo là đúng. Khoá chung `_KHOA_VIEC` với Generate All / Gen toàn bộ asset.
    _DANG: dict[int, dict] = {}
    _SO_DANG = itertools.count()
    TEN_VIEC = {"breakdown": "breakdown", "prompt": "viết prompt", "bo_tro": "sinh cú bổ trợ",
                "dich": "dịch", "anh": "vẽ ảnh", "dan": "vẽ ảnh dàn cảnh", "video": "gửi video",
                "mo_ta": "viết mô tả asset", "ref": "vẽ ảnh ref", "goi_y": "đọc kịch bản"}
    # Cùng nhóm = cùng ghi một thứ: breakdown, viết prompt, cú bổ trợ, dịch đều viết lại chữ clip.
    _NHOM = {"breakdown": "chu", "prompt": "chu", "bo_tro": "chu", "dich": "chu", "mo_ta": "asset", "ref": "asset"}

    def _dung_nhau(a: dict, b: dict) -> bool:
        """Cùng tập, cùng nhóm việc, cùng chương, và chỗ này chứa chỗ kia: chương ⊃ cảnh ⊃
        clip ⊃ shot (None / rỗng = cả tầng đó)."""
        return (a["tap"] == b["tap"] and _NHOM.get(a["viec"], a["viec"]) == _NHOM.get(b["viec"], b["viec"])
                and a["ch"] == b["ch"] and (a["i"] is None or b["i"] is None or a["i"] == b["i"])
                and (not a["ma"] or not b["ma"] or a["ma"] == b["ma"])
                and (not a["sid"] or not b["sid"] or a["sid"] == b["sid"]))

    def _cau_dang(o: dict) -> str:
        return f"{o['nguoi']} đang {TEN_VIEC[o['viec']]} ở {o['cho']}"

    def _cho_viec(tap: str, ch: str, i, ma: str, sid: str) -> tuple:
        """(chỉ số cảnh, nhãn chỗ cho người đọc) — clip drama gọi theo mã P, narration theo phân cảnh."""
        if ch and ma:
            _, i, j, c = _tim_canh(tap, ch, ma)
            k = next((k for k, s in enumerate(mdrama.doc_sh(c.get("sh"))) if s.get("sid") == sid), None)
            return i, f"{ch} · " + (c.get("pm") or f"phân cảnh {i + 1} · cảnh {j + 1}") +                 (f" · shot {k + 1}" if sid and k is not None else "")
        if ch and i is not None:
            d = kho.doc(tap, ch)["dong"]
            en = (d[i].get("en") or "") if 0 <= i < len(d) and kho.kieu_tap(tap)["loai"] == "drama" else ""
            return i, f"{ch} · " + (en[:60] or f"phân cảnh {i + 1}")
        if ch:
            return i, f"chương {ch}"
        if ma:
            return i, next((x.get("ten") for x in kho.ds_so(tap) if x["ma"] == ma), "") or ma
        return i, "cả tập"

    def _dang(viec: str):
        """Bọc route nút gen: vào sổ sau cửa gác quyền, rời sổ cả khi hỏng."""
        def boc(ham):
            @functools.wraps(ham)
            def chay(**kw):
                ai, tap, ch, ma, sid = (_ghi_duoc(kw["request"]), kw["tap"], kw.get("chuong", ""),
                                        kw.get("ma", ""), kw.get("sid", ""))
                i, cho = _cho_viec(tap, ch, kw.get("i"), ma, sid)
                moi = {"tap": tap, "viec": viec, "ch": ch, "i": i, "ma": ma, "sid": sid, "cho": cho,
                       "nguoi": ai, "bat_dau": time.time()}
                with _KHOA_VIEC:
                    v = _CHAY.get((tap, ch)) if ch else None
                    if v and v["chay"]:
                        raise HTTPException(409, f"{v['nguoi']} đang Generate All chương {ch} — đợi xong.")
                    if not ch and ma and (_VIEC.get(tap) or {}).get("chay"):
                        raise HTTPException(409, f"{_VIEC[tap]['nguoi']} đang gen toàn bộ asset — đợi xong.")
                    o = next((o for o in _DANG.values() if _dung_nhau(o, moi)), None)
                    if o:
                        raise HTTPException(409, _cau_dang(o) + " — đợi xong rồi bấm lại.")
                    k = next(_SO_DANG)
                    _DANG[k] = moi
                try:
                    return ham(**kw)
                finally:
                    with _KHOA_VIEC:
                        _DANG.pop(k, None)
            return chay
        return boc

    @app.get("/api/tap/{tap}/dang-chay")
    def dang_chay(tap: str):
        """Thanh "Đang chạy" của mọi tab: nút gen tay + Generate All + Gen toàn bộ asset của tập."""
        bay = time.time()

        def tom(v: dict) -> dict:
            return {"nguoi": v["nguoi"], "buoc": v["buoc"], "xong": v["xong"], "tong": v["tong"],
                    "loi": len(v["loi"]), "giay": int(bay - v["bat_dau"])}
        with _KHOA_VIEC:
            viec = [dict({x: o[x] for x in ("viec", "ch", "i", "ma", "sid", "cho", "nguoi")},
                         ten=TEN_VIEC[o["viec"]], giay=int(bay - o["bat_dau"]))
                    for o in _DANG.values() if o["tap"] == tap]
            chuong = [dict(tom(v), ch=ch) for (t, ch), v in _CHAY.items() if t == tap and v["chay"]]
            a = _VIEC.get(tap)
            asset = tom(a) if a and a["chay"] else None
        return {"viec": viec, "chuong": chuong, "asset": asset}

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
        # Trang ghi CẢ sổ bằng bản nó đang cầm: ghi giữa lúc việc nền đang viết
        # mô tả / thêm đồ vật là xoá im lặng phần máy vừa viết.
        if (_VIEC.get(tap) or {}).get("chay"):
            raise HTTPException(409, "Đang gen toàn bộ asset — đợi xong rồi lưu.")
        if _chuong_dang_chay(tap):
            raise HTTPException(409, _chuong_dang_chay(tap) + " — đợi xong rồi lưu.")
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
    @_dang("goi_y")
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

    _KHOA_SO = threading.Lock()     # đọc-vá-ghi sổ của máy (nút Sinh Asset, việc nền) trọn một nhịp

    def _ghi_mo_ta_2(tap: str, ma: str, ra: dict, kieu: dict) -> dict | None:
        """Ghi mô tả LLM vừa viết vào BẢN TRONG KHO (khuôn 2). Nhân vật drama giữ
        cụm kịch bản; prompt ảnh là khuôn câu Python ghép (`tai_san.pr_mau`)."""
        with _KHOA_SO:
            kho_so, muc = kho.ds_so(tap), None
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
        return muc

    @app.post("/api/tap/{tap}/so/{ma}/sinh")
    @_dang("mo_ta")
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
            muc = _ghi_mo_ta_2(tap, ma, ra, kieu) or muc
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
    @_dang("ref")
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

    def _mo_hinh_tai_san(tap: str) -> str:
        """Model vẽ asset: tập chọn (nút Model) > General (gen_canh) > GPT Image 2.
        User báo 28/10: đổi model ở General mà tool vẫn vẽ GPT2 — từng ghi cứng."""
        return ((kho.mo_hinh_tap(tap).get("anh") or "").strip()
                or (getattr(ve_anh, "model_ket", "") or "").strip() or mtai_san.MODEL_ANH)

    def _ref_khuon_2(tap: str, ma: str, muc: dict, model: str | None = None) -> dict:
        """Luật tài sản Padoma bằng GPT Image 2 (user chốt 27/10). Người: cận
        mặt 1:1 -> toàn thân 9:16 SỬA TỪ ảnh cận -> tấm gộp 4:3 (đây mới là ref);
        đồ vật nền trắng 1:1; nơi chốn 16:9 không người. Ảnh vẽ theo MÔ TẢ tiếng
        Anh — chưa có thì chặn, vẽ theo chữ Việt là ra ảnh sai. Bộ đồ phụ: cận mặt
        SỬA TỪ cận mặt của bản gốc (Padoma F2), vẽ từ chữ là mỗi bộ đồ một khuôn mặt.
        Đồ vật có ảnh nhân vật (mô tả gọi tên người đó): gửi kèm cận mặt người đó."""
        loai, chu = muc["loai"], (muc.get("chu") or "").strip()
        if not chu or mdrama.la_tieng_viet(chu):
            raise HTTPException(400, "Asset này chưa có mô tả tiếng Anh — bấm “Sinh Asset” "
                                     "trước, ảnh vẽ theo mô tả đó.")
        pr = (muc.get("pr") or "").strip() or mtai_san.pr_mau(loai, chu)
        try:
            dich = kho.duong_ref(tap, ma, ".png")
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        so = kho.ds_so(tap)
        goc = mtai_san.goc_cua(ma) if loai == "nhan_vat" else ""
        mat_goc = dich.with_name(goc + "__can.png") if goc and any(x["ma"] == goc for x in so) else None
        if mat_goc is not None and not mat_goc.exists():
            raise HTTPException(400, f"Bộ đồ phụ vẽ từ khuôn mặt của {goc} — vẽ {goc} trước.")
        nguoi = mtai_san.nguoi_cua_do(so, chu) if loai == "dao_cu" else []
        mat = [dich.with_name(x["ma"] + "__can.png") for x in nguoi]
        thieu = [x["ten"] for x, p in zip(nguoi, mat) if not p.exists()]
        if thieu:
            raise HTTPException(400, f"Đồ vật có ảnh của {', '.join(thieu)} — vẽ {', '.join(thieu)} trước, "
                                     "không thì máy bịa mặt người khác.")
        m = {"model": model or _mo_hinh_tai_san(tap)}
        try:
            if loai == "nhan_vat":
                can, toan = dich.with_name(ma + "__can.png"), dich.with_name(ma + "__toan.png")
                if mat_goc is not None:
                    ve_anh.gen_anh(mtai_san.PHIEN_BAN + " " + pr, can, ref=[mat_goc], ti_le="1:1", **m)
                else:
                    ve_anh.gen_anh(pr, can, ti_le="1:1", **m)
                ve_anh.gen_anh(mtai_san.toan_than(chu), toan, ref=[can], ti_le="9:16", **m)
                tam = mtai_san.ghep_tam(can, toan, dich.with_name(ma + "__tam.png"))
                kho.xoa_ref(tap, ma)
                tam.replace(dich)
            elif nguoi:
                ve_anh.gen_anh(" ".join([pr] + [mtai_san.ANH_NGUOI.format(i=i, ten=x["ten"])
                                                for i, x in enumerate(nguoi, 1)]),
                               dich, ref=mat, ti_le=mtai_san.TI_LE[loai], **m)
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

    # ------------------------------------------------------ toàn bộ asset
    # Nút "Gen toàn bộ asset" (user chốt 28/10: "làm giống padoma", `bo_anh.gen_thieu`).
    # Chạy nền ở máy chủ: đóng tab không mất việc. Tiến độ chỉ nằm trong bộ nhớ —
    # restart giữa chừng thì bấm lại, asset đã có ảnh được bỏ qua.
    _VIEC: dict[str, dict] = {}
    _CHAY: dict[tuple[str, str], dict] = {}     # (tập, chương) -> việc "Chạy tới duyệt ảnh"
    _KHOA_VIEC = threading.Lock()

    def _chuong_dang_chay(tap: str) -> str:
        """Câu báo nếu một chương của tập đang chạy nền ('' = không). Việc chạy chương ghi
        sổ (giọng, mục trường đoạn) và `ts`/`sh`/`pd` của clip: lưu cả sổ, dán lại kịch
        bản hay gen asset giữa chừng là đè phần máy vừa ghi."""
        with _KHOA_VIEC:
            v = next(((ch, v) for (t, ch), v in _CHAY.items() if t == tap and v["chay"]), None)
        return f"{v[1]['nguoi']} đang Generate All chương {v[0]}" if v else ""   # tên nút (user đổi 29/10)
    _NHO: dict = {}
    _KHOA_NHO = threading.Lock()

    def _nho(khoa: str, ham, tuoi: float):
        """Kết quả hỏi Seedvis nhớ `tuoi` giây, dùng chung mọi tab: trang hỏi mỗi
        phút mà mỗi tab một lượt là dồn lệnh lên Seedvis (hỏi dồn bị 429)."""
        with _KHOA_NHO:
            o = _NHO.get(khoa)
            if o is not None and _gio() - o[0] < tuoi:
                return o[1]
        gt = ham()
        with _KHOA_NHO:
            _NHO[khoa] = (_gio(), gt)
        return gt

    @app.get("/api/so-du")
    def so_du(moi: int = 0):
        """Số dư Seedvis của việc vẽ ảnh và việc dựng video. `moi` = vừa bấm gen:
        hỏi lại nếu số đã cũ hơn 10 giây."""
        def hoi():
            a, vd = getattr(ve_anh, "credit", None), getattr(ve_video, "credit", None)
            return {"anh": a, "video": vd, "chung": bool(getattr(ve_video, "cung_anh", a == vd))}
        return _nho("so_du", hoi, 10 if moi else 60)

    def _model_tat_ca(tap: str) -> tuple[str, str]:
        """(model hiệu lực, model dự phòng khi nó bảo trì)."""
        m = _mo_hinh_tai_san(tap)
        return m, (mtai_san.MODEL_DU_PHONG if m != mtai_san.MODEL_DU_PHONG else mtai_san.MODEL_ANH)

    def _ke_hoach_tap(tap: str) -> dict:
        so = kho.ds_so(tap)
        co_anh = {x["ma"] for x in so if kho.ref_dang_co(tap, x["ma"]) is not None}
        tim = kho.kieu_tap(tap)["loai"] == "drama" and not any(x["loai"] == "dao_cu" for x in so)
        return mtai_san.ke_hoach(so, co_anh, tim, *_model_tat_ca(tap))

    @app.get("/api/tap/{tap}/so/tat-ca")
    def xem_tat_ca(tap: str):
        model, du = _model_tat_ca(tap)
        ds = _nho("ds_model", lambda: getattr(ve_video, "danh_sach", None) or [], 60)
        m = next((x for x in ds if x.get("id") == model), None)
        with _KHOA_VIEC:
            v = _VIEC.get(tap)
            viec = dict(v, loi=list(v["loi"])) if v else None
        return {"ke_hoach": _ke_hoach_tap(tap), "viec": viec,
                "model": {"id": model, "du_phong": du,
                          "bao_tri": bool(ds) and (m is None or (m.get("status") or "active") != "active")}}

    @app.post("/api/tap/{tap}/so/tat-ca")
    def chay_tat_ca(tap: str, request: Request, than: dict = Body(default={})):
        ai = _ghi_duoc(request)
        if ve_anh is None:
            raise HTTPException(503, "Chưa bật bộ vẽ ảnh.")
        if _chuong_dang_chay(tap):
            raise HTTPException(409, _chuong_dang_chay(tap) + " — đợi xong rồi gen asset.")
        if kho.kieu_tap(tap)["khuon"] != "2":
            raise HTTPException(400, "Tập cũ (trước 27/10) vẽ từng asset — nút này đi theo luật "
                                     "tài sản khuôn Padoma.")
        hl, du = _model_tat_ca(tap)
        model = str(than.get("model") or hl).strip()
        if model not in (hl, du):
            raise HTTPException(400, f"Model '{model}' không phải model vẽ asset của tập này "
                                     f"({hl}) hay model dự phòng ({du}).")
        kh = _ke_hoach_tap(tap)
        if not (kh["do_vat"] or kh["mo_ta"] or kh["anh"]):
            raise HTTPException(400, "Mọi asset đã có ảnh — vẽ lại cái nào thì bấm trong thẻ asset đó.")
        with _KHOA_VIEC:
            v = _VIEC.get(tap)
            if v and v["chay"]:
                raise HTTPException(409, f"{v['nguoi']} đang chạy Gen toàn bộ asset cho tập này — đợi xong.")
            o = next((o for o in _DANG.values() if o["tap"] == tap and not o["ch"] and o["ma"]), None)
            if o:
                raise HTTPException(409, _cau_dang(o) + " — đợi xong rồi gen toàn bộ asset.")
            _VIEC[tap] = {"chay": True, "buoc": "do_vat" if kh["do_vat"] else "mo_ta", "xong": 0,
                          "tong": 0, "loi": [], "do_vat_moi": 0, "model": model, "nguoi": ai,
                          "bat_dau": time.time(), "het": None}
        threading.Thread(target=_chay_tat_ca, args=(tap, ai, model, kh["do_vat"]), daemon=True).start()
        return {"ok": True}

    def _loi_viec(tap: str, ma: str, ten: str, loi) -> None:
        with _KHOA_VIEC:
            _VIEC[tap]["loi"].append({"ma": ma, "ten": ten, "loi": str(loi)[:300]})

    def _chay_tat_ca(tap: str, ai: str, model: str, tim_do_vat: bool) -> None:
        """Đồ vật -> mô tả còn thiếu -> vẽ. Một asset hỏng không giết cả bộ."""
        from concurrent.futures import ThreadPoolExecutor

        v = _VIEC[tap]
        try:
            if tim_do_vat:
                try:
                    v["do_vat_moi"] = _tim_do_vat(tap, ai)
                except Exception as exc:  # noqa: BLE001 — thiếu đồ vật vẫn vẽ phần còn lại
                    _loi_viec(tap, "", "Tìm đồ vật", getattr(exc, "detail", exc))
            v["buoc"] = "mo_ta"
            kieu, so = kho.kieu_tap(tap), _so_day_du(tap)
            can = [x for x in so if x["loai"] in mtai_san.TI_LE and mtai_san.thieu_mo_ta(x)
                   and (x.get("yc") or "").strip()]

            def viet(x):
                try:
                    _ghi_mo_ta_2(tap, x["ma"], sinh_asset.sinh_asset_2(x, _tong_chu(so, "")), kieu)
                except Exception as exc:  # noqa: BLE001
                    _loi_viec(tap, x["ma"], x.get("ten", ""), f"Viết mô tả hỏng: {exc}")

            if can and hasattr(sinh_asset, "sinh_asset_2"):
                with ThreadPoolExecutor(max_workers=min(len(can), mtai_san.LUONG)) as ex:
                    list(ex.map(viet, can))
            v["buoc"] = "ve"
            so = kho.ds_so(tap)
            ma_so = {x["ma"] for x in so}
            ve = [x for x in so if x["loai"] in mtai_san.TI_LE and kho.ref_dang_co(tap, x["ma"]) is None]
            with _KHOA_VIEC:
                v["tong"] = len(ve)

            def ve_1(x):
                try:
                    _ref_khuon_2(tap, x["ma"], x, model)
                except HTTPException as exc:
                    _loi_viec(tap, x["ma"], x.get("ten", ""), exc.detail)
                except Exception as exc:  # noqa: BLE001
                    _loi_viec(tap, x["ma"], x.get("ten", ""), exc)
                finally:
                    with _KHOA_VIEC:
                        v["xong"] += 1

            phu = [x for x in ve if x["loai"] == "nhan_vat" and mtai_san.goc_cua(x["ma"]) in ma_so]
            anh_nguoi = [x for x in ve if x["loai"] == "dao_cu" and mtai_san.nguoi_cua_do(so, x.get("chu") or "")]
            # Bản gốc trước: bộ đồ phụ sửa từ ảnh cận của bản gốc; đồ vật có ảnh người cần mặt người đó.
            for dot in ([x for x in ve if x not in phu and x not in anh_nguoi], phu, anh_nguoi):
                if dot:
                    with ThreadPoolExecutor(max_workers=min(len(dot), mtai_san.LUONG)) as ex:
                        list(ex.map(ve_1, dot))
        except Exception as exc:  # noqa: BLE001
            _loi_viec(tap, "", "Gen toàn bộ asset", exc)
        finally:
            with _KHOA_VIEC:
                v.update(chay=False, buoc="xong", het=time.time())

    def _tim_do_vat(tap: str, ai: str) -> int:
        """Đồ vật cần ảnh riêng (luật bảng tài sản Padoma): LLM mỗi chương một lượt,
        song song; Python gộp trùng tên, bỏ mã clip lạ và mô tả chữ Việt; một lượt LLM
        rà cả tập gộp cùng một đồ vật mang tên khác nhau giữa các chương (DM002 29/10:
        "Bàn cờ" / "Bàn cờ gỗ"); rồi đánh mã `doNN`, gán vào `ts` các clip thấy rõ đồ
        vật (tối đa ảnh Grok nhận)."""
        from concurrent.futures import ThreadPoolExecutor

        if ky_thuat is None or not hasattr(ky_thuat, "tim_do_vat"):
            return 0
        chuong, noi, chu_clip = [], {}, {}
        for ch in kho.ds_chuong(tap):
            cs = [(dg, c) for dg in kho.doc(tap, ch["ma"])["dong"] for c in mdong.doc_canh(dg)
                  if c.get("pm") and c.get("id")]
            noi.update({c["pm"]: (ch["ma"], c["id"]) for _, c in cs})
            chu_clip.update({c["pm"]: c.get("t") or "" for _, c in cs})
            if cs:
                chuong.append(cs)
        if not chuong:
            return 0
        # Đồ vật có ảnh người phải gọi đúng tên nhân vật (user báo 29/10: báo đăng ảnh Nia ra người khác).
        ten_nv = mtai_san.ten_nhan_vat(kho.ds_so(tap))
        dau = f"NHÂN VẬT CỦA PHIM: {', '.join(ten_nv) or '(chưa có)'}\n\n"

        def hoi(cs):
            return ky_thuat.tim_do_vat(dau + "\n\n".join(f"{c['pm']} · {dg.get('en', '')}\n{c.get('t', '')}"
                                                         for dg, c in cs)) or {}

        with ThreadPoolExecutor(max_workers=min(len(chuong), 4)) as ex:
            ra = list(ex.map(hoi, chuong))
        gop: dict[str, dict] = {}
        for r in ra:
            for x in (r.get("do_vat") or []) if isinstance(r, dict) else []:
                if not isinstance(x, dict):
                    continue
                ten, chu = str(x.get("ten") or "").strip(), str(x.get("chu") or "").strip()
                clip = [p for p in (x.get("clip") or []) if isinstance(p, str) and p in noi]
                if not ten or not chu or mdrama.la_tieng_viet(chu) or not clip:
                    continue
                g = gop.setdefault(ten.lower(), {"ten": ten, "chu": chu, "clip": []})
                g["clip"] += [p for p in clip if p not in g["clip"]]
        ds = list(gop.values())
        if ds and hasattr(ky_thuat, "ra_do_vat"):
            try:
                nhom, sua = mtai_san.ap_ra(len(ds), _hoi_ra(_than_ra(ten_nv, ds, chu_clip)))
            except Exception as exc:  # noqa: BLE001 — rà hỏng thì giữ danh sách chưa gộp
                _loi_viec(tap, "", "Gộp đồ vật trùng", getattr(exc, "detail", exc))
                nhom, sua = [], {}
            for i, chu in sua.items():
                ds[i]["chu"] = chu
            for g in nhom:
                ds[g[0]]["clip"] = list(dict.fromkeys(p for j in g for p in ds[j]["clip"]))
            bo = {j for g in nhom for j in g[1:]}
            ds = [x for i, x in enumerate(ds) if i not in bo]
        moi: dict[str, dict] = {}
        with _KHOA_SO:
            so = kho.ds_so(tap)
            co, k = {x["ma"] for x in so}, 0
            for g in ds:
                k += 1
                while f"do{k:02d}" in co:
                    k += 1
                ma = f"do{k:02d}"
                co.add(ma)
                moi[ma] = g
                so.append({"ma": ma, "loai": "dao_cu", "ten": g["ten"], "chu": g["chu"],
                           "pr": mtai_san.pr_mau("dao_cu", g["chu"]), "yc": g["ten"], "tb": ""})
            if moi:
                kho.luu_so(tap, so)
        for ma, g in moi.items():
            for pm in g["clip"]:
                def them(c, ma=ma):
                    ts = list(c.get("ts") or [])
                    if ma not in ts and len(ts) < mdrama.ANH_TOI_DA:
                        c["ts"] = ts + [ma]
                _va_canh(tap, noi[pm][0], noi[pm][1], them, ai)
        return len(moi)

    def _hoi_ra(than: str) -> dict:
        """Lượt rà đồ vật cả tập, hỏng thì hỏi lại MỘT lần: đo DM002 29/10 lượt này mất
        121–126 giây, hai lần trong bốn quá giới hạn 180 giây của cổng LLM."""
        try:
            return ky_thuat.ra_do_vat(than)
        except Exception:  # noqa: BLE001
            return ky_thuat.ra_do_vat(than)

    @app.post("/api/tap/{tap}/so/ra-do-vat")
    def ra_do_vat(tap: str, request: Request):
        """Rà đồ vật của tập ĐÃ tìm trước bản gộp (DM002 29/10): gộp mục trùng — clip chuyển
        sang mục giữ, mục bỏ mất cả ảnh — và gọi tên người trong ảnh trên đồ vật. Mô tả đổi
        thì xoá ảnh cũ (vẽ sai người) để Gen toàn bộ asset vẽ lại."""
        ai = _ghi_duoc(request)
        if ky_thuat is None or not hasattr(ky_thuat, "ra_do_vat"):
            raise HTTPException(503, "Chưa bật LLM rà đồ vật.")
        if (_VIEC.get(tap) or {}).get("chay"):
            raise HTTPException(409, "Đang gen toàn bộ asset — đợi xong rồi rà.")
        if _chuong_dang_chay(tap):
            raise HTTPException(409, _chuong_dang_chay(tap) + " — đợi xong rồi rà.")
        so = kho.ds_so(tap)
        do = [x for x in so if x["loai"] == "dao_cu"]
        if not do:
            raise HTTPException(400, "Tập này chưa có đồ vật.")
        clip, chu_clip = {}, {}
        for ch in kho.ds_chuong(tap):
            for dg in kho.doc(tap, ch["ma"])["dong"]:
                for c in mdong.doc_canh(dg):
                    if c.get("pm") and c.get("id"):
                        clip[c["pm"]] = (ch["ma"], c["id"], c.get("ts") or [])
                        chu_clip[c["pm"]] = c.get("t") or ""
        ds = [{"ten": x["ten"], "chu": x.get("chu") or "", "clip": [p for p, v in clip.items() if x["ma"] in v[2]]}
              for x in do]
        try:
            nhom, sua = mtai_san.ap_ra(len(do), _hoi_ra(_than_ra(mtai_san.ten_nhan_vat(so), ds, chu_clip)))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Rà đồ vật hỏng: {exc}") from exc
        doi = {do[j]["ma"]: do[g[0]]["ma"] for g in nhom for j in g[1:]}
        sua_ma = {do[i]["ma"]: chu for i, chu in sua.items() if do[i]["ma"] not in doi}
        with _KHOA_SO:
            kho.luu_so(tap, [dict(x, chu=sua_ma[x["ma"]], pr=mtai_san.pr_mau("dao_cu", sua_ma[x["ma"]]))
                             if x["ma"] in sua_ma else x for x in kho.ds_so(tap) if x["ma"] not in doi])
        for m in [*doi, *sua_ma]:
            kho.xoa_ref(tap, m)
        for ch, cid, ts in clip.values():
            if any(m in doi for m in ts):
                def doi_ts(c):
                    c["ts"] = list(dict.fromkeys(doi.get(m, m) for m in (c.get("ts") or [])))
                _va_canh(tap, ch, cid, doi_ts, ai)
        return {"ok": True, "gop": [[do[i]["ma"] for i in g] for g in nhom], "sua": sorted(sua_ma),
                "xoa": sorted(doi)}

    # ------------------------------------------------------------ drama
    @app.post("/api/tap/{tap}/drama")
    def dan_drama(tap: str, request: Request, than: dict = Body(...)):
        """Dán CẢ `kich-ban.md` (skill /bien-kich-grok, khuôn Padoma) vào tập
        drama. Kịch bản lỗi khuôn thì KHÔNG ghi gì (giao ước với skill). Dán lại
        khớp clip theo mã P: giữ ảnh/video, độ dài đã chọn, prompt sửa tay."""
        ai = _ghi_duoc(request)
        if kho.kieu_tap(tap)["loai"] != "drama":
            raise HTTPException(400, "Tập này không phải tập drama — tạo tập mới loại Drama thoại.")
        if _chuong_dang_chay(tap):
            raise HTTPException(409, _chuong_dang_chay(tap) + " — đợi xong rồi dán lại.")
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

    # ------------------------------------------ Storage: tải video một lượt (29/10)
    # Liệt kê THEO KỊCH BẢN (chương -> dòng -> clip -> shot = thứ tự dựng), không quét
    # thư mục: file mồ côi (shot đã Breakdown lại) không lọt lên timeline. Tên file tự
    # xếp đúng thứ tự: mã P tăng theo thứ tự dựng (DM002 đo 348/348). Khai TRƯỚC
    # `/{tap}/{chuong}` — cùng bẫy với `/txt`.
    def _ds_video(tap: str) -> list[dict]:
        ra, truoc, gio = [], 0, time.time()
        for cg in kho.ds_chuong(tap):
            ch, dong = cg["ma"], kho.doc(tap, cg["ma"])["dong"]
            for i, dg in enumerate(dong):
                for j, c in enumerate(mdong.doc_canh(dg) if isinstance(dg, dict) else []):
                    ma, pm = c.get("id") or "", c.get("pm") or ""
                    if not ma:
                        continue
                    # (mã file video, sid, tên, loại, đang gen lại, mã ảnh của thẻ, giây). Clip kiểu
                    # cũ không có ảnh riêng của video — ảnh clip là ảnh tham chiếu, thẻ giữ chỗ.
                    if not pm:          # narration: phân cảnh đánh số LIỀN H -> E như trang
                        muc = [(ma, "", f"{ch}_PC{truoc + i + 1:03d}-{j + 1}", "canh", c.get("vid"), ma, 0)]
                    else:
                        dau, ss, lt, g = f"{ch}_{pm}", _ss(c), mdrama.loi_thoai(c.get("t")), _giay_clip(tap, c)
                        muc = [(ma, "", f"{dau}_clip_{g}s", "clip", c.get("vid"), "", g)]
                        for k, s in enumerate(mdrama.doc_sh(c.get("sh")), 1):
                            sid, g = s.get("sid") or "", mdrama.giay_shot(s, lt)
                            if sid:
                                ten = "_".join(x for x in (f"{dau}_s{k}", (s.get("co") or "").upper(), f"{g}s") if x)
                                muc.append((f"{ma}-{sid}", sid, ten, "shot", (ss.get(sid) or {}).get("vid"),
                                            f"{ma}-{sid}", g))
                    for m, sid, ten, loai, dang, ma_anh, g in muc:
                        try:
                            p = kho.duong_video(tap, m)
                            a = kho.duong_anh(tap, ma_anh) if ma_anh else None
                        except ValueError:
                            continue
                        if p.exists():
                            st = p.stat()
                            # `co` do LLM đặt, mã P chép từ kịch bản: lọc ký tự cho tên file + onclick
                            ten = re.sub(r"[^A-Za-z0-9_-]", "", ten) + ".mp4"
                            # `khoa` = mã tích chọn; `anh` = tem ảnh của thẻ (0 = giữ chỗ), trang
                            # ghép thẳng URL ảnh nhỏ — không gọi thêm request mỗi thẻ.
                            ra.append({"ch": ch, "ma": ma, "sid": sid, "khoa": m, "ten": ten, "loai": loai,
                                       "byte": st.st_size, "t": st.st_mtime, "dang": bool(dang), "giay": g,
                                       "anh": int(a.stat().st_mtime) if a and a.exists() else 0,
                                       "ghi": st.st_mtime > gio - GIAY_GHI, "p": p})
            truoc += len(dong)
        return ra

    @app.get("/api/tap/{tap}/kho-video")
    def kho_video(tap: str):
        """`moc` = mốc cho lần "chỉ video mới" sau. Lùi GIAY_GHI: file lần này bị bỏ vì
        đang ghi dở thì lần sau vẫn tính là mới."""
        return {"moc": time.time() - GIAY_GHI,
                "ds": [{k: v for k, v in x.items() if k != "p"} for x in _ds_video(tap)]}

    @app.get("/api/tap/{tap}/kho-video.zip")
    def kho_video_zip(tap: str, ch: str = "", loai: str = "", sau: float = 0, chon: str = ""):
        """ZIP MỘT chương, hoặc các mục ĐÃ TÍCH (`chon` = khoá cách dấu phẩy, được khác chương; GET
        vì POST qua gateway vướng CSRF). Chỉ nhận khoá có trong kịch bản — khoá lạ bỏ qua. Chảy
        luồng, không file tạm. Video đang gen lại vẫn vào (user chốt)."""
        if not ch and not chon:
            raise HTTPException(400, "Thiếu chương hoặc danh sách mục đã chọn.")
        k = set(chon.split(",")) if chon else None
        ds = [x for x in _ds_video(tap) if not x["ghi"] and (
              x["khoa"] in k if k is not None
              else x["ch"] == ch and (not loai or x["loai"] == loai) and x["t"] > sau)]
        noi = "Các mục đã chọn" if k is not None else f"Chương {ch}"
        if not ds:
            raise HTTPException(404, f"{noi} không có video nào khớp lọc.")
        tong = sum(x["byte"] for x in ds)
        if tong > TRAN_ZIP:
            gb = lambda n: f"{n / 1e9:.1f}".replace(".", ",")  # noqa: E731
            raise HTTPException(413, f"{noi} có {gb(tong)} GB video, quá trần {gb(TRAN_ZIP)} GB một lần tải — "
                                     + ("bỏ bớt mục đã chọn." if k is not None
                                        else "lọc theo loại hoặc chọn 'chỉ video mới'."))
        ten = (f"{tap}_chon_{len(ds)}" if k is not None else f"{tap}_{ch}{'_moi' if sau else ''}") + \
            f"_{time.strftime('%d%m-%H%M')}.zip"
        return StreamingResponse(_luong_zip([(x["p"], x["ten"]) for x in ds]), media_type="application/zip",
                                 headers={"Content-Disposition": f'attachment; filename="{ten}"',
                                          "Cache-Control": "no-store"})

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
                    # Thẻ Storyboard: tem file từng shot MỘT lượt cùng chương (DM002: 348 clip)
                    c["fs"] = {s["sid"]: _tem_shot(tap, f"{ma}-{s['sid']}") for s in sh if s.get("sid")}
        return ra

    def _tem_shot(tap: str, ten: str) -> list[int]:
        """[giờ sửa ảnh, giờ sửa video] tính bằng giây — vừa là cờ vừa là mã chống cache; 0 = chưa có.
        Mã hỏng không được làm sập cả GET chương."""
        ra = []
        for duong in (kho.duong_anh, kho.duong_video):
            try:
                ra.append(int(duong(tap, ten).stat().st_mtime))
            except (OSError, ValueError):
                ra.append(0)
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
    @_dang("dich")
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

    def _than_drama(dg: dict, cs: list[dict], tra: dict, truoc: dict | None = None) -> tuple[str, list[str]]:
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
        dong += [f"CẦN CÂU GIỌNG: {', '.join(can) or '(không)'}"] + _khoi_truoc(truoc) + ["", "CLIP:"]
        for c in cs:
            dong += _khoi_clip(c, tra)
        return "\n".join(dong), can

    def _khoi_truoc(tr: dict | None) -> list[str]:
        """Bố cục đã chốt của cảnh liền trước cùng phim trường — người còn ở cảnh này giữ nguyên."""
        c = (tr or {}).get("chung") or {}
        if not (c.get("dan") or "").strip():
            return []
        dong = ["", f"CẢNH TRƯỚC CÙNG NƠI (cùng phim trường, cùng buổi): {tr['en']}",
                f"- hang (trái → phải): {', '.join(c.get('hang') or [])}"]
        dong += [f"- {n}: ben={mdrama._cua(c.get('ben'), n) or '?'} · vi_tri: {mdrama._cua(c.get('vi_tri'), n)} · "
                 f"phong: {mdrama._cua(c.get('phong'), n)}" for n in tr["ten"]]
        return dong + [f"- cho: {c.get('cho') or ''}", f"- dan: {c.get('dan') or ''}", f"- look: {c.get('look') or ''}"]

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

    def _phan_chung(tap: str, dg: dict, cs: list[dict], tra: dict, truoc: dict | None = None) -> dict:
        """Lượt PHẦN CHUNG của cảnh (ánh sáng, trục, nền — khuôn Padoma: giống
        nhau giữa các clip, lệch là lộ khi dựng) + câu giọng người còn thiếu."""
        if truoc is not None and not (truoc["chung"].get("dan") or "").strip():
            raise HTTPException(400, f"Cảnh này cùng phim trường với {truoc['en']} — viết prompt cảnh đó trước: "
                                     "người có mặt từ trước giữ nguyên chỗ theo cảnh đó.")
        than, can = _than_drama(dg, cs, tra, truoc)
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
            with _KHOA_SO:      # ghi CẢ sổ: chạy chương viết nhiều cảnh cùng lúc
                so = kho.ds_so(tap)
                for x in so:
                    t = x["ten"].split(" · ")[0]
                    if x["loai"] == "nhan_vat" and t in moi and (
                            not (x.get("tieng") or "").strip() or mdrama.la_tieng_viet(x["tieng"])):
                        x["tieng"] = moi[t]
                kho.luu_so(tap, so)
        # Bố cục ảnh dàn cảnh (29/10, user chốt "LLM tự đánh dấu"): ai trái/phải, phông sau
        # lưng từng người, câu chỗ ngồi, câu tả ảnh dàn cảnh — Python ghép prompt từng shot.
        ben = chung.get("ben")

        def chu(khoa):          # {Tên: câu tiếng Anh}: phông sau lưng / chỗ ngồi riêng từng người
            x = chung.get(khoa)
            return {str(k): str(v).strip() for k, v in (x.items() if isinstance(x, dict) else []) if str(v).strip()}
        ra = dict({k: str(chung.get(k) or "") for k in ("look", "truc", "nen", "cho", "dan")},
                  ben={str(k): str(v) for k, v in (ben.items() if isinstance(ben, dict) else [])
                       if str(v) in mdrama.BEN},
                  phong=chu("phong"), vi_tri=chu("vi_tri"),
                  hang=[x.strip() for x in (chung.get("hang") if isinstance(chung.get("hang"), list) else [])
                        if isinstance(x, str) and x.strip()])
        # Khung người dựng kéo là của ẢNH dàn cảnh, không của chữ: viết lại chữ thì giữ (người
        # còn trong cảnh) — 29/10 bấm "Viết prompt cảnh" lại là mất không báo. Vẽ lại ảnh mới bỏ.
        nv = _nguoi_canh(tra, cs)
        if truoc is not None:       # người có mặt từ cảnh trước: Python ép đúng chỗ cũ, không tin LLM
            ra = mdrama.giu_cho_cu(ra, truoc["chung"], [n for n in nv if n in truoc["ten"]])
        cat = {n: h for n, h in ((_chung_cu(cs) or {}).get("cat") or {}).items() if n in nv}
        return dict(ra, cat=cat) if cat else ra

    def _chung_cu(cs: list[dict]) -> dict | None:
        """Phần chung đã viết của cảnh (clip nào cũng mang một bản) — viết lại một clip
        dùng lại y nguyên, kể cả khung cắt người dựng đã kéo."""
        cu = [x for x in (mdrama.doc_pd(y.get("pd")) for y in cs) if x.get("truc_canh")]
        if not cu:
            return None
        return dict({k: cu[0][k] for k in ("ben", "hang", "phong", "vi_tri", "cho", "dan", "cat") if k in cu[0]},
                    look=str(cu[0].get("look") or ""), truc=cu[0]["truc_canh"], nen=str(cu[0].get("nen") or ""))

    def _viet_clip(tap: str, chuong: str, dg: dict, cs: list[dict], chon: list[dict], tra: dict,
                   chung: dict, ai: str) -> dict:
        """Mỗi clip một lượt LLM, chạy SONG SONG (kiểm thử 28/10: một lượt cả cảnh
        5 clip quá 180 s 2/2 lần); phần chung giữ y nguyên ở mọi clip. LLM chỉ viết
        chữ cho các shot ĐÃ CHỐT. Clip nào lệch số shot thì KHÔNG lưu clip đó, báo
        rõ; clip đúng vẫn lưu. Câu vị trí / câu khung nhắc người NGOÀI KHUNG (Grok
        có thể vẽ thêm người đó) thì lưu và NHẮC soát ảnh (luật cứng 5) — user 30/10:
        chặn làm P137/P171/P191 (màn hình điện thoại hiện tên người gọi) và P252 (ảnh
        chụp Nia trên báo) không Create Prompt được."""
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
        viet, loi, nhac = 0, [], []
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
            sai = mdrama.kiem_pd(pd_ghep(pd, [dict(s, lap=l) for s, l in zip(sh, lap)]), c.get("t"))
            if sai:
                loi += [f"{c['pm']}: {s}" for s in sai]
                continue
            # `lap` tả phông thì NHẮC (luật cứng 5), không chặn: phông lấy từ ảnh dàn cảnh.
            nhac += [f"{c['pm']} shot {k}: {n}" for k, l in enumerate(lap, 1) for n in mdrama.nhac_lap(l)]
            nhac += [f"{c['pm']}: câu vị trí nhắc {n}, người không có trong khung — soát ảnh, Grok có thể vẽ thêm {n}"
                     for n in mdrama.nhac_ten(pd["truc"], ngoai)]
            nhac += [f"{c['pm']} shot {k}: câu khung nhắc {n}, người không có trong khung — soát ảnh, Grok có thể "
                     f"vẽ thêm {n}" for k, l in enumerate(lap, 1) for n in mdrama.nhac_ten(l, ngoai)]
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
        return {"ok": True, "viet": viet, "loi": loi, "nhac": nhac}

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
            # `co_mat` chỉ nhận người có tấm trong clip — tên lạ là LLM bịa người.
            nv = [tra[m]["ten"].split(" · ")[0] for m in (c.get("ts") or [])
                  if m in tra and tra[m]["loai"] == "nhan_vat"]
            for s in (s for s in (x.get("shots") or []) if isinstance(s, dict)):
                co, goc, cd = (str(s.get(k) or "").strip() for k in ("co", "goc", "cd"))
                ll = s.get("co_mat") if isinstance(s.get("co_mat"), list) else []
                cm = [n for n in nv if n in [y.strip() for y in ll if isinstance(y, str)]]
                sh.append({"t": str(s.get("t") or "").strip(), "co": co.upper() if co.upper() in CO_CHU else "MS",
                           "goc": goc if goc in GOC_CHU else "eye", "cd": cd if cd in CD_DRAMA else "",
                           "lap": "", "cau": s.get("cau"), "sid": _sid_moi({y.get("sid") for y in sh}),
                           "co_mat": cm or (nv if len(nv) == 1 else [])})
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
                y.pop("ss", None)       # shot mới mã mới: dấu duyệt/task của shot cũ hết nghĩa
            _va_canh(tap, chuong, c["id"], va, ai)
            so += 1
        return {"ok": True, "so_clip": so, "loi": loi}

    def _than_bd(dg: dict, cs: list[dict], c: dict, tra: dict) -> str:
        return "\n".join([f"CẢNH: {dg.get('en', '')}", dg.get("vi", ""), _noi_chon(cs, tra), ""]
                         + _khoi_clip(c, tra))

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/breakdown")
    @_dang("breakdown")
    def breakdown_clip(tap: str, chuong: str, ma: str, request: Request):
        """Breakdown lại MỘT clip drama — clip khác giữ shot, prompt, video."""
        ai = _ghi_duoc(request)
        _, i, _, c = _tim_canh(tap, chuong, ma)
        if not c.get("pm"):
            raise HTTPException(400, "Đây không phải clip drama.")
        dg, cs, tra = _canh_drama(tap, chuong, i, "drama_breakdown")
        return _breakdown_clip(tap, chuong, dg, cs, [c], tra, ai)

    @app.post("/api/tap/{tap}/{chuong}/dong/{i}/prompt-drama")
    @_dang("prompt")
    def prompt_drama(tap: str, chuong: str, i: int, request: Request):
        """Viết prompt MỌI clip ĐÃ BREAKDOWN của một cảnh drama: phần chung một
        lượt, rồi mỗi clip một lượt song song. Không clip nào có shot thì không gọi LLM."""
        ai = _ghi_duoc(request)
        dg, cs, tra = _canh_drama(tap, chuong, i)
        co, loi = _co_shot(cs)
        if not co:
            return {"ok": True, "viet": 0, "loi": loi}
        r = _viet_clip(tap, chuong, dg, cs, co, tra, _phan_chung(tap, dg, cs, tra, _truoc(tap, chuong, i)), ai)
        return dict(r, loi=loi + r["loi"])

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/prompt-drama")
    @_dang("prompt")
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
        chung = _chung_cu(cs) or _phan_chung(tap, dg, cs, tra, _truoc(tap, chuong, i))
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
        # `co_mat` chỉ vào dấu khi CÓ: shot trước 29/10 không có, dấu cũ không đổi oan.
        return _bam(c.get("t"), c.get("ts"), [(s.get("t"), s.get("co"), s.get("goc"), s.get("cau"))
                                              + ((s["co_mat"],) if s.get("co_mat") else ())
                                              for s in mdrama.doc_sh(c.get("sh"))])

    def _dau_video(tap: str, c: dict) -> str:
        if c.get("pm"):
            # Clip drama không có ảnh cảnh: dấu là prompt + GIỜ SỬA các tấm tham chiếu
            # (vẽ lại tấm là video cũ) + chữ clip (đổi Hình mà prompt chưa viết lại).
            return _bam(_prompt_video(tap, c), [(t.name, _mtime(t)) for t in _ref_ve(tap, dict(c, td=""))],
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
    @_dang("prompt")
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
    @_dang("breakdown")
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
    @_dang("bo_tro")
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
    @_dang("anh")
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
            if not all(isinstance(s.get(x, ""), str) for x in ("t", "lap", "huong", "gi")):
                return f"shot {k}: `t`/`lap`/`huong`/`gi` phải là chữ."
            if s.get("sid") and not (isinstance(s["sid"], str) and _RE_SID.fullmatch(s["sid"])):
                return f"shot {k}: `sid` sai dạng."
            cm = s.get("co_mat", [])
            if not (isinstance(cm, list) and all(isinstance(x, str) for x in cm)):
                return f"shot {k}: `co_mat` phải là danh sách tên."
            if s.get("gi") and s["gi"] not in map(str, mdrama.GIAY_CHON):
                return f"shot {k}: độ dài {s['gi']} giây không có — chỉ {'/'.join(map(str, mdrama.GIAY_CHON))}."
        sid = [s["sid"] for s in sh if s.get("sid")]
        if len(sid) != len(set(sid)):
            return "hai shot trùng `sid`."
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
                if k == "sh" and gt:
                    gt = _dat_sid(gt)
                if gt:
                    c[k] = gt
                else:
                    c.pop(k, None)

        c = _va_canh(tap, chuong, ma, va, ai)
        return {"ok": True, "v": c.get("v", "")}

    def _dat_sid(chu: str) -> str:
        """Shot chưa có `sid` (tab cũ, shot thêm tay) nhận mã mới; mã đã có giữ nguyên —
        ảnh/video của shot neo vào mã này."""
        import json as _json

        sh = _json.loads(chu)
        co = {s.get("sid") for s in sh if s.get("sid")}
        for s in sh:
            if not s.get("sid"):
                s["sid"] = _sid_moi(co)
                co.add(s["sid"])
        return _json.dumps(sh, ensure_ascii=False)

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
    @_dang("video")
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
        if (c.get("vid") or "").strip():      # tab cũ chưa thấy mã task: gửi nữa là trả tiền lần hai
            raise HTTPException(409, "Cảnh này đang dựng video — đợi xong rồi gửi lại.")
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
        # Prompt đánh số ảnh theo `ts`: ảnh dàn cảnh (`td`, luồng mỗi shot 29/10) không đi đường này.
        ref = _ref_ve(tap, dict(c, td=""))
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

    # ------------------------------------- drama: ảnh dàn cảnh + mỗi shot một video
    # User chốt 29/10 (spec `docs/SPEC_DONG_NHAT_PHOI_CANH.md`): mỗi shot một video Grok
    # i2v từ ảnh khung đầu ĐÃ DUYỆT; ảnh khung đầu vẽ từ MẢNH CẮT ảnh dàn cảnh quanh người
    # máy hướng tới, mọi máy cùng phía (luật 180°). Đo DM001 P031: phông sau lưng 3/3, hướng
    # nhìn 3/3 — gửi nguyên ảnh dàn cảnh thì 0/3 và 1/3, vẽ phòng nhìn ngược thì user bác.
    # Ảnh dàn cảnh = ref của mục trường đoạn (`td`), một tấm cho cả dòng (cảnh drama).

    def _nguoi_canh(tra: dict, cs: list[dict]) -> dict:
        """Tên -> mục sổ nhân vật có tấm trong các clip, theo thứ tự `ts`."""
        ra: dict = {}
        for c in cs:
            for m in c.get("ts") or []:
                if m in tra and tra[m]["loai"] == "nhan_vat":
                    ra.setdefault(tra[m]["ten"].split(" · ")[0], tra[m])
        return ra

    def _dong_drama(tap: str, chuong: str, i: int) -> tuple[dict, list[dict], dict]:
        d = kho.doc(tap, chuong)["dong"]
        if not 0 <= i < len(d):
            raise HTTPException(404, "Không có cảnh này.")
        cs = [c for c in mdong.doc_canh(d[i]) if c.get("pm") and c.get("id")]
        if not cs:
            raise HTTPException(400, "Dòng này không có clip drama nào.")
        return d[i], cs, {x["ma"]: x for x in kho.ds_so(tap)}

    def _td_cua(cs: list[dict], tra: dict) -> str:
        """Trường đoạn của cảnh: clip đầu đã xếp thì theo đó, chưa thì mã sẽ tạo lúc vẽ."""
        td = (cs[0].get("td") or "").strip()
        return td if td in tra and tra[td]["loai"] == "truong_doan" else "td_" + cs[0]["id"]

    def _buoi(dg: dict) -> str:
        """Buổi trong tiêu đề cảnh "C001 · nơi · trưa · N01" ('' khi không đọc được)."""
        p = [x.strip() for x in str(dg.get("en") or "").split(" · ")]
        return p[2].lower() if len(p) >= 4 else ""

    def _truoc(tap: str, chuong: str, i: int) -> dict | None:
        """Cảnh LIỀN TRƯỚC cùng phim trường: cùng nơi chốn, cùng buổi (user chốt 29/10: "nếu có
        người xuất hiện trong một cuộc trò chuyện có sẵn thì vị trí của những người xuất hiện
        trước phải được đảm bảo"). None = đầu cụm, vẽ như cảnh mới."""
        d = kho.doc(tap, chuong)["dong"]
        if not 0 < i < len(d):
            return None
        tra = {x["ma"]: x for x in kho.ds_so(tap)}
        a, b = ([c for c in mdong.doc_canh(d[k]) if c.get("pm") and c.get("id")] for k in (i - 1, i))

        def noi(cs):
            return next((m for c in cs for m in (c.get("ts") or []) if m in tra and tra[m]["loai"] == "boi_canh"), None)
        if not a or not b or noi(a) is None or noi(a) != noi(b) or _buoi(d[i - 1]) != _buoi(d[i]):
            return None
        return {"i": i - 1, "en": d[i - 1].get("en") or f"cảnh {i}", "td": _td_cua(a, tra),
                "chung": _chung_cu(a) or {}, "ten": list(_nguoi_canh(tra, a))}

    def _goc_dan(tap: str, tr: dict | None) -> str:
        """Thêm vào dấu bố cục ảnh dàn cảnh nối tiếp: ảnh cảnh trước vẽ lại thì ảnh này thành CŨ."""
        t = kho.ref_dang_co(tap, tr["td"]) if tr else None
        return f"\n{tr['td']}@{int(t.stat().st_mtime)}" if t is not None else ""

    def _cum(tap: str, chuong: str, dong: list[int]) -> list[list[int]]:
        """Các chuỗi cảnh cùng phim trường theo thứ tự (cảnh lẻ = chuỗi một cảnh)."""
        ra: list[list[int]] = []
        for i in dong:
            tr = _truoc(tap, chuong, i)
            if ra and tr and tr["i"] == ra[-1][-1]:
                ra[-1].append(i)
            else:
                ra.append([i])
        return ra

    def _dan_duyet(tap: str, td: str) -> bool:
        """Duyệt gắn với GIỜ SỬA file ảnh: vẽ lại ảnh dàn cảnh là tự hết duyệt."""
        t = kho.ref_dang_co(tap, td) if td else None
        return t is not None and kho.doc_vet(tap).get((td, "dan_duyet")) == str(int(t.stat().st_mtime))

    def _hop(pd: dict, ten: str) -> tuple:
        """Khung cắt của một người: người dựng đã kéo thì theo đó, chưa thì mặc định
        (`ben`; cảnh từ 3 người thì chia theo thứ tự trái→phải `hang`). Một chỗ với
        `nhac_khung` của thẻ shot, để nhắc đúng mảnh cắt thật."""
        return mdrama.khung_cua(pd, ten)

    def _dan(cs: list[dict], tra: dict, tr: dict | None = None) -> tuple[dict, dict, dict | None, str]:
        """(phần chung, người cả cảnh, nơi chốn, prompt ảnh dàn cảnh). Chưa có `dan` thì
        prompt rỗng — chưa viết prompt cảnh là chưa biết ai ngồi đâu. `tr` = cảnh trước cùng
        phim trường: prompt SỬA từ ảnh dàn cảnh cảnh đó."""
        chung = _chung_cu(cs) or {}
        nv = _nguoi_canh(tra, cs)
        noi = next((tra[m] for c in cs for m in (c.get("ts") or [])
                    if m in tra and tra[m]["loai"] == "boi_canh"), None)
        p = ""
        if (chung.get("dan") or "").strip():
            p = (mdrama.prompt_dan_noi(chung, list(nv.values()), tr["ten"], tr["chung"]) if tr
                 else mdrama.prompt_dan_canh(chung, list(nv.values()), noi))
        return chung, nv, noi, p

    @app.get("/api/tap/{tap}/{chuong}/dong/{i}/dan-canh")
    def xem_dan_canh(tap: str, chuong: str, i: int):
        _, cs, tra = _dong_drama(tap, chuong, i)
        tr = _truoc(tap, chuong, i)
        chung, nv, _, p = _dan(cs, tra, tr)
        td = _td_cua(cs, tra)
        t = kho.ref_dang_co(tap, td)
        return {"td": td, "co_anh": t is not None, "duyet": _dan_duyet(tap, td), "may_duyet": _may_duyet(tap, td),
                "ref_v": int(t.stat().st_mtime) if t is not None else 0, "nguoi": list(nv),
                "ben": chung.get("ben") or {}, "cat": {n: list(_hop(chung, n)) for n in nv},
                "san": bool(p), "prompt": p,
                # vẽ theo bố cục cũ (viết lại prompt cảnh sau khi vẽ): nhắc, không chặn
                "cu": _dan_cu(tap, td, p, _goc_dan(tap, tr)),
                # cùng phim trường với cảnh liền trước: ảnh này vẽ tiếp trên ảnh cảnh đó
                "truoc": {"ten": tr["en"], "i": tr["i"], "duyet": _dan_duyet(tap, tr["td"])} if tr else None}

    def _may_duyet(tap: str, td: str) -> bool:
        """Dàn cảnh đang duyệt bằng dấu MÁY (nút Chạy tới duyệt ảnh), chưa người nào xác nhận —
        trang nhắc soi lại. Gắn giờ sửa file như dấu duyệt: vẽ lại là hết cả hai."""
        t = kho.ref_dang_co(tap, td)
        return t is not None and _dan_duyet(tap, td) and \
            kho.doc_vet(tap).get((td, "dan_may")) == str(int(t.stat().st_mtime))

    def _dan_cu(tap: str, td: str, p: str, goc: str = "") -> bool:
        """Ảnh dàn cảnh vẽ theo bố cục CŨ: prompt cảnh viết lại sau lần vẽ, hay (`goc`) ảnh dàn
        cảnh của cảnh trước cùng phim trường đã vẽ lại."""
        dau = kho.doc_vet(tap).get((td, "dan"))
        return bool(kho.ref_dang_co(tap, td) is not None and dau and p and dau != _bam(p + goc))

    @app.post("/api/tap/{tap}/{chuong}/dong/{i}/dan-canh")
    @_dang("dan")
    def ve_dan_canh(tap: str, chuong: str, i: int, request: Request):
        """Vẽ ảnh dàn cảnh: tấm nơi chốn + tấm MỌI người của cảnh + câu bố cục LLM viết."""
        ai = _ghi_duoc(request)
        if ve_anh is None:
            raise HTTPException(503, "Chưa bật bộ vẽ ảnh.")
        return {"ok": True, "td": _ve_dan(tap, chuong, i, ai)}

    def _ve_dan(tap: str, chuong: str, i: int, ai: str) -> str:
        """Thân nút vẽ ảnh dàn cảnh — nút tay và việc chạy chương gọi chung."""
        dg, cs, tra = _dong_drama(tap, chuong, i)
        tr = _truoc(tap, chuong, i)
        _, nv, noi, p = _dan(cs, tra, tr)
        if not p:
            raise HTTPException(400, "Cảnh chưa có bố cục — bấm “Viết prompt cảnh” trước: LLM đánh dấu "
                                     "ai bên trái, ai bên phải rồi mới vẽ được ảnh dàn cảnh.")
        goc = kho.ref_dang_co(tap, tr["td"]) if tr else None
        if tr and (goc is None or not _dan_duyet(tap, tr["td"])):
            raise HTTPException(400, f"Cảnh này cùng phim trường với {tr['en']}: ảnh dàn cảnh vẽ TIẾP trên ảnh "
                                     "dàn cảnh cảnh đó (người có mặt trước giữ nguyên chỗ) — vẽ và duyệt ảnh đó trước.")
        # Cảnh sau trong cụm: phòng lấy từ ảnh cảnh trước, không gửi tấm nơi chốn.
        ma = ([noi["ma"]] if noi and not tr else []) + [x["ma"] for x in nv.values()]
        thieu = [tra[m]["ten"] for m in ma if kho.ref_dang_co(tap, m) is None]
        if thieu:
            raise HTTPException(400, f"Chưa có ảnh tham chiếu cho: {', '.join(thieu)} — vẽ ở màn Asset trước.")
        td = _td_cua(cs, tra)
        # Đọc-vá-ghi CẢ sổ trong một nhịp khoá: chạy chương vẽ nhiều cảnh cùng lúc, đọc
        # ngoài khoá là cảnh này ghi đè mất mục `td` cảnh kia vừa thêm.
        with _KHOA_SO:
            so = kho.ds_so(tap)
            if td not in {x["ma"] for x in so}:
                kho.luu_so(tap, so + [{"ma": td, "loai": "truong_doan", "ten": (dg.get("en") or td)[:80]}])
        for c in cs:
            if not (c.get("td") or "").strip():
                _va_canh(tap, chuong, c["id"], lambda y, td=td: y.update(td=td), ai)
        m, duoi = _mo_hinh(tap, cs[0], "anh"), ".png"
        if goc is not None and set(nv) == set(tr["ten"]):
            # Cùng đội hình, cùng phim trường: dùng lại ĐÚNG ảnh cảnh trước — khớp tuyệt đối, 0 credit.
            duoi = goc.suffix.lower()
            kho.duong_ref(tap, td, duoi).write_bytes(goc.read_bytes())
        else:
            try:
                ve_anh.gen_anh(p, kho.duong_ref(tap, td, ".png"),
                               ref=([goc] if goc is not None else []) + [kho.ref_dang_co(tap, x) for x in ma],
                               ti_le="16:9", **({"model": m} if m else {}))
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(502, f"Vẽ ảnh dàn cảnh hỏng: {exc}") from exc
        for d in kho.DUOI_REF:          # đổi đuôi thì đừng để lại bản cũ
            if d != duoi:
                kho.duong_ref(tap, td, d).unlink(missing_ok=True)
        kho.ghi_vet(tap, td, "dan", _bam(p + _goc_dan(tap, tr)))
        # Ảnh mới thì người đổi chỗ: khung kéo trên ảnh cũ hết đúng, về khung mặc định
        # (thẻ shot nhắc nếu khung mặc định dính người ngoài shot). Đọc lại cảnh: kéo khung
        # trong lúc ảnh đang vẽ (60–100 s) cũng là kéo trên ảnh cũ.
        import json as _json

        def bo_cat(y):
            pd = mdrama.doc_pd(y.get("pd"))
            if pd.pop("cat", None) is not None:
                y["pd"] = _json.dumps(pd, ensure_ascii=False)
        for c in _dong_drama(tap, chuong, i)[1]:
            if mdrama.doc_pd(c.get("pd")).get("cat"):
                _va_canh(tap, chuong, c["id"], bo_cat, ai)
        return td

    @app.post("/api/tap/{tap}/{chuong}/dong/{i}/dan-canh/duyet")
    def duyet_dan_canh(tap: str, chuong: str, i: int, request: Request):
        """Cổng của cả cảnh: mọi shot cắt từ ảnh này, sai chỗ ngồi ở đây là sai mọi shot."""
        _ghi_duoc(request)
        _, cs, tra = _dong_drama(tap, chuong, i)
        td = _td_cua(cs, tra)
        t = kho.ref_dang_co(tap, td)
        if t is None:
            raise HTTPException(400, "Cảnh này chưa có ảnh dàn cảnh để duyệt.")
        kho.ghi_vet(tap, td, "dan_duyet", str(int(t.stat().st_mtime)))
        kho.xoa_vet(tap, td, "dan_may")         # người đã soi: thôi là dấu máy duyệt
        return {"ok": True}

    @app.put("/api/tap/{tap}/{chuong}/dong/{i}/dan-canh/cat")
    def luu_cat(tap: str, chuong: str, i: int, request: Request, than: dict = Body(...)):
        """Khung cắt người dựng kéo trên ảnh dàn cảnh (user chốt 29/10: "có"). Ghi vào
        `pd.cat` của MỌI clip trong cảnh — phần chung, clip nào cũng mang một bản."""
        import json as _json

        ai = _ghi_duoc(request)
        _, cs, tra = _dong_drama(tap, chuong, i)
        nv = _nguoi_canh(tra, cs)
        cat = than.get("cat")
        if not isinstance(cat, dict) or not cat:
            raise HTTPException(400, "Thiếu `cat`.")
        sach = {}
        for ten, h in cat.items():
            if ten not in nv:
                raise HTTPException(400, f"'{ten}' không có trong cảnh này.")
            so = isinstance(h, list) and len(h) == 4 and all(
                isinstance(v, (int, float)) and not isinstance(v, bool) for v in h)
            if not so or not (0 <= h[0] < h[2] <= 1 and 0 <= h[1] < h[3] <= 1
                              and h[2] - h[0] >= 0.1 and h[3] - h[1] >= 0.1):
                raise HTTPException(400, f"Khung của {ten} sai: cần 0 ≤ x0 < x1 ≤ 1, 0 ≤ y0 < y1 ≤ 1, "
                                         "mỗi cạnh ít nhất 0,1.")
            sach[ten] = [round(float(v), 4) for v in h]
        co = [c for c in cs if mdrama.doc_pd(c.get("pd")).get("truc_canh")]
        if not co:
            raise HTTPException(400, "Cảnh chưa có bố cục — bấm “Viết prompt cảnh” trước.")
        for c in co:
            def va(y):
                pd = mdrama.doc_pd(y.get("pd"))
                if pd:
                    pd["cat"] = dict(pd.get("cat") or {}, **sach)
                    y["pd"] = _json.dumps(pd, ensure_ascii=False)
            _va_canh(tap, chuong, c["id"], va, ai)
        return {"ok": True}

    def _ss(c: dict) -> dict:
        import json as _json

        try:
            x = _json.loads(c.get("ss") or "{}")
        except ValueError:
            return {}
        return x if isinstance(x, dict) else {}

    def _sua_ss(tap: str, chuong: str, ma: str, sid: str, lam, ai: str) -> None:
        """Vá trạng thái MỘT shot trên bản mới nhất của clip."""
        import json as _json

        def va(y):
            ss = _ss(y)
            o = dict(ss.get(sid) or {})
            lam(o)
            if o:
                ss[sid] = o
            else:
                ss.pop(sid, None)
            if ss:
                y["ss"] = _json.dumps(ss, ensure_ascii=False)
            else:
                y.pop("ss", None)
        _va_canh(tap, chuong, ma, va, ai)

    def _shot_cua(tap: str, chuong: str, ma: str, sid: str) -> tuple[dict, list[dict], int]:
        _, _, _, c = _tim_canh(tap, chuong, ma)
        if not c.get("pm"):
            raise HTTPException(400, "Đây không phải clip drama.")
        sh = mdrama.doc_sh(c.get("sh"))
        k = next((k for k, s in enumerate(sh) if s.get("sid") == sid), None)
        if k is None:
            raise HTTPException(404, "Không có shot này — Breakdown lại là shot đổi mã.")
        return c, sh, k

    def _thieu_pd(c: dict) -> bool:
        """Clip chưa có prompt khớp bộ shot đang chốt (chưa viết, hay viết cho bộ shot khác)."""
        pd, sh = mdrama.doc_pd(c.get("pd")), mdrama.doc_sh(c.get("sh"))
        return len(pd.get("shots") or []) != len(sh) or bool(mdrama.kiem_pd(pd_ghep(pd, sh), c.get("t") or ""))

    def _ghep_shot(tap: str, c: dict, sh: list[dict], k: int) -> dict:
        """Mọi thứ một shot gửi đi: prompt ảnh, prompt video, giây, người, đồ vật.
        Trang hiện và lượt gửi cùng gọi hàm này — thấy gì gửi nấy."""
        pd = mdrama.doc_pd(c.get("pd"))
        t = c.get("t") or ""
        if _thieu_pd(c):
            raise HTTPException(400, "Clip chưa có prompt cho bộ shot này — bấm “Viết prompt cảnh” trước.")
        tra = {x["ma"]: x for x in kho.ds_so(tap)}
        s, lt = sh[k], mdrama.loi_thoai(t)
        nguoi = _nguoi_canh(tra, [c])
        # Đồ vật đi theo shot nào nhắc tên nó (`t` của shot, tiếng Việt như tên đồ).
        do = [tra[m] for m in (c.get("ts") or []) if m in tra and tra[m]["loai"] == "dao_cu"
              and tra[m]["ten"].lower() in (s.get("t") or "").lower()]
        tieng = {n: x["tieng"] for n, x in nguoi.items()
                 if (x.get("tieng") or "").strip() and not mdrama.la_tieng_viet(x["tieng"])}
        kh, giay = khung_shot(dict(s, cd="")), mdrama.giay_shot(s, lt)
        may = CD_DRAMA.get(s.get("cd") or "") or CD_DRAMA["static"]
        return {"pd": pd, "s": s, "nguoi": nguoi, "do": do, "giay": giay, "lt": lt,
                "anh": mdrama.prompt_anh_shot(pd, s, k, t, nguoi, do, kh),
                "video": mdrama.prompt_video_shot(pd, s, k, t, nguoi, tieng, do, kh, may, giay)}

    @app.get("/api/tap/{tap}/{chuong}/canh/{ma}/shot")
    def ds_shot(tap: str, chuong: str, ma: str):
        """Trạng thái từng shot cho thẻ shot của trang. Suy từ ĐĨA như cờ `anh` của cảnh."""
        _, _, _, c = _tim_canh(tap, chuong, ma)
        if not c.get("pm"):
            raise HTTPException(400, "Đây không phải clip drama.")
        ss, lt, ra, pd = _ss(c), mdrama.loi_thoai(c.get("t")), [], mdrama.doc_pd(c.get("pd"))
        for k, s in enumerate(mdrama.doc_sh(c.get("sh"))):
            sid = s.get("sid") or ""      # shot trước 29/10 chưa có mã: Breakdown lại
            o = ss.get(sid) or {}
            a = kho.duong_anh(tap, f"{ma}-{sid}") if sid else None
            v = kho.duong_video(tap, f"{ma}-{sid}") if sid else None
            ra.append({"sid": sid, "k": k + 1, "co_anh": bool(a and a.exists()),
                       "anh_v": int(a.stat().st_mtime) if a and a.exists() else 0,
                       "duyet": bool(o.get("duyet")), "dang": bool(o.get("vid")),
                       "co_video": bool(v and v.exists()),
                       "video_v": int(v.stat().st_mtime) if v and v.exists() else 0,
                       "giay": mdrama.giay_shot(s, lt), "chu_the": mdrama.chu_the(s, lt),
                       "co_mat": s.get("co_mat") or [],
                       "nhac": mdrama.nhac_lap(s.get("lap") or "") + mdrama.nhac_qua_vai(s, lt)
                       + mdrama.nhac_khung(pd, s, lt)})
        return ra

    @app.get("/api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/prompt")
    def xem_prompt_shot(tap: str, chuong: str, ma: str, sid: str):
        c, sh, k = _shot_cua(tap, chuong, ma, sid)
        try:
            g = _ghep_shot(tap, c, sh, k)
        except HTTPException:
            return {"anh": "", "video": "", "giay": 0}
        return {"anh": g["anh"], "video": g["video"], "giay": g["giay"]}

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/anh")
    @_dang("anh")
    def ve_anh_shot(tap: str, chuong: str, ma: str, sid: str, request: Request):
        ai = _ghi_duoc(request)
        if ve_anh is None:
            raise HTTPException(503, "Chưa bật bộ vẽ ảnh.")
        _ve_shot(tap, chuong, ma, sid, ai)
        return {"ok": True}

    def _ve_shot(tap: str, chuong: str, ma: str, sid: str, ai: str) -> None:
        """Thân nút vẽ ảnh khung đầu một shot — nút tay và việc chạy chương gọi chung."""
        c, sh, k = _shot_cua(tap, chuong, ma, sid)
        g = _ghep_shot(tap, c, sh, k)
        td = (c.get("td") or "").strip()
        master = kho.ref_dang_co(tap, td) if td else None
        if master is None:
            raise HTTPException(400, "Cảnh chưa có ảnh dàn cảnh — vẽ và duyệt ảnh dàn cảnh trước: mọi shot "
                                     "cắt từ ảnh đó.")
        if not _dan_duyet(tap, td):
            raise HTTPException(400, "Ảnh dàn cảnh chưa duyệt — xem kỹ ai ngồi đâu rồi bấm Duyệt.")
        s, nguoi = g["s"], g["nguoi"]
        thieu = [n for n in s.get("co_mat") or [] if n not in nguoi or kho.ref_dang_co(tap, nguoi[n]["ma"]) is None]
        thieu += [x["ten"] for x in g["do"] if kho.ref_dang_co(tap, x["ma"]) is None]
        if thieu:
            raise HTTPException(400, f"Chưa có ảnh tham chiếu cho: {', '.join(thieu)} — vẽ ở màn Asset trước.")
        # Image 1: mảnh cắt quanh người máy hướng tới; khung nhiều người (không qua vai)
        # hay shot không có ai thì nguyên ảnh dàn cảnh. Thứ tự ref = thứ tự `prompt_anh_shot`.
        ai_quay = mdrama.chu_the(s, g["lt"])
        dau = master if (mdrama.ca_canh(s) or not ai_quay) else mdrama.cat_master(
            master, _hop(g["pd"], ai_quay), kho.duong_anh(tap, f"{ma}-{sid}-cat"))
        ref = [dau] + [kho.ref_dang_co(tap, nguoi[n]["ma"]) for n in s.get("co_mat") or []] \
            + [kho.ref_dang_co(tap, x["ma"]) for x in g["do"]]
        m = _mo_hinh(tap, c, "anh")
        try:
            ve_anh.gen_anh(g["anh"], kho.duong_anh(tap, f"{ma}-{sid}"), ref=ref, ti_le="16:9",
                           **({"model": m} if m else {}))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Vẽ ảnh hỏng: {exc}") from exc
        # ảnh đổi thì con dấu duyệt cũ hết nghĩa
        _sua_ss(tap, chuong, ma, sid, lambda o: o.pop("duyet", None), ai)

    @app.get("/api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/anh")
    def xem_anh_shot(tap: str, chuong: str, ma: str, sid: str):
        _shot_cua(tap, chuong, ma, sid)
        t = kho.duong_anh(tap, f"{ma}-{sid}")
        if not t.exists():
            raise HTTPException(404, "Shot này chưa có ảnh.")
        return FileResponse(t, headers={"Cache-Control": "no-store"})

    @app.get("/api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/anh-nho")
    def xem_anh_nho_shot(tap: str, chuong: str, ma: str, sid: str):
        """Ảnh nhỏ cho thẻ Storyboard: ảnh gốc ~2,2 MB × 50 thẻ = 110 MB mỗi chương, ảnh nhỏ
        ~14 KB (đo DM002 29/10). Làm lần đầu có người xem, giữ cạnh ảnh gốc; ảnh gốc mới hơn
        (vẽ lại) thì làm lại. Không đọc kho: mã đã chặn ở `duong_anh`, mỗi thẻ một lượt gọi.
        URL mang `?v=` giờ sửa ảnh nên cho trình duyệt giữ hẳn — vẽ lại là URL mới."""
        _ = chuong
        try:
            goc = kho.duong_anh(tap, f"{ma}-{sid}")
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        if not goc.exists():
            raise HTTPException(404, "Shot này chưa có ảnh.")
        nho = goc.with_name(goc.stem + "-nho.jpg")
        try:
            b = nho.read_bytes() if nho.stat().st_mtime >= goc.stat().st_mtime else None
        except OSError:
            b = None
        if b is None:
            import io
            from PIL import Image

            with Image.open(goc) as im:
                im = im.convert("RGB")
                im.thumbnail((320, 320))
                o = io.BytesIO()
                im.save(o, "JPEG", quality=80)
            b = o.getvalue()
            # Ghi tạm rồi đổi tên: hai lượt cùng làm thì không ai đọc phải file dở.
            tam = nho.with_name(f"{nho.name}.{threading.get_ident()}.tam")
            tam.write_bytes(b)
            try:
                os.replace(tam, nho)
            except OSError:      # Windows: lượt khác đang đọc file này — lần sau làm lại
                tam.unlink(missing_ok=True)
        # Trả BYTE, không trả FileResponse: không giữ file mở để lượt khác còn thay được.
        return Response(b, media_type="image/jpeg",
                        headers={"Cache-Control": "private, max-age=31536000, immutable"})

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/duyet")
    def duyet_anh_shot(tap: str, chuong: str, ma: str, sid: str, request: Request):
        """Cổng tiền video của từng shot (luật `aigen`: video chỉ đốt sau duyệt)."""
        ai = _ghi_duoc(request)
        _shot_cua(tap, chuong, ma, sid)
        if not kho.duong_anh(tap, f"{ma}-{sid}").exists():
            raise HTTPException(400, "Shot này chưa có ảnh để duyệt.")
        _sua_ss(tap, chuong, ma, sid, lambda o: o.update(duyet="1"), ai)
        return {"ok": True}

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/video")
    @_dang("video")
    def video_shot(tap: str, chuong: str, ma: str, sid: str, request: Request):
        """Grok i2v từ ảnh đã duyệt của shot, độ dài của shot. Trả mã task NGAY."""
        ai = _ghi_duoc(request)
        if ve_video is None:
            raise HTTPException(503, "Chưa bật bộ dựng video.")
        c, sh, k = _shot_cua(tap, chuong, ma, sid)
        if (_ss(c).get(sid) or {}).get("vid"):
            raise HTTPException(409, "Shot này đang dựng video — đợi xong rồi gửi lại.")
        anh = kho.duong_anh(tap, f"{ma}-{sid}")
        if not anh.exists():
            raise HTTPException(400, "Shot này chưa có ảnh — vẽ ảnh trước đã.")
        if not (_ss(c).get(sid) or {}).get("duyet"):
            raise HTTPException(400, "Ảnh của shot này chưa được duyệt. Tiền video chỉ đốt sau cổng duyệt "
                                     "— xem ảnh rồi bấm Duyệt ảnh đã.")
        g = _ghep_shot(tap, c, sh, k)
        try:
            tid = ve_video.bat_dau(g["video"], anh, g["giay"], False, model=mdrama.MODEL_VIDEO)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Dựng video hỏng: {exc}") from exc
        # Task ĐÃ trả tiền: mã phải xuống kho bất kể ai đang giữ chương.
        _sua_ss(tap, chuong, ma, sid, lambda o: o.update(vid=str(tid)), ai)
        return {"ok": True, "vid": str(tid)}

    @app.post("/api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/video-kiem")
    def kiem_video_shot(tap: str, chuong: str, ma: str, sid: str, request: Request):
        """Như `video-kiem` của cảnh: hỏi một lần; xong thì tải về, xong hay hỏng đều quên mã."""
        ai = _ghi_duoc(request)
        if ve_video is None:
            raise HTTPException(503, "Chưa bật bộ dựng video.")
        c, _, _ = _shot_cua(tap, chuong, ma, sid)
        v = kho.duong_video(tap, f"{ma}-{sid}")
        tid = str((_ss(c).get(sid) or {}).get("vid") or "").strip()
        if not tid:
            return {"trang_thai": "xong" if v.exists() else "chua"}
        try:
            r = ve_video.trang_thai(tid) or {}
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Hỏi trạng thái hỏng: {exc}") from exc
        tt = str(r.get("status") or "").lower()
        if tt == "succeeded":
            try:
                ve_video.tai_ve(r.get("video_url") or "", v)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(502, f"Tải video về hỏng: {exc}") from exc
            _sua_ss(tap, chuong, ma, sid, lambda o: o.pop("vid", None), ai)
            return {"trang_thai": "xong"}
        if tt in ("failed", "cancelled"):
            _sua_ss(tap, chuong, ma, sid, lambda o: o.pop("vid", None), ai)
            return {"trang_thai": "hong", "loi": r.get("loi") or tt}
        return {"trang_thai": "dang"}

    @app.get("/api/tap/{tap}/{chuong}/canh/{ma}/shot/{sid}/video")
    def xem_video_shot(tap: str, chuong: str, ma: str, sid: str):
        _shot_cua(tap, chuong, ma, sid)
        t = kho.duong_video(tap, f"{ma}-{sid}")
        if not t.exists():
            raise HTTPException(404, "Shot này chưa có video.")
        return FileResponse(t, headers={"Cache-Control": "no-store"})

    # ----------------------------------- chạy cả chương tới duyệt ảnh shot (user chốt 29/10)
    # Một nút cho cả chương drama: Breakdown clip chưa có shot → Viết prompt cảnh → vẽ ảnh
    # dàn cảnh → MÁY TỰ DUYỆT dàn cảnh (user chốt "tự động duyệt ảnh phối cảnh") → ảnh khung
    # đầu mọi shot. Dừng ở duyệt ảnh shot: không duyệt shot hộ, không gọi video — tiền video
    # chỉ đốt sau cổng NGƯỜI duyệt. Khuôn việc nền của Gen toàn bộ asset: tiến độ trong bộ nhớ,
    # restart thì bấm lại, phần đã xong bỏ qua. Luật cứng 5: dàn cảnh máy duyệt mang dấu riêng
    # (`dan_may`) và được liệt kê — cảnh từ 3 người khung cắt mặc định còn lệch (đo C005 29/10).

    def _dong_cua(tap: str, chuong: str) -> list[int]:
        return [i for i, dg in enumerate(kho.doc(tap, chuong)["dong"])
                if any(c.get("pm") and c.get("id") for c in mdong.doc_canh(dg))]

    def _ke_hoach_chuong(tap: str, chuong: str) -> dict:
        """Việc còn thiếu của chương, Python đếm trên kho; shot của clip chưa Breakdown là số ƯỚC."""
        tra = {x["ma"]: x for x in kho.ds_so(tap)}
        kh = {"dong": 0, "clip": 0, "breakdown": 0, "prompt": 0, "dan": 0, "cho_duyet": 0, "shot": 0,
              "it_chac": [], "may_duyet": []}
        llm = 0
        for i, dg in enumerate(kho.doc(tap, chuong)["dong"]):
            cs = [c for c in mdong.doc_canh(dg) if c.get("pm") and c.get("id")]
            if not cs:
                continue
            bd = [c for c in cs if not mdrama.doc_sh(c.get("sh"))]
            pr = [c for c in cs if c in bd or _thieu_pd(c)]
            td, n = _td_cua(cs, tra), len(_nguoi_canh(tra, cs))
            co_dan = kho.ref_dang_co(tap, td) is not None
            kh["dong"] += 1
            kh["clip"] += len(cs)
            kh["breakdown"] += len(bd)
            kh["prompt"] += len(pr)
            kh["dan"] += not co_dan
            kh["cho_duyet"] += co_dan and not _dan_duyet(tap, td)
            kh["shot"] += sum(uoc_shot(c.get("t")) if c in bd else sum(
                1 for s in mdrama.doc_sh(c.get("sh"))
                if s.get("sid") and not kho.duong_anh(tap, f"{c['id']}-{s['sid']}").exists()) for c in cs)
            llm += bool(pr)
            if n >= 3:
                kh["it_chac"].append({"i": i, "ten": dg.get("en", ""), "nguoi": n})
            # Dấu máy nằm trong kho, không trong bộ nhớ việc: restart xong vẫn biết cảnh nào cần soi.
            if _may_duyet(tap, td):
                kh["may_duyet"].append({"i": i, "ten": dg.get("en", ""), "nguoi": n})
        model = _mo_hinh_tai_san(tap)
        anh = kh["dan"] + kh["shot"]
        return dict(kh, anh=anh, model=model, credit=anh * mtai_san.gia_anh(model, True),
                    phut=math.ceil(llm / LUONG_LLM_CHUONG) * PHUT_LLM_CANH
                    + math.ceil(anh * mtai_san.GIAY_ANH / (60 * LUONG_ANH_CHUONG)))

    @app.get("/api/tap/{tap}/{chuong}/chay")
    def xem_chay_chuong(tap: str, chuong: str):
        with _KHOA_VIEC:
            v = _CHAY.get((tap, chuong))
            viec = dict(v, loi=list(v["loi"]), may_duyet=list(v["may_duyet"])) if v else None
        return {"ke_hoach": _ke_hoach_chuong(tap, chuong), "viec": viec}

    @app.post("/api/tap/{tap}/{chuong}/chay")
    def chay_chuong(tap: str, chuong: str, request: Request):
        ai = _ghi_duoc(request)
        if kho.kieu_tap(tap)["loai"] != "drama":
            raise HTTPException(400, "Nút này dành cho tập drama — narration làm từng cảnh.")
        if ve_anh is None or not all(hasattr(ky_thuat, x) for x in ("drama_breakdown", "drama_canh", "drama_clip")):
            raise HTTPException(503, "Chưa bật bộ vẽ ảnh hay bộ sinh prompt.")
        giu = kho.ai_giu(tap, chuong)
        if giu and giu != ai:
            raise HTTPException(409, f"{giu} đang sửa chương {chuong} — đợi xong rồi chạy.")
        kh = _ke_hoach_chuong(tap, chuong)
        if not kh["dong"]:
            raise HTTPException(400, f"Chương {chuong} chưa có clip drama nào.")
        if not any(kh[x] for x in ("breakdown", "prompt", "dan", "cho_duyet", "shot")):
            raise HTTPException(400, f"Chương {chuong} đã tới bước duyệt ảnh shot — không còn gì để chạy.")
        with _KHOA_VIEC:
            if (_VIEC.get(tap) or {}).get("chay"):
                raise HTTPException(409, f"{_VIEC[tap]['nguoi']} đang gen toàn bộ asset — đợi xong rồi Generate All.")
            v = _CHAY.get((tap, chuong))
            if v and v["chay"]:
                raise HTTPException(409, f"{v['nguoi']} đang Generate All chương {chuong} — đợi xong.")
            o = next((o for o in _DANG.values() if o["tap"] == tap and o["ch"] == chuong), None)
            if o:
                raise HTTPException(409, _cau_dang(o) + " — đợi xong rồi Generate All.")
            _CHAY[(tap, chuong)] = {"chay": True, "buoc": "llm", "xong": 0, "tong": 0, "loi": [],
                                    "may_duyet": [], "nguoi": ai, "bat_dau": time.time(), "het": None}
        threading.Thread(target=_chay_chuong, args=(tap, chuong, ai), daemon=True).start()
        return {"ok": True}

    def _chay_chuong(tap: str, chuong: str, ai: str) -> None:
        """LLM từng cảnh (2 cảnh một lúc) → ảnh dàn cảnh → máy duyệt → ảnh shot (6 luồng).
        Một clip / một cảnh hỏng thì ghi lỗi rồi làm tiếp; không tự thử lại (tốn tiền)."""
        from concurrent.futures import ThreadPoolExecutor

        v = _CHAY[(tap, chuong)]
        hong, dung, ve_moi = {"llm": 0, "anh": 0}, set(), set()

        def loi(ten: str, chu) -> None:
            with _KHOA_VIEC:
                v["loi"].append({"ma": "", "ten": ten, "loi": str(chu)[:300]})

        def dem(loai: str, ok: bool, n: int = 1) -> None:
            """Lỗi nhà cung cấp LIỀN NHAU; đủ PHANH thì dừng hẳn loại việc đó."""
            with _KHOA_VIEC:
                hong[loai] = 0 if ok else hong[loai] + n
                vua = hong[loai] >= PHANH and loai not in dung
                if vua:
                    dung.add(loai)
            if vua:
                loi("Dừng " + ("LLM" if loai == "llm" else "vẽ ảnh"), f"{PHANH} lượt hỏng liền (hết quota / "
                    "hết credit?) — phần còn lại chưa làm; kiểm rồi bấm lại.")

        def buoc(ten: str, tong: int) -> None:
            with _KHOA_VIEC:
                v.update(buoc=ten, xong=0, tong=tong)

        def xong_1() -> None:
            with _KHOA_VIEC:
                v["xong"] += 1

        def ket_llm(ten: str, ds: list[str], ok: int, dau: str) -> None:
            for x in ds:
                loi(ten, x)
            n = sum(dau in x for x in ds)       # lỗi từ nhà LLM, không phải lỗi kiểm chữ
            if ok or n:
                dem("llm", bool(ok), n)

        def bat(ten: str, viec, loai: str, dau: str = "") -> bool:
            """Chạy `viec`; HTTPException 502 là lỗi nhà cung cấp, 400 là thiếu bước trước."""
            try:
                viec()
                return True
            except HTTPException as exc:
                loi(ten, dau + str(exc.detail))
                if exc.status_code == 502:
                    dem(loai, False)
            except Exception as exc:  # noqa: BLE001 — một cảnh / một shot hỏng không giết cả chương
                loi(ten, dau + str(exc))
            return False

        def llm_dong(i: int) -> None:
            dg, cs, tra = _dong_drama(tap, chuong, i)
            ten = dg.get("en") or f"cảnh {i + 1}"
            bd = [c for c in cs if not mdrama.doc_sh(c.get("sh"))]
            if bd and "llm" not in dung:
                r = _breakdown_clip(tap, chuong, dg, cs, bd, tra, ai)
                ket_llm(ten, r["loi"], r["so_clip"], "breakdown hỏng:")
                dg, cs, tra = _dong_drama(tap, chuong, i)
            co, _ = _co_shot(cs)
            for c in cs:
                if mdrama.doc_sh(c.get("sh")) and c not in co:
                    loi(ten, f"{c['pm']}: chữ clip đổi sau Breakdown — Breakdown lại bằng tay (máy không làm "
                             "lại: shot mới mã mới, mất ảnh, duyệt, video của shot cũ).")
            can = [c for c in co if _thieu_pd(c)]
            if not can or "llm" in dung:
                return
            chung = _chung_cu(cs)
            if not (chung or {}).get("dan"):
                # Chưa có bố cục: viết phần chung + MỌI clip đã Breakdown, như nút Viết prompt cảnh.
                chung, can = _phan_chung(tap, dg, cs, tra, _truoc(tap, chuong, i)), co
            r = _viet_clip(tap, chuong, dg, cs, can, tra, chung, ai)
            ket_llm(ten, r["loi"], r["viet"], "viết prompt hỏng:")

        def dan_dong(i: int) -> None:
            dg, cs, tra = _dong_drama(tap, chuong, i)
            if kho.ref_dang_co(tap, _td_cua(cs, tra)) is None and "anh" not in dung:
                if bat(dg.get("en", ""), lambda: _ve_dan(tap, chuong, i, ai), "anh", "Ảnh dàn cảnh: "):
                    ve_moi.add(i)
                    dem("anh", True)

        def may_duyet(i: int) -> None:
            dg, cs, tra = _dong_drama(tap, chuong, i)
            td = _td_cua(cs, tra)
            t = kho.ref_dang_co(tap, td)
            if t is None or _dan_duyet(tap, td):
                return
            tr = _truoc(tap, chuong, i)
            _, nv, _, p = _dan(cs, tra, tr)
            if _dan_cu(tap, td, p, _goc_dan(tap, tr)):
                loi(dg.get("en", ""), "Ảnh dàn cảnh vẽ theo bố cục CŨ (prompt cảnh viết lại sau lần vẽ) — máy "
                                      "không tự duyệt: vẽ lại hoặc duyệt tay.")
                return
            mt = str(int(t.stat().st_mtime))
            kho.ghi_vet(tap, td, "dan_duyet", mt)
            kho.ghi_vet(tap, td, "dan_may", mt)
            with _KHOA_VIEC:
                v["may_duyet"].append({"i": i, "ten": dg.get("en", ""), "td": td, "nguoi": len(nv),
                                       "co_san": i not in ve_moi})

        def tung(ham, i: int) -> None:
            """Một cảnh: lỗi ngoài dự kiến ghi lại, cảnh khác vẫn chạy; đếm tiến độ."""
            try:
                ten = kho.doc(tap, chuong)["dong"][i].get("en") or f"cảnh {i + 1}"
                bat(ten, lambda: ham(i), "llm" if ham is llm_dong else "anh")
            finally:
                xong_1()

        try:
            dong = _dong_cua(tap, chuong)
            buoc("llm", len(dong))
            # Cụm cùng phim trường chạy LẦN LƯỢT (cảnh sau giữ chỗ người theo cảnh trước), các cụm song song.
            cum = _cum(tap, chuong, dong)
            with ThreadPoolExecutor(max_workers=LUONG_LLM_CHUONG) as ex:
                list(ex.map(lambda ds: [tung(llm_dong, i) for i in ds], cum))
            buoc("dan", len(dong))

            def dan_cum(ds: list[int]) -> None:
                """Vẽ rồi máy duyệt ngay từng cảnh: cảnh sau vẽ tiếp trên ảnh cảnh trước đã duyệt."""
                for i in ds:
                    tung(dan_dong, i)
                    bat(f"cảnh {i + 1}", lambda i=i: may_duyet(i), "anh")
            with ThreadPoolExecutor(max_workers=LUONG_ANH_CHUONG) as ex:
                list(ex.map(dan_cum, cum))
            viec = []
            for i in dong:
                dg, cs, tra = _dong_drama(tap, chuong, i)
                if _dan_duyet(tap, _td_cua(cs, tra)):
                    viec += [(dg.get("en", ""), c, k, s["sid"]) for c in cs if not _thieu_pd(c)
                             for k, s in enumerate(mdrama.doc_sh(c.get("sh")), 1)
                             if s.get("sid") and not kho.duong_anh(tap, f"{c['id']}-{s['sid']}").exists()]
            buoc("shot", len(viec))

            def shot_1(x) -> None:
                ten, c, k, sid = x
                try:
                    if "anh" not in dung and bat(ten, lambda: _ve_shot(tap, chuong, c["id"], sid, ai), "anh",
                                                 f"{c['pm']} shot {k}: "):
                        dem("anh", True)
                finally:
                    xong_1()

            if viec:
                with ThreadPoolExecutor(max_workers=min(len(viec), LUONG_ANH_CHUONG)) as ex:
                    list(ex.map(shot_1, viec))
        except Exception as exc:  # noqa: BLE001
            loi("Generate All", exc)
        finally:
            with _KHOA_VIEC:
                v.update(chay=False, buoc="xong", het=time.time())

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

    @property
    def model_ket(self):
        """Model Owner cấp cho việc vẽ ảnh ở General (gen_canh); chưa cấp -> ""."""
        from autoedit.treatment.dich import doc_ket_viec

        return (doc_ket_viec("gen_canh") or {}).get("model") or ""

    @property
    def credit(self):
        """Số dư tài khoản của việc vẽ ảnh; không phải Seedvis / lỗi -> None."""
        from autoedit.treatment.dich import doc_ket_viec

        try:
            cd = doc_ket_viec("gen_canh") or {}
            m = _may_ve(cd) if cd.get("key") else None
            return m.tai_khoan().get("credit") if hasattr(m, "tai_khoan") else None
        except Exception:  # noqa: BLE001
            return None


class _VeVideo:
    """Seedance qua ArkClient, khoá lấy từ KÉT bằng slug của Treatment.

    Dùng chung cấp phát `gen_canh` với bộ vẽ ảnh: một khoá ARK chạy cả Seedream
    lẫn Seedance. Tách việc riêng chỉ để đo tiền tách bạch thì làm sau.
    """

    _LUOT = itertools.count()       # lượt xoay vòng khoá Lightvisual, chung mọi request của tiến trình

    def _ds_lv(self) -> tuple[list, str]:
        """[(id khoá, client)] mọi khoá Lightvisual ở `gen_video` (Owner chốt 29/10: "mặc định dùng
        ncc này để gen video"), đúng thứ tự trên General, kèm chế độ cấp. Khoá nhà khác (Seedvis)
        trong cùng việc không vào vòng."""
        from autoedit.aigen.lightvisual import LightvisualClient
        from autoedit.treatment.dich import doc_ket_viec

        cd = doc_ket_viec("gen_video") or {}
        ds = [k for k in (cd.get("ds") or [cd]) if k.get("key") and "lightvisual" in (k.get("base_url") or "")]
        return ([(k.get("id") or "", LightvisualClient(api_key=k["key"], base_url=k["base_url"])) for k in ds],
                cd.get("che_do") or "")

    def _lv(self):
        """(client, id khoá) cho một lượt GỬI video Grok; gen_video không có khoá Lightvisual -> None.
        Nhiều khoá (user duyệt 30/10: nhiều tài khoản cho đỡ nghẽn) -> xoay vòng. `du_phong` (failover
        ở General) -> luôn khoá đầu: hết số dư thì Owner tự gỡ, KHÔNG tự đổi (luật cứng 5)."""
        ds, che_do = self._ds_lv()
        if not ds:
            return None
        kid, m = ds[0] if che_do == "du_phong" else ds[next(self._LUOT) % len(ds)]
        return m, kid

    def _hoi_lan_luot(self, kid: str, lam):
        """HỎI / TẢI task Lightvisual đã gửi bằng khoá `kid`. Còn khoá đó -> chỉ nó (hỏi nhầm tài
        khoản là mất video); `vid` cũ không mang khoá -> khoá đầu như trước; khoá đã thu hồi -> lần
        lượt các khoá còn lại (GET không tốn tiền), hết thì ném lỗi cuối. Không còn khoá Lightvisual
        -> báo rõ, đừng đem hỏi nhầm Seedvis."""
        ds, _ = self._ds_lv()
        if not ds:
            raise RuntimeError("Video này dựng ở Lightvisual mà khoá gen_video không còn là Lightvisual — "
                               "Owner gán lại ở General › API Keys › Theo app › Treatment › gen_video.")
        loi = None
        for k, m in (([x for x in ds if x[0] == kid] or ds) if kid else ds[:1]):
            try:
                return lam(k, m)
            except Exception as exc:  # noqa: BLE001 — sang khoá kế
                loi = exc
        raise loi

    def _may(self):
        from autoedit.treatment.dich import doc_ket_viec

        # Việc riêng `gen_video` (ảnh và video là hai model khác nhau ở Seedvis);
        # chưa cấp thì dùng chung `gen_canh` như trước. gen_video là Lightvisual (chỉ chạy
        # Grok): model khác (Omni/Veo) và task Seedvis đang dở cũng đi khoá ảnh này.
        cd = doc_ket_viec("gen_video") or {}
        if not cd.get("key") or "lightvisual" in (cd.get("base_url") or ""):
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
            if self._ds_lv()[0]:      # /balance của Lightvisual báo 0đ cả khi gói ngày đang chạy
                return None
            m = self._may()
            return m.tai_khoan().get("credit") if hasattr(m, "tai_khoan") else None
        except Exception:  # noqa: BLE001
            return None

    @property
    def cung_anh(self):
        """Việc video và việc vẽ ảnh dùng CÙNG một khoá (video chưa cấp thì đi nhờ
        khoá ảnh) — trang hiện một số dư thay vì hai."""
        from autoedit.treatment.dich import doc_ket_viec

        v = (doc_ket_viec("gen_video") or {}).get("key")
        return not v or v == (doc_ket_viec("gen_canh") or {}).get("key")

    def _cua(self, model):
        """(client, id khoá): video GROK đi Lightvisual khi két cấp, còn lại `_may()`. Lỗi thì báo,
        KHÔNG tự đổi sang nhà kia (luật cứng 5) — đổi nhà là Owner gỡ / gán khoá ở General."""
        return ("grok" in (model or "") and self._lv()) or (self._may(), "")

    def bat_dau(self, prompt, anh, giay, am, model=None):
        """Mã task Lightvisual mang id khoá đã gửi (`lv_job_x@api-012`) để hỏi đúng tài khoản."""
        m, kid = self._cua(model)
        kw = {"model": model} if model else {}
        return _gan_khoa(m.gen_video_i2v(prompt, anh, giay=giay, am=am, **kw), kid)

    def bat_dau_ref(self, prompt, anh, giay, model=None):
        """Drama: dựng từ ảnh tham chiếu (Grok `multi-image-to-video`)."""
        m, kid = self._cua(model)
        if not hasattr(m, "gen_video_ref"):
            raise RuntimeError("Nhà video đang cấp không có đường ảnh tham chiếu — "
                               "drama cần Seedvis (Owner cấp ở General › API Keys › gen_video).")
        return _gan_khoa(m.gen_video_ref(prompt, anh, giay=giay, **({"model": model} if model else {})), kid)

    def trang_thai(self, tid):
        from autoedit.aigen.lightvisual import TIEN_TO_TASK

        if not str(tid).startswith(TIEN_TO_TASK):      # nhà theo mã task: đổi khoá giữa chừng không lạc
            return self._may().trang_thai_video(tid)
        ma, _, kid = str(tid).partition("@")

        def hoi(k, m):
            r = m.trang_thai_video(ma)
            # Đường tải mang khoá đã nhận task: route gọi `tai_ve` ngay sau, phải tải đúng tài khoản.
            return dict(r, video_url=r["video_url"] + "#" + k) if r.get("video_url") and k else r
        return self._hoi_lan_luot(kid, hoi)

    def tai_ve(self, url, dich):
        if "lightvisual.studio" not in (url or ""):
            return self._may().tai_video(url, dich)
        url, _, kid = url.partition("#")
        return self._hoi_lan_luot(kid, lambda k, m: m.tai_video(url, dich))


def _gan_khoa(tid, kid: str) -> str:
    """Mã task + id khoá két (không phải giá trị khoá). Seedvis / khoá không id -> giữ nguyên mã."""
    return f"{tid}@{kid}" if kid else str(tid)


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
    "7. `ly_do`: một câu vì sao chọn mã đó.\n"
    "8. `co_mat`: tên những người THẤY ĐƯỢC trong khung shot đó, chép đúng tên ở dòng \"trong khung\" của "
    "clip — qua vai thì có cả người ở tiền cảnh; cận một người thì chỉ người đó; người nói từ ngoài "
    "khung không có tên ở đây.\n\n"
    "BẢNG CỠ (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in CO_CHU.items()) + "\n"
    "BẢNG GÓC (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in GOC_CHU.items()) + "\n"
    "BẢNG CHUYỂN ĐỘNG (mã: nghĩa): " + "; ".join(f"{k}: {v}" for k, v in CD_DRAMA.items()) + "\n\n"
    "Trả về JSON: {\"shots\": [{\"t\": \"...\", \"co\": \"CU\", \"goc\": \"ots\", \"cd\": \"static\", "
    "\"cau\": [0], \"co_mat\": [\"...\"], \"ly_do\": \"...\"}]}")


# Luật đồ vật chép từ bảng tài sản Padoma (`bang_tai_san.py`, Spec 27 E) — chỉ phần đồ vật.
_LENH_DO_VAT = (
    "Bạn là trợ lý đạo diễn lập danh sách ĐỒ VẬT cần ảnh riêng cho một phim drama AI: Grok dựng mỗi clip từ "
    "ảnh tham chiếu, đồ vật không có ảnh thì mỗi clip vẽ một kiểu. Bạn nhận tên các NHÂN VẬT của phim và các "
    "clip của một phần phim: mã clip, tiêu đề cảnh, chữ biên kịch (`Hình:` tả từng shot, `Thoại:`).\n\n"
    "LUẬT:\n"
    "1. Chỉ lấy đồ vật LẶP LẠI qua nhiều clip hoặc CẦN NHÌN RÕ (được cầm, đưa, đọc, đặt giữa khung, là mấu "
    "chốt câu chuyện). Bỏ đồ chỉ thoáng qua; đồ nội thất thuộc nơi chốn (giường, bàn, ghế, cửa sổ); quần áo, "
    "trang sức người đang mặc (đã nằm trong tấm nhân vật); phụ kiện nhỏ (xích, khăn, vòng cổ).\n"
    "2. `ten`: tên tiếng Việt ngắn 2–5 chữ, gọi như kịch bản gọi. Một đồ vật một mục.\n"
    "3. `chu`: mô tả tiếng Anh 15–40 từ để vẽ ảnh đồ vật trên nền trắng: hình dáng, cỡ so với bàn tay, chất "
    "liệu, màu, tình trạng (mới, cũ, rách, mở hay đóng). Không người, không tay. Đồ có chữ đọc được trong "
    "phim (tên, chữ ký, ngày, số, biển, dòng khắc) thì chép NGUYÊN VĂN từng chữ trong ngoặc kép đúng như kịch "
    "bản; giấy tờ có chữ mà kịch bản không ghi thì ghi chữ hợp cốt truyện trong ngoặc kép.\n"
    "4. Đồ vật có ẢNH hay CHÂN DUNG một NHÂN VẬT (thẻ có ảnh, báo đăng ảnh, khung ảnh) thì trong `chu` gọi "
    "đúng TÊN nhân vật đó như danh sách NHÂN VẬT, KHÔNG để trong ngoặc kép, kèm người đó mặc gì trong ảnh: "
    "\"a small photo of Richard in a charcoal suit\". KHÔNG tả da, tóc, tuổi, nét mặt của người trong ảnh — "
    "máy gửi kèm ảnh mặt nhân vật. Tên chỉ IN thành chữ trên đồ thì vẫn trong ngoặc kép. "
    "Đồ vật không có ảnh người thì không viết tên nhân vật ngoài ngoặc kép.\n"
    "5. `clip`: mã các clip mà đồ vật THẤY RÕ trong khung và phải đúng hình. Clip chỉ nhắc tên mà không thấy "
    "đồ vật thì không gán.\n"
    "6. Không bịa đồ vật không có trong chữ biên kịch. Không có đồ vật nào đạt luật thì trả danh sách rỗng.\n\n"
    'Trả về JSON: {"do_vat": [{"ten": "...", "chu": "...", "clip": ["P001"]}]}')

# Đồ vật tìm theo từng chương nên cùng một vật mang nhiều tên (DM002 29/10: "Bàn cờ" / "Bàn cờ
# gỗ", sáu loại "đơn đào tạo") — một lượt rà cả tập. Luật 2 giữ ảnh người trên đồ vật đúng tên.
_LENH_RA_DO_VAT = (
    "Bạn rà danh sách ĐỒ VẬT của một phim drama AI. Danh sách tìm theo từng phần phim, nên cùng một đồ vật có "
    "thể mang nhiều tên. Mỗi mục: số [i], tên, mô tả tiếng Anh dùng vẽ ảnh, chữ biên kịch của vài clip có nó. "
    "Bạn cũng nhận tên các NHÂN VẬT của phim.\n\n"
    "LUẬT:\n"
    "1. `nhom`: các nhóm số thứ tự là CÙNG MỘT đồ vật trong truyện — cùng một vật thể, hay cùng một tờ giấy, "
    "tờ báo nhân vật cầm qua nhiều cảnh. Mục đầu nhóm là mục mô tả đúng nhất, giữ tên và mô tả của nó. Hai "
    "vật khác nhau cùng loại (hai tờ đơn khác nội dung, danh thiếp của hai người, hai tờ báo khác dòng tít) "
    "thì KHÔNG gộp. Không chắc thì KHÔNG gộp.\n"
    "2. `sua`: {\"i\": \"mô tả mới\"} chỉ cho đồ vật có ẢNH hay CHÂN DUNG một nhân vật trong danh sách NHÂN "
    "VẬT mà mô tả chưa gọi đúng tên (\"a woman\", \"a small photo square\") hay còn tả da, tóc, tuổi người "
    "trong ảnh. Viết lại mô tả tiếng Anh 15–40 từ, gọi TÊN nhân vật không để trong ngoặc kép, kèm người đó "
    "mặc gì trong ảnh theo chữ biên kịch; BỎ mọi chữ tả da, tóc, tuổi, nét mặt người trong ảnh (máy gửi kèm "
    "ảnh mặt nhân vật, chữ cũ như \"blonde\" là vẽ sai người); giữ nguyên mọi chữ trong ngoặc kép. Mô tả đã "
    "đúng thì không đưa vào.\n\n"
    'Trả về JSON: {"nhom": [[0, 3]], "sua": {"5": "..."}}')


_ANH_TREN_DO = re.compile(r"photo|portrait|picture", re.I)


def _than_ra(ten_nv: list[str], do: list[dict], chu_clip: dict) -> str:
    """Thân lượt rà đồ vật cả tập: tên nhân vật + mỗi đồ vật kèm chữ biên kịch tối đa hai
    clip có nó — đồ vật có ẢNH thì đoạn dài hơn để biết ai trong ảnh. Đo DM002 29/10: bỏ chữ
    clip của đồ không có ảnh không nhanh hơn (126 so với 121 giây) mà gộp sót 6 tờ đơn."""
    def mot(i, x):
        dai = 400 if _ANH_TREN_DO.search(x["chu"]) else 240
        return f"[{i}] {x['ten']} — {x['chu']}\n    " + "; ".join(
            f"{p}: {' '.join((chu_clip.get(p) or '').split())[:dai]}" for p in x["clip"][:2])
    return (f"NHÂN VẬT CỦA PHIM: {', '.join(ten_nv) or '(chưa có)'}\n\nĐỒ VẬT:\n"
            + "\n".join(mot(i, x) for i, x in enumerate(do)))


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

    def tim_do_vat(self, than):
        from autoedit.treatment.dich import LLM

        ra = LLM(VIEC_SINH_PROMPT).goi(_LENH_DO_VAT, than)
        return ra if isinstance(ra, dict) else {}

    def ra_do_vat(self, than):
        from autoedit.treatment.dich import LLM

        ra = LLM(VIEC_SINH_PROMPT).goi(_LENH_RA_DO_VAT, than)
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
