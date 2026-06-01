"""Lightweight rule + residual anomaly hooks (placeholder for streaming models)."""


def detect_anomalies(zones: list[dict], fuel: float) -> list[str]:
    flags: list[str] = []
    for z in zones:
        if z["temperature_c"] - z["setpoint_c"] > 35:
            flags.append(f"zone_{z['zone_id']}_tracking_error")
    if fuel < 600:
        flags.append("low_fuel_unexpected")
    return flags
