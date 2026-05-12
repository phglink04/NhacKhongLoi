import math


# ============================================================================
# 1. RMS (Root Mean Square) - Năng lượng tín hiệu
# ============================================================================
def compute_rms(frame):
    """
    Tính RMS (năng lượng) của một frame tín hiệu
    Args:
        frame: mảng các giá trị âm thanh
    Returns:
        float: giá trị RMS
    """
    if len(frame) == 0:
        return 0.0
    
    sum_squared = 0.0
    for sample in frame:
        sum_squared += sample * sample
    
    mean_squared = sum_squared / len(frame)
    rms = math.sqrt(mean_squared)
    return rms


def extract_rms_sequence(frames):
    """
    Trích xuất RMS cho toàn bộ chuỗi frames
    
    Args:
        frames: danh sách các frame
    
    Returns:
        list: danh sách giá trị RMS
    """
    rms_values = []
    for frame in frames:
        rms = compute_rms(frame)
        rms_values.append(rms)
    return rms_values


# ============================================================================
# 2. ZCR (Zero Crossing Rate) - Tỷ lệ vượt qua không
# ============================================================================
def compute_zcr(frame):
    """
    Tính ZCR (số lần tín hiệu vượt qua 0) của một frame
    
    Args:
        frame: mảng các giá trị âm thanh
    
    Returns:
        float: ZCR (giá trị từ 0 đến 1)
    """
    if len(frame) < 2:
        return 0.0
    
    zero_crossing_count = 0
    for i in range(len(frame) - 1):
        # Kiểm tra nếu dấu thay đổi (vượt qua 0)
        if (frame[i] >= 0 and frame[i + 1] < 0) or (frame[i] < 0 and frame[i + 1] >= 0):
            zero_crossing_count += 1
    
    zcr = zero_crossing_count / (len(frame) - 1)
    return zcr


def extract_zcr_sequence(frames):
    """
    Trích xuất ZCR cho toàn bộ chuỗi frames
    
    Args:
        frames: danh sách các frame
    
    Returns:
        list: danh sách giá trị ZCR
    """
    zcr_values = []
    for frame in frames:
        zcr = compute_zcr(frame)
        zcr_values.append(zcr)
    return zcr_values


# ============================================================================
# 3. Pitch Contour - Tần số cơ bản (Fundamental Frequency)
# ============================================================================
def find_fundamental_frequency(magnitude_spectrum, sample_rate=22050, fft_size=2048):
    """
    Tìm tần số cơ bản (F0) từ phổ tần số
    Sử dụng phương pháp tìm peak trong phổ (autocorrelation đơn giản)
    
    Args:
        magnitude_spectrum: phổ tần số (từ FFT)
        sample_rate: tần số lấy mẫu
        fft_size: kích thước FFT
    
    Returns:
        float: Fundamental Frequency (Hz)
    """
    if len(magnitude_spectrum) == 0:
        return 0.0
    
    # Xác định phạm vi tìm kiếm (80 Hz - 400 Hz cho âm nói)
    min_freq = 80
    max_freq = 400
    
    freq_resolution = sample_rate / fft_size
    min_bin = max(1, int(min_freq / freq_resolution))
    max_bin = min(len(magnitude_spectrum) - 1, int(max_freq / freq_resolution))
    
    # Tìm bin có magnitude lớn nhất trong phạm vi
    max_magnitude = 0.0
    max_bin_idx = min_bin
    
    for k in range(min_bin, max_bin + 1):
        if magnitude_spectrum[k] > max_magnitude:
            max_magnitude = magnitude_spectrum[k]
            max_bin_idx = k
    
    # Chuyển đổi bin index thành tần số
    fundamental_freq = max_bin_idx * freq_resolution
    
    return fundamental_freq


def extract_pitch_contour(stft_result, sample_rate=22050, fft_size=2048):
    """
    Trích xuất Pitch Contour (Fundamental Frequency) cho toàn bộ chuỗi STFT
    
    Args:
        stft_result: mảng phổ (từ STFT)
        sample_rate: tần số lấy mẫu
        fft_size: kích thước FFT
    
    Returns:
        list: danh sách giá trị Fundamental Frequency
    """
    pitch_values = []
    for spectrum in stft_result:
        f0 = find_fundamental_frequency(spectrum, sample_rate, fft_size)
        pitch_values.append(f0)
    return pitch_values


# ============================================================================
# 4. Chroma Features - Năng lượng theo pitch classes (12 nốt nhạc)
# ============================================================================
def compute_chroma(magnitude_spectrum, sample_rate=22050, fft_size=2048):
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


