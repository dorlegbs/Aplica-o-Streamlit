import streamlit as st
import pandas as pd
import plotly.express as px
import requests

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
# REST COUNTRIES
# =========================
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

# =========================
# WORLD BANK (INTERNET)
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
    st.title("🌍 Comunicação Digital Global")

    countries = get_all_countries()
    names = [c[0] for c in countries]

    # =========================
    # SELEÇÃO
    # =========================
    country1_name = st.selectbox("Escolha um país", names)
    country1 = next(c for c in countries if c[0] == country1_name)

    compare = st.checkbox("Comparar com outro país")

    if compare:
        names2 = [n for n in names if n != country1_name]
        country2_name = st.selectbox("Segundo país", names2)
        country2 = next(c for c in countries if c[0] == country2_name)

    # =========================
    # DADOS
    # =========================
    rest1 = get_rest_country_data(country1[3])
    wb1 = get_world_bank_internet(country1[3])

    # =========================
    # VISUAL
    # =========================
    st.header(country1_name)

    if rest1:
        flag_url = rest1.get('flag')

        if not flag_url:
            flag_url = f"https://flagcdn.com/w320/{rest1['cca2'].lower()}.png"

        if rest1['cca3'] == "AFG":
            flag_url = "https://geo5.net/imagens/bandeira-do-afeganistao-2000px.png"

        st.image(flag_url, width=120)

    # =========================
    # CONTROLES
    # =========================
    st.subheader("🎛️ Personalize a análise")

    col1, col2 = st.columns(2)

    with col1:
        show_internet = st.checkbox("🌐 Acesso à Internet", value=True)
        show_social = st.checkbox("📱 Redes Sociais (estimado)", value=True)
        show_population = st.checkbox("👥 População", value=True)

    with col2:
        st.markdown("ℹ️ Dados disponíveis:")
        st.markdown("- 🌐 Internet")
        st.markdown("- 📱 Redes sociais (estimado)")
        st.markdown("- 👥 População")

    # =========================
    # INTERNET
    # =========================
    if show_internet:
        with st.expander("🌐 Acesso à Internet"):
            if not wb1.empty:
                latest = wb1.iloc[-1]['Internet']
                st.markdown(f"**{latest:.1f}% da população usa internet**")

                fig = px.line(wb1, x='date', y='Internet')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Sem dados disponíveis")

    # =========================
    # REDES SOCIAIS
    # =========================
    if show_social:
        with st.expander("📱 Uso de Redes Sociais"):
            if not wb1.empty:
                social = wb1.iloc[-1]['Internet'] * 0.75
                st.markdown(f"Estimativa: **{social:.1f}% da população**")
            else:
                st.warning("Sem dados suficientes")

    # =========================
    # POPULAÇÃO
    # =========================
    if show_population:
        with st.expander("👥 População"):
            pop = f"{rest1['population']:,}" if rest1 and rest1['population'] else "N/A"
            st.markdown(f"População: **{pop}**")
            st.markdown(f"Idiomas: {', '.join(rest1['languages'])}")

    # =========================
    # COMPARAÇÃO
    # =========================
    if compare:
        rest2 = get_rest_country_data(country2[3])
        wb2 = get_world_bank_internet(country2[3])

        st.header("🔄 Comparação")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader(country1_name)
            pop1 = f"{rest1['population']:,}" if rest1 else "N/A"
            st.write(f"População: {pop1}")

        with col2:
            st.subheader(country2_name)
            pop2 = f"{rest2['population']:,}" if rest2 else "N/A"
            st.write(f"População: {pop2}")


# =========================
if __name__ == "__main__":
    main()
