#ifndef DEV_LOG_H
#define DEV_LOG_H
#include "stdint.h"
/**
 * @brief This function to log message
 * @param str The format string
 * @param ... The variable arguments
 */
void dev_log(const char* str, ...); 
void dev_log_hex(const uint8_t* data, uint32_t length); 
#endif // DEV_LOG_H