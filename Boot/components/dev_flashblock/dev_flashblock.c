/**
 * @file dev_flashblock.c
 * @brief Flash block management with 3-step erase state machine
 */

#include "dev_flashblock.h"
#include "dev_fls.h"
#include "dev_log.h"
#include "Fls_PBCfg.h"
#include <string.h>

/* ===== Private Data Structures ===== */

/**
 * @brief Internal erase operation context
 */
typedef struct {
    uint32_t start_address;        /**< Start address of erase operation */
    uint32_t length;               /**< Length in bytes to erase */
    uint32_t first_sector_idx;     /**< Index of first sector to erase */
    uint32_t last_sector_idx;      /**< Index of last sector to erase */
    uint32_t current_sector_idx;   /**< Current sector being erased */
    uint32_t total_sectors;        /**< Total number of sectors to erase */
} erase_context_t;

/**
 * @brief Flash block module state
 */
typedef struct {
    bool initialized;                           /**< Module initialization flag */
    dev_flashblock_config_t config;             /**< Configuration */
    dev_flashblock_erase_state_t erase_state;   /**< Current erase state */
    erase_context_t erase_ctx;                  /**< Erase context */
} flashblock_state_t;

/* ===== Private Variables ===== */

static flashblock_state_t g_flashblock_state = {
    .initialized = false,
    .erase_state = DEV_FLASHBLOCK_ERASE_IDLE
};

/* ===== Private Helper Functions ===== */

/**
 * @brief Check if address is in valid flash range
 */
static bool is_valid_flash_address(uint32_t address, uint32_t length)
{
    if (length == 0) {
        return false;
    }
    
    uint32_t end_address = address + length - 1;
    
    // Check if entire range is within flash memory region
    for (uint32_t i = 0; i < Fls_SectorCount; i++) {
        uint32_t sector_start = Fls_SectorTable[i].base_address;
        uint32_t sector_end = sector_start + Fls_SectorTable[i].size - 1;
        
        // Check if range starts in this sector
        if (address >= sector_start && address <= sector_end) {
            // Check if range also ends within valid flash space
            if (end_address <= sector_end) {
                return true;
            }
            // Range spans multiple sectors - need to verify continuity
            // For now, allow it if it doesn't exceed last sector
            if (i < Fls_SectorCount - 1) {
                continue;
            }
        }
    }
    
    // Check last sector
    if (Fls_SectorCount > 0) {
        uint32_t last_idx = Fls_SectorCount - 1;
        uint32_t last_sector_end = Fls_SectorTable[last_idx].base_address + 
                                   Fls_SectorTable[last_idx].size - 1;
        if (end_address <= last_sector_end) {
            return true;
        }
    }
    
    return false;
}

/**
 * @brief Find sector index containing the given address
 */
static int32_t find_sector_by_address(uint32_t address)
{
    for (uint32_t i = 0; i < Fls_SectorCount; i++) {
        uint32_t sector_start = Fls_SectorTable[i].base_address;
        uint32_t sector_end = sector_start + Fls_SectorTable[i].size;
        
        if (address >= sector_start && address < sector_end) {
            return (int32_t)i;
        }
    }
    
    return -1;  // Not found
}

/**
 * @brief Determine which sectors need to be erased
 * 
 * @param address Start address
 * @param length Length in bytes
 * @param first_sector Output: Index of first sector to erase
 * @param last_sector Output: Index of last sector to erase
 * @return true if sectors found, false otherwise
 */
static bool determine_erase_sectors(uint32_t address, uint32_t length,
                                     uint32_t *first_sector, uint32_t *last_sector)
{
    int32_t first_idx = find_sector_by_address(address);
    if (first_idx < 0) {
        dev_log("[FLASHBLOCK] ERROR: Start address 0x%08X not in any sector\n", address);
        return false;
    }
    
    uint32_t end_address = address + length - 1;
    int32_t last_idx = find_sector_by_address(end_address);
    if (last_idx < 0) {
        dev_log("[FLASHBLOCK] ERROR: End address 0x%08X not in any sector\n", end_address);
        return false;
    }
    
    *first_sector = (uint32_t)first_idx;
    *last_sector = (uint32_t)last_idx;
    
    dev_log("[FLASHBLOCK] INFO: Erase range: sectors %u to %u (total: %u sectors)\n",
                 *first_sector, *last_sector, (*last_sector - *first_sector + 1));
    
    return true;
}

/* ===== Public API Implementation ===== */

