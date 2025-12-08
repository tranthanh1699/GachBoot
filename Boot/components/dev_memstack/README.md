# Memory Stack - AUTOSAR Compliant NVM Storage

## Overview

3-layer AUTOSAR-compliant non-volatile memory stack with modular, code-generation-friendly configuration:

```
┌────────────────────────────────────────────┐
│  NvM (NV Manager)                          │  Block management, CRC, redundancy
├────────────────────────────────────────────┤
│  Fee (Flash EEPROM Emulation)              │  Virtual addressing, wear leveling
├────────────────────────────────────────────┤
│  Fls (Flash Driver)                        │  Hardware abstraction (STM32H7)
└────────────────────────────────────────────┘
```

## Key Features

✅ **Modular Configuration**: Config files separated from implementation  
✅ **Code Generation Ready**: `*_Cfg.h/c` files can be auto-generated  
✅ **Runtime Injection**: Configuration passed at initialization  
✅ **Multiple Configs**: Support test/production/simulation configs  
✅ **AUTOSAR Compliant**: Proper layer separation and interfaces  

---

## Quick Start

### Basic Usage

```c
#include "dev_fee.h"
#include "Fee_Cfg.h"

int main(void) {
    // Initialize hardware
    HAL_Init();
    SystemClock_Config();
    
    // Initialize memory stack (initializes Fee + Fls automatically)
    dev_err_t err = dev_fee_init(&Fee_Config);  // Or NULL for default
    if (err != DEV_OK) {
        return -1;
    }
    
    // Write data (auto-allocates, returns physical address)
    uint8_t data[] = "Hello, Flash!";
    uint32_t phys_addr;
    err = dev_fee_write(0, data, sizeof(data), &phys_addr);
    
    // Read data (using physical address)
    uint8_t buffer[sizeof(data)];
    err = dev_fee_read(phys_addr, buffer, sizeof(buffer));
    
    // Continue with application...
}
```

### Using NULL for Default Config

```c
// Pass NULL to use default generated config
dev_fee_init(NULL);  // Same as dev_fee_init(&Fee_Config)
```

---

## Architecture

### File Structure

```
dev_memstack/
├── dev_fls/                    # Flash Driver (Hardware Layer)
│   ├── Fls_Cfg.h              # ⚙️ GENERATED - Flash sector descriptors
│   ├── Fls_Cfg.c              # ⚙️ GENERATED - Sector table, config instance
│   ├── include/
│   │   └── dev_fls.h          # ✍️ MANUAL - Fls API interface
│   └── dev_fls.c              # ✍️ MANUAL - Fls implementation
│
├── dev_fee/                    # Flash EEPROM Emulation
│   ├── Fee_Cfg.h              # ⚙️ GENERATED - Virtual space, sector mapping
│   ├── Fee_Cfg.c              # ⚙️ GENERATED - Fee config instance
│   ├── include/
│   │   └── dev_fee.h          # ✍️ MANUAL - Fee API interface
│   └── dev_fee.c              # ✍️ MANUAL - Fee implementation
│
└── dev_nvm/                    # NV Manager (Block Management)
    ├── dev_nvm.h              # ✍️ MANUAL - NvM API
    └── dev_nvm.c              # ✍️ MANUAL - NvM implementation
```

### Configuration Files (Generated)

**Code generation tools produce these files - NEVER edit manually:**

#### `Fls_Cfg.h/c` - Flash Driver Configuration

Defines physical flash sectors:

```c
// Hardware parameters
#define FLS_CFG_WRITE_ALIGNMENT     32U      // STM32H7: 256-bit
#define FLS_CFG_ERASE_VALUE         0xFFU    // NOR flash

// Sector descriptor
typedef struct {
    uint32_t base_address;      // Physical address (e.g., 0x081C0000)
    uint32_t size;              // Sector size (e.g., 128KB)
    uint8_t  bank_index;        // Flash bank (1 or 2)
    uint8_t  sector_index;      // Hardware sector number (0-7)
    uint8_t  erase_value;       // 0xFF
    const char *name;           // "NVM_Sector_A"
} Fls_SectorDescriptor_t;

// Configuration structure
typedef struct {
    const Fls_SectorDescriptor_t *sector_table;
    uint8_t sector_count;
    uint32_t write_alignment;
    // ... other params
} Fls_ConfigType;

// Global config instance (generated)
extern const Fls_ConfigType Fls_Config;
```

