# Advanced Camera Tracking System (ACTS)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2B-0078D4?logo=windows&logoColor=white)](#)

ACTS là MVP (Minimum Viable Product) hệ thống giám sát thông minh do nhóm What Ever xây dựng cho dự án. Ứng dụng desktop (Tkinter) sử dụng webcam để phát hiện chuyển động thời gian thực, phát cảnh báo âm thanh, vẽ vùng giám sát và tự động ghi lại bằng chứng.

---

## Mục lục
- [Thông tin dự án](#thông-tin-dự-án)
- [Vấn đề & mục tiêu](#vấn-đề--mục-tiêu)
- [Tính năng chính](#tính-năng-chính)
- [Hướng mở rộng (proposal)](#hướng-mở-rộng-proposal)
- [Kiến trúc thư mục](#kiến-trúc-thư-mục)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt từ mã nguồn](#cài-đặt-từ-mã-nguồn)
- [Chạy nhanh bằng `ACTS_System.exe`](#chạy-nhanh-bằng-acts_systemexe)
- [Hướng dẫn vận hành UI](#hướng-dẫn-vận-hành-ui)
- [Quản lý dữ liệu & kiểm thử](#quản-lý-dữ-liệu--kiểm-thử)
- [Tài liệu tham khảo & liên hệ](#tài-liệu-tham-khảo--liên-hệ)

---

## Thông tin dự án

| Thuộc tính | Chi tiết |
| --- | --- |
| Mã dự án | ACTS – Advanced Camera Tracking System |
| Nhóm thực hiện | Anh Lê Nhật (Scrum Master) · Võ Nguyễn Trung Sơn · Vũ Đăng Huy · Nguyễn Đặng Minh Tuấn · Phan Công Doanh |
| Mentor | ThS. Lê Kim Hoàng – International School, Duy Tân University |
| Thời gian | 28/08/2025 → 04/12/2025 |
| Tài liệu gốc | `CMU-CS432KIS_Proposal_Camera-Tracking-System.docx` |

## Vấn đề & mục tiêu
- **Pain points**: CCTV truyền thống chỉ ghi hình thụ động, phản ứng chậm, nhiều cảnh báo giả và chưa kết nối IoT.
- **Giải pháp**: mang lại công cụ desktop đơn giản, chi phí thấp để giám sát theo thời gian thực, cảnh báo chính xác và lưu bằng chứng tự động.
- **SMART**: hoàn thành MVP trong 1 tháng với các tính năng phát hiện chuyển động, cảnh báo tức thì, lưu sự kiện và đạt ~80% hài lòng người dùng thử nghiệm.

## Tính năng chính
- **Real-time tracking**: `MainSystem` (`Main.py`) đọc webcam, lật khung hình và gửi qua `MotionDetector` (MOG2) trước khi render lên Tkinter GUI.
- **Zoning mode**: người dùng vẽ ROI ngay trên video; chỉ ROI mới kích hoạt cảnh báo/ghi hình.
- **Stateful alerting**: `AlertManager` dùng pygame để chuyển giữa SAFE → WARNING → DANGER, thay đổi màu UI và phát âm thanh.
- **Recording & capture**: `VideoRecorder` ghi MP4 (`mp4`) với timestamp; nút CAPTURE lưu ảnh JPG và đẩy vào hàng đợi lịch sử.
- **History queue & explorer**: các bằng chứng mới hiển thị thumbnail; nút `📂 History Folder` mở trực tiếp thư mục `recordings/`.
- **Dashboard trực quan**: thanh tiến trình, 15 đèn timeline, scales `Ignore Small Objects` & `Time to Record`, cùng bảng thống kê runtime/status.

## Hướng mở rộng (proposal)
- AI phân loại người/xe/thú cưng để giảm false-positive.
- Đồng bộ cảnh báo qua mobile app, SMS, email; tích hợp thiết bị IoT (đèn, khóa, robot tuần tra).
- Tính năng offline mode, báo cáo định kỳ, xác minh thiết bị, thanh toán/subscription cho bản thương mại.

## Kiến trúc thư mục
- `Main.py` – điều phối vòng đời ứng dụng, xử lý sự kiện GUI.
- `app_gui.py` – layout Tkinter, các nút START/STOP/ZONING/CAPTURE/RECORD, dashboard và lịch sử.
- `MotionDetector.py` – phát hiện chuyển động dựa trên ngưỡng diện tích.
- `alert_manager.py` – quản lý trạng thái cảnh báo và âm thanh.
- `videorecorder.py` – tạo thư mục `recordings/`, ghi MP4 và đóng file.
- `ACTS_System.exe` – bản build Windows đóng gói để chạy ngay.
- Tài nguyên: `Logo.png`, `alert.mp3`, proposal `.docx`.

## Yêu cầu hệ thống
- Windows 10/11, webcam hoạt động, loa/speaker để nghe cảnh báo.
- Python 3.10+ (nếu chạy từ source).
- Thư viện: `opencv-python`, `pygame`, `Pillow`, `numpy` (Tkinter có sẵn).

## Cài đặt từ mã nguồn
```bash
# 1. Khuyến nghị tạo virtualenv
pip install opencv-python pygame Pillow numpy

# 2. (Tuỳ chọn) chuẩn bị thư mục recordings
mkdir recordings

# 3. Chạy ứng dụng
python Main.py
```
> Lần đầu chạy hãy cho phép Windows truy cập camera/micro.

## Chạy nhanh bằng `ACTS_System.exe`
1. Double-click (hoặc `Run as administrator` nếu SmartScreen cảnh báo).
2. Chờ 2–5 giây để pygame/Tkinter nạp tài nguyên.
3. Nếu webcam đang bị app khác sử dụng, nhấn `STOP` rồi `START` sau khi giải phóng camera.
4. Ảnh/video vẫn lưu tại thư mục `recordings/` cùng cấp file `.exe`.

## Hướng dẫn vận hành UI
| Nút | Chức năng |
| --- | --- |
| `▶ START` | Mở webcam, bắt đầu loop xử lý và hiển thị trạng thái SAFE. |
| `■ STOP` | Dừng camera, dừng ghi hình/âm thanh, reset dashboard. |
| `⚠ ZONING` | Bật/tắt chế độ vẽ ROI; kéo-thả trên video để cố định vùng giám sát. |
| `📷 CAPTURE` | Lưu ảnh JPG tức thời, cập nhật lịch sử. |
| `● RECORD` | Ghi hình thủ công; hệ thống vẫn auto-record khi vào trạng thái `DANGER`. |
| `📂 History Folder` | Mở Explorer tại `recordings/` để xem/xoá/tải file. |

## Quản lý dữ liệu & kiểm thử
- Định dạng file:
  - Ảnh: `recordings/CAP-<ddmmyy-hhmmss>.jpg`
  - Video: `recordings/<dd-mm-YYYY-HH-MM-SS>.mp4`
- Theo dõi dung lượng thư mục `recordings/` và dọn thủ công khi cần.
- Mẹo vận hành:
  - Điều chỉnh `Ignore Small Objects` để khử nhiễu do vật nhỏ/côn trùng.
  - Tăng giảm `Time to Record` để phù hợp với độ dài clip mong muốn.
  - Nếu không nghe thấy âm cảnh báo, kiểm tra device audio hoặc quyền pygame.

## Tài liệu tham khảo & liên hệ
- Proposal chi tiết: `CMU-CS432KIS_Proposal_Camera-Tracking-System.docx`
- Tài nguyên: `Logo.png`, `alert.mp3`, `ACTS_System.exe`
- Liên hệ góp ý/backlog: Anh Lê Nhật – `nhatanhh.dev@gmail.com`