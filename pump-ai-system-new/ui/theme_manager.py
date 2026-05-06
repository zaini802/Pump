# =============================================================================
# ui/theme_manager.py  —  FIXED: headings/subheadings visible in ALL themes
# =============================================================================
import streamlit as st

def rgba(hex6, alpha):
    h = hex6.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def inject_theme(th):
    acc   = th["accent"];  acc2  = th["accent2"];  acc3  = th["accent3"]
    acc4  = th["accent4"]
    bg    = th["bg"];       sbg   = th["sidebar_bg"]; card  = th["card_bg"]
    text  = th["text"];     brd   = th["border"];    mlbl  = th["metric_lbl"]
    ga    = th["grad_a"];   gb    = th["grad_b"]

    st.markdown(f"""
<style>
/* BASE */
html,body,[class*="css"]{{ font-family:'Segoe UI',system-ui,sans-serif; }}
.stApp{{ background:{bg}; color:{text}; }}

/* MAIN AREA — all text */
.main p,.main span,.main div,
.block-container p,.block-container span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li {{ color:{text} !important; }}

/* markdown headings in main */
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{ color:{acc} !important; font-weight:800; }}
[data-testid="stMarkdownContainer"] h4  {{ color:{acc2} !important; font-weight:700; }}
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6  {{ color:{text} !important; font-weight:600; }}

/* widget labels */
.stSelectbox label,.stNumberInput label,.stSlider label,
.stTextInput label,.stTextArea label,.stCheckbox label,
.stRadio label,.stMultiSelect label {{ color:{text} !important; font-weight:600; }}

/* native st.metric */
[data-testid="stMetricLabel"] {{ color:{mlbl} !important; }}
[data-testid="stMetricValue"] {{ color:{text} !important; }}

/* expander */
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {{ color:{acc} !important; font-weight:700; }}
[data-testid="stExpander"] {{ background:{card} !important;
    border:1px solid {rgba(acc,0.3)} !important; border-radius:10px; }}

/* tabs */
[data-testid="stTabs"] button[role="tab"] {{ color:{text} !important; font-weight:600; }}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color:{acc} !important; border-bottom:2px solid {acc} !important; }}

/* SIDEBAR */
section[data-testid="stSidebar"] {{ background:{sbg} !important; }}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {{ color:{text} !important; }}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{ color:{acc} !important; }}
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] h5 {{ color:{acc2} !important; }}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] b {{ color:{acc} !important; }}
section[data-testid="stSidebar"] .stSelectbox>div>div,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stTextArea textarea {{
    background:{card} !important; color:{text} !important;
    border:1px solid {rgba(acc,0.5)} !important; border-radius:6px; }}

/* DEVELOPER BANNER */
.dev-banner{{
    background:linear-gradient(135deg,#0a2010,#0a1520,#100a20);
    border-radius:14px; padding:20px 28px; margin-bottom:20px;
    border:1px solid {rgba(acc,0.5)}; text-align:center;
}}
.dev-developed-by{{font-size:.80rem;color:#66bb6a;letter-spacing:2px;
    text-transform:uppercase;margin-bottom:6px;}}
.dev-name{{font-size:1.8rem;font-weight:900;color:#ffffff;letter-spacing:1px;}}
.dev-dept{{font-size:1.05rem;color:#ffd740;font-weight:600;margin-top:5px;}}
.dev-uni{{font-size:1rem;color:#ffffff;font-weight:700;margin-top:3px;}}
.dev-batch{{font-size:.95rem;color:#66bb6a;font-weight:600;margin-top:4px;}}

/* SECTION HEADINGS */
.sec-heading{{
    font-size:1.30rem; font-weight:800; letter-spacing:.6px;
    color:{acc}; padding:8px 0 4px 0; margin:20px 0 8px 0;
    border-bottom:2.5px solid {acc}; display:block;
}}

/* METRIC CARDS */
.metric-card{{background:{card};border-radius:12px;padding:14px 18px;
    margin:5px 0;border-left:4px solid {acc};
    box-shadow:0 2px 8px {rgba(acc,0.12)};}}
.metric-label{{font-size:.74rem;color:{mlbl};margin-bottom:3px;
    font-weight:500;text-transform:uppercase;letter-spacing:.4px;}}
.metric-value{{font-size:1.40rem;font-weight:800;color:{text};}}
.metric-unit{{font-size:.80rem;color:{mlbl};margin-left:4px;}}

/* PUMP CARDS */
.pump-card{{background:{card};border-radius:14px;padding:16px 20px;
    margin-bottom:12px;border:1px solid {rgba(acc,0.3)};}}
.pump-card.top{{border:2px solid {acc};box-shadow:0 0 18px {rgba(acc,0.22)};}}
.pump-card-title{{font-size:1.05rem;font-weight:700;color:{acc};}}
.pump-card-desc{{font-size:.87rem;color:{text};margin:6px 0;}}
.pump-card-meta{{font-size:.78rem;color:{mlbl};}}

/* CALC BOXES */
.calc-box{{
    background:#0d1117;
    border-left:4px solid {acc};
    padding:12px 18px;border-radius:8px;margin:8px 0;
    font-family:'Cascadia Code','Courier New',monospace;
    font-size:.88rem;color:#e6edf3;
    box-shadow:0 2px 8px rgba(0,0,0,0.25);
}}
.calc-box .cf,.calc-box span.cf{{ color:#ff79c6 !important; display:block; margin-bottom:3px; }}
.calc-box .cs,.calc-box span.cs{{ color:#8be9fd !important; display:block; margin-bottom:3px; }}
.calc-box .cr,.calc-box span.cr{{ color:#50fa7b !important; font-weight:700; display:block; }}
/* Override any theme text that bleeds into calc-box */
.calc-box *{{ color:inherit; }}
.calc-box .cf{{ color:#ff79c6 !important; }}
.calc-box .cs{{ color:#8be9fd !important; }}
.calc-box .cr{{ color:#50fa7b !important; }}

/* ALERT BOXES */
.warn-box{{background:#2d1a00;border-left:4px solid #ffa726;
    padding:10px 16px;border-radius:7px;margin:8px 0;color:#ffcc80;font-size:.87rem;}}
.info-box{{background:{card};border-left:4px solid {acc};
    padding:10px 16px;border-radius:7px;margin:8px 0;color:{text};font-size:.87rem;}}
.success-box{{background:#0d2b15;border-left:4px solid #66bb6a;
    padding:10px 16px;border-radius:7px;margin:8px 0;color:#a5d6a7;font-size:.87rem;}}
.danger-box{{background:#2b0d0d;border-left:4px solid #ef5350;
    padding:10px 16px;border-radius:7px;margin:8px 0;color:#ffcdd2;font-size:.87rem;}}

/* AI RESPONSE */
.ai-response{{background:{card};border-radius:12px;padding:18px 22px;
    border:1px solid {rgba(acc4,0.5)};font-size:.92rem;color:{text};
    line-height:1.75;box-shadow:0 2px 14px {rgba(acc4,0.15)};white-space:pre-wrap;}}
.ai-response strong,.ai-response b{{color:{acc} !important;}}

/* DIVIDER */
.fancy-div{{height:3px;border-radius:2px;margin:24px 0;
    background:linear-gradient(90deg,{ga},{gb},{acc3},{acc4});}}

/* DOWNLOAD BUTTONS */
[data-testid="stDownloadButton"] button{{
    background:{card} !important;color:{acc} !important;
    border:2px solid {acc} !important;border-radius:8px !important;
    font-weight:700 !important;transition:all .2s;}}
[data-testid="stDownloadButton"] button:hover{{
    background:{acc} !important;color:{bg} !important;}}

/* PRIMARY BUTTON */
[data-testid="stButton"] button[kind="primary"]{{
    background:linear-gradient(135deg,{ga},{gb}) !important;
    color:{bg} !important;border:none !important;
    font-weight:800 !important;font-size:1.05rem !important;
    padding:14px !important;border-radius:10px !important;}}

/* TABLES */
[data-testid="stDataFrame"] th{{background:{acc} !important;
    color:{bg} !important;font-weight:700 !important;}}
[data-testid="stDataFrame"] td{{color:{text} !important;background:{card} !important;}}

/* MOBILE */
@media(max-width:768px){{
    .metric-value{{font-size:1.05rem;}}
    .sec-heading{{font-size:1rem;}}
    .dev-name{{font-size:1.2rem;}}
}}

/* CATEGORY BUTTONS — ensure text always visible */
[data-testid="stButton"] button {{
    color: {text} !important;
    background: {card} !important;
    border: 1px solid {rgba(acc,0.35)} !important;
    border-radius: 8px !important;
    font-size: .88rem !important;
    font-weight: 600 !important;
    transition: all .15s ease;
    text-align: left !important;
    padding: 8px 14px !important;
}}
[data-testid="stButton"] button:hover {{
    background: {rgba(acc,0.18)} !important;
    border-color: {acc} !important;
    color: {acc} !important;
}}
</style>""", unsafe_allow_html=True)