**Example Configuration:**

```c
const Fls_SectorDescriptor_t Fls_SectorTable[] = {
    {
        .base_address = 0x081C0000,
        .size = 128 * 1024,
        .bank_index = 2,
        .sector_index = 6,
        .erase_value = 0xFF,
        .name = "NVM_Sector_A"
    },
    {
        .base_address = 0x081E0000,
        .size = 128 * 1024,
        .bank_index = 2,
        .sector_index = 7,
        .erase_value = 0xFF,
        .name = "NVM_Sector_B"
    }
};

const Fls_ConfigType Fls_Config = {
    .sector_table = Fls_SectorTable,
    .sector_count = 2,
    .write_alignment = 32,
    .erase_value = 0xFF,
    .write_timeout_ms = 100,
    .erase_timeout_ms = 2000
};
```

#### `Fee_Cfg.h/c` - Fee Configuration

Defines virtual address space and sector mapping:

```c
// Virtual address space
#define FEE_CFG_VIRTUAL_START           0x00000000U
#define FEE_CFG_VIRTUAL_SIZE            (128 * 1024)
#define FEE_CFG_SECTOR_FULL_THRESHOLD   (127 * 1024)

// Fee sector mapping
typedef struct {
    uint8_t fls_sector_index;   // Index in Fls_SectorTable[]
    bool is_primary;            // Primary sector flag
    const char *name;           // "Fee_Primary"
} Fee_SectorConfig_t;

// Configuration structure
typedef struct {
    const Fee_SectorConfig_t *sector_table;
    uint8_t sector_count;
    uint32_t virtual_start;
    uint32_t virtual_size;
    uint32_t sector_full_threshold;
    const Fls_ConfigType *fls_config;  // Reference to Fls config
} Fee_ConfigType;

extern const Fee_ConfigType Fee_Config;
```

**Example Configuration:**

```c
const Fee_SectorConfig_t Fee_SectorTable[] = {
    { .fls_sector_index = 0, .is_primary = true,  .name = "Fee_Primary" },
    { .fls_sector_index = 1, .is_primary = false, .name = "Fee_Secondary" }
};

const Fee_ConfigType Fee_Config = {
    .sector_table = Fee_SectorTable,
    .sector_count = 2,
    .virtual_start = 0x00000000,
    .virtual_size = 128 * 1024,
    .sector_full_threshold = 127 * 1024,
    .write_alignment = 32,
    .fls_config = &Fls_Config  // Link to Fls config
};
```

### Implementation Files (Manual)

**Hand-written driver logic - maintains stable API:**

#### `dev_fls.h/c` - Flash Driver

Key API with config injection:

```c
// Initialize with config (NULL = use default)
dev_err_t dev_fls_init(const Fls_ConfigType *config);

// Get active config
const Fls_ConfigType* dev_fls_get_config(void);

// Hardware operations
dev_err_t dev_fls_read(uint32_t address, uint8_t *buffer, uint32_t size);
dev_err_t dev_fls_write(uint32_t address, const uint8_t *data, uint32_t size);
dev_err_t dev_fls_erase_sector_by_index(uint8_t sector_index);
```

**Design Principles:**
- ✅ No extern config dependencies - Config injected at init
- ✅ Config copied internally - No external pointers after init
- ✅ Multiple configs supported - Pass different config for testing

#### `dev_fee.h/c` - Fee Implementation

Key API with config injection:

