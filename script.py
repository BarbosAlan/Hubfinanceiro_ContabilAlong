import os
import sys

from processors.ip_processor import ProcessOptions, process_csv_content


def processar_arquivo(nome_arquivo: str) -> None:
    if not os.path.exists(nome_arquivo):
        print(f'ERRO: Arquivo "{nome_arquivo}" não encontrado.')
        sys.exit(1)

    print(f'\nProcessando: {nome_arquivo}')

    with open(nome_arquivo, "rb") as f:
        content_bytes = f.read()

    result = process_csv_content(
        content_bytes,
        input_encoding="latin-1",
        options=ProcessOptions(statuses={"Completed"}),
    )
    metrics = result["metrics"]
    warnings = result["warnings"]

    print(f'  Total de linhas:               {metrics["total_rows"]:>10,}')
    print(f'  Linhas com vírgula no nome:    {metrics["linhas_problema"]:>10,}')
    if warnings.get("linhas_nao_corrigidas", 0):
        print(
            f'  ATENÇÃO: {warnings["linhas_nao_corrigidas"]} linhas não puderam ser corrigidas automaticamente.'
        )

    script_dir = os.path.dirname(os.path.abspath(__file__))
    nome_base  = os.path.splitext(os.path.basename(nome_arquivo))[0]
    nome_saida = os.path.join(script_dir, f'{nome_base}_TRATADO.csv')

    with open(nome_saida, 'wb') as f:
        f.write(result["output_bytes"])

    print(f'  Linhas Completed exportadas:   {metrics["linhas_exportadas"]:>10,}')
    print(f'  Arquivo gerado: {nome_saida}')
    print('  Concluído com sucesso!')

# ─────────────────────────────────────────
#  COLOQUE O NOME DO SEU ARQUIVO AQUI:
# ─────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Modo linha de comando: python processar_csv.py meu_arquivo.csv
        nome_arquivo = sys.argv[1]
    else:
        # Modo direto: edite a linha abaixo com o nome do arquivo
        nome_arquivo = 'IP - JUST - 885851711 - La Finteca.csv'

    processar_arquivo(nome_arquivo)