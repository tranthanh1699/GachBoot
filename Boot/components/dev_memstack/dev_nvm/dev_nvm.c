#include "dev_nvm.h"
#include "dev_crc.h"
#include "dev_memif.h"
#include <string.h>

CONFIG_LOG_TAG(DEV_NVM, true)

// NVM Runtime State
typedef struct {
    dev_nvm_block_state_t state;
    bool ram_changed;
    uint32_t nv_address;                // Physical flash address (from FLS)
} dev_nvm_block_runtime_t;

static dev_nvm_block_runtime_t block_runtime[DEV_NVM_MAX_BLOCKS];
static dev_nvm_statistics_t nvm_stats = {0};
static bool nvm_initialized = false;

/**
 * @brief Find block configuration by ID
 */
static const dev_nvm_block_config_t* find_block_config(uint16_t block_id)
{
    for (uint16_t i = 0; i < dev_nvm_block_config_count; i++) {
        if (dev_nvm_block_config_table[i].block_id == block_id) {
            return &dev_nvm_block_config_table[i];
        }
    }
    return NULL;
}

/**
 * @brief Find block runtime index
 */
static int16_t find_block_runtime_index(uint16_t block_id)
{
    for (uint16_t i = 0; i < dev_nvm_block_config_count; i++) {
        if (dev_nvm_block_config_table[i].block_id == block_id) {
            return i;
        }
    }
    return -1;
}

/**
 * @brief Validate block data with CRC (CRC stored after data)
 */
static bool validate_block_crc(uint32_t nv_address, const uint8_t *data, uint16_t data_len)
{
    // Read stored CRC from flash (after data)
    uint32_t stored_crc;
    dev_err_t err = dev_memif_read(nv_address + data_len, (uint8_t*)&stored_crc, sizeof(uint32_t));
    
    if (err != DEV_OK) {
        return false;
    }
    
    // Calculate CRC of data
    uint32_t calc_crc = dev_crc32_calculate(data, data_len);
    
    if (calc_crc != stored_crc) {
        DBG_OUT_W("CRC mismatch at 0x%08X: calc=0x%08X stored=0x%08X", 
                  nv_address, calc_crc, stored_crc);
        return false;
    }
    
    return true;
}

/**
 * @brief Read block from NV (uses FLS, runtime address tracking)
 */
static dev_err_t read_block_from_nv(const dev_nvm_block_config_t *config, 
                                     uint8_t *data, uint16_t length,
                                     uint32_t nv_address)
{
    dev_err_t err;
    
    if (nv_address == 0) {
        // Block never written
        return DEV_ERR_NOT_FOUND;
    }
    
    if (config->block_type == DEV_NVM_BLOCK_NATIVE) {
        // NATIVE: [Data][CRC32]
        err = dev_memif_read(nv_address, data, length);
        if (err != DEV_OK) {
            return err;
        }
        
        // Validate CRC
        if (config->use_crc && !validate_block_crc(nv_address, data, length)) {
            nvm_stats.crc_errors++;
            return DEV_ERR_CRC;
        }
        
        return DEV_OK;
    }
    else { // DEV_NVM_BLOCK_REDUNDANT
        // REDUNDANT: [Primary Data][Primary CRC32][Secondary Data][Secondary CRC32]
        uint32_t primary_addr = nv_address;
        uint32_t secondary_addr = nv_address + length + sizeof(uint32_t);
        
        uint8_t data_primary[length];
        uint8_t data_secondary[length];
        
        // Read primary
        err = dev_memif_read(primary_addr, data_primary, length);
        bool primary_valid = (err == DEV_OK);
        
        if (primary_valid && config->use_crc) {
            primary_valid = validate_block_crc(primary_addr, data_primary, length);
        }
        
        // Read secondary
        err = dev_memif_read(secondary_addr, data_secondary, length);
        bool secondary_valid = (err == DEV_OK);
        
        if (secondary_valid && config->use_crc) {
            secondary_valid = validate_block_crc(secondary_addr, data_secondary, length);
        }
        
        // Decision logic
        if (primary_valid && secondary_valid) {
            // Both valid - compare data
            if (memcmp(data_primary, data_secondary, length) == 0) {
                memcpy(data, data_primary, length);
                return DEV_OK;
            } else {
                // Data mismatch - use primary
                memcpy(data, data_primary, length);
                DBG_OUT_W("Block 0x%04X redundant copies differ, using primary", config->block_id);
                return DEV_OK;
            }
        }
        else if (primary_valid) {
            memcpy(data, data_primary, length);
            DBG_OUT_W("Block 0x%04X secondary invalid, using primary", config->block_id);
            return DEV_OK;
        }
        else if (secondary_valid) {
            memcpy(data, data_secondary, length);
            DBG_OUT_W("Block 0x%04X primary invalid, using secondary", config->block_id);
            return DEV_OK;
        }
        else {
            DBG_OUT_E("Block 0x%04X both copies invalid", config->block_id);
            nvm_stats.crc_errors++;
            return DEV_ERR_CRC;
        }
    }
}

