#include "dev_fls.h"
#include "dev_fls_config.h"
#include "stm32h7xx_hal.h"
#include <string.h>

CONFIG_LOG_TAG(DEV_FLS, true)

// FLS Runtime State (minimal - no sector management)
typedef struct {
    bool initialized;
} dev_fls_state_t;

static dev_fls_state_t fls_state = {0};
static dev_fls_statistics_t fls_stats = {0};

// Forward declarations
static dev_err_t fls_hal_erase_sector(uint8_t sector_index);
#if DEV_FLS_ERASE_BY_PAGE
static dev_err_t fls_hal_erase_page(uint32_t page_address);
#endif
static dev_err_t fls_hal_write(uint32_t address, const uint8_t *data, uint32_t length);

/**
 * @brief Initialize FLS module
 */
dev_err_t dev_fls_init(void)
{
    if (fls_state.initialized) {
        return DEV_OK;
    }
    
    DBG_OUT_I("Initializing FLS driver (hardware-only mode)...");
    
    memset(&fls_state, 0, sizeof(fls_state));
    memset(&fls_stats, 0, sizeof(fls_stats));
    
    fls_state.initialized = true;
    
    DBG_OUT_I("FLS initialized - Manages sectors 0x%08X to 0x%08X", 
              DEV_FLS_SECTOR_A_BASE_ADDRESS, 
              DEV_FLS_SECTOR_B_BASE_ADDRESS + DEV_FLS_SECTOR_SIZE - 1);
    
    return DEV_OK;
}

/**
 * @brief Read data from flash
 */
