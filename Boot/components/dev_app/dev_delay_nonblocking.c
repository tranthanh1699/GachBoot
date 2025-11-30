#include "dev_delay_nonblocking.h"
#include "dev_common.h"

/**
 * @brief Non-blocking delay
 * 
 * @param timer Pointer to timer
 * @param ms Delay in milliseconds
 * @return true if delay expired, false otherwise
 */
bool dev_delay_nonblocking_ms(delay_timer_t *timer, uint32_t ms)
{
    if (timer == NULL) {
        return false;
    }
    
    // Start timer if not running or delay time changed
    if (!timer->is_running || timer->delay_ms != ms) {
        timer->start_time = DEV_GET_TICK_MS();
        timer->delay_ms = ms;
        timer->is_running = true;
    }
    
    // Check timeout
    uint32_t current_time = DEV_GET_TICK_MS();
    uint32_t elapsed = current_time - timer->start_time;
    
    if (elapsed >= timer->delay_ms) {
        // Timeout - auto reset
        timer->start_time = current_time;
        return true;
    }
    
    return false;
}

/**
 * @brief Reset delay to start time
 * 
 * @param timer Pointer to timer
 */
void dev_delay_nonblocking_reset(delay_timer_t *timer)
{
    if (timer == NULL) {
        return;
    }
    
    timer->start_time = DEV_GET_TICK_MS();
    timer->is_running = true;
}

/**
 * @brief Stop delay timer
 * @param timer Pointer to timer
 */
void dev_delay_nonblocking_stop(delay_timer_t *timer)
{
    if (timer == NULL) {
        return;
    }
    timer->is_running = false;
}
