import asyncio
import base64
import gzip
import io
import json
import os
import pathlib
import zipfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response

from processors.genial_processor import process_genial_excel, format_genial_excel, GenialTargets
from processors.ip_processor import process_csv_content, ProcessOptions

app = FastAPI(title="Contabil Along Hub API", version="2.0.0")

MAX_CSV_SIZE  = 500 * 1024 * 1024  # 500 MB
MAX_XLSX_SIZE = 100 * 1024 * 1024  # 100 MB

_raw_origins = os.getenv("ALLOWED_ORIGIN", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["X-Metrics", "X-All-Metrics", "Content-Disposition"],
)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend FastAPI Ativo e Operante."}


@app.post("/api/ip/process")
async def process_ip(files: list[UploadFile] = File(...)):
    csv_files = [f for f in files if f.filename and f.filename.endswith(".csv")]

    if not csv_files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo .csv enviado.")

    contents = await asyncio.gather(*[uf.read() for uf in csv_files])

    for uf, content in zip(csv_files, contents):
        if len(content) > MAX_CSV_SIZE:
            safe = pathlib.Path(uf.filename).name
            raise HTTPException(status_code=413, detail=f"Arquivo '{safe}' excede o limite de 500 MB.")

    async def _process_one(content_bytes: bytes, filename: str) -> dict:
        safe_name = pathlib.Path(filename).name
        try:
            result = await asyncio.to_thread(
                process_csv_content,
                content_bytes,
                input_encoding=None,
                options=ProcessOptions(statuses={"Completed"}, preview_rows=10),
            )
            return {"_ok": True, "name": safe_name, **result}
        except Exception as e:
            return {"_ok": False, "name": safe_name, "error": str(e)}

    raw = await asyncio.gather(*[_process_one(c, f.filename) for f, c in zip(csv_files, contents)])

    ok      = [r for r in raw if r["_ok"]]
    failed  = [r for r in raw if not r["_ok"]]

    if not ok:
        detail = "; ".join(f"{r['name']}: {r['error']}" for r in failed)
        raise HTTPException(status_code=400, detail=f"Nenhum arquivo processado. Detalhes: {detail}")

    # Resposta binária com gzip pré-comprimido (o GZipMiddleware ignora responses
    # que já têm Content-Encoding setado, então não bufferiza tudo de novo).
    if len(ok) == 1:
        r = ok[0]
        compressed = gzip.compress(r["output_bytes"], compresslevel=1)
        metrics_header = json.dumps(r["metrics"])
        return Response(
            content=compressed,
            media_type="text/csv; charset=latin-1",
            headers={
                "Content-Encoding": "gzip",
                "Content-Disposition": f'attachment; filename="tratado_{r["name"]}"',
                "X-Metrics": metrics_header,
            },
        )

    # Múltiplos arquivos — ZIP com todos os CSVs
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        for r in ok:
            zf.writestr(f"tratado_{r['name']}", r["output_bytes"])
    zip_buf.seek(0)

    all_metrics = [{"name": r["name"], **r["metrics"]} for r in ok]
    return Response(
        content=zip_buf.read(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="tratados.zip"',
            "X-All-Metrics": json.dumps(all_metrics),
        },
    )


@app.post("/api/genial/process")
async def process_genial(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .xlsx")

    content_bytes = await file.read()

    if len(content_bytes) > MAX_XLSX_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo excede o limite de 100 MB.")

    safe_name = pathlib.Path(file.filename).name
    targets = GenialTargets().all

    try:
        df_final, stats = await asyncio.to_thread(process_genial_excel, content_bytes, targets=targets)
        excel_output = format_genial_excel(df_final, targets=targets).read()

        df_preview = df_final.copy()
        df_preview["Data"] = df_preview["Data"].apply(
            lambda x: x.strftime("%d/%m/%Y") if hasattr(x, "strftime") else str(x)
        )
        preview = df_preview.head(25).to_dict(orient="records")

        return JSONResponse(content={
            "filename": safe_name.replace(".xlsx", "_tratado.xlsx"),
            "output_base64": base64.b64encode(excel_output).decode("utf-8"),
            "stats": stats,
            "preview": preview,
        })
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao processar o extrato.")
