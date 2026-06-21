import os
import sys
import subprocess

# Reconfigure stdout to use UTF-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = """
========================================================================
     🛡️  HỆ THỐNG PHÁT HIỆN XÂM NHẬP MẠNG (IDS) ỨNG DỤNG AI  🛡️
                   -- BÀI TẬP LỚN NHÓM 10 --
========================================================================
    """
    print(banner)

def print_menu():
    print(" [1] Cài đặt Thư viện Phụ thuộc (pip install)")
    print(" [2] Huấn luyện Mô hình & So sánh Thuật toán (train.py)")
    print(" [3] Kiểm thử chéo với Dataset bên ngoài (.csv) (evaluate.py)")
    print(" [4] Chạy sniffer mạng trực tiếp trên Máy tính (live_sniffer.py)")
    print(" [5] Mô phỏng & Đánh giá Tính Sẵn sàng Máy chủ (DDoS vs Khách) (run_availability_test.py)")
    print(" [6] Đọc Tài liệu Hướng dẫn (README.md)")
    print(" [7] Thoát")
    print("========================================================================")

def run_command(command):
    print(f"\n[*] Đang chạy lệnh: {command}\n")
    try:
        # Chạy trực tiếp qua subprocess để hiển thị output realtime
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Có lỗi xảy ra khi thực thi lệnh: {e}")
    except KeyboardInterrupt:
        print("\n[!] Đã hủy thực thi lệnh từ bàn phím.")
    input("\nNhấn Enter để quay lại Menu chính...")

def main():
    while True:
        clear_screen()
        print_banner()
        print_menu()
        choice = input("Nhập lựa chọn của bạn (1-7): ").strip()
        
        if choice == '1':
            run_command("pip install -r requirements.txt")
        elif choice == '2':
            run_command("python src/train.py")
        elif choice == '3':
            print("\n=== KIỂM THỬ VỚI TỆP DỮ LIỆU NGOÀI (.csv) ===")
            custom_path = input("Nhập đường dẫn tệp CSV ngoài (Nhấn Enter để dùng tệp mặc định trong data/external/): ").strip()
            # Loại bỏ dấu ngoặc kép thừa nếu kéo thả tệp vào terminal
            custom_path = custom_path.strip('\"\'')
            if custom_path:
                run_command(f'python src/evaluate.py "{custom_path}"')
            else:
                run_command("python src/evaluate.py")
        elif choice == '4':
            print("\n[!] Chú ý: Chạy Sniffer trực tiếp cần quyền Quản trị viên (Admin) và cài đặt Npcap.")
            confirm = input("Xác nhận chạy? (y/n): ").strip().lower()
            if confirm == 'y':
                run_command("python src/live_sniffer.py")
        elif choice == '5':
            run_command("python src/run_availability_test.py")
        elif choice == '6':
            readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
            if os.path.exists(readme_path):
                clear_screen()
                print_banner()
                with open(readme_path, 'r', encoding='utf-8') as f:
                    print(f.read())
                input("\nNhấn Enter để quay lại Menu chính...")
            else:
                print("[!] File README.md không tồn tại.")
                input("\nNhấn Enter để quay lại...")
        elif choice == '7':
            print("\nCảm ơn bạn đã sử dụng chương trình. Tạm biệt!")
            break
        else:
            print("[!] Lựa chọn không hợp lệ. Vui lòng nhập lại.")
            time_delay = input("\nNhấn Enter để tiếp tục...")

if __name__ == "__main__":
    main()
