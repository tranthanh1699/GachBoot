#include "dev_fee.h"
#include "dev_fls.h"
#include <string.h>

CONFIG_LOG_TAG(DEV_FEE, true)

/**
 * @brief Fee runtime state
 * 
 * Manages virtual address space and sector lifecycle.
 * Fee alternates between sectors for wear leveling.
 */
typedef struct {
    Fee_ConfigType config;              /**< Copy of injected configuration */
    uint8_t active_fee_sector_index;    /**< Index in config.sector_table[] */
    uint32_t physical_write_position;   /**< Current physical write address */
    uint32_t next_virtual_address;      /**< Next virtual address to allocate */
    uint32_t sector_usage;              /**< Bytes used in active sector */
    bool initialized;                   /**< Initialization flag */
} dev_fee_state_t;

static dev_fee_state_t fee_state = {0};
static dev_fee_statistics_t fee_stats = {0};

// Forward declarations
static dev_err_t fee_scan_and_init_sectors(void);
static dev_err_t fee_find_active_sector(uint8_t *out_fee_sector_index);
static dev_err_t fee_find_write_position(uint8_t fee_sector_index);
static const Fls_SectorDescriptor_t* fee_get_fls_sector(uint8_t fee_sector_index);

/**
 * @brief Initialize Fee module with configuration
 */
dev_err_t dev_fee_init(const Fee_ConfigType *config)
{
    if (fee_state.initialized) {
        return DEV_OK;
    }
    
    // Use default config if NULL passed
    const Fee_ConfigType *active_config = (config != NULL) ? config : &Fee_Config;
    
    // Validate configuration
    DEV_RETURN_ON_FALSE(active_config->sector_table != NULL, DEV_ERR_INVALID_ARG, "Fee sector table is NULL");
    DEV_RETURN_ON_FALSE(active_config->sector_count > 0, DEV_ERR_INVALID_ARG, "Fee sector count is zero");
    DEV_RETURN_ON_FALSE(active_config->fls_config != NULL, DEV_ERR_INVALID_ARG, "Fls config reference is NULL");
    
    DBG_OUT_I("Initializing Fee driver (AUTOSAR compliant)");
    
    // Copy configuration into internal state
    memcpy(&fee_state.config, active_config, sizeof(Fee_ConfigType));
    memset(&fee_stats, 0, sizeof(fee_stats));
    
    // Initialize Fls with its config
    dev_err_t err = dev_fls_init(fee_state.config.fls_config);
    if (err != DEV_OK) {
        DBG_OUT_E("Fls init failed");
        return err;
    }
    
    // Scan sectors to determine active one and write position
    err = fee_scan_and_init_sectors();
    if (err != DEV_OK) {
        DBG_OUT_E("Fee sector scan failed");
        return err;
    }
    
    fee_state.initialized = true;
    
    // Update statistics
    fee_stats.active_sector_index = fee_state.active_fee_sector_index;
    fee_stats.active_sector_usage = fee_state.sector_usage;
    fee_stats.next_virtual_address = fee_state.next_virtual_address;
    
    const Fls_SectorDescriptor_t *fls_sector = fee_get_fls_sector(fee_state.active_fee_sector_index);
    DBG_OUT_I("Fee initialized - Active: %s (0x%08X), Usage: %u bytes, Next virt: 0x%08X",
              fee_state.config.sector_table[fee_state.active_fee_sector_index].name,
              fls_sector->base_address,
              fee_state.sector_usage,
              fee_state.next_virtual_address);
    
    return DEV_OK;
}

/**
 * @brief Scan sectors and initialize state
 */
static dev_err_t fee_scan_and_init_sectors(void)
{
    // Find which Fee sector is active (has data)
    uint8_t active_index = 0;
    dev_err_t err = fee_find_active_sector(&active_index);
    if (err != DEV_OK) {
        return err;
    }
    
    fee_state.active_fee_sector_index = active_index;
    
    // Find write position in active sector
    err = fee_find_write_position(active_index);
    if (err != DEV_OK) {
        return err;
    }
    
    return DEV_OK;
}

/**
 * @brief Find which Fee sector is active
 */
