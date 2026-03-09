import sys
import os
import uuid
import json
import time
import sqlite3
import pandas as pd
import streamlit as st
from ui.pdf_utils import pdf_from_report
from pathlib import Path

# -------------------------------------------------
# Path Setup for Imports
# -------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
rag_agents_dir = os.path.join(root_dir, "agents", "rag_agents")

if root_dir not in sys.path:
    sys.path.append(root_dir)
if rag_agents_dir not in sys.path:
    sys.path.append(rag_agents_dir)

# -------------------------------------------------
# Imports
# -------------------------------------------------
try:
    from agents.agent_graph import app as main_app
    from langgraph.types import Command
    from agents.rag_agents.rag_graph import rag_app
except ImportError:
    pass

# -------------------------------------------------
# Config & Global Styling (Fixed Navbar)
# -------------------------------------------------
st.set_page_config(page_title="AI Invoice Auditor", layout="wide", page_icon="🛡️", initial_sidebar_state="expanded")

def apply_custom_ui():
    st.markdown("""
        <style>
        :root {
            --bg-surface: #fff1f5;
            --bg-panel: #ffe4e8;
            --text-main: #2b1b23;
            --text-muted: #7a4b5a;
            --brand: #e11d48;
            --brand-strong: #be123c;
            --accent: #f97316;
            --border-soft: #f8b4c0;
            --shadow-soft: 0 12px 20px rgba(43, 27, 35, 0.08);
            --retro-glow: 0 0 14px rgba(225, 29, 72, 0.22);
            --retro-font: "Courier New", "Lucida Console", Monaco, monospace;
        }
        /* Keep default header visible so Streamlit's sidebar toggle works */
        /* Fixed Top Navbar */
        .fixed-navbar {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 60px;
            background: linear-gradient(90deg, #ffe4e8 0%, #ffd6e0 60%, #ffeef2 100%);
            border-bottom: 1px solid var(--border-soft);
            z-index: 999;
            display: flex;
            align-items: center;
            padding: 0 2rem;
            box-shadow: var(--shadow-soft);
        }
        .nav-logo { font-size: 1.6rem; margin-right: 12px; filter: drop-shadow(0 0 6px rgba(225,29,72,0.35)); }
        .nav-title { font-size: 1.25rem; font-weight: 700; color: var(--text-main); letter-spacing: 1.2px; text-transform: uppercase; font-family: var(--retro-font); }
        
        /* Main Content Offset */
        .main .block-container {
            padding-top: 5rem !important;
            background:
                radial-gradient(circle at top, rgba(225,29,72,0.12) 0%, rgba(255,241,245,0.92) 55%),
                repeating-linear-gradient(0deg, rgba(225,29,72,0.05) 0px, rgba(225,29,72,0.05) 1px, transparent 1px, transparent 56px),
                var(--bg-surface);
        }

        /* Ensure the whole app uses the pink surface */
        html, body, [data-testid="stApp"] {
            background: var(--bg-surface);
        }

        /* Sidebar Navigation Buttons */
        div[data-testid="stSidebarUserContent"] .stButton > button {
            width: 100%;
            text-align: left;
            background-color: transparent;
            border: 1px solid transparent;
            padding: 10px 16px;
            color: var(--text-main);
            border-radius: 8px;
            display: block;
        }
        div[data-testid="stSidebarUserContent"] .stButton > button:hover {
            background-color: rgba(225, 29, 72, 0.12);
            color: var(--brand);
            border-color: rgba(225, 29, 72, 0.35);
            box-shadow: var(--retro-glow);
        }

        /* Section Labels in Sidebar */
        .sidebar-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-muted);
            margin: 20px 0 10px 16px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Cards and tables */
        div[data-testid="stMetric"] {
            background: var(--bg-panel);
            border: 1px solid var(--border-soft);
            border-radius: 12px;
            padding: 12px 16px;
            box-shadow: var(--shadow-soft);
        }
        div[data-testid="stMetric"] > div {
            color: var(--text-main);
        }
        .stDataFrame, .stTable {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-soft);
        }
        button[kind="primary"] {
            background: linear-gradient(90deg, var(--brand) 0%, var(--accent) 100%);
            border: none;
            box-shadow: var(--retro-glow);
        }
        button[kind="primary"]:hover {
            background: linear-gradient(90deg, var(--brand-strong) 0%, #0284c7 100%);
        }

        /* Light retro theme text + sidebar */
        section[data-testid="stSidebar"] {
            background: #ffe4e8;
            border-right: 1px solid var(--border-soft);
        }
        .stMarkdown, .stCaption, .stText, .stHeader, .stSubheader {
            color: var(--text-main);
            font-family: var(--retro-font);
        }
        </style>

        <div class="fixed-navbar">
            <span class="nav-logo">🛡️</span>
            <div class="nav-title">AI Invoice Auditor</div>
        </div>
    """, unsafe_allow_html=True)

