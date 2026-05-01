import streamlit as st
import plotly.express as px
import pandas as pd

st.title("🌍 Mapa Global de Tendências")

# Exemplo simples (depois você liga ao seu cálculo real)
data = pd.DataFrame({
    "country": ["Brazil", "United States", "Japan"],
    "score": [75, 85, 65]
})

fig = px.choropleth(
    data,
    locations="country",
    locationmode="country names",
    color="score",
    title="Trend Score Global"
)

st.plotly_chart(fig, use_container_width=True)
