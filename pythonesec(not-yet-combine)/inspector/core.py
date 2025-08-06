import hashlib
import asyncio
import time
import re
from config import YARA_RULE_PATH, MALWARE_HASH_FILE
from .yara_scan import scan_yara_bytes
from .entropy import calculate_entropy
from .stego_check import detect_appended_data
from .utils import (
    load_malware_hashes, check_exif, pixel_anomaly,
    decode_qr, check_file_signature, suspicious_domain_match
)

def detect_base64_blocks(byte_data):
    """Python-based Base64 detection (more efficient than YARA for this)"""
    try:
        text_data = byte_data.decode('ascii', errors='ignore')
        # Look for long base64-like strings
        base64_pattern = r'[A-Za-z0-9+/]{100,}={0,2}'
        matches = re.findall(base64_pattern, text_data)
        return len(matches) > 0, len(matches)
    except:
        return False, 0

def detect_pe_characteristics(byte_data):
    """Enhanced PE detection beyond just MZ header"""
    if len(byte_data) < 64:
        return False
    
    # Check for MZ header
    if not byte_data.startswith(b'MZ'):
        return False
    
    try:
        # Get PE header offset
        pe_offset = int.from_bytes(byte_data[60:64], 'little')
        if pe_offset >= len(byte_data) - 4:
            return False
            
        # Check PE signature
        if byte_data[pe_offset:pe_offset+4] == b'PE\x00\x00':
            return True
    except:
        pass
    
    return False

async def scan_image_file(path, executor):
    start_time = time.perf_counter()
    loop = asyncio.get_event_loop()

    with open(path, 'rb') as f:
        byte_data = f.read()

    file_hash = hashlib.sha256(byte_data).hexdigest()
    known_hashes = await loop.run_in_executor(executor, load_malware_hashes, MALWARE_HASH_FILE)

    flags, details, attack_types = [], {}, []

    # Hash check 
    if file_hash in known_hashes:
        flags.append("known_hash")
        details["match"] = "SHA256 matched entry in malware_hashes.txt"
        attack_types.append("Known malicious image variant")

    # YARA scan
    yara_result = await loop.run_in_executor(executor, scan_yara_bytes, byte_data)
    flags.extend(yara_result["flags"])
    if yara_result["indicators"]:
        details["yara_indicators"] = ", ".join(yara_result["indicators"])

    # Metadata analysis 
    if await loop.run_in_executor(executor, check_exif, path):
        flags.append("suspicious_exif")
        details["exif_alert"] = "Found script-like entry in EXIF metadata"
        attack_types.append("Metadata-based injection or obfuscation")

    # Visual analysis 
    if await loop.run_in_executor(executor, pixel_anomaly, path):
        flags.append("pixel_uniformity")
        details["pixel_analysis"] = "Low grayscale deviation suggests forged visuals"
        attack_types.append("Tampering or image block manipulation")

    # File signature validation 
    if not await loop.run_in_executor(executor, check_file_signature, path):
        flags.append("invalid_signature")
        details["signature_check"] = "Image file signature mismatch"
        attack_types.append("Executable masquerading as image")

    # Enhanced PE detection 
    pe_detected = await loop.run_in_executor(executor, detect_pe_characteristics, byte_data)
    if pe_detected:
        flags.append("embedded_pe")
        details["pe_analysis"] = "Valid PE executable found in image"
        attack_types.append("Executable payload embedded in image")

    # Steganography detection 
    if await loop.run_in_executor(executor, detect_appended_data, path):
        flags.append("appended_data")
        details["tampering"] = "Extra data found after image end"
        attack_types.append("Steganographic payload hidden in image")

    # Entropy analysis 
    entropy = await loop.run_in_executor(executor, calculate_entropy, byte_data)
    if entropy < 3:
        flags.append("low_entropy")
        details["entropy"] = f"Entropy of {entropy:.2f} suggests overly uniform data"
        attack_types.append("Unnatural pixel encoding or padding")
    elif entropy > 7:
        flags.append("high_entropy")
        details["entropy"] = f"Entropy of {entropy:.2f} suggests encryption or packed data"
        attack_types.append("Obfuscated or encrypted data in image")

    # Base64 detection 
    has_base64, b64_count = await loop.run_in_executor(executor, detect_base64_blocks, byte_data)
    if has_base64:
        flags.append("base64_blocks")
        details["base64_analysis"] = f"Found {b64_count} large Base64-encoded blocks"
        attack_types.append("Base64-encoded payload detected")

    # QR code analysis 
    qr_result = await loop.run_in_executor(executor, decode_qr, path)
    if qr_result['valid']:
        details["qr_content"] = qr_result['content']
        if "http" in qr_result['content']:
            flags.append("malicious_qr")
            details["qr_protocol"] = "Unencrypted URL found in QR code"
            attack_types.append("Credential harvesting via QR redirect")
            if suspicious_domain_match(qr_result['content']):
                flags.append("phishing_domain")
                details["domain_analysis"] = "Domain resembles known phishing patterns"
                attack_types.append("Suspicious redirect to phishing domain")

    # Risk assessment
    risk_level = "none"
    critical_flags = {"known_hash", "yara_malware", "embedded_pe"}
    high_flags = {"yara_shellcode", "steganography_tool", "appended_data"}
    
    if any(flag in flags for flag in critical_flags):
        risk_level = "critical"
    elif any(flag in flags for flag in high_flags) or len(set(flags)) >= 3:
        risk_level = "high"
    elif len(set(flags)) == 2:
        risk_level = "medium"
    elif len(set(flags)) >= 1:
        risk_level = "low"

    end_time = time.perf_counter()
    duration_ms = int((end_time - start_time) * 1000)

    return {
        "filename": path.split('/')[-1],
        "hash": file_hash,
        "status": "malicious" if risk_level in ["high", "critical"] else "suspicious" if risk_level in ["medium", "low"] else "clean",
        "risk_level": risk_level,
        "flags": sorted(set(flags)),
        "details": details,
        "possible_attacks": sorted(set(attack_types)) or ["None detected"],
        "processing_time_ms": duration_ms
    }