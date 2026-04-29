## Contabil Along — Hub (Streamlit)

Este repositório é um **hub de módulos Streamlit** para tratamento de arquivos (CSV/XLSX).

### Rodar localmente

```bash
python -m pip install -r requirements.txt
streamlit run Home.py
```

### Estrutura

- `Home.py`: página inicial (hub)
- `pages/`: páginas (módulos)
- `processors/`: regras de negócio (sem Streamlit)

### Deploy (grátis) no Streamlit Community Cloud

- Suba o repositório para o GitHub
- No Streamlit Community Cloud, selecione o app e aponte o “Main file path” para `Home.py`

### Módulos atuais

- **Importação Transações IP (CSV)**: `pages/01_Importacao_Transacoes_IP.py`
- **Tratador de Extrato Genial (XLSX)**: `pages/02_Extrato_Genial.py`

