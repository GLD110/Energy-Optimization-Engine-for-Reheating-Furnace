"""Train CurveLSTM on synthetic furnace batches; writes ml/artifacts/lstm_curve.pt."""

from __future__ import annotations

import math
import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from ml.lstm_model import CurveLSTM, featurize_static


class SyntheticCurveDataset(Dataset):
    def __init__(self, n: int = 2000, out_len: int = 48) -> None:
        self.n = n
        self.out_len = out_len
        self.grades = ["S235", "S355", "S460", "C45", "304SS"]

    def __len__(self) -> int:
        return self.n

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        rng = random.Random(idx)
        t0 = rng.uniform(20, 350)
        tgt = rng.uniform(1050, 1250)
        tau = rng.uniform(25, 180)
        fuel = rng.uniform(400, 3200)
        speed = rng.uniform(0.8, 12)
        nz = rng.randint(3, 8)
        zones = [rng.uniform(900, 1220) for _ in range(nz)]
        grade = rng.choice(self.grades)
        x = featurize_static(t0, tgt, tau, fuel, speed, zones, grade)
        times = [tau * i / (self.out_len - 1) for i in range(self.out_len)]
        curve = []
        for i, tt in enumerate(times):
            alpha = i / max(1, self.out_len - 1)
            s = 1 / (1 + math.exp(-10 * (alpha - 0.45)))
            val = t0 + (tgt - t0) * s * (0.9 + rng.random() * 0.08)
            curve.append(val / 1300.0)
        y = torch.tensor(curve, dtype=torch.float32)
        return x.squeeze(0), y


def train(epochs: int = 8, batch: int = 64, out_len: int = 48) -> Path:
    ds = SyntheticCurveDataset(n=2500, out_len=out_len)
    dl = DataLoader(ds, batch_size=batch, shuffle=True)
    model = CurveLSTM(out_len=out_len)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    model.train()
    for _ in range(epochs):
        for xb, yb in dl:
            opt.zero_grad()
            pred, _ = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()
    out_dir = Path(__file__).resolve().parent / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "lstm_curve.pt"
    torch.save({"state_dict": model.state_dict(), "out_len": out_len}, path)
    return path


if __name__ == "__main__":
    p = train()
    print("saved", p)
