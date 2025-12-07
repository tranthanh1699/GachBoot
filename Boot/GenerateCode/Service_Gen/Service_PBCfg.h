#ifndef SERVICE_PBCFG_H
#define SERVICE_PBCFG_H

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

/* Forward declarations */
#ifndef STD_TYPES_H
typedef uint8_t Std_ReturnType;
typedef uint8_t ErrorCode_t;
#define E_OK 0x00u
#define E_NOT_OK 0x01u
#endif

/* UDS message structure */
typedef struct {
    const uint8_t *request;     /* Request buffer (including SID) */
    uint16_t request_len;       /* Request length */
    uint8_t *response;          /* Response buffer (output) */
    uint16_t *response_len;     /* Response length (output) */
} uds_message_t;

/* Service handler function pointer type */
typedef Std_ReturnType (*uds_service_handler_t)(const uds_message_t *message, ErrorCode_t *error_code);

/* Service configuration structure */
typedef struct {
    uint8_t service_id;                 /* Service ID (SID) */
    uds_service_handler_t handler;      /* Handler function */
    uint32_t session_mask;              /* Allowed sessions bitmask */
    uint32_t security_mask;             /* Required security levels bitmask */
} dcm_service_config_t;

/* Extern handler function declarations */
extern Std_ReturnType uds_service_0x10_handler(const uds_message_t *message, ErrorCode_t *error_code);
extern Std_ReturnType uds_service_0x11_handler(const uds_message_t *message, ErrorCode_t *error_code);
extern Std_ReturnType uds_service_0x22_handler(const uds_message_t *message, ErrorCode_t *error_code);
extern Std_ReturnType uds_service_0x27_handler(const uds_message_t *message, ErrorCode_t *error_code);
extern Std_ReturnType uds_service_0x2E_handler(const uds_message_t *message, ErrorCode_t *error_code);
extern Std_ReturnType uds_service_0x31_handler(const uds_message_t *message, ErrorCode_t *error_code);
extern Std_ReturnType uds_service_0x3E_handler(const uds_message_t *message, ErrorCode_t *error_code);

/* Service configuration table */
#define DCM_SERVICE_COUNT 7u
extern const dcm_service_config_t dcm_service_config_table[DCM_SERVICE_COUNT];

#endif /* SERVICE_PBCFG_H */
