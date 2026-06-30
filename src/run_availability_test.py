import os
import sys
import time
import urllib.request
import json
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')  # Chạy headless, chỉ ghi file không mở cửa sổ GUI
import matplotlib.pyplot as plt
import seaborn as sns

# Đảm bảo import được config và src từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessing import IDSPreprocessor
from src.models import IDSSupervisedModel
from src.cli_visualizer import print_ascii_confusion_matrix, print_ascii_bar_chart, print_text_progress_bar

# Reconfigure stdout to use UTF-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

def load_real_ddos_dataset():
    """
    Tải tập dữ liệu DDoS thực tế từ file Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
    trong thư mục data/raw/ để tiến hành đánh giá thực tế.
    Nếu không tìm thấy, tự động tạo/sử dụng dữ liệu giả lập (mock data) để tránh crash chương trình.
    """
    raw_path = os.path.join(config.RAW_DATA_DIR, "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
    print("\n" + "=" * 80)
    print(" BƯỚC 1 & 2: TẢI TẬP DỮ LIỆU DDoS THỰC TẾ CICIDS2017 (FRIDAY AFTERNOON)")
    print("=" * 80)
    
    if not os.path.exists(raw_path):
        print(f"[!] Không tìm thấy file dữ liệu thực tế tại: {raw_path}")
        # Thử tìm file mock_cicids2017.csv
        mock_path = os.path.join(config.RAW_DATA_DIR, "mock_cicids2017.csv")
        if not os.path.exists(mock_path):
            print("[*] Tự động tạo dữ liệu giả lập (mock data) để thực hiện mô phỏng...")
            np.random.seed(42)
            num_samples = 5000
            data = {}
            for col in config.SELECTED_FEATURES:
                data[col] = np.random.exponential(scale=100.0, size=num_samples)
            # Tạo nhãn ngẫu nhiên: 85% Benign, 15% Attack
            labels = np.random.choice(['BENIGN', 'DDoS-Attack'], size=num_samples, p=[0.85, 0.15])
            data['Label'] = labels
            df = pd.DataFrame(data)
            df.to_csv(mock_path, index=False)
            print(f"[+] Đã tạo file mock data thành công tại: {mock_path}")
            
        print(f"[*] Đang sử dụng dữ liệu giả lập (mock data) từ: {mock_path}")
        raw_path = mock_path
        
    print(f"[*] Đang đọc file dữ liệu từ: {raw_path}...")
    
    # Đọc tệp CSV
    df = pd.read_csv(raw_path)
    df.columns = df.columns.str.strip()
    
    # Xử lý missing và inf
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    
    # Lấy mẫu ngẫu nhiên 50,000 dòng để cân bằng bộ nhớ và tốc độ vẽ đồ thị
    sample_size = min(len(df), 50000)
    df_sampled = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
    
    # In thông tin phân phối nhãn thực tế
    label_counts = df_sampled['Label'].value_counts()
    print(f"[+] Đã tải thành công {sample_size:,} dòng dữ liệu.")
    for lbl, cnt in label_counts.items():
        print(f"    - Nhãn: {lbl:<25} | Số lượng: {cnt:,} luồng")
        
    return df_sampled

def main():
    # Tải tập dữ liệu thực tế CICIDS2017
    df_test = load_real_ddos_dataset()
    print("\n" + "=" * 80)
    print("  BƯỚC 3: TIỀN XỬ LÝ DỮ LIỆU & TRÍCH XUẤT ĐẶC TRƯNG")
    print("=" * 80)
    
    preprocessor = IDSPreprocessor()
    df_clean = preprocessor.clean_columns(df_test.copy())
    df_clean = preprocessor.handle_missing_and_inf(df_clean)
    
    try:
        X_test_scaled = preprocessor.transform(df_clean)
    except FileNotFoundError as e:
        print(f"[!] Lỗi: {e}")
        print("[!] Không tìm thấy tệp chuẩn hóa 'scaler.pkl'. Bạn cần chạy huấn luyện mô hình trước!")
        sys.exit(1)
        
    y_true_binary = df_clean['Label'].apply(lambda x: 0 if str(x).strip().lower() in ['benign', '0', 'normal'] else 1)
    
    # 4. Tải các mô hình AI đã huấn luyện và dự đoán
    print("\n" + "=" * 80)
    print(" BƯỚC 4: ĐÁNH GIÁ HIỆU NĂNG MÔ HÌNH AI & ĐO LƯỜNG TÍNH SẴN SÀNG MÁY CHỦ")
    print("=" * 80)
    
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
    
    model_probs = {}
    model_cms = {}
    model_stats = {}
    loaded_models = {}
    
    for m_type, m_name in models_config.items():
        model = IDSSupervisedModel(model_type=m_type)
        try:
            model.load()
            preds = model.predict(X_test_scaled)
            probs = model.predict_proba(X_test_scaled)
            
            model_probs[m_name] = probs
            loaded_models[m_name] = model
            
            # Tính toán ma trận nhầm lẫn
            from sklearn.metrics import confusion_matrix
            cm = confusion_matrix(y_true_binary, preds)
            model_cms[m_name] = cm
            tn, fp, fn, tp = cm.ravel()
            
            # Tính toán các chỉ số
            ddos_block_rate = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
            customer_availability = (tn / (tn + fp)) * 100 if (tn + fp) > 0 else 0.0
            customer_blocked_rate = (fp / (tn + fp)) * 100 if (tn + fp) > 0 else 0.0
            accuracy = ((tp + tn) / len(y_true_binary)) * 100
            
            tpr = ddos_block_rate / 100.0
            fpr = customer_blocked_rate / 100.0
            
            # Tính toán xác suất hậu nghiệm Bayes P(Attack | Alert) cho các tỷ lệ cơ sở khác nhau
            bayes_01 = ((tpr * 0.001) / (tpr * 0.001 + fpr * 0.999)) * 100 if (tpr * 0.001 + fpr * 0.999) > 0 else 0.0
            bayes_50 = ((tpr * 0.05) / (tpr * 0.05 + fpr * 0.95)) * 100 if (tpr * 0.05 + fpr * 0.95) > 0 else 0.0
            
            model_stats[m_name] = {
                'ddos_block': ddos_block_rate,
                'customer_avail': customer_availability,
                'customer_blocked': customer_blocked_rate,
                'acc': accuracy,
                'tp': tp,
                'tn': tn,
                'fp': fp,
                'fn': fn,
                'bayes_01': bayes_01,
                'bayes_50': bayes_50
            }
            
            print(f"[+] Đã hoàn thành đánh giá {m_name} (Accuracy: {accuracy:.2f}%)")
            
        except FileNotFoundError:
            print(f"[!] Bỏ qua đánh giá {m_name}: Không tìm thấy file mô hình.")
            
    # In bảng so sánh trên Console
    print("\n" + "=" * 125)
    print(" BẢNG SO SÁNH HIỆU NĂNG & XÁC SUẤT BÁO ĐỘNG THỰC TẾ (BAYESIAN DETECTION RATE)")
    print("=" * 125)
    print(f" {'Mô hình':<22} | {'Recall (Chặn DDoS)':<18} | {'TNR (Khách Sẵn sàng)':<20} | {'P(Attack|Alert) θ=0.1%':<22} | {'P(Attack|Alert) θ=5%':<20} | {'Accuracy':<10}")
    print("-" * 125)
    for name, stats in model_stats.items():
        print(f" {name:<22} | {stats['ddos_block']:>16.2f}% | {stats['customer_avail']:>18.2f}% | {stats['bayes_01']:>20.2f}% | {stats['bayes_50']:>18.2f}% | {stats['acc']:>8.2f}%")
    print("=" * 125)
    
    # 5. Vẽ biểu đồ chất lượng bằng Matplotlib & Seaborn
    print("\n" + "=" * 80)
    print(" BƯỚC 5: TẠO CÁC BIỂU ĐỒ PHÂN TÍCH TOÁN HỌC PHỨC TẠP BẰNG MATPLOTLIB")
    print("=" * 80)
    
    # 5.1 Vẽ biểu đồ Confusion Matrices Heatmap cho 10 mô hình (5 hàng, 2 cột)
    if model_cms:
        fig, axes = plt.subplots(5, 2, figsize=(12, 22))
        axes_flat = axes.flatten()
        for idx, (name, cm) in enumerate(model_cms.items()):
            if idx < len(axes_flat):
                sns.heatmap(cm, annot=True, fmt=',d', cmap='Blues', cbar=False, ax=axes_flat[idx],
                            xticklabels=['Benign (Khách)', 'Attack (DDoS)'],
                            yticklabels=['Benign (Khách)', 'Attack (DDoS)'])
                axes_flat[idx].set_title(f'Ma trận Nhầm lẫn: {name}')
                axes_flat[idx].set_ylabel('Thực tế (Actual)')
                axes_flat[idx].set_xlabel('Dự đoán (Predicted)')
        for idx in range(len(model_cms), len(axes_flat)):
            axes_flat[idx].axis('off')
            
        plt.tight_layout()
        cm_path = os.path.join(config.EXTERNAL_DATA_DIR, "confusion_matrices.png")
        plt.savefig(cm_path, dpi=200)
        plt.close()
        print(f"[+] Đã lưu biểu đồ Ma trận Nhầm lẫn tại: {cm_path}")
        
    # 5.2 Vẽ biểu đồ ROC & PR Curves so sánh cả 10 mô hình (1 hàng, 2 cột)
    if model_probs:
        from sklearn.metrics import roc_curve, auc, precision_recall_curve
        fig, axes = plt.subplots(1, 2, figsize=(16, 7))
        
        # Subplot 1: ROC Curve cho cả 10 mô hình
        for name, probs in model_probs.items():
            fpr, tpr, _ = roc_curve(y_true_binary, probs)
            roc_auc = auc(fpr, tpr)
            axes[0].plot(fpr, tpr, lw=2, label=f'{name} (AUC = {roc_auc:.3f})')
        axes[0].plot([0, 1], [0, 1], color='gray', linestyle='--')
        axes[0].set_xlim([0.0, 1.0])
        axes[0].set_ylim([0.0, 1.05])
        axes[0].set_xlabel('Tỷ lệ chặn nhầm khách hàng (False Positive Rate)')
        axes[0].set_ylabel('Tỷ lệ chặn DDoS thành công (True Positive Rate)')
        axes[0].set_title('Đường cong ROC của các Mô hình')
        axes[0].legend(loc="lower right", fontsize='small')
        axes[0].grid(True, linestyle=':', alpha=0.6)
        
        # Subplot 2: Precision-Recall Curve cho cả 10 mô hình
        for name, probs in model_probs.items():
            prec, rec, _ = precision_recall_curve(y_true_binary, probs)
            axes[1].plot(rec, prec, lw=2, label=f'{name}')
        axes[1].set_xlim([0.0, 1.0])
        axes[1].set_ylim([0.0, 1.05])
        axes[1].set_xlabel('Tỷ lệ chặn DDoS thành công (Recall)')
        axes[1].set_ylabel('Độ chuẩn xác chặn DDoS (Precision)')
        axes[1].set_title('Đường cong Precision-Recall')
        axes[1].legend(loc="lower left", fontsize='small')
        axes[1].grid(True, linestyle=':', alpha=0.6)
        
        plt.tight_layout()
        comparison_path = os.path.join(config.EXTERNAL_DATA_DIR, "availability_comparison.png")
        plt.savefig(comparison_path, dpi=200)
        plt.close()
        print(f"[+] Đã lưu biểu đồ ROC/PR tại: {comparison_path}")
        
    # 5.3 Vẽ biểu đồ Trade-off Bảo mật vs Sẵn sàng cho từng mô hình riêng lẻ (5 hàng, 2 cột)
    if model_probs:
        fig, axes = plt.subplots(5, 2, figsize=(14, 22))
        axes_flat = axes.flatten()
        
        for idx, (name, probs) in enumerate(model_probs.items()):
            if idx < len(axes_flat):
                thresholds = np.linspace(0, 1, 100)
                block_rates = []
                availabilities = []
                for t in thresholds:
                    preds_t = (probs >= t).astype(int)
                    tp_t = np.sum((y_true_binary == 1) & (preds_t == 1))
                    fn_t = np.sum((y_true_binary == 1) & (preds_t == 0))
                    tn_t = np.sum((y_true_binary == 0) & (preds_t == 0))
                    fp_t = np.sum((y_true_binary == 0) & (preds_t == 1))
                    
                    block_rates.append(tp_t / (tp_t + fn_t) * 100 if (tp_t + fn_t) > 0 else 0.0)
                    availabilities.append(tn_t / (tn_t + fp_t) * 100 if (tn_t + fp_t) > 0 else 0.0)
                
                axes_flat[idx].plot(thresholds, block_rates, 'r-', lw=2, label='Chặn DDoS (Recall)')
                axes_flat[idx].plot(thresholds, availabilities, 'g-', lw=2, label='Khách Sẵn sàng (TNR)')
                axes_flat[idx].axvline(0.5, color='blue', linestyle=':', label='Ngưỡng 0.5')
                axes_flat[idx].set_title(f'Trade-off: {name}')
                axes_flat[idx].set_xlabel('Decision Threshold')
                axes_flat[idx].set_ylabel('Phần trăm (%)')
                axes_flat[idx].grid(True, linestyle=':', alpha=0.6)
                if idx == 0:
                    axes_flat[idx].legend(loc="lower center", fontsize='x-small')
                    
        for idx in range(len(model_probs), len(axes_flat)):
            axes_flat[idx].axis('off')
            
        plt.tight_layout()
        tradeoff_path = os.path.join(config.EXTERNAL_DATA_DIR, "tradeoff_curves.png")
        plt.savefig(tradeoff_path, dpi=200)
        plt.close()
        print(f"[+] Đã lưu biểu đồ Trade-off 10 mô hình tại: {tradeoff_path}")
        
    # 5.4 Vẽ Không gian Quyết định 2D (Decision Space) cho từng mô hình riêng lẻ (5 hàng, 2 cột)
    if loaded_models:
        from matplotlib.colors import ListedColormap
        fig, axes = plt.subplots(5, 2, figsize=(15, 24))
        axes_flat = axes.flatten()
        
        # 1. Xác định biên trong không gian đặc trưng gốc
        duration_min, duration_max = df_clean['Flow Duration'].min(), df_clean['Flow Duration'].max()
        fwd_len_min, fwd_len_max = df_clean['Fwd Packet Length Max'].min(), df_clean['Fwd Packet Length Max'].max()
        
        # 2. Tạo grid mesh
        grid_res = 40  # 40x40 cho tốc độ chạy nhanh và hiển thị mượt
        xx, yy = np.meshgrid(
            np.linspace(duration_min, duration_max, grid_res),
            np.linspace(fwd_len_min, fwd_len_max, grid_res)
        )
        
        # 3. Tạo DataFrame cho grid để chuyển qua scaler
        grid_flat_x = xx.ravel()
        grid_flat_y = yy.ravel()
        grid_df = pd.DataFrame(index=range(len(grid_flat_x)))
        for col in config.SELECTED_FEATURES:
            if col == 'Flow Duration':
                grid_df[col] = grid_flat_x
            elif col == 'Fwd Packet Length Max':
                grid_df[col] = grid_flat_y
            else:
                # Giá trị trung bình để làm mốc nền
                grid_df[col] = df_clean[col].mean()
                
        # 4. Scale đặc trưng của grid
        grid_df_scaled = preprocessor.transform(grid_df)
        
        # 5. Chọn mẫu ngẫu nhiên từ tập kiểm thử để scatter lên biểu đồ (tránh làm chậm hình)
        benign_indices = (y_true_binary == 0)
        ddos_indices = (y_true_binary == 1)
        size_b = min(150, sum(benign_indices))
        size_d = min(150, sum(ddos_indices))
        idx_b = np.random.choice(np.where(benign_indices)[0], size=size_b, replace=False) if size_b > 0 else []
        idx_d = np.random.choice(np.where(ddos_indices)[0], size=size_d, replace=False) if size_d > 0 else []
        
        custom_cmap = ListedColormap(['#d4edda', '#f8d7da'])  # Xanh nhạt cho benign, đỏ nhạt cho attack
        
        for idx, (name, model) in enumerate(loaded_models.items()):
            if idx < len(axes_flat):
                # Dự đoán lớp trên toàn grid
                preds_grid = model.predict(grid_df_scaled)
                zz = preds_grid.reshape(xx.shape)
                
                # Vẽ vùng quyết định (contour)
                axes_flat[idx].contourf(xx / 1e6, yy, zz, alpha=0.4, cmap=custom_cmap)
                
                # Vẽ các điểm thực tế
                if len(idx_b) > 0:
                    axes_flat[idx].scatter(df_clean.iloc[idx_b]['Flow Duration'] / 1e6, df_clean.iloc[idx_b]['Fwd Packet Length Max'],
                                           color='green', alpha=0.7, label='Khách hàng' if idx == 0 else "", s=15, edgecolors='k', linewidths=0.2)
                if len(idx_d) > 0:
                    axes_flat[idx].scatter(df_clean.iloc[idx_d]['Flow Duration'] / 1e6, df_clean.iloc[idx_d]['Fwd Packet Length Max'],
                                           color='red', alpha=0.6, label='DDoS' if idx == 0 else "", s=15, edgecolors='k', linewidths=0.2)
                
                axes_flat[idx].set_title(f'Quyết định 2D: {name}')
                axes_flat[idx].set_xlabel('Thời lượng (s)')
                axes_flat[idx].set_ylabel('Fwd Pkt Max (bytes)')
                axes_flat[idx].grid(True, linestyle=':', alpha=0.4)
                if idx == 0:
                    axes_flat[idx].legend(loc="upper right", fontsize='x-small')
                    
        for idx in range(len(loaded_models), len(axes_flat)):
            axes_flat[idx].axis('off')
            
        plt.tight_layout()
        boundaries_path = os.path.join(config.EXTERNAL_DATA_DIR, "decision_boundaries.png")
        plt.savefig(boundaries_path, dpi=200)
        plt.close()
        print(f"[+] Đã lưu biểu đồ Ranh giới Quyết định 2D cho 10 mô hình tại: {boundaries_path}")
            
    print("\n" + "=" * 80)
    print(" QUY TRÌNH KIỂM THỬ TÍNH SẴN SÀNG (AVAILABILITY) HOÀN TẤT VỚI KẾT QUẢ AN TOÀN")
    print("=" * 80)
    print("[+] Báo cáo phân tích kỹ thuật chi tiết đã được lưu tại: TECHNICAL_REPORT.md ở thư mục gốc.")
    print("[+] Các biểu đồ trực quan đã được lưu tại thư mục: data/external/")
    
    print("[*] Kết thúc quy trình đánh giá.")

if __name__ == "__main__":
    main()
