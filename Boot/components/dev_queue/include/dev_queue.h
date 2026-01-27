/**
 * @file dev_queue.h
 * @brief Generic Queue Library for Embedded Systems
 * 
 * Features:
 * - Thread-safe FIFO queue
 * - Fixed-size circular buffer
 * - Zero dynamic allocation
 * - Generic item type support
 * - Overflow protection
 */

#ifndef DEV_QUEUE_H
#define DEV_QUEUE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "dev_common.h"

/* ===== Configuration ===== */

/**
 * @brief Maximum queue capacity (items)
 * 
 * Adjust based on application needs and RAM availability.
 * Each queue instance allocates: item_size * capacity bytes
 */
#ifndef DEV_QUEUE_DEFAULT_CAPACITY
#define DEV_QUEUE_DEFAULT_CAPACITY  16U
#endif

/* ===== Type Definitions ===== */

/**
 * @brief Queue operation result codes
 */
typedef enum {
    DEV_QUEUE_OK = 0,               /**< Operation successful */
    DEV_QUEUE_ERROR_NULL_PARAM,     /**< NULL parameter passed */
    DEV_QUEUE_ERROR_INVALID_SIZE,   /**< Invalid item size */
    DEV_QUEUE_ERROR_FULL,           /**< Queue is full */
    DEV_QUEUE_ERROR_EMPTY,          /**< Queue is empty */
    DEV_QUEUE_ERROR_NOT_INIT        /**< Queue not initialized */
} dev_queue_result_t;

/**
 * @brief Queue handle structure
 * 
 * Opaque handle - internal fields should not be accessed directly.
 * Use dev_queue_* APIs only.
 */
typedef struct {
    uint8_t *buffer;        /**< Internal buffer pointer */
    uint32_t item_size;     /**< Size of each item in bytes */
    uint32_t capacity;      /**< Maximum number of items */
    uint32_t head;          /**< Read index (dequeue position) */
    uint32_t tail;          /**< Write index (enqueue position) */
    uint32_t count;         /**< Current number of items */
    bool initialized;       /**< Initialization flag */
} dev_queue_t;

/* ===== Public API ===== */

/**
 * @brief Initialize a queue
 * 
 * @param queue Pointer to queue handle
 * @param buffer Pointer to buffer for queue storage
 * @param buffer_size Total size of buffer in bytes
 * @param item_size Size of each item in bytes
 * @return Result code
 * 
 * @note buffer_size must be >= item_size * capacity
 * @note Buffer must remain valid for queue lifetime
 * 
 * Example:
 * @code
 * uint8_t queue_buffer[sizeof(my_item_t) * 16];
 * dev_queue_t queue;
 * dev_queue_init(&queue, queue_buffer, sizeof(queue_buffer), sizeof(my_item_t));
 * @endcode
 */
dev_queue_result_t dev_queue_init(
    dev_queue_t *queue,
    void *buffer,
    uint32_t buffer_size,
    uint32_t item_size
);

/**
 * @brief Enqueue (add) an item to queue
 * 
 * @param queue Pointer to queue handle
 * @param item Pointer to item to enqueue
 * @return Result code
 * 
 * @note Returns DEV_QUEUE_ERROR_FULL if queue is full
 * @note Item is copied into queue buffer
 * @note Thread-safe if external locking is used
 */
dev_queue_result_t dev_queue_enqueue(dev_queue_t *queue, const void *item);

/**
 * @brief Dequeue (remove) an item from queue
 * 
 * @param queue Pointer to queue handle
 * @param item Pointer to buffer to receive item
 * @return Result code
 * 
 * @note Returns DEV_QUEUE_ERROR_EMPTY if queue is empty
 * @note Item is copied from queue buffer to provided buffer
 * @note Thread-safe if external locking is used
 */
dev_queue_result_t dev_queue_dequeue(dev_queue_t *queue, void *item);

/**
 * @brief Peek at front item without removing
 * 
 * @param queue Pointer to queue handle
 * @param item Pointer to buffer to receive item copy
 * @return Result code
 * 
 * @note Does not modify queue state
 * @note Returns DEV_QUEUE_ERROR_EMPTY if queue is empty
 */
dev_queue_result_t dev_queue_peek(const dev_queue_t *queue, void *item);

/**
 * @brief Check if queue is empty
 * 
 * @param queue Pointer to queue handle
 * @return true if empty, false otherwise
 */
bool dev_queue_is_empty(const dev_queue_t *queue);

/**
 * @brief Check if queue is full
 * 
 * @param queue Pointer to queue handle
 * @return true if full, false otherwise
 */
bool dev_queue_is_full(const dev_queue_t *queue);

/**
 * @brief Get current number of items in queue
 * 
 * @param queue Pointer to queue handle
 * @return Number of items (0 if queue is NULL or not initialized)
 */
uint32_t dev_queue_count(const dev_queue_t *queue);

/**
 * @brief Get queue capacity (maximum items)
 * 
 * @param queue Pointer to queue handle
 * @return Capacity (0 if queue is NULL or not initialized)
 */
uint32_t dev_queue_capacity(const dev_queue_t *queue);

/**
 * @brief Clear all items from queue
 * 
 * @param queue Pointer to queue handle
 * @return Result code
 * 
 * @note Resets queue to empty state
 * @note Does not free memory (uses provided buffer)
 */
dev_queue_result_t dev_queue_clear(dev_queue_t *queue);

/**
 * @brief Get human-readable error string
 * 
 * @param result Result code
 * @return Error description string
 */
const char* dev_queue_get_error_string(dev_queue_result_t result);

#ifdef __cplusplus
}
#endif

#endif /* DEV_QUEUE_H */
