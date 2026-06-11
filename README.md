# Hệ Thống Tìm Kiếm Nhạc Tương Tự — Tối Ưu Bằng Phân Cụm K-Means

## Mô tả

Hệ thống trích xuất đặc trưng âm thanh từ các bài hát và tìm kiếm bài hát có giai điệu tương tự. Sử dụng thuật toán **K-Means (K=10)** để phân cụm cơ sở dữ liệu 506 bài, giúp tối ưu truy vấn bằng cách chỉ duyệt các cụm gần nhất thay vì toàn bộ database.

---

## Cấu trúc dự án

```
csdldpt/
├── _0_crawl_and_cut_data_v2.py    # Thu thập & cắt dữ liệu âm thanh
├── _1_preprocess.py               # Tiền xử lý tín hiệu
├── _2_stft.py                     # Biến đổi Fourier (STFT)
├── _3_feature_extraction.py       # Trích xuất đặc trưng (18 chiều)
├── _4_normalize.py                # Chuẩn hóa Min-Max
├── _5_similarity.py               # Tính độ tương tự (Cosine + DTW)
├── _6_clustering.py               # Phân cụm K-Means (K=10)
├── build_database.py              # Xây dựng toàn bộ database
├── search_optimized.py            # Tìm kiếm tối ưu (cluster-based)
├── app.py                         # Web server (Flask)
├── templates/index.html           # Giao diện web
├── database/                      # Cơ sở dữ liệu (tự sinh)
├── Dataset_NhacKhongLoi/          # File .wav gốc
└── Dataset_Test/                  # File .wav test
```

---

## Cài đặt

```bash
pip install numpy scipy flask tqdm
```

---

## Hướng dẫn chạy

### Bước 1 — Xây dựng Database (chạy 1 lần)

**Nếu đã có thư mục `database/` với đầy đủ dữ liệu**, chỉ cần chạy phân cụm:

```bash
python _6_clustering.py
```

**Nếu chưa có database** (xây từ đầu):

```bash
python build_database.py
```

> `build_database.py` tự động chạy toàn bộ pipeline và phân cụm.

### Bước 2 — Tìm kiếm

**Giao diện Web:**

```bash
python app.py
```

Mở trình duyệt: **http://127.0.0.1:5000** → Upload file `.wav` → Nhấn Tìm kiếm.

**Dòng lệnh:**

```bash
python search_optimized.py
```

---

## Quy trình xử lý

```
File .wav → Tiền xử lý → STFT → Trích xuất đặc trưng (18D) → Chuẩn hóa → Lưu DB
                                                                              ↓
                                                                     K-Means (K=10)
                                                                              ↓
Query .wav → Trích xuất đặc trưng → Tìm cụm gần nhất → So sánh trong cụm → Kết quả
```

---

## Đặc trưng âm thanh (18 chiều)

| Đặc trưng      | Số chiều | Mô tả                           |
|----------------|----------|----------------------------------|
| RMS Energy     | 2        | Năng lượng trung bình & độ lệch |
| ZCR            | 2        | Tần suất tín hiệu đổi dấu      |
| Pitch          | 2        | Cao độ trung bình & độ lệch     |
| Chroma         | 12       | Phân bố năng lượng 12 nốt nhạc  |

---

## Thuật toán phân cụm & tìm kiếm

**Phân cụm (offline — chạy 1 lần):**
- K-Means++ khởi tạo centroid → Lặp gán cụm + cập nhật centroid → Hội tụ
- 506 bài hát → 10 cụm (29–79 bài/cụm)

**Tìm kiếm (online — mỗi lần query):**
1. Trích xuất đặc trưng file query
2. Tính khoảng cách Euclid từ query đến 10 centroid → Chọn 3 cụm gần nhất
3. So sánh query với các bài trong 3 cụm đó (Cosine Similarity + DTW Pitch)
4. Trả về top-K bài có score cao nhất

**Công thức score:** `score = 0.65 × pitch_similarity + 0.35 × vector_similarity`

---

## Mô tả file

| File | Vai trò |
|------|---------|
| `_1_preprocess.py` | Đọc WAV → Mono → Normalize → Trim → Pre-emphasis → Framing → Hamming |
| `_2_stft.py` | FFT từng frame → Log magnitude spectrum |
| `_3_feature_extraction.py` | Trích xuất RMS, ZCR, Pitch, Chroma → Vector 18 chiều |
| `_4_normalize.py` | Chuẩn hóa Min-Max về [0, 1] |
| `_5_similarity.py` | Cosine Similarity + Dynamic Time Warping (Pitch) |
| `_6_clustering.py` | K-Means++ phân 506 bài → 10 cụm |
| `build_database.py` | Gọi toàn bộ pipeline _1 → _6 |
| `search_optimized.py` | Tìm kiếm cluster-based qua dòng lệnh |
| `app.py` | Flask web server + giao diện upload |
