#ifndef DEV_FLS_CONFIG_H
#define DEV_FLS_CONFIG_H

#include <stdint.h>

/**
 * @brief FLS Configuration for STM32H743
 * 
 * STM32H743 Flash Layout:
 * - 2MB total flash (0x08000000 - 0x081FFFFF)
 * - Bank 1: Sector 0-7 (0x08000000 - 0x080FFFFF) - 1MB
 * - Bank 2: Sector 0-7 (0x08100000 - 0x081FFFFF) - 1MB
 * - Sector size: 128KB each (erase granularity)
 * - Write alignment: 256-bit (32 bytes) flash words
 * 
 * FLS uses last 2 sectors for NVM storage:
 * - Sector 6: 0x081C0000 - 0x081DFFFF (128KB)
 * - Sector 7: 0x081E0000 - 0x081FFFFF (128KB)
 * 
 * IMPORTANT:
 * - ERASE: STM32H7 only supports sector erase (128KB at a time)
 * - WRITE: Must align to 32-byte boundaries (256-bit flash word)
 */

// Sector A (Primary) - Bank 2, Sector 6
#define DEV_FLS_SECTOR_A_BASE_ADDRESS   0x081C0000
#define DEV_FLS_SECTOR_A_INDEX          6

// Sector B (Secondary) - Bank 2, Sector 7
#define DEV_FLS_SECTOR_B_BASE_ADDRESS   0x081E0000
#define DEV_FLS_SECTOR_B_INDEX          7

// Sector configuration
#define DEV_FLS_SECTOR_SIZE             0x20000     // 128KB
#define DEV_FLS_WRITE_ALIGNMENT         32          // STM32H7 Flash word = 256 bits = 32 bytes
#define DEV_FLS_BANK_INDEX              2           // Bank 2

// Erase granularity (hardware-dependent)
#define DEV_FLS_ERASE_BY_SECTOR         1           // STM32H7: Erase whole sector only
#define DEV_FLS_ERASE_BY_PAGE           0           // Not supported on STM32H7
#define DEV_FLS_PAGE_SIZE               0           // N/A for STM32H7 (sector erase only)

// Sector management thresholds
#define DEV_FLS_SECTOR_FULL_THRESHOLD   (DEV_FLS_SECTOR_SIZE - 1024)  // Leave 1KB margin

/**
 * @brief Get sector hardware index from base address
 */
static inline uint8_t dev_fls_get_sector_index(uint32_t sector_address)
{
    if (sector_address == DEV_FLS_SECTOR_A_BASE_ADDRESS) {
        return DEV_FLS_SECTOR_A_INDEX;
    } else if (sector_address == DEV_FLS_SECTOR_B_BASE_ADDRESS) {
        return DEV_FLS_SECTOR_B_INDEX;
    }
    return 0xFF;  // Invalid
}

/**
 * @brief Get alternate sector address
 */
static inline uint32_t dev_fls_get_alternate_sector(uint32_t current_sector)
{
    if (current_sector == DEV_FLS_SECTOR_A_BASE_ADDRESS) {
        return DEV_FLS_SECTOR_B_BASE_ADDRESS;
    } else {
        return DEV_FLS_SECTOR_A_BASE_ADDRESS;
    }
}

#endif // DEV_FLS_CONFIG_H
