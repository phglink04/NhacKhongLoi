# PHÂN TÍCH CHI TIẾT CÁC ĐỊNH DẠNG DỮ LIỆU TRONG HỆ THỐNG

Tài liệu này cung cấp cái nhìn chi tiết về các loại dữ liệu được sử dụng trong hệ thống tìm kiếm nhạc tương tự, so sánh các điểm giống và khác nhau giữa chúng từ định dạng vật lý, mục đích sử dụng cho đến cấu trúc lưu trữ bên trong.

---

## 1. Bảng Tổng Quan So Sánh Các Định Dạng Dữ Liệu

| Tên File/Thư mục | Định Dạng Vật Lý | Đặc Tính Dữ Liệu | Mục Đích Sử Dụng | Dung Lượng Ước Tính |
| :--- | :--- | :--- | :--- | :--- |
| `Dataset_NhacKhongLoi/` | Thư mục `.wav` | Dữ liệu âm thanh thô (Raw time-series) | Đầu vào gốc để trích xuất đặc trưng và phát nhạc | Rất lớn (~1.3 MB/file) |
| `database/audio_features.csv` | Văn bản `.csv` | Vector tĩnh (Static feature vector) | Phân cụm K-Means & tính Cosine Similarity nhanh | Nhỏ (~180 KB cho cả bộ) |
| `database/normalization.csv` | Văn bản `.csv` | Dữ liệu biên cực tiểu/cực đại (Metadata) | Chuẩn hóa Min-Max dữ liệu truy vấn | Cực nhỏ (< 1 KB) |
| `database/sequences/` | Thư mục `.npz` | Chuỗi đặc trưng động (Dynamic time-series) | So sánh chi tiết giai điệu bằng thuật toán DTW | Trung bình (~15 KB/file) |
| `database/cluster_centroids.npy`| Nhị phân `.npy` | Tâm cụm K-Means (10 tâm cụm 18 chiều) | Lọc nhanh các cụm chứa bài hát gần nhất | Cực nhỏ (~1.5 KB) |
| `database/cluster_index.json` | Văn bản `.json` | Từ điển ánh xạ (Key-value index) | Truy vết nhanh danh sách bài hát thuộc một cụm | Nhỏ (~15 KB) |
| `database/cluster_labels.json` | Văn bản `.json` | Bảng nhãn cụm (Key-value dictionary) | Xác định cụm của từng bài hát trong hệ thống | Nhỏ (~15 KB) |

---

## 2. Phân Tích So Sánh Chi Tiết (Giống & Khác Nhau)

### 2.1. Điểm Giống Nhau
* **Nguồn gốc dữ liệu**: Tất cả các file trong thư mục `database/` đều được phái sinh từ bước trích xuất đặc trưng tín hiệu số (DSP) của các tệp nhạc gốc `.wav` thông qua chạy script `build_database.py`.
* **Mối liên kết định danh**: Các tệp dữ liệu đặc trưng đều dùng chung khóa chính là `file_name` (tên file gốc, ví dụ: `003_HayTraoChoAnh.wav`) để liên kết thông tin xuyên suốt hệ thống từ CSDL, phân cụm cho đến giao diện người dùng.
* **Mục tiêu tối thượng**: Đều phục vụ cho việc tính toán độ tương đồng nhạc lý và tối ưu hóa thời gian chạy truy vấn tìm kiếm của ứng dụng Flask.

### 2.2. Điểm Khác Nhau Cốt Lõi

#### A. Khác biệt về Tính Tĩnh (Static) và Tính Động (Dynamic)
* **Dữ liệu Tĩnh (`audio_features.csv`, `cluster_centroids.npy`)**:
  * Các giá trị biểu diễn các đặc trưng được **tính trung bình trên toàn bộ bài hát**.
  * Kích thước vector cố định (luôn là 18 chiều cho mỗi bài hát), không phụ thuộc vào việc bài hát đó dài 10 giây hay 10 phút.
  * *Tác dụng*: Thích hợp để phân cụm nhanh, lưu trữ gọn nhẹ và so sánh tổng quát.
