rule SuspiciousImagePayload : image stego shellcode {
    meta:
        description = "Detects shellcode patterns and steganography markers in images"
        author = "satria"
        date = "2025-07-16"
        threat_level = "high"

    strings:
        // Shellcode patterns (not easily detectable in Python)
        $nop_sled = { 90 90 90 90 90 90 90 90 }  // Extended NOP sled
        $jmp_call_pop = { E8 ?? ?? ?? ?? 5? }     // Call-pop pattern
        $xor_decoder = { 31 C0 31 DB 31 C9 31 D2 } // Multi-register XOR
        $int3_breakpoint = { CC CC CC }           // Debug breakpoints
        
        // Steganography tool signatures (specific to tools)
        $jsteg_marker = "JSTEG" ascii
        $outguess_marker = "OUTGUESS" ascii  
        $openstego_marker = "OPENSTEGO" ascii
        $stegsolve_marker = "StegSolve" ascii
        $steghide_marker = "steghide" ascii
        
        // Obfuscation patterns
        $xor_string = "payload" xor(0x01-0xFF)
        $rot13_encoded = /[N-ZA-Mn-za-m]{10,}/ ascii // ROT13 patterns
        
        // Ransomware/malware specific strings
        $ransom_pdb1 = "klospad.pdb" ascii nocase
        $ransom_pdb2 = "keme132.dll" ascii nocase
        $crypto_terms = /(encrypt|decrypt|ransom|bitcoin|wallet)/i ascii

    condition:
        // Only pattern-based detection, let Python handle structure
        (
            2 of ($nop_sled, $jmp_call_pop, $xor_decoder, $int3_breakpoint) or
            any of ($jsteg_marker, $outguess_marker, $openstego_marker, $stegsolve_marker, $steghide_marker) or
            $xor_string or $rot13_encoded or
            any of ($ransom_pdb*, $crypto_terms)
        )
}