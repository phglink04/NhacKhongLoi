import numpy as np

# RMS- năn lượng trung bình của tín hiệu âm thanh
def rms_energy(frame):
    if len(frame) == 0: return 0.0
    return np.sqrt(np.mean(frame ** 2))

# Zero Crossing Rate - tốc độ thay đổi dấu của tín hiệu âm thanh
def zero_crossing_rate(frame):

    zero_crossing_count = 0
    for i in range(len(frame) - 1):
        # Kiểm tra nếu dấu thay đổi (vượt qua 0)
        if (frame[i] >= 0 and frame[i + 1] < 0) or (frame[i] < 0 and frame[i + 1] >= 0):
            zero_crossing_count += 1
    
    zcr = zero_crossing_count / (len(frame) - 1)
    return zcr

# extract Pitch contour
def pitch_contour(magnitude, sample_rate):
    freqs = np.fft.rfftfreq(len(magnitude) * 2 - 1, d=1/sample_rate)
    peak_index = np.argmax(magnitude)
    pitch_freq = freqs[peak_index]
    return pitch_freq

# extract chroma
def chroma_features(magnitude, sample_rate):
    """
    Tính Chroma features - năng lượng ở mỗi pitch class
    
    Args:
        magnitude_spectrum: phổ tần số
        sample_rate: tần số lấy mẫu
        fft_size: kích thước FFT
    
    Returns:
        list: 12 chroma features (cho 12 semitones)
    """
    # Khởi tạo chroma
    chroma = [0.0] * 12
    
    # Ánh xạ mỗi bin FFT đến chroma pitch class
    for k in range(len(magnitude_spectrum)):
        freq = k * sample_rate / fft_size
        
        if freq < 20:  # Bỏ qua tần số quá thấp
            continue
        
        # Tính semitone từ một tần số tham chiếu (C0 = 16.35 Hz)
        C0_Hz = 16.35
        semitone = 12 * math.log2(freq / C0_Hz)
        
        # Chuyển đổi sang pitch class (0-11)
        pitch_class = int(round(semitone)) % 12
        
        # Thêm năng lượng vào pitch class này
        chroma[pitch_class] += magnitude_spectrum[k]
    
    # Chuẩn hóa
    total_energy = sum(chroma)
    if total_energy > 0:
        chroma = [c / total_energy for c in chroma]
    
    return chroma

# Main Feature Extraction Function
def extract_features( frames, stft_result,sample_rate ):
    rms_list = []
    zcr_list = []
    pitch_counter = []
    chroma = []
    for i in range(len(frames)):
        frame = frames[i]
        magnitude = stft_result[i]
        # RMS
        rms = rms_energy(frame)
        rms_list.append(rms)
      
        # ZCR
        zcr = zero_crossing_rate(frame)
        zcr_list.append(zcr)
      
        # Pitch_contour
        pitch = pitch_contour(magnitude, sample_rate)
        pitch_counter.append(pitch)

        # Chroma
        chroma_features = chroma_features(magnitude, sample_rate)
        chroma.append(chroma_features)

    feature_vector = [
        np.mean(rms_list),
        np.std(rms_list),
        np.mean(zcr_list),
        np.std(zcr_list),
        np.mean(pitch_counter),
        np.std(pitch_counter),
        np.mean(chroma, axis=0)
    ]
    

    return feature_vector