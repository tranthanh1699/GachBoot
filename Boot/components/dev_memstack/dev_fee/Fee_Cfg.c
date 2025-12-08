/**
 * @file Fee_Cfg.c
 * @brief Flash EEPROM Emulation Configuration Implementation (CODE GENERATED)
 * 
 * This file contains the generated Fee sector mapping and configuration.
 * DO NOT EDIT MANUALLY - regenerate using configuration tool.
 * 
 * Generator: [YOUR_CONFIG_TOOL_NAME]
 * Generated: [TIMESTAMP]
 */

#include "Fee_Cfg.h"
#include "Fls_Cfg.h"  /* For Fls_Config reference */

/* ============================================================================
 * Generated Fee Sector Table
 * ============================================================================ */

/**
 * @brief Fee sector mapping
 * 
 * Configuration: 2 Fee sectors mapped to Fls sectors 0 and 1
 * Wear leveling: Ping-pong between these two sectors
 * 
 * Fee Sector 0 (Primary)   → Fls Sector 0 (Bank 2, Sector 6, 0x081C0000)
 * Fee Sector 1 (Secondary) → Fls Sector 1 (Bank 2, Sector 7, 0x081E0000)
 */
const Fee_SectorConfig_t Fee_SectorTable[] = {
    /* Fee Sector 0 - Primary */
    {
        .fls_sector_index = 0U,  /* Maps to Fls_SectorTable[0] */
        .is_primary = true,
        .name = "Fee_Primary"
    },
    
    /* Fee Sector 1 - Secondary */
    {
        .fls_sector_index = 1U,  /* Maps to Fls_SectorTable[1] */
        .is_primary = false,
        .name = "Fee_Secondary"
    }
};

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
const Fee_ConfigType Fee_Config = {
    .sector_table = Fee_SectorTable,
    .sector_count = sizeof(Fee_SectorTable) / sizeof(Fee_SectorConfig_t),
    .virtual_start = FEE_CFG_VIRTUAL_START,
    .virtual_size = FEE_CFG_VIRTUAL_SIZE,
    .sector_full_threshold = FEE_CFG_SECTOR_FULL_THRESHOLD,
    .write_alignment = FEE_CFG_WRITE_ALIGNMENT,
    .fls_config = &Fls_Config  /* Reference to Fls configuration */
};
