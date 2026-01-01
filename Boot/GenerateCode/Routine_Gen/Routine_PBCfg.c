/**
 * @file Routine_PBCfg.c
 * @brief UDS Routine Control Configuration Implementation
 * @date Generated on 2026-01-01 15:57:00
 * 
 * Auto-generated from gachboot_config.json
 * DO NOT EDIT MANUALLY
 */

#include "Routine_PBCfg.h"
#include "DCM_Session_PBCfg.h"
#include "Security_PBCfg.h"

/* ========================================================================== */
/*                         Routine Wrapper Implementations                    */
/* ========================================================================== */

/**
 * @brief Wrapper function for routine 0xFF00 - ROUTINE_ERASE_MEMORY
 */
static Std_ReturnType routine_erase_memory(
    uint8_t sub_function,
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len)
{
    switch (sub_function) {
        case UDS_ROUTINE_CONTROL_START:
            return routine_erase_memory_start(option_record, option_record_len,
                                              status_record, status_record_len);
        default:
            return E_NOT_OK;
    }
}

/* ========================================================================== */
/*                          Routine Registry Table                            */
/* ========================================================================== */

static const uds_routine_entry_t routine_registry[] = {
    {
        .rid = 0xFF00,
        .supported_subfunctions = 0x01U,
        .start_option_len = 8U,
        .start_status_len = 0U,
        .stop_option_len = 0U,
        .stop_status_len = 0U,
        .results_option_len = 0U,
        .results_status_len = 0U,
        .callback = routine_erase_memory,
        .session_mask = DCM_PROGRAMMING_SESSION_MASK | DCM_EXTENDED_SESSION_MASK,
        .security_mask = (1U << 1U) | (1U << 2U)  // Erase flash memory region
    },
};

#define ROUTINE_REGISTRY_SIZE (sizeof(routine_registry) / sizeof(uds_routine_entry_t))

/* ========================================================================== */
/*                         Registry Access Functions                          */
/* ========================================================================== */

/**
 * @brief Find routine entry in registry
 */
const uds_routine_entry_t* uds_routine_find_entry(uint16_t rid)
{
    for (uint16_t i = 0; i < ROUTINE_REGISTRY_SIZE; i++) {
        if (routine_registry[i].rid == rid) {
            return &routine_registry[i];
        }
    }
    return NULL;
}

/**
 * @brief Get routine registry
 */
const uds_routine_entry_t* uds_routine_get_registry(uint16_t *count)
{
    if (count != NULL) {
        *count = ROUTINE_REGISTRY_SIZE;
    }
    return routine_registry;
}

/**
 * @brief Validate option_record length for routine
 */
bool uds_routine_validate_option_length(const uds_routine_entry_t *entry, 
                                         uint8_t sub_function, 
                                         uint16_t option_record_len)
{
    if (entry == NULL) {
        return false;
    }
    
    uint16_t expected_len = 0;
    
    switch (sub_function) {
        case UDS_ROUTINE_CONTROL_START:
            expected_len = entry->start_option_len;
            break;
        case UDS_ROUTINE_CONTROL_STOP:
            expected_len = entry->stop_option_len;
            break;
        case UDS_ROUTINE_CONTROL_REQUEST_RESULTS:
            expected_len = entry->results_option_len;
            break;
        default:
            return false;
    }
    
    // If expected_len is 0, any length is accepted (variable/optional)
    if (expected_len == 0) {
        return true;
    }
    
    // Otherwise, must match exactly
    return (option_record_len == expected_len);
}
