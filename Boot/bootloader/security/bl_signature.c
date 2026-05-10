#include "bl_signature.h"
#include "bl_config.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#if defined(BL_SIGNATURE_VERIFY_ENABLE)
#undef BL_ENABLE_SIGNATURE_VERIFY
#define BL_ENABLE_SIGNATURE_VERIFY       BL_SIGNATURE_VERIFY_ENABLE
#endif

#if (BL_ENABLE_SIGNATURE_VERIFY != 0u)

#if defined(BL_RSA_PUBLIC_KEY_HEADER)
#include BL_RSA_PUBLIC_KEY_HEADER
#endif

#define BL_RSA_2048_BYTES                256u
#define BL_RSA_2048_WORDS                64u
#define BL_RSA_WORK_WORDS                (3u * BL_RSA_2048_WORDS)
#define BL_SHA256_BLOCK_SIZE             64u
#define BL_SHA256_DIGEST_SIZE            32u
#define BL_SHA256_LENGTH_SIZE            8u
#define BL_RSA_EXPONENT_65537_STEPS      16u

#ifndef BL_RSA_PUBLIC_KEY_N0INV
#define BL_RSA_PUBLIC_KEY_N0INV          0u
#endif

#ifndef BL_RSA_PUBLIC_KEY_N_WORDS
#define BL_RSA_PUBLIC_KEY_N_WORDS        BL_RSA_EMPTY_WORDS
#endif

#ifndef BL_RSA_PUBLIC_KEY_RR_WORDS
#define BL_RSA_PUBLIC_KEY_RR_WORDS       BL_RSA_EMPTY_WORDS
#endif

#define BL_RSA_EMPTY_WORDS                                                   \
{                                                                            \
    0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u,          \
    0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u,          \
    0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u,          \
    0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u           \
}


typedef struct
{
    uint32_t n0inv;
    uint32_t n[BL_RSA_2048_WORDS];
    uint32_t rr[BL_RSA_2048_WORDS];
} bl_rsa_public_key_t;

static const uint32_t bl_sha256_initial_state[8] =
{
    0x6A09E667u, 0xBB67AE85u, 0x3C6EF372u, 0xA54FF53Au,
    0x510E527Fu, 0x9B05688Cu, 0x1F83D9ABu, 0x5BE0CD19u
};

static const uint32_t bl_sha256_k[64] =
{
    0x428A2F98u, 0x71374491u, 0xB5C0FBCFu, 0xE9B5DBA5u,
    0x3956C25Bu, 0x59F111F1u, 0x923F82A4u, 0xAB1C5ED5u,
    0xD807AA98u, 0x12835B01u, 0x243185BEu, 0x550C7DC3u,
    0x72BE5D74u, 0x80DEB1FEu, 0x9BDC06A7u, 0xC19BF174u,
    0xE49B69C1u, 0xEFBE4786u, 0x0FC19DC6u, 0x240CA1CCu,
    0x2DE92C6Fu, 0x4A7484AAu, 0x5CB0A9DCu, 0x76F988DAu,
    0x983E5152u, 0xA831C66Du, 0xB00327C8u, 0xBF597FC7u,
    0xC6E00BF3u, 0xD5A79147u, 0x06CA6351u, 0x14292967u,
    0x27B70A85u, 0x2E1B2138u, 0x4D2C6DFCu, 0x53380D13u,
    0x650A7354u, 0x766A0ABBu, 0x81C2C92Eu, 0x92722C85u,
    0xA2BFE8A1u, 0xA81A664Bu, 0xC24B8B70u, 0xC76C51A3u,
    0xD192E819u, 0xD6990624u, 0xF40E3585u, 0x106AA070u,
    0x19A4C116u, 0x1E376C08u, 0x2748774Cu, 0x34B0BCB5u,
    0x391C0CB3u, 0x4ED8AA4Au, 0x5B9CCA4Fu, 0x682E6FF3u,
    0x748F82EEu, 0x78A5636Fu, 0x84C87814u, 0x8CC70208u,
    0x90BEFFFAu, 0xA4506CEBu, 0xBEF9A3F7u, 0xC67178F2u
};

