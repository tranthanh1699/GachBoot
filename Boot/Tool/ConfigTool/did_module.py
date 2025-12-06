#!/usr/bin/env python3
"""
DID Module - Validation and Code Generation for DIDs
Independent of NVM - follows struct.md specification
"""

from typing import Dict, List, Tuple
from datetime import datetime

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
        content += '#include <stdint.h>\n'
        content += '#include "dev_common.h"\n'
        content += '#include "svc_dcm.h"\n'
        content += '#include <string.h>\n'

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
        
        content += "#endif // DID_PBCFG_H\n"
        return content
    
    def generate_registry_source(self, dids: List[Dict]) -> str:
        """Generate DID_PBCfg.c"""
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
                content += f"            .session_mask = {did['read_config'].get('session_mask', '0')},\n"
                content += f"            .security_mask = {did['read_config'].get('security_mask', '0')}\n"
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
                content += f"            .session_mask = {did['write_config'].get('session_mask', '0')},\n"
                content += f"            .security_mask = {did['write_config'].get('security_mask', '0')},\n"
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


def generate_did_code(dids: List[Dict], project_name: str, version: str, output_path: str):
    """Generate DID configuration files"""
    import os
    
    generator = DidCodeGenerator(project_name, version)
    
    # Generate files
    registry_h = generator.generate_registry_header(dids)
    registry_c = generator.generate_registry_source(dids)
    
    # Write files
    os.makedirs(output_path, exist_ok=True)
    
    files = []
    for filename, content in [
        ("DID_PBCfg.h", registry_h),
        ("DID_PBCfg.c", registry_c)
    ]:
        filepath = os.path.join(output_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        files.append(filepath)
    
    return files
