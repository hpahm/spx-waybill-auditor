#!/usr/bin/env bash
# Khởi chạy tool đối soát vận đơn SPX

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -n "$1" ]; then
    # Nếu có truyền file PDF, chạy ngay qua giao diện dòng lệnh CLI
    python3 "$SCRIPT_DIR/check_spx.py" "$@"
else
    # Nếu không truyền tham số, khởi chạy giao diện Web trực quan
    echo "Khởi động giao diện Web trực quan..."
    python3 "$SCRIPT_DIR/app.py"
fi
