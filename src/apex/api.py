import os
from typing import Optional
from apex.strategy_simulator import (
    simulate_race_strategy,
    simulate_live_strategy,
    evaluate_custom_strategy,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from apex.data_loader import list_datasets, load_dataset
from apex.analytics import (
    compare_driver_pace,
    season_driver_leaderboard,
    grand_prix_driver_performance,
    grand_prix_lap_times,
    grand_prix_tyre_stints,
    grand_prix_tyre_degradation,
    grand_prix_tyre_degradation_v2,
    grand_prix_strategy_overview,
)
from apex.agent import ask_apex
from apex.ai_tools import compare_f1_drivers


app = FastAPI(
    title="Apex Intelligence AI",
    description=(
        "An F1 analytics and knowledge assistant powered by "
        "LangGraph, RAG, and Gemini."
    ),
    version="0.1.0",
)
allowed_origins = [
    "https://apex-intelligence-ai-red.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Also include any additional origins configured in Render
extra_origins = os.getenv("CORS_ORIGINS", "")

for origin in extra_origins.split(","):
    origin = origin.strip()
    if origin and origin not in allowed_origins:
        allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class CompareRequest(BaseModel):
    driver_a: str = Field(min_length=3, max_length=3)
    driver_b: str = Field(min_length=3, max_length=3)

class StrategySimulationRequest(BaseModel):
    pit_loss_seconds: float = Field(default=22.0, ge=0, le=90)
    max_stops: int = Field(default=3, ge=1, le=3)
    race_laps: Optional[int] = Field(default=None, ge=10, le=120)
    driver: Optional[str] = Field(default=None, min_length=3, max_length=3)


class LiveDriverState(BaseModel):
    current_compound: str
    tyre_age: int = Field(ge=1, le=100)


class LiveStrategyRequest(BaseModel):
    remaining_laps: int = Field(ge=1, le=120)
    pit_loss_seconds: float = Field(default=22.0, ge=0, le=90)
    max_stops: int = Field(default=3, ge=1, le=3)
    driver_states: dict[str, LiveDriverState]


class CustomStrategyStint(BaseModel):
    compound: str = Field(min_length=3, max_length=10)
    laps: int = Field(ge=1, le=120)


class CustomStrategyRequest(BaseModel):
    driver: str = Field(min_length=3, max_length=3)
    race_laps: int = Field(ge=10, le=120)
    pit_loss_seconds: float = Field(default=22.0, ge=0, le=90)
    stints: list[CustomStrategyStint] = Field(min_length=1, max_length=4)
    require_two_compounds: bool = True


@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": "Apex Intelligence AI",
    }


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
        driver_codes = [
            driver.strip().upper()
            for driver in drivers.split(",")
            if driver.strip()
        ]

        return grand_prix_lap_times(
            season,
            grand_prix,
            driver_codes,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
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

    unique_races = {
        (item["season"], item["grand_prix"]): item
        for item in datasets
    }

    return {
        "seasons": sorted({
            item["season"]
            for item in unique_races.values()
        }),
        "races": sorted(
            unique_races.values(),
            key=lambda item: (
                item["season"],
                item["grand_prix"],
            ),
        ),
    }


@app.get("/race/{season}/{grand_prix}/drivers")
def available_race_drivers(season: int, grand_prix: str):
    matches = [
        entry
        for entry in list_datasets()
        if entry.get("season") == season
        and entry.get("grand_prix", "").casefold()
        == grand_prix.strip().casefold()
        and entry.get("session_type") == "R"
        and entry.get("status") == "imported"
    ]

    if not matches:
        raise HTTPException(
            status_code=404,
            detail="Race dataset not found.",
        )

    matches.sort(
        key=lambda entry: (
            "race_tyres" not in entry.get("dataset_id", ""),
            entry.get("dataset_id", ""),
        )
    )

    _, laps = load_dataset(matches[0]["dataset_id"])

    if "Driver" not in laps.columns:
        raise HTTPException(
            status_code=422,
            detail="Driver information is missing from this dataset.",
        )

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


@app.get("/race/{season}/{grand_prix}/tyre-degradation")
def race_tyre_degradation(season: int, grand_prix: str):
    try:
        return grand_prix_tyre_degradation(season, grand_prix)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Tyre degradation analysis failed. Check the server terminal.",
        ) from exc


@app.get("/race/{season}/{grand_prix}/tyre-degradation-v2")
def race_tyre_degradation_v2(season: int, grand_prix: str):
    try:
        return grand_prix_tyre_degradation_v2(season, grand_prix)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Tyre degradation v2 analysis failed. Check the server terminal.",
        ) from exc


@app.get("/race/{season}/{grand_prix}/strategy/overview")
def race_strategy_overview(season: int, grand_prix: str):
    try:
        return grand_prix_strategy_overview(
            season,
            grand_prix,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Race strategy analysis failed. Check the server terminal.",
        ) from exc
def _get_race_tyre_dataset(season: int, grand_prix: str):
    matches = [
        entry
        for entry in list_datasets()
        if entry.get("season") == season
        and entry.get("session_type") == "R"
        and entry.get("status") == "imported"
        and entry.get("grand_prix", "").casefold()
        == grand_prix.strip().casefold()
    ]

    matches.sort(
        key=lambda entry: (
            "race_tyres" not in entry.get("dataset_id", ""),
            entry.get("dataset_id", ""),
        )
    )

    required = {
        "Driver",
        "lap_number",
        "lap_duration",
        "compound",
        "tyre_life",
    }

    for entry in matches:
        metadata, laps = load_dataset(entry["dataset_id"])

        if required.issubset(laps.columns):
            return metadata, laps

    raise ValueError(
        f"No imported tyre dataset found for {grand_prix} in {season}."
    )


@app.post("/race/{season}/{grand_prix}/strategy/simulate")
def historical_strategy_simulation(
    season: int,
    grand_prix: str,
    request: StrategySimulationRequest,
):
    try:
        _, laps = _get_race_tyre_dataset(season, grand_prix)

        return simulate_race_strategy(
            laps=laps,
            race_laps=request.race_laps,
            pit_loss_seconds=request.pit_loss_seconds,
            max_stops=request.max_stops,
            driver=request.driver,
        )

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Historical strategy simulation failed.",
        ) from exc


@app.post("/race/{season}/{grand_prix}/strategy/live")
def live_strategy_simulation(
    season: int,
    grand_prix: str,
    request: LiveStrategyRequest,
):
    try:
        _, laps = _get_race_tyre_dataset(season, grand_prix)

        states = {
            driver: state.model_dump()
            for driver, state in request.driver_states.items()
        }

        return simulate_live_strategy(
            laps=laps,
            driver_states=states,
            remaining_laps=request.remaining_laps,
            pit_loss_seconds=request.pit_loss_seconds,
            max_stops=request.max_stops,
        )

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Live strategy simulation failed.",
        ) from exc

@app.post("/race/{season}/{grand_prix}/strategy/custom")
def custom_strategy_simulation(
    season: int,
    grand_prix: str,
    request: CustomStrategyRequest,
):
    try:
        _, laps = _get_race_tyre_dataset(season, grand_prix)
        custom_stints = [
            {"compound": stint.compound, "laps": stint.laps}
            for stint in request.stints
        ]
        return evaluate_custom_strategy(
            laps=laps,
            driver=request.driver,
            stints=custom_stints,
            race_laps=request.race_laps,
            pit_loss_seconds=request.pit_loss_seconds,
            require_two_compounds=request.require_two_compounds,
        )

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Custom strategy evaluation failed.",
        ) from exc