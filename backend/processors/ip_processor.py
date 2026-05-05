import csv
import io
import sys

csv.field_size_limit(sys.maxsize)
import datetime as dt
from dataclasses import dataclass
from typing import Optional


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


def _parse_brl(s: str) -> Optional[float]:
    s = s.strip().replace("R$", "").strip()
    if not s:
        return None
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


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

    if len(header) < 20:
        raise ValueError(f"Layout inesperado: cabeçalho com {len(header)} colunas (esperado >= 20).")

    num_cols = 21 if len(header) >= 21 else 20

    # Índices conforme layout
    if num_cols >= 21:
        i_status, i_date, i_type, i_amount = 17, 18, 19, 20
    else:
        i_status, i_date, i_type, i_amount = 16, 17, 18, 19

    # Buffers de saída
    out_buf = io.BytesIO()
    out_wrapper = io.TextIOWrapper(out_buf, encoding=output_encoding, errors="replace", newline="")
    out_writer = csv.writer(out_wrapper, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    out_writer.writerow(["Data", "Valor", "Resumo da Transação"])

    err_rows: list[list[str]] = []
    preview: list[dict] = []

    total_rows = 0
    linhas_problema = 0
    linhas_nao_corrigidas = 0
    linhas_exportadas = 0
    soma_valor = 0.0
    soma_valor_ok = 0

    for raw in reader:
        total_rows += 1

        if len(raw) != num_cols:
            linhas_problema += 1
            fixed = fix_row(raw, num_cols)
            if len(fixed) != num_cols:
                linhas_nao_corrigidas += 1
                err_rows.append([f"Nao foi possivel corrigir para {num_cols} colunas", ",".join(raw)])
                continue
            raw = fixed

        # Filtro por status
        if options.statuses is not None and raw[i_status].strip() not in options.statuses:
            continue

        # Filtro por data
        if options.date_start or options.date_end:
            d = _parse_source_date(raw[i_date])
            if options.date_start and (d is None or d < options.date_start):
                continue
            if options.date_end and (d is None or d > options.date_end):
                continue

        date_str = _format_date(raw[i_date])
        valor_str = raw[i_amount].strip()
        desc = raw[2].strip().upper()
        tipo = raw[i_type].strip().upper()
        origin_name = raw[3].strip().upper()
        origin_acc = raw[7].strip()
        dest_name = raw[9].strip().upper()
        dest_acc = raw[13].strip()

        resumo = (
            f"{desc} - TIPO: {tipo} DE R$ {valor_str}"
            f" ORIGEM: {origin_name} (CONTA: {origin_acc})"
            f" P/ DESTINO: {dest_name} (CONTA: {dest_acc})"
        )

        out_writer.writerow([date_str, valor_str, resumo])
        linhas_exportadas += 1

        v = _parse_brl(valor_str)
        if v is not None:
            soma_valor += v
            soma_valor_ok += 1

        if len(preview) < options.preview_rows:
            preview.append({"Data": date_str, "Valor": valor_str, "Resumo da Transação": resumo})

    out_wrapper.flush()
    output_bytes = out_buf.getvalue()

    errors_bytes = b""
    if err_rows:
        ebuf = io.BytesIO()
        ewrapper = io.TextIOWrapper(ebuf, encoding=output_encoding, errors="replace", newline="")
        ewriter = csv.writer(ewrapper, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
        ewriter.writerow(["Motivo", "LinhaOriginal"])
        for row in err_rows:
            ewriter.writerow(row)
        ewrapper.flush()
        errors_bytes = ebuf.getvalue()

    return {
        "output_bytes": output_bytes,
        "errors_bytes": errors_bytes,
        "detected_input_encoding": input_encoding,
        "preview": preview,
        "metrics": {
            "total_rows": total_rows,
            "linhas_problema": linhas_problema,
            "linhas_exportadas": linhas_exportadas,
            "soma_valor": round(soma_valor, 2),
            "soma_valor_ok": soma_valor_ok,
        },
        "warnings": {"linhas_nao_corrigidas": linhas_nao_corrigidas},
    }
