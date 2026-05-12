import numpy as np


def compute_min_max(feature_matrix):
    min_vals = np.min(feature_matrix, axis=0)
    max_vals = np.max(feature_matrix, axis=0)
    return min_vals, max_vals

def normalize_vector( vector,min_vals,max_vals):
    normalized = []
    for i in range(len(vector)):
        if max_vals[i] == min_vals[i]:
            normalized.append(0)
        else:
            value = ((vector[i] - min_vals[i]) / (max_vals[i] - min_vals[i]))
            normalized.append(value)

    return normalized