#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPX Waybill Auditor - Web Application
Self-contained, zero-dependency local web app for drag-and-drop waybill verification.
Built with Python's standard library (http.server.ThreadingHTTPServer), fully multithreaded,
supports NDJSON real-time progress streaming and automatic temporary file cleanup.
"""

import os
import sys
import json
import time
import socket
import tempfile
import threading
import webbrowser
from urllib.parse import unquote
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from spx_checker import check_pdf, check_pdf_stream

DEFAULT_PORT = int(os.environ.get('PORT', 8765))
HOST = os.environ.get('HOST', '0.0.0.0')
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB max file size
UPLOAD_TMP_DIR = os.path.join(tempfile.gettempdir(), 'spx_auditor_uploads')
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)


def cleanup_zombie_files(max_age_seconds: int = 1800):
    """
    Tự động quét và dọn dẹp các file rác (.pdf, .png, .txt) nếu tiến trình trước đó bị crash
    hoặc ngắt kết nối đột ngột giữa chừng.
    """
    now = time.time()
    scan_dirs = [UPLOAD_TMP_DIR, tempfile.gettempdir()]
    for d in scan_dirs:
        if not os.path.exists(d):
            continue
        try:
            for fname in os.listdir(d):
                if (fname.startswith('spx_upload_') or fname.startswith('page-') or fname.startswith('ocr_')) and \
                   (fname.endswith('.pdf') or fname.endswith('.png') or fname.endswith('.txt')):
                    fpath = os.path.join(d, fname)
                    try:
                        if os.path.isfile(fpath) and (now - os.path.getmtime(fpath) > max_age_seconds):
                            os.remove(fpath)
                    except Exception:
                        pass
        except Exception:
            pass


def zombie_cleanup_worker():
    """Luồng nền (Daemon) định kỳ chạy mỗi 10 phút để dọn dẹp file tạm quá 30 phút."""
    while True:
        time.sleep(600)
        cleanup_zombie_files(max_age_seconds=1800)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPX Waybill Auditor - Đối Soát Vận Đơn</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #ee4d2d;
            --primary-hover: #d73211;
            --primary-gradient: linear-gradient(135deg, #ff5722 0%, #ee4d2d 100%);
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --danger: #ef4444;
            --danger-bg: #fef2f2;
            --success: #10b981;
            --success-bg: #ecfdf5;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 30px 20px; line-height: 1.5; }
        .container { max-width: 1240px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 25px; }
        header h1 { font-size: 26px; color: var(--primary); font-weight: 700; margin-bottom: 6px; }
        header p { color: var(--text-muted); font-size: 14px; }
        
        .upload-card {
            background: var(--card);
            border: 2px dashed var(--border);
            border-radius: 14px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 25px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .upload-card:hover, .upload-card.dragover {
            border-color: var(--primary);
            background: #fff5f2;
            transform: translateY(-1px);
        }
        .upload-card svg { width: 48px; height: 48px; fill: var(--primary); margin-bottom: 12px; }
        .upload-card p { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
        .upload-card span { font-size: 13px; color: var(--text-muted); }
        #fileInput { display: none; }

        /* Realtime Shopee Gradient Progress Bar Card */
        .progress-card {
            background: #ffffff;
            border-radius: 14px;
            border: 2px solid transparent;
            background-image: linear-gradient(#fff, #fff), linear-gradient(135deg, #ff7337, #ee4d2d, #ff5722);
            background-origin: border-box;
            background-clip: padding-box, border-box;
            padding: 22px 24px;
            margin-bottom: 25px;
            box-shadow: 0 4px 18px rgba(238, 77, 45, 0.12);
            display: none;
            animation: fadeIn 0.2s ease-in;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        
        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .file-info {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            font-weight: 600;
            color: #1e293b;
        }
        .file-badge {
            background: #fff5f2;
            color: var(--primary);
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            border: 1px solid #ffd4cb;
        }
        .file-size {
            font-weight: 400;
            color: var(--text-muted);
            font-size: 13px;
        }
        .progress-status {
            font-size: 13px;
            font-weight: 600;
            color: var(--primary);
        }
        .progress-bar-track {
            background: #f1f5f9;
            border-radius: 9999px;
            height: 12px;
            overflow: hidden;
            position: relative;
            margin-bottom: 8px;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.06);
        }
        .progress-bar-fill {
            height: 100%;
            width: 0%;
            border-radius: 9999px;
            background: linear-gradient(90deg, #ff7337, #ee4d2d, #ff5722);
            background-size: 200% 100%;
            transition: width 0.18s cubic-bezier(0.4, 0, 0.2, 1);
            animation: shimmer 2s linear infinite;
        }
        @keyframes shimmer {
            0% { background-position: 100% 0; }
            100% { background-position: -100% 0; }
        }
        .progress-footer {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 500;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
            display: none;
        }
        .stat-card {
            background: var(--card);
            padding: 18px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .stat-card .label { font-size: 13px; color: var(--text-muted); font-weight: 500; margin-bottom: 4px; }
        .stat-card .val { font-size: 24px; font-weight: 700; }
        .stat-card.total .val { color: var(--text); }
        .stat-card.match .val { color: var(--success); }
        .stat-card.mismatch .val { color: var(--danger); }

        .actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            display: none;
        }
        .btn-group { display: flex; gap: 10px; }
        button {
            padding: 9px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid var(--border);
            background: var(--card);
            color: var(--text);
            transition: 0.15s;
        }
        button:hover { background: #f1f5f9; }
        button.primary { background: var(--primary); color: #fff; border-color: var(--primary); }
        button.primary:hover { background: var(--primary-hover); }

        .table-container {
            background: var(--card);
            border-radius: 12px;
            border: 1px solid var(--border);
            overflow-x: auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            display: none;
        }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
        th { background: #f8fafc; padding: 12px 14px; font-weight: 600; color: #475569; border-bottom: 1px solid var(--border); }
        td { padding: 12px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }
        tr:last-child td { border-bottom: none; }
        tr:hover td { background: #fcfcfc; }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge.danger { background: var(--danger-bg); color: var(--danger); border: 1px solid #fecaca; }
        .badge.success { background: var(--success-bg); color: var(--success); }
        .code { font-family: monospace; font-weight: 600; color: #0284c7; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>Đối Soát Vận Đơn SPX</h1>
        <p>Kiểm tra địa chỉ người nhận</p>
    </header>

    <div class="upload-card" id="dropZone" onclick="document.getElementById('fileInput').click()">
        <svg viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
        <p>Bấm chọn file hoặc Kéo & Thả file PDF vận đơn vào đây</p>
        <span>Chỉ chấp nhận file định dạng .pdf (Tối đa 100MB)</span>
        <input type="file" id="fileInput" accept=".pdf,application/pdf">
    </div>

    <!-- Realtime Progress Bar Card -->
    <div class="progress-card" id="progressCard">
        <div class="progress-header">
            <div class="file-info">
                <span class="file-badge">PDF</span>
                <span id="progressFileName">filename.pdf</span>
                <span class="file-size" id="progressFileSize">(0 MB)</span>
            </div>
            <div class="progress-status" id="progressStatus">Đang khởi tạo...</div>
        </div>
        <div class="progress-bar-track">
            <div class="progress-bar-fill" id="progressBarFill"></div>
        </div>
        <div class="progress-footer">
            <span id="progressCountText">0 / 0 đơn</span>
            <span id="progressPercentText">0%</span>
        </div>
    </div>

    <div class="stats-grid" id="statsGrid">
        <div class="stat-card total">
            <div class="label">Tổng số đơn</div>
            <div class="val" id="valTotal">0</div>
        </div>
        <div class="stat-card match">
            <div class="label">Đơn khớp (Bỏ qua)</div>
            <div class="val" id="valMatch">0</div>
        </div>
        <div class="stat-card mismatch">
            <div class="label">Đơn LỆCH (Cần kiểm tra)</div>
            <div class="val" id="valMismatch">0</div>
        </div>
    </div>

    <div class="actions" id="actionsBar">
        <div style="font-weight: 600; font-size: 15px;" id="tableTitle">Danh sách đơn lệch</div>
        <div class="btn-group">
            <button onclick="toggleViewAll()" id="btnToggleAll">Xem tất cả các đơn</button>
            <button onclick="copyTableMarkdown()">Sao chép bảng (Markdown)</button>
            <button class="primary" onclick="exportCSV()">Xuất file Excel (CSV)</button>
        </div>
    </div>

    <div class="table-container" id="tableContainer">
        <table id="resultTable">
            <thead>
                <tr>
                    <th style="width: 50px; text-align: center;">STT</th>
                    <th style="width: 170px;">Mã vận đơn</th>
                    <th style="width: 130px;">Người nhận</th>
                    <th>Địa chỉ khách ghi</th>
                    <th>Địa chỉ hệ thống</th>
                    <th style="width: 220px;">Lệch ở đâu</th>
                </tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>
</div>

<script>
    let currentData = [];
    let showAll = false;

    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    function formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }

    ['dragenter', 'dragover'].forEach(name => {
        dropZone.addEventListener(name, (e) => { e.preventDefault(); dropZone.classList.add('dragover'); }, false);
    });
    ['dragleave', 'drop'].forEach(name => {
        dropZone.addEventListener(name, (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); }, false);
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    async function handleFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Lỗi: Chỉ chấp nhận file định dạng PDF (.pdf)!');
            return;
        }

        if (file.size > 100 * 1024 * 1024) {
            alert('Lỗi: Dung lượng file vượt quá giới hạn 100MB!');
            return;
        }

        // Khởi tạo hiển thị thanh tiến trình
        const progressCard = document.getElementById('progressCard');
        const progressBarFill = document.getElementById('progressBarFill');
        const progressFileName = document.getElementById('progressFileName');
        const progressFileSize = document.getElementById('progressFileSize');
        const progressStatus = document.getElementById('progressStatus');
        const progressCountText = document.getElementById('progressCountText');
        const progressPercentText = document.getElementById('progressPercentText');

        progressFileName.innerText = file.name;
        progressFileSize.innerText = `(${formatFileSize(file.size)})`;
        progressStatus.innerText = 'Đang tải file lên và phân tích...';
        progressCountText.innerText = 'Đang chuẩn bị...';
        progressPercentText.innerText = '0%';
        progressBarFill.style.width = '0%';
        progressCard.style.display = 'block';

        document.getElementById('statsGrid').style.display = 'none';
        document.getElementById('actionsBar').style.display = 'none';
        document.getElementById('tableContainer').style.display = 'none';

        currentData = [];

        try {
            const response = await fetch('/api/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/pdf',
                    'X-Filename': encodeURIComponent(file.name)
                },
                body: file
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.error || ('Lỗi máy chủ: HTTP ' + response.status));
            }

            // Đọc NDJSON stream theo thời gian thực
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\\n');
                buffer = lines.pop(); // Giữ lại phần chưa hoàn chỉnh cuối cùng

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);
                        if (event.error) {
                            throw new Error(event.error);
                        }
                        if (event.type === 'start') {
                            progressStatus.innerText = `Đang đối soát ${event.total} đơn...`;
                            progressCountText.innerText = `0 / ${event.total} đơn`;
                        } else if (event.type === 'progress') {
                            currentData.push(event.item);
                            progressBarFill.style.width = event.percent + '%';
                            progressCountText.innerText = `${event.current} / ${event.total} đơn`;
                            progressPercentText.innerText = `${event.percent}%`;
                            progressStatus.innerText = `Đang xử lý đơn #${event.current}...`;
                        } else if (event.type === 'done') {
                            currentData = event.results || currentData;
                            progressBarFill.style.width = '100%';
                            progressPercentText.innerText = '100%';
                            progressStatus.innerText = 'Hoàn tất đối soát!';
                        }
                    } catch (e) {
                        console.error('Parse chunk error:', e);
                    }
                }
            }

            // Hoàn tất và hiển thị bảng kết quả
            setTimeout(() => {
                progressCard.style.display = 'none';
                showAll = false;
                document.getElementById('btnToggleAll').innerText = 'Xem tất cả các đơn';
                render();
            }, 300);

        } catch (err) {
            progressCard.style.display = 'none';
            alert('Lỗi: ' + (err.message || err));
        } finally {
            fileInput.value = '';
        }
    }

    function render() {
        const total = currentData.length;
        const mismatches = currentData.filter(x => !x.is_match);
        const matches = total - mismatches.length;

        document.getElementById('valTotal').innerText = total;
        document.getElementById('valMatch').innerText = matches;
        document.getElementById('valMismatch').innerText = mismatches.length;

        document.getElementById('statsGrid').style.display = 'grid';
        document.getElementById('actionsBar').style.display = 'flex';
        document.getElementById('tableContainer').style.display = 'block';

        const displayList = showAll ? currentData : mismatches;
        document.getElementById('tableTitle').innerText = showAll 
            ? `Tất cả đơn hàng (${displayList.length})` 
            : `Danh sách đơn LỆCH (${displayList.length})`;

        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';

        if (displayList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: #10b981; font-weight: 600;">Tuyệt vời! Không phát hiện đơn nào bị lệch địa chỉ.</td></tr>';
            return;
        }

        displayList.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="text-align: center; font-weight: 600;">${index + 1}</td>
                <td><span class="code">${item.code}</span></td>
                <td><strong>${item.recipient}</strong></td>
                <td>${item.customer_address}</td>
                <td>${item.system_address}</td>
                <td>
                    ${item.is_match 
                        ? '<span class="badge success">Khớp</span>' 
                        : `<span class="badge danger">${item.reason}</span>`}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    function toggleViewAll() {
        showAll = !showAll;
        document.getElementById('btnToggleAll').innerText = showAll ? 'Chỉ xem đơn LỆCH' : 'Xem tất cả các đơn';
        render();
    }

    function copyTableMarkdown() {
        const mismatches = currentData.filter(x => !x.is_match);
        if (!mismatches.length) {
            alert('Không có đơn lệch nào để sao chép!');
            return;
        }

        let md = '| STT | Mã vận đơn (SPXVN...) | Người nhận | Địa chỉ khách ghi | Địa chỉ hệ thống | Lệch ở đâu |\\n';
        md += '|:---:|:---|:---|:---|:---|:---|\\n';
        mismatches.forEach((m, idx) => {
            md += `| ${idx + 1} | ${m.code} | ${m.recipient} | ${m.customer_address} | ${m.system_address} | ${m.reason} |\\n`;
        });
        md += `\\nĐã check ${currentData.length} đơn, ${currentData.length - mismatches.length} đơn khớp, ${mismatches.length} đơn lệch.`;

        navigator.clipboard.writeText(md).then(() => {
            alert('Đã sao chép bảng Markdown vào bộ nhớ tạm!');
        });
    }

    function exportCSV() {
        const mismatches = currentData.filter(x => !x.is_match);
        if (!mismatches.length) {
            alert('Không có đơn lệch nào để xuất!');
            return;
        }

        let csv = '\\uFEFFSTT,Mã vận đơn,Người nhận,Địa chỉ khách ghi,Địa chỉ hệ thống,Lệch ở đâu\\n';
        mismatches.forEach((m, idx) => {
            const row = [
                idx + 1,
                `"${m.code}"`,
                `"${m.recipient.replace(/"/g, '""')}"`,
                `"${m.customer_address.replace(/"/g, '""')}"`,
                `"${m.system_address.replace(/"/g, '""')}"`,
                `"${m.reason.replace(/"/g, '""')}"`
            ];
            csv += row.join(',') + '\\n';
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `SPX_Don_Lech_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
    }
</script>
</body>
</html>
"""


