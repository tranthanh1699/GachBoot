#ifndef UDS_RDBI_DID_REGISTRY_H
#define UDS_RDBI_DID_REGISTRY_H

#include "dev_common.h"
#include "svc_dcm.h"

/**
 * @brief DID Read callback function type - simplified
 * Callback assumes all validation is done by service handler
 * Just fill the data buffer with DID data
 * @param data Output data buffer (guaranteed to have enough space)
 * @return Std_ReturnType E_OK, E_NOT_OK, DCM_E_PENDING
 */
typedef Std_ReturnType (*uds_did_read_callback_t)(uint8_t *data);

/**
 * @brief DID Read length getter for variable length DIDs
 * Called by service handler to get actual data length before read
 * @param data_len Output: actual data length
 * @return Std_ReturnType E_OK, E_NOT_OK
 */
typedef Std_ReturnType (*uds_did_read_length_t)(uint16_t *data_len);

/**
 * @brief DID entry structure
 */
typedef struct {
    uint16_t did;                           // Data Identifier
    uint16_t expected_length;               // Expected data length (0 = variable length, use length_getter)
    uds_did_read_callback_t read_callback;  // Read callback function
    uds_did_read_length_t length_getter;    // Length getter for variable DIDs (NULL if fixed length)
    uint32_t session_mask;                  // Supported sessions (bitmask)
    uint32_t security_mask;                 // Required security levels (bitmask)
} uds_did_entry_t;

/**
 * @brief Find DID entry in registry
 * @param did Data Identifier to find
 * @return Pointer to DID entry, or NULL if not found
 */
const uds_did_entry_t* uds_rdbi_find_did(uint16_t did);

/**
 * @brief Get DID registry
 * @param count Output: number of DIDs in registry
 * @return Pointer to DID registry array
 */
const uds_did_entry_t* uds_rdbi_get_registry(uint16_t *count);

#endif // UDS_RDBI_DID_REGISTRY_H
