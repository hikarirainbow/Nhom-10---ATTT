import os
import sys

# Reconfigure stdout to use UTF-8 on Windows console to prevent UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

def print_ascii_bar_chart(data_dict, title="📊 ĐỒ THỊ THANH"):
    """
    Vẽ đồ thị thanh ASCII từ dictionary dữ liệu.
    Hỗ trợ hiển thị phần trăm (nếu giá trị <= 1.0) hoặc số lượng thực tế.
    """
    print(f"\n{title}")
    print("=" * 65)
    if not data_dict:
        print(" [!] Không có dữ liệu để hiển thị.")
        print("=" * 65)
        return
        
    max_val = max(data_dict.values())
    max_key_len = max(len(str(k)) for k in data_dict.keys())
    
    for key, val in data_dict.items():
        # Chiều dài tối đa của thanh là 30 ký tự
        bar_len = int((val / max_val) * 30) if max_val > 0 else 0
        bar = "█" * bar_len + "░" * (30 - bar_len)
        if val <= 1.0:
            print(f" {str(key):<{max_key_len}} | {bar} | {val*100:6.2f}%")
        else:
            print(f" {str(key):<{max_key_len}} | {bar} | {val:,.0f}")
    print("=" * 65)

def print_ascii_confusion_matrix(cm, labels=["BENIGN (An toàn)", "ATTACK (Độc hại)"]):
    """
    Vẽ ma trận nhầm lẫn (Confusion Matrix) 2x2 đẹp mắt bằng nét hộp UTF-8.
    """
    tn, fp = cm[0][0], cm[0][1]
    fn, tp = cm[1][0], cm[1][1]
    
    print("\n📊 MA TRẬN NHẦM LẪN (CONFUSION MATRIX)")
    print("┌───────────────────────────┬───────────────────────────────────┐")
    print("│                           │        Dự đoán (Predicted)        │")
    print(f"│ Thực tế (Actual)          │ {labels[0]:^15} │ {labels[1]:^15} │")
    print("├───────────────────────────┼─────────────────┬─────────────────┤")
    print(f"│ {labels[0]:<25} │ {tn:^15,.0f} │ {fp:^15,.0f} │")
    print("├───────────────────────────┼─────────────────┼─────────────────┤")
    print(f"│ {labels[1]:<25} │ {fn:^15,.0f} │ {tp:^15,.0f} │")
    print("└───────────────────────────┴─────────────────┴─────────────────┘")

def print_text_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=40, fill='█'):
    """
    Vẽ thanh tiến trình trên một dòng Terminal.
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        print()
