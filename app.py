import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from pytrends.request import TrendReq

# =========================
# MAPEAMENTO GOOGLE TRENDS
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
# LISTA DE PAÍSES
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

# =========================
# REST COUNTRIES (CORRIGIDO)
# =========================
@st.cache_data
def get_rest_country_data(cca3):
    try:
        url = f"https://restcountries.com/v3.1/alpha/{cca3}"
        data = requests.get(url).json()[0]

        languages = list(data.get('languages', {}).values()) or ["Não disponível"]

        return {
            'name': data['name']['common'],
            'pt_name': data.get('translations', {}).get('por', {}).get('common', data['name']['common']),
            'population': data.get('population'),
            'languages': languages,
            'region': data.get('region', 'N/A'),
            'cca2': data.get('cca2'),
            'cca3': data.get('cca3'),
            'flag': data.get('flags', {}).get('png', '')
        }
    except:
        return None

# =========================
# WORLD BANK
# =========================
@st.cache_data
def get_world_bank_internet(cca3):
    url = f"https://api.worldbank.org/v2/country/{cca3}/indicator/IT.NET.USER.ZS?format=json"

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
# GOOGLE TRENDS (CORRIGIDO)
# =========================
@st.cache_data
def get_google_trends(cca2):
    try:
        pn = COUNTRY_MAP.get(cca2, None)

        if not pn:
            return pd.DataFrame()

        pytrends = TrendReq(hl='pt-BR', tz=180)
        trends = pytrends.trending_searches(pn=pn)

        trends = trends.head(10)
        trends.columns = ['Tendência']
        trends['Posição'] = range(1, len(trends)+1)

        return trends
    except:
        return pd.DataFrame()

# =========================
# INSIGHTS (MELHORADOS)
# =========================
def generate_single_insights(rest, wb, trends):
    insights = []

    # INTERNET
    if not wb.empty:
        latest = wb.iloc[-1]['Internet']
        if latest > 80:
            nivel = "alto"
        elif latest > 50:
            nivel = "moderado"
        else:
            nivel = "baixo"

        insights.append(f"Acesso à internet {nivel} ({latest:.1f}%).")

        social = latest * 0.75
        insights.append(f"Uso estimado de redes sociais: {social:.1f}% da população.")
    else:
        insights.append("Sem dados recentes de internet.")

    # DEMOGRAFIA
    pop = f"{rest['population']:,}" if rest['population'] else "N/A"
    insights.append(f"População: {pop}. Idiomas: {', '.join(rest['languages'])}.")

    # TRENDS
    if not trends.empty:
        top = trends['Tendência'].tolist()[:5]
        insights.append(f"Tendências: {', '.join(top)}.")

        # ESTILO
        visual_words = ['youtube', 'tiktok', 'video', 'filme']
        text_words = ['noticia', 'artigo', 'blog']

        visual = sum(any(v in t.lower() for v in visual_words) for t in top)
        text = sum(any(v in t.lower() for v in text_words) for t in top)

        if visual > text:
            insights.append("Comunicação mais visual.")
        elif text > visual:
            insights.append("Comunicação mais textual.")
        else:
            insights.append("Comunicação equilibrada.")

        # LIBERDADE (melhor proxy)
        unique_words = len(set(" ".join(top).split()))
        if unique_words > 10:
            insights.append("Alta diversidade de temas → maior abertura informacional.")
        else:
            insights.append("Baixa diversidade → possível limitação informacional.")

    return "\n\n".join(insights)

# =========================
# APP
# =========================
def main():
    st.title("🌍 Comunicação Digital Global")

    countries = get_all_countries()
    names = [c[0] for c in countries]

    country1_name = st.selectbox("Escolha um país", names)
    country1 = next(c for c in countries if c[0] == country1_name)

    compare = st.checkbox("Comparar com outro país")

    if compare:
        names2 = [n for n in names if n != country1_name]
        country2_name = st.selectbox("Segundo país", names2)
        country2 = next(c for c in countries if c[0] == country2_name)

    # DADOS
    rest1 = get_rest_country_data(country1[3])
    wb1 = get_world_bank_internet(country1[3])
    trends1 = get_google_trends(country1[2])

    # VISUAL
    st.header(country1_name)

    if rest1['flag']:
        st.image(rest1['flag'], width=120)

    st.write(generate_single_insights(rest1, wb1, trends1))

    if not wb1.empty:
        fig = px.line(wb1, x='date', y='Internet', title="Internet ao longo do tempo")
        st.plotly_chart(fig)

    if not trends1.empty:
        st.table(trends1)

    # COMPARAÇÃO
    if compare:
        rest2 = get_rest_country_data(country2[3])
        wb2 = get_world_bank_internet(country2[3])
        trends2 = get_google_trends(country2[2])

        st.header("Comparação")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(country1_name)
            st.write(generate_single_insights(rest1, wb1, trends1))

        with col2:
            st.subheader(country2_name)
            st.write(generate_single_insights(rest2, wb2, trends2))

# =========================
if __name__ == "__main__":
    main()
