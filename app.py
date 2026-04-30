import sys

# Verifica pacotes obrigatórios antes de importar
required_packages = {
    "streamlit": "streamlit",
    "pandas": "pandas", 
    "plotly": "plotly",
    "requests": "requests",
    "pytrends": "pytrends"
}

missing = []
for module, package in required_packages.items():
    try:
        __import__(module)
    except ImportError:
        missing.append(package)

if missing:
    print(f"❌ Pacotes faltantes: {', '.join(missing)}")
    print(f"Instale com: pip install {' '.join(missing)}")
    sys.exit(1)

# Imports normais após verificação
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from pytrends.request import TrendReq

@st.cache_data
def get_all_countries():
    try:
        response = requests.get("https://restcountries.com/v3.1/all?fields=name,cca2,cca3,translations")
        if response.status_code == 200:
            countries = response.json()
            country_list = []
            for c in countries:
                pt_name = c.get('translations', {}).get('por', {}).get('common', c['name']['common'])
                common_name = c['name']['common']
                cca2 = c.get('cca2')
                cca3 = c.get('cca3')
                if cca2 and cca3:
                    country_list.append((pt_name, common_name, cca2, cca3))
            country_list.sort(key=lambda x: x[0])
            return country_list
        else:
            st.error("Falha ao carregar lista de países da API REST Countries")
            return []
    except Exception as e:
        st.error(f"Erro ao carregar lista de países: {e}")
        return []

@st.cache_data
def get_rest_country_data(country_name, cca2, cca3):
    try:
        response = requests.get(f"https://restcountries.com/v3.1/name/{country_name}?fullText=true")
        if response.status_code == 200:
            data = response.json()[0]
            return {
                'name': data['name']['common'],
                'pt_name': data.get('translations', {}).get('por', {}).get('common', data['name']['common']),
                'population': data.get('population', 'N/A'),
                'languages': list(data.get('languages', {}).values()),
                'region': data.get('region', 'N/A'),
                'cca2': data.get('cca2'),
                'cca3': data.get('cca3'),
                'flag': data.get('flags', {}).get('png', '')
            }
        else:
            return None
    except Exception as e:
        st.error(f"Erro ao buscar dados da REST Countries para {country_name}: {e}")
        return None

@st.cache_data
def get_world_bank_internet(cca3):
    url = f"https://api.worldbank.org/v2/country/{cca3}/indicator/IT.NET.USER.ZS?format=json&per_page=100"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                df = pd.DataFrame(data[1])
                df['date'] = pd.to_datetime(df['date'], format='%Y')
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                df = df.dropna(subset=['value'])
                df = df.sort_values('date')
                return df[['date', 'value']].rename(columns={'value': 'Usuários de Internet (% da População)'})
            else:
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar dados da World Bank para {cca3}: {e}")
        return pd.DataFrame()

@st.cache_data
def get_google_trends(cca2):
    try:
        pytrends = TrendReq(hl='pt-BR', tz=180)
        trends = pytrends.trending_searches(pn=cca2.lower())
        if trends is not None and not trends.empty:
            trends = trends.head(10)
            trends.columns = ['Tendência']
            trends['Posição'] = range(1, len(trends)+1)
            return trends[['Posição', 'Tendência']]
        else:
            return pd.DataFrame()
    except Exception as e:
        st.warning(f"Não foi possível buscar dados do Google Trends para {cca2}: {e}")
        return pd.DataFrame()

