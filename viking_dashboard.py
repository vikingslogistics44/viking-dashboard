import base64
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "FMCSA_RESULTS.csv"
REQUIRED_COLUMNS = [
    "Company",
    "Phone",
    "City",
    "State",
    "Power Units",
    "Status",
    "Tag",
    "Call_Attempts",
    "Last_Called",
]

STATUS_OPTIONS = ["No Answer", "Contacted", "Qualified", "Closed"]


def find_logo_path() -> Path | None:
    preferred_names = [
        "viking_logo.png",
        "viking_logo.jpg",
        "viking_logo.jpeg",
        "logo.png",
        "logo.jpg",
        "logo.jpeg",
    ]
    for name in preferred_names:
        candidate = BASE_DIR / name
        if candidate.exists():
            return candidate

    for pattern in ("*viking*.png", "*viking*.jpg", "*viking*.jpeg", "*logo*.png", "*logo*.jpg", "*logo*.jpeg"):
        matches = sorted(BASE_DIR.glob(pattern))
        if matches:
            return matches[0]

    image_candidates = sorted(
        path for path in BASE_DIR.iterdir() if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    if image_candidates:
        return image_candidates[0]

    return None


def render_logo_html(logo_path: Path) -> str:
    image_bytes = logo_path.read_bytes()
    encoded = base64.b64encode(image_bytes).decode("ascii")
    mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(logo_path.suffix.lower(), "image/png")
    return f"""
    <div class="viking-logo-shell">
        <img class="viking-logo-img" src="data:{mime_type};base64,{encoded}" alt="Viking logo" />
    </div>
    """


def render_section_header(title: str, rune: str = "ᚱ") -> None:
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-line"></div>
            <div class="section-title">{rune} {title}</div>
            <div class="section-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_panel_banner(title: str, subtitle: str = "") -> None:
    subtitle_html = f"<div class='panel-banner-subtitle'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class="panel-banner">
            <div class="panel-banner-ornament left">⚒</div>
            <div class="panel-banner-copy">
                <div class="panel-banner-title">{title}</div>
                {subtitle_html}
            </div>
            <div class="panel-banner-ornament right">⚒</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def ensure_csv_file() -> None:
    test_csv = BASE_DIR / "FMCSA_RESULTS_test.csv"
    if not CSV_PATH.exists() and test_csv.exists():
        test_csv.rename(CSV_PATH)


def normalize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    for column in REQUIRED_COLUMNS:
        if column not in dataframe.columns:
            if column == "Call_Attempts":
                dataframe[column] = 0
            else:
                dataframe[column] = ""

    dataframe["Call_Attempts"] = (
        pd.to_numeric(dataframe["Call_Attempts"], errors="coerce").fillna(0).astype(int)
    )
    dataframe["Phone"] = dataframe["Phone"].fillna("").astype(str)
    dataframe["Status"] = dataframe["Status"].fillna("").astype(str)
    dataframe["Tag"] = dataframe["Tag"].fillna("").astype(str)
    return dataframe


def load_data() -> pd.DataFrame:
    ensure_csv_file()
    if CSV_PATH.exists():
        try:
            dataframe = pd.read_csv(CSV_PATH)
        except Exception:
            dataframe = pd.DataFrame(columns=REQUIRED_COLUMNS)
    else:
        dataframe = pd.DataFrame(columns=REQUIRED_COLUMNS)

    dataframe = normalize_dataframe(dataframe)
    save_data(dataframe)
    return dataframe


def save_data(dataframe: pd.DataFrame) -> None:
    normalize_dataframe(dataframe).to_csv(CSV_PATH, index=False)


def persist_filtered_edits(full_df: pd.DataFrame, edited_filtered_df: pd.DataFrame) -> pd.DataFrame:
    updated_df = full_df.copy()
    for index in edited_filtered_df.index:
        if index in updated_df.index:
            for column in REQUIRED_COLUMNS:
                updated_df.loc[index, column] = edited_filtered_df.loc[index, column]
    return normalize_dataframe(updated_df)


st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;800&family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --bg-black: #070707;
            --bg-charcoal: #101112;
            --panel-dark: rgba(16, 17, 18, 0.92);
            --panel-dark-alt: rgba(20, 21, 23, 0.94);
            --panel-edge: rgba(255, 241, 203, 0.08);
            --gold: #E6C36C;
            --gold-soft: rgba(230, 195, 108, 0.18);
            --gold-strong: rgba(230, 195, 108, 0.34);
            --text-main: #F3E7C2;
            --text-muted: #B7A67A;
            --border: rgba(230, 195, 108, 0.42);
            --shadow-gold: 0 0 22px rgba(230, 195, 108, 0.18);
            --shadow-strong: 0 0 30px rgba(230, 195, 108, 0.24);
        }

        html, body, [class*="css"] {
            font-family: "Inter", sans-serif;
            background:
                radial-gradient(circle at top left, rgba(230, 195, 108, 0.08), transparent 34%),
                radial-gradient(circle at top right, rgba(230, 195, 108, 0.05), transparent 28%),
                linear-gradient(180deg, rgba(255,255,255,0.02), transparent 24%),
                linear-gradient(135deg, #050505 0%, #0c0d0f 40%, #141518 100%);
            color: var(--text-main);
        }

        .stApp {
            background:
                radial-gradient(circle at 50% -10%, rgba(230, 195, 108, 0.12), transparent 26%),
                radial-gradient(circle at 12% 18%, rgba(230, 195, 108, 0.06), transparent 20%),
                radial-gradient(circle at 84% 24%, rgba(230, 195, 108, 0.05), transparent 18%),
                linear-gradient(rgba(7, 7, 7, 0.88), rgba(7, 7, 7, 0.95)),
                repeating-linear-gradient(
                    135deg,
                    rgba(255, 255, 255, 0.02) 0px,
                    rgba(255, 255, 255, 0.02) 2px,
                    transparent 2px,
                    transparent 14px
                ),
                linear-gradient(135deg, #050505 0%, #0b0c0d 45%, #141518 100%);
            animation: battlefieldDrift 18s ease-in-out infinite;
        }

        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 2rem;
            max-width: 1480px;
        }

        h1, h2, h3 {
            font-family: "Cinzel", serif;
            color: var(--gold);
            letter-spacing: 0.06em;
        }

        h1 {
            text-transform: uppercase;
            text-shadow:
                0 0 8px rgba(230, 195, 108, 0.45),
                0 0 22px rgba(230, 195, 108, 0.2);
            animation: titlePulse 3.4s ease-in-out infinite;
        }

        p, label, .stCaption, .stMarkdown, .stText {
            color: var(--text-main);
        }

        [data-testid="stCaptionContainer"] {
            color: var(--text-muted);
        }

        @keyframes titlePulse {
            0%, 100% { text-shadow: 0 0 8px rgba(230, 195, 108, 0.35), 0 0 18px rgba(230, 195, 108, 0.14); }
            50% { text-shadow: 0 0 12px rgba(230, 195, 108, 0.58), 0 0 28px rgba(230, 195, 108, 0.28); }
        }

        @keyframes panelGlow {
            0%, 100% { box-shadow: inset 0 1px 0 rgba(255,255,255,0.03), 0 0 0 rgba(230, 195, 108, 0); }
            50% { box-shadow: inset 0 1px 0 rgba(255,255,255,0.03), 0 0 18px rgba(230, 195, 108, 0.12); }
        }

        @keyframes battlefieldDrift {
            0%, 100% { background-position: 0% 0%, 0% 0%, 100% 0%, 0 0, 0 0, 0 0; }
            50% { background-position: 0% 4%, 3% 2%, 97% 3%, 0 0, 8px 10px, 0 0; }
        }

        @keyframes emberPulse {
            0%, 100% { opacity: 0.55; transform: translate(-50%, -50%) scale(1); }
            50% { opacity: 0.85; transform: translate(-50%, -50%) scale(1.06); }
        }

        [data-testid="stMetric"] {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.08)),
                linear-gradient(135deg, rgba(230, 195, 108, 0.08), transparent 40%),
                repeating-linear-gradient(
                    135deg,
                    rgba(255, 255, 255, 0.015) 0px,
                    rgba(255, 255, 255, 0.015) 2px,
                    transparent 2px,
                    transparent 18px
                ),
                var(--panel-dark);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.03),
                inset 0 0 0 1px var(--panel-edge),
                0 0 0 1px rgba(230, 195, 108, 0.08),
                var(--shadow-gold);
            animation: panelGlow 4s ease-in-out infinite;
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
        }

        [data-testid="stMetricValue"] {
            color: var(--gold);
            font-family: "Cinzel", serif;
            text-shadow: 0 0 12px rgba(230, 195, 108, 0.18);
        }

        div[data-testid="stHorizontalBlock"] hr,
        [data-testid="stDivider"] {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(230, 195, 108, 0.82), transparent);
        }

        div[data-baseweb="select"] > div,
        .stTextInput > div > div,
        .stMultiSelect > div > div {
            background: var(--panel-dark-alt);
            border: 1px solid var(--border);
            color: var(--text-main);
            box-shadow: var(--shadow-gold);
        }

        div[data-baseweb="select"] * {
            color: var(--text-main) !important;
        }

        .stDataFrame, .stDataEditor {
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: var(--shadow-gold);
            background:
                repeating-linear-gradient(
                    135deg,
                    rgba(255, 255, 255, 0.012) 0px,
                    rgba(255, 255, 255, 0.012) 2px,
                    transparent 2px,
                    transparent 18px
                ),
                var(--panel-dark);
        }

        [data-testid="stDataEditor"] {
            position: relative;
        }

        [data-testid="stDataEditor"] [role="grid"] {
            background: var(--panel-dark);
        }

        [data-testid="stDataEditor"] [role="columnheader"] {
            background: linear-gradient(180deg, rgba(230, 195, 108, 0.15), rgba(230, 195, 108, 0.06));
            color: var(--gold);
            border-bottom: 1px solid var(--border);
            font-family: "Cinzel", serif;
            letter-spacing: 0.05em;
        }

        [data-testid="stDataEditor"] [role="row"]:nth-child(even) [role="gridcell"] {
            background: rgba(255, 255, 255, 0.015);
        }

        [data-testid="stDataEditor"] [role="row"]:nth-child(odd) [role="gridcell"] {
            background: rgba(255, 255, 255, 0.04);
        }

        [data-testid="stDataEditor"] [role="row"]:hover [role="gridcell"] {
            background: rgba(230, 195, 108, 0.12) !important;
            transition: background 0.2s ease;
        }

        [data-testid="stDataEditor"] [role="gridcell"] {
            color: var(--text-main);
            border-bottom: 1px solid rgba(230, 195, 108, 0.08);
        }

        .stButton > button {
            background: linear-gradient(180deg, #f0cf7e 0%, #c89d43 100%);
            color: #111;
            border: 1px solid rgba(255, 225, 155, 0.65);
            border-radius: 12px;
            font-weight: 700;
            letter-spacing: 0.03em;
            box-shadow:
                0 0 0 1px rgba(230, 195, 108, 0.18),
                0 10px 24px rgba(0, 0, 0, 0.32),
                0 0 18px rgba(230, 195, 108, 0.18);
            transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
        }

        .stButton > button:hover {
            background: linear-gradient(180deg, #d9b35b 0%, #a87d2c 100%);
            color: #080808;
            border-color: rgba(255, 225, 155, 0.8);
            box-shadow:
                0 0 0 1px rgba(230, 195, 108, 0.32),
                0 12px 28px rgba(0, 0, 0, 0.4),
                0 0 24px rgba(230, 195, 108, 0.28);
            transform: translateY(-1px);
            filter: brightness(1.02);
        }

        .stButton > button:focus {
            outline: none;
            box-shadow:
                0 0 0 1px rgba(230, 195, 108, 0.4),
                0 0 0 4px rgba(230, 195, 108, 0.12),
                0 0 24px rgba(230, 195, 108, 0.28);
        }

        .stButton > button::after {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: linear-gradient(120deg, transparent 0%, rgba(255,255,255,0.18) 45%, transparent 70%);
            transform: translateX(-120%);
            transition: transform 0.35s ease;
        }

        .stButton > button:hover::after {
            transform: translateX(120%);
        }

        [data-testid="stInfo"] {
            background: rgba(230, 195, 108, 0.08);
            border: 1px solid var(--border);
            color: var(--text-main);
            box-shadow: var(--shadow-gold);
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        .viking-hero {
            position: relative;
            margin: 0 auto 1.2rem auto;
            padding: 1.4rem 0 0.35rem 0;
            border-top: 1px solid rgba(230, 195, 108, 0.18);
            border-bottom: 1px solid rgba(230, 195, 108, 0.18);
            background:
                radial-gradient(circle at center, rgba(230, 195, 108, 0.08), transparent 44%),
                linear-gradient(90deg, transparent, rgba(230, 195, 108, 0.05), transparent);
        }

        .viking-hero::before,
        .viking-hero::after {
            content: "✦";
            position: absolute;
            top: 1rem;
            color: rgba(230, 195, 108, 0.68);
            font-size: 1rem;
            text-shadow: 0 0 16px rgba(230, 195, 108, 0.24);
        }

        .viking-hero::before {
            left: 2rem;
        }

        .viking-hero::after {
            right: 2rem;
        }

        .hero-axes {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 2rem;
            margin-bottom: -0.3rem;
            color: #b8c0c8;
            font-size: clamp(1.2rem, 2vw, 1.8rem);
            letter-spacing: 0.18em;
            text-shadow:
                0 0 10px rgba(184, 192, 200, 0.22),
                0 0 18px rgba(120, 132, 145, 0.16);
        }

        .viking-logo-shell {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin: 0 auto 0.45rem auto;
            position: relative;
        }

        .viking-logo-shell::before {
            content: "";
            position: absolute;
            left: 50%;
            top: 50%;
            width: min(64vw, 520px);
            height: min(64vw, 520px);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            background: radial-gradient(circle, rgba(230, 195, 108, 0.14), rgba(230, 195, 108, 0.02) 52%, transparent 72%);
            filter: blur(12px);
            animation: emberPulse 4.8s ease-in-out infinite;
        }

        .viking-logo-img {
            width: min(58vw, 460px);
            height: min(58vw, 460px);
            object-fit: cover;
            object-position: center;
            opacity: 0.62;
            clip-path: circle(43% at 50% 50%);
            filter:
                sepia(0.42)
                saturate(1.15)
                hue-rotate(-6deg)
                brightness(1.12)
                contrast(1.08)
                drop-shadow(0 0 24px rgba(230, 195, 108, 0.24));
            transition: opacity 0.2s ease, filter 0.2s ease;
            display: block;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }

        .viking-title {
            text-align: center;
            color: #f4e7bc;
            margin-top: -0.7rem;
            margin-bottom: 0.1rem;
            font-family: "Cinzel", serif;
            font-weight: 800;
            font-size: clamp(2.1rem, 5vw, 4.6rem);
            letter-spacing: 0.24em;
            text-transform: uppercase;
            text-shadow:
                0 0 14px rgba(230, 195, 108, 0.42),
                0 0 36px rgba(230, 195, 108, 0.16);
        }

        .viking-subtitle {
            text-align: center;
            color: var(--text-muted);
            margin: 0 auto 0.6rem auto;
            font-size: 0.82rem;
            letter-spacing: 0.44em;
            text-transform: uppercase;
        }

        .viking-divider {
            width: min(760px, 78vw);
            height: 16px;
            margin: 0 auto 0.15rem auto;
            position: relative;
        }

        .viking-divider::before,
        .viking-divider::after {
            content: "";
            position: absolute;
            top: 50%;
            width: calc(50% - 18px);
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(230, 195, 108, 0.85));
        }

        .viking-divider::before {
            left: 0;
        }

        .viking-divider::after {
            right: 0;
            transform: scaleX(-1);
        }

        .viking-divider span {
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -56%);
            color: var(--gold);
            font-size: 1rem;
            letter-spacing: 0.18em;
            text-shadow: 0 0 12px rgba(230, 195, 108, 0.3);
        }

        .section-header {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            gap: 0.9rem;
            margin: 1.2rem 0 0.7rem 0;
        }

        .section-line {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(230, 195, 108, 0.85), transparent);
        }

        .section-title {
            color: var(--gold);
            font-family: "Cinzel", serif;
            font-size: 1.08rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            text-shadow: 0 0 10px rgba(230, 195, 108, 0.22);
            white-space: nowrap;
        }

        .panel-banner {
            display: grid;
            grid-template-columns: 70px 1fr 70px;
            align-items: center;
            gap: 0.8rem;
            margin: 0.3rem 0 1rem 0;
            padding: 0.95rem 1rem;
            border: 1px solid rgba(230, 195, 108, 0.22);
            border-radius: 18px;
            background:
                radial-gradient(circle at center, rgba(230, 195, 108, 0.07), transparent 55%),
                repeating-linear-gradient(
                    135deg,
                    rgba(255, 255, 255, 0.01) 0px,
                    rgba(255, 255, 255, 0.01) 2px,
                    transparent 2px,
                    transparent 18px
                ),
                linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.12)),
                rgba(15, 16, 18, 0.92);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.04),
                inset 0 0 0 1px rgba(255, 241, 203, 0.05),
                0 0 26px rgba(230, 195, 108, 0.08);
        }

        .panel-banner-copy {
            text-align: center;
        }

        .panel-banner-title {
            color: #f2dfab;
            font-family: "Cinzel", serif;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 1rem;
            text-shadow: 0 0 12px rgba(230, 195, 108, 0.18);
        }

        .panel-banner-subtitle {
            color: var(--text-muted);
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.28em;
            margin-top: 0.25rem;
        }

        .panel-banner-ornament {
            color: #bcc5ce;
            text-align: center;
            font-size: 1.45rem;
            text-shadow:
                0 0 10px rgba(188, 197, 206, 0.2),
                0 0 16px rgba(120, 132, 145, 0.15);
        }

        .war-footer {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1rem;
            margin-top: 1.4rem;
            color: rgba(230, 195, 108, 0.74);
            font-size: 0.86rem;
            letter-spacing: 0.34em;
            text-transform: uppercase;
        }

        .war-footer::before,
        .war-footer::after {
            content: "";
            width: 120px;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(230, 195, 108, 0.8), transparent);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_path = find_logo_path()
