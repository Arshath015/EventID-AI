import streamlit as st
from config import has_required_config
from pages.register_page import page_register_person
from pages.dashboard_page import page_admin_dashboard
from pages.kiosk_page import page_auto_kiosk
from ui.theme import apply_theme


def main():
    apply_theme()

    if not has_required_config():
        st.error("SYSTEM HALT: Supabase credentials missing. Check .env configuration.")
        st.stop()

    st.markdown("<h1 style='text-align: center;'>SENTINEL // IDENTITY MATRIX</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Register Person", "Command Center", "Auto-Scan Kiosk"])

    with tab1:
        page_register_person()
    with tab2:
        page_admin_dashboard()
    with tab3:
        page_auto_kiosk()


if __name__ == "__main__":
    main()
