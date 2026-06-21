# BÁO CÁO NGHIÊN CỨU & THỰC NGHIỆM CHUYÊN SÂU
## Đề tài: Tìm Hiểu Về Xây Dựng Hệ Thống Phát Hiện Xâm Nhập Mạng (IDS) Với Trí Tuệ Nhân Tạo (AI)

**Nội dung thực hiện:**
1. Khảo sát và tiền xử lý tập dữ liệu **Kaggle CICIDS2017** làm nền tảng huấn luyện IDS.
2. Xây dựng, huấn luyện và so sánh **10 mô hình học máy phân lớp có giám sát** và **1 mô hình không giám sát (Isolation Forest)**.
3. Thiết lập thực nghiệm trên tập dữ liệu thực tế CICIDS2017: Đánh giá hiệu năng quy mô lớn (50,000 dòng luồng mạng) để đo lường tính sẵn sàng máy chủ (**Availability**) song song với tính bảo mật (**Security**).
4. Phân tích chi tiết, trực quan hóa ranh giới quyết định (Decision Boundaries) và đường cong đánh đổi (Threshold Trade-offs) cho từng mô hình một cách định lượng.

---

## 1. Cơ Sở Dữ Liệu Huấn Luyện (Kaggle CICIDS2017) & Trích Chọn Đặc Trưng

Hệ thống sử dụng tập dữ liệu **CICIDS2017** (được cung cấp và tải về từ nguồn Kaggle) làm bộ dữ liệu mẫu chuẩn (Ground Truth) để huấn luyện mô hình. Tập dữ liệu này chứa lưu lượng mạng của 5 ngày làm việc với đầy đủ các hành vi mạng thông thường (Benign) và các cuộc tấn công phổ biến như DDoS (LOIC/HOIC), Brute Force, Web Attacks, và Infiltration.

### 1.1. Tiền xử lý & Chuẩn hóa
* **Loại bỏ nhiễu và làm sạch:** Các luồng mạng có thuộc tính lỗi, giá trị trống (NaN) hoặc vô cực (Infinity - phát sinh do phép chia cho thời lượng luồng duration = 0) đều được lọc sạch triệt để.
* **Chuẩn hóa StandardScaler:** Chuyển đổi các đặc trưng mạng có phân phối lệch (skewed distributions) về phân phối chuẩn hóa có trung bình $\mu = 0$ và độ lệch chuẩn $\sigma = 1$:
  $$Z = \frac{X - \mu}{\sigma}$$

### 1.2. Danh sách 15 Đặc trưng Trích chọn (15 Core Features)
Để tối ưu hóa thời gian huấn luyện đồng thời đảm bảo khả năng triển khai thực tế bắt gói tin thời gian thực qua card mạng, hệ thống trích lọc 15 đặc trưng quan trọng nhất:
1. `Flow Duration` (Thời lượng luồng)
2. `Total Fwd Packets` (Tổng số gói truyền đi)
3. `Total Backward Packets` (Tổng số gói nhận về)
4. `Total Length of Fwd Packets` (Tổng dung lượng gói truyền đi)
5. `Total Length of Bwd Packets` (Tổng dung lượng gói nhận về)
6. `Fwd Packet Length Max` (Độ dài gói truyền đi lớn nhất)
7. `Fwd Packet Length Min` (Độ dài gói truyền đi nhỏ nhất)
8. `Fwd Packet Length Mean` (Độ dài gói truyền đi trung bình)
9. `Bwd Packet Length Max` (Độ dài gói nhận về lớn nhất)
10. `Bwd Packet Length Min` (Độ dài gói nhận về nhỏ nhất)
11. `Bwd Packet Length Mean` (Độ dài gói nhận về trung bình)
12. `Flow Bytes/s` (Tốc độ truyền byte trên giây)
13. `Flow Packets/s` (Tốc độ truyền gói trên giây)
14. `Flow IAT Mean` (Thời gian trung bình giữa các gói tin)
15. `Flow IAT Max` (Thời gian lớn nhất giữa các gói tin)

---

## 2. Cơ Sở Toán Học Của 11 Thuật Toán Thực Nghiệm

### 2.1. Random Forest (Rừng Ngẫu Nhiên)
Phương pháp học máy kết hợp (Bagging). Huấn luyện $B$ cây quyết định độc lập trên các tập mẫu Bootstrap. Sự phân tách nút dựa trên việc giảm chỉ số Gini Impurity:
$$G(t) = 1 - \sum_{c=0}^{1} p_c^2$$

