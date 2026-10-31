from fastapi.middleware.cors import CORSMiddleware
from typing import Literal
from fastapi import FastAPI
from apex.data_loader import list_datasets, load_dataset
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from apex.analytics import (
    compare_driver_pace,
    grand_prix_driver_performance,
    grand_prix_lap_times,
    grand_prix_tyre_stints,
    season_driver_leaderboard,
)
from apex.agent import ask_apex
from apex.ai_tools import compare_f1_drivers
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Apex Intelligence AI",
    description="An F1 analytics and knowledge assistant powered by LangGraph, RAG, and Ollama.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class CompareRequest(BaseModel):
    driver_a: str = Field(min_length=3, max_length=3)
    driver_b: str = Field(min_length=3, max_length=3)


@app.get("/health")
def health():
    return {"status": "ok", "application": "Apex Intelligence AI"}


@app.post("/ask")
def ask(request: AskRequest):
    try:
        answer = ask_apex(request.question.strip())

        return {
            "question": request.question,
            "answer": answer,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Apex could not process the question. Check the server terminal.",
        ) from exc


@app.post("/compare")
def compare(request: CompareRequest):
    try:
        result = compare_f1_drivers.invoke({
            "driver_a": request.driver_a.upper(),
            "driver_b": request.driver_b.upper(),
        })

        if "error" in result:
            raise HTTPException(status_code=422, detail=result)

        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Driver comparison failed. Check the server terminal.",
        ) from exc

@app.get("/season/{season}/leaderboard")
def season_leaderboard(season: int):
    try:
        return {
            "season": season,
            "drivers": season_driver_leaderboard(season),
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Season leaderboard failed. Check the server terminal.",
        ) from exc

@app.get("/race/{season}/{grand_prix}/performance")
def race_performance(season: int, grand_prix: str):
    try:
        return grand_prix_driver_performance(season, grand_prix)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Race performance analysis failed. Check the server terminal.",
        ) from exc
@app.get("/race/{season}/{grand_prix}/laps")   
def race_lap_times(
    season: int,
    grand_prix: str,
    drivers: str = "HAM,VER",
):
    try:
        driver_codes = drivers.split(",")
        return grand_prix_lap_times(
            season, grand_prix, driver_codes
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404, detail=str(exc)
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Lap-time analysis failed. Check the server terminal.",
        ) from exc
@app.get("/races")
def available_races():
    datasets = [
        {
            "season": entry["season"],
            "grand_prix": entry["grand_prix"],
            "dataset_id": entry["dataset_id"],
        }
        for entry in list_datasets()
        if entry.get("session_type") == "R"
        and entry.get("status") == "imported"
    ]

    # Avoid duplicate race choices if the manifest has duplicate entries.
    unique_races = {
        (item["season"], item["grand_prix"]): item
        for item in datasets
    }

    return {
        "seasons": sorted({item["season"] for item in unique_races.values()}),
        "races": sorted(
            unique_races.values(),
            key=lambda item: (item["season"], item["grand_prix"]),
        ),
    }

@app.get("/race/{season}/{grand_prix}/drivers")
def available_race_drivers(season: int, grand_prix: str):
    matches = [
        entry
        for entry in list_datasets()
        if entry.get("season") == season
        and entry.get("grand_prix") == grand_prix
        and entry.get("session_type") == "R"
        and entry.get("status") == "imported"
    ]

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="Race dataset not found."
        )

    _, laps = load_dataset(matches[0]["dataset_id"])

    drivers = sorted(
        laps["Driver"]
        .dropna()
        .astype(str)
        .str.upper()
        .unique()
        .tolist()
    )

    return {
        "season": season,
        "grand_prix": grand_prix,
        "drivers": drivers,
    }

@app.get("/race/{season}/{grand_prix}/stints")
def race_tyre_stints(season: int, grand_prix: str):
    try:
        return grand_prix_tyre_stints(season, grand_prix)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Tyre stint analysis failed. Check the server terminal.",
        ) from exc
