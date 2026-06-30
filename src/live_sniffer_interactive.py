import os
import sys
import time
import threading
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
    sys.exit(1)

# Import Windows keyboard modules
try:
    import msvcrt
except ImportError:
    print("[!] Cảnh báo: Mô-đun 'msvcrt' chỉ chạy trên Windows. Giao diện điều khiển độ nhạy bằng phím bấm có thể không hoạt động trên OS khác.")

# Đảm bảo import được config và src từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessing import IDSPreprocessor
from src.models import CascadedIDSModel

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
        
        self.flow_iats.append(packet_time - self.last_packet_time)
        self.last_packet_time = packet_time
        
        if direction == "fwd":
            self.fwd_packets += 1
            self.fwd_lengths.append(packet_len)
        else:
            self.bwd_packets += 1
            self.bwd_lengths.append(packet_len)

    def get_duration(self):
        return (self.last_packet_time - self.start_time) * 1e6  # Microseconds

    def extract_features(self):
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
        
        flow_bytes_s = (tot_len_fwd + tot_len_bwd) / (duration / 1e6) if duration > 0 else 0
        flow_pkts_s = (tot_fwd_pkts + tot_bwd_pkts) / (duration / 1e6) if duration > 0 else 0
        
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

class InteractiveIDSDetector:
    def __init__(self):
        self.preprocessor = IDSPreprocessor()
        self.model = CascadedIDSModel()
        self.threshold = 0.50
        self.stop_sniffing_flag = False
        self.active_flows = {}
        self.lock = threading.Lock()
        
        # Load mô hình
        try:
            self.model.load()
            print("[+] Đã tải mô hình phân tầng Cascaded IDS thành công.")
        except FileNotFoundError:
            print("[!] Không tìm thấy các file mô hình đã huấn luyện trong thư mục models/.")
            print("[!] Vui lòng chạy huấn luyện trước bằng cách chọn Option [2] ở Menu chính.")
            sys.exit(1)

    def parse_packet(self, packet):
        if self.stop_sniffing_flag:
            return
            
        if not packet.haslayer(IP):
            return
            
        ip_layer = packet[IP]
        proto = ip_layer.proto
        
        if packet.haslayer(TCP):
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif packet.haslayer(UDP):
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
        else:
            src_port = 0
            dst_port = 0
            
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst
        
        if src_ip < dst_ip:
            flow_key = (src_ip, dst_ip, src_port, dst_port, proto)
            direction = "fwd"
        else:
            flow_key = (dst_ip, src_ip, dst_port, src_port, proto)
            direction = "bwd"
            
        with self.lock:
            if flow_key not in self.active_flows:
                self.active_flows[flow_key] = NetworkFlow(src_ip, dst_ip, src_port, dst_port, proto)
            
            flow = self.active_flows[flow_key]
            flow.add_packet(packet, direction)
            
            # Phân tích luồng khi thu thập đủ 10 gói tin
            if (flow.fwd_packets + flow.bwd_packets) >= 10:
                self.analyze_flow(flow_key)

    def analyze_flow(self, flow_key):
        flow = self.active_flows[flow_key]
        features = flow.extract_features()
        df_features = pd.DataFrame([features])
        
        try:
            X_scaled = self.preprocessor.transform(df_features)
            prob = self.model.predict_proba(X_scaled)[0]
            
            # Lấy giá trị ngưỡng tại thời điểm đó
            current_thresh = self.threshold
            
            if prob >= current_thresh:
                # Phát ra tín hiệu ddos và đưa thẳng IPv4 của kẻ tấn công lên
                # In màu đỏ sặc sỡ trong console bằng mã màu ANSI
                print(f"\n\033[91m[TIN HIEU DDoS - PHAT HIEN TAN CONG]\033[0m")
                print(f"\033[91m -> IP KẺ TẤN CÔNG (Attacker IPv4) : {flow.src_ip}\033[0m")
                print(f"\033[91m -> IP NẠN NHÂN (Target IPv4)      : {flow.dst_ip}\033[0m")
                print(f" -> Cổng dịch vụ (Port): {flow.src_port} -> {flow.dst_port} | Giao thức: {flow.proto}")
                print(f" -> Xác suất độc hại: {prob*100:.2f}% (Ngưỡng cảnh báo hiện tại: {current_thresh:.2f})")
                print("-" * 75)
            else:
                print(".", end="", flush=True)
                
        except Exception:
            pass
            
        del self.active_flows[flow_key]

    def print_slider(self):
        width = 20
        pos = int(self.threshold * width)
        pos = max(0, min(width, pos))
        bar = ['='] * width
        if pos < width:
            bar[pos] = '|'
        else:
            bar[-1] = '|'
        bar_str = "".join(bar)
        
        if self.threshold < 0.3:
            sensitivity = "RẤT CAO (Dễ báo động)"
        elif self.threshold < 0.6:
            sensitivity = "TRUNG BÌNH"
        else:
            sensitivity = "THẤP (Khó báo động)"
            
        # Quay về đầu dòng và ghi đè
        sys.stdout.write(f"\r[CAU HINH] Thanh dieu chinh do nhay: [{bar_str}] {self.threshold:.2f} (Do nhay: {sensitivity})        ")
        sys.stdout.flush()

    def run_sniff_thread(self, interface):
        try:
            sniff(iface=interface, prn=self.parse_packet, filter="ip", store=0, stop_filter=lambda p: self.stop_sniffing_flag)
        except Exception as e:
            print(f"\n\n\033[91m[!] LỖI KHỞI CHẠY SNIFFER: {e}\033[0m")
            print("[!] Hướng dẫn khắc phục:")
            print("    1. Vui lòng cài đặt công cụ Npcap (hoặc WinPcap) để bắt gói tin ở tầng thấp trên Windows.")
            print("       Tải Npcap miễn phí tại: https://npcap.com/")
            print("    2. Hãy đảm bảo bạn chạy ứng dụng với quyền Quản trị viên (Run as Administrator).")
            print("\n-> Nhấn phím [q] để quay lại Menu chính...")
            self.stop_sniffing_flag = True

    def start(self):
        interface = config.SNIFF_INTERFACE
        
        print("\n========================================================================")
        print("      HE THONG PHAT HIEN XAM NHAP MANG (IDS) TUONG TAC REALTIME")
        print("========================================================================")
        print(f"[*] Card mạng: {interface if interface else 'Mặc định (Tự động lựa chọn)'}")
        print("[*] Hướng dẫn điều khiển:")
        print("    - Nhấn phím [+] để TĂNG độ nhạy (giảm ngưỡng lọc)")
        print("    - Nhấn phím [-] để GIẢM độ nhạy (tăng ngưỡng lọc)")
        print("    - Nhấn phím [q] hoặc [Ctrl+C] để thoát chương trình")
        print("========================================================================")
        
        # Bắt đầu chạy Sniffer ở luồng phụ (background thread)
        sniff_thread = threading.Thread(target=self.run_sniff_thread, args=(interface,))
        sniff_thread.daemon = True
        sniff_thread.start()
        
        print("[*] Bắt đầu bắt gói tin mạng thời gian thực. Đang lắng nghe...")
        self.print_slider()
        
        # Vòng lặp chính ở luồng chính lắng nghe sự kiện bàn phím không chặn (Non-blocking keyboard read)
        try:
            while not self.stop_sniffing_flag:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    # Trên Windows, getch() có thể trả về ký tự đặc biệt, lọc lấy byte thường
                    if key in [b'+', b'=']:
                        # Tăng độ nhạy đồng nghĩa với GIẢM ngưỡng threshold
                        self.threshold = max(0.00, self.threshold - 0.05)
                        self.print_slider()
                    elif key in [b'-', b'_']:
                        # Giảm độ nhạy đồng nghĩa với TĂNG ngưỡng threshold
                        self.threshold = min(1.00, self.threshold + 0.05)
                        self.print_slider()
                    elif key in [b'q', b'Q', b'\x03']:
                        print("\n\n[*] Đang dừng tiến trình bắt gói tin...")
                        self.stop_sniffing_flag = True
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n[!] Nhận tín hiệu ngắt từ bàn phím. Đang dừng...")
            self.stop_sniffing_flag = True
            
        sniff_thread.join(timeout=2.0)
        print("[+] Hệ thống IDS đã đóng an toàn. Tạm biệt!")

if __name__ == "__main__":
    detector = InteractiveIDSDetector()
    detector.start()
