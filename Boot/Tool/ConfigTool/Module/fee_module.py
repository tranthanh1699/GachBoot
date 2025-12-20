#!/usr/bin/env python3
"""
Fee Module - Validation and Code Generation for Flash EEPROM Emulation Configuration

This module handles Fee (Flash EEPROM Emulation) layer configuration:
- Virtual address space management
- Sector mapping to Fls physical sectors
- Wear leveling parameters
- Write alignment configuration
"""

from typing import Dict, List, Tuple
from datetime import datetime
import os

# Fee constraints
FEE_MIN_VIRTUAL_SIZE = 1024  # 1KB minimum
FEE_MAX_VIRTUAL_SIZE = 512 * 1024  # 512KB maximum
FEE_MIN_SECTORS = 2  # Need at least 2 sectors for wear leveling
FEE_MAX_SECTORS = 8  # Reasonable maximum


class FeeValidator:
    """Validator for Fee configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, fee_config: Dict, fls_config: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Fee configuration
        
        Args:
            fee_config: Fee configuration dictionary
            fls_config: Fls configuration dictionary (for sector validation)
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Validate virtual address space
        self._validate_virtual_space(fee_config)
        
        # Validate wear leveling parameters
        self._validate_wear_leveling(fee_config)
        
        # Validate sector mapping
        if 'sector_mapping' in fee_config and fee_config['sector_mapping']:
            self._validate_sector_mapping(fee_config['sector_mapping'], fls_config)
        else:
            self.errors.append("No Fee sector mapping defined")
        
        # Validate write alignment
        self._validate_write_alignment(fee_config, fls_config)
        
        return (len(self.errors) == 0, self.errors, self.warnings)
    
    def _validate_virtual_space(self, config: Dict):
        """Validate virtual address space configuration"""
        virtual_start_raw = config.get('virtual_start', 0)
        virtual_size = config.get('virtual_size', 0)
        
        # Parse virtual_start (could be string or int)
        try:
            if isinstance(virtual_start_raw, str):
                virtual_start = int(virtual_start_raw, 16) if virtual_start_raw.startswith('0x') else int(virtual_start_raw)
            else:
                virtual_start = virtual_start_raw
        except ValueError:
            self.errors.append(f"Invalid virtual_start format: {virtual_start_raw}")
            return
        
        # Validate start address
        if virtual_start != 0:
            self.warnings.append(f"Virtual start address is {hex(virtual_start)}, typically should be 0x00000000")
        
        # Validate size
        if virtual_size < FEE_MIN_VIRTUAL_SIZE:
            self.errors.append(f"Virtual size {virtual_size} is below minimum {FEE_MIN_VIRTUAL_SIZE}")
        elif virtual_size > FEE_MAX_VIRTUAL_SIZE:
            self.errors.append(f"Virtual size {virtual_size} exceeds maximum {FEE_MAX_VIRTUAL_SIZE}")
        
        # Check if size is power of 2 or nice round number
        if virtual_size > 0 and (virtual_size & (virtual_size - 1)) != 0:
            if virtual_size % 1024 != 0:
                self.warnings.append(f"Virtual size {virtual_size} is not aligned to 1KB boundary")
    
    def _validate_wear_leveling(self, config: Dict):
        """Validate wear leveling parameters"""
        threshold = config.get('sector_full_threshold', 0)
        virtual_size = config.get('virtual_size', 0)
        
        if threshold <= 0:
            self.errors.append("Sector full threshold must be positive")
            return
        
        if virtual_size > 0:
            if threshold > virtual_size:
                self.errors.append(f"Sector full threshold {threshold} exceeds virtual size {virtual_size}")
            elif threshold < virtual_size * 0.8:
                self.warnings.append(f"Sector full threshold {threshold} is less than 80% of virtual size, may cause frequent sector switches")
            
            # Warn if no margin for metadata
            margin = virtual_size - threshold
            if margin < 1024:
                self.warnings.append(f"Only {margin} bytes margin for sector metadata, recommend at least 1KB")
    
    def _validate_sector_mapping(self, sector_mapping: List[Dict], fls_config: Dict):
        """Validate Fee sector mapping to Fls sectors"""
        if not sector_mapping:
            self.errors.append("Empty sector mapping")
            return
        
        # Check minimum sectors for wear leveling
        if len(sector_mapping) < FEE_MIN_SECTORS:
            self.errors.append(f"Need at least {FEE_MIN_SECTORS} sectors for wear leveling, found {len(sector_mapping)}")
        
        # Check maximum sectors
        if len(sector_mapping) > FEE_MAX_SECTORS:
            self.warnings.append(f"Large number of sectors ({len(sector_mapping)}) may impact performance")
        
        # Get available Fls sectors
        fls_sectors = fls_config.get('sectors', [])
        fls_sector_indices = {i for i in range(len(fls_sectors))}
        
        used_fls_indices = set()
        primary_count = 0
        
        for i, mapping in enumerate(sector_mapping):
            # Check required fields
            if 'fls_sector_index' not in mapping:
                self.errors.append(f"Fee sector {i}: Missing fls_sector_index")
                continue
            
            fls_idx = mapping['fls_sector_index']
            is_primary = mapping.get('is_primary', False)
            
            # Check if Fls sector exists
            if fls_idx not in fls_sector_indices:
                self.errors.append(f"Fee sector {i}: Fls sector index {fls_idx} does not exist")
                continue
            
            # Check for duplicate mapping
            if fls_idx in used_fls_indices:
                self.errors.append(f"Fee sector {i}: Fls sector {fls_idx} already mapped")
            used_fls_indices.add(fls_idx)
            
            # Check name
            if 'name' not in mapping or not mapping['name']:
                self.warnings.append(f"Fee sector {i}: Missing or empty name")
            
            # Count primary sectors
            if is_primary:
                primary_count += 1
        
        # Warn if no primary sector or multiple primary sectors
        if primary_count == 0:
            self.warnings.append("No primary Fee sector defined, will use first sector as default")
        elif primary_count > 1:
            self.warnings.append(f"Multiple primary sectors defined ({primary_count}), only first will be used")
    
    def _validate_write_alignment(self, fee_config: Dict, fls_config: Dict):
        """Validate write alignment matches Fls"""
        fee_align = fee_config.get('write_alignment', 1)
        fls_align = fls_config.get('write_alignment', 1)
        
        if fee_align != fls_align:
            self.errors.append(f"Fee write alignment ({fee_align}) must match Fls write alignment ({fls_align})")
        
        # Check alignment is power of 2
        if fee_align > 0 and (fee_align & (fee_align - 1)) != 0:
            self.errors.append(f"Write alignment {fee_align} must be power of 2")


def validate_fee_config(config: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Validate Fee configuration
    
    Args:
        config: Full configuration dictionary with 'fee_config' and 'fls_config' keys
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    fee_config = config.get('fee_config', {})
    fls_config = config.get('fls_config', {})
    
    validator = FeeValidator()
    return validator.validate(fee_config, fls_config)


def generate_fee_code(config: Dict, output_path: str) -> List[str]:
    """
    Generate Fee configuration code (Fee_PBCfg.h and Fee_PBCfg.c)
    
    Args:
        config: Full configuration dictionary
        output_path: Base output directory (GenerateCode/)
        
    Returns:
        List of generated file paths
    """
    fee_config = config.get('fee_config', {})
    project = config.get('project', {})
    
    # Create Fee_Gen directory
    fee_gen_dir = os.path.join(output_path, 'Fee_Gen')
    os.makedirs(fee_gen_dir, exist_ok=True)
    
    # Generate header and source
    header_path = os.path.join(fee_gen_dir, 'Fee_PBCfg.h')
    source_path = os.path.join(fee_gen_dir, 'Fee_PBCfg.c')
    
    header_content = generate_fee_header(fee_config, project)
    source_content = generate_fee_source(fee_config, project)
    
    with open(header_path, 'w', encoding='utf-8') as f:
        f.write(header_content)
    
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(source_content)
    
    return [header_path, source_path]


def generate_fee_header(fee_config: Dict, project: Dict) -> str:
    """Generate Fee_PBCfg.h content"""
    
    project_name = project.get('name', 'GachBoot')
    project_version = project.get('version', '1.0.0')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Extract configuration
    virtual_start_raw = fee_config.get('virtual_start', 0)
    virtual_size = fee_config.get('virtual_size', 128 * 1024)
    sector_full_threshold = fee_config.get('sector_full_threshold', 127 * 1024)
    write_alignment = fee_config.get('write_alignment', 32)
    erase_value = fee_config.get('erase_value', 0xFF)
    sector_mapping = fee_config.get('sector_mapping', [])
    
    # Parse virtual_start (could be string or int)
    if isinstance(virtual_start_raw, str):
        virtual_start = int(virtual_start_raw, 16) if virtual_start_raw.startswith('0x') else int(virtual_start_raw)
    else:
        virtual_start = virtual_start_raw
    
    header = f"""/**
 * @file Fee_PBCfg.h
 * @brief Flash EEPROM Emulation Configuration (Post-Build) - Generated File
 * 
 * AUTO-GENERATED FILE - DO NOT EDIT MANUALLY!
 * Generated by: {project_name} ConfigTool (Fee Module)
 * Project: {project_name} v{project_version}
 * Generated: {timestamp}
 * 
 * This file contains Fee (Flash EEPROM Emulation) configuration:
 * - Virtual address space definition
 * - Sector mapping to Fls physical sectors
 * - Wear leveling parameters
 * - Write alignment settings
 */

