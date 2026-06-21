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

### 1.2. Phân tích lựa chọn đặc trưng bằng toán học (Feature Selection)
Để đảm bảo tính khoa học và tối ưu hiệu năng sniffer thời gian thực, hệ thống đã chạy đánh giá xếp hạng đặc trưng mạng dựa trên độ lợi thông tin **Random Forest Gini Importance** trên tập dữ liệu huấn luyện (ngày thứ Ba, Tư, Năm). Biểu đồ xếp hạng 20 đặc trưng mạng quan trọng nhất được lưu tại [feature_importance.png](file:///C:/Users/Hikari-Rainbow/antigravity/wise-einstein/data/external/feature_importance.png).

Kết quả chỉ ra các thuộc tính liên quan đến độ lệch chuẩn kích thước gói (`Bwd Packet Length Std`, `Packet Length Std`) và kích thước cửa sổ Forward (`Init_Win_bytes_forward`) đóng góp lượng thông tin cao nhất (>10%). 15 đặc trưng cốt lõi được lựa chọn trong dự án bao gồm:
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

Các đặc trưng này đại diện cho các thuộc tính dễ bắt gói và tính toán nhanh, đồng thời là các biến thay thế (surrogates) mạnh mẽ cho các đặc trưng đứng đầu về Gini Importance, giúp cân bằng hoàn hảo giữa tốc độ sniffer và độ chính xác phân lớp.

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

## 3. Thiết Lập Thực Nghiệm & Phân Chia Môi Trường Tránh Rò Rỉ Dữ Liệu

Để đảm bảo tính khoa học và loại bỏ hoàn toàn hiện tượng **Rò rỉ dữ liệu (Data Leakage)** do tính tương quan thời gian của các gói tin mạng, hệ thống phân chia môi trường thực nghiệm độc lập theo các ngày:
* **Tập Huấn luyện (Training Set):** Gộp mẫu ngẫu nhiên từ dữ liệu các ngày **Thứ Ba, Thứ Tư, Thứ Năm** (chứa lưu lượng thông thường Benign và DoS, Web Attacks, Infiltration). Quy mô tập huấn luyện sau khi cân bằng undersampling là 15,000 dòng.
* **Tập Kiểm thử Mù (Blind Test Set):** Hoàn toàn độc lập trên tệp lưu lượng **Friday Afternoon DDoS** (`Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv`).
* **Quy mô Blind Test:** Rút ngẫu nhiên **50,000 luồng mạng** độc lập từ file CSV ngày thứ Sáu:
  - **Tấn công DDoS (DDoS Attack):** 28,419 luồng (56.84%)
  - **Lưu lượng hợp lệ (Benign):** 21,581 luồng (43.16%)

---

## 4. Phân Tích Thực Nghiệm Chi Tiết Qua Từng Biểu Đồ

### 4.1. Khảo sát hiện tượng Quá khớp (Overfitting) trên Decision Tree
Để chứng minh hạn chế của mô hình cây đơn lẻ, chúng tôi tiến hành khảo sát độ chính xác của Decision Tree trên tập Train vs tập Test dưới các giới hạn chiều sâu cây (`max_depth`) khác nhau:

| Độ sâu tối đa (max_depth) | Accuracy Tập Train | Accuracy Tập Test | Khoảng cách Quá khớp (Gap) |
| :--- | :---: | :---: | :---: |
| **3** | 85.86% | 86.27% | -0.41% |
| **5** | 92.88% | 92.33% | 0.54% |
| **8** | 95.97% | 95.20% | 0.78% |
| **12** | 98.01% | 96.93% | 1.07% |
| **20** | 99.16% | 97.07% | 2.09% |
| **Không giới hạn (None)** | **99.48%** | **97.07%** | **2.41%** |

*Ý nghĩa:* Khi không giới hạn độ sâu (None), Decision Tree đạt 99.48% trên tập Train nhưng tụt xuống 97.07% trên tập Test. Hiện tượng quá khớp xảy ra do cây quyết định đơn lẻ cố gắng chia cắt không gian mẫu quá mịn để ghi nhớ tập Train, làm giảm khả năng tổng quát hóa trên dữ liệu thực tế.

### 4.2. Bảng số liệu tổng hợp hiệu năng thực nghiệm mù (Blind Test)
Dưới đây là bảng số liệu thống kê kết quả chạy thực nghiệm 50,000 luồng mạng đối với 10 mô hình học máy:

| Mô hình | Accuracy | Recall (DDoS) | TNR (Sẵn sàng) | P(Attack\|Alert) θ=0.1% | P(Attack\|Alert) θ=5% |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **AdaBoost** | 91.88% | 98.35% | 83.36% | 0.59% | 23.73% |
| **Linear SVM** | 91.57% | 91.33% | 91.88% | 1.11% | 37.19% |
| **Logistic Regression**| 89.97% | 88.54% | 91.85% | 1.08% | 36.38% |
| **Naive Bayes** | 89.27% | 99.76% | 75.46% | 0.41% | 17.62% |
| **Extra Trees** | 79.10% | 63.69% | 99.39% | **9.51%** | **84.67%** |
| **K-Nearest Neighbors**| 78.95% | 69.68% | 91.16% | 0.78% | 29.32% |
| **Random Forest** | 78.83% | 63.75% | 98.69% | 4.64% | 71.90% |
| **Decision Tree** | 77.86% | 63.39% | 96.90% | 2.01% | 51.88% |
| **Gradient Boosting** | 76.47% | 63.89% | 93.04% | 0.91% | 32.56% |
| **XGBoost** | 75.31% | 63.75% | 90.52% | 0.67% | 26.15% |

### 4.3. Phân tích Hình 1: Lưới Ma Trận Nhầm Lẫn (confusion_matrices.png)
* **Nhóm tuyến tính (SVM, Logistic) & Naive Bayes:** Đạt Recall rất cao (đều >88%, cao nhất là Naive Bayes 99.76%), tức là bỏ sót cực ít DDoS. Tuy nhiên, tính sẵn sàng dịch vụ (TNR) bị kéo thấp (75% - 91%), chặn nhầm một lượng lớn khách hàng lành mạnh (ví dụ Naive Bayes chặn nhầm 5,296 khách hàng trên tổng số 21,581 luồng Benign).
* **Nhóm mô hình cây (Random Forest, Extra Trees):** Đạt tính sẵn sàng rất cao (TNR lần lượt là 98.69% và 99.39%), hầu như không chặn nhầm khách thường. Nhưng khi gặp cuộc tấn công DDoS hoàn toàn mới ở ngày thứ Sáu, Recall của chúng bị giảm mạnh xuống mức 63.6% - 63.7%.

### 4.4. Phân tích Hình 2: Đường cong ROC và Precision-Recall (availability_comparison.png)
* **Precision-Recall Curve:** Thể hiện rõ nét nhược điểm của các mô hình tuyến tính và Naive Bayes. Đường cong Precision của các mô hình này bị tụt dốc nhanh chóng từ những giai đoạn đầu, phản ánh độ tin cậy của cảnh báo rất thấp do lượng báo động giả khổng lồ.

### 4.5. Phân tích Hình 3: Lưới Đồ Thị Ngưỡng Quyết Định (tradeoff_curves.png)
* **Nhóm mô hình cây:** Hai đường Recall (đỏ) và TNR (xanh lá) giao nhau ở khoảng ngưỡng 0.4 - 0.6. Tại ngưỡng mặc định 0.5, TNR đạt mức rất cao >98% nhưng Recall chỉ ở mức khoảng 63%.
* **Nhóm mô hình tuyến tính & Naive Bayes:** Hai đường này giao nhau rất sớm ở khoảng ngưỡng 0.1 - 0.3. Tại ngưỡng mặc định 0.5, các mô hình này đạt Recall cao nhưng TNR lại bị kéo thấp nghiêm trọng.

### 4.6. Phân tích Hình 4: Ranh Giới Quyết Định 2D (decision_boundaries.png)
* **Nhóm Tuyến tính (SVM, Logistic):** Siêu phẳng phân chia dạng đường thẳng bị ép nghiêng lớn, cắt lấn sâu vào khu vực phân bố của khách hàng để cố gắng bao trọn các điểm DDoS, dẫn đến vùng nhận diện nhầm lớn.
* **Các mô hình dạng cây:** Tạo ra ranh giới dạng bậc thang vuông vắn ôm sát các cụm dữ liệu, giúp bảo vệ tối đa lớp khách hàng nhưng lại bỏ sót một số luồng DDoS mới trên tập test mù.

### 4.7. Phân tích Toán học về Ngụy biện tỷ lệ cơ sở (Base Rate Fallacy)
Áp dụng định lý Bayes để tính toán xác suất thực tế một cảnh báo của IDS là cuộc tấn công thực sự $P(\text{Attack} | \text{Alert})$:
$$P(\text{Attack} | \text{Alert}) = \frac{\text{Recall} \times \theta}{\text{Recall} \times \theta + (1 - \text{TNR}) \times (1 - \theta)}$$
* Với tỷ lệ cơ sở thực tế $\theta = 0.1\%$, ngay cả mô hình Extra Trees có TNR cao lý tưởng (99.39%, tức FPR = 0.61%), xác suất $P(\text{Attack} | \text{Alert})$ cũng chỉ đạt **9.51%** (có nghĩa là 90.49% cảnh báo đưa ra là báo động giả).
* Đối với Naive Bayes (TNR = 75.46%), xác suất này tụt xuống mức cực thấp là **0.41%** (99.59% cảnh báo là chặn nhầm khách).
* Điều này chứng minh rằng chỉ số TNR cao trên tập dữ liệu cân bằng (50/50) là một cái bẫy ngụy biện. Khi đưa vào môi trường mạng tự nhiên có tỷ lệ tấn công cực nhỏ, số lượng cảnh báo giả sẽ lấn át hoàn toàn cảnh báo thật.

---

## 5. Đánh Giá Tổng Quát & Khuyến Nghị Vận Hành

1. **Sự đánh đổi khốc liệt giữa Bảo mật và Sẵn sàng:** Thực nghiệm mù chứng minh không một mô hình đơn lẻ nào đạt hiệu năng hoàn hảo ở cả hai khía cạnh. Nhóm cây (RF, Extra Trees) ưu tiên sự sẵn sàng của khách hàng nhưng bỏ sót tấn công, còn nhóm tuyến tính/boosting (AdaBoost, SVM) ưu tiên chặn bắt nhưng gây tắc nghẽn cho khách thường.
2. **Khuyến nghị kiến trúc IDS phân tầng (Sequential/Cascading Filtering):**
   * **Lớp 1 (Màng lọc sơ cấp - High Recall Filter):** Sử dụng các mô hình có độ nhạy cực cao như AdaBoost (Recall 98.35%) hoặc Naive Bayes (Recall 99.76%) để đóng vai trò chốt chặn đầu tiên bắt giữ hầu như toàn bộ các cuộc tấn công. Tuyệt đối không dùng mô hình có Recall thấp ở lớp ngoài cùng (như Random Forest, Recall ~63.75%) vì nó sẽ bỏ lọt ngay 36.25% các cuộc tấn công và khóa cứng Recall toàn hệ thống ở mức trần này.
   * **Lớp 2 (Màng lọc thứ cấp - High Precision Filter):** Các luồng bị gán nhãn tấn công/nghi ngờ bởi Lớp 1 (chứa nhiều cảnh báo giả của khách thường do TNR Lớp 1 thấp) sẽ được đẩy tiếp qua Lớp 2 sử dụng Random Forest hoặc Extra Trees (TNR > 98.6%). Lớp 2 thực hiện vai trò kiểm tra chéo, lọc sạch và loại bỏ các cảnh báo giả để giải phóng băng thông cho người dùng lành mạnh, giải quyết triệt để bài toán Base Rate Fallacy.
   * **Lớp 3 (Anomaly Detection):** Sử dụng Isolation Forest chạy ngầm song song để nhận diện các hành vi bất thường mới (Zero-day) chưa có dữ liệu gán nhãn huấn luyện.
