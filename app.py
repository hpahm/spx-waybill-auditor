#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPX Waybill Auditor - Web Application
Self-contained, zero-dependency local web app for drag-and-drop waybill verification.
Built with Python's standard library (http.server), fully compatible with Python 3.8 to 3.14+.
"""

import os
import sys
import json
import tempfile
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from spx_checker import check_pdf

DEFAULT_PORT = int(os.environ.get('PORT', 8765))
HOST = os.environ.get('HOST', '0.0.0.0')

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
            border-radius: 12px;
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
        }
        .upload-card svg { width: 48px; height: 48px; fill: var(--primary); margin-bottom: 12px; }
        .upload-card p { font-size: 15px; font-weight: 500; margin-bottom: 4px; }
        .upload-card span { font-size: 13px; color: var(--text-muted); }
        #fileInput { display: none; }

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
            border-radius: 10px;
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
        .loading { display: none; text-align: center; padding: 30px; font-weight: 500; color: var(--text-muted); }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 28px;
            height: 28px;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 12px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
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
        <span>Tự động đối soát tất cả các trang</span>
        <input type="file" id="fileInput" accept=".pdf">
    </div>

    <div class="loading" id="loading">
        <div class="spinner"></div>
        <p>Đang phân tích vận đơn và đối soát từng trang...</p>
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

    function handleFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Vui lòng chọn file định dạng PDF!');
            return;
        }

        document.getElementById('loading').style.display = 'block';
        document.getElementById('statsGrid').style.display = 'none';
        document.getElementById('actionsBar').style.display = 'none';
        document.getElementById('tableContainer').style.display = 'none';

        fetch('/api/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/pdf',
                'X-Filename': encodeURIComponent(file.name)
            },
            body: file
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById('loading').style.display = 'none';
            if (data.error) {
                alert('Lỗi: ' + data.error);
                return;
            }
            currentData = data.results || [];
            showAll = false;
            document.getElementById('btnToggleAll').innerText = 'Xem tất cả các đơn';
            render();
        })
        .catch(err => {
            document.getElementById('loading').style.display = 'none';
            alert('Lỗi gửi file: ' + err);
        });
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
            length = int(self.headers.get('Content-Length', 0))
            if length <= 0:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Không có dữ liệu file'}).encode('utf-8'))
                return

            pdf_bytes = self.rfile.read(length)

            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            try:
                results = check_pdf(tmp_path)
                resp_data = {'success': True, 'results': results}
            except Exception as e:
                resp_data = {'error': str(e)}
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(resp_data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def run_server(host=HOST, port=DEFAULT_PORT):
    server = HTTPServer((host, port), SPXRequestHandler)
    display_host = 'localhost' if host in ('0.0.0.0', '127.0.0.1') else host
    print("=" * 65)
    print(" SPX WAYBILL AUDITOR - SERVER IS RUNNING")
    print(f" URL: http://{display_host}:{port}")
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


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else DEFAULT_PORT
    run_server(port=port)
