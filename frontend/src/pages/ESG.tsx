import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { EmissionsSummary, EmissionsTrendPoint } from "@/api/client";
import { api } from "@/api/client";

export default function ESG() {
  const [sum, setSum] = useState<EmissionsSummary | null>(null);
  const [trend, setTrend] = useState<EmissionsTrendPoint[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const [s, t] = await Promise.all([
          api.get<EmissionsSummary>("/api/v1/emissions/summary"),
          api.get<EmissionsTrendPoint[]>("/api/v1/emissions/trend?window_hours=168"),
        ]);
        setSum(s.data);
        setTrend(t.data);
      } catch {
        /* ignore */
      }
    })();
  }, []);

  const series = trend.map((p) => ({
    ts: new Date(p.ts).toLocaleDateString(),
    co2: p.co2_kg_per_ton,
  }));

  const score = sum?.efficiency_score ?? 0;
  const hue = (score / 100) * 120;

  return (
    <>
      <h1>CO₂ emissions & ESG</h1>
      <p className="sub">kg CO₂ per ton of steel, synthetic trend when DB is empty.</p>
      <div className="grid cols-2">
        <div className="card">
          <h2>Efficiency score</h2>
          <div className="gauge" style={{ borderColor: `hsl(${hue}, 70%, 45%)` }}>
            <div style={{ textAlign: "center" }}>
              <div className="val">{score.toFixed(0)}</div>
              <div className="subg">0–100 (higher is cleaner)</div>
            </div>
          </div>
        </div>
        <div className="card">
          <h2>Snapshot</h2>
          {sum ? (
            <>
              <p>
                CO₂ / ton (now): <strong>{sum.co2_kg_per_ton_now} kg</strong>
              </p>
              <p>
                Daily estimate: <strong>{sum.daily_kg_co2.toLocaleString()} kg</strong>
              </p>
              <p>
                Weekly estimate: <strong>{sum.weekly_kg_co2.toLocaleString()} kg</strong>
              </p>
              <p className="sub">Fuel: {sum.fuel_type}</p>
            </>
          ) : (
            <p>Loading…</p>
          )}
        </div>
      </div>
      <div className="card" style={{ marginTop: "1rem", minHeight: 320 }}>
        <h2>CO₂ intensity trend</h2>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={series}>
            <defs>
              <linearGradient id="co2g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3dd6c3" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#3dd6c3" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2c3a50" />
            <XAxis dataKey="ts" stroke="#8fa3bd" interval={Math.floor(series.length / 8)} />
            <YAxis stroke="#8fa3bd" />
            <Tooltip />
            <Area type="monotone" dataKey="co2" stroke="#3dd6c3" fillOpacity={1} fill="url(#co2g)" name="kg/t" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
