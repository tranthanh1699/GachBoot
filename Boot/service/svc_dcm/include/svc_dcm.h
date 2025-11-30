#ifndef SVC_DCM_H
#define SVC_DCM_H
#include "dev_com_tp.h"
#include "dev_common.h"

// AUTOSAR Standard Types
#ifndef STD_TYPES_H
typedef uint8_t Std_ReturnType;
#define E_OK        0x00u
#define E_NOT_OK    0x01u
#endif

// DCM Standard Return Values (AUTOSAR DCM)
#define DCM_E_PENDING                           0x10u  // Service processing is pending

#define SVC_DCM_CONFIG_USE_RTOS     DEV_CONFIG_COMMON_USE_RTOS
#define SVC_DCM_TICK_INTERVAL_MS    10u // DCM service tick interval in milliseconds

// UDS Service IDs (ISO 14229-1)
#define UDS_SID_DIAGNOSTIC_SESSION_CONTROL      0x10
#define UDS_SID_ECU_RESET                       0x11
#define UDS_SID_SECURITY_ACCESS                 0x27
#define UDS_SID_TESTER_PRESENT                  0x3E
#define UDS_SID_READ_DATA_BY_ID                 0x22
#define UDS_SID_WRITE_DATA_BY_ID                0x2E
#define UDS_SID_ROUTINE_CONTROL                 0x31
#define UDS_SID_REQUEST_DOWNLOAD                0x34
#define UDS_SID_TRANSFER_DATA                   0x36
#define UDS_SID_REQUEST_TRANSFER_EXIT           0x37

// UDS Negative Response Code
#define UDS_NRC_POSITIVE_RESPONSE                        0x00
#define UDS_NRC_GENERAL_REJECT                           0x10
#define UDS_NRC_SERVICE_NOT_SUPPORTED                    0x11
#define UDS_NRC_SUBFUNCTION_NOT_SUPPORTED                0x12
#define UDS_NRC_INCORRECT_MESSAGE_LENGTH                 0x13
#define UDS_NRC_CONDITIONS_NOT_CORRECT                   0x22
#define UDS_NRC_REQUEST_SEQUENCE_ERROR                   0x24
#define UDS_NRC_REQUEST_OUT_OF_RANGE                     0x31
#define UDS_NRC_SECURITY_ACCESS_DENIED                   0x33
#define UDS_NRC_INVALID_KEY                              0x35
#define UDS_NRC_EXCEED_NUMBER_OF_ATTEMPTS                0x36
#define UDS_NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED          0x37
#define UDS_NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING  0x78  // Response pending - need more time

// UDS Session Types (ISO 14229-1) - Session IDs
#define UDS_SESSION_DEFAULT                     0x01
#define UDS_SESSION_PROGRAMMING                 0x02
#define UDS_SESSION_EXTENDED_DIAGNOSTIC         0x03

// UDS Session Bitmask (for DID/RID access control)
#define UDS_SESSION_MASK_DEFAULT                (1u << 0)   // 0x00000001
#define UDS_SESSION_MASK_PROGRAMMING            (1u << 1)   // 0x00000002
#define UDS_SESSION_MASK_EXTENDED               (1u << 2)   // 0x00000004
#define UDS_SESSION_MASK_ALL                    0xFFFFFFFFu // All sessions

// UDS Security Levels (ISO 14229-1) - Security Level IDs
#define UDS_SECURITY_LEVEL_LOCKED               0x00
#define UDS_SECURITY_LEVEL_1                    0x01
#define UDS_SECURITY_LEVEL_2                    0x02

// UDS Security Bitmask (for DID/RID access control)
#define UDS_SECURITY_MASK_LOCKED                (1u << 0)   // 0x00000001
#define UDS_SECURITY_MASK_LEVEL_1               (1u << 1)   // 0x00000002
#define UDS_SECURITY_MASK_LEVEL_2               (1u << 2)   // 0x00000004
#define UDS_SECURITY_MASK_ALL                   0xFFFFFFFFu // All security levels

// UDS Timing Parameters (ISO 14229-2)
#define UDS_S3_SERVER_TIMEOUT_MS                5000u  // 5 seconds
#define UDS_P2_SERVER_MAX_MS                    50u    // 50ms max response time
#define UDS_P2_STAR_SERVER_MAX_MS               5000u  // 5s extended response time
/**
 * @brief Initialize the DCM service
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t svc_dcm_init(void); 

/**
 * @brief Run the DCM service
 */
#if SVC_DCM_CONFIG_USE_RTOS == 1
void svc_dcm_task(void * argument);
#else 
void svc_dcm_main_function(void);
#endif
/**
 * @brief Notify DCM service of received SDU
 * @param sdu_info_p Pointer to the received SDU information
 * @return dev_err_t Returns DEV_OK on success, or an appropriate error code on failure.
 */
dev_err_t svc_notify_rx_indication(dev_com_tp_sdu_t * sdu_info_p);

#endif // SVC_DCM_H