* **Dữ liệu Động (`sequences/*.npz`)**:
  * Lưu trữ các đặc trưng **theo từng khung thời gian ngắn** (frame-by-frame) của bài hát.
  * Kích thước mảng biến thiên tùy thuộc vào độ dài thời gian của bài hát. Bài hát càng dài thì chuỗi mảng càng có nhiều phần tử.
  * *Tác dụng*: Cần thiết cho thuật toán DTW để so sánh diễn biến giai điệu theo trình tự thời gian.

#### B. Khác biệt về Định Dạng Vật Lý và Cách Truy Cập
* **Định dạng Plain-Text (`.csv`, `.json`)**:
  * Lưu dưới dạng văn bản thông thường, con người có thể mở bằng Notepad hoặc Excel để xem trực tiếp cấu trúc dữ liệu bên trong.
  * Dễ đọc, dễ sửa, nhưng tốc độ phân tích và tải dữ liệu bằng code chậm hơn định dạng nhị phân.
* **Định dạng Nhị phân (`.npy`, `.npz`)**:
  * Dữ liệu được mã hóa nhị phân chuyên dụng của thư viện NumPy.
  * Không thể đọc trực tiếp bằng Notepad thông thường (sẽ hiển thị các ký tự lỗi).
  * *Ưu điểm*: Được nén tối ưu, dung lượng nhỏ và tốc độ tải vào bộ nhớ RAM của Python nhanh gấp hàng chục lần so với file text.

---

## 3. Cấu Trúc Chi Tiết Bên Trong Từng File Dữ Liệu

### 3.1. Dữ liệu âm thanh thô (`.wav`)
* **Kiểu dữ liệu**: Mảng 1 chiều chứa các giá trị biên độ sóng âm tại mỗi điểm lấy mẫu thời gian.
* **Cấu trúc**: Nếu bài hát dài 30 giây với tần số `22050 Hz`, mảng sẽ có kích thước:
  $$\text{Size} = 30 \times 22050 = 661,500 \text{ mẫu số thực (float32)}$$

### 3.2. Bảng Vector Đặc Trưng Tĩnh (`database/audio_features.csv`)
* **Kiểu dữ liệu**: Dạng bảng 2D.
* **Cấu trúc hàng và cột**:
  ```csv
  file_name,rms_mean,rms_std,zcr_mean,zcr_std,pitch_mean,pitch_std,chroma_0,chroma_1,...,chroma_11
  003_HayTraoChoAnh.wav,0.124,0.045,0.081,0.032,342.1,120.4,0.08,0.12,...,0.05
  ```
  * Cột 1: Tên file gốc (dùng làm khóa liên kết).
  * Cột 2-7: Giá trị trung bình và độ lệch chuẩn của RMS Energy, Zero Crossing Rate và Pitch.
  * Cột 8-19: 12 giá trị phân bổ âm của Chroma tương ứng với 12 bán âm của âm giai (C, C#, D, D#,... B).

### 3.3. Chuỗi Đặc Trưng Động (`database/sequences/*.npz`)
* **Kiểu dữ liệu**: File lưu trữ nhị phân nén của NumPy chứa 2 mảng chính:
  1. `pitch` (Mảng 1D): $[p_1, p_2, p_3, ..., p_N]$ ghi lại tần số cơ bản tại mỗi khung hình thứ $i$ ($60 \le p_i \le 2000$).
  2. `chroma` (Ma trận 2D kích thước $N \times 12$): Ghi lại phân bổ âm thanh trên 12 nốt nhạc tại mỗi khung hình.

### 3.4. Chỉ Mục Phân Cụm (`database/cluster_index.json`)
* **Kiểu dữ liệu**: Cấu trúc từ điển JSON.
* **Cấu trúc cấu hình**:
  ```json
  {
    "0": [
      "003_HayTraoChoAnh.wav",
      "005_ThaiBinhMoHoiRoi.wav"
    ],
    "1": [
      "008_ChacAiDoSeVe.wav"
    ],
    ...
  }
  ```
  Giúp hệ thống thực hiện truy vấn lọc theo khối cụm cực nhanh mà không cần lọc tuyến tính toàn bộ bảng CSV.
