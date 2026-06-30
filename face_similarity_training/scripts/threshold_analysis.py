import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import *

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(RESULTS_DIR / "similarity_scores.csv")

genuine = df[df["type"] == "genuine"]["similarity"]
imposter = df[df["type"] == "imposter"]["similarity"]

plt.figure(figsize=(8, 5))
plt.hist(genuine, bins=50, alpha=0.7, label="Genuine")
plt.hist(imposter, bins=50, alpha=0.7, label="Imposter")
plt.axvline(0.75, color="red", linestyle="--", label="Threshold = 0.75")
plt.xlabel("Cosine Similarity")
plt.ylabel("Frequency")
plt.title("Face Similarity Score Distribution")
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS_DIR / "threshold_plot.png")
plt.show()

print("✅ Threshold analysis completed.")
