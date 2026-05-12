# Music Audio Feature Extraction and Similarity Search

## Mô tả dự án

Dự án này thực hiện trích xuất các đặc trưng âm thanh từ các bài hát nhạc dân gian và xây dựng một hệ thống tìm kiếm các bài hát tương tự dựa trên các đặc trưng này.

## Chức năng chính

- **Thu thập và xử lý dữ liệu âm thanh**: Tải xuống và cắt các tệp âm thanh từ các liên kết
- **Tiền xử lý âm thanh**: Chuẩn hóa và xử lý tín hiệu âm thanh
- **Trích xuất đặc trưng**: Sử dụng STFT (Short-Time Fourier Transform) để trích xuất đặc trưng âm thanh
- **Chuẩn hóa**: Chuẩn hóa các đặc trưng để so sánh
- **Tìm kiếm tương tự**: Tìm các bài hát có đặc trưng tương tự dựa trên độ đo khoảng cách

## Cấu trúc dự án

```
.
├── _0_crawl_and_cut_data_v2.py    # Script thu thập dữ liệu (phiên bản 2)
├── _0_crawl_and_cut_data.py       # Script thu thập dữ liệu (phiên bản 1)
├── _1_preprocess.py               # Tiền xử lý tín hiệu âm thanh
├── _2_stft.py                     # Tính toán STFT
├── _3_feature_extraction.py       # Trích xuất đặc trưng
├── _4_normalize.py                # Chuẩn hóa đặc trưng
├── _5_similarity.py               # Tính toán độ tương tự
├── build_database.py              # Xây dựng cơ sở dữ liệu
├── search.py                      # Tìm kiếm các bài hát tương tự
├── test.py                        # File kiểm thử
├── database/                      # Thư mục cơ sở dữ liệu
│   ├── audio_features.csv         # Bảng đặc trưng âm thanh
│   ├── normalization.csv          # Tham số chuẩn hóa
│   └── sequences/                 # Các file dữ liệu định dạng .npz
└── CrawlData_Timestamps/          # Dữ liệu timestamps từ quá trình thu thập
```

## Yêu cầu

- Python 3.7+
- NumPy
- SciPy
- Librosa
- Pandas
- Các thư viện khác (xem chi tiết trong requirements.txt nếu có)

## Hướng dẫn sử dụng

### 1. Thu thập và xử lý dữ liệu

```bash
python _0_crawl_and_cut_data_v2.py
```

### 2. Tiền xử lý âm thanh

```bash
python _1_preprocess.py
```

### 3. Tính toán STFT

```bash
python _2_stft.py
```

### 4. Trích xuất đặc trưng

```bash
python _3_feature_extraction.py
```

### 5. Chuẩn hóa đặc trưng

```bash
python _4_normalize.py
```

### 6. Tính toán độ tương tự

```bash
python _5_similarity.py
```

### 7. Xây dựng cơ sở dữ liệu

```bash
python build_database.py
```

### 8. Tìm kiếm các bài hát tương tự

```bash
python search.py
```

## Cấu trúc dữ liệu

### audio_features.csv
Bảng chứa các đặc trưng âm thanh được trích xuất từ các bài hát, bao gồm:
- ID bài hát
- Các đặc trưng số từ STFT (biên độ, tần số, v.v.)

### normalization.csv
Bảng chứa các tham số chuẩn hóa (min, max, trung bình, độ lệch chuẩn) cho mỗi đặc trưng

### sequences/
Thư mục chứa các file dữ liệu nhị phân (.npz) cho mỗi bài hát, được đặt tên theo ID:
- `001_GapMeTrongMo.npz` - Bài hát "Gặp Me Trong Mơ"
- `002_NhatKyCuaMe.npz` - Bài hát "Nhật Ký Của Me"
- ... và các bài hát khác

## Mô tả các file script

| File | Mô tả |
|------|-------|
| `_0_crawl_and_cut_data_v2.py` | Thu thập dữ liệu âm thanh từ các URL và cắt thành các đoạn |
| `_1_preprocess.py` | Tiền xử lý: chuẩn hóa biên độ, loại bỏ tiếng ồn, v.v. |
| `_2_stft.py` | Tính toán biến đổi Fourier thời gian ngắn từ dữ liệu âm thanh |
| `_3_feature_extraction.py` | Trích xuất các đặc trưng từ STFT (Mel-frequency, v.v.) |
| `_4_normalize.py` | Chuẩn hóa các đặc trưng về cùng một khoảng giá trị |
| `_5_similarity.py` | Tính toán độ đo tương tự giữa các bài hát |
| `build_database.py` | Tích hợp tất cả các bước vào một cơ sở dữ liệu |
| `search.py` | Giao diện tìm kiếm để tìm các bài hát tương tự |
| `test.py` | Các test case để xác minh chức năng |

## Cách hoạt động

1. **Chuỗi xử lý dữ liệu**: Dữ liệu âm thanh → Tiền xử lý → STFT → Trích xuất đặc trưng → Chuẩn hóa
2. **Lưu trữ**: Các đặc trưng được lưu trong CSV và dữ liệu định dạng NumPy
3. **Tìm kiếm**: Khi tìm kiếm, hệ thống so sánh các đặc trưng của bài hát truy vấn với tất cả các bài hát trong cơ sở dữ liệu

## Kết quả

Hệ thống trả về danh sách các bài hát được sắp xếp theo độ tương tự (từ cao nhất đến thấp nhất)

## Ghi chú

- Cơ sở dữ liệu hiện tại chứa 50+ bài hát nhạc dân gian Việt Nam
- Có thể mở rộng để thêm các bài hát hoặc loại nhạc khác
- Chất lượng kết quả phụ thuộc vào chất lượng dữ liệu đầu vào và các tham số trích xuất đặc trưng

## Tác giả

[Thêm thông tin tác giả nếu cần]

## Giấy phép

[Thêm thông tin giấy phép nếu cần]
