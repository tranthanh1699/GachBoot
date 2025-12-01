#ifndef UDS_ROUTINE_CONTROL_REGISTRY_H
#define UDS_ROUTINE_CONTROL_REGISTRY_H

#include "dev_common.h"
#include "svc_dcm.h"

/**
 * @brief Routine control sub-functions (ISO 14229-1)
 */
#define UDS_ROUTINE_CONTROL_START               0x01
#define UDS_ROUTINE_CONTROL_STOP                0x02
#define UDS_ROUTINE_CONTROL_REQUEST_RESULTS     0x03

/**
 * @brief Routine control callback function type
 * @param sub_function Sub-function (0x01=Start, 0x02=Stop, 0x03=RequestResults)
 * @param option_record Optional parameters (input)
 * @param option_record_len Length of option record
 * @param status_record Status/results (output)
 * @param status_record_len Length of status record (output)
 * @return Std_ReturnType E_OK, E_NOT_OK, DCM_E_PENDING
 */
typedef Std_ReturnType (*uds_routine_callback_t)(uint8_t sub_function,
                                                   const uint8_t *option_record,
                                                   uint16_t option_record_len,
                                                   uint8_t *status_record,
                                                   uint16_t *status_record_len);

/**
 * @brief Routine control entry structure
 */
typedef struct {
    uint16_t rid;                       // Routine Identifier
    uds_routine_callback_t callback;    // Routine handler callback
    uint32_t session_mask;              // Allowed sessions bitmask
    uint32_t security_mask;             // Required security bitmask
} uds_routine_entry_t;

/**
 * @brief Find routine entry in registry
 * @param rid Routine Identifier
 * @return Pointer to routine entry, or NULL if not found
 */
const uds_routine_entry_t* uds_routine_find_entry(uint16_t rid);

/**
 * @brief Get routine registry
 * @param count Output: number of entries
 * @return Pointer to routine registry
 */
const uds_routine_entry_t* uds_routine_get_registry(uint16_t *count);

#endif // UDS_ROUTINE_CONTROL_REGISTRY_H
