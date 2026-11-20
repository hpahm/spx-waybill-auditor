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
- **Dual Mode**:
  - **Interactive Web UI**: Modern drag-and-drop web dashboard with one-click Markdown & Excel (CSV) export.
  - **CLI Mode**: Fast command-line interface for terminal workflows and batch scripts.
- **Built-in OCR Fallback**: Automatically reads native PDF text streams; seamlessly triggers OCR via Tesseract when given scanned/rasterized documents.

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
4. Review mismatched orders, copy the Markdown table, or download the CSV report.

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
git clone <repo-url>
cd <repo-folder>

# Start container in detached mode
docker compose up -d --build
```

The Web UI will be immediately accessible on port `8765` (e.g. `http://your-server-ip:8765`).

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8765` | Port the web server listens on |
| `HOST` | `0.0.0.0` | Bind IP address (`0.0.0.0` for all interfaces) |

---

## Project Structure

```
.
├── spx_checker.py      # Core verification engine, PDF parser & admin matching rules
├── app.py              # Zero-dependency local Web UI (Python standard library http.server)
├── check_spx.py        # Command-line interface (CLI)
├── run.sh              # One-click execution shortcut
├── Dockerfile          # Production Docker configuration with poppler & tesseract pre-installed
├── docker-compose.yml  # Docker Compose stack definition
├── README.md           # English documentation
└── README_vi.md        # Vietnamese documentation
```

---

## License

MIT License. Free for personal and commercial use.
