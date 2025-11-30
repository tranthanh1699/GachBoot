#include "dcmdsl.h"
#include "svc_dcm.h"
#include "dcmdsd/dcmdsd.h"

CONFIG_LOG_TAG(DCMDSL, true)

// Session context
static dcmdsl_session_context_t session_ctx = {
    .current_session = UDS_SESSION_DEFAULT,
    .s3_timeout_counter = 0,
    .session_active = false,
    .active_protocol = 0
};

// Timing parameters
static const dcmdsl_timing_params_t timing_params = {
    .p2_server_max = UDS_P2_SERVER_MAX_MS,
    .p2_star_server_max = UDS_P2_STAR_SERVER_MAX_MS,
    .s3_server_timeout = UDS_S3_SERVER_TIMEOUT_MS
};

/**
 * @brief Initialize DSL layer
 */
dev_err_t dcmdsl_init(void)
{
    DBG_OUT_I("DCMDSL Initialized");
    session_ctx.current_session = UDS_SESSION_DEFAULT;
    session_ctx.s3_timeout_counter = 0;
    session_ctx.session_active = false;
    return DEV_OK;
}

/**
 * @brief Main function - handle timing and session management
 */
void dcmdsl_main_function(uint32_t elapsed_ms)
{
    // S3 Server timeout management
    if (session_ctx.session_active && session_ctx.current_session != UDS_SESSION_DEFAULT) {
        session_ctx.s3_timeout_counter += elapsed_ms;
        
        if (session_ctx.s3_timeout_counter >= timing_params.s3_server_timeout) {
            // S3 timeout - return to default session
            DBG_OUT_W("S3 Timeout! Returning to Default Session");
            session_ctx.current_session = UDS_SESSION_DEFAULT;
            session_ctx.session_active = false;
            session_ctx.s3_timeout_counter = 0;
        }
    }
}

/**
 * @brief Process incoming diagnostic request
 */
dev_err_t dcmdsl_process_request(dev_com_tp_sdu_t * sdu_info_p)
{
    DEV_RETURN_ON_FALSE(sdu_info_p != NULL, DEV_ERR_INVALID_ARG, "SDU Info pointer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduBuffer != NULL, DEV_ERR_INVALID_ARG, "SDU Buffer is NULL");
    DEV_RETURN_ON_FALSE(sdu_info_p->SduSize > 0, DEV_ERR_INVALID_ARG, "SDU Size must be greater than zero");
    
    // Reset S3 timer on any valid request
    dcmdsl_reset_s3_timer();
    
    // Forward to DSD for service dispatching
    return dcmdsd_process_request(sdu_info_p);
}

/**
 * @brief Get current session
 */
uint8_t dcmdsl_get_current_session(void)
{
    return session_ctx.current_session;
}

/**
 * @brief Get active session (alias for compatibility)
 */
uint8_t dcmdsl_get_active_session(void)
{
    return session_ctx.current_session;
}

/**
 * @brief Set session
 */
void dcmdsl_set_session(uint8_t session)
{
    session_ctx.current_session = session;
    session_ctx.session_active = (session != UDS_SESSION_DEFAULT);
    session_ctx.s3_timeout_counter = 0;
    DBG_OUT_I("Session changed to: 0x%02X", session);
}

/**
 * @brief Reset S3 timer
 */
void dcmdsl_reset_s3_timer(void)
{
    session_ctx.s3_timeout_counter = 0;
}

/**
 * @brief Check if session is active
 */
bool dcmdsl_is_session_active(void)
{
    return session_ctx.session_active;
}

/**
 * @brief Get timing parameters
 */
const dcmdsl_timing_params_t* dcmdsl_get_timing_params(void)
{
    return &timing_params;
}
