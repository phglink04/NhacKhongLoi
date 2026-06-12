import os
import sys
import wave
import numpy as np
import matplotlib.pyplot as plt
from _1_preprocess import preprocess_audio
from _2_stft import compute_stft
from _3_feature_extraction import extract_features, rms_energy, zero_crossing_rate

# Cấu hình thẩm mỹ phong cách Sleek Dark
plt.style.use('dark_background')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['grid.color'] = '#333333'
plt.rcParams['grid.linestyle'] = '--'

DATASET_DIR = "Dataset_NhacKhongLoi"
FEATURES_CSV = "database/audio_features.csv"

def find_file_by_index(idx):
    """Tìm file trong database dựa trên số thứ tự (STT) đầu tiên"""
    if not os.path.exists(FEATURES_CSV):
        return None
    
    prefix = f"{idx:03d}_"
    import csv
    with open(FEATURES_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row[0].startswith(prefix):
                return row[0]
    return None

def main():
    # 1. Chọn file nhạc
    idx = 1 # Mặc định chọn bài 1
    if len(sys.argv) >= 2:
        try:
            idx = int(sys.argv[1])
        except ValueError:
            print("Loi: Vui long truyen vao so thu tu bai hat (STT), vi du: python visualize_features.py 1")
            sys.exit(1)
            
    file_name = find_file_by_index(idx)
    if not file_name:
        # Lấy file đầu tiên trong thư mục nếu không tìm thấy index
        wav_files = [f for f in os.listdir(DATASET_DIR) if f.endswith('.wav')]
        if not wav_files:
            print("Khong tim thay file nhac .wav nao trong thu muc Dataset_NhacKhongLoi!")
            sys.exit(1)
        file_name = wav_files[0]

    file_path = os.path.join(DATASET_DIR, file_name)
    print(f"--- Dang trich xuat dac trung cho file: {file_name}")

    # 2. Đọc sóng âm thô để vẽ Waveform gốc
    with wave.open(file_path, "rb") as wav:
        sample_rate = wav.getframerate()
        n_frames = wav.getnframes()
        frames = wav.readframes(n_frames)
        raw_audio = np.frombuffer(frames, dtype=np.int16)
        raw_audio = raw_audio / (np.max(np.abs(raw_audio)) + 1e-8)
        raw_time = np.linspace(0, n_frames / sample_rate, len(raw_audio))

    # 3. Tiền xử lý & Trích xuất đặc trưng
    windowed_frames, sr = preprocess_audio(file_path)
    stft_spectrogram = compute_stft(windowed_frames)
    feature_dict = extract_features(windowed_frames, stft_spectrogram, sr)
    
    # Lấy các chuỗi đặc trưng theo thời gian
    rms = np.array([rms_energy(f) for f in windowed_frames])
    zcr = np.array([zero_crossing_rate(f) for f in windowed_frames])
    pitch = np.array(feature_dict["pitch_contour"])
    chroma = np.array(feature_dict["chroma_sequence"])
    
    # Trục thời gian cho các khung hình
    num_frames = len(rms)
    frame_time = np.linspace(0, (num_frames * 512) / sr, num_frames)

    # 4. Trực quan hóa các đặc trưng
    fig, axs = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f"TRUC QUAN HOA CAC DAC TRUNG AM THANH CHI TIET\nFile: {file_name}", fontsize=14, color='#66ccff', weight='bold')

    # Đồ thị 1: Waveform gốc & RMS Energy (Năng lượng)
    axs[0].plot(raw_time, raw_audio, color='#555555', alpha=0.5, label="Waveform")
    axs[0].plot(frame_time, rms * 3, color='#ff6666', linewidth=2, label="RMS Energy (x3)") # Nhân 3 để nổi bật trên waveform
    axs[0].set_title("1. Song am Waveform & Nang luong RMS Energy", color='#ffcc66', weight='bold')
    axs[0].set_ylabel("Bien do")
    axs[0].legend(loc="upper right")
    axs[0].grid(True)

    # Đồ thị 2: Zero Crossing Rate (ZCR)
    axs[1].plot(frame_time, zcr, color='#66ff66', linewidth=1.5, label="ZCR")
    axs[1].set_title("2. Toc do qua diem 0 (Zero Crossing Rate - ZCR)", color='#ffcc66', weight='bold')
    axs[1].set_ylabel("Ti le ZCR")
    axs[1].grid(True)

    # Đồ thị 3: Pitch Contour (Đường cao độ F0)
    axs[2].plot(frame_time, pitch, color='#ffb366', linewidth=1.5, label="Pitch")
    axs[2].set_title("3. Duong giai dieu Pitch Contour (F0)", color='#ffcc66', weight='bold')
    axs[2].set_ylabel("Tan so (Hz)")
    axs[2].grid(True)

    # Đồ thị 4: Chroma Spectrogram (Bản đồ nốt nhạc theo thời gian)
    # Chroma shape is (num_frames, 12). Cần transpose thành (12, num_frames) để vẽ
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    im = axs[3].imshow(
        chroma.T,
        origin='lower',
        cmap='plasma',
        aspect='auto',
        extent=[0, frame_time[-1], 0, 12]
    )
    axs[3].set_title("4. Ban do hoa am Chroma Spectrogram (12 Pitch Classes)", color='#ffcc66', weight='bold')
    axs[3].set_ylabel("Not nhac")
    axs[3].set_xlabel("Thoi gian (giay)")
    axs[3].set_yticks(np.arange(12) + 0.5)
    axs[3].set_yticklabels(notes)
    
    # Thêm thanh màu cho Chroma
    plt.colorbar(im, ax=axs[3], label='Nang luong', orientation='horizontal', pad=0.15)

    plt.tight_layout()
    print("--- Dang khoi chay cua so do thi dac trung...")
    plt.show()

if __name__ == "__main__":
    main()
