#ifndef DEV_RINGBUFFER_H
#define DEV_RINGBUFFER_H
#include <stdint.h>
#include <stdbool.h>
#include "dev_common.h"

typedef struct
{
    uint8_t *buffer;        // Pointer to the buffer memory
    uint32_t head;         // Index of the head (write position)
    uint32_t tail;         // Index of the tail (read position)
    uint32_t max_size;     // Maximum size of the buffer
    uint32_t fill_size;    // Current number of bytes in the buffer
} dev_ringbuffer_t;

/**
 * @brief Initialize the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @param size Size of the memory buffer in bytes.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_init(dev_ringbuffer_t *rb, uint32_t size);

/**
 * @brief Deinitialize the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_deinit(dev_ringbuffer_t *rb); 

/**
 * @brief Reset the ring buffer to empty state.
 * @param rb Pointer to the ring buffer structure.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_reset(dev_ringbuffer_t *rb);

/**
 * @brief Get the number of free bytes in the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @return uint32_t Number of free bytes in the buffer.
 */
uint32_t dev_ringbuffer_free_space(dev_ringbuffer_t *rb);

/**
 * @brief Write data to the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @param data Data to be written.
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_write_uint8(dev_ringbuffer_t *rb, uint8_t data); 

/**
 * @brief Read data from the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @param data Return pointer to store the read data (1 byte).
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t dev_ringbuffer_read_uint8(dev_ringbuffer_t *rb, uint8_t *data); 

/**
 * @brief Get the number of bytes currently stored in the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @return bool True if the buffer is empty, false otherwise.
 */
bool dev_ringbuffer_is_empty(dev_ringbuffer_t *rb);

/**
 * @brief Get the number of bytes currently stored in the ring buffer.
 * @param rb Pointer to the ring buffer structure.
 * @return uint32_t Number of bytes currently stored in the buffer.
 */
uint32_t dev_ringbuffer_size(dev_ringbuffer_t *rb);


#endif // DEV_RINGBUFFER_H