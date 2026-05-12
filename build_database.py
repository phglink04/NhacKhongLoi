import os
import csv
import numpy as np
from tqdm import tqdm  # Optional: thanh tiến trình

# Import các module đã sửa
from _1_preprocess import preprocess_audio
from _2_stft import compute_stft
from _3_feature_extraction import extract_features
from _4_normalize import compute_min_max, normalize_vector


def build_database(dataset_path="Dataset_NhacKhongLoi", 
                   output_dir="database"):
    """
    Xây dựng database đặc trưng âm nhạc
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/sequences", exist_ok=True)

    all_song_vectors = []
    file_names = []
    processed_count = 0
    error_count = 0

    print("🚀 Bắt đầu xây dựng database...")
    print(f"Thư mục dataset: {dataset_path}\n")

    # Lấy danh sách file wav
    audio_files = [f for f in os.listdir(dataset_path) if f.lower().endswith(".wav")]
    
    for file_name in tqdm(audio_files, desc="Đang xử lý"):
        try:
            file_path = os.path.join(dataset_path, file_name)
            
            # ==================== 1. Preprocess ====================
            windowed_frames, sample_rate = preprocess_audio(file_path)
            
            if len(windowed_frames) == 0:
                print(f"⚠️  File rỗng: {file_name}")
                continue

            # ==================== 2. Compute STFT ====================
            stft_result = compute_stft(windowed_frames)

            # ==================== 3. Extract Features ====================
            features_dict = extract_features(windowed_frames, stft_result, sample_rate)

            # Lưu song-level vector
            all_song_vectors.append(features_dict["song_vector"])
            file_names.append(file_name)

            # Lưu sequence features (pitch + chroma)
            seq_path = os.path.join(output_dir, "sequences", file_name.replace(".wav", ".npz"))
            np.savez_compressed(seq_path,
                                pitch=features_dict["pitch_contour"],
                                chroma=features_dict["chroma_sequence"])

            processed_count += 1

        except Exception as e:
            print(f"❌ Lỗi khi xử lý {file_name}: {e}")
            error_count += 1
            continue

    if processed_count == 0:
        print("❌ Không có file nào được xử lý!")
        return

    # ==================== 4. Normalize ====================
    feature_matrix = np.array(all_song_vectors)
    min_vals, max_vals = compute_min_max(feature_matrix)

    normalized_features = []
    for vec in feature_matrix:
        norm_vec = normalize_vector(vec, min_vals, max_vals)
        normalized_features.append(norm_vec)

    # ==================== 5. Lưu CSV (Song-level features) ====================
    csv_path = os.path.join(output_dir, "audio_features.csv")
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Header
        header = ["file_name", "rms_mean", "rms_std", "zcr_mean", "zcr_std", 
                  "pitch_mean", "pitch_std"] + [f"chroma_{i}" for i in range(12)]
        writer.writerow(header)
        
        # Data
        for name, norm_vec in zip(file_names, normalized_features):
            writer.writerow([name] + norm_vec)

    # ==================== 6. Lưu thông số normalize ====================
    norm_params_path = os.path.join(output_dir, "normalization.csv")
    with open(norm_params_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["feature", "min", "max"])
        
        feature_names = ["rms_mean", "rms_std", "zcr_mean", "zcr_std", 
                        "pitch_mean", "pitch_std"] + [f"chroma_{i}" for i in range(12)]
        
        for name, minv, maxv in zip(feature_names, min_vals, max_vals):
            writer.writerow([name, minv, maxv])

    # ==================== Kết quả ====================
    print("\n" + "="*60)
    print("✅ XÂY DỰNG DATABASE HOÀN TẤT!")
    print("="*60)
    print(f"✅ Số bài hát thành công : {processed_count}/{len(audio_files)}")
    print(f"❌ Lỗi                  : {error_count}")
    print(f"📁 Database folder      : {output_dir}/")
    print(f"   • music_features.csv     (song-level features)")
    print(f"   • normalization.csv      (min-max values)")
    print(f"   • sequences/             (pitch & chroma từng frame)")
    print(f"📊 Feature dimension    : {feature_matrix.shape[1]}")
    print("="*60)


if __name__ == "__main__":
    build_database()