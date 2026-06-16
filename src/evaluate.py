import os
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Reconfigure stdout to use UTF-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Đảm bảo import được config và src từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessing import IDSPreprocessor
from src.models import IDSSupervisedModel, IDSUnsupervisedModel

def main():
    # 1. Tìm kiếm dữ liệu thử nghiệm trong data/external/ hoặc data/processed/
    external_files = [f for f in os.listdir(config.EXTERNAL_DATA_DIR) if f.endswith('.csv')]
    
    if not external_files:
        print("[!] Không tìm thấy dữ liệu kiểm thử bên ngoài (.csv) trong thư mục data/external/.")
        print("[*] Vui lòng đặt file dữ liệu thử nghiệm (ví dụ: UNSW-NB15 hoặc file PCAP đã được trích xuất sang CSV) vào thư mục data/external/")
        print("[*] Chương trình sẽ tự động thoát...")
        sys.exit(0)
        
    filepath = os.path.join(config.EXTERNAL_DATA_DIR, external_files[0])
    print(f"[*] Đang tải dữ liệu kiểm thử bên ngoài từ: {filepath}")
    df_test = pd.read_csv(filepath)
    
    # 2. Khởi tạo preprocessor và chuyển đổi (transform) các feature
    preprocessor = IDSPreprocessor()
    try:
        X_test_scaled = preprocessor.transform(df_test)
    except FileNotFoundError as e:
        print(f"[!] Lỗi: {e}")
        print("[*] Bạn cần chạy huấn luyện mô hình trước (`python src/train.py`) để tạo scaler.pkl.")
        sys.exit(1)
        
    # Xác định cột Label trong dữ liệu test
    label_col = None
    for col in ['Label', 'label', 'Class', 'class']:
        if col in df_test.columns:
            label_col = col
            break
            
    if label_col is None:
        print("[!] Không tìm thấy cột nhãn ('Label' / 'class') trong dữ liệu test. Chỉ chạy dự đoán không đánh giá.")
        y_test_binary = None
    else:
        # Nhị phân hóa nhãn kiểm thử
        y_test_binary = df_test[label_col].apply(lambda x: 0 if str(x).strip().lower() in ['benign', '0', 'normal'] else 1)
        
    # 3. Load và đánh giá mô hình Random Forest
    rf_model = IDSSupervisedModel(model_type='rf')
    try:
        rf_model.load()
        rf_preds = rf_model.predict(X_test_scaled)
        
        print("\n" + "="*50)
        print("KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH RANDOM FOREST TRÊN DỮ LIỆU NGOÀI")
        print("="*50)
        
        if y_test_binary is not None:
            print(f"Accuracy: {accuracy_score(y_test_binary, rf_preds):.4f}")
            print(classification_report(y_test_binary, rf_preds, target_names=['Benign', 'Attack']))
            print("Confusion Matrix:")
            print(confusion_matrix(y_test_binary, rf_preds))
        else:
            total = len(rf_preds)
            attacks = sum(rf_preds)
            print(f"Tổng số luồng phân tích: {total}")
            print(f"Phát hiện luồng bất thường: {attacks} ({attacks/total*100:.2f}%)")
            
    except FileNotFoundError:
        print("[!] Không thấy mô hình Random Forest đã lưu. Bỏ qua.")
        
    # 4. Load và đánh giá mô hình XGBoost
    xgb_model = IDSSupervisedModel(model_type='xgb')
    try:
        xgb_model.load()
        xgb_preds = xgb_model.predict(X_test_scaled)
        
        print("\n" + "="*50)
        print("KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH XGBOOST TRÊN DỮ LIỆU NGOÀI")
        print("="*50)
        
        if y_test_binary is not None:
            print(f"Accuracy: {accuracy_score(y_test_binary, xgb_preds):.4f}")
            print(classification_report(y_test_binary, xgb_preds, target_names=['Benign', 'Attack']))
        else:
            total = len(xgb_preds)
            attacks = sum(xgb_preds)
            print(f"Tổng số luồng phân tích: {total}")
            print(f"Phát hiện luồng bất thường: {attacks} ({attacks/total*100:.2f}%)")
            
    except FileNotFoundError:
        print("[!] Không thấy mô hình XGBoost đã lưu. Bỏ qua.")

if __name__ == "__main__":
    main()
