# services/image_security_service.py
"""
Image Security Service
Core business logic for image scanning and threat detection
"""

import os
import hashlib
import time
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import yara
from PIL import Image
from PIL.ExifTags import TAGS
import magic

class ImageSecurityService:
    def __init__(self):
        self.malware_hashes = self._load_malware_hashes()
        self.yara_rules = self._compile_yara_rules()
        self.magic_mime = magic.Magic(mime=True)
        self.magic_desc = magic.Magic()
        
        # Configuration
        self.YARA_RULES_DIR = 'yara_rules'
        self.MALWARE_HASH_FILE = 'full_sha256.txt'
        
        # Ensure directories exist
        os.makedirs(self.YARA_RULES_DIR, exist_ok=True)
        
        print(f"ImageSecurityService initialized with {len(self.malware_hashes)} malware hashes")
    
    def _load_malware_hashes(self) -> set:
        """Load known malware SHA256 hashes"""
        hashes = set()
        if os.path.exists(self.MALWARE_HASH_FILE):
            try:
                with open(self.MALWARE_HASH_FILE, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and len(line) == 64:
                            hashes.add(line.lower())
            except Exception as e:
                print(f"Error loading malware hashes: {e}")
        return hashes
    
    def _create_yara_rules(self):
        """Create YARA rules for different scan types"""
        
        # Light scan rules - only critical threats
        light_rules = '''
rule Critical_Malware_Hash
{
    meta:
        description = "File matches known malware hash"
        severity = "critical"
        scan_type = "light"
        
    condition:
        false  // This will be handled by hash checking
}

rule Embedded_PE_Executable_Light
{
    meta:
        description = "PE executable embedded in image"
        severity = "critical"
        scan_type = "light"
        
    strings:
        $pe_header = { 4D 5A }
        $pe_signature = "This program cannot be run in DOS mode"
        
    condition:
        $pe_header and $pe_signature
}

rule Web_Shell_Critical
{
    meta:
        description = "Critical web shell signatures"
        severity = "critical"
        scan_type = "light"
        
    strings:
        $php_eval = "eval("
        $php_system = "system("
        $php_shell_exec = "shell_exec("
        $backdoor = "backdoor"
        
    condition:
        any of them
}

rule Fake_Image_Extension_Light
{
    meta:
        description = "Non-image content with image extension"
        severity = "high"
        scan_type = "light"
        
    strings:
        $pe_header = { 4D 5A }
        $elf_header = { 7F 45 4C 46 }
        $zip_header = { 50 4B 03 04 }
        
    condition:
        any of them
}
'''

        # Full scan rules - comprehensive detection
        full_rules = '''
rule Advanced_Steganography
{
    meta:
        description = "Advanced steganography detection"
        severity = "medium"
        scan_type = "full"
        
    strings:
        $steghide = "SteghidE"
        $outguess = "OutGuess"
        $zip_in_image = { 50 4B 03 04 }
        $rar_in_image = { 52 61 72 21 1A 07 00 }
        
    condition:
        any of them
}

rule Network_Threats_Full
{
    meta:
        description = "Network communication threats"
        severity = "high"
        scan_type = "full"
        
    strings:
        $http_post = "POST /"
        $base64_long = /[A-Za-z0-9+\/]{50,}/
        $suspicious_domain = /.+\.(tk|ml|ga|cf)/
        $c2_pattern = /[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]+/
        
    condition:
        2 of them
}

rule Cryptocurrency_Mining_Full
{
    meta:
        description = "Cryptocurrency mining indicators"
        severity = "medium"
        scan_type = "full"
        
    strings:
        $stratum = "stratum+tcp://"
        $mining_pool = "pool.minergate.com"
        $coinhive = "coinhive"
        $cryptonight = "cryptonight"
        
    condition:
        any of them
}

rule Living_Off_Land_Full
{
    meta:
        description = "Living-off-the-land techniques"
        severity = "medium"
        scan_type = "full"
        
    strings:
        $powershell_b64 = "powershell -e"
        $rundll32 = "rundll32"
        $certutil = "certutil"
        $bitsadmin = "bitsadmin"
        
    condition:
        any of them
}

rule Zero_Day_Indicators_Full
{
    meta:
        description = "Zero-day exploit indicators"
        severity = "critical"
        scan_type = "full"
        
    strings:
        $overflow_pattern = { 41 41 41 41 41 41 41 41 41 41 }
        $nop_sled = { 90 90 90 90 90 90 90 90 90 90 }
        $shellcode_pattern = { 31 C0 50 68 }
        
    condition:
        any of them
}

rule Phishing_Indicators_Full
{
    meta:
        description = "Phishing-related content"
        severity = "medium"
        scan_type = "full"
        
    strings:
        $paypal = "paypal" nocase
        $amazon = "amazon" nocase
        $microsoft = "microsoft" nocase
        $login_form = "login" nocase
        $verify_account = "verify" nocase
        
    condition:
        2 of them
}

rule Invalid_Headers_Full
{
    meta:
        description = "Invalid image headers - full scan"
        severity = "medium"
        scan_type = "full"
        
    strings:
        $jpeg_start = { FF D8 FF }
        $png_header = { 89 50 4E 47 0D 0A 1A 0A }
        $gif87a = "GIF87a"
        $gif89a = "GIF89a"
        
    condition:
        filename matches /\.(jpg|jpeg)$/i and not $jpeg_start at 0
        or filename matches /\.png$/i and not $png_header at 0
        or filename matches /\.gif$/i and not (($gif87a or $gif89a) at 0)
}
'''

        # Write rules to files
        with open(os.path.join(self.YARA_RULES_DIR, 'light_scan.yar'), 'w') as f:
            f.write(light_rules)
        
        with open(os.path.join(self.YARA_RULES_DIR, 'full_scan.yar'), 'w') as f:
            f.write(full_rules)
    
    def _compile_yara_rules(self):
        """Compile YARA rules"""
        self._create_yara_rules()
        
        try:
            rule_files = {}
            for rule_file in Path(self.YARA_RULES_DIR).glob('*.yar'):
                rule_files[rule_file.stem] = str(rule_file)
            
            if rule_files:
                compiled_rules = yara.compile(filepaths=rule_files)
                return compiled_rules
            else:
                return None
        except Exception as e:
            print(f"Error compiling YARA rules: {e}")
            return None
    
    def calculate_file_hash(self, file_path: str) -> Dict[str, str]:
        """Calculate file hashes"""
        hashes = {}
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            hashes['md5'] = hashlib.md5(content).hexdigest()
            hashes['sha1'] = hashlib.sha1(content).hexdigest()
            hashes['sha256'] = hashlib.sha256(content).hexdigest()
            hashes['sha512'] = hashlib.sha512(content).hexdigest()
        except Exception as e:
            print(f"Error calculating hashes: {e}")
        
        return hashes
    
    def check_malware_hash(self, file_hash: str) -> bool:
        """Check if hash matches known malware"""
        return file_hash.lower() in self.malware_hashes
    
    def get_file_info(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Get basic file information"""
        try:
            file_stat = os.stat(file_path)
            return {
                'filename': filename,
                'size_bytes': file_stat.st_size,
                'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                'mime_type': self.magic_mime.from_file(file_path),
                'file_type': self.magic_desc.from_file(file_path),
                'extension': Path(filename).suffix.lower()
            }
        except Exception as e:
            return {
                'filename': filename,
                'error': f"Error getting file info: {str(e)}"
            }
    
    def extract_exif_data(self, file_path: str) -> Dict[str, Any]:
        """Extract EXIF data from image"""
        exif_data = {}
        try:
            with Image.open(file_path) as img:
                exif_dict = img._getexif()
                
                if exif_dict:
                    for tag_id, value in exif_dict.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8')
                            except UnicodeDecodeError:
                                value = value.hex()
                        
                        exif_data[str(tag)] = str(value)
        except Exception as e:
            print(f"Error extracting EXIF: {e}")
        
        return exif_data
    
    def analyze_exif_threats(self, exif_data: Dict[str, Any], is_full_scan: bool) -> List[Dict[str, Any]]:
        """Analyze EXIF data for threats"""
        threats = []
        
        if is_full_scan:
            # Full scan - comprehensive EXIF analysis
            suspicious_patterns = {
                'script_injection': [r'<script', r'javascript:', r'eval\(', r'exec\('],
                'sql_injection': [r'union select', r'drop table', r'insert into'],
                'command_injection': [r'system\(', r'exec\(', r'shell_exec'],
                'xss_payload': [r'alert\(', r'document\.cookie', r'window\.location'],
                'file_inclusion': [r'\.\./', r'file://', r'http://']
            }
            
            for field, value in exif_data.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    
                    # Check suspicious patterns
                    for threat_type, patterns in suspicious_patterns.items():
                        for pattern in patterns:
                            if pattern in value_lower:
                                threats.append({
                                    'type': 'exif_threat',
                                    'subtype': threat_type,
                                    'field': field,
                                    'value': value[:100],
                                    'severity': 'high',
                                    'description': f'Suspicious {threat_type} in EXIF {field}'
                                })
                    
                    # Check for overly long values
                    if len(value) > 1000:
                        threats.append({
                            'type': 'exif_threat',
                            'subtype': 'buffer_overflow',
                            'field': field,
                            'value_length': len(value),
                            'severity': 'medium',
                            'description': f'Long EXIF {field} value ({len(value)} chars)'
                        })
                    
                    # Check for binary data
                    if any(ord(c) < 32 or ord(c) > 126 for c in value[:100]):
                        threats.append({
                            'type': 'exif_threat',
                            'subtype': 'binary_data',
                            'field': field,
                            'severity': 'medium',
                            'description': f'Binary data in EXIF {field}'
                        })
            
            # GPS privacy check
            gps_fields = ['GPS GPSLatitude', 'GPS GPSLongitude', 'GPSInfo']
            for field in gps_fields:
                if field in exif_data:
                    threats.append({
                        'type': 'privacy_threat',
                        'subtype': 'gps_location',
                        'field': field,
                        'value': exif_data[field],
                        'severity': 'low',
                        'description': 'GPS location data found'
                    })
        else:
            # Light scan - only critical EXIF threats
            critical_patterns = ['<script', 'eval(', 'system(', 'exec(']
            for field, value in exif_data.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    for pattern in critical_patterns:
                        if pattern in value_lower:
                            threats.append({
                                'type': 'exif_threat',
                                'subtype': 'critical_injection',
                                'field': field,
                                'value': value[:50],
                                'severity': 'critical',
                                'description': f'Critical threat in EXIF {field}'
                            })
        
        return threats
    
    def run_yara_scan(self, file_path: str, is_full_scan: bool) -> List[Dict[str, Any]]:
        """Run YARA rules scan"""
        matches = []
        
        if not self.yara_rules:
            return matches
        
        try:
            yara_matches = self.yara_rules.match(file_path)
            
            for match in yara_matches:
                # Filter based on scan type
                scan_type = match.meta.get('scan_type', 'full')
                
                if not is_full_scan and scan_type == 'full':
                    continue  # Skip full-scan-only rules in light scan
                
                threat_info = {
                    'rule_name': match.rule,
                    'namespace': match.namespace,
                    'severity': match.meta.get('severity', 'unknown'),
                    'description': match.meta.get('description', 'No description'),
                    'scan_type': scan_type,
                    'strings_matched': len(match.strings)
                }
                
                # Add string details for full scan
                if is_full_scan:
                    threat_info['matched_strings'] = []
                    for string_match in match.strings:
                        threat_info['matched_strings'].append({
                            'identifier': string_match.identifier,
                            'instances_count': len(string_match.instances),
                            'first_offset': string_match.instances[0].offset if string_match.instances else 0
                        })
                
                matches.append(threat_info)
        
        except Exception as e:
            print(f"Error running YARA scan: {e}")
        
        return matches
    
    def perform_light_scan(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Perform light security scan - critical threats only"""
        scan_start = time.time()
        
        result = {
            'scan_type': 'light',
            'file_info': self.get_file_info(file_path, filename),
            'hash_analysis': None,
            'yara_matches': [],
            'exif_analysis': None,
            'threat_summary': {
                'total_threats': 0,
                'critical_threats': 0,
                'high_threats': 0,
                'medium_threats': 0,
                'low_threats': 0
            },
            'scan_duration': 0
        }
        
        try:
            # 1. Hash analysis (always included)
            hashes = self.calculate_file_hash(file_path)
            is_malware = self.check_malware_hash(hashes.get('sha256', ''))
            
            result['hash_analysis'] = {
                'sha256': hashes.get('sha256', ''),
                'known_malware': is_malware,
                'reputation': 'malicious' if is_malware else 'unknown'
            }
            
            if is_malware:
                result['threat_summary']['critical_threats'] += 1
                result['threat_summary']['total_threats'] += 1
            
            # 2. Light YARA scan (critical rules only)
            yara_matches = self.run_yara_scan(file_path, is_full_scan=False)
            result['yara_matches'] = yara_matches
            
            # 3. Basic EXIF check (critical threats only)
            exif_data = self.extract_exif_data(file_path)
            exif_threats = self.analyze_exif_threats(exif_data, is_full_scan=False)
            
            result['exif_analysis'] = {
                'has_exif': len(exif_data) > 0,
                'threats_found': len(exif_threats),
                'exif_threats': exif_threats
            }
            
            # Count threats
            all_threats = yara_matches + exif_threats
            for threat in all_threats:
                severity = threat.get('severity', 'unknown')
                if severity == 'critical':
                    result['threat_summary']['critical_threats'] += 1
                elif severity == 'high':
                    result['threat_summary']['high_threats'] += 1
                elif severity == 'medium':
                    result['threat_summary']['medium_threats'] += 1
                elif severity == 'low':
                    result['threat_summary']['low_threats'] += 1
                
                result['threat_summary']['total_threats'] += 1
            
            result['scan_duration'] = round(time.time() - scan_start, 3)
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def perform_full_scan(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Perform comprehensive security scan"""
        scan_start = time.time()
        
        result = {
            'scan_type': 'full',
            'file_info': self.get_file_info(file_path, filename),
            'hash_analysis': None,
            'yara_matches': [],
            'exif_analysis': None,
            'advanced_analysis': None,
            'threat_summary': {
                'total_threats': 0,
                'critical_threats': 0,
                'high_threats': 0,
                'medium_threats': 0,
                'low_threats': 0
            },
            'scan_duration': 0
        }
        
        try:
            # 1. Complete hash analysis
            hashes = self.calculate_file_hash(file_path)
            is_malware = self.check_malware_hash(hashes.get('sha256', ''))
            
            result['hash_analysis'] = {
                'hashes': hashes,
                'known_malware': is_malware,
                'reputation': 'malicious' if is_malware else 'unknown'
            }
            
            if is_malware:
                result['threat_summary']['critical_threats'] += 1
                result['threat_summary']['total_threats'] += 1
            
            # 2. Full YARA scan (all rules)
            yara_matches = self.run_yara_scan(file_path, is_full_scan=True)
            result['yara_matches'] = yara_matches
            
            # 3. Complete EXIF analysis
            exif_data = self.extract_exif_data(file_path)
            exif_threats = self.analyze_exif_threats(exif_data, is_full_scan=True)
            
            result['exif_analysis'] = {
                'has_exif': len(exif_data) > 0,
                'exif_data': exif_data,
                'exif_size': len(str(exif_data)),
                'threats_found': len(exif_threats),
                'exif_threats': exif_threats
            }
            
            # 4. Advanced analysis (file structure, entropy, etc.)
            result['advanced_analysis'] = self._perform_advanced_analysis(file_path, filename)
            
            # Count all threats
            all_threats = yara_matches + exif_threats
            advanced_threats = result['advanced_analysis'].get('threats', [])
            all_threats.extend(advanced_threats)
            
            for threat in all_threats:
                severity = threat.get('severity', 'unknown')
                if severity == 'critical':
                    result['threat_summary']['critical_threats'] += 1
                elif severity == 'high':
                    result['threat_summary']['high_threats'] += 1
                elif severity == 'medium':
                    result['threat_summary']['medium_threats'] += 1
                elif severity == 'low':
                    result['threat_summary']['low_threats'] += 1
                
                result['threat_summary']['total_threats'] += 1
            
            result['scan_duration'] = round(time.time() - scan_start, 3)
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _perform_advanced_analysis(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Perform advanced file analysis"""
        analysis = {
            'file_structure': {},
            'entropy_analysis': {},
            'format_validation': {},
            'threats': []
        }
        
        try:
            # File structure analysis
            file_stat = os.stat(file_path)
            analysis['file_structure'] = {
                'size_analysis': {
                    'size_bytes': file_stat.st_size,
                    'suspicious_size': file_stat.st_size > 10 * 1024 * 1024,  # >10MB
                    'too_small': file_stat.st_size < 1024  # <1KB
                }
            }
            
            # Basic entropy analysis
            with open(file_path, 'rb') as f:
                data = f.read(8192)  # First 8KB
                if data:
                    entropy = self._calculate_entropy(data)
                    analysis['entropy_analysis'] = {
                        'entropy_score': entropy,
                        'high_entropy': entropy > 7.5,  # Suspicious if too high
                        'analysis': 'High entropy may indicate compression or encryption'
                    }
                    
                    if entropy > 7.8:
                        analysis['threats'].append({
                            'type': 'entropy_anomaly',
                            'severity': 'medium',
                            'description': f'High entropy score: {entropy:.2f}'
                        })
            
            # Format validation
            extension = Path(filename).suffix.lower()
            mime_type = self.magic_mime.from_file(file_path)
            
            analysis['format_validation'] = {
                'extension': extension,
                'mime_type': mime_type,
                'format_mismatch': not self._validate_format_match(extension, mime_type)
            }
            
            if analysis['format_validation']['format_mismatch']:
                analysis['threats'].append({
                    'type': 'format_mismatch',
                    'severity': 'high',
                    'description': f'Extension {extension} doesn\'t match MIME type {mime_type}'
                })
        
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0
        
        # Count byte frequencies
        frequencies = [0] * 256
        for byte in data:
            frequencies[byte] += 1
        
        # Calculate entropy
        length = len(data)
        entropy = 0
        for freq in frequencies:
            if freq > 0:
                p = freq / length
                entropy -= p * (p.bit_length() - 1)
        
        return entropy
    
    def _validate_format_match(self, extension: str, mime_type: str) -> bool:
        """Validate if file extension matches MIME type"""
        format_mappings = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp',
            '.ico': 'image/x-icon',
            '.psd': 'image/vnd.adobe.photoshop'
        }
        
        expected_mime = format_mappings.get(extension.lower())
        return expected_mime and expected_mime in mime_type
    
    def scan_file(self, file_data: bytes, filename: str, is_full_scan: bool = False) -> Dict[str, Any]:
        """Main method to scan uploaded file"""
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
        
        try:
            # Perform appropriate scan type
            if is_full_scan:
                result = self.perform_full_scan(temp_file_path, filename)
            else:
                result = self.perform_light_scan(temp_file_path, filename)
            
            return result
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"Error cleaning up temp file: {e}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information and statistics"""
        return {
            'service_name': 'ImageSecurityService',
            'version': '1.0.0',
            'malware_hashes_loaded': len(self.malware_hashes),
            'yara_rules_compiled': self.yara_rules is not None,
            'scan_types': ['light', 'full'],
            'supported_formats': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.psd']
        }