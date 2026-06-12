import os
import sys
import wave
import json
import csv
import numpy as np
import matplotlib.pyplot as plt

# Cấu hình thẩm mỹ phong cách Sleek Dark
plt.style.use('dark_background')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['grid.color'] = '#333333'
plt.rcParams['grid.linestyle'] = '--'

DATASET_DIR = "Dataset_NhacKhongLoi"
SEQUENCE_DIR = "database/sequences"
FEATURES_CSV = "database/audio_features.csv"

def load_wav_waveform(file_name):
    """Đọc dữ liệu sóng âm thô của file wav"""
    path = os.path.join(DATASET_DIR, file_name)
    if not os.path.exists(path):
        return None, None
    
    with wave.open(path, "rb") as wav:
        sample_rate = wav.getframerate()
        n_frames = wav.getnframes()
        frames = wav.readframes(n_frames)
        audio = np.frombuffer(frames, dtype=np.int16)
        # Chuẩn hóa biên độ về [-1, 1]
        audio = audio / (np.max(np.abs(audio)) + 1e-8)
        # Tính thời gian (giây) cho trục X
        duration = n_frames / sample_rate
        time_axis = np.linspace(0, duration, len(audio))
        return time_axis, audio

def load_features(file_name):
    """Tải chuỗi đặc trưng pitch và chroma từ file .npz"""
    npz_name = file_name.replace('.wav', '.npz')
    path = os.path.join(SEQUENCE_DIR, npz_name)
    if not os.path.exists(path):
        return None, None
    
    data = np.load(path)
    return data['pitch'], data['chroma']

def dtw_warping_path(x, y, window=50):
    """Tính toán ma trận khoảng cách DTW và tìm đường đi tối ưu (Warping Path)"""
    n = len(x)
    m = len(y)
    w = max(window, abs(n - m) + 1)
    
    cost = np.full((n+1, m+1), np.inf)
    cost[0, 0] = 0.0
    
    for i in range(1, n+1):
        j_start = max(1, i - w)
        j_end = min(m, i + w)
        for j in range(j_start, j_end + 1):
            diff = abs(x[i-1] - y[j-1])
            cost[i, j] = diff + min(cost[i-1, j], cost[i, j-1], cost[i-1, j-1])
            
    # Backtracking tìm warping path
    path = []
    i, j = n, m
    while i > 0 or j > 0:
        path.append((i-1, j-1))
        if i == 0:
            j -= 1
        elif j == 0:
            i -= 1
        else:
            choices = [cost[i-1, j], cost[i, j-1], cost[i-1, j-1]]
            best = np.argmin(choices)
            if best == 0:
                i -= 1
            elif best == 1:
                j -= 1
            else:
                i -= 1
                j -= 1
    path.reverse()
    return path, cost[1:, 1:]