st.markdown("<div class='viking-hero'>", unsafe_allow_html=True)
st.markdown("<div class='hero-axes'>⚒ ᚦ ⚒</div>", unsafe_allow_html=True)
if logo_path is not None:
    st.markdown(render_logo_html(logo_path), unsafe_allow_html=True)
st.markdown(
    """
    <div class='viking-title'>MC LEAD ENGINE</div>
    <div class='viking-divider'><span>ᚦ</span></div>
    <div class='viking-subtitle'>Fleet Command Console</div>
    """,
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)
st.caption("FMCSA Pipeline Dashboard")

df = load_data()

render_section_header("Filters", "ᚠ")
render_panel_banner("VIKINGS DASHBOARD", "TOGETHER WE CONQUER")
status_options = ["All"] + sorted(value for value in df["Status"].unique() if value)
tag_options = ["All"] + sorted(value for value in df["Tag"].unique() if value)

f1, f2, f3 = st.columns(3)
status_filter = f1.selectbox("Filter by Status", status_options)
tag_filter = f2.selectbox("Filter by Tag", tag_options)
phone_filter = f3.selectbox("Filter by Has Phone", ["All", "Yes", "No"])

filtered_df = df.copy()
if status_filter != "All":
    filtered_df = filtered_df[filtered_df["Status"] == status_filter]