```c
// Initialize with config (NULL = use default, initializes Fls automatically)
dev_err_t dev_fee_init(const Fee_ConfigType *config);

// Get active config
const Fee_ConfigType* dev_fee_get_config(void);

// Virtual address operations
dev_err_t dev_fee_write(uint32_t virt_addr, const uint8_t *data, uint32_t size, uint32_t *phys_addr_out);
dev_err_t dev_fee_read(uint32_t phys_addr, uint8_t *buffer, uint32_t size);
```

**Design Principles:**
- ✅ Fls config passed through Fee config - Single injection point
- ✅ Fee initializes Fls automatically - Ensures correct config used
- ✅ No direct Fls config access - Fee only sees its own config

---

## Layer Responsibilities

### Fls (Flash Driver)
- Physical flash operations (read/write/erase)
- Sector descriptor management
- Hardware alignment enforcement (32-byte for STM32H7)
- **Does NOT**: Manage logical addressing, wear leveling, sector state

### Fee (Flash EEPROM Emulation)
- Virtual address space (0x00000000 - 0x0001FFFF)
- Wear leveling via sector ping-pong
- Auto-allocation of virtual addresses
- Sector lifecycle management
- **Does NOT**: Know about NvM blocks, CRC, redundancy

### NvM (NV Manager)
- Block-based storage API
- CRC validation
- Redundant block support
- Default value management
- **Does NOT**: Know about flash hardware, sectors

---

## Configuration Injection Flow

```
┌─────────────────┐
│ Code Generator  │ (STM32CubeMX, custom script, etc.)
└────────┬────────┘
         │ Generates
         ▼
┌─────────────────┐
│   Fls_Cfg.h/c   │ Flash sectors: 0x081C0000, 0x081E0000, ...
│   Fee_Cfg.h/c   │ Virtual space: 0x0 - 0x1FFFF, sector mapping
└────────┬────────┘
         │ Compiled into firmware
         ▼
┌─────────────────┐
│   main.c        │
│                 │   dev_fee_init(&Fee_Config);  // Uses generated config
│                 │   // Or: dev_fee_init(NULL);  // NULL = default
└─────────────────┘
         │ Runtime injection
         ▼
┌─────────────────┐
│   dev_fee.c     │ Copies Fee_Config internally
│                 │ Initializes Fls: dev_fls_init(fee_config.fls_config)
└────────┬────────┘
         │ Injects Fls config
         ▼
┌─────────────────┐
│   dev_fls.c     │ Copies Fls_Config internally
│                 │ All operations use internal config copy
└─────────────────┘
```

---

## Benefits of Modular Architecture

### 1. Code Generation Friendly

Config files (`*_Cfg.h/c`) can be **completely regenerated** without affecting manual code:

```bash
# Regenerate configs (overwrites Cfg files only)
$ config_tool --mcu STM32H743 --output Fls_Cfg.c Fee_Cfg.c

# Manual code (dev_*.c) unchanged - no merge conflicts!
```

### 2. Testing with Multiple Configurations

```c
// Production config (generated)
extern const Fls_ConfigType Fls_Config;

// Test config (hand-written for unit tests)
const Fls_ConfigType Test_Fls_Config = {
    .sector_table = Test_Sectors,  // Simulated sectors
    .sector_count = 2,
    .write_alignment = 32,
    // ...
};

// In test code:
dev_fls_init(&Test_Fls_Config);  // Use test config
```

### 3. No Build-Time Dependencies

```c
// ❌ OLD (compile-time dependency)
extern const Fls_SectorDescriptor_t fls_sectors[];  // Hardcoded

// ✅ NEW (runtime injection)
dev_fls_init(&Fls_Config);  // Data passed at runtime
```

### 4. Layer Decoupling

Each layer is **independent**:
- **Fls**: Knows nothing about Fee - pure hardware driver
- **Fee**: Depends on Fls interface, not Fls config
- **NvM**: Depends on Fee interface, not Fee config

---

## Hardware Configuration

**STM32H743VIT6**:
- Flash: 2MB (0x08000000 - 0x081FFFFF)
- NVM Storage: Bank 2, Sectors 6-7 (256KB total)
- Write Alignment: 32 bytes (256-bit flash word)
- Erase Granularity: 128KB sector

