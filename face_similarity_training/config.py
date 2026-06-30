from pathlib import Path

# =========================
# Base Directory
# =========================
BASE_DIR = Path(__file__).resolve().parent
# BASE_DIR -> app/face_similarity_training

# =========================
# Data Directories
# =========================
DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

ALIGNED_DIR = PROCESSED_DATA_DIR / "aligned_faces"
EMBEDDINGS_DIR = PROCESSED_DATA_DIR / "embeddings"

# =========================
# Model Directory
# =========================
MODELS_DIR = BASE_DIR / "models"

# =========================
# Results Directory
# =========================
RESULTS_DIR = BASE_DIR / "results"

# =========================
# Create Required Folders
# =========================
for path in [
    RAW_DATA_DIR,
    ALIGNED_DIR,
    EMBEDDINGS_DIR,
    MODELS_DIR,
    RESULTS_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)
