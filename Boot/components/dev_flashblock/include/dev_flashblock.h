/**
 * @file dev_flashblock.h
 * @brief Flash Block Management Module
 * 
 * Provides high-level flash operations with automatic sector management
 * and 32-byte alignment handling for STM32H7 flash controller.
 * 
 * Features:
 * - Automatic sector erase based on address and length
 * - 32-byte aligned write operations
 * - Buffer padding and alignment handling
 * - Progress callback support
 */

#ifndef DEV_FLASHBLOCK_H
#define DEV_FLASHBLOCK_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ===== Type Definitions ===== */

/**
 * @brief Flash block erase state
 */
typedef enum {
    DEV_FLASHBLOCK_ERASE_IDLE = 0,     /**< No active erase operation */
    DEV_FLASHBLOCK_ERASE_PREPARED,     /**< Erase prepared, sectors identified */
    DEV_FLASHBLOCK_ERASE_ERASING,      /**< Erase in progress */
    DEV_FLASHBLOCK_ERASE_COMPLETED     /**< Erase completed, awaiting finish */
} dev_flashblock_erase_state_t;

/**
 * @brief Flash block operation result codes
 */
typedef enum {
    DEV_FLASHBLOCK_OK = 0,              /**< Operation successful */
    DEV_FLASHBLOCK_ERROR_INVALID_ADDR,  /**< Invalid flash address */
    DEV_FLASHBLOCK_ERROR_INVALID_LEN,   /**< Invalid length (0 or too large) */
    DEV_FLASHBLOCK_ERROR_ALIGNMENT,     /**< Alignment error */
    DEV_FLASHBLOCK_ERROR_ERASE,         /**< Erase operation failed */
    DEV_FLASHBLOCK_ERROR_WRITE,         /**< Write operation failed */
    DEV_FLASHBLOCK_ERROR_VERIFY,        /**< Verification failed */
    DEV_FLASHBLOCK_ERROR_BUSY,          /**< Flash controller busy */
    DEV_FLASHBLOCK_ERROR_TIMEOUT,       /**< Operation timeout */
    DEV_FLASHBLOCK_ERROR_NOT_INIT,      /**< Module not initialized */
    DEV_FLASHBLOCK_ERROR_INVALID_STATE  /**< Invalid state for operation */
} dev_flashblock_result_t;

/**
 * @brief Progress callback function type
 * 
 * @param current_bytes Number of bytes processed so far
 * @param total_bytes Total number of bytes to process
 * @param context User context pointer
 */
typedef void (*dev_flashblock_progress_cb_t)(uint32_t current_bytes, uint32_t total_bytes, void *context);

/**
 * @brief Flash block configuration
 */
typedef struct {
    uint32_t write_alignment;           /**< Write alignment requirement (default: 32 bytes) */
    uint32_t erase_timeout_ms;          /**< Erase timeout per sector in milliseconds */
    uint32_t write_timeout_ms;          /**< Write timeout per block in milliseconds */
    bool auto_verify;                   /**< Enable automatic write verification */
    dev_flashblock_progress_cb_t progress_cb;  /**< Progress callback (optional) */
    void *context;                      /**< User context for callback */
} dev_flashblock_config_t;

/* ===== Public Functions ===== */

/**
 * @brief Initialize flash block module
 * 
 * @param config Configuration structure (NULL for default config)
 * @return Operation result
 */
dev_flashblock_result_t dev_flashblock_init(const dev_flashblock_config_t *config);

/**
 * @brief Step 1: Prepare erase operation
 * 
 * Determines which sectors need to be erased based on address and length.
 * Uses memory layout configuration to identify affected sectors.
 * 
 * State transition: IDLE -> PREPARED
 * 
 * @param address Start address in flash
 * @param length Length in bytes to erase
 * @return Result code
 * 
 * @note This only prepares the erase, does not perform actual erase
 * @note Must call dev_flashblock_erase_do() to execute erase
 */
dev_flashblock_result_t dev_flashblock_erase_start(uint32_t address, uint32_t length);

/**
 * @brief Step 2: Execute erase operation
 * 
 * Erases the sectors identified in erase_start().
 * Can be called multiple times to erase sectors incrementally.
 * 
 * State transition: PREPARED -> ERASING -> COMPLETED
 * 
 * @return Result code
 * 
 * @note Must call dev_flashblock_erase_start() first
 * @note Call dev_flashblock_erase_finish() when done
 */
dev_flashblock_result_t dev_flashblock_erase_do(void);

/**
 * @brief Step 3: Finalize erase operation
 * 
 * Confirms erase completion and resets state for next operation.
 * 
 * State transition: COMPLETED -> IDLE
 * 
 * @return Result code
 * 
 * @note Resets internal state, ready for next erase_start()
 */
dev_flashblock_result_t dev_flashblock_erase_finish(void);

/**
 * @brief Get current erase state
 * 
 * @return Current erase state
 */
dev_flashblock_erase_state_t dev_flashblock_get_erase_state(void);

/**
 * @brief Get erase progress information
 * 
 * @param current_sector Output: Current sector being erased (can be NULL)
 * @param total_sectors Output: Total sectors to erase (can be NULL)
 * @return Result code
 */
dev_flashblock_result_t dev_flashblock_get_erase_progress(uint32_t *current_sector, uint32_t *total_sectors);

/**
 * @brief Get current erase state
 * 
 * @return Current erase state
 */
dev_flashblock_erase_state_t dev_flashblock_get_erase_state(void);

/**
 * @brief Get erase progress information
 * 
 * @param current_sector Output: Current sector being erased (can be NULL)
 * @param total_sectors Output: Total sectors to erase (can be NULL)
 * @return Result code
 */
dev_flashblock_result_t dev_flashblock_get_erase_progress(uint32_t *current_sector, uint32_t *total_sectors);

/**
 * @brief Get human-readable error string
 * 
 * @param result Result code
 * @return Error description string
 */
const char* dev_flashblock_get_error_string(dev_flashblock_result_t result);

#ifdef __cplusplus
}
#endif

#endif /* DEV_FLASHBLOCK_H */
