#!/usr/bin/env python3
"""
DID Module - Validation and Code Generation for DIDs
Independent of NVM - follows struct.md specification
"""

from typing import Dict, List, Tuple
from datetime import datetime


typdefContent = """

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

/**
 * @brief DID read callback function type
 * 
 * @param data      Output buffer to fill with DID data
 * @return Std_ReturnType E_OK if success, E_NOT_OK if failed
 * 
 * @note Callback must fill 'data' buffer with DID value
 *       Buffer size is guaranteed to be >= expected_length
 */
typedef Std_ReturnType (*uds_did_read_callback_t)(uint8_t *data);

/**
 * @brief DID write callback function type
 * 
 * @param data      Input data to write
 * @param length    Length of input data
 * @return Std_ReturnType E_OK if success, E_NOT_OK if failed
 * 
 * @note Callback must validate and process input data
 *       Length is pre-validated against expected_length range
 */
typedef Std_ReturnType (*uds_did_write_callback_t)(const uint8_t *data, ErrorCode_t * ErrorCode);

/**
 * @brief DID IO control callback function type (Future: Service 0x2F)
 * 
 * @param control_option    Control option parameter
 * @param control_param     Control parameter data
 * @param param_length      Length of control parameter
 * @param state_record      Output buffer for control state record
 * @param state_length      Output length of state record
 * @return Std_ReturnType E_OK if success, E_NOT_OK if failed
 */
typedef Std_ReturnType (*uds_did_io_control_callback_t)(
    uint8_t control_option,
    const uint8_t *control_param,
    uint16_t param_length,
    uint8_t *state_record,
    uint16_t *state_length
);

/**
 * @brief DID dynamic length getter function type
 * 
 * @return uint16_t Current length of DID data (for variable length DIDs)
 * 
 * @note Only used if expected_length = 0 (variable length)
 *       Return 0 if DID has no data available
 */
typedef uint16_t (*uds_did_length_getter_t)(void);

/**
 * @brief DID registry entry structure
 * 
 * This structure defines a complete DID configuration including:
 * - Basic properties (ID, length)
 * - Service-specific callbacks
 * - Service-specific access control (session/security)
 * - Data validation settings
 */
typedef struct {
    /* ===== Basic DID Properties ===== */
    uint16_t did;                           /**< Data Identifier (0x0000 - 0xFFFF) */
    uint16_t expected_length;               /**< Expected data length (0 = variable) */
    uint16_t min_length;                    /**< Minimum length (for variable DIDs) */
    uint16_t max_length;                    /**< Maximum length (for variable DIDs) */
    
    /* ===== Service 0x22 (Read Data By Identifier) ===== */
    struct {
        uds_did_read_callback_t callback;   /**< Read callback function */
        uds_did_length_getter_t length_getter; /**< Dynamic length getter (if variable) */
        uint32_t session_mask;              /**< Allowed sessions (UDS_SESSION_MASK_xxx) */
        uint32_t security_mask;             /**< Required security level (UDS_SECURITY_MASK_xxx) */
    } read_config;
    
    /* ===== Service 0x2E (Write Data By Identifier) ===== */
    struct {
        uds_did_write_callback_t callback;  /**< Write callback function */
        uint32_t session_mask;              /**< Allowed sessions */
        uint32_t security_mask;             /**< Required security level */
        bool semantic_validation;           /**< Enable semantic validation */
    } write_config;
    
    /* ===== Service 0x2F (Input Output Control By Identifier) - Future ===== */
    struct {
        uds_did_io_control_callback_t callback; /**< IO control callback */
        uint32_t session_mask;              /**< Allowed sessions */
        uint32_t security_mask;             /**< Required security level */
        uint8_t supported_options;          /**< Supported control options bitmask */
    } io_control_config;
    
} uds_did_entry_t;

"""

