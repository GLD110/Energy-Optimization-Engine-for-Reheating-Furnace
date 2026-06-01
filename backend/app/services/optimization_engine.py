"""Constrained fuel/zone optimization using SciPy (baseline before RL)."""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from app.schemas import HeatingCurveRequest, OptimizeRequest
from app.services.emissions import estimate_co2
from ml.curve_heuristic import predict_curves


@dataclass
class PhysicsParams:
    heat_transfer_coeff: float = 0.018
    fuel_to_power: float = 0.55  # abstract gain: °C per Nm³/h per minute scaling


def _simulate_exit_and_uniformity(
    req: HeatingCurveRequest,
    fuel_nm3h: float,
    zone_setpoints: np.ndarray,
) -> tuple[float, float, float]:
    """Lightweight surrogate: exit temp rises with fuel and setpoints; uniformity from zone spread."""
    target = req.target_exit_temp_c
    t0 = req.slab_initial_temp_c
    tau = max(req.residence_time_min, 1.0)
    avg_zone = float(np.mean(zone_setpoints))
    gain = PhysicsParams.fuel_to_power * (fuel_nm3h / 2000.0) * np.sqrt(tau)
    exit_est = min(target + 40, t0 + gain * 420 + 0.012 * (avg_zone - t0) * tau)
    spread = float(np.std(zone_setpoints))
    uniformity = max(0.0, 1.0 - min(1.0, spread / 120.0))
    deviation_penalty = abs(exit_est - target)
    return exit_est, uniformity, deviation_penalty


def optimize_schedule(req: OptimizeRequest) -> dict:
    n_z = len(req.zone_temperatures_c)
    z0 = np.array(req.zone_temperatures_c, dtype=float)
    max_fuel = req.max_fuel_nm3h or max(req.fuel_flow_nm3h * 1.4, 500.0)

    def objective(x: np.ndarray) -> float:
        fuel = float(x[0])
        dz = x[1 : 1 + n_z]
        zones = z0 + dz
        exit_est, uniformity, dev = _simulate_exit_and_uniformity(req, fuel, zones)
        em = estimate_co2(req.fuel_type, fuel, steel_throughput_tph=50.0)
        fuel_cost = fuel * req.fuel_price_per_nm3
        co2_cost = em.co2_kg_per_hour * req.co2_price_per_kg
        # Reward-style as minimization: penalize deviation, maximize uniformity via (1-u)
        return (
            fuel_cost
            + co2_cost
            + 2.5 * dev
            + 35.0 * (1.0 - uniformity)
            + 0.001 * max(0.0, exit_est - req.target_exit_temp_c) ** 2
        )

    x0 = np.concatenate([[req.fuel_flow_nm3h], np.zeros(n_z)])
    bounds = [(50.0, max_fuel)] + [(-40.0, 40.0)] * n_z

    def con_exit(x: np.ndarray) -> float:
        fuel = float(x[0])
        zones = z0 + x[1 : 1 + n_z]
        exit_est, _, _ = _simulate_exit_and_uniformity(req, fuel, zones)
        return exit_est - (req.target_exit_temp_c - 12.0)

    def con_no_overheat(x: np.ndarray) -> float:
        fuel = float(x[0])
        zones = z0 + x[1 : 1 + n_z]
        exit_est, _, _ = _simulate_exit_and_uniformity(req, fuel, zones)
        return (req.target_exit_temp_c + 25.0) - exit_est

    cons = (
        {"type": "ineq", "fun": con_exit},
        {"type": "ineq", "fun": con_no_overheat},
    )

    res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 120})
    if not res.success:
        res = minimize(objective, x0, method="SLSQP", bounds=bounds, options={"maxiter": 200})
    x_opt = res.x if res.success else x0
    fuel_opt = float(x_opt[0])
    zones_opt = (z0 + x_opt[1 : 1 + n_z]).tolist()
    exit_est, u_score, _ = _simulate_exit_and_uniformity(req, fuel_opt, np.array(zones_opt))
    em = estimate_co2(req.fuel_type, fuel_opt, steel_throughput_tph=50.0)

    hc = predict_curves(req)
    ml_zones = hc["recommended_zone_setpoints_c"]
    n = min(len(zones_opt), len(ml_zones))
    blended_zones = [0.5 * (zones_opt[i] + ml_zones[i]) for i in range(n)]
    if len(blended_zones) < len(zones_opt):
        blended_zones.extend(zones_opt[len(blended_zones) :])

    ok = res.success and (req.target_exit_temp_c - 15) <= exit_est <= (req.target_exit_temp_c + 25)

    return {
        "recommended_fuel_nm3h": fuel_opt,
        "recommended_zone_setpoints_c": blended_zones,
        "predicted_exit_temp_c": exit_est,
        "predicted_uniformity": u_score,
        "objective_value": float(res.fun),
        "co2_kg_per_hour": em.co2_kg_per_hour,
        "constraints_ok": bool(ok),
        "message": "SLSQP constrained optimum blended with ML setpoints."
        if ok
        else "Optimizer finished; verify constraints on plant digital twin.",
        "raw_optimizer": json.dumps({"success": bool(res.success), "nit": int(res.nit)}),
    }
