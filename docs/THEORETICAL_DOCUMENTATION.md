# TÀI LIỆU LÝ THUYẾT CHI TIẾT VỀ HỆ THỐNG XỬ LÝ ÂM THANH

Tài liệu này cung cấp nền tảng lý thuyết toán học và xử lý tín hiệu số (DSP) cơ bản được áp dụng trong hệ thống tìm kiếm nhạc tương tự của bạn.

---

## 1. Tiền Xử Lý Tín Hiệu (Audio Preprocessing)

### 1.1. Định lý lấy mẫu Nyquist-Shannon
Âm thanh tự nhiên là tín hiệu liên tục theo thời gian (analog). Để xử lý trên máy tính, nó phải được số hóa thành tín hiệu rời rạc qua quá trình lấy mẫu (sampling).
* **Định lý Nyquist-Shannon**: Để khôi phục hoàn hảo một tín hiệu liên tục có tần số cao nhất là $f_{\text{max}}$, tần số lấy mẫu $f_s$ phải thỏa mãn:
  $$f_s > 2 \cdot f_{\text{max}}$$
* **Ứng dụng**: Tai người bình thường chỉ nghe được âm thanh trong dải tần số từ $20\text{ Hz}$ đến $20000\text{ Hz}$. Do đó, tần số lấy mẫu chuẩn thu âm thường là $44100\text{ Hz}$. Trong dự án của bạn, tần số lấy mẫu được đưa về **`22050 Hz`** ($f_{\text{max}} = 11025\text{ Hz}$), vừa đủ để giữ lại các đặc trưng giọng hát và nhạc cụ chính của bản nhạc mà lại giảm được 50% lượng dữ liệu cần tính toán.

### 1.2. Bộ lọc tiền nhấn (Pre-emphasis Filter)
Khi thu âm, các thành phần tần số cao của giọng nói hoặc nhạc cụ thường có năng lượng thấp hơn nhiều so với tần số thấp. Bộ lọc tiền nhấn giúp khuếch đại tần số cao nhằm cân bằng phổ biên độ.
* **Công thức toán học**:
  $$y[t] = x[t] - \alpha \cdot x[t-1]$$
  Trong đó: $x[t]$ là tín hiệu gốc, $y[t]$ là tín hiệu sau lọc, và hệ số $\alpha = 0.97$.
* **Ý nghĩa vật lý**: Đây là một bộ lọc thông cao (High-pass filter) dạng sai phân bậc nhất, giúp làm nổi bật các đặc trưng âm sắc tần số cao (như âm treble, tiếng gió, tiếng nhạc cụ gõ).

### 1.3. Phân khung (Framing) và Cửa sổ Hamming (Hamming Window)
* **Phân khung (Framing)**: Tín hiệu âm thanh là tín hiệu phi tuyến và thay đổi liên tục theo thời gian. Tuy nhiên, trong các khoảng thời gian rất ngắn (từ $10\text{ ms}$ đến $100\text{ ms}$), tín hiệu âm thanh có thể được coi là dừng (quasi-stationary). Hệ thống chia tín hiệu thành các khung ngắn xếp chồng lên nhau:
  * Độ dài khung (`frame_size`): $2048$ mẫu ($\approx 93\text{ ms}$).
  * Độ dịch khung (`hop_length`): $512$ mẫu ($\approx 23\text{ ms}$), tương ứng độ chồng lấp $75\%$.
* **Cửa sổ Hamming**: Khi cắt tín hiệu thành các khung hình chữ nhật, tại hai rìa khung sẽ xảy ra hiện tượng đứt gãy tín hiệu đột ngột gây ra hiện tượng rò rỉ phổ (spectral leakage) khi biến đổi Fourier. Hệ thống nhân từng khung với cửa sổ Hamming để đưa tín hiệu ở hai rìa về gần bằng 0 một cách mượt mà.
  * **Công thức cửa sổ Hamming**:
    $$w[n] = 0.54 - 0.46 \cos\left(\frac{2\pi n}{N-1}\right), \quad 0 \le n \le N-1$$
    *(Với $N$ là độ dài khung $2048$)*.

---

## 2. Biến Đổi Fourier Thời Gian Ngắn (STFT)

Để phân tích tần số của tín hiệu âm thanh thay đổi theo thời gian, ta áp dụng phép biến đổi **Short-Time Fourier Transform (STFT)**.

* **Công thức toán học**:
  $$X(m, \omega) = \sum_{n=-\infty}^{\infty} x[n] w[n - m] e^{-j \omega n}$$
  Trong đó: $x[n]$ là tín hiệu đầu vào, $w[n]$ là hàm cửa sổ Hamming, và $e^{-j \omega n}$ là thành phần dao động điều hòa phức.
* **Biến đổi Fourier nhanh (FFT)**: Hệ thống sử dụng thuật toán **Real FFT (RFFT)** để chuyển nhanh từng khung từ miền thời gian sang miền tần số, tạo ra ma trận phổ biên độ $|X(m, \omega)|$.
* **Thang Log-magnitude**: Tai người cảm nhận cường độ âm thanh theo thang phi tuyến tính (logarit) chứ không theo thang tuyến tính. Do đó, phổ biên độ được chuyển đổi:
  $$Y(m, \omega) = \ln\left(1 + |X(m, \omega)|\right)$$

---

## 3. Trích Xuất Đặc Trưng Âm Thanh (Audio Features)

