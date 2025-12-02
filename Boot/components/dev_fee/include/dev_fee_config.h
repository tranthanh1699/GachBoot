#ifndef DEV_FEE_CONFIG_H
#define DEV_FEE_CONFIG_H

#include <stdint.h>

/**
 * @brief Fee Configuration
 * 
 * Fee uses Fls-managed sectors for wear leveling.
 * Two-sector strategy: Active and Standby
 */

// Fee uses same sectors as Fls
#define DEV_FEE_SECTOR_A_BASE_ADDRESS   0x081C0000  // Sector 6
#define DEV_FEE_SECTOR_B_BASE_ADDRESS   0x081E0000  // Sector 7
#define DEV_FEE_SECTOR_SIZE             0x20000     // 128KB

// Fee write alignment (same as Fls)
#define DEV_FEE_WRITE_ALIGNMENT         32          // 32 bytes

// Sector full threshold (leave margin for metadata)
#define DEV_FEE_SECTOR_FULL_THRESHOLD   (DEV_FEE_SECTOR_SIZE - 1024)  // Leave 1KB margin

/**
 * @brief Get alternate sector address
 */
static inline uint32_t dev_fee_get_alternate_sector(uint32_t current_sector)
{
    if (current_sector == DEV_FEE_SECTOR_A_BASE_ADDRESS) {
        return DEV_FEE_SECTOR_B_BASE_ADDRESS;
    } else {
        return DEV_FEE_SECTOR_A_BASE_ADDRESS;
    }
}

#endif // DEV_FEE_CONFIG_H
