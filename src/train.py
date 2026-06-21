import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Reconfigure stdout to use UTF-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Đảm bảo import được config và src từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessing import IDSPreprocessor
from src.models import IDSSupervisedModel, IDSUnsupervisedModel
from src.cli_visualizer import print_ascii_bar_chart, print_ascii_confusion_matrix

def generate_mock_dataset(num_samples=5000):
    """
    Tạo dữ liệu giả lập (mock data) với cùng các cột thuộc tính của CICIDS2017
    để người dùng có thể chạy thử nghiệm code ngay lập tức trước khi tải dataset thật.
    """
    print(f"[*] Không tìm thấy dữ liệu thật. Đang tạo {num_samples} dòng dữ liệu giả lập...")
    np.random.seed(42)
    
    data = {}
    # Tạo các cột thuộc tính số ngẫu nhiên
    for col in config.SELECTED_FEATURES:
        data[col] = np.random.exponential(scale=100.0, size=num_samples)
        
    # Tạo nhãn ngẫu nhiên: 85% Benign, 15% Attack
    labels = np.random.choice(['BENIGN', 'DDoS-Attack'], size=num_samples, p=[0.85, 0.15])
    data['Label'] = labels
    
    df = pd.DataFrame(data)
    # Lưu ra file csv mẫu
    mock_file = os.path.join(config.RAW_DATA_DIR, "mock_cicids2017.csv")
    df.to_csv(mock_file, index=False)
    print(f"[+] Dữ liệu giả lập đã được ghi tại: {mock_file}")
    return df

