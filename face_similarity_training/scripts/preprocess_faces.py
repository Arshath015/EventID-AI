import sys
from pathlib import Path

# ---- required to access config.py ----
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import *

import cv2
import os
from mtcnn import MTCNN
from tqdm import tqdm

detector = MTCNN()

def process_folder(input_dir, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    for person_id in tqdm(os.listdir(input_dir), desc=f"Processing {input_dir.name}"):
        person_path = input_dir / person_id
        if not person_path.is_dir():
            continue

        save_person_dir = output_dir / person_id
        save_person_dir.mkdir(exist_ok=True)

        for img_name in os.listdir(person_path):
            img_path = person_path / img_name
            img = cv2.imread(str(img_path))

            if img is None:
                continue

            try:
                faces = detector.detect_faces(img)
            except Exception:
                # Skip images that break MTCNN internally
                continue

            if not faces:
                continue

            x, y, w, h = faces[0]["box"]

            # Ensure valid bounding box
            if w <= 0 or h <= 0:
                continue

            x, y = max(0, x), max(0, y)
            face = img[y:y+h, x:x+w]

            if face is None or face.size == 0:
                continue

            # Skip very small faces (important!)
            if face.shape[0] < 50 or face.shape[1] < 50:
                continue

            face = cv2.resize(face, (112, 112))
            cv2.imwrite(str(save_person_dir / img_name), face)

def main():
    train_dir = RAW_DATA_DIR / "vggface2" / "versions" / "1" / "train"
    val_dir = RAW_DATA_DIR / "vggface2" / "versions" / "1" / "val"

    aligned_train_dir = ALIGNED_DIR / "train"
    aligned_val_dir = ALIGNED_DIR / "val"

    print("Preprocessing TRAIN images...")
    process_folder(train_dir, aligned_train_dir)

    print("Preprocessing VAL images...")
    process_folder(val_dir, aligned_val_dir)

    print("✅ Face preprocessing completed successfully.")


if __name__ == "__main__":
    main()
