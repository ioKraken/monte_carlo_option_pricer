"""Visual theme: dark palette, page CSS and a matching Plotly template."""
import plotly.graph_objects as go
import plotly.io as pio

# Palette
BG = "#0a0e17"
SURFACE = "#111827"
SURFACE_2 = "#161e2e"
BORDER = "#1f2a3c"
TEXT = "#e6edf7"
MUTED = "#8b98ad"

C_PRIMARY = "#2dd4bf"   # teal: main series
C_SECONDARY = "#a78bfa"  # violet: second series / spot marker
C_AMBER = "#fbbf24"
C_ROSE = "#fb7185"      # strike marker / negative
C_SPOT = C_SECONDARY
C_STRIKE = C_ROSE
C_PATHS = "rgba(45, 212, 191, 0.24)"

FONT_SANS = "'Inter', -apple-system, 'Segoe UI', sans-serif"
FONT_MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, .stApp, .stApp *:not([data-testid="stIconMaterial"]):not(code):not(pre) {{ font-family: {FONT_SANS}; }}
.stApp .eyebrow, .stApp .chip, .stApp .footer,
.stApp div[data-testid="stMetricValue"], .stApp div[data-testid="stMetricValue"] *,
.stApp div[data-testid="stMetricLabel"] p, .stApp section[data-testid="stSidebar"] h2 {{ font-family: {FONT_MONO} !important; }}
.stApp {{
    background:
        radial-gradient(1100px 520px at 12% -8%, rgba(45,212,191,0.10), transparent 60%),
        radial-gradient(900px 480px at 100% 0%, rgba(167,139,250,0.10), transparent 55%),
        {BG};
    color: {TEXT};
}}
header[data-testid="stHeader"] {{ background: transparent; }}
footer, #MainMenu {{ visibility: hidden; }}
.block-container {{ padding-top: 2.2rem; max-width: 1280px; }}

/* Hero */
.hero {{ padding: 1.6rem 0 1.2rem; }}
.hero .eyebrow {{
    font: 500 0.72rem {FONT_MONO}; letter-spacing: 0.22em; text-transform: uppercase;
    color: {C_PRIMARY}; margin-bottom: 0.7rem;
}}
.hero h1 {{
    font-size: 2.7rem; line-height: 1.08; font-weight: 700; letter-spacing: -0.03em;
    margin: 0 0 0.7rem; padding: 0;
    background: linear-gradient(92deg, #ffffff 10%, {C_PRIMARY} 55%, {C_SECONDARY} 100%);
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}}
.hero p {{ color: {MUTED}; font-size: 1.02rem; max-width: 46rem; margin: 0; }}
.chips {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1.1rem; }}
.chip {{
    font: 500 0.74rem {FONT_MONO}; color: {MUTED};
    border: 1px solid {BORDER}; background: rgba(17,24,39,0.7);
    padding: 0.28rem 0.7rem; border-radius: 999px;
}}