def main():
    # 1. Tìm kiếm file CSV trong thư mục data/raw/
    all_csv_files = [f for f in os.listdir(config.RAW_DATA_DIR) if f.endswith('.csv')]
    
    # Chỉ giữ các tệp tin chứa 'tuesday', 'wednesday', 'thursday' để tránh rò rỉ dữ liệu (data leakage)
    csv_files = [f for f in all_csv_files if any(day in f.lower() for day in ['tuesday', 'wednesday', 'thursday'])]
    
    if not csv_files:
        df = generate_mock_dataset(num_samples=5000)
    elif len(csv_files) == 1:
        # Load file CSV duy nhất tìm được
        filepath = os.path.join(config.RAW_DATA_DIR, csv_files[0])
        print(f"[*] Đang tải dữ liệu thực từ: {filepath}")
        df = pd.read_csv(filepath)
    else:
        # Tải và gộp dữ liệu từ toàn bộ các file (tất cả các ngày trong tuần được lọc)
        print(f"[*] Phát hiện {len(csv_files)} file CSV thực tế để huấn luyện. Đang tải và gộp mẫu dữ liệu...")
        dfs = []
        for file in csv_files:
            filepath = os.path.join(config.RAW_DATA_DIR, file)
            print(f"  -> Đang đọc và lấy mẫu file: {file}")
            
            # Đọc file
            temp_df = pd.read_csv(filepath)
            # Làm sạch khoảng trắng tên cột
            temp_df.columns = temp_df.columns.str.strip()
            # Xử lý nhanh NaN và inf trước khi lấy mẫu
            temp_df = temp_df.replace([np.inf, -np.inf], np.nan).dropna()
            
            # Lấy mẫu ngẫu nhiên tối đa 40,000 dòng để cân bằng dung lượng bộ nhớ
            sample_size = min(len(temp_df), 40000)
            sampled_df = temp_df.sample(n=sample_size, random_state=42)
            dfs.append(sampled_df)
            
        df = pd.concat(dfs, ignore_index=True)
        print(f"[+] Đã gộp thành công {len(dfs)} file dữ liệu. Tổng số dòng thu được: {len(df)}")
        
    # 2. Tiền xử lý dữ liệu
    preprocessor = IDSPreprocessor()
    X, y = preprocessor.fit_transform(df, label_column='Label')
    
    # 3. Cân bằng dữ liệu (Chỉ áp dụng cho Supervised)
    X_bal, y_bal = preprocessor.balance_data(X, y, strategy='undersample', ratio=1.0)
    
    # Giới hạn kích thước mẫu huấn luyện tối đa là 15,000 dòng để 10 mô hình chạy nhanh
    max_samples = 15000
    if len(X_bal) > max_samples:
        print(f"\n[*] Đang thu nhỏ mẫu xuống {max_samples} dòng (vẫn giữ cân bằng 50/50) để tăng tốc huấn luyện 10 mô hình...")
        df_temp = pd.concat([X_bal, y_bal], axis=1)
        # Tách hai nhãn và lấy mẫu
        df_benign = df_temp[df_temp[y_bal.name] == 0].sample(n=max_samples // 2, random_state=42)
        df_attack = df_temp[df_temp[y_bal.name] == 1].sample(n=max_samples // 2, random_state=42)
        df_shuffled = pd.concat([df_benign, df_attack]).sample(frac=1.0, random_state=42).reset_index(drop=True)
        X_bal = df_shuffled[config.SELECTED_FEATURES]
        y_bal = df_shuffled[y_bal.name]
    
    # Chia tập Train / Test
    X_train, X_test, y_train, y_test = train_test_split(X_bal, y_bal, test_size=0.2, random_state=42)
    
    # 3.5. Nghiên cứu Overfitting trên Decision Tree với các độ sâu khác nhau
    print("\n" + "=" * 65)
    print(" 📊 NGHIÊN CỨU CHIỀU SÂU CÂY QUYẾT ĐỊNH (DECISION TREE DEPTH STUDY)")
    print("=" * 65)
    from sklearn.tree import DecisionTreeClassifier
    depths = [3, 5, 8, 12, 20, None]
    print(f" {'Max Depth':<10} | {'Train Accuracy':<16} | {'Test Accuracy':<16} | {'Overfitting Gap'}")
    print("-" * 65)
    for d in depths:
        dt_test = DecisionTreeClassifier(max_depth=d, random_state=42)
        dt_test.fit(X_train, y_train)
        train_acc = dt_test.score(X_train, y_train) * 100
        test_acc = dt_test.score(X_test, y_test) * 100
        gap = train_acc - test_acc
        depth_str = str(d) if d is not None else "None (Max)"
        print(f" {depth_str:<10} | {train_acc:>13.2f}% | {test_acc:>13.2f}% | {gap:>12.2f}%")
    print("-" * 65 + "\n")

    # Lưu kết quả đánh giá để so sánh cuối cùng
    comparison_results = {}
    
    # Danh sách 10 mô hình học máy phân lớp có giám sát
    supervised_models_config = {
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
    
    # 4. Huấn luyện và Đánh giá tuần tự 10 mô hình giám sát
    for m_type, m_name in supervised_models_config.items():
        print("\n" + "=" * 65)
        print(f" HUẤN LUYỆN & ĐÁNH GIÁ MÔ HÌNH: {m_name.upper()} ({m_type})")
        print("=" * 65)
        
        clf = IDSSupervisedModel(model_type=m_type)
        try:
            clf.build()
            clf.train(X_train, y_train)
            clf.save()
            
            # Dự đoán và tính toán Accuracy
            preds = clf.predict(X_test)
            acc = accuracy_score(y_test, preds)
            comparison_results[m_name] = acc
            
            print(f"\n[+] Kết quả {m_name}: Accuracy = {acc:.4f}")
            print(classification_report(y_test, preds, target_names=['Benign', 'Attack'], zero_division=0))
            print_ascii_confusion_matrix(confusion_matrix(y_test, preds))
        except Exception as e:
            print(f"[!] Lỗi khi huấn luyện {m_name}: {e}")
            
    # 5. Huấn luyện mô hình Học không giám sát (Isolation Forest)
    # Lấy các dòng Benign từ tập train để huấn luyện
    X_train_benign = X_train[y_train == 0]
    
    if len(X_train_benign) > 0:
        print("\n" + "=" * 65)
        print(" HUẤN LUYỆN MÔ HÌNH KHÔNG GIÁM SÁT: ISOLATION FOREST")
        print("=" * 65)
        
        anomaly_ids = IDSUnsupervisedModel()
        anomaly_ids.train(X_train_benign)
        anomaly_ids.save()
        
        # Đánh giá Isolation Forest trên tập test đầy đủ
        anomaly_preds = anomaly_ids.predict(X_test)
        anomaly_acc = accuracy_score(y_test, anomaly_preds)
        comparison_results["Isolation Forest (Anomaly)"] = anomaly_acc
        print(f"\n[+] Kết quả Isolation Forest: Accuracy = {anomaly_acc:.4f}")
        print(classification_report(y_test, anomaly_preds, target_names=['Benign', 'Attack'], zero_division=0))
        print_ascii_confusion_matrix(confusion_matrix(y_test, anomaly_preds))
    else:
        print("[!] Không đủ dữ liệu Benign để huấn luyện Isolation Forest.")
        
    # Trực quan hóa so sánh độ chính xác của các mô hình học trên terminal
    print_ascii_bar_chart(comparison_results, title="🏆 SO SÁNH ĐỘ CHÍNH XÁC (ACCURACY) CỦA 11 THUẬT TOÁN")
 
if __name__ == "__main__":
    main()
