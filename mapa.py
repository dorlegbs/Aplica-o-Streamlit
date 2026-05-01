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
