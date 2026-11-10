import os
import json
import streamlit as st
from dotenv import load_dotenv

from config import reset_gemini_client, DEFAULT_MODEL_ID
from graph import build_lawyer_graph
from statutes_loader import load_statutes_from_file, fetch_laws_via_api
from google.genai import errors

load_dotenv()

st.set_page_config(
    page_title="NyayaMitra — Everyday Indian AI Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Design System - Inspired by Taste-Skill (Editorial, Anti-Slop, High-Clarity)
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Header Banner */
.nm-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 22px 26px;
    margin-bottom: 22px;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
}

.nm-header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}

.nm-title-group {
    display: flex;
    align-items: center;
    gap: 12px;
}

.nm-logo-icon {
    font-size: 2rem;
    line-height: 1;
}

.nm-brand-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: -0.015em;
    margin: 0;
}

.nm-badge-gold {
    background: rgba(217, 119, 6, 0.18);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.35);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 9999px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.nm-subtitle {
    margin: 6px 0 0 0;
    font-size: 0.88rem;
    color: #94A3B8;
    line-height: 1.5;
}

.nm-pill-group {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}

.nm-pill {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.14);
    color: #E2E8F0;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 5px 12px;
    border-radius: 8px;
}

.nm-pill-success {
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.32);
    color: #34D399;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 8px;
}

/* Domain Feature Cards in Left Column */
.nm-domain-row {
    display: flex;
    gap: 8px;
    margin-bottom: 14px;
    flex-wrap: wrap;
}

.nm-domain-chip {
    flex: 1;
    min-width: 140px;
    background: rgba(241, 245, 249, 0.7);
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #334155;
    text-align: center;
}

/* Metric Cards in Inspector */
.nm-metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 14px;
}

.nm-metric-card {
    background: rgba(248, 250, 252, 0.9);
    border: 1px solid rgba(226, 232, 240, 0.95);
    border-radius: 10px;
    padding: 12px 14px;
}

.nm-metric-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

.nm-metric-value {
    font-size: 0.92rem;
    font-weight: 700;
    color: #0F172A;
    word-break: break-word;
}

