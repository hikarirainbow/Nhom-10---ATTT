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
      HE THONG PHAT HIEN XAM NHAP MANG (IDS) UNG DUNG AI
                    -- BAI TAP LON NHOM 10 --
========================================================================
    """
    print(banner)

def print_menu():
    print(" [1] Cai dat thu vien va moi truong phu thuoc")
    print(" [2] Huan luyen lai he thong va so sanh cac thuat toan")
    print(" [3] Danh gia cheo mo hinh Cascaded IDS tren 7 tap du lieu thuc te")
    print(" [4] Mo phong hieu nang va danh gia mo hinh phan tang Cascaded IDS")
    print(" [5] Khoi chay sniffer giam sat luu luong mang thoi gian thuc")
    print(" [6] Kiem thu hieu nang voi tep du lieu ngoai")
    print(" [7] Chay danh gia so sanh hieu nang 10 mo hinh co ban")
    print(" [8] Xem tai lieu huong dan su dung (README)")
    print(" [0] Thoat chuong trinh")
    print("========================================================================")

def run_command(command):
    print(f"\n[*] Dang chay lenh: {command}\n")
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Co loi xay ra khi thuc thi lenh: {e}")
    except KeyboardInterrupt:
        print("\n[INFO] Da huy thuc thi lenh tu ban phim.")
    input("\nNhan Enter de quay lai Menu chinh...")

def main():
    while True:
        clear_screen()
        print_banner()
        print_menu()
        choice = input("Nhap lua chon cua ban (0-8): ").strip()
        
        if choice == '1':
            run_command("pip install -r requirements.txt")
            confirm_dl = input("\nBan co muon su dung tai lieu goc cua ung dung? (y/n): ").strip().lower()
            if confirm_dl in ['y', 'yes']:
                run_command("python src/download_dataset.py")
        elif choice == '2':
            run_command("python src/train.py")
        elif choice == '3':
            run_command("python src/run_multi_dataset_eval.py")
        elif choice == '4':
            run_command("python src/run_cascaded_simulation.py")
        elif choice == '5':
            print("\n[!] Chu y: Chay Sniffer truc tiep can quyen Quan tri vien (Admin) va cai dat Npcap.")
            confirm = input("Xac nhan chay? (y/n): ").strip().lower()
            if confirm == 'y':
                run_command("python src/live_sniffer_interactive.py")
        elif choice == '6':
            print("\n=== KIEM THU VOI TEP DU LIEU NGOAI (.csv) ===")
            custom_path = input("Nhap duong dan tep CSV ngoai (Nhan Enter de dung tep mac dinh): ").strip()
            custom_path = custom_path.strip('\"\'')
            if custom_path:
                run_command(f'python src/evaluate.py "{custom_path}"')
            else:
                run_command("python src/evaluate.py")
        elif choice == '7':
            run_command("python src/run_availability_test.py")
        elif choice == '8':
            readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
            if os.path.exists(readme_path):
                clear_screen()
                print_banner()
                with open(readme_path, 'r', encoding='utf-8') as f:
                    print(f.read())
                input("\nNhan Enter de quay lai Menu chinh...")
            else:
                print("[!] File README.md khong ton tai.")
                input("\nNhan Enter de quay lai...")
        elif choice == '0':
            print("\nCam on ban da su dung chuong trinh. Tam biet!")
            break
        else:
            print("[!] Lua chon khong hop le. Vui long nhap lai.")
            time_delay = input("\nNhan Enter de tiep tuc...")

if __name__ == "__main__":
    main()
