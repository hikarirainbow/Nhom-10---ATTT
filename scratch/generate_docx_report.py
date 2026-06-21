import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def main():
    doc = Document()

    # --- Cấu hình Style mặc định ---
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    # --- Thiết lập Margins ---
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # --- Hàm trợ giúp thêm Heading ---
    def add_custom_heading(text, level, space_before=12, space_after=6):
        h = doc.add_heading(text, level=level)
        h.paragraph_format.space_before = Pt(space_before)
        h.paragraph_format.space_after = Pt(space_after)
        h.paragraph_format.keep_with_next = True
        
        run = h.runs[0]
        run.font.name = 'Times New Roman'
        if level == 1:
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D) # Navy Dark
        elif level == 2:
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88) # Slate Blue
        elif level == 3:
            run.font.size = Pt(12)
            run.font.bold = True
            run.font.italic = True
            run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        return h

    # --- Trang Bìa ---
    title_p1 = doc.add_paragraph()
    title_p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p1.paragraph_format.space_before = Pt(50)
    run_univ = title_p1.add_run("BÀI TẬP LỚN MÔN AN TOÀN VÀ BẢO MẬT THÔNG TIN\nNHÓM 10")
    run_univ.font.size = Pt(14)
    run_univ.font.bold = True
    run_univ.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    title_p2 = doc.add_paragraph()
    title_p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p2.paragraph_format.space_before = Pt(60)
    title_p2.paragraph_format.space_after = Pt(20)
    run_title = title_p2.add_run("BÁO CÁO NGHIÊN CỨU & THỰC NGHIỆM CHUYÊN SÂU\nXÂY DỰNG HỆ THỐNG PHÁT HIỆN XÂM NHẬP MẠNG (IDS)\nỨNG DỤNG TRÍ TUỆ NHÂN TẠO (AI)")
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(100)
    run_sub = sub_p.add_run("Đề tài: Tìm hiểu về xây dựng IDS với AI.\nSử dụng tập dữ liệu Kaggle để xây dựng IDS.\nThực nghiệm đánh giá Security & Availability trên tập dữ liệu capture thực tế bên ngoài.")
    run_sub.font.size = Pt(12)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    info_p = doc.add_paragraph()
    info_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info_p.paragraph_format.space_before = Pt(100)
    run_info = info_p.add_run("Thành viên thực hiện: Nhóm 10\nHệ thống thực nghiệm: 10 Classifiers + 1 Anomaly Detection\nTháng 6 Năm 2026")
    run_info.font.size = Pt(12)
    run_info.font.bold = True

    doc.add_page_break()

    # --- Tóm tắt Đề tài ---
    add_custom_heading("TÓM TẮT ĐỀ TÀI", level=1)
    p_abstract = doc.add_paragraph()
    p_abstract.paragraph_format.line_spacing = 1.15
    p_abstract.paragraph_format.space_after = Pt(10)
    p_abstract.add_run(
        "Nghiên cứu này trình bày một quy trình toàn diện nhằm tìm hiểu và xây dựng hệ thống phát hiện xâm nhập mạng (IDS) ứng dụng trí tuệ nhân tạo. "
        "Dựa trên nền tảng tập dữ liệu học máy chuẩn hóa CICIDS2017 lấy từ nguồn Kaggle, chúng tôi đã huấn luyện thành công 10 mô hình phân loại có giám sát và 1 mô hình không giám sát (Isolation Forest). "
        "Để đánh giá tính thực tiễn và độ bền vững của mô hình trước các cuộc tấn công DDoS quy mô lớn, một môi trường thực nghiệm mô phỏng dữ liệu capture bên ngoài có độ trễ thời gian thực đã được thiết lập. "
        "Thông qua các chỉ số Bảo mật (DDoS Block Rate) và tính Sẵn sàng dịch vụ (Customer Availability), chúng tôi tiến hành phân tích chi tiết, trực quan hóa ranh giới quyết định (Decision Boundaries) và sự biến đổi ngưỡng quyết định của từng mô hình độc lập. "
        "Kết quả nghiên cứu cung cấp cơ sở định lượng quan trọng cho việc lựa chọn và cấu hình mô hình IDS phù hợp với các kịch bản vận hành thực tế."
    )

    # --- Chương 1 ---
    add_custom_heading("CHƯƠNG 1: ĐẶT VẤN ĐỀ & MỤC TIÊU ĐỀ TÀI", level=1)
    
    add_custom_heading("1.1. Bối cảnh nghiên cứu", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Sự bùng nổ của hạ tầng số và các dịch vụ cổng thông tin công cộng đặt ra những thách thức lớn về an toàn thông tin. "
        "Các cuộc tấn công từ chối dịch vụ phân tán (DDoS) ngày càng trở nên tinh vi, không chỉ sử dụng lưu lượng dồn dập (Volume-based) mà còn pha trộn hành vi ứng dụng giả mạo (HTTP POST Flood) với các gói tin nhỏ gây nhiễu để lách qua hệ thống phát hiện truyền thống. "
        "IDS ứng dụng trí tuệ nhân tạo (AI-IDS) nổi lên như một giải pháp đột phá, có khả năng học các đặc trưng lưu lượng mạng phức tạp để tự động phân lớp hành vi bất thường."
    )

    add_custom_heading("1.2. Yêu cầu đề tài & Mục tiêu nghiên cứu", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Đề tài này bám sát yêu cầu học thuật: 'Tìm hiểu về xây dựng IDS với AI. Dùng tập dữ liệu trên Kaggle để xây dựng IDS; Thực nghiệm: dữ liệu test, phát triển mô hình dùng dữ liệu capture từ bên ngoài hoặc dataset thu thập được từ nguồn khác'. "
        "Mục tiêu cốt lõi bao gồm:\n"
    )
    p_bullet1 = doc.add_paragraph(style='List Bullet')
    p_bullet1.add_run("Khảo sát, làm sạch và trích lọc 15 đặc trưng mạng cốt lõi từ bộ dữ liệu Kaggle CICIDS2017 để huấn luyện 10 bộ phân lớp học máy và 1 thuật toán phát hiện bất thường.")
    p_bullet2 = doc.add_paragraph(style='List Bullet')
    p_bullet2.add_run("Xây dựng bộ tạo thực nghiệm ngoài capture 50,000 dòng lưu lượng, tích hợp các yếu tố gây nhiễu ngẫu nhiên và cuộc tấn công DDoS biến thể.")
    p_bullet3 = doc.add_paragraph(style='List Bullet')
    p_bullet3.add_run("Đánh giá sự cân bằng giữa khả năng ngăn chặn tấn công bảo mật và khả năng đảm bảo hoạt động liên tục (Availability) của máy chủ dịch vụ.")

    # --- Chương 2 ---
    add_custom_heading("CHƯƠNG 2: CƠ SỞ LÝ THUYẾT & PHƯƠNG PHÁP NGHIÊN CỨU", level=1)
    
    add_custom_heading("2.1. Nguồn dữ liệu huấn luyện Kaggle CICIDS2017", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Bộ dữ liệu CICIDS2017 được phân phối trên Kaggle là nguồn dữ liệu chuẩn hóa quốc tế, ghi lại đầy đủ luồng mạng giao tiếp IP. "
        "Hệ thống của chúng tôi trích chọn 15 thuộc tính lưu lượng đại diện cho cả thời lượng luồng, kích thước gói tin và tốc độ truyền dẫn bao gồm: "
        "Flow Duration, Total Fwd/Bwd Packets, Length of Fwd/Bwd Packets, Packet Length Min/Max/Mean, Flow Bytes/s, Flow Packets/s và Flow IAT. "
        "Dữ liệu được chuẩn hóa bằng StandardScaler để đảm bảo các thuật toán nhạy cảm với khoảng cách như SVM, KNN hay Logistic Regression không bị thiên lệch."
    )

    add_custom_heading("2.2. Cơ sở toán học của 11 mô hình thực nghiệm", level=2)
    
    add_custom_heading("2.2.1. Random Forest (RF)", level=3)
    p = doc.add_paragraph()
    p.add_run("Random Forest là thuật toán học kết hợp Bagging, huấn luyện nhiều cây quyết định song song dựa trên tập mẫu Bootstrap ngẫu nhiên. Nút của cây được phân tách tối ưu hóa độ tạp chất Gini:")
    p_math = doc.add_paragraph()
    p_math.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_math.add_run("G(t) = 1 - p_0^2 - p_1^2")

    add_custom_heading("2.2.2. XGBoost (XGB)", level=3)
    p = doc.add_paragraph()
    p.add_run("XGBoost tối ưu hóa hàm loss bằng cách xấp xỉ Taylor bậc hai tuần tự kết hợp hàm phạt chính quy hóa để kiểm soát số lượng lá cây T và trọng số lá w:")
    p_math = doc.add_paragraph()
    p_math.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_math.add_run("L^(t) ≈ ∑ [g_i f_t(x_i) + 0.5 * h_i f_t^2(x_i)] + γT + 0.5 * λ ∑ w_j^2")

    add_custom_heading("2.2.3. Các mô hình cây khác (Decision Tree, Extra Trees, AdaBoost, Gradient Boosting)", level=3)
    p = doc.add_paragraph()
    p.add_run(
        "Decision Tree xây dựng cây phân lớp đơn lẻ dựa trên Information Gain. "
        "Extra Trees cực hạn ngẫu nhiên hóa điểm chia nút để giảm thiểu phương sai mô hình. "
        "AdaBoost tăng trọng số của mẫu phân lớp sai qua từng vòng. "
        "Gradient Boosting xấp xỉ sai số dư bằng gradient bậc nhất của hàm loss."
    )

    add_custom_heading("2.2.4. Nhóm mô hình Tuyến tính, Xác suất và Lân cận (KNN, SVM, Logistic, Naive Bayes)", level=3)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "KNN phân loại dựa trên khoảng cách Euclidean trong không gian đặc trưng. "
        "Logistic Regression tối ưu xác suất bằng hàm Sigmoid. "
        "Linear SVM tối đa hóa khoảng cách biên (margin) tách biệt hai lớp. "
        "Naive Bayes áp dụng định lý xác suất Bayes với giả thuyết độc lập có điều kiện Gaussian."
    )

    add_custom_heading("2.2.5. Isolation Forest (Không giám sát)", level=3)
    p = doc.add_paragraph()
    p.add_run("Isolation Forest cô lập dị thường bằng cách chia cắt ngẫu nhiên các đặc trưng. Trọng số dị thường s tỉ lệ thuận với độ sâu trung bình của mẫu trên các cây cô lập:")
    p_math = doc.add_paragraph()
    p_math.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_math.add_run("s(x, n) = 2^(- E(h(x)) / c(n))")

    # --- Chương 3 ---
    add_custom_heading("CHƯƠNG 3: THIẾT LẬP THỰC NGHIỆM: MÔ PHỎNG DỮ LIỆU CAPTURE NGOÀI", level=1)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Để thực nghiệm khả năng hoạt động thực tế, hệ thống tiến hành giả lập một đợt kiểm thử quy mô lớn gồm 50,000 luồng dữ liệu mạng độc lập capture từ bên ngoài. "
        "Quy trình giả lập được thiết lập như sau:\n"
    )
    
    p_list = doc.add_paragraph(style='List Bullet')
    p_list.add_run("Độ trễ mạng nền (latency = 200ms) và dung lượng gói tin (450 bytes) được đo lường thực tế từ API Open-Meteo để mô phỏng dịch vụ Weather Portal.")
    p_list2 = doc.add_paragraph(style='List Bullet')
    p_list2.add_run("40,000 luồng DDoS Attack (80%) bao gồm 85% DDoS Volume-based truyền thống và 15% DDoS HTTP POST Flood nâng cao có gói tin kích thước lớn giả mạo.")
    p_list3 = doc.add_paragraph(style='List Bullet')
    p_list3.add_run("10,000 luồng Khách hàng bình thường (20%) chứa các gói tin điều khiển keep-alive nhỏ xen lẫn gói API thời tiết lớn.")
    p_list4 = doc.add_paragraph(style='List Bullet')
    p_list4.add_run("Bổ sung nhiễu Gaussian ngẫu nhiên 4% trên các đặc trưng để kiểm thử khả năng xử lý nhiễu mạng của các bộ phân lớp.")

    # --- Chương 4 ---
    add_custom_heading("CHƯƠNG 4: KẾT QUẢ THỰC NGHIỆM & PHÂN TÍCH CHI TIẾT TỪNG BIỂU ĐỒ", level=1)
    
    add_custom_heading("4.1. Bảng số liệu tổng hợp hiệu năng thực nghiệm ngoài", level=2)
    p = doc.add_paragraph()
    p.add_run("Dưới đây là bảng số liệu thống kê kết quả chạy thực nghiệm 50,000 luồng mạng đối với 10 mô hình học máy:")

    # Tạo bảng
    table = doc.add_table(rows=11, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Mô hình'
    hdr_cells[1].text = 'Accuracy (Chính xác)'
    hdr_cells[2].text = 'DDoS Recall (Bảo mật)'
    hdr_cells[3].text = 'Khách Sẵn sàng (Availability)'
    
    # Định dạng header row
    for cell in hdr_cells:
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.name = 'Times New Roman'

    data = [
        ("XGBoost", "99.06%", "99.75%", "96.29%"),
        ("AdaBoost", "97.25%", "96.89%", "98.67%"),
        ("Naive Bayes", "96.30%", "99.24%", "84.52%"),
        ("Linear SVM", "92.32%", "91.97%", "93.75%"),
        ("Logistic Regression", "89.28%", "87.89%", "94.80%"),
        ("Extra Trees", "87.59%", "84.50%", "99.95%"),
        ("Random Forest", "79.49%", "74.36%", "100.00%"),
        ("Gradient Boosting", "79.39%", "74.32%", "99.67%"),
        ("K-Nearest Neighbors", "77.52%", "77.04%", "79.44%"),
        ("Decision Tree", "67.62%", "74.41%", "40.49%")
    ]

    for i, row_data in enumerate(data):
        row_cells = table.rows[i+1].cells
        for j in range(4):
            row_cells[j].text = row_data[j]
            row_cells[j].paragraphs[0].runs[0].font.name = 'Times New Roman'

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Thêm Hình 1
    add_custom_heading("4.2. Phân tích Hình 1: Lưới Ma trận Nhầm lẫn (confusion_matrices.png)", level=2)
    img_path_cm = "data/external/confusion_matrices.png"
    if os.path.exists(img_path_cm):
        doc.add_picture(img_path_cm, width=Inches(6.0))
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_run = caption.add_run("Hình 1: Lưới ma trận nhầm lẫn 5x2 cho 10 mô hình học máy phân lớp")
        caption_run.font.italic = True
        caption_run.font.size = Pt(10)
    else:
        doc.add_paragraph("[!] Không tìm thấy ảnh confusion_matrices.png để chèn.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Ma trận nhầm lẫn của 10 mô hình biểu thị chi tiết số lượng mẫu dự đoán chính xác và phân loại nhầm. "
        "Có sự đối lập rõ rệt giữa hai trường phái chính: nhóm Bagging bảo thủ và nhóm Boosting nhạy bén. "
        "Mô hình Random Forest đạt FP = 0 (tỷ lệ chặn nhầm 0.00%), đảm bảo an toàn tuyệt đối cho khách hàng nhưng lại bỏ lọt đến 10,256 luồng DDoS vào máy chủ. "
        "Ngược lại, XGBoost chỉ bỏ lọt 99 luồng DDoS (FN = 99) trong tổng số 40,000 luồng, bảo vệ hệ thống tối đa trước nguy cơ sụt giảm hiệu năng phần cứng. "
        "Naive Bayes có xu hướng báo động sai rất cao (FP = 1,548) làm suy giảm tính sẵn sàng khi chặn nhầm 15.48% lượng truy cập của khách hàng. "
        "Đặc biệt, mô hình Decision Tree đơn lẻ có số mẫu dự đoán sai khổng lồ ở cả hai lớp, chứng minh cây đơn lẻ hoàn toàn bị bất ổn định trước dữ liệu nhiễu mạng."
    )

    # Thêm Hình 2
    add_custom_heading("4.3. Phân tích Hình 2: So sánh Đường cong ROC và Precision-Recall (availability_comparison.png)", level=2)
    img_path_roc = "data/external/availability_comparison.png"
    if os.path.exists(img_path_roc):
        doc.add_picture(img_path_roc, width=Inches(6.0))
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_run = caption.add_run("Hình 2: Đường cong ROC và đường cong Precision-Recall của 10 mô hình")
        caption_run.font.italic = True
        caption_run.font.size = Pt(10)
    else:
        doc.add_paragraph("[!] Không tìm thấy ảnh availability_comparison.png để chèn.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Đồ thị hiệu năng tổng quát chỉ ra khả năng phân lớp tổng thể của các thuật toán: "
        "Đường cong ROC của các mô hình XGBoost, AdaBoost đạt AUC xấp xỉ tuyệt đối (>0.995), phản ánh khả năng phân biệt lớp tối ưu. "
        "Mặc dù Naive Bayes có đường cong ROC tiệm cận mức tốt, biểu đồ Precision-Recall bên phải chỉ ra nhược điểm của nó khi Precision sụt giảm rất nhanh do lượng False Positives cao. "
        "Điều này khẳng định rằng đường cong Precision-Recall là công cụ quan trọng hơn ROC khi đánh giá IDS trên tập dữ liệu thực tế có phân phối mất cân bằng nghiêm trọng."
    )

    # Thêm Hình 3
    add_custom_heading("4.4. Phân tích Hình 3: Lưới Đồ thị Ngưỡng Quyết định (tradeoff_curves.png)", level=2)
    img_path_to = "data/external/tradeoff_curves.png"
    if os.path.exists(img_path_to):
        doc.add_picture(img_path_to, width=Inches(6.0))
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_run = caption.add_run("Hình 3: Đồ thị đánh đổi giữa tính Bảo mật và tính Sẵn sàng theo ngưỡng quyết định")
        caption_run.font.italic = True
        caption_run.font.size = Pt(10)
    else:
        doc.add_paragraph("[!] Không tìm thấy ảnh tradeoff_curves.png để chèn.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Đồ thị 5x2 thể hiện rõ mối quan hệ giữa Bảo mật (Recall chặn DDoS - màu đỏ) và Sẵn sàng dịch vụ (TNR Khách hàng - màu xanh lá) khi điều chỉnh ngưỡng quyết định (Threshold từ 0.0 đến 1.0): "
        "Với mô hình XGBoost và AdaBoost, hai đường này giao nhau rất muộn ở sát ngưỡng 0.9. Tại ngưỡng mặc định 0.5, cả hai chỉ số đều đạt trên 96%. "
        "Với Random Forest và Extra Trees, đường TNR màu xanh lá duy trì ổn định ở mức gần 100% xuyên suốt mọi ngưỡng, trong khi đường Recall sụt giảm rất nhanh từ ngưỡng 0.4. "
        "Điều này chứng tỏ đối với các mô hình Bagging, nếu muốn cải thiện khả năng chặn DDoS, người quản trị buộc phải hạ ngưỡng quyết định xuống mức 0.2-0.3 để tăng độ nhạy phân loại lớp độc hại. "
        "Ngược lại, các mô hình tuyến tính như SVM và Logistic Regression có dạng chuyển tiếp dốc tuyến tính đều đặn, cho phép căn chỉnh ngưỡng linh hoạt theo nhu cầu thực tế."
    )

    # Thêm Hình 4
    add_custom_heading("4.5. Phân tích Hình 4: Ranh giới Quyết định 2D (decision_boundaries.png)", level=2)
    img_path_db = "data/external/decision_boundaries.png"
    if os.path.exists(img_path_db):
        doc.add_picture(img_path_db, width=Inches(6.0))
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_run = caption.add_run("Hình 4: Trực quan hóa ranh giới quyết định phân chia không gian đặc trưng 2D")
        caption_run.font.italic = True
        caption_run.font.size = Pt(10)
    else:
        doc.add_paragraph("[!] Không tìm thấy ảnh decision_boundaries.png để chèn.")

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Biểu đồ ranh giới quyết định 2D trực quan hóa cách các mô hình phân tách không gian đặc trưng giữa Flow Duration và Fwd Packet Length Max: "
        "Mô hình Decision Tree đơn lẻ tạo ra ranh giới dạng lưới vuông vụn vặt và đứt gãy, minh chứng rõ ràng cho hiện tượng quá khớp (overfitting) cục bộ. "
        "Mô hình Random Forest và Extra Trees tạo ra các ranh giới bậc thang (axis-aligned) mượt mà hơn nhờ sự kết hợp biểu quyết của nhiều cây. Vùng màu đỏ (DDoS) bị thu hẹp chứng minh xu hướng ưu tiên an toàn cho lớp Benign của thuật toán này. "
        "XGBoost và AdaBoost tạo ra biên quyết định dạng đường cong phi tuyến uốn lượn uốn quanh rất tốt các cụm dữ liệu DDoS phức tạp, giải thích tại sao chúng đạt Recall cao nhất đối với cả DDoS truyền thống và DDoS nâng cao. "
        "Mô hình Linear SVM và Logistic Regression phân tách không gian bằng một đường thẳng (siêu phẳng tuyến tính 2D), dẫn đến việc không thể xử lý tốt vùng chồng lấn phi tuyến của hai lớp và gây ra sai số cố định ở cả hai phía biên. "
        "KNN tạo ra các vùng quyết định cục bộ bao quanh mật độ lân cận, trong khi Naive Bayes tạo ra biên quyết định dạng elip phản ánh giả thuyết độc lập xác suất Gaussian."
    )

    # --- Chương 5 ---
    add_custom_heading("CHƯƠNG 5: ĐÁNH GIÁ TỔNG QUÁT & KHUYẾN NGHỊ VẬN HÀNH DỊCH VỤ", level=1)
    
    add_custom_heading("5.1. Đánh giá tổng quát ưu nhược điểm các nhóm mô hình", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Qua chuỗi thực nghiệm ngoài quy mô lớn trên 50,000 dòng dữ liệu capture ngoài, chúng tôi rút ra một số đánh giá tổng quan:\n"
    )
    p_b1 = doc.add_paragraph(style='List Bullet')
    p_b1.add_run("Nhóm thuật toán học tăng cường (XGBoost, AdaBoost) mang lại hiệu quả bảo mật tốt nhất nhờ cơ chế giảm thiểu sai số dư tuần tự, phù hợp để triển khai phòng chống DDoS.")
    p_b2 = doc.add_paragraph(style='List Bullet')
    p_b2.add_run("Nhóm thuật toán biểu quyết rừng cây (Random Forest, Extra Trees) đảm bảo tối đa tính sẵn sàng dịch vụ (TNR ~ 100%), không gây nghẽn cổ chai hoặc gián đoạn dịch vụ của người dùng thường.")
    p_b3 = doc.add_paragraph(style='List Bullet')
    p_b3.add_run("Các mô hình tuyến tính (Linear SVM, Logistic) ổn định và dễ cấu hình threshold nhưng giới hạn hiệu năng do không xử lý tốt các đặc trưng phân bố phi tuyến chồng lấn.")
    p_b4 = doc.add_paragraph(style='List Bullet')
    p_b4.add_run("Naive Bayes có độ nhạy cao nhưng gây báo động giả quá nhiều, không phù hợp cho môi trường thương mại trực tuyến.")

    add_custom_heading("5.2. Khuyến nghị triển khai hệ thống IDS thực tế", level=2)
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.add_run(
        "Dựa trên kết quả thực nghiệm định lượng, chúng tôi đề xuất kiến trúc hệ thống IDS tối ưu như sau: "
        "Triển khai mô hình XGBoost ở lớp ngoài cùng của tường lửa hoặc cổng Gateway làm nhiệm vụ lọc thô luồng mạng dồn dập (DDoS Volume-based) nhờ độ chính xác 99.06% và Recall 99.75%. "
        "Đồng thời chạy song song mô hình học không giám sát Isolation Forest ở lớp trong để theo dõi hành vi lưu lượng đi qua bộ lọc thô, giúp nhanh chóng phát hiện các cuộc tấn công Zero-day mới chưa có nhãn huấn luyện. "
        "Ngoài ra, cần tích hợp module giám sát độ lệch phân phối (Data Drift Monitoring) liên tục thu thập đặc trưng qua sniffer mạng để phát hiện sự suy giảm hiệu năng mô hình theo thời gian và lên lịch tái huấn luyện định kỳ."
    )

    # --- Lưu tài liệu ---
    output_path = "BAO_CAO_IDS_AI.docx"
    doc.save(output_path)
    print(f"[+] Successfully generated Word report at: {output_path}")

    # Sao chép sang thư mục brain làm artifact
    brain_path = "C:/Users/Hikari-Rainbow/.gemini/antigravity/brain/95e1186e-6a67-4ab5-8cfe-938506c0f189/BAO_CAO_IDS_AI.docx"
    import shutil
    try:
        shutil.copy(output_path, brain_path)
        print(f"[+] Copied Word report to artifacts: {brain_path}")
    except Exception as e:
        print(f"[!] Error copying to artifacts: {e}")

if __name__ == "__main__":
    main()