/**
 * @brief Write block to NV (uses FLS for dynamic addressing)
 */
static dev_err_t write_block_to_nv(const dev_nvm_block_config_t *config,
                                    const uint8_t *data, uint16_t length,
                                    uint32_t *out_nv_address)
{
    dev_err_t err;
    uint32_t crc = 0;
    
    if (config->use_crc) {
        crc = dev_crc32_calculate(data, length);
    }
    
    if (config->block_type == DEV_NVM_BLOCK_NATIVE) {
        // NATIVE: Write [Data][CRC32]
        uint32_t write_addr;
        
        // Write data via MemIf (Fee manages addressing)
        err = dev_memif_write(0, data, length, &write_addr);
        if (err != DEV_OK) {
            return err;
        }
        
        // Write CRC after data
        if (config->use_crc) {
            uint32_t crc_addr;
            err = dev_memif_write(0, (uint8_t*)&crc, sizeof(uint32_t), &crc_addr);
            if (err != DEV_OK) {
                return err;
            }
        }
        
        *out_nv_address = write_addr;
        return DEV_OK;
    }
    else { // DEV_NVM_BLOCK_REDUNDANT
        // REDUNDANT: Write both copies [Primary Data+CRC][Secondary Data+CRC]
        uint32_t primary_addr, secondary_addr;
        
        // Write primary copy
        err = dev_memif_write(0, data, length, &primary_addr);
        if (err != DEV_OK) {
            return err;
        }
        
        if (config->use_crc) {
            uint32_t crc_addr;
            err = dev_memif_write(0, (uint8_t*)&crc, sizeof(uint32_t), &crc_addr);
            if (err != DEV_OK) {
                return err;
            }
        }
        
        // Write secondary copy
        err = dev_memif_write(0, data, length, &secondary_addr);
        if (err != DEV_OK) {
            return err;
        }
        
        if (config->use_crc) {
            uint32_t crc_addr;
            err = dev_memif_write(0, (uint8_t*)&crc, sizeof(uint32_t), &crc_addr);
            if (err != DEV_OK) {
                return err;
            }
        }
        
        *out_nv_address = primary_addr;
        return DEV_OK;
    }
}

/**
 * @brief Initialize NVM module (AUTOSAR style)
 */
dev_err_t dev_nvm_init(void)
{
    if (nvm_initialized) {
        return DEV_OK;
    }
    
    DBG_OUT_I("Initializing NVM module...");
    
    // Initialize runtime state
    memset(block_runtime, 0, sizeof(block_runtime));
    memset(&nvm_stats, 0, sizeof(nvm_stats));
    
    // Initialize MemIf (which initializes Fee and Fls chain)
    dev_err_t err = dev_memif_init();
    if (err != DEV_OK) {
        DBG_OUT_E("MemIf init failed");
        return err;
    }
    
    // Restore all blocks from NV to RAM
    for (uint16_t i = 0; i < dev_nvm_block_config_count; i++) {
        const dev_nvm_block_config_t *config = &dev_nvm_block_config_table[i];
        
        // Try to read from last known address (0 if never written)
        err = read_block_from_nv(config, config->ram_address, config->block_size,
                                  block_runtime[i].nv_address);
        
        if (err == DEV_OK) {
            // Block found in NV - loaded to RAM
            block_runtime[i].state = DEV_NVM_BLOCK_VALID;
            DBG_OUT_I("Block 0x%04X restored from 0x%08X", config->block_id, block_runtime[i].nv_address);
        } else {
            // Block not found or invalid - use ROM defaults
            block_runtime[i].state = DEV_NVM_BLOCK_INVALID;
            block_runtime[i].nv_address = 0;  // Mark as never written
            
            // Load default data to RAM
            if (config->rom_address != NULL) {
                memcpy(config->ram_address, config->rom_address, config->block_size);
                DBG_OUT_W("Block 0x%04X not found, loaded ROM defaults", config->block_id);
            } else {
                // No default data - use all zeros
                memset(config->ram_address, 0, config->block_size);
                DBG_OUT_W("Block 0x%04X not found, cleared to zeros", config->block_id);
            }
        }
        
        block_runtime[i].ram_changed = false;
    }
    
    nvm_initialized = true;
    DBG_OUT_I("NVM initialization complete");
    return DEV_OK;
}

