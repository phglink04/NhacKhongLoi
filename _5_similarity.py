import numpy as np
from scipy.spatial.distance import cosine

def cosine_similarity(v1, v2):
    """Tính similarity giữa 2 vector (0 đến 1)"""
    v1 = np.array(v1, dtype=np.float32)
    v2 = np.array(v2, dtype=np.float32)
    return 1 - cosine(v1, v2)


def dtw_distance(x, y, max_len=2000):
    """Dynamic Time Warping cho Pitch Contour"""
    x = np.array(x, dtype=np.float32)
    y = np.array(y, dtype=np.float32)
    
    # Giới hạn độ dài để tránh chậm
    if len(x) > max_len:
        x = x[::len(x)//max_len + 1]
    if len(y) > max_len:
        y = y[::len(y)//max_len + 1]
    
    if len(x) == 0 or len(y) == 0:
        return float('inf')
    
    n, m = len(x), len(y)
    cost = np.full((n+1, m+1), np.inf)
    cost[0, 0] = 0.0
    
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost[i, j] = abs(x[i-1] - y[j-1]) + min(cost[i-1, j], 
                                                     cost[i, j-1], 
                                                     cost[i-1, j-1])
    return cost[n, m]


def compute_melody_similarity(query_features, db_features, query_seq, db_seq):
    """
    Tính độ tương đồng giai điệu tổng hợp
    """
    # 1. Song-level vector similarity
    vec_sim = cosine_similarity(query_features["song_vector"], db_features["song_vector"])
    
    # 2. Pitch Contour similarity (DTW) - quan trọng nhất cho giai điệu
    pitch_dtw = dtw_distance(query_seq["pitch"], db_seq["pitch"])
    pitch_sim = 1 / (1 + pitch_dtw / 100)          # chuyển về thang 0-1
    
    # 3. Kết hợp trọng số
    final_score = 0.65 * pitch_sim + 0.35 * vec_sim
    
    return final_score, pitch_sim, vec_sim