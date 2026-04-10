import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ocr-pdf")
async def ocr_pdf(
    file: UploadFile = File(...),
    language: str = Form("deu+eng"),
    force_ocr: bool = Form("false"),
    skip_text: bool = Form("true"),
    deskew: bool = Form("true"),
    rotate_pages: bool = Form("true"),
    output_type: str = Form("pdf"),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_pdf = tmpdir_path / "input.pdf"
        output_pdf = tmpdir_path / "output.pdf"

        with input_pdf.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        cmd = [
            "ocrmypdf",
            "--language",
            language,
            "--output-type",
            output_type,
        ]

        if force_ocr.lower() == "true":
            cmd.append("--force-ocr")
        elif skip_text.lower() == "true":
            cmd.append("--skip-text")

        if deskew.lower() == "true":
            cmd.append("--deskew")

        if rotate_pages.lower() == "true":
            cmd.append("--rotate-pages")

        cmd.extend([str(input_pdf), str(output_pdf)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start OCRmyPDF: {e}")

        if result.returncode != 0:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "returncode": result.returncode,
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                },
            )

        if not output_pdf.exists():
            raise HTTPException(status_code=500, detail="OCR output PDF was not created")

        download_name = Path(file.filename).stem + ".ocr.pdf"

        return FileResponse(
            path=str(output_pdf),
            media_type="application/pdf",
            filename=download_name,
        )