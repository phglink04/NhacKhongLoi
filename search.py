import csv
import numpy as np
import os
from _1_preprocess import preprocess_audio
from _2_stft import compute_stft
from _3_feature_extraction import extract_features
from _4_normalize import normalize_vector
from _5_similarity import compute_melody_similarity, cosine_similarity

# ==================== LOAD NORMALIZATION PARAMS ====================
min_vals = []
max_vals = []
with open("database/normalization.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        min_vals.append(float(row[1]))
        max_vals.append(float(row[2]))

min_vals = np.array(min_vals)
max_vals = np.array(max_vals)


def search_similar_songs(query_path="query.wav", top_k=10):
    print(f"🔍 Đang phân tích file query: {query_path}\n")
    
    # Xử lý query
    frames, sample_rate = preprocess_audio(query_path)
    stft_result = compute_stft(frames)
    query_dict = extract_features(frames, stft_result, sample_rate)
    
    query_vector = normalize_vector(query_dict["song_vector"], min_vals, max_vals)
    
    # Load query sequence
    query_seq = {
        "pitch": query_dict["pitch_contour"],
        "chroma": query_dict["chroma_sequence"]
    }

    results = []
    
    print("Đang so sánh với database...\n")
    
    with open("database/audio_features.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        
        for row in reader:
            file_name = row[0]
            db_vector = list(map(float, row[1:]))
            
            # Load sequence của bài hát trong database
            seq_path = f"database/sequences/{file_name.replace('.wav', '.npz')}"
            if os.path.exists(seq_path):
                db_seq_data = np.load(seq_path)
                db_seq = {"pitch": db_seq_data['pitch'], "chroma": db_seq_data['chroma']}
            else:
                db_seq = None
            
            # Tính similarity
            score, pitch_sim, vec_sim = compute_melody_similarity(
                query_dict, {"song_vector": db_vector}, query_seq, db_seq
            )
            
            results.append({
                "file_name": file_name,
                "score": score,
                "pitch_sim": pitch_sim,
                "vector_sim": vec_sim
            })

    # Sắp xếp theo độ tương đồng giảm dần
    results.sort(key=lambda x: x["score"], reverse=True)

    # In kết quả
    print("="*80)
    print(f"TOP {top_k} BÀI HÁT CÓ GIAI ĐIỆU GIỐNG NHẤT")
    print("="*80)
    
    for i in range(min(top_k, len(results))):
        item = results[i]
        print(f"{i+1:2d}. {item['file_name']:45} → {item['score']*100:6.2f}%  "
              f"(Pitch: {item['pitch_sim']*100:5.1f}%)")

    return results


if __name__ == "__main__":
    search_similar_songs(query_path="D:\\study_document\\ky2nam4\\CSDLDPT\\csdldpt\\Dataset_Test\\002_NangAmXaDan.wav", top_k=5)
