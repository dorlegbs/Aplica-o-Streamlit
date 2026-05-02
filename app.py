import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# =========================
# CONFIGURAÇÕES DA INTERFACE
# =========================

# Define as configurações globais da página (título e ícone da aba) e aplica um estilo visual customizado usando CSS para modificar cores, fontes e o layout dos cartões.

st.set_page_config(
    page_title="Comunicação Digital Global",
    page_icon="🌍",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #333333;
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

# Contém uma função auxiliar que gera a URL da imagem da bandeira do país selecionado através do FlagCDN.

def get_flag_url(rest_data: dict) -> str:
    if not rest_data:
        return ""
    cca2 = (rest_data.get('cca2') or '').lower()
    return f"https://flagcdn.com/w320/{cca2}.png"


# =========================
# DADOS
# =========================

#Obtém a lista de todos os países da API REST Countries.

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

#Busca detalhes específicos de um país (idiomas, população).

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

#Usa a API do World Bank para obter o histórico de acesso à internet ao longo dos anos.

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
            x=wb1['date'].dt.year, y=wb1['growth'].round(1),
            name=name1,
            marker_color=['#2a9e5c' if v >= 0 else '#d94f4f' for v in wb1['growth'].fillna(0)],
        ))
    if wb2 is not None and not wb2.empty and len(wb2) > 1:
        wb2 = wb2.copy()
        wb2['growth'] = wb2['Internet'].pct_change() * 100
        fig.add_trace(go.Bar(
            x=wb2['date'].dt.year, y=wb2['growth'].round(1),
            name=name2,
            marker_color='#e28a1a',
            opacity=0.75,
        ))
    fig.update_layout(**CHART_LAYOUT, height=260,
                      yaxis_ticksuffix="%", barmode='group')
    return fig


# =========================
# FUNCIONAMENTO DO APP
# =========================

#Inicia a função principal (main) e carrega a lista inicial de nomes de países que serão usados nos menus de seleção.

def main():
    countries = get_all_countries()
    names = [c[0] for c in countries]

# =========================
# SIDEBAR
# =========================

#Cria o menu lateral onde o usuário escolhe o país principal, ativa ou desativa a comparação com um segundo país e seleciona quais métricas deseja visualizar.
    
    with st.sidebar:
        st.markdown("### 🌍 Comunicação Digital Global")
        st.markdown("---")

        st.markdown("**País principal**")
        country1_name = st.selectbox("", names, label_visibility="collapsed")
        country1 = next(c for c in countries if c[0] == country1_name)

        st.markdown("---")

        st.markdown("**Comparar com**")
        compare = st.checkbox("Ativar comparação")
        country2 = None
        country2_name = None
        if compare:
            names2 = [n for n in names if n != country1_name]
            country2_name = st.selectbox(" ", names2, label_visibility="collapsed")
            country2 = next(c for c in countries if c[0] == country2_name)

        st.markdown("---")

        st.markdown("**Exibir**")
        show_internet   = st.checkbox("Acesso à Internet", value=True)
        show_social     = st.checkbox("Redes Sociais (est.)", value=True)
        show_population = st.checkbox("População", value=True)

        st.markdown("---")
        st.caption("Fontes: REST Countries · World Bank")

# =========================
# DADOS
# =========================

#Executa as chamadas de API para os países selecionados e realiza cálculos estatísticos, como a estimativa de usuários de redes sociais (baseada em 75% dos usuários de internet).
    
    rest1 = get_rest_country_data(country1[3])
    wb1   = get_world_bank_internet(country1[3])

    rest2 = get_rest_country_data(country2[3]) if country2 else None
    wb2   = get_world_bank_internet(country2[3]) if country2 else pd.DataFrame()

    latest1 = wb1.iloc[-1]['Internet'] if not wb1.empty else None
    latest2 = wb2.iloc[-1]['Internet'] if not wb2.empty else None
    social1 = latest1 * 0.75 if latest1 else None
    social2 = latest2 * 0.75 if latest2 else None
    pop1    = rest1['population'] if rest1 else None
    pop2    = rest2['population'] if rest2 else None

# =========================
# CABEÇALHO
# =========================

#Renderiza o título dinâmico da página, que muda conforme os países selecionados, e adiciona o subtítulo da aplicação.
    
    title_html = f" {country1_name}"
    if compare and country2_name:
        title_html += f' <span class="badge-compare">⇄ Comparando com {country2_name}</span>'
    st.markdown(f'<div class="page-title">{title_html}</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Análise de conectividade e comunicação digital</div>', unsafe_allow_html=True)

# =========================
# BANDEIRAS
# =========================

#Exibe as imagens das bandeiras dos países escolhidos no topo da página para identificação visual rápida.
    
    if rest1:
        flag_cols = st.columns([1, 8]) if not compare else st.columns([1, 1, 6])
        with flag_cols[0]:
            st.image(get_flag_url(rest1), width=80)
        if compare and rest2:
            with flag_cols[1]:
                st.image(get_flag_url(rest2), width=80)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

