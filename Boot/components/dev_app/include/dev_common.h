#ifndef DEV_COMMON_H
#define DEV_COMMON_H
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>


/* Include device header */
#include "stm32h7xx_hal.h"
#include "usbd_cdc_if.h"

/* Extern device variables */
extern TIM_HandleTypeDef htim17;
extern UART_HandleTypeDef huart1;
/* Device Configuration */
#define DEV_CONFIG_COMMON_USE_RTOS    0  // Set to 1 if using RTOS

/* User lib */
#include "dev_log.h"
#define DEV_LOG_BUFF(buff, len) HAL_UART_Transmit(&huart1, buff, len, 10);
#define DEV_LOG dev_log
#define DEV_LOG_HEX dev_log_hex

#define DEV_DELAY_MS(ms)     HAL_Delay(ms)
#define DEV_GET_TICK_MS()    HAL_GetTick()

typedef enum
{
	/* Common Error Codes */
    DEV_OK,							/* No error */
    DEV_ERR, 						/* Generic error */
	DEV_ERR_MODULE_NOT_INIT,		/* Module not initialized */
    DEV_ERR_INVALID_ARG,			/* Invalid argument */
	DEV_ERR_NO_MEM,					/* Out of memory */
    DEV_ERR_TIMEOUT,				/* Operation timed out */
	DEV_ERR_REGISTER_EVENT_FAIL, 	/* Event registration failed */
	DEV_ERR_ARRAY_OUT_OF_BOUND,		/* Array index out of bounds */
	DEV_ERR_CRC_FAIL,				/* CRC check failed */
	DEV_ERR_NOT_FOUND,				/* Item not found */
	DEV_ERR_PERMISSION_DENIED,		/* Permission denied */
	DEV_ERR_CRC,					/* CRC check failed */
	DEV_ERR_HARDWARE,				/* Hardware error */

	/* Specific Error Codes can be added here */
} dev_err_t;

/* ========== Common Macros ========== */
#define DEV_UNUSED(x)                   ((void)(x))
#define DEV_ARRAY_SIZE(a)               (sizeof(a) / sizeof((a)[0]))
#define DEV_MIN(a, b)                   ((a) < (b) ? (a) : (b))
#define DEV_MAX(a, b)                   ((a) > (b) ? (a) : (b))
#define DEV_CLAMP(val, min, max)        DEV_MAX(min, DEV_MIN(val, max))

// #define CONFIG_LOG_DEFAULT_LEVEL_NONE
#ifndef CONFIG_LOG_DEFAULT_LEVEL_NONE
#define CONFIG_LOG_TAG(name, enable)	static const char *const_TAG = #name ; 														\
										static const bool const_log_enabled = enable;
										
#define DBG_OUT(msg,...)			    if (const_log_enabled == true) { 															\
											DEV_LOG("---> [%s-%d]: " msg "\r\n", const_TAG, __LINE__, ##__VA_ARGS__); 				\
										}

#define DBG_OUT_RAW(msg,...)			if (const_log_enabled == true) { 															\
											DEV_LOG(msg, ##__VA_ARGS__); 															\
										}
									
#define DBG_OUT_E(msg,...)			    if (const_log_enabled == true) { 															\
											DEV_LOG("\033[0;31m---> [%s-%d]: " msg "\033[0m\r\n", const_TAG, __LINE__, ##__VA_ARGS__);\
										}

#define DBG_OUT_W(msg,...)              if (const_log_enabled == true) { 															\
											DEV_LOG("\033[0;33m---> [%s-%d]: " msg "\033[0m\r\n", const_TAG, __LINE__, ##__VA_ARGS__);\
										}
										

#define DBG_OUT_I(msg,...)              if (const_log_enabled == true) { 															\
											DEV_LOG("\033[0;32m---> [%s-%d]: " msg "\033[0m\r\n", const_TAG, __LINE__, ##__VA_ARGS__);\
										}

#define DBG_OUT_RAW_I(msg,...)          if (const_log_enabled == true) { 															\
											DEV_LOG("\033[0;32m" msg "\033[0m", ##__VA_ARGS__); 									\
										}

#define DBG_OUT_HEX(data, length)		if (const_log_enabled == true) { 															\
											DEV_LOG_HEX(data, length); 																\
										}

#else
#define CONFIG_LOG_TAG(name, enable)		
#define DBG_OUT(...)
#define DBG_OUT_RAW(...)
#define DBG_OUT_E(...)
#define DBG_OUT_W(...)
#define DBG_OUT_I(...)
#define DBG_OUT_RAW_I(...)
#endif

#define DEV_RETURN_ON_FALSE(a, err_code, msg, ...) do {            \
        if (!(a)) {                                                \
                DBG_OUT_E(msg "\n", ##__VA_ARGS__);                \
            return err_code;                                       \
        }                                                          \
    } while(0)


/* ========= DELAY NONBLOCKING ========= */
#include "dev_delay_nonblocking.h"
#define DEV_DELAY_CFG_NON_BLOCKING(timer)   	delay_timer_t timer = {0, 0, false};
#define DEV_DELAY_NON_BLOCKING_MS(timer, ms)   	dev_delay_nonblocking_ms(&timer, ms)
#define DEV_DELAY_NON_BLOCKING_RESET(timer)   	dev_delay_nonblocking_reset(&timer)
#define DEV_DELAY_NON_BLOCKING_STOP(timer)   	dev_delay_nonblocking_stop(&timer)


/**
 * @brief This function to check timeout
 * @param start_time Start time in milliseconds
 * @param timeout_ms Timeout duration in milliseconds
 * @return true if timeout occurred, false otherwise
 */
static inline bool dev_common_is_timeout(uint64_t start_time, uint32_t timeout_ms)
{
    return (DEV_GET_TICK_MS() - start_time) >= timeout_ms;
}




#endif