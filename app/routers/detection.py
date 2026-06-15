import cv2
# pyrefly: ignore [missing-import]
import asyncio
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi import BackgroundTasks
from fastapi import Request
from fastapi.responses import StreamingResponse
# pyrefly: ignore [missing-import]
from ultralytics import YOLO

router = APIRouter(prefix="/detection", tags=["detection"])

MODEL_PATH = (
    r"c:\Users\wajih\My_Boxes_Project.v2i.yolov8-obb\runs\obb\train\weights\best.pt"
)
model = YOLO(MODEL_PATH)


def generate_frames():
    """Generator that captures webcam frames, runs YOLO inference, and yields MJPEG chunks."""
    cap = cv2.VideoCapture(0)
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            # Run inference with confidence threshold
            results = model.predict(source=frame, conf=0.5, verbose=False)
            annotated = results[0].plot()

            _, buffer = cv2.imencode(".jpg", annotated)
            frame_bytes = buffer.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame_bytes
                + b"\r\n"
            )
    finally:
        cap.release()


@router.get("/stream", summary="Live MJPEG stream with YOLO detections")
def video_stream():
    """
    Returns a multipart MJPEG stream.
    Embed directly in HTML:
        <img src="http://localhost:8000/detection/stream" />
    """
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/status", summary="Detection service status")
def detection_status():
    """Returns the current status and model path being used."""
    return {
        "status": "running",
        "model": MODEL_PATH,
        "stream_url": "/detection/stream",
    }


# New: presence endpoint and background processor
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.removal_watch_service import RemovalWatchService
import os
import json
from fastapi import UploadFile, File
from typing import List

# Optional mapping file: class label -> product_id
MAPPING_PATH = os.path.join(os.path.dirname(__file__), '..', 'detection_mapping.json')
try:
    with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
        DETECTION_MAPPING = json.load(f)
except Exception:
    DETECTION_MAPPING = {}


class PresencePayload(BaseModel):
    etagere_code: str
    product_id: int
    count: int = 1


@router.post("/presence")
def report_presence(payload: PresencePayload, db: Session = Depends(get_db)):
    service = RemovalWatchService(timeout_minutes=2)
    try:
        service.upsert_presence(db, payload.etagere_code, payload.product_id, payload.count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "presence recorded"}


@router.post('/infer')
def infer_image(file: UploadFile = File(...)):
    """Run model inference on an uploaded image and return detected labels and boxes.

    The response includes any mapped `product_id` when `detection_mapping.json` is provided.
    """
    try:
        contents = file.file.read()
        # Run inference on bytes via model.predict (ultralytics accepts numpy arrays/files; for simplicity, pass bytes path)
        # Save to a temp file
        import tempfile
        import numpy as np
        import cv2

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.' + file.filename.split('.')[-1])
        tmp.write(contents)
        tmp.flush()
        tmp.close()

        results = model.predict(source=tmp.name, conf=0.4, verbose=False)
        detections = []
        for r in results:
            if r.obb is not None:
                for b in r.obb:
                    cls = int(b.cls.cpu().numpy()) if hasattr(b, 'cls') else None
                    label = results[0].names[cls] if cls is not None and cls in results[0].names else str(cls)
                    conf = float(b.conf.cpu().numpy()) if hasattr(b, 'conf') else None
                    bbox = b.xyxyxyxy.cpu().numpy().tolist() if hasattr(b, 'xyxyxyxy') else None
                    product_id = DETECTION_MAPPING.get(label)
                    detections.append({
                        'label': label,
                        'confidence': conf,
                        'bbox': bbox,
                        'product_id': product_id
                    })
            else:
                boxes = r.boxes
                for b in boxes:
                    cls = int(b.cls.cpu().numpy()) if hasattr(b, 'cls') else None
                    label = results[0].names[cls] if cls is not None and cls in results[0].names else str(cls)
                    conf = float(b.conf.cpu().numpy()) if hasattr(b, 'conf') else None
                    bbox = b.xyxy.cpu().numpy().tolist() if hasattr(b, 'xyxy') else None
                    product_id = DETECTION_MAPPING.get(label)
                    detections.append({
                        'label': label,
                        'confidence': conf,
                        'bbox': bbox,
                        'product_id': product_id
                    })

        try:
            os.unlink(tmp.name)
        except Exception:
            pass

        return {'detections': detections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class InferReportItem(BaseModel):
    etagere_code: str
    label: str | None = None
    product_id: int | None = None
    count: int = 1


@router.post('/infer_and_report')
def infer_and_report(items: List[InferReportItem], db: Session = Depends(get_db)):
    """Accepts inferred items (labels or product_ids) and reports presence using mapping when needed."""
    service = RemovalWatchService(timeout_minutes=2)
    results = []
    for it in items:
        pid = it.product_id
        if pid is None and it.label:
            pid = DETECTION_MAPPING.get(it.label)
        if pid is None:
            results.append({'etagere_code': it.etagere_code, 'status': 'skipped', 'reason': 'no mapping'})
            continue
        try:
            service.upsert_presence(db, it.etagere_code, pid, it.count)
            results.append({'etagere_code': it.etagere_code, 'product_id': pid, 'status': 'ok'})
        except Exception as e:
            results.append({'etagere_code': it.etagere_code, 'product_id': pid, 'status': 'error', 'error': str(e)})

    return {'results': results}


# Background task runner (started from main startup event)
async def removal_watch_runner(app):
    """Background runner that periodically processes expired removal watches.

    This runner is resilient: it logs errors and continues running.
    """
    service = RemovalWatchService(timeout_minutes=2)
    import logging
    logger = logging.getLogger("removal_watch_runner")
    logger.info("Removal watch runner started")
    while True:
        try:
            from app.db import SessionLocal
            db = SessionLocal()
            service.process_expired_watches(db)
        except Exception as e:
            logger.exception(f"Error while processing removal watches: {e}")
        finally:
            try:
                db.close()
            except Exception:
                pass

        await asyncio.sleep(30)

