import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
import sys

# Đảm bảo import được config từ thư mục gốc
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class IDSPreprocessor:
    def __init__(self, scaler_path=None):
        self.scaler = StandardScaler()
        self.scaler_path = scaler_path or os.path.join(config.MODELS_DIR, "scaler.pkl")
        self.label_mapping = None
        self.reverse_label_mapping = None

    def clean_columns(self, df):
        """Làm sạch tên cột (bỏ khoảng trắng thừa ở đầu/cuối)"""
        df.columns = df.columns.str.strip()
        return df

    def handle_missing_and_inf(self, df):
        """Xử lý các giá trị NaN và Infinite thường gặp ở CICIDS2017"""
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        return df

    def downsize_types(self, df):
        """Tự động ép kiểu dữ liệu số về kiểu nhỏ hơn để tối ưu RAM"""
        df = df.copy()
        for col in df.columns:
            col_type = df[col].dtype
            if col_type != object and not isinstance(col_type, pd.CategoricalDtype):
                c_min = df[col].min()
                c_max = df[col].max()
                if str(col_type).startswith('int'):
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                elif str(col_type).startswith('float'):
                    if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        df[col] = df[col].astype(np.float32)
        return df

    def fit_transform(self, df, label_column='Label'):
        """Tiền xử lý toàn diện cho tập train"""
        df = self.clean_columns(df)
        df = self.handle_missing_and_inf(df)
        
        # Xóa trùng lặp nếu bật cấu hình
        if getattr(config, 'DROP_DUPLICATES', True):
            initial_rows = len(df)
            df = df.drop_duplicates().reset_index(drop=True)
            print(f"[+] Đã loại bỏ {initial_rows - len(df)} dòng dữ liệu trùng lặp. Còn lại {len(df)} dòng.")
        
        # Tách features và labels
        X = df[config.SELECTED_FEATURES].copy()
        y = df[label_column].copy()
        
        # Tối ưu kiểu dữ liệu nếu bật cấu hình
        if getattr(config, 'DOWNSIZE_TYPES', True):
            X = self.downsize_types(X)
            
        # Chuẩn hóa features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=config.SELECTED_FEATURES)
        
        # Encode nhãn (nhãn nhị phân: Benign = 0, Attack = 1 hoặc đa lớp)
        y_binary = y.apply(lambda x: 0 if str(x).strip().lower() in ['benign', '0', 'normal'] else 1)
        
        # Lưu scaler để dùng lại cho realtime capture
        joblib.dump(self.scaler, self.scaler_path)
        print(f"[+] Scaler đã được lưu tại {self.scaler_path}")
        
        return X_scaled, y_binary

    def transform(self, df):
        """Dùng cho tập test hoặc dữ liệu capture thực tế (chỉ transform không fit)"""
        df = self.clean_columns(df)
        df = self.handle_missing_and_inf(df)
        
        # Nếu thiếu một số feature cấu hình, điền 0
        X = pd.DataFrame(index=df.index)
        for col in config.SELECTED_FEATURES:
            if col in df.columns:
                X[col] = df[col]
            else:
                X[col] = 0.0
                
        # Tối ưu kiểu dữ liệu nếu bật cấu hình
        if getattr(config, 'DOWNSIZE_TYPES', True):
            X = self.downsize_types(X)
            
        # Load scaler đã lưu
        if os.path.exists(self.scaler_path):
            self.scaler = joblib.load(self.scaler_path)
        else:
            raise FileNotFoundError(f"Scaler không tìm thấy tại {self.scaler_path}. Vui lòng chạy fit trước.")
            
        X_scaled = self.scaler.transform(X)
        return pd.DataFrame(X_scaled, columns=config.SELECTED_FEATURES)

    def balance_data(self, X, y, strategy='undersample', ratio=1.0):
        """
        Xử lý mất cân bằng dữ liệu.
        Vì tập Benign chiếm số lượng áp đảo, việc giảm mẫu (undersampling) 
        là phương pháp nhanh và nhẹ nhàng nhất cho môi trường bài tập.
        """
        df_temp = pd.concat([X, y], axis=1)
        label_col = y.name
        
        df_benign = df_temp[df_temp[label_col] == 0]
        df_attack = df_temp[df_temp[label_col] == 1]
        
        n_attack = len(df_attack)
        n_benign = len(df_benign)
        
        print(f"[*] Số lượng mẫu trước cân bằng: Benign={n_benign}, Attack={n_attack}")
        
        if strategy == 'undersample' and n_benign > n_attack:
            df_benign_sampled = df_benign.sample(n=int(n_attack * ratio), random_state=42)
            df_balanced = pd.concat([df_benign_sampled, df_attack], axis=0)
        else:
            df_balanced = df_temp
            
        df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
        
        X_balanced = df_balanced[config.SELECTED_FEATURES]
        y_balanced = df_balanced[label_col]
        
        print(f"[+] Số lượng mẫu sau cân bằng: Benign={len(y_balanced[y_balanced==0])}, Attack={len(y_balanced[y_balanced==1])}")
        return X_balanced, y_balanced
