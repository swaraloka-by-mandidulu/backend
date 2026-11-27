# be-Swaraloka backend

FastAPI backend that searches Freesound for sound samples of Indonesian musical instruments. It keeps the Freesound API key on the server and exposes a small REST API for the frontend.

See [API_CONTRACT.md](./API_CONTRACT.md) for the frontend/backend contract.

## Requirements

- Python 3.10+
- A Freesound API key from https://freesound.org/apiv2/apply

## Setup

Run all commands from this folder.

```powershell
python -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

If PowerShell blocks virtualenv activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then edit it:

```env
FREESOUND_API_KEY=your_key_here
FRONTEND_ORIGINS=http://localhost:5173,http://localhost:3000
```

`FRONTEND_ORIGINS` is optional. It defaults to the two origins above. Add your deployed frontend URL there in production.

`.env` is gitignored — never commit the API key. `.env.example` contains placeholders only and is safe to commit.

## Run the server

```powershell
python -m uvicorn app.main:app --reload
```
or
```cmd
fastapi dev app/main.py
```

Then open:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

Press `Ctrl+C` to stop.

## Quick API checks

In PowerShell use `curl.exe`; plain `curl` is an alias for `Invoke-WebRequest`.

```powershell
curl.exe http://localhost:8000/
curl.exe http://localhost:8000/health
```

Search for one instrument:

```powershell
curl.exe --get http://localhost:8000/sounds/search `
  --data-urlencode "instrument=angklung" `
  --data-urlencode "page_size=12"
```

Search with an audio descriptor:

```powershell
curl.exe --get http://localhost:8000/sounds/search `
  --data-urlencode "instrument=gamelan" `
  --data-urlencode "descriptor=pitch:[200 TO 1200]" `
  --data-urlencode "page_size=12"
```

Valid `instrument` values: `angklung`, `gamelan`, `bonang`, `saron`, `gong-ageng`, `kendang`, `suling`, `kacapi`, `tifa`, `sasando`, `gamba`.

If a search returns no results with the default `tag:indonesia` filter, the backend retries once without it and adds the response header `X-Freesound-Broadened: true`.
