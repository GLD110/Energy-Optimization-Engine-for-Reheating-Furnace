from __future__ import annotations

import torch
import torch.nn as nn


class CurveLSTM(nn.Module):
    """Maps static batch features to a temporal furnace temperature trajectory."""

    def __init__(
        self,
        static_dim: int = 16,
        hidden: int = 64,
        layers: int = 2,
        out_len: int = 48,
    ) -> None:
        super().__init__()
        self.out_len = out_len
        self.encoder = nn.Sequential(
            nn.Linear(static_dim, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
        )
        self.cell = nn.LSTM(
            input_size=hidden,
            hidden_size=hidden,
            num_layers=layers,
            batch_first=True,
        )
        self.head = nn.Linear(hidden, 1)
        self.zone_head = nn.Linear(hidden, 1)

    def forward(self, x_static: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # x_static: (B, static_dim)
        h0 = self.encoder(x_static).unsqueeze(1).repeat(1, self.out_len, 1)
        y, _ = self.cell(h0)
        curve = self.head(y).squeeze(-1)
        z = self.zone_head(y[:, -1, :]).squeeze(-1)
        return curve, z


def featurize_static(
    t0: float,
    tgt: float,
    tau: float,
    fuel: float,
    speed: float,
    zones: list[float],
    grade: str,
    pad_zones: int = 8,
) -> torch.Tensor:
    import hashlib

    vec: list[float] = [
        t0 / 1300.0,
        tgt / 1300.0,
        tau / 240.0,
        fuel / 4000.0,
        speed / 30.0,
        sum(zones) / max(1, len(zones)) / 1300.0,
        (max(zones) - min(zones)) / 200.0 if zones else 0.0,
    ]
    zpad = list(zones[:pad_zones]) + [0.0] * max(0, pad_zones - len(zones))
    vec.extend([z / 1300.0 for z in zpad])
    gh = int(hashlib.md5(grade.encode(), usedforsecurity=False).hexdigest()[:4], 16) / 65535.0
    vec.append(gh)
    while len(vec) < 16:
        vec.append(0.0)
    return torch.tensor(vec[:16], dtype=torch.float32).unsqueeze(0)
