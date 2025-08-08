# app.py
"""
Main Flask Application Entry Point
Image Security Scanner with Controller/Service Architecture
"""

import os
import sys
from flask import Flask
from flask_cors import CORS

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import controller
from controllers.image_security_controller import ImageSecurityController

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Enable CORS for API access
    CORS(app, origins=['*'])
    
    return app

# Create Flask app
app = create_app()

# Initialize controller
controller = ImageSecurityController()

# Register routes
@app.route('/scan', methods=['POST'])
def scan_image():
    """Main scanning endpoint"""
    from flask import request, jsonify
    response, status_code = controller.scan_image(request)
    return jsonify(response), status_code

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    from flask import jsonify
    response, status_code = controller.health_check()
    return jsonify(response), status_code

@app.route('/stats', methods=['GET'])
def get_scanner_stats():
    """Scanner statistics endpoint"""
    from flask import jsonify
    response, status_code = controller.get_scanner_stats()
    return jsonify(response), status_code

@app.route('/', methods=['GET'])
def index():
    """API information endpoint"""
    from flask import jsonify
    from datetime import datetime
    
    return jsonify({
        'service': 'Image Security Scanner API',
        'version': '1.0.0',
        'status': 'operational',
        'endpoints': {
            'POST /scan': 'Image security scanning (supports is_full_scan parameter)',
            'GET /health': 'Health check and service status',
            'GET /stats': 'Scanner statistics and capabilities',
            'GET /': 'API information (this endpoint)'
        },
        'scan_types': {
            'light': 'Fast scan for critical threats only (< 0.5s)',
            'full': 'Comprehensive security analysis (1-3s)'
        },
        'supported_formats': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.psd'],
        'max_file_size': '50MB',
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large error"""
    from flask import jsonify
    from datetime import datetime
    
    return jsonify({
        'status': 'error',
        'message': 'File too large. Maximum size: 50MB',
        'error_code': 413,
        'timestamp': datetime.now().isoformat()
    }), 413

@app.errorhandler(400)
def bad_request(error):
    """Handle bad request error"""
    from flask import jsonify
    from datetime import datetime
    
    return jsonify({
        'status': 'error',
        'message': 'Bad request. Check request format and parameters.',
        'error_code': 400,
        'timestamp': datetime.now().isoformat()
    }), 400

@app.errorhandler(404)
def not_found(error):
    """Handle not found error"""
    from flask import jsonify
    from datetime import datetime
    
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found. Available endpoints: /scan, /health, /stats',
        'error_code': 404,
        'available_endpoints': ['/scan', '/health', '/stats', '/'],
        'timestamp': datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    from flask import jsonify
    from datetime import datetime
    
    return jsonify({
        'status': 'error',
        'message': 'Internal server error occurred.',
        'error_code': 500,
        'timestamp': datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    print("  Starting Image Security Scanner API")
    print("=" * 60)
    print("   Configuration:")
    print(f"   • Max file size: {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB")
    print(f"   • Supported formats: JPG, PNG, GIF, BMP, TIFF, WebP, ICO, PSD")
    print(f"   • Scan types: Light (fast) & Full (comprehensive)")
    print("")
    print("   Available endpoints:")
    print("   • POST /scan      - Image security scanning")
    print("   • GET  /health    - Health check and status")
    print("   • GET  /stats     - Scanner statistics")
    print("   • GET  /          - API information")
    print("")
    print("   Example usage:")
    print("   Light scan:")
    print("   curl -X POST -F 'file=@image.jpg' -F 'is_full_scan=false' http://localhost:5000/scan")
    print("")
    print("   Full scan:")
    print("   curl -X POST -F 'file=@image.jpg' -F 'is_full_scan=true' http://localhost:5000/scan")
    print("")
    print("   JSON upload:")
    print("   curl -X POST -H 'Content-Type: application/json' \\")
    print("        -d '{\"image_base64\":\"data:image/jpeg;base64,...\",\"is_full_scan\":true}' \\")
    print("        http://localhost:5000/scan")
    print("=" * 60)
    
    # Check if required directories exist
    required_dirs = ['controllers', 'services', 'yara_rules', 'uploads']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            print(f"📁 Created directory: {dir_name}")
    
    # Check if malware hash file exists
    if not os.path.exists('full_sha256.txt'):
        print("   Warning: full_sha256.txt not found. Malware hash checking will be limited.")
        print("   Place your malware hash database as 'full_sha256.txt' in the root directory.")
    else:
        with open('full_sha256.txt', 'r') as f:
            hash_count = sum(1 for line in f if line.strip() and not line.startswith('#'))
        print(f" Loaded {hash_count} malware hashes from full_sha256.txt")
    
    print("")
    print("Server starting at http://localhost:5000")
    print("   Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the Flask development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )