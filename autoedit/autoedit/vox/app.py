r"""Tool VOX — tầng web, CỔNG RIÊNG 9123 (user chốt 07/10/2026: tool riêng, UI riêng, treatment giữ nguyên).

Người dùng thả 1–3 ảnh, nhập giây TỪNG ảnh, chọn khung hình + STYLE (Collage art / Black Grid /
Non-Grid), CHỐT LỚP bằng khung (máy đề xuất, người kéo / xoá) -> một mp4. KHÔNG có ô camera: máy tự
lên nhịp + camera (`collage.bien_dao`). Dựng nặng ở thợ `python -m autoedit.collage.tho`.

Bước Lớp cần SAM: nạp LƯỜI trong tiến trình web lần đầu có người dùng tới (khoá một lượt một).

Danh tính + quyền do cổng 9000 tiêm (`X-Remote-User`, `X-Remote-Actions`), cùng khuôn treatment:
bật `VOX_TRUST_PROXY=1` thì chỉ tin header từ loopback (gateway proxy từ 127.0.0.1).

Chạy:  python -m uvicorn autoedit.vox.app:tao_app_mac_dinh --factory --port 9123
"""

from __future__ import annotations

import base64
import io
import json
import os
import threading
import time
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response

from autoedit.collage import psd as mpsd
from autoedit.collage.hang_doi import GOC_MAC_DINH, HangDoi, ma_moi

TRANG = Path(__file__).parent / "static" / "vox.html"
HANH_DONG_DUNG = "dung"
TOI_DA_ANH = 3
TOI_DA_LOP = 12
TOI_DA_MB = 30
TOI_DA_MB_PSD = 200                      # PSD nhiều layer nặng (PSD thật của team: 5–46 MB)
THO_CHET_SAU = 120                       # giây không thấy dấu sống của thợ -> cảnh báo

# CÙNG LUẬT với bộ dựng `collage.mau` (test đối chiếu); chép ra đây để web khỏi kéo torch khi không cần.
STYLE = {"collage": "Collage art", "black_grid": "Black Grid", "non_grid": "Non-Grid"}
KHUNG = {"16:9": "Ngang 16:9", "4:5": "Dọc 4:5", "9:16": "Đứng 9:16"}
_TI_LE = {"16:9": 16 / 9, "4:5": 4 / 5, "9:16": 9 / 16}
_MAU_LOP = [(255, 90, 60), (60, 200, 110), (70, 140, 255), (250, 200, 40), (210, 90, 230), (40, 210, 220)]


def _tin_header(request: Request) -> bool:
    if os.getenv("VOX_TRUST_PROXY", "").strip() != "1":
        return True
    host = (request.client.host if request.client else "") or ""
    return host in ("127.0.0.1", "::1", "localhost")


def _nguoi(request: Request) -> str:
    return (request.headers.get("x-remote-user") or "").strip() if _tin_header(request) else ""


def _hanh_dong(request: Request) -> set[str]:
    """App CHỈ TIN cờ gateway tính (luật cụm), không tự suy quyền theo level. Thiếu -> rỗng."""
    if not _tin_header(request):
        return set()
    return {x.strip() for x in (request.headers.get("x-remote-actions") or "").split(",") if x.strip()}


def _ai_dung(request: Request) -> str:
    ai = _nguoi(request)
    if not ai:
        raise HTTPException(401, "Chưa đăng nhập — mở tool qua cổng 9000.")
    if HANH_DONG_DUNG not in _hanh_dong(request):
        raise HTTPException(403, "Bạn chưa có quyền dựng video VOX — Owner cấp ở General › Permissions.")
    return ai


def _kiem_khung_lop(ds) -> list[list[float]]:
    ds = list(ds or [])
    if len(ds) > TOI_DA_LOP:
        raise ValueError(f"Mỗi ảnh tối đa {TOI_DA_LOP} lớp.")
    ra = []
    for k in ds:
        x0, y0, x1, y1 = (float(v) for v in k)
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1 and x1 - x0 >= 0.01 and y1 - y0 >= 0.01):
            raise ValueError("Khung lớp phải nằm trong ảnh và đủ lớn.")
        ra.append([round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)])
    return ra


