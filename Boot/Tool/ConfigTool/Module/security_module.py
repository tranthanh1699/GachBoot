"""
Security Access (Service 0x27) configuration validator and code generator
"""

import re
from typing import Dict, List, Tuple

def parse_hex(value: str) -> int:
    """Parse hex string to integer"""
    if isinstance(value, int):
        return value
    value = value.strip()
    if value.startswith('0x') or value.startswith('0X'):
        return int(value, 16)
    return int(value)

class SecurityValidator:
    """Validator for Security Access configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, security_levels: List[Dict]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate security level configurations
        Returns: (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        if not security_levels:
            self.errors.append("No security levels configured")
            return False, self.errors, self.warnings
        
        seen_levels = set()
        seen_seed_subs = set()
        seen_key_subs = set()
        
        for idx, sec in enumerate(security_levels):
            # Check required fields
            required_fields = ['security_level', 'seed_request_sub', 'key_request_sub', 
                             'seed_size', 'key_size', 'max_attempts', 'delay_time',
                             'supported_sessions', 'get_seed_func', 'compare_key_func']
            
            for field in required_fields:
                if field not in sec:
                    self.errors.append(f"Security level {idx}: Missing required field '{field}'")
                    continue
            
            if self.errors:
                continue
                
            # Validate security level
            level = sec['security_level']
            if not isinstance(level, int) or level < 1 or level > 255:
                self.errors.append(f"Security level {idx}: Invalid level {level} (must be 1-255)")
            elif level in seen_levels:
                self.errors.append(f"Security level {idx}: Duplicate level {level}")
            else:
                seen_levels.add(level)
            
            # Validate seed request sub-function
            seed_sub = parse_hex(sec['seed_request_sub'])
            if seed_sub < 0x01 or seed_sub > 0xFF or seed_sub % 2 == 0:
                self.errors.append(f"Security level {idx}: Seed sub-function must be odd (0x01, 0x03, 0x05...)")
            elif seed_sub in seen_seed_subs:
                self.errors.append(f"Security level {idx}: Duplicate seed sub-function 0x{seed_sub:02X}")
            else:
                seen_seed_subs.add(seed_sub)
            
            # Validate key request sub-function
            key_sub = parse_hex(sec['key_request_sub'])
            expected_key_sub = seed_sub + 1
            if key_sub != expected_key_sub:
                self.errors.append(f"Security level {idx}: Key sub-function 0x{key_sub:02X} should be 0x{expected_key_sub:02X} (seed+1)")
            elif key_sub in seen_key_subs:
                self.errors.append(f"Security level {idx}: Duplicate key sub-function 0x{key_sub:02X}")
            else:
                seen_key_subs.add(key_sub)
            
            # Validate sizes
            if not isinstance(sec['seed_size'], int) or sec['seed_size'] < 1 or sec['seed_size'] > 16:
                self.errors.append(f"Security level {idx}: Seed size must be 1-16 bytes")
            
            if not isinstance(sec['key_size'], int) or sec['key_size'] < 1 or sec['key_size'] > 16:
                self.errors.append(f"Security level {idx}: Key size must be 1-16 bytes")
            
            # Validate max attempts
            if not isinstance(sec['max_attempts'], int) or sec['max_attempts'] < 1:
                self.errors.append(f"Security level {idx}: Max attempts must be >= 1")
            
            # Validate delay time
            if not isinstance(sec['delay_time'], int) or sec['delay_time'] < 0:
                self.errors.append(f"Security level {idx}: Delay time must be >= 0 ms")
            
            # Validate function names
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', sec['get_seed_func']):
                self.errors.append(f"Security level {idx}: Invalid get_seed function name")
            
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', sec['compare_key_func']):
                self.errors.append(f"Security level {idx}: Invalid compare_key function name")
            
            # Validate sessions
            if not isinstance(sec['supported_sessions'], list) or len(sec['supported_sessions']) == 0:
                self.errors.append(f"Security level {idx}: Must have at least one supported session")
        
        return len(self.errors) == 0, self.errors, self.warnings


class SecurityGenerator:
    """Code generator for Security Access configuration"""
    
    def __init__(self, project_name: str = "GachBoot", version: str = "1.0.0"):
        self.project_name = project_name
        self.version = version
    
    def generate_header(self, security_levels: List[Dict]) -> str:
        """Generate Security_PBCfg.h"""
        content = f"""/**
 * @file Security_PBCfg.h
 * @brief Security Access Configuration (Post-Build) - Generated File
 * @note DO NOT MODIFY - Auto-generated by {self.project_name} Config Tool v{self.version}
 */

