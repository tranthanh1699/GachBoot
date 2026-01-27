/**
 * @file uds_service_0x37.c
 * @brief UDS Service 0x37 - Request Transfer Exit Implementation
 * @date 2025-01-27
 * 
 * Finalizes download sequence and closes the session.
 */

#include "uds_service_0x37.h"
#include "dev_common.h"
#include "dev_flashblock.h"
#include "../service_0x34/uds_service_0x34.h"
#include <string.h>

CONFIG_LOG_TAG(UDS_0x37, true)

Std_ReturnType uds_service_0x37_handler(const uds_message_t *message, ErrorCode_t *error_code)
{
    // Request format: [37][transferRequestParameterRecord] (optional)
    if (message->request_len < 1) {
        DBG_OUT_E("Request too short");
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
    
    DBG_OUT_I("Transfer Exit - received %lu/%lu bytes",
              ctx->bytes_transferred, ctx->total_size);
    
    // Check if all data was received
    if (ctx->bytes_transferred != ctx->total_size) {
        DBG_OUT_W("Incomplete transfer: %lu/%lu bytes",
                  ctx->bytes_transferred, ctx->total_size);
        // ISO 14229 allows partial transfers, but we return error
        *error_code = UDS_NRC_TRANSFER_DATA_SUSPEND;
        return E_NOT_OK;
    }
    
    // Wait for flashblock to finish writing queued data
    if (dev_flashblock_is_busy()) {
        DBG_OUT_I("Waiting for flash writes to complete...");
        *error_code = UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING;
        return DCM_E_PENDING;
    }
    
    // Check queue is empty (all writes completed)
    if (dev_flashblock_get_queue_count() > 0) {
        DBG_OUT_I("Queue not empty, waiting...");
        *error_code = UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING;
        return DCM_E_PENDING;
    }
    
    // Close download session
    uds_download_reset_context();
    
    DBG_OUT_I("Download session closed successfully");
    
    // Build positive response: [77] (no additional data)
    *(message->response_len) = 0;
    
    return E_OK;
}