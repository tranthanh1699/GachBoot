#ifndef BL_SIGNATURE_H
#define BL_SIGNATURE_H

#include "bl_types.h"

bool bl_signature_is_required(void);
bl_status_t bl_signature_verify(uint32_t firmware_address, uint32_t firmware_size,
                                const uint8_t *signature, uint16_t signature_length);

#endif /* BL_SIGNATURE_H */
