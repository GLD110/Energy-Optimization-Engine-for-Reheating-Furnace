"""Deterministic live furnace simulator for dashboard demos."""

from datetime import datetime, timezone

import math

from app.config import settings


def live_state(t: float | None = None) -> dict:
    t = t if t is not None else datetime.now(timezone.utc).timestamp() / 60.0
    zones = []
    flags: list[str] = []
    for z in range(1, settings.num_zones + 1):
        base = 1080 + 15 * math.sin(t / 30.0 + z) + (z - 1) * 6
        temp = base + 4 * math.sin(t / 7.0 + z * 1.7)
        if z == settings.num_zones and temp > 1210:
            flags.append("preheat_zone_hot_spot")
        zones.append(
            {
                "zone_id": z,
                "temperature_c": round(temp, 1),
                "setpoint_c": round(base, 1),
                "fuel_share": round(0.18 + 0.03 * math.sin(t / 11 + z), 3),
            }
        )
    slab = sum(z["temperature_c"] for z in zones) / len(zones) - 180
    fuel = 1180 + 60 * math.sin(t / 45.0)
    speed = 1.85 + 0.05 * math.sin(t / 20.0)
    return {
        "ts": datetime.now(timezone.utc),
        "zones": zones,
        "slab_surface_avg_c": round(slab, 1),
        "fuel_total_nm3h": round(fuel, 1),
        "conveyor_speed_mmin": round(speed, 2),
        "anomaly_flags": flags,
    }
