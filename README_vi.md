# 📦 SPX Waybill Auditor (Đối Soát Vận Đơn SPX)

👉 **[Read English Version](README.md)**

> **SPX Waybill Auditor** là công cụ kiểm tra và đối soát địa chỉ vận đơn **SPX Express** tốc độ cao, chạy hoàn toàn **offline cục bộ**. Tự động phát hiện các đơn hàng bị lệch giữa **địa chỉ chi tiết do khách ghi** và **địa chỉ hành chính hệ thống chuẩn hóa**, giúp shop tránh giao nhầm tuyến hoặc bị hoàn hàng với **chi phí 0 token AI**.

---

## 🌟 Điểm Nổi Bật

- **⚡ Siêu Nhanh**: Xử lý hơn 100 trang vận đơn PDF trong chưa đầy 0.2 giây.
- **💰 Tiết Kiệm Tuyệt Đối (0 Token)**: Chạy 100% trên máy tính cá nhân hoặc server riêng. Không cần API key, không phụ thuộc dịch vụ AI đám mây.
- **🎯 Đối Soát Chuẩn Xác Theo Quy Tắc Nghiệp Vụ**:
  - Tự động bỏ qua khi chỉ khác cấp hành chính nhưng trùng tên (*Xã An Khánh* vs *Phường An Khánh*, *Quận Bắc Từ Liêm* vs *Huyện Bắc Từ Liêm*, *TP Hải Phòng* vs *Thành phố Hải Phòng*).
  - Bắt chính xác các trường hợp lệch tên thực tế (*Phường An Biên* vs *Phường Lam Sơn*, *Phường 14* vs *Phường 24*, *Thị trấn Ba Tơ* vs *Xã Ba Tô*).
  - Xử lý mượt mà các trường hợp đặc biệt: khoảng trắng quanh dấu nháy (*Huyện Ia H ' Drai* vs *Huyện Ia H' Drai*), chữ viết tắt (*P.*, *Q.*, *H.*, *X.*, *TP.*), khách gõ tiếng Việt không dấu.
- **📊 Thanh Tiến Trình (Progress Bar) Gradient Cam Shopee Thời Gian Thực**:
  - Giao diện bo tròn viền gradient Shopee sang trọng.
  - Hiển thị trực tiếp tỷ lệ phần trăm (`%`), số lượng đơn `X / Y`, tên file và dung lượng file theo thời gian thực.
  - Cơ chế **NDJSON Streaming** với header `X-Accel-Buffering: no`, truyền tải mượt mà không bị nghẽn đệm khi chạy qua Nginx Reverse Proxy.
- **🚀 Server Đa Luồng (`ThreadingHTTPServer`) Chuẩn Doanh Nghiệp**:
  - Mỗi request được phục vụ độc lập trên 1 thread riêng, giải quyết triệt để tình trạng treo hàng đợi.
  - Tích hợp timeout ngắt kết nối sau 60 giây chống bot mạng scan cổng.
- **⚡ Tối Ưu Hóa OCR Đa Nhân (Multi-Core)**:
  - Tự động đọc lớp chữ PDF gốc; nếu gặp file ảnh scan, hệ thống tự động chạy OCR song song trên 2–4 core CPU (tăng tốc 3–4 lần).
- **🔒 Bảo Vệ Server & Tự Động Dọn Rác Bộ Nhớ Tạm**:
  - Chặn tuyệt đối file không phải PDF: kiểm tra đuôi mở rộng, kiểm tra chữ ký nhị phân (`%PDF-`), giới hạn kích thước file 100MB.
  - Daemon nền tự động quét dọn file tạm rác (.pdf, .png) quá 30 phút, chống tràn ổ cứng VPS.
- **🖥️ Hỗ Trợ 2 Chế Độ Tiện Lợi**:
  - **Giao diện Web trực quan**: Kéo & thả file PDF, có nút sao chép bảng Markdown và xuất file Excel (CSV) với 1 click.
  - **Dòng lệnh (CLI)**: Phù hợp chạy trong terminal hoặc tích hợp vào hệ thống tự động hóa.

