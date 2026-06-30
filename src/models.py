import os
import joblib
import numpy as np
import sys
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, AdaBoostClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import IsolationForest
import xgboost as xgb

# Đảm bảo import được config từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class IDSSupervisedModel:
    def __init__(self, model_type='rf'):
        self.model_type = model_type
        self.model = None
        self.model_path = os.path.join(config.MODELS_DIR, f"ids_{model_type}.pkl")

    def build(self):
        if self.model_type == 'rf':
            self.model = RandomForestClassifier(**config.RF_PARAMS)
        elif self.model_type == 'xgb':
            params = config.XGB_PARAMS.copy()
            cuda_supported = False
            try:
                # Thử nghiệm xem môi trường hiện tại có hỗ trợ CUDA trong XGBoost không
                test_clf = xgb.XGBClassifier(n_estimators=1, max_depth=1, tree_method='hist', device='cuda')
                test_clf.fit([[0]], [0])
                cuda_supported = True
            except Exception:
                cuda_supported = False
                
            if cuda_supported:
                params['tree_method'] = 'hist'
                params['device'] = 'cuda'
                print("[🚀 CUDA] Phát hiện GPU tương thích! Đã tối ưu mô hình XGBoost chạy trên CUDA.")
            else:
                params.pop('device', None)
                print("[💻 CPU] Không phát hiện CUDA hoặc driver không tương thích. Chạy XGBoost bằng CPU.")
                
            self.model = xgb.XGBClassifier(**params)
        elif self.model_type == 'dt':
            self.model = DecisionTreeClassifier(**config.DT_PARAMS)
        elif self.model_type == 'et':
            self.model = ExtraTreesClassifier(**config.ET_PARAMS)
        elif self.model_type == 'ada':
            self.model = AdaBoostClassifier(**config.ADA_PARAMS)
        elif self.model_type == 'gb':
            self.model = GradientBoostingClassifier(**config.GB_PARAMS)
        elif self.model_type == 'knn':
            self.model = KNeighborsClassifier(**config.KNN_PARAMS)
        elif self.model_type == 'lr':
            self.model = LogisticRegression(**config.LR_PARAMS)
        elif self.model_type == 'svm':
            self.model = LinearSVC(**config.SVM_PARAMS)
        elif self.model_type == 'nb':
            self.model = GaussianNB(**config.NB_PARAMS)
        else:
            raise ValueError(f"Không hỗ trợ mô hình học máy: {self.model_type}")
        print(f"[+] Khởi tạo thành công mô hình: {self.model_type}")

    def train(self, X_train, y_train):
        print(f"[*] Đang huấn luyện mô hình {self.model_type}...")
        self.model.fit(X_train, y_train)
        print(f"[+] Huấn luyện xong!")

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)[:, 1]
        elif hasattr(self.model, "decision_function"):
            df = self.model.decision_function(X)
            # Dùng Sigmoid để đưa về miền [0, 1]
            return 1 / (1 + np.exp(-df))
        else:
            # Fallback nếu không có cả hai (ví dụ một số mô hình không chuẩn hóa)
            return self.model.predict(X)

    def save(self):
        joblib.dump(self.model, self.model_path)
        print(f"[+] Mô hình được lưu tại: {self.model_path}")

    def load(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"[+] Tải mô hình {self.model_type} thành công từ {self.model_path}")
        else:
            raise FileNotFoundError(f"Không tìm thấy file mô hình tại {self.model_path}")


class IDSUnsupervisedModel:
    """
    Mô hình học không giám sát dùng để phát hiện bất thường (Anomaly Detection).
    Phù hợp để phát hiện các cuộc tấn công mới chưa từng thấy (Zero-day).
    Sử dụng Isolation Forest để minh họa (hoặc làm nền tảng trước khi phát triển Autoencoder).
    """
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(config.MODELS_DIR, "ids_anomaly_iforest.pkl")

    def train(self, X_benign_only):
        """Chỉ huấn luyện trên dữ liệu bình thường (Benign)"""
        print("[*] Đang huấn luyện Isolation Forest cho Anomaly Detection...")
        self.model = IsolationForest(contamination=0.01, random_state=42, n_jobs=-1)
        self.model.fit(X_benign_only)
        print("[+] Huấn luyện xong Isolation Forest!")

    def predict(self, X):
        # Isolation Forest trả về -1 cho dị thường, 1 cho bình thường
        preds = self.model.predict(X)
        # Chuyển đổi: 0 = Benign, 1 = Attack (dị thường)
        binary_preds = [1 if p == -1 else 0 for p in preds]
        return binary_preds

    def save(self):
        joblib.dump(self.model, self.model_path)
        print(f"[+] Mô hình Anomaly được lưu tại: {self.model_path}")

    def load(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"[+] Tải mô hình Anomaly thành công từ {self.model_path}")
        else:
            raise FileNotFoundError(f"Không tìm thấy file mô hình tại {self.model_path}")


