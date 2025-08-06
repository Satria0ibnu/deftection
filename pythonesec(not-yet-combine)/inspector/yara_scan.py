import yara
import logging
from config import YARA_RULE_PATH

# Initialize rules with error handling
try:
    COMPILED_RULES = yara.compile(filepath=YARA_RULE_PATH)
except yara.YaraCompileError as e:
    logging.error(f"YARA compile error: {e}")
    COMPILED_RULES = None
except FileNotFoundError:
    logging.error(f"YARA rules file not found: {YARA_RULE_PATH}")
    COMPILED_RULES = None

def scan_yara_bytes(byte_data):
    if not COMPILED_RULES:
        return {"flags": [], "indicators": []}
    
    try:
        matches = COMPILED_RULES.match(data=byte_data)
        indicators, flags = [], []

        for match in matches:
            rule_name = match.rule
            
            # Map YARA rule matches to specific flags
            for string_match in match.strings:
                identifier = string_match.identifier
                matched_data = string_match.instances[0].matched_data if string_match.instances else b""
                
                # Shellcode detection
                if identifier in ['$nop_sled', '$jmp_call_pop', '$xor_decoder']:
                    flags.append("yara_shellcode")
                    indicators.append(f"Shellcode pattern detected: {identifier}")
                
                elif identifier == '$int3_breakpoint':
                    flags.append("yara_debug")
                    indicators.append("Debug breakpoints found")
                
                # Steganography tools
                elif 'steg' in identifier or 'outguess' in identifier or 'jsteg' in identifier:
                    flags.append("steganography_tool")
                    indicators.append(f"Steganography tool signature: {matched_data.decode('ascii', errors='ignore')}")
                
                # Obfuscation
                elif identifier in ['$xor_string', '$rot13_encoded']:
                    flags.append("yara_obfuscation")
                    indicators.append("Obfuscated string patterns detected")
                
                # Ransomware/malware indicators
                elif 'ransom' in identifier or 'crypto_terms' in identifier:
                    flags.append("yara_malware")
                    indicators.append(f"Malware indicator: {matched_data.decode('ascii', errors='ignore')}")

        return {"flags": list(set(flags)), "indicators": indicators}
    
    except yara.Error as e:
        logging.error(f"YARA scanning error: {e}")
        return {"flags": [], "indicators": []}