---

## 🚀 Hướng Dẫn Sử Dụng Nhanh (Chạy Local)

### Yêu Cầu Cài Đặt

Tool sử dụng các công cụ hệ thống Linux có sẵn:
- **Python 3.8+**
- **poppler-utils** (cung cấp lệnh `pdftotext` và `pdftoppm`):
  ```bash
  # Trên Debian / Ubuntu
  sudo apt-get install -y poppler-utils

  # Trên Arch Linux
  sudo pacman -S poppler

  # Trên macOS (Homebrew)
  brew install poppler
  ```
- *(Tùy chọn, chỉ cần khi file là ảnh scan hoàn toàn)* **tesseract-ocr** tiếng Việt:
  ```bash
  # Trên Debian / Ubuntu
  sudo apt-get install -y tesseract-ocr tesseract-ocr-vie
  ```

---

### Cách 1: Giao Diện Web Kéo Thả (Khuyên Dùng)

1. Mở terminal và chạy:
   ```bash
   ./run.sh
   # Hoặc: python3 app.py
   ```
2. Trình duyệt sẽ tự động mở trang `http://localhost:8765`.
3. Kéo thả file PDF vận đơn SPX vào khung trên màn hình.
4. Theo dõi thanh tiến trình thời gian thực, xem danh sách đơn lệch, bấm **"Sao chép bảng (Markdown)"** hoặc **"Xuất file Excel (CSV)"**.

---

### Cách 2: Chạy Từ Dòng Lệnh (CLI)

```bash
# Kiểm tra file PDF và in danh sách đơn lệch ra màn hình
python3 check_spx.py duong_dan_file.pdf

# Xuất thẳng danh sách đơn lệch ra file CSV (mở bằng Excel)
python3 check_spx.py duong_dan_file.pdf --csv don_lech.csv

# Xem toàn bộ danh sách (cả đơn khớp lẫn đơn lệch)
python3 check_spx.py duong_dan_file.pdf --all
```

---

## 🐳 Triển Khai Lên Server / Docker (Production)

Để đưa tool lên máy chủ (VPS, Cloud Server, Docker Swarm):

```bash
# Di chuyển vào thư mục dự án
git clone https://github.com/hpahm/spx-waybill-auditor.git
cd spx-waybill-auditor

# Khởi động container bằng Docker Compose
docker compose up -d --build
```

Ứng dụng sẽ chạy tại cổng `8765` (truy cập qua `http://ip-cua-server:8765`).

### Tối Ưu Hóa Docker
- **Healthcheck siêu nhẹ**: Dùng `curl` (<2MB RAM) thay vì khởi động lại môi trường Python mỗi 30s.
- **Giới hạn xoay vòng log**: Cấu hình `max-size: 10m`, `max-file: 3` chống đầy ổ cứng VPS.

### Cấu Hình Biến Môi Trường

| Biến | Mặc định | Mô tả |
|---|---|---|
| `PORT` | `8765` | Cổng HTTP lắng nghe |
| `HOST` | `0.0.0.0` | Địa chỉ IP bind (`0.0.0.0` để truy cập từ ngoài server) |

---

## 📁 Cấu Trúc Mã Nguồn

```
.
├── spx_checker.py      # Thuật toán cốt lõi: OCR đa luồng, stream NDJSON & đối soát
├── app.py              # Server đa luồng (ThreadingHTTPServer), NDJSON streaming & daemon dọn rác
├── check_spx.py        # Giao diện dòng lệnh CLI
├── run.sh              # Script chạy nhanh
├── Dockerfile          # Cấu hình Docker với curl, poppler & tesseract
├── docker-compose.yml  # Docker Compose stack với log rotation
├── README.md           # Tài liệu tiếng Anh
└── README_vi.md        # Tài liệu tiếng Việt
```

---

## 📄 Bản Quyền

Giấy phép MIT. Sử dụng tự do và miễn phí cho mục đích cá nhân lẫn thương mại.
