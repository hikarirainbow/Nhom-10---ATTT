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

def get_open_source_api_metrics():
    """
    Truy vấn API Thời tiết Open-Meteo để xác định chủ đề kiểm thử (Weather Portal),
    đồng thời đo lường độ trễ mạng thực tế và dung lượng phản hồi (payload size).
    """
    url = "https://api.open-meteo.com/v1/forecast?latitude=21.0285&longitude=105.8542&current_weather=true"
    print("\n" + "=" * 80)
    print("🌐 BƯỚC 1: TRUY VẤN API MÃ NGUỒN MỞ ĐỂ XÁC ĐỊNH CHỦ ĐỀ & THIẾT LẬP THAM SỐ GỐC")
    print("=" * 80)
    print(f"[*] Đang kết nối tới API: {url}...")
    
    start_time = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read()
            latency = time.perf_counter() - start_time
            payload_size = len(data)
            
            # Đọc một phần dữ liệu thời tiết để xác định chủ đề
            weather_json = json.loads(data.decode('utf-8'))
            temp = weather_json.get("current_weather", {}).get("temperature", "N/A")
            windspeed = weather_json.get("current_weather", {}).get("windspeed", "N/A")
            
            print(f"[+] Kết nối API thành công!")
            print(f"    - Chủ đề xác định: CỔNG THÔNG TIN DỰ BÁO THỜI TIẾT QUỐC GIA (Weather Portal API)")
            print(f"    - Nhiệt độ hiện tại tại Hà Nội: {temp}°C | Tốc độ gió: {windspeed} km/h")
            print(f"    - Độ trễ mạng (Latency) đo được: {latency * 1000:.2f} ms")
            print(f"    - Dung lượng gói tin phản hồi (Payload size): {payload_size} bytes")
            return latency, payload_size, True
    except Exception as e:
        latency = 0.20  # Fallback 200ms
        payload_size = 450  # Fallback 450 bytes
        print(f"[!] Không thể kết nối tới API thời tiết (Có thể thiết bị đang ngoại tuyến): {e}")
        print(f"[!] Chế độ Fallback được kích hoạt:")
        print(f"    - Chủ đề mô phỏng: CỔNG THÔNG TIN DỰ BÁO THỜI TIẾT QUỐC GIA (Offline Simulator)")
        print(f"    - Độ trễ mạng mặc định: {latency * 1000:.2f} ms")
        print(f"    - Dung lượng phản hồi mặc định: {payload_size} bytes")
        return latency, payload_size, False

def generate_ddos_flow():
    """
    Sinh luồng DDoS (HTTP Get Flood) có độ khó cao hơn (Thực tế hơn):
    Pha trộn giữa DDoS Get Flood truyền thống (gói nhỏ) và DDoS nâng cao (HTTP POST Flood 
    chứa payload lớn giả mạo) để lách qua các bộ lọc độ dài cơ bản.
    """
    # 85% DDoS truyền thống (gói nhỏ), 15% DDoS nâng cao (gói lớn giả mạo)
    is_advanced = np.random.rand() < 0.15
    duration = np.random.uniform(5.0, 25.0)  # 5s - 25s
    fwd_pkts = np.random.randint(3, 12)
    bwd_pkts = np.random.randint(2, 8)
    
    if is_advanced:
        # Giả lập payload giả mạo lớn để lọt qua lọc kích thước gói
        fwd_len_tot = np.random.uniform(800, 2500)
        bwd_len_tot = np.random.uniform(5000, 10000)
        fwd_len_max = np.random.uniform(200, 800)
    else:
        # DDoS truyền thống
        fwd_len_tot = np.random.uniform(20, 45)
        bwd_len_tot = np.random.uniform(5000, 10000)
        fwd_len_max = np.random.uniform(6, 20)
        
    flow_bytes_s = (fwd_len_tot + bwd_len_tot) / duration
    flow_pkts_s = (fwd_pkts + bwd_pkts) / duration
    
    # IAT
    flow_iat_mean = (duration / (fwd_pkts + bwd_pkts - 1)) * 1e6
    flow_iat_max = flow_iat_mean * np.random.uniform(1.5, 3.5)
    
    return {
        'Flow Duration': duration * 1e6,
        'Total Fwd Packets': fwd_pkts,
        'Total Backward Packets': bwd_pkts,
        'Total Length of Fwd Packets': fwd_len_tot,
        'Total Length of Bwd Packets': bwd_len_tot,
        'Fwd Packet Length Max': fwd_len_max,
        'Fwd Packet Length Min': 6,
        'Fwd Packet Length Mean': fwd_len_tot / fwd_pkts,
        'Bwd Packet Length Max': np.random.uniform(3000, 6000),
        'Bwd Packet Length Min': 0,
        'Bwd Packet Length Mean': bwd_len_tot / bwd_pkts,
        'Flow Bytes/s': flow_bytes_s,
        'Flow Packets/s': flow_pkts_s,
        'Flow IAT Mean': flow_iat_mean,
        'Flow IAT Max': flow_iat_max,
        'Label': 'DDoS-Attack'
    }