dev_err_t dev_fls_read(uint32_t address, uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(fls_state.initialized, DEV_ERR_MODULE_NOT_INIT, "FLS not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    DEV_RETURN_ON_FALSE(dev_fls_is_managed_address(address), DEV_ERR_INVALID_ARG, "Address not managed");
    
    // Direct memory read from flash
    memcpy(data, (const void*)address, length);
    fls_stats.total_reads++;
    
    return DEV_OK;
}

/**
 * @brief Write data to flash
 */
dev_err_t dev_fls_write(uint32_t address, const uint8_t *data, uint32_t length)
{
    DEV_RETURN_ON_FALSE(fls_state.initialized, DEV_ERR_MODULE_NOT_INIT, "FLS not initialized");
    DEV_RETURN_ON_FALSE(data != NULL, DEV_ERR_INVALID_ARG, "Data is NULL");
    DEV_RETURN_ON_FALSE(length > 0, DEV_ERR_INVALID_ARG, "Length is zero");
    DEV_RETURN_ON_FALSE(dev_fls_is_managed_address(address), DEV_ERR_INVALID_ARG, "Address not managed");
    
    // Check alignment
    if (address % DEV_FLS_WRITE_ALIGNMENT != 0) {
        DBG_OUT_E("Address 0x%08X not aligned to %u bytes", address, DEV_FLS_WRITE_ALIGNMENT);
        return DEV_ERR_INVALID_ARG;
    }
    
    // Align length up to write alignment
    uint32_t aligned_length = ((length + DEV_FLS_WRITE_ALIGNMENT - 1) / DEV_FLS_WRITE_ALIGNMENT) * DEV_FLS_WRITE_ALIGNMENT;
    
    // Check if write would exceed sector boundary
    uint32_t sector_base = (address == DEV_FLS_SECTOR_A_BASE_ADDRESS || 
                             (address >= DEV_FLS_SECTOR_A_BASE_ADDRESS && address < DEV_FLS_SECTOR_A_BASE_ADDRESS + DEV_FLS_SECTOR_SIZE))
                            ? DEV_FLS_SECTOR_A_BASE_ADDRESS : DEV_FLS_SECTOR_B_BASE_ADDRESS;
    uint32_t sector_end = sector_base + DEV_FLS_SECTOR_SIZE;
    
    if (address + aligned_length > sector_end) {
        DBG_OUT_E("Write would exceed sector boundary: addr=0x%08X, len=%u, end=0x%08X", 
                  address, aligned_length, sector_end);
        return DEV_ERR_INVALID_ARG;
    }
    
    // Create padded buffer if needed
    uint8_t write_buffer[aligned_length];
    memcpy(write_buffer, data, length);
    
    // Pad with 0xFF (erased flash state)
    if (aligned_length > length) {
        memset(write_buffer + length, 0xFF, aligned_length - length);
    }
    
    // Write to hardware
    dev_err_t err = fls_hal_write(address, write_buffer, aligned_length);
    
    if (err == DEV_OK) {
        fls_stats.total_writes++;
        DBG_OUT_I("FLS write: 0x%08X (%u bytes, %u aligned)", address, length, aligned_length);
    } else {
        fls_stats.write_errors++;
        DBG_OUT_E("FLS write failed at 0x%08X", address);
    }
    
    return err;
}

/**
 * @brief Erase flash sector
 */
dev_err_t dev_fls_erase_sector(uint32_t sector_address)
{
    DEV_RETURN_ON_FALSE(fls_state.initialized, DEV_ERR_MODULE_NOT_INIT, "FLS not initialized");
    DEV_RETURN_ON_FALSE(dev_fls_is_managed_address(sector_address), DEV_ERR_INVALID_ARG, "Invalid sector address");
    
#if DEV_FLS_ERASE_BY_SECTOR
    // STM32H7: Erase whole sector
    uint8_t sector_idx = dev_fls_get_sector_index(sector_address);
    if (sector_idx == 0xFF) {
        DBG_OUT_E("Invalid sector address 0x%08X", sector_address);
        return DEV_ERR_INVALID_ARG;
    }
    
    dev_err_t err = fls_hal_erase_sector(sector_idx);
    
    if (err == DEV_OK) {
        fls_stats.total_erases++;
        DBG_OUT_I("Sector 0x%08X erased", sector_address);
    } else {
        fls_stats.erase_errors++;
    }
    
    return err;
    
#elif DEV_FLS_ERASE_BY_PAGE
    // For MCUs with page erase
    uint32_t page_addr = sector_address;
    uint32_t sector_end = sector_address + DEV_FLS_SECTOR_SIZE;
    
    while (page_addr < sector_end) {
        dev_err_t err = fls_hal_erase_page(page_addr);
        if (err != DEV_OK) {
            DBG_OUT_E("Page erase failed at 0x%08X", page_addr);
            fls_stats.erase_errors++;
            return err;
        }
        page_addr += DEV_FLS_PAGE_SIZE;
        fls_stats.total_erases++;
    }
    
    DBG_OUT_I("Sector 0x%08X erased (page-level)", sector_address);
    return DEV_OK;
    
#else
    #error "FLS erase mode not configured"
#endif
}

/**
 * @brief Erase all FLS-managed sectors
 */
dev_err_t dev_fls_erase_all(void)
{
    DEV_RETURN_ON_FALSE(fls_state.initialized, DEV_ERR_MODULE_NOT_INIT, "FLS not initialized");
    
    DBG_OUT_I("Erasing all FLS sectors...");
    
    dev_err_t err_a = dev_fls_erase_sector(DEV_FLS_SECTOR_A_BASE_ADDRESS);
    dev_err_t err_b = dev_fls_erase_sector(DEV_FLS_SECTOR_B_BASE_ADDRESS);
    
    if (err_a != DEV_OK || err_b != DEV_OK) {
        DBG_OUT_E("Erase all failed");
        return DEV_ERR_HARDWARE;
    }
    
    DBG_OUT_I("All sectors erased");
    return DEV_OK;
}

/**
 * @brief Check if address is managed by FLS
 */
bool dev_fls_is_managed_address(uint32_t address)
{
    return (address >= DEV_FLS_SECTOR_A_BASE_ADDRESS && 
            address < (DEV_FLS_SECTOR_A_BASE_ADDRESS + DEV_FLS_SECTOR_SIZE)) ||
           (address >= DEV_FLS_SECTOR_B_BASE_ADDRESS && 
            address < (DEV_FLS_SECTOR_B_BASE_ADDRESS + DEV_FLS_SECTOR_SIZE));
}

/**
 * @brief Blank check - verify if flash area is erased
 */
bool dev_fls_blank_check(uint32_t address, uint32_t length)
{
    if (!dev_fls_is_managed_address(address)) {
        return false;
    }
    
    const uint32_t *ptr = (const uint32_t*)address;
    uint32_t words = length / 4;
    
    for (uint32_t i = 0; i < words; i++) {
        if (ptr[i] != 0xFFFFFFFF) {
            return false;
        }
    }
    
    // Check remaining bytes
    const uint8_t *byte_ptr = (const uint8_t*)(ptr + words);
    for (uint32_t i = 0; i < (length % 4); i++) {
        if (byte_ptr[i] != 0xFF) {
            return false;
        }
    }
    
    return true;
}

/**
 * @brief Get FLS statistics
 */
dev_err_t dev_fls_get_statistics(dev_fls_statistics_t *stats)
{
    DEV_RETURN_ON_FALSE(fls_state.initialized, DEV_ERR_MODULE_NOT_INIT, "FLS not initialized");
    DEV_RETURN_ON_FALSE(stats != NULL, DEV_ERR_INVALID_ARG, "Stats is NULL");
    
    memcpy(stats, &fls_stats, sizeof(dev_fls_statistics_t));
    return DEV_OK;
}

// ============================================================================
// Hardware Abstraction Layer (HAL)
// ============================================================================

/**
 * @brief HAL: Erase flash sector (STM32H7)
 */
static dev_err_t fls_hal_erase_sector(uint8_t sector_index)
{
    FLASH_EraseInitTypeDef erase_init;
    uint32_t sector_error = 0;
    
    // Unlock flash
    HAL_FLASH_Unlock();
    
    // Configure erase
    erase_init.TypeErase = FLASH_TYPEERASE_SECTORS;
    erase_init.Banks = FLASH_BANK_2;
    erase_init.Sector = sector_index;
    erase_init.NbSectors = 1;
    erase_init.VoltageRange = FLASH_VOLTAGE_RANGE_3;  // 2.7V - 3.6V
    
    // Execute erase
    HAL_StatusTypeDef status = HAL_FLASHEx_Erase(&erase_init, &sector_error);
    
    // Lock flash
    HAL_FLASH_Lock();
    
    if (status != HAL_OK || sector_error != 0xFFFFFFFF) {
        DBG_OUT_E("HAL flash erase failed: status=%d, error=0x%08X", status, sector_error);
        return DEV_ERR_HARDWARE;
    }
    
    return DEV_OK;
}

#if DEV_FLS_ERASE_BY_PAGE
/**
 * @brief HAL: Erase flash page (placeholder for MCUs with page erase)
 */
static dev_err_t fls_hal_erase_page(uint32_t page_address)
{
    DBG_OUT_E("Page erase not implemented for this MCU");
    return DEV_ERR_NOT_SUPPORTED;
}
#endif

/**
 * @brief HAL: Write to flash (STM32H7)
 */
static dev_err_t fls_hal_write(uint32_t address, const uint8_t *data, uint32_t length)
{
    // Unlock flash
    HAL_FLASH_Unlock();
    
    // STM32H7 writes in 256-bit (32 bytes) flash words
    uint32_t *src = (uint32_t*)data;
    uint32_t words = length / 32;
    
    for (uint32_t i = 0; i < words; i++) {
        uint32_t write_addr = address + (i * 32);
        
        // Program 256-bit flash word (8 x 32-bit words)
        HAL_StatusTypeDef status = HAL_FLASH_Program(FLASH_TYPEPROGRAM_FLASHWORD, 
                                                       write_addr, 
                                                       (uint32_t)(src + i * 8));
        
        if (status != HAL_OK) {
            HAL_FLASH_Lock();
            DBG_OUT_E("HAL flash write failed at 0x%08X: status=%d", write_addr, status);
            return DEV_ERR_HARDWARE;
        }
    }
    
    // Lock flash
    HAL_FLASH_Lock();
    
    return DEV_OK;
}