#ifndef SECURITY_PBCFG_H
#define SECURITY_PBCFG_H

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

/* ========================================================================== */
/*                              Type Definitions                              */
/* ========================================================================== */
// Forward declare Std_ReturnType if not already defined

#ifndef STD_TYPES_H
typedef uint8_t Std_ReturnType;
typedef uint8_t ErrorCode_t;
#define E_OK        0x00u
#define E_NOT_OK    0x01u
#endif

/* Security Level Sub-functions */
"""
        
        # Generate sub-function defines
        for sec in security_levels:
            level = sec['security_level']
            seed_sub = parse_hex(sec['seed_request_sub'])
            key_sub = parse_hex(sec['key_request_sub'])
            
            content += f"#define SECURITY_LEVEL_{level}_REQUEST_SEED  0x{seed_sub:02X}\n"
            content += f"#define SECURITY_LEVEL_{level}_SEND_KEY      0x{key_sub:02X}\n"
        
        content += "\n/* Security Level Count */\n"
        content += f"#define SECURITY_LEVEL_COUNT  {len(security_levels)}U\n\n"
        
        # Typedef for callback functions
        content += "/* Security Level Callback Types */\n"
        content += "/**\n"
        content += " * @brief Seed generation callback\n"
        content += " * Generate a seed for security access\n"
        content += " * @param security_level Security level (1, 2, ...)\n"
        content += " * @param seed Output seed buffer (max 16 bytes)\n"
        content += " * @return Std_ReturnType E_OK, E_NOT_OK\n"
        content += " */\n"
        content += "typedef Std_ReturnType (*uds_security_get_seed_t)(uint8_t security_level, uint8_t *seed);\n\n"
        
        content += "/**\n"
        content += " * @brief Key comparison callback\n"
        content += " * Compare received key with expected key\n"
        content += " * @param security_level Security level (1, 2, ...)\n"
        content += " * @param key Received key buffer\n"
        content += " * @param seed Previously sent seed buffer\n"
        content += " * @return Std_ReturnType E_OK (key valid), E_NOT_OK (key invalid)\n"
        content += " */\n"
        content += "typedef Std_ReturnType (*uds_security_compare_key_t)(uint8_t security_level, const uint8_t *key, const uint8_t *seed);\n\n"
        
        # Typedef for security level config structure
        content += "/**\n"
        content += " * @brief Security level configuration entry (AUTOSAR DcmDspSecurityRow)\n"
        content += " */\n"
        content += "typedef struct {\n"
        content += "    uint8_t security_level;                     // Security level (1, 2, ...)\n"
        content += "    uint8_t security_sub_function_seed;         // Sub-function for request seed (0x01, 0x03, ...)\n"
        content += "    uint8_t security_sub_function_key;          // Sub-function for send key (0x02, 0x04, ...)\n"
        content += "    uint8_t seed_size;                          // Seed size in bytes\n"
        content += "    uint8_t key_size;                           // Key size in bytes\n"
        content += "    uint8_t num_failed_security_access;         // Max failed attempts before lockout\n"
        content += "    uint32_t security_delay_time_ms;            // Delay time after failed attempts (ms)\n"
        content += "    uint32_t session_mask;                      // Allowed sessions for security access\n"
        content += "    uds_security_get_seed_t get_seed_callback;  // Seed generation callback\n"
        content += "    uds_security_compare_key_t compare_key_callback;  // Key comparison callback\n"
        content += "} dcm_security_level_config_t;\n\n"
        
        # Extern callback function declarations
        content += "/* External callback function declarations (User must implement) */\n"
        for sec in security_levels:
            content += f"extern Std_ReturnType {sec['get_seed_func']}(uint8_t security_level, uint8_t *seed);\n"
            content += f"extern Std_ReturnType {sec['compare_key_func']}(uint8_t security_level, const uint8_t *key, const uint8_t *seed);\n"
        
        content += "\n/* External Security Level Configuration Table */\n"
        content += "extern const dcm_security_level_config_t security_level_config_table[SECURITY_LEVEL_COUNT];\n\n"
        content += "#endif /* SECURITY_PBCFG_H */\n"
        return content
    
    def calculate_session_mask(self, supported_sessions: List[str], session_map: Dict) -> int:
        """Calculate session mask from session names"""
        if not supported_sessions or not session_map:
            return 0
        
        mask = 0
        for session_name in supported_sessions:
            if session_name in session_map:
                session = session_map[session_name]
                value = parse_hex(session['session_value'])
                mask |= (1 << value)
        return mask
    
    def generate_source(self, security_levels: List[Dict], session_map: Dict = None) -> str:
        """Generate Security_PBCfg.c"""
        if session_map is None:
            session_map = {}
        
        content = f"""/**
 * @file Security_PBCfg.c
 * @brief Security Access Configuration (Post-Build) - Generated File
 * @note DO NOT MODIFY - Auto-generated by {self.project_name} Config Tool v{self.version}
 */