/**
 * @brief Read NVM block
 */
dev_err_t dev_nvm_read_block(uint16_t block_id, uint8_t *data, uint16_t length)
{
    DEV_RETURN_ON_FALSE(nvm_initialized, DEV_ERR_MODULE_NOT_INIT, "NVM not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data pointer is NULL");
    
    const dev_nvm_block_config_t *config = find_block_config(block_id);
    DEV_RETURN_ON_FALSE(config != NULL, DEV_ERR_NOT_FOUND, "Block not found");
    DEV_RETURN_ON_FALSE(length == config->block_size, DEV_ERR_INVALID_ARG, "Invalid length");
    
    // Copy from RAM mirror
    memcpy(data, config->ram_address, length);
    nvm_stats.total_reads++;
    
    return DEV_OK;
}

/**
 * @brief Write NVM block
 */
dev_err_t dev_nvm_write_block(uint16_t block_id, const uint8_t *data, uint16_t length)
{
    DEV_RETURN_ON_FALSE(nvm_initialized, DEV_ERR_MODULE_NOT_INIT, "NVM not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data pointer is NULL");
    
    const dev_nvm_block_config_t *config = find_block_config(block_id);
    DEV_RETURN_ON_FALSE(config != NULL, DEV_ERR_NOT_FOUND, "Block not found");
    DEV_RETURN_ON_FALSE(length == config->block_size, DEV_ERR_INVALID_ARG, "Invalid length");
    DEV_RETURN_ON_FALSE(!config->write_protection, DEV_ERR_PERMISSION_DENIED, "Block is write-protected");
    
    int16_t idx = find_block_runtime_index(block_id);
    DEV_RETURN_ON_FALSE(idx >= 0, DEV_ERR_NOT_FOUND, "Block runtime not found");
    
    // Update RAM mirror
    memcpy(config->ram_address, data, length);
    
    // Write to NV via FLS (FLS returns physical address)
    uint32_t nv_address;
    dev_err_t err = write_block_to_nv(config, data, length, &nv_address);
    
    if (err == DEV_OK) {
        block_runtime[idx].state = DEV_NVM_BLOCK_VALID;
        block_runtime[idx].ram_changed = false;
        block_runtime[idx].nv_address = nv_address;  // Store FLS address
        nvm_stats.total_writes++;
        DBG_OUT_I("Block 0x%04X written to 0x%08X", block_id, nv_address);
    } else {
        nvm_stats.write_errors++;
        DBG_OUT_E("Block 0x%04X write failed", block_id);
    }
    
    return err;
}

/**
 * @brief Restore NVM block from NV to RAM (or ROM defaults if NV invalid)
 */
dev_err_t dev_nvm_restore_block(uint16_t block_id)
{
    DEV_RETURN_ON_FALSE(nvm_initialized, DEV_ERR_MODULE_NOT_INIT, "NVM not initialized");
    
    const dev_nvm_block_config_t *config = find_block_config(block_id);
    DEV_RETURN_ON_FALSE(config != NULL, DEV_ERR_NOT_FOUND, "Block not found");
    
    int16_t idx = find_block_runtime_index(block_id);
    DEV_RETURN_ON_FALSE(idx >= 0, DEV_ERR_NOT_FOUND, "Block runtime not found");
    
    dev_err_t err = read_block_from_nv(config, config->ram_address, config->block_size,
                                        block_runtime[idx].nv_address);
    
    if (err == DEV_OK) {
        block_runtime[idx].state = DEV_NVM_BLOCK_VALID;
        block_runtime[idx].ram_changed = false;
        DBG_OUT_I("Block 0x%04X restored from 0x%08X", block_id, block_runtime[idx].nv_address);
    } else {
        // NV read failed - restore from ROM defaults
        if (config->rom_address != NULL) {
            memcpy(config->ram_address, config->rom_address, config->block_size);
            DBG_OUT_W("Block 0x%04X NV invalid, restored from ROM", block_id);
        } else {
            memset(config->ram_address, 0, config->block_size);
            DBG_OUT_W("Block 0x%04X NV invalid, cleared to zeros", block_id);
        }
        block_runtime[idx].state = DEV_NVM_BLOCK_INVALID;
        nvm_stats.read_errors++;
    }
    
    return err;
}