def _kiem_cau_hinh(ch, so_anh: int) -> dict:
    try:
        ds = list(ch["anh"])
        if not 1 <= len(ds) <= TOI_DA_ANH:
            raise ValueError(f"Mỗi video 1–{TOI_DA_ANH} ảnh.")
        if len(ds) != so_anh:
            raise ValueError("Số ảnh gửi lên không khớp cấu hình.")
        sach = []
        for x in ds:
            giay = float(x["giay"])
            if not 0.5 <= giay <= 60:
                raise ValueError("Giây mỗi ảnh từ 0,5 đến 60.")
            muc = {"giay": round(giay, 2), "khung_lop": _kiem_khung_lop(x.get("khung_lop"))}
            try:
                psd_lop = sorted({int(i) for i in (x.get("psd_lop") or [])})
            except (TypeError, ValueError) as exc:
                raise ValueError("Khối PSD hỏng.") from exc
            if len(psd_lop) > TOI_DA_LOP or any(i < 0 for i in psd_lop):
                raise ValueError(f"Mỗi ảnh tối đa {TOI_DA_LOP} lớp.")
            if psd_lop:
                muc["psd_lop"] = psd_lop
            sach.append(muc)
        khung = ch.get("khung") or "16:9"
        if khung not in KHUNG:
            raise ValueError("Khung chỉ được 16:9, 4:5 hoặc 9:16.")
        style = ch.get("style") or "collage"
        if style not in STYLE:
            raise ValueError("Style chỉ được Collage art, Black Grid hoặc Non-Grid.")
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(400, str(exc) if isinstance(exc, ValueError) else "Cấu hình hỏng.") from exc
    return {"anh": sach, "khung": khung, "style": style}


def _doc_anh_gui(f: UploadFile) -> tuple[bytes, str]:
    from PIL import Image

    b = f.file.read(TOI_DA_MB_PSD * 1024 * 1024 + 1)
    if mpsd.la_psd(b):
        if len(b) > TOI_DA_MB_PSD * 1024 * 1024:
            raise HTTPException(400, f"PSD quá {TOI_DA_MB_PSD} MB.")
        try:
            mpsd.doc(b)
        except Exception as exc:  # noqa: BLE001 — mọi kiểu hỏng đều là "PSD không đọc được"
            raise HTTPException(400, f"'{f.filename}' là PSD hỏng hoặc không đọc được.") from exc
        return b, ".psd"
    if len(b) > TOI_DA_MB * 1024 * 1024:
        raise HTTPException(400, f"Ảnh quá {TOI_DA_MB} MB.")
    try:
        im = Image.open(io.BytesIO(b))
        im.verify()
        duoi = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[im.format]
    except Exception as exc:  # noqa: BLE001 — mọi kiểu hỏng đều là "không phải ảnh dùng được"
        raise HTTPException(400, f"'{f.filename}' không phải ảnh PNG/JPG/WEBP/PSD.") from exc
    return b, duoi


def _kiem_khoi_psd(b: bytes, duoi: str, muc: dict) -> None:
    """Đối chiếu khối chọn với CHÍNH file gửi lên: khối có thật, đang hiện, và còn ít nhất 1 khối làm nền."""
    chon = muc.get("psd_lop") or []
    if duoi != ".psd":
        if chon:
            raise HTTPException(400, "Chỉ ảnh PSD mới chọn khối theo layer.")
        return
    if muc["khung_lop"]:
        raise HTTPException(400, "Ảnh PSD chọn khối theo layer, không kéo khung.")
    lop = mpsd.doc(b)["lop"]
    for i in chon:
        if i >= len(lop):
            raise HTTPException(400, f"PSD không có khối số {i}.")
        if not lop[i]["hien"]:
            raise HTTPException(400, f"Khối '{lop[i]['ten']}' đang ẩn trong PSD.")
    if chon and not any(x["hien"] and x["chi_so"] not in chon for x in lop):
        raise HTTPException(400, "Phải chừa ít nhất 1 khối đang hiện làm nền.")


def _url_anh(im, kieu: str) -> str:
    b = io.BytesIO()
    im.save(b, kieu, **({"quality": 85} if kieu == "JPEG" else {}))
    return f"data:image/{kieu.lower()};base64," + base64.b64encode(b.getvalue()).decode()


