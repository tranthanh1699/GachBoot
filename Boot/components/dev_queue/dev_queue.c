/**
 * @file dev_queue.c
 * @brief Generic Queue Library Implementation
 */

#include "dev_queue.h"
#include "dev_common.h"
#include <string.h>

CONFIG_LOG_TAG(DEV_QUEUE, true)

/* ===== Private Helper Macros ===== */

#define QUEUE_VALIDATE_PARAM(queue) \
    do { \
        if ((queue) == NULL) { \
            DBG_OUT_E("NULL queue pointer"); \
            return DEV_QUEUE_ERROR_NULL_PARAM; \
        } \
        if (!(queue)->initialized) { \
            DBG_OUT_E("Queue not initialized"); \
            return DEV_QUEUE_ERROR_NOT_INIT; \
        } \
    } while(0)

/* ===== Public API Implementation ===== */

dev_queue_result_t dev_queue_init(
    dev_queue_t *queue,
    void *buffer,
    uint32_t buffer_size,
    uint32_t item_size
)
{
    // Validate parameters
    if (queue == NULL) {
        DBG_OUT_E("NULL queue pointer");
        return DEV_QUEUE_ERROR_NULL_PARAM;
    }
    
    if (buffer == NULL) {
        DBG_OUT_E("NULL buffer pointer");
        return DEV_QUEUE_ERROR_NULL_PARAM;
    }
    
    if (item_size == 0) {
        DBG_OUT_E("Invalid item size (0)");
        return DEV_QUEUE_ERROR_INVALID_SIZE;
    }
    
    // Calculate capacity
    uint32_t capacity = buffer_size / item_size;
    if (capacity == 0) {
        DBG_OUT_E("Buffer too small (size=%u, item_size=%u)", 
                buffer_size, item_size);
        return DEV_QUEUE_ERROR_INVALID_SIZE;
    }
    
    // Initialize queue structure
    queue->buffer = (uint8_t*)buffer;
    queue->item_size = item_size;
    queue->capacity = capacity;
    queue->head = 0;
    queue->tail = 0;
    queue->count = 0;
    queue->initialized = true;
    
    DBG_OUT_I("Initialized - capacity=%u, item_size=%u", 
            capacity, item_size);
    
    return DEV_QUEUE_OK;
}

dev_queue_result_t dev_queue_enqueue(dev_queue_t *queue, const void *item)
{
    QUEUE_VALIDATE_PARAM(queue);
    
    if (item == NULL) {
        DBG_OUT_E("NULL item pointer");
        return DEV_QUEUE_ERROR_NULL_PARAM;
    }
    
    // Check if queue is full
    if (queue->count >= queue->capacity) {
        DBG_OUT_W("Queue full (count=%u, capacity=%u)", 
                queue->count, queue->capacity);
        return DEV_QUEUE_ERROR_FULL;
    }
    
    // Copy item to queue buffer at tail position
    uint32_t offset = queue->tail * queue->item_size;
    memcpy(queue->buffer + offset, item, queue->item_size);
    
    // Update tail (circular wrap)
    queue->tail = (queue->tail + 1) % queue->capacity;
    queue->count++;
    
    return DEV_QUEUE_OK;
}

dev_queue_result_t dev_queue_dequeue(dev_queue_t *queue, void *item)
{
    QUEUE_VALIDATE_PARAM(queue);
    
    if (item == NULL) {
        DBG_OUT_E("NULL item pointer");
        return DEV_QUEUE_ERROR_NULL_PARAM;
    }
    
    // Check if queue is empty
    if (queue->count == 0) {
        return DEV_QUEUE_ERROR_EMPTY;
    }
    
    // Copy item from queue buffer at head position
    uint32_t offset = queue->head * queue->item_size;
    memcpy(item, queue->buffer + offset, queue->item_size);
    
    // Update head (circular wrap)
    queue->head = (queue->head + 1) % queue->capacity;
    queue->count--;
    
    return DEV_QUEUE_OK;
}

dev_queue_result_t dev_queue_peek(const dev_queue_t *queue, void *item)
{
    if (queue == NULL) {
        DBG_OUT_E("NULL queue pointer");
        return DEV_QUEUE_ERROR_NULL_PARAM;
    }
    
    if (!queue->initialized) {
        DBG_OUT_E("Queue not initialized");
        return DEV_QUEUE_ERROR_NOT_INIT;
    }
    
    if (item == NULL) {
        DBG_OUT_E("NULL item pointer");
        return DEV_QUEUE_ERROR_NULL_PARAM;
    }
    
    // Check if queue is empty
    if (queue->count == 0) {
        return DEV_QUEUE_ERROR_EMPTY;
    }
    
    // Copy item without modifying queue state
    uint32_t offset = queue->head * queue->item_size;
    memcpy(item, queue->buffer + offset, queue->item_size);
    
    return DEV_QUEUE_OK;
}

bool dev_queue_is_empty(const dev_queue_t *queue)
{
    if (queue == NULL || !queue->initialized) {
        return true;
    }
    return (queue->count == 0);
}

bool dev_queue_is_full(const dev_queue_t *queue)
{
    if (queue == NULL || !queue->initialized) {
        return false;
    }
    return (queue->count >= queue->capacity);
}

uint32_t dev_queue_count(const dev_queue_t *queue)
{
    if (queue == NULL || !queue->initialized) {
        return 0;
    }
    return queue->count;
}

uint32_t dev_queue_capacity(const dev_queue_t *queue)
{
    if (queue == NULL || !queue->initialized) {
        return 0;
    }
    return queue->capacity;
}

dev_queue_result_t dev_queue_clear(dev_queue_t *queue)
{
    QUEUE_VALIDATE_PARAM(queue);
    
    queue->head = 0;
    queue->tail = 0;
    queue->count = 0;
    
    DBG_OUT_I("Queue cleared");
    
    return DEV_QUEUE_OK;
}

const char* dev_queue_get_error_string(dev_queue_result_t result)
{
    switch (result) {
        case DEV_QUEUE_OK:
            return "Success";
        case DEV_QUEUE_ERROR_NULL_PARAM:
            return "NULL parameter";
        case DEV_QUEUE_ERROR_INVALID_SIZE:
            return "Invalid size";
        case DEV_QUEUE_ERROR_FULL:
            return "Queue full";
        case DEV_QUEUE_ERROR_EMPTY:
            return "Queue empty";
        case DEV_QUEUE_ERROR_NOT_INIT:
            return "Queue not initialized";
        default:
            return "Unknown error";
    }
}
