# BÁO CÁO NGHIÊN CỨU & THỰC NGHIỆM CHUYÊN SÂU
## Đề tài: Tìm Hiểu Về Xây Dựng Hệ Thống Phát Hiện Xâm Nhập Mạng (IDS) Với Trí Tuệ Nhân Tạo (AI)

**Nội dung thực hiện:**
1. Khảo sát và tiền xử lý tập dữ liệu **Kaggle CICIDS2017** làm nền tảng huấn luyện IDS.
2. Xây dựng, huấn luyện và so sánh **10 mô hình học máy phân lớp có giám sát** và **1 mô hình không giám sát (Isolation Forest)**.
3. Thiết lập môi trường thực nghiệm ngoài: Mô phỏng lưu lượng capture thực tế quy mô lớn (50,000 dòng luồng mạng) pha trộn hành vi tinh vi để đánh giá tính sẵn sàng máy chủ (**Availability**) song song với tính bảo mật (**Security**).
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

## 3. Thiết Lập Thực Nghiệm: Mô Phỏng Capture Ngoài Quy Mô Lớn

Để đáp ứng yêu cầu kiểm thử mô hình thực tế bằng nguồn dữ liệu capture bên ngoài (External Captured Data), chúng tôi đã thiết kế một module giả lập mạng nâng cao (`run_availability_test.py`) sinh ra **50,000 dòng luồng mạng** trộn lẫn giữa:
* **80% Tấn công DDoS (40,000 dòng):** Bao gồm 85% DDoS truyền thống (gói nhỏ dồn dập, Fwd Packet Length Max từ 6 - 20 bytes) và 15% DDoS nâng cao (HTTP POST Flood giả lập payload lớn, Fwd Packet Length Max từ 800 - 2500 bytes nhằm vượt qua bộ lọc độ dài thô).
* **20% Khách hàng Hợp lệ (10,000 dòng):** Bao gồm 85% kết nối Weather API thông thường (Fwd Packet Length Max từ 100 - 1500 bytes) lấy dữ liệu thời gian thực từ Open-Meteo API và 15% kết nối Keep-Alive/Ping điều khiển dung lượng cực nhỏ (chồng lấn lên dải phân phối của DDoS thô).
* **Nhiễu Gaussian mạng thực tế:** Tích hợp 4% biến động ngẫu nhiên trên toàn bộ các cột đặc trưng để tạo ra độ nhiễu và thử thách độ bền vững (robustness) của mô hình.

---

## 4. Phân Tích Thực Nghiệm Chi Tiết Qua Từng Biểu Đồ

Kết quả thực nghiệm của 10 mô hình giám sát trên tập dữ liệu capture ngoài 50,000 dòng được thống kê định lượng dưới bảng sau:

| Mô hình | Accuracy (Chính xác) | DDoS Recall (Bảo mật) | Khách Sẵn sàng (Availability) |
| :--- | :---: | :---: | :---: |
| **XGBoost** | **99.06%** | **99.75%** | 96.29% |
| **AdaBoost** | **97.25%** | 96.89% | 98.67% |
| **Naive Bayes** | 96.30% | 99.24% | 84.52% |
| **Linear SVM** | 92.32% | 91.97% | 93.75% |
| **Logistic Regression** | 89.28% | 87.89% | 94.80% |
| **Extra Trees** | 87.59% | 84.50% | **99.95%** |
| **Random Forest** | 79.49% | 74.36% | **100.00%** |
| **Gradient Boosting** | 79.39% | 74.32% | **99.67%** |
| **K-Nearest Neighbors**| 77.52% | 77.04% | 79.44% |
| **Decision Tree** | 67.62% | 74.41% | 40.49% |

Dưới đây là phân tích chi tiết từng biểu đồ thu được từ thực nghiệm:

