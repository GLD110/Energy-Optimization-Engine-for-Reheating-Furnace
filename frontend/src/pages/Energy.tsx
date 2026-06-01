import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { EmissionsTrendPoint, LiveFurnaceState, OptimizeResponse } from "@/api/client";
import { api } from "@/api/client";

const predictBody = {
  slab_initial_temp_c: 140,
  steel_grade: "S355",
  target_exit_temp_c: 1190,
  zone_temperatures_c: [1010, 1070, 1110, 1150, 1180],
  residence_time_min: 90,
  fuel_flow_nm3h: 1300,
  conveyor_speed_mmin: 1.75,
  fuel_type: "natural_gas" as const,
  fuel_price_per_nm3: 0.35,
};

export default function Energy() {
  const [live, setLive] = useState<LiveFurnaceState | null>(null);
  const [trend, setTrend] = useState<EmissionsTrendPoint[]>([]);
  const [opt, setOpt] = useState<OptimizeResponse | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [l, tr, o] = await Promise.all([
          api.get<LiveFurnaceState>("/api/v1/live"),
          api.get<EmissionsTrendPoint[]>("/api/v1/emissions/trend?window_hours=72"),
          api.post<OptimizeResponse>("/api/v1/optimize", predictBody),
        ]);
        setLive(l.data);
        setTrend(tr.data);
        setOpt(o.data);
      } catch {
        /* ignore */
      }
    })();
  }, []);

  const fuelSeries = trend.slice(-24).map((p, i) => ({
    h: `-${24 - i}h`,
    fuel: p.fuel_rate_nm3h,
  }));

  return (
    <>
      <h1>Energy consumption analytics</h1>
      <p className="sub">Live fuel proxy and recent fuel intensity from emissions trend endpoint.</p>
      <div className="grid cols-2">
        <div className="card">
          <h2>Live fuel (Nm³/h)</h2>
          {live ? <p style={{ fontSize: "2rem", margin: 0 }}>{live.fuel_total_nm3h}</p> : <p>Loading…</p>}
        </div>
        <div className="card">
          <h2>Optimizer output</h2>
          {opt ? (
            <>
              <p>
                Recommended fuel: <strong>{opt.recommended_fuel_nm3h.toFixed(0)} Nm³/h</strong>
              </p>
              <p>
                Predicted exit: <strong>{opt.predicted_exit_temp_c.toFixed(1)} °C</strong>
              </p>
              <p className="sub">{opt.message}</p>
            </>
          ) : (
            <p>Run backend to load optimizer.</p>
          )}
        </div>
      </div>
      <div className="card" style={{ marginTop: "1rem", minHeight: 320 }}>
        <h2>Fuel consumption (recent window)</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={fuelSeries}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2c3a50" />
            <XAxis dataKey="h" stroke="#8fa3bd" />
            <YAxis stroke="#8fa3bd" />
            <Tooltip />
            <Bar dataKey="fuel" fill="#1e9bff" name="Nm³/h" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
