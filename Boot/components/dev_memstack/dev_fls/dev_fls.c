#include "dev_fls.h"
#include "stm32h7xx_hal.h"
#include <string.h>

CONFIG_LOG_TAG(DEV_FLS, true)

/**
 * @brief Fls runtime state
 * 
 * Stores injected configuration and runtime statistics.
 * Configuration is copied at init time - no external dependencies.
 */
typedef struct {
    Fls_ConfigType config;              /**< Copy of injected configuration */
    bool initialized;                   /**< Initialization flag */
} dev_fls_state_t;

static dev_fls_state_t fls_state = {0};
static dev_fls_statistics_t fls_stats = {0};

// Forward declarations
static dev_err_t fls_hal_write_flash_word(uint32_t address, const uint8_t *data);
static dev_err_t fls_hal_erase_sector_by_hw_index(uint8_t bank, uint8_t sector);

// Public function forward declarations (defined later)
bool dev_fls_is_managed_address(uint32_t address);
const Fls_SectorDescriptor_t* dev_fls_get_sector_by_address(uint32_t address);

/**
 * @brief Initialize Fls module with configuration
 */
dev_err_t dev_fls_init(const Fls_ConfigType *config)
{
    if (fls_state.initialized) {
        return DEV_OK;
    }
    
    // Use default config if NULL passed
    const Fls_ConfigType *active_config = (config != NULL) ? config : &Fls_Config;
    
    // Validate configuration
    DEV_RETURN_ON_FALSE(active_config->sector_table != NULL, DEV_ERR_INVALID_ARG, "Sector table is NULL");
    DEV_RETURN_ON_FALSE(active_config->sector_count > 0, DEV_ERR_INVALID_ARG, "Sector count is zero");
    DEV_RETURN_ON_FALSE(active_config->write_alignment > 0, DEV_ERR_INVALID_ARG, "Invalid write alignment");
    
    DBG_OUT_I("Initializing Fls driver (AUTOSAR compliant)");
    
    // Copy configuration into internal state
    memcpy(&fls_state.config, active_config, sizeof(Fls_ConfigType));
    memset(&fls_stats, 0, sizeof(fls_stats));
    
    // Log managed sectors
    DBG_OUT_I("Fls manages %u sectors:", fls_state.config.sector_count);
    for (uint8_t i = 0; i < fls_state.config.sector_count; i++) {
        const Fls_SectorDescriptor_t *sector = &fls_state.config.sector_table[i];
        DBG_OUT_I("  [%u] %s: 0x%08X - 0x%08X (%u KB, Bank %u, Sector %u)",
                  i, sector->name, sector->base_address,
                  sector->base_address + sector->size - 1,
                  sector->size / 1024, sector->bank_index, sector->sector_index);
    }
    
    fls_state.initialized = true;
    return DEV_OK;
}

/**
 * @brief Read data from flash
 */
