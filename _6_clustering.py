import numpy as np
import csv
import os
import json


# ==================== K-MEANS CLUSTERING====================

def kmeans_init_centroids(data, k, seed=42):
    """Khởi tạo centroid bằng K-Means++ để có kết quả tốt hơn random"""
    np.random.seed(seed)
    n_samples = data.shape[0]
    
    # Chọn centroid đầu tiên ngẫu nhiên
    first_idx = np.random.randint(0, n_samples)
    centroids = [data[first_idx]]
    
    for _ in range(1, k):
        # Tính khoảng cách từ mỗi điểm đến centroid gần nhất
        distances = np.array([
            min(np.sum((x - c) ** 2) for c in centroids)
            for x in data
        ])
        # Xác suất chọn tỷ lệ với khoảng cách bình phương
        probs = distances / distances.sum()
        next_idx = np.random.choice(n_samples, p=probs)
        centroids.append(data[next_idx])
    
    return np.array(centroids)


def kmeans_assign_clusters(data, centroids):
    """Gán mỗi điểm dữ liệu vào cluster có centroid gần nhất"""
    # Tính khoảng cách Euclid từ mỗi điểm đến tất cả centroids
    # data: (n, d), centroids: (k, d)
    distances = np.sqrt(((data[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2).sum(axis=2))
    labels = np.argmin(distances, axis=1)
    return labels, distances


def kmeans_update_centroids(data, labels, k):
    """Cập nhật centroids = trung bình các điểm trong cluster"""
    new_centroids = np.zeros((k, data.shape[1]))
    for i in range(k):
        cluster_points = data[labels == i]
        if len(cluster_points) > 0:
            new_centroids[i] = cluster_points.mean(axis=0)
    return new_centroids


def kmeans(data, k=10, max_iters=100, tol=1e-6, seed=42):
    """
    Thuật toán K-Means clustering
    
    Parameters:
        data: numpy array (n_samples, n_features) - dữ liệu đã normalize
        k: int - số cụm
        max_iters: int - số vòng lặp tối đa
        tol: float - ngưỡng hội tụ
        seed: int - random seed
    
    Returns:
        labels: numpy array - nhãn cluster cho mỗi điểm
        centroids: numpy array - tâm các cluster
        inertia: float - tổng khoảng cách bình phương đến centroid
    """
    print(f"🔄 Đang chạy K-Means với K={k}...")
    
    # Khởi tạo centroids bằng K-Means++
    centroids = kmeans_init_centroids(data, k, seed)
    
    for iteration in range(max_iters):
        # Bước 1: Gán cluster
        labels, distances = kmeans_assign_clusters(data, centroids)
        
        # Bước 2: Cập nhật centroids
        new_centroids = kmeans_update_centroids(data, labels, k)
        
        # Kiểm tra hội tụ
        shift = np.sqrt(((new_centroids - centroids) ** 2).sum())
        centroids = new_centroids
        
        if shift < tol:
            print(f"   ✅ Hội tụ sau {iteration + 1} vòng lặp (shift={shift:.8f})")
            break
    else:
        print(f"   ⚠️  Đạt giới hạn {max_iters} vòng lặp (shift={shift:.8f})")
    
    # Tính inertia (tổng khoảng cách bình phương)
    inertia = sum(
        np.sum((data[labels == i] - centroids[i]) ** 2)
        for i in range(k)
    )
    
    return labels, centroids, inertia


# ==================== XÂY DỰNG VÀ LƯU CLUSTER INDEX ====================

def build_cluster_index(k=10, db_dir="database"):
    """
    Đọc audio_features.csv, chạy K-Means, lưu kết quả clustering
    
    Output files:
        - database/cluster_centroids.npy   : tâm các cluster (k, n_features)
        - database/cluster_index.json      : mapping cluster_id -> [file_names]
        - database/cluster_labels.json     : mapping file_name -> cluster_id
    """
    # ==================== 1. Load dữ liệu từ CSV ====================
    file_names = []
    feature_vectors = []
    
    csv_path = os.path.join(db_dir, "audio_features.csv")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # skip header
        for row in reader:
            file_names.append(row[0])
            feature_vectors.append(list(map(float, row[1:])))
    
    data = np.array(feature_vectors, dtype=np.float64)
    print(f"📊 Loaded {len(file_names)} bài hát, {data.shape[1]} features")
    
    # ==================== 2. Chạy K-Means ====================
    labels, centroids, inertia = kmeans(data, k=k)
    
    # ==================== 3. Thống kê các cluster ====================
    cluster_index = {}   # cluster_id -> list[file_name]
    cluster_labels = {}  # file_name -> cluster_id
    
    for i in range(k):
        cluster_files = [file_names[j] for j in range(len(file_names)) if labels[j] == i]
        cluster_index[str(i)] = cluster_files
        for fname in cluster_files:
            cluster_labels[fname] = int(i)
    
    # ==================== 4. In thống kê ====================
    print(f"\n{'='*60}")
    print(f"📊 KẾT QUẢ PHÂN CỤM K-MEANS (K={k})")
    print(f"{'='*60}")
    print(f"{'Cluster':<12} {'Số bài hát':<15} {'Ví dụ'}")
    print(f"{'-'*60}")
    
    for i in range(k):
        files = cluster_index[str(i)]
        examples = ", ".join(files[:3])
        if len(files) > 3:
            examples += f" ... (+{len(files)-3})"
        print(f"  Cụm {i:<6} {len(files):<15} {examples}")
    
    print(f"{'-'*60}")
    print(f"  Tổng cộng: {sum(len(v) for v in cluster_index.values())} bài hát")
    print(f"  Inertia  : {inertia:.4f}")
    print(f"{'='*60}")
    
    # ==================== 5. Lưu kết quả ====================
    # Lưu centroids
    centroids_path = os.path.join(db_dir, "cluster_centroids.npy")
    np.save(centroids_path, centroids)
    print(f"\n💾 Đã lưu centroids    → {centroids_path}")
    
    # Lưu cluster index (cluster_id -> file list)
    index_path = os.path.join(db_dir, "cluster_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(cluster_index, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu cluster index → {index_path}")
    
    # Lưu cluster labels (file -> cluster_id)
    labels_path = os.path.join(db_dir, "cluster_labels.json")
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(cluster_labels, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu cluster labels → {labels_path}")
    
    return labels, centroids, cluster_index


if __name__ == "__main__":
    build_cluster_index(k=10)
