import time
import streamlit as st
from supabase import ClientOptions, create_client
from config import SUPABASE_URL, SUPABASE_KEY, STORAGE_BUCKET


@st.cache_resource
def get_supabase_client():
    """Initializes Supabase Client with proper ClientOptions to fix the dict error."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    try:
        opts = ClientOptions(postgrest_client_timeout=30)
        return create_client(SUPABASE_URL, SUPABASE_KEY, options=opts)
    except Exception:
        return None


supabase = get_supabase_client()


def has_supabase_connection():
    return supabase is not None


def get_signed_url(photo_path, ttl=3600):
    if not photo_path or not has_supabase_connection():
        return None

    for _ in range(3):
        try:
            res = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(photo_path, ttl)
            return res.get("signedURL")
        except Exception:
            time.sleep(0.5)
    return None


def fetch_realtime_data():
    if not has_supabase_connection():
        return [], [], set()

    try:
        users = supabase.table("id_cards").select("*").execute().data
        verifications = supabase.table("verifications").select("*").execute().data
        verified_uuids = {v["card_id"] for v in verifications if v["result"] == "success"}
        return users, verifications, verified_uuids
    except Exception:
        return [], [], set()


def insert_registration(payload):
    if not has_supabase_connection():
        return []
    try:
        return supabase.table("id_cards").insert(payload).execute().data
    except Exception:
        return []


def update_person(record_id, payload):
    if not has_supabase_connection():
        return None
    try:
        return supabase.table("id_cards").update(payload).eq("id", record_id).execute()
    except Exception:
        return None


def delete_person(record_id):
    if not has_supabase_connection():
        return None
    try:
        return supabase.table("id_cards").delete().eq("id", record_id).execute()
    except Exception:
        return None


def insert_verification(payload):
    if not has_supabase_connection():
        return None
    try:
        return supabase.table("verifications").insert(payload).execute()
    except Exception:
        return None


def get_existing_person(email, rrn):
    if not has_supabase_connection():
        return []
    try:
        return supabase.table("id_cards").select("id").or_(f"email.eq.{email},rrn.eq.{rrn}").execute().data
    except Exception:
        return []


def upload_photo(img_bytes, file_path):
    if not has_supabase_connection():
        return None
    try:
        return supabase.storage.from_(STORAGE_BUCKET).upload(file=img_bytes, path=file_path, file_options={"content-type": "image/jpeg"})
    except Exception:
        return None


def get_existing_verification(card_id):
    if not has_supabase_connection():
        return []
    try:
        return supabase.table("verifications").select("id").eq("card_id", card_id).eq("result", "success").execute().data
    except Exception:
        return []
