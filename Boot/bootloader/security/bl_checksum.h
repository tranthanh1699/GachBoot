#ifndef BL_CHECKSUM_H
#define BL_CHECKSUM_H

#include <stdint.h>

uint16_t bl_checksum_crc16_ccitt_false(const uint8_t *data, uint16_t length);
uint32_t bl_checksum_crc32(const uint8_t *data, uint32_t length);

#endif /* BL_CHECKSUM_H */
