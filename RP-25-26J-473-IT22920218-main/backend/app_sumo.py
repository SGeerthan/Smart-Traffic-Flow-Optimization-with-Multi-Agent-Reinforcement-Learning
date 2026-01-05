import asyncio
import sys
import os
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from controller.state_models import StatusResponse, EmergencyInfo, SignalState, DecisionInfo, Road, RoadMetricsSet, PredictionSet, PredictionMetrics, InputHealthInfo, WestCameraInfo, DetectionInfo, TrafficCounts, RoadVehicleCounts
from controller.sumo_connector import SUMOConnector
from controller.traffic_controller import TrafficController
from controller.memory_store import MemoryStore
from controller.prediction import TrafficPredictor
from controller.data_provider import HybridProvider
from controller.road_provider import HybridProvider as RoadHybridProvider, FakeProvider
from controller.yolo_west_source import YoloWestSource

# Load environment variables
load_dotenv()

app = FastAPI(title="Smart Traffic Backend (SUMO)", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SUMO configuration path
SUMO_CFG = os.path.join(os.path.dirname(__file__), "..", "sumo", "junction.sumocfg")

# Metrics logging path
METRICS_LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "logs.jsonl")

# Ensure logs directory exists
os.makedirs(os.path.dirname(METRICS_LOG_PATH), exist_ok=True)

# Load hybrid provider configuration from environment
USE_CAMERA_WEST = os.getenv("USE_CAMERA_WEST", "false").lower() == "true"
WEST_CAMERA_INDEX = int(os.getenv("WEST_CAMERA_INDEX", "0"))
WEST_MODEL_PATH = os.getenv("WEST_MODEL_PATH", "models/best.pt")
WEST_CONF = float(os.getenv("WEST_CONF", "0.20"))
WEST_IOU = float(os.getenv("WEST_IOU", "0.45"))
WEST_IMGSZ = int(os.getenv("WEST_IMGSZ", "960"))
WEST_MAX_DET = int(os.getenv("WEST_MAX_DET", "100"))
WEST_USE_TRACKING = os.getenv("WEST_USE_TRACKING", "false").lower() == "true"
WEST_ROI = os.getenv("WEST_ROI", "")
WEST_SMOOTHING_ENABLED = os.getenv("WEST_SMOOTHING_ENABLED", "true").lower() == "true"
WEST_SMOOTHING_WINDOW = int(os.getenv("WEST_SMOOTHING_WINDOW", "5"))
WEST_RESIZE_WIDTH = int(os.getenv("WEST_RESIZE_WIDTH", "960"))

# Task 3: WEST source mode configuration (webcam or video)
WEST_SOURCE_MODE = os.getenv("WEST_SOURCE_MODE", "webcam").lower()
WEST_VIDEO_PATH = os.getenv("WEST_VIDEO_PATH", "")
WEST_LOOP_VIDEO = os.getenv("WEST_LOOP_VIDEO", "false").lower() == "true"

# Core simulation components
memory_store = MemoryStore("data/memory.json")
sumo_connector = None  # Initialized on start
controller = TrafficController(memory_store=memory_store)
predictor = TrafficPredictor()
data_provider = HybridProvider(
    use_camera_west=USE_CAMERA_WEST,
    camera_index=WEST_CAMERA_INDEX,
    model_path=WEST_MODEL_PATH,
    conf=WEST_CONF,
    iou=WEST_IOU,
    imgsz=WEST_IMGSZ,
    max_det=WEST_MAX_DET,
    use_tracking=WEST_USE_TRACKING,
    roi_west=WEST_ROI,
    smoothing_enabled=WEST_SMOOTHING_ENABLED,
    smoothing_window=WEST_SMOOTHING_WINDOW,
    resize_width=WEST_RESIZE_WIDTH,
    source_mode=WEST_SOURCE_MODE,
    video_path=WEST_VIDEO_PATH if WEST_VIDEO_PATH else None,
    loop_video=WEST_LOOP_VIDEO,
)

