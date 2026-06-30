import urllib.request
import cv2
import numpy as np
import streamlit as st
from services.biometric_service import bio_engine
from services.supabase_service import get_signed_url


@st.cache_data(ttl=120)
def build_knowledge_base():
    """Downloads active users' photos and builds a vector embedding dictionary."""
    from services.supabase_service import supabase

    users = supabase.table("id_cards").select("id, full_name, photo_path").eq("is_active", True).execute().data
    kb = {}

    for user in users:
        url = get_signed_url(user['photo_path'])
        if url:
            try:
                response = urllib.request.urlopen(url)
                image = np.asarray(bytearray(response.read()), dtype="uint8")
                image_bgr = cv2.imdecode(image, cv2.IMREAD_COLOR)
                emb, _ = bio_engine.extract_and_embed(image_bgr, enforce_detection=False)
                if emb is not None:
                    kb[user['id']] = {'name': user['full_name'], 'embedding': emb}
            except Exception:
                pass
    return kb
