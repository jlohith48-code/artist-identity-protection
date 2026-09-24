import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import time
from tests.evaluation_dataset import EVALUATION_PAIRS
from app.utils.similarity import compute_lyrics_vector, cosine_similarity_from_json
from app.utils.hashing import generate_lyrics_hash

def run_hashing_vectorizer_baseline():
    print("=" * 70)
    print("BASELINE EVALUATION: HashingVectorizer (256-dim)")
    print("=" * 70)

    start_time = time.time()
    results = []

    for item in EVALUATION_PAIRS:
        t_a = item["text_a"]
        t_b = item["text_b"]

        # Exact hash check
        hash_a = generate_lyrics_hash(t_a)
        hash_b = generate_lyrics_hash(t_b)
        exact_hash_match = (hash_a == hash_b)

        # Vector similarity
        v_a = compute_lyrics_vector(t_a)
        v_b = compute_lyrics_vector(t_b)
        score = cosine_similarity_from_json(v_a, v_b)

        results.append({
            "id": item["id"],
            "category": item["category"],
            "languages": f"{item['language_a']} -> {item['language_b']}",
            "expected": item["expected_similarity"],
            "exact_hash_match": exact_hash_match,
            "hashing_vec_score": round(score, 4)
        })

    total_time = (time.time() - start_time) * 1000
    avg_latency = total_time / len(EVALUATION_PAIRS)

    print(f"{'ID':<8} {'Category':<28} {'Languages':<20} {'ExactHash':<10} {'VecScore':<10} {'Expected':<18}")
    print("-" * 95)
    for r in results:
        print(f"{r['id']:<8} {r['category']:<28} {r['languages']:<20} {str(r['exact_hash_match']):<10} {r['hashing_vec_score']:<10} {r['expected']:<18}")

    print("-" * 95)
    print(f"Total time: {total_time:.2f} ms | Avg per pair: {avg_latency:.2f} ms")
    return results

if __name__ == "__main__":
    run_hashing_vectorizer_baseline()
