import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import numpy as np
from tests.evaluation_dataset import EVALUATION_PAIRS

def cosine_similarity(v1, v2):
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 0.0
    return float(np.dot(v1, v2) / denom)

def evaluate_model(model_name):
    print("\n" + "=" * 75)
    print(f"EVALUATING MODEL: {model_name}")
    print("=" * 75)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("sentence_transformers not installed!")
        return None

    load_start = time.time()
    model = SentenceTransformer(model_name)
    load_time = (time.time() - load_start) * 1000
    print(f"Model load time: {load_time:.2f} ms")

    start_time = time.time()
    results = []

    for item in EVALUATION_PAIRS:
        t_a = item["text_a"]
        t_b = item["text_b"]

        emb_a = model.encode(t_a)
        emb_b = model.encode(t_b)

        score = cosine_similarity(emb_a, emb_b)
        results.append({
            "id": item["id"],
            "category": item["category"],
            "languages": f"{item['language_a']} -> {item['language_b']}",
            "expected": item["expected_similarity"],
            "score": round(score, 4)
        })

    eval_time = (time.time() - start_time) * 1000
    avg_latency = eval_time / (len(EVALUATION_PAIRS) * 2)

    print(f"{'ID':<8} {'Category':<28} {'Languages':<20} {'Score':<10} {'Expected':<18}")
    print("-" * 90)
    for r in results:
        print(f"{r['id']:<8} {r['category']:<28} {r['languages']:<20} {r['score']:<10} {r['expected']:<18}")

    print("-" * 90)
    print(f"Total encode time: {eval_time:.2f} ms | Avg per text: {avg_latency:.2f} ms")
    return {
        "model_name": model_name,
        "load_time_ms": round(load_time, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "dimension": len(emb_a),
        "results": results
    }

if __name__ == "__main__":
    for m in ["all-MiniLM-L6-v2", "paraphrase-multilingual-MiniLM-L12-v2"]:
        try:
            evaluate_model(m)
        except Exception as e:
            print(f"Failed to evaluate {m}: {e}")
