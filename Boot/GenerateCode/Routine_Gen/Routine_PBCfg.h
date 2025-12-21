#ifndef ROUTINE_PBCFG_H
#define ROUTINE_PBCFG_H

/**
 * @file Routine_PBCfg.h
 * @brief UDS Routine Control Configuration (Service 0x31)
 * @date Generated on 2025-12-21 15:06:03
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
    uint16_t rid;                    /**< Routine Identifier */
    uds_routine_callback_t callback; /**< Routine handler callback */
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
 * @param option_record Memory address (4 bytes) + Memory size (4 bytes)
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

/**
 * @brief Erase flash memory region - REQUEST_RESULTS
 * @param option_record No parameters
 * @param option_record_len Length of option record
 * @param status_record Status byte (0x00=Complete)
 * @param status_record_len Length of status record (output)
 * @return E_OK on success, E_NOT_OK on failure
 */
extern Std_ReturnType routine_erase_memory_request_results(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/**
 * @brief Check programming preconditions (voltage, temperature, etc.)
 */
/**
 * @brief Check programming preconditions (voltage, temperature, etc.) - START
 * @param option_record No parameters
 * @param option_record_len Length of option record
 * @param status_record Status byte (0x00=OK, 0x01=NOT OK)
 * @param status_record_len Length of status record (output)
 * @return E_OK on success, E_NOT_OK on failure
 */
extern Std_ReturnType routine_check_programming_dependencies_start(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/**
 * @brief Verify memory integrity using CRC/Checksum
 */
/**
 * @brief Verify memory integrity using CRC/Checksum - START
 * @param option_record Memory address (4 bytes) + Memory size (4 bytes)
 * @param option_record_len Length of option record
 * @param status_record Status byte (0x00=Started)
 * @param status_record_len Length of status record (output)
 * @return E_OK on success, E_NOT_OK on failure
 */
extern Std_ReturnType routine_check_memory_start(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/**
 * @brief Verify memory integrity using CRC/Checksum - REQUEST_RESULTS
 * @param option_record No parameters
 * @param option_record_len Length of option record
 * @param status_record Status byte + CRC32 (4 bytes)
 * @param status_record_len Length of status record (output)
 * @return E_OK on success, E_NOT_OK on failure
 */
extern Std_ReturnType routine_check_memory_request_results(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/**
 * @brief Verify application software integrity
 */
/**
 * @brief Verify application software integrity - START
 * @param option_record No parameters
 * @param option_record_len Length of option record
 * @param status_record Status byte (0x00=Valid, 0x01=Invalid)
 * @param status_record_len Length of status record (output)
 * @return E_OK on success, E_NOT_OK on failure
 */
extern Std_ReturnType routine_verify_application_integrity_start(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/**
 * @brief Check if programming session was completed successfully
 */
/**
 * @brief Check if programming session was completed successfully - START
 * @param option_record No parameters
 * @param option_record_len Length of option record
 * @param status_record Status byte (0x00=OK, 0x01=Failed)
 * @param status_record_len Length of status record (output)
 * @return E_OK on success, E_NOT_OK on failure
 */
extern Std_ReturnType routine_check_programming_integrity_start(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len
);

/* ========================================================================== */
/*                           Routine Name Constants                           */
/* ========================================================================== */

#define ROUTINE_ERASE_MEMORY                               0xFF00  /**< Erase flash memory region */
#define ROUTINE_CHECK_PROGRAMMING_DEPENDENCIES             0xFF01  /**< Check programming preconditions (voltage, temperature, etc.) */
#define ROUTINE_CHECK_MEMORY                               0x0202  /**< Verify memory integrity using CRC/Checksum */
#define ROUTINE_VERIFY_APPLICATION_INTEGRITY               0x0203  /**< Verify application software integrity */
#define ROUTINE_CHECK_PROGRAMMING_INTEGRITY                0x0204  /**< Check if programming session was completed successfully */

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
 * @brief Get routine registry
 * @param count Output: number of entries
 * @return Pointer to routine registry
 */
const uds_routine_entry_t* uds_routine_get_registry(uint16_t *count);

#endif /* ROUTINE_PBCFG_H */
