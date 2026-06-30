from datetime import datetime
import streamlit as st
from services.supabase_service import fetch_realtime_data, get_signed_url, update_person, delete_person


def page_admin_dashboard():
    st.markdown("## 🌐 Command Center Dashboard")
    st.markdown("<div class='cyber-box'>Real-time global synchronization and identity management matrix.</div>", unsafe_allow_html=True)

    users, verifications, verified_uuids = fetch_realtime_data()

    total_users = len(users)
    active_users = sum(1 for u in users if u["is_active"])
    inactive_users = total_users - active_users
    total_verified = len(verified_uuids)
    pending_users = total_users - total_verified

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TOTAL REG", total_users)
    c2.metric("ACTIVE", active_users)
    c3.metric("INACTIVE", inactive_users)
    c4.metric("VERIFIED", total_verified)
    c5.metric("PENDING", pending_users)

    st.markdown("<br>### 🗃️ Identity Records Matrix", unsafe_allow_html=True)
    search = st.text_input("Query Name or RRN", placeholder="Enter search parameters...")

    for row in users:
        if search and search.lower() not in row["full_name"].lower() and search not in row["rrn"]:
            continue

        status_color = "🟢 ACTIVE" if row["is_active"] else "🔴 INACTIVE"
        verif_status = "✅ VERIFIED" if row["id"] in verified_uuids else "⏳ PENDING"

        with st.expander(f"{status_color} | {verif_status} | {row['full_name']} ({row['rrn']})"):
            st.markdown("<div class='cyber-box'>", unsafe_allow_html=True)
            col_img, col_data, col_logs = st.columns([1, 2, 2])

            with col_img:
                url = get_signed_url(row["photo_path"], 60)
                if url:
                    st.image(url, width=150)

            with col_data:
                st.markdown(f"**UUID:** `{row['id']}`")
                u_name = st.text_input("Name", row["full_name"], key=f"n_{row['id']}")
                u_rrn = st.text_input("RRN", row["rrn"], key=f"r_{row['id']}")
                u_dept = st.text_input("Dept", row["department"], key=f"d_{row['id']}")
                u_phone = st.text_input("Phone", row["phone"], key=f"p_{row['id']}")
                u_email = st.text_input("Email", row["email"], key=f"e_{row['id']}")
                u_active = st.checkbox("Account Active", row["is_active"], key=f"a_{row['id']}")

                cu, cd = st.columns(2)
                if cu.button("UPDATE PERSON", key=f"u_{row['id']}"):
                    update_person(row["id"], {
                        "full_name": u_name,
                        "rrn": u_rrn,
                        "department": u_dept,
                        "phone": u_phone,
                        "email": u_email,
                        "is_active": u_active,
                        "updated_at": datetime.utcnow().isoformat(),
                    })
                    st.rerun()

                if cd.button("DELETE PERSON", key=f"del_{row['id']}"):
                    delete_person(row["id"])
                    st.rerun()

            with col_logs:
                st.markdown("**User Verification Logs:**")
                user_logs = [v for v in verifications if v.get("card_id") == row["id"]]

                if not user_logs:
                    st.info("No verification logs found for this user.")
                else:
                    log_html = "<div style='height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; color: #a1dcf1;'>"
                    for lg in sorted(user_logs, key=lambda x: str(x.get("created_at", "")), reverse=True):
                        timestamp = str(lg.get("created_at", "Unknown Time"))[:19]
                        result = lg.get("result", "Unknown")
                        note = lg.get("note", "N/A")
                        log_html += f"<div>[{timestamp}] Result: <b>{result}</b><br>Note: {note}</div><hr style='border-color: #007b80; margin: 5px 0;'>"
                    log_html += "</div>"
                    st.markdown(log_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