static dev_err_t fee_find_active_sector(uint8_t *out_fee_sector_index)
{
    // Check each Fee sector for data
    bool sector_has_data[2];  /* Max 2 sectors for wear leveling */
    
    for (uint8_t i = 0; i < fee_state.config.sector_count; i++) {
        const Fls_SectorDescriptor_t *fls_sector = fee_get_fls_sector(i);
        if (fls_sector == NULL) {
            DBG_OUT_E("Fee sector [%u] maps to invalid Fls sector", i);
            return DEV_ERR_INVALID_ARG;
        }
        
        // Check if sector has data (not all 0xFF)
        sector_has_data[i] = !dev_fls_blank_check(fls_sector->base_address, fee_state.config.write_alignment);
        
        DBG_OUT_I("Fee sector [%u] %s: %s",
                  i, fee_state.config.sector_table[i].name,
                  sector_has_data[i] ? "HAS DATA" : "EMPTY");
    }
    
    // Determine active sector
    if (!sector_has_data[0] && !sector_has_data[1]) {
        // Both empty - use primary
        *out_fee_sector_index = 0;
        DBG_OUT_I("Both sectors empty, using primary");
        return DEV_OK;
    }
    
    if (sector_has_data[0] && !sector_has_data[1]) {
        *out_fee_sector_index = 0;
        DBG_OUT_I("Using Fee sector 0 (has data)");
        return DEV_OK;
    }
    
    if (!sector_has_data[0] && sector_has_data[1]) {
        *out_fee_sector_index = 1;
        DBG_OUT_I("Using Fee sector 1 (has data)");
        return DEV_OK;
    }
    
    // Both have data - use primary (sector 0)
    *out_fee_sector_index = 0;
    DBG_OUT_W("Both sectors have data, using primary (sector 0)");
    return DEV_OK;
}

/**
 * @brief Find write position in active sector
 */
static dev_err_t fee_find_write_position(uint8_t fee_sector_index)
{
    const Fls_SectorDescriptor_t *fls_sector = fee_get_fls_sector(fee_sector_index);
    if (fls_sector == NULL) {
        return DEV_ERR_INVALID_ARG;
    }
    
    // Scan sector to find first blank (0xFF) position
    uint32_t scan_addr = fls_sector->base_address;
    uint32_t sector_end = fls_sector->base_address + fls_sector->size;
    
    while (scan_addr < sector_end) {
        if (dev_fls_blank_check(scan_addr, fee_state.config.write_alignment)) {
            // Found empty space - this is write position
            fee_state.physical_write_position = scan_addr;
            fee_state.sector_usage = scan_addr - fls_sector->base_address;
            fee_state.next_virtual_address = fee_state.sector_usage;  // Virtual = offset in sector
            
            DBG_OUT_I("Write position found at 0x%08X (offset %u)", scan_addr, fee_state.sector_usage);
            return DEV_OK;
        }
        scan_addr += fee_state.config.write_alignment;
    }
    
    // Sector is full
    fee_state.physical_write_position = sector_end;
    fee_state.sector_usage = fls_sector->size;
    fee_state.next_virtual_address = fls_sector->size;
    
    DBG_OUT_W("Sector is FULL, will switch on next write");
    return DEV_OK;
}

/**
 * @brief Write data (allocates from virtual space)
 */
dev_err_t dev_fee_write(uint32_t virtual_address, const uint8_t *data, 
                        uint32_t length, uint32_t *out_physical_address)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(out_physical_address != NULL, DEV_ERR_INVALID_ARG, "Output address is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    
    // Note: virtual_address parameter ignored - we use append mode (auto-increment)
    (void)virtual_address;  // Unused in current implementation
    
    // Calculate aligned length
    uint32_t write_align = fee_state.config.write_alignment;
    uint32_t aligned_length = ((length + write_align - 1) / write_align) * write_align;
    
    // Check if sector switch needed
    const Fls_SectorDescriptor_t *fls_sector = fee_get_fls_sector(fee_state.active_fee_sector_index);
    uint32_t available = (fls_sector->base_address + fls_sector->size) - fee_state.physical_write_position;
    
    if (available < aligned_length || fee_state.sector_usage >= fee_state.config.sector_full_threshold) {
        DBG_OUT_W("Sector full (usage=%u), switching...", fee_state.sector_usage);
        
        dev_err_t err = dev_fee_switch_sector();
        if (err != DEV_OK) {
            DBG_OUT_E("Sector switch failed");
            fee_stats.write_errors++;
            return err;
        }
        
        // Re-get Fls sector after switch
        fls_sector = fee_get_fls_sector(fee_state.active_fee_sector_index);
    }
    
    // Write to physical address via Fls
    uint32_t write_addr = fee_state.physical_write_position;
    dev_err_t err = dev_fls_write(write_addr, data, length);
    
    if (err != DEV_OK) {
        DBG_OUT_E("Fls write failed at 0x%08X", write_addr);
        fee_stats.write_errors++;
        return err;
    }
    
    // Return physical address to caller (for reading)
    *out_physical_address = write_addr;
    
    // Update state
    fee_state.physical_write_position += aligned_length;
    fee_state.sector_usage += aligned_length;
    fee_state.next_virtual_address += aligned_length;
    
    // Update statistics
    fee_stats.total_writes++;
    fee_stats.active_sector_usage = fee_state.sector_usage;
    fee_stats.next_virtual_address = fee_state.next_virtual_address;
    
    return DEV_OK;
}

