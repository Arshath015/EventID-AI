import uuid
import cv2
import numpy as np
import streamlit as st
from services.biometric_service import bio_engine
from services.qr_service import generate_qr
from services.email_service import send_qr_email
from services.supabase_service import get_existing_person, insert_registration, upload_photo


def page_register_person():
    st.markdown("## 👤 Register New Person")
    st.markdown("<div class='cyber-box'>Input subject metadata and establish biometric baseline.</div>", unsafe_allow_html=True)

    if "reg_camera_active" not in st.session_state:
        st.session_state.reg_camera_active = False

    if not st.session_state.reg_camera_active:
        st.warning("⚠️ Hardware Lock: Camera is currently sleeping to prevent conflict with the Auto-Scan Kiosk.")
        if st.button("📸 ACTIVATE REGISTRATION CAMERA"):
            st.session_state.reg_camera_active = True
            st.rerun()
        return

    if st.button("🛑 DEACTIVATE CAMERA (Click this before switching to Kiosk)"):
        st.session_state.reg_camera_active = False
        st.rerun()

    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        full_name = col1.text_input("Full Legal Name")
        rrn = col1.text_input("Registration ID / RRN")
        department = col2.text_input("Department / Clearances")
        phone = col2.text_input("Secure Comm Number")
        email = st.text_input("Secure Email (For QR Dispatch)")

        st.markdown("### 📷 Biometric Acquisition")
        st.info("PROTOCOL: Look directly at the camera. Ensure face is centered and well-lit.")
        img_buffer = st.camera_input("Acquire Biometrics")

        submitted = st.form_submit_button("REGISTER PERSON")

    if submitted:
        if not all([full_name, rrn, department, phone, email, img_buffer]):
            st.error("SYSTEM ERROR: All fields and biometric scan are mandatory.")
            return

        exists = get_existing_person(email, rrn)
        if exists:
            st.error("CONFLICT: RRN or Email already exists in the mainframe.")
            return

        img_bytes = img_buffer.getvalue()
        cv_img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        emb, box = bio_engine.extract_and_embed(cv_img, enforce_detection=True)

        if emb is None:
            st.error("BIOMETRIC REJECTION: Facial geometry unreadable. Ensure direct frontal angle and proper lighting.")
            return

        with st.spinner("ENCRYPTING AND UPLOADING SUBJECT DATA..."):
            file_path = f"photos/{uuid.uuid4()}.jpg"
            upload_photo(img_bytes, file_path)
            res = insert_registration({
                "full_name": full_name,
                "rrn": rrn,
                "department": department,
                "phone": phone,
                "email": email,
                "photo_path": file_path,
                "is_active": True,
            })

            card_id = res[0]["id"]
            qr_buf = generate_qr(card_id)
            send_qr_email(email, full_name, qr_buf.getvalue())

            st.success(f"✅ REGISTRATION COMPLETE. UUID: {card_id}")
            st.image(qr_buf.getvalue(), width=200)
