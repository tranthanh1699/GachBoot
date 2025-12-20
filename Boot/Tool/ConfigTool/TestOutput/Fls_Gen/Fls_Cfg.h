/**
 * @file Fls_Cfg.h
 * @brief Flash Driver Configuration (CODE GENERATED - DO NOT EDIT MANUALLY)
 * 
 * Flash Driver Configuration for NVM Storage
 * 
 * AUTOSAR Standard: AUTOSAR_SWS_FlashDriver.pdf
 * Generator: GachBoot ConfigTool
 * Generated: 2025-12-20 22:23:20
 */

#ifndef FLS_CFG_H
#define FLS_CFG_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

/* ============================================================================
 * Configuration Parameters (Generated)
 * ============================================================================ */

/**
 * @brief MCU: STM32H743VIT6
 * Flash Memory: 2MB (0x08000000 - 0x081FFFFF)
 */

/* Hardware Constraints */
#define FLS_CFG_WRITE_ALIGNMENT         32U     /**< Flash write alignment */
#define FLS_CFG_READ_ALIGNMENT          1U      /**< Byte-aligned read */
#define FLS_CFG_ERASE_VALUE             0xFFU   /**< NOR flash erased state */
#define FLS_CFG_BASE_ADDRESS            0x08000000U  /**< Flash start address */
#define FLS_CFG_TOTAL_SIZE              (2097152U)  /**< Total flash size */

/* Performance Parameters */
#define FLS_CFG_WRITE_TIMEOUT_MS        100U    /**< Max write timeout */
#define FLS_CFG_ERASE_TIMEOUT_MS        2000U   /**< Max erase timeout per sector */

/* ============================================================================
 * Physical Sector Descriptors (Generated)
 * ============================================================================ */

/**
 * @brief Flash sector descriptor
 * 
 * Describes physical flash sector properties.
 * Each sector is independently erasable hardware unit.
 */
typedef struct {
    uint32_t base_address;      /**< Physical start address */
    uint32_t size;              /**< Sector size in bytes */
    uint8_t  bank_index;        /**< Flash bank number (1 or 2) */
    uint8_t  sector_index;      /**< Hardware sector index within bank (0-7) */
    uint8_t  erase_value;       /**< Value after erase (0xFF for NOR flash) */
    const char *name;           /**< Human-readable sector name */
} Fls_SectorDescriptor_t;

/**
 * @brief Complete flash configuration
 * 
 * Contains all generated configuration data.
 * Passed to Fls_Init() at runtime.
 */
typedef struct {
    const Fls_SectorDescriptor_t *sector_table;    /**< Pointer to sector array */
    uint8_t sector_count;                          /**< Number of sectors */
    uint32_t write_alignment;                      /**< Write alignment requirement */
    uint32_t read_alignment;                       /**< Read alignment requirement */
    uint8_t erase_value;                           /**< Erase value */
    uint32_t write_timeout_ms;                     /**< Write timeout */
    uint32_t erase_timeout_ms;                     /**< Erase timeout */
} Fls_ConfigType;

/* ============================================================================
 * Generated Configuration Instance
 * ============================================================================ */

/**
 * @brief Generated sector table
 */
extern const Fls_SectorDescriptor_t Fls_SectorTable[];
extern const uint8_t Fls_SectorCount;

/**
 * @brief Default configuration instance
 * 
 * Pre-configured with generated values.
 * Can be passed directly to Fls_Init().
 */
extern const Fls_ConfigType Fls_Config;

#ifdef __cplusplus
}
#endif

#endif /* FLS_CFG_H */
