#ifndef BL_LOG_H
#define BL_LOG_H

#include "bl_config.h"

#if (BL_ENABLE_LOG != 0u)
void bl_log_info(const char *message);
void bl_log_error(const char *message);
#else
#define bl_log_info(message)            do { (void)(message); } while (0)
#define bl_log_error(message)           do { (void)(message); } while (0)
#endif

#endif /* BL_LOG_H */
