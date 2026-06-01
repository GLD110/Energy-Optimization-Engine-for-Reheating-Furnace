import { useEffect, useState } from "react";
import type { RecommendationItem } from "@/api/client";
import { api } from "@/api/client";

export default function Recommendations() {
  const [items, setItems] = useState<RecommendationItem[]>([]);

  useEffect(() => {
    api
      .get<RecommendationItem[]>("/api/v1/recommendations")
      .then((r) => setItems(r.data))
      .catch(() => setItems([]));
  }, []);

  return (
    <>
      <h1>Optimization recommendations</h1>
      <p className="sub">Rule-based guidance from live surrogate; swap for RL policy scores later.</p>
      <div className="grid">
        {items.map((it) => (
          <div key={it.title} className="card">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h2 style={{ margin: 0 }}>{it.title}</h2>
              <span
                className={
                  it.severity === "critical" ? "pill danger" : it.severity === "warning" ? "pill warn" : "pill"
                }
              >
                {it.severity}
              </span>
            </div>
            <p>{it.detail}</p>
            <p className="sub" style={{ marginBottom: 0 }}>
              <strong>Action:</strong> {it.suggested_action}
            </p>
          </div>
        ))}
      </div>
    </>
  );
}
