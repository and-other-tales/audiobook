import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

from .agent import process_manuscript

app = FastAPI(title="Audiobook Generator Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/live")
def live():
    return {"status": "live"}

@app.get("/ready")
def ready():
    return {"status": "ready"}

@app.post("/generate", summary="Generate audiobook from manuscript")
async def generate(manuscript: UploadFile = File(...)):
    filename = manuscript.filename or ""
    ext = filename.split(".")[-1].lower()
    if ext not in ("txt", "docx", "pdf"):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    try:
        contents = await manuscript.read()
        zip_bytes = await process_manuscript(contents, filename)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    headers = {"Content-Disposition": 'attachment; filename="audiobook.zip"'}
    return Response(content=zip_bytes, media_type="application/zip", headers=headers)