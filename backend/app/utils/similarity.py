import json
import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

_vectorizer = HashingVectorizer(n_features=256, alternate_sign=False, norm='l2')

def compute_lyrics_vector(lyrics: str) -> str:
    vector = _vectorizer.transform([lyrics]).toarray()[0]
    return json.dumps(vector.tolist())

def cosine_similarity_from_json(vec1_json: str, vec2_json: str) -> float:
    v1 = np.array(json.loads(vec1_json))
    v2 = np.array(json.loads(vec2_json))
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 0.0
    return float(np.dot(v1, v2) / denom)
