# Memory Stack Module (AUTOSAR-Inspired)

<div align="center">

**4-Layer Non-Volatile Memory Management System**

[Architecture](#-architecture) • [Configuration](#-configuration) • [Initialization](#-initialization) • [Usage](#-usage) • [Porting](#-porting-guide) • [API Reference](#-api-reference)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Layer Responsibilities](#-layer-responsibilities)
- [Configuration](#-configuration)
  - [Adding New Block](#adding-new-nvm-block)
  - [Flash Memory Layout](#configuring-flash-memory-layout)
  - [Sector Configuration](#configuring-sectors)
- [Initialization](#-initialization)
- [Usage](#-usage)
  - [Writing Data](#writing-data-to-nvm)
  - [Reading Data](#reading-data-from-nvm)
  - [Block Management](#block-management)
  - [Statistics](#getting-statistics)
- [Porting Guide](#-porting-guide)
  - [Port to New Hardware](#porting-to-new-hardware-stm32)
  - [Port to Different MCU Family](#porting-to-different-mcu-family)
- [API Reference](#-api-reference)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

Memory Stack is a 4-layer non-volatile memory (NVM) management system based on AUTOSAR standards, designed for:

- ✅ **Automotive applications** - Bootloader, ECU configuration data
- ✅ **Industrial systems** - Calibration data, device parameters
- ✅ **IoT devices** - Settings persistence, logging

### Key Features

| Feature | Description |
|---------|-------------|
| **AUTOSAR Architecture** | NvM → MemIf → Fee → Fls (4 layers) |
| **Block Types** | NATIVE (single copy), REDUNDANT (dual copy with CRC) |
| **Wear Leveling** | 2-sector ping-pong strategy |
| **Dynamic Addressing** | Fee allocates addresses automatically |
| **Power-Loss Protection** | Inline CRC32 after each write |
| **Fast Reads** | RAM mirrors for zero flash access |
| **Alignment Handling** | Auto-padding to flash word boundaries |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│              (Your code: write/read NVM blocks)             │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ dev_nvm_write_block()
                            │ dev_nvm_read_block()
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   NvM (NV Manager)                          │
│  • Block management (6 blocks: VIN, Serial, etc.)           │
│  • CRC32 calculation & validation                           │
│  • Redundancy (primary + secondary copies)                  │
│  • RAM mirrors for fast read                                │
│  Files: dev_nvm.c, dev_nvm_config.h                         │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ dev_memif_write()
                            │ dev_memif_read()
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            MemIf (Memory Interface - Routing Layer)         │
│  • Device abstraction (Flash/EEPROM agnostic)               │
│  • Job status tracking                                      │
│  • Routes all calls to Fee                                  │
│  Files: dev_memif.c                                         │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ dev_fee_write()
                            │ dev_fee_read()
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Fee (Flash EEPROM Emulation)                   │
│  • Logical sector management (A/B sectors)                  │
│  • Dynamic address allocation                               │
│  • Wear leveling (auto sector switch when full)             │
│  • Write position tracking                                  │
│  Files: dev_fee.c, dev_fee_config.h                         │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ dev_fls_write()
                            │ dev_fls_read()
                            │ dev_fls_erase_sector()
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Fls (Flash Hardware Driver)                    │
│  • STM32H7 flash read/write/erase                           │
│  • 32-byte alignment & padding (0xFF)                       │
│  • Sector boundary protection                               │
│  • HAL API wrapper                                          │
│  Files: dev_fls.c, dev_fls_config.h                         │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ HAL_FLASH_Program()
                            ▼
                    [STM32H7 Flash Hardware]
```

---

## 📦 Layer Responsibilities

### 1. NvM (NV Manager) - `dev_nvm/`

**Role:** Application-facing block management

**Responsibilities:**
- Manage 6 NVM blocks (VIN, ECU Serial, Fingerprint, etc.)
- Calculate & validate CRC32 for data integrity
- Handle REDUNDANT blocks (write 2 copies)
- Maintain RAM mirrors for fast reads
- Track block states (VALID/INVALID/CHANGED)

**Configuration:**
- `dev_nvm_config.h` - Block definitions (ID, length, type, ROM defaults)

### 2. MemIf (Memory Interface) - `dev_memif/`

**Role:** Device abstraction layer (AUTOSAR standard)

**Responsibilities:**
- Route read/write/erase calls to Fee
- Track job status (IDLE/BUSY/OK/FAILED)
- Provide device-agnostic API

**Configuration:**
- No configuration needed (simple routing)

### 3. Fee (Flash EEPROM Emulation) - `dev_fee/`

**Role:** Sector management & wear leveling

**Responsibilities:**
- Manage 2 sectors (Sector A/B) for ping-pong strategy
- Allocate addresses dynamically (no fixed addresses)
- Switch sectors automatically when full (>127KB used)
- Track write position & sector usage
- Scan sectors at boot to find active sector

**Configuration:**
- `dev_fee_config.h` - Sector addresses, sizes

### 4. Fls (Flash Driver) - `dev_fls/`

**Role:** Hardware abstraction

**Responsibilities:**
- Read/write/erase STM32H7 flash memory
- Handle 32-byte write alignment (pad with 0xFF)
- Protect sector boundaries
- Wrap STM32 HAL APIs

**Configuration:**
- `dev_fls_config.h` - Flash addresses, alignment, erase modes

---

## ⚙️ Configuration

### Adding New NVM Block

**Step 1:** Define block in `dev_nvm/include/dev_nvm_config.h`

```c
// Block IDs (unique 16-bit identifiers)
#define DEV_NVM_BLOCK_VIN           0x0001
#define DEV_NVM_BLOCK_ECU_SERIAL    0x0002
#define DEV_NVM_BLOCK_FINGERPRINT   0x0003
#define DEV_NVM_BLOCK_YOUR_BLOCK    0x0007  // Add new ID

// Block configuration array
static const dev_nvm_block_config_t nvm_block_config[] = {
    // ... existing blocks ...
    
    // Your new block
    {
        .block_id = DEV_NVM_BLOCK_YOUR_BLOCK,
        .block_length = 64,                          // Data length in bytes
        .block_type = DEV_NVM_BLOCK_TYPE_REDUNDANT,  // NATIVE or REDUNDANT
        .ram_data = nvm_ram_your_block,              // RAM mirror pointer
        .rom_data = default_your_block,              // Default value pointer
        .write_protection = false,                   // true = read-only
        .crc_enabled = true                          // Enable CRC validation
    }
};

// Update block count
#define DEV_NVM_BLOCK_COUNT 7  // Was 6, now 7
```

**Step 2:** Declare RAM mirror & ROM default in `dev_nvm_config.h`

```c
// RAM mirrors (global variables for fast read)
static uint8_t nvm_ram_vin[17];
static uint8_t nvm_ram_ecu_serial[4];
static uint8_t nvm_ram_your_block[64];  // Add this

// ROM defaults (const data for initialization)
static const uint8_t default_vin[17] = "VIN0000000000000";
static const uint8_t default_ecu_serial[4] = {0x00, 0x00, 0x00, 0x01};
static const uint8_t default_your_block[64] = {0xFF, 0xFF, ...};  // Add this
```

**Step 3:** Use in application code

```c
#include "dev_nvm.h"

// Write data to new block
uint8_t my_data[64] = {0x01, 0x02, 0x03, ...};
dev_err_t err = dev_nvm_write_block(DEV_NVM_BLOCK_YOUR_BLOCK, my_data, 64);
if (err == DEV_OK) {
    DBG_OUT_I("[NVM] Your block written successfully");
}

// Read data from new block (fast - from RAM mirror)
uint8_t buffer[64];
err = dev_nvm_read_block(DEV_NVM_BLOCK_YOUR_BLOCK, buffer, 64);
```

**Block Type Selection:**

| Type | When to Use | Storage | Integrity |
|------|-------------|---------|-----------|
| **NATIVE** | Non-critical data, large blocks | 1 copy + CRC32 | CRC32 validation |
| **REDUNDANT** | Critical data (VIN, Serial) | 2 copies + 2 CRC32 | Dual redundancy + CRC |

**Memory Cost:**
- NATIVE: `length + 4 bytes` (data + CRC)
- REDUNDANT: `2 × (length + 4 bytes)` (primary + secondary)

---

### Configuring Flash Memory Layout

**File:** `dev_fls/include/dev_fls_config.h`

```c
// STM32H743: Bank 2, Sectors 6-7 (256KB total)
#define DEV_FLS_SECTOR_A_BASE_ADDRESS   0x081C0000  // Sector 6 (128KB)
#define DEV_FLS_SECTOR_B_BASE_ADDRESS   0x081E0000  // Sector 7 (128KB)

// Flash word alignment (STM32H7: 32 bytes = 256 bits)
#define DEV_FLS_WRITE_ALIGNMENT         32

// Erase mode
#define DEV_FLS_ERASE_BY_SECTOR         1
#define DEV_FLS_ERASE_BY_PAGE           0

// Helper functions
static inline uint8_t dev_fls_get_sector_index(uint32_t address) {
    if (address == DEV_FLS_SECTOR_A_BASE_ADDRESS) return 6;
    if (address == DEV_FLS_SECTOR_B_BASE_ADDRESS) return 7;
    return 0xFF;  // Invalid
}

static inline uint32_t dev_fls_get_alternate_sector(uint32_t address) {
    if (address == DEV_FLS_SECTOR_A_BASE_ADDRESS) 
        return DEV_FLS_SECTOR_B_BASE_ADDRESS;
    return DEV_FLS_SECTOR_A_BASE_ADDRESS;
}
```

**To use different sectors/banks:**

1. Check STM32 reference manual for flash layout
2. Update sector addresses (`0x081C0000` → your sector address)
3. Update sector indices in `dev_fls_get_sector_index()`
4. Ensure sectors are same size (128KB recommended)

---

### Configuring Sectors

**File:** `dev_fee/include/dev_fee_config.h`

```c
// Sector configuration (must match Fls config)
#define DEV_FEE_SECTOR_A_ADDRESS    0x081C0000
#define DEV_FEE_SECTOR_B_ADDRESS    0x081E0000
#define DEV_FEE_SECTOR_SIZE         (128 * 1024)  // 128KB

// Helper function
static inline uint32_t dev_fee_get_alternate_sector(uint32_t sector) {
    if (sector == DEV_FEE_SECTOR_A_ADDRESS)
        return DEV_FEE_SECTOR_B_ADDRESS;
    return DEV_FEE_SECTOR_A_ADDRESS;
}
```

**Important:** Fee sector addresses MUST match Fls sector addresses!

---

## 🚀 Initialization

### Initialization Order (Bottom-Up)

Initialize layers from hardware to application:

```c
#include "dev_nvm.h"  // Includes all lower layers

void system_init(void) {
    // 1. Initialize NVM (will auto-init MemIf → Fee → Fls)
    dev_err_t err = dev_nvm_init();
    if (err != DEV_OK) {
        DBG_OUT_E("[SYSTEM] NVM init failed: %d", err);
        return;
    }
    
    DBG_OUT_I("[SYSTEM] Memory stack initialized");
    
    // At this point:
    // - Fls initialized (flash ready)
    // - Fee scanned sectors (found active sector, write position)
    // - MemIf ready (routing layer)
    // - NvM restored all blocks from flash (or loaded ROM defaults)
}
```

### What Happens During Init?

**1. Fls Init (`dev_fls_init()`)**
- Clears internal state
- Marks driver as initialized
- Flash hardware already initialized by STM32 HAL

**2. Fee Init (`dev_fee_init()`)**
- Calls `dev_fls_init()`
- Scans both sectors (A & B) to find which has data:
  - Checks first 32 bytes of each sector
  - Selects sector with data as active
  - If both empty, defaults to Sector A
- Scans active sector to find next free write position
- Logs: `"Active sector: 0x081C0000, Write position: 0x081C0080"`

**3. MemIf Init (`dev_memif_init()`)**
- Calls `dev_fee_init()`
- Sets status to IDLE
- Simple routing layer, no complex logic

**4. NvM Init (`dev_nvm_init()`)**
- Calls `dev_memif_init()`
- Restores all 6 blocks from flash:
  - For each block:
    - If `nv_address != 0`: Read from flash, validate CRC
    - If `nv_address == 0` or CRC invalid: Load ROM default
  - Updates RAM mirrors
  - Sets block state (VALID/INVALID)
- Logs: `"Block 0x0001 restored from 0x081C0000"` or `"Block 0x0002 not found, loaded ROM defaults"`

---

## 💾 Usage

### Writing Data to NVM

**Basic Write (NATIVE Block):**

```c
#include "dev_nvm.h"

uint8_t fingerprint[32] = "MyProgrammingFingerprint2024...";

dev_err_t err = dev_nvm_write_block(
    DEV_NVM_BLOCK_FINGERPRINT,  // Block ID
    fingerprint,                 // Data pointer
    32                           // Length (must match config)
);

if (err == DEV_OK) {
    DBG_OUT_I("[APP] Fingerprint written");
} else {
    DBG_OUT_E("[APP] Write failed: %d", err);
}
```

**Write with Validation (REDUNDANT Block):**

```c
uint8_t vin[17] = "WVWZZZ1KZXW123456";

// Write (automatic redundancy - 2 copies written)
err = dev_nvm_write_block(DEV_NVM_BLOCK_VIN, vin, 17);

// Verify by reading back
uint8_t verify[17];
err = dev_nvm_read_block(DEV_NVM_BLOCK_VIN, verify, 17);
if (memcmp(vin, verify, 17) == 0) {
    DBG_OUT_I("[APP] VIN verified OK");
}
```

**Write Flow (What Happens Internally):**

```
Application: dev_nvm_write_block(VIN, "WVWZZZ...", 17)
    ↓
NvM: Calculate CRC32(data) = 0x12345678
     Write primary copy: dev_memif_write(0, data, 17, &addr1)
     Write primary CRC:  dev_memif_write(0, &crc, 4, &addr2)
     Write secondary copy: dev_memif_write(0, data, 17, &addr3)
     Write secondary CRC:  dev_memif_write(0, &crc, 4, &addr4)
     Update RAM mirror: nvm_ram_vin = "WVWZZZ..."
     Store address: block_runtime[0].nv_address = addr1
    ↓
MemIf: Route to Fee
    ↓
Fee: Allocate address: write_position = 0x081C0000
     Call dev_fls_write(0x081C0000, data, 17)
     Update write_position += 32 (aligned)
     Return allocated address
    ↓
Fls: Align length: 17 → 32 bytes
     Create buffer: [17 bytes data][15 bytes 0xFF padding]
     Call HAL_FLASH_Program(0x081C0000, buffer, 32)
    ↓
Hardware: Write 256-bit flash word to 0x081C0000
```

---

### Reading Data from NVM

**Fast Read (from RAM mirror - recommended):**

```c
uint8_t buffer[17];

// Reads from RAM mirror (zero flash access, instant)
dev_err_t err = dev_nvm_read_block(DEV_NVM_BLOCK_VIN, buffer, 17);

if (err == DEV_OK) {
    DBG_OUT_I("[APP] VIN: %.*s", 17, buffer);
}
```

**Restore from Flash (when RAM mirror invalid):**

```c
// Force restore from flash (e.g., after power-on)
dev_err_t err = dev_nvm_restore_block(DEV_NVM_BLOCK_VIN);

if (err == DEV_OK) {
    DBG_OUT_I("[APP] VIN restored from flash");
    
    // Now read from RAM mirror
    uint8_t vin[17];
    dev_nvm_read_block(DEV_NVM_BLOCK_VIN, vin, 17);
} else {
    DBG_OUT_W("[APP] Restore failed, using ROM defaults");
}
```

**Read Flow (Fast Path):**

```
Application: dev_nvm_read_block(VIN, buffer, 17)
    ↓
NvM: Copy from RAM mirror: memcpy(buffer, nvm_ram_vin, 17)
     Return immediately (no flash access!)
```

**Read Flow (Restore Path):**

```
Application: dev_nvm_restore_block(VIN)
    ↓
NvM: Get stored address: nv_address = 0x081C0000
     Read primary copy: dev_memif_read(0x081C0000, data_primary, 17)
     Read primary CRC:  dev_memif_read(0x081C0011, &crc_primary, 4)
     Validate: calc_crc == stored_crc? ✓
     Read secondary copy & validate ✓
     Compare primary vs secondary ✓
     Copy to RAM mirror: nvm_ram_vin = data_primary
    ↓
MemIf: Route to Fee
    ↓
Fee: Route to Fls
    ↓
Fls: Direct memory read: memcpy(buffer, (void*)0x081C0000, 17)
     (Flash is memory-mapped on STM32)
```

---

### Block Management

**Check Block State:**

```c
dev_nvm_block_state_t state = dev_nvm_get_block_state(DEV_NVM_BLOCK_VIN);

switch (state) {
    case DEV_NVM_BLOCK_VALID:
        DBG_OUT_I("Block is valid (data in RAM and flash)");
        break;
    case DEV_NVM_BLOCK_INVALID:
        DBG_OUT_W("Block is invalid (using ROM defaults)");
        break;
    case DEV_NVM_BLOCK_CHANGED:
        DBG_OUT_I("Block changed in RAM (not yet written to flash)");
        break;
    case DEV_NVM_BLOCK_UNKNOWN:
        DBG_OUT_E("Block ID not found");
        break;
}
```

**Invalidate Block (Reset to ROM Default):**

```c
dev_err_t err = dev_nvm_invalidate_block(DEV_NVM_BLOCK_FINGERPRINT);
// RAM mirror cleared, block marked as INVALID
// Next read returns ROM default value
```

**Restore All Blocks (e.g., after system reset):**

```c
void system_power_on_restore(void) {
    for (uint16_t block_id = 0x0001; block_id <= 0x0006; block_id++) {
        dev_err_t err = dev_nvm_restore_block(block_id);
        if (err != DEV_OK) {
            DBG_OUT_W("[SYSTEM] Block 0x%04X restore failed", block_id);
        }
    }
}
```

---

### Getting Statistics

**NvM Statistics:**

```c
dev_nvm_statistics_t nvm_stats = dev_nvm_get_statistics();

DBG_OUT_I("=== NVM Statistics ===");
DBG_OUT_I("Total reads:  %u", nvm_stats.total_reads);
DBG_OUT_I("Total writes: %u", nvm_stats.total_writes);
DBG_OUT_I("CRC errors:   %u", nvm_stats.crc_errors);
DBG_OUT_I("Blocks valid: %u / %u", nvm_stats.valid_blocks, DEV_NVM_BLOCK_COUNT);
```

**Fee Statistics:**

```c
dev_fee_statistics_t fee_stats = dev_fee_get_statistics();

DBG_OUT_I("=== Fee Statistics ===");
DBG_OUT_I("Active sector: 0x%08X", fee_stats.active_sector_address);
DBG_OUT_I("Sector usage:  %u / %u bytes", fee_stats.active_sector_usage, 128*1024);
DBG_OUT_I("Write position: 0x%08X", fee_stats.write_position);
DBG_OUT_I("Sector switches: %u", fee_stats.sector_switches);
DBG_OUT_I("Total writes: %u", fee_stats.total_writes);
```

**Fls Statistics:**

```c
dev_fls_statistics_t fls_stats = dev_fls_get_statistics();

DBG_OUT_I("=== Fls Statistics ===");
DBG_OUT_I("Total reads:  %u", fls_stats.total_reads);
DBG_OUT_I("Total writes: %u", fls_stats.total_writes);
DBG_OUT_I("Total erases: %u", fls_stats.total_erases);
```

---

## 🔧 Porting Guide

### Porting to New Hardware (STM32)

**Scenario:** You want to use different sectors on same STM32H743

**Steps:**

1. **Check flash layout in reference manual:**
   ```
   Example: Use Bank 1, Sectors 4-5 instead of Bank 2, Sectors 6-7
   Sector 4: 0x08060000 - 0x0807FFFF (128KB)
   Sector 5: 0x08080000 - 0x0809FFFF (128KB)
   ```

2. **Update `dev_fls/include/dev_fls_config.h`:**

   ```c
   // Old
   #define DEV_FLS_SECTOR_A_BASE_ADDRESS   0x081C0000
   #define DEV_FLS_SECTOR_B_BASE_ADDRESS   0x081E0000
   
   // New
   #define DEV_FLS_SECTOR_A_BASE_ADDRESS   0x08060000
   #define DEV_FLS_SECTOR_B_BASE_ADDRESS   0x08080000
   
   // Update sector index helper
   static inline uint8_t dev_fls_get_sector_index(uint32_t address) {
       if (address == 0x08060000) return 4;  // Sector 4
       if (address == 0x08080000) return 5;  // Sector 5
       return 0xFF;
   }
   ```

3. **Update `dev_fee/include/dev_fee_config.h`:**

   ```c
   #define DEV_FEE_SECTOR_A_ADDRESS    0x08060000
   #define DEV_FEE_SECTOR_B_ADDRESS    0x08080000
   #define DEV_FEE_SECTOR_SIZE         (128 * 1024)
   ```

4. **Rebuild & flash:**
   ```bash
   cmake --build build/Debug --target Boot -j 8
   ```

**That's it!** No code changes needed, only config updates.

---

### Porting to Different MCU Family

**Scenario:** Port from STM32H7 to STM32F4/G4/L4/etc.

#### Step 1: Update Fls Hardware Layer

**File:** `dev_fls/dev_fls.c`

**Functions to modify:**

1. **`fls_hal_write()`** - Flash programming

   ```c
   // STM32H7 (current)
   static dev_err_t fls_hal_write(uint32_t address, const uint8_t *data, uint16_t length) {
       HAL_FLASH_Unlock();
       
       // STM32H7: 256-bit flash word (32 bytes)
       for (uint32_t i = 0; i < length; i += 32) {
           HAL_StatusTypeDef status = HAL_FLASH_Program(
               FLASH_TYPEPROGRAM_FLASHWORD,
               address + i,
               (uint32_t)&data[i]
           );
           if (status != HAL_OK) {
               HAL_FLASH_Lock();
               return DEV_ERR_HARDWARE;
           }
       }
       
       HAL_FLASH_Lock();
       return DEV_OK;
   }
   
   // STM32F4 (example port)
   static dev_err_t fls_hal_write(uint32_t address, const uint8_t *data, uint16_t length) {
       HAL_FLASH_Unlock();
       
       // STM32F4: 32-bit word (4 bytes)
       for (uint32_t i = 0; i < length; i += 4) {
           uint32_t word = *(uint32_t*)&data[i];
           HAL_StatusTypeDef status = HAL_FLASH_Program(
               FLASH_TYPEPROGRAM_WORD,
               address + i,
               word
           );
           if (status != HAL_OK) {
               HAL_FLASH_Lock();
               return DEV_ERR_HARDWARE;
           }
       }
       
       HAL_FLASH_Lock();
       return DEV_OK;
   }
   ```

2. **`fls_hal_erase_sector()`** - Sector erase

   ```c
   // STM32H7 (current)
   static dev_err_t fls_hal_erase_sector(uint8_t sector_index) {
       FLASH_EraseInitTypeDef erase_init;
       erase_init.TypeErase = FLASH_TYPEERASE_SECTORS;
       erase_init.Banks = FLASH_BANK_2;  // Bank 2
       erase_init.Sector = sector_index;
       erase_init.NbSectors = 1;
       erase_init.VoltageRange = FLASH_VOLTAGE_RANGE_3;
       
       uint32_t sector_error = 0;
       HAL_FLASH_Unlock();
       HAL_StatusTypeDef status = HAL_FLASHEx_Erase(&erase_init, &sector_error);
       HAL_FLASH_Lock();
       
       return (status == HAL_OK) ? DEV_OK : DEV_ERR_HARDWARE;
   }
   
   // STM32F4 (example port)
   static dev_err_t fls_hal_erase_sector(uint8_t sector_index) {
       FLASH_EraseInitTypeDef erase_init;
       erase_init.TypeErase = FLASH_TYPEERASE_SECTORS;
       erase_init.Banks = FLASH_BANK_1;  // F4 has BANK_1
       erase_init.Sector = sector_index;
       erase_init.NbSectors = 1;
       erase_init.VoltageRange = FLASH_VOLTAGE_RANGE_3;  // 2.7V-3.6V
       
       uint32_t sector_error = 0;
       HAL_FLASH_Unlock();
       HAL_StatusTypeDef status = HAL_FLASHEx_Erase(&erase_init, &sector_error);
       HAL_FLASH_Lock();
       
       return (status == HAL_OK) ? DEV_OK : DEV_ERR_HARDWARE;
   }
   ```

#### Step 2: Update Flash Configuration

**File:** `dev_fls/include/dev_fls_config.h`

```c
// STM32H7 (current)
#define DEV_FLS_WRITE_ALIGNMENT         32  // 256-bit flash word

// STM32F4 (example)
#define DEV_FLS_WRITE_ALIGNMENT         4   // 32-bit word

// STM32L4 (example)
#define DEV_FLS_WRITE_ALIGNMENT         8   // 64-bit double word

// Update sector addresses for your MCU
#define DEV_FLS_SECTOR_A_BASE_ADDRESS   0x08060000  // Check datasheet!
#define DEV_FLS_SECTOR_B_BASE_ADDRESS   0x08080000
```

#### Step 3: Update Sector Configuration

Check your MCU's flash layout and update:

```c
// STM32H743 (current): 128KB sectors
#define DEV_FLS_SECTOR_SIZE         (128 * 1024)

// STM32F407 (example): 128KB sector 11
#define DEV_FLS_SECTOR_SIZE         (128 * 1024)

// STM32L476 (example): 2KB pages (use multiple pages as "sector")
#define DEV_FLS_SECTOR_SIZE         (64 * 2 * 1024)  // 64 pages = 128KB
```

#### Step 4: Test on New Hardware

```c
void test_memory_stack(void) {
    // Initialize
    dev_nvm_init();
    
    // Write test
    uint8_t test_data[32] = "Test data for new hardware!";
    dev_err_t err = dev_nvm_write_block(DEV_NVM_BLOCK_FINGERPRINT, test_data, 32);
    DBG_OUT_I("Write test: %s", (err == DEV_OK) ? "PASS" : "FAIL");
    
    // Read test
    uint8_t read_buffer[32];
    err = dev_nvm_read_block(DEV_NVM_BLOCK_FINGERPRINT, read_buffer, 32);
    DBG_OUT_I("Read test: %s", (err == DEV_OK && memcmp(test_data, read_buffer, 32) == 0) ? "PASS" : "FAIL");
    
    // Statistics
    dev_fls_statistics_t stats = dev_fls_get_statistics();
    DBG_OUT_I("Fls writes: %u, reads: %u", stats.total_writes, stats.total_reads);
}
```

---

## 📚 API Reference

### NvM API

```c
// Initialization
dev_err_t dev_nvm_init(void);

// Block operations
dev_err_t dev_nvm_write_block(uint16_t block_id, const uint8_t *data, uint16_t length);
dev_err_t dev_nvm_read_block(uint16_t block_id, uint8_t *data, uint16_t length);
dev_err_t dev_nvm_restore_block(uint16_t block_id);
dev_err_t dev_nvm_invalidate_block(uint16_t block_id);

// Status & statistics
dev_nvm_block_state_t dev_nvm_get_block_state(uint16_t block_id);
dev_nvm_statistics_t dev_nvm_get_statistics(void);
```

### MemIf API

```c
// Initialization
dev_err_t dev_memif_init(void);

// Memory operations
dev_err_t dev_memif_read(uint32_t address, uint8_t *data, uint16_t length);
dev_err_t dev_memif_write(uint32_t address, const uint8_t *data, uint16_t length, uint32_t *out_address);
dev_err_t dev_memif_erase(uint32_t address, uint16_t length);

// Status
dev_memif_status_t dev_memif_get_status(void);
dev_memif_job_result_t dev_memif_get_job_result(void);
```

### Fee API

```c
// Initialization
dev_err_t dev_fee_init(void);

// Memory operations
dev_err_t dev_fee_read(uint32_t address, uint8_t *data, uint16_t length);
dev_err_t dev_fee_write(const uint8_t *data, uint16_t length, uint32_t *out_address);
dev_err_t dev_fee_erase_all(void);

// Statistics
dev_fee_statistics_t dev_fee_get_statistics(void);
```

### Fls API

```c
// Initialization
dev_err_t dev_fls_init(void);

// Memory operations
dev_err_t dev_fls_read(uint32_t address, uint8_t *data, uint16_t length);
dev_err_t dev_fls_write(uint32_t address, const uint8_t *data, uint16_t length);
dev_err_t dev_fls_erase_sector(uint32_t sector_address);
dev_err_t dev_fls_erase_all(void);
dev_err_t dev_fls_blank_check(uint32_t address, uint16_t length);

// Statistics
dev_fls_statistics_t dev_fls_get_statistics(void);
```

---

## 📝 Examples

### Example 1: Write & Read VIN

```c
#include "dev_nvm.h"

void example_vin_management(void) {
    // Initialize memory stack
    dev_nvm_init();
    
    // Write VIN (17 characters)
    const char* vin = "WVWZZZ1KZXW123456";
    dev_err_t err = dev_nvm_write_block(DEV_NVM_BLOCK_VIN, (uint8_t*)vin, 17);
    
    if (err == DEV_OK) {
        DBG_OUT_I("VIN written successfully");
    }
    
    // Read VIN (fast - from RAM)
    char vin_buffer[18] = {0};  // +1 for null terminator
    err = dev_nvm_read_block(DEV_NVM_BLOCK_VIN, (uint8_t*)vin_buffer, 17);
    
    if (err == DEV_OK) {
        DBG_OUT_I("VIN: %s", vin_buffer);
    }
}
```

### Example 2: Redundant Block with Validation

```c
void example_ecu_serial_with_validation(void) {
    dev_nvm_init();
    
    // Write ECU serial (4 bytes, REDUNDANT type)
    uint32_t ecu_serial = 0x12345678;
    dev_err_t err = dev_nvm_write_block(
        DEV_NVM_BLOCK_ECU_SERIAL,
        (uint8_t*)&ecu_serial,
        4
    );
    
    if (err == DEV_OK) {
        // Verify by reading back
        uint32_t verify_serial = 0;
        err = dev_nvm_read_block(
            DEV_NVM_BLOCK_ECU_SERIAL,
            (uint8_t*)&verify_serial,
            4
        );
        
        if (verify_serial == ecu_serial) {
            DBG_OUT_I("ECU serial verified: 0x%08X", verify_serial);
        } else {
            DBG_OUT_E("Verification failed!");
        }
    }
}
```

### Example 3: Check Wear Leveling

```c
void example_monitor_wear_leveling(void) {
    dev_nvm_init();
    
    // Write lots of data to trigger sector switch
    uint8_t dummy_data[1024];
    memset(dummy_data, 0xAB, 1024);
    
    for (int i = 0; i < 130; i++) {  // 130KB of writes
        dev_nvm_write_block(DEV_NVM_BLOCK_FINGERPRINT, dummy_data, 32);
        
        // Check sector every 10 writes
        if (i % 10 == 0) {
            dev_fee_statistics_t stats = dev_fee_get_statistics();
            DBG_OUT_I("Iteration %d: Sector 0x%08X, Usage %u bytes, Switches %u",
                i,
                stats.active_sector_address,
                stats.active_sector_usage,
                stats.sector_switches
            );
        }
    }
}
```

### Example 4: Power-Loss Recovery Test

```c
void example_power_loss_recovery(void) {
    // Simulate power-on
    DBG_OUT_I("=== Simulating power-on ===");
    
    // Initialize (auto-restores all blocks)
    dev_nvm_init();
    
    // Check each block state
    for (uint16_t block_id = 0x0001; block_id <= 0x0006; block_id++) {
        dev_nvm_block_state_t state = dev_nvm_get_block_state(block_id);
        
        switch (state) {
            case DEV_NVM_BLOCK_VALID:
                DBG_OUT_I("Block 0x%04X: VALID (restored from flash)", block_id);
                break;
            case DEV_NVM_BLOCK_INVALID:
                DBG_OUT_W("Block 0x%04X: INVALID (using ROM defaults)", block_id);
                break;
            default:
                DBG_OUT_E("Block 0x%04X: Unknown state", block_id);
                break;
        }
    }
}
```

---

## 🐛 Troubleshooting

### Issue: "NVM write failed with DEV_ERR_BUSY"

**Cause:** Previous write operation still pending (should not happen with current sync implementation)

**Solution:**
```c
// Check MemIf status before write
dev_memif_status_t status = dev_memif_get_status();
if (status == DEV_MEMIF_BUSY) {
    DBG_OUT_W("MemIf busy, waiting...");
    // Wait or retry
}
```

### Issue: "Block not found after init"

**Cause:** Block never written, or flash erased

**Solution:** This is normal for first-time use. NvM automatically loads ROM defaults.

```c
dev_nvm_block_state_t state = dev_nvm_get_block_state(DEV_NVM_BLOCK_VIN);
if (state == DEV_NVM_BLOCK_INVALID) {
    DBG_OUT_I("Block using ROM defaults (never written)");
    // Write block to persist data
    dev_nvm_write_block(DEV_NVM_BLOCK_VIN, my_vin, 17);
}
```

### Issue: "CRC errors on read"

**Cause:** Flash corruption, power loss during write, or hardware failure

**Solution:**
```c
dev_nvm_statistics_t stats = dev_nvm_get_statistics();
if (stats.crc_errors > 0) {
    DBG_OUT_E("CRC errors detected: %u", stats.crc_errors);
    
    // For REDUNDANT blocks: Secondary copy may be valid
    dev_nvm_restore_block(block_id);  // Will try secondary copy
    
    // If still failing: Invalidate and rewrite
    dev_nvm_invalidate_block(block_id);
    dev_nvm_write_block(block_id, fresh_data, length);
}
```

### Issue: "Sector switch not happening"

**Cause:** Not enough writes to fill 127KB threshold

**Solution:** Check Fee statistics:
```c
dev_fee_statistics_t fee_stats = dev_fee_get_statistics();
DBG_OUT_I("Sector usage: %u / %u bytes",
    fee_stats.active_sector_usage,
    DEV_FEE_SECTOR_SIZE
);

if (fee_stats.active_sector_usage > 127 * 1024) {
    DBG_OUT_I("Sector should switch on next write");
}
```

### Issue: "Flash write alignment error"

**Cause:** STM32H7 requires 32-byte aligned writes

**Solution:** This is handled automatically by Fls layer. If you see this error:
1. Check `DEV_FLS_WRITE_ALIGNMENT` in config
2. Verify HAL is using `FLASH_TYPEPROGRAM_FLASHWORD`
3. Ensure `fls_hal_write()` pads data correctly

### Issue: "Out of memory in NVM sector"

**Cause:** Too many writes, sector full (>127KB used)

**Solution:**
```c
// Check available space
dev_fee_statistics_t stats = dev_fee_get_statistics();
uint32_t available = DEV_FEE_SECTOR_SIZE - stats.active_sector_usage;

if (available < 1024) {
    DBG_OUT_W("Low space: %u bytes remaining", available);
    
    // Option 1: Trigger manual sector switch
    // (Automatic switch happens on next write)
    
    // Option 2: Erase old data (DANGEROUS - loses all data!)
    // dev_fee_erase_all();  // Only if you're sure!
}
```

---

## 📖 Additional Resources

- **Code Flow Documentation:** [NVM_CODE_FLOW.md](../NVM_CODE_FLOW.md) - Detailed write/read/erase flows
- **Architecture Documentation:** [NVM_ARCHITECTURE.md](../NVM_ARCHITECTURE.md) - System design & verification
- **AUTOSAR DCM Specification:** AUTOSAR Diagnostic Communication Manager
- **STM32H7 Reference Manual:** Flash memory programming details

---

## 🎯 Quick Reference

| Task | Function | File |
|------|----------|------|
| Add new block | Edit `nvm_block_config[]` | `dev_nvm_config.h` |
| Change flash sectors | Update sector addresses | `dev_fls_config.h`, `dev_fee_config.h` |
| Port to new MCU | Modify `fls_hal_*()` | `dev_fls.c` |
| Write data | `dev_nvm_write_block()` | Application code |
| Read data | `dev_nvm_read_block()` | Application code |
| Check statistics | `dev_nvm_get_statistics()` | Application code |
| Initialize stack | `dev_nvm_init()` | `main.c` |

---

<div align="center">

**Memory Stack v1.0 - AUTOSAR-Inspired NVM Solution**

Made with ❤️ for reliable data persistence

</div>