/* Headings */
h1, h2, h3 {{ letter-spacing: -0.02em; color: {TEXT}; }}
h2 {{ font-weight: 600; }}
h3 {{ font-weight: 600; font-size: 1.15rem; color: {TEXT}; margin-top: 1.4rem; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {SURFACE}; border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] h2 {{
    font: 600 0.74rem {FONT_MONO}; letter-spacing: 0.18em; text-transform: uppercase;
    color: {C_PRIMARY};
}}

/* Tabs */
div[data-baseweb="tab-list"] {{ gap: 0.25rem; border-bottom: 1px solid {BORDER}; }}
button[data-baseweb="tab"] {{
    background: transparent; color: {MUTED}; font-weight: 500; padding: 0.7rem 1.1rem;
    border-radius: 8px 8px 0 0;
}}
button[data-baseweb="tab"]:hover {{ color: {TEXT}; background: rgba(255,255,255,0.03); }}
button[data-baseweb="tab"][aria-selected="true"] {{ color: {C_PRIMARY}; }}
div[data-baseweb="tab-highlight"] {{ background: {C_PRIMARY}; height: 2px; }}

/* Metric cards */
div[data-testid="stMetric"] {{
    background: linear-gradient(180deg, {SURFACE_2}, {SURFACE});
    border: 1px solid {BORDER}; border-radius: 14px; padding: 1rem 1.15rem;
    box-shadow: 0 8px 24px -14px rgba(0,0,0,0.8);
}}
div[data-testid="stMetric"]:hover {{ border-color: rgba(45,212,191,0.45); }}
div[data-testid="stMetricLabel"] p {{
    color: {MUTED}; font: 500 0.72rem {FONT_MONO}; letter-spacing: 0.1em; text-transform: uppercase;
}}
div[data-testid="stMetricValue"] {{
    font-family: {FONT_MONO}; font-weight: 600; color: {TEXT}; font-size: 1.7rem;
}}

/* Buttons */
.stButton > button {{
    border-radius: 10px; border: 1px solid {BORDER}; background: {SURFACE_2};
    color: {TEXT}; font-weight: 500; transition: all .15s ease;
}}
.stButton > button:hover {{ border-color: {C_PRIMARY}; color: {C_PRIMARY}; }}
.stButton > button[kind="primary"] {{
    background: linear-gradient(92deg, {C_PRIMARY}, #22b8cf 60%, {C_SECONDARY});
    color: #04121a; border: none; font-weight: 600;
    box-shadow: 0 10px 28px -12px rgba(45,212,191,0.65);
}}
.stButton > button[kind="primary"]:hover {{ filter: brightness(1.08); color: #04121a; }}

/* Inputs, tables, alerts */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="base-input"] {{
    background: {BG}; border-color: {BORDER}; border-radius: 8px;
}}
div[data-testid="stDataFrame"] {{ border: 1px solid {BORDER}; border-radius: 12px; overflow: hidden; }}
div[data-testid="stAlert"] {{ border-radius: 12px; border: 1px solid {BORDER}; }}
hr {{ border-color: {BORDER}; }}
div[data-testid="stPlotlyChart"] {{
    background: {SURFACE}; border-radius: 14px;
    outline: 1px solid {BORDER}; outline-offset: -1px;
}}
div[data-testid="stPlotlyChart"] svg.main-svg {{ background: transparent !important; }}

/* Footer */
.footer {{
    text-align: center; color: {MUTED}; font: 400 0.78rem {FONT_MONO};
    padding: 1.6rem 0 0.6rem; letter-spacing: 0.04em;
}}
</style>
"""

HERO = """
<div class="hero">
  <div class="eyebrow">Quantitative Finance Toolkit</div>
  <h1>Monte Carlo<br>Option Pricer</h1>
  <p>Price European and American options by simulation, benchmark them against
  Black-Scholes, and explore the Greeks, all with live market inputs.</p>
  <div class="chips">
    <span class="chip">Geometric Brownian Motion</span>
    <span class="chip">Longstaff-Schwartz LSM</span>
    <span class="chip">Black-Scholes Greeks</span>
    <span class="chip">Yahoo Finance</span>
  </div>
</div>
"""

FOOTER = '<div class="footer">Monte Carlo Option Pricer &nbsp;/&nbsp; educational tool, not financial advice</div>'


def register_plotly_template() -> None:
    """Make every Plotly chart in the app use the dark theme by default."""
    axis = dict(
        gridcolor="rgba(139,152,173,0.12)", zerolinecolor="rgba(139,152,173,0.25)",
        linecolor=BORDER, tickfont=dict(color=MUTED), title=dict(font=dict(color=MUTED)),
        automargin=True,
    )
    pio.templates["mcdark"] = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
            font=dict(family=FONT_SANS, color=TEXT, size=12),
            colorway=[C_PRIMARY, C_SECONDARY, C_AMBER, C_ROSE],
            xaxis=axis, yaxis=axis,
            legend=dict(font=dict(color=MUTED), bgcolor="rgba(0,0,0,0)"),
            hoverlabel=dict(bgcolor=SURFACE_2, bordercolor=BORDER, font=dict(color=TEXT)),
            margin=dict(l=56, r=24, t=24, b=52),
        )
    )
    pio.templates.default = "mcdark"
