import csv
import io
import datetime as dt
from dataclasses import dataclass
from typing import Optional


def fix_row(r: list[str]) -> list[str]:
    """Corrige linhas onde DestinationName contém vírgulas e foi quebrado em múltiplas colunas."""
    if len(r) == 21:
        return r
    prefix = r[:9]
    suffix = r[-11:]
    dest_name = ",".join(r[9 : len(r) - 11])
    return prefix + [dest_name] + suffix


def format_date(date_str: str) -> str:
    """Converte 'DD-MM-YYYY HH:MM:SS' para 'DD/MM/YYYY'."""
    if date_str and "-" in date_str:
        parts = date_str.split(" ")[0]
        d, m, y = parts.split("-")
        return f"{d}/{m}/{y}"
    return date_str


def _parse_source_date(date_str: str) -> Optional[dt.date]:
    if not date_str:
        return None
    try:
        date_part = date_str.split(" ")[0]
        d, m, y = date_part.split("-")
        return dt.date(int(y), int(m), int(d))
    except Exception:
        return None


def _parse_brl_number(value: str) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("R$", "").strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def detect_encoding(content_bytes: bytes) -> str:
    try:
        content_bytes.decode("utf-8", errors="strict")
        return "utf-8"
    except Exception:
        return "latin-1"


@dataclass(frozen=True)
class ProcessOptions:
    statuses: Optional[set[str]] = None  # ex: {'Completed'}
    date_start: Optional[dt.date] = None
    date_end: Optional[dt.date] = None
    preview_rows: int = 50


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
    reader = csv.reader(io.StringIO(content))

    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("CSV vazio.")

    if len(header) < 21:
        raise ValueError(
            f"Layout inesperado: cabeçalho com {len(header)} colunas (esperado >= 21)."
        )

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(output, encoding=output_encoding, errors="replace", newline="")
    writer = csv.writer(wrapper, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    writer.writerow(["Data", "Valor", "Resumo da Transação"])

    errors_output = io.BytesIO()
    errors_wrapper = io.TextIOWrapper(
        errors_output, encoding=output_encoding, errors="replace", newline=""
    )
    errors_writer = csv.writer(errors_wrapper, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    errors_writer.writerow(["Motivo", "LinhaOriginal"])

    total_rows = 0
    linhas_problema = 0
    linhas_nao_corrigidas = 0
    linhas_exportadas = 0
    soma_valor = 0.0
    soma_valor_ok = 0
    preview: list[dict] = []

    for raw in reader:
        total_rows += 1
        if len(raw) != 21:
            linhas_problema += 1

        r = fix_row(raw)
        if len(r) != 21:
            linhas_nao_corrigidas += 1
            errors_writer.writerow(["Nao foi possivel corrigir para 21 colunas", ",".join(raw)])
            continue

        status = (r[17] or "").strip()
        if options.statuses is not None and status not in options.statuses:
            continue

        src_date = _parse_source_date(r[18])
        if options.date_start and src_date and src_date < options.date_start:
            continue
        if options.date_end and src_date and src_date > options.date_end:
            continue

        data = format_date(r[18])
        valor = r[20]
        desc = r[2].upper() if r[2] else ""
        tipo = r[19].upper()
        origin_name = r[3].upper() if r[3] else ""
        origin_acc = r[7]
        dest_name = r[9].upper() if r[9] else ""
        dest_acc = r[13]

        if desc:
            resumo = (
                f"{desc} - TIPO: {tipo} DE R$ {valor} "
                f"ORIGEM: {origin_name} (CONTA: {origin_acc}) "
                f"P/ DESTINO: {dest_name} (CONTA: {dest_acc})"
            )
        else:
            resumo = (
                f" - TIPO: {tipo} DE R$ {valor} "
                f"ORIGEM: {origin_name} (CONTA: {origin_acc}) "
                f"P/ DESTINO: {dest_name} (CONTA: {dest_acc})"
            )

        resumo = resumo.encode(output_encoding, errors="replace").decode(output_encoding)
        writer.writerow([data, valor, resumo])
        linhas_exportadas += 1

        v = _parse_brl_number(valor)
        if v is not None:
            soma_valor += v
            soma_valor_ok += 1

        if len(preview) < options.preview_rows:
            preview.append({"Data": data, "Valor": valor, "Resumo da Transação": resumo})

    wrapper.flush()
    errors_wrapper.flush()

    errors_bytes = errors_output.getvalue()
    if linhas_nao_corrigidas == 0:
        errors_bytes = b""

    return {
        "output_bytes": output.getvalue(),
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
        "warnings": {
            "linhas_nao_corrigidas": linhas_nao_corrigidas,
        },
    }

