#!/bin/bash
# Cổng DEV của RenderY — port 9120, dữ liệu RIÊNG.
#
# Vì sao tách dữ liệu: 07/09 một job test chạy trên kho chung đã đóng dấu geo
# "ecuador" lên 480 cảnh ref Afghanistan. Lần đó phát hiện kịp; lần sau chưa
# chắc. Bản dev có so_tra.db riêng (bản sao 12MB, đủ 12.802 clip để thử thật),
# ghi bẩn không ai chịu hậu quả.
#
# Dùng chung qua junction (chỉ nên ĐỌC): ban_sach/ 16GB, kenh/ 929MB.

set -e
cd "$(dirname "$0")/autoedit"

export AUTOEDIT_DATA_ROOT="C:/Users/Administrator/RenderY-dev"
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

echo "RenderY DEV"
echo "  code      : $(pwd)"
echo "  data root : $AUTOEDIT_DATA_ROOT"
echo "  port      : 9120   (production 9118 KHÔNG bị đụng)"
echo

exec .venv/Scripts/python.exe -m uvicorn autoedit.web.server:app \
     --host 127.0.0.1 --port 9120
