/**
 * @file routine_callbacks.c
 * @brief Implementation of routine control callbacks
 * @date 2025-12-21
 * 
 * This file implements all routine callbacks declared in Routine_PBCfg.h
 */
#include "uds_rid_callback.h"
#include "dev_common.h"
#include "Routine_PBCfg.h"

CONFIG_LOG_TAG(ROUTINE_CB, true)

/* ========================================================================== */
/*                    Routine 0xFF00 - Erase Memory                           */
/* ========================================================================== */

/**
 * @brief Start erase memory routine
 */
Std_ReturnType routine_erase_memory_start(
    const uint8_t *option_record,
    uint16_t option_record_len,
    uint8_t *status_record,
    uint16_t *status_record_len)
{
    DBG_OUT_I("Erase Memory routine started");
    return E_OK;
}

void routine_erase_memory_proc(void)
{
    
}