### 4.1. Phân tích Hình 1: Lưới Ma Trận Nhầm Lẫn (confusion_matrices.png)
Biểu đồ 5x2 chứa 10 heatmaps thể hiện chính xác số lượng mẫu phân loại đúng/sai (True/False Positive/Negative) của từng mô hình:
* **Random Forest & Extra Trees:** Đạt số lượng báo động giả bằng 0 ($FP = 0$ đối với Random Forest và $FP = 5$ đối với Extra Trees). Điều này đảm bảo tính sẵn sàng tuyệt đối cho khách hàng nhưng lại bỏ lọt đến hơn $10,000$ luồng DDoS ($FN \approx 10,256$).
* **XGBoost & AdaBoost:** Giảm thiểu tối đa lỗi bỏ sót DDoS ($FN = 99$ đối với XGBoost và $FN = 1,244$ đối với AdaBoost), ngăn chặn hiệu quả việc làm sập tài nguyên máy chủ.
* **Naive Bayes:** Mặc dù có độ chính xác tương đối cao, nhưng mô hình này gây ra báo động sai cực kỳ nhiều ($FP = 1,548$, tức chặn nhầm 15.48% khách hàng hợp lệ).
* **Decision Tree:** Đạt kết quả kém nhất với số lượng phân lớp sai khổng lồ ($FP = 5,951$, tức chặn nhầm hơn 59% khách hàng bình thường), thể hiện sự quá khớp của một cây quyết định đơn lẻ.

### 4.2. Phân tích Hình 2: So sánh Đường cong ROC và Precision-Recall (availability_comparison.png)
Biểu đồ so sánh trực tiếp hiệu năng phân lớp tổng quát:
* **Đường cong ROC:** Các mô hình **XGBoost**, **AdaBoost** và **Naive Bayes** áp sát góc trên bên trái với chỉ số AUC lần lượt đạt $0.998$, $0.995$ và $0.988$. Điều này chứng minh các mô hình này có khả năng phân biệt lớp tấn công tốt nhất. Ngược lại, **Decision Tree** đơn lẻ có đường cong ROC tiệm cận đường chéo ngẫu nhiên ($AUC \approx 0.67$), thể hiện hiệu năng phân biệt kém.
* **Đường cong Precision-Recall:** Trong điều kiện mất cân bằng dữ liệu của capture ngoài (80% tấn công, 20% khách), đường cong PR của **XGBoost** và **AdaBoost** duy trì ở mức cao gần $1.0$ trên hầu hết dải Recall. Điều này khẳng định khi chúng cảnh báo DDoS, độ tin cậy đạt gần $100\%$, không làm ảnh hưởng đến tài nguyên máy chủ.

### 4.3. Phân tích Hình 3: Lưới Đồ Thị Ngưỡng Quyết Định (tradeoff_curves.png)
Đồ thị 5x2 mô tả sự thay đổi của Recall chặn DDoS (đỏ) và TNR Khách hàng (xanh lá) theo ngưỡng quyết định (Threshold từ 0.0 đến 1.0):
* **XGBoost & AdaBoost:** Hai đường Recall và TNR giao nhau rất muộn (ở ngưỡng threshold $\approx 0.85$ - $0.90$). Tại ngưỡng mặc định $0.5$, cả hai chỉ số đều đạt mức tối ưu (>96%). Người quản trị có thể điều chỉnh threshold lên mức $0.8$ để đạt được $98.5\%$ Customer Availability trong khi vẫn duy trì được $97\%$ DDoS Block Rate.
* **Random Forest & Extra Trees:** Đường TNR (xanh lá) nằm ngang tiệm cận mức $100\%$ xuyên suốt mọi ngưỡng threshold từ 0.1 đến 0.9. Ngược lại, đường Recall chặn DDoS (đỏ) sụt giảm rất dốc từ ngưỡng $0.4$. Điều này phản ánh tính bảo thủ cao của mô hình Bagging: mô hình ưu tiên bảo vệ khách hàng trước, chấp nhận bỏ lọt DDoS nếu không có bằng chứng cực kỳ rõ ràng.
* **Logistic Regression & Linear SVM:** Hai đường giao nhau ở ngưỡng cân bằng $\approx 0.5$ với cả hai chỉ số đều nằm trong khoảng $88\% - 94\%$. Ranh giới quyết định tuyến tính khiến mô hình có độ nhạy threshold rất đều đặn (dạng đường thẳng tuyến tính).