#include "Security_PBCfg.h"

/* Security Level Configuration Table */
const dcm_security_level_config_t security_level_config_table[SECURITY_LEVEL_COUNT] = {{
"""
        
        # Generate configuration entries
        for idx, sec in enumerate(security_levels):
            level = sec['security_level']
            seed_sub = parse_hex(sec['seed_request_sub'])
            key_sub = parse_hex(sec['key_request_sub'])
            seed_size = sec['seed_size']
            key_size = sec['key_size']
            max_attempts = sec['max_attempts']
            delay_time = sec['delay_time']
            supported_sessions = sec['supported_sessions']
            session_mask = self.calculate_session_mask(supported_sessions, session_map)
            get_seed = sec['get_seed_func']
            compare_key = sec['compare_key_func']
            
            content += f"    {{ /* Security Level {level} */\n"
            content += f"        .security_level = {level},\n"
            content += f"        .security_sub_function_seed = 0x{seed_sub:02X},\n"
            content += f"        .security_sub_function_key = 0x{key_sub:02X},\n"
            content += f"        .seed_size = {seed_size},\n"
            content += f"        .key_size = {key_size},\n"
            content += f"        .num_failed_security_access = {max_attempts},\n"
            content += f"        .security_delay_time_ms = {delay_time},\n"
            content += f"        .session_mask = {session_mask},  /* {', '.join(supported_sessions)} */\n"
            content += f"        .get_seed_callback = {get_seed},\n"
            content += f"        .compare_key_callback = {compare_key}\n"
            content += "    }" + ("," if idx < len(security_levels) - 1 else "") + "\n"
        
        content += "};\n"
        
        return content


def validate_security_levels(security_levels: List[Dict]) -> tuple:
    """
    Validate security level configurations
    Returns: (is_valid, errors, warnings)
    """
    validator = SecurityValidator()
    return validator.validate(security_levels)


def generate_security_code(security_levels: List[Dict], sessions: List[Dict], 
                          project_name: str, version: str, output_path: str) -> List[str]:
    """
    Generate security access configuration code
    Returns: List of generated file paths
    """
    import os
    
    # Create session map
    session_map = {s['session_name']: s for s in sessions}
    
    # Validate configuration
    validator = SecurityValidator()
    is_valid, errors, warnings = validator.validate(security_levels)
    
    if not is_valid:
        raise ValueError("Security configuration validation failed:\n" + "\n".join(errors))
    
    # Create output directory
    output_dir = os.path.join(output_path, "Security_Gen")
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean old files
    header_path = os.path.join(output_dir, "Security_PBCfg.h")
    source_path = os.path.join(output_dir, "Security_PBCfg.c")
    
    for old_file in [header_path, source_path]:
        if os.path.exists(old_file):
            os.remove(old_file)
    
    # Generate code
    generator = SecurityGenerator(project_name, version)
    
    header_content = generator.generate_header(security_levels)
    source_content = generator.generate_source(security_levels, session_map)
    
    # Write files
    with open(header_path, 'w', encoding='utf-8') as f:
        f.write(header_content)
    
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(source_content)
    
    return [header_path, source_path]
