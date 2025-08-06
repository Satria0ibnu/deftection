from config import SUPPORTED_FORMATS
from .utils import get_image_format

def detect_appended_data(path):
    try:
        with open(path, 'rb') as f:
            content = f.read()

        img_format = get_image_format(path)

        if img_format == "JPEG":
            eof = b'\xff\xd9'
        elif img_format == "PNG":
            eof = b'\x00\x00\x00\x00IEND\xaeB`\x82'
        elif img_format == "GIF":
            eof = b'\x3b'
        else:
            eof = None

        if eof and eof in content:
            eof_index = content.rfind(eof)
            return eof_index < len(content) - len(eof)
        return False
    except:
        return False