### 2.2. XGBoost (Extreme Gradient Boosting)
Học tăng cường (Boosting) tối ưu hóa hàm mục tiêu có chứa số hạng phạt độ phức tạp (chính quy hóa $\Omega(f)$) qua xấp xỉ Taylor bậc hai:
$$\mathcal{L}^{(t)} \approx \sum_{i=1}^{n} \left[ g_i f_t(x_i) + \frac{1}{2} h_i f_t^2(x_i) \right] + \gamma T + \frac{1}{2} \lambda \sum_{j=1}^{T} w_j^2$$
Trong đó $g_i$ và $h_i$ là gradient bậc nhất và bậc hai của hàm loss đối với dự đoán trước đó.

### 2.3. Decision Tree (Cây Quyết Định)
Xây dựng một cây quyết định duy nhất bằng cách phân tách không gian đặc trưng đệ quy nhằm tối đa hóa lượng thông tin thu được (Information Gain - IG) tại mỗi nút:
$$\text{IG}(T, a) = H(T) - H(T|a)$$

### 2.4. Extra Trees (Cây Cực Hạn Ngẫu Nhiên)
Gần tương tự như Random Forest nhưng ngưỡng phân tách $\theta$ cho từng đặc trưng được chọn ngẫu nhiên hoàn toàn thay vì tìm kiếm tối ưu. Thuật toán này giúp giảm đáng kể phương sai (variance) và nhạy bén hơn với các biến thể nhiễu mạng.

### 2.5. AdaBoost (Adaptive Boosting)
AdaBoost huấn luyện các cây quyết định 1 tầng (Decision Stumps) tuần tự. Các mẫu bị phân lớp sai ở vòng trước sẽ được nhân trọng số tăng lên trong vòng huấn luyện tiếp theo:
$$w_i^{(t+1)} = w_i^{(t)} \exp(-\alpha_t y_i h_t(x_i))$$

### 2.6. Gradient Boosting (Gradient Boosting Machine)
Xây dựng các cây tuần tự để xấp xỉ trực tiếp gradient âm của hàm mất mát (loss function) theo giá trị dự đoán, giúp mô hình hội tụ tốt hơn trên các không gian phi tuyến phức tạp:
$$F_m(x) = F_{m-1}(x) + \gamma_m h_m(x)$$

### 2.7. K-Nearest Neighbors (KNN - K Láng Giềng Gần Nhất)
KNN phân lớp dữ liệu dựa trên khoảng cách Euclidean trong không gian đặc trưng $d$-chiều đã được chuẩn hóa:
$$d(x, x') = \sqrt{\sum_{j=1}^{d} (x_j - x_j')^2}$$
Mẫu mới sẽ được gán nhãn theo biểu quyết đa số của $K$ láng giềng gần nhất.

### 2.8. Logistic Regression (Hồi Quy Logistic)
Mô hình tuyến tính sử dụng hàm logistic (sigmoid) để dự đoán xác suất luồng mạng thuộc lớp độc hại:
$$P(Y=1|X) = \sigma(W^T X + b) = \frac{1}{1 + e^{-(W^T X + b)}}$$

### 2.9. Linear SVM (Máy Vectơ Hỗ Trợ Tuyến Tính)
Tìm siêu phẳng phân tách lề tối đa (maximum margin hyperplane) để phân tách lớp DDoS và lớp Benign:
$$\min_{W, b} \frac{1}{2} \|W\|^2 + C \sum_{i=1}^N \xi_i \quad \text{s.t.} \quad y_i(W^T x_i + b) \ge 1 - \xi_i$$

### 2.10. Naive Bayes (Phân Lớp Bayes Ngây Thơ)
Mô hình xác suất dựa trên định lý Bayes với giả thiết độc lập có điều kiện giữa các đặc trưng:
$$P(Y=c|X) \propto P(Y=c) \prod_{j=1}^{d} P(X_j|Y=c)$$
Với giả thiết đặc trưng liên tục tuân theo phân phối xác suất Gaussian.

### 2.11. Isolation Forest (Rừng Cô Lập - Không Giám Sát)
Huấn luyện độc quyền trên dữ liệu lưu lượng bình thường (Benign) nhằm phát hiện bất thường (Anomaly Detection). Nó cô lập các điểm dữ liệu bằng cách chia cắt ngẫu nhiên. Điểm dị thường được tính bằng:
$$s(x, n) = 2^{-\frac{\mathbb{E}(h(x))}{c(n)}}$$
Các luồng có $s \to 1$ có độ sâu trung bình ngắn, dễ bị cô lập $\implies$ Cảnh báo tấn công bất thường (Zero-day).

---

## 3. Thiết Lập Thực Nghiệm: Dữ Liệu Thực Tế CICIDS2017

Để đáp ứng yêu cầu thực nghiệm ngoài trên tập dữ liệu thực tế, hệ thống tiến hành tải trực tiếp tệp ghi lưu lượng thực tế **Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv** từ thư mục `data/raw/` của bộ dữ liệu CICIDS2017 gốc.
* **Quy mô mẫu đánh giá:** Rút ngẫu nhiên **50,000 luồng mạng** độc lập từ file CSV thô (dung lượng 77MB) để thực nghiệm kiểm thử.
* **Phân phối nhãn thực tế:**
  - **Tấn công DDoS (DDoS Attack):** 28,419 luồng (56.84%)
  - **Lưu lượng hợp lệ (Benign):** 21,581 luồng (43.16%)
* **Đặc tính dữ liệu:** Dữ liệu chứa các cuộc tấn công DDoS thực tế dạng LOIC/HOIC cùng các luồng truy cập thật của người dùng mạng, không sử dụng dữ liệu giả lập.

---

## 4. Phân Tích Thực Nghiệm Chi Tiết Qua Từng Biểu Đồ

Kết quả thực nghiệm của 10 mô hình giám sát trên tập dữ liệu thực tế 50,000 dòng được thống kê định lượng dưới bảng sau:

| Mô hình | Accuracy (Chính xác) | DDoS Recall (Bảo mật) | Khách Sẵn sàng (Availability) |
| :--- | :---: | :---: | :---: |
| **Gradient Boosting** | **99.68%** | **99.83%** | 99.49% |
| **Random Forest** | **99.62%** | **99.83%** | 99.34% |
| **XGBoost** | **99.56%** | **99.81%** | 99.24% |
| **Decision Tree** | 99.45% | 99.81% | 98.99% |
| **K-Nearest Neighbors**| 99.15% | 99.77% | 98.33% |
| **AdaBoost** | 99.08% | 99.88% | 98.03% |
| **Extra Trees** | 98.27% | 99.90% | 96.14% |
| **Logistic Regression** | 86.18% | 99.95% | 68.06% |
| **Linear SVM** | 86.17% | 99.95% | 68.03% |
| **Naive Bayes** | 79.35% | 99.96% | 52.21% |

Dưới đây là phân tích chi tiết từng biểu đồ thu được từ thực nghiệm:

### 4.1. Phân tích Hình 1: Lưới Ma Trận Nhầm Lẫn (confusion_matrices.png)
Biểu đồ 5x2 chứa 10 heatmaps thể hiện chính xác số lượng mẫu phân loại đúng/sai (True/False Positive/Negative) của từng mô hình trên dữ liệu thực tế:
* **Nhóm mô hình cây phân lớp (GB, RF, XGB, DT, Ada, ET):** Đạt tỷ lệ phân loại cực kỳ chính xác. Ví dụ, Gradient Boosting chỉ chặn nhầm 110 khách hàng (FP = 110) và chỉ bỏ sót 49 luồng DDoS (FN = 49) trên tổng số 50,000 dòng kiểm thử thực tế.
* **Nhóm mô hình Tuyến tính (Logistic, SVM) & Naive Bayes:** Đạt Recall rất cao (FN < 15, nghĩa là bỏ sót cực ít DDoS) nhưng lại gây ra lượng cảnh báo sai khổng lồ. Naive Bayes chặn nhầm đến 10,314 khách hàng hợp lệ (FP = 10,314), làm sụt giảm nghiêm trọng tính sẵn sàng của hệ thống mạng (TNR chỉ đạt 52.21%).
* **Decision Tree đơn lẻ:** Đạt kết quả xuất sắc (TNR 98.99%, Recall 99.81%), cho thấy tính phân tách rõ ràng của các đặc trưng DDoS LOIC gốc trong CICIDS2017.

