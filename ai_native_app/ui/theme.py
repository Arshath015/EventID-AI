import streamlit as st
from datetime import datetime


def apply_theme():
    st.set_page_config(page_title="JARVIS // Secure Identity", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(
        """
        <style>
            /* Main Background & Text */
            .stApp { background-color: #03080c; color: #00f3ff; font-family: 'Courier New', Courier, monospace; }
            h1, h2, h3, h4, h5, h6 { color: #00f3ff !important; font-family: 'Courier New', Courier, monospace; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 10px #00f3ff; }
            p, span, div, label { color: #a1dcf1; }

            /* Neon Tabs & Navigation */
            .stTabs [data-baseweb="tab-list"] { background-color: #010406; border-radius: 5px; border-bottom: 1px solid #007b80; padding: 10px 10px 0px 10px; }
            .stTabs [data-baseweb="tab"] { color: #007b80; padding-right: 20px; padding-left: 20px; font-weight: bold; }
            .stTabs [aria-selected="true"] { color: #00f3ff !important; border-bottom: 2px solid #00f3ff !important; text-shadow: 0 0 10px #00f3ff; }

            /* Neon Buttons */
            .stButton>button {
                border: 1px solid #00f3ff; color: #00f3ff; background-color: rgba(0, 243, 255, 0.05);
                transition: all 0.3s ease; border-radius: 2px; font-weight: bold; text-transform: uppercase;
                box-shadow: inset 0 0 5px #00f3ff; width: 100%;
            }
            .stButton>button:hover {
                background-color: #00f3ff; color: #03080c; box-shadow: 0 0 15px #00f3ff, inset 0 0 10px #03080c;
            }

            /* Inputs */
            .stTextInput>div>div>input {
                background-color: rgba(0, 243, 255, 0.02); color: #00f3ff; border: 1px solid #007b80;
                font-family: 'Courier New', monospace; box-shadow: inset 0 0 5px #007b80;
            }

            /* Metrics */
            .stMetric .metric-value { color: #00f3ff !important; text-shadow: 0 0 10px #00f3ff; }
            .stMetric .metric-label { color: #007b80 !important; }

            /* Alerts & Custom Cyber Box */
            .stAlert { background-color: rgba(0, 243, 255, 0.05); border: 1px solid #00f3ff; color: #00f3ff; }
            .cyber-box {
                border: 1px solid #00f3ff; background: rgba(0, 243, 255, 0.03); padding: 15px; margin-bottom: 15px;
                box-shadow: 0 0 10px rgba(0, 243, 255, 0.2), inset 0 0 10px rgba(0, 243, 255, 0.1);
                position: relative;
            }
            .cyber-box::before { content: ''; position: absolute; top: -2px; left: -2px; width: 10px; height: 10px; border-top: 2px solid #00f3ff; border-left: 2px solid #00f3ff; }
            .cyber-box::after { content: ''; position: absolute; bottom: -2px; right: -2px; width: 10px; height: 10px; border-bottom: 2px solid #00f3ff; border-right: 2px solid #00f3ff; }

            /* System Terminal Logs */
            .terminal-log {
                background-color: #010406; border: 1px solid #007b80; padding: 10px; height: 300px;
                overflow-y: auto; font-family: 'Courier New', monospace; font-size: 14px; color: #00f3ff;
                box-shadow: inset 0 0 10px #000;
            }
            .terminal-line { margin: 2px 0; border-bottom: 1px solid rgba(0, 243, 255, 0.1); padding-bottom: 2px;}
            .status-granted { color: #00ff00; text-shadow: 0 0 5px #00ff00; font-weight: bold;}
            .status-denied { color: #ff003c; text-shadow: 0 0 5px #ff003c; font-weight: bold;}
            .status-warn { color: #ffb700; text-shadow: 0 0 5px #ffb700; font-weight: bold;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_terminal_logs(logs):
    """Generates the HTML for the cyber terminal logs."""
    html = "<div class='terminal-log'>"
    for log in reversed(logs[-30:]):
        timestamp = datetime.now().strftime("%H:%M:%S")
        css_class = ""
        if "Granted" in log or "SUCCESS" in log:
            css_class = "status-granted"
        elif "Denied" in log or "CRITICAL" in log or "Mismatch" in log or "INVALID" in log:
            css_class = "status-denied"
        elif "Duplicate" in log or "WARNING" in log:
            css_class = "status-warn"

        html += f"<div class='terminal-line'>[{timestamp}] SYS: <span class='{css_class}'>{log}</span></div>"
    html += "</div>"
    return html