dev_flashblock_result_t dev_flashblock_init(const dev_flashblock_config_t *config)
{
    if (config != NULL) {
        memcpy(&g_flashblock_state.config, config, sizeof(dev_flashblock_config_t));
    } else {
        // Default configuration
        g_flashblock_state.config.write_alignment = 32;
        g_flashblock_state.config.erase_timeout_ms = 2000;
        g_flashblock_state.config.write_timeout_ms = 100;
        g_flashblock_state.config.auto_verify = false;
        g_flashblock_state.config.progress_cb = NULL;
        g_flashblock_state.config.context = NULL;
    }
    
    g_flashblock_state.erase_state = DEV_FLASHBLOCK_ERASE_IDLE;
    memset(&g_flashblock_state.erase_ctx, 0, sizeof(erase_context_t));
    g_flashblock_state.initialized = true;
    
    dev_log("[FLASHBLOCK] INFO: Flash block module initialized\n");
    return DEV_FLASHBLOCK_OK;
}

dev_flashblock_result_t dev_flashblock_erase_start(uint32_t address, uint32_t length)
{
    // Check initialization
    if (!g_flashblock_state.initialized) {
        dev_log("[FLASHBLOCK] ERROR: Module not initialized\n");
        return DEV_FLASHBLOCK_ERROR_NOT_INIT;
    }
    
    // Check state - must be IDLE
    if (g_flashblock_state.erase_state != DEV_FLASHBLOCK_ERASE_IDLE) {
        dev_log("[FLASHBLOCK] ERROR: Erase already in progress (state: %d)\n", g_flashblock_state.erase_state);
        return DEV_FLASHBLOCK_ERROR_INVALID_STATE;
    }
    
    // Validate parameters
    if (length == 0) {
        dev_log("[FLASHBLOCK] ERROR: Invalid length: 0\n");
        return DEV_FLASHBLOCK_ERROR_INVALID_LEN;
    }
    
    if (!is_valid_flash_address(address, length)) {
        dev_log("[FLASHBLOCK] ERROR: Invalid flash range: 0x%08X - 0x%08X\n", address, address + length - 1);
        return DEV_FLASHBLOCK_ERROR_INVALID_ADDR;
    }
    
    // Determine which sectors to erase
    uint32_t first_sector, last_sector;
    if (!determine_erase_sectors(address, length, &first_sector, &last_sector)) {
        return DEV_FLASHBLOCK_ERROR_INVALID_ADDR;
    }
    
    // Setup erase context
    g_flashblock_state.erase_ctx.start_address = address;
    g_flashblock_state.erase_ctx.length = length;
    g_flashblock_state.erase_ctx.first_sector_idx = first_sector;
    g_flashblock_state.erase_ctx.last_sector_idx = last_sector;
    g_flashblock_state.erase_ctx.current_sector_idx = first_sector;
    g_flashblock_state.erase_ctx.total_sectors = last_sector - first_sector + 1;
    
    // Transition to PREPARED state
    g_flashblock_state.erase_state = DEV_FLASHBLOCK_ERASE_PREPARED;
    
    dev_log("[FLASHBLOCK] INFO: Erase prepared: addr=0x%08X, len=%u, sectors=[%u..%u]\n",
                 address, length, first_sector, last_sector);
    
    return DEV_FLASHBLOCK_OK;
}

dev_flashblock_result_t dev_flashblock_erase_do(void)
{
    // Check initialization
    if (!g_flashblock_state.initialized) {
        return DEV_FLASHBLOCK_ERROR_NOT_INIT;
    }
    
    // Check state - must be PREPARED or ERASING
    if (g_flashblock_state.erase_state != DEV_FLASHBLOCK_ERASE_PREPARED &&
        g_flashblock_state.erase_state != DEV_FLASHBLOCK_ERASE_ERASING) {
        dev_log("[FLASHBLOCK] ERROR: Invalid state for erase_do: %d\n", g_flashblock_state.erase_state);
        return DEV_FLASHBLOCK_ERROR_INVALID_STATE;
    }
    
    // Transition to ERASING state
    g_flashblock_state.erase_state = DEV_FLASHBLOCK_ERASE_ERASING;
    
    // Erase all sectors in the range
    for (uint32_t i = g_flashblock_state.erase_ctx.current_sector_idx;
         i <= g_flashblock_state.erase_ctx.last_sector_idx;
         i++)
    {
        uint32_t sector_addr = Fls_SectorTable[i].base_address;
        uint32_t sector_size = Fls_SectorTable[i].size;
        
        dev_log("[FLASHBLOCK] INFO: Erasing sector %u (addr=0x%08X, size=%u bytes)...\n",
                     i, sector_addr, sector_size);
        
        // Erase sector using dev_fls (pass sector index, not ID)
        dev_err_t fls_result = dev_fls_erase_sector((uint8_t)i);
        
        if (fls_result != DEV_OK) {
            dev_log("[FLASHBLOCK] ERROR: Failed to erase sector %u: error %d\n", i, fls_result);
            g_flashblock_state.erase_state = DEV_FLASHBLOCK_ERASE_IDLE;
            return DEV_FLASHBLOCK_ERROR_ERASE;
        }
        
        // Update current sector
        g_flashblock_state.erase_ctx.current_sector_idx = i + 1;
        
        // Report progress
        if (g_flashblock_state.config.progress_cb != NULL) {
            uint32_t sectors_done = i - g_flashblock_state.erase_ctx.first_sector_idx + 1;
            g_flashblock_state.config.progress_cb(
                sectors_done,
                g_flashblock_state.erase_ctx.total_sectors,
                g_flashblock_state.config.context
            );
        }
    }
    
    // All sectors erased successfully
    g_flashblock_state.erase_state = DEV_FLASHBLOCK_ERASE_COMPLETED;
    
    dev_log("[FLASHBLOCK] INFO: Erase completed successfully (%u sectors)\n",
                 g_flashblock_state.erase_ctx.total_sectors);
    
    return DEV_FLASHBLOCK_OK;
}

