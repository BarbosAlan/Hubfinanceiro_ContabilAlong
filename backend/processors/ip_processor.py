import csv
import io
import sys

csv.field_size_limit(sys.maxsize)
import datetime as dt
from dataclasses import dataclass
from typing import Optional

import pandas as pd


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
    preview_rows: int = 10


def _parse_source_date(s: str) -> Optional[dt.date]:
    try:
        part = s.split(" ")[0]
        d, m, y = part.split("-")
        return dt.date(int(y), int(m), int(d))
    except Exception:
        return None


_Q = '"'


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

    sample = content_bytes[:8192].decode(input_encoding, errors="replace")
    first_newline = sample.index("\n") if "\n" in sample else len(sample)
    try:
        dialect = csv.Sniffer().sniff(sample[:4096])
        header_fields = list(csv.reader([sample[:first_newline]], dialect))[0]
    except Exception:
        header_fields = sample[:first_newline].split(",")

    num_header_cols = len(header_fields)
    if num_header_cols < 20:
        raise ValueError(f"Layout inesperado: cabeçalho com {num_header_cols} colunas (esperado >= 20).")

    num_cols = 21 if num_header_cols >= 21 else 20

    if num_cols >= 21:
        col_status, col_date, col_type, col_amount = header_fields[17], header_fields[18], header_fields[19], header_fields[20]
    else:
        col_status, col_date, col_type, col_amount = header_fields[16], header_fields[17], header_fields[18], header_fields[19]

    col_desc      = header_fields[2]
    col_orig_name = header_fields[3]
    col_orig_acc  = header_fields[7]
    col_dest_name = header_fields[9]
    col_dest_acc  = header_fields[13]

    usecols = [col_desc, col_orig_name, col_orig_acc, col_dest_name, col_dest_acc,
               col_status, col_date, col_type, col_amount]

    total_data_lines = content_bytes.count(b"\n") - 1

    out_buf = io.BytesIO()
    out_buf.write(('\"Data\",\"Valor\",\"Resumo da Transação\"\r\n').encode(output_encoding, errors="replace"))

    total_lidas       = 0
    linhas_exportadas = 0
    soma_valor        = 0.0
    soma_valor_ok     = 0
    preview_rows: list[dict] = []

    for chunk in pd.read_csv(
        io.BytesIO(content_bytes),
        dtype=str,
        keep_default_na=False,
        on_bad_lines="skip",
        engine="c",
        low_memory=False,
        encoding=input_encoding,
        encoding_errors="replace",
        chunksize=50_000,
        usecols=usecols,
    ):
        total_lidas += len(chunk)

        if options.statuses is not None:
            chunk = chunk[chunk[col_status].str.strip().isin(options.statuses)]

        if (options.date_start or options.date_end) and not chunk.empty:
            dates = chunk[col_date].apply(_parse_source_date)
            if options.date_start:
                chunk = chunk[dates.apply(lambda d: d is not None and d >= options.date_start)]
            if options.date_end:
                chunk = chunk[dates.apply(lambda d: d is not None and d <= options.date_end)]

        if chunk.empty:
            continue

        data_col   = chunk[col_date].str[:10].str.replace("-", "/", regex=False)
        valor_col  = chunk[col_amount].fillna("").str.strip()
        desc       = chunk[col_desc].fillna("").str.strip().str.upper()
        tipo       = chunk[col_type].fillna("").str.strip().str.upper()
        orig_name  = chunk[col_orig_name].fillna("").str.strip().str.upper()
        orig_acc   = chunk[col_orig_acc].fillna("").str.strip()
        dest_name  = chunk[col_dest_name].fillna("").str.strip().str.upper()
        dest_acc   = chunk[col_dest_acc].fillna("").str.strip()
        del chunk  # libera o DataFrame do chunk antes de construir as strings

        resumo = (
            desc + " - TIPO: " + tipo + " DE R$ " + valor_col
            + " ORIGEM: " + orig_name + " (CONTA: " + orig_acc + ")"
            + " P/ DESTINO: " + dest_name + " (CONTA: " + dest_acc + ")"
        )
        del desc, tipo, orig_name, orig_acc, dest_name, dest_acc

        joined = _Q + data_col + _Q + "," + _Q + valor_col + _Q + "," + _Q + resumo + _Q
        out_buf.write(("\r\n".join(joined.values) + "\r\n").encode(output_encoding, errors="replace"))

        linhas_exportadas += len(data_col)

        if len(preview_rows) < options.preview_rows:
            needed = options.preview_rows - len(preview_rows)
            for d, v, r in zip(data_col.values[:needed], valor_col.values[:needed], resumo.values[:needed]):
                preview_rows.append({"Data": d, "Valor": v, "Resumo da Transação": r})

        numeric = pd.to_numeric(
            valor_col.str.replace(r"R\$\s*", "", regex=True)
                     .str.replace(r"\.(?=\d{3})", "", regex=True)
                     .str.replace(",", ".", regex=False),
            errors="coerce",
        )
        soma_valor    += float(numeric.sum(skipna=True))
        soma_valor_ok += int(numeric.notna().sum())
        del joined, resumo, data_col, valor_col, numeric

    linhas_nao_corrigidas = max(0, total_data_lines - total_lidas)
    soma_valor = round(soma_valor, 2)

    return {
        "output_bytes": out_buf.getvalue(),
        "errors_bytes": b"",
        "detected_input_encoding": input_encoding,
        "preview": preview_rows,
        "metrics": {
            "total_rows": total_data_lines,
            "linhas_problema": linhas_nao_corrigidas,
            "linhas_exportadas": linhas_exportadas,
            "soma_valor": soma_valor,
            "soma_valor_ok": soma_valor_ok,
        },
        "warnings": {"linhas_nao_corrigidas": linhas_nao_corrigidas},
    }
