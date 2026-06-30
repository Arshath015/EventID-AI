import time
import cv2
import numpy as np
import streamlit as st
from services.biometric_service import bio_engine
from services.qr_service import decode_qr
from services.supabase_service import get_existing_verification, insert_verification
from services.knowledge_service import build_knowledge_base
from config import VERIFICATION_THRESHOLD
from ui.theme import render_terminal_logs


def page_auto_kiosk():
    st.markdown("## 👁️ Advanced Security Kiosk")
    st.markdown("<div class='cyber-box'>Continuous Scanning Active. Step 1: Scan QR. Step 2: Face Cross-Check.</div>", unsafe_allow_html=True)

    if "sys_logs" not in st.session_state:
        st.session_state.sys_logs = ["SYSTEM BOOT INITIALIZED", "WAITING FOR START COMMAND..."]

    col_btn, col_warn = st.columns([1, 3])

    if not st.session_state.get("kiosk_running", False):
        if col_btn.button("▶ START KIOSK"):
            st.session_state.kiosk_running = True
            st.session_state.sys_logs.append("KIOSK LOOP INITIATED.")
            st.rerun()
        col_warn.info("System Offline. Click Start to begin loop.")
        return

    if col_btn.button("🛑 STOP KIOSK"):
        st.session_state.kiosk_running = False
        st.session_state.sys_logs.append("KIOSK HALTED BY ADMIN.")
        st.rerun()
    col_warn.warning("⚠️ Kiosk is currently utilizing the camera. Stop Kiosk before switching tabs.")

    with st.spinner("SYNCHRONIZING VECTOR KNOWLEDGE BASE..."):
        kb = build_knowledge_base()

    col_vid, col_term = st.columns([2, 1])
    st_frame = col_vid.empty()
    st_term = col_term.empty()

    cap = cv2.VideoCapture(0)
    time.sleep(1.0)

    state = "INIT"
    state_start_time = time.time()

    target_uuid = None
    target_name = None
    target_emb = None

    def update_terminal():
        st_term.markdown(render_terminal_logs(st.session_state.sys_logs), unsafe_allow_html=True)

    while st.session_state.kiosk_running:
        ret, frame = cap.read()

        if not ret or frame is None:
            st.session_state.sys_logs.append("WARNING: CAMERA SIGNAL LOST. RECONNECTING...")
            update_terminal()
            cap.release()
            time.sleep(1.0)
            cap = cv2.VideoCapture(0)
            continue

        frame = cv2.flip(frame, 1)
        display_frame = frame.copy()
        h, w, _ = display_frame.shape

        COLOR_CYAN = (255, 255, 0)
        COLOR_GREEN = (0, 255, 0)
        COLOR_RED = (0, 0, 255)
        COLOR_YELLOW = (0, 255, 255)

        cv2.rectangle(display_frame, (0, 0), (w, h), COLOR_CYAN, 2)
        scan_y = int((time.time() * 200) % h)
        cv2.line(display_frame, (0, scan_y), (w, scan_y), COLOR_CYAN, 1)

        np.random.seed(int(time.time() * 5) % (2**32 - 1))
        for i in range(12):
            col_x = 30 + i * (w // 12)
            for j in range(6):
                row_y = (int(time.time() * 100) + j * 50 + i * 40) % h
                val = f"{np.random.randint(0, 4095):03X}"
                cv2.putText(display_frame, val, (col_x, row_y), cv2.FONT_HERSHEY_PLAIN, 0.8, (100, 100, 0), 1, cv2.LINE_AA)

        sys_str = f"CORE.MEM: {np.random.randint(1000,9999)} TB/s | UPLINK: STABLE"
        cv2.putText(display_frame, sys_str, (10, h - 15), cv2.FONT_HERSHEY_PLAIN, 1.0, COLOR_CYAN, 1, cv2.LINE_AA)

        elapsed = time.time() - state_start_time

        if state == "INIT":
            cv2.putText(display_frame, "SYSTEM READY", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_CYAN, 2)
            cv2.putText(display_frame, "PRESENT SECURE QR CREDENTIAL", (w // 2 - 250, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            if elapsed > 1.5:
                state = "QR_SCAN"
                state_start_time = time.time()
                st.session_state.sys_logs.append("ACTIVATING QR SCANNER...")

        elif state == "QR_SCAN":
            cv2.putText(display_frame, "AWAITING QR CODE...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_CYAN, 2)
            cx, cy = w // 2, h // 2
            cv2.rectangle(display_frame, (cx - 100, cy - 100), (cx + 100, cy + 100), COLOR_CYAN, 2)

            qr_data = decode_qr(frame)
            if qr_data:
                if qr_data in kb:
                    target_uuid = qr_data
                    target_name = kb[qr_data]["name"]
                    target_emb = kb[qr_data]["embedding"]
                    st.session_state.sys_logs.append(f"VALID QR DETECTED: {target_name}")
                    state = "FACE_SCAN_INIT"
                    state_start_time = time.time()
                else:
                    st.session_state.sys_logs.append("INVALID QR: Identity not found in Database.")
                    state = "RESULT_INVALID_QR"
                    state_start_time = time.time()

        elif state == "FACE_SCAN_INIT":
            cv2.putText(display_frame, f"WELCOME {target_name}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_GREEN, 2)
            cv2.putText(display_frame, "PLEASE LOOK AT THE CAMERA", (w // 2 - 220, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            if elapsed > 2.0:
                state = "FACE_SCAN"
                state_start_time = time.time()
                st.session_state.sys_logs.append("INITIATING FACIAL CROSS-CHECK...")

        elif state == "FACE_SCAN":
            cv2.putText(display_frame, "CROSS-CHECKING BIOMETRICS...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_CYAN, 2)
            cx, cy = w // 2, h // 2
            cv2.circle(display_frame, (cx, cy), 150, COLOR_CYAN, 1)

            emb, box = bio_engine.extract_and_embed(frame, enforce_detection=False)
            if emb is not None and box is not None:
                fx, fy, fw, fh = box["x"], box["y"], box["w"], box["h"]
                cv2.rectangle(display_frame, (fx, fy), (fx + fw, fy + fh), COLOR_GREEN, 2)

                sim = np.dot(emb, target_emb)
                if sim > VERIFICATION_THRESHOLD:
                    st.session_state.sys_logs.append(f"FACE CROSS-CHECK PASSED (Sim: {sim:.2f})")
                    state = "VALIDATE"
                    state_start_time = time.time()
                else:
                    cv2.putText(display_frame, "IDENTITY MISMATCH", (fx, fy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLOR_RED, 2)
                    if elapsed > 5.0:
                        st.session_state.sys_logs.append("CRITICAL: BIOMETRIC CROSS-CHECK FAILED.")
                        state = "RESULT_MISMATCH"
                        state_start_time = time.time()

            elif elapsed > 8.0:
                st.session_state.sys_logs.append("TIMEOUT: No face detected.")
                state = "INIT"
                state_start_time = time.time()

        elif state == "VALIDATE":
            cv2.putText(display_frame, "VALIDATING ENCRYPTION & ACCESS...", (w // 2 - 250, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, COLOR_YELLOW, 2)
            st_frame.image(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB), channels="RGB")
            update_terminal()
            time.sleep(1.0)

            prior = get_existing_verification(target_uuid)
            if prior:
                st.session_state.ai_report = "Duplicate Detected – Entry Denied"
            else:
                st.session_state.ai_report = "New Entry Detected – Access Granted"
                insert_verification({"card_id": target_uuid, "result": "success"})

            st.session_state.sys_logs.append(st.session_state.ai_report)
            state = "RESULT"
            state_start_time = time.time()

        elif state in ["RESULT", "RESULT_INVALID_QR", "RESULT_MISMATCH"]:
            if state == "RESULT":
                report = st.session_state.ai_report
                color = COLOR_GREEN if "Granted" in report else COLOR_RED
            elif state == "RESULT_INVALID_QR":
                report = "INVALID OR UNRECOGNIZED QR CODE"
                color = COLOR_RED
            else:
                report = "BIOMETRIC MISMATCH - ENTRY DENIED"
                color = COLOR_RED

            cv2.rectangle(display_frame, (50, h // 2 - 60), (w - 50, h // 2 + 60), (0, 0, 0), -1)
            cv2.rectangle(display_frame, (50, h // 2 - 60), (w - 50, h // 2 + 60), color, 2)
            cv2.putText(display_frame, "AI DECISION REPORT", (70, h // 2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(display_frame, report, (70, h // 2 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            if elapsed > 4.0:
                target_uuid, target_name, target_emb = None, None, None
                st.session_state.sys_logs.append("RESETTING KIOSK FOR NEXT SUBJECT...")
                state = "INIT"
                state_start_time = time.time()

        st_frame.image(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB), channels="RGB")
        update_terminal()
        time.sleep(0.05)

    cap.release()
