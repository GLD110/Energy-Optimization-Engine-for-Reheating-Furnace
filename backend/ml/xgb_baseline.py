"""Optional XGBoost tabular baseline: predicts mean optimal temperature from static inputs."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import xgboost as xgb

from ml.lstm_model import featurize_static


def _synth_rows(n: int = 5000) -> tuple[np.ndarray, np.ndarray]:
    xs: list[np.ndarray] = []
    ys: list[float] = []
    for i in range(n):
        rng = random.Random(i)
        t0 = rng.uniform(20, 400)
        tgt = rng.uniform(1040, 1260)
        tau = rng.uniform(20, 200)
        fuel = rng.uniform(300, 3500)
        speed = rng.uniform(0.7, 15)
        nz = rng.randint(3, 8)
        zones = [rng.uniform(880, 1230) for _ in range(nz)]
        grade = rng.choice(["S235", "S355", "S460"])
        v = featurize_static(t0, tgt, tau, fuel, speed, zones, grade).squeeze(0).numpy()
        xs.append(v)
        ys.append(float(0.55 * t0 + 0.45 * tgt + 0.02 * (fuel / 1000.0) * tau))
    return np.stack(xs), np.array(ys, dtype=np.float32)


def train_xgb(path: Path | None = None) -> Path:
    path = path or Path(__file__).resolve().parent / "artifacts" / "xgb_mean_temp.json"
    X, y = _synth_rows()
    dtrain = xgb.DMatrix(X, label=y)
    params = {"max_depth": 6, "eta": 0.08, "objective": "reg:squarederror"}
    booster = xgb.train(params, dtrain, num_boost_round=80)
    path.parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(path))
    return path


if __name__ == "__main__":
    p = train_xgb()
    print("saved", p)
