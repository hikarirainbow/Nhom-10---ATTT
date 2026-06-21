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
    Sinh luồng DDoS (HTTP Get Flood):
    Mô phỏng chính xác miền giá trị của cuộc tấn công trong CICIDS2017:
    Thời lượng luồng dài, gói tin fwd cực nhỏ (GET/SYN), gói tin bwd lớn (phản hồi lỗi/trang web),
    IAT trung bình và lớn.
    """
    duration = np.random.uniform(5.0, 25.0)  # 5s - 25s
    fwd_pkts = np.random.randint(3, 6)
    bwd_pkts = np.random.randint(2, 5)
    
    # Payload fwd rất nhỏ (chỉ header kết nối / HTTP GET ngắn), bwd rất lớn (HTML error/response)
    fwd_len_tot = np.random.uniform(20, 45)
    bwd_len_tot = np.random.uniform(5000, 10000)
    
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
        'Fwd Packet Length Max': np.random.uniform(6, 20),
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
    Sinh luồng truy cập của khách hàng bình thường đọc thông tin thời tiết:
    Thời gian luồng dài (5s-20s), gói tin fwd lớn (GET + headers hoàn chỉnh),
    gói tin bwd cực lớn (nhiều phản hồi json từ API), IAT giãn cách tự nhiên.
    """
    duration = np.random.uniform(5.0, 20.0)  # 5s - 20s
    fwd_pkts = np.random.randint(10, 25)
    bwd_pkts = np.random.randint(10, 30)
    
    # HTTP GET Request đầy đủ headers + data
    fwd_len_tot = np.random.uniform(500, 3000)
    # Payload phản hồi thời tiết thực tế từ Open-Meteo API
    bwd_len_tot = payload_size * np.random.uniform(4.0, 10.0)  # Gộp nhiều request truy vấn
    
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
        'Fwd Packet Length Max': np.random.uniform(100, 1500),
        'Fwd Packet Length Min': np.random.uniform(0, 60),
        'Fwd Packet Length Mean': fwd_len_tot / fwd_pkts,
        'Bwd Packet Length Max': np.random.uniform(200, 1000),
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
    
    models = {
        'Random Forest': IDSSupervisedModel(model_type='rf'),
        'XGBoost': IDSSupervisedModel(model_type='xgb')
    }
    
    model_probs = {}
    model_cms = {}
    
    for name, model in models.items():
        try:
            model.load()
            preds = model.predict(X_test_scaled)
            probs = model.predict_proba(X_test_scaled)
            
            model_probs[name] = probs
            
            # Tính toán ma trận nhầm lẫn
            from sklearn.metrics import confusion_matrix
            cm = confusion_matrix(y_true_binary, preds)
            model_cms[name] = cm
            tn, fp, fn, tp = cm.ravel()
            
            # Tính toán các chỉ số an ninh và vận hành
            ddos_block_rate = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
            customer_availability = (tn / (tn + fp)) * 100 if (tn + fp) > 0 else 0.0
            customer_blocked_rate = (fp / (tn + fp)) * 100 if (tn + fp) > 0 else 0.0
            accuracy = ((tp + tn) / len(y_true_binary)) * 100
            
            # Phân loại trạng thái vận hành của hệ thống
            if customer_availability >= 99.5:
                status = "🟢 XUẤT SẮC (Excellent) - Máy chủ thông suốt hoàn toàn cho khách hàng."
            elif customer_availability >= 95.0:
                status = "🟡 TỐT (Good) - Hầu hết khách hàng truy cập bình thường."
            else:
                status = "🔴 CẦN CẢI THIỆN (Critical) - Nhiều khách hàng bị chặn nhầm, ảnh hưởng tính sẵn sàng!"
                
            print(f"\n📈 KẾT QUẢ VẬN HÀNH MÔ HÌNH: {name.upper()}")
            print("-" * 55)
            print(f"⚡ Tổng số luồng kiểm thử thực tế: {len(y_true_binary):,}")
            print(f"🔒 Tỷ lệ chặn tấn công DDoS (DDoS Block Rate): {ddos_block_rate:.2f}% (Chặn thành công {tp:,}/{tp+fn:,} luồng dồn dập)")
            print(f"👥 Tỷ lệ sẵn sàng cho khách hàng (Customer Availability): {customer_availability:.2f}% (Thông suốt {tn:,}/{tn+fp:,} luồng khách hàng)")
            print(f"⚠️  Tỷ lệ chặn nhầm khách hàng (Customer Block Rate): {customer_blocked_rate:.2f}% (Bị từ chối dịch vụ nhầm: {fp:,} khách)")
            print(f"🎯 Độ chính xác tổng thể (Accuracy): {accuracy:.2f}%")
            print(f"📋 Đánh giá trạng thái vận hành: {status}")
            
            print_ascii_confusion_matrix(cm, labels=["Benign (Khách)", "Attack (DDoS)"])
            
            # Vẽ biểu đồ ASCII hiển thị số lượng được chặn/cho qua
            print_ascii_bar_chart(
                {
                    "Chặn đứng DDoS (Đúng)": tp,
                    "Thông suốt Khách (Đúng)": tn,
                    "Chặn nhầm Khách (Sai)": fp,
                    "Bỏ lọt DDoS (Sai)": fn
                },
                title=f"📊 PHÂN BỐ XỬ LÝ LƯU LƯỢNG MẠNG ({name.upper()})"
            )
            
        except FileNotFoundError:
            print(f"[!] Bỏ qua đánh giá {name}: Không tìm thấy file mô hình đã huấn luyện.")
            
    # 5. Vẽ biểu đồ chất lượng bằng Matplotlib & Seaborn
    print("\n" + "=" * 80)
    print("📈 BƯỚC 5: TẠO CÁC BIỂU ĐỒ PHÂN TÍCH TOÁN HỌC PHỨC TẠP BẰNG MATPLOTLIB")
    print("=" * 80)
    
    # 5.1 Vẽ biểu đồ Confusion Matrices Heatmap
    if model_cms:
        fig, axes = plt.subplots(1, len(model_cms), figsize=(12, 5))
        if len(model_cms) == 1:
            axes = [axes]
        for idx, (name, cm) in enumerate(model_cms.items()):
            sns.heatmap(cm, annot=True, fmt=',d', cmap='Blues', cbar=False, ax=axes[idx],
                        xticklabels=['Benign (Khách)', 'Attack (DDoS)'],
                        yticklabels=['Benign (Khách)', 'Attack (DDoS)'])
            axes[idx].set_title(f'Ma trận Nhầm lẫn: {name}')
            axes[idx].set_ylabel('Thực tế (Actual)')
            axes[idx].set_xlabel('Dự đoán (Predicted)')
        plt.tight_layout()
        cm_path = os.path.join(config.EXTERNAL_DATA_DIR, "confusion_matrices.png")
        plt.savefig(cm_path, dpi=300)
        plt.close()
        print(f"[+] Đã lưu biểu đồ Ma trận Nhầm lẫn tại: {cm_path}")
        
    # 5.2 Vẽ biểu đồ Availability & Security Curves (ROC, PR, Threshold, 2D Feature Space)
    if model_probs:
        from sklearn.metrics import roc_curve, auc, precision_recall_curve
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        
        # Subplot 1: ROC Curve
        for name, probs in model_probs.items():
            fpr, tpr, _ = roc_curve(y_true_binary, probs)
            roc_auc = auc(fpr, tpr)
            axes[0, 0].plot(fpr, tpr, lw=2, label=f'{name} (AUC = {roc_auc:.4f})')
        axes[0, 0].plot([0, 1], [0, 1], color='gray', linestyle='--')
        axes[0, 0].set_xlim([0.0, 1.0])
        axes[0, 0].set_ylim([0.0, 1.05])
        axes[0, 0].set_xlabel('Tỷ lệ chặn nhầm khách hàng (False Positive Rate)')
        axes[0, 0].set_ylabel('Tỷ lệ chặn DDoS thành công (True Positive Rate)')
        axes[0, 0].set_title('Đường cong ROC')
        axes[0, 0].legend(loc="lower right")
        axes[0, 0].grid(True, linestyle=':', alpha=0.6)
        
        # Subplot 2: Precision-Recall Curve
        for name, probs in model_probs.items():
            prec, rec, _ = precision_recall_curve(y_true_binary, probs)
            axes[0, 1].plot(rec, prec, lw=2, label=f'{name}')
        axes[0, 1].set_xlim([0.0, 1.0])
        axes[0, 1].set_ylim([0.0, 1.05])
        axes[0, 1].set_xlabel('Tỷ lệ chặn DDoS thành công (Recall)')
        axes[0, 1].set_ylabel('Độ chuẩn xác chặn DDoS (Precision)')
        axes[0, 1].set_title('Đường cong Precision-Recall')
        axes[0, 1].legend(loc="lower left")
        axes[0, 1].grid(True, linestyle=':', alpha=0.6)
        
        # Subplot 3: Trade-off giữa Security (DDoS Block) và Availability (Customer Allowed) theo Threshold (XGBoost)
        if 'XGBoost' in model_probs:
            xgb_p = model_probs['XGBoost']
            thresholds = np.linspace(0, 1, 100)
            block_rates = []
            availabilities = []
            for t in thresholds:
                preds_t = (xgb_p >= t).astype(int)
                cm_t = confusion_matrix(y_true_binary, preds_t)
                tn_t, fp_t, fn_t, tp_t = cm_t.ravel()
                block_rates.append(tp_t / (tp_t + fn_t) * 100 if (tp_t + fn_t) > 0 else 0)
                availabilities.append(tn_t / (tn_t + fp_t) * 100 if (tn_t + fp_t) > 0 else 0)
            axes[1, 0].plot(thresholds, block_rates, 'r-', lw=2, label='Chặn DDoS (DDoS Block Rate)')
            axes[1, 0].plot(thresholds, availabilities, 'g-', lw=2, label='Tính sẵn sàng cho Khách (Availability)')
            axes[1, 0].axvline(0.5, color='blue', linestyle=':', label='Ngưỡng Mặc định (0.5)')
            axes[1, 0].set_xlabel('Ngưỡng ra quyết định (Decision Threshold)')
            axes[1, 0].set_ylabel('Tỷ lệ phần trăm (%)')
            axes[1, 0].set_title('Bảo mật vs Tính Sẵn sàng (XGBoost)')
            axes[1, 0].legend(loc="lower center")
            axes[1, 0].grid(True, linestyle=':', alpha=0.6)
        else:
            axes[1, 0].text(0.5, 0.5, 'Cần nạp mô hình XGBoost để vẽ', ha='center', va='center')
            
        # Subplot 4: Phân tán 2D các Đặc trưng và Ranh giới Quyết định (Decision Space)
        benign_indices = (y_true_binary == 0)
        ddos_indices = (y_true_binary == 1)
        
        # Tránh lỗi chọn mẫu nếu số lượng quá nhỏ
        size_b = min(500, sum(benign_indices))
        size_d = min(500, sum(ddos_indices))
        
        idx_b = np.random.choice(np.where(benign_indices)[0], size=size_b, replace=False) if size_b > 0 else []
        idx_d = np.random.choice(np.where(ddos_indices)[0], size=size_d, replace=False) if size_d > 0 else []
        
        if len(idx_b) > 0:
            axes[1, 1].scatter(df_clean.iloc[idx_b]['Flow Duration'] / 1e6, df_clean.iloc[idx_b]['Fwd Packet Length Max'], 
                                color='green', alpha=0.5, label='Khách hàng (Benign)', s=15)
        if len(idx_d) > 0:
            axes[1, 1].scatter(df_clean.iloc[idx_d]['Flow Duration'] / 1e6, df_clean.iloc[idx_d]['Fwd Packet Length Max'], 
                                color='red', alpha=0.4, label='DDoS Flood (Attack)', s=15)
        
        axes[1, 1].set_xlabel('Thời lượng luồng (Flow Duration - giây)')
        axes[1, 1].set_ylabel('Gói fwd lớn nhất (Fwd Packet Length Max - bytes)')
        axes[1, 1].set_title('Không gian Quyết định 2D (Decision Space)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, linestyle=':', alpha=0.6)
        
        plt.tight_layout()
        comparison_path = os.path.join(config.EXTERNAL_DATA_DIR, "availability_comparison.png")
        plt.savefig(comparison_path, dpi=300)
        plt.close()
        print(f"[+] Đã lưu biểu đồ Phân tích Tính sẵn sàng tại: {comparison_path}")
            
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
    except Exception as e:
        print(f"[!] Không thể tự động mở tệp: {e}")

if __name__ == "__main__":
    main()
