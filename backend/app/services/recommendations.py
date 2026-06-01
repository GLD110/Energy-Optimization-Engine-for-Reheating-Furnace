from app.schemas import LiveFurnaceState, RecommendationItem


def build_recommendations(state: LiveFurnaceState) -> list[RecommendationItem]:
    items: list[RecommendationItem] = []
    max_z = max((z["temperature_c"] for z in state.zones), default=0)
    min_z = min((z["temperature_c"] for z in state.zones), default=0)
    spread = max_z - min_z
    if spread > 80:
        items.append(
            RecommendationItem(
                title="High cross-zone thermal spread",
                severity="warning",
                detail=f"ΔT across zones is {spread:.0f} °C; uneven heating increases scrap risk.",
                suggested_action="Lower preheat zone setpoint 10–15 °C and increase soak zone fuel share slightly.",
            )
        )
    if state.fuel_total_nm3h > 1350:
        items.append(
            RecommendationItem(
                title="Fuel above rolling average",
                severity="info",
                detail="Total fuel flow is elevated versus typical load.",
                suggested_action="Run constrained optimizer with tightened exit band and review conveyor speed.",
            )
        )
    if state.anomaly_flags:
        items.append(
            RecommendationItem(
                title="Anomaly indicators",
                severity="critical",
                detail=", ".join(state.anomaly_flags),
                suggested_action="Inspect burner alignment and roll pyrometer calibration.",
            )
        )
    if not items:
        items.append(
            RecommendationItem(
                title="Process within envelope",
                severity="info",
                detail="No hard violations detected on surrogate rules.",
                suggested_action="Continue monitoring ESG panel and schedule weekly model refresh.",
            )
        )
    return items
