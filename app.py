import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# STYLE (visual mais clean)
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

# =========================
# COUNTRIES LIST
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
# REST COUNTRIES
# =========================
@st.cache_data
def get_rest_country_data(cca3):
    try:
        url = f"https://restcountries.com/v3.1/alpha/{cca3}"
        data = requests.get(url).json()[0]

        return {
            'name': data['name']['common'],
            'pt_name': data.get('translations', {}).get('por', {}).get('common', data['name']['common']),
            'population': data.get('population'),
            'languages': list(data.get('languages', {}).values()) or ["N/A"],
            'region': data.get('region', 'N/A'),
            'cca2': data.get('cca2'),
            'flag': data.get('flags', {}).get('png', '')
        }
    except:
        return None

# =========================
# WORLD BANK (Internet)
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
# APP
# =========================
def main():
    countries = get_all_countries()
    names = [c[0] for c in countries]

    # =========================
    # SIDEBAR
    # =========================
    st.sidebar.title("🎛️ Filtros")

    country1_name = st.sidebar.selectbox("🌍 País", names)
    country1 = next(c for c in countries if c[0] == country1_name)

    compare = st.sidebar.checkbox("Comparar países")

    if compare:
        names2 = [n for n in names if n != country1_name]
        country2_name = st.sidebar.selectbox("Segundo país", names2)
        country2 = next(c for c in countries if c[0] == country2_name)

    # =========================
    # DADOS
    # =========================
    rest1 = get_rest_country_data(country1[3])
    wb1 = get_world_bank_internet(country1[3])

    # =========================
    # HEADER
    # =========================
    st.title("🌍 Comunicação Digital Global")

    if rest1 and rest1['flag']:
        st.image(rest1['flag'], width=100)

    # =========================
    # CARDS (KPIs)
    # =========================
    if rest1 and not wb1.empty:
        internet = wb1.iloc[-1]['Internet']
        population = rest1['population']
        social = internet * 0.75

        col1, col2, col3 = st.columns(3)

        col1.metric("🌐 Internet", f"{internet:.1f}%")
        col2.metric("📱 Social (estimado)", f"{social:.1f}%")
        col3.metric("👥 População", f"{population:,}")

    # =========================
    # GRÁFICOS
    # =========================
    st.subheader("📊 Análise")

    col1, col2 = st.columns(2)

    with col1:
        if not wb1.empty:
            fig = px.line(
                wb1,
                x='date',
                y='Internet',
                title="Uso de Internet ao longo do tempo"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Sem dados de internet")

    with col2:
        if rest1:
            st.markdown("### 🌎 Informações Gerais")
            st.write(f"**Região:** {rest1['region']}")
            st.write(f"**Idiomas:** {', '.join(rest1['languages'])}")

    # =========================
    # COMPARAÇÃO
    # =========================
    if compare:
        rest2 = get_rest_country_data(country2[3])
        wb2 = get_world_bank_internet(country2[3])

        st.subheader("🔄 Comparação")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### {country1_name}")
            if not wb1.empty:
                st.metric("Internet", f"{wb1.iloc[-1]['Internet']:.1f}%")

        with col2:
            st.markdown(f"### {country2_name}")
            if not wb2.empty:
                st.metric("Internet", f"{wb2.iloc[-1]['Internet']:.1f}%")

        # gráfico comparativo
        if not wb1.empty and not wb2.empty:
            df_compare = pd.merge(
                wb1[['date', 'Internet']],
                wb2[['date', 'Internet']],
                on='date',
                how='inner',
                suffixes=(f'_{country1_name}', f'_{country2_name}')
            )

            fig = px.line(df_compare, x='date', y=df_compare.columns[1:])
            st.plotly_chart(fig, use_container_width=True)


# =========================
if __name__ == "__main__":
    main()
