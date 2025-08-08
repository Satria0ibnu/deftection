# controllers/image_security_controller.py
"""
Image Security Controller
Handles HTTP requests and response formatting for image security scanning
"""

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

from flask import Flask, request, jsonify
from services.image_security_service import ImageSecurityService

class ImageSecurityController:
    def __init__(self):
        self.service = ImageSecurityService()
        
        # Configuration
        self.MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        self.ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.psd'}
    
    def scan_image(self, request) -> Tuple[Dict[str, Any], int]:
        """Main endpoint for image security scanning"""
        try:
            # Extract file data and parameters
            file_data, filename, validation_error = self._extract_file_data(request)
            
            if validation_error:
                return self._error_response(validation_error, 400)
            
            # Extract scan parameters
            is_full_scan = self._extract_scan_parameters(request)
            
            # Perform scan using service
            scan_result = self.service.scan_file(file_data, filename, is_full_scan)
            
            # Format and return response
            return self._format_scan_response(scan_result, filename, is_full_scan)
        
        except Exception as e:
            return self._error_response(f"Internal scan error: {str(e)}", 500)
    
    def health_check(self) -> Tuple[Dict[str, Any], int]:
        """Health check endpoint"""
        try:
            service_info = self.service.get_service_info()
            
            response = {
                'status': 'healthy',
                'service_info': service_info,
                'configuration': {
                    'max_file_size_mb': self.MAX_FILE_SIZE // (1024 * 1024),
                    'allowed_extensions': list(self.ALLOWED_EXTENSIONS),
                    'scan_types': ['light', 'full']
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return response, 200
        
        except Exception as e:
            return self._error_response(f"Health check failed: {str(e)}", 500)
    
    def get_scanner_stats(self) -> Tuple[Dict[str, Any], int]:
        """Get scanner statistics"""
        try:
            service_info = self.service.get_service_info()
            
            response = {
                'status': 'success',
                'scanner_statistics': {
                    'service_info': service_info,
                    'scan_capabilities': {
                        'light_scan': {
                            'description': 'Fast scan for critical threats only',
                            'includes': [
                                'Known malware hash checking',
                                'Critical YARA rules (PE executables, web shells)',
                                'Basic EXIF threat detection',
                                'File format validation'
                            ],
                            'average_duration': '< 0.5 seconds'
                        },
                        'full_scan': {
                            'description': 'Comprehensive security analysis',
                            'includes': [
                                'Complete hash analysis (MD5, SHA1, SHA256, SHA512)',
                                'All YARA rules (malware, steganography, network threats)',
                                'Complete EXIF analysis with privacy checks',
                                'Advanced file structure analysis',
                                'Entropy analysis',
                                'Format validation and mismatch detection'
                            ],
                            'average_duration': '1-3 seconds'
                        }
                    },
                    'threat_detection': {
                        'categories': [
                            'Malware (executables, web shells, ransomware)',
                            'Steganography (hidden data, tools)',
                            'Network threats (C2, phishing, data exfiltration)',
                            'Advanced threats (zero-day, cryptocurrency mining)',
                            'Privacy concerns (GPS data, metadata)',
                            'Format manipulation (fake extensions, polyglots)'
                        ]
                    }
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return response, 200
        
        except Exception as e:
            return self._error_response(f"Stats retrieval failed: {str(e)}", 500)
    
    def _extract_file_data(self, request) -> Tuple[bytes, str, str]:
        """Extract file data from request"""
        try:
            # Handle JSON request with base64 data
            if request.is_json:
                json_data = request.get_json()
                
                if 'image_base64' not in json_data:
                    return None, None, 'JSON request must contain "image_base64"field'
                
                try:
                    base64_data = json_data['image_base64']
                    if base64_data.startswith('data:'):
                        base64_data = base64_data.split(',')[1]
                    
                    file_data = base64.b64decode(base64_data)
                    filename = json_data.get('filename', 'uploaded_image.bin')
                    
                except Exception as e:
                    return None, None, f'Invalid base64 data: {str(e)}'
            
            # Handle form data with file upload
            elif 'file' in request.files:
                uploaded_file = request.files['file']
                
                if uploaded_file.filename == '':
                    return None, None, 'No file selected'
                
                file_data = uploaded_file.read()
                filename = uploaded_file.filename
            
            else:
                return None, None, 'No file provided. Use "file"field for form data or "image_base64"for JSON'
            
            # Validate file size
            if len(file_data) > self.MAX_FILE_SIZE:
                return None, None, f'File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB'
            
            # Validate file extension
            file_extension = Path(filename).suffix.lower()
            if file_extension not in self.ALLOWED_EXTENSIONS:
                return None, None, f'File type not allowed. Allowed extensions: {", ".join(self.ALLOWED_EXTENSIONS)}'
            
            return file_data, filename, None
        
        except Exception as e:
            return None, None, f'Error extracting file data: {str(e)}'
    
    def _extract_scan_parameters(self, request) -> bool:
        """Extract scan parameters from request"""
        # Default to light scan
        is_full_scan = False
        
        try:
            if request.is_json:
                json_data = request.get_json()
                is_full_scan = json_data.get('is_full_scan', False)
            else:
                # Check form data or query parameters
                is_full_scan = request.form.get('is_full_scan', 'false').lower() == 'true'
                if not is_full_scan:
                    is_full_scan = request.args.get('is_full_scan', 'false').lower() == 'true'
            
            # Ensure boolean type
            if isinstance(is_full_scan, str):
                is_full_scan = is_full_scan.lower() in ['true', '1', 'yes', 'on']
            else:
                is_full_scan = bool(is_full_scan)
        
        except Exception as e:
            print(f"Error extracting scan parameters: {e}")
            is_full_scan = False
        
        return is_full_scan
    
    def _format_scan_response(self, scan_result: Dict[str, Any], filename: str, is_full_scan: bool) -> Tuple[Dict[str, Any], int]:
        """Format scan results into API response"""
        # Determine risk level and status code
        threat_summary = scan_result.get('threat_summary', {})
        risk_level = self._calculate_risk_level(threat_summary)
        
        # Base response structure
        response = {
            'status': 'success',
            'scan_result': {
                'scan_type': 'full' if is_full_scan else 'light',
                'risk_level': risk_level,
                'file_info': scan_result.get('file_info', {}),
                'security_analysis': self._format_security_analysis(scan_result, is_full_scan),
                'threat_summary': threat_summary,
                'recommendations': self._generate_recommendations(scan_result, risk_level),
                'scan_metadata': {
                    'scan_duration': scan_result.get('scan_duration', 0),
                    'scan_timestamp': datetime.now().isoformat(),
                    'scanner_version': '1.0.0',
                    'is_full_scan': is_full_scan
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Add error if present
        if 'error' in scan_result:
            response['scan_result']['error'] = scan_result['error']
        
        return response, 200
    
    def _format_security_analysis(self, scan_result: Dict[str, Any], is_full_scan: bool) -> Dict[str, Any]:
        """Format security analysis section"""
        analysis = {}
        
        # Hash analysis
        hash_analysis = scan_result.get('hash_analysis', {})
        if is_full_scan:
            analysis['hash_analysis'] = {
                'hashes': hash_analysis.get('hashes', {}),
                'known_malware': hash_analysis.get('known_malware', False),
                'reputation': hash_analysis.get('reputation', 'unknown')
            }
        else:
            analysis['hash_analysis'] = {
                'sha256': hash_analysis.get('sha256', ''),
                'known_malware': hash_analysis.get('known_malware', False),
                'reputation': hash_analysis.get('reputation', 'unknown')
            }
        
        # YARA detections
        yara_matches = scan_result.get('yara_matches', [])
        analysis['yara_detections'] = {
            'total_rules_matched': len(yara_matches),
            'matches': yara_matches
        }
        
        # EXIF analysis
        exif_analysis = scan_result.get('exif_analysis', {})
        if is_full_scan:
            analysis['exif_analysis'] = {
                'has_exif_data': exif_analysis.get('has_exif', False),
                'exif_data': exif_analysis.get('exif_data', {}),
                'exif_size_bytes': exif_analysis.get('exif_size', 0),
                'threats_found': exif_analysis.get('threats_found', 0),
                'exif_threats': exif_analysis.get('exif_threats', [])
            }
        else:
            analysis['exif_analysis'] = {
                'has_exif_data': exif_analysis.get('has_exif', False),
                'threats_found': exif_analysis.get('threats_found', 0),
                'exif_threats': exif_analysis.get('exif_threats', [])
            }
        
        # Advanced analysis (full scan only)
        if is_full_scan:
            advanced_analysis = scan_result.get('advanced_analysis', {})
            analysis['advanced_analysis'] = {
                'file_structure': advanced_analysis.get('file_structure', {}),
                'entropy_analysis': advanced_analysis.get('entropy_analysis', {}),
                'format_validation': advanced_analysis.get('format_validation', {}),
                'additional_threats': advanced_analysis.get('threats', [])
            }
        
        return analysis
    
    def _calculate_risk_level(self, threat_summary: Dict[str, Any]) -> str:
        """Calculate overall risk level"""
        critical = threat_summary.get('critical_threats', 0)
        high = threat_summary.get('high_threats', 0)
        medium = threat_summary.get('medium_threats', 0)
        low = threat_summary.get('low_threats', 0)
        
        if critical > 0:
            return 'CRITICAL'
        elif high > 0:
            return 'HIGH'
        elif medium > 0:
            return 'MEDIUM'
        elif low > 0:
            return 'LOW'
        else:
            return 'CLEAN'
    
    def _generate_recommendations(self, scan_result: Dict[str, Any], risk_level: str) -> list:
        """Generate security recommendations"""
        recommendations = []
        
        # Risk-based recommendations
        if risk_level == 'CRITICAL':
            recommendations.extend([
                "CRITICAL: Do not open or execute this file",
                "CRITICAL: Quarantine this file immediately",
                "CRITICAL: Run full system antivirus scan",
                "CRITICAL: Report to security team immediately"
            ])
        elif risk_level == 'HIGH':
            recommendations.extend([
                "HIGH RISK: Exercise extreme caution",
                "Isolate file and verify source",
                "Consider additional malware scanning"
            ])
        elif risk_level == 'MEDIUM':
            recommendations.extend([
                "MEDIUM RISK: Review detected threats",
                "Verify file authenticity and source"
            ])
        elif risk_level == 'LOW':
            recommendations.extend([
                "LOW RISK: Minor concerns detected",
                "Review privacy and metadata concerns"
            ])
        else:
            recommendations.extend([
                "CLEAN: No security threats detected",
                "File appears safe to use"
            ])
        
        # Hash-specific recommendations
        hash_analysis = scan_result.get('hash_analysis', {})
        if hash_analysis.get('known_malware'):
            recommendations.append("MALWARE: File matches known malware signatures")
        
        # YARA-specific recommendations
        yara_matches = scan_result.get('yara_matches', [])
        if yara_matches:
            critical_rules = [m for m in yara_matches if m.get('severity') == 'critical']
            if critical_rules:
                recommendations.append(f"CRITICAL YARA: {len(critical_rules)} critical rules triggered")
        
        # EXIF-specific recommendations
        exif_analysis = scan_result.get('exif_analysis', {})
        exif_threats = exif_analysis.get('exif_threats', [])
        if exif_threats:
            critical_exif = [t for t in exif_threats if t.get('severity') == 'critical']
            if critical_exif:
                recommendations.append("CRITICAL EXIF: Malicious content in metadata")
        
        # General recommendations
        scan_type = scan_result.get('scan_type', 'light')
        if scan_type == 'light' and risk_level != 'CLEAN':
            recommendations.append("SUGGESTION: Run full scan for detailed analysis")
        
        recommendations.extend([
            "Always verify file sources",
            "Keep antivirus software updated",
            "Use principle of least privilege"
        ])
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    def _error_response(self, message: str, status_code: int) -> Tuple[Dict[str, Any], int]:
        """Generate error response"""
        return {
            'status': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }, status_code