# =========================
# MÉTRICAS
# =========================

#Apresenta os números principais (população, % de internet, idiomas) em cartões destacados, mostrando a diferença (delta) caso a comparação esteja ativada.
    
    metric_cols = st.columns(4)

    if show_population:
        with metric_cols[0]:
            st.metric(
                label=f"População — {rest1['name'] if rest1 else ''}",
                value=f"{pop1:,}" if pop1 else "N/A",
                delta=f"vs {pop2:,}" if pop2 else None,
            )
    if show_internet:
        with metric_cols[1]:
            st.metric(
                label=f"Internet — {rest1['name'] if rest1 else ''}",
                value=f"{latest1:.1f}%" if latest1 else "N/A",
                delta=f"{latest1 - latest2:+.1f}pp vs {rest2['name']}" if (latest1 and latest2) else None,
            )
    if show_social:
        with metric_cols[2]:
            st.metric(
                label="Redes Sociais (est.)",
                value=f"{social1:.1f}%" if social1 else "N/A",
                delta=f"{social1 - social2:+.1f}pp" if (social1 and social2) else None,
            )
    with metric_cols[3]:
        lang_str = ', '.join(rest1['languages'][:2]) if rest1 else "N/A"
        st.metric(label="🗣️ Idiomas", value=lang_str)

    st.markdown("")

# =========================
# GRÁFICOS
# =========================

#Gera e exibe visualmente a evolução histórica do acesso à internet e o crescimento anual, organizando-os em duas colunas.
    
    if show_internet and not wb1.empty:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown('<div class="section-card">'
                        '<div class="section-title">Evolução do acesso à internet</div>'
                        '<div class="section-sub">% da população com acesso à internet ao longo dos anos</div>',
                        unsafe_allow_html=True)
            fig = internet_line_chart(
                wb1, wb2 if compare else None,
                name1=rest1['name'] if rest1 else country1_name,
                name2=rest2['name'] if rest2 else (country2_name or "")
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="section-card">'
                        '<div class="section-title">Crescimento anual</div>'
                        '<div class="section-sub">Variação percentual anual no acesso à internet</div>',
                        unsafe_allow_html=True)
            fig2 = mom_growth_chart(
                wb1, wb2 if compare else None,
                name1=rest1['name'] if rest1 else country1_name,
                name2=rest2['name'] if rest2 else (country2_name or "")
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# =========================
# BARRA COMPARATIVA (POPULAÇÃO)
# =========================

#Cria um gráfico de barras específico para comparar visualmente o tamanho das populações entre os dois países selecionados.
    
    if show_population and compare and pop1 and pop2:
        st.markdown('<div class="section-card">'
                    '<div class="section-title">Comparação de população</div>'
                    '<div class="section-sub">Habitantes totais por país</div>',
                    unsafe_allow_html=True)
        fig3 = bar_comparison_chart(
            labels=[rest1['name'], rest2['name']],
            values=[pop1, pop2],
            colors=['#378add', '#e28a1a'],
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# REDES SOCIAIS
# =========================

#Mostra barras de progresso que representam a porcentagem estimada da população que utiliza redes sociais em cada país.
    
    if show_social:
        st.markdown('<div class="section-card">'
                    '<div class="section-title">Estimativa de uso de redes sociais</div>'
                    '<div class="section-sub">Estimativa baseada em 75% dos usuários de internet</div>',
                    unsafe_allow_html=True)
        s_cols = st.columns(2 if compare else 1)
        with s_cols[0]:
            if social1:
                st.progress(int(social1), text=f"{rest1['name'] if rest1 else country1_name}: {social1:.1f}%")
            else:
                st.warning("Sem dados suficientes")
        if compare and len(s_cols) > 1:
            with s_cols[1]:
                if social2:
                    st.progress(int(social2), text=f"{rest2['name'] if rest2 else country2_name}: {social2:.1f}%")
                else:
                    st.warning("Sem dados suficientes")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# TABELA COMPARATIVA
# =========================

#Gera uma tabela final de resumo com todos os dados e indicadores lado a lado.
    
    if compare and rest1 and rest2:
        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Resumo comparativo</div>', unsafe_allow_html=True)
        st.markdown("")

        df_compare = pd.DataFrame({
            "Indicador": ["População", "Internet (%)", "Redes sociais est. (%)", "Idiomas", "Código"],
            rest1['name']: [
                f"{pop1:,}" if pop1 else "N/A",
                f"{latest1:.1f}%" if latest1 else "N/A",
                f"{social1:.1f}%" if social1 else "N/A",
                ', '.join(rest1['languages']),
                rest1['cca3'],
            ],
            rest2['name']: [
                f"{pop2:,}" if pop2 else "N/A",
                f"{latest2:.1f}%" if latest2 else "N/A",
                f"{social2:.1f}%" if social2 else "N/A",
                ', '.join(rest2['languages']),
                rest2['cca3'],
            ],
        })
        st.dataframe(df_compare, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

