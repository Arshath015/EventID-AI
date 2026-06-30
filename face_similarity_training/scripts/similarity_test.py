import sys
from pathlib import Path

# ---- access config.py ----
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import *

import numpy as np
import random
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import csv

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_embeddings(split):
    return np.load(
        EMBEDDINGS_DIR / f"{split}_embeddings.npy",
        allow_pickle=True
    )

def main():
    data = load_embeddings("val")  # validation set for testing

    genuine_scores = []
    imposter_scores = []

    # group embeddings by person
    person_map = {}
    for item in data:
        person_map.setdefault(item["person_id"], []).append(item["embedding"])

    persons = list(person_map.keys())

    # Genuine comparisons (same person)
    for person in tqdm(persons, desc="Genuine comparisons"):
        embeds = person_map[person]
        if len(embeds) < 2:
            continue

        for i in range(len(embeds) - 1):
            sim = cosine_similarity(
                embeds[i].reshape(1, -1),
                embeds[i + 1].reshape(1, -1)
            )[0][0]
            genuine_scores.append(sim)

    # Imposter comparisons (different persons)
    for _ in tqdm(range(len(genuine_scores)), desc="Imposter comparisons"):
        p1, p2 = random.sample(persons, 2)
        e1 = random.choice(person_map[p1])
        e2 = random.choice(person_map[p2])

        sim = cosine_similarity(
            e1.reshape(1, -1),
            e2.reshape(1, -1)
        )[0][0]
        imposter_scores.append(sim)

    # Save results
    with open(RESULTS_DIR / "similarity_scores.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "similarity"])
        for s in genuine_scores:
            writer.writerow(["genuine", s])
        for s in imposter_scores:
            writer.writerow(["imposter", s])

    print("✅ Similarity testing completed.")
    print(f"Genuine samples: {len(genuine_scores)}")
    print(f"Imposter samples: {len(imposter_scores)}")

if __name__ == "__main__":
    main()
