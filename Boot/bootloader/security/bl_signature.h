#ifndef BL_SIGNATURE_H
#define BL_SIGNATURE_H

#include "bl_types.h"

bool bl_signature_is_required(void);

#define BL_SHA256_BLOCK_SIZE             64u
#define BL_SHA256_DIGEST_SIZE            32u
#define BL_SHA256_LENGTH_SIZE            8u

typedef struct
{
    uint64_t bit_count;
    uint32_t state[8];
    uint8_t buffer[BL_SHA256_BLOCK_SIZE];
    uint32_t buffer_length;
} bl_sha256_ctx_t;

void bl_sha256_init(bl_sha256_ctx_t *ctx);
void bl_sha256_update(bl_sha256_ctx_t *ctx, const uint8_t *data, uint32_t length);
void bl_sha256_final(bl_sha256_ctx_t *ctx, uint8_t *digest);

bl_status_t bl_signature_verify_digest(const uint8_t *digest, const uint8_t *signature, uint16_t signature_length);
bl_status_t bl_signature_verify(uint32_t firmware_address, uint32_t firmware_size,
                                const uint8_t *signature, uint16_t signature_length);

#endif /* BL_SIGNATURE_H */
