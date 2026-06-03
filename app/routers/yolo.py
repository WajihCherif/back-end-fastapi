import base64
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from datetime import datetime
from app.db import SessionLocal
from app.services.alert_service import AlertService
from app.models.etagere import Etagere
# pyrefly: ignore [missing-import]
from ultralytics import YOLO
import json
import os

router = APIRouter(
    prefix="/yolo",
    tags=["yolo"]
)

# Load the trained YOLOv8-OBB model (empty shelf detection)
MODEL_PATH = (
    "C:/Users/wajih/Empty spaces in a supermarket hanger.v29i.yolov8-obb"
    "/runs/detect/train/weights/best.pt"
)
model = YOLO(MODEL_PATH)

# Load standard YOLOv8 model for person detection (COCO class 0: person)
COCO_MODEL_PATH = "C:/Users/wajih/Empty spaces in a supermarket hanger.v29i.yolov8-obb/yolov8n.pt"
if os.path.exists(COCO_MODEL_PATH):
    person_model = YOLO(COCO_MODEL_PATH)
else:
    person_model = YOLO("yolov8n.pt")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Server-side per-camera state for box-missing tracking
    # Structure: { cam_key: { last_count:int, timer_task:asyncio.Task|None, missing_count:int, missing_since:datetime|None, timeout_minutes:int, alert_fired:bool } }
    if not hasattr(websocket.app.state, 'camera_states'):
        websocket.app.state.camera_states = {}
    camera_states = websocket.app.state.camera_states
    alert_service = AlertService()
    try:
        while True:
            # Receive data from the client. Expect JSON string with { camKey, image }
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                cam_key = payload.get('camKey')
                image_data = payload.get('image')
            except Exception:
                # Fallback: client sent raw base64 string
                cam_key = None
                image_data = data

            # Decode base64 image
            header, encoded = image_data.split(",", 1) if "," in image_data else ("", image_data)
            nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                await websocket.send_json({"error": "Invalid image data"})
                continue

            # Run inference
            results = model(img, verbose=False)
            
            # Run person detection
            person_results = person_model(img, verbose=False)
            has_person = False
            for r in person_results:
                if r.boxes is not None and len(r.boxes) > 0:
                    cls = r.boxes.cls.cpu().numpy()
                    if 0 in cls:  # 0 is the COCO class for 'person'
                        has_person = True
                        break
            
            detections = []
            for r in results:
                # ── OBB model path ──────────────────────────────────
                # r.obb is not None only when the model is an OBB model
                # AND it detected something. An empty tensor is falsy,
                # so we must check `is not None` first, then `len > 0`.
                if r.obb is not None and len(r.obb) > 0:
                    boxes = r.obb.xyxyxyxy.cpu().numpy()  # (N, 4, 2)
                    confs = r.obb.conf.cpu().numpy()
                    cls   = r.obb.cls.cpu().numpy()

                    for i in range(len(boxes)):
                        detections.append({
                            "corners":    boxes[i].tolist(),
                            "confidence": float(confs[i]),
                            "class":      int(cls[i]),
                            "label":      model.names[int(cls[i])],
                        })

                # ── Standard (non-OBB) model fallback ───────────────
                elif r.boxes is not None and len(r.boxes) > 0:
                    boxes = r.boxes.xyxy.cpu().numpy()
                    confs = r.boxes.conf.cpu().numpy()
                    cls   = r.boxes.cls.cpu().numpy()

                    for i in range(len(boxes)):
                        detections.append({
                            "bbox":       boxes[i].tolist(),
                            "confidence": float(confs[i]),
                            "class":      int(cls[i]),
                            "label":      model.names[int(cls[i])],
                        })
                # else: no detections this frame — detections stays []

            # Determine product count (product label or class==2)
            product_count = sum(1 for d in detections if d.get('label') == 'product' or d.get('class') == 2)

            # Server-side box-missing tracking
            try:
                if cam_key:
                    state = camera_states.get(cam_key, {
                        'last_count': product_count,
                        'timer_task': None,
                        'missing_count': 0,
                        'missing_since': None,
                        'timeout_minutes': 5,
                        'alert_fired': False,
                    })

                    last = state.get('last_count', product_count)

                    async def box_alert_watcher(key, missing_count, timeout_minutes):
                        await asyncio.sleep(timeout_minutes * 60)
                        s = websocket.app.state.camera_states.get(key)
                        # If state missing or alert already fired, skip
                        if not s or s.get('alert_fired'):
                            return
                        current_count = s.get('last_count', 0)
                        missing = s.get('missing_count', 0)
                        # If still missing, create alert in DB
                        if current_count < ( (s.get('missing_count') or missing) + current_count ):
                            # Resolve etagere and product info from DB
                            db = SessionLocal()
                            try:
                                et = db.query(Etagere).filter(Etagere.etagere_code == key).first()
                                product_id = et.product_id if et else None
                                product_name = et.product.name if (et and et.product) else (et.name if et else 'Unknown')
                                expected_quantity = et.quantity_etagere if et else (current_count + missing)

                                message = f"{missing} box(es) of \"{product_name}\" missing from shelf {et.name if et else key} (code {key}) for {timeout_minutes} minute(s)."

                                alert_service.create_alert(
                                    db=db,
                                    product_id=product_id or 0,
                                    product_name=product_name or 'Unknown',
                                    alert_type='box_missing',
                                    expected_quantity=expected_quantity,
                                    actual_quantity=current_count,
                                    message=message,
                                    quantity_etagere=current_count,
                                    boxes_missing_count=missing,
                                    state_change_time=s.get('missing_since'),
                                    timeout_minutes=timeout_minutes,
                                    etagere_id=et.id if et else None,
                                    stock_id=None,
                                    depot_id=et.depot_id if et else None
                                )
                                s['alert_fired'] = True
                                websocket.app.state.camera_states[key] = s
                            except Exception as e:
                                print('Error creating box_missing alert:', e)
                            finally:
                                db.close()

                    # Detect decrease
                    if last > product_count:
                        missing = last - product_count
                        # If no watcher running, start one
                        if not state.get('timer_task'):
                            state['missing_count'] = missing
                            state['missing_since'] = datetime.utcnow()
                            state['timeout_minutes'] = state.get('timeout_minutes', 5)
                            task = asyncio.create_task(box_alert_watcher(cam_key, state.get('missing_count'), state['timeout_minutes']))
                            state['timer_task'] = task
                            state['alert_fired'] = False
                            websocket.app.state.camera_states[cam_key] = state
                        else:
                            # update missing count
                            state['missing_count'] = missing
                            websocket.app.state.camera_states[cam_key] = state
                    elif product_count >= last:
                        # Product(s) returned — cancel any pending timer
                        if state.get('timer_task'):
                            t = state.get('timer_task')
                            if not t.done():
                                t.cancel()
                            state['timer_task'] = None
                        state['missing_count'] = 0
                        state['missing_since'] = None
                        state['alert_fired'] = False
                        websocket.app.state.camera_states[cam_key] = state

                    # Update last_count
                    state['last_count'] = product_count
                    websocket.app.state.camera_states[cam_key] = state
            except Exception as e:
                print('Box tracking error:', e)

            # Send results back to client
            await websocket.send_json({
                "detections": detections,
                "count":      len(detections),
                "product_count": product_count,
                "has_person": has_person,
            })

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
