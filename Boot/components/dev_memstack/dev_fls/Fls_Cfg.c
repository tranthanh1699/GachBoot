/**
 * @file Fls_Cfg.c
 * @brief Flash Driver Configuration Implementation (CODE GENERATED)
 * 
 * This file contains the generated sector table and configuration.
 * DO NOT EDIT MANUALLY - regenerate using configuration tool.
 * 
 * Generator: [YOUR_CONFIG_TOOL_NAME]
 * Generated: [TIMESTAMP]
 * MCU: STM32H743VIT6
 */

#include "Fls_Cfg.h"

/* ============================================================================
 * Generated Sector Table
 * ============================================================================ */

/**
 * @brief Physical sector descriptors
 * 
 * Configuration: NVM storage on Bank 2, Sectors 6-7
 * Total capacity: 256KB (2 x 128KB sectors)
 * Purpose: Wear-leveling storage for Fee layer
 */
const Fls_SectorDescriptor_t Fls_SectorTable[] = {
    /* Sector Index 0 - Bank 2, Sector 6 (NVM_Sector_A) */
    {
        .base_address = 0x081C0000U,
        .size = 128U * 1024U,
        .bank_index = 2U,
        .sector_index = 6U,
        .erase_value = 0xFFU,
        .name = "NVM_Sector_A"
    },
    
    /* Sector Index 1 - Bank 2, Sector 7 (NVM_Sector_B) */
    {
        .base_address = 0x081E0000U,
        .size = 128U * 1024U,
        .bank_index = 2U,
        .sector_index = 7U,
        .erase_value = 0xFFU,
        .name = "NVM_Sector_B"
    }
};

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
const Fls_ConfigType Fls_Config = {
    .sector_table = Fls_SectorTable,
    .sector_count = sizeof(Fls_SectorTable) / sizeof(Fls_SectorDescriptor_t),
    .write_alignment = FLS_CFG_WRITE_ALIGNMENT,
    .read_alignment = FLS_CFG_READ_ALIGNMENT,
    .erase_value = FLS_CFG_ERASE_VALUE,
    .write_timeout_ms = FLS_CFG_WRITE_TIMEOUT_MS,
    .erase_timeout_ms = FLS_CFG_ERASE_TIMEOUT_MS
};
