import csv
import numpy as np

from _1_preprocess import preprocess_audio
from _2_stft import compute_stft
from _3_feature_extraction import extract_features
from _4_normalize import normalize_vector
from _5_similarity import euclidean_distance

# load normalization params
min_vals = []
max_vals = []

with open( "database/normalization.csv","r") as f:

    reader = csv.reader(f)
    next(reader)
    for row in reader:
        min_vals.append(float(row[1]))
        max_vals.append(float(row[2]))

# process query audio

query_path = "query.wav"

frames, sample_rate = preprocess_audio( query_path )

stft_result = compute_stft(frames)

query_features = extract_features(
    frames,
    stft_result,
    sample_rate
)

query_vector = normalize_vector(
    query_features,
    min_vals,
    max_vals
)

# compute similarity with database

results = []

with open( "database/music_features.csv", "r" ) as f:
    reader = csv.reader(f)

    next(reader)

    for row in reader:
        file_name = row[0]
        db_vector = list(map(float, row[1:]) )

        distance = euclidean_distance(
            query_vector,
            db_vector
        )

        results.append(
            (file_name, distance)
        )

# sort by distance

results.sort(key=lambda x: x[1])

# print top 5 results

print("\nTOP 5 SIMILAR SONGS:\n")

for i in range(5):
    print( i + 1, results[i][0], "distance:", results[i][1] )