#ifndef FEE_PBCFG_H
#define FEE_PBCFG_H

#ifdef __cplusplus
extern "C" {{
#endif

#include <stdint.h>
#include <stdbool.h>

/* ============================================================================
 * Virtual Address Space Configuration (Generated)
 * ============================================================================ */

/**
 * @brief Fee provides continuous virtual address space for NvM
 * 
 * Virtual space: {hex(virtual_start)} - {hex(virtual_start + virtual_size - 1)} ({virtual_size // 1024}KB)
 * Physical space: Ping-pongs between Fee sectors for wear leveling
 * 
 * NvM sees only virtual addresses.
 * Fee transparently maps virtual → physical.
 */
#define FEE_CFG_VIRTUAL_START           {hex(virtual_start)}     /**< Virtual address start */
#define FEE_CFG_VIRTUAL_SIZE            ({virtual_size}U)        /**< {virtual_size // 1024}KB virtual space */
#define FEE_CFG_VIRTUAL_END             (FEE_CFG_VIRTUAL_START + FEE_CFG_VIRTUAL_SIZE - 1U)

/* ============================================================================
 * Wear Leveling Configuration (Generated)
 * ============================================================================ */

/**
 * @brief Sector switch threshold
 * 
 * When active sector usage exceeds this threshold, Fee switches to alternate sector.
 * Leave margin for sector header and metadata.
 */
#define FEE_CFG_SECTOR_FULL_THRESHOLD   ({sector_full_threshold}U)  /**< {sector_full_threshold // 1024}KB (leave {(virtual_size - sector_full_threshold) // 1024}KB margin) */

/**
 * @brief Write alignment
 * 
 * Must match Fls write alignment requirement.
 * All Fee writes are aligned to this boundary.
 */
#define FEE_CFG_WRITE_ALIGNMENT         {write_alignment}U             /**< {write_alignment} bytes */

/**
 * @brief Erase value
 * 
 * Value of erased flash memory (typically 0xFF for NOR flash).
 */
#define FEE_CFG_ERASE_VALUE             {hex(erase_value)}           /**< Erased flash value */

/* ============================================================================
 * Fee Sector Configuration (Generated)
 * ============================================================================ */

/**
 * @brief Fee sector descriptor
 * 
 * Maps Fee logical sectors to physical Fls sectors.
 * Fee ping-pongs between these sectors for wear leveling.
 */
typedef struct {{
    uint8_t fls_sector_index;       /**< Index in Fls_SectorTable[] */
    bool is_primary;                /**< Primary sector flag (used first) */
    const char *name;               /**< Human-readable name */
}} Fee_SectorConfig_t;

/**
 * @brief Complete Fee configuration
 * 
 * Contains all generated configuration data.
 * Passed to Fee_Init() at runtime.
 */
typedef struct {{
    const Fee_SectorConfig_t *sector_table;     /**< Pointer to Fee sector array */
    uint8_t sector_count;                       /**< Number of Fee sectors */
    uint32_t virtual_start;                     /**< Virtual address start */
    uint32_t virtual_size;                      /**< Virtual address space size */
    uint32_t sector_full_threshold;             /**< Sector switch threshold */
    uint32_t write_alignment;                   /**< Write alignment */
    uint8_t erase_value;                        /**< Erased flash value */
}} Fee_ConfigType;

/* ============================================================================
 * Generated Configuration Instances
 * ============================================================================ */

/**
 * @brief Fee sector table
 * 
 * Maps {len(sector_mapping)} Fee logical sector{'s' if len(sector_mapping) != 1 else ''} to Fls physical sectors.
 * Fee alternates between these for wear leveling.
 */
extern const Fee_SectorConfig_t Fee_SectorTable[];
extern const uint8_t Fee_SectorCount;

/**
 * @brief Default Fee configuration
 * 
 * Pre-configured with generated values.
 * Pass to Fee_Init(&Fee_Config) to initialize.
 */
extern const Fee_ConfigType Fee_Config;

#ifdef __cplusplus
}}
#endif

