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


@app.post("/ocr-pdf")
async def ocr_pdf(
    file: UploadFile = File(...),
    language: str = Form("deu+eng"),
    force_ocr: str = Form("false"),
    skip_text: str = Form("true"),
    deskew: str = Form("true"),
    rotate_pages: str = Form("true"),
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
            "--language", language,
            "--output-type", output_type,
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

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "returncode": result.returncode,
                    "stderr": result.stderr,
                    "stdout": result.stdout,
                    "command": cmd,
                },
            )

        if not output_pdf.exists():
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "detail": "OCR output PDF was not created",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )

        pdf_bytes = output_pdf.read_bytes()
        filename = f"{Path(file.filename).stem}.ocr.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )
