import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Reconfigure stdout to use UTF-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Đảm bảo import được config và src từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessing import IDSPreprocessor
from src.models import IDSSupervisedModel, IDSUnsupervisedModel
from src.cli_visualizer import print_ascii_confusion_matrix, print_ascii_bar_chart

def main():
    # 1. Tìm kiếm dữ liệu thử nghiệm từ đối số dòng lệnh hoặc trong data/external/
    filepath = None
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        external_files = [f for f in os.listdir(config.EXTERNAL_DATA_DIR) if f.endswith('.csv')]
        if external_files:
            filepath = os.path.join(config.EXTERNAL_DATA_DIR, external_files[0])
            
    if not filepath or not os.path.exists(filepath):
        print("[!] Không tìm thấy dữ liệu kiểm thử bên ngoài (.csv).")
        print("[*] Hướng dẫn: Chạy chương trình với đối số đường dẫn tệp:")
        print("    python src/evaluate.py <đường_dẫn_tệp_csv>")
        sys.exit(1)
        
    print(f"[*] Đang tải dữ liệu kiểm thử từ: {filepath}")
    df_test = pd.read_csv(filepath)
    
    # 2. Khởi tạo preprocessor và chuyển đổi (transform) các feature
    preprocessor = IDSPreprocessor()
    df_test = preprocessor.clean_columns(df_test)
    df_test = preprocessor.handle_missing_and_inf(df_test)
    
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
        
    # Danh sách 10 mô hình học máy phân lớp giám sát
    models_config = {
        'rf': 'Random Forest',
        'xgb': 'XGBoost',
        'dt': 'Decision Tree',
        'et': 'Extra Trees',
        'ada': 'AdaBoost',
        'gb': 'Gradient Boosting',
        'knn': 'K-Nearest Neighbors',
        'lr': 'Logistic Regression',
        'svm': 'Linear SVM',
        'nb': 'Naive Bayes'
    }
    
    # 3. Đánh giá tuần tự từng mô hình
    for m_type, m_name in models_config.items():
        model = IDSSupervisedModel(model_type=m_type)
        try:
            model.load()
            preds = model.predict(X_test_scaled)
            
            print("\n" + "="*65)
            print(f" KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH {m_name.upper()} ({m_type})")
            print("="*65)
            
            if y_test_binary is not None:
                print(f"Accuracy: {accuracy_score(y_test_binary, preds):.4f}")
                print(classification_report(y_test_binary, preds, target_names=['Benign', 'Attack'], zero_division=0))
                print_ascii_confusion_matrix(confusion_matrix(y_test_binary, preds))
                
                # Vẽ biểu đồ ASCII phân phối dự đoán
                attacks = int(sum(preds))
                benign = len(preds) - attacks
                print_ascii_bar_chart({"Benign (An toàn)": benign, "Attack (Độc hại)": attacks}, title=f"📊 PHÂN BỐ LƯU LƯỢNG MẠNG DỰ ĐOÁN ({m_name.upper()})")
            else:
                total = len(preds)
                attacks = int(sum(preds))
                benign = total - attacks
                print(f"Tổng số luồng phân tích: {total}")
                print(f"Phát hiện luồng bất thường: {attacks} ({attacks/total*100:.2f}%)")
                print_ascii_bar_chart({"Benign (An toàn)": benign, "Attack (Độc hại)": attacks}, title=f"📊 PHÂN BỐ LƯU LƯỢNG MẠNG PHÁT HIỆN ({m_name.upper()})")
                
        except FileNotFoundError:
            print(f"[!] Không tìm thấy mô hình {m_name} đã lưu. Bỏ qua.")

if __name__ == "__main__":
    main()
