/**
 * @file Memory_Layout_Config.h
 * @brief Memory Layout Configuration
 * @date Generated on 2025-12-27 21:38:25
 * 
 * Auto-generated from gachboot_config.json
 * DO NOT EDIT MANUALLY
 */

#ifndef MEMORY_LAYOUT_CONFIG_H
#define MEMORY_LAYOUT_CONFIG_H

#include <stdint.h>

/* ========================================================================== */
/*                         Bootloader Region                                  */
/* ========================================================================== */

#define BOOTLOADER_START_ADDRESS        0x08000000U    /* Bootloader: Bootloader firmware region */
#define BOOTLOADER_SIZE                 0x00040000U
#define BOOTLOADER_END_ADDRESS          (BOOTLOADER_START_ADDRESS + BOOTLOADER_SIZE - 1)

/* ========================================================================== */
/*                         Application Region                                 */
/* ========================================================================== */

#define APPLICATION_START_ADDRESS       0x08100000U   /* Application: Application firmware region */
#define APPLICATION_SIZE                0x00100000U
#define APPLICATION_END_ADDRESS         (APPLICATION_START_ADDRESS + APPLICATION_SIZE - 1)

/* ========================================================================== */
/*                         Download Region (UDS 0x34)                        */
/* ========================================================================== */

#define DOWNLOAD_BASE_ADDRESS           0x08100000U
#define DOWNLOAD_MAX_SIZE_BYTES         0x00100000U
#define DOWNLOAD_ALIGNMENT_BYTES        32U
#define DOWNLOAD_MAX_BLOCK_LENGTH_BYTES 200U

/* ========================================================================== */
/*                         Memory Region Validation                           */
/* ========================================================================== */

/**
 * @brief Check if address is in bootloader region
 */
static inline uint8_t is_address_in_bootloader(uint32_t address)
{
    return (address >= BOOTLOADER_START_ADDRESS && address <= BOOTLOADER_END_ADDRESS);
}

/**
 * @brief Check if address is in application region
 */
static inline uint8_t is_address_in_application(uint32_t address)
{
    return (address >= APPLICATION_START_ADDRESS && address <= APPLICATION_END_ADDRESS);
}

/**
 * @brief Check if address is valid for download
 */
static inline uint8_t is_address_valid_for_download(uint32_t address, uint32_t size)
{
    if (address < DOWNLOAD_BASE_ADDRESS)
        return 0;
    
    if ((address + size) > (DOWNLOAD_BASE_ADDRESS + DOWNLOAD_MAX_SIZE_BYTES))
        return 0;
    
    if ((address % DOWNLOAD_ALIGNMENT_BYTES) != 0)
        return 0;
    
    return 1;
}

#endif /* MEMORY_LAYOUT_CONFIG_H */
