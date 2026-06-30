import sys
from pathlib import Path

# ---- access config.py ----
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import *

import cv2
import numpy as np
from deepface import DeepFace
from tqdm import tqdm
import os

EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

def generate_embeddings(split_name):
    input_dir = ALIGNED_DIR / split_name
    embeddings = []

    for person_id in tqdm(os.listdir(input_dir), desc=f"Embedding {split_name}"):
        person_dir = input_dir / person_id
        if not person_dir.is_dir():
            continue

        for img_name in os.listdir(person_dir):
            img_path = person_dir / img_name

            try:
                embedding = DeepFace.represent(
                    img_path=str(img_path),
                    model_name="ArcFace",
                    detector_backend="retinaface",
                    enforce_detection=False
                )[0]["embedding"]

                embeddings.append({
                    "person_id": person_id,
                    "image": img_name,
                    "embedding": np.array(embedding)
                })

            except Exception:
                continue

    np.save(EMBEDDINGS_DIR / f"{split_name}_embeddings.npy", embeddings)
    print(f"Saved {split_name} embeddings.")

def main():
    generate_embeddings("train")
    generate_embeddings("val")
    print("✅ Embedding generation completed successfully (DeepFace).")

if __name__ == "__main__":
    main()
