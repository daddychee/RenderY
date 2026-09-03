# -*- coding: utf-8 -*-
"""Sổ gọi nền (03/09) — mỗi call LLM của rendery ghi MỘT dòng về gateway
loopback POST /api/so-goi (khuôn radary/so_goi_nen.py).

VÌ SAO CÓ FILE NÀY — sự cố 03/09: job dựng chết hàng loạt vì GLM hết tiền
(mã 1113), nhân sự phải nhắn tay qua chat báo "tool đang lỗi". Hệ giám sát
không hề biết, vì rendery là app DUY NHẤT gọi LLM mà chưa ghi sổ gọi: tab
Quota & Calls thấy 0 call LLM trong khi thực tế đang gọi và hỏng hàng chục lần.
Ghi sổ rồi thì lỗi tiền/quota hiện ngay trên khối "nhịp gọi" cùng mọi app khác,
không phải chờ người báo.

Sổ chết KHÔNG được làm hỏng việc thật → nuốt mọi lỗi, timeout ngắn.
Chỉ gửi ĐUÔI 4 của khóa, không bao giờ gửi khóa trần.
"""
import json
import os
import urllib.request


def ghi(dich_vu, duoi="", units=0, ok=True, ma_loi="", model="", viec="",
        ms=None):
    try:
        goc = os.environ.get("GATEWAY_URL", "http://127.0.0.1:9000")
        body = json.dumps({"app": "rendery", "dich_vu": dich_vu, "duoi": duoi,
                           "units": units, "ok": ok, "ma_loi": ma_loi,
                           "model": model, "viec": viec, "ms": ms}).encode()
        req = urllib.request.Request(goc + "/api/so-goi", data=body,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=2).close()
    except Exception:  # noqa: BLE001
        pass