def extract_chroma_sequence(stft_result, sample_rate=22050, fft_size=2048):
    """
    Trích xuất Chroma features cho toàn bộ chuỗi STFT
    
    Args:
        stft_result: mảng phổ (từ STFT)
        sample_rate: tần số lấy mẫu
        fft_size: kích thước FFT
    
    Returns:
        list: danh sách chroma vectors
    """
    chroma_sequence = []
    for spectrum in stft_result:
        chroma = compute_chroma(spectrum, sample_rate, fft_size)
        chroma_sequence.append(chroma)
    return chroma_sequence


# ============================================================================
# 5. Hàm tính Mean và Std (độ lệch chuẩn)
# ============================================================================
def calculate_mean(values):
    """
    Tính trung bình (mean)
    
    Args:
        values: danh sách các giá trị
    
    Returns:
        float: giá trị mean
    """
    if len(values) == 0:
        return 0.0
    return sum(values) / len(values)


def calculate_std(values):
    """
    Tính độ lệch chuẩn (standard deviation)
    
    Args:
        values: danh sách các giá trị
    
    Returns:
        float: giá trị std
    """
    if len(values) == 0:
        return 0.0
    
    mean = calculate_mean(values)
    variance = 0.0
    
    for val in values:
        variance += (val - mean) ** 2
    
    variance /= len(values)
    std = math.sqrt(variance)
    return std


def calculate_mean_std_for_sequence(feature_sequence):
    """
    Tính mean và std cho một chuỗi đặc trưng
    
    Args:
        feature_sequence: danh sách các giá trị hoặc danh sách các vector
    
    Returns:
        tuple: (mean, std)
    """
    mean = calculate_mean(feature_sequence)
    std = calculate_std(feature_sequence)
    return mean, std


def calculate_mean_std_for_chroma(chroma_sequence):
    """
    Tính mean và std cho mỗi chroma bin riêng biệt
    
    Args:
        chroma_sequence: danh sách các chroma vectors (mỗi vector có 12 giá trị)
    
    Returns:
        tuple: (mean_vector, std_vector) mỗi cái có 12 giá trị
    """
    if len(chroma_sequence) == 0:
        return [0.0] * 12, [0.0] * 12
    
    num_chroma = len(chroma_sequence[0])
    
    # Tính mean cho mỗi chroma bin
    mean_vector = []
    for chroma_idx in range(num_chroma):
        values = [chroma[chroma_idx] for chroma in chroma_sequence]
        mean = calculate_mean(values)
        mean_vector.append(mean)
    
    # Tính std cho mỗi chroma bin
    std_vector = []
    for chroma_idx in range(num_chroma):
        values = [chroma[chroma_idx] for chroma in chroma_sequence]
        std = calculate_std(values)
        std_vector.append(std)
    
    return mean_vector, std_vector


# ============================================================================
# 6. Hàm chính - Trích xuất đặc trưng RMS, ZCR, Pitch, Chroma + Mean/Std
# ============================================================================
def extract_main_features(audio_frames, stft_result, sample_rate=22050, fft_size=2048):
    """
    Trích xuất các đặc trưng chính: RMS, ZCR, Pitch Contour, Chroma
    và tính Mean + Std cho mỗi đặc trưng
    
    Args:
        audio_frames: danh sách frame từ audio
        stft_result: mảng phổ (từ STFT)
        sample_rate: tần số lấy mẫu
        fft_size: kích thước FFT
    
    Returns:
        dict: từ điển chứa:
            - 'rms': {'values': list, 'mean': float, 'std': float}
            - 'zcr': {'values': list, 'mean': float, 'std': float}
            - 'pitch': {'values': list, 'mean': float, 'std': float}
            - 'chroma': {
                'values': list of 12-element vectors,
                'mean': 12-element vector,
                'std': 12-element vector
              }
    """
    # Trích xuất chuỗi đặc trưng
    rms_sequence = extract_rms_sequence(audio_frames)
    zcr_sequence = extract_zcr_sequence(audio_frames)
    pitch_sequence = extract_pitch_contour(stft_result, sample_rate, fft_size)
    chroma_sequence = extract_chroma_sequence(stft_result, sample_rate, fft_size)
    
    # Tính mean và std
    rms_mean, rms_std = calculate_mean_std_for_sequence(rms_sequence)
    zcr_mean, zcr_std = calculate_mean_std_for_sequence(zcr_sequence)
    pitch_mean, pitch_std = calculate_mean_std_for_sequence(pitch_sequence)
    chroma_mean, chroma_std = calculate_mean_std_for_chroma(chroma_sequence)
    
    # Tổng hợp kết quả
    features = {
        'rms': {
            'values': rms_sequence,
            'mean': rms_mean,
            'std': rms_std
        },
        'zcr': {
            'values': zcr_sequence,
            'mean': zcr_mean,
            'std': zcr_std
        },
        'pitch': {
            'values': pitch_sequence,
            'mean': pitch_mean,
            'std': pitch_std
        },
        'chroma': {
            'values': chroma_sequence,
            'mean': chroma_mean,
            'std': chroma_std
        }
    }
    
    return features