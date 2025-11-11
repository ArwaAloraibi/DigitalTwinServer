from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from collections import deque

# optional dataset utilities (best-effort, requires pandas/numpy)
try:
    from utils.dataset_loader import dataset_summary, load_aircraft_dataset
except Exception:
    dataset_summary = None
    load_aircraft_dataset = None

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Store last 60 seconds of data
engine_history = deque(maxlen=60)

# Latest engine data
engine_data = {
    "energy": 500,
    "temp": 300
}

# If a dataset file is provided via environment variable, try to load and expose metrics
DATASET_CSV = os.getenv("DATASET_CSV")
_dataset_info = None
if DATASET_CSV and dataset_summary is not None:
    try:
        _dataset_info = dataset_summary(DATASET_CSV)
    except Exception as e:
        _dataset_info = {"error": f"Failed to load dataset: {str(e)}"}

@app.get("/engine")
async def get_engine_data():
    return JSONResponse(engine_data)


@app.get("/dataset-metrics")
async def dataset_metrics():
    """Return summary metrics from the loaded aircraft sensor dataset.
    
    Set DATASET_CSV=/path/to/PM_train.txt (or .csv, .xlsx) to enable.
    If pandas isn't installed or file isn't present, this will return a helpful message.
    """
    if DATASET_CSV is None:
        return JSONResponse({"available": False, "reason": "DATASET_CSV not set"})
    if dataset_summary is None:
        return JSONResponse({"available": False, "reason": "dataset utilities not available (install pandas/numpy)"})
    return JSONResponse({"available": True, "summary": _dataset_info})

@app.get("/dashboard")
async def dashboard():
    if engine_history:
        temps = [d['temp'] for d in engine_history]
        energies = [d['energy'] for d in engine_history]
        avg_temp = sum(temps) / len(temps)
        max_energy = max(energies)
        predicted_overheat = temps[-1] + 50
        alert = predicted_overheat > 550
    else:
        avg_temp = 0
        max_energy = 0
        alert = False

    html = f"""
    <html>
        <head><title>Digital Twin Dashboard</title></head>
        <body>
            <h1>Engine Digital Twin Dashboard</h1>
            <p>Current Temperature: {engine_data['temp']:.1f} °C</p>
            <p>Current Energy: {engine_data['energy']:.1f} kW</p>
            <p>Average Temperature (last {len(engine_history)}s): {avg_temp:.1f} °C</p>
            <p>Max Energy (last {len(engine_history)}s): {max_energy:.1f} kW</p>
            <p>Predicted Overheat: {"YES" if alert else "NO"}</p>
        </body>
    </html>
    """
    return HTMLResponse(html)

@app.websocket("/ws/engine")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            msg = await websocket.receive_json()  # receive data from 3D model
            engine_data["energy"] = msg["energy"]
            engine_data["temp"] = msg["temp"]

            # store in history
            engine_history.append({"energy": engine_data["energy"], "temp": engine_data["temp"]})

            # analytics
            avg_temp = sum(d['temp'] for d in engine_history)/len(engine_history)
            predicted_overheat = engine_data["temp"] + 50
            alert = predicted_overheat > 550

            # send back current state + analytics
            await websocket.send_json({
                "energy": engine_data["energy"],
                "temp": engine_data["temp"],
                "avg_temp": avg_temp,
                "predicted_overheat": predicted_overheat,
                "alert": alert
            })
        except Exception as e:
            print("WebSocket disconnected:", e)
            break