class CascadedIDSModel:
    """
    Hệ thống phát hiện xâm nhập mạng phân tầng (Cascaded IDS):
    - Lớp 1: Mô hình học có giám sát có Recall cao (mặc định: AdaBoost - 'ada')
    - Lớp 2: Mô hình học có giám sát có TNR/Precision cao (mặc định: Extra Trees - 'et')
    - Lớp 3: Mô hình học không giám sát phát hiện dị thường (mặc định: Isolation Forest)
    """
    def __init__(self, layer1_type='ada', layer2_type='et'):
        self.layer1_type = layer1_type
        self.layer2_type = layer2_type
        self.layer1 = IDSSupervisedModel(model_type=layer1_type)
        self.layer2 = IDSSupervisedModel(model_type=layer2_type)
        self.anomaly = IDSUnsupervisedModel()
        self.model_type = "cascaded"
        self.has_anomaly = False

    def load(self):
        print(f"[*] Đang tải mô hình phân tầng Cascaded (L1: {self.layer1_type.upper()}, L2: {self.layer2_type.upper()})...")
        self.layer1.load()
        self.layer2.load()
        try:
            self.anomaly.load()
            self.has_anomaly = True
        except FileNotFoundError:
            print("[!] Cảnh báo: Không tải được mô hình Isolation Forest (Anomaly). Bỏ qua lớp phát hiện Zero-day.")
            self.has_anomaly = False

    def predict(self, X):
        """
        Dự đoán nhãn theo kiến trúc phân tầng:
        - Lớp 1 (AdaBoost) quét qua tất cả. Các luồng được gán nhãn Benign (0) được cho qua.
        - Các luồng bị Lớp 1 gán nhãn Attack (1) sẽ chuyển qua Lớp 2 (Extra Trees) để lọc báo động giả.
        - Nhãn cuối cùng là nhãn từ Lớp 2 đối với các luồng nghi ngờ, và 0 đối với các luồng Lớp 1 cho là an toàn.
        """
        import numpy as np
        import pandas as pd
        
        # 1. Dự đoán Lớp 1
        preds_l1 = self.layer1.predict(X)
        
        # 2. Lọc các luồng nghi ngờ (Lớp 1 dự đoán là Attack)
        final_preds = np.copy(preds_l1)
        
        attack_indices = np.where(preds_l1 == 1)[0]
        if len(attack_indices) > 0:
            # Lấy các dòng dữ liệu nghi ngờ
            if isinstance(X, pd.DataFrame):
                X_suspicious = X.iloc[attack_indices]
            else:
                X_suspicious = X[attack_indices]
                
            # Dự đoán Lớp 2
            preds_l2 = self.layer2.predict(X_suspicious)
            
            # Cập nhật kết quả cuối cùng: chỉ những luồng được Lớp 2 xác nhận mới là Attack
            final_preds[attack_indices] = preds_l2
            
        return final_preds

    def predict_detailed(self, X):
        """
        Dự đoán chi tiết và trả về phân loại cụ thể bao gồm:
        - 0: Benign (Bình thường)
        - 1: Attack (Tấn công đã được xác nhận qua Lớp 2)
        - 2: Anomaly (Cảnh báo dị thường/Zero-day bởi Isolation Forest)
        """
        import numpy as np
        
        # Lấy dự đoán từ cascade giám sát
        supervised_preds = self.predict(X)
        
        # Khởi tạo kết quả chi tiết (0 = Benign)
        detailed_preds = np.copy(supervised_preds)
        
        # Nếu có mô hình anomaly, chạy song song để tìm dị thường trên các luồng được gán nhãn Benign
        if self.has_anomaly:
            anomaly_preds = self.anomaly.predict(X)
            for i in range(len(supervised_preds)):
                if supervised_preds[i] == 0 and anomaly_preds[i] == 1:
                    # Gán nhãn dị thường (2) cho luồng Benign bị nghi ngờ
                    detailed_preds[i] = 2
                    
        return detailed_preds

    def predict_proba(self, X):
        # Xác suất kết hợp phân tầng: P(Attack) = min(P(L1_Attack), P(L2_Attack))
        import numpy as np
        prob_l1 = self.layer1.predict_proba(X)
        prob_l2 = self.layer2.predict_proba(X)
        return np.minimum(prob_l1, prob_l2)

