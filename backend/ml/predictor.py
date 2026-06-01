from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import torch

from app.config import settings
from app.schemas import HeatingCurveRequest
from ml.curve_heuristic import predict_curves
from ml.lstm_model import CurveLSTM, featurize_static


def _artifact_path() -> Path:
    base = Path(__file__).resolve().parent
    return (base / "artifacts" / "lstm_curve.pt").resolve()


def predict_with_model(req: HeatingCurveRequest) -> dict[str, Any] | None:
    path = Path(settings.ml_artifact_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / settings.ml_artifact_path
    if not path.exists():
        path = _artifact_path()
    if not os.path.exists(path):
        return None

    ckpt = torch.load(path, map_location="cpu", weights_only=False)
    out_len = int(ckpt.get("out_len", settings.sequence_length))
    model = CurveLSTM(out_len=out_len)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    x = featurize_static(
        req.slab_initial_temp_c,
        req.target_exit_temp_c,
        req.residence_time_min,
        req.fuel_flow_nm3h,
        req.conveyor_speed_mmin,
        req.zone_temperatures_c,
        req.steel_grade,
    )
    with torch.no_grad():
        curve_n, _z = model(x)
    curve = (curve_n.squeeze(0).numpy() * 1300.0).tolist()
    times = [req.residence_time_min * i / max(1, out_len - 1) for i in range(out_len)]
    base = predict_curves(req, sequence_len=out_len)
    # Blend ML trajectory with heuristic setpoints for stability
    blended_opt = [0.6 * c + 0.4 * h for c, h in zip(curve, base["optimal_curve_c"], strict=False)]
    base["optimal_curve_c"] = [round(x, 2) for x in blended_opt]
    base["time_min"] = [round(t, 2) for t in times]
    base["model_note"] = "LSTM checkpoint + heuristic blend"
    return base


def predict_heating(req: HeatingCurveRequest) -> dict[str, Any]:
    out = predict_with_model(req)
    if out is None:
        h = predict_curves(req, sequence_len=settings.sequence_length)
        h["model_note"] = "Heuristic baseline (train LSTM via ml/train_lstm.py)"
        return h
    return out
