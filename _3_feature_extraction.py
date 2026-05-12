import numpy as np
import math

# ==================== CÁC HÀM ĐẶC TRƯNG ====================
def rms_energy(frame):
    if len(frame) == 0: 
        return 0.0
    return np.sqrt(np.mean(frame ** 2))


def zero_crossing_rate(frame):
    if len(frame) < 2:
        return 0.0
    count = np.sum(np.diff(np.sign(frame)) != 0)
    return count / (len(frame) - 1)


def pitch_contour(magnitude, sample_rate):
    """Sửa lỗi freqs"""
    N = 2 * (len(magnitude) - 1)                    # Độ dài gốc của frame
    freqs = np.fft.rfftfreq(N, d=1/sample_rate)
    peak_index = np.argmax(magnitude)
    pitch = freqs[peak_index]
    return pitch if 60 <= pitch <= 2000 else 0.0


def chroma_features(magnitude, sample_rate, fft_size=2048):
    """Chroma 12 chiều"""
    chroma = np.zeros(12)
    freqs = np.fft.rfftfreq(fft_size, d=1/sample_rate)[:len(magnitude)]
    
    for k, mag in enumerate(magnitude):
        freq = freqs[k]
        if freq < 20:
            continue
        # Tính pitch class
        pitch_class = int(round(12 * np.log2(freq / 440.0) + 69)) % 12
        chroma[pitch_class] += mag
    
    total = np.sum(chroma)
    if total > 0:
        chroma = chroma / total
    return chroma


# ==================== TRÍCH XUẤT TẤT CẢ ====================

def extract_features(frames, stft_result, sample_rate):
    rms_list = []
    zcr_list = []
    pitch_list = []
    chroma_list = []
    
    for i in range(len(frames)):
        frame = frames[i]
        magnitude = stft_result[i]
        
        rms_list.append(rms_energy(frame))
        zcr_list.append(zero_crossing_rate(frame))
        pitch_list.append(pitch_contour(magnitude, sample_rate))
        chroma_list.append(chroma_features(magnitude, sample_rate))
    
    # Tạo feature vector
    chroma_mean = np.mean(chroma_list, axis=0)   # 12 chiều
    
    song_features = [
        np.mean(rms_list), np.std(rms_list),
        np.mean(zcr_list), np.std(zcr_list),
        np.mean(pitch_list), np.std(pitch_list),
    ] + list(chroma_mean)                        # Thêm 12 chroma
    
    pitch_contour_array = np.array(pitch_list)
    chroma_sequence = np.array(chroma_list)   # shape = (n_frames, 12)
    
    return {
        "song_vector": np.array(song_features),      # vector cố định
        "pitch_contour": pitch_contour_array,        # dùng cho DTW
        "chroma_sequence": chroma_sequence           # dùng cho DTW chroma
    }