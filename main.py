import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, JSONResponse

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}


def compress_pdf(input_pdf: Path, output_pdf: Path, quality="ebook"):
    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_pdf}",
        str(input_pdf),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript failed: {result.stderr}")


@app.post("/ocr-pdf")
async def ocr_pdf(
    file: UploadFile = File(...),
    language: str = Form("deu+eng"),
    skip_text: str = Form("true"),
    deskew: str = Form("true"),
    rotate_pages: str = Form("true"),
    output_type: str = Form("pdf"),
    compress: str = Form("true"),
    quality: str = Form("ebook"),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        input_pdf = tmpdir / "input.pdf"
        ocr_pdf = tmpdir / "ocr.pdf"
        compressed_pdf = tmpdir / "compressed.pdf"

        # Datei speichern
        with input_pdf.open("wb") as f:
            shutil.copyfileobj(file.file, f)

        # OCRmyPDF Befehl
        cmd = [
            "ocrmypdf",
            "--language", language,
            "--output-type", output_type,
        ]

        if skip_text == "true":
            cmd.append("--skip-text")

        if deskew == "true":
            cmd.append("--deskew")

        if rotate_pages == "true":
            cmd.append("--rotate-pages")

        cmd.extend([str(input_pdf), str(ocr_pdf)])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return JSONResponse(
                status_code=500,
                content={
                    "step": "ocrmypdf",
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                },
            )

        final_pdf = ocr_pdf

        # Ghostscript Komprimierung
        if compress == "true":
            try:
                compress_pdf(ocr_pdf, compressed_pdf, quality=quality)
                final_pdf = compressed_pdf
            except Exception as e:
                # fallback → OCR-PDF behalten
                final_pdf = ocr_pdf

        pdf_bytes = final_pdf.read_bytes()

        filename = Path(file.filename).stem + ".ocr.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )
