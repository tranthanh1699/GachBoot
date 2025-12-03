/**
 * @file uds_did_callbacks.h
 * @brief DID Callback Function Declarations
 * 
 * This file declares all DID read/write/io_control callback functions
 * referenced in the DID registry.
 * 
 * @author GachBoot Team
 * @date 2024
 */

#ifndef UDS_DID_CALLBACKS_H
#define UDS_DID_CALLBACKS_H

#include <stdint.h>
#include "dev_common.h"
#include "svc_dcm.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================== */
/*                         Read Callback Declarations                         */
/* ========================================================================== */

/**
 * @brief Read VIN (Vehicle Identification Number) - DID 0xF190
 * @param data Output buffer (17 bytes guaranteed)
 * @return Std_ReturnType E_OK if success
 */
extern Std_ReturnType did_read_vin(uint8_t *data);

/**
 * @brief Read Boot Software ID - DID 0xF183
 * @param data Output buffer (11 bytes guaranteed)
 * @return Std_ReturnType E_OK if success
 */
extern Std_ReturnType did_read_boot_sw_id(uint8_t *data);

/**
 * @brief Read Application Software ID - DID 0xF184
 * @param data Output buffer (10 bytes guaranteed)
 * @return Std_ReturnType E_OK if success
 */
extern Std_ReturnType did_read_app_sw_id(uint8_t *data);

/**
 * @brief Read ECU Serial Number - DID 0xF18C
 * @param data Output buffer (4 bytes guaranteed)
 * @return Std_ReturnType E_OK if success
 */
extern Std_ReturnType did_read_ecu_serial(uint8_t *data);

/**
 * @brief Read ECU Configuration - DID 0xF100
 * @param data Output buffer (2 bytes guaranteed)
 * @return Std_ReturnType E_OK if success
 */
extern Std_ReturnType did_read_ecu_config(uint8_t *data);

/* ========================================================================== */
/*                        Write Callback Declarations                         */
/* ========================================================================== */

/**
 * @brief Write Programming Fingerprint - DID 0xF15A
 * @param data Input data (1-32 bytes, pre-validated)
 * @param data_len Length of input data
 * @return Std_ReturnType E_OK if success, E_NOT_OK if validation failed
 */
extern Std_ReturnType did_write_fingerprint(const uint8_t *data, uint16_t data_len);

/**
 * @brief Write Programming Date - DID 0xF199
 * @param data Input data (4 bytes: YYYY/MM/DD, pre-validated length)
 * @param data_len Length of input data (always 4)
 * @return Std_ReturnType E_OK if success, E_NOT_OK if semantic validation failed
 */
Std_ReturnType did_write_programming_date(const uint8_t *data, uint16_t data_len);

/**
 * @brief Write ECU Configuration - DID 0xF100
 * @param data Input data (2 bytes, pre-validated length)
 * @param data_len Length of input data (always 2)
 * @return Std_ReturnType E_OK if success, E_NOT_OK if validation failed
 */
Std_ReturnType did_write_ecu_config(const uint8_t *data, uint16_t data_len);

/* ========================================================================== */
/*                    IO Control Callback Declarations (Future)               */
/* ========================================================================== */

/* Add IO control callbacks here when implementing Service 0x2F */

#ifdef __cplusplus
}
#endif

#endif /* UDS_DID_CALLBACKS_H */
