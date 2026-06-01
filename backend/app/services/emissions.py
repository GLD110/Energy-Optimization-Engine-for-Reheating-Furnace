"""Real-time CO₂ estimation from fuel use and emission factors (IPCC-style defaults)."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# kg CO2 per Nm³ fuel (natural gas ~2.0, varies by CH4 content)
EMISSION_FACTORS_KG_CO2_PER_NM3 = {
    "natural_gas": 1.96,
    "light_oil": 2.6,  # per liter proxy: use kgCO2 per Nm³ equivalent if gasified; here scaled for API consistency
    "electric": 0.0,  # grid factor should be applied separately
}

# For oil we document that client should pass fuel_flow as "energy-equivalent Nm³" or use gas; simplify:
EMISSION_FACTORS_KG_CO2_PER_L_OIL = {"light_oil": 2.5}


@dataclass
class EmissionResult:
    co2_kg_per_hour: float
    co2_kg_per_ton_steel: float
    efficiency_score: float  # lower is better; normalized 0-100 where 100 = best-in-class proxy


def estimate_co2(
    fuel_type: str,
    fuel_rate_nm3h: float,
    steel_throughput_tph: float,
) -> EmissionResult:
    ft = fuel_type.lower()
    if ft == "light_oil":
        factor = EMISSION_FACTORS_KG_CO2_PER_NM3.get("light_oil", 2.4)
    else:
        factor = EMISSION_FACTORS_KG_CO2_PER_NM3.get(ft, EMISSION_FACTORS_KG_CO2_PER_NM3["natural_gas"])

    co2_kg_h = max(0.0, fuel_rate_nm3h * factor)
    tph = max(1e-6, steel_throughput_tph)
    co2_per_ton = co2_kg_h / tph

    # Proxy score: map 40–120 kg/t to 100–0
    ref_low, ref_high = 40.0, 120.0
    clamped = max(ref_low, min(ref_high, co2_per_ton))
    efficiency_score = 100.0 * (1.0 - (clamped - ref_low) / (ref_high - ref_low))

    return EmissionResult(
        co2_kg_per_hour=co2_kg_h,
        co2_kg_per_ton_steel=co2_per_ton,
        efficiency_score=float(efficiency_score),
    )


def synthetic_trend_points(now: datetime | None = None, hours: int = 168) -> list[dict]:
    """Generate dashboard trend data when DB is sparse."""
    import math
    import random

    rng = random.Random(42)
    now = now or datetime.now(timezone.utc)
    out: list[dict] = []
    for h in range(hours, 0, -1):
        ts = now - timedelta(hours=h)
        base = 85 + 10 * math.sin(h / 12.0) + rng.uniform(-3, 3)
        out.append(
            {
                "ts": ts,
                "co2_kg_per_ton": max(35.0, base),
                "throughput_tph": 45 + rng.uniform(-4, 4),
                "fuel_rate_nm3h": 1200 + 80 * math.sin(h / 24.0) + rng.uniform(-40, 40),
            }
        )
    return out
