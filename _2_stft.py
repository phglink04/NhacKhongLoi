import numpy as np


def compute_stft(windowed_frames):
    stft_result = []
 
    for frame in windowed_frames:
        fft_result = np.fft.fft(frame)
        magnitude = np.abs(fft_result)
        stft_result.append(magnitude)

    stft_result = np.array(stft_result)
    stft_result = stft_result[:, :1024]

    return stft_result