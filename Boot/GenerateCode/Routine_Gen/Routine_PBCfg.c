/**
 * @file Routine_PBCfg.c
 * @brief UDS Routine Control Configuration Implementation
 * @date Generated on 2025-12-21 16:20:08
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
        case UDS_ROUTINE_CONTROL_REQUEST_RESULTS:
            return routine_erase_memory_request_results(option_record, option_record_len,
                                              status_record, status_record_len);
        default:
            return E_NOT_OK;
    }
}

/**
 * @brief Wrapper function for routine 0xFF01 - ROUTINE_CHECK_PROGRAMMING_DEPENDENCIES
 */
static Std_ReturnType routine_check_programming_dependencies(
    uint8_t sub_function,
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len)
{
    switch (sub_function) {
        case UDS_ROUTINE_CONTROL_START:
            return routine_check_programming_dependencies_start(option_record, option_record_len,
                                              status_record, status_record_len);
        default:
            return E_NOT_OK;
    }
}

/**
 * @brief Wrapper function for routine 0x0202 - ROUTINE_CHECK_MEMORY
 */
static Std_ReturnType routine_check_memory(
    uint8_t sub_function,
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len)
{
    switch (sub_function) {
        case UDS_ROUTINE_CONTROL_START:
            return routine_check_memory_start(option_record, option_record_len,
                                              status_record, status_record_len);
        case UDS_ROUTINE_CONTROL_REQUEST_RESULTS:
            return routine_check_memory_request_results(option_record, option_record_len,
                                              status_record, status_record_len);
        default:
            return E_NOT_OK;
    }
}

/**
 * @brief Wrapper function for routine 0x0203 - ROUTINE_VERIFY_APPLICATION_INTEGRITY
 */
static Std_ReturnType routine_verify_application_integrity(
    uint8_t sub_function,
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len)
{
    switch (sub_function) {
        case UDS_ROUTINE_CONTROL_START:
            return routine_verify_application_integrity_start(option_record, option_record_len,
                                              status_record, status_record_len);
        default:
            return E_NOT_OK;
    }
}

/**
 * @brief Wrapper function for routine 0x0204 - ROUTINE_CHECK_PROGRAMMING_INTEGRITY
 */
static Std_ReturnType routine_check_programming_integrity(
    uint8_t sub_function,
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len)
{
    switch (sub_function) {
        case UDS_ROUTINE_CONTROL_START:
            return routine_check_programming_integrity_start(option_record, option_record_len,
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
        .callback = routine_erase_memory,
        .session_mask = DCM_PROGRAMMING_SESSION_MASK,
        .security_mask = (1U << 1U) | (1U << 2U)  // Erase flash memory region
    },
    {
        .rid = 0xFF01,
        .callback = routine_check_programming_dependencies,
        .session_mask = DCM_PROGRAMMING_SESSION_MASK,
        .security_mask = (1U << 1U) | (1U << 2U)  // Check programming preconditions (voltage, temperature, etc.)
    },
    {
        .rid = 0x0202,
        .callback = routine_check_memory,
        .session_mask = DCM_EXTENDED_SESSION_MASK | DCM_PROGRAMMING_SESSION_MASK,
        .security_mask = 0xFFFFFFFF  // Verify memory integrity using CRC/Checksum
    },
    {
        .rid = 0x0203,
        .callback = routine_verify_application_integrity,
        .session_mask = DCM_EXTENDED_SESSION_MASK | DCM_PROGRAMMING_SESSION_MASK,
        .security_mask = 0xFFFFFFFF  // Verify application software integrity
    },
    {
        .rid = 0x0204,
        .callback = routine_check_programming_integrity,
        .session_mask = DCM_PROGRAMMING_SESSION_MASK | DCM_EXTENDED_SESSION_MASK,
        .security_mask = (1U << 1U)  // Check if programming session was completed successfully
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
