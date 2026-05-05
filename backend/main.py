import asyncio
import base64
import io
import os
import pathlib
import zipfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from processors.genial_processor import process_genial_excel, format_genial_excel, GenialTargets
from processors.ip_processor import process_csv_content, ProcessOptions

app = FastAPI(title="Contabil Along Hub API", version="2.0.0")

MAX_CSV_SIZE  = 100 * 1024 * 1024  # 100 MB
MAX_XLSX_SIZE = 100 * 1024 * 1024  # 100 MB

# Defina ALLOWED_ORIGIN no Render com a URL do Vercel para restringir acesso
_raw_origins = os.getenv("ALLOWED_ORIGIN", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
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
            raise HTTPException(status_code=413, detail=f"Arquivo '{safe}' excede o limite de 100 MB.")

    async def _process_one(content_bytes: bytes, filename: str) -> dict:
        safe_name = pathlib.Path(filename).name
        try:
            result = await asyncio.to_thread(
                process_csv_content,
                content_bytes,
                input_encoding=None,
                options=ProcessOptions(statuses={"Completed"}, preview_rows=50),
            )
            return {
                "name": safe_name,
                "output_base64": base64.b64encode(result["output_bytes"]).decode("utf-8"),
                "errors_base64": base64.b64encode(result["errors_bytes"]).decode("utf-8") if result["errors_bytes"] else None,
                "metrics": result["metrics"],
                "warnings": result["warnings"],
                "preview": result["preview"],
            }
        except Exception as e:
            return {"_error": True, "filename": safe_name, "error": f"Erro interno: {str(e)}"}

    raw = await asyncio.gather(*[_process_one(c, f.filename) for f, c in zip(csv_files, contents)])

    results = [r for r in raw if not r.get("_error")]
    errors  = [{"filename": r["filename"], "error": r["error"]} for r in raw if r.get("_error")]

    if not results and errors:
        error_details = "; ".join([e["error"] for e in errors])
        raise HTTPException(status_code=400, detail=f"Nenhum arquivo processado com sucesso. Detalhes: {error_details}")

    all_zip_base64 = None
    if len(results) > 1:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in results:
                zf.writestr(f"tratado_{r['name']}", base64.b64decode(r["output_base64"]))
        zip_buffer.seek(0)
        all_zip_base64 = base64.b64encode(zip_buffer.read()).decode("utf-8")

    return JSONResponse(content={"results": results, "errors": errors, "all_zip_base64": all_zip_base64})


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
