#include "Service_PBCfg.h"

/* Service configuration table */
const dcm_service_config_t dcm_service_config_table[DCM_SERVICE_COUNT] = {
    /* Service 0x10 - 0x10 */
    {
        .service_id = 0x10,
        .handler = uds_service_0x10_handler,
        .session_mask = 14u,  /* DCM_DEFAULT_SESSION, DCM_PROGRAMMING_SESSION, DCM_EXTENDED_SESSION */
        .security_mask = 0u  /*  */
    },
    /* Service 0x22 - 0x22 */
    {
        .service_id = 0x22,
        .handler = uds_service_0x22_handler,
        .session_mask = 14u,  /* DCM_DEFAULT_SESSION, DCM_PROGRAMMING_SESSION, DCM_EXTENDED_SESSION */
        .security_mask = 0u  /*  */
    },
    /* Service 0x27 - 0x27 */
    {
        .service_id = 0x27,
        .handler = uds_service_0x27_handler,
        .session_mask = 12u,  /* DCM_EXTENDED_SESSION, DCM_PROGRAMMING_SESSION */
        .security_mask = 0u  /*  */
    },
    /* Service 0x2E - 0x2E */
    {
        .service_id = 0x2E,
        .handler = uds_service_0x2E_handler,
        .session_mask = 12u,  /* DCM_EXTENDED_SESSION, DCM_PROGRAMMING_SESSION */
        .security_mask = 2u  /* Level 1 */
    },
    /* Service 0x3E - 0x3E */
    {
        .service_id = 0x3E,
        .handler = uds_service_0x3E_handler,
        .session_mask = 14u,  /* DCM_DEFAULT_SESSION, DCM_PROGRAMMING_SESSION, DCM_EXTENDED_SESSION */
        .security_mask = 0u  /*  */
    },
    /* Service 0x11 - 0x11 */
    {
        .service_id = 0x11,
        .handler = uds_service_0x11_handler,
        .session_mask = 14u,  /* DCM_DEFAULT_SESSION, DCM_PROGRAMMING_SESSION, DCM_EXTENDED_SESSION */
        .security_mask = 0u  /*  */
    },
    /* Service 0x31 - 0x31 */
    {
        .service_id = 0x31,
        .handler = uds_service_0x31_handler,
        .session_mask = 12u,  /* DCM_PROGRAMMING_SESSION, DCM_EXTENDED_SESSION */
        .security_mask = 0u  /*  */
    },
    /* Service 0x36 - 0x36 */
    {
        .service_id = 0x36,
        .handler = uds_service_0x36_handler,
        .session_mask = 4u,  /* DCM_PROGRAMMING_SESSION */
        .security_mask = 6u  /* Level 1, Level 2 */
    },
    /* Service 0x34 - 0x34 */
    {
        .service_id = 0x34,
        .handler = uds_service_0x34_handler,
        .session_mask = 4u,  /* DCM_PROGRAMMING_SESSION */
        .security_mask = 6u  /* Level 1, Level 2 */
    },
    /* Service 0x37 - 0x37 */
    {
        .service_id = 0x37,
        .handler = uds_service_0x37_handler,
        .session_mask = 4u,  /* DCM_PROGRAMMING_SESSION */
        .security_mask = 6u  /* Level 1, Level 2 */
    }
};