/**
 * @brief Read data from physical address
 */
dev_err_t dev_fee_read(uint32_t physical_address, uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    
    // Direct read via Fls (no translation needed - physical address is stable)
    dev_err_t err = dev_fls_read(physical_address, data, length);
    
    if (err == DEV_OK) {
        fee_stats.total_reads++;
    }
    
    return err;
}

/**
 * @brief Get active sector info
 */
dev_err_t dev_fee_get_active_sector(uint32_t *sector_address, uint32_t *sector_usage)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    DEV_RETURN_ON_FALSE(sector_address != NULL, DEV_ERR_INVALID_ARG, "Sector address is NULL");
    DEV_RETURN_ON_FALSE(sector_usage != NULL, DEV_ERR_INVALID_ARG, "Sector usage is NULL");
    
    const Fls_SectorDescriptor_t *fls_sector = fee_get_fls_sector(fee_state.active_fee_sector_index);
    if (fls_sector == NULL) {
        return DEV_ERR_INVALID_ARG;
    }
    
    *sector_address = fls_sector->base_address;
    *sector_usage = fee_state.sector_usage;
    
    return DEV_OK;
}

/**
 * @brief Switch to alternate sector
 */
dev_err_t dev_fee_switch_sector(void)
{
    DEV_RETURN_ON_FALSE(fee_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fee not initialized");
    
    // Determine alternate Fee sector
    uint8_t new_fee_sector_index = (fee_state.active_fee_sector_index == 0) ? 1 : 0;
    
    const Fls_SectorDescriptor_t *new_fls_sector = fee_get_fls_sector(new_fee_sector_index);
    if (new_fls_sector == NULL) {
        DBG_OUT_E("Invalid alternate Fee sector");
        return DEV_ERR_INVALID_ARG;
    }
    
    DBG_OUT_I("Switching from %s to %s...",
              fee_state.config.sector_table[fee_state.active_fee_sector_index].name,
              fee_state.config.sector_table[new_fee_sector_index].name);
    
    // Erase new sector
    dev_err_t err = dev_fls_erase_sector(fee_state.config.sector_table[new_fee_sector_index].fls_sector_index);
    if (err != DEV_OK) {
        DBG_OUT_E("Failed to erase alternate sector");
        return err;
    }
    
    // Switch to new sector
    fee_state.active_fee_sector_index = new_fee_sector_index;
    fee_state.physical_write_position = new_fls_sector->base_address;
    fee_state.sector_usage = 0;
    fee_state.next_virtual_address = 0;
    
    // Update statistics
    fee_stats.sector_switches++;
    fee_stats.active_sector_index = fee_state.active_fee_sector_index;
    fee_stats.active_sector_usage = 0;
    fee_stats.next_virtual_address = 0;
    
    DBG_OUT_I("Sector switch complete - now using %s at 0x%08X",
              fee_state.config.sector_table[new_fee_sector_index].name,
              new_fls_sector->base_address);
    
    return DEV_OK;
}

/**
 * @brief Check if sector is full
 */
bool dev_fee_is_sector_full(void)
{
    if (!fee_state.initialized) {
        return false;
    }
    
    return (fee_state.sector_usage >= fee_state.config.sector_full_threshold);
}

/**
 * @brief Get statistics
 */
dev_err_t dev_fee_get_statistics(dev_fee_statistics_t *stats)
{
    DEV_RETURN_ON_FALSE(stats != NULL, DEV_ERR_INVALID_ARG, "Stats pointer is NULL");
    memcpy(stats, &fee_stats, sizeof(dev_fee_statistics_t));
    return DEV_OK;
}

/**
 * @brief Helper: Get Fls sector from Fee sector index
 */
static const Fls_SectorDescriptor_t* fee_get_fls_sector(uint8_t fee_sector_index)
{
    if (!fee_state.initialized || fee_sector_index >= fee_state.config.sector_count) {
        return NULL;
    }
    
    uint8_t fls_sector_index = fee_state.config.sector_table[fee_sector_index].fls_sector_index;
    return dev_fls_get_sector_by_index(fls_sector_index);
}

/**
 * @brief Get current configuration
 */
const Fee_ConfigType* dev_fee_get_config(void)
{
    if (!fee_state.initialized) {
        return NULL;
    }
    return &fee_state.config;
}
