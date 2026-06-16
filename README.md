# Hệ thống Phát hiện Xâm nhập Mạng (IDS) ứng dụng Trí tuệ Nhân tạo (AI)

Dự án này cung cấp một khung sườn (skeleton) hoàn chỉnh để xây dựng, huấn luyện và chạy thực nghiệm hệ thống IDS dựa trên Học máy (Machine Learning) và Học không giám sát (Anomaly Detection).

Hệ thống được thiết kế để:
1. **Huấn luyện:** Sử dụng các tập dữ liệu lưu lượng mạng nổi tiếng như **CICIDS2017** hoặc **CSE-CIC-IDS2018** từ Kaggle.
2. **Kiểm thử độc lập:** Chạy đánh giá chéo (cross-test) với các bộ dữ liệu khác như **UNSW-NB15**.
3. **Thực nghiệm thời gian thực (Real-time Sniffing):** Bắt trực tiếp gói tin từ card mạng (sử dụng Scapy), nhóm thành các luồng (flows), tự động trích xuất các đặc trưng và phân loại xem đó là lưu lượng an toàn hay độc hại.

---

## 📁 Cấu trúc thư mục dự án

```text
Nhóm 10 - ATTT/
├── data/
│   ├── raw/                 # Chứa dữ liệu gốc (.csv) tải từ Kaggle (ví dụ: Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv)
│   ├── processed/           # Dữ liệu sau khi qua bộ tiền xử lý và chuẩn hóa
│   └── external/            # Dữ liệu kiểm thử bên ngoài (file CSV từ dataset khác hoặc file PCAP đã được trích xuất)
├── models/                  # Lưu các mô hình đã huấn luyện (.pkl) và scaler (.pkl)
├── src/
│   ├── __init__.py
│   ├── preprocessing.py     # Module làm sạch dữ liệu, chuẩn hóa (StandardScaler), xử lý mất cân bằng
│   ├── models.py            # Wrapper cho Random Forest, XGBoost và Isolation Forest
│   ├── train.py             # Script huấn luyện chính (có cơ chế tự tạo Mock Data để chạy thử ngay lập tức)
│   ├── evaluate.py          # Script đánh giá mô hình trên tập dữ liệu kiểm thử bên ngoài
│   └── live_sniffer.py      # Bộ capture gói tin realtime bằng Scapy và phân loại trực tiếp
├── config.py                # Cấu hình đường dẫn, danh sách 15 thuộc tính chính, siêu tham số
├── requirements.txt         # Các thư viện Python cần cài đặt
└── README.md                # Hướng dẫn này
```

---

## 🚀 Hướng dẫn Cài đặt & Sử dụng

### 1. Chuẩn bị Môi trường
Khuyên dùng Python 3.9 - 3.11. Cài đặt các thư viện phụ thuộc bằng pip:

```bash
pip install -r requirements.txt
```