**Flash Memory Map:**

```
Bank 1 (1MB):                      Bank 2 (1MB):
0x08000000 - Bootloader           0x08100000 - Application
   ...                               ...
                                  0x081C0000 - NVM Sector A (128KB) ← Fee Primary
                                  0x081E0000 - NVM Sector B (128KB) ← Fee Secondary
```

---

## Code Generator Integration

### What Your Tool Must Generate

#### 1. `Fls_Cfg.c` Template

```c
#include "Fls_Cfg.h"

const Fls_SectorDescriptor_t Fls_SectorTable[] = {
    {
        .base_address = /* Physical address */,
        .size = /* Sector size in bytes */,
        .bank_index = /* Flash bank (1 or 2) */,
        .sector_index = /* HW sector index (0-7) */,
        .erase_value = 0xFFU,
        .name = /* Sector name */
    },
    // Repeat for each sector...
};

const Fls_ConfigType Fls_Config = {
    .sector_table = Fls_SectorTable,
    .sector_count = sizeof(Fls_SectorTable) / sizeof(Fls_SectorDescriptor_t),
    .write_alignment = 32U,  // STM32H7: 32 bytes
    .read_alignment = 1U,
    .erase_value = 0xFFU,
    .write_timeout_ms = 100U,
    .erase_timeout_ms = 2000U
};
```

#### 2. `Fee_Cfg.c` Template

```c
#include "Fee_Cfg.h"
#include "Fls_Cfg.h"

const Fee_SectorConfig_t Fee_SectorTable[] = {
    {
        .fls_sector_index = 0U,  // Index in Fls_SectorTable[]
        .is_primary = true,
        .name = "Fee_Primary"
    },
    {
        .fls_sector_index = 1U,
        .is_primary = false,
        .name = "Fee_Secondary"
    }
};

const Fee_ConfigType Fee_Config = {
    .sector_table = Fee_SectorTable,
    .sector_count = sizeof(Fee_SectorTable) / sizeof(Fee_SectorConfig_t),
    .virtual_start = 0x00000000U,
    .virtual_size = 128U * 1024U,
    .sector_full_threshold = 127U * 1024U,
    .write_alignment = 32U,
    .fls_config = &Fls_Config  // IMPORTANT: Link to Fls config
};
```

### Python Generator Example

```python
def generate_fls_config(mcu, sectors):
    """Generate Fls_Cfg.c"""
    params = get_mcu_params(mcu)
    
    sector_entries = []
    for s in sectors:
        entry = f"""    {{
        .base_address = {s['address']:#010x}U,
        .size = {s['size']}U,
        .bank_index = {s['bank']}U,
        .sector_index = {s['hw_index']}U,
        .erase_value = 0xFFU,
        .name = "{s['name']}"
    }}"""
        sector_entries.append(entry)
    
    content = f"""#include "Fls_Cfg.h"

const Fls_SectorDescriptor_t Fls_SectorTable[] = {{
{',\n'.join(sector_entries)}
}};

const Fls_ConfigType Fls_Config = {{
    .sector_table = Fls_SectorTable,
    .sector_count = {len(sectors)}U,
    .write_alignment = {params['write_alignment']}U,
    .read_alignment = 1U,
    .erase_value = 0xFFU,
    .write_timeout_ms = {params['write_timeout']}U,
    .erase_timeout_ms = {params['erase_timeout']}U
}};
"""
    return content

# Example usage:
sectors = [
    {'address': 0x081C0000, 'size': 128*1024, 'bank': 2, 'hw_index': 6, 'name': 'NVM_Sector_A'},
    {'address': 0x081E0000, 'size': 128*1024, 'bank': 2, 'hw_index': 7, 'name': 'NVM_Sector_B'}
]

fls_cfg = generate_fls_config('STM32H743VIT6', sectors)
with open('Fls_Cfg.c', 'w') as f:
    f.write(fls_cfg)
```

---

## Testing Guide

### Creating Custom Test Config

