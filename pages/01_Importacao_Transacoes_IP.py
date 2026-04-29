import io
import os
import zipfile

import streamlit as st

from processors.ip_processor import ProcessOptions, process_csv_content
from ui.layout import page_layout


st.set_page_config(page_title="Importação Transações IP", layout="wide")
page_layout(active_key="ip", title="Importação IP", breadcrumb="Importação IP")

st.markdown(
    """
    <div class="card" style="margin-bottom: 12px;">
      <div style="font-weight: 800; font-size: 16px; color: #1a1a2e;">Importação Transações IP</div>
      <div style="margin-top: 4px; color: #6b7280; font-size: 13px;">
        Upload de CSVs → filtra <b>Completed</b> → corrige vírgulas em nomes → baixa <code>_TRATADO.csv</code>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_files = st.file_uploader(
    "Selecione o(s) arquivo(s) CSV",
    type=["csv"],
    accept_multiple_files=True,
)

input_encoding = "latin-1"
output_encoding = "latin-1"
with st.expander("Opções avançadas (encoding)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        input_encoding = st.selectbox("Encoding de entrada", ["latin-1", "utf-8"], index=0)
    with col2:
        output_encoding = st.selectbox("Encoding de saída", ["latin-1", "utf-8"], index=0)

if not uploaded_files:
    st.info("Envie um ou mais arquivos para começar.")
    st.stop()

processar_btn = st.button("Processar arquivo(s)", type="primary")

if not processar_btn:
    st.stop()

results: list[dict] = []
errors: list[tuple[str, str]] = []

with st.spinner("Processando arquivo(s)..."):
    for uf in uploaded_files:
        try:
            result = process_csv_content(
                uf.getvalue(),
                input_encoding=input_encoding,
                output_encoding=output_encoding,
                options=ProcessOptions(statuses={"Completed"}, preview_rows=50),
            )
            results.append(
                {
                    "name": uf.name,
                    "output_bytes": result["output_bytes"],
                    "errors_bytes": result["errors_bytes"],
                    "metrics": result["metrics"],
                    "warnings": result["warnings"],
                    "preview": result["preview"],
                }
            )
        except Exception as e:
            errors.append((uf.name, str(e)))

if errors:
    st.error("Alguns arquivos falharam ao processar:")
    for name, msg in errors:
        st.write(f"- `{name}`: {msg}")

if not results:
    st.stop()
    
st.success("Processamento concluído com sucesso!")

st.markdown('<div class="section-title">RESUMO DA IMPORTAÇÃO</div>', unsafe_allow_html=True)

total_rows = sum(r["metrics"]["total_rows"] for r in results)
linhas_problema = sum(r["metrics"]["linhas_problema"] for r in results)
linhas_exportadas = sum(r["metrics"]["linhas_exportadas"] for r in results)
linhas_nao_corrigidas = sum(r["warnings"]["linhas_nao_corrigidas"] for r in results)

st.markdown(
    f"""
    <div class="stat-grid" style="grid-template-columns: repeat(4, 1fr);">
      <div class="card">
        <div class="stat-label">ARQUIVOS</div>
        <div class="stat-value">{len(results)}</div>
      </div>
      <div class="card">
        <div class="stat-label">TOTAL (LINHAS)</div>
        <div class="stat-value">{total_rows:,}</div>
      </div>
      <div class="card">
        <div class="stat-label">VÍRGULAS DETECTADAS</div>
        <div class="stat-value">{linhas_problema:,}</div>
      </div>
      <div class="card">
        <div class="stat-label">EXPORTADOS (OK)</div>
        <div class="stat-value">{linhas_exportadas:,}</div>
      </div>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True,
)

if linhas_nao_corrigidas > 0:
    st.warning(
        f"{linhas_nao_corrigidas} linha(s) não puderam ser corrigidas automaticamente e foram ignoradas."
    )

st.markdown('<div class="section-title">DOWNLOADS E RESULTADOS</div>', unsafe_allow_html=True)
if len(results) == 1:
    base, _ = os.path.splitext(results[0]["name"])
    st.download_button(
        "⬇ Baixar CSV tratado",
        data=results[0]["output_bytes"],
        file_name=f"{base}_TRATADO.csv",
        mime="text/csv",
        type="primary",
    )
else:
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for r in results:
            base, _ = os.path.splitext(r["name"])
            z.writestr(f"{base}_TRATADO.csv", r["output_bytes"])
    zip_buf.seek(0)

    st.download_button(
        "⬇ Baixar .zip com todos os tratados",
        data=zip_buf.getvalue(),
        file_name="tratados.zip",
        mime="application/zip",
        type="primary",
    )

with st.expander("Detalhes por arquivo"):
    for r in results:
        st.write(
            f'- `{r["name"]}` → exportadas: **{r["metrics"]["linhas_exportadas"]}** '
            f'| problemas: **{r["metrics"]["linhas_problema"]}** '
            f'| não corrigidas: **{r["warnings"]["linhas_nao_corrigidas"]}**'
        )

with st.expander("Pré-visualização (primeiras linhas)"):
    for r in results:
        st.markdown(f"**{r['name']}**")
        st.dataframe(r["preview"], use_container_width=True, hide_index=True)

with st.expander("Linhas não corrigidas (download)"):
    downloadable = [r for r in results if r.get("errors_bytes")]
    if not downloadable:
        st.info("Nenhuma linha problemática ficou sem correção.")
    else:
        for r in downloadable:
            base, _ = os.path.splitext(r["name"])
            st.download_button(
                f"Baixar erros — {r['name']}",
                data=r["errors_bytes"],
                file_name=f"{base}_ERROS.csv",
                mime="text/csv",
            )

# Update global stats (session)
st.session_state["global_files_processed"] = st.session_state.get("global_files_processed", 0) + len(
    results
)
st.session_state["global_lines_processed"] = st.session_state.get("global_lines_processed", 0) + int(
    linhas_exportadas
)

