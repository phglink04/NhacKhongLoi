import numpy as np

def euclidean_distance(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)

    return np.sqrt(
        np.sum((v1 - v2) ** 2)
    )