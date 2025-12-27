/**
 * @file dev_os.h
 * @brief Operating System Abstraction Layer - Timer-based Task Scheduler
 * 
 * This module provides a lightweight task scheduler that can work with:
 * - Non-RTOS: Timer-based cyclic task execution
 * - RTOS: Can be extended for FreeRTOS/CMSIS-RTOS support
 * 
 * Features:
 * - Background task execution
 * - Cyclic tasks with configurable periods (1ms, 10ms, 20ms, 100ms, 1000ms)
 * - Task registration API
 * - Initialization task support
 */

#ifndef DEV_OS_H
#define DEV_OS_H

#include "dev_common.h"
#include <stdint.h>
#include <stdbool.h>

/* ===== Configuration Macros ===== */

/**
 * @brief Enable/Disable RTOS support
 * 0 = Non-RTOS (Timer-based)
 * 1 = RTOS (FreeRTOS/CMSIS-RTOS)
 */
#ifndef DEV_OS_CFG_USE_RTOS
#define DEV_OS_CFG_USE_RTOS    0
#endif

/**
 * @brief Base timer tick period in microseconds
 * Default: 1000us (1ms) - matches most common RTOS tick rates
 */
#define DEV_OS_BASE_TICK_US    1000u

/**
 * @brief Task cycle time macros (in milliseconds)
 * These macros define standard task periods
 */
#define DEV_OS_TASK_CYCLE_1MS      1u      // Fast task - 1ms
#define DEV_OS_TASK_CYCLE_10MS     10u     // Standard task - 10ms
#define DEV_OS_TASK_CYCLE_20MS     20u     // Standard task - 20ms  
#define DEV_OS_TASK_CYCLE_100MS    100u    // Slow task - 100ms
#define DEV_OS_TASK_CYCLE_1000MS   1000u   // Very slow task - 1000ms

/* ===== Type Definitions ===== */

/**
 * @brief Task function pointer type
 */
typedef void (*dev_os_task_func_t)(void);

/**
 * @brief Task cycle time enumeration
 */
typedef enum {
    DEV_OS_CYCLE_1MS = 0,      /**< 1ms cycle */
    DEV_OS_CYCLE_10MS,         /**< 10ms cycle */
    DEV_OS_CYCLE_20MS,         /**< 20ms cycle */
    DEV_OS_CYCLE_100MS,        /**< 100ms cycle */
    DEV_OS_CYCLE_1000MS,       /**< 1000ms cycle */
    DEV_OS_CYCLE_MAX
} dev_os_cycle_t;

/**
 * @brief OS statistics
 */
typedef struct {
    uint32_t tick_1ms;             /**< 1ms tick counter */
    uint32_t tick_10ms;            /**< 10ms tick counter */
    uint32_t tick_20ms;            /**< 20ms tick counter */
    uint32_t tick_100ms;           /**< 100ms tick counter */
    uint32_t tick_1000ms;          /**< 1000ms tick counter */
    uint32_t bg_task_executions;   /**< Background task execution counter */
} dev_os_stats_t;

/* ===== Public API Functions ===== */

/**
 * @brief Initialize the OS module
 * 
 * Must be called before any other OS functions.
 * Automatically runs initialization tasks from Os_PBCfg.
 * 
 * @return DEV_OK on success, DEV_ERR on failure
 */
dev_err_t dev_os_init(void);

/**
 * @brief Main scheduler function (Non-RTOS only)
 * 
 * This function should be called from the timer interrupt handler.
 * It processes all cyclic tasks according to their cycle times.
 * 
 * NOTE: For RTOS mode, this is handled automatically by the RTOS scheduler.
 */
void dev_os_tick_handler(void);

/**
 * @brief Process background tasks (Non-RTOS only)
 * 
 * This function should be called continuously in the main loop.
 * It executes all background tasks from Os_PBCfg.
 * 
 * NOTE: For RTOS mode, background tasks run in a dedicated low-priority thread.
 */
void dev_os_process_bg_tasks(void);

/**
 * @brief Get OS statistics
 * 
 * @param stats Pointer to statistics structure to fill
 * @return DEV_OK on success
 */
dev_err_t dev_os_get_stats(dev_os_stats_t *stats);

/**
 * @brief Get base tick counter (1ms)
 * 
 * @return Current tick count in milliseconds
 */
uint32_t dev_os_get_tick_ms(void);

#endif // DEV_OS_H