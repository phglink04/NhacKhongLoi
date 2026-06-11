# HƯỚNG DẪN KỸ THUẬT VÀ QUY TRÌNH VẬN HÀNH HỆ THỐNG

Tài liệu này giải thích chi tiết cơ chế hoạt động, các đặc trưng kỹ thuật, phương pháp so sánh âm thanh, vai trò của việc phân cụm, và cấu trúc đầu vào/đầu ra kèm theo tham chiếu dòng code thực tế trong file `app.py`.

---

## 1. Tại Sao Lựa Chọn Định Dạng WAV?

Hệ thống sử dụng định dạng **WAV (Waveform Audio File Format)** làm chuẩn xử lý trung gian vì các lý do kỹ thuật sau:
* **Không nén và bảo toàn dữ liệu gốc (Lossless & Uncompressed)**: Tệp WAV lưu trữ âm thanh thô dưới dạng PCM. Các định dạng nén có mất mát (như MP3, M4A) triệt tiêu bớt các dải tần số để giảm dung lượng, điều này làm sai lệch phổ âm thanh và ảnh hưởng trực tiếp đến độ chính xác khi phân tích tần số ngắn hạn (STFT) hay trích xuất đặc trưng.
* **Dễ dàng đọc thành mảng số (NumPy Array)**: File WAV biểu diễn biên độ sóng âm theo thời gian một cách trực tiếp. Các thư viện Python (như `librosa`, `scipy.io.wavfile`) có thể nạp trực tiếp dữ liệu này thành mảng số thực để tính toán mà không cần bộ giải mã phức tạp.
* **Đồng nhất thông số kỹ thuật (Standardization)**: File WAV giúp dễ dàng ép cấu hình về tần số lấy mẫu `22050 Hz`, kênh đơn (`mono`), và dải biên độ $[-1, 1]$ trước khi phân tích.

---

## 2. Cách So Sánh Hai File Âm Thanh

Hệ thống kết hợp **2 phương pháp đo khoảng cách toán học** để tính toán độ tương đồng giữa bài hát truy vấn (Query) và bài hát trong cơ sở dữ liệu (CSDL):

```
Độ tương đồng cuối cùng = 65% Giai điệu (DTW) + 35% Cấu trúc chung (Cosine)
```

1. **Độ tương đồng cấu trúc (Cosine Similarity - Trọng số 35%)**:
   * So sánh hai vector đặc trưng cố định 18 chiều của hai bài hát (bao gồm thông tin trung bình về năng lượng, độ to nhỏ, độ nhiễu và hợp âm Chroma).
   * Đo góc giữa hai vector trong không gian 18 chiều. Trả về giá trị trong dải $[0, 1]$.
2. **Độ tương đồng giai điệu (Dynamic Time Warping - DTW - Trọng số 65%)**:
   * So sánh chuỗi biến thiên cao độ theo thời gian (`pitch_contour`).
   * DTW tự động "co dãn" trục thời gian để căn chỉnh các nốt nhạc trùng khớp nhau, giúp nhận diện chính xác kể cả khi người dùng hát nhanh hoặc chậm hơn bản gốc.
   * Khoảng cách DTW được chuẩn hóa về điểm tương đồng giai điệu theo công thức:
     $$\text{pitch\_sim} = \frac{1}{1 + \frac{\text{dtw\_distance}}{100}}$$

---

## 3. Tại Sao Phải Chuẩn Hóa Đặc Trưng?

Hệ thống sử dụng phương pháp **Chuẩn hóa Min-Max (Min-Max Normalization)** để đưa toàn bộ 18 chiều đặc trưng về cùng một khoảng giá trị $[0, 1]$:

* **Tránh hiện tượng chiếm ưu thế (Scale Domination)**: Các đặc trưng có khoảng giá trị tự nhiên khác xa nhau. Ví dụ, cao độ (Pitch) dao động từ $60$ đến $2000$ Hz, trong khi năng lượng (RMS) hay Chroma chỉ dao động trong khoảng $0$ đến $1$. Nếu không chuẩn hóa, sự chênh lệch lớn của Pitch sẽ lấn át hoàn toàn các đặc trưng còn lại, khiến hệ thống chỉ so sánh cao độ mà bỏ qua nhịp điệu và hợp âm.
* **Đảm bảo tính chính xác cho K-Means**: Thuật toán phân cụm K-Means tính khoảng cách Euclid giữa các điểm dữ liệu. Nếu không chuẩn hóa, không gian hình học sẽ bị méo mó theo trục có biên độ lớn, khiến kết quả phân cụm sai lệch.

---

## 4. Vai Trò Của Phân Cụm K-Means (`_6_clustering.py`)

Thuật toán phân cụm **K-Means (với K=10)** được sử dụng như một **bộ chỉ mục tối ưu hóa tốc độ tìm kiếm**:

