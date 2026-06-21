import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier

# Đảm bảo import được config từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=" * 80)
    print("📊 BẮT ĐẦU PHÂN TÍCH LỰA CHỌN ĐẶC TRƯNG BẰNG TOÁN HỌC (FEATURE IMPORTANCE)")
    print("=" * 80)
    
    # 1. Tìm các tệp tin dữ liệu huấn luyện (Tuesday, Wednesday, Thursday)
    raw_dir = config.RAW_DATA_DIR
    csv_files = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
    train_files = [f for f in csv_files if any(day in f.lower() for day in ['tuesday', 'wednesday', 'thursday'])]
    
    if not train_files:
        print("[!] Không tìm thấy các file dữ liệu Tuesday, Wednesday, Thursday trong data/raw/!")
        sys.exit(1)
        
    print(f"[+] Phát hiện các tệp tin huấn luyện: {train_files}")
    
    # 2. Đọc và gộp mẫu dữ liệu từ các ngày để phân tích
    dfs = []
    for file in train_files:
        filepath = os.path.join(raw_dir, file)
        print(f"  -> Đang đọc mẫu từ file: {file}...")
        df_temp = pd.read_csv(filepath)
        df_temp.columns = df_temp.columns.str.strip()
        df_temp = df_temp.replace([np.inf, -np.inf], np.nan).dropna()
        
        # Lấy mẫu 15,000 dòng từ mỗi file để đảm bảo cân bằng bộ nhớ
        sample_size = min(len(df_temp), 15000)
        dfs.append(df_temp.sample(n=sample_size, random_state=42))
        
    df_all = pd.concat(dfs, ignore_index=True)
    print(f"[+] Đã gộp mẫu dữ liệu thành công. Quy mô: {len(df_all):,} dòng.")
    
    # 3. Làm sạch nhãn và đặc trưng
    # Encode nhãn nhị phân: Benign = 0, Attack = 1
    y = df_all['Label'].apply(lambda x: 0 if str(x).strip().lower() in ['benign', '0', 'normal'] else 1)
    
    # Loại bỏ các cột thông tin phi cấu trúc mạng (Metadata)
    metadata_cols = ['flow id', 'source ip', 'source port', 'destination ip', 'destination port', 'protocol', 'timestamp', 'label', 'external ips']
    feature_cols = [col for col in df_all.columns if col.lower() not in metadata_cols]
    
    X = df_all[feature_cols].copy()
    
    # Xử lý các cột dạng Object còn sót lại (nếu có) bằng cách ép kiểu số
    for col in X.columns:
        if X[col].dtype == object:
            X[col] = pd.to_numeric(X[col], errors='coerce')
    X = X.fillna(0.0)
    
    print(f"[+] Tổng số đặc trưng mạng đưa vào phân tích ban đầu: {len(X.columns)} đặc trưng.")
    
    # 4. Huấn luyện Random Forest để tính toán Feature Importance
    print("[*] Đang tính toán Feature Importance sử dụng Random Forest Classifier...")
    rf = RandomForestClassifier(n_estimators=50, max_depth=12, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    
    # 5. Sắp xếp và chọn đặc trưng
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    # Tạo DataFrame chứa độ quan trọng đặc trưng
    feat_imp_df = pd.DataFrame({
        'Feature': X.columns[indices],
        'Importance': importances[indices]
    })
    
    # Lưu bảng xếp hạng đặc trưng đầy đủ tại data/external/
    csv_out_path = os.path.join(config.EXTERNAL_DATA_DIR, "feature_importance_ranking.csv")
    feat_imp_df.to_csv(csv_out_path, index=False)
    print(f"[+] Đã lưu bảng xếp hạng đặc trưng đầy đủ tại: {csv_out_path}")
    
    # 6. Vẽ biểu đồ Top 20 đặc trưng mạng quan trọng nhất
    plt.figure(figsize=(12, 8))
    top_n = 20
    top_features = feat_imp_df.head(top_n)
    
    # Vẽ biểu đồ thanh ngang
    sns.barplot(x='Importance', y='Feature', data=top_features, palette="viridis")
    plt.title(f'Top {top_n} Đặc trưng mạng quan trọng nhất (Random Forest Gini Importance)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Mức độ đóng góp thông tin (Importance Score)', fontsize=12)
    plt.ylabel('Tên đặc trưng mạng', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    
    # Lưu ảnh biểu đồ
    plot_path = os.path.join(config.EXTERNAL_DATA_DIR, "feature_importance.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[+] Biểu đồ đặc trưng đã được lưu tại: {plot_path}")
    
    # Sao chép sang thư mục brain làm artifact
    brain_path = "C:/Users/Hikari-Rainbow/.gemini/antigravity/brain/95e1186e-6a67-4ab5-8cfe-938506c0f189/feature_importance.png"
    import shutil
    try:
        shutil.copy(plot_path, brain_path)
        print(f"[+] Đã sao chép biểu đồ sang thư mục brain artifact.")
    except Exception as e:
        print(f"[!] Không thể sao chép sang brain path: {e}")
        
    # In ra danh sách top 15 đặc trưng xem có trùng khớp với SELECTED_FEATURES không
    print("\n📊 SO SÁNH TOP 15 ĐẶC TRƯNG MẠNG THUẬT TOÁN ĐỀ XUẤT VS SELECTED_FEATURES:")
    print("-" * 80)
    print(f" {'Hạng':<5} | {'Đặc trưng phân tích':<35} | {'Điểm đóng góp':<15} | {'Được chọn trong dự án?'}")
    print("-" * 80)
    selected_lower = [f.lower() for f in config.SELECTED_FEATURES]
    for idx, row in top_features.head(15).reset_index().iterrows():
        is_selected = "Có (Trùng khớp)" if row['Feature'].lower() in selected_lower else "Không (Tính năng bổ trợ)"
        print(f" #{idx+1:<4} | {row['Feature']:<35} | {row['Importance']:>13.4f} | {is_selected}")
    print("-" * 80)

if __name__ == "__main__":
    main()
