import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.title("🌍 Mapa Global de Conectividade Digital")

# =========================
# FUNÇÕES
# =========================
@st.cache_data
def get_countries():
    url = "https://restcountries.com/v3.1/all?fields=name,cca3"
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

# =========================
# COLETA
# =========================
countries = get_countries()

data = []

with st.spinner("🔄 Carregando dados globais..."):
    for c in countries:
        name = c["name"]["common"]
        cca3 = c.get("cca3")

        if not cca3:
            continue

        internet = get_internet(cca3)

        # fallback simples
        if internet is None:
            internet = 0

        data.append({
            "country": name,
            "internet": round(internet, 1)
        })

df = pd.DataFrame(data)

# =========================
# MAPA
# =========================
fig = px.choropleth(
    df,
    locations="country",
    locationmode="country names",
    color="internet",
    color_continuous_scale="Blues",
    title="🌐 % da população com acesso à internet"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# RANKING
# =========================
st.subheader("🏆 Ranking de Conectividade")

top = df.sort_values("internet", ascending=False).head(10)
bottom = df.sort_values("internet").head(10)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🔝 Mais conectados")
    st.dataframe(top)

with col2:
    st.markdown("### 🔻 Menos conectados")
    st.dataframe(bottom)
