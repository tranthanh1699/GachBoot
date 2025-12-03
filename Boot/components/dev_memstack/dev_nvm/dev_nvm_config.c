#include "dev_nvm_config.h"

// RAM Mirrors for each block
uint8_t nvm_ram_vin[17] = {0};
uint8_t nvm_ram_ecu_serial[4] = {0};
uint8_t nvm_ram_programming_date[4] = {0};
uint8_t nvm_ram_ecu_config[2] = {0};
uint8_t nvm_ram_fingerprint[32] = {0};
uint8_t nvm_ram_dtc_storage[20] = {0};

// Default ROM values for each block
static const uint8_t default_vin[17] = "WVWZZZ1KZXW123456";  // Default VIN
static const uint8_t default_ecu_serial[4] = {0x00, 0x00, 0x00, 0x01};  // Serial 1
static const uint8_t default_programming_date[4] = {0x02, 0x0C, 0x07, 0xE9};  // Dec 2, 2025
static const uint8_t default_ecu_config[2] = {0x00, 0x01};  // Config version 1
static const uint8_t default_fingerprint[32] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                                                  0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                                                  0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                                                  0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// NVM Block Configuration Table (nv_address removed - FLS manages dynamically)
const dev_nvm_block_config_t dev_nvm_block_config_table[] = {
    {
        .block_id = DEV_NVM_BLOCK_VIN,
        .block_size = 17,
        .rom_address = default_vin,
        .ram_address = nvm_ram_vin,
        .block_type = DEV_NVM_BLOCK_REDUNDANT,
        .write_protection = false,
        .use_crc = true
    },
    {
        .block_id = DEV_NVM_BLOCK_ECU_SERIAL,
        .block_size = 4,
        .rom_address = default_ecu_serial,
        .ram_address = nvm_ram_ecu_serial,
        .block_type = DEV_NVM_BLOCK_REDUNDANT,
        .write_protection = true,
        .use_crc = true
    },
    {
        .block_id = DEV_NVM_BLOCK_PROGRAMMING_DATE,
        .block_size = 4,
        .rom_address = default_programming_date,
        .ram_address = nvm_ram_programming_date,
        .block_type = DEV_NVM_BLOCK_NATIVE,
        .write_protection = false,
        .use_crc = true
    },
    {
        .block_id = DEV_NVM_BLOCK_ECU_CONFIG,
        .block_size = 2,
        .rom_address = default_ecu_config,
        .ram_address = nvm_ram_ecu_config,
        .block_type = DEV_NVM_BLOCK_NATIVE,
        .write_protection = false,
        .use_crc = true
    },
    {
        .block_id = DEV_NVM_BLOCK_FINGERPRINT,
        .block_size = 32,
        .rom_address = default_fingerprint,
        .ram_address = nvm_ram_fingerprint,
        .block_type = DEV_NVM_BLOCK_REDUNDANT,
        .write_protection = false,
        .use_crc = true
    },
    {
        .block_id = DEV_NVM_BLOCK_DTC_STORAGE,
        .block_size = 20,
        .rom_address = NULL,
        .ram_address = nvm_ram_dtc_storage,
        .block_type = DEV_NVM_BLOCK_NATIVE,
        .write_protection = false,
        .use_crc = true
    }
};

const uint16_t dev_nvm_block_config_count = sizeof(dev_nvm_block_config_table) / sizeof(dev_nvm_block_config_t);
