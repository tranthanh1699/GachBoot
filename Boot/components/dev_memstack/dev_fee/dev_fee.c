#include "dev_fee.h"
#include "dev_fee_config.h"
#include "dev_fls.h"
#include <string.h>

CONFIG_LOG_TAG(DEV_FEE, true)

// Fee Runtime State
typedef struct {
    uint32_t active_sector;             // Current active sector base address
    uint32_t write_position;            // Current write position in active sector
    bool initialized;                   // Initialization flag
} dev_fee_state_t;

static dev_fee_state_t fee_state = {0};
static dev_fee_statistics_t fee_stats = {0};

// Forward declarations
static dev_err_t fee_scan_sectors_and_init(void);
static dev_err_t fee_switch_sector(void);

/**
 * @brief Initialize Fee module
 */
dev_err_t dev_fee_init(void)
{
    if (fee_state.initialized) {
        return DEV_OK;
    }
    
    DBG_OUT_I("Initializing Fee driver...");
    
    // Reset state
    memset(&fee_state, 0, sizeof(fee_state));
    memset(&fee_stats, 0, sizeof(fee_stats));
    
    // Initialize Fls first
    dev_err_t err = dev_fls_init();
    if (err != DEV_OK) {
        DBG_OUT_E("Fls init failed");
        return err;
    }
    
    // Scan sectors to determine active one and write position
    err = fee_scan_sectors_and_init();
    if (err != DEV_OK) {
        DBG_OUT_E("Fee sector scan failed");
        return err;
    }
    
    fee_state.initialized = true;
    fee_stats.active_sector_address = fee_state.active_sector;
    fee_stats.active_sector_usage = fee_state.write_position - fee_state.active_sector;
    fee_stats.write_position = fee_state.write_position;
    
    DBG_OUT_I("Fee initialized - Active sector: 0x%08X, Usage: %u bytes", 
              fee_state.active_sector, fee_stats.active_sector_usage);
    
    return DEV_OK;
}

/**
 * @brief Scan sectors to find active one and determine write position
 */
static dev_err_t fee_scan_sectors_and_init(void)
{
    uint32_t sector_a_addr = DEV_FEE_SECTOR_A_BASE_ADDRESS;
    uint32_t sector_b_addr = DEV_FEE_SECTOR_B_BASE_ADDRESS;
    
    // Check which sector has valid data (not all 0xFF)
    bool sector_a_has_data = !dev_fls_blank_check(sector_a_addr, DEV_FEE_WRITE_ALIGNMENT);
    bool sector_b_has_data = !dev_fls_blank_check(sector_b_addr, DEV_FEE_WRITE_ALIGNMENT);
    
    if (!sector_a_has_data && !sector_b_has_data) {
        // Both sectors empty - use sector A
        fee_state.active_sector = sector_a_addr;
        fee_state.write_position = sector_a_addr;
        DBG_OUT_I("Both sectors empty, using Sector A");
        return DEV_OK;
    }
    
    if (sector_a_has_data && !sector_b_has_data) {
        // Sector A has data, B is empty
        fee_state.active_sector = sector_a_addr;
    } else if (!sector_a_has_data && sector_b_has_data) {
        // Sector B has data, A is empty
        fee_state.active_sector = sector_b_addr;
    } else {
        // Both have data - use the one with most recent write (prefer A)
        fee_state.active_sector = sector_a_addr;
    }
    
    // Find write position by scanning for first 0xFFFFFFFF
    uint32_t scan_addr = fee_state.active_sector;
    uint32_t sector_end = fee_state.active_sector + DEV_FEE_SECTOR_SIZE;
    
    // Use write alignment for scan
    while (scan_addr < sector_end) {
        if (dev_fls_blank_check(scan_addr, DEV_FEE_WRITE_ALIGNMENT)) {
            // Found empty space
            fee_state.write_position = scan_addr;
            DBG_OUT_I("Active sector: 0x%08X, Write position: 0x%08X", 
                      fee_state.active_sector, fee_state.write_position);
            return DEV_OK;
        }
        scan_addr += DEV_FEE_WRITE_ALIGNMENT;
    }
    
    // Sector is full
    fee_state.write_position = sector_end;
    DBG_OUT_W("Active sector 0x%08X is full, will switch on next write", fee_state.active_sector);
    
    return DEV_OK;
}

/**
 * @brief Write data to Fee (dynamic addressing)
 */
