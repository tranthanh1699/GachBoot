/**
 * @file dev_memstack.c
 * @brief Memory Stack Initialization Implementation
 */

#include "dev_memstack.h"
#include "dev_fls.h"
#include "dev_fee.h"
#include "dev_nvm.h"
#include "Fls_PBCfg.h"
#include "Fee_PBCfg.h"

CONFIG_LOG_TAG(MEMSTACK, true)

dev_err_t dev_memstack_init(void)
{
    dev_err_t result;
    
    DBG_OUT_I("Memory stack initialization started");
    
    /* Step 1: Initialize FLS (Flash Low-level Driver) */
    DBG_OUT_I("Initializing FLS...");
    result = dev_fls_init(&Fls_Config);
    if (result != DEV_OK) {
        DBG_OUT_E("FLS initialization failed: %d", result);
        return result;
    }
    DBG_OUT_I("FLS initialized successfully");
    
    /* Step 2: Initialize FEE (Flash EEPROM Emulation) */
    DBG_OUT_I("Initializing FEE...");
    result = dev_fee_init(&Fee_Config);
    if (result != DEV_OK) {
        DBG_OUT_E("FEE initialization failed: %d", result);
        return result;
    }
    DBG_OUT_I("FEE initialized successfully");
    
    /* Step 3: Initialize NVM (Non-Volatile Memory Manager) */
    DBG_OUT_I("Initializing NVM...");
    result = dev_nvm_init();
    if (result != DEV_OK) {
        DBG_OUT_E("NVM initialization failed: %d", result);
        return result;
    }
    DBG_OUT_I("NVM initialized successfully");
    
    DBG_OUT_I("Memory stack initialization completed");
    
    return DEV_OK;
}