> [!NOTE]
> Trên hệ điều hành Windows, thư viện `scapy` cần phần mềm hỗ trợ bắt gói tin là **Npcap** (hoặc WinPcap). Nếu chạy sniffer bị lỗi, hãy tải và cài đặt Npcap tại: [https://npcap.com/](https://npcap.com/)

### 2. Huấn luyện Mô hình (`train.py`)
Mặc định, script huấn luyện sẽ tìm kiếm file dữ liệu dạng `.csv` trong thư mục `data/raw/`.
* **Nếu chưa có dữ liệu thật:** Chạy script sẽ tự động sinh ra một file dữ liệu giả lập (mock dataset) chứa 1,000 dòng có cấu trúc tương đương tập dữ liệu CICIDS2017 để bạn chạy thử nghiệm toàn bộ luồng code.
* **Nếu có dữ liệu thật:** Tải các file CSV của tập dữ liệu CICIDS2017 từ Kaggle và đặt vào thư mục `data/raw/`. Chương trình sẽ tự động nhận diện và huấn luyện trên dữ liệu thật.

Chạy lệnh sau để huấn luyện:
```bash
python src/train.py
```

Sau khi chạy xong, các mô hình và bộ chuẩn hóa sẽ được lưu tại thư mục `models/`:
- `models/scaler.pkl` (Bộ chuẩn hóa dữ liệu)
- `models/ids_rf.pkl` (Mô hình Random Forest)
- `models/ids_xgb.pkl` (Mô hình XGBoost)
- `models/ids_anomaly_iforest.pkl` (Mô hình Isolation Forest cho phát hiện dị thường)

### 3. Đánh giá trên dữ liệu kiểm thử bên ngoài (`evaluate.py`)
Đặt tập dữ liệu kiểm thử bên ngoài (ví dụ một phần của dataset UNSW-NB15 dạng `.csv` có chứa cột nhãn `Label` hoặc tương tự) vào thư mục `data/external/`.

Chạy lệnh để bắt đầu đánh giá:
```bash
python src/evaluate.py
```
Hệ thống sẽ tải mô hình đã huấn luyện trong thư mục `models/`, tiền xử lý dữ liệu kiểm thử theo đúng bộ chuẩn hóa đã học, chạy dự đoán và xuất báo cáo độ chính xác (F1-score, Precision, Recall, Confusion Matrix) của từng thuật toán.

### 4. Giám sát lưu lượng mạng Realtime (`live_sniffer.py`)
Khi mô hình AI đã được huấn luyện thành công và lưu lại trong thư mục `models/`, bạn có thể chạy sniffer mạng để phát hiện tấn công trực tiếp từ máy tính của mình.

Chạy lệnh dưới quyền Admin (quyền quản trị hệ thống để Scapy có thể bắt gói tin từ card mạng):
* **Windows (PowerShell/CMD):** Chạy PowerShell/CMD dưới quyền **Administrator** rồi gõ:
  ```powershell
  python src/live_sniffer.py
  ```

Mỗi khi hệ thống nhận diện được một luồng mạng có các đặc trưng giống hành vi tấn công (vượt ngưỡng cảnh báo xác suất trong `config.py`), một thông báo cảnh báo sẽ hiển thị trực quan lên màn hình.

---

## 📊 15 Thuộc tính lưu lượng được chọn lọc (Selected Features)

Để đảm bảo hệ thống sniffer realtime chạy mượt mà trên máy tính cá nhân và không bị nghẽn cổ chai khi tính toán 80 thuộc tính phức tạp của CICFlowMeter, dự án sử dụng 15 thuộc tính cốt lõi được nghiên cứu đánh giá là có đóng góp cao nhất cho việc nhận diện các cuộc tấn công thông thường (như Port Scan, DoS, DDoS):

1. **Flow Duration**: Tổng thời gian của luồng (Microseconds).
2. **Total Fwd Packets**: Tổng số gói tin gửi đi.
3. **Total Backward Packets**: Tổng số gói tin nhận về.
4. **Total Length of Fwd Packets**: Tổng kích thước các gói tin gửi đi.
5. **Total Length of Bwd Packets**: Tổng kích thước các gói tin nhận về.
6. **Fwd Packet Length Max/Min/Mean**: Kích thước gói tin lớn nhất/nhỏ nhất/trung bình của chiều gửi.
7. **Bwd Packet Length Max/Min/Mean**: Kích thước gói tin lớn nhất/nhỏ nhất/trung bình của chiều nhận.
8. **Flow Bytes/s**: Tốc độ truyền tải byte trên một giây.
9. **Flow Packets/s**: Tốc độ truyền tải gói tin trên một giây.
10. **Flow IAT Mean/Max**: Khoảng thời gian trung bình/lớn nhất giữa các gói tin liên tiếp.

---

## 🛠️ Hướng phát triển thêm cho bài tập nhóm
Để bài tập lớn đạt kết quả cao nhất, nhóm 10 có thể phát triển thêm các phần sau từ khung sườn này:
1. **Xây dựng Giao diện người dùng (Dashboard):** Sử dụng thư viện `streamlit` để vẽ biểu đồ realtime các cuộc tấn công phát hiện được (như biểu đồ tròn phân loại attack type, biểu đồ đường biểu thị traffic volume).
2. **Nâng cấp Anomaly Detection:** Thay thế Isolation Forest bằng mạng Neural Autoencoder viết bằng PyTorch để học sâu hơn về hành vi bình thường.
3. **Tự động chặn (Intrusion Prevention System - IPS):** Viết script gọi câu lệnh firewall của hệ điều hành (ví dụ: `netsh advfirewall` trên Windows hoặc `iptables` trên Linux) để block IP nguồn phát sinh tấn công ngay khi mô hình phát hiện ra.