### 4.4. Phân tích Hình 4: Ranh Giới Quyết Định 2D (decision_boundaries.png)
Hình ảnh 5x2 trực quan hóa cách các mô hình phân chia không gian đặc trưng giữa `Flow Duration` (trục hoành - giây) và `Fwd Packet Length Max` (trục tung - bytes):
* **Cây Quyết định đơn lẻ (Decision Tree):** Tạo ra các phân vùng ô cờ vuông vức, đứt gãy và chắp vá. Điều này thể hiện rõ hiện tượng quá khớp (overfitting) cục bộ vào các điểm dữ liệu nhiễu.
* **Random Forest & Extra Trees:** Các ranh giới quyết định dạng bậc thang song song với các trục tọa độ (axis-aligned hyperplanes). Do biểu quyết trung bình của nhiều cây, các biên này mượt mà hơn Decision Tree nhưng vẫn mang hình khối góc cạnh rõ rệt. Vùng đỏ (tấn công) bị thu hẹp đáng kể về phía góc dưới, giải thích lý do tại sao chúng bỏ sót các cuộc tấn công DDoS có gói tin lớn.
* **XGBoost & AdaBoost:** Tạo ra các vùng quyết định phi tuyến uốn lượn mềm mại bao phủ cực tốt các cụm dữ liệu DDoS màu đỏ. Sự kết hợp của nhiều cây yếu tuần tự giúp mô hình tạo ra ranh giới quyết định linh hoạt nhất, bao bọc chuẩn xác kể cả các cuộc tấn công DDoS HTTP POST nâng cao (gói tin lớn).
* **Linear SVM & Logistic Regression:** Ranh giới quyết định là một đường thẳng (siêu phẳng tuyến tính 2D) phân chia không gian làm hai nửa. Do phân phối của DDoS nâng cao và Khách hàng điều khiển bị chồng lấn phi tuyến lên nhau, đường thẳng này không thể phân tách hoàn hảo, buộc phải chấp nhận sự pha trộn sai số ở cả hai phía biên.
* **K-Nearest Neighbors (KNN):** Ranh giới quyết định tạo thành các đảo nhỏ cô lập bao quanh các cụm điểm dữ liệu cục bộ, rất nhạy cảm với mật độ điểm lân cận.
* **Naive Bayes:** Ranh giới quyết định có dạng đường cong elip trơn nhẵn, phản ánh các đường đồng mức xác suất của phân phối Gaussian giả định. Do giả định các biến độc lập, biên quyết định này không phản ánh tốt các tương quan chéo, dẫn đến việc cắt quá sâu vào vùng xanh của khách hàng.

---

## 5. Đánh Giá Tổng Quát & Khuyến Nghị Vận Hành

1. **Nhóm Học tăng cường (Boosting - XGBoost, AdaBoost):**
   * **Đánh giá:** Đạt hiệu năng toàn diện nhất. XGBoost là mô hình xuất sắc nhất với độ chính xác 99.06% và Recall chặn DDoS đạt 99.75%.
   * **Vận hành:** Khuyên dùng làm bộ lọc lưu lượng chính (Firewall / Reverse Proxy) cho hệ thống để ngăn ngừa hoàn toàn nguy cơ sập máy chủ do DDoS dồn dập.
2. **Nhóm Rừng cây (Bagging - Random Forest, Extra Trees):**
   * **Đánh giá:** Bảo vệ hoàn hảo trải nghiệm khách hàng (TNR $\approx 100\%$).
   * **Vận hành:** Thích hợp triển khai ở môi trường mạng nội bộ hoặc các dịch vụ tài chính nhạy cảm nơi việc chặn nhầm một giao dịch hợp lệ của khách hàng đem lại thiệt hại lớn hơn nhiều so với việc trễ nải phát hiện tấn công.
3. **Nhóm Tuyến tính & Xác suất (SVM, Logistic, Naive Bayes):**
   * **Đánh giá:** Naive Bayes học cực nhanh và nhạy bén với DDoS nhưng gây phiền toái lớn cho khách hàng. SVM và Logistic ổn định nhưng giới hạn bởi tính tuyến tính.
   * **Vận hành:** Có thể dùng làm các bộ phân loại phụ (Secondary Check) hoặc chạy song song để tham chiếu kiểm tra chéo.
4. **Mô hình Không giám sát (Isolation Forest):**
   * **Đánh giá:** Mặc dù độ chính xác trên tập DDoS đã biết không cao bằng XGBoost, Isolation Forest là chốt chặn duy nhất có khả năng phát hiện các cuộc tấn công mới chưa có mẫu huấn luyện (Zero-day) nhờ cơ chế cô lập điểm dị thường.
   * **Vận hành:** Khuyên dùng chạy ngầm song song để phát hiện bất thường và kích hoạt cảnh báo sớm cho đội ngũ quản trị hệ thống (SOC).
