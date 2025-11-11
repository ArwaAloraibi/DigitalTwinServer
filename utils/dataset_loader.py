"""Dataset loader for engine sensor data (NASA CMAPSS format or similar).

Supports space-delimited .txt, .csv, .xlsx formats.
Computes engine efficiency / degradation metrics from raw sensor data.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional


def load_aircraft_dataset(path: str) -> pd.DataFrame:
    """Load aircraft sensor data from .txt, .csv, or .xlsx file.
    
    Supports space-delimited files (common in NASA CMAPSS format).
    Returns a DataFrame with no column names (caller responsibility to map).
    
    Args:
        path: Path to the data file (.txt, .csv, or .xlsx).
    
    Returns:
        DataFrame with raw sensor data.
    
    Raises:
        FileNotFoundError if file doesn't exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    if path.lower().endswith(('.xlsx', '.xls')):
        df = pd.read_excel(path, header=None)
    elif path.lower().endswith('.txt'):
        # Assume space-delimited (NASA CMAPSS format)
        df = pd.read_csv(path, sep=r'\s+', header=None)
    else:
        # Try CSV
        df = pd.read_csv(path, header=None)
    
    return df


def compute_engine_degradation(df: pd.DataFrame, 
                               unit_id_col: int = 0,
                               cycle_col: int = 1,
                               sensor_cols: Optional[list] = None) -> Tuple[Dict, pd.DataFrame]:
    """Compute engine degradation metrics from sensor data.
    
    For each unit (engine), computes:
    - Remaining Useful Life (RUL) = max_cycle - current_cycle (synthetic)
    - Sensor trend (slope of sensor values over time as proxy for efficiency degradation)
    - Mean and std of key sensors
    
    Args:
        df: DataFrame with columns: [unit_id, cycle, ...sensors...]
        unit_id_col: Column index for unit/engine ID (default: 0)
        cycle_col: Column index for cycle/time step (default: 1)
        sensor_cols: List of column indices to use for degradation (default: all except first 2)
    
    Returns:
        (summary_dict, enriched_df) where:
        - summary_dict has keys: mean_rul, max_rul, mean_sensor_degradation, etc.
        - enriched_df is df with added 'RUL' column
    """
    if sensor_cols is None:
        sensor_cols = list(range(2, df.shape[1]))
    
    # Copy to avoid mutating input
    df_enrich = df.copy()
    
    # Compute RUL for each unit
    max_cycle_per_unit = df_enrich.groupby(unit_id_col)[cycle_col].max()
    
    def compute_rul(row):
        unit = row[unit_id_col]
        cycle = row[cycle_col]
        return max_cycle_per_unit[unit] - cycle
    
    df_enrich['RUL'] = df_enrich.apply(compute_rul, axis=1)
    
    # Compute sensor degradation (slope of sensor values over time per unit)
    degradation_slopes = []
    for unit_id in df_enrich[unit_id_col].unique():
        unit_data = df_enrich[df_enrich[unit_id_col] == unit_id]
        for sensor_idx in sensor_cols:
            # Simple linear regression: compute slope of sensor vs cycle
            X = unit_data[cycle_col].values
            y = unit_data[sensor_idx].values
            if len(X) > 1 and not np.all(np.isnan(y)):
                # Fit a line
                valid_idx = ~np.isnan(y)
                if valid_idx.sum() > 1:
                    slope = np.polyfit(X[valid_idx], y[valid_idx], 1)[0]
                    degradation_slopes.append(slope)
    
    # Summary metrics
    summary = {
        "rows": int(len(df_enrich)),
        "units": int(df_enrich[unit_id_col].nunique()),
        "mean_rul": float(np.mean(df_enrich['RUL'])),
        "max_rul": float(np.max(df_enrich['RUL'])),
        "min_rul": float(np.min(df_enrich['RUL'])),
        "mean_sensor_degradation_slope": float(np.mean(degradation_slopes)) if degradation_slopes else None,
        "num_sensors": int(len(sensor_cols))
    }
    
    return summary, df_enrich


def dataset_summary(path: str) -> Dict:
    """Load dataset and return summary with degradation metrics.
    
    Args:
        path: Path to aircraft sensor dataset file.
    
    Returns:
        Dictionary with summary stats and degradation metrics.
    """
    try:
        df = load_aircraft_dataset(path)
    except Exception as e:
        return {"error": f"Failed to load dataset: {str(e)}"}
    
    try:
        summary, _ = compute_engine_degradation(df)
        return summary
    except Exception as e:
        return {"error": f"Failed to compute metrics: {str(e)}"}
