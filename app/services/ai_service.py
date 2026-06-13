import os
import json
import logging
import numpy as np
from PIL import Image
import torch

try:
    import faiss
except ImportError:
    faiss = None

try:
    import open_clip
except ImportError:
    open_clip = None

from ultralytics import YOLO

logger = logging.getLogger(__name__)

class AIService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AIService, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.yolo_model = None
        self.person_model = None
        self.clip_model = None
        self.clip_preprocess = None
        self.faiss_index = None
        self.faiss_meta = None
        
        # Paths
        self.yolo_model_path = "C:/Users/wajih/My_Boxes_Project.v2i.yolov8-obb (1)/runs/detect/train/weights/best.pt"
        self.person_model_path = "yolov8n.pt"
        self.index_dir = "C:/Users/wajih/my_boxes_project.v4i.yolov8-obb/catalog_index"
        
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Performance / caching
        # We only run CLIP on a box every few frames if it hasn't moved much?
        # For simplicity, we can start by running it on every detection, but maybe limit rate.
        
        self._initialized = True
        logger.info("AIService initialized (models not loaded yet)")

    def load_models(self):
        if self.yolo_model is None:
            logger.info("Loading YOLO models...")
            # If the trained model doesn't exist, fallback to general yolo11n or yolov8n
            if os.path.exists(self.yolo_model_path):
                self.yolo_model = YOLO(self.yolo_model_path)
            else:
                self.yolo_model = YOLO("yolov8n.pt")
                
            self.person_model = YOLO(self.person_model_path)

        if self.clip_model is None and open_clip is not None:
            logger.info("Loading OpenCLIP model ViT-B-32...")
            self.clip_model, _, self.clip_preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32', pretrained='openai'
            )
            self.clip_model.to(self.device)
            self.clip_model.eval()

        if self.faiss_index is None and faiss is not None:
            index_path = os.path.join(self.index_dir, 'catalog.index')
            meta_path = os.path.join(self.index_dir, 'catalog_meta.json')
            if os.path.exists(index_path) and os.path.exists(meta_path):
                logger.info("Loading FAISS index...")
                self.faiss_index = faiss.read_index(index_path)
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self.faiss_meta = json.load(f)
            else:
                logger.warning(f"FAISS index not found at {self.index_dir}")

    def recognize_crop(self, crop_pil: Image.Image, threshold=0.28, topk=1):
        if not self.clip_model or not self.faiss_index:
            return "Unknown", 0.0

        # preprocess
        img_t = self.clip_preprocess(crop_pil).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            emb = self.clip_model.encode_image(img_t)
            
        emb = emb.cpu().numpy().astype('float32')
        faiss.normalize_L2(emb)
        
        D, I = self.faiss_index.search(emb, topk)
        sim = float(D[0][0]) if D.shape[1] > 0 else 0.0
        best_i = int(I[0][0]) if I.shape[1] > 0 else -1
        
        if sim >= threshold and best_i >= 0 and best_i < len(self.faiss_meta):
            name = self.faiss_meta[best_i].get('name', 'Unknown')
        else:
            name = 'Unknown'
            
        return name, sim

    def predict_frame(self, cv2_img, run_clip=True):
        """
        Runs YOLO detection, checks for persons, and optionally runs CLIP recognition.
        Returns: {
            "detections": [...],
            "count": int,
            "has_person": bool,
            "product_count": int
        }
        """
        self.load_models()
        
        # Person detection
        person_results = self.person_model(cv2_img, verbose=False)
        has_person = False
        for r in person_results:
            if r.boxes is not None and len(r.boxes) > 0:
                cls = r.boxes.cls.cpu().numpy()
                if 0 in cls:  # COCO class 0 is person
                    has_person = True
                    break

        # Main detection
        results = self.yolo_model(cv2_img, conf=0.15, imgsz=640, verbose=False)
        detections = []
        
        # Convert cv2 image to PIL for CLIP cropping (RGB)
        pil_img = Image.fromarray(cv2_img[..., ::-1]) if run_clip and self.clip_model else None
        
        for r in results:
            if r.obb is not None and len(r.obb) > 0:
                boxes = r.obb.xyxyxyxy.cpu().numpy()
                confs = r.obb.conf.cpu().numpy()
                cls   = r.obb.cls.cpu().numpy()
                
                for i in range(len(boxes)):
                    # For OBB, we need a bounding box crop for CLIP.
                    # Simple approach: take min/max x and y of the 4 corners
                    x_coords = boxes[i][:, 0]
                    y_coords = boxes[i][:, 1]
                    x1, y1 = int(np.min(x_coords)), int(np.min(y_coords))
                    x2, y2 = int(np.max(x_coords)), int(np.max(y_coords))
                    
                    label = self.yolo_model.names[int(cls[i])]
                    recognized_name = label
                    sim = 1.0
                    
                    # Only recognize "products" or specific classes, wait, YOLO detects Khamra / salvage.
                    # If YOLO already detects them accurately, do we even need CLIP?
                    # Bypass CLIP if YOLO already recognizes specific labels correctly
                    if False and run_clip and pil_img and label == 'generic_box':
                        try:
                            # Clamp coordinates
                            x1, y1 = max(0, x1), max(0, y1)
                            x2, y2 = min(pil_img.width, x2), min(pil_img.height, y2)
                            
                            if x2 > x1 and y2 > y1:
                                crop = pil_img.crop((x1, y1, x2, y2))
                                recognized_name, sim = self.recognize_crop(crop)
                        except Exception as e:
                            logger.error(f"Error in CLIP recognition: {e}")
                    
                    detections.append({
                        "corners": boxes[i].tolist(),
                        "confidence": float(confs[i]),
                        "class": int(cls[i]),
                        "label": recognized_name,
                        "clip_similarity": sim
                    })
                    
            elif r.boxes is not None and len(r.boxes) > 0:
                boxes = r.boxes.xyxy.cpu().numpy()
                confs = r.boxes.conf.cpu().numpy()
                cls   = r.boxes.cls.cpu().numpy()
                
                for i in range(len(boxes)):
                    x1, y1, x2, y2 = map(int, boxes[i])
                    label = self.yolo_model.names[int(cls[i])]
                    recognized_name = label
                    sim = 1.0
                    
                    if run_clip and pil_img and label == 'generic_box':
                        try:
                            # Clamp coordinates
                            x1, y1 = max(0, x1), max(0, y1)
                            x2, y2 = min(pil_img.width, x2), min(pil_img.height, y2)
                            
                            if x2 > x1 and y2 > y1:
                                crop = pil_img.crop((x1, y1, x2, y2))
                                recognized_name, sim = self.recognize_crop(crop)
                        except Exception as e:
                            logger.error(f"Error in CLIP recognition: {e}")
                    
                    detections.append({
                        "bbox": boxes[i].tolist(),
                        "confidence": float(confs[i]),
                        "class": int(cls[i]),
                        "label": recognized_name,
                        "clip_similarity": sim
                    })

        product_count = len(detections) # In this scenario, all detections are considered products

        return {
            "detections": detections,
            "count": len(detections),
            "product_count": product_count,
            "has_person": has_person
        }
