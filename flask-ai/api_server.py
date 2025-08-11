"""
Combined Stateless API Server for Defect Detection + Security Scanning
Support both JSON (base64) and form-data (file upload) for ALL endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import logging
from datetime import datetime

# Import controllers from flask-ai (main base)
from controllers.detection_controller import DetectionController

# Import services from flask-ai (main base) 
from services.detection_service import DetectionService

# Import security scanning components from pythonsec2
from controllers.image_security_controller import ImageSecurityController

class CombinedAPIServer:
    """
    FIXED Combined API Server: Flask-AI (main) + Security Scanner
    Support both JSON and form-data requests
    """
    
    def __init__(self, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.host = host
        self.port = port
        
        # Setup logging
        self._setup_logging()
        
        # Initialize services (flask-ai main base)
        self.detection_service = DetectionService()
        
        # Initialize controllers (flask-ai main base)
        self.detection_controller = DetectionController(self.detection_service)
        
        # Initialize security scanner (from pythonsec2)
        self.security_controller = ImageSecurityController()
        
        # Setup routes
        self._setup_routes()
        
        print("FIXED Combined API Server initialized (Flask-AI + Security Scanner)")
    
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('combined_detection.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _setup_routes(self):
        """Setup all API endpoints"""
        
        # ===========================
        # FLASK-AI ROUTES (MAIN BASE) 
        # ===========================
        
        # Health and system endpoints (flask-ai)
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return self.detection_controller.health_check()
        
        @self.app.route('/api/system/info', methods=['GET'])
        def system_info():
            return self.detection_controller.get_system_info()
        
        @self.app.route('/api/system/status', methods=['GET'])
        def system_status():
            return self.detection_controller.get_system_status()
        
        # Detection endpoints (flask-ai) - FIXED
        @self.app.route('/api/detection/image', methods=['POST'])
        def detect_image():
            return self.detection_controller.process_image(request)
        
        @self.app.route('/api/detection/frame', methods=['POST'])
        def detect_frame():
            return self.detection_controller.process_frame(request)
        
        @self.app.route('/api/detection/batch', methods=['POST'])
        def detect_batch():
            return self.detection_controller.process_batch(request)
        
        # Configuration endpoints (flask-ai)
        @self.app.route('/api/config/thresholds', methods=['GET'])
        def get_thresholds():
            return self.detection_controller.get_detection_thresholds()
        
        @self.app.route('/api/config/thresholds', methods=['PUT'])
        def update_thresholds():
            return self.detection_controller.update_detection_thresholds(request)
        
        # ===========================
        # NEW COMBINED ENDPOINT - FIXED
        # ===========================
        
        @self.app.route('/api/detection/combined', methods=['POST'])
        def detect_combined():
            """
            FIXED: Combined defect detection + security scan
            Supports both JSON (base64) and form-data (file upload)
            Parameter: is_scan_threat (boolean) - if true, adds security scan with is_full_scan=false
            """
            try:
                self.logger.info(f"Combined detection request - Content-Type: {request.content_type}")
                
                # Get defect detection result (flask-ai main) - FIXED
                defect_result = self.detection_controller.process_image(request)
                
                # Extract JSON response from Flask response object
                if hasattr(defect_result, 'get_json'):
                    defect_data = defect_result.get_json()
                    defect_status_code = defect_result.status_code
                elif isinstance(defect_result, tuple):
                    defect_response, defect_status_code = defect_result
                    if hasattr(defect_response, 'get_json'):
                        defect_data = defect_response.get_json()
                    else:
                        defect_data = defect_response.json if hasattr(defect_response, 'json') else defect_response
                else:
                    defect_data = defect_result
                    defect_status_code = 200
                
                # Check if security scan requested - FIXED for both content types
                is_scan_threat = False
                
                if request.is_json or 'application/json' in str(request.content_type):
                    json_data = request.get_json()
                    if json_data:
                        is_scan_threat = json_data.get('is_scan_threat', False)
                elif request.form:
                    is_scan_threat = request.form.get('is_scan_threat', 'false').lower() == 'true'
                
                self.logger.info(f"Security scan requested: {is_scan_threat}")
                
                if is_scan_threat:
                    # Add security scan with is_full_scan=false (light scan)
                    try:
                        # Create a modified request for security scan
                        security_result = self.security_controller.scan_image_laravel(request)
                        
                        # Extract security response
                        if isinstance(security_result, tuple):
                            security_data, security_status_code = security_result
                        else:
                            security_data = security_result
                            security_status_code = 200
                        
                        # Merge responses if both successful
                        if defect_status_code == 200 and security_status_code == 200:
                            # Ensure defect_data has the right structure
                            if not isinstance(defect_data, dict):
                                defect_data = {'data': defect_data} if defect_data else {'data': {}}
                            
                            # Add security scan to defect result
                            if 'data' not in defect_data:
                                defect_data['data'] = {}
                            
                            defect_data['security_scan'] = security_data.get('data', security_data)
                            defect_data['combined_analysis'] = True
                            defect_data['timestamp'] = datetime.now().isoformat()
                            
                            return jsonify(defect_data), 200
                        else:
                            # Return defect result with security error info
                            if not isinstance(defect_data, dict):
                                defect_data = {'data': defect_data} if defect_data else {'data': {}}
                            
                            defect_data['security_scan'] = {
                                'status': 'error',
                                'error': 'Security scan failed',
                                'details': security_data if security_status_code != 200 else 'Unknown error'
                            }
                            defect_data['combined_analysis'] = True
                            defect_data['timestamp'] = datetime.now().isoformat()
                            
                            return jsonify(defect_data), defect_status_code
                    
                    except Exception as security_error:
                        self.logger.error(f"Security scan error: {security_error}")
                        # Return defect result with security error info
                        if not isinstance(defect_data, dict):
                            defect_data = {'data': defect_data} if defect_data else {'data': {}}
                        
                        defect_data['security_scan'] = {
                            'status': 'error',
                            'error': f'Security scan failed: {str(security_error)}',
                            'details': str(security_error)
                        }
                        defect_data['combined_analysis'] = True
                        defect_data['timestamp'] = datetime.now().isoformat()
                        
                        return jsonify(defect_data), defect_status_code
                else:
                    # Return only defect detection
                    if not isinstance(defect_data, dict):
                        defect_data = {'data': defect_data} if defect_data else {'data': {}}
                    
                    defect_data['combined_analysis'] = False
                    defect_data['timestamp'] = datetime.now().isoformat()
                    
                    return jsonify(defect_data), defect_status_code
                    
            except Exception as e:
                self.logger.error(f"Combined detection error: {e}")
                return jsonify({
                    'status': 'error',
                    'error': f'Combined detection failed: {str(e)}',
                    'timestamp': datetime.now().isoformat(),
                    'combined_analysis': False
                }), 500
        
        # ===========================
        # SECURITY SCANNER ENDPOINTS - FIXED
        # ===========================
        
        @self.app.route('/api/security/scan', methods=['POST'])
        def security_scan():
            """
            FIXED: Security scan endpoint (normal format)
            Supports both JSON (base64) and form-data (file upload)
            Parameter: is_full_scan (boolean) - from request
            """
            return self.security_controller.scan_image(request)
        
        @self.app.route('/api/security/scan/laravel', methods=['POST'])
        def security_scan_laravel():
            """
            FIXED: Security scan endpoint (Laravel format)
            Supports both JSON (base64) and form-data (file upload)
            Parameter: is_full_scan (boolean) - from request
            """
            return self.security_controller.scan_image_laravel(request)
        
        # Security health endpoints
        @self.app.route('/api/security/health', methods=['GET'])
        def security_health():
            return self.security_controller.health_check()
        
        @self.app.route('/api/security/stats', methods=['GET'])
        def security_stats():
            return self.security_controller.get_scanner_stats()
        
        # ===========================
        # ERROR HANDLERS
        # ===========================
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'error': 'Endpoint not found',
                'message': 'The requested API endpoint does not exist',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                'error': 'Internal server error',
                'message': 'An internal error occurred while processing the request',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        @self.app.errorhandler(400)
        def bad_request(error):
            return jsonify({
                'error': 'Bad request',
                'message': 'Invalid request data or parameters',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        @self.app.errorhandler(413)
        def file_too_large(error):
            return jsonify({
                'error': 'File too large',
                'message': 'File exceeds maximum allowed size',
                'timestamp': datetime.now().isoformat()
            }), 413
        
        @self.app.errorhandler(415)
        def unsupported_media_type(error):
            return jsonify({
                'error': 'Unsupported Media Type',
                'message': 'Content-Type not supported. Use application/json or multipart/form-data',
                'supported_types': ['application/json', 'multipart/form-data'],
                'timestamp': datetime.now().isoformat()
            }), 415
    
    def run(self, debug=False):
        """Start the FIXED Combined API server"""
        print("Starting FIXED Combined API Server (Flask-AI + Security Scanner)")
        print("=" * 70)
        print(f"Server URL: http://{self.host}:{self.port}")
        print()
        print("FLASK-AI ENDPOINTS (Main Base) - FIXED:")
        print(f"  Health Check: GET /api/health")
        print(f"  System Info:  GET /api/system/info") 
        print(f"  Detect Image: POST /api/detection/image")
        print(f"                Support: JSON (image_base64) + Form-data (image/file)")
        print(f"  Detect Frame: POST /api/detection/frame")
        print(f"                Support: JSON (frame_base64/image_base64) + Form-data (frame/image/file)")
        print(f"  Batch Detect: POST /api/detection/batch")
        print(f"                Support: JSON (images array) + Form-data (multiple files)")
        print()
        print("NEW COMBINED ENDPOINT - FIXED:")
        print(f"  Combined:     POST /api/detection/combined")
        print(f"                Support: JSON + Form-data")
        print(f"                Param: is_scan_threat=true for security scan")
        print()
        print("SECURITY SCANNER ENDPOINTS - FIXED:")
        print(f"  Security Scan: POST /api/security/scan")
        print(f"                 Support: JSON (image_base64/image/file_base64/data) + Form-data")
        print(f"                 Param: is_full_scan=true/false")
        print(f"  Laravel Format: POST /api/security/scan/laravel")
        print(f"                  Support: JSON (image_base64/image/file_base64/data) + Form-data") 
        print(f"                  Param: is_full_scan=true/false")
        print(f"  Security Health: GET /api/security/health")
        print(f"  Security Stats:  GET /api/security/stats")
        print("=" * 70)
        print("ALL ENDPOINTS NOW SUPPORT BOTH JSON AND FORM-DATA!")
        print("JSON: Use 'image_base64', 'frame_base64' fields")
        print("Form-data: Use 'image', 'file', 'frame' fields")
        print("=" * 70)
        
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True, use_reloader=False)


def create_combined_api_server(host='0.0.0.0', port=5001):
    """Factory function to create FIXED combined API server"""
    return CombinedAPIServer(host=host, port=port)


if __name__ == "__main__":
    # Create and start the FIXED combined API server
    api_server = create_combined_api_server()
    api_server.run(debug=True)