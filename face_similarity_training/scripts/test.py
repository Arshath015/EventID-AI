import os
import logging

# [1] SUPPRESS WARNINGS (Protobuf/Tensorflow Noise)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings
warnings.filterwarnings('ignore')
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import cv2
import numpy as np
import threading
import time
from deepface import DeepFace

# =============================================================================
# [CONFIG] SYSTEM PARAMETERS
# =============================================================================
WINDOW_NAME = "Face Similarity Training - Sentinel OS"
REF_DIR = "data"
# UPDATED: Matches your uploaded file extension
REFERENCE_FILE = os.path.join(REF_DIR, "me.jpg") 
MODEL_NAME = "ArcFace"

# Thresholds
VERIFICATION_THRESHOLD = 0.50 

# COLORS
C_CYAN   = (255, 255, 0)
C_RED    = (0, 0, 255)
C_GREEN  = (0, 255, 0)
C_WHITE  = (255, 255, 255)
C_YELLOW = (0, 215, 255)
C_DARK   = (20, 20, 20)
C_GREY   = (80, 80, 80)

# FONTS
F_HEADER = cv2.FONT_HERSHEY_SIMPLEX
F_DATA   = cv2.FONT_HERSHEY_PLAIN

# =============================================================================
# [CORE] BIOMETRIC PIPELINE
# =============================================================================
class BioPipeline:
    def __init__(self):
        self.ref_embedding = None
        self.ref_crop = None 
        
        if not os.path.exists(REF_DIR):
            os.makedirs(REF_DIR)

        print("[INIT] Loading ArcFace Tensor Core...")
        try:
            # Warmup
            DeepFace.represent(img_path=np.zeros((112,112,3), dtype=np.uint8), 
                               model_name=MODEL_NAME, enforce_detection=False)
        except:
            pass 

    def _l2_normalize(self, x):
        norm = np.linalg.norm(x)
        if norm == 0: return x
        return x / norm

    def get_embedding(self, image_bgr, backend='opencv'):
        """
        Extracts embedding. Allows changing backend for Reference vs Live.
        """
        try:
            # Handle PNG Transparency
            if image_bgr.shape[-1] == 4:
                image_bgr = cv2.cvtColor(image_bgr, cv2.COLOR_BGRA2BGR)

            # 1. DETECT
            # We use the specific backend passed to the function
            faces = DeepFace.extract_faces(
                img_path=image_bgr, 
                detector_backend=backend, 
                enforce_detection=True,
                align=True
            )
            
            if not faces: return None, None, None
            
            # Select largest face
            target_face = max(faces, key=lambda x: x['facial_area']['w'] * x['facial_area']['h'])

            # 2. ALIGN & RESIZE (Strict 112x112)
            face_img = (target_face['face'] * 255).astype(np.uint8)
            if face_img.shape[-1] == 3:
                face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
            
            aligned_img = cv2.resize(face_img, (112, 112))
            
            # 3. EMBED
            embeddings = DeepFace.represent(
                img_path=aligned_img,
                model_name=MODEL_NAME,
                enforce_detection=False,
                detector_backend='skip',
                align=False
            )
            
            if not embeddings: return None, None, None
            
            # 4. NORMALIZE
            raw_vec = np.array(embeddings[0]['embedding'])
            norm_vec = self._l2_normalize(raw_vec)
            
            return norm_vec, aligned_img, target_face['facial_area']

        except Exception as e:
            # print(f"DEBUG: {e}") 
            return None, None, None

    def load_reference(self):
        # Handle file extension mismatches (jpg vs png)
        target_file = REFERENCE_FILE
        if not os.path.exists(target_file):
            # Try alternative extension
            alt = target_file.replace(".jpg", ".png")
            if os.path.exists(alt): target_file = alt
        
        if os.path.exists(target_file):
            print(f"[CORE] Reading Reference: {target_file}")
            img = cv2.imread(target_file, cv2.IMREAD_UNCHANGED)
            if img is None: return "FILE_ERROR"
            
            # CRITICAL FIX: Use 'ssd' backend for Reference Image
            # 'opencv' fails on side profiles. 'ssd' is robust and included in cv2.
            print("[CORE] Analysing Reference Face (High Precision)...")
            vec, crop, _ = self.get_embedding(img, backend='ssd')
            
            # Fallback if SSD fails
            if vec is None:
                print("[CORE] Retrying with alternative detector...")
                vec, crop, _ = self.get_embedding(img, backend='mtcnn')

            if vec is not None:
                self.ref_embedding = vec
                self.ref_crop = crop
                print(f"[CORE] Reference Locked.")
                return "SUCCESS"
            else:
                print("[CORE] No face detected. Try a front-facing image.")
                return "NO_FACE"
        return "NOT_FOUND"