apply_custom_ui()

# -------------------------------------------------
# State & Data Helpers
# -------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

REPORTS_DIR = os.path.join("data", "reports")

def load_reports():
    reports = []
    if os.path.exists(REPORTS_DIR):
        files = sorted([f for f in os.listdir(REPORTS_DIR) if f.endswith(".json")])
        for file in files:
            try:
                with open(os.path.join(REPORTS_DIR, file)) as f:
                    data = json.load(f)
                    data["_filename"] = file 
                    reports.append(data)
            except: continue
    return reports

def get_pending_interrupts():
    try:
        conn = sqlite3.connect("checkpoints.sqlite", timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
        if not cursor.fetchone():
            conn.close()
            return []
        cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
        threads = [row[0] for row in cursor.fetchall()]
        conn.close()
    except: return []
    
    pending = []
    interrupt_nodes = ["data_validation_interrupt_node", "business_validation_interrupt_node"]
    if 'main_app' not in globals(): return []

    for tid in threads:
        config = {"configurable": {"thread_id": tid}}
        try:
            state = main_app.get_state(config)
        except Exception:
            continue
        if state.next and any(node in state.next for node in interrupt_nodes):
            pending.append((tid, state))
    return pending


reports_data = load_reports()
# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
import streamlit.components.v1 as components

# --- SIDEBAR LOGIC ---
with st.sidebar:
    st.markdown('<div class="sidebar-label" style="font-weight:bold; margin-bottom:10px;">Main Menu</div>', unsafe_allow_html=True)
    
    # Initialize session state if not present
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    if st.button("📊 Dashboard", use_container_width=True): 
        st.session_state.page = "Dashboard"
    if st.button("⚖️ Review Queue", use_container_width=True): 
        st.session_state.page = "Review"
    if st.button("💬 AI Assistant", use_container_width=True): 
        st.session_state.page = "Chat"

    if st.session_state.get("page") == "Chat":
        st.divider()
        st.markdown('<div class="sidebar-label">Processed Files</div>', unsafe_allow_html=True)
        
        
        if 'reports_data' not in globals() and 'reports_data' not in locals():
            st.caption("No files processed yet.")
        else:
            for idx, report in enumerate(reports_data):
                invoice_details = report.get("invoice_details", {})
                header = invoice_details.get("header", invoice_details)
                inv_id = invoice_details.get("invoice_no") or header.get("invoice_no") or "No Invoice Number"
                vendor = invoice_details.get("vendor_id") or header.get("vendor_id") or "Unknown Vendor"
                
                with st.expander(f"📄 {inv_id}"):
                    st.caption(f"**Vendor:** {vendor}")
                    st.caption(f"**Verdict:** {report.get('final_verdict', 'N/A')}")
                    human_verdict = report.get("human_verdict")
                    if human_verdict:
                        st.caption(f"**Human Verdict:** {str(human_verdict).upper()}")
                    human_remarks = report.get("human_remarks")
                    if human_remarks:
                        if isinstance(human_remarks, list):
                            remarks_text = "; ".join(str(r) for r in human_remarks if r)
                        else:
                            remarks_text = str(human_remarks)
                        if remarks_text.strip():
                            st.caption(f"**Human Remarks:** {remarks_text}")
                    try:
                        pdf_bytes = pdf_from_report(report)
                        st.download_button(
                            "⬇️ Download PDF",
                            data=pdf_bytes,
                            file_name=f"{inv_id}_report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.caption(f"PDF unavailable: {e}")
                    if st.button("Query File", key=f"q_{inv_id}_{idx}", use_container_width=True):
                        st.session_state.chat_query = f"Tell me about invoice {inv_id}"

# --- MAIN CONTENT ---
# st.title(f"Current Page: {st.session_state.page}")
# -------------------------------------------------
# MAIN CONTENT
# -------------------------------------------------


# --- 1. DASHBOARD ---
if st.session_state.page == "Dashboard":
    st.header("AI audit dashboard")
    if reports_data:
        total_invoices = len(reports_data)
        total_val = sum(
            float(
                (r.get("invoice_details", {}).get("header") or r.get("invoice_details", {})).get("total_amount")
                or 0
            )
            for r in reports_data
        )
        approved = sum(
            1
            for r in reports_data
            if str(r.get("final_verdict") or "").strip().lower() == "accept"
        )
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Processed", total_invoices)
        m2.metric("Total Volume", f"${total_val:,.2f}")
        m3.metric("Approved", approved)
        m4.metric("Success Rate", f"{(approved/total_invoices)*100:.1f}%")

        st.divider()
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Invoice History")
            rows = []
            for r in reports_data:
                invoice_details = r.get("invoice_details", {})
                header = invoice_details.get("header", invoice_details)
                rows.append({
                    "Date": header.get("invoice_date"),
                    "Vendor": header.get("vendor_id"),
                    "ID": header.get("invoice_no"),
                    "Amount": header.get("total_amount"),
                    "Status": (r.get("final_verdict") or "unknown").upper(),
                    "Human Verdict": (r.get("human_verdict") or "N/A").upper(),
                    "Human Remarks": (
                        "; ".join(r for r in (r.get("human_remarks") or []) if r)
                        if isinstance(r.get("human_remarks"), list)
                        else (r.get("human_remarks") or "N/A")
                    ),
                })
            st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
        with col2:
            st.subheader("Top Vendors")
            # Extract vendors, filtering out None/Empty values
            vendors = []
            for r in reports_data:
                invoice_details = r.get("invoice_details", {})
                header = invoice_details.get("header", invoice_details)
                vendors.append(header.get("vendor_id"))
            # Convert to Series and drop any nulls
            vendor_series = pd.Series(vendors).dropna()

            if not vendor_series.empty:
                # Count occurrences
                vendor_counts = vendor_series.value_counts().reset_index()
                vendor_counts.columns = ['Vendor', 'Count']
                
                # Using st.bar_chart directly on the counts
                # Or use st.altair_chart for explicit typing to kill the warning
                st.bar_chart(vendor_counts.set_index('Vendor'))
            else:
                st.caption("No vendor data available to chart.")
    else:
        st.info("No data found in reports directory.")

# --- 2. REVIEW QUEUE ---
elif st.session_state.page == "Review":
    st.header("Review Queue")
    pending = get_pending_interrupts()
    if not pending:
        st.success("No invoices currently require manual review.")
    else:
        for tid, state in pending:
            node = state.next[0]
            try:
                interrupt_val = state.tasks[0].interrupts[0].value
            except:
                interrupt_val = {"filename": "N/A", "errors": []}

            with st.container(border=True):
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.subheader(f"📄 {interrupt_val.get('filename')}")
                    st.caption(f"Halted at: `{node}`")
                    errors = interrupt_val.get('errors') or ["No Error was sent"]
                    for e in errors:
                        st.error(e, icon="⚠️")
                with c2:
                    st.write("**Human Action**")
                    choice = st.radio("Decision", ["Approve", "Reject"], key=f"sel_{tid}", horizontal=True)
                    notes = st.text_input("Remarks", key=f"rem_{tid}")
                    if st.button("Submit Decision", key=f"btn_{tid}", type="primary"):
                        if notes:
                            decision = "accept" if choice == "Approve" else "reject"
                            main_app.invoke(
                                Command(resume={"remarks": [notes], "decision": decision}),
                                config={"configurable":{"thread_id": tid}},
                            )
                            st.success("Decision recorded.")
                            time.sleep(1); st.rerun()
                        else: st.warning("Please enter remarks.")

elif st.session_state.page == "Chat":
    st.title("AI Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you analyze your audits today?"}]

    # Chat container: only scrolls when content exceeds height
    chat_container = st.container(height=300)
    for msg in st.session_state.messages:
        chat_container.chat_message(msg["role"]).markdown(msg["content"])

    prompt = st.chat_input("Ask a question about your invoices...")
    if "chat_query" in st.session_state: prompt = st.session_state.pop("chat_query")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        chat_container.chat_message("user").markdown(prompt)

        with chat_container.chat_message("assistant"):
            ans_placeholder = st.empty()
            with st.spinner("Analyzing..."):
                try:
                    if 'rag_app' in globals():
                        result = rag_app.invoke({"query": prompt}, config={"configurable":{"thread_id": "user"}})
                        answer = result.get("answer", "No data found.")
                    else: answer = "RAG Agent offline."
                    
                    # Fix: Ensure markdown is rendered by using markdown() instead of write()
                    full_text = ""
                    for word in answer.split():
                        full_text += word + " "
                        time.sleep(0.02)
                        ans_placeholder.markdown(full_text + "▌")
                    ans_placeholder.markdown(full_text)
                    st.session_state.messages.append({"role": "assistant", "content": full_text})
                except Exception as e:
                    st.error(f"Error: {e}")