### 3.1. RMS Energy (Năng lượng hiệu dụng)
Biểu thị độ to vật lý (loudness) của khung âm thanh.
* **Công thức**:
  $$x_{\text{RMS}} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} x_i^2}$$
  *(Với $x_i$ là biên độ của mẫu thứ $i$ trong khung)*.

### 3.2. Zero Crossing Rate (ZCR)
Tần suất thay đổi dấu (từ dương sang âm hoặc ngược lại) của tín hiệu trong một khung.
* **Công thức**:
  $$\text{ZCR} = \frac{1}{2(N-1)} \sum_{i=1}^{N-1} |\operatorname{sgn}(x_i) - \operatorname{sgn}(x_{i-1})|$$
* **Ứng dụng**: ZCR cao thường tương ứng với tiếng ồn, nhạc cụ gõ (trống, xèng) hoặc phụ âm không thanh. ZCR thấp tương ứng với các nốt nhạc có giai điệu rõ ràng.

### 3.3. Chroma Features (Pitch Class Profile - PCP)
Đây là đặc trưng mạnh mẽ nhất đại diện cho hòa âm (harmony) và hợp âm của bài hát, độc lập với quãng tám và nhạc cụ thể hiện.
* **Lý thuyết**: Hệ thống âm nhạc phương Tây chia một quãng tám thành 12 bán âm ($C, C^\sharp, D, D^\sharp, E, F, F^\sharp, G, G^\sharp, A, A^\sharp, B$). Tần số của nốt nhạc được tính theo công thức:
  $$f = 440 \cdot 2^{\frac{p - 69}{12}}$$
  *(Với $p$ là chỉ số MIDI)*.
* **Cách tính**: Hệ thống gộp năng lượng của tất cả các tần số thuộc cùng một nốt nhạc ở các quãng tám khác nhau lại thành một vector 12 chiều. Vector này sau đó được chuẩn hóa để tổng bằng 1.

---

## 4. Các Phương Pháp So Sánh Độ Tương Đồng

### 4.1. Độ tương đồng Cosine (Cosine Similarity)
Sử dụng để đo mức độ tương đồng giữa hai vector đặc trưng tĩnh 18 chiều đại diện cho toàn bộ bài hát.
* **Công thức**:
  $$\text{Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$$
* **Ý nghĩa**: Giá trị trả về từ $-1$ đến $1$ (ở đây đặc trưng luôn dương nên nằm trong khoảng $[0, 1]$). Giá trị càng gần 1 thể hiện hướng của hai vector càng trùng nhau, tức cấu trúc âm thanh tổng thể càng giống nhau.

### 4.2. Dynamic Time Warping (DTW)
Được sử dụng để so khớp chuỗi giai điệu cao độ biến thiên theo thời gian.
* **Bài toán**: Hai bản nhạc có cùng giai điệu nhưng được hát với tốc độ khác nhau (một bản nhanh hơn, một bản chậm hơn) sẽ có độ dài chuỗi cao độ khác nhau. Phép so sánh khoảng cách Euclid thông thường sẽ thất bại.
* **Thuật toán**: DTW xây dựng ma trận khoảng cách tích lũy $D$ kích thước $M \times N$ giữa hai chuỗi $X$ và $Y$:
  $$D(i, j) = d(x_i, y_j) + \min\Big(D(i-1, j), \, D(i, j-1), \, D(i-1, j-1)\Big)$$
  Đường đi có tổng chi phí nhỏ nhất từ góc dưới bên trái $(1, 1)$ đến góc trên bên phải $(M, N)$ chính là khoảng cách DTW tối ưu.
* **Tối ưu hóa Sakoe-Chiba Band**: Giới hạn đường đi chỉ nằm trong một khoảng hẹp $W$ xung quanh đường chéo của ma trận:
  $$|i - j| \le W$$
  Giúp giảm độ phức tạp tính toán từ $O(N \cdot M)$ xuống $O(N \cdot W)$ và ngăn chặn việc "co dãn" thời gian quá mức phi thực tế.

---

## 5. Thuật Toán Phân Cụm K-Means++

K-Means là thuật toán học không giám sát phân cụm dữ liệu nhằm tối thiểu hóa hàm mục tiêu WCSS (Tổng bình phương khoảng cách trong cụm):
$$\text{WCSS} = \sum_{j=1}^{k} \sum_{\mathbf{x} \in S_j} \|\mathbf{x} - \boldsymbol{\mu}_j\|^2$$

* **Cải tiến K-Means++**: Khởi tạo các tâm cụm ban đầu bằng phương pháp xác suất:
  1. Chọn tâm cụm đầu tiên $\boldsymbol{\mu}_1$ ngẫu nhiên từ tập dữ liệu.
  2. Với mỗi điểm dữ liệu $\mathbf{x}$, tính khoảng cách ngắn nhất $D(\mathbf{x})$ đến các tâm cụm đã chọn.
  3. Chọn tâm cụm tiếp theo $\boldsymbol{\mu}_i$ từ các điểm dữ liệu với xác suất tỉ lệ thuận với bình phương khoảng cách:
     $$P(\mathbf{x}) = \frac{D(\mathbf{x})^2}{\sum_{\mathbf{y}} D(\mathbf{y})^2}$$
  4. Lặp lại bước 2 và 3 cho đến khi đủ $k$ tâm cụm.
  * *Ưu điểm*: Đảm bảo các tâm cụm khởi tạo được phân tán rộng khắp không gian đặc trưng, giúp thuật toán hội tụ nhanh hơn và đạt kết quả tối ưu hơn.