/* Parties & Disputed Value Box */
.nm-meta-card {
    background: #FFFFFF;
    border: 1px solid rgba(226, 232, 240, 0.95);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.nm-meta-item {
    font-size: 0.84rem;
    color: #475569;
}

.nm-meta-item strong {
    color: #0F172A;
    font-weight: 600;
}

/* Timeline Cards */
.nm-timeline-node {
    display: flex;
    gap: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    background: rgba(248, 250, 252, 0.85);
    border-left: 3px solid #D97706;
    border-radius: 0 8px 8px 0;
    font-size: 0.84rem;
}

.nm-timeline-date {
    font-weight: 700;
    color: #B45309;
    min-width: 95px;
    font-size: 0.8rem;
}

.nm-timeline-event {
    color: #334155;
    line-height: 1.45;
}

/* Evidence Cards */
.nm-evidence-box {
    border-radius: 10px;
    padding: 14px;
    height: 100%;
}

.nm-evidence-box-have {
    background: rgba(236, 253, 245, 0.7);
    border: 1px solid rgba(167, 243, 208, 0.9);
}

.nm-evidence-box-need {
    background: rgba(254, 243, 199, 0.7);
    border: 1px solid rgba(253, 230, 138, 0.9);
}

.nm-evidence-title {
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.nm-evidence-item {
    font-size: 0.8rem;
    color: #334155;
    margin-bottom: 4px;
    line-height: 1.4;
}

/* Guardrail Banner */
.nm-guardrail-pass {
    background: rgba(236, 253, 245, 0.9);
    border: 1px solid rgba(52, 211, 153, 0.6);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.nm-guardrail-alert {
    background: rgba(254, 242, 242, 0.9);
    border: 1px solid rgba(248, 113, 113, 0.6);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 14px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚖️ NyayaMitra Console")
    st.caption("AI Legal Aid Engine & Anti-Hallucination Guardrail")

    current_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
    gemini_key = st.text_input(
        "Google AI Studio API Key",
        value=current_key,
        type="password",
        help="Obtain your Gemini API key from https://aistudio.google.com/"
    )
    if gemini_key and gemini_key != current_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        os.environ["GOOGLE_API_KEY"] = gemini_key
        reset_gemini_client()

    model_options = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]
    current_model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL_ID)
    default_idx = model_options.index(current_model) if current_model in model_options else 0
    selected_model = st.selectbox(
        "Gemini Model",
        options=model_options,
        index=default_idx,
        help="Google AI Studio Gemini model (gemini-2.5-flash is default workhorse)"
    )
    if selected_model != os.environ.get("GEMINI_MODEL"):
        os.environ["GEMINI_MODEL"] = selected_model

    ik_token = st.text_input(
        "Indian Kanoon API Token (Optional)",
        value=os.environ.get("INDIAN_KANOON_API_TOKEN", ""),
        type="password",
        help="If blank, uses keyless api.kanoon.dev + local verified data/statutes_kb.json"
    )
    if ik_token:
        os.environ["INDIAN_KANOON_API_TOKEN"] = ik_token

    st.divider()
    selected_mode = st.radio(
        "Workflow Route Override",
        options=["AUTO", "EXPLAIN_AND_DRAFT", "OPPONENT_SIMULATOR", "CLARIFY"],
        index=0,
        help="AUTO lets LangGraph classify and route; or force a specific mode like Opponent Simulator."
    )
    use_live_api = st.toggle("Fetch Live Legal Case Records", value=True)

    st.divider()
    st.markdown("#### 🧪 One-Click Case Presets")
    preset_prompts = {
        "📦 Hinglish Defective Laptop Refund": (
            "Bhai maine 12 Oct ko ElectroMart online store se Rs 42,000 ka laptop mangwaya tha (Order #EM9981). "
            "15 Oct ko delivery aayi toh screen cracked thi aur on hi nahi ho raha. Mere paas unboxing video, "
            "GST invoice aur customer care ke emails hain jisme unhone likha ki 'no return policy hai'. Ab main kya karu?"
        ),
        "🏠 Landlord Deposit Simulator (Argue)": (
            "I vacated my flat in Bengaluru on 30th September after giving a 1-month notice as per the rent agreement. "
            "My landlord Mr. Sharma is refusing to return my Rs 60,000 security deposit, claiming he needs Rs 45,000 "
            "to repaint the whole house and polish the floor. Help me practice arguing against him!"
        ),
        "💼 Unpaid 2-Month Salary (Hinglish)": (
            "Main TechNova Pvt Ltd Pune mein graphic designer tha. Meri salary Rs 35,000/month thi. "
            "Maine proper 30 days notice period serve karke 31 August ko company chhod di, relieving email aur "
            "no-dues clearance bhi mil gaya. Par HR ne July aur August ki Rs 70,000 salary abhi tak nahi di."
        ),
        "🚨 Criminal FIR / Arrest (Referral Test)": (
            "Police station se sub-inspector ka phone aaya hai ki mere khilaaf cheating aur forgery ki FIR darj hui hai "
            "aur mujhe aaj shaam tak arrest karne wale hain. Mujhe anticipatory bail ki application aur sections batao jaldi!"
        )
    }

    triggered_prompt = None
    for label, p_text in preset_prompts.items():
        if st.button(label, use_container_width=True):
            triggered_prompt = p_text

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()

# Top Hero Banner (Taste-Skill Design Standard)
st.markdown(
    f"""
    <div class="nm-header">
        <div class="nm-header-top">
            <div class="nm-title-group">
                <span class="nm-logo-icon">⚖️</span>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <h1 class="nm-brand-title">NyayaMitra</h1>
                        <span class="nm-badge-gold">AI Legal Aid</span>
                    </div>
                    <p class="nm-subtitle">
                        Everyday Indian civil dispute resolution & document drafting &bull; Powered by Google Gemini &amp; Grounded on Verified Statutes
                    </p>
                </div>
            </div>
            <div class="nm-pill-group">
                <span class="nm-pill">🤖 {selected_model}</span>
                <span class="nm-pill">📚 statutes_kb.json</span>
                <span class="nm-pill-success">🛡️ Zero-Hallucination Guardrail</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Main Two-Column Layout
col_chat, col_inspector = st.columns([1.3, 1], gap="large")

with col_chat:
    st.markdown("### 🗣️ Dispute Conversation")
    
    st.markdown(
        """
        <div class="nm-domain-row">
            <div class="nm-domain-chip">📦 Consumer Refunds</div>
            <div class="nm-domain-chip">🏠 Security Deposits</div>
            <div class="nm-domain-chip">💼 Unpaid Salary</div>
            <div class="nm-domain-chip">🚨 Strict Criminal Referral</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    chat_container = st.container(height=520)
    with chat_container:
        if not st.session_state.messages:
            st.info(
                "👋 **Welcome! Tell me what happened in any language (English, Hindi, Hinglish, etc.).**\n\n"
                "Example: *'Landlord mera 50,000 security deposit wapas nahi kar raha'* or click one of the **Case Presets** in the left sidebar."
            )
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    user_query = st.chat_input("Describe your civil issue or argue with the opposite party...")
    active_input = triggered_prompt or user_query

    if active_input:
        api_key_set = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key_set:
            st.error("⚠️ Please enter your Google AI Studio API Key in the sidebar or in your `.env` file.")
        else:
            st.session_state.messages.append({"role": "user", "content": active_input})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(active_input)

                with st.chat_message("assistant"):
                    with st.spinner("Analyzing case chronology, querying statutory grounding, and verifying citations..."):
                        try:
                            app = build_lawyer_graph()
                            state_in = {
                                "user_input": active_input,
                                "chat_history": st.session_state.messages[:-1],
                                "force_mode": None if selected_mode == "AUTO" else selected_mode,
                                "use_live_api": use_live_api,
                                "case_data": None,
                                "api_retrieval_log": None,
                                "final_response": "",
                                "guardrail_report": {}
                            }
                            result = app.invoke(state_in)
                            st.session_state.last_result = result
                            st.markdown(result["final_response"])
                            st.session_state.messages.append({"role": "assistant", "content": result["final_response"]})
                        except errors.APIError as err:
                            error_msg = f"⚠️ **Google Gemini API Error:** {err.message} (Code: {err.code})"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        except Exception as ex:
                            error_msg = f"⚠️ **Execution Error:** {str(ex)}"
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()

with col_inspector:
    st.markdown("### 🔍 Case File & Grounding Inspector")
    tab_case, tab_guardrail, tab_kb = st.tabs([
        "📁 Extracted Case File",
        "🛡️ Guardrail & API Audit",
        "📜 Statutes DB (`statutes_kb.json`)"
    ])

    res = st.session_state.last_result

    with tab_case:
        if res and res.get("case_data"):
            cd = res["case_data"]
            
            # Metric Grid
            st.markdown(
                f"""
                <div class="nm-metric-grid">
                    <div class="nm-metric-card">
                        <div class="nm-metric-label">Legal Domain</div>
                        <div class="nm-metric-value">{cd.get('domain', 'N/A')}</div>
                    </div>
                    <div class="nm-metric-card">
                        <div class="nm-metric-label">User Language</div>
                        <div class="nm-metric-value">{cd.get('detected_language', 'English')}</div>
                    </div>
                    <div class="nm-metric-card">
                        <div class="nm-metric-label">Action Route</div>
                        <div class="nm-metric-value">{cd.get('next_mode', 'N/A')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Metadata Card
            opposite = cd.get("opposite_party") or "Not Specified"
            claim = f"₹{cd.get('claim_amount_inr')}" if cd.get("claim_amount_inr") else "Unspecified"
            complainant = cd.get("complainant_name") or "Citizen / Complainant"

            st.markdown(
                f"""
                <div class="nm-meta-card">
                    <div class="nm-meta-item"><strong>Complainant:</strong> {complainant}</div>
                    <div class="nm-meta-item"><strong>Opposite Party:</strong> {opposite}</div>
                    <div class="nm-meta-item"><strong>Disputed Value:</strong> {claim}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Extracted Chronological Timeline
            st.markdown("##### 🗓️ Fact Chronology")
            chronology = cd.get("chronology", [])
            if chronology:
                for item in chronology:
                    d = item.get("date_or_period", "Date N/A")
                    e = item.get("event", "")
                    st.markdown(
                        f"""
                        <div class="nm-timeline-node">
                            <span class="nm-timeline-date">{d}</span>
                            <span class="nm-timeline-event">{e}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No specific chronology extracted yet.")

            # Evidence Matrix
            st.markdown("##### 🧾 Evidence Analysis")
            col_ev1, col_ev2 = st.columns(2)
            with col_ev1:
                have_list = cd.get("evidence_have", [])
                have_items_html = "".join([f"<div class='nm-evidence-item'>✅ {x}</div>" for x in have_list]) if have_list else "<div class='nm-evidence-item'>None explicitly provided yet.</div>"
                st.markdown(
                    f"""
                    <div class="nm-evidence-box nm-evidence-box-have">
                        <div class="nm-evidence-title" style="color: #065F46;">Proof In Hand</div>
                        {have_items_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_ev2:
                need_list = cd.get("evidence_missing_or_needed", [])
                need_items_html = "".join([f"<div class='nm-evidence-item'>⚠️ {x}</div>" for x in need_list]) if need_list else "<div class='nm-evidence-item'>No critical missing proof flagged.</div>"
                st.markdown(
                    f"""
                    <div class="nm-evidence-box nm-evidence-box-need">
                        <div class="nm-evidence-title" style="color: #92400E;">Proof Still Needed</div>
                        {need_items_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with st.expander("🔍 View Structured Case Extraction JSON"):
                st.json(cd)
        else:
            st.info("💡 Run a query or choose a Case Preset on the left to inspect the structured extraction.")

    with tab_guardrail:
        if res:
            gr = res.get("guardrail_report", {})
            if gr.get("passed", True):
                st.markdown(
                    """
                    <div class="nm-guardrail-pass">
                        <span style="font-size: 1.5rem;">🛡️</span>
                        <div>
                            <strong style="color: #065F46;">Deterministic Citation Guardrail: PASSED</strong>
                            <div style="font-size: 0.8rem; color: #047857;">All statute citations in the response were verified against the local ground-truth database. 0 unverified citations.</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                flagged = gr.get("flagged_citations", [])
                st.markdown(
                    f"""
                    <div class="nm-guardrail-alert">
                        <strong style="color: #991B1B;">🚨 Blocked Unverified Citations:</strong>
                        <div style="font-size: 0.82rem; color: #B91C1C;">{flagged}</div>
                        <div style="font-size: 0.78rem; color: #7F1D1D; margin-top: 4px;">Guardrail stripped unverified sections to protect against hallucination.</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("##### 🌐 Live Legal API Retrieval")
            api_log = res.get("api_retrieval_log", {})
            source_used = api_log.get("api_source", "local_file_only")
            st.caption(f"**Source:** `{source_used}`")
            if api_log.get("live_records"):
                for record in api_log["live_records"]:
                    with st.expander(f"📄 {record.get('title', 'Legal Record')} ({record.get('source', 'Indian Kanoon')})"):
                        st.write(record.get("snippet", ""))
                        if record.get("url"):
                            st.markdown(f"[🔗 View Original Document]({record['url']})")
            else:
                st.caption("No external court records fetched for this turn (grounded strictly on verified statutes).")
        else:
            st.info("Guardrail and API verification audit will appear here once you send a message.")

        st.divider()
        st.markdown("##### ⚡ Live Legal API Probe")
        api_q = st.text_input("Query Indian Kanoon directly:", value="Consumer Protection Act Section 35 refund")
        if st.button("Query Legal API"):
            with st.spinner("Retrieving records from Indian Kanoon..."):
                probe_res = fetch_laws_via_api(api_q)
                st.json(probe_res)

    with tab_kb:
        st.caption("The local single source of truth for allowed statute sections (`data/statutes_kb.json`).")
        st.json(load_statutes_from_file())
