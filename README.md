# IBP Forecast Converter

This app lets users:

- Upload an IBP forecast workbook (`.xlsx`)
- Convert it into the `assortment_by_customer` layout
- Download the converted file
- View and download past input/output files from a dashboard

## Run locally

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Start the app:

```powershell
uvicorn app:app --host 0.0.0.0 --port 8765
```

3. Open:

`http://127.0.0.1:8765`

## Notes on conversion

- Input data source: `customer` sheet in uploaded workbook
- Output template: `data/assortment_template.xlsx`
- Output workbook keeps the same sheet structure and styling pattern as the template
- Qty and Rev are populated from:
  - `Consensus Dmd Plan Qty (with SOH)` -> `Consensus Dmd Plan Qty (with SOH)`
  - `Consensus Dmd  Plan Rev (with SOH)` -> `Consensus Dmd Plan Rev (with SOH)`

## Publish publicly

Use a host like Render/Railway:

1. Push this folder to a GitHub repo.
2. Create a new Web Service from that repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Deploy and use the generated `https://...` URL as your public link.