def generate_benign_customer_flow(base_latency, payload_size):
    """
    Sinh luồng truy cập của khách hàng bình thường có độ khó cao hơn (Thực tế hơn):
    Pha trộn giữa truy cập Web thông thường (payload lớn) và các kết nối điều khiển
    (TCP Keep-Alive / Heartbeat / API Check) có kích thước siêu nhỏ chồng lấn lên miền của DDoS.
    """
    # 85% truy vấn lớn, 15% gói kết nối điều khiển nhỏ
    is_control = np.random.rand() < 0.15
    duration = np.random.uniform(2.0, 20.0)  # 2s - 20s
    
    if is_control:
        # Gói tin điều khiển nhỏ (gây nhiễu, chồng lấn lên DDoS)
        fwd_pkts = np.random.randint(2, 4)
        bwd_pkts = np.random.randint(1, 3)
        fwd_len_tot = np.random.uniform(20, 80)
        bwd_len_tot = np.random.uniform(20, 80)
        fwd_len_max = np.random.uniform(6, 40)
        bwd_len_max = np.random.uniform(6, 40)
    else:
        # Khách truy cập thời tiết thông thường
        fwd_pkts = np.random.randint(10, 25)
        bwd_pkts = np.random.randint(10, 30)
        fwd_len_tot = np.random.uniform(500, 3000)
        bwd_len_tot = payload_size * np.random.uniform(4.0, 10.0)
        fwd_len_max = np.random.uniform(100, 1500)
        bwd_len_max = np.random.uniform(200, 1000)
        
    flow_bytes_s = (fwd_len_tot + bwd_len_tot) / duration
    flow_pkts_s = (fwd_pkts + bwd_pkts) / duration
    
    flow_iat_mean = (duration / (fwd_pkts + bwd_pkts - 1)) * 1e6
    flow_iat_max = flow_iat_mean * np.random.uniform(2.2, 4.5)
    
    return {
        'Flow Duration': duration * 1e6,
        'Total Fwd Packets': fwd_pkts,
        'Total Backward Packets': bwd_pkts,
        'Total Length of Fwd Packets': fwd_len_tot,
        'Total Length of Bwd Packets': bwd_len_tot,
        'Fwd Packet Length Max': fwd_len_max,
        'Fwd Packet Length Min': np.random.uniform(0, 60),
        'Fwd Packet Length Mean': fwd_len_tot / fwd_pkts,
        'Bwd Packet Length Max': bwd_len_max,
        'Bwd Packet Length Min': np.random.uniform(0, 60),
        'Bwd Packet Length Mean': bwd_len_tot / bwd_pkts,
        'Flow Bytes/s': flow_bytes_s,
        'Flow Packets/s': flow_pkts_s,
        'Flow IAT Mean': flow_iat_mean,
        'Flow IAT Max': flow_iat_max,
        'Label': 'BENIGN'
    }

def main():
    # 1. Thu thập thông tin nền (latency, payload size) từ API thật
    latency, payload_size, online = get_open_source_api_metrics()
    
    # 2. Sinh tập dữ liệu kiểm thử quy mô lớn
    print("\n" + "=" * 80)
    print("📊 BƯỚC 2: MÔ PHỎNG CHIẾN DỊCH DDoS QUY MÔ LỚN (AVAILABILITY TEST DATASET)")
    print("=" * 80)
    
    total_samples = 50000
    ddos_ratio = 0.80  # 80% DDoS, 20% Benign
    num_ddos = int(total_samples * ddos_ratio)
    num_benign = total_samples - num_ddos
    
    print(f"[*] Quy mô sinh dữ liệu: {total_samples:,} dòng luồng mạng")
    print(f"    - Luồng DDoS Flood tấn công (Mục tiêu: Cần phát hiện chặn): {num_ddos:,} luồng")
    print(f"    - Luồng Khách hàng hợp lệ (Mục tiêu: Phải chừa đường cho qua): {num_benign:,} luồng")
    
    # Trộn ngẫu nhiên nhãn trước để quá trình sinh chân thực
    labels = ["DDoS-Attack"] * num_ddos + ["BENIGN"] * num_benign
    np.random.shuffle(labels)
    
    flows = []
    for idx, label in enumerate(labels):
        if label == "DDoS-Attack":
            flow = generate_ddos_flow()
        else:
            flow = generate_benign_customer_flow(latency, payload_size)
        flows.append(flow)
        
        # Cập nhật thanh tiến trình sau mỗi 2,000 dòng
        if (idx + 1) % 2000 == 0 or (idx + 1) == total_samples:
            print_text_progress_bar(idx + 1, total_samples, prefix='Đang giả lập luồng dữ liệu', suffix='Hoàn thành', length=30)
            
    df_test = pd.DataFrame(flows)
    
    # Thêm nhiễu ngẫu nhiên Gaussian để giả lập tính biến động của mạng thực tế
    noise_factor = 0.04
    for col in df_test.columns:
        if col != 'Label':
            df_test[col] = df_test[col].apply(lambda x: max(x * (1 + np.random.normal(0, noise_factor)), 0.0))
            
    # Lưu tập dữ liệu kiểm thử quy mô lớn
    output_path = os.path.join(config.EXTERNAL_DATA_DIR, "large_ddos_availability_test.csv")
    df_test.to_csv(output_path, index=False)
    print(f"\n[+] Đã ghi tập dữ liệu kiểm thử thành công vào: {output_path}")
    
    # 3. Tiền xử lý dữ liệu kiểm thử
    print("\n" + "=" * 80)
    print("⚙️  BƯỚC 3: TIỀN XỬ LÝ DỮ LIỆU & TRÍCH XUẤT ĐẶC TRƯNG")
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
    print("🧠 BƯỚC 4: ĐÁNH GIÁ HIỆU NĂNG MÔ HÌNH AI & ĐO LƯỜNG TÍNH SẴN SÀNG MÁY CHỦ")
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
            
            model_stats[m_name] = {
                'ddos_block': ddos_block_rate,
                'customer_avail': customer_availability,
                'customer_blocked': customer_blocked_rate,
                'acc': accuracy,
                'tp': tp,
                'tn': tn,
                'fp': fp,
                'fn': fn
            }
            
            print(f"[+] Đã hoàn thành đánh giá {m_name} (Accuracy: {accuracy:.2f}%)")
            
        except FileNotFoundError:
            print(f"[!] Bỏ qua đánh giá {m_name}: Không tìm thấy file mô hình.")
            
    # In bảng so sánh trên Console
    print("\n" + "=" * 85)
    print("📊 BẢNG SO SÁNH HIỆU NĂNG 10 MÔ HÌNH (AVAILABILITY VS SECURITY)")
    print("=" * 85)
    print(f" {'Mô hình':<22} | {'Chặn DDoS (Recall)':<20} | {'Khách Sẵn sàng (TNR)':<20} | {'Độ chính xác':<15}")
    print("-" * 85)
    for name, stats in model_stats.items():
        print(f" {name:<22} | {stats['ddos_block']:>18.2f}% | {stats['customer_avail']:>18.2f}% | {stats['acc']:>13.2f}%")
    print("=" * 85)
    
    # 5. Vẽ biểu đồ chất lượng bằng Matplotlib & Seaborn
    print("\n" + "=" * 80)
    print("📈 BƯỚC 5: TẠO CÁC BIỂU ĐỒ PHÂN TÍCH TOÁN HỌC PHỨC TẠP BẰNG MATPLOTLIB")
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
    print("🎉 QUY TRÌNH KIỂM THỬ TÍNH SẴN SÀNG (AVAILABILITY) HOÀN TẤT VỚI KẾT QUẢ AN TOÀN")
    print("=" * 80)
    print("[+] Báo cáo phân tích kỹ thuật chi tiết đã được lưu tại: TECHNICAL_REPORT.md ở thư mục gốc.")
    print("[+] Các biểu đồ trực quan đã được lưu tại thư mục: data/external/")
    
    try:
        # Prompt hỏi người dùng mở báo cáo và hình ảnh trực tiếp
        confirm = input("\n👉 Bạn có muốn tự động mở báo cáo (TECHNICAL_REPORT.md) và các biểu đồ ảnh vừa vẽ không? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            print("[*] Đang mở tệp báo cáo và biểu đồ ảnh...")
            os.system("start TECHNICAL_REPORT.md")
            os.system(f'start "" "{os.path.join(config.EXTERNAL_DATA_DIR, "confusion_matrices.png")}"')
            os.system(f'start "" "{os.path.join(config.EXTERNAL_DATA_DIR, "availability_comparison.png")}"')
            os.system(f'start "" "{os.path.join(config.EXTERNAL_DATA_DIR, "tradeoff_curves.png")}"')
            os.system(f'start "" "{os.path.join(config.EXTERNAL_DATA_DIR, "decision_boundaries.png")}"')
    except Exception as e:
        print(f"[!] Không thể tự động mở tệp: {e}")

if __name__ == "__main__":
    main()
