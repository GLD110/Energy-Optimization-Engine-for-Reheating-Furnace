import { useState } from "react";
import type { WhatIfResponse } from "@/api/client";
import { api } from "@/api/client";

const base = {
  slab_initial_temp_c: 130,
  steel_grade: "S355",
  target_exit_temp_c: 1185,
  zone_temperatures_c: [1000, 1060, 1100, 1145, 1175],
  residence_time_min: 92,
  fuel_flow_nm3h: 1250,
  conveyor_speed_mmin: 1.8,
};

export default function WhatIf() {
  const [df, setDf] = useState(-5);
  const [dc, setDc] = useState(0);
  const [res, setRes] = useState<WhatIfResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await api.post<WhatIfResponse>("/api/v1/whatif", {
        base,
        delta_fuel_pct: df,
        delta_conveyor_pct: dc,
      });
      setRes(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1>What-if simulation</h1>
      <p className="sub">Fast surrogate comparing fuel and speed deltas against the same zone snapshot.</p>
      <div className="card" style={{ marginBottom: "1rem" }}>
        <div className="row">
          <label>
            Δ fuel %
            <input type="number" value={df} onChange={(e) => setDf(Number(e.target.value))} />
          </label>
          <label>
            Δ conveyor %
            <input type="number" value={dc} onChange={(e) => setDc(Number(e.target.value))} />
          </label>
          <button className="primary" type="button" disabled={loading} onClick={run}>
            Simulate
          </button>
        </div>
      </div>
      {res && (
        <div className="grid cols-2">
          <div className="card">
            <h2>Exit temperature</h2>
            <p>
              Baseline: <strong>{res.baseline_exit_estimate_c} °C</strong>
            </p>
            <p>
              Scenario: <strong>{res.scenario_exit_estimate_c} °C</strong>
            </p>
          </div>
          <div className="card">
            <h2>Fuel & CO₂</h2>
            <p>
              Fuel {res.baseline_fuel_nm3h} → {res.scenario_fuel_nm3h} Nm³/h
            </p>
            <p>
              CO₂ {res.baseline_co2_kg_h} → {res.scenario_co2_kg_h} kg/h
            </p>
          </div>
        </div>
      )}
    </>
  );
}
