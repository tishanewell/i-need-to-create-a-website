from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from converter import convert_file

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "inputs"
OUTPUT_DIR = DATA_DIR / "outputs"
TEMPLATE_PATH = DATA_DIR / "assortment_template.xlsx"
HISTORY_PATH = DATA_DIR / "conversions.json"

app = FastAPI(title="IBP Forecast Converter")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def ensure_storage() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text("[]", encoding="utf-8")


def load_history() -> list[dict[str, Any]]:
    ensure_storage()
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_history(items: list[dict[str, Any]]) -> None:
    HISTORY_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    items = load_history()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "conversions": sorted(items, key=lambda x: x["created_at"], reverse=True),
        },
    )


@app.get("/api/conversions", response_class=JSONResponse)
def list_conversions() -> JSONResponse:
    return JSONResponse(load_history())


@app.post("/api/convert")
async def convert_upload(forecast: UploadFile = File(...)) -> RedirectResponse:
    ensure_storage()
    conversion_id = uuid.uuid4().hex[:12]
    input_name = f"{conversion_id}_input_{Path(forecast.filename or 'forecast.xlsx').name}"
    output_name = f"{conversion_id}_output_assortment_by_customer.xlsx"
    input_path = INPUT_DIR / input_name
    output_path = OUTPUT_DIR / output_name

    with input_path.open("wb") as f:
        shutil.copyfileobj(forecast.file, f)

    try:
        summary = convert_file(input_path, TEMPLATE_PATH, output_path)
    except Exception as exc:
        input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    history = load_history()
    history.append(
        {
            "id": conversion_id,
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "input_filename": forecast.filename,
            "input_path": str(input_path.name),
            "output_path": str(output_path.name),
            "summary": summary,
        }
    )
    save_history(history)
    return RedirectResponse(url="/", status_code=303)


@app.get("/download/{conversion_id}/{file_kind}")
def download_file(conversion_id: str, file_kind: str) -> FileResponse:
    history = load_history()
    item = next((row for row in history if row["id"] == conversion_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Conversion not found.")

    if file_kind == "input":
        path = INPUT_DIR / item["input_path"]
        download_name = item["input_filename"] or path.name
    elif file_kind == "output":
        path = OUTPUT_DIR / item["output_path"]
        download_name = "assortment_by_customer.xlsx"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    if not path.exists():
        raise HTTPException(status_code=404, detail="File does not exist.")

    return FileResponse(path, filename=download_name)
