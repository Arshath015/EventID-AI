import cv2
import numpy as np
import streamlit as st
from config import MODEL_NAME

try:
    from deepface import DeepFace
except Exception:
    DeepFace = None


class BiometricEngine:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        if self.face_cascade.empty():
            self.face_cascade = None

        if DeepFace is not None:
            try:
                DeepFace.represent(img_path=np.zeros((112, 112, 3), dtype=np.uint8), model_name=MODEL_NAME, enforce_detection=False)
            except Exception:
                pass

    def l2_normalize(self, x):
        norm = np.linalg.norm(x)
        return x / norm if norm > 0 else x

    def _simple_face_embedding(self, image_bgr):
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        if self.face_cascade is None:
            return None, None

        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        if len(faces) == 0:
            return None, None

        x, y, w, h = max(faces, key=lambda item: item[2] * item[3])
        face_region = image_bgr[y:y + h, x:x + w]
        if face_region.size == 0:
            return None, None

        aligned_img = cv2.resize(face_region, (112, 112))
        hsv = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten().astype(np.float32)
        return self.l2_normalize(hist), {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}

    def extract_and_embed(self, image_bgr, enforce_detection=True):
        if image_bgr is None:
            return None, None

        if DeepFace is not None:
            try:
                faces = DeepFace.extract_faces(img_path=image_bgr, detector_backend='opencv', enforce_detection=enforce_detection, align=True)
                if not faces:
                    return None, None

                target_face = max(faces, key=lambda item: item['facial_area']['w'] * item['facial_area']['h'])
                if target_face['confidence'] < 0.5:
                    return None, None

                face_img = (target_face['face'] * 255).astype(np.uint8)
                if face_img.shape[-1] == 3:
                    face_img = cv2.cvtColor(face_img, cv2.COLOR_RGB2BGR)
                aligned_img = cv2.resize(face_img, (112, 112))

                embeddings = DeepFace.represent(img_path=aligned_img, model_name=MODEL_NAME, enforce_detection=False, detector_backend='skip', align=False)
                if not embeddings:
                    return None, None

                raw_vec = np.array(embeddings[0]['embedding'])
                norm_vec = self.l2_normalize(raw_vec)
                return norm_vec, target_face['facial_area']
            except Exception:
                pass

        return self._simple_face_embedding(image_bgr)


@st.cache_resource
def get_biometric_engine():
    """Caches the heavy AI model loading so the UI never lags."""
    return BiometricEngine()


bio_engine = get_biometric_engine()
