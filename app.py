import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# =========================
# CONFIGURAÇÕES DA INTERFACE
# =========================

st.set_page_config(
    page_title="Comunicação Digital Global",
    page_icon="🌍",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #1a1d23;
    }
    [data-testid="stSidebar"] * {
        color: #d4d8e0 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stCheckbox label {
        color: #8a8f9c !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.08);
    }
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }
    .page-title {
        font-size: 1.6rem;
        font-weight: 600;
        color: #1a1d23;
        margin-bottom: 0.25rem;
    }
    .page-subtitle {
        font-size: 0.85rem;
        color: #888;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e8e8e8;
        border-radius: 10px;
        padding: 1rem 1.25rem;
    }
    .section-card {
        background: #ffffff;
        border: 1px solid #e8e8e8;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a1d23;
        margin-bottom: 0.2rem;
    }
    .section-sub {
        font-size: 0.78rem;
        color: #aaa;
        margin-bottom: 1rem;
    }
    .badge-compare {
        display: inline-block;
        background: #e6f0ff;
        color: #1a5fd4;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 3px 12px;
        border-radius: 20px;
        margin-left: 10px;
        vertical-align: middle;
    }
    [data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e8e8e8;
        border-radius: 10px;
        padding: 1rem 1.25rem;
    }
    .custom-divider {
        border: none;
        border-top: 1px solid #f0f0f0;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# =========================
# AUXILIARES (BANDEIRA)
# =========================

def get_flag_url(rest_data: dict) -> str:
    if not rest_data:
        return ""
    cca2 = (rest_data.get('cca2') or '').lower()
    return f"https://flagcdn.com/w320/{cca2}.png"


# =========================
# DADOS
# =========================

@st.cache_data
def get_all_countries():
    response = requests.get("https://restcountries.com/v3.1/all?fields=name,cca2,cca3,translations")
    countries = response.json()
    country_list = []
    for c in countries:
        pt_name = c.get('translations', {}).get('por', {}).get('common', c['name']['common'])
        country_list.append((pt_name, c['name']['common'], c['cca2'], c['cca3']))
    country_list.sort(key=lambda x: x[0])
    return country_list

@st.cache_data
def get_rest_country_data(cca3):
    try:
        url = f"https://restcountries.com/v3.1/alpha/{cca3}"
        data = requests.get(url).json()[0]
        languages = list(data.get('languages', {}).values()) or ["Não disponível"]
        return {
            'name': data['name']['common'],
            'population': data.get('population'),
            'languages': languages,
            'cca2': data.get('cca2'),
            'cca3': data.get('cca3'),
            'flag': data.get('flags', {}).get('png', '')
        }
    except:
        return None

@st.cache_data
def get_world_bank_internet(cca3):
    url = f"https://api.worldbank.org/v2/country/{cca3}/indicator/IT.NET.USER.ZS?format=json&per_page=30"
    try:
        data = requests.get(url).json()
        if len(data) > 1:
            df = pd.DataFrame(data[1])
            df['date'] = pd.to_datetime(df['date'], format='%Y')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna().sort_values('date')
            return df.rename(columns={'value': 'Internet'})
        return pd.DataFrame()
    except:
        return pd.DataFrame()


# =========================
# HELPERS DE PLOT
# =========================

CHART_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12, color="#444"),
    margin=dict(t=10, b=40, l=40, r=10),
    xaxis=dict(showgrid=False, linecolor="#e8e8e8"),
    yaxis=dict(gridcolor="#f0f0f0", linecolor="#e8e8e8"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

def internet_line_chart(wb1, wb2=None, name1="", name2=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=wb1['date'], y=wb1['Internet'],
        name=name1,
        mode='lines+markers',
        line=dict(color='#378add', width=2.5),
        marker=dict(size=4),
        fill='tozeroy',
        fillcolor='rgba(55,138,221,0.08)'
    ))
    if wb2 is not None and not wb2.empty:
        fig.add_trace(go.Scatter(
            x=wb2['date'], y=wb2['Internet'],
            name=name2,
            mode='lines+markers',
            line=dict(color='#e28a1a', width=2.5, dash='dash'),
            marker=dict(size=4),
        ))
    fig.update_layout(**CHART_LAYOUT, yaxis_range=[0, 100],
                      yaxis_ticksuffix="%", height=260)
    return fig

def bar_comparison_chart(labels, values, colors):
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:,.0f}" for v in values],
        textposition='outside',
    ))
    layout = {**CHART_LAYOUT, 'height': 220}
    layout['yaxis'] = dict(showgrid=False, showticklabels=False, linecolor="#e8e8e8")
    fig.update_layout(**layout)
    return fig

def mom_growth_chart(wb1, wb2=None, name1="", name2=""):
    fig = go.Figure()
    if len(wb1) > 1:
        wb1 = wb1.copy()
        wb1['growth'] = wb1['Internet'].pct_change() * 100
        fig.add_trace(go.Bar(
            x=wb1['
