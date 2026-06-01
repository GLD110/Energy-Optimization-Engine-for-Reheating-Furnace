import { useEffect, useState } from "react";
import type { LiveFurnaceState } from "@/api/client";
import { api } from "@/api/client";

function tempColor(t: number) {
  const x = Math.min(1, Math.max(0, (t - 980) / 280));
  const r = Math.round(40 + 180 * x);
  const g = Math.round(70 + 120 * (1 - Math.abs(x - 0.55)));
  const b = Math.round(120 + 80 * (1 - x));
  return `rgb(${r},${g},${b})`;
}

export default function Live() {
  const [data, setData] = useState<LiveFurnaceState | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let on = true;
    const tick = async () => {
      try {
        const { data: d } = await api.get<LiveFurnaceState>("/api/v1/live");
        if (on) {
          setData(d);
          setErr(null);
        }
      } catch {
        if (on) setErr("Cannot reach API. Start backend on port 8000.");
      }
    };
    tick();
    const id = setInterval(tick, 4000);
    return () => {
      on = false;
      clearInterval(id);
    };
  }, []);

  return (
    <>
      <h1>Furnace live view</h1>
      <p className="sub">Simulated multi-zone telemetry with lightweight anomaly rules.</p>
      {err && <div className="card">{err}</div>}
      {data && (
        <div className="grid cols-2">
          <div className="card">
            <h2>Zone heatmap</h2>
            <div className="heatmap">
              {data.zones.map((z) => (
                <div key={z.zone_id} className="cell" style={{ background: tempColor(z.temperature_c) }}>
                  <div>Z{z.zone_id}</div>
                  <strong>{z.temperature_c}°C</strong>
                  <div style={{ opacity: 0.85, marginTop: 4 }}>SP {z.setpoint_c}°C</div>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <h2>Process KPIs</h2>
            <p>
              Slab surface avg: <strong>{data.slab_surface_avg_c} °C</strong>
            </p>
            <p>
              Total fuel: <strong>{data.fuel_total_nm3h} Nm³/h</strong>
            </p>
            <p>
              Conveyor: <strong>{data.conveyor_speed_mmin} m/min</strong>
            </p>
            <p>
              Flags:{" "}
              {data.anomaly_flags.length === 0 ? (
                <span className="pill">none</span>
              ) : (
                data.anomaly_flags.map((f) => (
                  <span key={f} className="pill danger" style={{ marginRight: 6 }}>
                    {f}
                  </span>
                ))
              )}
            </p>
          </div>
        </div>
      )}
    </>
  );
}
