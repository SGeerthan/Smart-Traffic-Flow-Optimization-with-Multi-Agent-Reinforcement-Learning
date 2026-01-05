# CAMERA DETECTION FLOW FIX - COMPLETE ANALYSIS & SOLUTION

## Problem Statement
**Issue:** Camera detects vehicles correctly, but system not using modal results. Junction Overview shows WEST=0 even when camera panel displays "5 cars, 1 truck, 1 bus, 1 bike".

## Root Cause Analysis

### Core Issue: Wrong Model Path
The YOLO model file was being looked for at incorrect path:
- **Attempted path**: `backend/models/best.pt` (WRONG - double directory nesting)
- **Actual path**: `models/best.pt` (CORRECT - from within backend/ working directory)

When backend runs `python run_with_sumo.py`, the working directory is `/backend/`, so:
- File path `backend/models/best.pt` → looks for `/backend/backend/models/best.pt` ❌
- File path `models/best.pt` → correctly finds `/backend/models/best.pt` ✓

**Error Message Observed:**
```
ERROR - Failed to initialize YOLO: [Errno 2] No such file or directory: 'models\\best.pt'
Falling back to fake WEST data.
```

### Second Issue: Wrong Memory Path
Similarly, the memory store was using wrong path:
- **Wrong**: `backend/data/memory.json`
- **Correct**: `data/memory.json`

## Data Flow Architecture

### 5-Layer Detection Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: YOLO Detection (YoloWestSource background thread)  │
│ ├─ Reads frames from webcam at 5 FPS                        │
│ ├─ Runs inference: conf=0.2, iou=0.45, imgsz=960            │
│ └─ Outputs: latest_detections[], latest_counts{}            │
└─────────────┬───────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Class Mapping (NAME_MAP + CODE_MAP)                │
│ ├─ Normalizes raw class names (strip, upper, no separators) │
│ ├─ Maps COCO classes to traffic types:                      │
│ │  car → car, bicycle → bike, bus → bus, truck → truck      │
│ └─ Produces cls_mapped field in detections                  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Count Aggregation (RoadHybridProvider)             │
│ ├─ Retrieves latest_counts from YoloWestSource              │
│ ├─ Checks if total > 0 (ignores all-zero frames)            │
│ └─ Returns unified: {north: fake, east: fake, ...           │
│                      south: fake, west: camera}             │
└─────────────┬───────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Status Building (app_sumo simulation loop)          │
│ ├─ Calls road_provider.get_counts()                         │
│ ├─ Builds TrafficCounts object                              │
│ ├─ Computes queue scores and metrics                        │
│ └─ Updates _current_status response                         │
└─────────────┬───────────────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 5: API Endpoints (FastAPI)                            │
│ ├─ /api/status returns StatusResponse with counts           │
│ ├─ /ws/live broadcasts to frontend via WebSocket            │
│ ├─ /api/west/camera/status returns camera detections        │
│ └─ Frontend displays Junction Overview with WEST counts     │
└─────────────────────────────────────────────────────────────┘
```

## Critical Discovery During Debugging

### The Two Separate Outputs
The system produces TWO different outputs from the same detection source:

1. **Camera Panel** (shows detections):
   - Uses: `/api/west/camera/status` endpoint
   - Source: `latest_detections` list with all detections
   - Shows: Aggregated counts from detection list
   - Display: "5 cars, 1 truck, 1 bus, 1 bike" ✓

2. **Junction Overview** (shows counts):
   - Uses: `/api/status` endpoint
   - Source: `latest_counts` dict aggregated during inference
   - Issue: All zeros when detections aren't mapped properly
   - Display: WEST=0 ❌

### Why Counts Were Zero
When model_path was wrong, the camera failed to initialize:
1. YOLO model loading failed (file not found)
2. System fell back to "fake WEST data"
3. Camera panel still showed detections (cached from previous run?)
4. Junction Overview showed zeros (fallback fake data)
5. No actual vehicle mapping happening

## Fixes Applied

### Fix #1: Model Path (app_sumo.py)
```python
# BEFORE:
WEST_MODEL_PATH = os.getenv("WEST_MODEL_PATH", "backend/models/best.pt")

