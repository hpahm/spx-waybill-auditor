#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPX Waybill Auditor - Core Engine
High-performance, offline address verification engine for SPX Express shipping labels.
Zero AI token cost, pure deterministic matching with administrative normalization.
"""

import os
import re
import subprocess
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Tuple, Generator, Any

# 63 provinces and major aliases across Vietnam
PROVINCES = [
    'Bà Rịa - Vũng Tàu', 'Bà Rịa Vũng Tàu', 'Vũng Tàu',
    'Thừa Thiên Huế', 'Huế',
    'TP. Hồ Chí Minh', 'TP Hồ Chí Minh', 'Thành phố Hồ Chí Minh', 'Hồ Chí Minh', 'TP.HCM', 'TPHCM', 'Sài Gòn',
    'Hà Nội', 'Hải Phòng', 'Đà Nẵng', 'Cần Thơ',
    'An Giang', 'Bắc Giang', 'Bắc Kạn', 'Bạc Liêu',
    'Bắc Ninh', 'Bến Tre', 'Bình Định', 'Bình Dương', 'Bình Phước',
    'Bình Thuận', 'Cà Mau', 'Cao Bằng', 'Đắk Lắk', 'Đắk Nông',
    'Điện Biên', 'Đồng Nai', 'Đồng Tháp', 'Gia Lai', 'Hà Giang',
    'Hà Nam', 'Hà Tĩnh', 'Hải Dương', 'Hậu Giang', 'Hòa Bình',
    'Hưng Yên', 'Khánh Hòa', 'Kiên Giang', 'Kon Tum', 'Lai Châu',
    'Lâm Đồng', 'Lạng Sơn', 'Lào Cai', 'Long An', 'Nam Định',
    'Nghệ An', 'Ninh Bình', 'Ninh Thuận', 'Phú Thọ', 'Phú Yên',
    'Quảng Bình', 'Quảng Nam', 'Quảng Ngãi', 'Quảng Ninh', 'Quảng Trị',
    'Sóc Trăng', 'Sơn La', 'Tây Ninh', 'Thái Bình', 'Thái Nguyên',
    'Thanh Hóa', 'Tiền Giang', 'Trà Vinh',
    'Tuyên Quang', 'Vĩnh Long', 'Vĩnh Phúc', 'Yên Bái'
]
ADMIN_PREFIX_REGEX = re.compile(
    r'^(?:Phường|P\.?|Xã|X\.?|Thị\s*trấn|Thị\s*Trấn|TT\.?|Quận|Q\.?|Huyện|H\.?|Thị\s*xã|Thị\s*Xã|TX\.?|Thành\s*phố|Thành\s*Phố|TP\.?|Tỉnh)\s*',
    re.IGNORECASE
)

WARD_PATTERN = re.compile(
    r'(?:\bPhường|\bP\.?|\bThị\s*trấn|\bTT|(?<!thị\s)(?<!thị)\bxã|(?<!thị\s)(?<!thị)\bx\.)\s+([^,]+)',
    re.IGNORECASE
)

DISTRICT_PATTERN = re.compile(
    r'\b(Quận|Q\.?|Huyện|H\.?|Thị\s*xã|TX)\s+([^,]+)',
    re.IGNORECASE
)

PROV_REGEX_STR = r'(?:Tỉnh|Thành\s*phố|Thành\s*Phố|TP\.|TP)?\s*(?:' + '|'.join(
    r'\b' + re.escape(p) + r'\b' for p in sorted(PROVINCES, key=len, reverse=True)
) + r')'
PROV_PATTERN = re.compile(PROV_REGEX_STR, re.IGNORECASE)


def remove_vietnamese_accents(text: str) -> str:
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text


def has_vietnamese_accents(text: str) -> bool:
    return bool(re.search(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', text, re.IGNORECASE))


def norm_text(s: str) -> str:
    """
    Chuẩn hóa chuỗi văn bản:
    - Loại bỏ dấu câu thừa, chuyển thường.
    - Chuẩn hóa dấu thanh kiểu cũ/mới (Hòa vs Hoà, Thủy vs Thuỷ).
    - Chuẩn hóa khoảng trắng quanh dấu nháy đơn (') và dấu gạch nối (-)
      (ví dụ: "Ia H ' Drai" -> "Ia H'Drai").
    - Chuẩn hóa từ viết tắt phổ biến (đg -> đường, kđt -> khu đô thị, tdp -> tổ dân phố).
    """
    if not s:
        return ''
    s = s.strip(' .,-;:')
    s = s.lower()
    s = s.replace('òa', 'oà').replace('òe', 'oè').replace('ùy', 'uỳ')
    s = s.replace('óa', 'oá').replace('óe', 'oé').replace('úy', 'uý')
    s = s.replace('đg', 'đường').replace('kđt', 'khu đô thị').replace('tdp', 'tổ dân phố')
    # Chuẩn hóa dấu nháy đơn
    s = re.sub(r"[’‘`]", "'", s)
    s = re.sub(r"\s*'\s*", "'", s)
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def clean_admin_name(s: str) -> str:
    s = norm_text(s)
    s = ADMIN_PREFIX_REGEX.sub('', s).strip(' .,-')
    return s


def is_name_equal(name1: str, name2: str) -> bool:
    """
    So sánh tên 2 đơn vị hành chính:
    1. So khớp sau khi loại bỏ tiền tố hành chính và chuẩn hóa dấu cách/dấu nháy.
    2. Nếu 1 bên gõ không dấu hoàn toàn (unaccented), so khớp dạng không dấu.
    3. Nếu cả 2 đều có dấu, giữ nguyên dấu để phân biệt tên khác nhau (ví dụ: Ba Tơ vs Ba Tô).
    """
    n1 = clean_admin_name(name1)
    n2 = clean_admin_name(name2)
    if not n1 or not n2:
        return n1 == n2
    if n1 == n2:
        return True
    # Hỗ trợ trường hợp khách gõ tiếng Việt không dấu
    if not has_vietnamese_accents(n1) or not has_vietnamese_accents(n2):
        return remove_vietnamese_accents(n1) == remove_vietnamese_accents(n2)
    return False


def extract_pages_from_pdf(pdf_path: str) -> List[str]:
    try:
        raw_text = subprocess.check_output(
            ['pdftotext', pdf_path, '-'],
            stderr=subprocess.DEVNULL
        ).decode('utf-8', errors='ignore')
        pages = raw_text.split('\x0c')
        if pages and not pages[-1].strip():
            pages.pop()
        
        non_empty = [p for p in pages if len(p.strip()) > 30]
        if len(non_empty) >= len(pages) * 0.8 and len(pages) > 0:
            return pages
    except Exception:
        pass

    return ocr_pdf(pdf_path)


def _ocr_single_image(args: Tuple[int, str, str]) -> Tuple[int, str]:
    idx, img_path, out_base = args
    try:
        subprocess.run(
            ['tesseract', img_path, out_base, '-l', 'vie+eng', '--psm', '6'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        txt_path = out_base + '.txt'
        if os.path.exists(txt_path):
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                return idx, f.read()
    except Exception:
        pass
    return idx, ''


def ocr_pdf(pdf_path: str) -> List[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(['pdftoppm', '-png', '-r', '200', pdf_path, os.path.join(tmpdir, 'page')],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        img_files = sorted([f for f in os.listdir(tmpdir) if f.startswith('page-') and f.endswith('.png')])
        if not img_files:
            return []

        max_workers = min(4, os.cpu_count() or 2)
        tasks = [
            (i, os.path.join(tmpdir, img_name), os.path.join(tmpdir, f'ocr_{i}'))
            for i, img_name in enumerate(img_files)
        ]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            ocr_results = list(executor.map(_ocr_single_image, tasks))

        ocr_results.sort(key=lambda x: x[0])
        return [text for _, text in ocr_results]


def parse_page(page_text: str) -> Tuple[str, str, str]:
    m_code = re.search(r'\b(SPXVN[0-9A-Z]+)\b', page_text)
    code = m_code.group(1) if m_code else 'Không tìm thấy'

    end_idx = page_text.find('*** Người gửi phải cam kết')
    if end_idx == -1:
        end_idx = page_text.find('Nội dung hàng')

    recip_block = ''
    m_sdt = re.search(r'SĐT:?\s*\d+', page_text)
    if m_sdt and end_idx != -1 and end_idx > m_sdt.end():
        recip_block = page_text[m_sdt.end():end_idx].strip()
    elif 'Đến:' in page_text:
        den_idx = page_text.find('Đến:')
        if end_idx != -1 and end_idx > den_idx:
            recip_block = page_text[den_idx + 4:end_idx].strip()
        else:
            recip_block = page_text[den_idx + 4:den_idx + 400].strip()
    else:
        recip_block = page_text[:400].strip()

    lines = [l.strip() for l in recip_block.splitlines() if l.strip()]
    if lines:
        name = lines[0]
        addr = ' '.join(lines[1:])
    else:
        name = 'Không rõ'
        addr = ''

    return code, name, addr


def split_address(full_addr: str) -> Tuple[str, str]:
    matches = list(PROV_PATTERN.finditer(full_addr))
    if len(matches) >= 2:
        first_m = matches[0]
        end_pos = first_m.end()
        part1 = full_addr[:end_pos].strip(' ,')
        part2 = full_addr[end_pos:].strip(' ,')
        return part1, part2

    w_matches = list(WARD_PATTERN.finditer(full_addr))
    if len(w_matches) >= 2:
        second_w = w_matches[1]
        start_pos = second_w.start()
        part1 = full_addr[:start_pos].strip(' ,')
        part2 = full_addr[start_pos:].strip(' ,')
        return part1, part2

    return full_addr, full_addr


def compare_addresses(part1: str, part2: str) -> Tuple[bool, str]:
    if not part2 or part1 == part2:
        return True, ""

    w1 = list(WARD_PATTERN.finditer(part1))
    w2 = list(WARD_PATTERN.finditer(part2))

    d1 = list(DISTRICT_PATTERN.finditer(part1))
    d2 = list(DISTRICT_PATTERN.finditer(part2))

    if w1 and w2:
        ward1_str = w1[-1].group(0).strip(' ,')
        ward2_str = w2[0].group(0).strip(' ,')

        if not is_name_equal(ward1_str, ward2_str):
            reason = f"{ward1_str} vs {ward2_str}"
            if d2:
                dist2_str = d2[0].group(0).strip(' ,')
                if not d1 or not is_name_equal(d1[-1].group(0), dist2_str):
                    reason = f"{ward1_str} vs {ward2_str}, {dist2_str}"
            return False, reason

    if d1 and d2:
        dist1_str = d1[-1].group(0).strip(' ,')
        dist2_str = d2[0].group(0).strip(' ,')

        if not is_name_equal(dist1_str, dist2_str):
            return False, f"{dist1_str} vs {dist2_str}"

    return True, ""


def check_pdf_stream(pdf_path: str) -> Generator[Dict[str, Any], None, None]:
    pages = extract_pages_from_pdf(pdf_path)
    total_pages = len(pages)

    yield {
        'type': 'start',
        'total': total_pages
    }

    results = []
    mismatches_count = 0

    for idx, page_text in enumerate(pages, 1):
        code, name, full_addr = parse_page(page_text)
        part1, part2 = split_address(full_addr)
        is_match, reason = compare_addresses(part1, part2)

        item = {
            'page': idx,
            'code': code,
            'recipient': name,
            'raw_address': full_addr,
            'customer_address': part1,
            'system_address': part2,
            'is_match': is_match,
            'reason': reason
        }
        results.append(item)
        if not is_match:
            mismatches_count += 1

        percent = round((idx / total_pages) * 100) if total_pages > 0 else 100
        yield {
            'type': 'progress',
            'current': idx,
            'total': total_pages,
            'percent': percent,
            'item': item
        }

    matches_count = total_pages - mismatches_count
    yield {
        'type': 'done',
        'total': total_pages,
        'matches': matches_count,
        'mismatches': mismatches_count,
        'results': results
    }


def check_pdf(pdf_path: str) -> List[Dict]:
    results = []
    for event in check_pdf_stream(pdf_path):
        if event.get('type') == 'progress' and 'item' in event:
            results.append(event['item'])
    return results


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Cách dùng: python3 spx_checker.py <duong_dan_file.pdf>")
        sys.exit(1)

    input_pdf = sys.argv[1]
    if os.path.exists(input_pdf):
        print(f"Đang kiểm tra: {input_pdf}...")
        res = check_pdf(input_pdf)
        mismatches = [r for r in res if not r['is_match']]
        print(f"Đã check {len(res)} đơn, {len(res) - len(mismatches)} đơn khớp, {len(mismatches)} đơn lệch.\n")
        print("| STT | Mã vận đơn (SPXVN...) | Người nhận | Địa chỉ khách ghi | Địa chỉ hệ thống | Lệch ở đâu |")
        print("|:---:|:---|:---|:---|:---|:---|")
        for i, m in enumerate(mismatches, 1):
            print(f"| {i} | {m['code']} | {m['recipient']} | {m['customer_address']} | {m['system_address']} | {m['reason']} |")
    else:
        print(f"Lỗi: Không tìm thấy file '{input_pdf}'")
        sys.exit(1)