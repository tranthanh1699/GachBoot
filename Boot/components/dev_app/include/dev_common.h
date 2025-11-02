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

/* User lib */
#include "dev_log.h"
#define DEV_LOG dev_log

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
											char hex_buf[256];																		\
											int hex_idx = 0;																		\
											DEV_LOG("---> [%s-%d]: Hex Dump - Length: %d\r\n", const_TAG, __LINE__, length); 		\
											for (uint32_t i = 0; i < length; i++) {												\
												if (i % 16 == 0 && hex_idx > 0) {													\
													hex_buf[hex_idx] = '\0';														\
													DBG_OUT_RAW("%s\r\n", hex_buf);													\
													hex_idx = 0;																	\
												}																					\
												if (i % 16 == 0) {																	\
													hex_idx += snprintf(&hex_buf[hex_idx], sizeof(hex_buf) - hex_idx, "     ");	\
												}																					\
												hex_idx += snprintf(&hex_buf[hex_idx], sizeof(hex_buf) - hex_idx, "%02X ", data[i]);\
											}																						\
											if (hex_idx > 0) {																		\
												hex_buf[hex_idx] = '\0';															\
												DBG_OUT_RAW("%s\r\n", hex_buf);														\
											}																						\
										}

#else
#define CONFIG_LOG_TAG(name)				
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