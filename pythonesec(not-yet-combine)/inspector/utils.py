import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode
import cv2
import magic
import os

def load_malware_hashes(path):
    try:
        with open(path, 'r') as f:
            return set(line.strip().lower() for line in f if line.strip())
    except:
        return set()

def check_exif(path):
    try:
        img = Image.open(path)
        exif = img._getexif()
        if exif:
            for value in exif.values():
                if isinstance(value, str) and 'script' in value.lower():
                    return True
        return False
    except:
        return False

def pixel_anomaly(path):
    try:
        img = Image.open(path).convert('L')
        arr = np.array(img)
        return np.std(arr) < 5
    except:
        return False

def decode_qr(path):
    try:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        decoded = decode(img)
        if not decoded:
            return {'valid': False, 'content': None}
        return {'valid': True, 'content': decoded[0].data.decode('utf-8')}
    except:
        return {'valid': False, 'content': None}

def check_file_signature(path):
    try:
        with open(path, 'rb') as f:
            sig = f.read(12)
        if sig.startswith(b'\xff\xd8'): return True        # JPEG
        if sig.startswith(b'\x89PNG\r\n\x1a\n'): return True # PNG
        if sig[:2] == b'BM': return True                   # BMP
        if sig.startswith(b'GIF87a') or sig.startswith(b'GIF89a'): return True # GIF
        if sig.startswith(b'RIFF') and b'WEBP' in sig: return True # WEBP
        return False
    except:
        return False

def get_image_format(path):
    try:
        img = Image.open(path)
        return img.format.upper()
    except:
        return "UNKNOWN"

def get_mime_type(path):
    try:
        mime = magic.Magic(mime=True)
        return mime.from_file(path)
    except:
        return "unknown/unknown"

def validate_extension(path):
    ext = os.path.splitext(path)[1].lower()
    allowed_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
    return ext in allowed_exts

def suspicious_domain_match(url):
    suspect_terms = ["login", "verify", "support", ".ru", ".xyz", ".top"]
    return any(term in url.lower() for term in suspect_terms)