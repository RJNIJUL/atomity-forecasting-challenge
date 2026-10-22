from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def build_targets(data_dir: Path) -> pd.DataFrame:
    cpu_path = data_dir / "vm_cpu_readings.csv.gz"
    cpu = pd.read_csv(cpu_path)

    targets = (
        cpu.groupby("timestamp")
        .agg(
            active_vm_count=("vm_id", "nunique"),
            aggregate_cpu_utilization=("avg_cpu", "mean"),
        )
        .reset_index()
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    return targets


def forecast_targets(targets: pd.DataFrame, horizon: int = 24) -> pd.DataFrame:
    if len(targets) <= horizon:
        raise ValueError("not enough observations for the requested forecast horizon")

    train = targets.iloc[:-horizon].copy()
    holdout = targets.iloc[-horizon:].copy()

    cpu_history = train["aggregate_cpu_utilization"].astype(float).tolist()

    model = ExponentialSmoothing(
        cpu_history,
        trend=None,
        seasonal=None,
        initialization_method="estimated",
    ).fit()

    cpu_forecast = model.forecast(horizon)

    predictions = pd.DataFrame({
        "timestamp": holdout["timestamp"].values,
        "active_vm_count": train["active_vm_count"].iloc[-1],
        "aggregate_cpu_utilization": cpu_forecast,
    })

    predictions["active_vm_count"] = predictions["active_vm_count"].astype(int)
    predictions["aggregate_cpu_utilization"] = (
        predictions["aggregate_cpu_utilization"].astype(float)
    )

    if not predictions["timestamp"].is_unique:
        raise ValueError("prediction timestamps must be unique")

    if predictions.isna().any().any():
        raise ValueError("predictions contain missing values")

    if not predictions["aggregate_cpu_utilization"].between(0, 100).all():
        raise ValueError("CPU predictions must be between 0 and 100")

    return predictions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    targets = build_targets(args.data)
    predictions = forecast_targets(targets)

    predictions.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()