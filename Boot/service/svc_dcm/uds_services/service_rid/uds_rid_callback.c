/**
 * @file routine_callbacks.c
 * @brief Implementation of routine control callbacks
 * @date 2025-12-21
 * 
 * This file implements all routine callbacks declared in Routine_PBCfg.h
 */
#include "uds_rid_callback.h"
#include "dev_common.h"
#include "Routine_PBCfg.h"
#include "dev_flashblock.h"
#include "Memory_Layout_Config.h"
#include "svc_dcm.h"
#include <string.h>

CONFIG_LOG_TAG(ROUTINE_CB, true)

/* ========================================================================== */
/*                    Routine 0xFF00 - Erase Memory                           */
/* ========================================================================== */

/**
 * @brief Erase memory state machine
 */
typedef enum {
    ERASE_STATE_IDLE = 0,           /**< No active erase */
    ERASE_STATE_ERASING,            /**< Erase in progress */
    ERASE_STATE_COMPLETED,          /**< Erase completed successfully */
    ERASE_STATE_ERROR               /**< Erase failed */
} erase_routine_state_t;

static erase_routine_state_t s_erase_state = ERASE_STATE_IDLE;
static dev_flashblock_result_t s_erase_result = DEV_FLASHBLOCK_OK;

/**
 * @brief Start erase memory routine
 * 
 * Option Record Format (8 bytes):
 *   [0-3]: Start Address (32-bit, big-endian)
 *   [4-7]: Length (32-bit, big-endian)
 * 
 * Status Record Format (1 byte):
 *   0x00 = Erase started successfully
 */
Std_ReturnType routine_erase_memory_start(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len)
{
    // Validate input parameters
    if (option_record == NULL || option_record_len < 8) {
        DBG_OUT_E("Invalid option record (need 8 bytes: addr + length)");
        return E_NOT_OK;
    }
    
    // Parse address and length (big-endian)
    uint32_t address = ((uint32_t)option_record[0] << 24) |
                       ((uint32_t)option_record[1] << 16) |
                       ((uint32_t)option_record[2] << 8) |
                       ((uint32_t)option_record[3]);
    
    uint32_t length = ((uint32_t)option_record[4] << 24) |
                      ((uint32_t)option_record[5] << 16) |
                      ((uint32_t)option_record[6] << 8) |
                      ((uint32_t)option_record[7]);
    
    DBG_OUT_I("Erase request: addr=0x%08lX, len=%lu bytes", address, length);
    
    // Validate address matches application start
    if (address != APPLICATION_START_ADDRESS) {
        DBG_OUT_E("Invalid erase address 0x%08lX (expected 0x%08lX)", 
                  address, APPLICATION_START_ADDRESS);
        if (status_record != NULL && status_record_len != NULL) {
            status_record[0] = 0x31;  // Request out of range
            *status_record_len = 1;
        }
        return E_NOT_OK;
    }
    
    // Validate length does not exceed application size
    if (length == 0 || length > APPLICATION_SIZE) {
        DBG_OUT_E("Invalid erase length %lu (max %lu)", length, APPLICATION_SIZE);
        if (status_record != NULL && status_record_len != NULL) {
            status_record[0] = 0x31;  // Request out of range
            *status_record_len = 1;
        }
        return E_NOT_OK;
    }
    
    // Check if already erasing (reject new request)
    if (s_erase_state == ERASE_STATE_ERASING) {
        DBG_OUT_W("Erase already in progress, rejecting new request");
        if (status_record != NULL && status_record_len != NULL) {
            status_record[0] = 0x22;  // Conditions not correct
            *status_record_len = 1;
        }
        return E_NOT_OK;
    }
    
    // Queue erase operation
    dev_flashblock_result_t result = dev_flashblock_erase_async(
        address,
        length,
        NULL,  // No callback needed
        NULL
    );
    
    if (result != DEV_FLASHBLOCK_OK) {
        DBG_OUT_E("Failed to queue erase: %s", dev_flashblock_get_error_string(result));
        s_erase_state = ERASE_STATE_ERROR;
        s_erase_result = result;
        if (status_record != NULL && status_record_len != NULL) {
            status_record[0] = 0x72;  // General programming failure
            *status_record_len = 1;
        }
        return E_NOT_OK;
    }
    
    // Update state
    s_erase_state = ERASE_STATE_ERASING;
    s_erase_result = DEV_FLASHBLOCK_OK;
    
    DBG_OUT_I("Erase queued successfully");
    
    // Return status indicating operation is in progress
    if (status_record != NULL && status_record_len != NULL) {
        status_record[0] = 0x00;  // Operation started
        *status_record_len = 1;
    }
    
    return E_OK;
}