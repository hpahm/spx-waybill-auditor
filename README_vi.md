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
  - Xử lý mượt mà các trường hợp đặc biệt: dấu cách quanh dấu nháy đơn (*Huyện Ia H ' Drai* vs *Huyện Ia H' Drai*), chữ viết tắt (*P.*, *Q.*, *H.*, *X.*, *TP.*), khách gõ tiếng Việt không dấu.
- **🖥️ Hỗ Trợ 2 Chế Độ Tiện Lợi**:
  - **Giao diện Web trực quan**: Kéo & thả file PDF, có nút sao chép bảng Markdown và xuất file Excel (CSV) với 1 click.
  - **Dòng lệnh (CLI)**: Phù hợp chạy trong terminal hoặc tích hợp vào hệ thống tự động hóa.
- **🔍 Cơ Chế OCR Tự Động**: Đọc trực tiếp lớp chữ (Text Layer) của PDF gốc; tự động kích hoạt Tesseract OCR nếu gặp file scan/ảnh chụp.

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
  # Debian / Ubuntu
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
4. Xem danh sách đơn lệch, bấm **"Sao chép bảng (Markdown)"** hoặc **"Xuất file Excel (CSV)"**.

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

Nếu bạn muốn đưa tool lên máy chủ (VPS, Cloud Server, Docker Swarm) để nhân viên trong shop cùng truy cập qua trình duyệt:

```bash
# Di chuyển vào thư mục dự án
cd App

# Khởi động container bằng Docker Compose
docker compose up -d --build
```

Ứng dụng sẽ chạy tại cổng `8765` (truy cập qua `http://ip-cua-server:8765`).

### Cấu Hình Biến Môi Trường

| Biến | Mặc định | Mô tả |
|---|---|---|
| `PORT` | `8765` | Cổng HTTP lắng nghe |
| `HOST` | `0.0.0.0` | Địa chỉ IP bind (`0.0.0.0` để truy cập từ ngoài server) |

---

## 📁 Cấu Trúc Mã Nguồn

```
.
├── spx_checker.py      # Thuật toán cốt lõi: bóc tách địa chỉ, chuẩn hóa hành chính & đối soát
├── app.py              # Web server độc lập (dùng thư viện chuẩn http.server, không cần Flask/FastAPI)
├── check_spx.py        # Giao diện dòng lệnh CLI
├── run.sh              # Script chạy nhanh
├── Dockerfile          # Cấu hình đóng gói Docker tối ưu cho production
├── docker-compose.yml  # File compose khởi chạy nhanh 1 lệnh
├── README.md           # Tài liệu tiếng Anh
└── README_vi.md        # Tài liệu tiếng Việt
```

---

## 📄 Bản Quyền

Giấy phép MIT. Sử dụng tự do và miễn phí cho mục đích cá nhân lẫn thương mại.
