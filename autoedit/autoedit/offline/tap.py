r"""MỘT TIMELINE CHO CẢ TẬP — QĐ17 (user chốt 17/09).

User: *"Vẫn với cách nhập liệu cũ (H, C, E) nhưng bây giờ tôi muốn hòa chung tất
cả vào 1 timeline thay vì chia như cũ. Việc chia chỉ thể hiện bằng cách đặt tên
khối."* Chốt hướng A: gộp thật ở tầng dữ liệu; **khoá sổ và giao hàng cho cả
tập**.

Ý CHÍNH: **tập là một project bình thường**.
  media/voice_master.wav  = voice các chương nối lại (mỗi chương cắt từ `offset`
                            của nó, ép về 48 kHz stereo — đo 17/09: master có cả
                            mono lẫn stereo)
  offline.json            = hợp đồng các chương nối lại: khối dịch theo trục
                            VOICE, miếng hình dịch theo trục TIMELINE, mỗi khối
                            mang `chuong`; `offset` = 0
Nhờ vậy 16 endpoint `/api/offline/{project_id}` và panel dùng lại nguyên: voice,
PUT, khoá sổ, Export (`_cat_voice` cắt từ master tập), trim, Add Shot, nhạc.

GHÉP THEO ĐOẠN, không nối vào đuôi: đo LI103 thật, C2 chạy lại 4 lần và C4 về
SAU CÙNG. Mỗi lần gộp: đoạn đã có trong tập GIỮ NGUYÊN (giữ chỉnh tay), chương
mới CHÈN đúng chỗ theo thứ tự H → C1.. → E, chương `lam_lai` THAY đúng đoạn đó.

Phân tích vẫn theo CHƯƠNG (luật 06/09 "không gộp voice cả tập" giữ nguyên) —
gộp là bước SAU phân tích.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DUOI_TAP = "-tap"          # project_id của tập: <mã tập>-tap (ổn định, không dấu giờ)
NHAN_TAP = "TAP"           # nhãn "chương" của project tập -> draft OFF_<tập>_TAP
SR, KENH = 48000, 2        # định dạng chung khi nối voice
# Dưới mức này là sai số làm tròn của ffprobe, KHÔNG phải lệch thật. Đo trên
# `kim048-tap` (18/09): banner kêu "E: file voice ngắn hơn khối 0.01s" — báo
# oan làm người dựng mất lòng tin rồi bỏ qua cả cảnh báo thật.
SAI_SO_S = 0.05
TEN_DOAN = "doan_{ma}.wav"  # voice từng chương đã cắt, nằm trong media/ của tập


def ten_project_tap(ma_tap: str) -> str:
    """`LI103` -> `li103-tap`. Khớp rào `[\\w.-]{1,80}` của `_pdir_offline`."""
    gon = re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9_-]", "_", str(ma_tap or ""))).strip("_")
    return (gon or "khong_ten").lower() + DUOI_TAP


def la_project_tap(ten: str) -> bool:
    return str(ten or "").endswith(DUOI_TAP)


def thu_tu_chuong(ma: str) -> int:
    """H = 0 · C<n> = n · E = cuối. Tên lạ xếp sau mọi chương C, trước E."""
    from autoedit.web.chapters import phan_tich_ten

    pt = phan_tich_ten(str(ma or ""))
    return pt[1] if pt else 500_000


# ───────────────────────────── hàm thuần ─────────────────────────────

def noi_hop_dong(doan: list[dict]) -> dict:
    """Nối hợp đồng các chương -> hợp đồng TẬP. Hàm thuần, không đọc ổ đĩa.

    `doan[i] = {"ma": "C1", "project_id": "...", "hd": <hợp đồng chương>,
                "dai_voice": <độ dài THẬT của file voice đã cắt từ offset>}`

    Bất biến quan trọng: `dai_voice` phải là độ dài đo được của đoạn voice, vì
    `_cat_voice` cắt master tập tại `v0` — dịch khối đúng bằng độ dài đoạn
    trước thì voice mới rơi đúng chỗ.

    Đuôi im lặng thừa cuối chương (cat_khoi bỏ đuôi < 1s) NHẬP vào thở của khối
    cuối + miếng cuối: file vẫn có đoạn đó, không nhập thì chương sau lệch hình.
    """
    from autoedit.offline import hinh as mhinh

    doan = sorted(doan, key=lambda d: thu_tu_chuong(d["ma"]))
    khoi_all: list[dict] = []
    hinh_all: list[dict] = []
    chuong_ds: list[dict] = []
    canh_bao: list[str] = []
    chu_the: list[str] = []
    V = 0.0                                   # trục VOICE: tổng voice các đoạn trước
    T = 0.0                                   # trục TIMELINE: voice + thở người thêm
    for d in doan:
        ma, hd = str(d["ma"]).upper(), d["hd"] or {}
        dai = float(d["dai_voice"])
        ks = [dict(k) for k in hd.get("khoi") or []]
        hs = [dict(h) for h in (hd.get("hinh") or mhinh.sinh_tu_khoi(ks))]
        if not ks:
            continue
        cuoi = ks[-1]
        du = round(dai - (float(cuoi["v1"]) + float(cuoi.get("tho") or 0)), 3)
        if du > 0.005:
            cuoi["tho"] = round(float(cuoi.get("tho") or 0) + du, 3)
            if hs:
                hs[-1]["dur"] = round(float(hs[-1]["dur"]) + du, 3)
        elif du < -SAI_SO_S:
            canh_bao.append(f"{ma}: file voice ngắn hơn khối {-du:.2f}s — kiểm master")
        n0 = len(khoi_all)
        for k in ks:
            k["v0"] = round(float(k["v0"]) + V, 3)
            k["v1"] = round(float(k["v1"]) + V, 3)
            k["ranh_mem"] = [round(float(x) + V, 3) for x in (k.get("ranh_mem") or [])]
            k["chuong"] = ma
            khoi_all.append(k)
        for h in hs:
            h["t0"] = round(float(h["t0"]) + T, 3)
            h["khoi_goc"] = int(h.get("khoi_goc") or 0) + n0
            hinh_all.append(h)
        chuong_ds.append({"ma": ma, "project_id": str(d.get("project_id") or ""),
                          "dai_voice": dai, "so_khoi": len(ks),
                          "trang_thai": hd.get("trang_thai") or "pha1"})
        canh_bao += [f"{ma}: {c}" for c in (hd.get("canh_bao") or [])]
        for x in hd.get("chu_the_tap") or []:
            if x not in chu_the:
                chu_the.append(x)
        V = round(V + dai, 3)
        T = round(mhinh.tong_dai(khoi_all), 3)

    dau = (doan[0]["hd"] if doan else {}) or {}
    now = datetime.now(timezone.utc).isoformat()
    hd = {
        "phien_ban": 0, "la_tap": True, "ngay": now,
        "ma_tap": dau.get("ma_tap") or "", "dia_danh": dau.get("dia_danh") or "",
        "ngach": dau.get("ngach") or "", "nhan_vat": dau.get("nhan_vat") or {},
        "nguoi_tao": "", "ngay_tao": now,
        "offset": 0.0, "tong_voice": round(V, 2),
        "avd_s": dau.get("avd_s") or 0,
        "dong_kiem": any((d["hd"] or {}).get("dong_kiem", True) for d in doan),
        "kieu_chay": dau.get("kieu_chay") or "",
        "framing": dau.get("framing") or {},
        "uu_tien_nguon": dau.get("uu_tien_nguon") or "",
        "chu_the_tap": chu_the,
        "trang_thai": "pha1",
        "chuong_ds": chuong_ds,
        "khoi": khoi_all, "hinh": hinh_all,
        "canh_bao": canh_bao,
    }
    if hinh_all:
        mhinh.khit_mep(hd)
    return hd


def tach_doan(hd_tap: dict) -> list[dict]:
    """Nghịch đảo của `noi_hop_dong`: hợp đồng tập -> các đoạn ở toạ độ CHƯƠNG
    (khối quy 0, miếng quy 0, khoi_goc quy 0). Để gộp lại mà giữ chỉnh tay."""
    ra: list[dict] = []
    khoi = hd_tap.get("khoi") or []
    hinh = hd_tap.get("hinh") or []
    cb = hd_tap.get("canh_bao") or []
    n0 = 0
    for c in hd_tap.get("chuong_ds") or []:
        ma, n = str(c["ma"]).upper(), int(c.get("so_khoi") or 0)
        ks = khoi[n0:n0 + n]
        if not ks:
            n0 += n
            continue
        V = float(ks[0]["v0"])
        hs = [h for h in hinh if n0 <= int(h.get("khoi_goc") or 0) < n0 + n]
        T = float(hs[0]["t0"]) if hs else 0.0
        ks2 = []
        for k in ks:
            k2 = {**k, "v0": round(float(k["v0"]) - V, 3),
                  "v1": round(float(k["v1"]) - V, 3),
                  "ranh_mem": [round(float(x) - V, 3) for x in (k.get("ranh_mem") or [])]}
            k2.pop("chuong", None)
            ks2.append(k2)
        hs2 = [{**h, "t0": round(float(h["t0"]) - T, 3),
                "khoi_goc": int(h.get("khoi_goc") or 0) - n0} for h in hs]
        dau = f"{ma}: "
        ra.append({"ma": ma, "project_id": str(c.get("project_id") or ""),
                   "dai_voice": float(c.get("dai_voice") or 0),
                   "hd": {"khoi": ks2, "hinh": hs2,
                          "trang_thai": c.get("trang_thai") or "pha1",
                          "canh_bao": [x[len(dau):] for x in cb if x.startswith(dau)]}})
        n0 += n
    return ra


# ───────────────────────────── ffmpeg ─────────────────────────────

def _dai_am(f: Path) -> float:
    from autoedit.project import ffprobe_duration

    return round(float(ffprobe_duration(f) or 0.0), 3)


def cat_doan_voice(master: Path, offset: float, dich: Path) -> float:
    """Cắt voice một chương từ `offset` tới hết, ép 48 kHz stereo PCM. Trả độ
    dài THẬT đo được (đây là `dai_voice` của đoạn)."""
    dich = Path(dich)
    dich.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0.0, float(offset)):.3f}",
                    "-i", str(master), "-ar", str(SR), "-ac", str(KENH),
                    "-c:a", "pcm_s16le", str(dich)], check=True, timeout=600)
    return _dai_am(dich)


def noi_voice(doan: list[Path], dich: Path) -> float:
    """Nối các đoạn (cùng định dạng) -> master tập. Trả độ dài."""
    dich = Path(dich)
    ds = dich.with_name("doan_noi.txt")
    ds.write_text("".join(f"file '{Path(p).resolve().as_posix()}'\n" for p in doan),
                  encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(ds), "-c", "copy", str(dich)], check=True, timeout=600)
    return _dai_am(dich)


# ───────────────────────────── gộp tập ─────────────────────────────

def _goc_script_cua(pdir: Path) -> str:
    try:
        p = json.loads((Path(pdir) / "project.json").read_text(encoding="utf-8"))
        return (p.get("inputs") or {}).get("original_script_path") or ""
    except Exception:  # noqa: BLE001
        return ""


def _goc_script_tap(projects_dir: Path, ma_tap: str, doan: list[dict]) -> str:
    r"""`...\LI103\RenderY\H\H.txt` -> `...\LI103\RenderY\TAP\TAP.txt`.

    `nhan_chuong_tu_script` đọc ra "TAP", `ma_tap_tu_duong_dan` đọc ra mã tập;
    draft xuất tên `OFF_<tập>_TAP`, giấy tờ giao vào `Compose Timeline\TAP`."""
    from autoedit.duong_dan import TEN_THU_MUC_CHUONG

    for d in doan:
        goc = _goc_script_cua(projects_dir / str(d.get("project_id") or "x"))
        if not goc:
            continue
        p = Path(goc.replace("\\", "/"))
        for cha in p.parents:
            if cha.name.lower() == TEN_THU_MUC_CHUONG:
                return str(cha / NHAN_TAP / f"{NHAN_TAP}.txt")
    return str(Path(projects_dir).parent / ma_tap / "RenderY" / NHAN_TAP / f"{NHAN_TAP}.txt")


def _ghi_project_json(d: Path, projects_dir: Path, ma_tap: str, doan: list[dict]) -> None:
    """project.json tối thiểu để `_read_project`, `tap-list`, `thay_mau` đọc
    được như mọi project; tham số dựng lấy theo chương đầu."""
    f = d / "project.json"
    cu: dict = {}
    if f.is_file():
        try:
            cu = json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            cu = {}
    inp_dau: dict = {}
    for x in doan:
        try:
            inp_dau = (json.loads((projects_dir / x["project_id"] / "project.json")
                                  .read_text(encoding="utf-8")).get("inputs") or {})
            break
        except Exception:  # noqa: BLE001
            continue
    inp = {k: inp_dau.get(k) for k in ("channel", "kenh_ref", "avd_phut", "dia_danh",
                                        "uu_tien_nguon", "kieu_chay", "phuong_an")}
    inp["original_script_path"] = _goc_script_tap(projects_dir, ma_tap, doan)
    inp["original_voice_path"] = ""
    now = datetime.now(timezone.utc).isoformat()
    f.write_text(json.dumps({
        "schema_version": 1, "project_id": d.name, "title": f"TẬP {ma_tap}",
        "created_at": cu.get("created_at") or now, "project_dir": str(d),
        "la_tap": True, "ma_tap": ma_tap,
        "chuong": [{"ma": x["ma"], "project_id": x.get("project_id") or ""} for x in doan],
        "inputs": inp, "stages": {}, "voice_master_path": "media\\voice_master.wav",
    }, ensure_ascii=False, indent=1), encoding="utf-8")


def gop_tap(projects_dir: Path, ma_tap: str, chuong: dict[str, Path],
            lam_lai=(), nguoi_tao: str = "", tab: str = "") -> dict:
    """Gộp (lại) tập. `chuong` = {mã chương: thư mục project đã phân tích}.

    - đoạn ĐÃ có trong tập: giữ nguyên (chỉnh tay đi theo), trừ mã trong `lam_lai`
    - chương chưa có: cắt voice + chèn đúng thứ tự
    - trạng thái (user chốt 17/09): chương pha 1 vào -> tập lùi pha 1; tập đã
      KHOÁ mà thêm chương -> mở lại pha 2; còn lại giữ nguyên
    - `nhac`, `noi_xuat`, `nguoi_tao`, `phien_ban` của tập giữ qua các lần gộp
    """
    from autoedit.offline import hinh as mhinh, runner as orun

    projects_dir = Path(projects_dir)
    lam_lai = {str(x).upper() for x in (lam_lai or ())}
    d = projects_dir / ten_project_tap(ma_tap)
    (d / "media").mkdir(parents=True, exist_ok=True)
    cu = orun.doc(d) if (d / orun.TEN_HOP_DONG).is_file() else None
    doan_cu = {x["ma"]: x for x in tach_doan(cu)} if cu else {}
    chon = {str(k).upper(): Path(v) for k, v in chuong.items()}

    giu: list[str] = []
    moi: list[str] = []
    thay: list[str] = []
    doan: list[dict] = []
    for ma, x in doan_cu.items():
        if ma in lam_lai and ma in chon:
            continue                                  # thay bằng bản mới bên dưới
        giu.append(ma)
        doan.append(x)
    for ma, pdir in sorted(chon.items(), key=lambda kv: thu_tu_chuong(kv[0])):
        if ma in doan_cu and ma not in lam_lai:
            continue
        hd_c = orun.doc(pdir)
        if hd_c is None:
            continue                                  # chương chưa phân tích
        master = pdir / "media" / "voice_master.wav"
        if not master.is_file():
            raise RuntimeError(f"chương {ma} thiếu media/voice_master.wav")
        dai = cat_doan_voice(master, float(hd_c.get("offset") or 0),
                             d / "media" / TEN_DOAN.format(ma=ma))
        doan.append({"ma": ma, "project_id": pdir.name, "hd": hd_c, "dai_voice": dai})
        (thay if ma in doan_cu else moi).append(ma)
    if not doan:
        raise RuntimeError("chưa có chương nào phân tích xong để gộp")
    doan.sort(key=lambda x: thu_tu_chuong(x["ma"]))

    mieng = [d / "media" / TEN_DOAN.format(ma=x["ma"]) for x in doan]
    thieu = [p.name for p in mieng if not p.is_file()]
    if thieu:
        raise RuntimeError(f"thiếu voice đoạn {', '.join(thieu)} — gộp lại với lam_lai")
    noi_voice(mieng, d / "media" / "voice_master.wav")

    hd = noi_hop_dong(doan)
    vao = {*moi, *thay}
    if cu is None:
        tt = "pha1" if any((x["hd"] or {}).get("trang_thai", "pha1") == "pha1"
                           for x in doan) else "pha2"
    elif any((x["hd"] or {}).get("trang_thai", "pha1") == "pha1"
             for x in doan if x["ma"] in vao):
        tt = "pha1"
    elif vao and cu.get("trang_thai") == "khoa":
        tt = "pha2"
    else:
        tt = cu.get("trang_thai") or "pha2"
    hd["trang_thai"] = tt
    if cu:
        for k in ("nhac", "noi_xuat", "nguoi_tao", "ngay_tao", "phien_ban"):
            if k in cu:
                hd[k] = cu[k]
    hd["nguoi_tao"] = hd.get("nguoi_tao") or nguoi_tao
    _ghi_project_json(d, projects_dir, ma_tap, doan)
    orun.luu(d, hd, tab=tab)
    return {"project_id": d.name, "moi": moi, "giu": giu, "thay": thay,
            "so_khoi": len(hd["khoi"]), "so_hinh": len(hd["hinh"]),
            "tong_s": mhinh.tong_dai(hd["khoi"]), "trang_thai": tt,
            "chuong": [x["ma"] for x in doan]}