### 4.2. Phân tích Hình 2: So sánh Đường cong ROC và Precision-Recall (availability_comparison.png)
* **Đường cong ROC:** Các mô hình dạng cây quyết định và lân cận (Gradient Boosting, Random Forest, XGBoost, KNN, AdaBoost) đều có đường cong ROC áp sát góc trên bên trái với AUC đạt mức lý tưởng từ 0.992 đến 0.999.
* **Đường cong Precision-Recall:** Thể hiện rõ sự suy giảm độ tin cậy của nhóm tuyến tính và Naive Bayes. Precision của Naive Bayes sụt giảm mạnh từ giai đoạn đầu, phản ánh tỷ lệ báo động giả (False Alarms) cực lớn, gây quá tải cho bộ phận quản trị mạng nếu đưa vào vận hành thực tế.

### 4.3. Phân tích Hình 3: Lưới Đồ Thị Ngưỡng Quyết Định (tradeoff_curves.png)
* **Các mô hình cây quyết định (GB, RF, XGB, DT):** Hai đường Recall (đỏ) và TNR (xanh lá) giao nhau cực kỳ trễ ở sát ngưỡng 0.95 và duy trì ở mức cao >99% tại ngưỡng mặc định 0.5. Người vận hành có thể an tâm sử dụng ngưỡng mặc định 0.5.
* **Các mô hình tuyến tính (SVM, Logistic) & Naive Bayes:** Hai đường này giao nhau rất sớm ở khoảng ngưỡng 0.1 - 0.2. Tại ngưỡng mặc định 0.5, TNR của chúng chỉ đạt từ 52.2% đến 68.1% (chặn nhầm 32% - 48% khách hàng). Để bảo vệ tính sẵn sàng cho khách hàng trên các mô hình tuyến tính này, người quản trị buộc phải nâng ngưỡng quyết định lên mức >0.9.

### 4.4. Phân tích Hình 4: Ranh Giới Quyết Định 2D (decision_boundaries.png)
* **Các mô hình dạng cây:** Tạo ra vùng ranh giới quyết định rất mạch lạc và vuông vắn (các đường bậc thang song song với trục). Random Forest, Gradient Boosting và XGBoost bao bọc chặt chẽ các cụm điểm dữ liệu DDoS màu đỏ mà không xâm phạm vào vùng màu xanh của khách hàng.
* **Nhóm Tuyến tính (SVM, Logistic):** Siêu phẳng phân chia dạng đường thẳng bị ép nghiêng quá mức, lấn sâu vào khu vực phân bố của khách hàng để cố gắng đạt Recall 99.95% cho DDoS, dẫn đến vùng nhận diện nhầm lớn.
* **KNN & Naive Bayes:** KNN tạo ra biên phân chia rất chi tiết bao quanh các mật độ điểm lân cận, còn Naive Bayes tạo ra các đường phân mức xác suất dạng cong elip trơn, nhưng cắt quá nhiều vào vùng phân bố Benign.

---

## 5. Đánh Giá Tổng Quát & Khuyến Nghị Vận Hành

1. **Nhóm thuật toán dạng cây (Gradient Boosting, Random Forest, XGBoost):**
   * **Đánh giá:** Hoạt động cực kỳ hoàn hảo trên dữ liệu thực với độ chính xác >99.5% và độ cân bằng Bảo mật vs Sẵn sàng tối ưu (>99%).
   * **Vận hành:** Nên ưu tiên sử dụng các mô hình này làm bộ dò quét chính tại các chốt chặn tự động của hệ thống, giúp bảo đảm an toàn thông tin mà không làm ảnh hưởng đến tính sẵn sàng dịch vụ của khách hàng.
2. **Các mô hình tuyến tính (SVM, Logistic Regression):**
   * **Đánh giá:** Khả năng phát hiện DDoS gần như tuyệt đối (99.95%) nhưng lại có xu hướng chặn nhầm lượng lớn khách hàng (32%), gây gián đoạn dịch vụ nghiêm trọng nếu chạy tự động.
   * **Vận hành:** Có thể tích hợp kiểm tra chéo (Cross-validation) bằng các mô hình tuyến tính khi phát hiện nghi ngờ cao ở lớp lọc phụ.
3. **Mô hình Không giám sát (Isolation Forest):**
   * **Đánh giá:** Isolation Forest đóng vai trò chốt chặn phụ độc lập để phát hiện các cuộc tấn công Zero-day mới chưa có nhãn huấn luyện trong tập dữ liệu gốc.
   * **Vận hành:** Chạy ngầm song song để phát hiện bất thường và kích hoạt cảnh báo sớm.
