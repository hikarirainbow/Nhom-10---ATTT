import os
import sys
import time
from collections import defaultdict
import numpy as np
import pandas as pd
import joblib

# Reconfigure stdout to use UTF-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Thư viện Scapy để bắt và phân tích gói tin
try:
    from scapy.all import sniff, IP, TCP, UDP
except ImportError:
    print("[!] Không tìm thấy thư viện 'scapy'. Vui lòng cài đặt bằng: pip install scapy")
    print("[!] Chương trình sniffer realtime sẽ không thể chạy nếu thiếu Scapy.")

# Đảm bảo import được config và src từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessing import IDSPreprocessor
from src.models import IDSSupervisedModel

class NetworkFlow:
    """
    Class quản lý trạng thái của một luồng lưu lượng (Flow) và tính toán 15 đặc trưng chính
    """
    def __init__(self, src_ip, dst_ip, src_port, dst_port, proto):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.proto = proto
        
        self.start_time = time.time()
        self.last_packet_time = self.start_time
        
        # Số lượng gói tin
        self.fwd_packets = 0
        self.bwd_packets = 0
        
        # Độ dài gói tin
        self.fwd_lengths = []
        self.bwd_lengths = []
        
        # Thời gian giữa các gói tin (IAT - Inter Arrival Time)
        self.flow_iats = []

    def add_packet(self, packet, direction):
        packet_time = float(packet.time)
        packet_len = len(packet)
        
        # Tính khoảng thời gian giữa các gói tin (IAT)
        self.flow_iats.append(packet_time - self.last_packet_time)
        self.last_packet_time = packet_time
        
        if direction == "fwd":
            self.fwd_packets += 1
            self.fwd_lengths.append(packet_len)
        else:
            self.bwd_packets += 1
            self.bwd_lengths.append(packet_len)

    def get_duration(self):
        return (self.last_packet_time - self.start_time) * 1e6  # Đổi sang Microseconds giống CICIDS2017

    def extract_features(self):
        """Trích xuất 15 thuộc tính cấu hình tương đương CICFlowMeter"""
        duration = self.get_duration()
        tot_fwd_pkts = self.fwd_packets
        tot_bwd_pkts = self.bwd_packets
        
        tot_len_fwd = sum(self.fwd_lengths) if self.fwd_lengths else 0
        tot_len_bwd = sum(self.bwd_lengths) if self.bwd_lengths else 0
        
        fwd_len_max = max(self.fwd_lengths) if self.fwd_lengths else 0
        fwd_len_min = min(self.fwd_lengths) if self.fwd_lengths else 0
        fwd_len_mean = np.mean(self.fwd_lengths) if self.fwd_lengths else 0
        
        bwd_len_max = max(self.bwd_lengths) if self.bwd_lengths else 0
        bwd_len_min = min(self.bwd_lengths) if self.bwd_lengths else 0
        bwd_len_mean = np.mean(self.bwd_lengths) if self.bwd_lengths else 0
        
        # Tốc độ gói tin và byte trên giây
        flow_bytes_s = (tot_len_fwd + tot_len_bwd) / (duration / 1e6) if duration > 0 else 0
        flow_pkts_s = (tot_fwd_pkts + tot_bwd_pkts) / (duration / 1e6) if duration > 0 else 0
        
        # Thống kê IAT (Inter Arrival Time)
        flow_iat_mean = np.mean(self.flow_iats) * 1e6 if self.flow_iats else 0
        flow_iat_max = max(self.flow_iats) * 1e6 if self.flow_iats else 0
        
        return {
            'Flow Duration': duration,
            'Total Fwd Packets': tot_fwd_pkts,
            'Total Backward Packets': tot_bwd_pkts,
            'Total Length of Fwd Packets': tot_len_fwd,
            'Total Length of Bwd Packets': tot_len_bwd,
            'Fwd Packet Length Max': fwd_len_max,
            'Fwd Packet Length Min': fwd_len_min,
            'Fwd Packet Length Mean': fwd_len_mean,
            'Bwd Packet Length Max': bwd_len_max,
            'Bwd Packet Length Min': bwd_len_min,
            'Bwd Packet Length Mean': bwd_len_mean,
            'Flow Bytes/s': flow_bytes_s,
            'Flow Packets/s': flow_pkts_s,
            'Flow IAT Mean': flow_iat_mean,
            'Flow IAT Max': flow_iat_max
        }


