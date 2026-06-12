# BỘ CÂU HỎI VÀ ĐÁP ÁN BẢO VỆ ĐỒ ÁN MÔN CƠ SỞ DỮ LIỆU ĐA PHƯƠNG TIỆN

Tài liệu này tổng hợp những câu hỏi mà giáo viên môn **Cơ sở dữ liệu đa phương tiện (CSDL Đa phương tiện)** thường đặt ra khi chấm đồ án hoặc bài tập lớn, kèm theo ý đồ của câu hỏi và gợi ý câu trả lời chuẩn học thuật bám sát mã nguồn dự án của bạn.

---

## CHỦ ĐỀ 1: TIỀN XỬ LÝ & BIẾN ĐỔI TÍN HIỆU SỐ (DSP)

### Câu hỏi 1: Tại sao em lại chọn tần số lấy mẫu là 22050 Hz cho các file nhạc trong CSDL thay vì giữ nguyên 44100 Hz chuẩn gốc?
* **Ý đồ của giáo viên**: Kiểm tra hiểu biết về **Định lý lấy mẫu Nyquist-Shannon** và khả năng tối ưu hóa tài nguyên hệ thống đa phương tiện.
* **Câu trả lời**:
  > "Thưa thầy/cô, theo định lý lấy mẫu Nyquist-Shannon, để khôi phục được tín hiệu có tần số cao nhất là $f_{\text{max}}$ thì tần số lấy mẫu $f_s$ phải lớn hơn $2 \cdot f_{\text{max}}$. Tai người bình thường chỉ nghe được âm thanh trong dải tần số từ $20\text{ Hz}$ đến $20000\text{ Hz}$. Do đó, tần số lấy mẫu chuẩn thu âm thường là $44100\text{ Hz}$. Trong dự án của bạn, tần số lấy mẫu được đưa về **`22050 Hz`** (đáp ứng tần số tối đa $11025\text{ Hz}$), vừa đủ để giữ lại các đặc trưng giọng hát và nhạc cụ chính của bản nhạc mà lại giảm được 50% lượng dữ liệu cần tính toán."

### Câu hỏi 2: Phân khung (Framing) tín hiệu để làm gì? Tại sao phải dùng cửa sổ Hamming thay vì cắt khung hình chữ nhật thông thường?
* **Ý đồ của giáo viên**: Kiểm tra kiến thức về tính chất dừng của tín hiệu và hiện tượng **Rò rỉ phổ (Spectral Leakage)**.
* **Câu trả lời**:
  > "Tín hiệu âm thanh thay đổi liên tục theo thời gian (phi tuyến). Để phân tích tần số, chúng ta phải chia nhỏ tín hiệu thành các khung hình dài 2048 mẫu ($\approx 93\text{ ms}$) xếp chồng lên nhau 512 mẫu để đảm bảo tính chất 'dừng' của tín hiệu trong khung đó. 
  > Nếu ta dùng khung hình chữ nhật (cắt trực tiếp), tại hai rìa khung sẽ xảy ra hiện tượng đứt gãy tín hiệu đột ngột, gây ra các tần số nhiễu giả khi thực hiện biến đổi Fourier (gọi là rò rỉ phổ). Hệ thống áp dụng **cửa sổ Hamming** để triệt tiêu biên độ ở hai đầu khung về gần bằng 0 một cách mượt mà, giúp phổ tần số sau khi biến đổi Fourier chính xác hơn."

---

## CHỦ ĐỀ 2: TRÍCH XUẤT ĐẶC TRƯNG ĐA PHƯƠNG TIỆN (FEATURE EXTRACTION)

### Câu hỏi 3: Đặc trưng Chroma (Pitch Class Profile) là gì và tại sao nó lại là đặc trưng quan trọng nhất cho bài toán tìm kiếm giai điệu nhạc?
* **Ý đồ của giáo viên**: Kiểm tra hiểu biết về các đặc trưng mức cao (High-level features) chuyên dụng cho âm nhạc.
* **Câu trả lời**:
  > "Đặc trưng Chroma biểu diễn sự phân bổ năng lượng phổ âm thanh vào 12 nốt nhạc cơ bản ($C, C^\sharp, D,..., B$) trong một quãng tám. Nó có đặc tính **bất biến với quãng tám (Octave equivalence)** và **âm sắc nhạc cụ**. Nghĩa là dù bài hát được thể hiện bằng đàn Piano ở quãng tám thứ 4 hay bằng sáo trúc ở quãng tám thứ 5, hoặc do ca sĩ nam/nữ hát tông khác nhau, cấu trúc vector Chroma vẫn giữ nguyên sự tương đồng về hòa âm. Điều này giúp Chroma vượt trội hơn các đặc trưng tần số thô khi so khớp giai điệu."

### Câu hỏi 4: Sự khác nhau giữa đặc trưng tĩnh (Song-level) và đặc trưng động (Sequence) trong hệ thống của em là gì? Chúng được sử dụng ở bước nào?
* **Ý đồ của giáo viên**: Kiểm tra cách tổ chức và sử dụng đặc trưng để tối ưu hóa thời gian chạy.
* **Câu trả lời**:
  > "1. **Đặc trưng tĩnh (18 chiều)**: Được tính trung bình trên toàn bộ bài hát (gồm RMS, ZCR, Pitch mean/std và 12 chiều Chroma trung bình). Dữ liệu này lưu trong file `audio_features.csv` để phục vụ cho thuật toán phân cụm K-Means và tính Cosine Similarity nhanh.
  > 2. **Đặc trưng động**: Là chuỗi thay đổi theo từng khung hình thời gian (gồm mảng Pitch và ma trận Chroma $N \times 12$). Dữ liệu này được lưu trong các file `.npz` để phục vụ cho thuật toán DTW so khớp chi tiết diễn biến thời gian của giai điệu giữa file truy vấn và các bài hát được chọn."

