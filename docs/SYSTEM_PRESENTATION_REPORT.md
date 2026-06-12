# BÁO CÁO KIẾN TRÚC VÀ QUY TRÌNH HỆ THỐNG TÌM KIẾM NHẠC TƯƠNG ĐỒNG

Báo cáo này làm rõ thiết kế hệ thống tìm kiếm nhạc tương đồng dựa trên nội dung (Content-Based Music Information Retrieval - CBMIR) sử dụng các đặc trưng âm thanh kết hợp giữa phân cụm K-Means++ và so khớp chuỗi thời gian DTW.

---

## PHẦN A: SƠ ĐỒ KHỐI VÀ QUY TRÌNH THỰC HIỆN CỦA HỆ THỐNG

Kiến trúc hệ thống được phân chia làm hai phân hệ chính: **Phân hệ Ngoại tuyến (Offline Phase)** để xây dựng cơ sở dữ liệu đặc trưng và **Phân hệ Trực tuyến (Online Phase)** để xử lý tệp truy vấn (Query) và tìm kiếm thời gian thực.

### 1. Sơ đồ khối tổng thể của hệ thống

```mermaid
graph TD
    %% Offline Phase
    subgraph "PHÂN HỆ NGOẠI TUYẾN (OFFLINE DATABASE BUILDING)"
        A[CSDL Nhạc Gốc .wav] --> B[Tiền xử lý âm thanh & Chia khung]
        B --> C[Biến đổi STFT]
        C --> D[Trích xuất Đặc trưng: RMS, ZCR, Pitch, Chroma]
        D --> E[Chuẩn hóa Min-Max các Vector đặc trưng]
        E --> F[K-Means Clustering: Phân cụm 506 bài hát thành 10 cụm]
        F --> G[Lưu trữ Database: database/audio_features.csv & database/sequences/*.npz]
    end

    %% Online Phase
    subgraph "PHÂN HỆ TRỰC TUYẾN (ONLINE REAL-TIME SEARCH)"
        H[File âm thanh truy vấn - Query .wav] --> I[Tiền xử lý & Trích xuất đặc trưng Query]
        I --> J[Chuẩn hóa Vector Query theo thang đo CSDL]
        G --> K[Nạp CSDL đặc trưng & chuỗi sequences vào RAM]
        J --> L[Tìm kiếm 3 cụm gần nhất - Nearest Clusters]
        K --> L
        L --> M[So sánh chi tiết trong 3 cụm bằng DTW & Cosine]
        M --> N[Tính điểm tương đồng lai ghép Hybrid Score]
        N --> O[Sắp xếp giảm dần & Xuất TOP 5 bài hát giống nhất]
    end
```

---

### 2. Quy trình thực hiện cụ thể khi tìm kiếm

Quy trình xử lý đối với tệp truy vấn đầu vào (cho cả 2 trường hợp: bài hát **đã có** hoặc **chưa có** trong CSDL):

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant App as Web Server / Search Engine
    participant DB as CSDL RAM / File
    
    User->>App: Gửi file truy vấn (.wav)
    Note over App: Bước 1: Tiền xử lý tín hiệu (Resampling, Mono, Normalization, Trim Silence)
    Note over App: Bước 2: Chia khung (Frame size = 2048, Hop size = 512) & Nhân cửa sổ Hamming
    Note over App: Bước 3: Tính STFT miền tần số cho từng khung
    Note over App: Bước 4: Trích xuất đặc trưng (18-dim Vector, Pitch contour, Chroma sequence)
    
    App->>DB: Lấy dữ liệu Tâm cụm K-Means & Dữ liệu bài hát trong RAM
    DB-->>App: Trả về 10 tâm cụm & toàn bộ sequences
    
    Note over App: Bước 5: Tính khoảng cách Euclid từ Vector Query tới 10 tâm cụm
    Note over App: Bước 6: Lọc ra 3 cụm có tâm gần nhất để khoanh vùng tìm kiếm
    Note over App: Bước 7: Tính toán song song trên 3 cụm này:
    Note over App: - Cosine Similarity giữa Vector đặc trưng
    Note over App: - DTW Distance giữa Pitch contour & Chroma sequence
    Note over App: Bước 8: Tính Hybrid Score = 0.65 * Pitch_sim + 0.35 * Vector_sim
    Note over App: Bước 9: Sắp xếp kết quả giảm dần theo Hybrid Score
    
    App-->>User: Trả về TOP 5 file âm thanh có độ tương đồng cao nhất