class LiveIDSDetector:
    def __init__(self, model_type='rf'):
        self.preprocessor = IDSPreprocessor()
        self.model = IDSSupervisedModel(model_type=model_type)
        
        # Load mô hình và scaler
        try:
            self.model.load()
            print(f"[+] Đã tải mô hình phân loại {model_type} thành công.")
        except FileNotFoundError:
            print(f"[!] Không thấy mô hình {model_type}. Vui lòng chạy huấn luyện trước bằng `python src/train.py`.")
            sys.exit(1)
            
        # Dictionary lưu trữ luồng mạng đang hoạt động
        # Key: (src_ip, dst_ip, src_port, dst_port, proto)
        self.active_flows = {}

    def parse_packet(self, packet):
        """Callback xử lý mỗi gói tin bắt được"""
        if not packet.haslayer(IP):
            return
            
        ip_layer = packet[IP]
        proto = ip_layer.proto
        
        # Chỉ xử lý TCP và UDP để lấy port
        if packet.haslayer(TCP):
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif packet.haslayer(UDP):
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
        else:
            # Gói tin IP khác (ví dụ ICMP), gán port mặc định 0
            src_port = 0
            dst_port = 0
            
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        
        # Xác định key của flow (đảm bảo hai chiều giao tiếp cùng chung 1 flow key)
        # Flow key chính: (IP nhỏ, IP lớn, Port nhỏ, Port lớn, Protocol)
        if src_ip < dst_ip:
            flow_key = (src_ip, dst_ip, src_port, dst_port, proto)
            direction = "fwd"
        else:
            flow_key = (dst_ip, src_ip, dst_port, src_port, proto)
            direction = "bwd"
            
        # Nếu luồng chưa tồn tại, tạo mới
        if flow_key not in self.active_flows:
            self.active_flows[flow_key] = NetworkFlow(src_ip, dst_ip, src_port, dst_port, proto)
            
        # Cập nhật thông số gói tin vào luồng
        flow = self.active_flows[flow_key]
        flow.add_packet(packet, direction)
        
        # Nếu luồng đã thu thập đủ gói tin (ví dụ > 5 gói) hoặc thời gian hoạt động kéo dài, tiến hành phân tích
        if (flow.fwd_packets + flow.bwd_packets) >= 10:
            self.analyze_flow(flow_key)

    def analyze_flow(self, flow_key):
        flow = self.active_flows[flow_key]
        
        # Trích xuất đặc trưng
        features = flow.extract_features()
        df_features = pd.DataFrame([features])
        
        # Tiền xử lý (scaling) sử dụng preprocessor đã load scaler
        try:
            X_scaled = self.preprocessor.transform(df_features)
            
            # Dự đoán
            prob = self.model.predict_proba(X_scaled)[0]
            pred = 1 if prob >= config.ALERT_THRESHOLD else 0
            
            # Hiển thị cảnh báo
            if pred == 1:
                print(f"\n[ ALERT] PHÁT HIỆN TẤN CÔNG (IDS Alert)!")
                print(f" -> Luồng: {flow.src_ip}:{flow.src_port} -> {flow.dst_ip}:{flow.dst_port} (Proto: {flow.proto})")
                print(f" -> Xác suất độc hại: {prob*100:.2f}%")
                print(f" -> Đặc trưng tiêu biểu: Flow Duration: {features['Flow Duration']:.2f}μs, Fwd Packets: {features['Total Fwd Packets']}, Bwd Packets: {features['Total Backward Packets']}")
            else:
                print(".", end="", flush=True) # Dấu chấm biểu thị luồng Benign bình thường
                
        except Exception as e:
            # Bỏ qua các lỗi tính toán chia cho 0 hoặc scaler chưa sẵn sàng
            pass
            
        # Xóa khỏi danh sách hoạt động để tránh đầy bộ nhớ
        del self.active_flows[flow_key]

    def start_sniffing(self, interface=None):
        if interface is None:
            interface = config.SNIFF_INTERFACE
            
        print(f"[*] Bắt đầu giám sát lưu lượng mạng realtime...")
        print(f"[*] Card mạng: {interface if interface else 'Mặc định'}")
        print("[*] Nhấn Ctrl+C để dừng giám sát.")
        
        # Chạy sniffer với bộ lọc IP
        sniff(iface=interface, prn=self.parse_packet, filter="ip", store=0)


if __name__ == "__main__":
    print("\n========================================================")
    print("      🔍 CHỌN MÔ HÌNH HỌC MÁY CHO LIVE SNIFFER 🔍")
    print("========================================================")
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
    for idx, (m_type, m_name) in enumerate(models_config.items(), 1):
        print(f" [{idx}] {m_name} ({m_type})")
    print("========================================================")
    
    choice = input("Nhập lựa chọn của bạn (Mặc định: 1 - Random Forest): ").strip()
    selected_type = 'rf'
    if choice:
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(models_config):
                selected_type = list(models_config.keys())[choice_idx]
        except ValueError:
            pass
            
    print(f"\n[*] Đang khởi tạo bộ dò với mô hình: {models_config[selected_type]}...")
    detector = LiveIDSDetector(model_type=selected_type)
    try:
        detector.start_sniffing()
    except KeyboardInterrupt:
        print("\n[+] Đã dừng sniffer. Chương trình kết thúc.")
