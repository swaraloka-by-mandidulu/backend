import os
from typing import Annotated

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY")
FREESOUND_SEARCH_URL = "https://freesound.org/apiv2/search/"
DEFAULT_COUNTRY_FILTER = "tag:indonesia"

INSTRUMENT_QUERIES = {
    "angklung": "angklung",
    "gamelan": "gamelan",
    "bonang": "bonang",
    "saron": "saron",
    "gong-ageng": '"gong ageng"',
    "kendang": "kendang",
    "suling": "suling",
    "kacapi": "kacapi",
    "tifa": "tifa",
    "sasando": "sasando",
    "gamba": "gamba",
}

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="be-Swaraloka",
    description="Backend application using Freesound API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Welcome to Swaraloka API"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

def call_freesound(params: dict[str, object]) -> httpx.Response:
    try:
        response = httpx.get(
            FREESOUND_SEARCH_URL,
            params=params,
            headers={"Authorization": f"Token {FREESOUND_API_KEY}"},
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text[:500]) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Freesound API unavailable") from exc
    return response

@app.get("/sounds/search")
def search_sounds(
    instrument: Annotated[str | None, Query(description="Canonical instrument id, e.g. angklung")] = None,
    query: str = "",
    tag: Annotated[list[str] | None, Query(description="Extra Freesound tag filter")] = None,
    descriptor: Annotated[
        list[str] | None,
        Query(description="Freesound audio descriptor filter, e.g. bpm:[60 TO 120]"),
    ] = None,
    raw_filter: Annotated[str | None, Query(alias="filter", description="Raw Freesound filter string")] = None,
    fields: str = "id,name,tags,username,license,url,previews,duration,score",
    sort: str = "score",
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=150),
):
    if not FREESOUND_API_KEY:
        raise HTTPException(status_code=500, detail="FREESOUND_API_KEY is not configured")

    valid_instruments = ", ".join(INSTRUMENT_QUERIES)
    if not instrument:
        raise HTTPException(status_code=400, detail=f"instrument is required. Valid instruments: {valid_instruments}")

    base_query = INSTRUMENT_QUERIES.get(instrument)
    if base_query is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown instrument '{instrument}'. Valid instruments: {valid_instruments}",
        )

    full_query = " ".join(part for part in (base_query, query.strip()) if part)
    extra_filters = [
        *(f"tag:{value}" for value in tag or [] if value),
        *(value for value in descriptor or [] if value),
    ]
    if raw_filter:
        extra_filters.append(raw_filter)

    def build_params(filters: list[str]) -> dict[str, object]:
        params: dict[str, object] = {
            "query": full_query,
            "fields": fields,
            "sort": sort,
            "page": page,
            "page_size": page_size,
        }
        if filters:
            params["filter"] = " ".join(filters)
        return params

    response = call_freesound(build_params([DEFAULT_COUNTRY_FILTER, *extra_filters]))
    payload = response.json()

    if payload.get("count") == 0:
        broader = call_freesound(build_params(extra_filters))
        return JSONResponse(
            content=broader.json(),
            headers={"X-Freesound-Broadened": "true"},
        )

    return payload
