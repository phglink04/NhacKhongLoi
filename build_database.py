import os
import csv
import numpy as np

from _1_preprocess import preprocess_audio
from _2_stft import compute_stft
from _3_feature_extraction import extract_features
from _4_normalize import ( compute_min_max, normalize_vector)

dataset_path = "Dataset_NhacKhongLoi"
all_features = []
file_names = []

# extract features for each audio file in dataset

for file_name in os.listdir(dataset_path):

    if file_name.endswith(".wav"):

        file_path = os.path.join( dataset_path, file_name)
        print("Processing:", file_name)
        frames, sample_rate = preprocess_audio(file_path)
        stft_result = compute_stft(frames)
        features = extract_features(
            frames,
            stft_result,
            sample_rate
        )

        all_features.append(features)
        file_names.append(file_name)

feature_matrix = np.array(all_features)

# compute normalization params and normalize features

min_vals, max_vals = compute_min_max( feature_matrix)
normalized_features = []
for vector in feature_matrix:
    norm_vector = normalize_vector( vector, min_vals, max_vals )
    normalized_features.append(norm_vector)

# SAVE TO CSV

os.makedirs("database", exist_ok=True)

with open( "database/music_features.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "file_name",
        "rms_std",
        "rms_mean",
        "zcr_std",
        "zcr_mean",
        "pitch_std",
        "pitch_mean",
        "chroma"
    ])

    for i in range(len(file_names)):
        writer.writerow( [file_names[i]]  + normalized_features[i] )

# SAVE NORMALIZATION PARAMS

with open( "database/normalization.csv","w", newline="" ) as f:
    writer = csv.writer(f)
    writer.writerow([ "feature", "min", "max" ])
    names = [
        "rms",
        "zcr",
        "pitch",
        "chroma"
    ]

    for i in range(len(names)):
        writer.writerow([
            names[i],
            min_vals[i],
            max_vals[i]
        ])

print("DATABASE BUILT SUCCESSFULLY")