static const uint8_t bl_sha256_digest_info_prefix[19] =
{
    0x30u, 0x31u, 0x30u, 0x0Du, 0x06u, 0x09u, 0x60u, 0x86u,
    0x48u, 0x01u, 0x65u, 0x03u, 0x04u, 0x02u, 0x01u, 0x05u,
    0x00u, 0x04u, 0x20u
};

static const bl_rsa_public_key_t bl_rsa_public_key =
{
    BL_RSA_PUBLIC_KEY_N0INV,
    BL_RSA_PUBLIC_KEY_N_WORDS,
    BL_RSA_PUBLIC_KEY_RR_WORDS
};

static uint32_t bl_rotr32(uint32_t value, uint32_t shift)
{
    return (value >> shift) | (value << (32u - shift));
}

static uint32_t bl_read_u32_be(const uint8_t *data)
{
    return ((uint32_t)data[0] << 24u) |
           ((uint32_t)data[1] << 16u) |
           ((uint32_t)data[2] << 8u) |
           ((uint32_t)data[3]);
}

static void bl_write_u64_be(uint8_t *data, uint64_t value)
{
    uint32_t index = 0u;

    for (index = 0u; index < BL_SHA256_LENGTH_SIZE; index++)
    {
        data[BL_SHA256_LENGTH_SIZE - 1u - index] = (uint8_t)(value & 0xFFu);
        value >>= 8u;
    }
}

static void bl_sha256_transform(bl_sha256_ctx_t *ctx, const uint8_t *block)
{
    uint32_t w[64];
    uint32_t a;
    uint32_t b;
    uint32_t c;
    uint32_t d;
    uint32_t e;
    uint32_t f;
    uint32_t g;
    uint32_t h;
    uint32_t index = 0u;

    for (index = 0u; index < 16u; index++)
    {
        w[index] = bl_read_u32_be(&block[index * 4u]);
    }

    for (index = 16u; index < 64u; index++)
    {
        uint32_t s0 = bl_rotr32(w[index - 15u], 7u) ^ bl_rotr32(w[index - 15u], 18u) ^ (w[index - 15u] >> 3u);
        uint32_t s1 = bl_rotr32(w[index - 2u], 17u) ^ bl_rotr32(w[index - 2u], 19u) ^ (w[index - 2u] >> 10u);
        w[index] = w[index - 16u] + s0 + w[index - 7u] + s1;
    }

    a = ctx->state[0];
    b = ctx->state[1];
    c = ctx->state[2];
    d = ctx->state[3];
    e = ctx->state[4];
    f = ctx->state[5];
    g = ctx->state[6];
    h = ctx->state[7];

    for (index = 0u; index < 64u; index++)
    {
        uint32_t s1 = bl_rotr32(e, 6u) ^ bl_rotr32(e, 11u) ^ bl_rotr32(e, 25u);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + s1 + ch + bl_sha256_k[index] + w[index];
        uint32_t s0 = bl_rotr32(a, 2u) ^ bl_rotr32(a, 13u) ^ bl_rotr32(a, 22u);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = s0 + maj;

        h = g;
        g = f;
        f = e;
        e = d + temp1;
        d = c;
        c = b;
        b = a;
        a = temp1 + temp2;
    }

    ctx->state[0] += a;
    ctx->state[1] += b;
    ctx->state[2] += c;
    ctx->state[3] += d;
    ctx->state[4] += e;
    ctx->state[5] += f;
    ctx->state[6] += g;
    ctx->state[7] += h;
}

