#ifndef DEV_FEE_H
#define DEV_FEE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "dev_common.h"
#include "Fee_PBCfg.h"  /* Generated configuration */

/**
 * @file dev_fee.h
 * @brief Flash EEPROM Emulation (AUTOSAR Fee) - Logical Address Management
 * 
 * Responsibilities:
 * - Provide virtual address space for NvM
 * - Map virtual addresses to physical Fls addresses
 * - Manage sector lifecycle (wear leveling)
 * - Track write position and sector usage
 * - Handle sector switching transparently
 * 
 * Virtual Address Space:
 * - Fee provides continuous virtual space from 0x00000000
 * - NvM allocates blocks in this virtual space
 * - Fee maps virtual → physical (may change after sector switch)
 * - Physical addresses returned to NvM for reading
 * 
 * AUTOSAR Compliance:
 * - Configuration injection at runtime (dev_fee_init with config pointer)
 * - No hardcoded dependencies on generated config
 * - Layered on top of Fls driver
 */

/**
 * @brief Fee sector state
 */
typedef enum {
    DEV_FEE_SECTOR_ERASED = 0,      /**< Sector is erased (all 0xFF) */
    DEV_FEE_SECTOR_ACTIVE,          /**< Sector is currently active (writing) */
    DEV_FEE_SECTOR_FULL,            /**< Sector is full (needs switch) */
    DEV_FEE_SECTOR_INVALIDATED      /**< Sector invalidated (old data) */
} dev_fee_sector_state_t;

/**
 * @brief Fee statistics
 */
typedef struct {
    uint32_t total_writes;              /**< Total write operations */
    uint32_t total_reads;               /**< Total read operations */
    uint32_t sector_switches;           /**< Number of sector switches */
    uint32_t active_sector_index;       /**< Current Fee sector index */
    uint32_t active_sector_usage;       /**< Bytes used in active sector */
    uint32_t next_virtual_address;      /**< Next available virtual address */
    uint32_t write_errors;              /**< Write error count */
} dev_fee_statistics_t;

/**
 * @brief Initialize Fee module with configuration
 * 
 * @param config Pointer to generated configuration (from Fee_Cfg.c)
 *               Pass &Fee_Config for default configuration
 *               Pass NULL to use default configuration
 *               Pass custom config for testing or alternate setups
 * 
 * @return DEV_OK on success
 *         DEV_ERR_INVALID_ARG if config is invalid
 *         DEV_ERR_MODULE_NOT_INIT if Fls not initialized
 * 
 * @note Config is copied internally - caller can free after init
 * @note Automatically scans sectors to determine active one
 * @note Sets up write position for append operations
 */
dev_err_t dev_fee_init(const Fee_ConfigType *config);

/**
 * @brief Write data to virtual address (NvM writes)
 * @param virtual_address Virtual address where to write (ignored, auto-allocated)
 * @param data Data to write
 * @param length Data length
 * @param out_physical_address [OUT] Physical address where data was written
 * @return DEV_OK on success, error code otherwise
 * 
 * @note Virtual address is auto-incremented (append mode)
 * @note Returns physical address for subsequent reads
 * @note May trigger sector switch if active sector is full
 * @note Physical address remains valid until next sector switch
 * 
 * Usage by NvM:
 * @code
 * uint32_t phys_addr;
 * dev_fee_write(0, data, len, &phys_addr);  // Virtual addr ignored
 * // Store phys_addr in block_runtime for reads
 * @endcode
 */
dev_err_t dev_fee_write(uint32_t virtual_address, const uint8_t *data, 
                        uint32_t length, uint32_t *out_physical_address);

/**
 * @brief Read data from physical address (NvM reads)
 * @param physical_address Physical address (returned by write)
 * @param data Buffer to store read data
 * @param length Number of bytes to read
 * @return DEV_OK on success, error code otherwise
 * 
 * @note Uses physical address directly (no translation needed)
 * @note Physical addresses are stable (don't change)
 */
dev_err_t dev_fee_read(uint32_t physical_address, uint8_t *data, uint32_t length);

/**
 * @brief Get active sector information
 * @param sector_address [OUT] Physical base address of active sector
 * @param sector_usage [OUT] Bytes used in active sector
 * @return DEV_OK on success
 * 
 * @note Used by NvM for flash scanning during init
 */
dev_err_t dev_fee_get_active_sector(uint32_t *sector_address, uint32_t *sector_usage);

/**
 * @brief Manually trigger sector switch
 * @return DEV_OK on success, error code otherwise
 * 
 * @note Normally called automatically when sector full
 * @note Can be called manually for testing or defragmentation
 * @note Erases alternate sector and resets write position
 */
dev_err_t dev_fee_switch_sector(void);

/**
 * @brief Get Fee statistics
 * @param stats Pointer to statistics structure
 * @return DEV_OK on success
 */
dev_err_t dev_fee_get_statistics(dev_fee_statistics_t *stats);

/**
 * @brief Check if sector switch is needed
 * @return true if switch needed, false otherwise
 */
bool dev_fee_is_sector_full(void);

/**
 * @brief Get current Fee configuration
 * 
 * Returns pointer to active configuration.
 * Useful for diagnostics and testing.
 * 
 * @return Pointer to active config
 *         NULL if not initialized
 * 
 * @note Do not modify returned config
 */
const Fee_ConfigType* dev_fee_get_config(void);

#ifdef __cplusplus
}
#endif

#endif // DEV_FEE_H
