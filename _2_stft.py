import numpy as np


def compute_stft(windowed_frames):
    stft_result = []
 
    for frame in windowed_frames:
        fft_result = np.fft.rfft(frame)
        magnitude = np.abs(fft_result)
        stft_result.append(magnitude)

    stft_result = np.array(stft_result)
    stft_result = stft_result[:, :1024]
    stft_log = np.log1p(stft_result)
    return stft_log