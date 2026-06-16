import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import IsolationForest
import xgboost as xgb
import sys

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
            self.model = xgb.XGBClassifier(**config.XGB_PARAMS)
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
