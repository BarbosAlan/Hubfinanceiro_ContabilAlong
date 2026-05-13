import asyncio
import base64
import gzip
import io
import json
import os
import pathlib
import time
import uuid
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
JOB_TTL_S     = 600                # jobs expiram após 10 min

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

# Armazenamento em memória dos jobs de processamento IP
_jobs: dict[str, dict] = {}


def _cleanup_expired_jobs() -> None:
    now = time.time()
    expired = [jid for jid, j in _jobs.items() if now - j.get("created_at", now) > JOB_TTL_S]
    for jid in expired:
        _jobs.pop(jid, None)


async def _run_ip_job(job_id: str, files: list[tuple[str, bytes]]) -> None:
    """Processa os arquivos em background e armazena o resultado no job."""
    try:
        async def _one(name: str, content: bytes) -> dict:
            result = await asyncio.to_thread(
                process_csv_content,
                content,
                input_encoding=None,
                options=ProcessOptions(statuses={"Completed"}, preview_rows=10),
            )
            return {"name": name, **result}

        results = await asyncio.gather(*[_one(n, c) for n, c in files])
        ok      = [r for r in results if "output_bytes" in r]

        if not ok:
            _jobs[job_id] = {"status": "error", "error": "Nenhum arquivo processado com sucesso.",
                             "created_at": _jobs[job_id]["created_at"]}
            return

        if len(ok) == 1:
            r = ok[0]
            compressed = await asyncio.to_thread(gzip.compress, r["output_bytes"], 1)
            _jobs[job_id] = {
                "status": "done",
                "content": compressed,
                "media_type": "text/csv; charset=latin-1",
                "content_encoding": "gzip",
                "filename": f"tratado_{r['name']}",
                "metrics": [{"name": r["name"], **r["metrics"]}],
                "created_at": _jobs[job_id]["created_at"],
            }
        else:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
                for r in ok:
                    zf.writestr(f"tratado_{r['name']}", r["output_bytes"])
            zip_buf.seek(0)
            _jobs[job_id] = {
                "status": "done",
                "content": zip_buf.read(),
                "media_type": "application/zip",
                "content_encoding": None,
                "filename": "tratados.zip",
                "metrics": [{"name": r["name"], **r["metrics"]} for r in ok],
                "created_at": _jobs[job_id]["created_at"],
            }
    except Exception as e:
        _jobs[job_id] = {"status": "error", "error": str(e),
                         "created_at": _jobs[job_id].get("created_at", time.time())}


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend FastAPI Ativo e Operante."}


@app.post("/api/ip/process")
async def process_ip(files: list[UploadFile] = File(...)):
    _cleanup_expired_jobs()

    csv_files = [f for f in files if f.filename and f.filename.endswith(".csv")]
    if not csv_files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo .csv enviado.")

    contents = await asyncio.gather(*[uf.read() for uf in csv_files])

    for uf, content in zip(csv_files, contents):
        if len(content) > MAX_CSV_SIZE:
            safe = pathlib.Path(uf.filename).name
            raise HTTPException(status_code=413, detail=f"Arquivo '{safe}' excede o limite de 500 MB.")

    job_id = uuid.uuid4().hex[:12]
    named_files = [(pathlib.Path(f.filename).name, c) for f, c in zip(csv_files, contents)]

    _jobs[job_id] = {"status": "processing", "created_at": time.time()}
    asyncio.create_task(_run_ip_job(job_id, named_files))

    return JSONResponse({"job_id": job_id, "results": [], "errors": [], "all_zip_base64": None})


@app.get("/api/ip/status/{job_id}")
async def ip_job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado ou expirado.")
    if job["status"] == "error":
        raise HTTPException(status_code=400, detail=job["error"])
    return {"status": job["status"]}


@app.get("/api/ip/download/{job_id}")
async def ip_job_download(job_id: str):
    job = _jobs.pop(job_id, None)  # consome o job (libera memória)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="Resultado não disponível.")

    headers: dict[str, str] = {
        "Content-Disposition": f'attachment; filename="{job["filename"]}"',
        "X-All-Metrics": json.dumps(job["metrics"]),
    }
    if job.get("content_encoding"):
        headers["Content-Encoding"] = job["content_encoding"]

    return Response(
        content=job["content"],
        media_type=job["media_type"],
        headers=headers,
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
