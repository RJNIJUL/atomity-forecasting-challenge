# Cloud Workload Forecasting Challenge

AI/ML take-home challenge built from the **Microsoft Azure Public Dataset V2** VM trace.

## Start here

1. Read [`ASSIGNMENT.md`](ASSIGNMENT.md).
2. Read [`DATASET.md`](DATASET.md).
3. Download the **`data-v1` GitHub Release** dataset and extract it as `challenge_data/`.
4. Read [`SUBMISSION.md`](SUBMISSION.md).
5. Implement your analysis and forecasting pipeline.

The challenge dataset is distributed as a versioned GitHub Release rather than committed to the repository. The `data-v1` release contains the fixed curated dataset used for this assignment.

## Environment setup

Python **3.11 or newer** is required.

Create a virtual environment:

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
py -m venv .venv
.venv\Scripts\activate.bat
```

Install the project and development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Verify the installation:

```bash
python -m pytest -q
```

The repository includes a small test suite covering the starter forecasting utilities. Run it before beginning the assignment.

## Dataset download

The hiring dataset is distributed as the fixed `data-v1` release of this repository.

**Download:** [Azure Dataset v1 Release](https://github.com/atomityhq/forecasting-challenge/releases/tag/data-v1)

Download `data-v1.tar.gz` from the release and extract it into the repository as `challenge_data/`:

```bash
mkdir -p challenge_data
tar -xzf data-v1.tar.gz -C challenge_data
```

The resulting layout is:

```text
challenge_data/
├── vm_cpu_readings.csv.gz
├── vm_metadata.csv.gz
├── DATA_CARD.md
└── SHA256SUMS
```

Verify the dataset before starting the assignment:

```bash
cd challenge_data
sha256sum -c SHA256SUMS
```

You should see:

```text
vm_cpu_readings.csv.gz: OK
vm_metadata.csv.gz: OK
DATA_CARD.md: OK
```

The release is a real, curated subset of the Microsoft Azure Public Dataset V2. It is not synthetic data.

The dataset contains 10,000 VMs with 134 CPU measurements per VM at five-minute intervals, for a total of 1,340,000 CPU observations.

Use the exact `data-v1` release provided for this assignment. Do not substitute another dataset or a different version of the Azure Public Dataset.

## What you are solving

The underlying data contains anonymized VM workload telemetry sampled every five minutes. Your job is to understand the workload and build a defensible forecasting pipeline for near-term aggregate demand.

The challenge is intentionally open-ended. We evaluate reasoning, time-series methodology, leakage prevention, error analysis, reproducibility, and the quality of your operational conclusions—not just model complexity.


## Solution

The forecasting pipeline constructs two timestamp-level targets:

- `active_vm_count`: number of unique VMs represented at each timestamp.
- `aggregate_cpu_utilization`: mean VM-level `avg_cpu` across the VMs represented at each timestamp.

The dataset contains 134 timestamps at five-minute intervals. The first 110 timestamps are used for development and model selection, while the final 24 timestamps are kept as an untouched holdout.

### Validation

Model selection uses chronological walk-forward validation with a 24-timestamp forecast horizon. No random train/test split or future target information is used.

The following approaches were compared:

- Persistence / rolling baselines
- Random Forest using lag and rolling features
- Ridge Regression using lag and rolling features
- Exponential Smoothing

Exponential Smoothing achieved the best average walk-forward performance:

| Model | Average MAE | Average RMSE |
|---|---:|---:|
| 60-minute rolling mean | 0.2335 | 0.2613 |
| Random Forest | 0.2286 | 0.2570 |
| Ridge Regression | 0.2505 | 0.2780 |
| Exponential Smoothing | **0.2208** | **0.2510** |

The final model uses level-only Exponential Smoothing for aggregate CPU utilization. The active VM count is constant across the available timestamps, so the final forecast carries forward the latest observed count.

### Reproduce predictions

From the repository root, with the virtual environment activated:

```powershell
python -m cwfc.forecast --data challenge_data --output predictions.csv


## Expected environment

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Model dependencies are intentionally not prescribed. Add only what you need and document them.

## Source

Microsoft Azure Public Dataset V2:
https://github.com/Azure/AzurePublicDataset

The official V2 documentation describes a 30-day VM trace with five-minute CPU readings, VM metadata, and encrypted subscription/deployment/VM identifiers. The full upstream trace is much larger than this challenge release.

## Submission

Submit your work as a repository or archive according to [`SUBMISSION.md`](SUBMISSION.md).
