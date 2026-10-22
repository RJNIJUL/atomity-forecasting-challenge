# Cloud Workload Forecasting Challenge

## 1. Executive Summary

This project forecasts near-term aggregate cloud workload demand from VM-level CPU telemetry sampled at five-minute intervals.

Two timestamp-level targets were constructed from the supplied VM readings:

* `active_vm_count`: number of unique VMs represented at each timestamp.
* `aggregate_cpu_utilization`: mean VM-level average CPU utilization across the VMs represented at each timestamp.

The dataset contains 10,000 VMs and 134 five-minute timestamps, giving 1,340,000 CPU observations. The first 110 timestamps were treated as the development period and the final 24 timestamps as an untouched two-hour holdout.

Several forecasting approaches were evaluated using chronological walk-forward validation. The tested approaches included persistence/rolling baselines, Random Forest regression with lag features, Ridge regression, and Exponential Smoothing.

Exponential Smoothing achieved the best average walk-forward performance, with an MAE of 0.2208 percentage points and RMSE of 0.2510 percentage points. It was selected as the final CPU forecasting method because it provided the best overall validation performance while remaining substantially simpler and easier to reproduce than the feature-based machine-learning alternatives.

The active VM count was constant at 10,000 across all observed timestamps, so no separate predictive model was required for this target.

## 2. Problem Definition

The objective was to forecast the next 24 timestamps, corresponding to two hours at the five-minute sampling cadence.

The challenge emphasizes time-aware validation, leakage prevention, reproducibility, error analysis, and operational reasoning rather than model complexity alone.

The forecasting problem was therefore treated as a chronological time-series task. The final 24 timestamps were never used for model selection or parameter fitting.

## 3. Data and Target Construction

The supplied challenge release contains VM metadata and CPU readings.

The CPU readings contain:

* `timestamp`
* `vm_id`
* `min_cpu`
* `max_cpu`
* `avg_cpu`

The data contains 134 unique timestamps:

* First timestamp: 0 seconds
* Last timestamp: 39,900 seconds
* Sampling interval: 300 seconds
* Sampling frequency: five minutes

The CPU table contains 1,340,000 observations and 10,000 unique VMs.

Data-quality checks found no missing values, duplicate rows, or duplicate `(timestamp, vm_id)` pairs in the CPU readings.

The targets were constructed directly from the VM-level readings:

```text
active_vm_count
    = number of unique vm_id values at each timestamp

aggregate_cpu_utilization
    = mean(avg_cpu) across represented VMs at each timestamp
```

The resulting target table contains 134 rows.

The active VM count was 10,000 at every timestamp. This indicates that the supplied challenge population was fully represented throughout the trace.

## 4. Development and Holdout Strategy

The complete target series was constructed before splitting the data chronologically.

The split was:

* Development period: first 110 timestamps
* Final holdout: last 24 timestamps

The development period ends at timestamp 32,700 seconds.

The final holdout begins at timestamp 33,000 seconds and ends at 39,900 seconds.

The final holdout targets were not used during model selection.

Within the development period, model evaluation used expanding-window walk-forward validation with a 24-timestamp forecast horizon.

The validation origins were 62, 70, 78, and 86 development observations. At each origin, the model was fitted only on observations available before that origin and then recursively forecast the following 24 timestamps.

This avoids the leakage that would occur if future development observations were used to train a model for an earlier validation origin.

## 5. Baselines and Models

### Persistence baseline

The persistence baseline forecasts the last observed CPU value across the full forecast horizon.

It provides a simple reference point for determining whether more sophisticated approaches provide useful improvement.

### Rolling mean baseline

A 60-minute rolling mean, corresponding to 12 five-minute observations, was evaluated as a second simple baseline.

Its average walk-forward performance was:

* MAE: 0.2335
* RMSE: 0.2613

The rolling mean performed well in some validation windows but struggled when the underlying workload regime changed.

### Random Forest

A Random Forest regressor was evaluated using:

* lag 1
* lag 2
* lag 3
* lag 6
* lag 12
* 12-point rolling mean

The model used 200 trees, maximum depth 5, and a fixed random seed.

Average walk-forward performance:

* MAE: 0.2286
* RMSE: 0.2570

This was slightly better than the rolling mean, but the improvement was relatively small.

### Ridge Regression

Ridge regression used the same lag and rolling features as the Random Forest.

Average walk-forward performance:

* MAE: 0.2505
* RMSE: 0.2780

It therefore did not improve on the simpler baseline or Random Forest and was not selected.

### Exponential Smoothing

A level-only Exponential Smoothing model was also evaluated.

No trend or seasonal component was imposed because the development series did not show a sufficiently stable repeating seasonal pattern at the available time scale.

Average walk-forward performance:

* MAE: 0.2208
* RMSE: 0.2510

This was the best average result among the tested approaches.

## 6. Model Comparison