if tag_filter != "All":
    filtered_df = filtered_df[filtered_df["Tag"] == tag_filter]
if phone_filter == "Yes":
    filtered_df = filtered_df[filtered_df["Phone"].str.strip() != ""]
elif phone_filter == "No":
    filtered_df = filtered_df[filtered_df["Phone"].str.strip() == ""]
filtered_df = filtered_df.copy()

total = len(filtered_df)
new = len(filtered_df[filtered_df["Status"] == "New"])
contacted = len(filtered_df[filtered_df["Status"] == "Contacted"])
qualified = len(filtered_df[filtered_df["Status"] == "Qualified"])
closed = len(filtered_df[filtered_df["Status"] == "Closed"])

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Leads", total)
col2.metric("New", new)
col3.metric("Contacted", contacted)
col4.metric("Qualified", qualified)
col5.metric("Closed", closed)

st.divider()
render_section_header("Lead Table", "ᚲ")
render_panel_banner("Lead Ledger", "Forged records and live edits")

edited_df = st.data_editor(
    filtered_df,
    use_container_width=True,
    num_rows="dynamic",
    disabled=["Last_Called", "Call_Attempts"],
    key="lead_editor",
)

updated_df = persist_filtered_edits(df, edited_df)
if not updated_df.equals(df):
    save_data(updated_df)
    df = updated_df
    filtered_df = edited_df.copy()

