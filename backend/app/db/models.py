from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    zone_id: Mapped[int] = mapped_column(Integer, index=True)
    temperature_c: Mapped[float] = mapped_column(Float)
    fuel_flow_nm3h: Mapped[float] = mapped_column(Float)
    conveyor_speed_mmin: Mapped[float] = mapped_column(Float)


class EmissionSnapshot(Base):
    __tablename__ = "emission_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    fuel_type: Mapped[str] = mapped_column(String(32))
    fuel_rate_nm3h: Mapped[float] = mapped_column(Float)
    steel_throughput_tph: Mapped[float] = mapped_column(Float)
    co2_kg_per_ton: Mapped[float] = mapped_column(Float)
    co2_kg_total: Mapped[float] = mapped_column(Float)
    efficiency_score: Mapped[float] = mapped_column(Float)


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    recommended_fuel_nm3h: Mapped[float] = mapped_column(Float)
    predicted_exit_c: Mapped[float] = mapped_column(Float)
    uniformity_score: Mapped[float] = mapped_column(Float)