class DidValidator:
    """Validator for DID configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, dids: List[Dict]) -> Tuple[bool, List[str], List[str]]:
        """Validate DIDs - completely independent of NVM"""
        self.errors = []
        self.warnings = []
        
        if not dids:
            self.warnings.append("No DIDs defined")
            return (True, self.errors, self.warnings)
        
        did_values = set()
        did_names = set()
        
        for i, did in enumerate(dids):
            self._validate_did(i, did, did_values, did_names)
        
        return (len(self.errors) == 0, self.errors, self.warnings)
    
    def _validate_did(self, index: int, did: Dict, did_values: set, did_names: set):
        """Validate single DID - based on struct.md"""
        # DID identifier
        if 'did' not in did:
            self.errors.append(f"DID {index}: missing did")
        elif not isinstance(did['did'], str) or not did['did'].startswith('0x'):
            self.errors.append(f"DID {index}: did must be hex string (e.g., '0xF190')")
        elif did['did'] in did_values:
            self.errors.append(f"Duplicate DID: {did['did']}")
        else:
            did_values.add(did['did'])
        
        # DID name
        if 'did_name' not in did:
            self.errors.append(f"DID {index}: missing did_name")
        elif not did['did_name'] or not did['did_name'].isupper():
            self.errors.append(f"DID {index}: did_name must be uppercase")
        elif did['did_name'] in did_names:
            self.errors.append(f"Duplicate did_name: {did['did_name']}")
        else:
            did_names.add(did['did_name'])
        
        # Fixed length
        if 'fixed_length' not in did:
            did['fixed_length'] = True  # Default
        
        # Expected length
        if 'expected_length' not in did:
            self.errors.append(f"DID {index}: missing expected_length")
        
        # Min/Max for variable length
        if not did.get('fixed_length', True):
            if 'min_length' not in did:
                self.errors.append(f"DID {index}: variable DID needs min_length")
            if 'max_length' not in did:
                self.errors.append(f"DID {index}: variable DID needs max_length")
        
        # Read config
        if 'read_config' in did:
            if 'callback' not in did['read_config']:
                self.errors.append(f"DID {index}: read_config missing callback")
        
        # Write config
        if 'write_config' in did:
            if 'callback' not in did['write_config']:
                self.errors.append(f"DID {index}: write_config missing callback")


class DidCodeGenerator:
    """Code generator for DIDs based on actual source code structure"""
    
    def __init__(self, project_name: str, version: str):
        self.project_name = project_name
        self.version = version
    
    def generate_registry_header(self, dids: List[Dict]) -> str:
        """Generate DID_PBCfg.h"""
        content = self._file_header("DID_PBCfg.h", "DID Registry Declarations")
        content += "#ifndef DID_PBCFG_H\n"
        content += "#define DID_PBCFG_H\n\n"
        content += '#include <stdio.h>\n'
        content += '#include <stdint.h>\n'
        content += '#include <stdbool.h>\n\n'

        # Add typedefs
        content += typdefContent + "\n"
        # DID constants
        content += "// DID Identifiers\n"
        for did in dids:
            content += f"#define {did['did_name']}  {did['did']}\n"
        content += "\n"
        
        content += f"// Total DID count\n"
        content += f"#define UDS_DID_COUNT_GENERATED {len(dids)}\n\n"
        
        # Declare registry
        content += "// Generated DID Registry\n"
        content += "extern const uds_did_entry_t uds_did_registry_generated[UDS_DID_COUNT_GENERATED];\n\n"
        
        # Extern callback function declarations
        content += '\n\n'
        content += "/* ========================================================================== */\n"
        content += "/*                   Callback Function Declarations                           */\n"
        content += "/* ========================================================================== */\n"
        content += "// User must implement these callback functions\n\n"
        
        for did in dids:
            # Read callback
            if 'read_config' in did and did['read_config'].get('callback'):
                func_name = did['read_config']['callback']
                content += f"extern Std_ReturnType {func_name}(uint8_t *data);\n"
            
            # Length getter for variable length
            if 'read_config' in did and did['read_config'].get('length_getter'):
                length_getter = did['read_config']['length_getter'].strip()
                if length_getter:
                    content += f"extern uint16_t {length_getter}(void);\n"
            
            # Write callback
            if 'write_config' in did and did['write_config'].get('callback'):
                func_name = did['write_config']['callback']
                content += f"extern Std_ReturnType {func_name}(const uint8_t *data, ErrorCode_t * ErrorCode);\n"
        
        content += "\n#endif // DID_PBCFG_H\n"
        return content
    
    def generate_registry_source(self, dids: List[Dict], session_map: Dict = None, security_map: Dict = None) -> str:
        """Generate DID_PBCfg.c"""
        session_map = session_map or {}
        security_map = security_map or {}
        
        def calculate_session_mask(supported_sessions):
            """Calculate session mask from list of session names"""
            if not supported_sessions or not session_map:
                return 0
            mask = 0
            for session_name in supported_sessions:
                if session_name in session_map:
                    session = session_map[session_name]
                    value_str = session['session_value']
                    if value_str.startswith('0x') or value_str.startswith('0X'):
                        value = int(value_str, 16)
                    else:
                        value = int(value_str)
                    mask |= (1 << value)
            return mask
        
        def calculate_security_mask(required_security_levels):
            """Calculate security mask from list of security levels"""
            if not required_security_levels or not security_map:
                return 0
            mask = 0
            for level in required_security_levels:
                mask |= (1 << level)
            return mask
        
        content = self._file_header("DID_PBCfg.c", "DID Registry Implementation")
        content += '#include "DID_PBCfg.h"\n'
        content += '#include <stddef.h>\n\n'
        
        # Registry table
        content += "// DID Registry Table\n"
        content += "const uds_did_entry_t uds_did_registry_generated[UDS_DID_COUNT_GENERATED] = {\n"
        
        for i, did in enumerate(dids):
            content += f"    // {did.get('description', did['did_name'])}\n"
            content += f"    {{\n"
            content += f"        .did = {did['did']},\n"
            content += f"        .expected_length = {did.get('expected_length', 0)},\n"
            content += f"        .min_length = {did.get('min_length', 0)},\n"
            content += f"        .max_length = {did.get('max_length', 0)},\n"
            
            # Read config
            content += f"        .read_config = {{\n"
            if 'read_config' in did and did['read_config'].get('callback'):
                content += f"            .callback = {did['read_config']['callback']},\n"
                length_getter = did['read_config'].get('length_getter', '') or ''
                length_getter = length_getter.strip()
                content += f"            .length_getter = {length_getter if length_getter else 'NULL'},\n"
                
                # Calculate session_mask from supported_sessions
                supported_sessions = did['read_config'].get('supported_sessions', [])
                session_mask = calculate_session_mask(supported_sessions)
                content += f"            .session_mask = {session_mask},  /* {', '.join(supported_sessions) if supported_sessions else 'None'} */\n"
                
                # Calculate security_mask from required_security_levels
                required_security = did['read_config'].get('required_security_levels', [])
                security_mask = calculate_security_mask(required_security)
                security_comment = ', '.join([f"Level {lvl}" for lvl in required_security]) if required_security else 'None'
                content += f"            .security_mask = {security_mask}  /* {security_comment} */\n"
            else:
                content += f"            .callback = NULL,\n"
                content += f"            .length_getter = NULL,\n"
                content += f"            .session_mask = 0,\n"
                content += f"            .security_mask = 0\n"
            content += f"        }},\n"
            
            # Write config
            content += f"        .write_config = {{\n"
            if 'write_config' in did and did['write_config'].get('callback'):
                content += f"            .callback = {did['write_config']['callback']},\n"
                
                # Calculate session_mask from supported_sessions
                supported_sessions = did['write_config'].get('supported_sessions', [])
                session_mask = calculate_session_mask(supported_sessions)
                content += f"            .session_mask = {session_mask},  /* {', '.join(supported_sessions) if supported_sessions else 'None'} */\n"
                
                # Calculate security_mask from required_security_levels
                required_security = did['write_config'].get('required_security_levels', [])
                security_mask = calculate_security_mask(required_security)
                security_comment = ', '.join([f"Level {lvl}" for lvl in required_security]) if required_security else 'None'
                content += f"            .security_mask = {security_mask},  /* {security_comment} */\n"
                
                content += f"            .semantic_validation = {'true' if did['write_config'].get('semantic_validation', False) else 'false'}\n"
            else:
                content += f"            .callback = NULL,\n"
                content += f"            .session_mask = 0,\n"
                content += f"            .security_mask = 0,\n"
                content += f"            .semantic_validation = false\n"
            content += f"        }},\n"
            
            # IO control (future)
            content += f"        .io_control_config = {{\n"
            content += f"            .callback = NULL,\n"
            content += f"            .session_mask = 0,\n"
            content += f"            .security_mask = 0,\n"
            content += f"            .supported_options = 0\n"
            content += f"        }}\n"
            
            content += f"    }}"
            content += ",\n" if i < len(dids) - 1 else "\n"
        
        content += "};\n"
        
        return content
    
    def _file_header(self, filename: str, description: str) -> str:
        """Generate file header"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""/**
 * @file {filename}
 * @brief {description}
 * 
 * AUTO-GENERATED FILE - DO NOT EDIT MANUALLY!
 * Generated by: GachBoot ConfigTool (DID Module)
 * Project: {self.project_name} v{self.version}
 * Generated: {timestamp}
 */

