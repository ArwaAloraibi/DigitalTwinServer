# DigitalTwinServer — Aircraft Sensor Dataset Integration

FastAPI-based digital twin server for aircraft engine monitoring with integrated Kaggle dataset support.

## Quick Start

### 1. Create a virtual environment and install dependencies

```bash
cd /home/arwa_aloraibi/code/ga/projects/project3/DigitalTwinServer
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Configure Kaggle credentials (already done)

Credentials are stored at `~/.config/kaggle/kaggle.json` (secure, 600 perms).

### 3. Download the aircraft sensor dataset

The dataset has already been downloaded to `data/Dataset/PM_train.txt` (20,631 rows of sensor data from 100 aircraft engines).

### 4. Run the FastAPI server with dataset metrics

```bash
export DATASET_CSV="$(pwd)/data/Dataset/PM_train.txt"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the endpoints

- **Engine data**: http://127.0.0.1:8000/engine
- **Dashboard**: http://127.0.0.1:8000/dashboard
- **Dataset metrics**: http://127.0.0.1:8000/dataset-metrics
- **WebSocket**: ws://127.0.0.1:8000/ws/engine (for real-time updates)

## Dataset Overview

**File**: `data/Dataset/PM_train.txt` (NASA CMAPSS Turbofan Engine Degradation Simulation Dataset)

**Structure**:
- 20,631 rows × 26 columns
- Column 0: Engine Unit ID (1-100)
- Column 1: Operating Cycle (time step)
- Columns 2-25: Sensor readings (24 sensors: temperatures, pressures, speeds, etc.)

**Computed Metrics**:
- **Remaining Useful Life (RUL)**: Mean 107.81 cycles, Max 361.00, Min 0.0
- **Sensor Degradation**: Average slope of sensor values over time (proxy for efficiency loss)
- **Units**: 100 aircraft engines tracked

## Example Response: `/dataset-metrics`

```json
{
  "available": true,
  "summary": {
    "rows": 20631,
    "units": 100,
    "mean_rul": 107.81,
    "max_rul": 361.00,
    "min_rul": 0.00,
    "mean_sensor_degradation_slope": 0.0185,
    "num_sensors": 24
  }
}
```

## Files

- `main.py` — FastAPI server with dataset integration
- `requirements.txt` — Python dependencies (fastapi, uvicorn, pandas, numpy)
- `utils/dataset_loader.py` — Dataset loader and degradation metrics computation
- `scripts/download_kaggle.py` — Helper script to download datasets from Kaggle
- `engine.json` — DTDL schema for digital twin
- `data/Dataset/PM_train.txt` — Aircraft sensor training data (20.6 MB uncompressed)

## Advanced Use: Download a Different Dataset

To download a different Kaggle dataset:

```bash
source venv/bin/activate
python scripts/download_kaggle.py owner/dataset-name --dest data --file output.txt
export DATASET_CSV="$(pwd)/data/output.txt"
python -m uvicorn main:app --reload
```

## Implementation Details

### Engine Degradation Metrics

The loader computes:

1. **Remaining Useful Life (RUL)**: For each sensor reading at cycle $c$ in engine $u$:
   $$\text{RUL}(u,c) = \max_{\text{cycle}}(u) - c$$

2. **Sensor Degradation**: Fit a linear model of each sensor value over operating cycles:
   $$\text{Slope}_{\text{sensor}} = \frac{\partial \text{SensorValue}}{\partial \text{Cycle}}$$
   
   The mean degradation slope aggregates all sensor/unit combinations and is a proxy for efficiency loss.

3. **Summary Statistics**: Row count, unit count, RUL percentiles, sensor count.

### DataFrame Format

All dataset files (`.txt`, `.csv`, `.xlsx`) are loaded into a DataFrame with no named columns.  
Column 0 = Unit ID, Column 1 = Cycle, Columns 2+ = Sensor values.

## Notes

- **Unit Normalization**: The dataset uses raw sensor units (temperatures in °R, pressures in psi, etc.). All computations are dimensionless (e.g., slopes are per-cycle).
- **RUL Interpretation**: RUL = 0 means end-of-life reached. Higher RUL = more useful cycles remaining before engine degradation becomes critical.
- **Sensor Count**: NASA CMAPSS includes 24 analog sensor readings per cycle.

## Troubleshooting

**"DATASET_CSV not set"**: Set the environment variable before starting the server:
```bash
export DATASET_CSV="$(pwd)/data/Dataset/PM_train.txt"
```

**"dataset utilities not available"**: Install pandas/numpy:
```bash
source venv/bin/activate
python -m pip install pandas numpy
```

**"File not found"**: Verify the path exists:
```bash
ls -la data/Dataset/PM_train.txt
```

---

**Next Steps**:
- Train a predictive model on the RUL data to forecast engine failures.
- Stream synthetic sensor data via WebSocket and compute real-time degradation metrics.
- Integrate a visualization dashboard (React/Vue) to display engine health in real-time.