#endif /* FEE_PBCFG_H */
"""
    
    return header


def generate_fee_source(fee_config: Dict, project: Dict) -> str:
    """Generate Fee_PBCfg.c content"""
    
    project_name = project.get('name', 'GachBoot')
    project_version = project.get('version', '1.0.0')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Extract configuration
    virtual_start_raw = fee_config.get('virtual_start', 0)
    virtual_size = fee_config.get('virtual_size', 128 * 1024)
    sector_full_threshold = fee_config.get('sector_full_threshold', 127 * 1024)
    write_alignment = fee_config.get('write_alignment', 32)
    erase_value = fee_config.get('erase_value', 0xFF)
    sector_mapping = fee_config.get('sector_mapping', [])
    
    # Parse virtual_start (could be string or int)
    if isinstance(virtual_start_raw, str):
        virtual_start = int(virtual_start_raw, 16) if virtual_start_raw.startswith('0x') else int(virtual_start_raw)
    else:
        virtual_start = virtual_start_raw
    
    # Generate sector table entries
    sector_entries = []
    for i, mapping in enumerate(sector_mapping):
        fls_idx = mapping.get('fls_sector_index', 0)
        is_primary = mapping.get('is_primary', False)
        name = mapping.get('name', f'Fee_Sector_{i}')
        
        comment = f"/* Fee Sector {i}"
        if is_primary:
            comment += " - Primary"
        comment += " */"
        
        entry = f"""    {comment}
    {{
        .fls_sector_index = {fls_idx}U,  /* Maps to Fls_SectorTable[{fls_idx}] */
        .is_primary = {'true' if is_primary else 'false'},
        .name = "{name}"
    }}"""
        sector_entries.append(entry)
    
    sectors_str = ',\n    \n'.join(sector_entries)
    
    source = f"""/**
 * @file Fee_PBCfg.c
 * @brief Flash EEPROM Emulation Configuration Implementation (Post-Build)
 * 
 * AUTO-GENERATED FILE - DO NOT EDIT MANUALLY!
 * Generated by: {project_name} ConfigTool (Fee Module)
 * Project: {project_name} v{project_version}
 * Generated: {timestamp}
 * 
 * This file contains the Fee sector mapping and configuration implementation.
 */

