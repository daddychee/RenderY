r"""CÂY THƯỚC — đo hợp đồng offline.json ra SỐ.

Vì sao có file này (METHODOLOGY BH3): tới 07/09, kênh phát hiện lỗi chủ đạo vẫn
là mắt user trong lúc vận hành — 11 commit ghi "user bắt/user báo", riêng 06/09
có 85 commit vá liên tiếp. Luật cứng #4 nói "Python đo" nhưng chưa có công cụ
nào đo ĐẦU RA. Ba thứ hỏng suốt ngày 07/09 (Framing không tới nơi, AVD vô hiệu,
nhịp chạy theo hơi thở người đọc) đều lộ ngay nếu chạy lệnh này một lần.

Hàm thuần: nhận dict hợp đồng, trả dict số. Không đọc file, không in.
"""

from __future__ import annotations

import statistics as st


def _phan_vi(ds: list[float], p: float) -> float:
    if not ds:
        return 0.0
    xs = sorted(ds)
    return xs[min(len(xs) - 1, max(0, int(len(xs) * p) - 1))]


def do(hd: dict) -> dict:
    """1 hợp đồng -> số đo. Khoá nào không đo được thì 0/rỗng, không ném lỗi."""
    khoi = hd.get("khoi") or []
    hinh = hd.get("hinh") or []
    fr = hd.get("framing") or {}
    than = float(fr.get("than") or 0)

    dai = [round(float(k.get("v1", 0)) - float(k.get("v0", 0)), 2) for k in khoi]
    dai_hinh = [round(float(h.get("dur") or 0), 2) for h in hinh]
    co_uv = sum(1 for k in khoi if k.get("uv"))
    n = len(khoi) or 1

    # nguồn của clip ĐANG ĐƯỢC CHỌN ở mỗi khối (sổ nguồn gốc thu nhỏ)
    nguon: dict[str, int] = {}
    for k in khoi:
        uv, i = k.get("uv") or [], k.get("chon", -1)
        if 0 <= i < len(uv):
            g = (uv[i] or {}).get("nguon") or "?"
            nguon[g] = nguon.get(g, 0) + 1

    return {
        "ma_tap": hd.get("ma_tap") or "",
        "trang_thai": hd.get("trang_thai") or "",
        "dong_kiem": bool(hd.get("dong_kiem")),
        "avd_s": float(hd.get("avd_s") or 0),
        "dia_danh": hd.get("dia_danh") or "",
        "uu_tien_nguon": hd.get("uu_tien_nguon") or "",
        "framing_ten": fr.get("ten") or "",
        "framing_than": than,
        "so_khoi": len(khoi),
        "so_hinh": len(hinh),
        "tong_s": float(hd.get("tong_voice") or 0),
        "khoi_median": round(st.median(dai), 2) if dai else 0.0,
        "khoi_p90": round(_phan_vi(dai, 0.9), 2),
        "khoi_max": round(max(dai), 2) if dai else 0.0,
        "hinh_median": round(st.median(dai_hinh), 2) if dai_hinh else 0.0,
        "hinh_max": round(max(dai_hinh), 2) if dai_hinh else 0.0,
        # cổng của bậc 3: khối dài hơn 1,6× chuẩn kênh là chỗ nhịp bị ì
        "khoi_qua_dai": sum(1 for x in dai if than > 0 and x > than * 1.6),
        # cổng của QĐ5: Auto chỉ tự khoá sổ khi khay phủ >= 50% khối
        "co_uv": co_uv,
        "ty_le_co_uv": round(co_uv / n, 3),
        "truu_tuong": sum(1 for k in khoi if k.get("truu_tuong")),
        "nguoi_sua": sum(1 for h in hinh if h.get("nguoi_sua")),
        "nguon": dict(sorted(nguon.items(), key=lambda x: -x[1])),
        "canh_bao": list(hd.get("canh_bao") or []),
    }


def dong_bao_cao(s: dict, ten: str = "") -> list[str]:
    """Số đo -> vài dòng đọc được. Dấu ✗/⚠ chỉ đặt ở chỗ ĐO ĐƯỢC là sai."""
    fr = (f"{s['framing_ten']} · thân {s['framing_than']:.2f}s"
          if s["framing_ten"] else "✗ KHÔNG CÓ")
    avd = f"{s['avd_s'] / 60:.1f} phút" if s["avd_s"] > 0 else "✗ chưa khai"
    lech = ""
    if s["framing_than"] > 0 and s["hinh_median"] > 0:
        d = s["hinh_median"] / s["framing_than"] - 1
        lech = f"  (lệch chuẩn kênh {d:+.0%})"
    ra = [
        f"{ten or s['ma_tap'] or '?'} · {s['trang_thai']} · "
        f"{'ĐỒNG KIỂM' if s['dong_kiem'] else 'AUTO'}",
        f"  Framing   : {fr}",
        f"  AVD       : {avd}   địa danh: {s['dia_danh'] or '✗ trống'}   "
        f"ưu tiên: {s['uu_tien_nguon'] or '✗ trống'}",
        f"  Khối      : {s['so_khoi']} · median {s['khoi_median']}s · "
        f"p90 {s['khoi_p90']}s · dài nhất {s['khoi_max']}s"
        + (f" · {s['khoi_qua_dai']} khối > 1,6× chuẩn kênh"
           if s["framing_than"] > 0 else ""),
        f"  Miếng hình: {s['so_hinh']} · median {s['hinh_median']}s · "
        f"dài nhất {s['hinh_max']}s{lech}",
        f"  Có ứng viên: {s['co_uv']}/{s['so_khoi']} ({s['ty_le_co_uv']:.0%})"
        + ("  ⚠ dưới 50% — Auto sẽ KHÔNG tự khoá sổ"
           if s["ty_le_co_uv"] < 0.5 else ""),
        f"  Nguồn đang chọn: "
        + (" · ".join(f"{k} {v}" for k, v in s["nguon"].items()) or "chưa chọn"),
    ]
    ra += [f"  ⚠ {c}" for c in s["canh_bao"]]
    return ra