---

## CHỦ ĐỀ 3: THUẬT TOÁN ĐỘ TƯƠNG ĐỒNG & SO KHỚP (SIMILARITY MATCHING)

### Câu hỏi 5: Tại sao em không dùng khoảng cách Euclid để so sánh hai chuỗi Pitch mà phải dùng thuật toán Dynamic Time Warping (DTW)?
* **Ý đồ của giáo viên**: Kiểm tra hiểu biết về sự co dãn thời gian (Time warping) của dữ liệu đa phương tiện liên tục.
* **Câu trả lời**:
  > "Hai bản nhạc cùng một giai điệu nhưng có thể được chơi với tốc độ nhanh chậm khác nhau. Nếu dùng khoảng cách Euclid, ta bắt buộc hai chuỗi phải có độ dài bằng nhau và so sánh từng cặp điểm thứ $t$ cố định. Chỉ cần một bài hát lệch nhịp một chút, khoảng cách Euclid sẽ tăng vọt và cho kết quả sai lệch.
  > Thuật toán **DTW** giải quyết bài toán này bằng cách uốn khớp thời gian, tự động căn chỉnh và tìm đường đi tối ưu giữa các điểm có tần số giống nhau kể cả khi một bên bị kéo dài hoặc co ngắn lại theo thời gian."

### Câu hỏi 6: Sakoe-Chiba Band trong thuật toán DTW của em có tác dụng gì?
* **Ý đồ của giáo viên**: Kiểm tra khả năng tối ưu thuật toán động và hạn chế sai lệch uốn khớp.
* **Câu trả lời**:
  > "Sakoe-Chiba Band giới hạn đường đi uốn khớp của DTW trong một cửa sổ độ rộng $W$ (mặc định là 50 khung hình) xung quanh đường chéo chính của ma trận khoảng cách tích lũy. Tác dụng của nó là:
  > 1. **Tối ưu tốc độ**: Giảm độ phức tạp tính toán DTW từ $O(N \cdot M)$ xuống $O(N \cdot W)$, giúp thuật toán chạy nhanh hơn rất nhiều.
  > 2. **Tránh uốn khớp phi thực tế**: Ngăn chặn việc thuật toán khớp một nốt nhạc cực ngắn của file này với một đoạn nhạc cực dài của file kia."

---

## CHỦ ĐỀ 4: PHÂN CỤM & TỐI ƯU HÓA CƠ SỞ DỮ LIỆU (INDEXING)

### Câu hỏi 7: Thuật toán K-Means giúp tối ưu hóa thời gian tìm kiếm như thế nào? Nêu cơ chế hoạt động của tìm kiếm tối ưu (Search Optimized)?
* **Ý đồ của giáo viên**: Đây là câu hỏi cốt lõi của môn học về **Lập chỉ mục (Indexing)** để tăng tốc độ tìm kiếm trong CSDL Đa phương tiện.
* **Câu trả lời**:
  > "If không phân cụm, với mỗi truy vấn ta phải quét tuyến tính và tính khoảng cách DTW với toàn bộ 506 bài hát trong CSDL, điều này cực kỳ tốn thời gian do DTW có chi phí tính toán lớn.
  > Nhờ phân cụm **K-Means (K=10)**:
  > 1. Hệ thống tính khoảng cách Euclid từ file Query tới **10 tâm cụm (centroids)** trước (chỉ tốn 10 phép tính khoảng cách trên không gian 18 chiều, gần như tức thời).
  > 2. Lọc ra **3 cụm gần nhất** và chỉ thực hiện so khớp chi tiết DTW với các bài hát nằm trong 3 cụm này.
  > 3. Bỏ qua hoàn toàn 7 cụm còn lại. Cơ chế này giúp giảm không gian quét từ 506 bài xuống còn khoảng 150-180 bài (tiết kiệm 65% - 75% thời gian tính toán)."

### Câu hỏi 8: Em hãy giải thích sự khác biệt giữa khởi tạo K-Means truyền thống và K-Means++?
* **Ý đồ của giáo viên**: Đánh giá hiểu biết sâu về thuật toán phân cụm dữ liệu.
* **Câu trả lời**:
  > "K-Means truyền thống chọn ngẫu nhiên $K$ điểm dữ liệu ban đầu làm tâm cụm. Cách này rất dễ làm các tâm cụm nằm quá gần nhau, dẫn đến thuật toán rơi vào cực trị cục bộ và chất lượng phân cụm kém.
  > **K-Means++** giải quyết vấn đề này bằng cách khởi tạo tâm cụm theo xác suất: Chỉ chọn ngẫu nhiên tâm thứ nhất, các tâm tiếp theo sẽ được chọn ưu tiên từ các điểm dữ liệu nằm xa các tâm đã có nhất (tỷ lệ thuận với bình phương khoảng cách $D(x)^2$). Cách khởi tạo thông minh này giúp các tâm cụm phân tán đều hơn, thuật toán hội tụ nhanh hơn và phân cụm chính xác hơn."
