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
    ERASE_STATE_PREPARED,           /**< Erase prepared, waiting for do */
    ERASE_STATE_ERASING,            /**< Erase in progress */
    ERASE_STATE_COMPLETED,          /**< Erase completed successfully */
    ERASE_STATE_ERROR               /**< Erase failed */
} erase_routine_state_t;

static erase_routine_state_t s_erase_state = ERASE_STATE_IDLE;
static uint32_t s_erase_address = 0;
static uint32_t s_erase_length = 0;
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
    if (s_erase_state == ERASE_STATE_PREPARED || s_erase_state == ERASE_STATE_ERASING) {
        DBG_OUT_W("Erase already in progress, rejecting new request");
        return E_NOT_OK;
    }
    
    // Prepare erase operation
    dev_flashblock_result_t result = dev_flashblock_erase_start(address, length);
    if (result != DEV_FLASHBLOCK_OK) {
        DBG_OUT_E("Failed to prepare erase: %d", result);
        s_erase_state = ERASE_STATE_ERROR;
        s_erase_result = result;
        return E_NOT_OK;
    }
    
    // Store parameters and update state
    s_erase_address = address;
    s_erase_length = length;
    s_erase_state = ERASE_STATE_PREPARED;
    s_erase_result = DEV_FLASHBLOCK_OK;
    
    DBG_OUT_I("Erase routine accepted: addr=0x%08lX, len=%lu bytes", address, length);
    
    // Start routine returns status: 0x01 = "in progress"
    // This tells tester the operation is running in background
    if (status_record != NULL && status_record_len != NULL) {
        status_record[0] = 0x01;  // In progress
        *status_record_len = 1;
    }
    
    return E_OK;  // Accepted, background processing started
}

/**
 * @brief Process erase memory routine (background task)
 * 
 * Called periodically in main loop to perform incremental erase.
 * Uses state machine to track progress.
 */
void routine_erase_memory_proc(void)
{
    switch (s_erase_state) {
        case ERASE_STATE_IDLE:
        case ERASE_STATE_COMPLETED:
        case ERASE_STATE_ERROR:
            // Nothing to do
            break;
            
        case ERASE_STATE_PREPARED:
            // Transition to erasing
            s_erase_state = ERASE_STATE_ERASING;
            DBG_OUT_I("Starting erase operation...");
            // Fall through to erasing
            
        case ERASE_STATE_ERASING:
            // Perform erase (this may take multiple calls for large regions)
            s_erase_result = dev_flashblock_erase_do();
            
            if (s_erase_result == DEV_FLASHBLOCK_OK) {
                // Erase sector completed, check if more sectors to erase
                dev_flashblock_erase_state_t erase_state = dev_flashblock_get_erase_state();
                
                if (erase_state == DEV_FLASHBLOCK_ERASE_COMPLETED) {
                    // All sectors erased, finalize
                    s_erase_result = dev_flashblock_erase_finish();
                    
                    if (s_erase_result == DEV_FLASHBLOCK_OK) {
                        s_erase_state = ERASE_STATE_COMPLETED;
                        DBG_OUT_I("Erase completed successfully");
                    } else {
                        s_erase_state = ERASE_STATE_ERROR;
                        DBG_OUT_E("Erase finish failed: %d", s_erase_result);
                    }
                }
                // else: still erasing, continue in next call
            } else {
                // Erase failed
                s_erase_state = ERASE_STATE_ERROR;
                DBG_OUT_E("Erase operation failed: %d", s_erase_result);
            }
            break;
    }
}

/**
 * @brief Get erase routine result
 * 
 * Status Record Format (1 byte):
 *   0x00 = Erase completed successfully
 *   0x01 = Erase in progress
 *   0x02 = Erase failed
 */
Std_ReturnType routine_erase_memory_result(
    uint8_t *status_record,
    uint16_t *status_record_len)
{
    if (status_record == NULL || status_record_len == NULL) {
        return E_NOT_OK;
    }
    
    switch (s_erase_state) {
        case ERASE_STATE_IDLE:
            // No erase started
            status_record[0] = 0xFF;  // Not started
            *status_record_len = 1;
            return E_NOT_OK;
            
        case ERASE_STATE_PREPARED:
        case ERASE_STATE_ERASING:
            // Still in progress
            status_record[0] = 0x01;  // In progress
            *status_record_len = 1;
            return E_OK;
            
        case ERASE_STATE_COMPLETED:
            // Completed successfully
            status_record[0] = 0x00;  // Success
            *status_record_len = 1;
            return E_OK;
            
        case ERASE_STATE_ERROR:
            // Failed
            status_record[0] = 0x02;  // Error
            status_record[1] = (uint8_t)s_erase_result;  // Error code
            *status_record_len = 2;
            return E_NOT_OK;
            
        default:
            return E_NOT_OK;
    }
}