#!/usr/bin/env python3
"""
GachBoot Code Generator
Generate C/H files from JSON configuration (AUTOSAR-like approach)
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class CodeGenerator:
    def __init__(self, config_path: str):
        """Initialize generator with config file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.project_name = self.config['project']['name']
        self.version = self.config['project']['version']
        self.output_path = self.config['project']['generated_path']
        
    def generate_all(self):
        """Generate all configuration files"""
        print(f"=== {self.project_name} Code Generator v{self.version} ===")
        print(f"Generating configuration files...")
        
        # Create output directory
        os.makedirs(self.output_path, exist_ok=True)
        
        # Generate files
        self.generate_nvm_config()
        self.generate_did_registry()
        self.generate_did_callbacks()
        
        print(f"✓ Generation complete! Files written to: {self.output_path}")
    
    def generate_nvm_config(self):
        """Generate dev_nvm_config.h"""
        blocks = self.config['nvm_blocks']
        
        content = self._file_header("dev_nvm_config_generated.h", "NVM Block Configuration")
        content += "#ifndef DEV_NVM_CONFIG_GENERATED_H\n"
        content += "#define DEV_NVM_CONFIG_GENERATED_H\n\n"
        content += "#include <stdint.h>\n\n"
        
        # Block count
        content += f"// NVM Block Configuration (Generated from JSON)\n"
        content += f"#define DEV_NVM_BLOCK_COUNT {len(blocks)}\n\n"
        
        # Block IDs
        content += "// Block ID definitions\n"
        for block in blocks:
            content += f"#define {block['block_name']}_ID  {block['block_id']}\n"
        content += "\n"
        
        # Block structure array
        content += "// Block descriptors\n"
        content += "static const dev_nvm_block_descriptor_t nvm_block_descriptors[] = {\n"
        
        for i, block in enumerate(blocks):
            default_vals = ', '.join([f"0x{v:02X}" for v in block['default_value']])
            content += f"    // Block {i}: {block['description']}\n"
            content += f"    {{\n"
            content += f"        .block_id = {block['block_id']},\n"
            content += f"        .data_length = {block['data_length']},\n"
            content += f"        .default_data = (uint8_t[]){{{default_vals}}}\n"
            content += f"    }}"
            content += ",\n" if i < len(blocks) - 1 else "\n"
        
        content += "};\n\n"
        content += "#endif // DEV_NVM_CONFIG_GENERATED_H\n"
        
        self._write_file("dev_nvm_config_generated.h", content)
    
    def generate_did_registry(self):
        """Generate uds_did_registry_generated.c"""
        dids = self.config['dids']
        
        content = self._file_header("uds_did_registry_generated.c", "DID Registry Configuration")
        content += '#include "uds_did_registry.h"\n'
        content += '#include "uds_did_callbacks.h"\n'
        content += '#include "dcmdsl/dcmdsl.h"\n\n'
        
        # DID constants
        content += "// DID Identifiers\n"
        for did in dids:
            content += f"#define {did['did_name']}  {did['did']}\n"
        content += "\n"
        
        # Session mask helper
        content += "// Helper: Convert session array to bitmask\n"
        content += "static uint8_t session_to_mask(const char** sessions, int count) {\n"
        content += "    uint8_t mask = 0;\n"
        content += "    for (int i = 0; i < count; i++) {\n"
        content += "        if (strcmp(sessions[i], \"DEFAULT\") == 0) mask |= (1 << UDS_SESSION_DEFAULT);\n"
        content += "        if (strcmp(sessions[i], \"PROGRAMMING\") == 0) mask |= (1 << UDS_SESSION_PROGRAMMING);\n"
        content += "        if (strcmp(sessions[i], \"EXTENDED_DIAGNOSTIC\") == 0) mask |= (1 << UDS_SESSION_EXTENDED_DIAGNOSTIC);\n"
        content += "    }\n"
        content += "    return mask;\n"
        content += "}\n\n"
        
        # DID registry table
        content += "// DID Registry Table\n"
        content += "const uds_did_entry_t uds_did_registry[] = {\n"
        
        for i, did in enumerate(dids):
            content += f"    // {did['description']}\n"
            content += f"    {{\n"
            content += f"        .did = {did['did']},\n"
            content += f"        .data_length = {did['data_length']},\n"
            
            # Callbacks
            read_cb = f"uds_did_read_{did['did_name'].lower()}" if did['read_access'] else "NULL"
            write_cb = f"uds_did_write_{did['did_name'].lower()}" if did['write_access'] else "NULL"
            content += f"        .read_callback = {read_cb},\n"
            content += f"        .write_callback = {write_cb},\n"
            
            # Session and security
            sessions_str = ', '.join([f'"{s}"' for s in did['session_required']])
            content += f"        .session_mask = session_to_mask((const char*[]){{{sessions_str}}}, {len(did['session_required'])}),\n"
            content += f"        .security_level = {did['security_level']}\n"
            content += f"    }}"
            content += ",\n" if i < len(dids) - 1 else "\n"
        
        content += "};\n\n"
        content += f"const uint16_t uds_did_registry_count = {len(dids)};\n"
        
        self._write_file("uds_did_registry_generated.c", content)
    
    def generate_did_callbacks(self):
        """Generate uds_did_callbacks_generated.c/h"""
        dids = self.config['dids']
        nvm_blocks = {b['block_id']: b for b in self.config['nvm_blocks']}
        
        # Generate header
        h_content = self._file_header("uds_did_callbacks_generated.h", "DID Callback Declarations")
        h_content += "#ifndef UDS_DID_CALLBACKS_GENERATED_H\n"
        h_content += "#define UDS_DID_CALLBACKS_GENERATED_H\n\n"
        h_content += '#include "uds_did_registry.h"\n\n'
        
        # Generate C file
        c_content = self._file_header("uds_did_callbacks_generated.c", "DID Callback Implementations")
        c_content += '#include "uds_did_callbacks_generated.h"\n'
        c_content += '#include "dev_nvm.h"\n'
        c_content += '#include <string.h>\n\n'
        
        for did in dids:
            did_lower = did['did_name'].lower()
            
            # Read callback
            if did['read_access']:
                h_content += f"Std_ReturnType uds_did_read_{did_lower}(uint8_t *data, uint16_t *length);\n"
                
                c_content += f"// Read callback for {did['description']}\n"
                c_content += f"Std_ReturnType uds_did_read_{did_lower}(uint8_t *data, uint16_t *length) {{\n"
                
                if did['data_type'] == 'NVM':
                    block = nvm_blocks[did['nvm_block_id']]
                    c_content += f"    dev_err_t err = dev_nvm_read({block['block_name']}_ID, data, {did['data_length']});\n"
                    c_content += f"    if (err == DEV_OK) {{\n"
                    c_content += f"        *length = {did['data_length']};\n"
                    c_content += f"        return E_OK;\n"
                    c_content += f"    }}\n"
                    c_content += f"    return E_NOT_OK;\n"
                elif did['data_type'] == 'STATIC':
                    static_data = ', '.join([f"0x{v:02X}" for v in did['static_data']])
                    c_content += f"    static const uint8_t static_data[] = {{{static_data}}};\n"
                    c_content += f"    memcpy(data, static_data, {did['data_length']});\n"
                    c_content += f"    *length = {did['data_length']};\n"
                    c_content += f"    return E_OK;\n"
                else:  # DYNAMIC
                    c_content += f"    // TODO: Implement dynamic read logic\n"
                    c_content += f"    *length = {did['data_length']};\n"
                    c_content += f"    return E_OK;\n"
                
                c_content += "}\n\n"
            
            # Write callback
            if did['write_access']:
                h_content += f"Std_ReturnType uds_did_write_{did_lower}(const uint8_t *data, uint16_t length);\n"
                
                c_content += f"// Write callback for {did['description']}\n"
                c_content += f"Std_ReturnType uds_did_write_{did_lower}(const uint8_t *data, uint16_t length) {{\n"
                c_content += f"    if (length != {did['data_length']}) return E_NOT_OK;\n"
                
                if did['data_type'] == 'NVM':
                    block = nvm_blocks[did['nvm_block_id']]
                    c_content += f"    dev_err_t err = dev_nvm_write({block['block_name']}_ID, data, length);\n"
                    c_content += f"    return (err == DEV_OK) ? E_OK : E_NOT_OK;\n"
                else:
                    c_content += f"    // TODO: Implement write logic for {did['data_type']} type\n"
                    c_content += f"    return E_OK;\n"
                
                c_content += "}\n\n"
        
        h_content += "\n#endif // UDS_DID_CALLBACKS_GENERATED_H\n"
        
        self._write_file("uds_did_callbacks_generated.h", h_content)
        self._write_file("uds_did_callbacks_generated.c", c_content)
    
    def _file_header(self, filename: str, description: str) -> str:
        """Generate file header"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""/**
 * @file {filename}
 * @brief {description}
 * 
 * AUTO-GENERATED FILE - DO NOT EDIT MANUALLY!
 * Generated by: GachBoot ConfigTool
 * Project: {self.project_name} v{self.version}
 * Generated: {timestamp}
 */

"""
        return header
    
    def _write_file(self, filename: str, content: str):
        """Write generated content to file"""
        filepath = os.path.join(self.output_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Generated: {filename}")


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        config_file = "gachboot_config.json"
    else:
        config_file = sys.argv[1]
    
    if not os.path.exists(config_file):
        print(f"Error: Config file not found: {config_file}")
        sys.exit(1)
    
    try:
        generator = CodeGenerator(config_file)
        generator.generate_all()
    except Exception as e:
        print(f"Error during code generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
