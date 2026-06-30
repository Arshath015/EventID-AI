import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
STORAGE_BUCKET = "id_photos"
MODEL_NAME = "ArcFace"
VERIFICATION_THRESHOLD = 0.50


def has_required_config():
    return bool(SUPABASE_URL and SUPABASE_KEY)
