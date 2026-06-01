import axios from "axios";

export const api = axios.create({ baseURL: "" });

export type LiveFurnaceState = {
  ts: string;
  zones: { zone_id: number; temperature_c: number; setpoint_c: number; fuel_share: number }[];
  slab_surface_avg_c: number;
  fuel_total_nm3h: number;
  conveyor_speed_mmin: number;
  anomaly_flags: string[];
};

export type HeatingCurveResponse = {
  time_min: number[];
  optimal_curve_c: number[];
  actual_curve_c: number[] | null;
  recommended_zone_setpoints_c: number[];
  predicted_exit_uniformity: number;
  model_note: string;
};

export type OptimizeResponse = {
  recommended_fuel_nm3h: number;
  recommended_zone_setpoints_c: number[];
  predicted_exit_temp_c: number;
  predicted_uniformity: number;
  objective_value: number;
  co2_kg_per_hour: number;
  constraints_ok: boolean;
  message: string;
};

export type EmissionsSummary = {
  co2_kg_per_ton_now: number;
  daily_kg_co2: number;
  weekly_kg_co2: number;
  efficiency_score: number;
  fuel_type: string;
};

export type EmissionsTrendPoint = {
  ts: string;
  co2_kg_per_ton: number;
  throughput_tph: number;
  fuel_rate_nm3h: number;
};

export type RecommendationItem = {
  title: string;
  severity: "info" | "warning" | "critical";
  detail: string;
  suggested_action: string;
};

export type WhatIfResponse = {
  baseline_exit_estimate_c: number;
  scenario_exit_estimate_c: number;
  baseline_fuel_nm3h: number;
  scenario_fuel_nm3h: number;
  baseline_co2_kg_h: number;
  scenario_co2_kg_h: number;
};
