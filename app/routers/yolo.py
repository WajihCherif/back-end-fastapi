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
# pyrefly: ignore [missing-import]
from ultralytics import YOLO
import time
import json
import os

YOLO_MODEL_PATH = r"c:\Users\wajih\My_Boxes_Project.v2i.yolov8-obb\runs\obb\train\weights\best.pt"
yolo_model = YOLO(YOLO_MODEL_PATH) if os.path.exists(YOLO_MODEL_PATH) else YOLO("yolov8n.pt")
person_model = YOLO("yolov8n.pt")

router = APIRouter(
    prefix="/yolo",
    tags=["yolo"]
)




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

            # Run inference directly with YOLO
            person_results = person_model(img, verbose=False)
            has_person = False
            for r in person_results:
                if r.boxes is not None and len(r.boxes) > 0:
                    cls = r.boxes.cls.cpu().numpy()
                    if 0 in cls:  # COCO class 0 is person
                        has_person = True
                        break

            results = yolo_model(img, conf=0.15, imgsz=640, verbose=False)
            detections = []
            
            for r in results:
                if r.obb is not None and len(r.obb) > 0:
                    boxes = r.obb.xyxyxyxy.cpu().numpy()
                    confs = r.obb.conf.cpu().numpy()
                    cls   = r.obb.cls.cpu().numpy()
                    
                    for i in range(len(boxes)):
                        label = yolo_model.names[int(cls[i])]
                        detections.append({
                            "corners": boxes[i].tolist(),
                            "confidence": float(confs[i]),
                            "class": int(cls[i]),
                            "label": label,
                        })
                        
                elif r.boxes is not None and len(r.boxes) > 0:
                    boxes = r.boxes.xyxy.cpu().numpy()
                    confs = r.boxes.conf.cpu().numpy()
                    cls   = r.boxes.cls.cpu().numpy()
                    
                    for i in range(len(boxes)):
                        label = yolo_model.names[int(cls[i])]
                        detections.append({
                            "bbox": boxes[i].tolist(),
                            "confidence": float(confs[i]),
                            "class": int(cls[i]),
                            "label": label,
                        })

            product_count = len(detections)

            # Server-side box-missing tracking (backup — main logic handled by frontend)
            try:
                if cam_key:
                    state = camera_states.get(cam_key, {
                        'last_count': product_count,
                        'timer_task': None,
                        'missing_count': 0,
                        'missing_since': None,
                        'timeout_minutes': 5,
                        'alert_fired': False,
                        'initialized': False,
                    })

                    # Skip comparison until we have at least one baseline reading
                    if not state.get('initialized'):
                        state['last_count'] = product_count
                        state['initialized'] = True
                        camera_states[cam_key] = state
                    else:
                        last = state.get('last_count', product_count)

                        async def box_alert_watcher(key, missing_count, timeout_minutes):
                            await asyncio.sleep(timeout_minutes * 60)
                            s = websocket.app.state.camera_states.get(key)
                            if not s or s.get('alert_fired'):
                                return
                            current_count = s.get('last_count', 0)
                            still_missing = s.get('missing_count', 0)
                            # Fire alert only if boxes are still missing
                            if still_missing > 0 and current_count < (current_count + still_missing):
                                db = SessionLocal()
                                try:
                                    et = db.query(Etagere).filter(Etagere.etagere_code == key).first()
                                    product_id = et.product_id if et else None
                                    product_name = et.product.name if (et and et.product) else (et.name if et else 'Unknown')
                                    expected_quantity = et.quantity_etagere if et else (current_count + still_missing)
                                    message = (
                                        f"{still_missing} boîte(s) de \"{product_name}\" manquante(s) "
                                        f"depuis l'étagère {et.name if et else key} ({key}) "
                                        f"depuis {timeout_minutes} minute(s)."
                                    )
                                    alert_service.create_alert(
                                        db=db,
                                        product_id=product_id or 0,
                                        product_name=product_name or 'Unknown',
                                        alert_type='box_missing',
                                        expected_quantity=expected_quantity,
                                        actual_quantity=current_count,
                                        message=message,
                                        quantity_etagere=current_count,
                                        boxes_missing_count=still_missing,
                                        state_change_time=s.get('missing_since'),
                                        timeout_minutes=timeout_minutes,
                                        etagere_id=et.id if et else None,
                                        etagere_code=et.etagere_code if et else key,
                                        stock_id=None,
                                        depot_id=et.depot_id if et else None
                                    )
                                    print(f"[ALERT CREATED] box_missing for cam_key={key}, missing={still_missing}")
                                    s['alert_fired'] = True
                                    websocket.app.state.camera_states[key] = s
                                except Exception as e:
                                    print(f'Error creating box_missing alert: {e}')
                                finally:
                                    db.close()

                        if last > product_count:
                            missing = last - product_count
                            if not state.get('timer_task'):
                                state['missing_count'] = missing
                                state['missing_since'] = datetime.utcnow()
                                task = asyncio.create_task(
                                    box_alert_watcher(cam_key, missing, state.get('timeout_minutes', 5))
                                )
                                state['timer_task'] = task
                                state['alert_fired'] = False
                                print(f"[TRACKING] cam={cam_key}, {last} -> {product_count}, {missing} missing, timer started")
                            else:
                                state['missing_count'] = missing
                        elif product_count >= last and last > 0:
                            if state.get('timer_task'):
                                t = state['timer_task']
                                if not t.done():
                                    t.cancel()
                                state['timer_task'] = None
                                print(f"[TRACKING] cam={cam_key}, product returned ({last} -> {product_count}), timer cancelled")
                            state['missing_count'] = 0
                            state['missing_since'] = None
                            state['alert_fired'] = False

                        state['last_count'] = product_count
                        camera_states[cam_key] = state
            except Exception as e:
                print(f'Box tracking error: {e}')

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
