#ifndef DEV_FEE_H
#define DEV_FEE_H

#include "dev_common.h"
#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Flash EEPROM Emulation (Fee) - AUTOSAR-compliant
 * 
 * Manages logical flash memory operations with wear leveling and sector switching.
 * Provides EEPROM-like interface on top of flash hardware.
 * 
 * Responsibilities:
 * - Sector management (active/standby sectors)
 * - Wear leveling (automatic sector switching)
 * - Write position tracking
 * - Logical-to-physical address mapping
 * - Garbage collection
 * 
 * Architecture:
 * NvM → MemIf → Fee (this layer) → Fls → Hardware
 * 
 * Sector Strategy:
 * - Two sectors: Active and Standby
 * - Active sector receives all writes
 * - When full: switch to standby, mark old as invalid
 * - Automatic garbage collection
 */

/**
 * @brief Fee Job Status
 */
typedef enum {
    DEV_FEE_JOB_OK = 0,                 // Job completed successfully
    DEV_FEE_JOB_PENDING = 1,            // Job is pending
    DEV_FEE_JOB_FAILED = 2,             // Job failed
    DEV_FEE_SECTOR_SWITCHED = 3         // Sector switch occurred during operation
} dev_fee_job_status_t;

/**
 * @brief Fee Sector State
 */
typedef enum {
    DEV_FEE_SECTOR_EMPTY = 0,           // Sector is erased
    DEV_FEE_SECTOR_ACTIVE = 1,          // Sector is actively being written
    DEV_FEE_SECTOR_STANDBY = 2,         // Sector is erased and ready
    DEV_FEE_SECTOR_FULL = 3,            // Sector is full
    DEV_FEE_SECTOR_INVALID = 4          // Sector has errors
} dev_fee_sector_state_t;

/**
 * @brief Fee Statistics
 */
typedef struct {
    uint32_t total_writes;              // Total write operations
    uint32_t total_reads;               // Total read operations
    uint32_t sector_switches;           // Number of sector switches
    uint32_t garbage_collections;       // Number of GC cycles
    uint32_t active_sector_address;     // Current active sector base
    uint32_t active_sector_usage;       // Bytes used in active sector
    uint32_t write_position;            // Current write position
} dev_fee_statistics_t;

/**
 * @brief Initialize Fee module
 * @return dev_err_t Error code
 * 
 * @note Must be called after Fls initialization
 */
dev_err_t dev_fee_init(void);

/**
 * @brief Write data to Fee (dynamic addressing)
 * @param data Source data buffer
 * @param length Number of bytes to write
 * @param out_address Output: Logical address where data was written
 * @return dev_err_t Error code
 * 
 * @note Fee automatically:
 *       - Finds next available position in active sector
 *       - Switches to standby sector if full
 *       - Returns logical address for NvM to track
 */
dev_err_t dev_fee_write(const uint8_t *data, uint32_t length, uint32_t *out_address);

/**
 * @brief Read data from Fee
 * @param address Logical address (previously returned by dev_fee_write)
 * @param data Destination buffer
 * @param length Number of bytes to read
 * @return dev_err_t Error code
 */
dev_err_t dev_fee_read(uint32_t address, uint8_t *data, uint32_t length);

/**
 * @brief Erase all Fee-managed sectors
 * @return dev_err_t Error code
 */
dev_err_t dev_fee_erase_all(void);

/**
 * @brief Force sector switch (for testing/maintenance)
 * @return dev_err_t Error code
 */
dev_err_t dev_fee_force_sector_switch(void);

/**
 * @brief Get active sector information
 * @param out_sector Output: Active sector base address
 * @param out_usage Output: Bytes used in active sector
 * @return dev_err_t Error code
 */
dev_err_t dev_fee_get_active_sector(uint32_t *out_sector, uint32_t *out_usage);

/**
 * @brief Get Fee statistics
 * @param stats Output statistics structure
 * @return dev_err_t Error code
 */
dev_err_t dev_fee_get_statistics(dev_fee_statistics_t *stats);

/**
 * @brief Check if address is managed by Fee
 * @param address Address to check
 * @return true if address is managed
 */
bool dev_fee_is_managed_address(uint32_t address);

#endif // DEV_FEE_H
