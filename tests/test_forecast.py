import pandas as pd

from cwfc.forecast import forecast_targets


def test_forecast_targets_returns_expected_output():
    timestamps = list(range(0, 45 * 300, 300))

    targets = pd.DataFrame({
        "timestamp": timestamps,
        "active_vm_count": [10] * len(timestamps),
        "aggregate_cpu_utilization": [
            20 + (i % 5) for i in range(len(timestamps))
        ],
    })

    predictions = forecast_targets(targets, horizon=24)

    assert len(predictions) == 24
    assert list(predictions.columns) == [
        "timestamp",
        "active_vm_count",
        "aggregate_cpu_utilization",
    ]
    assert predictions["timestamp"].is_unique
    assert predictions["active_vm_count"].eq(10).all()
    assert predictions["aggregate_cpu_utilization"].between(0, 100).all()
    assert predictions["aggregate_cpu_utilization"].notna().all()