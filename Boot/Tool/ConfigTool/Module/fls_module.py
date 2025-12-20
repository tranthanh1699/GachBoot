#!/usr/bin/env python3
"""
Fls Module - Validation and Code Generation for Flash Driver Configuration
"""

from typing import Dict, List, Tuple
from datetime import datetime

# STM32H7 Flash constraints
STM32H7_FLASH_BASE = 0x08000000
STM32H7_FLASH_SIZE = 2 * 1024 * 1024  # 2MB
STM32H7_BANK_SIZE = 1024 * 1024  # 1MB per bank
STM32H7_SECTOR_SIZE = 128 * 1024  # 128KB per sector
STM32H7_SECTORS_PER_BANK = 8

class FlsValidator:
    """Validator for Fls configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, fls_config: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate Fls configuration"""
        self.errors = []
        self.warnings = []
        
        # Validate hardware parameters
        self._validate_hardware_params(fls_config)
        
        # Validate sectors
        if 'sectors' in fls_config and fls_config['sectors']:
            self._validate_sectors(fls_config['sectors'])
        else:
            self.warnings.append("No flash sectors defined")
        
        return (len(self.errors) == 0, self.errors, self.warnings)
    
    def _validate_hardware_params(self, config: Dict):
        """Validate hardware parameters"""
        # Base address
        base_addr = config.get('base_address', '')
        try:
            addr = int(base_addr, 16) if isinstance(base_addr, str) else base_addr
            if addr != STM32H7_FLASH_BASE:
                self.warnings.append(f"Base address {hex(addr)} differs from STM32H7 standard {hex(STM32H7_FLASH_BASE)}")
        except ValueError:
            self.errors.append(f"Invalid base address format: {base_addr}")
        
        # Total size
        total_size = config.get('total_size', 0)
        if total_size != STM32H7_FLASH_SIZE:
            self.warnings.append(f"Total size {total_size} differs from STM32H7 standard {STM32H7_FLASH_SIZE}")
        
        # Write alignment
        write_align = config.get('write_alignment', 0)
        if write_align not in [1, 2, 4, 8, 16, 32]:
            self.warnings.append(f"Unusual write alignment: {write_align} bytes")
        
        # Timeouts
        write_timeout = config.get('write_timeout_ms', 0)
        if write_timeout <= 0:
            self.errors.append("Write timeout must be positive")
        elif write_timeout < 10:
            self.warnings.append("Write timeout seems very short")
        
        erase_timeout = config.get('erase_timeout_ms', 0)
        if erase_timeout <= 0:
            self.errors.append("Erase timeout must be positive")
        elif erase_timeout < 100:
            self.warnings.append("Erase timeout seems very short for sector erase")
    
    def _validate_sectors(self, sectors: List[Dict]):
        """Validate sector configuration"""
        if not sectors:
            self.warnings.append("Empty sector list")
            return
        
        addresses = []
        
        for i, sector in enumerate(sectors):
            # Check required fields
            if 'start_address' not in sector:
                self.errors.append(f"Sector {i}: Missing start_address")
                continue
            if 'size' not in sector:
                self.errors.append(f"Sector {i}: Missing size")
                continue
            
            # Parse addresses
            try:
                start = int(sector['start_address'], 16) if isinstance(sector['start_address'], str) else sector['start_address']
                size = int(sector['size'], 16) if isinstance(sector['size'], str) else sector['size']
            except ValueError as e:
                self.errors.append(f"Sector {i}: Invalid address format - {e}")
                continue
            
            # Check alignment
            if start % STM32H7_SECTOR_SIZE != 0:
                self.warnings.append(f"Sector {i}: Start address {hex(start)} not sector-aligned for STM32H7")
            
            # Check size
            if size != STM32H7_SECTOR_SIZE:
                self.warnings.append(f"Sector {i}: Size {size} differs from standard STM32H7 sector size {STM32H7_SECTOR_SIZE}")
            
            # Check bank and sector index
            bank = sector.get('bank_index', 0)
            sector_idx = sector.get('sector_index', 0)
            
            if bank not in [1, 2]:
                self.errors.append(f"Sector {i}: Invalid bank index {bank} (must be 1 or 2)")
            
            if sector_idx >= STM32H7_SECTORS_PER_BANK:
                self.errors.append(f"Sector {i}: Invalid sector index {sector_idx} (must be 0-7)")
            
            # Check for overlaps
            end = start + size
            for prev_start, prev_end, prev_i in addresses:
                if not (end <= prev_start or start >= prev_end):
                    self.errors.append(f"Sector {i} overlaps with sector {prev_i}")
            
            addresses.append((start, end, i))
        
        # Check total coverage
        addresses.sort()
        if addresses:
            first_addr = addresses[0][0]
            last_addr = addresses[-1][1]
            
            if first_addr < STM32H7_FLASH_BASE:
                self.errors.append(f"Sector starts before flash base address")
            
            if last_addr > STM32H7_FLASH_BASE + STM32H7_FLASH_SIZE:
                self.errors.append(f"Sector extends beyond flash memory")


