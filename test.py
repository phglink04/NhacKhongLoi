import numpy as np

# Duong dan toi file .npz thuc te
file_path = r"database/sequences/001_GapMeTrongMo.npz"

# Nap file .npz
with np.load(file_path) as data:
    # 1. Liet ke cac mang du lieu (.files)
    print("=== DATA ARRAYS IN FILE ===")
    print(data.files) 
    
    # 2. Xem mang Pitch
    pitch_data = data['pitch']
    print("\n=== PITCH DATA ===")
    print(f"Shape: {pitch_data.shape}")
    print(f"Dtype: {pitch_data.dtype}")
    print(f"First 10 values: {pitch_data[:10]}")
    
    # 3. Xem ma tran Chroma
    chroma_data = data['chroma']
    print("\n=== CHROMA DATA ===")
    print(f"Shape: {chroma_data.shape}")
    print(f"Dtype: {chroma_data.dtype}")
    print(f"First frame chroma values:\n{chroma_data[0]}")
