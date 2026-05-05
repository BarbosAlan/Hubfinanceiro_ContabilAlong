import csv
import io
import sys

csv.field_size_limit(sys.maxsize)
import datetime as dt
from dataclasses import dataclass
from typing import Optional

import pandas as pd


def fix_row(r: list[str], expected: int = 21) -> list[str]:
    """Corrige linhas onde DestinationName contém vírgulas e foi quebrado em múltiplas colunas."""
    if len(r) == expected:
        return r
    suffix_len = expected - 10
    prefix = r[:9]
    suffix = r[-suffix_len:]
    dest_name = ",".join(r[9 : len(r) - suffix_len])
    return prefix + [dest_name] + suffix


def detect_encoding(content_bytes: bytes) -> str:
    try:
        content_bytes.decode("utf-8", errors="strict")
        return "utf-8"
    except Exception:
        return "latin-1"


@dataclass(frozen=True)
class ProcessOptions:
    statuses: Optional[set[str]] = None
    date_start: Optional[dt.date] = None
    date_end: Optional[dt.date] = None
    preview_rows: int = 50


def _parse_source_date(s: str) -> Optional[dt.date]:
    try:
        part = s.split(" ")[0]
        d, m, y = part.split("-")
        return dt.date(int(y), int(m), int(d))
    except Exception:
        return None


def _read_with_pandas(content: str) -> tuple[pd.DataFrame, int]:
    """Lê o CSV com o parser C do pandas (rápido). Retorna (df, linhas_puladas)."""
    buf = io.StringIO(content)
    df = pd.read_csv(
        buf,
        dtype=str,
        keep_default_na=False,
        on_bad_lines="skip",
        engine="c",
        low_memory=False,
    )
    # Conta linhas puladas (on_bad_lines='skip') comparando com contagem rápida
    total_data_lines = content.count("\n") - 1  # -1 pelo header
    linhas_puladas = max(0, total_data_lines - len(df))
    return df, linhas_puladas


def process_csv_content(
    content_bytes: bytes,
    *,
    input_encoding: Optional[str] = "latin-1",
    output_encoding: str = "latin-1",
    options: Optional[ProcessOptions] = None,
) -> dict:
    if options is None:
        options = ProcessOptions(statuses={"Completed"})

    if input_encoding is None:
        input_encoding = detect_encoding(content_bytes)

    content = content_bytes.decode(input_encoding, errors="replace")

    # Detecta número de colunas via header
    first_newline = content.index("\n") if "\n" in content else len(content)
    try:
        dialect = csv.Sniffer().sniff(content[:4096])
        header_fields = list(csv.reader([content[:first_newline]], dialect))[0]
    except Exception:
        header_fields = content[:first_newline].split(",")

    num_header_cols = len(header_fields)
    if num_header_cols < 20:
        raise ValueError(f"Layout inesperado: cabeçalho com {num_header_cols} colunas (esperado >= 20).")

    num_cols = 21 if num_header_cols >= 21 else 20

    # Mapeamento de índices conforme layout
    if num_cols >= 21:
        col_status, col_date, col_type, col_amount = header_fields[17], header_fields[18], header_fields[19], header_fields[20]
    else:
        col_status, col_date, col_type, col_amount = header_fields[16], header_fields[17], header_fields[18], header_fields[19]

    col_desc     = header_fields[2]
    col_orig_name = header_fields[3]
    col_orig_acc  = header_fields[7]
    col_dest_name = header_fields[9]
    col_dest_acc  = header_fields[13]

    # Leitura principal com parser C do pandas
    df, linhas_nao_corrigidas = _read_with_pandas(content)
    total_rows = len(df) + linhas_nao_corrigidas

    _empty = {
        "output_bytes": b"",
        "errors_bytes": b"",
        "detected_input_encoding": input_encoding,
        "preview": [],
        "metrics": {
            "total_rows": total_rows,
            "linhas_problema": linhas_nao_corrigidas,
            "linhas_exportadas": 0,
            "soma_valor": 0.0,
            "soma_valor_ok": 0,
        },
        "warnings": {"linhas_nao_corrigidas": linhas_nao_corrigidas},
    }

    if df.empty:
        return _empty

    # Filtro por status
    if options.statuses is not None:
        df = df[df[col_status].str.strip().isin(options.statuses)]

    # Filtro por data
    if (options.date_start or options.date_end) and not df.empty:
        dates = df[col_date].apply(_parse_source_date)
        if options.date_start:
            df = df[dates.apply(lambda d: d is not None and d >= options.date_start)]
        if options.date_end:
            df = df[dates.apply(lambda d: d is not None and d <= options.date_end)]

    if df.empty:
        return _empty

    # Geração de colunas de saída — tudo vetorizado
    data_col   = df[col_date].str[:10].str.replace("-", "/", regex=False)
    valor_col  = df[col_amount].fillna("").str.strip()
    desc       = df[col_desc].fillna("").str.strip().str.upper()
    tipo       = df[col_type].fillna("").str.strip().str.upper()
    orig_name  = df[col_orig_name].fillna("").str.strip().str.upper()
    orig_acc   = df[col_orig_acc].fillna("").str.strip()
    dest_name  = df[col_dest_name].fillna("").str.strip().str.upper()
    dest_acc   = df[col_dest_acc].fillna("").str.strip()

    resumo = (
        desc + " - TIPO: " + tipo + " DE R$ " + valor_col
        + " ORIGEM: " + orig_name + " (CONTA: " + orig_acc + ")"
        + " P/ DESTINO: " + dest_name + " (CONTA: " + dest_acc + ")"
    )

    df_out = pd.DataFrame({"Data": data_col.values, "Valor": valor_col.values, "Resumo da Transação": resumo.values})

    linhas_exportadas = len(df_out)

    numeric = pd.to_numeric(
        valor_col.str.replace(r"R\$\s*", "", regex=True)
                 .str.replace(r"\.(?=\d{3})", "", regex=True)
                 .str.replace(",", ".", regex=False),
        errors="coerce",
    )
    soma_valor = round(float(numeric.sum(skipna=True)), 2)
    soma_valor_ok = int(numeric.notna().sum())

    csv_str = df_out.to_csv(index=False, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    output_bytes = csv_str.encode(output_encoding, errors="replace")

    preview = df_out.head(options.preview_rows).to_dict(orient="records")

    return {
        "output_bytes": output_bytes,
        "errors_bytes": b"",
        "detected_input_encoding": input_encoding,
        "preview": preview,
        "metrics": {
            "total_rows": total_rows,
            "linhas_problema": linhas_nao_corrigidas,
            "linhas_exportadas": linhas_exportadas,
            "soma_valor": soma_valor,
            "soma_valor_ok": soma_valor_ok,
        },
        "warnings": {"linhas_nao_corrigidas": linhas_nao_corrigidas},
    }
