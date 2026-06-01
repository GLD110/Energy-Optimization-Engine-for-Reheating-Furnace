import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from app.main import app

def main() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json() == {"status": "ok"}
        body = {
            "slab_initial_temp_c": 100,
            "steel_grade": "S355",
            "target_exit_temp_c": 1180,
            "zone_temperatures_c": [1000, 1050, 1100, 1150, 1180],
            "residence_time_min": 90,
            "fuel_flow_nm3h": 1200,
            "conveyor_speed_mmin": 1.8,
        }
        r = client.post("/api/v1/predict/heating-curve", json=body)
        assert r.status_code == 200, r.text
        j = r.json()
        assert len(j["time_min"]) == len(j["optimal_curve_c"])
        print("predict_ok", j["model_note"][:60])
        o = client.post(
            "/api/v1/optimize",
            json={**body, "fuel_type": "natural_gas", "fuel_price_per_nm3": 0.35},
        )
        assert o.status_code == 200, o.text
        print("optimize_ok", o.json()["recommended_fuel_nm3h"])


if __name__ == "__main__":
    main()
