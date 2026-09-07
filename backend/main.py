"""
LabelCheck AI — backend
------------------------
Photograph a packaged product's label -> OCR extracts the text ->
rule engine cross-checks it against Rule 6 of the Legal Metrology
(Packaged Commodities) Rules, 2011 -> returns a per-field compliance report.

Run:
    pip install -r requirements.txt
    # Tesseract OCR engine must also be installed on the OS:
    #   Ubuntu/Debian:  sudo apt-get install tesseract-ocr
    #   macOS:          brew install tesseract
    #   Windows:        https://github.com/UB-Mannheim/tesseract/wiki
    python -m uvicorn main:app --reload --port 8000
Then open http://localhost:8000
"""

import io
from pathlib import Path

import pytesseract
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from PIL import Image, ImageOps
from pydantic import BaseModel

from rules import run_all_checks, compute_verdict

app = FastAPI(title="LabelCheck AI")

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


# ---------------------------------------------------------------------------
# Image preprocessing (improves OCR accuracy on real-world photos)
# ---------------------------------------------------------------------------

def preprocess_image(raw_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)   # respect phone camera orientation
    img = img.convert("L")               # grayscale
    img = ImageOps.autocontrast(img)     # boost contrast on flat/dim photos
    return img


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class FieldOut(BaseModel):
    key: str
    label: str
    status: str
    detected_value: str | None
    note: str


class ScanResult(BaseModel):
    verdict: str
    summary: str
    fields: list[FieldOut]
    raw_text: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/scan", response_model=ScanResult)
async def scan_label(image: UploadFile = File(...)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    raw_bytes = await image.read()
    try:
        img = preprocess_image(raw_bytes)
        raw_text = pytesseract.image_to_string(img)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR failed: {exc}")

    if not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Couldn't read any text from this photo. Try a clearer, closer, well-lit shot.",
        )

    results = run_all_checks(raw_text)
    verdict_info = compute_verdict(results)

    return ScanResult(
        verdict=verdict_info["verdict"],
        summary=verdict_info["summary"],
        fields=[FieldOut(**r.to_dict()) for r in results],
        raw_text=raw_text.strip(),
    )


# ---------------------------------------------------------------------------
# Serve the frontend (single command runs both)
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