#include "Fee_PBCfg.h"

/* ============================================================================
 * Generated Fee Sector Table
 * ============================================================================ */

/**
 * @brief Fee sector mapping
 * 
 * Configuration: {len(sector_mapping)} Fee sector{'s' if len(sector_mapping) != 1 else ''}
 * Wear leveling: Ping-pong between these sectors
 */
const Fee_SectorConfig_t Fee_SectorTable[] = {{
{sectors_str}
}};

const uint8_t Fee_SectorCount = sizeof(Fee_SectorTable) / sizeof(Fee_SectorConfig_t);

/* ============================================================================
 * Generated Fee Configuration Instance
 * ============================================================================ */

/**
 * @brief Default Fee configuration
 * 
 * Pre-configured with all generated parameters.
 * Pass this to Fee_Init(&Fee_Config) to initialize the driver.
 */
const Fee_ConfigType Fee_Config = {{
    .sector_table = Fee_SectorTable,
    .sector_count = sizeof(Fee_SectorTable) / sizeof(Fee_SectorConfig_t),
    .virtual_start = FEE_CFG_VIRTUAL_START,
    .virtual_size = FEE_CFG_VIRTUAL_SIZE,
    .sector_full_threshold = FEE_CFG_SECTOR_FULL_THRESHOLD,
    .write_alignment = FEE_CFG_WRITE_ALIGNMENT,
    .erase_value = FEE_CFG_ERASE_VALUE
}};

/* End of generated Fee configuration */
"""
    
    return source