def find_file_by_index(idx):
    """Tìm file trong database dựa trên số thứ tự (STT) đầu tiên"""
    if not os.path.exists(FEATURES_CSV):
        return None
    
    prefix = f"{idx:03d}_"
    with open(FEATURES_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row[0].startswith(prefix):
                return row[0]
    return None

def main():
    # 1. Chọn 2 file để so sánh
    idx1, idx2 = 1, 2 # Mặc định so sánh bài 1 và bài 2
    if len(sys.argv) >= 3:
        try:
            idx1 = int(sys.argv[1])
            idx2 = int(sys.argv[2])
        except ValueError:
            print("Lỗi: Vui lòng truyền vào số thứ tự bài hát (STT), ví dụ: python visualize_comparison.py 1 2")
            sys.exit(1)
            
    file1 = find_file_by_index(idx1)
    file2 = find_file_by_index(idx2)
    
    if not file1 or not file2:
        # Nếu không tìm thấy bằng index, lấy 2 file đầu tiên trong thư mục dataset
        wav_files = [f for f in os.listdir(DATASET_DIR) if f.endswith('.wav')]
        if len(wav_files) < 2:
            print("Không đủ 2 file nhạc trong CSDL để so sánh!")
            sys.exit(1)
        file1 = wav_files[0] if not file1 else file1
        file2 = wav_files[1] if not file2 else file2
        
    print(f"--- Dang so sanh:\n  1. {file1}\n  2. {file2}\n")
    
    # 2. Load Waveforms
    t1, wave1 = load_wav_waveform(file1)
    t2, wave2 = load_wav_waveform(file2)
    
    # 3. Load Pitch & Chroma
    pitch1, chroma1 = load_features(file1)
    pitch2, chroma2 = load_features(file2)
    
    if pitch1 is None or pitch2 is None:
        print("Lỗi: Không tìm thấy file chuỗi đặc trưng (.npz) tương ứng trong database/sequences/.")
        print("Hãy chắc chắn đã chạy build_database.py trước.")
        sys.exit(1)

    # 4. Tính toán DTW Warping Path
    # Lọc bỏ các giá trị 0 (khoảng lặng) để DTW chính xác hơn
    p1_filtered = np.copy(pitch1)
    p2_filtered = np.copy(pitch2)
    path, cost_matrix = dtw_warping_path(p1_filtered, p2_filtered, window=50)

    # 5. Vẽ đồ thị
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle(f"SO SÁNH ĐẶC TRƯNG VÀ ĐỘ TƯƠNG ĐỒNG ÂM THANH\n(1) {file1}  vs  (2) {file2}", fontsize=14, color='#66ccff', weight='bold')

    # Plot 1: Waveforms (Dạng sóng)
    ax1 = plt.subplot(3, 2, 1)
    if t1 is not None:
        ax1.plot(t1, wave1, color='#ff6666', alpha=0.7, label=f"Bài {idx1}")
    if t2 is not None:
        ax1.plot(t2, wave2, color='#66ff66', alpha=0.5, label=f"Bài {idx2}")
    ax1.set_title("1. Biên độ sóng âm thô (Waveforms)", color='#ffcc66', weight='bold')
    ax1.set_xlabel("Thời gian (giây)")
    ax1.set_ylabel("Biên độ")
    ax1.grid(True)
    ax1.legend()

    # Plot 2: Pitch Contours (Đường giai điệu Pitch Contour (F0))
    ax2 = plt.subplot(3, 2, 2)
    ax2.plot(pitch1, color='#ff6666', label=f"Bài {idx1} Pitch", linewidth=1.5)
    ax2.plot(pitch2, color='#66ff66', label=f"Bài {idx2} Pitch", linewidth=1.5, alpha=0.8)
    ax2.set_title("2. Đường giai điệu Pitch Contour (F0)", color='#ffcc66', weight='bold')
    ax2.set_xlabel("Chỉ số Khung hình (Frame Index)")
    ax2.set_ylabel("Tần số (Hz)")
    ax2.grid(True)
    ax2.legend()

    # Plot 3: Chroma Note Distribution (Phân bổ nốt nhạc trung bình)
    ax3 = plt.subplot(3, 2, 3)
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    mean_chroma1 = np.mean(chroma1, axis=0)
    mean_chroma2 = np.mean(chroma2, axis=0)
    x_indices = np.arange(12)
    width = 0.35
    ax3.bar(x_indices - width/2, mean_chroma1, width, label=f"Bài {idx1}", color='#ff6666')
    ax3.bar(x_indices + width/2, mean_chroma2, width, label=f"Bài {idx2}", color='#66ff66')
    ax3.set_title("3. Phân bổ nốt nhạc trung bình (Chroma Profile)", color='#ffcc66', weight='bold')
    ax3.set_xticks(x_indices)
    ax3.set_xticklabels(notes)
    ax3.set_ylabel("Năng lượng trung bình")
    ax3.grid(True, axis='y')
    ax3.legend()

    # Plot 4: DTW Cumulative Cost Matrix & Alignment Path
    ax4 = plt.subplot(3, 2, 4)
    # Vẽ ma trận chi phí dưới dạng ảnh nhiệt (heatmap)
    im = ax4.imshow(cost_matrix.T, origin='lower', cmap='plasma', aspect='auto')
    # Vẽ đường đi tối ưu (Warping Path) màu trắng đè lên
    path_x = [p[0] for p in path]
    path_y = [p[1] for p in path]
    ax4.plot(path_x, path_y, color='#ffffff', linewidth=2.5, label="Warping Path")
    ax4.set_title("4. Căn chỉnh thời gian DTW (Warping Path)", color='#ffcc66', weight='bold')
    ax4.set_xlabel(f"Khung hình Bài {idx1}")
    ax4.set_ylabel(f"Khung hình Bài {idx2}")
    plt.colorbar(im, ax=ax4, label='Chi phí tích lũy')
    ax4.legend()

    # Plot 5: Pitch comparison sau khi đã căn chỉnh bằng DTW
    ax5 = plt.subplot(3, 2, (5, 6))
    aligned_p1 = [pitch1[p[0]] for p in path]
    aligned_p2 = [pitch2[p[1]] for p in path]
    ax5.plot(aligned_p1, color='#ff6666', label=f"Bài {idx1} (Đã căn chỉnh)", linewidth=1.5)
    ax5.plot(aligned_p2, color='#66ff66', label=f"Bài {idx2} (Đã căn chỉnh)", linewidth=1.5, alpha=0.8)
    ax5.set_title("5. So sánh cao độ (Pitch) sau khi uốn khớp thời gian bằng DTW", color='#ffcc66', weight='bold')
    ax5.set_xlabel("Trục thời gian ảo đã căn chỉnh (DTW Aligned Axis)")
    ax5.set_ylabel("Tần số (Hz)")
    ax5.grid(True)
    ax5.legend()

    plt.tight_layout()
    print("--- Dang khoi chay cua so do thi truc quan...")
    plt.show()

if __name__ == "__main__":
    main()
