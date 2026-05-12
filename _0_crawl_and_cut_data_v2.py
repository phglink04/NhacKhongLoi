import os
import subprocess
import re
import unicodedata
import yt_dlp

global_track_count = 1

# lưu tên bài đã cắt
existing_names = set()
TXT_FOLDER = "CrawlData_Timestamps"
OUTPUT_DIR = "Dataset_NhacKhongLoi"

# tạo folder output nếu chưa có
os.makedirs(OUTPUT_DIR, exist_ok=True)
# Hàm chuyển thời gian "mm:ss" hoặc "hh:mm:ss" sang giây
def time_to_sec(t_str):
    parts = [int(p) for p in t_str.split(':')]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

# Hàm làm sạch tên bài và nghệ sĩ
def clean_title(raw_title):
    match = re.match(r'(.*?)\s*\((.*?)\)', raw_title)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    elif '-' in raw_title:
        parts = raw_title.split('-', 1)
        return parts[0].strip(), parts[1].strip()
    return raw_title.strip(), "Unknown Artist"

# Hàm tạo tên file an toàn
def make_safe_filename(text):
    text = text.title()
    text = text.replace('Đ', 'D').replace('đ', 'd')
    text = unicodedata.normalize(
        'NFD',
        text
    ).encode(
        'ascii',
        'ignore'
    ).decode('utf-8')

    text = re.sub(r'[^a-zA-Z0-9]', '', text)
    return text

# Đọc tên bài đã có trong folder output để tránh trùng lặp
for filename in os.listdir(OUTPUT_DIR):
    if filename.endswith(".wav"):
        name = os.path.splitext(filename)[0]
        # bỏ số thứ tự
        name = re.sub(r'^\d+_', '', name)
        existing_names.add(name.lower())
        global_track_count += 1

# lấy file txt để xử lý
txt_files = [
    f for f in os.listdir(TXT_FOLDER)
    if f.endswith(".txt")
]

if len(txt_files) == 0:
    print("❌ Không tìm thấy file txt nào.")
    exit()

# xử lý từng file txt một
for txt_filename in txt_files:
    txt_path = os.path.join(
        TXT_FOLDER,
        txt_filename
    )
    print(f"\n{'='*60}")
    print(f"📄 Đang xử lý: {txt_filename}")
    print(f"{'='*60}")

    # đọc nội dung file txt
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = [
            line.strip()
            for line in f
            if line.strip()
        ]

    if len(lines) < 2:
        print("⚠️ File không đủ dữ liệu.")
        continue

    url = lines[0] 
    print(f"🎵 URL: {url}")

    temp_filename = f"temp_{hash(url)}.wav" # tên tạm để lưu audio gốc

    # tải audio từ YouTube
    print("⏳ Đang tải audio...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': temp_filename.replace('.wav', ''),
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Download thành công")
    except Exception as e:
        print(f"❌ Lỗi download: {e}")
        continue

    # phân tích nội dung để lấy thông tin track
    tracks_info = []
    for line in lines[1:]:
        match = re.search(
            r'\b(?:\d{1,2}:)?\d{1,2}:\d{2}\b',
            line
        )
        if match:
            time_str = match.group(0)
            raw_title = line.replace(
                time_str,
                ''
           ).strip()
            raw_title = re.sub(
                r'^[-:.\s]+|[-:.\s]+$',
                '',
                raw_title
            )
            tracks_info.append({

                'time_str': time_str,

                'raw_title': raw_title
            })

    # số track tìm được
    num_tracks = len(tracks_info)
    if num_tracks == 0:
        print("⚠️ Không có timestamp.")
        continue
    print(f"🎼 Tổng số track: {num_tracks}")
    # xử lý từng track một
    for i in range(num_tracks):
        start_sec = time_to_sec(
            tracks_info[i]['time_str']
        )
        # duration
        if i < num_tracks - 1:

            end_sec = time_to_sec(
                tracks_info[i + 1]['time_str']
            )

            duration = end_sec - start_sec
        else:
            duration = 9999
        title, artist = clean_title(
            tracks_info[i]['raw_title']
        )
        clean_name = make_safe_filename(title) # tên file an toàn
        normalized_name = clean_name.lower() # tên chuẩn hóa để check trùng lặp
        if normalized_name in existing_names:
            print(f"❌ Bỏ qua bài trùng: {title}")
            continue
        # thêm vào set
        existing_names.add(normalized_name)
# cắt audio theo timestamp
        cut_start = start_sec + 20 # cắt từ 20 giây sau 
        cut_duration = 30 # cắt 30 giây
        # bài quá ngắn
        if duration < 50:
            if duration > 20:
                cut_duration = duration - 20
            else:
                print(f"⏭️ Bỏ qua track {i+1}")
                continue
        output_name = os.path.join(
            OUTPUT_DIR,
            f"{global_track_count:03d}_{clean_name}.wav"
        )
        print(f"✅ {title}")
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(cut_start),
            "-t",
            str(cut_duration),
            "-i",
            temp_filename,
            "-ar",
            "22050",
            "-ac",
            "1",
            "-metadata",
            f"title={title}",
            "-metadata",
            f"artist={artist}",
            "-metadata",
            f"track={global_track_count}",
            "-metadata",
            f"comment=YouTube: {url}",
            output_name
        ]

        subprocess.run(

            cmd,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL
        )

        global_track_count += 1

    # ======================================
    # XÓA FILE TẠM
    # ======================================
    if os.path.exists(temp_filename):

        os.remove(temp_filename)

        print(f"🧹 Đã xóa: {temp_filename}")

print("\n🎉 HOÀN TẤT!")