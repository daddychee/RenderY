#!/bin/bash
# Cổng PRODUCTION của RenderY — 9118, cổng team và CRM đang dùng.
#
# BẮT BUỘC có RENDERY_TRUST_PROXY=1. Đo thật 07/09: cờ này đặt ở cấp MÁY nên
# tiến trình nào không thừa kế (vd khởi động từ shell mở trước khi cờ được đặt)
# sẽ KHÔNG tin header X-Remote-User/X-Remote-Role của CRM -> mọi người thành vô
# danh, luật "người nộp tập mới được sửa sequence" và cổng owner/admin sai hết,
# mà KHÔNG có lỗi nào hiện ra. Đặt tường minh ở đây để không phụ thuộc thừa kế.
#
# Chạy TỪ CHECKOUT CHỨA CHÍNH FILE NÀY: hàng đợi `jobs.db` và 48 project (136GB)
# của team nằm trong checkout, không phải trong data root.
#
# Data root để MẶC ĐỊNH (~/AutoEdit) — kho Library + sổ tra thật của team.
# KHÔNG đặt AUTOEDIT_DATA_ROOT ở đây; muốn chạy thử thì dùng chay_dev.sh.

set -e
cd "$(dirname "$0")/autoedit"

export RENDERY_TRUST_PROXY=1
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

echo "RenderY PRODUCTION"
echo "  code      : $(pwd)"
echo "  data root : mặc định (~/AutoEdit)"
echo "  SSO       : RENDERY_TRUST_PROXY=1 (tin header CRM khi gọi từ loopback)"
echo "  port      : 9118"
echo

exec .venv/Scripts/python.exe -m uvicorn autoedit.web.server:app \
     --host 127.0.0.1 --port 9118