source_info = f"mode={WEST_SOURCE_MODE}"
if WEST_SOURCE_MODE == "video":
    source_info += f", video={WEST_VIDEO_PATH}, loop={WEST_LOOP_VIDEO}"
else:
    source_info += f", cam={WEST_CAMERA_INDEX}"

logger.info(f"Hybrid Provider initialized: USE_CAMERA_WEST={USE_CAMERA_WEST}, {source_info}, "
            f"model_path={WEST_MODEL_PATH}, conf={WEST_CONF}, roi={'set' if WEST_ROI else 'none'}, "
            f"smoothing={WEST_SMOOTHING_ENABLED}")

# Initialize unified road provider (fake for N/E/S, YOLO for WEST) - created at simulation start
road_provider = None

# Direct YOLO WEST source (singleton)
yolo_west = None
if USE_CAMERA_WEST:
    try:
        yolo_west = YoloWestSource(
            model_path=WEST_MODEL_PATH,
            cam_index=WEST_CAMERA_INDEX,
            conf=WEST_CONF,
            iou=WEST_IOU,
            imgsz=WEST_IMGSZ,
            max_det=WEST_MAX_DET,
            use_tracking=WEST_USE_TRACKING,
            roi_str=WEST_ROI,
            smoothing_window=WEST_SMOOTHING_WINDOW,
            enable_smoothing=WEST_SMOOTHING_ENABLED,
            resize_width=WEST_RESIZE_WIDTH,
            source_mode=WEST_SOURCE_MODE,
            video_path=WEST_VIDEO_PATH if WEST_VIDEO_PATH else None,
            loop_video=WEST_LOOP_VIDEO,
        )
        yolo_west.start()
        logger.info(f"[INIT] YoloWestSource started: model={WEST_MODEL_PATH}, cam={WEST_CAMERA_INDEX}, mode={WEST_SOURCE_MODE}")
    except Exception as e:
        logger.error(f"[INIT] Failed to start YoloWestSource: {e}", exc_info=True)
        yolo_west = None
else:
    logger.info("[INIT] YoloWestSource disabled (USE_CAMERA_WEST=false)")

# Runtime state
simulation_active: bool = False
_sim_task: Optional[asyncio.Task] = None
_time_sec: int = 0
_current_status: Optional[StatusResponse] = None

class ControlResponse(BaseModel):
    status: str
    message: Optional[str] = None

