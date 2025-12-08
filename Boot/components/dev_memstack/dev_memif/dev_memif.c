#include "dev_memif.h"
#include "dev_fee.h"
#include "Fee_Cfg.h"
#include <string.h>

CONFIG_LOG_TAG(DEV_MEMIF, true)

// MemIf Runtime State
typedef struct {
    bool initialized;
    dev_memif_status_t status;
    dev_memif_status_t job_result;
    dev_memif_mode_t mode;
} dev_memif_state_t;

static dev_memif_state_t memif_state = {0};

/**
 * @brief Initialize MemIf module
 */
dev_err_t dev_memif_init(void)
{
    if (memif_state.initialized) {
        return DEV_OK;
    }
    
    DBG_OUT_I("Initializing MemIf...");
    
    memset(&memif_state, 0, sizeof(memif_state));
    
    // Initialize underlying Fee driver with default config
    dev_err_t err = dev_fee_init(NULL);  // NULL = use default Fee_Config
    if (err != DEV_OK) {
        DBG_OUT_E("Fee init failed");
        memif_state.status = DEV_MEMIF_UNINIT;
        return err;
    }
    
    memif_state.initialized = true;
    memif_state.status = DEV_MEMIF_JOB_OK;
    memif_state.job_result = DEV_MEMIF_JOB_OK;
    memif_state.mode = DEV_MEMIF_MODE_FAST;
    
    DBG_OUT_I("MemIf initialized");
    return DEV_OK;
}

/**
 * @brief Read data from memory
 */
dev_err_t dev_memif_read(uint32_t address, uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(memif_state.initialized, DEV_ERR_MODULE_NOT_INIT, "MemIf not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    
    memif_state.status = DEV_MEMIF_BUSY;
    
    // Route to Fee
    dev_err_t err = dev_fee_read(address, data, length);
    
    if (err == DEV_OK) {
        memif_state.status = DEV_MEMIF_JOB_OK;
        memif_state.job_result = DEV_MEMIF_JOB_OK;
    } else {
        memif_state.status = DEV_MEMIF_JOB_FAILED;
        memif_state.job_result = DEV_MEMIF_JOB_FAILED;
    }
    
    return err;
}

/**
 * @brief Write data to memory
 */
dev_err_t dev_memif_write(uint32_t address, const uint8_t *data, uint32_t length, 
                           uint32_t *out_physical_address)
{
    DEV_RETURN_ON_FALSE(memif_state.initialized, DEV_ERR_MODULE_NOT_INIT, "MemIf not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    
    memif_state.status = DEV_MEMIF_BUSY;
    
    // Route to Fee - virtual address is managed by Fee (use 0 for auto-allocation)
    dev_err_t err = dev_fee_write(address, data, length, out_physical_address);
    
    if (err == DEV_OK) {
        memif_state.status = DEV_MEMIF_JOB_OK;
        memif_state.job_result = DEV_MEMIF_JOB_OK;
    } else {
        memif_state.status = DEV_MEMIF_JOB_FAILED;
        memif_state.job_result = DEV_MEMIF_JOB_FAILED;
    }
    
    return err;
}

/**
 * @brief Erase memory block
 * @note Fee doesn't have erase_all API - erase is handled automatically during sector switch
 */
dev_err_t dev_memif_erase(uint32_t address, uint32_t length)
{
    DEV_RETURN_ON_FALSE(memif_state.initialized, DEV_ERR_MODULE_NOT_INIT, "MemIf not initialized");
    
    // Fee manages erase automatically during sector switching
    // This is a no-op for Fee - return OK
    DBG_OUT_W("MemIf erase is no-op for Fee (automatic sector management)");
    
    memif_state.status = DEV_MEMIF_JOB_OK;
    memif_state.job_result = DEV_MEMIF_JOB_OK;
    
    return DEV_OK;
}

/**
 * @brief Invalidate memory block
 */
dev_err_t dev_memif_invalidate(uint32_t address)
{
    DEV_RETURN_ON_FALSE(memif_state.initialized, DEV_ERR_MODULE_NOT_INIT, "MemIf not initialized");
    
    // Note: Invalidation can be implemented in Fee if needed
    memif_state.status = DEV_MEMIF_JOB_OK;
    memif_state.job_result = DEV_MEMIF_JOB_OK;
    
    return DEV_OK;
}

/**
 * @brief Get MemIf status
 */
dev_memif_status_t dev_memif_get_status(void)
{
    return memif_state.status;
}

/**
 * @brief Get job result
 */
dev_memif_status_t dev_memif_get_job_result(void)
{
    return memif_state.job_result;
}

/**
 * @brief Set device mode
 */
dev_err_t dev_memif_set_mode(dev_memif_mode_t mode)
{
    DEV_RETURN_ON_FALSE(memif_state.initialized, DEV_ERR_MODULE_NOT_INIT, "MemIf not initialized");
    
    memif_state.mode = mode;
    DBG_OUT_I("MemIf mode set to %s", mode == DEV_MEMIF_MODE_FAST ? "FAST" : "SLOW");
    
    return DEV_OK;
}
