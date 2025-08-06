import asyncio
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from inspector.core import scan_image_file
from inspector.utils import get_mime_type, validate_extension, get_image_format
from config import SUPPORTED_FORMATS

UPLOAD_FOLDER = 'uploads'
executor = ThreadPoolExecutor()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/scan', methods=['POST'])
def scan():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'No file provided'}), 400

    filename = secure_filename(file.filename)
    filepath = f'{UPLOAD_FOLDER}/{filename}'
    file.save(filepath)

    if not validate_extension(filepath):
        return jsonify({'error': 'Unsupported file extension'}), 400

    mime = get_mime_type(filepath)
    if not mime.startswith("image/"):
        return jsonify({'error': f'Invalid MIME type: {mime}'}), 400

    img_format = get_image_format(filepath)
    if img_format not in SUPPORTED_FORMATS:
        return jsonify({'error': f'Unsupported image format: {img_format}'}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(scan_image_file(filepath, executor))
    loop.close()

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)