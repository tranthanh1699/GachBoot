#include "dcmdsl.h"
#include "svc_dcm.h"
#include "dcmdsd/dcmdsd.h"
#include "../uds_services/service_0x27/uds_security_config.h"

CONFIG_LOG_TAG(DCMDSL, true)

/**
 * @brief Session change callback - Reset security on session change
 */
static void session_change_security_reset_callback(uint8_t old_session, uint8_t new_session)
{
    // Reset security on session change (ISO 14229-1)
    // Exception: Default -> Programming keeps security
    if (!(old_session == UDS_SESSION_DEFAULT && new_session == UDS_SESSION_PROGRAMMING)) {
        uds_security_reset_all();
        DBG_OUT_I("Security reset due to session change");
    }
}

// Session context
static dcmdsl_session_context_t session_ctx = {
    .current_session = UDS_SESSION_DEFAULT,
    .s3_timeout_counter = 0,
    .session_active = false,
    .active_protocol = 0
};

// Session change callbacks
static dcmdsl_session_change_callback_t session_callbacks[DCMDSL_MAX_SESSION_CALLBACKS];
static uint8_t session_callback_count = 0;

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
    
    // Register built-in session change callbacks
    dcmdsl_register_session_callback(session_change_security_reset_callback);
    
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
            
            // Use dcmdsl_set_session to trigger callbacks
            dcmdsl_set_session(UDS_SESSION_DEFAULT);
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
uint8_t dcmdsl_get_session(void)
{
    return session_ctx.current_session;
}

/**
 * @brief Notify session change callbacks
 */
static void notify_session_callbacks(uint8_t old_session, uint8_t new_session)
{
    for (uint8_t i = 0; i < session_callback_count; i++) {
        if (session_callbacks[i] != NULL) {
            session_callbacks[i](old_session, new_session);
        }
    }
}

/**
 * @brief Set session
 */
void dcmdsl_set_session(uint8_t session)
{
    uint8_t old_session = session_ctx.current_session;
    
    if (old_session != session) {
        session_ctx.current_session = session;
        session_ctx.session_active = (session != UDS_SESSION_DEFAULT);
        session_ctx.s3_timeout_counter = 0;
        
        DBG_OUT_I("Session changed: 0x%02X -> 0x%02X", old_session, session);
        
        // Notify all registered callbacks
        notify_session_callbacks(old_session, session);
    }
}

/**
 * @brief Register session change callback
 */
dev_err_t dcmdsl_register_session_callback(dcmdsl_session_change_callback_t callback)
{
    DEV_RETURN_ON_FALSE(callback != NULL, DEV_ERR_INVALID_ARG, "Callback is NULL");
    DEV_RETURN_ON_FALSE(session_callback_count < DCMDSL_MAX_SESSION_CALLBACKS, 
                       DEV_ERR_NO_MEM, "Max callbacks reached");
    
    // Check if already registered
    for (uint8_t i = 0; i < session_callback_count; i++) {
        if (session_callbacks[i] == callback) {
            return DEV_OK;  // Already registered
        }
    }
    
    session_callbacks[session_callback_count++] = callback;
    DBG_OUT_I("Session callback registered (%d/%d)", session_callback_count, DCMDSL_MAX_SESSION_CALLBACKS);
    return DEV_OK;
}

/**
 * @brief Unregister session change callback
 */
dev_err_t dcmdsl_unregister_session_callback(dcmdsl_session_change_callback_t callback)
{
    DEV_RETURN_ON_FALSE(callback != NULL, DEV_ERR_INVALID_ARG, "Callback is NULL");
    
    for (uint8_t i = 0; i < session_callback_count; i++) {
        if (session_callbacks[i] == callback) {
            // Shift remaining callbacks
            for (uint8_t j = i; j < session_callback_count - 1; j++) {
                session_callbacks[j] = session_callbacks[j + 1];
            }
            session_callbacks[--session_callback_count] = NULL;
            DBG_OUT_I("Session callback unregistered (%d/%d)", session_callback_count, DCMDSL_MAX_SESSION_CALLBACKS);
            return DEV_OK;
        }
    }
    
    return DEV_ERR_NOT_FOUND;
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
