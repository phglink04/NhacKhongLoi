import os
import csv
import json
import time
import numpy as np
from flask import Flask, render_template, request, jsonify

from _1_preprocess import preprocess_audio
from _2_stft import compute_stft
from _3_feature_extraction import extract_features
from _4_normalize import normalize_vector
from _5_similarity import compute_melody_similarity

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==================== LOAD DATABASE (1 lần khi khởi động) ====================

print("Loading database...")

# Normalization params
min_vals, max_vals = [], []
with open("database/normalization.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        min_vals.append(float(row[1]))
        max_vals.append(float(row[2]))
min_vals = np.array(min_vals)
max_vals = np.array(max_vals)

# Cluster data
cluster_centroids = np.load("database/cluster_centroids.npy")
with open("database/cluster_index.json", "r", encoding="utf-8") as f:
    cluster_index = json.load(f)

# All features
db_features = {}
with open("database/audio_features.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        db_features[row[0]] = list(map(float, row[1:]))

total_songs = len(db_features)
print(f"Database loaded: {total_songs} songs, {len(cluster_centroids)} clusters")


# ==================== SEARCH LOGIC ====================

def find_nearest_clusters(query_vector, centroids, n_clusters=3):
    distances = []
    for i in range(len(centroids)):
        dist = np.sqrt(np.sum((np.array(query_vector) - centroids[i]) ** 2))
        distances.append((str(i), dist))
    distances.sort(key=lambda x: x[1])
    return distances[:n_clusters]


def do_search(file_path, top_k=10, n_clusters=3):
    """Thực hiện tìm kiếm và trả về kết quả dạng dict"""
    t_start = time.time()

    # 1. Trích xuất đặc trưng
    frames, sample_rate = preprocess_audio(file_path)
    stft_result = compute_stft(frames)
    query_dict = extract_features(frames, stft_result, sample_rate)
    query_vector = normalize_vector(query_dict["song_vector"], min_vals, max_vals)
    query_seq = {
        "pitch": query_dict["pitch_contour"],
        "chroma": query_dict["chroma_sequence"]
    }

    # 2. Tìm cụm gần nhất
    nearest = find_nearest_clusters(query_vector, cluster_centroids, n_clusters)
    songs_to_search = sum(len(cluster_index[cid]) for cid, _ in nearest)

    # 3. So sánh trong các cụm đã chọn
    results = []
    for cluster_id, _ in nearest:
        for file_name in cluster_index[cluster_id]:
            db_vector = db_features[file_name]
            seq_path = f"database/sequences/{file_name.replace('.wav', '.npz')}"
            
            if os.path.exists(seq_path):
                db_seq_data = np.load(seq_path)
                db_seq = {"pitch": db_seq_data['pitch'], "chroma": db_seq_data['chroma']}
            else:
                db_seq = None

            score, pitch_sim, vec_sim = compute_melody_similarity(
                query_dict, {"song_vector": db_vector}, query_seq, db_seq
            )
            
            # Tạo tên hiển thị từ file name
            display_name = file_name.replace('.wav', '').split('_', 1)
            song_id = display_name[0]
            song_title = display_name[1] if len(display_name) > 1 else display_name[0]
            # Thêm khoảng trắng trước chữ hoa (CamelCase -> readable)
            import re
            readable_title = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', song_title)

            results.append({
                "rank": 0,
                "file_name": file_name,
                "song_id": song_id,
                "title": readable_title,
                "score": round(score * 100, 2),
                "pitch_sim": round(pitch_sim * 100, 2),
                "vec_sim": round(vec_sim * 100, 2),
                "cluster": int(cluster_id)
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:top_k]
    for i, r in enumerate(results):
        r["rank"] = i + 1

    elapsed = round(time.time() - t_start, 2)

    return {
        "results": results,
        "stats": {
            "total_songs": total_songs,
            "songs_searched": songs_to_search,
            "clusters_used": n_clusters,
            "time_seconds": elapsed,
            "savings_percent": round((1 - songs_to_search / total_songs) * 100, 1)
        }
    }


# ==================== ROUTES ====================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    if "audio" not in request.files:
        return jsonify({"error": "Không có file audio"}), 400

    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "Chưa chọn file"}), 400

    top_k = int(request.form.get("top_k", 10))
    n_clusters = int(request.form.get("n_clusters", 3))

    # Lưu file tạm
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        result = do_search(filepath, top_k=top_k, n_clusters=n_clusters)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Xóa file tạm
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