def generate_single_insights(rest_data, wb_df, trends_df):
    insights = []
    if not wb_df.empty:
        latest_year = wb_df['date'].max().year
        latest_value = wb_df[wb_df['date'].dt.year == latest_year]['Usuários de Internet (% da População)'].values[0]
        insights.append(f"**Acesso à Internet**: Em {latest_year}, {rest_data['pt_name']} tinha {latest_value:.1f}% da população usando internet.")
        if latest_value > 80:
            insights.append("Isso indica conectividade digital muito alta, sugerindo amplo acesso a ferramentas de comunicação online.")
        elif latest_value > 50:
            insights.append("Isso indica conectividade digital moderada a alta, com potencial significativo de engajamento online.")
        else:
            insights.append("Isso indica menor conectividade digital, o que pode limitar canais de comunicação online generalizados.")
    else:
        insights.append("**Acesso à Internet**: Não há dados recentes da World Bank sobre uso de internet para este país.")
    
    insights.append(f"**Demografia**: População de {rest_data['population']:,}, com idiomas principais: {', '.join(rest_data['languages'])}.")
    
    if not wb_df.empty:
        latest_value = wb_df[wb_df['date'].dt.year == latest_year]['Usuários de Internet (% da População)'].values[0]
        estimated_social = latest_value * 0.75
        insights.append(f"**Uso Estimado de Redes Sociais**: Aproximadamente {estimated_social:.1f}% da população (75% dos usuários de internet), indicando engajamento {'alto' if estimated_social >60 else 'moderado' if estimated_social >30 else 'baixo'} com plataformas sociais.")
    
    if not trends_df.empty:
        top_trends = trends_df['Tendência'].tolist()[:5]
        insights.append(f"**Tendências de Busca Recentes**: As principais buscas recentes incluem {', '.join(top_trends)}.")
        visual_keywords = ['instagram', 'tiktok', 'youtube', 'vídeo', 'foto']
        text_keywords = ['notícias', 'twitter', 'blog', 'artigo', 'texto']
        visual_count = sum(1 for t in top_trends if any(k in t.lower() for k in visual_keywords))
        text_count = sum(1 for t in top_trends if any(k in t.lower() for k in text_keywords))
        if visual_count > text_count:
            insights.append("As tendências de busca sugerem um estilo de comunicação digital mais voltado para o visual.")
        elif text_count > visual_count:
            insights.append("As tendências de busca sugerem um estilo de comunicação digital mais voltado para o texto.")
        else:
            insights.append("As tendências de busca sugerem um mix equilibrado de comunicação visual e textual.")
        
        if len(trends_df) >= 8:
            insights.append("Tópicos diversos em tendências sugerem um nível relativamente alto de liberdade de imprensa e acesso aberto à informação.")
        else:
            insights.append("Tópicos de tendências limitados podem sugerir acesso mais restrito à informação, sujeito a verificação adicional.")
    else:
        insights.append("**Tendências de Busca**: Não há dados recentes do Google Trends disponíveis para este país.")
    
    return "\n\n".join(insights)

def generate_comparative_insights(rest1, wb1, trends1, rest2, wb2, trends2):
    insights = []
    if not wb1.empty and not wb2.empty:
        latest_year1 = wb1['date'].max().year
        val1 = wb1[wb1['date'].dt.year == latest_year1]['Usuários de Internet (% da População)'].values[0]
        latest_year2 = wb2['date'].max().year
        val2 = wb2[wb2['date'].dt.year == latest_year2]['Usuários de Internet (% da População)'].values[0]
        insights.append(f"**Conectividade Digital**: {rest1['pt_name']} ({val1:.1f}% de usuários de internet) vs {rest2['pt_name']} ({val2:.1f}%). ")
        if val1 > val2:
            insights.append(f"{rest1['pt_name']} tem penetração de internet significativamente maior, sugerindo melhor acesso a ferramentas de comunicação digital.")
        elif val2 > val1:
            insights.append(f"{rest2['pt_name']} tem penetração de internet significativamente maior, sugerindo melhor acesso a ferramentas de comunicação digital.")
        else:
            insights.append("Ambos os países têm níveis similares de penetração de internet.")
    
    pop1 = rest1['population']
    pop2 = rest2['population']
    insights.append(f"**População**: {rest1['pt_name']} ({pop1:,}) vs {rest2['pt_name']} ({pop2:,}). ")
    if pop1 > pop2:
        insights.append(f"{rest1['pt_name']} tem população maior, o que pode levar a canais de comunicação mais diversos.")
    
    lang1 = set(rest1['languages'])
    lang2 = set(rest2['languages'])
    common_langs = lang1.intersection(lang2)
    if common_langs:
        insights.append(f"**Idiomas Comuns**: Ambos os países compartilham {', '.join(common_langs)}, facilitando a comunicação digital transfronteiriça.")
    else:
        insights.append(f"**Idiomas**: Não há idiomas comuns entre {rest1['pt_name']} ({', '.join(rest1['languages'])}) e {rest2['pt_name']} ({', '.join(rest2['languages'])}), o que pode criar barreiras de comunicação.")
    
    if not trends1.empty and not trends2.empty:
        trends1_list = trends1['Tendência'].tolist()
        trends2_list = trends2['Tendência'].tolist()
        insights.append(f"**Tendências de Busca**: Principais tendências de {rest1['pt_name']}: {', '.join(trends1_list[:3])}; de {rest2['pt_name']}: {', '.join(trends2_list[:3])}.")
        common_trends = set(t.lower() for t in trends1_list).intersection(set(t.lower() for t in trends2_list))
        if common_trends:
            insights.append(f"Tópicos de tendências comuns incluem {', '.join(common_trends)}, indicando interesses globais compartilhados.")
    
    return "\n\n".join(insights)

def main():
    st.set_page_config(page_title="Explorador de Comunicação Digital", layout="wide")
    st.title("🌍 Explorador de Comunicação Digital Global")
    st.markdown("Explore como países comunicam digitalmente usando dados reais da World Bank, REST Countries e Google Trends.")
    
    with st.spinner("Carregando lista de países..."):
        country_list = get_all_countries()
    
    if not country_list:
        st.error("Falha ao carregar lista de países. Tente novamente mais tarde.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Selecione o Primeiro País")
        selected_pt_name1 = st.selectbox("Escolha um país", [c[0] for c in country_list], key="country1")
        country1_tuple = next(c for c in country_list if c[0] == selected_pt_name1)
        pt_name1, common_name1, cca2_1, cca3_1 = country1_tuple
    
    add_second = st.checkbox("Adicionar segundo país para comparação")
    pt_name2, common_name2, cca2_2, cca3_2 = None, None, None, None
    if add_second:
        with col2:
            st.subheader("Selecione o Segundo País")
            available_pt_names = [c[0] for c in country_list if c[0] != pt_name1]
            selected_pt_name2 = st.selectbox("Escolha um segundo país", available_pt_names, key="country2")
            country2_tuple = next(c for c in country_list if c[0] == selected_pt_name2)
            pt_name2, common_name2, cca2_2, cca3_2 = country2_tuple
    
    with st.spinner(f"Carregando dados para {pt_name1}..."):
        rest1 = get_rest_country_data(common_name1, cca2_1, cca3_1)
        wb1 = get_world_bank_internet(cca3_1)
        trends1 = get_google_trends(cca2_1)
    
    if not rest1:
        st.error(f"Falha ao carregar dados para {pt_name1}")
        return
    
    rest2, wb2, trends2 = None, pd.DataFrame(), pd.DataFrame()
    if add_second and pt_name2:
        with st.spinner(f"Carregando dados para {pt_name2}..."):
            rest2 = get_rest_country_data(common_name2, cca2_2, cca3_2)
            wb2 = get_world_bank_internet(cca3_2)
            trends2 = get_google_trends(cca2_2)
        if not rest2:
            st.error(f"Falha ao carregar dados para {pt_name2}")
            return
    
    st.header(f"📊 Perfil Digital de {pt_name1}")
    st.subheader("Informações Gerais")
    col1_info, col2_info = st.columns([1,3])
    with col1_info:
        if rest1['flag']:
            st.image(rest1['flag'], width=150)
    with col2_info:
        st.markdown(f"**População**: {rest1['population']:,}")
        st.markdown(f"**Idiomas**: {', '.join(rest1['languages'])}")
        st.markdown(f"**Região**: {rest1['region']}")
    
    if not wb1.empty:
        st.subheader("Acesso à Internet ao Longo do Tempo")
        fig = px.line(wb1, x='date', y='Usuários de Internet (% da População)', title=f"Usuários de Internet em {pt_name1} (% da População)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Não há dados da World Bank sobre acesso à internet para este país.")
    
    if not trends1.empty:
        st.subheader("Tendências Recentes do Google (Top 10)")
        st.table(trends1)
    else:
        st.warning("Não há dados do Google Trends disponíveis para este país.")
    
    st.subheader("📝 Perfil Automático de Comunicação")
    st.markdown(generate_single_insights(rest1, wb1, trends1))
    
    if add_second and rest2:
        st.header(f"🔄 Comparação: {pt_name1} vs {pt_name2}")
        col1_comp, col2_comp = st.columns(2)
        with col1_comp:
            st.subheader(pt_name1)
            st.markdown(f"**População**: {rest1['population']:,}")
            st.markdown(f"**Idiomas**: {', '.join(rest1['languages'])}")
        with col2_comp:
            st.subheader(pt_name2)
            st.markdown(f"**População**: {rest2['population']:,}")
            st.markdown(f"**Idiomas**: {', '.join(rest2['languages'])}")
        
        if not wb1.empty or not wb2.empty:
            st.subheader("Comparação de Acesso à Internet")
            if not wb1.empty and not wb2.empty:
                wb1['País'] = pt_name1
                wb2['País'] = pt_name2
                combined_wb = pd.concat([wb1, wb2])
                fig = px.line(combined_wb, x='date', y='Usuários de Internet (% da População)', color='País', title="Comparação de Usuários de Internet")
                st.plotly_chart(fig, use_container_width=True)
        
        if not trends1.empty or not trends2.empty:
            st.subheader("Comparação de Tendências do Google")
            col1_trends, col2_trends = st.columns(2)
            with col1_trends:
                st.markdown(f"**{pt_name1} - Top Tendências**")
                if not trends1.empty:
                    st.table(trends1)
                else:
                    st.warning("Sem dados")
            with col2_trends:
                st.markdown(f"**{pt_name2} - Top Tendências**")
                if not trends2.empty:
                    st.table(trends2)
                else:
                    st.warning("Sem dados")
        
        st.subheader("📝 Insights Comparativos")
        st.markdown(generate_comparative_insights(rest1, wb1, trends1, rest2, wb2, trends2))
    
    st.markdown("---")
    st.markdown("Fontes de Dados: World Bank Open Data, REST Countries API, Google Trends (via pytrends)")

if __name__ == "__main__":
    main()
