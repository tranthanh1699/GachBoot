#include "uds_routine_control_registry.h"
#include <string.h>

CONFIG_LOG_TAG(ROUTINE_CTRL, true)

// Forward declarations of routine callbacks
static Std_ReturnType routine_erase_memory(uint8_t sub_function, const uint8_t *option_record, 
                                           uint16_t option_record_len, uint8_t *status_record, uint16_t *status_record_len);
static Std_ReturnType routine_check_programming_dependencies(uint8_t sub_function, const uint8_t *option_record,
                                                              uint16_t option_record_len, uint8_t *status_record, uint16_t *status_record_len);
static Std_ReturnType routine_check_memory(uint8_t sub_function, const uint8_t *option_record,
                                           uint16_t option_record_len, uint8_t *status_record, uint16_t *status_record_len);

// Routine Control Registry
static const uds_routine_entry_t routine_registry[] = {
    // RID      Callback                                    Session Mask                                            Security Mask
    {0xFF00,    routine_erase_memory,                       UDS_SESSION_MASK_PROGRAMMING,                          UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2},  // Erase Memory
    {0xFF01,    routine_check_programming_dependencies,     UDS_SESSION_MASK_PROGRAMMING,                          UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2},  // Check Programming Dependencies
    {0x0202,    routine_check_memory,                       UDS_SESSION_MASK_EXTENDED | UDS_SESSION_MASK_PROGRAMMING, UDS_SECURITY_MASK_ALL},                              // Check Memory
};

#define ROUTINE_REGISTRY_SIZE (sizeof(routine_registry) / sizeof(uds_routine_entry_t))

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
    *count = ROUTINE_REGISTRY_SIZE;
    return routine_registry;
}

// ============================================================================
// Routine Callback Implementations
// ============================================================================

/**
 * @brief Routine 0xFF00 - Erase Memory
 * Start: Begin erase operation
 * RequestResults: Get erase status
 */
static Std_ReturnType routine_erase_memory(uint8_t sub_function, const uint8_t *option_record,
                                           uint16_t option_record_len, uint8_t *status_record, uint16_t *status_record_len)
{
    if (sub_function == UDS_ROUTINE_CONTROL_START) {
        // Expect: memoryAddress (4 bytes) + memorySize (4 bytes)
        if (option_record_len != 8) {
            DBG_OUT_E("Invalid option record length: %d (expected 8)", option_record_len);
            return E_NOT_OK;
        }
        
        uint32_t address = (option_record[0] << 24) | (option_record[1] << 16) | 
                          (option_record[2] << 8) | option_record[3];
        uint32_t size = (option_record[4] << 24) | (option_record[5] << 16) | 
                       (option_record[6] << 8) | option_record[7];
        
        DBG_OUT_I("Erase Memory: Address=0x%08X, Size=%u bytes", address, size);
        
        // TODO: Implement actual flash erase
        // For now, just return success
        status_record[0] = 0x00;  // Status: Success
        *status_record_len = 1;
        return E_OK;
    }
    else if (sub_function == UDS_ROUTINE_CONTROL_REQUEST_RESULTS) {
        // Return erase status
        status_record[0] = 0x00;  // Status: Complete
        *status_record_len = 1;
        return E_OK;
    }
    
    return E_NOT_OK;
}

/**
 * @brief Routine 0xFF01 - Check Programming Dependencies
 * Start: Check if conditions are met for programming
 */
static Std_ReturnType routine_check_programming_dependencies(uint8_t sub_function, const uint8_t *option_record,
                                                              uint16_t option_record_len, uint8_t *status_record, uint16_t *status_record_len)
{
    (void)option_record;
    (void)option_record_len;
    
    if (sub_function == UDS_ROUTINE_CONTROL_START) {
        DBG_OUT_I("Check Programming Dependencies");
        
        // TODO: Implement actual checks (voltage, temperature, etc.)
        // For now, return success
        status_record[0] = 0x00;  // Dependencies OK
        *status_record_len = 1;
        return E_OK;
    }
    
    return E_NOT_OK;
}

/**
 * @brief Routine 0x0202 - Check Memory
 * Start: Verify memory integrity (CRC/Checksum)
 */
static Std_ReturnType routine_check_memory(uint8_t sub_function, const uint8_t *option_record,
                                           uint16_t option_record_len, uint8_t *status_record, uint16_t *status_record_len)
{
    if (sub_function == UDS_ROUTINE_CONTROL_START) {
        // Expect: memoryAddress (4 bytes) + memorySize (4 bytes)
        if (option_record_len != 8) {
            DBG_OUT_E("Invalid option record length: %d (expected 8)", option_record_len);
            return E_NOT_OK;
        }
        
        uint32_t address = (option_record[0] << 24) | (option_record[1] << 16) | 
                          (option_record[2] << 8) | option_record[3];
        uint32_t size = (option_record[4] << 24) | (option_record[5] << 16) | 
                       (option_record[6] << 8) | option_record[7];
        
        DBG_OUT_I("Check Memory: Address=0x%08X, Size=%u bytes", address, size);
        
        // TODO: Implement actual CRC/checksum verification
        // For now, return success
        status_record[0] = 0x00;  // Check passed
        status_record[1] = 0x12;  // Dummy CRC
        status_record[2] = 0x34;
        status_record[3] = 0x56;
        status_record[4] = 0x78;
        *status_record_len = 5;
        return E_OK;
    }
    
    return E_NOT_OK;
}
