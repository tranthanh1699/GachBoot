#ifndef UDS_WDBI_DID_REGISTRY_H
#define UDS_WDBI_DID_REGISTRY_H

#include "dev_common.h"
#include "svc_dcm.h"

/**
 * @brief DID Write callback function type - simplified
 * Callback assumes all validation is done by service handler
 * Just use the data buffer to write DID data
 * @param data Input data buffer (already validated by service handler)
 * @param data_len Input data length (already validated by service handler)
 * @return Std_ReturnType E_OK, E_NOT_OK, DCM_E_PENDING
 */
typedef Std_ReturnType (*uds_did_write_callback_t)(const uint8_t *data, uint16_t data_len);

/**
 * @brief DID write entry structure
 */
typedef struct {
    uint16_t did;                            // Data Identifier
    uint16_t expected_length;                // Expected data length (0 = variable length)
    uint16_t min_length;                     // Minimum data length for variable DIDs (0 = use expected_length)
    uint16_t max_length;                     // Maximum data length for variable DIDs (0 = use expected_length)
    uds_did_write_callback_t write_callback; // Write callback function
    uint32_t session_mask;                   // Supported sessions (bitmask)
    uint32_t security_mask;                  // Required security levels (bitmask)
} uds_wdbi_did_entry_t;

/**
 * @brief Find DID entry in write registry
 * @param did Data Identifier to find
 * @return Pointer to DID entry, or NULL if not found
 */
const uds_wdbi_did_entry_t* uds_wdbi_find_did(uint16_t did);

/**
 * @brief Get DID write registry
 * @param count Output: number of DIDs in registry
 * @return Pointer to DID registry array
 */
const uds_wdbi_did_entry_t* uds_wdbi_get_registry(uint16_t *count);

#endif // UDS_WDBI_DID_REGISTRY_H
