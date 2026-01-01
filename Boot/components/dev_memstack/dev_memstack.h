/**
 * @file dev_memstack.h
 * @brief Memory Stack Initialization API
 * 
 * This module provides a unified initialization interface for the entire
 * memory stack: FLS (Flash Driver) + FEE (Flash EEPROM Emulation) + NVM (NVM Manager)
 */

#ifndef DEV_MEMSTACK_H
#define DEV_MEMSTACK_H

#include "dev_common.h"

/**
 * @brief Initialize the entire memory stack
 * 
 * Initializes all memory layers in the correct order:
 * 1. FLS (Flash Low-level Driver)
 * 2. FEE (Flash EEPROM Emulation)
 * 3. NVM (Non-Volatile Memory Manager)
 * 
 * Uses pre-generated configurations from GenerateCode.
 * 
 * @return DEV_OK if all layers initialized successfully
 * @return Error code from first failed layer
 */
dev_err_t dev_memstack_init(void);

#endif /* DEV_MEMSTACK_H */
