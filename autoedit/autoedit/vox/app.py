r"""Tool VOX — tầng web, CỔNG RIÊNG 9123 (user chốt 07/10/2026: tool riêng, UI riêng, treatment giữ nguyên).

Người dùng thả 1–3 ảnh, nhập giây TỪNG ảnh, chọn mẫu + camera + cú nối -> một mp4. Web CHỈ xếp
hàng (`collage.hang_doi`) và đọc kết quả; dựng nặng ở thợ `python -m autoedit.collage.tho`
(tiến trình riêng) — web không kéo torch.

Danh tính + quyền do cổng 9000 tiêm (`X-Remote-User`, `X-Remote-Actions`), cùng khuôn treatment:
bật `VOX_TRUST_PROXY=1` thì chỉ tin header từ loopback (gateway proxy từ 127.0.0.1).

Chạy:  python -m uvicorn autoedit.vox.app:tao_app_mac_dinh --factory --port 9123
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import time
from pathlib import Path

from fastapi import Body, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from autoedit.collage.hang_doi import GOC_MAC_DINH, HangDoi, ma_moi
from autoedit.collage.kho_tach import KhoTach

TRANG = Path(__file__).parent / "static" / "vox.html"
HANH_DONG_DUNG = "dung"
TOI_DA_ANH = 3
TOI_DA_MB = 30
THO_CHET_SAU = 120                       # giây không thấy dấu sống của thợ -> cảnh báo

# Bảng mã — CÙNG LUẬT với bộ dựng `collage.mau` (test đối chiếu); chép ra đây để web khỏi kéo torch.
MAU = {"chieu_sau": "Chiều sâu", "popup": "Pop-up 2.5D"}
NOI = {"lia_len": "Lia lên", "lia_ngang": "Lia ngang", "cat": "Cắt thẳng"}
KHUNG = {"16:9": "Ngang 16:9", "4:5": "Dọc 4:5", "9:16": "Đứng 9:16"}
CAMERA = {"": "Tự nhiên (thở nhẹ)", "push_in": "Đẩy vào", "pull_out": "Lùi ra", "tilt_up": "Ngước lên",
          "tilt_down": "Cúi xuống", "truck_left": "Trượt trái", "truck_right": "Trượt phải",
          "track": "Bám theo", "pan_left": "Lia trái", "pan_right": "Lia phải", "arc": "Vòng cung",
          "orbit": "Quay quanh", "crash_zoom": "Phóng giật", "whip_pan": "Lia vút", "static": "Đứng yên"}
CO = {"khong_tach_duoc_vat": "Không tách được vật — đang dựng như Chiều sâu",
      "diem_sam_thap": "Máy không chắc đường cắt", "mep_yeu": "Mép vật lẫn với nền"}


def nhan_anh(du_lieu: bytes) -> str:
    """Nhãn bản tách theo ẢNH — khớp `collage.mau.nhan_anh` (sha1 nội dung, 20 ký tự)."""
    return "anh/" + hashlib.sha1(du_lieu).hexdigest()[:20]


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


def _kiem_cau_hinh(ch, so_anh: int) -> dict:
    try:
        ds, noi = list(ch["anh"]), list(ch.get("noi") or [])
        if not 1 <= len(ds) <= TOI_DA_ANH:
            raise ValueError(f"Mỗi video 1–{TOI_DA_ANH} ảnh.")
        if len(ds) != so_anh:
            raise ValueError("Số ảnh gửi lên không khớp cấu hình.")
        if len(noi) != len(ds) - 1 or any(n not in NOI for n in noi):
            raise ValueError("Mỗi chỗ nối giữa hai ảnh phải chọn một cú nối.")
        sach = []
        for x in ds:
            giay = float(x["giay"])
            if not 0.5 <= giay <= 60:
                raise ValueError("Giây mỗi ảnh từ 0,5 đến 60.")
            if x.get("mau") not in MAU or (x.get("cd") or "") not in CAMERA:
                raise ValueError("Mẫu hoặc camera không có trong bảng.")
            sach.append({"giay": round(giay, 2), "mau": x["mau"], "cd": x.get("cd") or ""})
        khung = ch.get("khung") or "16:9"
        if khung not in KHUNG:
            raise ValueError("Khung chỉ được 16:9, 4:5 hoặc 9:16.")
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(400, str(exc) if isinstance(exc, ValueError) else "Cấu hình hỏng.") from exc
    return {"anh": sach, "noi": noi, "khung": khung}


def _doc_anh_gui(f: UploadFile) -> tuple[bytes, str]:
    from PIL import Image

    b = f.file.read(TOI_DA_MB * 1024 * 1024 + 1)
    if len(b) > TOI_DA_MB * 1024 * 1024:
        raise HTTPException(400, f"Ảnh quá {TOI_DA_MB} MB.")
    try:
        im = Image.open(io.BytesIO(b))
        im.verify()
        duoi = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[im.format]
    except Exception as exc:  # noqa: BLE001 — mọi kiểu hỏng đều là "không phải ảnh dùng được"
        raise HTTPException(400, f"'{f.filename}' không phải ảnh PNG/JPG/WEBP.") from exc
    return b, duoi


def tao_app(goc: Path | str | None = None) -> FastAPI:
    goc = Path(goc or GOC_MAC_DINH)
    hd = HangDoi(goc / "hang_doi.db")
    kt = KhoTach(goc)
    app = FastAPI(title="VOX")

    def _viec_cua(ma: str, request: Request) -> dict:
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
        return {"mau": MAU, "noi": NOI, "camera": CAMERA, "co": CO, "khung": KHUNG, "toi_da_anh": TOI_DA_ANH}

    @app.post("/api/viec")
    def gui(request: Request, anh: list[UploadFile] = File(...), cau_hinh: str = Form(...)):
        ai = _ai_dung(request)
        try:
            ch = _kiem_cau_hinh(json.loads(cau_hinh), len(anh))
        except json.JSONDecodeError as exc:
            raise HTTPException(400, "Cấu hình hỏng.") from exc
        doc = [_doc_anh_gui(f) for f in anh]
        ma = ma_moi()
        thu_muc = goc / "viec" / ma
        thu_muc.mkdir(parents=True, exist_ok=True)
        for i, ((b, duoi), x) in enumerate(zip(doc, ch["anh"])):
            p = thu_muc / f"anh_{i}{duoi}"
            p.write_bytes(b)
            x.update(anh=str(p), nhan=nhan_anh(b))
        hd.tao(nguoi=ai, model="VOX-chuoi", giay=sum(x["giay"] for x in ch["anh"]), cd="",
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
            anh = []
            for x in ch["anh"]:
                tt = kt.thong_tin(x["nhan"]) if x["mau"] == "popup" else None
                anh.append({"giay": x["giay"], "mau": x["mau"], "cd": x["cd"],
                            "co": (tt or {}).get("co", []), "co_tach": tt is not None})
            ra.append({"id": v["id"], "tao": v["tao"], "trang_thai": v["trang_thai"], "loi": v.get("loi") or "",
                       "thu_tu": hd.thu_tu(v["id"]) if v["trang_thai"] == "cho" else 0,
                       "giay": v["giay"], "anh": anh, "noi": ch.get("noi") or [], "khung": ch.get("khung") or "16:9",
                       "bat_dau": v.get("bat_dau"), "xong_luc": v.get("xong_luc")})
        return {"viec": ra}

    @app.get("/api/viec/{ma}/video")
    def video(ma: str, request: Request):
        v = _viec_cua(ma, request)
        if v["trang_thai"] != "xong" or not v.get("ra") or not Path(v["ra"]).exists():
            raise HTTPException(409, "Video chưa dựng xong.")
        return FileResponse(v["ra"], media_type="video/mp4", filename=f"vox_{ma}.mp4")

    def _anh_thu(v: dict, i: int) -> dict:
        ds = json.loads(v["chuoi"])["anh"]
        if not 0 <= i < len(ds):
            raise HTTPException(404, "Không có ảnh này.")
        return ds[i]

    @app.get("/api/viec/{ma}/anh/{i}")
    def anh_goc(ma: str, i: int, request: Request):
        return FileResponse(_anh_thu(_viec_cua(ma, request), i)["anh"])

    @app.get("/api/viec/{ma}/tach/{i}")
    def doc_tach(ma: str, i: int, request: Request):
        x = _anh_thu(_viec_cua(ma, request), i)
        tt = kt.thong_tin(x["nhan"]) if x["mau"] == "popup" else None
        if not tt:
            raise HTTPException(404, "Ảnh này chưa có bản tách (chưa dựng xong hoặc là Chiều sâu).")
        return {"co": tt["co"], "diem": tt["diem"], "so_vat": tt["so_vat"]}

    @app.get("/api/viec/{ma}/tach/{i}/xem")
    def xem_tach(ma: str, i: int, request: Request):
        x = _anh_thu(_viec_cua(ma, request), i)
        tt = kt.thong_tin(x["nhan"])
        if not tt or not Path(tt["xem"]).exists():
            raise HTTPException(404, "Chưa có ảnh xem bản tách.")
        return FileResponse(tt["xem"], headers={"Cache-Control": "no-store"})

    @app.post("/api/viec/{ma}/tach/{i}")
    def tach_lai(ma: str, i: int, request: Request, than: dict = Body(default={})):
        """Bấm điểm lên ảnh Pop-up (tỉ lệ 0..1; dau 1 = thuộc vật, 0 = nền) -> dựng lại CẢ chuỗi
        thành việc mới; ảnh khác dùng lại bản tách đã lưu nên không tách lại."""
        ai = _ai_dung(request)
        v = _viec_cua(ma, request)
        if v["nguoi"] != ai:
            raise HTTPException(403, "Chỉ người gửi việc mới tách lại được.")
        x = _anh_thu(v, i)
        if x["mau"] != "popup":
            raise HTTPException(400, "Tách lại chỉ dùng cho ảnh chọn mẫu Pop-up 2.5D.")
        try:
            diem = [{"x": float(d["x"]), "y": float(d["y"]), "dau": int(d["dau"])} for d in than.get("diem") or []]
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(400, "Điểm bấm hỏng.") from exc
        if not 1 <= len(diem) <= 20 or not all(0 <= d["x"] <= 1 and 0 <= d["y"] <= 1 and d["dau"] in (0, 1)
                                                for d in diem):
            raise HTTPException(400, "Cần 1–20 điểm nằm trong ảnh.")
        if not any(d["dau"] == 1 for d in diem):
            raise HTTPException(400, "Cần ít nhất một điểm chuột TRÁI vào vật.")
        ch = json.loads(v["chuoi"])
        for j, y in enumerate(ch["anh"]):
            y.pop("diem", None)
            if j == i:
                y["diem"] = diem
        moi = ma_moi()
        thu_muc = goc / "viec" / moi
        thu_muc.mkdir(parents=True, exist_ok=True)
        for y in ch["anh"]:                                  # chép ảnh: việc cũ bị dọn không làm hỏng việc mới
            p = thu_muc / Path(y["anh"]).name
            shutil.copyfile(y["anh"], p)
            y["anh"] = str(p)
        hd.tao(nguoi=ai, model="VOX-chuoi", giay=v["giay"], cd="", anh=ch["anh"][0]["anh"], nhan="",
               id=moi, chuoi=ch)
        return {"id": moi}

    return app


def tao_app_mac_dinh() -> FastAPI:
    return tao_app()