dev_err_t dev_fls_read(uint32_t address, uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(fls_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fls not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data buffer is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    DEV_RETURN_ON_FALSE(dev_fls_is_managed_address(address), DEV_ERR_INVALID_ARG, "Address 0x%08X not managed", address);
    
    // Direct memory-mapped read from flash
    memcpy(data, (const void*)address, length);
    fls_stats.total_reads++;
    
    return DEV_OK;
}

/**
 * @brief Write data to flash
 */
dev_err_t dev_fls_write(uint32_t address, const uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(fls_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fls not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    DEV_RETURN_ON_FALSE(dev_fls_is_managed_address(address), DEV_ERR_INVALID_ARG, "Address 0x%08X not managed", address);
    
    // Check write alignment
    uint32_t write_align = fls_state.config.write_alignment;
    if (address % write_align != 0) {
        DBG_OUT_E("Address 0x%08X not aligned to %u bytes", address, write_align);
        fls_stats.write_errors++;
        return DEV_ERR_INVALID_ARG;
    }
    
    // Get sector info to check boundaries
    const Fls_SectorDescriptor_t *sector = dev_fls_get_sector_by_address(address);
    if (sector == NULL) {
        DBG_OUT_E("Address 0x%08X does not belong to any managed sector", address);
        fls_stats.write_errors++;
        return DEV_ERR_INVALID_ARG;
    }
    
    // Align length up to write alignment
    uint32_t aligned_length = ((length + write_align - 1) / write_align) * write_align;
    
    // Check sector boundary
    uint32_t sector_end = sector->base_address + sector->size;
    if (address + aligned_length > sector_end) {
        DBG_OUT_E("Write would exceed sector boundary: addr=0x%08X, len=%u, sector_end=0x%08X",
                  address, aligned_length, sector_end);
        fls_stats.write_errors++;
        return DEV_ERR_INVALID_ARG;
    }
    
    // Prepare write buffer with padding
    uint8_t write_buffer[aligned_length];
    memcpy(write_buffer, data, length);
    
    // Pad with erase value (0xFF)
    if (aligned_length > length) {
        memset(write_buffer + length, sector->erase_value, aligned_length - length);
    }
    
    // Write in flash words
    uint32_t write_addr = address;
    for (uint32_t offset = 0; offset < aligned_length; offset += write_align) {
        dev_err_t err = fls_hal_write_flash_word(write_addr, write_buffer + offset);
        if (err != DEV_OK) {
            DBG_OUT_E("Flash write failed at 0x%08X", write_addr);
            fls_stats.write_errors++;
            return err;
        }
        write_addr += write_align;
    }
    
    fls_stats.total_writes++;
    return DEV_OK;
}

/**
 * @brief Erase flash sector
 */
dev_err_t dev_fls_erase_sector(uint8_t sector_index)
{
    DEV_RETURN_ON_FALSE(fls_state.initialized, DEV_ERR_MODULE_NOT_INIT, "Fls not initialized");
    DEV_RETURN_ON_FALSE(sector_index < fls_state.config.sector_count, DEV_ERR_INVALID_ARG, "Invalid sector index %u", sector_index);
    
    const Fls_SectorDescriptor_t *sector = &fls_state.config.sector_table[sector_index];
    
    DBG_OUT_I("Erasing sector [%u] %s at 0x%08X (%u KB)...", 
              sector_index, sector->name, sector->base_address, sector->size / 1024);
    
    dev_err_t err = fls_hal_erase_sector_by_hw_index(sector->bank_index, sector->sector_index);
    
    if (err == DEV_OK) {
        fls_stats.total_erases++;
        DBG_OUT_I("Sector erased successfully");
    } else {
        fls_stats.erase_errors++;
        DBG_OUT_E("Sector erase failed");
    }
    
    return err;
}

/**
 * @brief Check if flash region is blank
 */
bool dev_fls_blank_check(uint32_t address, uint32_t length)
{
    if (!fls_state.initialized || !dev_fls_is_managed_address(address)) {
        return false;
    }
    
    const Fls_SectorDescriptor_t *sector = dev_fls_get_sector_by_address(address);
    if (sector == NULL) {
        return false;
    }
    
    const uint8_t *ptr = (const uint8_t*)address;
    for (uint32_t i = 0; i < length; i++) {
        if (ptr[i] != sector->erase_value) {
            return false;  // Found non-erased byte
        }
    }
    
    return true;  // All bytes match erase value
}

/**
 * @brief Get sector by physical address
 */
const Fls_SectorDescriptor_t* dev_fls_get_sector_by_address(uint32_t address)
{
    if (!fls_state.initialized) return NULL;
    
    for (uint8_t i = 0; i < fls_state.config.sector_count; i++) {
        const Fls_SectorDescriptor_t *sector = &fls_state.config.sector_table[i];
        if (address >= sector->base_address && 
            address < (sector->base_address + sector->size)) {
            return sector;
        }
    }
    return NULL;
}

/**
 * @brief Get sector by table index
 */
const Fls_SectorDescriptor_t* dev_fls_get_sector_by_index(uint8_t sector_index)
{
    if (!fls_state.initialized || sector_index >= fls_state.config.sector_count) {
        return NULL;
    }
    return &fls_state.config.sector_table[sector_index];
}

/**
 * @brief Check if address is managed
 */
bool dev_fls_is_managed_address(uint32_t address)
{
    return (dev_fls_get_sector_by_address(address) != NULL);
}

/**
 * @brief Get statistics
 */
dev_err_t dev_fls_get_statistics(dev_fls_statistics_t *stats)
{
    DEV_RETURN_ON_FALSE(stats != NULL, DEV_ERR_INVALID_ARG, "Stats pointer is NULL");
    memcpy(stats, &fls_stats, sizeof(dev_fls_statistics_t));
    return DEV_OK;
}

/**
 * @brief HAL: Write 32-byte flash word
 */
static dev_err_t fls_hal_write_flash_word(uint32_t address, const uint8_t *data)
{
    HAL_FLASH_Unlock();
    
    // STM32H7: Program 256-bit (32 bytes) flash word
    HAL_StatusTypeDef hal_status = HAL_FLASH_Program(FLASH_TYPEPROGRAM_FLASHWORD, address, (uint32_t)data);
    
    HAL_FLASH_Lock();
    
    if (hal_status != HAL_OK) {
        return DEV_ERR_HARDWARE;
    }
    
    return DEV_OK;
}

/**
 * @brief HAL: Erase sector by bank and hardware sector index
 */
static dev_err_t fls_hal_erase_sector_by_hw_index(uint8_t bank, uint8_t sector)
{
    FLASH_EraseInitTypeDef erase_init;
    uint32_t sector_error = 0;
    
    erase_init.TypeErase = FLASH_TYPEERASE_SECTORS;
    erase_init.Banks = (bank == 1) ? FLASH_BANK_1 : FLASH_BANK_2;
    erase_init.Sector = sector;
    erase_init.NbSectors = 1;
    erase_init.VoltageRange = FLASH_VOLTAGE_RANGE_3;  // 2.7-3.6V
    
    HAL_FLASH_Unlock();
    
    HAL_StatusTypeDef hal_status = HAL_FLASHEx_Erase(&erase_init, &sector_error);
    
    HAL_FLASH_Lock();
    
    if (hal_status != HAL_OK) {
        DBG_OUT_E("HAL erase failed: Bank %u, Sector %u, Error: 0x%08X", bank, sector, sector_error);
        return DEV_ERR_HARDWARE;
    }
    
    return DEV_OK;
}

/**
 * @brief Get current configuration
 */
const Fls_ConfigType* dev_fls_get_config(void)
{
    if (!fls_state.initialized) {
        return NULL;
    }
    return &fls_state.config;
}