dev_flashblock_result_t dev_flashblock_erase_finish(void)
{
    // Check initialization
    if (!g_flashblock_state.initialized) {
        return DEV_FLASHBLOCK_ERROR_NOT_INIT;
    }
    
    // Check state - must be COMPLETED
    if (g_flashblock_state.erase_state != DEV_FLASHBLOCK_ERASE_COMPLETED) {
        dev_log("[FLASHBLOCK] ERROR: Invalid state for erase_finish: %d\n", g_flashblock_state.erase_state);
        return DEV_FLASHBLOCK_ERROR_INVALID_STATE;
    }
    
    // Reset context and transition to IDLE
    memset(&g_flashblock_state.erase_ctx, 0, sizeof(erase_context_t));
    g_flashblock_state.erase_state = DEV_FLASHBLOCK_ERASE_IDLE;
    
    dev_log("[FLASHBLOCK] INFO: Erase operation finalized, ready for next operation\n");
    
    return DEV_FLASHBLOCK_OK;
}

dev_flashblock_erase_state_t dev_flashblock_get_erase_state(void)
{
    return g_flashblock_state.erase_state;
}

dev_flashblock_result_t dev_flashblock_get_erase_progress(uint32_t *current_sector, uint32_t *total_sectors)
{
    if (!g_flashblock_state.initialized) {
        return DEV_FLASHBLOCK_ERROR_NOT_INIT;
    }
    
    if (current_sector != NULL) {
        if (g_flashblock_state.erase_state == DEV_FLASHBLOCK_ERASE_ERASING) {
            *current_sector = g_flashblock_state.erase_ctx.current_sector_idx - 
                             g_flashblock_state.erase_ctx.first_sector_idx;
        } else if (g_flashblock_state.erase_state == DEV_FLASHBLOCK_ERASE_COMPLETED) {
            *current_sector = g_flashblock_state.erase_ctx.total_sectors;
        } else {
            *current_sector = 0;
        }
    }
    
    if (total_sectors != NULL) {
        *total_sectors = g_flashblock_state.erase_ctx.total_sectors;
    }
    
    return DEV_FLASHBLOCK_OK;
}

const char* dev_flashblock_get_error_string(dev_flashblock_result_t result)
{
    switch (result) {
        case DEV_FLASHBLOCK_OK:
            return "Success";
        case DEV_FLASHBLOCK_ERROR_INVALID_ADDR:
            return "Invalid flash address";
        case DEV_FLASHBLOCK_ERROR_INVALID_LEN:
            return "Invalid length";
        case DEV_FLASHBLOCK_ERROR_ALIGNMENT:
            return "Alignment error";
        case DEV_FLASHBLOCK_ERROR_ERASE:
            return "Erase operation failed";
        case DEV_FLASHBLOCK_ERROR_WRITE:
            return "Write operation failed";
        case DEV_FLASHBLOCK_ERROR_VERIFY:
            return "Verification failed";
        case DEV_FLASHBLOCK_ERROR_BUSY:
            return "Flash controller busy";
        case DEV_FLASHBLOCK_ERROR_TIMEOUT:
            return "Operation timeout";
        case DEV_FLASHBLOCK_ERROR_NOT_INIT:
            return "Module not initialized";
        case DEV_FLASHBLOCK_ERROR_INVALID_STATE:
            return "Invalid state for operation";
        default:
            return "Unknown error";
    }
}
