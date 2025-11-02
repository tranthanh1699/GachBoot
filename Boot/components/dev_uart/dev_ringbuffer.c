#include "dev_ringbuffer.h"
#include "dev_common.h"
#include <stdlib.h>

CONFIG_LOG_TAG(RINGBUFFER, true)
/**
 * @brief Initialize the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @param size Size of the memory buffer in bytes.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_init(dev_ringbuffer_t *rb, uint32_t size)
{
    DEV_RETURN_ON_FALSE(rb != NULL, DEV_ERR_INVALID_ARG, "Ring buffer pointer is NULL");
    DEV_RETURN_ON_FALSE(size > 0, DEV_ERR_INVALID_ARG, "Ring buffer size must be greater than 0");

    rb->buffer = (uint8_t *)calloc(size, sizeof(uint8_t));

    DEV_RETURN_ON_FALSE(rb->buffer != NULL, DEV_ERR_NO_MEM, "Failed to allocate memory for ring buffer");

    rb->max_size = size;
    rb->head = 0;
    rb->tail = 0;
    rb->fill_size = 0;

    return DEV_OK;
}

/**
 * @brief Deinitialize the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_deinit(dev_ringbuffer_t *rb)
{
    DEV_RETURN_ON_FALSE(rb != NULL, DEV_ERR_INVALID_ARG, "Ring buffer pointer is NULL");

    free(rb->buffer);
    rb->buffer = NULL;
    rb->max_size = 0;
    rb->head = 0;
    rb->tail = 0;
    rb->fill_size = 0;

    return DEV_OK;
}

/**
 * @brief Reset the ring buffer to empty state.
 * @param rb Pointer to the ring buffer structure.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_reset(dev_ringbuffer_t *rb)
{
    DEV_RETURN_ON_FALSE(rb != NULL, DEV_ERR_INVALID_ARG, "Ring buffer pointer is NULL");

    rb->head = 0;
    rb->tail = 0;
    rb->fill_size = 0;

    return DEV_OK;
}

/**
 * @brief Get the number of free bytes in the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @return uint32_t Number of free bytes in the buffer.
 */
uint32_t dev_ringbuffer_free_space(dev_ringbuffer_t *rb)
{
    DEV_RETURN_ON_FALSE(rb != NULL, 0, "Ring buffer pointer is NULL");

    return rb->max_size - rb->fill_size;
}

/**
 * @brief Write data to the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @param data Data to be written.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_write_uint8(dev_ringbuffer_t *rb, uint8_t data)
{
    DEV_RETURN_ON_FALSE(rb != NULL, DEV_ERR_INVALID_ARG, "Ring buffer pointer is NULL");

    uint32_t next_head; 
    uint32_t next_tail; 

    rb->buffer[rb->tail] = data;
    next_tail = (++rb->tail) % rb->max_size;
    rb->tail = next_tail;

    if(rb->fill_size == rb->max_size)
    {
        next_head = (++rb->head) % rb->max_size;
        rb->head = next_head;
    }
    else
    {
        rb->fill_size++;
    }

    return DEV_OK;
}

/**
 * @brief Read data from the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @param data Return pointer to store the read data (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_read_uint8(dev_ringbuffer_t *rb, uint8_t *data)
{
    DEV_RETURN_ON_FALSE(rb != NULL, DEV_ERR_INVALID_ARG, "Ring buffer pointer is NULL");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data pointer is NULL");

    DEV_RETURN_ON_FALSE(!dev_ringbuffer_is_empty(rb), DEV_ERR, "Ring buffer is empty");
    uint32_t next_head;
    *data = rb->buffer[rb->head];
    next_head = (++rb->head) % rb->max_size;
    rb->head = next_head;
    rb->fill_size--;
    return DEV_OK;
}

/**
 * @brief Get the number of bytes currently stored in the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @return bool True if the buffer is empty, false otherwise.
 */
bool dev_ringbuffer_is_empty(dev_ringbuffer_t *rb)
{
    DEV_RETURN_ON_FALSE(rb != NULL, true, "Ring buffer pointer is NULL");
    return rb->fill_size == 0 ? true : false;
}

/**
 * @brief Get the number of bytes currently stored in the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @return uint32_t Number of bytes currently stored in the buffer.
 */
uint32_t dev_ringbuffer_size(dev_ringbuffer_t *rb)
{
    uint32_t retVal = 0;
    DEV_RETURN_ON_FALSE(rb != NULL, retVal, "Ring buffer pointer is NULL");
    retVal = rb->fill_size;
    return retVal;
}