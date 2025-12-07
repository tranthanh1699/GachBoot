#!/usr/bin/env python3
"""
NVM Module - Validation and Code Generation for NVM Blocks
"""

from typing import Dict, List, Tuple
from datetime import datetime

nvmTypedefs = """

/**
 * @brief NVM Block Management Types (AUTOSAR-like)
 */

// NVM Block Management Type
typedef enum {
    DEV_NVM_BLOCK_NATIVE = 0,           // Single copy (no redundancy)
    DEV_NVM_BLOCK_REDUNDANT = 1         // Dual copy with CRC validation
} dev_nvm_block_type_t;


typedef struct {
    uint16_t block_id;                  // Unique block identifier
    uint16_t block_size;                // Data size in bytes
    const uint8_t *rom_address;         // Default ROM data (const array)
    uint8_t *ram_address;               // RAM mirror address
    dev_nvm_block_type_t block_type;    // Native or Redundant
    bool write_protection;              // Write protection flag
    bool use_crc;                       // Enable CRC validation
} dev_nvm_block_config_t;
"""

class NvmValidator:
    """Validator for NVM blocks configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, blocks: List[Dict]) -> Tuple[bool, List[str], List[str]]:
        """Validate NVM blocks"""
        self.errors = []
        self.warnings = []
        
        if not blocks:
            self.warnings.append("No NVM blocks defined")
            return (True, self.errors, self.warnings)
        
        block_ids = set()
        block_names = set()
        
        for i, block in enumerate(blocks):
            self._validate_block(i, block, block_ids, block_names)
        
        return (len(self.errors) == 0, self.errors, self.warnings)
    
    def _validate_block(self, index: int, block: Dict, block_ids: set, block_names: set):
        """Validate single NVM block"""
        # Block ID
        if 'block_id' not in block:
            self.errors.append(f"Block {index}: missing block_id")
        elif not isinstance(block['block_id'], int) or block['block_id'] < 0:
            self.errors.append(f"Block {index}: block_id must be non-negative integer")
        elif block['block_id'] in block_ids:
            self.errors.append(f"Duplicate block_id: {block['block_id']}")
        else:
            block_ids.add(block['block_id'])
        
        # Block Name
        if 'block_name' not in block:
            self.errors.append(f"Block {index}: missing block_name")
        elif not block['block_name'] or not block['block_name'].isupper():
            self.errors.append(f"Block {index}: block_name must be uppercase")
        elif block['block_name'] in block_names:
            self.errors.append(f"Duplicate block_name: {block['block_name']}")
        else:
            block_names.add(block['block_name'])
        
        # Data Length (block_size)
        if 'block_size' not in block:
            self.errors.append(f"Block {index}: missing block_size")
        elif not isinstance(block['block_size'], int) or block['block_size'] <= 0:
            self.errors.append(f"Block {index}: block_size must be positive integer")
        elif block['block_size'] > 256:
            self.warnings.append(f"Block {index}: block_size > 256 bytes (large block)")
        
        # Block Type
        if 'block_type' not in block:
            self.errors.append(f"Block {index}: missing block_type")
        elif block['block_type'] not in ['NATIVE', 'REDUNDANT']:
            self.errors.append(f"Block {index}: block_type must be NATIVE or REDUNDANT")
        
        # ROM Address (array name)
        if 'rom_data' not in block:
            self.errors.append(f"Block {index}: missing rom_data")
        elif not isinstance(block['rom_data'], str):
            self.errors.append(f"Block {index}: rom_data must be a string (array name)")
        elif not block['rom_data'].strip():
            self.errors.append(f"Block {index}: rom_data cannot be empty")
        
        # RAM Address (array name, optional)
        if 'ram_data' in block:
            if not isinstance(block['ram_data'], str):
                self.errors.append(f"Block {index}: ram_data must be a string (array name)")
            elif not block['ram_data'].strip():
                self.warnings.append(f"Block {index}: ram_data is empty, will auto-generate")
        
        # Write Protection
        if 'write_protection' not in block:
            block['write_protection'] = False  # Default
        elif not isinstance(block['write_protection'], bool):
            self.errors.append(f"Block {index}: write_protection must be boolean")
        
        # Use CRC
        if 'use_crc' not in block:
            block['use_crc'] = True  # Default
        elif not isinstance(block['use_crc'], bool):
            self.errors.append(f"Block {index}: use_crc must be boolean")


class NvmCodeGenerator:
    """Code generator for NVM blocks"""
    
    def __init__(self, project_name: str, version: str):
        self.project_name = project_name
        self.version = version
    
    def generate_header(self, blocks: List[Dict]) -> str:
        """Generate NvM_PBCfg.h"""
        content = self._file_header("NvM_PBCfg.h", "NVM Block Configuration Declarations")
        content += "#ifndef NVM_PBCFG_H\n"
        content += "#define NVM_PBCFG_H\n\n"
        content += '#include <stdio.h>' + "\n"
        content += '#include <stdint.h>' + "\n"
        content += '#include <stdbool.h>' + "\n" + "\n"
        
        # Add typedefs
        content += nvmTypedefs + "\n"
        
        # Block count
        content += f"// NVM Block Configuration\n"
        content += f"#define DEV_NVM_MAX_BLOCKS {len(blocks)}\n\n"
        
        # Block IDs
        content += "// Block ID Definitions\n"
        for block in blocks:
            content += f"#define {block['block_name']}  0x{block['block_id']:04X}\n"
        content += "\n"
        
        # Block config table
        content += "// Block Configuration Table\n"
        content += "extern const dev_nvm_block_config_t dev_nvm_block_config_table[DEV_NVM_MAX_BLOCKS];\n"
        content += "extern const uint16_t dev_nvm_block_config_count;\n\n"
        
        content += "#endif // NVM_PBCFG_H\n"
        
        return content
    
    def generate_source(self, blocks: List[Dict]) -> str:
        """Generate NvM_PBCfg.c"""
        content = self._file_header("NvM_PBCfg.c", "NVM Block Configuration Implementation")
        content += '#include "NvM_PBCfg.h"\n'
        content += '#include <stddef.h>\n\n'
        
        # External declarations for user-provided arrays
        content += "// External Array Declarations (defined by user)\n"
        for block in blocks:
            # ROM array - must be provided
            rom_array = block['rom_data']
            content += f"extern const uint8_t {rom_array}[{block['block_size']}];\n"
            
            # RAM array - check if provided
            ram_array = block.get('ram_data', '') or ''
            ram_array = ram_array.strip()
            if ram_array:
                content += f"extern uint8_t {ram_array}[{block['block_size']}];\n"
            else:
                # Auto-generate RAM array name
                content += f"uint8_t nvm_ram_{block['block_name'].lower()}[{block['block_size']}];\n"
        content += "\n"
        
        # Block configuration table
        content += "// Block Configuration Table\n"
        content += "const dev_nvm_block_config_t dev_nvm_block_config_table[DEV_NVM_MAX_BLOCKS] = {\n"
        
        for i, block in enumerate(blocks):
            block_type = f"DEV_NVM_BLOCK_{block['block_type']}"
            rom_array = block['rom_data']
            ram_array = block.get('ram_data', '') or ''
            ram_array = ram_array.strip() or f"nvm_ram_{block['block_name'].lower()}"
            
            content += f"    // {block.get('description', 'No description')}\n"
            content += f"    {{\n"
            content += f"        .block_id = {block['block_name']},\n"
            content += f"        .block_size = {block['block_size']},\n"
            content += f"        .rom_address = {rom_array},\n"
            content += f"        .ram_address = {ram_array},\n"
            content += f"        .block_type = {block_type},\n"
            content += f"        .write_protection = {'true' if block.get('write_protection', False) else 'false'},\n"
            content += f"        .use_crc = {'true' if block.get('use_crc', True) else 'false'}\n"
            content += f"    }}"
            content += ",\n" if i < len(blocks) - 1 else "\n"
        
        content += "};\n\n"
        content += f"const uint16_t dev_nvm_block_config_count = DEV_NVM_MAX_BLOCKS;\n"
        
        return content
    
    def _file_header(self, filename: str, description: str) -> str:
        """Generate file header"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""/**
 * @file {filename}
 * @brief {description}
 * 
 * AUTO-GENERATED FILE - DO NOT EDIT MANUALLY!
 * Generated by: GachBoot ConfigTool (NVM Module)
 * Project: {self.project_name} v{self.version}
 * Generated: {timestamp}
 */