# =============================================================================
# [UI] GRAPHICS ENGINE
# =============================================================================
class SentinelUI:
    def __init__(self):
        self.frame_idx = 0
        self.log_buffer = []
        self._log("SENTINEL OS v7.3 ONLINE")
        self.vignette_mask = None 
    
    def _log(self, msg):
        self.log_buffer.append(f">> {msg}")
        if len(self.log_buffer) > 6: self.log_buffer.pop(0)

    def draw_tech_box(self, frame, x, y, w, h, color, title=""):
        sub = frame[y:y+h, x:x+w]
        if sub.size > 0:
            white_rect = np.full(sub.shape, 20, dtype=np.uint8)
            res = cv2.addWeighted(sub, 0.6, white_rect, 0.4, 1.0)
            frame[y:y+h, x:x+w] = res
        
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 1)
        l = 15
        cv2.line(frame, (x, y), (x+l, y), color, 2)
        cv2.line(frame, (x+w, y), (x+w-l, y), color, 2)
        cv2.line(frame, (x, y+h), (x+l, y+h), color, 2)
        cv2.line(frame, (x+w, y+h), (x+w-l, y+h), color, 2)
        
        if title:
            cv2.putText(frame, title, (x+10, y-8), F_HEADER, 0.5, color, 1, cv2.LINE_AA)

    def draw_clean_mesh(self, frame, box, color):
        x, y, w, h = box['x'], box['y'], box['w'], box['h']
        cx, cy = x + w//2, y + h//2
        
        # 1. Heavy Corners
        l = int(w * 0.20) 
        t = 2
        cv2.line(frame, (x, y), (x+l, y), color, t)
        cv2.line(frame, (x, y), (x, y+l), color, t)
        cv2.line(frame, (x+w, y), (x+w-l, y), color, t)
        cv2.line(frame, (x+w, y), (x+w, y+l), color, t)
        cv2.line(frame, (x, y+h), (x+l, y+h), color, t)
        cv2.line(frame, (x, y+h), (x, y+h-l), color, t)
        cv2.line(frame, (x+w, y+h), (x+w-l, y+h), color, t)
        cv2.line(frame, (x+w, y+h), (x+w, y+h-l), color, t)

        # 2. Central Radar
        radius = int(w * 0.35)
        cv2.circle(frame, (cx, cy), radius, color, 1, cv2.LINE_AA)
        
        # Rotating Scanner
        angle_rad = np.radians((self.frame_idx * 5) % 360)
        end_x = int(cx + radius * np.cos(angle_rad))
        end_y = int(cy + radius * np.sin(angle_rad))
        cv2.line(frame, (cx, cy), (end_x, end_y), color, 1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 3, color, -1)

        # 3. Crosshair Grid
        grid_cols = 3
        grid_rows = 3
        step_x = w // (grid_cols + 1)
        step_y = h // (grid_rows + 1)
        for i in range(1, grid_cols + 1):
            for j in range(1, grid_rows + 1):
                px = x + (i * step_x)
                py = y + (j * step_y)
                if np.sqrt((px-cx)**2 + (py-cy)**2) < radius * 0.9:
                    cv2.line(frame, (px-3, py), (px+3, py), color, 1)
                    cv2.line(frame, (px, py-3), (px, py+3), color, 1)

    def render(self, frame, state, stats, ref_crop=None, ref_status=""):
        self.frame_idx += 1
        h, w = frame.shape[:2]
        
        # Vignette
        if self.vignette_mask is None or self.vignette_mask.shape[:2] != (h, w):
            Y, X = np.ogrid[:h, :w]
            center = (w/2, h/2)
            mask = 1 - (np.sqrt((X - center[0])**2 + (Y - center[1])**2) / (np.sqrt(w**2 + h**2)/1.5))
            self.vignette_mask = np.clip(mask, 0.4, 1.0)[..., np.newaxis]
        np.multiply(frame, self.vignette_mask, out=frame, casting="unsafe")

        # Header
        cv2.rectangle(frame, (0, 0), (w, 40), C_DARK, -1)
        cv2.line(frame, (0, 40), (w, 40), C_CYAN, 1)
        cv2.putText(frame, WINDOW_NAME, (20, 28), F_HEADER, 0.7, C_CYAN, 2, cv2.LINE_AA)
        
        # Logs
        self.draw_tech_box(frame, 20, 60, 280, 150, C_CYAN, "SYSTEM KERNEL")
        for i, log in enumerate(self.log_buffer):
            cv2.putText(frame, log, (25, 85 + i*20), F_DATA, 0.8, C_GREEN, 1)

        # Bottom Left: Reference Display
        panel_y = h - 200
        self.draw_tech_box(frame, 20, panel_y, 160, 180, C_YELLOW, "TARGET REF")
        
        if state == "ACTIVE" and ref_crop is not None:
            disp_ref = cv2.resize(ref_crop, (140, 140))
            frame[panel_y+25:panel_y+165, 30:170] = disp_ref
            cv2.putText(frame, "ID: LOCKED", (30, panel_y+175), F_DATA, 0.9, C_YELLOW, 1)
        else:
            err_msg = "NO DATA"
            color = C_RED
            if ref_status == "NO_FACE": err_msg = "REF FACE INVALID"
            elif ref_status == "NOT_FOUND": err_msg = "FILE NOT FOUND"
            
            cv2.putText(frame, err_msg, (30, panel_y+90), F_DATA, 0.9, color, 1)
            if state == "WAIT_REF":
                 cv2.putText(frame, "[SPACE] CAPTURE", (30, panel_y+110), F_DATA, 0.9, C_WHITE, 1)

        # Active UI
        if state == "ACTIVE" and stats:
            score = stats['score']
            is_match = stats['is_match']
            box = stats['box']
            aligned_face = stats['aligned']
            color = C_GREEN if is_match else C_RED

            self.draw_clean_mesh(frame, box, color)
            
            # Neural Input
            if aligned_face is not None:
                preview_size = 140
                rx, ry = w - preview_size - 40, h - preview_size - 40
                self.draw_tech_box(frame, rx-10, ry-30, preview_size+20, preview_size+40, C_CYAN, "NEURAL INPUT")
                frame[ry:ry+preview_size, rx:rx+preview_size] = cv2.resize(aligned_face, (preview_size, preview_size))

            # Score
            px, py = w - 300, 60
            self.draw_tech_box(frame, px, py, 280, 200, color, "LIVE METRICS")
            cv2.putText(frame, "ACCESS GRANTED" if is_match else "ACCESS DENIED", (px+10, py+50), F_HEADER, 0.8, color, 2)
            cv2.putText(frame, f"SCORE: {score:.4f}", (px+10, py+100), F_HEADER, 1.2, C_WHITE, 2)
            
            # Bar
            bar_w = 250
            cv2.rectangle(frame, (px+10, py+130), (px+10+bar_w, py+145), C_GREY, -1)
            fill_w = int(min(score, 1.0) * bar_w)
            cv2.rectangle(frame, (px+10, py+130), (px+10+fill_w, py+145), color, -1)
            tx = px+10 + int(VERIFICATION_THRESHOLD * bar_w)
            cv2.line(frame, (tx, py+125), (tx, py+150), C_YELLOW, 2)
            
            # Connector
            cx, cy = box['x']+box['w'], box['y']+20
            cv2.line(frame, (cx, cy), (px, py+20), color, 1)

        elif state == "WAIT_REF":
             cv2.putText(frame, "INITIALIZATION REQUIRED", (w//2-150, h//2), F_HEADER, 0.8, C_RED, 2)

# =============================================================================
# [MAIN] CONTROLLER
# =============================================================================
class App:
    def __init__(self):
        self.pipeline = BioPipeline()
        self.ui = SentinelUI()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        self.lock = threading.Lock()
        self.running = True
        self.latest_frame = None
        self.current_stats = None
        
        # Load Reference
        self.ref_status = self.pipeline.load_reference()
        if self.ref_status == "SUCCESS":
            self.state = "ACTIVE"
        else:
            self.state = "WAIT_REF"
            self.ui._log(f"REF ERROR: {self.ref_status}")

        self.thread = threading.Thread(target=self.processing_loop)
        self.thread.daemon = True
        self.thread.start()

    def processing_loop(self):
        while self.running:
            if self.state != "ACTIVE": 
                time.sleep(0.1)
                continue
            
            with self.lock:
                if self.latest_frame is None: continue
                frame_process = self.latest_frame.copy()

            # Process Live (Uses OpenCV for speed)
            live_vec, aligned_img, face_area = self.pipeline.get_embedding(frame_process, backend='opencv')
            
            stats = None
            if live_vec is not None and self.pipeline.ref_embedding is not None:
                score = np.dot(self.pipeline.ref_embedding, live_vec)
                stats = {
                    'score': score,
                    'is_match': score > VERIFICATION_THRESHOLD,
                    'box': face_area,
                    'aligned': aligned_img
                }
                self.ui._log(f"ID_CHECK: {score:.3f}")
            
            self.current_stats = stats
            time.sleep(0.03)

    def run(self):
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            
            with self.lock:
                self.latest_frame = frame
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                self.running = False
                break
            
            # Manual Capture (Only if needed)
            if self.state == "WAIT_REF" and key == 32:
                self.ui._log("CAPTURING NEW REFERENCE...")
                cv2.imwrite(REFERENCE_FILE, frame)
                self.ref_status = self.pipeline.load_reference()
                if self.ref_status == "SUCCESS":
                    self.ui._log("REFERENCE LOCKED.")
                    self.state = "ACTIVE"
                else:
                    self.ui._log(f"CAPTURE FAILED: {self.ref_status}")

            self.ui.render(frame, self.state, self.current_stats, self.pipeline.ref_crop, self.ref_status)
            cv2.imshow(WINDOW_NAME, frame)
            
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = App()
    app.run()