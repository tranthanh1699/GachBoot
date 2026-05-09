#include "bl_frame.h"
#include "bl_checksum.h"

#include <assert.h>
#include <stdint.h>

static void test_crc16_reference(void)
{
    const uint8_t data[] = { '1', '2', '3', '4', '5', '6', '7', '8', '9' };
    assert(bl_checksum_crc16_ccitt_false(data, (uint16_t)sizeof(data)) == 0x29B1u);
}

static void test_crc32_reference(void)
{
    const uint8_t data[] = { '1', '2', '3', '4', '5', '6', '7', '8', '9' };
    assert(bl_checksum_crc32(data, (uint32_t)sizeof(data)) == 0xCBF43926u);
}

static void test_frame_round_trip(void)
{
    bl_frame_t tx = {0};
    bl_frame_t rx = {0};
    bl_error_t error_code = BL_ERROR_INTERNAL;
    uint8_t buffer[BL_FRAME_MAX_SIZE] = {0};
    uint16_t encoded_size = 0u;

    tx.version = BL_PROTOCOL_VERSION;
    tx.command = BL_CMD_HELLO;
    tx.sequence = 7u;
    tx.length = 5u;
    tx.payload[0] = BL_PROTOCOL_VERSION;

    assert(bl_frame_encode(&tx, buffer, (uint16_t)sizeof(buffer), &encoded_size) == BL_STATUS_OK);
    assert(bl_frame_decode(buffer, encoded_size, &rx, &error_code) == BL_STATUS_OK);
    assert(error_code == BL_ERROR_OK);
    assert(rx.version == tx.version);
    assert(rx.command == tx.command);
    assert(rx.sequence == tx.sequence);
    assert(rx.length == tx.length);
    assert(rx.payload[0] == tx.payload[0]);
}

static void test_frame_rejects_bad_crc(void)
{
    bl_frame_t tx = {0};
    bl_frame_t rx = {0};
    bl_error_t error_code = BL_ERROR_OK;
    uint8_t buffer[BL_FRAME_MAX_SIZE] = {0};
    uint16_t encoded_size = 0u;

    tx.version = BL_PROTOCOL_VERSION;
    tx.command = BL_CMD_HELLO;
    tx.sequence = 1u;
    tx.length = 1u;
    tx.payload[0] = BL_PROTOCOL_VERSION;

    assert(bl_frame_encode(&tx, buffer, (uint16_t)sizeof(buffer), &encoded_size) == BL_STATUS_OK);
    buffer[encoded_size - 1u] ^= 0x01u;

    assert(bl_frame_decode(buffer, encoded_size, &rx, &error_code) == BL_STATUS_CHECKSUM);
    assert(error_code == BL_ERROR_CHECKSUM_MISMATCH);
}

int main(void)
{
    test_crc16_reference();
    test_crc32_reference();
    test_frame_round_trip();
    test_frame_rejects_bad_crc();
    return 0;
}
