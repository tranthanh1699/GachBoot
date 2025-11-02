#ifndef DEV_CRC_H
#define DEV_CRC_H
#include "dev_common.h"

/* ================ CRC8 Algorithm ================ */
typedef struct
{
    uint8_t crc; 
} dev_crc8_t;
/**
 * @brief Initialize the CRC8 context.
 * @param crc8 Pointer to the CRC8 context.
 */
void dev_crc8_init(dev_crc8_t *crc8);

/**
 * @brief Update the CRC8 with new data.
 * @param crc8 Pointer to the CRC8 context.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 */
void dev_crc8_update(dev_crc8_t *crc8, const void *data, uint32_t length);

/**
 * @brief Finalize the CRC8 calculation and get the result.
 * @param crc8 Pointer to the CRC8 context.
 * @return The calculated CRC8 value.
 */
uint8_t dev_crc8_finalize(dev_crc8_t *crc8);

/**
 * @brief Calculate the CRC8 of a data buffer in one step.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 * @return The calculated CRC8 value.
 */
uint8_t dev_crc8_calculate(const void *data, uint32_t length);

/* ================ CRC16 Algorithm ================ */
typedef struct
{
    uint16_t crc; 
} dev_crc16_t;

/**
 * @brief Initialize the CRC16 context.
 * @param crc16 Pointer to the CRC16 context.
 */
void dev_crc16_init(dev_crc16_t *crc16);

/**
 * @brief Update the CRC16 with new data.
 * @param crc16 Pointer to the CRC16 context.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 */
void dev_crc16_update(dev_crc16_t *crc16, const void *data, uint32_t length);

/**
 * @brief Finalize the CRC16 calculation and get the result.
 * @param crc16 Pointer to the CRC16 context.
 * @return The calculated CRC16 value.
 */
uint16_t dev_crc16_finalize(dev_crc16_t *crc16);

/**
 * @brief Calculate the CRC16 of a data buffer in one step.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 * @return The calculated CRC16 value.
 */
uint16_t dev_crc16_calculate(const void *data, uint32_t length);

/* ================ CRC32 Algorithm ================ */
typedef struct
{
    uint32_t crc; 
} dev_crc32_t;

/**
 * @brief Initialize the CRC32 context.
 * @param crc32 Pointer to the CRC32 context.
 */
void dev_crc32_init(dev_crc32_t *crc32);

/**
 * @brief Update the CRC32 with new data.
 * @param crc32 Pointer to the CRC32 context.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 */ 
void dev_crc32_update(dev_crc32_t *crc32, const void *data, uint32_t length);

/**
 * @brief Finalize the CRC32 calculation and get the result.
 * @param crc32 Pointer to the CRC32 context.
 * @return The calculated CRC32 value.
 */
uint32_t dev_crc32_finalize(dev_crc32_t *crc32);

/**
 * @brief Calculate the CRC32 of a data buffer in one step.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 * @return The calculated CRC32 value.
 */ 
uint32_t dev_crc32_calculate(const void *data, uint32_t length);

#endif // DEV_CRC_H