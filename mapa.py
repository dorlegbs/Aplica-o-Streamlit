import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from pytrends.request import TrendReq

st.page_link("pages/1_Mapa_Global.py", label="🌍 Ver Mapa Global")

st.title("🌍 Mapa Global de Comunicação Digital")

# =========================
# CONFIG
# =========================
COUNTRY_MAP = {
    "BR": "brazil",
    "US": "united_states",
    "JP": "japan",
    "FR": "france",
    "DE": "germany",
    "GB": "united_kingdom",
    "IN": "india",
    "CA": "canada",
    "AU": "australia"
}

# =========================
# FUNÇÕES
# =========================
@st.cache_data
def get_countries():
    url = "https://restcountries.com/v3.1/all?fields=name,cca2,cca3"
    return requests.get(url).json()

@st.cache_data
def get_internet(cca3):
    try:
        url = f"https://api.worldbank.org/v2/country/{cca3}/indicator/IT.NET.USER.ZS?format=json"
        data = requests.get(url).json()

        if len(data) > 1:
            df = pd.DataFrame(data[1])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna()

            if not df.empty:
                return df.iloc[0]['value']
    except:
        pass

    return None

@st.cache_data
def get_trends_score(cca2):
    try:
        pn = COUNTRY_MAP.get(cca2)

        if not pn:
            return 20  # fallback baixo

        pytrends = TrendReq(hl='pt-BR', tz=180)

        try:
            trends = pytrends.trending_searches(pn=pn)
            return min(len(trends) * 5, 50)
        except:
            return 20
    except:
        return 20

def calculate_score(internet, trend_score):
    if internet is None:
        internet = 30  # fallback

    score = (internet * 0.6) + (trend_score * 0.4)
    return round(min(score, 100), 1)

# =========================
# COLETA DE DADOS
# =========================
countries = get_countries()

data_list = []

with st.spinner("🔄 Calculando dados globais..."):
    for c in countries:
        name = c["name"]["common"]
        cca2 = c.get("cca2")
        cca3 = c.get("cca3")

        if not cca2 or not cca3:
            continue

        internet = get_internet(cca3)
        trend_score = get_trends_score(cca2)

        final_score = calculate_score(internet, trend_score)

        data_list.append({
            "country": name,
            "score": final_score
        })

df = pd.DataFrame(data_list)

# =========================
# MAPA
# =========================
fig = px.choropleth(
    df,
    locations="country",
    locationmode="country names",
    color="score",
    color_continuous_scale="YlOrRd",
    title="🌍 Trend Score Global",
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# TOP PAÍSES
# =========================
st.subheader("🏆 Top Países")

top = df.sort_values("score", ascending=False).head(10)

st.dataframe(top)
