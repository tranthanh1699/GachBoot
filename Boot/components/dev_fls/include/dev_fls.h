#ifndef DEV_FLS_H
#define DEV_FLS_H

#include "dev_common.h"
#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Flash Driver (FLS) - Hardware Abstraction Layer
 * 
 * AUTOSAR-compliant hardware driver for flash memory.
 * Provides low-level read/write/erase operations WITHOUT logical management.
 * 
 * Responsibilities:
 * - Direct hardware access (read/write/erase)
 * - Flash unlock/lock
 * - Hardware error handling
 * - Write alignment enforcement
 * 
 * NOT responsible for:
 * - Sector switching (handled by Fee)
 * - Wear leveling (handled by Fee)
 * - Write position tracking (handled by Fee)
 * - Block addressing (handled by Fee)
 * 
 * Layer Architecture:
 * NvM → MemIf → Fee → Fls (this layer) → Hardware
 */

/**
 * @brief FLS Job Result
 */
typedef enum {
    DEV_FLS_JOB_OK = 0,                 // Operation successful
    DEV_FLS_JOB_PENDING = 1,            // Operation in progress (async mode)
    DEV_FLS_JOB_FAILED = 2              // Operation failed
} dev_fls_job_result_t;

/**
 * @brief FLS Statistics
 */
typedef struct {
    uint32_t total_reads;               // Total read operations
    uint32_t total_writes;              // Total write operations
    uint32_t total_erases;              // Total erase operations
    uint32_t read_errors;               // Read error count
    uint32_t write_errors;              // Write error count
    uint32_t erase_errors;              // Erase error count
} dev_fls_statistics_t;

/**
 * @brief Initialize FLS module
 * @return dev_err_t Error code
 */
dev_err_t dev_fls_init(void);

/**
 * @brief Read data from flash
 * @param address Source flash address
 * @param data Destination buffer
 * @param length Number of bytes to read
 * @return dev_err_t Error code
 * 
 * @note Direct memory read, no alignment required
 */
dev_err_t dev_fls_read(uint32_t address, uint8_t *data, uint32_t length);

/**
 * @brief Write data to flash
 * @param address Target flash address (must be aligned to DEV_FLS_WRITE_ALIGNMENT)
 * @param data Source data buffer
 * @param length Number of bytes to write (will be aligned up)
 * @return dev_err_t Error code
 * 
 * @note Length will be rounded up to DEV_FLS_WRITE_ALIGNMENT
 * @note Caller must ensure target area is erased (0xFF)
 * @note STM32H7: Address must be 32-byte aligned
 */
dev_err_t dev_fls_write(uint32_t address, const uint8_t *data, uint32_t length);

/**
 * @brief Erase flash sector
 * @param sector_address Base address of sector to erase
 * @return dev_err_t Error code
 * 
 * @note STM32H7: Erases entire 128KB sector
 * @note Sector address must match sector base (0x081C0000 or 0x081E0000)
 */
dev_err_t dev_fls_erase_sector(uint32_t sector_address);

/**
 * @brief Erase all FLS-managed sectors
 * @return dev_err_t Error code
 * 
 * @note Erases all sectors configured in dev_fls_config.h
 */
dev_err_t dev_fls_erase_all(void);

/**
 * @brief Check if address is within FLS-managed range
 * @param address Address to check
 * @return true if address is managed by FLS
 */
bool dev_fls_is_managed_address(uint32_t address);

/**
 * @brief Blank check - verify if flash area is erased
 * @param address Start address
 * @param length Number of bytes to check
 * @return true if all bytes are 0xFF (erased)
 */
bool dev_fls_blank_check(uint32_t address, uint32_t length);

/**
 * @brief Get FLS statistics
 * @param stats Output statistics structure
 * @return dev_err_t Error code
 */
dev_err_t dev_fls_get_statistics(dev_fls_statistics_t *stats);

/**
 * @brief Get active sector information
 * @param out_sector Output: Active sector base address
 * @param out_usage Output: Bytes used in active sector
 * @return dev_err_t Error code
 */
dev_err_t dev_fls_get_active_sector(uint32_t *out_sector, uint32_t *out_usage);

/**
 * @brief Get FLS statistics
 * @param stats Output statistics
 * @return dev_err_t Error code
 */
dev_err_t dev_fls_get_statistics(dev_fls_statistics_t *stats);

/**
 * @brief Force sector switch (for testing/maintenance)
 * @return dev_err_t Error code
 */
dev_err_t dev_fls_force_sector_switch(void);

/**
 * @brief Check if address is in FLS managed region
 * @param address Address to check
 * @return true if address is managed by FLS
 */
bool dev_fls_is_managed_address(uint32_t address);

#endif // DEV_FLS_H
