import io
import cv2
import qrcode


def generate_qr(data: str) -> io.BytesIO:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf


def decode_qr(frame_bgr):
    detector = cv2.QRCodeDetector()

    def safe_decode(img):
        try:
            data, points, _ = detector.detectAndDecode(img)
            if points is not None and data:
                return data
        except Exception:
            return None
        return None

    data = safe_decode(frame_bgr)
    if data:
        return data

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    data = safe_decode(gray)
    if data:
        return data

    enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
    data = safe_decode(enhanced)
    if data:
        return data

    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    return safe_decode(thresh)
