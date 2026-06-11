# Audio Playback Feature - Hệ Thống Tìm Kiếm Nhạc

## 📻 Tính Năng Mới: Phát Nhạc Trực Tiếp

Người dùng giờ có thể **nghe trực tiếp các bài hát trong kết quả tìm kiếm** mà không cần tải file về.

---

## ✨ Những Gì Được Thêm Vào

### 1. **Web Interface Enhancements** (`templates/index.html`)

#### Thêm CSS cho Audio Player
```css
.audio-controls      /* Container cho các control */
.play-btn           /* Nút play/pause động */
.progress-bar       /* Thanh tiến độ có thể click */
.audio-duration     /* Hiển thị thời lượng */
```

#### Cập Nhật HTML Result Item
- Mỗi kết quả tìm kiếm giờ có:
  - 🔘 Nút **Play/Pause** (gradient động)
  - 📊 **Thanh tiến độ** (click để seek)
  - ⏱️ **Hiển thị thời gian** (--:-- ban đầu, cập nhật khi load)
  - 🔊 **HTML5 Audio Element** (ẩn)

#### Thêm JavaScript Functions
```javascript
toggleAudio(resultId, filename)    // Phát/tạm dừng âm thanh
seekAudio(event, resultId)         // Tua thanh tiến độ
formatTime(seconds)                // Format: MM:SS
```

### 2. **Backend Improvements** (`app.py`)

#### Route: `GET /audio/<filename>`
- ✅ **Phục vụ file audio** từ `Dataset_NhacKhongLoi/`
- ✅ **Hỗ trợ Range requests** (seek bar tương tác)
- ✅ **Detect MIME type** tự động (.wav, .mp3, .flac, .ogg)
- ✅ **CORS headers** cho playback từ browser
- ✅ **Security validation** để tránh path traversal attacks
- ✅ **Error handling** toàn diện

---

## 🎵 Cách Sử Dụng

### 1. **Khởi Động Web Server**
```bash
python app.py
```
Mở: `http://127.0.0.1:5000`

### 2. **Upload & Tìm Kiếm**
- Kéo thả file `.wav` hoặc click chọn
- Nhấn **🔍 Tìm kiếm**
- Chờ kết quả hiển thị

### 3. **Phát Bài Hát**
```
Mỗi kết quả có nút ▶:
▶  Click → Bắt đầu phát
⏸  Click → Tạm dừng
Click trên thanh → Tua đến vị trí khác
```

---

## 🔊 Features Chi Tiết

| Feature | Mô Tả |
|---------|-------|
| **Play/Pause** | Click nút để phát/tạm dừng |
| **Progress Bar** | Thanh xanh cho thấy vị trí hiện tại |
| **Seek** | Click thanh để nhảy đến vị trí |
| **Duration** | Hiển thị tổng thời lượng bài hát |
| **Auto-stop** | Tự động dừng khi phát bài khác |
| **Error Handling** | Thông báo nếu không thể phát |
| **Format Support** | .wav, .mp3, .flac, .ogg |

---

## 🎨 UI/UX Design

### Play Button States
```
Dừng (mặc định):
▶ [Blue Gradient]

Đang phát:
⏸ [Pink/Red Gradient]

Hover:
  Scale: 1.1 (phóng to)
  Shadow: Gradient mờ
```

### Progress Bar
- **Background**: Xám nhạt (10% opacity)
- **Fill**: Gradient xanh (667eea → 764ba2)
- **Height**: 4px (mảnh nhẹ)
- **Interaction**: Click để seek

---

## 📡 API Response Includes

Search results giờ trả về:
```json
{
  "results": [
    {
      "file_name": "001_GapMeTrongMo.wav",
      "title": "Gặp Mẹ Trong Mơ",
      "score": 85.5,
      ...
    }
  ]
}
```

→ `file_name` được sử dụng để request `/audio/<file_name>`

---

## 🔐 Security

Route `/audio/<filename>` có bảo vệ:
- ✅ Validate `filename` để tránh `../../../` traversal
- ✅ Verify file nằm trong `Dataset_NhacKhongLoi/`
- ✅ MIME type detection
- ✅ Exception handling

---

## 📊 Files Thay Đổi

| File | Thay Đổi |
|------|----------|
| `templates/index.html` | +CSS audio player, +HTML audio controls, +JS functions |
| `app.py` | Cập nhật route `/audio/<filename>` với validation & CORS |
| `README.md` | Thêm mô tả tính năng, API docs |

---

## ⚠️ Lưu Ý

1. **Các file phải nằm trong `Dataset_NhacKhongLoi/`** với tên khớp với `file_name` trong database
2. **Một lần chỉ phát một bài** (bài mới sẽ dừng bài cũ)
3. **Browser phải hỗ trợ HTML5 Audio** (mọi trình duyệt hiện đại đều hỗ trợ)
4. **CORS enabled** nhưng chỉ cho audioplayback

---

## 🚀 Mở Rộng Tương Lai

- ⭐ Playlist
- 🔊 Volume control
- 🔁 Loop/Repeat modes
- 💾 Download audio
- 📈 Visualizer
- ⌨️ Keyboard shortcuts

---

## 💡 Troubleshooting

### ❌ Nút play không hoạt động
→ Kiểm tra console (F12 → Console) để xem error

### ❌ Không nghe được âm thanh
→ Đảm bảo file `.wav` có trong `Dataset_NhacKhongLoi/` với tên chính xác

### ❌ CORS error
→ Backend đã có CORS headers, refresh page nếu cần

---

**Version**: 1.0  
**Last Updated**: 2026-05-12
