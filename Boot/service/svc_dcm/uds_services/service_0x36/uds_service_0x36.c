/**
 * @file uds_service_0x36.c
 * @brief UDS Service 0x36 - Transfer Data Implementation
 * @date 2025-01-27
 * 
 * Receives data blocks during download sequence and writes to flash.
 */

#include "uds_service_0x36.h"
#include "dev_common.h"
#include "dev_flashblock.h"
#include "../service_0x34/uds_service_0x34.h"
#include <string.h>

CONFIG_LOG_TAG(UDS_0x36, true)

Std_ReturnType uds_service_0x36_handler(const uds_message_t *message, ErrorCode_t *error_code)
{
    // Request format: [36][blockSequenceCounter][transferRequestParameterRecord]
    if (message->request_len < 3) {
        DBG_OUT_E("Request too short: %u bytes", message->request_len);
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }
    
    // Get download session
    const uds_download_context_t *ctx = uds_download_get_context();
    
    if (!ctx->active) {
        DBG_OUT_E("No active download session");
        *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
        return E_NOT_OK;
    }
    
    uint8_t block_sequence = message->request[1];
    const uint8_t *data = &message->request[2];
    uint16_t data_len = message->request_len - 2;
    
    DBG_OUT_I("Transfer Data - block=%u, len=%u bytes", block_sequence, data_len);
    
    // Verify block sequence counter
    if (block_sequence != ctx->expected_block_sequence) {
        DBG_OUT_E("Wrong block sequence: got %u, expected %u",
                  block_sequence, ctx->expected_block_sequence);
        *error_code = UDS_NRC_WRONG_BLOCK_SEQUENCE_COUNTER;
        return E_NOT_OK;
    }
    
    // Calculate target flash address
    uint32_t write_address = ctx->start_address + ctx->bytes_transferred;
    
    // Check if data exceeds total size
    if (ctx->bytes_transferred + data_len > ctx->total_size) {
        DBG_OUT_E("Data exceeds total size: %lu + %u > %lu",
                  ctx->bytes_transferred, data_len, ctx->total_size);
        *error_code = UDS_NRC_TRANSFER_DATA_SUSPEND;
        return E_NOT_OK;
    }
    
    DBG_OUT_I("Writing %u bytes to 0x%08lX (progress: %lu/%lu)",
              data_len, write_address, 
              ctx->bytes_transferred + data_len, ctx->total_size);
    
    // Queue write operation to flashblock
    dev_flashblock_result_t result = dev_flashblock_write_async(
        write_address,
        data,
        data_len,
        NULL,
        NULL
    );
    
    if (result != DEV_FLASHBLOCK_OK) {
        DBG_OUT_E("Failed to queue write: %s", dev_flashblock_get_error_string(result));
        
        if (result == DEV_FLASHBLOCK_ERROR_BUSY) {
            *error_code = UDS_NRC_BUSY_REPEAT_REQUEST;
        } else if (result == DEV_FLASHBLOCK_ERROR_INVALID_ADDR) {
            *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        } else {
            *error_code = UDS_NRC_GENERAL_PROGRAMMING_FAILURE;
        }
        return E_NOT_OK;
    }
    
    // Update session state (cast away const - safe here)
    uds_download_context_t *ctx_mut = (uds_download_context_t*)ctx;
    ctx_mut->bytes_transferred += data_len;
    ctx_mut->expected_block_sequence = (block_sequence + 1) & 0xFF;
    
    // Build positive response: [76][blockSequenceCounter]
    message->response[0] = block_sequence;
    *(message->response_len) = 1;
    
    DBG_OUT_I("Block %u queued - progress: %lu/%lu bytes",
              block_sequence, ctx->bytes_transferred, ctx->total_size);
    
    return E_OK;
}