def validate_fls_config(config: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Validate Fls configuration
    
    Args:
        config: Full configuration dictionary with 'fls_config' key
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    fls_config = config.get('fls_config', {})
    validator = FlsValidator()
    return validator.validate(fls_config)


def generate_fls_code(config: Dict, output_dir: str) -> List[str]:
    """
    Generate Fls configuration C code
    
    Args:
        config: Full configuration dictionary
        output_dir: Output directory path
        
    Returns:
        List of generated file paths
    """
    import os
    
    fls_config = config.get('fls_config', {})
    if not fls_config:
        return []
    
    # Create output directory
    fls_gen_dir = os.path.join(output_dir, 'Fls_Gen')
    os.makedirs(fls_gen_dir, exist_ok=True)
    
    # Generate header
    header_content = generate_fls_header(fls_config, config)
    header_path = os.path.join(fls_gen_dir, 'Fls_PBCfg.h')
    with open(header_path, 'w', encoding='utf-8') as f:
        f.write(header_content)
    
    # Generate source
    source_content = generate_fls_source(fls_config, config)
    source_path = os.path.join(fls_gen_dir, 'Fls_PBCfg.c')
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(source_content)
    
    return [header_path, source_path]


def generate_fls_header(fls_config: Dict, config: Dict) -> str:
    """Generate Fls_PBCfg.h content"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = config.get('project', {}).get('name', 'Unknown')
    version = config.get('project', {}).get('version', '1.0.0')
    
    # Extract parameters with defaults
    base_addr = fls_config.get('base_address', '0x08000000')
    if isinstance(base_addr, int):
        base_addr = f"0x{base_addr:08X}"
    
    total_size = fls_config.get('total_size', STM32H7_FLASH_SIZE)
    write_align = fls_config.get('write_alignment', 32)
    read_align = fls_config.get('read_alignment', 1)
    erase_value = fls_config.get('erase_value', 0xFF)
    write_timeout = fls_config.get('write_timeout_ms', 100)
    erase_timeout = fls_config.get('erase_timeout_ms', 2000)
    
    mcu_name = fls_config.get('mcu_name', 'STM32H743VIT6')
    description = fls_config.get('description', 'Flash Driver Configuration')
    
    header = f'''/**
 * @file Fls_PBCfg.h
 * @brief Flash Driver Configuration (Post-Build) - Generated File
 * 
 * {description}
 * 
 * AUTO-GENERATED FILE - DO NOT EDIT MANUALLY!
 * Generated by: GachBoot ConfigTool (Flash Module)
 * Project: {project_name} v{version}
 * Generated: {timestamp}
 * 
 * AUTOSAR Standard: AUTOSAR_SWS_FlashDriver.pdf
 */

#ifndef FLS_PBCFG_H
#define FLS_PBCFG_H

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

/* ============================================================================
 * Configuration Parameters (Generated)
 * ============================================================================ */

/**
 * @brief MCU: {mcu_name}
 * Flash Memory: {total_size // (1024*1024)}MB ({base_addr} - 0x{int(base_addr, 16) + total_size - 1:08X})
 */

/* Hardware Constraints */
#define FLS_CFG_WRITE_ALIGNMENT         {write_align}U     /**< Flash write alignment */
#define FLS_CFG_READ_ALIGNMENT          {read_align}U      /**< Byte-aligned read */
#define FLS_CFG_ERASE_VALUE             0x{erase_value:02X}U   /**< NOR flash erased state */
#define FLS_CFG_BASE_ADDRESS            {base_addr}U  /**< Flash start address */
#define FLS_CFG_TOTAL_SIZE              ({total_size}U)  /**< Total flash size */

/* Performance Parameters */
#define FLS_CFG_WRITE_TIMEOUT_MS        {write_timeout}U    /**< Max write timeout */
#define FLS_CFG_ERASE_TIMEOUT_MS        {erase_timeout}U   /**< Max erase timeout per sector */

/* ============================================================================
 * Physical Sector Descriptors (Generated)
 * ============================================================================ */

/**
 * @brief Flash sector descriptor
 * 
 * Describes physical flash sector properties.
 * Each sector is independently erasable hardware unit.
 */
typedef struct {{
    uint32_t base_address;      /**< Physical start address */
    uint32_t size;              /**< Sector size in bytes */
    uint8_t  bank_index;        /**< Flash bank number (1 or 2) */
    uint8_t  sector_index;      /**< Hardware sector index within bank (0-7) */
    uint8_t  erase_value;       /**< Value after erase (0xFF for NOR flash) */
    const char *name;           /**< Human-readable sector name */
}} Fls_SectorDescriptor_t;

/**
 * @brief Complete flash configuration
 * 
 * Contains all generated configuration data.
 * Passed to Fls_Init() at runtime.
 */
typedef struct {{
    const Fls_SectorDescriptor_t *sector_table;    /**< Pointer to sector array */
    uint8_t sector_count;                          /**< Number of sectors */
    uint32_t write_alignment;                      /**< Write alignment requirement */
    uint32_t read_alignment;                       /**< Read alignment requirement */
    uint8_t erase_value;                           /**< Erase value */
    uint32_t write_timeout_ms;                     /**< Write timeout */
    uint32_t erase_timeout_ms;                     /**< Erase timeout */
}} Fls_ConfigType;

/* ============================================================================
 * Generated Configuration Instance
 * ============================================================================ */

/**
 * @brief Generated sector table
 * 
 * Configuration Summary:
 * - MCU: {mcu_name}
 * - Total Sectors: {len(fls_config.get('sectors', []))}
 * - Flash Base: {base_addr}
 * - Total Size: {total_size // (1024*1024)}MB
 */
extern const Fls_SectorDescriptor_t Fls_SectorTable[];
extern const uint8_t Fls_SectorCount;

/**
 * @brief Default configuration instance
 * 
 * Pre-configured with generated values.
 * Can be passed directly to Fls_Init().
 */
extern const Fls_ConfigType Fls_Config;

#endif /* FLS_PBCFG_H */
'''
    return header


def generate_fls_source(fls_config: Dict, config: Dict) -> str:
    """Generate Fls_PBCfg.c content"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    project_name = config.get('project', {}).get('name', 'Unknown')
    version = config.get('project', {}).get('version', '1.0.0')
    
    mcu_name = fls_config.get('mcu_name', 'STM32H743VIT6')
    sectors = fls_config.get('sectors', [])
    
    # Generate sector table entries
    sector_entries = []
    for i, sector in enumerate(sectors):
        start_addr = sector.get('start_address', '0x08000000')
        if isinstance(start_addr, int):
            start_addr = f"0x{start_addr:08X}U"
        elif isinstance(start_addr, str) and not start_addr.endswith('U'):
            start_addr = f"{start_addr}U"
        
        size = sector.get('size', 128 * 1024)
        if isinstance(size, str):
            size_str = f"{size}U"
        else:
            # Format size nicely (e.g., 128 * 1024)
            if size % 1024 == 0:
                size_str = f"{size // 1024}U * 1024U"
            else:
                size_str = f"{size}U"
        
        bank = sector.get('bank_index', 1)
        sector_idx = sector.get('sector_index', i)
        erase_val = sector.get('erase_value', 0xFF)
        name = sector.get('name', f"Sector_{i}")
        description = sector.get('description', '')
        
        comment = f"/* Sector {i} - Bank {bank}, Sector {sector_idx}"
        if description:
            comment += f" ({description})"
        comment += " */"
        
        entry = f'''    {comment}
    {{
        .base_address = {start_addr},
        .size = {size_str},
        .bank_index = {bank}U,
        .sector_index = {sector_idx}U,
        .erase_value = 0x{erase_val:02X}U,
        .name = "{name}"
    }}'''
        sector_entries.append(entry)
    
    sectors_table = ',\n    \n'.join(sector_entries) if sector_entries else '    /* No sectors configured */'
    
    # Generate comments about sector usage
    sector_summary = []
    for sector in sectors:
        start = sector.get('start_address', '0x00000000')
        if isinstance(start, int):
            start = f"0x{start:08X}"
        size = sector.get('size', 0)
        if isinstance(size, int):
            size_kb = size // 1024
        else:
            size_kb = int(size, 16) // 1024 if isinstance(size, str) else 0
        name = sector.get('name', 'Unnamed')
        description = sector.get('description', '')
        
        bank = sector.get('bank_index', 1)
        sector_idx = sector.get('sector_index', 0)
        
        line = f" * - Bank {bank}, Sector {sector_idx}: {start}"
        if size_kb > 0:
            end_addr = int(start, 16) + (size_kb * 1024) - 1
            line += f" - 0x{end_addr:08X} ({size_kb}KB)"
        line += f" [{name}]"
        if description:
            line += f" - {description}"
        sector_summary.append(line)
    
    summary_text = '\n'.join(sector_summary) if sector_summary else ' * No sectors configured'
    
    source = f'''/**
 * @file Fls_PBCfg.c
 * @brief Flash Driver Configuration Implementation (Post-Build)
 * 
 * AUTO-GENERATED FILE - DO NOT EDIT MANUALLY!
 * This file contains the generated sector table and configuration.
 * 
 * Generated by: GachBoot ConfigTool (Flash Module)
 * Project: {project_name} v{version}
 * Generated: {timestamp}
 * MCU: {mcu_name}
 */

#include "Fls_PBCfg.h"

/* ============================================================================
 * Generated Sector Table
 * ============================================================================ */

/**
 * @brief Physical sector descriptors
 * 
 * Flash Configuration:
{summary_text}
 * 
 * Total sectors: {len(sectors)}
 */
const Fls_SectorDescriptor_t Fls_SectorTable[] = {{
{sectors_table}
}};

const uint8_t Fls_SectorCount = sizeof(Fls_SectorTable) / sizeof(Fls_SectorDescriptor_t);

/* ============================================================================
 * Generated Configuration Instance
 * ============================================================================ */

/**
 * @brief Default Fls configuration
 * 
 * Pre-configured with all generated parameters.
 * Pass this to Fls_Init(&Fls_Config) to initialize the driver.
 */
const Fls_ConfigType Fls_Config = {{
    .sector_table = Fls_SectorTable,
    .sector_count = sizeof(Fls_SectorTable) / sizeof(Fls_SectorDescriptor_t),
    .write_alignment = FLS_CFG_WRITE_ALIGNMENT,
    .read_alignment = FLS_CFG_READ_ALIGNMENT,
    .erase_value = FLS_CFG_ERASE_VALUE,
    .write_timeout_ms = FLS_CFG_WRITE_TIMEOUT_MS,
    .erase_timeout_ms = FLS_CFG_ERASE_TIMEOUT_MS
}};
'''
    return source
