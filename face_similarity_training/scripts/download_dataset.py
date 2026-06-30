import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import *

import kagglehub
from config import RAW_DATA_DIR

path = kagglehub.dataset_download("hearfool/vggface2")

print("Dataset downloaded at:", path)
print("Move dataset into:", RAW_DATA_DIR)
