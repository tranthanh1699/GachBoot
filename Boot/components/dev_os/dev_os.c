/**
 * @file dev_os.c
 * @brief Operating System Abstraction Layer - Implementation
 */

#include "dev_os.h"
#include "dev_common.h"
#include "Os_PBCfg.h"
#include "stm32h7xx_hal_tim.h"
#include <string.h>

CONFIG_LOG_TAG(DEV_OS, true)

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef* htim)
{
    if(htim->Instance == TIM17) {
        dev_os_tick_handler();
    }
}


/**
 * @brief OS module state
 */
typedef struct {
    bool initialized;
    
    // Statistics
    dev_os_stats_t stats;
    
    // Cycle counters for non-RTOS scheduling
    uint32_t counter_1ms;
    uint32_t counter_10ms;
    uint32_t counter_20ms;
    uint32_t counter_100ms;
    uint32_t counter_1000ms;
} dev_os_state_t;

/* ===== Private Variables ===== */

static dev_os_state_t g_os_state = {0};

/* ===== Private Helper Functions ===== */

/**
 * @brief Process all cyclic tasks for a specific cycle time
 * @note Calls generated config API with converted cycle type
 */
static void process_cyclic_tasks(dev_os_cycle_t cycle)
{
    // Convert dev_os_cycle_t to os_cfg_cycle_t and call generated API
    os_config_run_cyclic_tasks((os_cfg_cycle_t)cycle);
}

/* ===== Public API Implementation ===== */

dev_err_t dev_os_init(void)
{
    if (g_os_state.initialized) {
        DBG_OUT_W("OS already initialized");
        return DEV_OK;
    }
    
    // Clear state
    memset(&g_os_state, 0, sizeof(dev_os_state_t));
    
    // Initialize counters
    g_os_state.counter_1ms = 0;
    g_os_state.counter_10ms = 0;
    g_os_state.counter_20ms = 0;
    g_os_state.counter_100ms = 0;
    g_os_state.counter_1000ms = 0;
    
    g_os_state.initialized = true;
    
    DBG_OUT_I("OS initialized (Non-RTOS mode)");
    
    // Run initialization tasks from generated config
    DBG_OUT_I("Running init tasks...");
    os_config_run_init_tasks();
    HAL_TIM_Base_Start_IT(&htim17);
    return DEV_OK;
}

void dev_os_tick_handler(void)
{
    // Increment 1ms counter
    g_os_state.counter_1ms++;
    g_os_state.stats.tick_1ms++;
    
    // Process 1ms tasks
    process_cyclic_tasks(DEV_OS_CYCLE_1MS);
    
    // Check 10ms cycle
    if (g_os_state.counter_1ms >= 10) {
        g_os_state.counter_10ms++;
        g_os_state.stats.tick_10ms++;
        process_cyclic_tasks(DEV_OS_CYCLE_10MS);
        
        // Reset counter but keep remainder for accurate timing
        g_os_state.counter_1ms = 0;
    }
    
    // Check 20ms cycle
    if (g_os_state.counter_10ms >= 2) {
        g_os_state.counter_20ms++;
        g_os_state.stats.tick_20ms++;
        process_cyclic_tasks(DEV_OS_CYCLE_20MS);
        
        g_os_state.counter_10ms = 0;
    }
    
    // Check 100ms cycle
    if (g_os_state.counter_20ms >= 5) {
        g_os_state.counter_100ms++;
        g_os_state.stats.tick_100ms++;
        process_cyclic_tasks(DEV_OS_CYCLE_100MS);
        
        g_os_state.counter_20ms = 0;
    }
    
    // Check 1000ms cycle
    if (g_os_state.counter_100ms >= 10) {
        g_os_state.counter_1000ms++;
        g_os_state.stats.tick_1000ms++;
        process_cyclic_tasks(DEV_OS_CYCLE_1000MS);
        
        g_os_state.counter_100ms = 0;
    }
}

void dev_os_process_bg_tasks(void)
{
    // Call generated config API to execute all background tasks
    os_config_run_bg_tasks();
    
    g_os_state.stats.bg_task_executions++;
}

dev_err_t dev_os_get_stats(dev_os_stats_t *stats)
{
    if (!g_os_state.initialized) {
        return DEV_ERR_MODULE_NOT_INIT;
    }
    
    if (stats == NULL) {
        return DEV_ERR_INVALID_ARG;
    }
    
    memcpy(stats, &g_os_state.stats, sizeof(dev_os_stats_t));
    
    return DEV_OK;
}

uint32_t dev_os_get_tick_ms(void)
{
    return g_os_state.stats.tick_1ms;
}

