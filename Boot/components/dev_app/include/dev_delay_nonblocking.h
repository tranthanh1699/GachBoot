#ifndef DEV_DELAY_H
#define DEV_DELAY_H
#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Delay timer structure
 */
typedef struct {
    uint32_t start_time;
    uint32_t delay_ms;
    bool is_running;
} delay_timer_t;

/**
 * @brief Non-blocking delay
 * 
 * @param timer Pointer to timer (dùng static local variable)
 * @param ms Delay in milliseconds
 * @return true if delay expired, false otherwise
 */
bool dev_delay_nonblocking_ms(delay_timer_t *timer, uint32_t ms);

/**
 * @brief Reset delay to start time
 * @param timer Pointer to timer
 */
void dev_delay_nonblocking_reset(delay_timer_t *timer);

/**
 * @brief Stop delay timer
 * @param timer Pointer to timer
 */
void dev_delay_nonblocking_stop(delay_timer_t *timer);

#endif // DEV_DELAY_H