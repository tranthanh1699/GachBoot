#include "bl_signature.h"
#include "bl_config.h"

bl_status_t bl_signature_verify(uint32_t firmware_address, uint32_t firmware_size,
                                const uint8_t *signature, uint16_t signature_length)
{
    (void)firmware_address;
    (void)firmware_size;
    (void)signature;
    (void)signature_length;

#if (BL_ENABLE_SIGNATURE_VERIFY == 0u)
    return BL_STATUS_OK;
#else
    return BL_STATUS_NOT_SUPPORTED;
#endif
}