void bl_sha256_init(bl_sha256_ctx_t *ctx)
{
    uint32_t index = 0u;

    ctx->bit_count = 0u;
    ctx->buffer_length = 0u;

    for (index = 0u; index < 8u; index++)
    {
        ctx->state[index] = bl_sha256_initial_state[index];
    }

    for (index = 0u; index < BL_SHA256_BLOCK_SIZE; index++)
    {
        ctx->buffer[index] = 0u;
    }
}

void bl_sha256_update(bl_sha256_ctx_t *ctx, const uint8_t *data, uint32_t length)
{
    uint32_t index = 0u;

    ctx->bit_count += ((uint64_t)length * 8u);

    while (index < length)
    {
        ctx->buffer[ctx->buffer_length] = data[index];
        ctx->buffer_length++;
        index++;

        if (ctx->buffer_length == BL_SHA256_BLOCK_SIZE)
        {
            bl_sha256_transform(ctx, ctx->buffer);
            ctx->buffer_length = 0u;
        }
    }
}

void bl_sha256_final(bl_sha256_ctx_t *ctx, uint8_t *digest)
{
    uint32_t index = 0u;

    ctx->buffer[ctx->buffer_length] = 0x80u;
    ctx->buffer_length++;

    if (ctx->buffer_length > (BL_SHA256_BLOCK_SIZE - BL_SHA256_LENGTH_SIZE))
    {
        while (ctx->buffer_length < BL_SHA256_BLOCK_SIZE)
        {
            ctx->buffer[ctx->buffer_length] = 0u;
            ctx->buffer_length++;
        }

        bl_sha256_transform(ctx, ctx->buffer);
        ctx->buffer_length = 0u;
    }

    while (ctx->buffer_length < (BL_SHA256_BLOCK_SIZE - BL_SHA256_LENGTH_SIZE))
    {
        ctx->buffer[ctx->buffer_length] = 0u;
        ctx->buffer_length++;
    }

    bl_write_u64_be(&ctx->buffer[BL_SHA256_BLOCK_SIZE - BL_SHA256_LENGTH_SIZE], ctx->bit_count);
    bl_sha256_transform(ctx, ctx->buffer);

    for (index = 0u; index < 8u; index++)
    {
        digest[(index * 4u) + 0u] = (uint8_t)(ctx->state[index] >> 24u);
        digest[(index * 4u) + 1u] = (uint8_t)(ctx->state[index] >> 16u);
        digest[(index * 4u) + 2u] = (uint8_t)(ctx->state[index] >> 8u);
        digest[(index * 4u) + 3u] = (uint8_t)(ctx->state[index]);
    }
}

static bool bl_rsa_key_is_configured(const bl_rsa_public_key_t *key)
{
    return (key->n0inv != 0u);
}

static void bl_rsa_sub_mod(const bl_rsa_public_key_t *key, uint32_t *value)
{
    uint64_t borrow = 0u;
    uint32_t index = 0u;

    for (index = 0u; index < BL_RSA_2048_WORDS; index++)
    {
        uint64_t diff = (uint64_t)value[index] - (uint64_t)key->n[index] - borrow;
        value[index] = (uint32_t)diff;
        borrow = (diff >> 63u) & 1u;
    }
}

static bool bl_rsa_ge_mod(const bl_rsa_public_key_t *key, const uint32_t *value)
{
    uint32_t index = BL_RSA_2048_WORDS;

    while (index > 0u)
    {
        index--;
        if (value[index] < key->n[index])
        {
            return false;
        }
        if (value[index] > key->n[index])
        {
            return true;
        }
    }

    return true;
}

