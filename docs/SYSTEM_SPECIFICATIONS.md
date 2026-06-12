# Tài Liệu Đặc Tả Chi Tiết Chức Năng Hoạt Động Của Hệ Thống
## Hệ Thống Tìm Kiếm Nhạc Tương Tự Bằng Phân Cụm K-Means

Dự án này là một hệ thống hoàn chỉnh cho phép tìm kiếm bài hát có giai điệu tương tự với một file nhạc đầu vào (Query). Để tối ưu hóa tốc độ tìm kiếm trên cơ sở dữ liệu lớn (506 bài hát trong Dataset), hệ thống sử dụng thuật toán phân cụm **K-Means (K=10)** thủ công cùng phương pháp đo độ tương đồng lai ghép giữa **Euclid/Cosine** trên vector đặc trưng và **Dynamic Time Warping (DTW)** trên đường bao cao độ (pitch contour).

---

## 1. Kiến Trúc Tổng Quan & Luồng Xử Lý Dữ Liệu (Pipeline)

Quy trình xử lý của hệ thống được chia làm hai giai đoạn chính:

```
[ Giai đoạn 1: Offline - Xây dựng Cơ sở dữ liệu ]
File nhạc (.wav) -> Tiền xử lý -> STFT -> Trích xuất đặc trưng (18D + Sequence) -> Chuẩn hóa Min-Max -> K-Means (K=10) -> Lưu DB

[ Giai đoạn 2: Online - Tìm kiếm thời gian thực ]
Query (.wav) -> Trích xuất đặc trưng -> Tìm các Centroid gần nhất -> So sánh với các bài trong Cụm -> Xếp hạng & Phát nhạc
```

---

## 2. Chi Tiết Các Chức Năng & Thành Phần Kỹ Thuật

### 2.1. Tiền Xử Lý Tín Hiệu Âm Thanh (`_1_preprocess.py`)
Mục tiêu là chuẩn hóa các tệp âm thanh đầu vào về một định dạng thống nhất và làm sạch nhiễu/khoảng lặng trước khi phân tích tần số.
1. **Chuyển đổi định dạng**: Nếu file đầu vào không phải dạng `.wav` (ví dụ `.mp3`), hệ thống sử dụng `ffmpeg` để convert tự động sang tần số lấy mẫu `22050 Hz`, kênh đơn (`mono`).
2. **Chuyển kênh (Mono Conversion)**: Gộp các kênh âm thanh stereo (2 kênh) thành mono (1 kênh) bằng cách tính trung bình cộng để giảm một nửa lượng dữ liệu tính toán.
3. **Chuẩn hóa biên độ (Amplitude Normalization)**: Chia toàn bộ dữ liệu biên độ âm thanh cho giá trị biên độ lớn nhất để đưa tín hiệu về dải giới hạn $[-1, 1]$.
4. **Loại bỏ khoảng lặng (Trimming Silence)**: Loại bỏ các đoạn không có âm thanh ở đầu và cuối bài hát dựa trên ngưỡng năng lượng (threshold = `0.02`).
5. **Bộ lọc tiền nhấn (Pre-emphasis)**: Áp dụng bộ lọc sai phân $y[t] = x[t] - \alpha \cdot x[t-1]$ với hệ số $\alpha = 0.97$. Bước này giúp khuếch đại các thành phần tần số cao (thường bị suy giảm khi thu âm).
6. **Chia khung tín hiệu (Framing)**: Chia tín hiệu liên tục thành các khung ngắn xếp chồng lên nhau.
   - Độ dài khung (`frame_size`): `2048` mẫu (~93 ms).
   - Độ dịch khung (`hop_length`): `512` mẫu (~23 ms).
7. **Cửa sổ Hamming (Hamming Window)**: Nhân mỗi khung tín hiệu với cửa sổ Hamming để làm giảm hiện tượng rò rỉ phổ (spectral leakage) ở hai rìa khung trước khi chạy biến đổi Fourier.

---

### 2.2. Biến Đổi Fourier Thời Gian Ngắn (`_2_stft.py`)
Chuyển đổi tín hiệu từ miền thời gian (time-domain) sang miền tần số (frequency-domain).
- Hệ thống áp dụng thuật toán **Real FFT (Fast Fourier Transform)** trên từng khung tín hiệu đã nhân cửa sổ Hamming.
- Biên độ phổ (magnitude spectrum) được trích xuất bằng cách lấy trị tuyệt đối của kết quả FFT.
- Để phù hợp hơn với thang đo cảm nhận âm lượng phi tuyến tính của tai người, hệ thống chuyển đổi phổ biên độ sang thang logarit: $\text{stft\_log} = \ln(1 + \text{magnitude})$.

---

### 2.3. Trích Xuất Đặc Trưng Âm Thanh 18 Chiều (`_3_feature_extraction.py`)
Hệ thống trích xuất hai loại đặc trưng: **Vector đặc trưng tĩnh** (đại diện cho toàn bộ bài hát) và **Chuỗi đặc trưng động** (đại diện cho sự thay đổi theo thời gian).

#### Đặc trưng Song-level tĩnh (18 chiều):
1. **RMS Energy (Năng lượng hiệu dụng - 2 chiều)**: Đo lường độ lớn/cường độ của âm thanh. Trích xuất giá trị **trung bình** (mean) và **độ lệch chuẩn** (std) trên toàn bộ các khung.
2. **Zero Crossing Rate (Tốc độ qua điểm 0 - 2 chiều)**: Đếm số lần tín hiệu đổi dấu. Giúp nhận diện mức độ nhiễu hoặc các âm sắc sắc bén. Trích xuất **trung bình** và **độ lệch chuẩn**.
3. **Pitch Contour (Đường cao độ - 2 chiều)**: Tìm tần số cơ bản (F0) dựa trên đỉnh tần số trong khoảng từ `60 Hz` đến `2000 Hz`. Trích xuất **trung bình** và **độ lệch chuẩn** của tần số cao độ trên toàn bài.
4. **Chroma Features (Đặc trưng màu âm/hòa âm - 12 chiều)**: Phổ tần số được gộp vào 12 bán âm của một quãng tám chuẩn (C, C#, D, D#, E, F, F#, G, G#, A, A#, B). Hệ thống tính toán phân bố năng lượng trung bình trên 12 nốt nhạc này để thể hiện cấu trúc hòa âm của bài hát.

#### Đặc trưng Sequence động (Dành cho so khớp chuỗi thời gian):
- **Chuỗi Pitch**: Lưu lại mảng cao độ của từng khung hình theo thời gian.
- **Chuỗi Chroma**: Lưu lại mảng 12 chiều đặc trưng chroma của từng khung hình theo thời gian.

---

### 2.4. Chuẩn Hóa Min-Max (`_4_normalize.py`)
Do các đặc trưng có đơn vị đo lường khác nhau (ví dụ: Pitch lên tới hàng nghìn Hz, ZCR chỉ dao động dưới 1.0), hệ thống thực hiện chuẩn hóa Min-Max để đưa tất cả 18 chiều đặc trưng về cùng dải $[0, 1]$, tránh việc đặc trưng có giá trị lớn lấn át các đặc trưng khác khi phân cụm.
- Các tham số Min và Max của từng chiều được lưu lại trong file `database/normalization.csv`.

---

### 2.5. Đo Độ Tương Đồng Lai Ghép (`_5_similarity.py`)
Khi so khớp hai bài hát, hệ thống áp dụng công thức lai ghép kết hợp giữa cấu trúc tổng quát và chi tiết thời gian:
1. **Độ tương đồng Vector tĩnh (Cosine Similarity)**:
   - Đo góc giữa hai vector đặc trưng 18 chiều đã chuẩn hóa.
   - Thể hiện sự tương đồng về phong cách, mức độ năng lượng, và màu âm tổng thể của hai bài hát.
2. **Độ tương đồng Giai điệu động (Dynamic Time Warping - DTW)**:
   - So khớp chuỗi thời gian của cao độ (pitch contour) giữa Query và Database.
   - Sử dụng **Sakoe-Chiba Band** (cửa sổ tìm kiếm quanh đường chéo chênh lệch tối đa 50 khung hình) để tối ưu thời gian tính toán và hạn chế các liên kết quá xa.
   - Khoảng cách DTW được chuyển đổi thành độ tương đồng (thang điểm 0 - 1) qua công thức:
     $$\text{pitch\_similarity} = \frac{1}{1 + \frac{\text{dtw\_distance}}{100}}$$
3. **Công thức điểm tổng hợp (Weighted Score)**:
   - Nhạc giai điệu phụ thuộc rất nhiều vào cao độ theo thời gian, do đó hệ thống ưu tiên cao độ:
     $$\text{Score} = 0.65 \times \text{pitch\_similarity} + 0.35 \times \text{vector\_similarity}$$

---

### 2.6. Phân Cụm Tối Ưu Bằng K-Means (`_6_clustering.py` & `build_database.py`)
Thuật toán K-Means được cài đặt **thủ công hoàn toàn** (không sử dụng thư viện ngoài như `scikit-learn`):
1. **Khởi tạo (K-Means++)**: Thay vì chọn ngẫu nhiên các tâm cụm (centroid), thuật toán sử dụng phương pháp xác suất K-Means++ để phân tán các tâm ban đầu ra xa nhau nhất có thể. Điều này giúp giảm thiểu việc rơi vào cực trị cục bộ và tăng tốc độ hội tụ.
2. **Vòng lặp tối ưu**:
   - **Gán cụm**: Tính khoảng cách Euclid từ mỗi vector bài hát đến các tâm cụm hiện tại, gán bài hát vào cụm có tâm gần nhất.
   - **Cập nhật tâm**: Tính trung bình tọa độ các bài hát trong mỗi cụm để làm tâm mới.
   - **Dừng**: Vòng lặp dừng lại khi sự thay đổi của các tâm cụm nhỏ hơn ngưỡng sai số $\text{tol} = 10^{-6}$ hoặc đạt số lần lặp tối đa `100`.
3. **Lưu trữ kết quả**: Kết quả phân cụm được lưu thành chỉ mục dưới dạng:
   - `cluster_centroids.npy`: Tọa độ 18 chiều của các tâm cụm.
   - `cluster_index.json`: Từ điển ánh xạ `ID cụm` -> `Danh sách tên các file nhạc thuộc cụm`.
   - `cluster_labels.json`: Ánh xạ nhanh `Tên file` -> `Cụm của nó`.

---

### 2.7. Tìm Kiếm Tối Ưu Cluster-based (`search_optimized.py`)
Đây là trái tim giúp hệ thống truy vấn cực nhanh:
1. Trích xuất đặc trưng của file Query thành vector 18 chiều.
2. Tính khoảng cách Euclid từ vector Query đến **10 tâm cụm (centroids)**.
3. Chỉ chọn ra $N$ cụm gần nhất (mặc định $N = 3$) để tìm kiếm chi tiết.
4. Hệ thống **bỏ qua hoàn toàn** các cụm còn lại. Thay vì duyệt 506 bài, hệ thống chỉ duyệt các bài hát thuộc 3 cụm này (thường chỉ chiếm 30% - 40% cơ sở dữ liệu), giúp **tiết kiệm từ 60% đến 80% thời gian tính toán**.
5. Tính điểm tương đồng lai ghép giữa Query và các bài hát được chọn, sắp xếp giảm dần và trả về kết quả Top-K.

---

### 2.8. Giao Diện Web & Máy Chủ (`app.py` & `templates/index.html`)
Cung cấp trải nghiệm trực quan cho người dùng cuối qua nền tảng Web:
- **Tải lên & Chuyển đổi**: Cho phép kéo thả file hoặc chọn tệp qua giao diện. Tự động chuyển đổi định dạng và phân tích trên server thông qua các route API của Flask (`POST /search`).
- **Tùy chỉnh tham số**: Người dùng có thể chỉnh số lượng kết quả (`top_k`) và mức độ quét cụm (`n_clusters`).
- **Thống kê hiệu năng**: Hiển thị thời gian phản hồi thực tế, số lượng bài hát đã được duyệt trong database và tỉ lệ tiết kiệm tài nguyên hệ thống thu được nhờ thuật toán phân cụm.
- **Trình phát nhạc tích hợp (Audio Playback Engine)**:
  - Cho phép nghe thử trực tiếp từng bài hát trong danh sách kết quả trả về.
  - Sử dụng cơ chế phát trực tiếp (Range Requests) từ backend `/audio/<filename>` để hỗ trợ kéo thả thanh tiến độ (seek-bar) mà không cần tải toàn bộ tệp về trước.
  - Có tính năng tự ngắt bài hát đang phát nếu người dùng bấm phát một bài khác.

---

## 3. Danh Sách Tệp Tin & Nhiệm Vụ

| Đường dẫn tệp tin | Vai trò chức năng chính |
| :--- | :--- |
| `_1_preprocess.py` | Load âm thanh, Mono hóa, Trim khoảng lặng, Bộ lọc tiền nhấn, Chia khung và Nhân cửa sổ Hamming. |
| `_2_stft.py` | Tính toán Real FFT từng khung tín hiệu và chuyển đổi sang thang logarit. |
| `_3_feature_extraction.py` | Trích xuất các đặc trưng tĩnh (18D) và chuỗi cao độ/hòa âm động. |
| `_4_normalize.py` | Thực hiện tính Min-Max và chuẩn hóa dữ liệu đặc trưng về dải $[0, 1]$. |
| `_5_similarity.py` | Tính độ tương quan Cosine trên vector và thuật toán DTW so khớp giai điệu. |
| `_6_clustering.py` | Cài đặt thuật toán phân cụm K-Means thủ công, tính toán tâm cụm và lưu chỉ mục cụm. |
| `build_database.py` | Chạy toàn bộ pipeline để xây dựng cơ sở dữ liệu âm thanh từ dataset WAV gốc. |
| `search_optimized.py` | Thực hiện tìm kiếm nhanh bằng cách chọn cụm gần nhất qua dòng lệnh (CLI). |
| `app.py` | Server Flask cung cấp API tìm kiếm, luồng phát nhạc (Range Requests) và bảo mật tệp tin. |
| `templates/index.html` | Giao diện đồ họa (UI) tương tác, trình phát nhạc tùy biến và biểu đồ kết quả. |