render_section_header("Status Commands", "ᛉ")
render_panel_banner("Command Actions", "Issue outcome orders")
if edited_df.empty:
    st.info("No leads match the current filters.")
else:
    selected_index = st.selectbox("Select Lead", edited_df.index)
    c1, c2, c3, c4 = st.columns(4)

    def apply_status(status: str) -> None:
        df.loc[selected_index, "Status"] = status
        df.loc[selected_index, "Call_Attempts"] = int(df.loc[selected_index, "Call_Attempts"]) + 1
        df.loc[selected_index, "Last_Called"] = pd.Timestamp.now().isoformat()
        save_data(df)
        st.rerun()

    if c1.button("❌ No Answer"):
        apply_status("No Answer")
    if c2.button("📞 Contacted"):
        apply_status("Contacted")
    if c3.button("🔥 Qualified"):
        apply_status("Qualified")
    if c4.button("✅ Closed"):
        apply_status("Closed")

st.divider()
render_section_header("Battle Analytics", "ᛟ")
left_chart, right_chart = st.columns(2)

with left_chart:
    render_panel_banner("Leads by Tag", "Territory distribution")
    st.bar_chart(filtered_df["Tag"].replace("", "Unassigned").value_counts(), use_container_width=True)

with right_chart:
    render_panel_banner("Activity Overview", "Campaign status")
    st.bar_chart(filtered_df["Status"].replace("", "Unassigned").value_counts(), use_container_width=True)

st.markdown("<div class='war-footer'>ᚠ Command Ready ᚱ</div>", unsafe_allow_html=True)
