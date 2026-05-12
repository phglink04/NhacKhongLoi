import os
import subprocess
import re
import unicodedata
import yt_dlp
global_track_count = 1
# ==========================================
# 1. CẤU HÌNH DỮ LIỆU ĐẦU VÀO & THƯ MỤC
# ==========================================
# Thư mục lưu trữ kết quả cuối cùng
OUTPUT_DIR = "Dataset_NhacKhongLoi"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Từ điển (Dictionary) ghép nối: "Link YouTube" : "Tên file TXT chứa timestamp"
YOUTUBE_DATA = {
    "https://www.youtube.com/watch?v=40stvXzlLJE": "timestamp_link1.txt",
    # Bạn cứ phẩy và thêm các link khác vào đây...
}

# ==========================================
# CÁC HÀM PHỤ TRỢ
# ==========================================
def time_to_sec(t_str):
    parts = [int(p) for p in t_str.split(':')]
    if len(parts) == 2: return parts[0] * 60 + parts[1]
    elif len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

def clean_title(raw_title):
    match = re.match(r'(.*?)\s*\((.*?)\)', raw_title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    elif '-' in raw_title:
        parts = raw_title.split('-', 1)
        return parts[1].strip(), parts[0].strip()
    return raw_title.strip(), "Unknown Artist"

def make_safe_filename(text):
    # 1. Viết hoa chữ cái đầu mỗi từ để khi xóa khoảng trắng vẫn dễ đọc (CamelCase)
    text = text.title()
    
    # 2. Xử lý riêng chữ Đ và đ (Vì thư viện chuẩn không tự xử lý được chữ này)
    text = text.replace('Đ', 'D').replace('đ', 'd')
    
    # 3. Tách các dấu thanh (huyền, sắc, hỏi, ngã, nặng) ra khỏi chữ cái và xóa chúng đi
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    
    # 4. Xóa toàn bộ dấu cách và các ký tự đặc biệt (chỉ giữ lại chữ cái và chữ số)
    text = re.sub(r'[^a-zA-Z0-9]', '', text)
    
    return text
# ==========================================
# QUY TRÌNH XỬ LÝ CHÍNH
# ==========================================
for url, txt_file in YOUTUBE_DATA.items():
    print(f"\n{'='*50}")
    print(f"BẮT ĐẦU XỬ LÝ: {url}")
    print(f"File Timestamp: {txt_file}")
    print(f"{'='*50}")

    # Kiểm tra xem file TXT có tồn tại không trước khi tốn công tải Video
    if not os.path.exists(txt_file):
        print(f"❌ BỎ QUA: Không tìm thấy file '{txt_file}'.")
        continue

    # --------------------------------------------------
    # BƯỚC 1: CÀO (CRAWL) ÂM THANH TỪ YOUTUBE
    # --------------------------------------------------
    # Tạo tên file tạm thời cho file tải về (tránh trùng lặp)
    temp_filename = f"temp_downloaded_{hash(url)}.wav"
    
    print("⏳ Đang tải âm thanh từ YouTube xuống...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': temp_filename.replace('.wav', ''), # yt-dlp tự động thêm đuôi .wav
        'quiet': True, # Tắt log rác của yt-dlp cho màn hình sạch sẽ
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Tải hoàn tất!")
    except Exception as e:
        print(f"❌ Lỗi khi tải video: {e}")
        continue

    # --------------------------------------------------
    # BƯỚC 2: ĐỌC VÀ BÓC TÁCH FILE TIMESTAMP
    # --------------------------------------------------
    tracks_info = []
    with open(txt_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            match = re.search(r'\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b', line)
            if match:
                time_str = match.group(0)
                raw_title = line.replace(time_str, '').strip()
                raw_title = re.sub(r'^[-:.\s]+|[-:.\s]+$', '', raw_title)
                tracks_info.append({'time_str': time_str, 'raw_title': raw_title})

    num_tracks = len(tracks_info) 
    if num_tracks == 0:
        print("⚠️ File txt không có mốc thời gian nào.")
        if os.path.exists(temp_filename): os.remove(temp_filename)
        continue

    # --------------------------------------------------
    # BƯỚC 3: ÁP DỤNG LUẬT CẮT (BỎ 10S ĐẦU, LẤY 30S) & LƯU FILE
    # --------------------------------------------------
    print(f"✂️ Tiến hành cắt {num_tracks} bài hát...\n")
    for i in range(num_tracks):
        start_sec = time_to_sec(tracks_info[i]['time_str'])
        
        # TÍNH TOÁN DURATION THÔNG MINH CHO BÀI CUỐI CÙNG
        if i < num_tracks - 1:
            # Nếu chưa phải bài cuối -> Có mốc tiếp theo để tính khoảng cách
            end_sec = time_to_sec(tracks_info[i+1]['time_str'])
            duration = end_sec - start_sec
        else:
            # NẾU LÀ BÀI CUỐI CÙNG: 
            # Giả sử nó đủ dài (cho 1 con số lớn), FFMPEG sẽ tự động cắt đến hết video nếu video ngắn hơn.
            duration = 9999 

        title, artist = clean_title(tracks_info[i]['raw_title'])

        # --- ÁP DỤNG LOGIC CẮT CỦA BẠN ---
        cut_start = start_sec + 10
        cut_duration = 30
        
        # Xử lý các bài hát quá ngắn (nếu có)
        if duration < 40:
            if duration > 10:
                cut_duration = duration - 10
            else:
                print(f"⏭️ Bỏ qua track {i+1}: Quá ngắn (<10s).")
                continue

        # Gọi hàm làm sạch tên bài hát
        clean_name = make_safe_filename(title)
        
        # Đặt tên file: Nối số thứ tự và tên bài hát bằng dấu gạch dưới (để tuyệt đối không có khoảng trắng)
        output_name = os.path.join(OUTPUT_DIR, f"{global_track_count:03d}_{clean_name}.wav")

        print(f"  -> Đang lưu: {title} (Ca sĩ: {artist})")
        
        cmd = [
            "ffmpeg", "-y", 
            "-ss", str(cut_start), 
            "-t", str(cut_duration), 
            "-i", temp_filename,
            "-ar", "22050", "-ac", "1",
            "-metadata", f"title={title}",
            "-metadata", f"artist={artist}",
            "-metadata", f"track={global_track_count}",
            output_name
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        global_track_count += 1
    # --------------------------------------------------
    # BƯỚC 4: DỌN DẸP RÁC (XÓA FILE WAV GỐC TẢI TỪ YOUTUBE)
    # --------------------------------------------------
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
        print(f"🧹 Đã dọn dẹp file tạm: {temp_filename}")

print("\n🎉 TẤT CẢ QUY TRÌNH ĐÃ HOÀN TẤT THÀNH CÔNG!")