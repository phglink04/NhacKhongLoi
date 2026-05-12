import wave
import numpy as np
import os


def preprocess_audio(file_path):
#   check file wav if not, convert to wav using ffmpeg
    if not file_path.endswith(".wav"):
        temp_path = file_path.rsplit(".", 1)[0] + ".wav"
        cmd = [
            "ffmpeg", "-y", "-i",
            file_path,
            "-ar",  "22050", "-ac", "1",
            temp_path
        ]
        os.system(" ".join(cmd))
        file_path = temp_path
#   1. Load audio file
    wav = wave.open(file_path, "r")
    sample_rate = wav.getframerate()
    n_frames = wav.getnframes()
    n_channels = wav.getnchannels()
    frames = wav.readframes(n_frames) # Đọc dữ liệu nhị phân
    audio = np.frombuffer(frames, dtype=np.int16) # Chuyển binary -> waveform

#   2. Convert to mono if stereo
    if n_channels == 2:
        audio = audio.reshape(-1, 2)
        audio = audio.mean(axis=1)

#   3. Normalize volum to [-1, 1]
    audio = audio / np.max(np.abs(audio))

#   4. Trim silence
    threshold = 0.02
    non_silent = np.where(np.abs(audio) > threshold)[0]
    start = non_silent[0]
    end = non_silent[-1]
    audio = audio[start:end]

#   5. Pre-emphasis
    alpha = 0.97
    emphasized = np.append(audio[0],audio[1:] - alpha * audio[:-1])

#   6. Framing
    frame_size = 2048 # 93ms
    hop_length = 512 # 23ms
    frames = []

    for i in range( 0,len(emphasized) - frame_size,hop_length ):
        frame = emphasized[i:i + frame_size]
        frames.append(frame)

    frames = np.array(frames)

#   7. Hamming Window
    hamming = np.hamming(frame_size)
    windowed_frames = frames * hamming

    return windowed_frames, sample_rate