"""
        return header


def validate_nvm_blocks(blocks: List[Dict]) -> Tuple[bool, List[str], List[str]]:
    """Convenience function to validate NVM blocks"""
    validator = NvmValidator()
    return validator.validate(blocks)


def generate_nvm_code(blocks: List[Dict], project_name: str, version: str, output_path: str):
    """Generate NVM configuration files"""
    import os
    
    generator = NvmCodeGenerator(project_name, version)
    
    # Generate header and source
    header_content = generator.generate_header(blocks)
    source_content = generator.generate_source(blocks)
    
    # Create NvM_Gen subfolder
    nvm_output_path = os.path.join(output_path, "NvM_Gen")
    os.makedirs(nvm_output_path, exist_ok=True)
    
    # Clean old files in NvM_Gen folder
    for old_file in os.listdir(nvm_output_path):
        old_file_path = os.path.join(nvm_output_path, old_file)
        if os.path.isfile(old_file_path):
            os.remove(old_file_path)
    
    header_file = os.path.join(nvm_output_path, "NvM_PBCfg.h")
    source_file = os.path.join(nvm_output_path, "NvM_PBCfg.c")
    
    with open(header_file, 'w', encoding='utf-8') as f:
        f.write(header_content)
    
    with open(source_file, 'w', encoding='utf-8') as f:
        f.write(source_content)
    
    return [header_file, source_file]


if __name__ == "__main__":
    # Test validation
    test_blocks = [
        {
            "block_id": 0,
            "block_name": "NVM_BLOCK_VIN",
            "data_length": 4,
            "default_value": [0x11, 0x22, 0x33, 0x44],
            "description": "Vehicle Identification Number"
        }
    ]
    
    is_valid, errors, warnings = validate_nvm_blocks(test_blocks)
    
    if warnings:
        print("Warnings:", warnings)
    if errors:
        print("Errors:", errors)
    else:
        print("✓ NVM blocks valid")
        
        # Test generation
        files = generate_nvm_code(test_blocks, "TestProject", "1.0.0", "./test_output")
        print(f"Generated: {files}")
