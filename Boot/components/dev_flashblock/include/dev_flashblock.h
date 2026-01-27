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
 * @brief Flash block state machine
 */
typedef enum {
    DEV_FLASHBLOCK_STATE_IDLE = 0,     /**< Idle, ready for new operation */
    DEV_FLASHBLOCK_STATE_BUSY,         /**< Operation in progress */
    DEV_FLASHBLOCK_STATE_WAITING       /**< Waiting for flash to be ready */
} dev_flashblock_state_t;

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
 * @brief Operation completion callback function type
 * 
 * @param result Operation result code
 * @param context User context pointer
 */
typedef void (*dev_flashblock_completion_cb_t)(dev_flashblock_result_t result, void *context);

/**
 * @brief Operation completion callback function type
 * 
 * @param result Operation result code
 * @param context User context pointer
 */
typedef void (*dev_flashblock_completion_cb_t)(dev_flashblock_result_t result, void *context);

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
 * @brief Enqueue erase operation (Non-blocking)
 * 
 * Adds erase operation to queue. Background task will process it.
 * 
 * @param address Start address in flash
 * @param length Length in bytes to erase
 * @param callback Completion callback (optional, can be NULL)
 * @param context User context for callback
 * @return Result code
 *         - DEV_FLASHBLOCK_OK: Successfully enqueued
 *         - DEV_FLASHBLOCK_ERROR_INVALID_ADDR: Invalid address
 *         - DEV_FLASHBLOCK_ERROR_BUSY: Queue is full
 * 
 * @note Non-blocking: Returns immediately after enqueue
 * @note Actual erase performed by background task
 */
dev_flashblock_result_t dev_flashblock_erase_async(
    uint32_t address, 
    uint32_t length,
    dev_flashblock_completion_cb_t callback,
    void *context
);

/**
 * @brief Enqueue write operation (Non-blocking)
 * 
 * Adds write operation to queue. Data is copied to internal buffer.
 * Background task will process write in 32-byte chunks.
 * 
 * @param address Start address in flash
 * @param data Data to write (will be copied)
 * @param length Length in bytes
 * @param callback Completion callback (optional, can be NULL)
 * @param context User context for callback
 * @return Result code
 *         - DEV_FLASHBLOCK_OK: Successfully enqueued
 *         - DEV_FLASHBLOCK_ERROR_INVALID_ADDR: Invalid address
 *         - DEV_FLASHBLOCK_ERROR_INVALID_LEN: Length exceeds 256 bytes
 *         - DEV_FLASHBLOCK_ERROR_BUSY: Queue is full
 * 
 * @note Non-blocking: Returns immediately after enqueue
 * @note Data is copied, caller can free buffer after return
 * @note Max write size: 256 bytes per call
 */
dev_flashblock_result_t dev_flashblock_write_async(
    uint32_t address,
    const uint8_t *data,
    uint32_t length,
    dev_flashblock_completion_cb_t callback,
    void *context
);

/**
 * @brief Background task to process flash operations
 * 
 * Processes queued operations one at a time.
 * Handles 32-byte chunking for STM32H7.
 * Checks flash busy state before each operation.
 * 
 * @note Must be called periodically (e.g., from main loop or RTOS task)
 * @note Processes one chunk per call to avoid blocking
 */
void dev_flashblock_process(void);

/**
 * @brief Get flash block state
 * 
 * @return Current state (IDLE, BUSY, WAITING)
 */
dev_flashblock_state_t dev_flashblock_get_state(void);

/**
 * @brief Get number of pending operations in queue
 * 
 * @return Number of operations waiting to be processed
 */
uint8_t dev_flashblock_get_queue_count(void);

/**
 * @brief Check if flash block is busy
 * 
 * @return true if busy (processing operation), false if idle
 */
bool dev_flashblock_is_busy(void);

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