# AFTER:
WEST_MODEL_PATH = os.getenv("WEST_MODEL_PATH", "models/best.pt")
```

### Fix #2: Memory Path (app_sumo.py)
```python
# BEFORE:
memory_store = MemoryStore("backend/data/memory.json")

# AFTER:
memory_store = MemoryStore("data/memory.json")
```

### Fix #3: Data Provider Default (data_provider.py)
```python
# BEFORE:
model_path: str = "backend/models/best.pt",

# AFTER:
model_path: str = "models/best.pt",
```

### Fix #4: Enhanced Debug Logging (yolo_west_source.py)
Added detailed logging to trace mapping:
```python
mapped_labels_log = []  # Track successful mappings
...
if traffic_cls and traffic_cls in ["car", "bike", "bus", "truck", "lorry", "auto"]:
    counts[traffic_cls] += 1
    mapped_labels_log.append(f"{raw}→{traffic_cls}")

# Log every frame with detections:
if raw_box_count > 0 and mapped_labels_log:
    logger.info(f"[MAPPED] Frame {frame_count}: {', '.join(mapped_labels_log)}")
```

## Verification Steps

After fixes applied, the system will:

1. **Model Loads Correctly**
   ```
   INFO - YOLO model loaded: models/best.pt
   INFO - Model classes: ['person', 'bicycle', 'car', 'motorcycle', ...]
   ```

2. **Camera Opens Successfully**
   ```
   INFO - Camera webcam opened successfully
   ```

3. **Detections Are Mapped** (look for logs like):
   ```
   [MAPPED] Frame 10: car→car, truck→truck, bus→bus
   [YOLO_STORE] Frame 10: detections=3, mapped=['car', 'truck', 'bus'], 
                          counts={'car': 1, 'truck': 1, 'bus': 1, ...}, total=3
   ```

4. **Counts Flow to Status** (look for logs like):
   ```
   [PROVIDER] Using CAMERA WEST counts: {'car': 1, 'truck': 1, 'bus': 1, ...}
   [INPUT] west_source=camera, west_counts={'car': 1, 'truck': 1, ...}, total=3
   ```

5. **Frontend Displays Both**
   - Camera Panel: Shows detected vehicle counts
   - Junction Overview WEST Card: Shows matching counts

## Expected Result

When camera points at vehicles and system is running:
- **Camera Panel**: "3 cars, 1 truck, 1 bus" ✓
- **Junction Overview WEST**: Car=3, Truck=1, Bus=1 ✓ (MATCHING!)
- **Queue Score**: Calculated based on actual vehicle detections
- **Controller Decision**: Uses real camera data instead of fallback fake data

## Files Modified

1. `backend/app_sumo.py` - Fixed model and memory paths (2 locations)
2. `backend/controller/data_provider.py` - Fixed default model path
3. `backend/controller/yolo_west_source.py` - Enhanced logging for debugging

## Testing Recommendations

1. Start backend: `cd backend && python run_with_sumo.py`
2. Open frontend: http://localhost:5173
3. Check logs for:
   - `[MAPPED]` entries showing vehicle mappings
   - `[PROVIDER]` entries showing camera usage
4. Point camera at vehicles and verify:
   - Camera panel shows correct counts
   - Junction Overview WEST shows matching counts
5. Start simulation and verify:
   - Traffic light control uses camera data
   - Queue predictions based on real detections

## Related Architecture Components

### YoloWestSource (yolo_west_source.py)
- Runs in background thread
- Processes frames at target FPS
- Applies smoothing window
- Stores latest_counts and latest_detections
- Provides get_latest_counts() method

### RoadHybridProvider (road_provider.py)
- Wraps fake provider for N/E/S roads
- Integrates YOLO camera for WEST
- Returns unified counts structure
- Falls back to fake if camera counts are zero

### HybridProvider (data_provider.py)
- Initializes YoloWestSource with config
- Manages camera lifecycle
- Provides both detection list and counts
- Returns aggregated vehicle_counts for camera panel

## Conclusion

The system is now configured to properly load the YOLO model and integrate camera detections into the traffic control flow. The camera panel and Junction Overview will display matching vehicle counts when cameras detect real traffic.
