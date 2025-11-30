#ifndef DCMDSL_H
#define DCMDSL_H

#include "dev_common.h"
#include "dev_com_tp.h"

// Session management
typedef struct {
    uint8_t current_session;
    uint32_t s3_timeout_counter;
    bool session_active;
    uint8_t active_protocol;
} dcmdsl_session_context_t;

// Timing parameters
typedef struct {
    uint32_t p2_server_max;
    uint32_t p2_star_server_max;
    uint32_t s3_server_timeout;
} dcmdsl_timing_params_t;

/**
 * @brief Initialize DSL layer
 */
dev_err_t dcmdsl_init(void);

/**
 * @brief Main function - handle timing and session management
 * @param elapsed_ms Elapsed time in milliseconds
 */
void dcmdsl_main_function(uint32_t elapsed_ms);

/**
 * @brief Process incoming diagnostic request
 * @param sdu_info_p Pointer to SDU information
 * @return dev_err_t Error code
 */
dev_err_t dcmdsl_process_request(dev_com_tp_sdu_t * sdu_info_p);

/**
 * @brief Get current session
 * @return uint8_t Current session type
 */
uint8_t dcmdsl_get_current_session(void);

/**
 * @brief Set session
 * @param session Session type
 */
void dcmdsl_set_session(uint8_t session);

/**
 * @brief Reset S3 timer
 */
void dcmdsl_reset_s3_timer(void);

/**
 * @brief Check if session is active
 * @return bool True if non-default session is active
 */
bool dcmdsl_is_session_active(void);

/**
 * @brief Get timing parameters for current session
 * @return dcmdsl_timing_params_t* Pointer to timing parameters
 */
const dcmdsl_timing_params_t* dcmdsl_get_timing_params(void);

#endif // DCMDSL_H
