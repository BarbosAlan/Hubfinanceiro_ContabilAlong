from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import zipfile
import json
import base64

from processors.genial_processor import process_genial_excel, format_genial_excel, GenialTargets
from processors.ip_processor import process_csv_content, ProcessOptions

app = FastAPI(title="Contabil Along Hub API", version="2.0.0")

# Permitir acesso do Frontend (Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Altere na producao para a URL do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend FastAPI Ativo e Operante."}

@app.post("/api/ip/process")
async def process_ip(files: list[UploadFile] = File(...)):
    results = []
    errors = []
    
    for uf in files:
        if not uf.filename.endswith(".csv"):
            continue
            
        content_bytes = await uf.read()
        try:
            result = process_csv_content(
                content_bytes,
                input_encoding=None,
                options=ProcessOptions(statuses={"Completed"}, preview_rows=50)
            )
            # Para retornar JSON limpo, precisamos encodar os bytes como base64
            # Para o frontend fazer download do blob
            results.append({
                "name": uf.filename,
                "output_base64": base64.b64encode(result["output_bytes"]).decode('utf-8'),
                "errors_base64": base64.b64encode(result["errors_bytes"]).decode('utf-8') if result["errors_bytes"] else None,
                "metrics": result["metrics"],
                "warnings": result["warnings"],
                "preview": result["preview"]
            })
        except Exception as e:
            errors.append({"filename": uf.filename, "error": str(e)})

    if not results and errors:
        raise HTTPException(status_code=400, detail="Nenhum arquivo processado com sucesso. Erros: " + str(errors))

    all_zip_base64 = None
    if len(results) > 1:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for r in results:
                zf.writestr(f"tratado_{r['name']}", base64.b64decode(r["output_base64"]))
        zip_buffer.seek(0)
        all_zip_base64 = base64.b64encode(zip_buffer.read()).decode('utf-8')

    return JSONResponse(content={"results": results, "errors": errors, "all_zip_base64": all_zip_base64})

@app.post("/api/genial/process")
async def process_genial(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .xlsx")
        
    content_bytes = await file.read()
    targets = GenialTargets().all
    
    try:
        df_final, stats = process_genial_excel(content_bytes, targets=targets)
        excel_output = format_genial_excel(df_final, targets=targets).read()

        # Converte datas para string antes de serializar o preview
        df_preview = df_final.copy()
        df_preview['Data'] = df_preview['Data'].apply(
            lambda x: x.strftime('%d/%m/%Y') if hasattr(x, 'strftime') else str(x)
        )
        preview = df_preview.head(25).to_dict(orient='records')

        return JSONResponse(content={
            "filename": file.filename.replace(".xlsx", "_tratado.xlsx"),
            "output_base64": base64.b64encode(excel_output).decode('utf-8'),
            "stats": stats,
            "preview": preview
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
