#ifndef DEV_MEMIF_H
#define DEV_MEMIF_H

#include "dev_common.h"
#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Memory Abstraction Interface (MemIf) - AUTOSAR-compliant
 * 
 * Provides unified interface for upper layers (NvM) to access memory drivers.
 * Abstracts Fee/Ea drivers, allowing NvM to work with any memory type.
 * 
 * Architecture:
 * NvM → MemIf (this layer) → Fee → Fls → Hardware
 * 
 * MemIf routes requests to underlying Fee driver.
 */

/**
 * @brief MemIf Job Status
 */
typedef enum {
    DEV_MEMIF_JOB_OK = 0,               // Job completed successfully
    DEV_MEMIF_JOB_PENDING = 1,          // Job is pending
    DEV_MEMIF_JOB_CANCELED = 2,         // Job was canceled
    DEV_MEMIF_JOB_FAILED = 3,           // Job failed
    DEV_MEMIF_UNINIT = 4,               // Module not initialized
    DEV_MEMIF_BUSY = 5,                 // Module is busy
    DEV_MEMIF_BUSY_INTERNAL = 6         // Internal operation ongoing
} dev_memif_status_t;

/**
 * @brief MemIf Device Mode
 */
typedef enum {
    DEV_MEMIF_MODE_SLOW = 0,            // Slow mode (reduced speed)
    DEV_MEMIF_MODE_FAST = 1             // Fast mode (normal speed)
} dev_memif_mode_t;

/**
 * @brief Initialize MemIf module
 * @return dev_err_t Error code
 */
dev_err_t dev_memif_init(void);

/**
 * @brief Read data from memory
 * @param address Logical address (Fee manages addressing)
 * @param data Destination buffer
 * @param length Number of bytes to read
 * @return dev_err_t Error code
 */
dev_err_t dev_memif_read(uint32_t address, uint8_t *data, uint32_t length);

/**
 * @brief Write data to memory
 * @param address Logical address (Fee manages addressing)
 * @param data Source data buffer
 * @param length Number of bytes to write
 * @param out_physical_address Output: Physical address where data was written (optional)
 * @return dev_err_t Error code
 */
dev_err_t dev_memif_write(uint32_t address, const uint8_t *data, uint32_t length, 
                           uint32_t *out_physical_address);

/**
 * @brief Erase memory block
 * @param address Logical address of block to erase
 * @param length Length of block to erase
 * @return dev_err_t Error code
 */
dev_err_t dev_memif_erase(uint32_t address, uint32_t length);

/**
 * @brief Invalidate memory block
 * @param address Logical address of block to invalidate
 * @return dev_err_t Error code
 */
dev_err_t dev_memif_invalidate(uint32_t address);

/**
 * @brief Get MemIf status
 * @return dev_memif_status_t Current status
 */
dev_memif_status_t dev_memif_get_status(void);

/**
 * @brief Get job result
 * @return dev_memif_status_t Job result
 */
dev_memif_status_t dev_memif_get_job_result(void);

/**
 * @brief Set device mode
 * @param mode Target mode (slow/fast)
 * @return dev_err_t Error code
 */
dev_err_t dev_memif_set_mode(dev_memif_mode_t mode);

#endif // DEV_MEMIF_H