"""
        return header


def validate_dids(dids: List[Dict]) -> Tuple[bool, List[str], List[str]]:
    """Convenience function to validate DIDs"""
    validator = DidValidator()
    return validator.validate(dids)


def generate_did_code(dids: List[Dict], sessions: List[Dict], security_levels: List[Dict], project_name: str, version: str, output_path: str):
    """Generate DID configuration files"""
    import os
    
    # Create session lookup map
    session_map = {s['session_name']: s for s in sessions}
    
    # Create security level lookup map
    security_map = {s['security_level']: s for s in security_levels}
    
    generator = DidCodeGenerator(project_name, version)
    
    # Generate files with session and security maps
    registry_h = generator.generate_registry_header(dids)
    registry_c = generator.generate_registry_source(dids, session_map, security_map)
    
    # Create DID_Gen subfolder
    did_output_path = os.path.join(output_path, "DID_Gen")
    os.makedirs(did_output_path, exist_ok=True)
    
    # Clean old files in DID_Gen folder
    for old_file in os.listdir(did_output_path):
        old_file_path = os.path.join(did_output_path, old_file)
        if os.path.isfile(old_file_path):
            os.remove(old_file_path)
    
    files = []
    for filename, content in [
        ("DID_PBCfg.h", registry_h),
        ("DID_PBCfg.c", registry_c)
    ]:
        filepath = os.path.join(did_output_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        files.append(filepath)
    
    return files