dev_err_t dev_fee_write(const uint8_t *data, uint32_t length, uint32_t *out_address)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(out_address != NULL, DEV_ERR_INVALID_ARG, "Output address is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    DEV_RETURN_ON_FALSE(length <= DEV_FEE_SECTOR_SIZE, DEV_ERR_INVALID_ARG, "Length exceeds sector size");
    
    // Align length to write alignment
    uint32_t aligned_length = ((length + DEV_FEE_WRITE_ALIGNMENT - 1) / DEV_FEE_WRITE_ALIGNMENT) * DEV_FEE_WRITE_ALIGNMENT;
    
    // Check if current sector has enough space
    uint32_t sector_end = fee_state.active_sector + DEV_FEE_SECTOR_SIZE;
    uint32_t available = sector_end - fee_state.write_position;
    
    if (available < aligned_length || fee_state.write_position >= (fee_state.active_sector + DEV_FEE_SECTOR_FULL_THRESHOLD)) {
        // Sector full - switch to alternate
        DBG_OUT_W("Sector 0x%08X full (%u bytes used), switching...", 
                  fee_state.active_sector, fee_state.write_position - fee_state.active_sector);
        
        dev_err_t err = fee_switch_sector();
        if (err != DEV_OK) {
            DBG_OUT_E("Sector switch failed");
            return err;
        }
    }
    
    // Write data at current position via Fls (Fls handles alignment padding)
    uint32_t write_addr = fee_state.write_position;
    dev_err_t err = dev_fls_write(write_addr, data, length);
    
    if (err == DEV_OK) {
        *out_address = write_addr;
        fee_state.write_position += aligned_length;
        fee_stats.total_writes++;
        fee_stats.active_sector_usage = fee_state.write_position - fee_state.active_sector;
        fee_stats.write_position = fee_state.write_position;
        
        DBG_OUT_I("Fee write: 0x%08X (%u bytes, %u aligned)", write_addr, length, aligned_length);
    } else {
        DBG_OUT_E("Fee write failed at 0x%08X", write_addr);
    }
    
    return err;
}

/**
 * @brief Read data from Fee
 */
dev_err_t dev_fee_read(uint32_t address, uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    
    // Route to Fls
    dev_err_t err = dev_fls_read(address, data, length);
    
    if (err == DEV_OK) {
        fee_stats.total_reads++;
    }
    
    return err;
}

/**
 * @brief Switch to alternate sector
 */
static dev_err_t fee_switch_sector(void)
{
    uint32_t old_sector = fee_state.active_sector;
    uint32_t new_sector = dev_fee_get_alternate_sector(old_sector);
    
    DBG_OUT_I("Switching from 0x%08X to 0x%08X", old_sector, new_sector);
    
    // Erase new sector via Fls
    dev_err_t err = dev_fls_erase_sector(new_sector);
    if (err != DEV_OK) {
        DBG_OUT_E("Failed to erase new sector 0x%08X", new_sector);
        return err;
    }
    
    // Switch to new sector
    fee_state.active_sector = new_sector;
    fee_state.write_position = new_sector;
    
    // Update statistics
    fee_stats.sector_switches++;
    fee_stats.active_sector_address = new_sector;
    fee_stats.active_sector_usage = 0;
    fee_stats.write_position = new_sector;
    
    DBG_OUT_I("Sector switch complete - New sector: 0x%08X", new_sector);
    
    return DEV_OK;
}

/**
 * @brief Erase all Fee-managed sectors
 */
dev_err_t dev_fee_erase_all(void)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    
    DBG_OUT_I("Erasing all Fee sectors...");
    
    // Erase both sectors via Fls
    dev_err_t err = dev_fls_erase_all();
    if (err != DEV_OK) {
        DBG_OUT_E("Erase all failed");
        return err;
    }
    
    // Reset to sector A
    fee_state.active_sector = DEV_FEE_SECTOR_A_BASE_ADDRESS;
    fee_state.write_position = DEV_FEE_SECTOR_A_BASE_ADDRESS;
    fee_stats.active_sector_address = DEV_FEE_SECTOR_A_BASE_ADDRESS;
    fee_stats.active_sector_usage = 0;
    fee_stats.write_position = DEV_FEE_SECTOR_A_BASE_ADDRESS;
    
    DBG_OUT_I("All sectors erased");
    return DEV_OK;
}

/**
 * @brief Force sector switch
 */
dev_err_t dev_fee_force_sector_switch(void)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    
    DBG_OUT_W("Forcing sector switch...");
    return fee_switch_sector();
}

/**
 * @brief Get active sector information
 */
dev_err_t dev_fee_get_active_sector(uint32_t *out_sector, uint32_t *out_usage)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    DEV_RETURN_ON_FALSE(out_sector != NULL, DEV_ERR_INVALID_ARG, "Output sector is NULL");
    DEV_RETURN_ON_FALSE(out_usage != NULL, DEV_ERR_INVALID_ARG, "Output usage is NULL");
    
    *out_sector = fee_state.active_sector;
    *out_usage = fee_state.write_position - fee_state.active_sector;
    
    return DEV_OK;
}

/**
 * @brief Get Fee statistics
 */
dev_err_t dev_fee_get_statistics(dev_fee_statistics_t *stats)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    DEV_RETURN_ON_FALSE(stats != NULL, DEV_ERR_INVALID_ARG, "Stats is NULL");
    
    fee_stats.active_sector_usage = fee_state.write_position - fee_state.active_sector;
    fee_stats.write_position = fee_state.write_position;
    memcpy(stats, &fee_stats, sizeof(dev_fee_statistics_t));
    
    return DEV_OK;
}

/**
 * @brief Check if address is managed by Fee
 */
bool dev_fee_is_managed_address(uint32_t address)
{
    return dev_fls_is_managed_address(address);
}
