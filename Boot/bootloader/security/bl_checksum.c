#include "bl_checksum.h"

#define BL_CRC16_INIT_VALUE             0xFFFFu
#define BL_CRC16_POLY                   0x1021u
#define BL_CRC32_INIT_VALUE             0xFFFFFFFFu
#define BL_CRC32_POLY                   0xEDB88320u

uint16_t bl_checksum_crc16_ccitt_false(const uint8_t *data, uint16_t length)
{
    uint16_t crc = BL_CRC16_INIT_VALUE;
    uint16_t index = 0u;

    if (data == (const uint8_t *)0)
    {
        return 0u;
    }

    for (index = 0u; index < length; index++)
    {
        uint8_t bit_index = 0u;
        crc ^= (uint16_t)((uint16_t)data[index] << 8u);
        for (bit_index = 0u; bit_index < 8u; bit_index++)
        {
            if ((crc & 0x8000u) != 0u)
            {
                crc = (uint16_t)((uint16_t)(crc << 1u) ^ BL_CRC16_POLY);
            }
            else
            {
                crc = (uint16_t)(crc << 1u);
            }
        }
    }

    return crc;
}

uint32_t bl_checksum_crc32(const uint8_t *data, uint32_t length)
{
    uint32_t crc = BL_CRC32_INIT_VALUE;
    uint32_t index = 0u;

    if (data == (const uint8_t *)0)
    {
        return 0u;
    }

    for (index = 0u; index < length; index++)
    {
        uint8_t bit_index = 0u;
        crc ^= (uint32_t)data[index];
        for (bit_index = 0u; bit_index < 8u; bit_index++)
        {
            if ((crc & 1u) != 0u)
            {
                crc = (crc >> 1u) ^ BL_CRC32_POLY;
            }
            else
            {
                crc >>= 1u;
            }
        }
    }

    return ~crc;
}
