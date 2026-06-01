"""Heuristic + grade-aware heating curve used when no trained checkpoint is available."""

from __future__ import annotations

import hashlib
import math
from typing import Any

from app.schemas import HeatingCurveRequest


def _grade_factor(steel_grade: str) -> float:
    h = int(hashlib.sha256(steel_grade.encode()).hexdigest()[:8], 16)
    return 0.92 + (h % 17) / 100.0


def predict_curves(req: HeatingCurveRequest, sequence_len: int = 48) -> dict[str, Any]:
    t0 = req.slab_initial_temp_c
    tgt = req.target_exit_temp_c
    tau = req.residence_time_min
    zones = req.zone_temperatures_c
    n = len(zones)
    times = [tau * i / (sequence_len - 1) for i in range(sequence_len)]
    gf = _grade_factor(req.steel_grade)

    optimal: list[float] = []
    actual: list[float] = []
    for i, _ in enumerate(times):
        alpha = i / max(1, sequence_len - 1)
        # S-curve approach to reduce overshoot
        s = 1 / (1 + math.exp(-10 * (alpha - 0.45)))
        opt = t0 + (tgt - t0) * s * gf
        optimal.append(round(min(tgt + 25, max(t0 - 5, opt)), 2))
        z_avg = sum(zones) / n
        noise = 6 * math.sin(alpha * math.pi * 2) + (z_avg - opt) * 0.08
        actual.append(round(min(tgt + 40, max(t0, opt + noise)), 2))

    # Ramp setpoints along furnace length toward target profile
    ramp = [t0 + (tgt - t0) * (j / max(1, n - 1)) * 0.92 for j in range(n)]
    recommended = [round(min(tgt + 30, max(zones[j] - 15, 0.55 * zones[j] + 0.45 * ramp[j])), 1) for j in range(n)]

    spread = max(1e-6, max(zones) - min(zones))
    uniformity = max(0.0, min(1.0, 1.0 - spread / 150.0))

    return {
        "time_min": [round(t, 2) for t in times],
        "optimal_curve_c": optimal,
        "actual_curve_c": actual,
        "recommended_zone_setpoints_c": recommended,
        "predicted_exit_uniformity": round(uniformity, 3),
    }