static void bl_rsa_mont_mul_add(const bl_rsa_public_key_t *key, uint32_t *c, uint32_t a, const uint32_t *b)
{
    uint64_t acc_a = ((uint64_t)a * (uint64_t)b[0]) + (uint64_t)c[0];
    uint32_t d0 = (uint32_t)acc_a * key->n0inv;
    uint64_t acc_b = ((uint64_t)d0 * (uint64_t)key->n[0]) + (uint32_t)acc_a;
    uint32_t index = 0u;

    for (index = 1u; index < BL_RSA_2048_WORDS; index++)
    {
        acc_a = (acc_a >> 32u) + ((uint64_t)a * (uint64_t)b[index]) + (uint64_t)c[index];
        acc_b = (acc_b >> 32u) + ((uint64_t)d0 * (uint64_t)key->n[index]) + (uint32_t)acc_a;
        c[index - 1u] = (uint32_t)acc_b;
    }

    acc_a = (acc_a >> 32u) + (acc_b >> 32u);
    c[BL_RSA_2048_WORDS - 1u] = (uint32_t)acc_a;

    if ((acc_a >> 32u) != 0u)
    {
        bl_rsa_sub_mod(key, c);
    }
}

static void bl_rsa_mont_mul(const bl_rsa_public_key_t *key, uint32_t *c, const uint32_t *a, const uint32_t *b)
{
    uint32_t index = 0u;

    for (index = 0u; index < BL_RSA_2048_WORDS; index++)
    {
        c[index] = 0u;
    }

    for (index = 0u; index < BL_RSA_2048_WORDS; index++)
    {
        bl_rsa_mont_mul_add(key, c, a[index], b);
    }
}

static void bl_rsa_mod_pow_65537(const bl_rsa_public_key_t *key, uint8_t *inout, uint32_t *work)
{
    uint32_t *a = work;
    uint32_t *a_r = &work[BL_RSA_2048_WORDS];
    uint32_t *aa_r = &work[2u * BL_RSA_2048_WORDS];
    uint32_t index = 0u;
    uint32_t step = 0u;

    for (index = 0u; index < BL_RSA_2048_WORDS; index++)
    {
        uint32_t byte_index = (BL_RSA_2048_WORDS - 1u - index) * 4u;
        a[index] = ((uint32_t)inout[byte_index + 0u] << 24u) |
                   ((uint32_t)inout[byte_index + 1u] << 16u) |
                   ((uint32_t)inout[byte_index + 2u] << 8u) |
                   ((uint32_t)inout[byte_index + 3u]);
    }

    bl_rsa_mont_mul(key, a_r, a, key->rr);

    for (step = 0u; step < BL_RSA_EXPONENT_65537_STEPS; step += 2u)
    {
        bl_rsa_mont_mul(key, aa_r, a_r, a_r);
        bl_rsa_mont_mul(key, a_r, aa_r, aa_r);
    }

    bl_rsa_mont_mul(key, aa_r, a_r, a);

    if (bl_rsa_ge_mod(key, aa_r) == true)
    {
        bl_rsa_sub_mod(key, aa_r);
    }

    for (index = BL_RSA_2048_WORDS; index > 0u; index--)
    {
        uint32_t value = aa_r[index - 1u];
        *inout = (uint8_t)(value >> 24u);
        inout++;
        *inout = (uint8_t)(value >> 16u);
        inout++;
        *inout = (uint8_t)(value >> 8u);
        inout++;
        *inout = (uint8_t)value;
        inout++;
    }
}

static bool bl_constant_time_equal(const uint8_t *left, const uint8_t *right, uint32_t length)
{
    uint8_t diff = 0u;
    uint32_t index = 0u;

    for (index = 0u; index < length; index++)
    {
        diff = (uint8_t)(diff | (left[index] ^ right[index]));
    }

    return (diff == 0u);
}