def _log_metrics(time_sec: int, metrics: RoadMetricsSet, signal_state: SignalState, predictions: Optional[Dict] = None):
    """Log metrics and predictions to JSONL file for analysis"""
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "simulation_time": time_sec,
            "metrics": metrics.dict(),
            "signal": {
                "green_road": signal_state.greenRoad.value,
                "remaining_seconds": signal_state.remaining
            }
        }
        
        # Add prediction data if available
        if predictions:
            log_entry["predictions"] = {}
            for road, pred in predictions.items():
                log_entry["predictions"][road.value] = {
                    "queue_trend": pred.get("queue_trend", "stable"),
                    "heavy_traffic_probability": pred.get("heavy_traffic_probability", 0.0),
                    "congestion_level": pred.get("congestion_level", "LOW"),
                    "predicted_eta_clear_seconds": pred.get("predicted_eta_clear_seconds", 0),
                }
        
        with open(METRICS_LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Warning: Could not log metrics: {e}")

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    global _current_status
    if _current_status is None:
        # Return idle status
        from controller.state_models import TrafficCounts, RoadVehicleCounts
        empty_counts = TrafficCounts(
            north=RoadVehicleCounts(),
            east=RoadVehicleCounts(),
            south=RoadVehicleCounts(),
            west=RoadVehicleCounts(),
        )
        input_health = InputHealthInfo(**data_provider.get_health_status())
        camera_info_dict = data_provider.get_camera_info()
        west_camera = WestCameraInfo(
            camera_ok=camera_info_dict["camera_ok"],
            last_frame_ts=camera_info_dict["last_frame_ts"],
            detections=[DetectionInfo(**d) for d in camera_info_dict["detections"]],
            using_fake_fallback=camera_info_dict["using_fake_fallback"],
        )
        _current_status = StatusResponse(
            time=_time_sec,
            counts=empty_counts,
            queues={Road.north: 0, Road.east: 0, Road.south: 0, Road.west: 0},
            signal=SignalState(greenRoad=Road.south, remaining=0),
            emergency=EmergencyInfo(active=False, road=None),
            decision=DecisionInfo(method="idle", reason="simulation not started"),
            inputs=input_health,
            west_camera=west_camera,
        )
    return _current_status

@app.get("/api/memory/summary")
async def memory_summary():
    return memory_store.summary()

@app.get("/api/west/camera/frame")
async def get_west_camera_frame():
    """
    Get latest annotated frame from WEST camera as JPEG.
    Returns 503 if camera disabled or unavailable.
    """
    frame_bytes = data_provider.get_camera_frame_jpeg()
    if frame_bytes is None:
        return Response(
            content=b"",
            status_code=503,
            media_type="application/json",
            headers={"X-Camera-Status": "unavailable"}
        )
    return Response(content=frame_bytes, media_type="image/jpeg", headers={
        "Cache-Control": "no-store",
        "Pragma": "no-cache"
    })

@app.get("/api/west/camera/status")
async def get_west_camera_status():
    """
    Get detailed WEST camera status including detections.
    Returns camera health, detection list, and fallback status.
    """
    return data_provider.get_camera_info()

# === Manual Control API Endpoints ===

class ModeRequest(BaseModel):
    mode: str  # "AUTO" or "MANUAL"

class ModeResponse(BaseModel):
    mode: str
    manual_active: bool
    manual_command: Optional[str] = None
    remaining_seconds: int = 0

class ManualApplyRequest(BaseModel):
    command: str  # "NS_GREEN" | "EW_GREEN" | "ALL_RED"
    duration: int  # 10-120 seconds

class ManualApplyResponse(BaseModel):
    status: str
    message: str
    command: str
    duration: int

@app.get("/api/control/mode", response_model=ModeResponse)
async def get_control_mode():
    """Get current control mode (AUTO or MANUAL)"""
    import time
    current_time = time.time()
    
    remaining = 0
    if controller.mode == "MANUAL" and controller.manual_until:
        remaining = max(0, int(controller.manual_until - current_time))
    
    return ModeResponse(
        mode=controller.mode,
        manual_active=(controller.mode == "MANUAL"),
        manual_command=controller.manual_command,
        remaining_seconds=remaining
    )

@app.post("/api/control/mode", response_model=ModeResponse)
async def set_control_mode(request: ModeRequest):
    """Switch between AUTO and MANUAL mode"""
    import time
    current_time = time.time()
    
    if request.mode not in ["AUTO", "MANUAL"]:
        raise ValueError("Mode must be 'AUTO' or 'MANUAL'")
    
    if request.mode == "AUTO":
        controller.cancel_manual()
        _log_manual_event("mode_change", "AUTO", None, 0, "user_request")
    else:
        # Just set mode to MANUAL, command will be applied separately
        controller.mode = "MANUAL"
        _log_manual_event("mode_change", "MANUAL", None, 0, "user_request")
    
    remaining = 0
    if controller.mode == "MANUAL" and controller.manual_until:
        remaining = max(0, int(controller.manual_until - current_time))
    
    return ModeResponse(
        mode=controller.mode,
        manual_active=(controller.mode == "MANUAL"),
        manual_command=controller.manual_command,
        remaining_seconds=remaining
    )

@app.post("/api/control/manual/apply", response_model=ManualApplyResponse)
async def apply_manual_control(request: ManualApplyRequest):
    """Apply a manual control command with duration"""
    import time
    current_time = time.time()
    
    # Validate command
    valid_commands = ["NS_GREEN", "EW_GREEN", "ALL_RED"]
    if request.command not in valid_commands:
        return ManualApplyResponse(
            status="error",
            message=f"Invalid command. Must be one of: {', '.join(valid_commands)}",
            command=request.command,
            duration=request.duration
        )
    
    # Validate duration
    if not (10 <= request.duration <= 120):
        return ManualApplyResponse(
            status="error",
            message="Duration must be between 10 and 120 seconds",
            command=request.command,
            duration=request.duration
        )
    
    # Apply manual control
    controller.set_manual_mode(request.command, request.duration, current_time)
    _log_manual_event("manual_apply", "MANUAL", request.command, request.duration, "user_request")
    
    return ManualApplyResponse(
        status="success",
        message=f"Manual control applied: {request.command} for {request.duration}s",
        command=request.command,
        duration=request.duration
    )

@app.post("/api/control/manual/cancel", response_model=ControlResponse)
async def cancel_manual_control():
    """Cancel manual override and return to AUTO mode"""
    if controller.mode != "MANUAL":
        return ControlResponse(status="info", message="Not in manual mode")
    
    controller.cancel_manual()
    _log_manual_event("manual_cancel", "AUTO", None, 0, "user_request")
    
    return ControlResponse(status="success", message="Manual control cancelled, returned to AUTO mode")

def _log_manual_event(event_type: str, mode: str, command: Optional[str], duration: int, reason: str):
    """Log manual control events to JSONL file"""
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "simulation_time": _time_sec,
            "event_type": event_type,  # mode_change, manual_apply, manual_expire, manual_cancel, emergency_interrupt
            "mode": mode,
            "command": command,
            "duration": duration,
            "reason": reason
        }
        
        with open(METRICS_LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Warning: Could not log manual event: {e}")

@app.post("/api/control/start", response_model=ControlResponse)
async def start_simulation():
    global simulation_active, _sim_task, sumo_connector
    if simulation_active:
        return ControlResponse(status="already_running")
    
    try:
        # Initialize SUMO connector
        sumo_connector = SUMOConnector(SUMO_CFG, use_gui=True)
        sumo_connector.connect()
        
        simulation_active = True
        _sim_task = asyncio.create_task(_run_loop())
        return ControlResponse(status="started", message="SUMO simulation started with GUI")
    except Exception as e:
        return ControlResponse(status="error", message=f"Failed to start SUMO: {str(e)}")

@app.post("/api/control/stop", response_model=ControlResponse)
async def stop_simulation():
    global simulation_active, _sim_task, sumo_connector
    simulation_active = False
    if _sim_task:
        _sim_task.cancel()
        _sim_task = None
    if sumo_connector:
        sumo_connector.disconnect()
        sumo_connector = None
    # Cleanup data provider resources (camera, etc)
    try:
        data_provider.shutdown()
    except Exception as e:
        logger.warning(f"Error shutting down data provider: {e}")
    return ControlResponse(status="stopped", message="SUMO simulation stopped")

# WebSocket clients
_ws_clients: List[WebSocket] = []

@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.append(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            _ws_clients.remove(websocket)
        except ValueError:
            pass

def _convert_predictions_to_prediction_set(predictions: Optional[Dict]) -> PredictionSet:
    """Convert prediction dictionary to PredictionSet model."""
    if not predictions:
        return PredictionSet()
    
    def to_metrics(pred_dict: dict) -> PredictionMetrics:
        return PredictionMetrics(
            queue_trend=pred_dict.get("queue_trend", "stable"),
            arrivals_10s=pred_dict.get("arrivals_10s", 0.0),
            arrivals_30s=pred_dict.get("arrivals_30s", 0.0),
            heavy_traffic_probability=pred_dict.get("heavy_traffic_probability", 0.0),
            congestion_level=pred_dict.get("congestion_level", "LOW"),
            predicted_eta_clear_seconds=pred_dict.get("predicted_eta_clear_seconds", 0),
        )
    
    return PredictionSet(
        north=to_metrics(predictions.get(Road.north, {})),
        east=to_metrics(predictions.get(Road.east, {})),
        south=to_metrics(predictions.get(Road.south, {})),
        west=to_metrics(predictions.get(Road.west, {})),
    )

async def _broadcast_update(status: StatusResponse):
    stale: List[WebSocket] = []
    for ws in list(_ws_clients):
        try:
            await ws.send_json(status.dict())
        except Exception:
            stale.append(ws)
    for s in stale:
        try:
            _ws_clients.remove(s)
        except ValueError:
            pass

async def _run_loop():
    global _time_sec, _current_status, simulation_active, sumo_connector
    
    # Reset controller state
    controller.reset()
    predictor.reset()
    _time_sec = 0

    try:
        # Initialize unified road provider at simulation start
        global road_provider
        if road_provider is None:
            fake_provider = FakeProvider(data_provider.fake_gen)
            yolo_west = data_provider.yolo_source if USE_CAMERA_WEST else None
            road_provider = RoadHybridProvider(fake_provider, yolo_west)
            logger.info(f"[INIT] Road provider ready: USE_CAMERA_WEST={USE_CAMERA_WEST}, yolo_west={yolo_west is not None}")
            if yolo_west:
                logger.info(f"[INIT] YoloWestSource initialized: {yolo_west}")
        
        while simulation_active and sumo_connector.is_running():
            import time
            current_real_time = time.time()
            
            # 1) Step SUMO simulation
            sumo_connector.step()
            
            # 2) Get vehicle counts from unified provider (WEST=camera if ok, N/E/S=fake)
            road_counts_dict = road_provider.get_counts()
            metadata = road_provider.get_metadata()
            
            # Debug: log raw counts every second
            if _time_sec % 1 == 0:
                logger.debug(f"[RAW] road_counts_dict WEST: {road_counts_dict['west']}, metadata: {metadata}")
            
            # Convert to TrafficCounts object for controller
            counts = TrafficCounts(
                north=RoadVehicleCounts(**road_counts_dict["north"]),
                east=RoadVehicleCounts(**road_counts_dict["east"]),
                south=RoadVehicleCounts(**road_counts_dict["south"]),
                west=RoadVehicleCounts(**road_counts_dict["west"]),
            )
            
            # 2.5) OVERRIDE WEST with direct YOLO if available (ensures camera data is used)
            west_source = "sumo"
            if yolo_west is not None:
                try:
                    west_counts = yolo_west.get_latest_counts()
                    if west_counts and isinstance(west_counts, dict):
                        # Replace only west part of counts with camera data
                        counts.west.car = west_counts.get("car", 0)
                        counts.west.bike = west_counts.get("bike", 0)
                        counts.west.bus = west_counts.get("bus", 0)
                        counts.west.truck = west_counts.get("truck", 0)
                        counts.west.lorry = west_counts.get("lorry", 0)
                        counts.west.auto = west_counts.get("auto", 0)
                        west_source = "camera"
                        
                        # Update metadata to reflect camera usage
                        metadata['west_source'] = 'camera'
                except Exception as e:
                    logger.error(f"[WEST OVERRIDE] Failed to get camera counts: {e}")
            
            # Debug logging every 2 seconds
            if _time_sec % 2 == 0:
                west_total = counts.west.car + counts.west.bike + counts.west.bus + counts.west.truck + counts.west.lorry + counts.west.auto
                logger.info(f"[WEST INPUT] t={_time_sec}, using_camera={yolo_west is not None}, "
                           f"west_source={west_source}, west_counts={counts.west.dict()}, total={west_total}")
            
            emergency = sumo_connector.detect_emergency()

            # 3) Update vehicle tracking for metrics
            sumo_connector._update_vehicle_tracking()

            # 4) Compute queues
            queues = controller.compute_queues(counts)

            # 5) Compute metrics
            metrics = sumo_connector.compute_metrics()

            # 6) Compute predictions using queue history
            predictions = predictor.predict(metrics)

            # 7) Tick controller: decide next phase with metrics and predictions
            decision_info = controller.tick_and_decide(
                time_sec=_time_sec,
                counts=counts,
                queues=queues,
                metrics=metrics,
                emergency=emergency,
                predictions=predictions,
            )
            
            # 7.5) Append west_source to decision reason for debugging
            if west_source == "camera":
                decision_info.reason = f"{decision_info.reason} [west_source=camera]"
            else:
                decision_info.reason = f"{decision_info.reason} [west_source=sumo]"
            
            # 8) Send phase command to SUMO
            # Handle manual ALL_RED command specially
            if controller.mode == "MANUAL" and controller.manual_command == "ALL_RED":
                sumo_connector.set_all_red(duration=1)
            else:
                sumo_connector.set_green_phase(controller.current_green, controller.remaining_green)
            
            # Check if manual expired and log
            if controller.check_manual_expired(current_real_time):
                _log_manual_event("manual_expire", "AUTO", None, 0, "duration_expired")

            # 9) Build manual info
            from controller.state_models import ManualInfo
            manual_info = ManualInfo(
                active=(controller.mode == "MANUAL"),
                command=controller.manual_command,
                remaining_seconds=controller.get_manual_remaining(current_real_time)
            )
            
            # 9a) Build input health info (camera status)
            input_health = InputHealthInfo(**data_provider.get_health_status())
            
            # 10) Get actual SUMO green state
            actual_green_info = sumo_connector.get_actual_green_info()
            
            # 10.5) Get WEST camera info for dashboard display
            camera_info_dict = data_provider.get_camera_info()
            west_camera = WestCameraInfo(
                camera_ok=camera_info_dict["camera_ok"],
                last_frame_ts=camera_info_dict["last_frame_ts"],
                detections=[DetectionInfo(**d) for d in camera_info_dict["detections"]],
                using_fake_fallback=camera_info_dict["using_fake_fallback"],
            )
            
            # Debug: Log WEST counts before building status (every 2 seconds)
            if _time_sec % 2 == 0:
                west_total = counts.west.car + counts.west.bike + counts.west.bus + counts.west.truck + counts.west.lorry + counts.west.auto
                logger.info(f"[STATUS_BUILD] t={_time_sec}, WEST_total={west_total}, WEST_counts={counts.west.dict()}")
            
            # 11) Build status object with metrics, predictions, manual info, input health, and SUMO actual state
            _current_status = StatusResponse(
                time=_time_sec,
                counts=counts,
                queues=queues,
                signal=SignalState(greenRoad=controller.current_green, remaining=controller.remaining_green),
                emergency=emergency,
                decision=decision_info,
                metrics=metrics,
                prediction=_convert_predictions_to_prediction_set(predictions),
                mode=controller.mode,
                manual=manual_info,
                inputs=input_health,
                west_camera=west_camera,
                sumo_phase_index=actual_green_info["sumo_phase_index"],
                sumo_tls_state=actual_green_info["sumo_tls_state"],
                actual_green_group=actual_green_info["actual_green_group"],
                actual_green_roads=actual_green_info["actual_green_roads"],
            )

            # 12) Log metrics and predictions every decision cycle
            if _time_sec % controller.decision_cycle == 0:
                _log_metrics(_time_sec, metrics, _current_status.signal, predictions)

            # 13) Broadcast to WebSocket clients
            await _broadcast_update(_current_status)

            # 14) Advance time
            _time_sec += 1
            await asyncio.sleep(1)
            
        # Simulation ended
        simulation_active = False
        if sumo_connector:
            sumo_connector.disconnect()
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in simulation loop: {e}")
        simulation_active = False
        if sumo_connector:
            sumo_connector.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
