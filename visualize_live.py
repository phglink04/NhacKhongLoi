import os
import sys
import wave
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# winsound chỉ chạy trên hệ điều hành Windows để phát âm thanh không đồng bộ (asynchronous)
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# Cấu hình thẩm mỹ phong cách Sleek Dark
plt.style.use('dark_background')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10

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
            print("Loi: Vui long truyen vao so thu tu bai hat (STT), vi du: python visualize_live.py 1")
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
    print(f"--- Dang doc file: {file_name}")

    # 2. Đọc thông số file WAV
    with wave.open(file_path, "rb") as wav:
        sample_rate = wav.getframerate()
        n_frames = wav.getnframes()
        channels = wav.getnchannels()
        frames = wav.readframes(n_frames)
        audio_data = np.frombuffer(frames, dtype=np.int16)
        
        # Nếu là stereo, gộp về mono
        if channels == 2:
            audio_data = audio_data.reshape(-1, 2).mean(axis=1)
            
        # Chuẩn hóa về dải [-1, 1]
        audio_data = audio_data / (np.max(np.abs(audio_data)) + 1e-8)

    duration = n_frames / sample_rate
    print(f"--- Thong so: Sample Rate={sample_rate}Hz, Thoi luong={duration:.2f}s")

    # 3. Chuẩn bị phân khung (Framing)
    frame_size = 2048
    hop_length = 512
    # Tính toán khoảng thời gian giữa các khung (khoảng 23.2ms ở tần số 22050Hz)
    interval_ms = int(round((hop_length / sample_rate) * 1000))
    
    # Tạo danh sách các điểm bắt đầu của khung
    frame_starts = list(range(0, len(audio_data) - frame_size, hop_length))
    total_frames = len(frame_starts)

    # 4. Tạo giao diện Matplotlib
    fig = plt.figure(figsize=(12, 8))
    fig.suptitle(f"BO TRUC QUAN HOA LIVE AM THANH (MIEN THOI GIAN & TAN SO)\nFile: {file_name}", fontsize=14, color='#66ccff', weight='bold')

    # Subplot 1: Sóng âm toàn bài và thanh trỏ vị trí trượt
    ax1 = plt.subplot(3, 1, 1)
    time_axis = np.linspace(0, duration, len(audio_data))
    # Vẽ dạng sóng nén (downsampled để vẽ nhanh)
    decimate_factor = max(1, len(audio_data) // 5000)
    ax1.plot(time_axis[::decimate_factor], audio_data[::decimate_factor], color='#444444', alpha=0.8, linewidth=0.5)
    ax1.set_title("1. Dang song toan bo bai hat (Waveform)", color='#ffcc66', weight='bold')
    ax1.set_ylabel("Bien do")
    ax1.set_xlim(0, duration)
    # Đường thẳng đứng màu đỏ chỉ vị trí thời gian hiện tại
    time_cursor = ax1.axvline(x=0, color='#ff3333', linewidth=2, label="Vi tri hien tai")
    ax1.legend(loc="upper right")
    ax1.grid(True, color='#222222')

    # Subplot 2: Khung sóng âm hiện tại (Miền Thời Gian)
    ax2 = plt.subplot(3, 2, 3)
    frame_time_axis = np.linspace(0, (frame_size / sample_rate) * 1000, frame_size)
    line_time, = ax2.plot(frame_time_axis, np.zeros(frame_size), color='#ff6666', linewidth=1.5)
    ax2.set_title("2. Khung tin hieu hien tai (Time Domain)", color='#ffcc66', weight='bold')
    ax2.set_xlabel("Thoi gian khung (ms)")
    ax2.set_ylabel("Bien do")
    ax2.set_ylim(-1.1, 1.1)
    ax2.grid(True, color='#222222')

    # Subplot 3: Phổ tần số FFT của khung hiện tại (Miền Tần Số)
    ax3 = plt.subplot(3, 2, 4)
    # Tính trục tần số cho rfft
    freq_axis = np.fft.rfftfreq(frame_size, d=1/sample_rate)
    line_freq, = ax3.plot(freq_axis, np.zeros(len(freq_axis)), color='#66ff66', linewidth=1.5)
    ax3.set_title("3. Pho tan so FFT hien tai (Frequency Domain)", color='#ffcc66', weight='bold')
    ax3.set_xlabel("Tan so (Hz)")
    ax3.set_ylabel("Nang luong (Magnitude)")
    ax3.set_xlim(0, 4000) # Hầu hết năng lượng nhạc nằm dưới 4kHz
    ax3.set_ylim(0, 30)   # Giới hạn biên độ hiển thị
    ax3.grid(True, color='#222222')

    plt.tight_layout()

    import time
    start_time = [None]  # Dùng list để ghi nhận thời điểm bắt đầu vẽ trong hàm nested

    # 5. Hàm cập nhật hoạt ảnh (Animation Update)
    def update(frame_idx):
        if start_time[0] is None:
            start_time[0] = time.time()
            
        # Tính thời gian thực trôi qua kể từ khi hoạt ảnh bắt đầu
        elapsed = time.time() - start_time[0]
        
        # Quy đổi thời gian trôi qua ra chỉ số khung hình tương ứng
        real_frame_idx = int(elapsed * sample_rate / hop_length)
        
        # Nếu đã đi hết bài hát thì dừng hoạt ảnh
        if real_frame_idx >= total_frames:
            real_frame_idx = total_frames - 1
            
        start_idx = frame_starts[real_frame_idx]
        current_time = start_idx / sample_rate
        
        # Cập nhật vị trí con trỏ thời gian trên sóng âm toàn bài
        time_cursor.set_xdata([current_time, current_time])
        
        # Lấy dữ liệu của khung hiện tại
        frame_data = audio_data[start_idx : start_idx + frame_size]
        
        # Nhân cửa sổ Hamming để giống với giải thuật STFT của hệ thống
        windowed_frame = frame_data * np.hamming(frame_size)
        
        # Cập nhật biểu đồ miền thời gian
        line_time.set_ydata(windowed_frame)
        
        # Tính toán FFT nhanh để chuyển sang miền tần số
        fft_result = np.fft.rfft(windowed_frame)
        magnitude = np.abs(fft_result)
        
        # Cập nhật biểu đồ miền tần số
        line_freq.set_ydata(magnitude)
        
        return time_cursor, line_time, line_freq

    # 6. Phát âm thanh không đồng bộ (Asynchronous Playback) trên Windows
    if HAS_WINSOUND:
        print("--- Dang phat am thanh song song...")
        # Sử dụng cờ SND_ASYNC để phát nhạc nền mà không chặn luồng vẽ đồ thị
        winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        print("--- Canh bao: Khong ho tro winsound tren he dieu hanh nay. Chi hien thi animation.")

    # 7. Khởi chạy Animation với interval cực nhỏ (15ms)
    # Cơ chế Time-based sync sẽ tự động nhảy cóc (skip frames) nếu rendering bị chậm
    ani = FuncAnimation(
        fig, 
        update, 
        frames=total_frames, 
        interval=15, 
        blit=True, 
        repeat=False
    )

    print("--- Dang khoi chay cua so hoat anh truc quan...")
    plt.show()
    
    # Sau khi đóng cửa sổ Matplotlib, tắt âm thanh phát nền
    if HAS_WINSOUND:
        winsound.PlaySound(None, winsound.SND_PURGE)

if __name__ == "__main__":
    main()