class SPXRequestHandler(BaseHTTPRequestHandler):
    timeout = 60  # Ngắt kết nối treo hoặc bot scan mạng sau 60s

    def do_GET(self):
        if self.path == '/' or self.path.startswith('/?'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/check':
            try:
                length = int(self.headers.get('Content-Length', 0))
            except ValueError:
                length = 0

            # 1. Kiểm tra kích thước file
            if length <= 0:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Không có dữ liệu file tải lên'}).encode('utf-8'))
                return

            if length > MAX_UPLOAD_SIZE:
                self.send_response(413)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Dung lượng file vượt quá giới hạn 100MB'}).encode('utf-8'))
                return

            # 2. Kiểm tra tên file & định dạng .pdf
            raw_filename = self.headers.get('X-Filename', '')
            filename = unquote(raw_filename).strip()
            if filename and not filename.lower().endswith('.pdf'):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Định dạng file không hợp lệ! Hệ thống chỉ chấp nhận file PDF (.pdf)'}).encode('utf-8'))
                return

            # Đọc toàn bộ nội dung file
            pdf_bytes = self.rfile.read(length)

            # 3. Kiểm tra Magic Bytes (%PDF-) để chặn tuyệt đối file giả mạo đuôi
            if not pdf_bytes.startswith(b'%PDF-'):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Tệp tải lên không phải là file PDF hợp lệ (Magic header signature mismatch)'}).encode('utf-8'))
                return

            # Lưu vào thư mục tạm an toàn
            with tempfile.NamedTemporaryFile(dir=UPLOAD_TMP_DIR, prefix='spx_upload_', suffix='.pdf', delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            try:
                # Gửi header NDJSON streaming hỗ trợ Nginx
                self.send_response(200)
                self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache, no-transform')
                self.send_header('X-Accel-Buffering', 'no')  # Chống Nginx đệm chunk
                self.end_headers()

                # Stream từng đơn hàng theo thời gian thực
                for event in check_pdf_stream(tmp_path):
                    chunk = json.dumps(event, ensure_ascii=False) + '\n'
                    self.wfile.write(chunk.encode('utf-8'))
                    self.wfile.flush()

            except Exception as e:
                try:
                    err_chunk = json.dumps({'error': str(e)}, ensure_ascii=False) + '\n'
                    self.wfile.write(err_chunk.encode('utf-8'))
                    self.wfile.flush()
                except Exception:
                    pass
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
        else:
            self.send_response(404)
            self.end_headers()


def run_server(host=HOST, port=DEFAULT_PORT):
    # Dọn dẹp các file rác cũ khi khởi động server
    cleanup_zombie_files(max_age_seconds=1800)

    # Khởi chạy Daemon dọn rác nền định kỳ mỗi 10 phút
    cleaner_thread = threading.Thread(target=zombie_cleanup_worker, daemon=True)
    cleaner_thread.start()

    # Sử dụng ThreadingHTTPServer đa luồng xử lý song song nhiều request
    server = ThreadingHTTPServer((host, port), SPXRequestHandler)
    server.daemon_threads = True

    display_host = 'localhost' if host in ('0.0.0.0', '127.0.0.1') else host
    print("=" * 65)
    print(" SPX WAYBILL AUDITOR - PRODUCTION SERVER (MULTITHREADED)")
    print(f" URL: http://{display_host}:{port}")
    print(" Features: Multithreaded, NDJSON Streaming, Parallel OCR, Auto Cleanup")
    print(" Drag & drop your SPX waybill PDF to audit.")
    print(" Press Ctrl+C to terminate.")
    print("=" * 65)

    if host == '127.0.0.1' or host == '0.0.0.0':
        try:
            webbrowser.open(f'http://localhost:{port}')
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else DEFAULT_PORT
    run_server(port=port)
