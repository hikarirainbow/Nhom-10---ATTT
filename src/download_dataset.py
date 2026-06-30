import os
import sys
import requests
import webbrowser
import time

# Reconfigure stdout for UTF-8 to prevent encoding errors on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

FILE_ID = "1eCVuxAvzM_QZejfwKNNg5lSwXLYEF9fW"
DOWNLOAD_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"
DESTINATION = os.path.join("data", "download.rar")

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def download_file():
    print("========================================================================")
    print("      TAI BO DU LIEU GOC CICIDS2017 TU GOOGLE DRIVE")
    print("========================================================================")
    print(f"[*] Chuan bi tai file 'download.rar' ve thu muc 'data'...")
    
    # Tao thu muc data neu chua co
    os.makedirs("data", exist_ok=True)
    
    session = requests.Session()
    
    try:
        # Gui request dau tien de lay cookie va token canh bao virus (neu co)
        response = session.get("https://docs.google.com/uc?export=download", params={'id': FILE_ID}, stream=True)
        token = get_confirm_token(response)
        
        params = {'id': FILE_ID}
        if token:
            params['confirm'] = token
            
        response = session.get("https://docs.google.com/uc?export=download", params=params, stream=True)
        
        # Lay do dai file neu co
        total_size = int(response.headers.get('content-length', 0))
        
        print("[*] Dang tai xuong du lieu (vui long cho)...")
        
        start_time = time.time()
        downloaded = 0
        chunk_size = 1024 * 1024 # 1MB chunk
        
        with open(DESTINATION, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        speed = downloaded / (time.time() - start_time) / (1024 * 1024) # MB/s
                        sys.stdout.write(f"\r  -> Da tai: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({percent:.1f}%) | Toc do: {speed:.2f} MB/s    ")
                    else:
                        speed = downloaded / (time.time() - start_time) / (1024 * 1024)
                        sys.stdout.write(f"\r  -> Da tai: {downloaded / (1024*1024):.1f} MB | Toc do: {speed:.2f} MB/s    ")
                    sys.stdout.flush()
                    
        print(f"\n[+] Tai thanh cong! File da duoc luu tai: {DESTINATION}")
        print("[!] HUONG DAN TIEP THEO:")
        print("    1. Vui long mo thu muc 'data' va giai nen tep tin 'download.rar'.")
        print("    2. Sao chep tat ca cac tep tin .csv vao trong thu muc 'data/raw/'.")
        print("    3. Sau khi hoan tat, ban co the chay day du cac tinh nang cua ung dung.")
        
    except Exception as e:
        print(f"\n[ERROR] Khong the tai xuong truc tiep qua script: {e}")
        print("[*] He thong se tu dong mo trinh duyet web de tai tep tin...")
        time.sleep(2)
        webbrowser.open(DOWNLOAD_URL)
        print("[+] Da mo link tai ve tren trinh duyet web cua ban.")
        print("[!] Vui long luu file 'download.rar' vao thu muc 'data/' cua du an va giai nen vao 'data/raw/'.")

if __name__ == "__main__":
    download_file()
