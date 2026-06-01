from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EmissionSnapshot, OptimizationRun, SensorReading
from app.db.session import get_db
from app.schemas import (
    EmissionsSummary,
    EmissionsTrendPoint,
    HeatingCurveRequest,
    HeatingCurveResponse,
    LiveFurnaceState,
    OptimizeRequest,
    OptimizeResponse,
    RecommendationItem,
    WhatIfRequest,
    WhatIfResponse,
)
from app.services.emissions import estimate_co2, synthetic_trend_points
from app.services.live_simulator import live_state
from app.services.optimization_engine import optimize_schedule
from app.services.anomaly import detect_anomalies
from app.services.recommendations import build_recommendations
from ml.predictor import predict_heating

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/live", response_model=LiveFurnaceState)
async def furnace_live() -> LiveFurnaceState:
    raw = live_state()
    extra = detect_anomalies(raw["zones"], raw["fuel_total_nm3h"])
    raw["anomaly_flags"] = list({*raw.get("anomaly_flags", []), *extra})
    return LiveFurnaceState(**raw)


@router.post("/predict/heating-curve", response_model=HeatingCurveResponse)
async def heating_curve(body: HeatingCurveRequest) -> HeatingCurveResponse:
    out = predict_heating(body)
    note = out.pop("model_note", "")
    return HeatingCurveResponse(
        time_min=out["time_min"],
        optimal_curve_c=out["optimal_curve_c"],
        actual_curve_c=out.get("actual_curve_c"),
        recommended_zone_setpoints_c=out["recommended_zone_setpoints_c"],
        predicted_exit_uniformity=out["predicted_exit_uniformity"],
        model_note=note,
    )


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize(body: OptimizeRequest, db: AsyncSession = Depends(get_db)) -> OptimizeResponse:
    result = optimize_schedule(body)
    run = OptimizationRun(
        ts=datetime.now(timezone.utc),
        payload_json=json.dumps(body.model_dump()),
        recommended_fuel_nm3h=result["recommended_fuel_nm3h"],
        predicted_exit_c=result["predicted_exit_temp_c"],
        uniformity_score=result["predicted_uniformity"],
    )
    db.add(run)
    await db.commit()
    return OptimizeResponse(
        recommended_fuel_nm3h=result["recommended_fuel_nm3h"],
        recommended_zone_setpoints_c=result["recommended_zone_setpoints_c"],
        predicted_exit_temp_c=result["predicted_exit_temp_c"],
        predicted_uniformity=result["predicted_uniformity"],
        objective_value=result["objective_value"],
        co2_kg_per_hour=result["co2_kg_per_hour"],
        constraints_ok=result["constraints_ok"],
        message=result["message"],
    )


@router.get("/emissions/summary", response_model=EmissionsSummary)
async def emissions_summary() -> EmissionsSummary:
    raw = live_state()
    em = estimate_co2("natural_gas", raw["fuel_total_nm3h"], 50.0)
    daily = em.co2_kg_per_hour * 24 * 0.92
    weekly = daily * 7
    return EmissionsSummary(
        co2_kg_per_ton_now=round(em.co2_kg_per_ton_steel, 2),
        daily_kg_co2=round(daily, 1),
        weekly_kg_co2=round(weekly, 1),
        efficiency_score=round(em.efficiency_score, 1),
        fuel_type="natural_gas",
    )


@router.get("/emissions/trend", response_model=list[EmissionsTrendPoint])
async def emissions_trend(window_hours: int = 168, db: AsyncSession = Depends(get_db)) -> list[EmissionsTrendPoint]:
    window_hours = max(24, min(window_hours, 720))
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    res = await db.execute(select(EmissionSnapshot).where(EmissionSnapshot.ts >= since).order_by(EmissionSnapshot.ts))
    rows = res.scalars().all()
    if len(rows) < 8:
        return [
            EmissionsTrendPoint(
                ts=p["ts"],
                co2_kg_per_ton=p["co2_kg_per_ton"],
                throughput_tph=p["throughput_tph"],
                fuel_rate_nm3h=p["fuel_rate_nm3h"],
            )
            for p in synthetic_trend_points(hours=window_hours)
        ]
    return [
        EmissionsTrendPoint(
            ts=r.ts,
            co2_kg_per_ton=r.co2_kg_per_ton,
            throughput_tph=r.steel_throughput_tph,
            fuel_rate_nm3h=r.fuel_rate_nm3h,
        )
        for r in rows
    ]


@router.get("/recommendations", response_model=list[RecommendationItem])
async def recommendations() -> list[RecommendationItem]:
    st = LiveFurnaceState(**live_state())
    return build_recommendations(st)


@router.post("/whatif", response_model=WhatIfResponse)
async def what_if(body: WhatIfRequest) -> WhatIfResponse:
    from app.services.optimization_engine import _simulate_exit_and_uniformity

    import numpy as np

    base = body.base
    fuel_b = base.fuel_flow_nm3h
    fuel_s = fuel_b * (1.0 + body.delta_fuel_pct / 100.0)
    speed_b = base.conveyor_speed_mmin
    speed_s = speed_b * (1.0 + body.delta_conveyor_pct / 100.0)
    z = np.array(base.zone_temperatures_c, dtype=float)
    ex_b, _, _ = _simulate_exit_and_uniformity(base, fuel_b, z)
    req_s = base.model_copy(update={"fuel_flow_nm3h": fuel_s, "conveyor_speed_mmin": speed_s})
    ex_s, _, _ = _simulate_exit_and_uniformity(req_s, fuel_s, z)
    em_b = estimate_co2("natural_gas", fuel_b, 50.0)
    em_s = estimate_co2("natural_gas", fuel_s, 50.0)
    return WhatIfResponse(
        baseline_exit_estimate_c=round(ex_b, 1),
        scenario_exit_estimate_c=round(ex_s, 1),
        baseline_fuel_nm3h=round(fuel_b, 1),
        scenario_fuel_nm3h=round(fuel_s, 1),
        baseline_co2_kg_h=round(em_b.co2_kg_per_hour, 1),
        scenario_co2_kg_h=round(em_s.co2_kg_per_hour, 1),
    )


@router.post("/ingest/demo-batch")
async def ingest_demo(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Seed time-series rows for dashboard demos."""
    now = datetime.now(timezone.utc)
    n = 0
    for h in range(72):
        ts = now - timedelta(hours=h)
        for zid in range(1, 6):
            db.add(
                SensorReading(
                    ts=ts,
                    zone_id=zid,
                    temperature_c=1050 + zid * 5 + (72 - h) * 0.05,
                    fuel_flow_nm3h=1180 + zid * 12,
                    conveyor_speed_mmin=1.8,
                )
            )
            n += 1
        em = estimate_co2("natural_gas", 1180 + h * 2, 48 + (h % 5))
        db.add(
            EmissionSnapshot(
                ts=ts,
                fuel_type="natural_gas",
                fuel_rate_nm3h=1180 + h * 2,
                steel_throughput_tph=48 + (h % 5),
                co2_kg_per_ton=em.co2_kg_per_ton_steel,
                co2_kg_total=em.co2_kg_per_hour * 1.0,
                efficiency_score=em.efficiency_score,
            )
        )
    await db.commit()
    return {"inserted": n + 72}