/**
 * @brief Invalidate NVM block
 */
dev_err_t dev_nvm_invalidate_block(uint16_t block_id)
{
    DEV_RETURN_ON_FALSE(nvm_initialized, DEV_ERR_MODULE_NOT_INIT, "NVM not initialized");
    
    int16_t idx = find_block_runtime_index(block_id);
    DEV_RETURN_ON_FALSE(idx >= 0, DEV_ERR_NOT_FOUND, "Block runtime not found");
    
    block_runtime[idx].state = DEV_NVM_BLOCK_INVALID;
    DBG_OUT_I("Block 0x%04X invalidated", block_id);
    
    return DEV_OK;
}

/**
 * @brief Erase NVM block (erase at fixed NV address)
 */
dev_err_t dev_nvm_erase_block(uint16_t block_id)
{
    DEV_RETURN_ON_FALSE(nvm_initialized, DEV_ERR_MODULE_NOT_INIT, "NVM not initialized");
    
    const dev_nvm_block_config_t *config = find_block_config(block_id);
    DEV_RETURN_ON_FALSE(config != NULL, DEV_ERR_NOT_FOUND, "Block not found");
    DEV_RETURN_ON_FALSE(!config->write_protection, DEV_ERR_PERMISSION_DENIED, "Block is write-protected");
    
    int16_t idx = find_block_runtime_index(block_id);
    DEV_RETURN_ON_FALSE(idx >= 0, DEV_ERR_NOT_FOUND, "Block runtime not found");
    
    // Note: Erase via FLS - write zeros to invalidate block
    uint32_t block_total_size = config->block_size + sizeof(uint32_t);  // Data + CRC
    if (config->block_type == DEV_NVM_BLOCK_REDUNDANT) {
        block_total_size *= 2;  // Both copies
    }
    
    uint8_t zero_buffer[block_total_size];
    memset(zero_buffer, 0, block_total_size);
    
    uint32_t erase_addr;
    dev_err_t err = dev_memif_write(0, zero_buffer, block_total_size, &erase_addr);
    
    if (err == DEV_OK) {
        block_runtime[idx].state = DEV_NVM_BLOCK_INVALID;
        block_runtime[idx].nv_address = 0;  // Mark as erased
        DBG_OUT_I("Block 0x%04X erased", block_id);
    } else {
        DBG_OUT_E("Block 0x%04X erase failed", block_id);
    }
    
    return err;
}

/**
 * @brief Get block state
 */
dev_err_t dev_nvm_get_block_state(uint16_t block_id, dev_nvm_block_state_t *state)
{
    DEV_RETURN_ON_FALSE(nvm_initialized, DEV_ERR_MODULE_NOT_INIT, "NVM not initialized");
    DEV_RETURN_ON_FALSE(state != NULL, DEV_ERR_INVALID_ARG, "State pointer is NULL");
    
    int16_t idx = find_block_runtime_index(block_id);
    DEV_RETURN_ON_FALSE(idx >= 0, DEV_ERR_NOT_FOUND, "Block runtime not found");
    
    *state = block_runtime[idx].state;
    return DEV_OK;
}

/**
 * @brief Set RAM block changed flag
 */
dev_err_t dev_nvm_set_ram_block_changed(uint16_t block_id)
{
    DEV_RETURN_ON_FALSE(nvm_initialized, DEV_ERR_MODULE_NOT_INIT, "NVM not initialized");
    
    int16_t idx = find_block_runtime_index(block_id);
    DEV_RETURN_ON_FALSE(idx >= 0, DEV_ERR_NOT_FOUND, "Block runtime not found");
    
    block_runtime[idx].ram_changed = true;
    return DEV_OK;
}

/**
 * @brief Get NVM statistics
 */
dev_err_t dev_nvm_get_statistics(dev_nvm_statistics_t *stats)
{
    DEV_RETURN_ON_FALSE(nvm_initialized, DEV_ERR_MODULE_NOT_INIT, "NVM not initialized");
    DEV_RETURN_ON_FALSE(stats != NULL, DEV_ERR_INVALID_ARG, "Stats pointer is NULL");
    
    memcpy(stats, &nvm_stats, sizeof(dev_nvm_statistics_t));
    return DEV_OK;
}

/**
 * @brief Main function for background processing
 */
void dev_nvm_main_function(void)
{
    // Background task: Write pending blocks
    // Can be extended for automatic periodic writes
}