* **Giai đoạn xây dựng Database (`build_database.py`)**: Gom nhóm toàn bộ bài hát trong CSDL thành 10 nhóm dựa trên vector đặc trưng và sinh ra các file chỉ mục:
  * `cluster_centroids.npy`: Tọa độ 10 tâm cụm.
  * `cluster_index.json`: Bản đồ ánh xạ `ID Cụm -> [Danh sách tên các file nhạc thuộc cụm]`.
* **Giai đoạn Tìm kiếm (`app.py` / `search_optimized.py`)**: 
  * Khi nhận file query, hệ thống tính khoảng cách từ file query tới 10 tâm cụm để tìm ra **3 cụm gần nhất**.
  * Hệ thống chỉ thực hiện chạy so sánh chi tiết (DTW và Cosine) với các bài hát thuộc 3 cụm này thay vì toàn bộ CSDL.
  * Việc này giúp tiết kiệm tới **70% số lượng phép tính DTW**, tăng tốc độ phản hồi đáng kể.

---

## 5. Quy Trình Vận Hành Và Vị Trí Dòng Code Trong `app.py`

### 5.1. Tải CSDL Vào RAM Khi Khởi Động
Để phản hồi tức thời, toàn bộ dữ liệu chỉ mục và đặc trưng được nạp vào bộ nhớ trước khi server Flask lắng nghe:
* **Dòng 24 - 38**: Tải các giá trị Min-Max chuẩn hóa, tâm cụm K-Means và chỉ mục cụm.
* **Dòng 41 - 58**: Nạp toàn bộ các vector đặc trưng cố định và chuỗi giai điệu (`.npz` chứa pitch & chroma) của tất cả bài hát vào RAM.

### 5.2. Đầu Vào (Input)
Khi người dùng tải file lên từ giao diện, server Flask tiếp nhận thông qua API POST `/search`:
* **Dòng 150 - 153**: Tiếp nhận file âm thanh đầu vào từ client.
* **Dòng 157 - 158**: Đọc các tham số cấu hình tìm kiếm (`top_k`, `n_clusters`).
* **Dòng 160 - 163**: Lưu file tạm thời vào thư mục `uploads/` để xử lý.

### 5.3. Quy Trình So Sánh Với CSDL (Hàm `do_search()`)
Hàm `do_search` tại **dòng 74** thực hiện toàn bộ logic so sánh:
1. **Trích xuất đặc trưng của file Query (Dòng 79 - 86)**:
   ```python
   frames, sample_rate = preprocess_audio(file_path)
   stft_result = compute_stft(frames)
   query_dict = extract_features(frames, stft_result, sample_rate)
   query_vector = normalize_vector(query_dict["song_vector"], min_vals, max_vals)
   query_seq = {
       "pitch": query_dict["pitch_contour"],
       "chroma": query_dict["chroma_sequence"]
   }
   ```
2. **Lọc tìm cụm gần nhất (Dòng 89 - 90)**:
   ```python
   nearest = find_nearest_clusters(query_vector, cluster_centroids, n_clusters)
   songs_to_search = sum(len(cluster_index[cid]) for cid, _ in nearest)
   ```
3. **So sánh chi tiết trong các cụm đã lọc (Dòng 94 - 101)**:
   ```python
   for cluster_id, _ in nearest:
       for file_name in cluster_index[cluster_id]:
           db_vector = db_features[file_name]
           db_seq = db_sequences.get(file_name)

           score, pitch_sim, vec_sim = compute_melody_similarity(
               query_dict, {"song_vector": db_vector}, query_seq, db_seq
           )
   ```

### 5.4. Kết Quả Đầu Ra (Output)
Hệ thống gom tất cả kết quả, sắp xếp theo độ tương đồng giảm dần, lọc lấy số lượng bài hát yêu cầu (`top_k`) và trả về dạng JSON:
* **Dòng 111 - 120**: Khởi tạo cấu trúc kết quả cho từng bài hát (bao gồm thứ hạng, tên hiển thị đẹp, điểm tương đồng giai điệu/cấu trúc/tổng hợp và thông tin cụm).
* **Dòng 122 - 123**: Sắp xếp kết quả giảm dần và lấy ra `top_k` phần tử.
* **Dòng 129 - 138**: Đóng gói danh sách kết quả kèm các thông số thống kê hiệu suất tìm kiếm:
  ```python
  return {
      "results": results,
      "stats": {
          "total_songs": total_songs,        # Tổng số bài hát gốc
          "songs_searched": songs_to_search,   # Số bài thực tế đã so sánh
          "clusters_used": n_clusters,       # Số cụm đã kiểm tra
          "time_seconds": elapsed,           # Thời gian thực hiện (giây)
          "savings_percent": round((1 - songs_to_search / total_songs) * 100, 1) # % Tiết kiệm tài nguyên
      }
  }
  ```
* **Dòng 169**: Gửi trả kết quả dạng JSON về cho trình duyệt hiển thị.
