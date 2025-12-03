#ifndef DEV_NVM_H
#define DEV_NVM_H

#include "dev_common.h"
#include <stdint.h>
#include <stdbool.h>

/**
 * @brief NVM Block Management Types (AUTOSAR-like)
 */

// NVM Block Management Type
typedef enum {
    DEV_NVM_BLOCK_NATIVE = 0,           // Single copy (no redundancy)
    DEV_NVM_BLOCK_REDUNDANT = 1         // Dual copy with CRC validation
} dev_nvm_block_type_t;

// NVM Block State
typedef enum {
    DEV_NVM_BLOCK_INVALID = 0,          // Block not initialized or corrupted
    DEV_NVM_BLOCK_VALID = 1,            // Block data is valid
    DEV_NVM_BLOCK_INCONSISTENT = 2      // Redundant copies don't match
} dev_nvm_block_state_t;

// NVM Operation Result
typedef enum {
    DEV_NVM_REQ_OK = 0,                 // Operation successful
    DEV_NVM_REQ_PENDING = 1,            // Operation in progress
    DEV_NVM_REQ_BLOCK_SKIPPED = 2,      // Block skipped (not changed)
    DEV_NVM_REQ_NV_INVALIDATED = 3,     // NV block invalidated
    DEV_NVM_REQ_CANCELED = 4,           // Operation canceled
    DEV_NVM_REQ_NOT_OK = 5              // Operation failed
} dev_nvm_request_result_t;

/**
 * @brief NVM Block Configuration (AUTOSAR NvM compliant)
 * Note: nv_address removed - FLS manages flash addressing dynamically
 */
typedef struct {
    uint16_t block_id;                  // Unique block identifier
    uint16_t block_size;                // Data size in bytes
    const uint8_t *rom_address;         // Default ROM data (const array)
    uint8_t *ram_address;               // RAM mirror address
    dev_nvm_block_type_t block_type;    // Native or Redundant
    bool write_protection;              // Write protection flag
    bool use_crc;                       // Enable CRC validation
} dev_nvm_block_config_t;

/**
 * @brief NVM Block in Flash Layout (AUTOSAR style)
 * 
 * NATIVE block:
 *   [Data (N bytes)][CRC32 (4 bytes)]
 * 
 * REDUNDANT block:
 *   [Primary Data (N bytes)][Primary CRC32 (4 bytes)]
 *   [Secondary Data (N bytes)][Secondary CRC32 (4 bytes)]
 */

/**
 * @brief NVM Statistics
 */
typedef struct {
    uint32_t total_reads;               // Total read operations
    uint32_t total_writes;              // Total write operations
    uint32_t read_errors;               // Read error count
    uint32_t write_errors;              // Write error count
    uint32_t crc_errors;                // CRC validation errors
} dev_nvm_statistics_t;

/**
 * @brief Initialize NVM module
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_init(void);

/**
 * @brief Read NVM block
 * @param block_id Block identifier
 * @param data Destination buffer
 * @param length Data length
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_read_block(uint16_t block_id, uint8_t *data, uint16_t length);

/**
 * @brief Write NVM block
 * @param block_id Block identifier
 * @param data Source buffer
 * @param length Data length
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_write_block(uint16_t block_id, const uint8_t *data, uint16_t length);

/**
 * @brief Restore NVM block from ROM to RAM
 * @param block_id Block identifier
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_restore_block(uint16_t block_id);

/**
 * @brief Invalidate NVM block
 * @param block_id Block identifier
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_invalidate_block(uint16_t block_id);

/**
 * @brief Erase NVM block
 * @param block_id Block identifier
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_erase_block(uint16_t block_id);

/**
 * @brief Get block state
 * @param block_id Block identifier
 * @param state Output state
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_get_block_state(uint16_t block_id, dev_nvm_block_state_t *state);

/**
 * @brief Set RAM block changed flag (mark for write)
 * @param block_id Block identifier
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_set_ram_block_changed(uint16_t block_id);

/**
 * @brief Get NVM statistics
 * @param stats Output statistics
 * @return dev_err_t Error code
 */
dev_err_t dev_nvm_get_statistics(dev_nvm_statistics_t *stats);

/**
 * @brief Main function for background processing
 * @note Call periodically from main loop
 */
void dev_nvm_main_function(void);

#endif // DEV_NVM_H
