import os

# --- PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
EXTERNAL_DATA_DIR = os.path.join(DATA_DIR, "external")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Tạo các thư mục nếu chưa tồn tại
for path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR, MODELS_DIR]:
    os.makedirs(path, exist_ok=True)

# --- MODEL TRAINING CONFIGURATION ---
# Tự động loại bỏ trùng lặp dữ liệu huấn luyện để tránh biased
DROP_DUPLICATES = True
# Tự động tối ưu giảm kiểu dữ liệu số (downsize types) để tiết kiệm RAM
DOWNSIZE_TYPES = True

# Danh sách 15 features quan trọng nhất được chọn lọc để giảm tải hiệu năng và dễ trích xuất realtime
SELECTED_FEATURES = [
    'Flow Duration',
    'Total Fwd Packets',
    'Total Backward Packets',
    'Total Length of Fwd Packets',
    'Total Length of Bwd Packets',
    'Fwd Packet Length Max',
    'Fwd Packet Length Min',
    'Fwd Packet Length Mean',
    'Bwd Packet Length Max',
    'Bwd Packet Length Min',
    'Bwd Packet Length Mean',
    'Flow Bytes/s',
    'Flow Packets/s',
    'Flow IAT Mean',
    'Flow IAT Max'
]

# Siêu tham số cho mô hình
RF_PARAMS = {
    'n_estimators': 100,
    'max_depth': 15,
    'random_state': 42,
    'n_jobs': -1
}

XGB_PARAMS = {
    'n_estimators': 100,
    'max_depth': 6,
    'learning_rate': 0.1,
    'random_state': 42,
    'n_jobs': -1
}

# --- SNIFFER CONFIGURATION ---
# Cấu hình cho live capture
SNIFF_INTERFACE = None  # None nghĩa là tự động chọn card mạng mặc định
SNIFF_TIMEOUT = 10      # Thời gian sniff mỗi chu kỳ (giây)
ALERT_THRESHOLD = 0.5   # Ngưỡng xác suất để cảnh báo xâm nhập
