import os
import sys
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
from src.models import CascadedIDSModel

# Reconfigure stdout to use UTF-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

def load_simulation_dataset():
    """
    Tải tập dữ liệu DDoS thực tế từ file Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
    Nếu không có, tự động chuyển đổi sang mock data.
    """
    raw_path = os.path.join(config.RAW_DATA_DIR, "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
    print("\n" + "=" * 80)
    print(" BƯỚC 1: TẢI TẬP DỮ LIỆU MÔ PHỎNG (CASCADED IDS SIMULATION)")
    print("=" * 80)
    
    if not os.path.exists(raw_path):
        print(f"[!] Không tìm thấy file dữ liệu thực tế tại: {raw_path}")
        mock_path = os.path.join(config.RAW_DATA_DIR, "mock_cicids2017.csv")
        if not os.path.exists(mock_path):
            print("[*] Tự động tạo dữ liệu giả lập (mock data)...")
            np.random.seed(42)
            num_samples = 5000
            data = {}
            for col in config.SELECTED_FEATURES:
                data[col] = np.random.exponential(scale=100.0, size=num_samples)
            labels = np.random.choice(['BENIGN', 'DDoS-Attack'], size=num_samples, p=[0.85, 0.15])
            data['Label'] = labels
            df = pd.DataFrame(data)
            df.to_csv(mock_path, index=False)
            print(f"[+] Đã tạo file mock data thành công tại: {mock_path}")
        print(f"[*] Đang sử dụng dữ liệu giả lập (mock data) từ: {mock_path}")
        raw_path = mock_path

    print(f"[*] Đang đọc dữ liệu từ: {raw_path}...")
    df = pd.read_csv(raw_path)
    df.columns = df.columns.str.strip()
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    
    sample_size = min(len(df), 50000)
    df_sampled = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
    
    label_counts = df_sampled['Label'].value_counts()
    print(f"[+] Tải thành công {sample_size:,} dòng dữ liệu.")
    for lbl, cnt in label_counts.items():
        print(f"    - Nhãn: {lbl:<25} | Số lượng: {cnt:,} luồng")
        
    return df_sampled

def main():
    df_test = load_simulation_dataset()
    
    print("\n" + "=" * 80)
    print("  BƯỚC 2: TIỀN XỬ LÝ & TRÍCH XUẤT ĐẶC TRƯNG")
    print("=" * 80)
    preprocessor = IDSPreprocessor()
    df_clean = preprocessor.clean_columns(df_test.copy())
    df_clean = preprocessor.handle_missing_and_inf(df_clean)
    
    try:
        X_test_scaled = preprocessor.transform(df_clean)
    except FileNotFoundError as e:
        print(f"[!] Lỗi: {e}")
        print("[!] Không tìm thấy tệp chuẩn hóa 'scaler.pkl'. Vui lòng huấn luyện mô hình trước bằng Option [2].")
        sys.exit(1)
        
    y_true_binary = df_clean['Label'].apply(lambda x: 0 if str(x).strip().lower() in ['benign', '0', 'normal'] else 1)
    
    print("\n" + "=" * 80)
    print(" BƯỚC 3: ĐÁNH GIÁ MÔ HÌNH PHÂN TẦNG CASCADED IDS")
    print("=" * 80)
    
    model = CascadedIDSModel()
    try:
        model.load()
    except FileNotFoundError as e:
        print(f"[!] Lỗi: {e}")
        print("[!] Vui lòng huấn luyện các mô hình thành phần (AdaBoost & Extra Trees) trước.")
        sys.exit(1)
        
    print("[*] Đang thực hiện dự đoán mô phỏng...")
    preds = model.predict(X_test_scaled)
    probs = model.predict_proba(X_test_scaled)
    
    # 4. Tính toán các chỉ số chất lượng
    from sklearn.metrics import confusion_matrix, classification_report
    cm = confusion_matrix(y_true_binary, preds)
    tn, fp, fn, tp = cm.ravel()
    
    ddos_block_rate = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
    customer_availability = (tn / (tn + fp)) * 100 if (tn + fp) > 0 else 0.0
    customer_blocked_rate = (fp / (tn + fp)) * 100 if (tn + fp) > 0 else 0.0
    accuracy = ((tp + tn) / len(y_true_binary)) * 100
    
    tpr = ddos_block_rate / 100.0
    fpr = customer_blocked_rate / 100.0
    
    # Bayes
    bayes_01 = ((tpr * 0.001) / (tpr * 0.001 + fpr * 0.999)) * 100 if (tpr * 0.001 + fpr * 0.999) > 0 else 0.0
    bayes_50 = ((tpr * 0.05) / (tpr * 0.05 + fpr * 0.95)) * 100 if (tpr * 0.05 + fpr * 0.95) > 0 else 0.0
    
    print("\n" + "=" * 90)
    print(" KẾT QUẢ ĐÁNH GIÁ MÔ PHỎNG CASCADED IDS")
    print("=" * 90)
    print(f" - Độ chính xác chung (Accuracy)           : {accuracy:.4f}%")
    print(f" - Tỷ lệ chặn tấn công DDoS (Recall/TPR)    : {ddos_block_rate:.2f}%")
    print(f" - Tỷ lệ khách hàng sẵn sàng (TNR)         : {customer_availability:.2f}%")
    print(f" - Tỷ lệ khách hàng bị chặn nhầm (FPR)     : {customer_blocked_rate:.2f}%")
    print(f" - Xác suất báo động đúng Bayes (θ = 0.1%) : {bayes_01:.4f}%")
    print(f" - Xác suất báo động đúng Bayes (θ = 5%)   : {bayes_50:.4f}%")
    print("-" * 90)
    print("Chi tiết Classification Report:")
    print(classification_report(y_true_binary, preds, target_names=['Benign (Khách)', 'Attack (DDoS)'], zero_division=0))
    print("=" * 90)
    
    # 5. Vẽ đồ thị
    print("\n" + "=" * 80)
    print(" BƯỚC 4: VẼ BIỂU ĐỒ PHÂN TÍCH ĐƠN LẺ CHO CASCADED IDS")
    print("=" * 80)
    
    os.makedirs(config.EXTERNAL_DATA_DIR, exist_ok=True)
    
    # 5.1 Confusion Matrix
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt=',d', cmap='Reds', cbar=False,
                xticklabels=['Benign (Khách)', 'Attack (DDoS)'],
                yticklabels=['Benign (Khách)', 'Attack (DDoS)'])
    plt.title('Ma Trận Nhầm Lẫn - Cascaded IDS Model')
    plt.ylabel('Thực Tế (Actual)')
    plt.xlabel('Dự Đoán (Predicted)')
    plt.tight_layout()
    cm_path = os.path.join(config.EXTERNAL_DATA_DIR, "cascaded_confusion_matrix.png")
    plt.savefig(cm_path, dpi=200)
    plt.close()
    print(f"[+] Đã lưu Ma trận nhầm lẫn tại: {cm_path}")
    
    # 5.2 ROC & PR Curve
    from sklearn.metrics import roc_curve, auc, precision_recall_curve
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # ROC
    fpr_curve, tpr_curve, _ = roc_curve(y_true_binary, probs)
    roc_auc = auc(fpr_curve, tpr_curve)
    axes[0].plot(fpr_curve, tpr_curve, color='darkorange', lw=2, label=f'ROC Curve (AUC = {roc_auc:.4f})')
    axes[0].plot([0, 1], [0, 1], color='navy', linestyle='--')
    axes[0].set_xlim([0.0, 1.0])
    axes[0].set_ylim([0.0, 1.05])
    axes[0].set_xlabel('False Positive Rate (FPR)')
    axes[0].set_ylabel('True Positive Rate (TPR / Recall)')
    axes[0].set_title('Đường Cong ROC')
    axes[0].legend(loc="lower right")
    axes[0].grid(True, linestyle=':', alpha=0.6)
    
    # PR Curve
    prec, rec, _ = precision_recall_curve(y_true_binary, probs)
    axes[1].plot(rec, prec, color='green', lw=2, label='PR Curve')
    axes[1].set_xlim([0.0, 1.0])
    axes[1].set_ylim([0.0, 1.05])
    axes[1].set_xlabel('Recall / TPR')
    axes[1].set_ylabel('Precision')
    axes[1].set_title('Đường Cong Precision-Recall')
    axes[1].legend(loc="lower left")
    axes[1].grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    roc_path = os.path.join(config.EXTERNAL_DATA_DIR, "cascaded_roc_curve.png")
    plt.savefig(roc_path, dpi=200)
    plt.close()
    print(f"[+] Đã lưu Đường cong ROC/PR tại: {roc_path}")
    
    # 5.3 Trade-off Curve
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
        
    plt.figure(figsize=(7, 5))
    plt.plot(thresholds, block_rates, 'r-', lw=2, label='Chặn DDoS (Recall)')
    plt.plot(thresholds, availabilities, 'g-', lw=2, label='Khách Sẵn Sàng (TNR)')
    plt.axvline(0.5, color='blue', linestyle=':', label='Ngưỡng Mặc Định 0.5')
    plt.title('Đường Cong Đánh Đổi Bảo Mật vs Tính Sẵn Sàng (Cascaded IDS)')
    plt.xlabel('Decision Threshold')
    plt.ylabel('Phần trăm (%)')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc="lower center")
    plt.tight_layout()
    tradeoff_path = os.path.join(config.EXTERNAL_DATA_DIR, "cascaded_tradeoff.png")
    plt.savefig(tradeoff_path, dpi=200)
    plt.close()
    print(f"[+] Đã lưu Biểu đồ đánh đổi tại: {tradeoff_path}")
    
    print("\n" + "=" * 80)
    print(" QUY TRÌNH MÔ PHỎNG HOÀN TẤT THÀNH CÔNG")
    print("=" * 80)
    print("[*] Kết thúc quy trình đánh giá Cascaded IDS.")

if __name__ == "__main__":
    main()
