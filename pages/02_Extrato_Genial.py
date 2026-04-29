import streamlit as st

from processors.genial_processor import GenialTargets, format_genial_excel, process_genial_excel
from ui.layout import page_layout


st.set_page_config(page_title="Tratador de Extrato Genial", layout="wide")
page_layout(active_key="genial", title="Extrato Genial", breadcrumb="Extrato Genial")

st.markdown(
    """
    <div class="card" style="margin-bottom: 12px;">
      <div style="font-weight: 800; font-size: 16px; color: #1a1a2e;">Tratador de Extrato Genial</div>
      <div style="margin-top: 4px; color: #6b7280; font-size: 13px;">
        Upload do Excel → agrupa PAY IN/OUT e bloqueios judiciais → baixa <code>_tratado.xlsx</code>.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Selecione o arquivo Excel (.xlsx)",
    type=["xlsx"],
)

targets = GenialTargets()

st.markdown("### Alvos de agrupamento")
st.write(", ".join(targets.all))

processar_btn = st.button("Processar arquivo", type="primary", disabled=uploaded_file is None)

if not processar_btn:
    st.stop()

if uploaded_file is None:
    st.stop()

with st.spinner("Processando..."):
    try:
        df_final, stats = process_genial_excel(uploaded_file.getvalue(), targets=targets.all)
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        st.stop()

st.success("Processamento concluído com sucesso!")

st.markdown('<div class="section-title">RESUMO DO PROCESSAMENTO</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="stat-grid" style="grid-template-columns: repeat(4, 1fr);">
      <div class="card">
        <div class="stat-label">LINHAS ORIGINAIS</div>
        <div class="stat-value">{stats['linhas_originais']:,}</div>
      </div>
      <div class="card">
        <div class="stat-label">OUTROS MANTIDOS</div>
        <div class="stat-value">{stats['outros_mantidos']:,}</div>
      </div>
      <div class="card">
        <div class="stat-label">AGRUPADOS (ITENS)</div>
        <div class="stat-value">{stats['agrupados']:,}</div>
      </div>
      <div class="card">
        <div class="stat-label">TOTAL NA SÁIDA</div>
        <div class="stat-value">{stats['total_saida']:,}</div>
      </div>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">PRÉ-VISUALIZAÇÃO DOS DADOS</div>', unsafe_allow_html=True)
st.dataframe(
    df_final.head(25),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Data": st.column_config.DateColumn("Data"),
        "HISTORICO": st.column_config.TextColumn("Histórico"),
        "Valor": st.column_config.NumberColumn("Valor", format="%.2f"),
        "HISTORICO DE LANÇAMENTO": st.column_config.TextColumn("Hist. Lançamento"),
    },
)
if len(df_final) > 25:
    st.caption(f"Mostrando 25 de {len(df_final)} linhas...")

st.markdown('<div class="section-title">DOWNLOADS E RESULTADOS</div>', unsafe_allow_html=True)
excel_output = format_genial_excel(df_final, targets=targets.all)
nome_arquivo = uploaded_file.name.replace(".xlsx", "_tratado.xlsx")

st.download_button(
    label="Baixar Excel tratado",
    data=excel_output,
    file_name=nome_arquivo,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
)

# Update global stats (session)
st.session_state["global_files_processed"] = st.session_state.get("global_files_processed", 0) + 1
st.session_state["global_lines_processed"] = st.session_state.get("global_lines_processed", 0) + int(
    stats["total_saida"]
)