```

---

## PHẦN B: CÁC KẾT QUẢ TRUNG GIAN TRONG QUÁ TRÌNH TÌM KIẾM

Trong quá trình thực thi tìm kiếm trực tuyến, hệ thống sẽ tuần tự tạo ra các cấu trúc dữ liệu trung gian trong RAM để chuyển đổi thông tin từ sóng cơ học sang các đặc trưng toán học phục vụ đối sánh:

| Tên kết quả trung gian | Cấu trúc dữ liệu & Kích thước (Shape) | Ý nghĩa vật lý / Nhạc lý | Vai trò trong thuật toán |
| :--- | :--- | :--- | :--- |
| **1. Khung tín hiệu thô (Preprocessed Frames)** | Mảng 2D: $F \times 2048$ <br>*(với $F$ là số khung hình)* | Đoạn sóng âm ngắn thời gian $93\text{ ms}$ đã lọc nhiễu, chuẩn hóa biên độ về $[-1, 1]$ và nhân cửa sổ Hamming để tránh rò rỉ phổ. | Làm dữ liệu đầu vào sạch cho phép biến đổi Fourier nhanh (FFT). |
| **2. Phổ biên độ logarit (Log STFT Spectrogram)** | Ma trận 2D: $F \times 1024$ | Năng lượng phân bổ trên 1024 dải tần số từ $0$ đến $11025\text{ Hz}$ theo từng khung thời gian. | Làm cơ sở trích xuất tần số giai điệu (F0) và nốt nhạc (Chroma). |
| **3. Chuỗi Cao độ gốc (Raw Pitch Contour - F0)** | Mảng 1D: $F$ phần tử | Chuỗi tần số của nốt nhạc chính (giọng ca sĩ/nhạc cụ chính) biến thiên theo thời gian (Hz). | Làm chuỗi dữ liệu động đầu vào cho giải thuật đối sánh giai điệu bằng DTW. |
| **4. Chuỗi Hòa âm (Chroma Sequence)** | Mảng 2D: $F \times 12$ | Năng lượng phân bổ trên 12 nốt nhạc cơ bản ($C, C^\sharp, D,..., B$) qua từng khung thời gian. | Đặc trưng cho hòa âm và hợp âm nền, giúp đối sánh bằng DTW Chroma. |
| **5. Vector Đặc trưng tĩnh (Normalized Song Vector)** | Mảng 1D: $18$ chiều <br>*(Dải trị $[0, 1]$)* | Thống kê tổng quan về bài hát: Giá trị trung bình/Độ lệch chuẩn của RMS, ZCR, Pitch và phân bổ trung bình Chroma 12 nốt. | Dùng để tính **Cosine Similarity** (phong cách nhạc) và phân cụm **K-Means**. |
| **6. Khoảng cách Euclid tâm cụm** | Mảng 1D: $10$ phần tử | Mức độ sai khác giữa bài hát Query với phong cách chủ đạo của 10 cụm nhạc trong CSDL. | Dùng để chọn nhanh 3 cụm gần nhất, giảm $70\%$ số lượng bài hát cần so khớp DTW chi tiết. |
| **7. Ma trận chi phí tích lũy DTW** | Ma trận 2D: $N \times M$ <br>*(với $N, M$ là số khung của 2 bài)* | Tổng chi phí căn chỉnh nhịp độ tối thiểu lũy kế giữa khung $i$ của bài Query và khung $j$ của bài đối sánh. | Đường đi ngắn nhất trên ma trận này (Warping Path) cho ra khoảng cách DTW cuối cùng dùng để tính độ tương đồng giai điệu (`pitch_sim`). |

---

## Ý NGHĨA KHI FILE TRUY VẤN NẰM NGOÀI CƠ SỞ DỮ LIỆU
* **Nếu file truy vấn đã có trong CSDL**: Kết quả trả về chắc chắn sẽ có bài hát đó xếp ở vị trí **Top 1 với độ tương đồng 100.00%**, theo sau là 4 bài hát có giai điệu tương tự.
* **Nếu file truy vấn chưa có trong CSDL**: Quy trình trích xuất đặc trưng vẫn diễn ra hoàn toàn tương tự. Hệ thống sử dụng mô hình K-Means và chuẩn hóa dữ liệu dựa trên các tham số đã huấn luyện trước đó để định vị bài hát lạ này vào cụm phù hợp nhất, sau đó dùng DTW tìm ra 5 bài hát có cấu trúc giai điệu tương tự nhất trong CSDL mà không bị crash hay lỗi hệ thống. Điều này thể hiện tính **khái quát hóa (generalization)** cao của hệ thống đa phương tiện.