def _anh_cat_khung(b: bytes, khung: str, rong_max: int = 1024) -> np.ndarray:
    """Ảnh -> cắt GIỮA đúng tỉ lệ khung hình (như `mau.doc_anh_khung` lúc dựng) -> thu nhỏ cho SAM."""
    from PIL import Image

    im = Image.open(io.BytesIO(b)).convert("RGB")
    w, h = im.size
    tl = _TI_LE[khung]
    if w / h > tl:
        nw = round(h * tl)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = round(w / tl)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    if im.size[0] > rong_max:
        im = im.resize((rong_max, round(im.size[1] * rong_max / im.size[0])), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def _anh_xem(rgb: np.ndarray, masks, khung_lop) -> str:
    """Ảnh xem: phần máy cắt tô màu từng lớp + viền khung + số thứ tự -> data URL JPEG."""
    from PIL import Image, ImageDraw

    a = rgb.copy()
    for i, m in enumerate(masks):
        a[m] = a[m] * 0.45 + np.float32(_MAU_LOP[i % len(_MAU_LOP)]) / 255 * 0.55
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    h, w = rgb.shape[:2]
    for i, (x0, y0, x1, y1) in enumerate(khung_lop):
        c = _MAU_LOP[i % len(_MAU_LOP)]
        d.rectangle((x0 * w, y0 * h, x1 * w, y1 * h), outline=c, width=max(2, w // 400))
        d.rectangle((x0 * w, y0 * h, x0 * w + 22, y0 * h + 20), fill=c)
        d.text((x0 * w + 6, y0 * h + 4), str(i + 1), fill=(0, 0, 0))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


class MayLop:
    """SAM + độ sâu thật, nạp LƯỜI (chỉ khi có người dùng bước Lớp)."""

    def __init__(self):
        self._sam = None

    def _s(self):
        from autoedit.collage import tach

        self._sam = self._sam or tach.TachSam()
        return self._sam

    def de_xuat(self, rgb) -> list[list[float]]:
        from autoedit.collage import lop, mau

        return lop.de_xuat_khung(rgb, mau.uoc_do_sau(rgb), self._s())

    def cat(self, rgb, khung_lop) -> list[np.ndarray]:
        from autoedit.collage import lop

        h, w = rgb.shape[:2]
        return lop.cat_theo_khung(rgb, [lop.khung_px(k, w, h) for k in khung_lop], self._s())


def tao_app(goc: Path | str | None = None, may_lop=None) -> FastAPI:
    goc = Path(goc or GOC_MAC_DINH)
    hd = HangDoi(goc / "hang_doi.db")
    may = may_lop or MayLop()
    khoa_may = threading.Lock()                              # một lượt SAM một lúc: CPU chung với thợ
    app = FastAPI(title="VOX")

    def _viec_cua(ma: str) -> dict:
        v = hd.doc(ma)
        if not v or not json.loads(v.get("chuoi") or "{}").get("anh"):
            raise HTTPException(404, "Không thấy việc.")
        return v

    @app.get("/", response_class=HTMLResponse)
    def trang():
        return HTMLResponse(TRANG.read_text(encoding="utf-8"), headers={"Cache-Control": "no-store"})

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/api/suc-khoe")
    def suc_khoe():
        mo_dun = []
        try:
            mo_dun.append({"ten": "hang_doi", "trang_thai": "ok", "chi_tiet": str(hd.duong)})
        except Exception as exc:  # noqa: BLE001
            mo_dun.append({"ten": "hang_doi", "trang_thai": "loi", "chi_tiet": str(exc)[:120]})
        song = goc / "tho.song"
        tuoi = time.time() - song.stat().st_mtime if song.exists() else None
        mo_dun.append({"ten": "tho", "trang_thai": "ok" if tuoi is not None and tuoi < THO_CHET_SAU else "canh_bao",
                       "chi_tiet": (f"thợ dựng sống ({tuoi:.0f} s trước)" if tuoi is not None and tuoi < THO_CHET_SAU
                                    else "thợ dựng chưa chạy — việc gửi lên sẽ nằm chờ")})
        muc = ("loi" if any(m["trang_thai"] == "loi" for m in mo_dun)
               else "canh_bao" if any(m["trang_thai"] == "canh_bao" for m in mo_dun) else "ok")
        return {"trang_thai": muc, "mo_dun": mo_dun}

    @app.get("/api/toi")
    def toi(request: Request):
        return {"nguoi": _nguoi(request), "dung_duoc": HANH_DONG_DUNG in _hanh_dong(request)}

    @app.get("/api/bang")
    def bang():
        return {"style": STYLE, "khung": KHUNG, "toi_da_anh": TOI_DA_ANH, "toi_da_lop": TOI_DA_LOP}

    @app.post("/api/lop")
    def lop(request: Request, anh: UploadFile = File(...), khung: str = Form("16:9"), khung_lop: str = Form(""),
            de_xuat: str = Form("")):
        """Bước LỚP: `de_xuat`=1 -> máy đề xuất khung; luôn trả ảnh xem phần máy CẮT trong từng khung
        (trên ảnh đã cắt đúng khung hình, như lúc dựng)."""
        _ai_dung(request)
        if khung not in KHUNG:
            raise HTTPException(400, "Khung chỉ được 16:9, 4:5 hoặc 9:16.")
        try:
            ds = _kiem_khung_lop(json.loads(khung_lop) if khung_lop else [])
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, str(exc) if isinstance(exc, ValueError) else "Khung lớp hỏng.") from exc
        b, _ = _doc_anh_gui(anh)
        rgb = _anh_cat_khung(b, khung)
        with khoa_may:
            if de_xuat:
                ds = _kiem_khung_lop(may.de_xuat(rgb))
            masks = may.cat(rgb, ds) if ds else []
        return {"khung_lop": ds, "xem": _anh_xem(rgb, masks, ds)}

    @app.post("/api/psd")
    def doc_psd(request: Request, anh: UploadFile = File(...)):
        """PSD -> khối cấp ngoài cùng (ảnh nhỏ từng khối) + ảnh xem cả canvas + khối máy tick sẵn."""
        _ai_dung(request)
        b, duoi = _doc_anh_gui(anh)
        if duoi != ".psd":
            raise HTTPException(400, "Không phải file PSD.")
        d = mpsd.doc(b)
        for x, im in zip(d["lop"], mpsd.anh_nho(b)):
            x["nho"] = _url_anh(im, "PNG") if im is not None else ""
        de_xuat = mpsd.de_xuat(d["lop"])
        return dict(d, de_xuat=de_xuat, con_trong_nen=mpsd.khoi_con_trong_nen(b, de_xuat) if de_xuat else [],
                    xem=_url_anh(mpsd.anh_xem(b), "JPEG"))

    @app.post("/api/viec")
    def gui(request: Request, anh: list[UploadFile] = File(...), cau_hinh: str = Form(...)):
        ai = _ai_dung(request)
        try:
            ch = _kiem_cau_hinh(json.loads(cau_hinh), len(anh))
        except json.JSONDecodeError as exc:
            raise HTTPException(400, "Cấu hình hỏng.") from exc
        doc = [_doc_anh_gui(f) for f in anh]
        for (b, duoi), x in zip(doc, ch["anh"]):
            _kiem_khoi_psd(b, duoi, x)
        ma = ma_moi()
        thu_muc = goc / "viec" / ma
        thu_muc.mkdir(parents=True, exist_ok=True)
        for i, ((b, duoi), x) in enumerate(zip(doc, ch["anh"])):
            p = thu_muc / f"anh_{i}{duoi}"
            p.write_bytes(b)
            x["anh"] = str(p)
        hd.tao(nguoi=ai, model="VOX-style", giay=sum(x["giay"] for x in ch["anh"]), cd="",
               anh=ch["anh"][0]["anh"], nhan="", id=ma, chuoi=ch)
        return {"id": ma}

    @app.get("/api/viec")
    def ds_viec(request: Request):
        ai = _nguoi(request)
        if not ai:
            raise HTTPException(401, "Chưa đăng nhập — mở tool qua cổng 9000.")
        ra = []
        for v in hd.cua(ai):
            ch = json.loads(v.get("chuoi") or "{}")
            if not ch.get("anh"):
                continue
            ra.append({"id": v["id"], "tao": v["tao"], "trang_thai": v["trang_thai"], "loi": v.get("loi") or "",
                       "thu_tu": hd.thu_tu(v["id"]) if v["trang_thai"] == "cho" else 0,
                       "giay": v["giay"], "khung": ch.get("khung") or "16:9", "style": STYLE.get(ch.get("style"), ""),
                       "anh": [{"giay": x["giay"], "so_lop": len(x.get("psd_lop") or x.get("khung_lop") or []),
                                "psd": str(x["anh"]).lower().endswith(".psd")} for x in ch["anh"]],
                       "bat_dau": v.get("bat_dau"), "xong_luc": v.get("xong_luc")})
        return {"viec": ra}

    @app.get("/api/viec/{ma}/video")
    def video(ma: str):
        v = _viec_cua(ma)
        if v["trang_thai"] != "xong" or not v.get("ra") or not Path(v["ra"]).exists():
            raise HTTPException(409, "Video chưa dựng xong.")
        return FileResponse(v["ra"], media_type="video/mp4", filename=f"vox_{ma}.mp4")

    @app.get("/api/viec/{ma}/anh/{i}")
    def anh_goc(ma: str, i: int):
        ds = json.loads(_viec_cua(ma)["chuoi"])["anh"]
        if not 0 <= i < len(ds):
            raise HTTPException(404, "Không có ảnh này.")
        if str(ds[i]["anh"]).lower().endswith(".psd"):          # trình duyệt không xem được PSD
            b = io.BytesIO()
            mpsd.anh_xem(ds[i]["anh"], rong_max=800).save(b, "JPEG", quality=85)
            return Response(b.getvalue(), media_type="image/jpeg")
        return FileResponse(ds[i]["anh"])

    return app


def tao_app_mac_dinh() -> FastAPI:
    return tao_app()
