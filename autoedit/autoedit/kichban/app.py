r"""Bàn kịch bản — tầng web, chạy CỔNG RIÊNG (mặc định 9121).

Vì sao không nhét vào app 9118 (user lo 15/09: *"code luôn trên production bây
giờ sẽ ảnh hưởng tới công việc của team"*): app này khởi động/khởi động lại bao
nhiêu lần cũng không cắt UI của người đang dựng, và lỗi import ở đây không giết
tiến trình kia. Khi nào chạy ổn định thì gắn một dòng link vào nav của 9118.

Danh tính: header `X-Remote-User` do cổng CRM đặt — cùng quy ước với 9118 để đặt
sau cùng một cổng gác là chạy ngay. Không có header thì CHỈ ĐỌC (401 khi ghi):
2-3 người làm cùng lúc, không biết ai là ai thì không khoá được gì.

Chạy:  python -m autoedit.kichban.app --port 9121
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

from autoedit.kichban import dong as mdong
from autoedit.kichban.kho import Kho, KhoaBiGiu

TRANG = Path(__file__).parent / "static" / "kichban.html"


def _khoa_ket_co() -> bool:
    """Két OUTLIERY đã có khoá chưa — để UI nói rõ đang dùng đường nào."""
    try:
        from autoedit.kichban.dich import _khoa_tu_ket

        return bool(_khoa_tu_ket()[0])
    except Exception:  # noqa: BLE001
        return False


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


def _ghi_duoc(request: Request) -> str:
    ai = _nguoi(request)
    if not ai:
        raise HTTPException(401, "Chưa đăng nhập — cổng CRM chưa gửi X-Remote-User.")
    return ai


def tao_app(kho: Kho, dich=None, kiem=None, thu_llm=None) -> FastAPI:
    """`kho`, `dich`, `kiem` tiêm từ ngoài: test chạy DB tạm + đồ giả, không mạng."""
    app = FastAPI(title="Bàn kịch bản RenderY")

    # ------------------------------------------------------------- trang
    @app.get("/", response_class=HTMLResponse)
    def trang():
        return TRANG.read_text(encoding="utf-8")

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

    @app.get("/api/toi")
    def toi(request: Request):
        """Trang cần biết MÌNH là ai để biết chương nào là khoá của mình, chương
        nào của người khác. Không có header thì trả rỗng — trang tự chuyển sang
        chế độ chỉ xem thay vì để người ta gõ cả buổi rồi 401 lúc lưu."""
        return {"nguoi": _nguoi(request)}

    # ------------------------------------------------------------- cài đặt
    def _che(k: str) -> str:
        """Khoá đọc ra luôn CHE. Mạng nội bộ + danh tính mới là tên tự khai, nên
        không API nào được trả khoá thật."""
        return f"…{k[-4:]}" if k else ""

    @app.get("/api/cai-dat")
    def doc_cai_dat():
        d = kho.doc_cai_dat()
        d["llm_key"] = _che(d.get("llm_key", ""))
        d["co_ket"] = bool(_khoa_ket_co())
        return d

    @app.post("/api/cai-dat")
    def luu_cai_dat(request: Request, than: dict = Body(...)):
        _ghi_duoc(request)
        try:
            kho.luu_cai_dat(than or {})
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True}

    @app.post("/api/cai-dat/thu")
    def thu_cai_dat(request: Request):
        """Dán khoá xong bấm THỬ được ngay — không thì lỗi chỉ lộ lúc đang kiểm
        chứng giữa chừng, sau khi đã tốn một lượt tra Google."""
        _ghi_duoc(request)
        if thu_llm is None:
            raise HTTPException(503, "Chưa bật đường thử.")
        try:
            return {"ok": True, **(thu_llm(kho.doc_cai_dat()) or {})}
        except Exception as exc:  # noqa: BLE001 — báo lỗi ra UI, không nổ 500
            return {"ok": False, "loi": str(exc)}

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
        """Chỉ dịch dòng CÒN THIẾU — không đụng dòng người đã sửa tay, và không
        đốt tiền dịch lại cả chương mỗi lần chẻ một dòng."""
        ai = _ghi_duoc(request)
        if dich is None:
            raise HTTPException(503, "Chưa bật bộ dịch.")
        d = kho.doc(tap, chuong)["dong"]
        can = [i for i, x in enumerate(d) if not (x.get("vi") or "").strip()
               and (x.get("en") or "").strip()]
        if not can:
            return {"dich": 0}
        try:
            ra = dich.dich([d[i]["en"] for i in can])
        except Exception as exc:          # noqa: BLE001 — cột tiếng Anh phải còn nguyên
            raise HTTPException(502, f"Dịch hỏng: {exc}") from exc
        for i, v in zip(can, ra):
            d[i]["vi"] = v
        try:
            kho.luu(tap, chuong, d, kho.doc(tap, chuong)["outline"], ai)
        except KhoaBiGiu as exc:
            raise HTTPException(409, str(exc)) from exc
        return {"dich": len(can)}

    # ---------------------------------------------------------- citation
    @app.post("/api/tap/{tap}/{chuong}/kiem")
    def kiem_doan_api(tap: str, chuong: str, request: Request, than: dict = Body(...)):
        """Kiểm chứng ĐOẠN người dùng bôi đen — chỉ chạy khi có người bấm.

        Gác khoá chương như mọi đường ghi: thẻ citation là dữ liệu của chương,
        người khác đang giữ thì không được chen vào. Và mỗi lượt là tiền thật
        (1 lượt Serper + 2 lượt GLM) nên phải biết ai bấm.
        """
        ai = _ghi_duoc(request)
        if kiem is None:
            raise HTTPException(503, "Chưa bật bộ kiểm chứng (thiếu khoá Serper/GLM).")
        doan = (than.get("doan") or "").strip()
        if not doan:
            raise HTTPException(400, "Chưa chọn đoạn nào để kiểm.")
        dang = kho.ai_giu(tap, chuong)
        if dang and dang != ai:
            raise HTTPException(409, f"{dang} đang sửa chương này.")
        try:
            kq = kiem(doan)
        except Exception as exc:  # noqa: BLE001 — chữ của người viết phải còn nguyên
            raise HTTPException(502, f"Kiểm hỏng: {exc}") from exc
        d = kq.ra_dict()
        kho.luu_citation(tap, chuong, d, ai)
        return d

    @app.get("/api/tap/{tap}/{chuong}/citation")
    def ds_citation(tap: str, chuong: str):
        return kho.ds_citation(tap, chuong)

    @app.delete("/api/tap/{tap}/{chuong}/citation/{chu_ky}")
    def xoa_citation(tap: str, chuong: str, chu_ky: str, request: Request):
        _ghi_duoc(request)
        kho.xoa_citation(tap, chuong, chu_ky)
        return {"ok": True}

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
    """Đọc cài đặt MỖI LẦN dịch: đổi khoá/model trong tab Cài đặt là ăn ngay,
    không phải khởi động lại máy chủ."""

    def __init__(self, kho: Kho) -> None:
        self.kho = kho

    def dich(self, cau):
        from autoedit.kichban.dich import DichGLM

        return DichGLM(cai_dat=self.kho.doc_cai_dat(), viec="dich").dich(cau)


def _dich_mac_dinh(kho: Kho):
    return _Dich(kho)


def _kiem_mac_dinh(kho: Kho):
    """Bộ kiểm chứng thật: Serper tra -> Python tải -> GLM đọc -> Python soi lại.

    Bản chụp trang nằm CẠNH kho (`<thư mục db>/bangchung/`) — bằng chứng lúc kiểm,
    vì link chết sau 6-12 tháng là chuyện thường.
    """
    from functools import partial

    from autoedit.kichban.kiem import kiem_doan
    from autoedit.kichban.tra import LlmKiem, tai_thong_minh, tim_gop

    def _chay(doan, **kw):
        llm = LlmKiem(cai_dat=kho.doc_cai_dat())     # đọc cài đặt mỗi lượt kiểm
        return kiem_doan(doan, tim=tim_gop, tai=tai_thong_minh, llm=llm,
                         thu_muc_chup=kho.duong.parent / "bangchung", **kw)

    _ = partial
    return _chay


def _thu_llm(cai_dat: dict) -> dict:
    """Bấm Thử: gọi đúng cấu hình đang lưu bằng một câu ngắn nhất có thể."""
    from autoedit.kichban.dich import DichGLM

    m = DichGLM(cai_dat=cai_dat)
    if not m.key:
        raise RuntimeError("Chưa có khoá — dán vào ô Khoá rồi Lưu.")
    tra = m.dich(["Hello."])
    return {"model": m.model, "dia_chi": m.url, "tra_loi": (tra or [""])[0][:80]}


def tao_app_mac_dinh() -> FastAPI:
    """Chỗ bám cho uvicorn: `autoedit.kichban.app:tao_app_mac_dinh --factory`.

    FACTORY chứ không phải biến `APP` sẵn ở module: biến sẵn nghĩa là chỉ IMPORT
    thôi đã mở SQLite, và cả suite test sẽ đẻ ra DB thật trong thư mục nhà.
    """
    kho = _kho_mac_dinh()
    return tao_app(kho, dich=_dich_mac_dinh(kho), kiem=_kiem_mac_dinh(kho),
                   thu_llm=_thu_llm)


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