```c
// In test_memstack.c

// Define test sectors (smaller for faster tests)
static const Fls_SectorDescriptor_t Test_Fls_Sectors[] = {
    {
        .base_address = 0x08000000,
        .size = 4096,  // 4KB
        .bank_index = 1,
        .sector_index = 0,
        .erase_value = 0xFF,
        .name = "Test_Sector_A"
    },
    {
        .base_address = 0x08001000,
        .size = 4096,
        .bank_index = 1,
        .sector_index = 1,
        .erase_value = 0xFF,
        .name = "Test_Sector_B"
    }
};

static const Fls_ConfigType Test_Fls_Config = {
    .sector_table = Test_Fls_Sectors,
    .sector_count = 2,
    .write_alignment = 4,  // Smaller for testing
    .read_alignment = 1,
    .erase_value = 0xFF,
    .write_timeout_ms = 10,
    .erase_timeout_ms = 100
};

static const Fee_SectorConfig_t Test_Fee_Sectors[] = {
    { .fls_sector_index = 0, .is_primary = true,  .name = "Test_Primary" },
    { .fls_sector_index = 1, .is_primary = false, .name = "Test_Secondary" }
};

static const Fee_ConfigType Test_Fee_Config = {
    .sector_table = Test_Fee_Sectors,
    .sector_count = 2,
    .virtual_start = 0x00000000,
    .virtual_size = 4096,
    .sector_full_threshold = 4000,
    .write_alignment = 4,
    .fls_config = &Test_Fls_Config
};

// Test case
void test_fee_write_read(void) {
    // Initialize with test config
    dev_fee_init(&Test_Fee_Config);
    
    // Test write
    uint8_t write_data[] = "Test Data";
    uint32_t phys_addr;
    dev_err_t err = dev_fee_write(0, write_data, sizeof(write_data), &phys_addr);
    assert(err == DEV_OK);
    
    // Test read
    uint8_t read_data[sizeof(write_data)];
    err = dev_fee_read(phys_addr, read_data, sizeof(read_data));
    assert(err == DEV_OK);
    assert(memcmp(write_data, read_data, sizeof(write_data)) == 0);
}
```

---

## Troubleshooting

### Error: "Sector table is NULL"
**Cause**: Config not properly initialized  
**Fix**: Ensure `Fls_Config.sector_table` points to valid array

### Error: "Invalid write alignment"
**Cause**: Config alignment doesn't match MCU  
**Fix**: For STM32H7, write_alignment **must be 32**

### Error: "Fls config reference is NULL"
**Cause**: `Fee_Config.fls_config` not set  
**Fix**: Link Fee to Fls config: `.fls_config = &Fls_Config`

### Compilation Error: "undefined reference to `Fls_Config`"
**Cause**: `Fls_Cfg.c` not added to build  
**Fix**: Ensure `Fls_Cfg.c` and `Fee_Cfg.c` are in CMakeLists.txt

---

## Migration from Old Architecture

### Old API (Deprecated)
```c
dev_fls_init();  // Hardcoded config
dev_fee_init();  // Hardcoded config
```

### New API
```c
dev_fls_init(&Fls_Config);  // Config injection
dev_fee_init(&Fee_Config);  // Config injection (also initializes Fls)
// Or use NULL for default:
dev_fee_init(NULL);
```

---

## Summary

| Aspect | Old | New |
|--------|-----|-----|
| **Config** | Hardcoded (compile-time) | Injected (runtime) |
| **Testing** | Single config | Multiple configs |
| **Generation** | Manual editing | Tool generated |
| **Coupling** | Tight (extern) | Loose (injection) |
| **AUTOSAR** | Partial | Full compliance |

---

## Status

✅ **Completed**:
- Modular configuration architecture
- Runtime config injection
- Generated config file structure (`Fls_Cfg`, `Fee_Cfg`)
- Complete implementation (Fls, Fee)

⏳ **Remaining**:
- Update NvM to use Fee API (currently uses old MemIf)
- Hardware validation on target
- Code generator tool development

---

**Architecture**: Clean, testable, code-generation-friendly! 🎉
