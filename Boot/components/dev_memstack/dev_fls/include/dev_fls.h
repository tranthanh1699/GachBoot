#ifndef DEV_FLS_H
#define DEV_FLS_H

#ifdef __cplusplus
extern "C" {
#endif

#include "dev_common.h"
#include "Fls_Cfg.h"  /* Generated configuration */

/**
 * @file dev_fls.h
 * @brief Flash Driver (AUTOSAR Fls) - Hardware Interface Layer
 * 
 * Responsibilities:
 * - Provide access to physical flash memory
 * - Execute hardware operations (read/write/erase)
 * - Enforce hardware constraints (alignment, boundaries)
 * - Report sector information
 * 
 * NOT Responsible for:
 * - Logical address management (Fee's job)
 * - Wear leveling (Fee's job)
 * - Sector state tracking (Fee's job)
 * - Write position management (Fee's job)
 * 
 * AUTOSAR Compliance:
 * - Configuration injection at runtime (dev_fls_init with config pointer)
 * - No hardcoded dependencies on generated config
 * - Pure hardware abstraction layer
 */

/**
 * @brief Fls module statistics
 */
typedef struct {
    uint32_t total_reads;       /**< Total read operations */
    uint32_t total_writes;      /**< Total write operations */
    uint32_t total_erases;      /**< Total erase operations */
    uint32_t read_errors;       /**< Read error count */
    uint32_t write_errors;      /**< Write error count */
    uint32_t erase_errors;      /**< Erase error count */
} dev_fls_statistics_t;

/**
 * @brief Initialize Fls module with configuration
 * 
 * @param config Pointer to generated configuration (from Fls_Cfg.c)
 *               Pass &Fls_Config for default configuration
 *               Pass NULL to use default configuration
 *               Pass custom config for testing or alternate setups
 * 
 * @return DEV_OK on success
 *         DEV_ERR_INVALID_ARG if config is invalid
 *         DEV_ERR_HW_INIT if HAL initialization fails
 * 
 * @note Config is copied internally - caller can free after init
 * @note Must be called before any other Fls API
 */
dev_err_t dev_fls_init(const Fls_ConfigType *config);

/**
 * @brief Read data from flash memory
 * @param address Physical flash address
 * @param data Buffer to store read data
 * @param length Number of bytes to read
 * @return DEV_OK on success, error code otherwise
 * 
 * @note Address can be byte-aligned (DEV_FLS_READ_ALIGNMENT = 1)
 * @note Reads directly from flash memory (no caching)
 */
dev_err_t dev_fls_read(uint32_t address, uint8_t *data, uint32_t length);

/**
 * @brief Write data to flash memory
 * @param address Physical flash address (must be 32-byte aligned)
 * @param data Data to write
 * @param length Number of bytes to write
 * @return DEV_OK on success, error code otherwise
 * 
 * @note Address must be aligned to DEV_FLS_WRITE_ALIGNMENT (32 bytes)
 * @note Length will be padded to 32-byte boundary (padded with 0xFF)
 * @note Cannot write across sector boundaries
 * @note Cannot write to already written flash (must erase first)
 */
dev_err_t dev_fls_write(uint32_t address, const uint8_t *data, uint32_t length);

/**
 * @brief Erase a flash sector
 * @param sector_index Index in dev_fls_sector_table[]
 * @return DEV_OK on success, error code otherwise
 * 
 * @note STM32H7: Erases entire 128KB sector (hardware limitation)
 * @note Erase sets all bytes to 0xFF
 * @note Erase time: ~1-2 seconds per sector
 */
dev_err_t dev_fls_erase_sector(uint8_t sector_index);

/**
 * @brief Check if flash region is blank (all 0xFF)
 * @param address Physical flash address
 * @param length Number of bytes to check
 * @return true if blank, false otherwise
 * 
 * @note Used by Fee to find empty space
 */
bool dev_fls_blank_check(uint32_t address, uint32_t length);

/**
 * @brief Get sector descriptor by physical address
 * @param address Physical flash address
 * @return Pointer to sector descriptor, NULL if address not managed
 * 
 * @note Used by Fee to determine which sector an address belongs to
 * @note Returns pointer from active config - do not modify
 */
const Fls_SectorDescriptor_t* dev_fls_get_sector_by_address(uint32_t address);

/**
 * @brief Get sector descriptor by table index
 * @param sector_index Index in configured sector table
 * @return Pointer to sector descriptor, NULL if invalid index
 * 
 * @note Returns pointer from active config - do not modify
 */
const Fls_SectorDescriptor_t* dev_fls_get_sector_by_index(uint8_t sector_index);

/**
 * @brief Check if address is within managed flash range
 * @param address Physical flash address
 * @return true if managed, false otherwise
 */
bool dev_fls_is_managed_address(uint32_t address);

/**
 * @brief Get Fls statistics
 * @param stats Pointer to statistics structure
 * @return DEV_OK on success
 */
dev_err_t dev_fls_get_statistics(dev_fls_statistics_t *stats);

/**
 * @brief Get current Fls configuration
 * 
 * Returns pointer to active configuration.
 * Useful for higher layers (Fee) to query sector info.
 * 
 * @return Pointer to active config
 *         NULL if not initialized
 * 
 * @note Do not modify returned config
 */
const Fls_ConfigType* dev_fls_get_config(void);

#ifdef __cplusplus
}
#endif

#endif // DEV_FLS_H
