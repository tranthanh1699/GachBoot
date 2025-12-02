#ifndef DEV_NVM_CONFIG_H
#define DEV_NVM_CONFIG_H

#include "dev_nvm.h"

/**
 * @brief NVM Configuration Parameters
 */

// Flash configuration now managed by FLS driver
// NVM uses dynamic addressing via dev_fls_write()
#define DEV_NVM_MAX_BLOCKS              16          // Maximum number of blocks

// Block IDs (Application-defined)
#define DEV_NVM_BLOCK_VIN               0x0001      // VIN storage (17 bytes)
#define DEV_NVM_BLOCK_ECU_SERIAL        0x0002      // ECU Serial (4 bytes)
#define DEV_NVM_BLOCK_PROGRAMMING_DATE  0x0003      // Programming date (4 bytes)
#define DEV_NVM_BLOCK_ECU_CONFIG        0x0004      // ECU configuration (2 bytes)
#define DEV_NVM_BLOCK_FINGERPRINT       0x0005      // Fingerprint (32 bytes)
#define DEV_NVM_BLOCK_DTC_STORAGE       0x0006      // DTC storage (256 bytes)

/**
 * @brief RAM mirrors for NVM blocks
 */
extern uint8_t nvm_ram_vin[17];
extern uint8_t nvm_ram_ecu_serial[4];
extern uint8_t nvm_ram_programming_date[4];
extern uint8_t nvm_ram_ecu_config[2];
extern uint8_t nvm_ram_fingerprint[32];
extern uint8_t nvm_ram_dtc_storage[20];

/**
 * @brief NVM Block Configuration Table
 */
extern const dev_nvm_block_config_t dev_nvm_block_config_table[DEV_NVM_MAX_BLOCKS];
extern const uint16_t dev_nvm_block_config_count;

#endif // DEV_NVM_CONFIG_H
