/**
 * @file uds_did_registry.h
 * @brief Unified DID Registry for UDS Services (0x22, 0x2E, 0x2F)
 * 
 * This module provides a centralized DID configuration system that supports
 * multiple UDS services (Read/Write/IO Control) with per-service callbacks
 * and access control.
 * 
 * Features:
 * - Single DID configuration for all services
 * - Per-service callback functions (read/write/io_control)
 * - Per-service session & security masks
 * - Fixed/variable length support
 * - Semantic data validation
 * 
 * @author GachBoot Team
 * @date 2024
 */

#ifndef UDS_DID_REGISTRY_H
#define UDS_DID_REGISTRY_H

#include <stdint.h>
#include <stdbool.h>

// Forward declare Std_ReturnType if not already defined
#ifndef STD_TYPES_H
typedef uint8_t Std_ReturnType;
#define E_OK        0x00u
#define E_NOT_OK    0x01u
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================== */
/*                              Type Definitions                              */
/* ========================================================================== */

/**
 * @brief DID read callback function type
 * 
 * @param data      Output buffer to fill with DID data
 * @return Std_ReturnType E_OK if success, E_NOT_OK if failed
 * 
 * @note Callback must fill 'data' buffer with DID value
 *       Buffer size is guaranteed to be >= expected_length
 */
typedef Std_ReturnType (*uds_did_read_callback_t)(uint8_t *data);

/**
 * @brief DID write callback function type
 * 
 * @param data      Input data to write
 * @param length    Length of input data
 * @return Std_ReturnType E_OK if success, E_NOT_OK if failed
 * 
 * @note Callback must validate and process input data
 *       Length is pre-validated against expected_length range
 */
typedef Std_ReturnType (*uds_did_write_callback_t)(const uint8_t *data, uint16_t length);

/**
 * @brief DID IO control callback function type (Future: Service 0x2F)
 * 
 * @param control_option    Control option parameter
 * @param control_param     Control parameter data
 * @param param_length      Length of control parameter
 * @param state_record      Output buffer for control state record
 * @param state_length      Output length of state record
 * @return Std_ReturnType E_OK if success, E_NOT_OK if failed
 */
typedef Std_ReturnType (*uds_did_io_control_callback_t)(
    uint8_t control_option,
    const uint8_t *control_param,
    uint16_t param_length,
    uint8_t *state_record,
    uint16_t *state_length
);

/**
 * @brief DID dynamic length getter function type
 * 
 * @return uint16_t Current length of DID data (for variable length DIDs)
 * 
 * @note Only used if expected_length = 0 (variable length)
 *       Return 0 if DID has no data available
 */
typedef uint16_t (*uds_did_length_getter_t)(void);

/**
 * @brief DID registry entry structure
 * 
 * This structure defines a complete DID configuration including:
 * - Basic properties (ID, length)
 * - Service-specific callbacks
 * - Service-specific access control (session/security)
 * - Data validation settings
 */
typedef struct {
    /* ===== Basic DID Properties ===== */
    uint16_t did;                           /**< Data Identifier (0x0000 - 0xFFFF) */
    uint16_t expected_length;               /**< Expected data length (0 = variable) */
    uint16_t min_length;                    /**< Minimum length (for variable DIDs) */
    uint16_t max_length;                    /**< Maximum length (for variable DIDs) */
    
    /* ===== Service 0x22 (Read Data By Identifier) ===== */
    struct {
        uds_did_read_callback_t callback;   /**< Read callback function */
        uds_did_length_getter_t length_getter; /**< Dynamic length getter (if variable) */
        uint32_t session_mask;              /**< Allowed sessions (UDS_SESSION_MASK_xxx) */
        uint32_t security_mask;             /**< Required security level (UDS_SECURITY_MASK_xxx) */
    } read_config;
    
    /* ===== Service 0x2E (Write Data By Identifier) ===== */
    struct {
        uds_did_write_callback_t callback;  /**< Write callback function */
        uint32_t session_mask;              /**< Allowed sessions */
        uint32_t security_mask;             /**< Required security level */
        bool semantic_validation;           /**< Enable semantic validation */
    } write_config;
    
    /* ===== Service 0x2F (Input Output Control By Identifier) - Future ===== */
    struct {
        uds_did_io_control_callback_t callback; /**< IO control callback */
        uint32_t session_mask;              /**< Allowed sessions */
        uint32_t security_mask;             /**< Required security level */
        uint8_t supported_options;          /**< Supported control options bitmask */
    } io_control_config;
    
} uds_did_entry_t;

/* ========================================================================== */
/*                            Function Prototypes                             */
/* ========================================================================== */

/**
 * @brief Find DID entry in registry
 * 
 * @param did       Data Identifier to search for
 * @return const uds_did_entry_t* Pointer to DID entry, or NULL if not found
 */
const uds_did_entry_t* uds_did_registry_find(uint16_t did);

/**
 * @brief Get total number of DIDs in registry
 * 
 * @return uint16_t Number of registered DIDs
 */
uint16_t uds_did_registry_get_count(void);

/**
 * @brief Check if DID supports specific service
 * 
 * @param did       Data Identifier
 * @param service   Service ID (0x22, 0x2E, 0x2F)
 * @return bool true if DID supports service, false otherwise
 */
bool uds_did_supports_service(uint16_t did, uint8_t service);

/**
 * @brief Validate DID access for service in current session/security
 * 
 * @param did       Data Identifier
 * @param service   Service ID (0x22, 0x2E, 0x2F)
 * @param session_mask   Current session mask (UDS_SESSION_MASK_xxx)
 * @param security_mask  Current security mask (UDS_SECURITY_MASK_xxx)
 * @return Std_ReturnType E_OK if allowed, E_NOT_OK if denied
 */
Std_ReturnType uds_did_validate_access(
    uint16_t did,
    uint8_t service,
    uint32_t session_mask,
    uint32_t security_mask
);

/**
 * @brief Get DID length (handles both fixed and variable length)
 * 
 * @param did       Data Identifier
 * @param service   Service ID (0x22, 0x2E, 0x2F)
 * @return uint16_t DID data length in bytes, 0 if DID not found
 */
uint16_t uds_did_get_length(uint16_t did, uint8_t service);

/**
 * @brief Validate DID data length
 * 
 * @param did       Data Identifier
 * @param service   Service ID (0x22, 0x2E, 0x2F)
 * @param length    Length to validate
 * @return bool true if length is valid, false otherwise
 */
bool uds_did_validate_length(uint16_t did, uint8_t service, uint16_t length);

/* ========================================================================== */
/*                         UDS Service & Mask Definitions                     */
/* ========================================================================== */
/* Note: Session and Security masks are defined in svc_dcm.h */

/* Service IDs */
#ifndef UDS_SID_READ_DATA_BY_IDENTIFIER
#define UDS_SID_READ_DATA_BY_IDENTIFIER         0x22
#define UDS_SID_WRITE_DATA_BY_IDENTIFIER        0x2E
#define UDS_SID_IO_CONTROL_BY_IDENTIFIER        0x2F
#endif

#ifdef __cplusplus
}
#endif

#endif /* UDS_DID_REGISTRY_H */
