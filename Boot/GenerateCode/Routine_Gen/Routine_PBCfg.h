#ifndef ROUTINE_PBCFG_H
#define ROUTINE_PBCFG_H

/**
 * @file Routine_PBCfg.h
 * @brief UDS Routine Control Configuration (Service 0x31)
 * @date Generated on 2025-12-27 21:38:25
 * 
 * This file contains routine registry and callback declarations
 */

#include <stdint.h>
#include <stdbool.h>

/* ========================================================================== */
/*                           Forward Declarations                             */
/* ========================================================================== */

#ifndef STD_TYPES_H
typedef uint8_t Std_ReturnType;
#define E_OK        0x00u
#define E_NOT_OK    0x01u
#define DCM_E_PENDING    0x10u
#endif

/* ========================================================================== */
/*                         Routine Control Constants                          */
/* ========================================================================== */

/* Routine Control Sub-functions (ISO 14229-1) */
#define UDS_ROUTINE_CONTROL_START               0x01
#define UDS_ROUTINE_CONTROL_STOP                0x02
#define UDS_ROUTINE_CONTROL_REQUEST_RESULTS     0x03

/* ========================================================================== */
/*                              Type Definitions                              */
/* ========================================================================== */

/**
 * @brief Routine control callback function type
 * @param sub_function Sub-function (0x01=Start, 0x02=Stop, 0x03=RequestResults)
 * @param option_record Optional parameters (input)
 * @param option_record_len Length of option record
 * @param status_record Status/results (output)
 * @param status_record_len Length of status record (output)
 * @return Std_ReturnType E_OK, E_NOT_OK, DCM_E_PENDING
 */
typedef Std_ReturnType (*uds_routine_callback_t)(
    uint8_t sub_function,
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/**
 * @brief Routine control entry structure
 */
typedef struct {
    uint16_t rid;                    /**< Routine Identifier */    uint8_t supported_subfunctions;  /**< Bitmask: bit0=START, bit1=STOP, bit2=REQUEST_RESULTS */
    uint16_t start_option_len;       /**< Expected option_record length for START (0=variable) */
    uint16_t start_status_len;       /**< Expected status_record length for START */
    uint16_t stop_option_len;        /**< Expected option_record length for STOP (0=variable) */
    uint16_t stop_status_len;        /**< Expected status_record length for STOP */
    uint16_t results_option_len;     /**< Expected option_record length for REQUEST_RESULTS (0=variable) */
    uint16_t results_status_len;     /**< Expected status_record length for REQUEST_RESULTS */    uds_routine_callback_t callback; /**< Routine handler callback */
    uint32_t session_mask;           /**< Allowed sessions bitmask */
    uint32_t security_mask;          /**< Required security bitmask */
} uds_routine_entry_t;

/* ========================================================================== */
/*                         Routine Callback Declarations                      */
/* ========================================================================== */

/**
 * @brief Erase flash memory region
 */
/**
 * @brief Erase flash memory region - START
 * @param option_record Optional: Memory address (4 bytes) + Memory size (4 bytes). If omitted, erases default region (Bank 2).
 * @param option_record_len Length of option record
 * @param status_record Status byte (0x00=Success)
 * @param status_record_len Length of status record (output)
 * @return E_OK on success, E_NOT_OK on failure
 */
extern Std_ReturnType routine_erase_memory_start(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/* ========================================================================== */
/*                           Routine Name Constants                           */
/* ========================================================================== */

#define ROUTINE_ERASE_MEMORY                               0xFF00  /**< Erase flash memory region */

/* ========================================================================== */
/*                    Record Length Definitions                               */
/* ========================================================================== */

#define ROUTINE_ERASE_MEMORY_START_OPTION_LENGTH    8U
#define ROUTINE_ERASE_MEMORY_START_STATUS_LENGTH    0U

/* ========================================================================== */
/*                         Registry Access Functions                          */
/* ========================================================================== */

/**
 * @brief Find routine entry in registry
 * @param rid Routine Identifier
 * @return Pointer to routine entry, or NULL if not found
 */
const uds_routine_entry_t* uds_routine_find_entry(uint16_t rid);

/**
 * @brief Validate option_record length for routine
 * @param entry Routine entry
 * @param sub_function Sub-function (0x01=START, 0x02=STOP, 0x03=REQUEST_RESULTS)
 * @param option_record_len Actual length from request
 * @return true if valid, false otherwise
 * @note If expected length is 0, any length is accepted (variable/optional)
 */
bool uds_routine_validate_option_length(const uds_routine_entry_t *entry, 
                                         uint8_t sub_function, 
                                         uint16_t option_record_len);

/**
 * @brief Get routine registry
 * @param count Output: number of entries
 * @return Pointer to routine registry
 */
const uds_routine_entry_t* uds_routine_get_registry(uint16_t *count);

#endif /* ROUTINE_PBCFG_H */
