import cv2
# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
# pyrefly: ignore [missing-import]
from ultralytics import YOLO

router = APIRouter(prefix="/detection", tags=["detection"])

MODEL_PATH = (
    "C:/Users/wajih/Empty spaces in a supermarket hanger.v29i.yolov8-obb"
    "/runs/detect/train/weights/best.pt"
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
