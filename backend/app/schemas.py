from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ZoneTemps(BaseModel):
    zone_1: float = Field(..., description="Zone 1 temperature °C")
    zone_2: float
    zone_3: float
    zone_4: float
    zone_5: float


class HeatingCurveRequest(BaseModel):
    slab_initial_temp_c: float = Field(..., ge=0, le=800)
    steel_grade: str = Field("S355", max_length=64)
    target_exit_temp_c: float = Field(..., ge=800, le=1300)
    zone_temperatures_c: list[float] = Field(..., min_length=1, max_length=8)
    residence_time_min: float = Field(..., gt=0, le=240)
    fuel_flow_nm3h: float = Field(..., ge=0)
    conveyor_speed_mmin: float = Field(..., gt=0, le=30)
    carbon_weight_pct: float | None = Field(None, ge=0, le=2.5)


class HeatingCurveResponse(BaseModel):
    time_min: list[float]
    optimal_curve_c: list[float]
    actual_curve_c: list[float] | None = None
    recommended_zone_setpoints_c: list[float]
    predicted_exit_uniformity: float = Field(..., ge=0, le=1)
    model_note: str


class OptimizeRequest(HeatingCurveRequest):
    fuel_type: Literal["natural_gas", "light_oil", "electric"] = "natural_gas"
    fuel_price_per_nm3: float = Field(0.35, ge=0)
    co2_price_per_kg: float = Field(0.0, ge=0)
    max_fuel_nm3h: float | None = None


class OptimizeResponse(BaseModel):
    recommended_fuel_nm3h: float
    recommended_zone_setpoints_c: list[float]
    predicted_exit_temp_c: float
    predicted_uniformity: float
    objective_value: float
    co2_kg_per_hour: float
    constraints_ok: bool
    message: str


class EmissionsTrendPoint(BaseModel):
    ts: datetime
    co2_kg_per_ton: float
    throughput_tph: float
    fuel_rate_nm3h: float


class EmissionsSummary(BaseModel):
    co2_kg_per_ton_now: float
    daily_kg_co2: float
    weekly_kg_co2: float
    efficiency_score: float
    fuel_type: str


class LiveFurnaceState(BaseModel):
    ts: datetime
    zones: list[dict]
    slab_surface_avg_c: float
    fuel_total_nm3h: float
    conveyor_speed_mmin: float
    anomaly_flags: list[str]


class RecommendationItem(BaseModel):
    title: str
    severity: Literal["info", "warning", "critical"]
    detail: str
    suggested_action: str


class WhatIfRequest(BaseModel):
    base: HeatingCurveRequest
    delta_fuel_pct: float = Field(0.0, ge=-30, le=30)
    delta_conveyor_pct: float = Field(0.0, ge=-20, le=20)


class WhatIfResponse(BaseModel):
    baseline_exit_estimate_c: float
    scenario_exit_estimate_c: float
    baseline_fuel_nm3h: float
    scenario_fuel_nm3h: float
    baseline_co2_kg_h: float
    scenario_co2_kg_h: float
