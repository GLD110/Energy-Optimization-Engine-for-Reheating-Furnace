import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { HeatingCurveResponse } from "@/api/client";
import { api } from "@/api/client";

const defaultBody = {
  slab_initial_temp_c: 120,
  steel_grade: "S355",
  target_exit_temp_c: 1180,
  zone_temperatures_c: [1020, 1080, 1120, 1160, 1185],
  residence_time_min: 95,
  fuel_flow_nm3h: 1280,
  conveyor_speed_mmin: 1.8,
};

export default function HeatingCurve() {
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState<HeatingCurveResponse | null>(null);

  const chartData = useMemo(() => {
    if (!resp) return [];
    return resp.time_min.map((t, i) => ({
      t,
      optimal: resp.optimal_curve_c[i],
      actual: resp.actual_curve_c ? resp.actual_curve_c[i] : null,
    }));
  }, [resp]);

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await api.post<HeatingCurveResponse>("/api/v1/predict/heating-curve", defaultBody);
      setResp(data);
      setNote(data.model_note);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1>Predicted heating curve</h1>
      <p className="sub">LSTM when `ml/artifacts/lstm_curve.pt` exists; otherwise grade-aware heuristic.</p>
      <div className="row" style={{ marginBottom: "1rem" }}>
        <button className="primary" type="button" disabled={loading} onClick={run}>
          {loading ? "Running…" : "Predict curve"}
        </button>
        {note && <span className="pill">{note}</span>}
      </div>
      {resp && (
        <div className="grid cols-2">
          <div className="card" style={{ minHeight: 360 }}>
            <h2>Trajectory</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2c3a50" />
                <XAxis dataKey="t" name="min" stroke="#8fa3bd" />
                <YAxis stroke="#8fa3bd" domain={["auto", "auto"]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="optimal" stroke="#3dd6c3" dot={false} name="Optimal °C" />
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="#7aa7ff"
                  dot={false}
                  connectNulls
                  name="Actual est. °C"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="card">
            <h2>Recommended zone setpoints</h2>
            <p className="sub" style={{ marginTop: 0 }}>
              Uniformity score: {(resp.predicted_exit_uniformity * 100).toFixed(1)}%
            </p>
            <div className="heatmap">
              {resp.recommended_zone_setpoints_c.map((sp, idx) => (
                <div key={idx} className="cell" style={{ background: "#182433" }}>
                  <div>Z{idx + 1}</div>
                  <strong>{sp.toFixed(0)}°C</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
