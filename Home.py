import streamlit as st

from ui.layout import page_layout


st.set_page_config(page_title="Contabil Along — Hub", layout="wide", initial_sidebar_state="expanded")
page_layout(active_key="dashboard", title="Início", breadcrumb="Início")

files_processed = st.session_state.get("global_files_processed", 0)
lines_processed = st.session_state.get("global_lines_processed", 0)

st.markdown(
    f"""
    <div class="stat-grid">
      <div class="card">
        <div class="stat-label">MÓDULOS ATIVOS</div>
        <div class="stat-value">2</div>
      </div>
      <div class="card">
        <div class="stat-label">ARQUIVOS PROCESSADOS</div>
        <div class="stat-value">{files_processed}</div>
      </div>
      <div class="card">
        <div class="stat-label">TOTAL DE LINHAS TRATADAS</div>
        <div class="stat-value">{lines_processed}</div>
      </div>
    </div>
    <div class="section-title">MÓDULOS DISPONÍVEIS</div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* Transforma a coluna inteira do módulo em um botão clicável */
    div[data-testid="column"] {
        position: relative;
    }
    div[data-testid="column"] div[data-testid="stPageLink"] {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        opacity: 0; /* Invisível, mas clicável */
        z-index: 10;
    }
    div[data-testid="column"] div[data-testid="stPageLink"]:hover {
        cursor: pointer;
    }
    div[data-testid="column"]:hover .module-card {
        transform: translateY(-4px);
        box-shadow: 0 12px 28px rgba(0,0,0,0.05);
        border-color: rgba(26,26,46,0.12);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        <div class="module-card">
          <div class="module-icon">⇄</div>
          <div class="module-title">Importação Transações IP</div>
          <div class="module-desc">
            Processa arquivos CSV de transações, filtra status Completed e corrige vírgulas em nomes.
            Exporta CSV(s) tratados.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/01_Importacao_Transacoes_IP.py", label="Ir para modulo")

with col2:
    st.markdown(
        """
        <div class="module-card">
          <div class="module-icon">◈</div>
          <div class="module-title">Tratador de Extrato Genial</div>
          <div class="module-desc">
            Agrupa lançamentos PAY IN/OUT e débitos judiciais por data, gera Excel formatado.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/02_Extrato_Genial.py", label="Ir para modulo")


