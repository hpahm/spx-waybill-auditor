# SPX Waybill Auditor

👉 **[Xem bản Tiếng Việt (Vietnamese version)](README_vi.md)**

> **SPX Waybill Auditor** is a high-performance, offline shipping label address verification engine for **SPX Express**. It automatically cross-checks recipient addresses to detect discrepancies between buyer-entered detail addresses and system-standardized administrative units with **zero AI token cost**.

---

## Key Features

- **Blazing Fast**: Processes 100+ PDF waybill pages in under 0.2 seconds.
- **100% Offline & Free**: Runs locally on your machine or private server. No API keys, no cloud dependencies, zero recurring token fees.
- **Smart Administrative Matching**:
  - Compares Vietnamese administrative levels (Ward/Commune, District/Town, City/Province).
  - Automatically handles level naming changes (*Xã An Khánh* vs *Phường An Khánh*, *Quận* vs *Huyện*, *Thành phố* vs *TP*).
  - Accurately identifies genuine name mismatches (*Phường An Biên* vs *Phường Lam Sơn*, *Phường 14* vs *Phường 24*, *Thị trấn Ba Tơ* vs *Xã Ba Tô*).
  - Handles edge cases: whitespace variations around quotes (*Huyện Ia H ' Drai* vs *Huyện Ia H' Drai*), punctuation, abbreviations (*P.*, *Q.*, *H.*, *X.*, *TP.*), and unaccented customer inputs.
- **Real-Time NDJSON Streaming Progress Bar**:
  - Beautiful Shopee orange gradient progress bar with rounded corners.
  - Live progress tracking displaying percentage (`%`), order counter (`X / Y`), filename, and formatted file size.
  - Zero-buffering real-time streaming (`X-Accel-Buffering: no`), perfectly tuned for Nginx reverse proxies.
- **Enterprise-Grade Server & Concurrency**:
  - Built-in `ThreadingHTTPServer`: Handles concurrent requests seamlessly without hanging or blocking.
  - 60-second connection timeout to mitigate internet port scans and stale sockets.
- **Multi-Core Parallel OCR**:
  - Automatically reads native PDF text streams; seamlessly triggers multi-threaded Tesseract OCR across 2–4 CPU cores for scanned/rasterized documents (3–4x faster).
- **Security & Storage Protection**:
  - Strict upload validation: Blocks non-PDF files, checks `%PDF-` magic header bytes, and enforces a 100MB size limit.
  - Automatic zombie file cleanup daemon: Runs periodically to keep temporary directories lean and prevent disk overflow.
- **Dual Mode**:
  - **Interactive Web UI**: Modern drag-and-drop web dashboard with one-click Markdown & Excel (CSV) export.
  - **CLI Mode**: Fast command-line interface for terminal workflows and batch scripts.

---

## Quick Start (Local)

### Prerequisites

The tool relies on standard Linux utilities:
- **Python 3.8+**
- **poppler-utils** (`pdftotext`, `pdftoppm`):
  ```bash
  # Debian / Ubuntu
  sudo apt-get install -y poppler-utils

  # Arch Linux
  sudo pacman -S poppler

  # macOS (Homebrew)
  brew install poppler
  ```
- *(Optional, only for scanned PDFs)* **tesseract-ocr** with Vietnamese data:
  ```bash
  # Debian / Ubuntu
  sudo apt-get install -y tesseract-ocr tesseract-ocr-vie
  ```

---

### Option 1: Web Interface (Recommended)

1. Launch the server:
   ```bash
   ./run.sh
   # Or: python3 app.py
   ```
2. Your default web browser will automatically open `http://localhost:8765`.
3. Simply **drag and drop** your SPX waybill PDF onto the dashboard.
4. Watch the real-time progress bar, review mismatched orders, copy the Markdown table, or download the CSV report.

---

### Option 2: Command Line (CLI)

```bash
# Check a PDF file and view mismatches in terminal
python3 check_spx.py /path/to/waybill.pdf

# Export mismatched orders directly to CSV
python3 check_spx.py /path/to/waybill.pdf --csv mismatches.csv

# View all orders (both matched and mismatched)
python3 check_spx.py /path/to/waybill.pdf --all
```

---

## Server & Docker Deployment (Production)

Deploying to any Linux VPS, Docker host, or cloud server takes a single command:

```bash
# Clone the repository
git clone https://github.com/hpahm/spx-waybill-auditor.git
cd spx-waybill-auditor

# Start container in detached mode
docker compose up -d --build
```

The Web UI will be immediately accessible on port `8765` (e.g. `http://your-server-ip:8765`).

### Docker Optimizations
- **Lightweight Healthcheck**: Built with `curl` (<2MB memory footprint) instead of spawning heavy Python runtime processes.
- **Log Rotation**: Built-in JSON-file log limits (`max-size: 10m`, `max-file: 3`) to protect VPS disk space.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8765` | Port the web server listens on |
| `HOST` | `0.0.0.0` | Bind IP address (`0.0.0.0` for all interfaces) |

---

## Project Structure

```
.
├── spx_checker.py      # Core verification engine, parallel OCR & streaming generator
├── app.py              # Multithreaded Web UI, NDJSON streaming & zombie file cleanup
├── check_spx.py        # Command-line interface (CLI)
├── run.sh              # One-click execution shortcut
├── Dockerfile          # Production Docker configuration with curl, poppler & tesseract
├── docker-compose.yml  # Docker Compose stack with log rotation
├── README.md           # English documentation
└── README_vi.md        # Vietnamese documentation
```

---

## License

MIT License. Free for personal and commercial use.
