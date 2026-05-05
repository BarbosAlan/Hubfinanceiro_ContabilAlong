import csv
import io
import sys

csv.field_size_limit(sys.maxsize)
import datetime as dt
from dataclasses import dataclass
from typing import Optional

import pandas as pd


def fix_row(r: list[str]) -> list[str]:
    """Corrige linhas onde DestinationName contém vírgulas e foi quebrado em múltiplas colunas."""
    if len(r) == 21:
        return r
    prefix = r[:9]
    suffix = r[-11:]
    dest_name = ",".join(r[9 : len(r) - 11])
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


def _parse_brl_series(series: pd.Series) -> pd.Series:
    s = series.fillna("").astype(str).str.strip()
    s = s.str.replace(r"R\$\s*", "", regex=True).str.strip()
    mask_both = s.str.contains(r"\.", regex=False) & s.str.contains(",")
    s = s.copy()
    s[mask_both] = s[mask_both].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    mask_comma = ~mask_both & s.str.contains(",")
    s[mask_comma] = s[mask_comma].str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _format_date(s: str) -> str:
    if s and "-" in s:
        part = s.split(" ")[0]
        d, m, y = part.split("-")
        return f"{d}/{m}/{y}"
    return s


def _parse_source_date(s: str) -> Optional[dt.date]:
    try:
        part = s.split(" ")[0]
        d, m, y = part.split("-")
        return dt.date(int(y), int(m), int(d))
    except Exception:
        return None


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
    
    try:
        dialect = csv.Sniffer().sniff(content[:4096])
        reader = csv.reader(io.StringIO(content), dialect=dialect)
    except Exception:
        reader = csv.reader(io.StringIO(content))

    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("CSV vazio.")

    if len(header) < 21:
        raise ValueError(f"Layout inesperado: cabeçalho com {len(header)} colunas (esperado >= 21).")

    rows: list[list[str]] = []
    error_rows: list[list[str]] = []
    linhas_problema = 0
    linhas_nao_corrigidas = 0

    for raw in reader:
        if len(raw) != 21:
            linhas_problema += 1
            fixed = fix_row(raw)
            if len(fixed) != 21:
                linhas_nao_corrigidas += 1
                error_rows.append(["Nao foi possivel corrigir para 21 colunas", ",".join(raw)])
                continue
            rows.append(fixed)
        else:
            rows.append(raw)

    total_rows = len(rows) + linhas_nao_corrigidas

    _empty_result = {
        "output_bytes": b"",
        "errors_bytes": b"",
        "detected_input_encoding": input_encoding,
        "preview": [],
        "metrics": {
            "total_rows": total_rows,
            "linhas_problema": linhas_problema,
            "linhas_exportadas": 0,
            "soma_valor": 0.0,
            "soma_valor_ok": 0,
        },
        "warnings": {"linhas_nao_corrigidas": linhas_nao_corrigidas},
    }

    if not rows:
        return _empty_result

    col = [f"c{i}" for i in range(21)]
    df = pd.DataFrame(rows, columns=col)

    # Filtro por status (coluna 17)
    if options.statuses is not None:
        df = df[df["c17"].str.strip().isin(options.statuses)]

    # Filtro por data (coluna 18)
    if (options.date_start or options.date_end) and not df.empty:
        dates = df["c18"].apply(_parse_source_date)
        if options.date_start:
            df = df[dates.apply(lambda d: d is not None and d >= options.date_start)]
        if options.date_end:
            df = df[dates.apply(lambda d: d is not None and d <= options.date_end)]

    if df.empty:
        return _empty_result

    # Colunas de saída
    data_col = df["c18"].apply(_format_date)
    valor_col = df["c20"].fillna("")

    # Resumo vetorizado
    desc = df["c2"].fillna("").str.upper()
    tipo = df["c19"].fillna("").str.upper()
    origin_name = df["c3"].fillna("").str.upper()
    origin_acc = df["c7"].fillna("")
    dest_name = df["c9"].fillna("").str.upper()
    dest_acc = df["c13"].fillna("")

    suffix = (
        " - TIPO: " + tipo + " DE R$ " + valor_col
        + " ORIGEM: " + origin_name + " (CONTA: " + origin_acc + ")"
        + " P/ DESTINO: " + dest_name + " (CONTA: " + dest_acc + ")"
    )
    resumo_col = desc + suffix

    df_out = pd.DataFrame({
        "Data": data_col.values,
        "Valor": valor_col.values,
        "Resumo da Transação": resumo_col.values,
    })

    linhas_exportadas = len(df_out)

    numeric_valores = _parse_brl_series(df_out["Valor"])
    soma_valor = float(numeric_valores.sum(skipna=True))
    soma_valor_ok = int(numeric_valores.notna().sum())

    csv_str = df_out.to_csv(index=False, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    output_bytes = csv_str.encode(output_encoding, errors="replace")

    errors_bytes = b""
    if error_rows:
        buf = io.BytesIO()
        wrapper = io.TextIOWrapper(buf, encoding=output_encoding, errors="replace", newline="")
        w = csv.writer(wrapper, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        w.writerow(["Motivo", "LinhaOriginal"])
        for row in error_rows:
            w.writerow(row)
        wrapper.flush()
        errors_bytes = buf.getvalue()

    preview = df_out.head(options.preview_rows).to_dict(orient="records")

    return {
        "output_bytes": output_bytes,
        "errors_bytes": errors_bytes,
        "detected_input_encoding": input_encoding,
        "preview": preview,
        "metrics": {
            "total_rows": total_rows,
            "linhas_problema": linhas_problema,
            "linhas_exportadas": linhas_exportadas,
            "soma_valor": soma_valor,
            "soma_valor_ok": soma_valor_ok,
        },
        "warnings": {"linhas_nao_corrigidas": linhas_nao_corrigidas},
    }
