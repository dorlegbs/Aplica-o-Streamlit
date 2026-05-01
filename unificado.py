import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Configuração da página (deve ser a primeira linha do Streamlit)
st.set_page_config(page_title="Global Digital Insights", layout="wide")

# =========================================================
# FUNÇÕES DE DADOS (Compartilhadas entre as abas)
# =========================================================

@st.cache_data
def get_all_countries():
    try:
        response = requests.get("https://restcountries.com/v3.1/all?fields=name,cca2,cca3,translations")
        countries = response.json()
        country_list = []
        for c in countries:
            pt_name = c.get('translations', {}).get('por', {}).get('common', c['name']['common'])
            country_list.append((pt_name, c['name']['common'], c['cca2'], c['cca3']))
        country_list.sort(key=lambda x: x[0])
        return country_list
    except:
        return []

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
    url = f"https://api.worldbank.org/v2/country/{cca3}/indicator/IT.NET.USER.ZS?format=json"
    try:
        data = requests.get(url).json()
        if len(data) > 1 and data[1]:
            df = pd.DataFrame(data[1])
            df['date'] = pd.to_datetime(df['date'], format='%Y')
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna().sort_values('date')
            return df.rename(columns={'value': 'Internet'})
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# =========================================================
# ABA 1: ANÁLISE POR PAÍS (Antigo app.py)
# =========================================================
def render_analise_detalhada():
    st.title("🌍 Análise de Comunicação Digital")
    
    countries = get_all_countries()
    names = [c[0] for c in countries]

    country1_name = st.selectbox("Escolha um país", names)
    country1 = next(c for c in countries if c[0] == country1_name)

    rest1 = get_rest_country_data(country1[3])
    wb1 = get_world_bank_internet(country1[3])

    col_flag, col_info = st.columns([1, 4])
    
    with col_flag:
        if rest1:
            st.image(rest1['flag'], width=150)
    
    with col_info:
        st.header(country1_name)
        if rest1:
            st.write(f"**População:** {rest1['population']:,}")
            st.write(f"**Idiomas:** {', '.join(rest1['languages'])}")

    if not wb1.empty:
        st.subheader("Histórico de Acesso à Internet")
        fig = px.line(wb1, x='date', y='Internet', title=f"% de Usuários em {country1_name}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Dados históricos não disponíveis para este país.")

# =========================================================
# ABA 2: MAPA GLOBAL (Antigo mapa.py)
# =========================================================
def render_mapa_global():
    st.title("🗺️ Mapa Global de Conectividade")
    st.info("Carregando dados globais do Banco Mundial... Isso pode levar alguns segundos.")

    countries = get_all_countries()
    map_data = []

    # Criando uma barra de progresso para o mapa
    progress_bar = st.progress(0)
    
    # Para performance, vamos pegar apenas os dados mais recentes de cada país
    # Nota: Em um app real, o ideal seria ter um CSV pré-carregado para o mapa
    for i, c in enumerate(countries[:50]): # Limitado a 50 para exemplo rápido
        cca3 = c[3]
        url = f"https://api.worldbank.org/v2/country/{cca3}/indicator/IT.NET.USER.ZS?format=json&per_page=1"
        try:
            res = requests.get(url).json()
            if len(res) > 1 and res[1][0]['value']:
                map_data.append({
                    "País": c[0],
                    "ISO": cca3,
                    "Conectividade": res[1][0]['value']
                })
        except:
            continue
        progress_bar.progress((i + 1) / 50)
    
    df_map = pd.DataFrame(map_data)

    if not df_map.empty:
        fig = px.choropleth(df_map, 
                            locations="ISO",
                            color="Conectividade",
                            hover_name="País",
                            color_continuous_scale=px.colors.sequential.Plasma,
                            title="Porcentagem da População com Acesso à Internet")
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Não foi possível carregar os dados do mapa.")

# =========================================================
# MENU PRINCIPAL (SIDEBAR)
# =========================================================
def main():
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para:", ["Análise por País", "Mapa Global"])

    if page == "Análise por País":
        render_analise_detalhada()
    else:
        render_mapa_global()

if __name__ == "__main__":
    main()
