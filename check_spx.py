#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPX Waybill Auditor - CLI
Command-line interface for checking SPX Express waybill address discrepancies.

Usage:
    python3 check_spx.py <waybill.pdf>
    python3 check_spx.py <waybill.pdf> --csv output.csv
    python3 check_spx.py <waybill.pdf> --all
"""

import sys
import os
import argparse
import csv
from spx_checker import check_pdf


def print_table(mismatches, total, matches, show_all=False, all_results=None):
    CYAN = '\033[96m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

    if not mismatches and not show_all:
        print(f"\n{GREEN}{BOLD}✔ Không phát hiện đơn nào bị lệch tên hành chính.{RESET}")
        print(f"Đã check {total} đơn, {matches} đơn khớp, 0 đơn lệch.\n")
        return

    items_to_display = all_results if show_all else mismatches
    title = f"TẤT CẢ ĐƠN HÀNG ({len(items_to_display)} đơn)" if show_all else f"DANH SÁCH ĐƠN LỆCH ({len(items_to_display)} đơn)"

    print(f"\n{BOLD}{title}:{RESET}")
    print("=" * 115)
    header = f"{'STT':^5} | {'Mã vận đơn':^18} | {'Người nhận':^18} | {'Trạng thái / Lệch ở đâu':^35}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * 115)

    for i, m in enumerate(items_to_display, 1):
        stt_str = f"{i:^5}"
        code_str = f"{m['code']:<18}"
        name_str = f"{m['recipient'][:18]:<18}"
        if m['is_match']:
            status_str = f"{GREEN}Khớp{RESET}"
        else:
            status_str = f"{RED}{m['reason']:<35}{RESET}"
        print(f"{stt_str} | {CYAN}{code_str}{RESET} | {name_str} | {status_str}")
        if not m['is_match'] or show_all:
            print(f"   ↳ {YELLOW}Khách ghi:{RESET} {m['customer_address']}")
            print(f"   ↳ {GREEN}Hệ thống :{RESET} {m['system_address']}")
        print("-" * 115)

    print(f"\n{BOLD}Tổng kết:{RESET} Đã check {total} đơn, {matches} đơn khớp, {RED if mismatches else GREEN}{BOLD}{len(mismatches)} đơn lệch{RESET}.\n")


def main():
    parser = argparse.ArgumentParser(
        description="SPX Waybill Auditor: Offline shipping label address verification tool (0 AI tokens)."
    )
    parser.add_argument("pdf_path", nargs="?", help="Đường dẫn tới file PDF vận đơn SPX")
    parser.add_argument("--csv", help="Đường dẫn file CSV để xuất kết quả đơn lệch", default=None)
    parser.add_argument("--all", action="store_true", help="Hiển thị tất cả đơn hàng (bao gồm cả đơn khớp)")

    args = parser.parse_args()

    pdf_path = args.pdf_path
    if not pdf_path:
        # Tự động tìm file PDF trong thư mục hiện tại nếu không truyền tham số
        pdfs = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
        if pdfs:
            pdf_path = pdfs[0]
            print(f"[*] Tự động chọn file PDF trong thư mục: {pdf_path}")
        else:
            parser.print_help()
            sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"Lỗi: Không tìm thấy file '{pdf_path}'")
        sys.exit(1)

    print(f"Đang kiểm tra: {pdf_path}...")
    results = check_pdf(pdf_path)

    mismatches = [r for r in results if not r['is_match']]
    matches = len(results) - len(mismatches)

    print_table(mismatches, len(results), matches, show_all=args.all, all_results=results)

    if args.csv:
        with open(args.csv, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['STT', 'Mã vận đơn', 'Người nhận', 'Địa chỉ khách ghi', 'Địa chỉ hệ thống', 'Lệch ở đâu'])
            for i, m in enumerate(mismatches, 1):
                writer.writerow([i, m['code'], m['recipient'], m['customer_address'], m['system_address'], m['reason']])
        print(f"✔ Đã xuất kết quả đơn lệch ra file: {args.csv}")


if __name__ == '__main__':
    main()
