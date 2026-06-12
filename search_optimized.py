import csv
import numpy as np
import os
import json
import time
from _1_preprocess import preprocess_audio
from _2_stft import compute_stft
from _3_feature_extraction import extract_features
from _4_normalize import normalize_vector
from _5_similarity import compute_melody_similarity, cosine_similarity

# 1. Load normalization params
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

# 2. Load cluster data
cluster_centroids = np.load("database/cluster_centroids.npy")

with open("database/cluster_index.json", "r", encoding="utf-8") as f:
    cluster_index = json.load(f)

with open("database/cluster_labels.json", "r", encoding="utf-8") as f:
    cluster_labels = json.load(f)

# 3. Load toàn bộ features vào memory để truy vấn nhanh
db_features = {}  # file_name -> normalized vector
with open("database/audio_features.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        db_features[row[0]] = list(map(float, row[1:]))

# 4. Pre-load toàn bộ sequences vào RAM
db_sequences = {}
for fname in db_features.keys():
    seq_path = f"database/sequences/{fname.replace('.wav', '.npz')}"
    if os.path.exists(seq_path):
        data = np.load(seq_path)
        db_sequences[fname] = {"pitch": data['pitch'], "chroma": data['chroma']}
    else:
        db_sequences[fname] = None


def find_nearest_clusters(query_vector, centroids, n_clusters=3):
    """
    Tìm n_clusters cụm có centroid gần nhất với query vector
    
    Returns:
        List[(cluster_id, distance)] sắp xếp theo khoảng cách tăng dần
    """
    distances = []
    for i in range(len(centroids)):
        dist = np.sqrt(np.sum((np.array(query_vector) - centroids[i]) ** 2))
        distances.append((str(i), dist))
    
    distances.sort(key=lambda x: x[1])
    return distances[:n_clusters]


def search_with_clustering(query_path="query.wav", top_k=10, n_search_clusters=3):
    """
    Tìm kiếm bài hát tương tự sử dụng CLUSTERING để tối ưu query
    
    Thay vì so sánh với toàn bộ 507 bài, chỉ so sánh với các bài
    trong n_search_clusters cụm gần nhất.
    
    Parameters:
        query_path: đường dẫn file WAV cần tìm
        top_k: số kết quả trả về
        n_search_clusters: số cụm gần nhất sẽ tìm kiếm (mặc định 3)
    """
    print(f"🔍 TÌM KIẾM VỚI PHÂN CỤM (Cluster-based Search)")
    print(f"{'='*70}")
    print(f"📂 Query file: {query_path}")
    print(f"🔢 Số cụm tìm kiếm: {n_search_clusters}/{len(cluster_centroids)}")
    print()
    
    # ==================== 1. Xử lý query ====================
    t_start = time.time()
    
    print("⏳ Bước 1: Trích xuất đặc trưng query...")
    frames, sample_rate = preprocess_audio(query_path)
    stft_result = compute_stft(frames)
    query_dict = extract_features(frames, stft_result, sample_rate)
    query_vector = normalize_vector(query_dict["song_vector"], min_vals, max_vals)
    
    query_seq = {
        "pitch": query_dict["pitch_contour"],
        "chroma": query_dict["chroma_sequence"]
    }
    
    t_extract = time.time()
    print(f"   ✅ Hoàn tất ({t_extract - t_start:.2f}s)")
    
    # ==================== 2. Tìm các cụm gần nhất ====================
    print(f"\n⏳ Bước 2: Tìm {n_search_clusters} cụm gần nhất...")
    nearest_clusters = find_nearest_clusters(query_vector, cluster_centroids, n_search_clusters)
    
    total_songs_in_db = sum(len(v) for v in cluster_index.values())
    songs_to_search = sum(len(cluster_index[cid]) for cid, _ in nearest_clusters)
    
    print(f"Các cụm được chọn:")
    for cid, dist in nearest_clusters:
        n_songs = len(cluster_index[cid])
        print(f"Cụm {cid}: {n_songs} bài hát (khoảng cách: {dist:.4f})")
    
    print(f"\nTìm kiếm trong {songs_to_search}/{total_songs_in_db} bài hát "
          f"({songs_to_search/total_songs_in_db*100:.1f}% database)")
    
    # ==================== 3. So sánh chỉ trong các cụm đã chọn ====================
    print(f"\nBước 3: Tính similarity trong các cụm đã chọn...")
    t_search_start = time.time()
    
    results = []
    compared_count = 0
    
    for cluster_id, _ in nearest_clusters:
        for file_name in cluster_index[cluster_id]:
            db_vector = db_features[file_name]
            db_seq = db_sequences.get(file_name)
            
            # Tính similarity
            score, pitch_sim, vec_sim = compute_melody_similarity(
                query_dict, {"song_vector": db_vector}, query_seq, db_seq
            )
            
            results.append({
                "file_name": file_name,
                "score": score,
                "pitch_sim": pitch_sim,
                "vector_sim": vec_sim,
                "cluster": int(cluster_id)
            })
            compared_count += 1
    
    t_search_end = time.time()
    print(f"So sánh {compared_count} bài hát ({t_search_end - t_search_start:.2f}s)")
    
    # ==================== 4. Sắp xếp và in kết quả ====================
    results.sort(key=lambda x: x["score"], reverse=True)
    
    t_total = time.time() - t_start
    
    print(f"\n{'='*80}")
    print(f"TOP {top_k} BÀI HÁT CÓ GIAI ĐIỆU GIỐNG NHẤT (Cluster-based)")
    print(f"{'='*80}")
    print(f"{'STT':<5} {'Tên bài hát':<45} {'Score':<10} {'Pitch':<10} {'Cụm':<6}")
    print(f"{'-'*80}")
    
    for i in range(min(top_k, len(results))):
        item = results[i]
        print(f"{i+1:2d}.  {item['file_name']:45} "
              f"{item['score']*100:6.2f}%   "
              f"{item['pitch_sim']*100:5.1f}%   "
              f"C{item['cluster']}")
    
    print(f"{'-'*80}")
    print(f"\nTHỐNG KÊ HIỆU SUẤT:")
    print(f"   • Thời gian trích xuất query : {t_extract - t_start:.2f}s")
    print(f"   • Thời gian tìm kiếm         : {t_search_end - t_search_start:.2f}s")
    print(f"   • Tổng thời gian             : {t_total:.2f}s")
    print(f"   • Số bài so sánh             : {compared_count}/{total_songs_in_db} "
          f"(tiết kiệm {(1 - compared_count/total_songs_in_db)*100:.1f}%)")
    print(f"{'='*80}")
    
    return results




# ==================== MAIN ====================

if __name__ == "__main__":
    query = "D:\\study_document\\ky2nam4\\CSDLDPT\\csdldpt\\Dataset_Test\\002_NangAmXaDan.wav"
    print(f"Tìm kiếm file: {query}")    
    search_with_clustering(query_path=query, top_k=5, n_search_clusters=3)