static bool bl_rsa_check_pkcs1_sha256(const uint8_t *encoded, const uint8_t *digest)
{
    uint8_t diff = 0u;
    uint32_t index = 0u;
    uint32_t ps_end = BL_RSA_2048_BYTES - sizeof(bl_sha256_digest_info_prefix) - BL_SHA256_DIGEST_SIZE;

    diff = (uint8_t)(diff | (encoded[0] ^ 0x00u));
    diff = (uint8_t)(diff | (encoded[1] ^ 0x01u));

    for (index = 2u; index < (ps_end - 1u); index++)
    {
        diff = (uint8_t)(diff | (encoded[index] ^ 0xFFu));
    }

    diff = (uint8_t)(diff | (encoded[ps_end - 1u] ^ 0x00u));

    if (bl_constant_time_equal(&encoded[ps_end], bl_sha256_digest_info_prefix,
                               (uint32_t)sizeof(bl_sha256_digest_info_prefix)) == false)
    {
        diff = 1u;
    }

    if (bl_constant_time_equal(&encoded[BL_RSA_2048_BYTES - BL_SHA256_DIGEST_SIZE],
                               digest, BL_SHA256_DIGEST_SIZE) == false)
    {
        diff = 1u;
    }

    return (diff == 0u);
}

static bool bl_rsa_verify_sha256(const bl_rsa_public_key_t *key, const uint8_t *signature, const uint8_t *digest)
{
    uint8_t encoded[BL_RSA_2048_BYTES];
    uint32_t work[BL_RSA_WORK_WORDS];

    (void)memcpy(encoded, signature, BL_RSA_2048_BYTES);
    bl_rsa_mod_pow_65537(key, encoded, work);

    return bl_rsa_check_pkcs1_sha256(encoded, digest);
}

#endif /* BL_ENABLE_SIGNATURE_VERIFY != 0u */

bool bl_signature_is_required(void)
{
#if (BL_ENABLE_SIGNATURE_VERIFY == 0u)
    return false;
#else
    return true;
#endif
}

bl_status_t bl_signature_verify(uint32_t firmware_address, uint32_t firmware_size,
                                const uint8_t *signature, uint16_t signature_length)
{
#if (BL_ENABLE_SIGNATURE_VERIFY == 0u)
    (void)firmware_address;
    (void)firmware_size;
    (void)signature;
    (void)signature_length;
    return BL_STATUS_OK;
#else
    bl_sha256_ctx_t sha_ctx;
    uint8_t digest[BL_SHA256_DIGEST_SIZE];
    const uint8_t *firmware = (const uint8_t *)(uintptr_t)firmware_address;

    if ((firmware_address == 0u) || (firmware_size == 0u) || (signature == (const uint8_t *)0))
    {
        return BL_STATUS_PARAM;
    }

    if (signature_length != BL_RSA_2048_BYTES)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_rsa_key_is_configured(&bl_rsa_public_key) == false)
    {
        return BL_STATUS_NOT_SUPPORTED;
    }

    bl_sha256_init(&sha_ctx);
    bl_sha256_update(&sha_ctx, firmware, firmware_size);
    bl_sha256_final(&sha_ctx, digest);

    if (bl_rsa_verify_sha256(&bl_rsa_public_key, signature, digest) == false)
    {
        return BL_STATUS_ERROR;
    }

    return BL_STATUS_OK;
#endif
}

bl_status_t bl_signature_verify_digest(const uint8_t *digest, const uint8_t *signature, uint16_t signature_length)
{
#if (BL_ENABLE_SIGNATURE_VERIFY == 0u)
    (void)digest;
    (void)signature;
    (void)signature_length;
    return BL_STATUS_OK;
#else
    if ((digest == (const uint8_t *)0) || (signature == (const uint8_t *)0))
    {
        return BL_STATUS_PARAM;
    }

    if (signature_length != BL_RSA_2048_BYTES)
    {
        return BL_STATUS_PARAM;
    }

    if (bl_rsa_key_is_configured(&bl_rsa_public_key) == false)
    {
        return BL_STATUS_NOT_SUPPORTED;
    }

    if (bl_rsa_verify_sha256(&bl_rsa_public_key, signature, digest) == false)
    {
        return BL_STATUS_ERROR;
    }

    return BL_STATUS_OK;
#endif
}
