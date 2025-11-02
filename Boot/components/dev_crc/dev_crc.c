#include "dev_crc.h"

CONFIG_LOG_TAG(CRC, true)


/**
 * @brief Initialize the CRC8 context.
 * @param crc8 Pointer to the CRC8 context.
 */
void dev_crc8_init(dev_crc8_t *crc8)
{
    if(crc8 == NULL)
    {
        DBG_OUT_E("CRC8 context is NULL");
        return;
    }
    crc8->crc = 0x00; 
}

/**
 * @brief Update the CRC8 with new data.
 * @param crc8 Pointer to the CRC8 context.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 */
void dev_crc8_update(dev_crc8_t *crc8, const void *data, uint32_t length)
{
    if(crc8 == NULL || data == NULL)
    {
        DBG_OUT_E("CRC8 context or data is NULL");
        return;
    }

    uint8_t crc = crc8->crc;
    const uint8_t *byte_data = (const uint8_t *)data;
    while (length--)
    {
        crc ^= *byte_data++;
        for (uint8_t i = 0; i < 8; i++)
        {
            crc = (crc & 0x80u) ? (uint8_t)((crc << 1) ^ 0x07u) : (uint8_t)(crc << 1);
        }
    }
    crc8->crc = crc;
}

/**
 * @brief Finalize the CRC8 calculation and get the result.
 * @param crc8 Pointer to the CRC8 context.
 * @return The calculated CRC8 value.
 */
uint8_t dev_crc8_finalize(dev_crc8_t *crc8)
{
    if(crc8 == NULL)
    {
        DBG_OUT_E("CRC8 context is NULL");
        return 0;
    }
    return crc8->crc;
}

/**
 * @brief Calculate the CRC8 of a data buffer in one step.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 * @return The calculated CRC8 value.
 */
uint8_t dev_crc8_calculate(const void *data, uint32_t length)
{
    dev_crc8_t crc8;
    dev_crc8_init(&crc8);
    dev_crc8_update(&crc8, data, length);
    return dev_crc8_finalize(&crc8);
}

/* ================ CRC16 Algorithm ================ */
/**
 * @brief Initialize the CRC16 context.
 * @param crc16 Pointer to the CRC16 context.
 */
void dev_crc16_init(dev_crc16_t *crc16)
{
    if(crc16 == NULL)
    {
        DBG_OUT_E("CRC16 context is NULL");
        return;
    }
    crc16->crc = 0xFFFF; 
}

/**
 * @brief Update the CRC16 with new data.
 * @param crc16 Pointer to the CRC16 context.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 */
void dev_crc16_update(dev_crc16_t *crc16, const void *data, uint32_t length)
{
    if(crc16 == NULL || data == NULL)
    {
        DBG_OUT_E("CRC16 context or data is NULL");
        return;
    }

    uint16_t crc = crc16->crc;
    const uint8_t *byte_data = (const uint8_t *)data;
    while (length--)
    {
        crc ^= (uint16_t)(*byte_data++) << 8;
        for (uint8_t i = 0; i < 8; i++)
        {
            crc = (crc & 0x8000u) ? (uint16_t)((crc << 1) ^ 0x1021u) : (uint16_t)(crc << 1);
        }
    }
    crc16->crc = crc;
}

/**
 * @brief Finalize the CRC16 calculation and get the result.
 * @param crc16 Pointer to the CRC16 context.
 * @return The calculated CRC16 value.
 */
uint16_t dev_crc16_finalize(dev_crc16_t *crc16)
{
    if(crc16 == NULL)
    {
        DBG_OUT_E("CRC16 context is NULL");
        return 0;
    }
    return crc16->crc;
}

/**
 * @brief Calculate the CRC16 of a data buffer in one step.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 * @return The calculated CRC16 value.
 */
uint16_t dev_crc16_calculate(const void *data, uint32_t length)
{
    dev_crc16_t crc16;
    dev_crc16_init(&crc16);
    dev_crc16_update(&crc16, data, length);
    return dev_crc16_finalize(&crc16);
}

/* ================ CRC32 Algorithm ================ */
/**
 * @brief Initialize the CRC32 context.
 * @param crc32 Pointer to the CRC32 context.
 */
void dev_crc32_init(dev_crc32_t *crc32)
{
    if (crc32 == NULL)
    {
        DBG_OUT_E("CRC32 context is NULL");
        return;
    }
    crc32->crc = 0xFFFFFFFF;
}

/**
 * @brief Update the CRC32 with new data.
 * @param crc32 Pointer to the CRC32 context.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 */ 
void dev_crc32_update(dev_crc32_t *crc32, const void *data, uint32_t length)
{
    if (crc32 == NULL || data == NULL)
    {
        DBG_OUT_E("CRC32 context or data is NULL");
        return;
    }

    uint32_t crc = crc32->crc;
    const uint8_t *byte_data = (const uint8_t *)data;
    while (length--)
    {
        crc ^= (uint32_t)(*byte_data++);
        for (uint8_t i = 0; i < 8; i++)
        {
            crc = (crc & 1u) ? (crc >> 1) ^ 0xEDB88320u : (crc >> 1);
        }
    }
    crc32->crc = crc;
}

/**
 * @brief Finalize the CRC32 calculation and get the result.
 * @param crc32 Pointer to the CRC32 context.
 * @return The calculated CRC32 value.
 */
uint32_t dev_crc32_finalize(dev_crc32_t *crc32)
{
    if (crc32 == NULL)
    {
        DBG_OUT_E("CRC32 context is NULL");
        return 0;
    }
    return ~crc32->crc;
}

/**
 * @brief Calculate the CRC32 of a data buffer in one step.
 * @param data Pointer to the data buffer.
 * @param length Length of the data buffer in bytes.
 * @return The calculated CRC32 value.
 */ 
uint32_t dev_crc32_calculate(const void *data, uint32_t length)
{
    dev_crc32_t crc32;
    dev_crc32_init(&crc32);
    dev_crc32_update(&crc32, data, length);
    return dev_crc32_finalize(&crc32);
}