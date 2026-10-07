r"""Thợ dựng Vox — tiến trình RIÊNG, lấy việc trong hàng đợi, dựng, ghi kết quả.

Chạy: `python -m autoedit.collage.tho` (Owner bật qua start-all — Claude không tự bật).
Bật lại sau khi chết: việc đang dở tự quay về hàng chờ (`khoi_phuc`).
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from autoedit.collage.hang_doi import HangDoi


def chay_mot(hd: HangDoi, dung) -> bool:
    """Làm MỘT việc. Trả False khi hàng trống. Lỗi -> việc `hong` kèm lý do (trang hiện lên)."""
    viec = hd.lay_tiep()
    if not viec:
        return False
    try:
        hd.xong(viec["id"], str(dung(viec)))
    except Exception as exc:  # noqa: BLE001 — mọi lỗi phải về tới người bấm
        hd.hong(viec["id"], f"{type(exc).__name__}: {exc}"[:400])
    return True


CONG_THO = 9124                     # chỉ để GIỮ CHỖ (PORTS.md): start-all biết thợ đã chạy, không bật trùng


def giu_cong(cong: int):
    """Mở cổng loopback giữ chỗ. Trả socket (giữ suốt đời thợ) hoặc None nếu đã có thợ khác giữ."""
    import socket

    s = socket.socket()
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):              # Windows: cấm tiến trình khác chiếm chung cổng
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        s.bind(("127.0.0.1", cong))
        s.listen(1)
    except OSError:
        s.close()
        return None
    return s


def danh_dau_song(goc) -> None:
    """Dấu sống mỗi vòng — trang sức khoẻ của tool VOX đọc để báo 'thợ chưa chạy' thay vì xanh giả."""
    p = Path(goc) / "tho.song"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(str(time.time()), encoding="utf-8")


def dung_mac_dinh(viec: dict, goc=None) -> Path:
    """Chọn mẫu theo MODEL của việc. Pop-up dùng bản tách lưu theo cảnh (`nhan` = tập/mã cảnh)."""
    import json

    from autoedit.collage import mau
    from autoedit.collage.hang_doi import GOC_MAC_DINH
    from autoedit.collage.kho_tach import KhoTach

    ra = Path(viec["anh"]).parent / "ra.mp4"
    chuoi = json.loads(viec.get("chuoi") or "{}")
    if chuoi.get("anh"):                                       # tool VOX riêng: chuỗi ảnh
        W, H = mau.KHUNG[chuoi.get("khung") or "16:9"]          # việc trước 07/10 không có khung
        mau.dung_chuoi(chuoi["anh"], chuoi.get("noi") or [], ra, KhoTach(goc or GOC_MAC_DINH), W=W, H=H)
    elif str(viec.get("model") or "").startswith("VOX-popup"):
        mau.dung_popup(Path(viec["anh"]), float(viec["giay"]), viec.get("cd") or "", ra, viec["nhan"],
                       KhoTach(goc or GOC_MAC_DINH), diem=json.loads(viec.get("diem") or "[]") or None)
    else:
        mau.dung_video(Path(viec["anh"]), float(viec["giay"]), viec.get("cd") or "", ra)
    return ra


def main() -> None:
    from autoedit.collage.hang_doi import GOC_MAC_DINH

    p = argparse.ArgumentParser(description="Thợ dựng video Vox")
    p.add_argument("--goc", default=str(GOC_MAC_DINH))
    p.add_argument("--mot-lan", action="store_true", help="làm hết hàng rồi thoát (thử)")
    p.add_argument("--cong", type=int, default=CONG_THO, help="cổng giữ chỗ; 0 = không giữ (thử)")
    a = p.parse_args()
    giu = giu_cong(a.cong) if a.cong else True
    if giu is None:
        print(f"tho: đã có thợ giữ cổng {a.cong} — thoát, không bật trùng", flush=True)
        return
    hd = HangDoi(Path(a.goc) / "hang_doi.db")
    print(f"tho: khôi phục {hd.khoi_phuc()} việc dở · hàng đợi {hd.duong}", flush=True)
    import threading

    def _nhip():                                             # luồng riêng: đang dựng việc dài vẫn báo sống
        while True:
            danh_dau_song(a.goc)
            time.sleep(30)
    threading.Thread(target=_nhip, daemon=True).start()
    while True:
        t0 = time.time()
        if chay_mot(hd, lambda v: dung_mac_dinh(v, goc=a.goc)):
            print(f"tho: xong 1 việc trong {time.time() - t0:.0f} s", flush=True)
            continue
        if a.mot_lan:
            return
        time.sleep(2)


if __name__ == "__main__":
    main()
