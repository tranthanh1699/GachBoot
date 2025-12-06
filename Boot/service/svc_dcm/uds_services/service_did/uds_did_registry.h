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
#include "svc_dcm.h"
#include "dev_common.h"
#include "DID_PBCfg.h"


/* Service IDs */
#ifndef UDS_SID_READ_DATA_BY_IDENTIFIER
#define UDS_SID_READ_DATA_BY_IDENTIFIER         0x22
#define UDS_SID_WRITE_DATA_BY_IDENTIFIER        0x2E
#define UDS_SID_IO_CONTROL_BY_IDENTIFIER        0x2F
#endif

#ifdef __cplusplus
extern "C" {
#endif

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

#ifdef __cplusplus
}
#endif

#endif /* UDS_DID_REGISTRY_H */