| Model                  | Average MAE | Average RMSE |
| ---------------------- | ----------: | -----------: |
| 60-minute rolling mean |      0.2335 |       0.2613 |
| Random Forest          |      0.2286 |       0.2570 |
| Ridge Regression       |      0.2505 |       0.2780 |
| Exponential Smoothing  |  **0.2208** |   **0.2510** |

The improvement from Exponential Smoothing over the rolling mean is modest rather than dramatic.

This is important because it suggests that the aggregate CPU series is relatively difficult to predict beyond its recent level. A more complex model does not automatically provide a meaningful improvement.

The final model was therefore selected based on both validation performance and simplicity.

## 7. Error Analysis

Model performance varied considerably across validation origins.

For example, the Exponential Smoothing MAE values were:

| Origin |    MAE |
| -----: | -----: |
|     62 | 0.2861 |
|     70 | 0.3667 |
|     78 | 0.1017 |
|     86 | 0.1288 |

This variation indicates that the workload does not behave as a completely stable stationary process.

The development series contains periods where the aggregate CPU level changes noticeably. During such regime changes, models based primarily on recent history can temporarily lag behind the new level.

The validation results also show that no single model dominated every origin:

* Rolling mean performed best at origin 62.
* Exponential Smoothing performed best at origin 70.
* Random Forest performed best at origin 78.
* Rolling mean performed best at origin 86.

This supports using multiple chronological validation windows rather than selecting a model from a single train/validation split.

## 8. Peak and Regime Behavior

The aggregate CPU series showed short-term fluctuations and a higher-utilization regime during part of the development period.

Lag autocorrelation was strongest at short lags and decreased with longer lags. For example, the lag-1 autocorrelation was approximately 0.63, while the lag-12 correlation was approximately 0.18 and the lag-24 correlation was close to zero.

This suggests that recent observations contain useful information, but the series does not provide strong evidence of a stable daily seasonal cycle within the available trace.

A simple time trend was also weak, with a correlation of approximately -0.17 between the time index and aggregate CPU utilization. Therefore, a simple global linear trend was not considered sufficient justification for a trend-based forecasting model.

## 9. Final Forecast

After model selection, Exponential Smoothing was refitted using all 110 development observations.

The final model generated forecasts for the 24 untouched holdout timestamps.

The predicted aggregate CPU utilization was approximately:

```text
9.166976%
```

for each holdout timestamp.

The flat forecast is a consequence of using a level-only Exponential Smoothing model. After estimating the current underlying level, the model carries that level forward over the forecast horizon.

The active VM count forecast was 10,000 for all 24 timestamps because the observed count was constant throughout the available trace.

The resulting `predictions.csv` contains exactly 24 rows and the required columns:

```text
timestamp
active_vm_count
aggregate_cpu_utilization
```

The generated CPU predictions were checked to ensure that they were within the valid 0–100% range and contained no missing values.

Because the final holdout is intentionally kept untouched, no holdout MAE or RMSE is reported. Reporting such a metric would require using the withheld target values and would defeat the purpose of the holdout evaluation.

## 10. Operational Recommendation

For this dataset, the forecasting model should be treated primarily as a short-term workload-level signal rather than a precise prediction of individual VM behavior.

The forecast suggests an aggregate CPU utilization level around 9.17% over the next two hours, while the active VM population is expected to remain at approximately 10,000 based on the observed trace.

For capacity planning, this forecast could be combined with a safety margin rather than being used as an exact resource requirement. The validation results show that workload regimes can change, so an operational system should monitor forecast error and recent workload movement continuously.

A practical deployment would therefore:

1. Generate forecasts on the same five-minute cadence.
2. Compare recent actual utilization with the previous forecast.
3. Track rolling MAE or RMSE.
4. Trigger additional capacity investigation when utilization moves substantially above the forecast level.
5. Re-evaluate the model if the workload distribution or VM population changes materially.

## 11. Reproducibility

The final forecasting logic is implemented in:

```text
src/cwfc/forecast.py
```

Predictions can be reproduced from the repository root with:

```powershell
python -m cwfc.forecast --data challenge_data --output predictions.csv
```

The project also includes automated tests for the forecasting pipeline.

The final test suite contains three tests covering the forecasting output as well as the repository's existing metrics and validation utilities.

The challenge dataset itself is not committed to the repository. It is expected to be supplied separately through the versioned `data-v1` release.

## 12. Limitations and Future Work

The main limitation is the short historical horizon: only 134 five-minute timestamps are available. This restricts the ability to establish reliable long-term seasonal patterns.

The aggregate target also hides VM-level heterogeneity. Individual VMs may experience very different workload patterns even when the aggregate CPU level remains stable.

Future work could evaluate:

* Longer historical traces.
* Prediction intervals rather than point forecasts.
* Separate modeling of VM categories.
* More robust regime-change detection.
* Direct multi-step forecasting.
* Models specifically designed for changing workload distributions.

However, given the size and structure of the supplied challenge data, the selected level-based model provides a strong balance between validation performance, simplicity, and reproducibility.
