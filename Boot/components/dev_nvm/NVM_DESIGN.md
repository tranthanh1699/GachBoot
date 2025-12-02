# NVM Driver Design Document

## Architecture Overview

NVM (Non-Volatile Memory) driver quản lý persistent storage với circular buffer và wear leveling, dựa trên AUTOSAR NvM module.

## Data Flow

### Boot/Initialization Flow
```
Power On
    │
    ├──> dev_nvm_init()
    │        │
    │        ├──> For each block:
    │        │        │
    │        │        ├──> find_latest_block_in_sector()
    │        │        │        │
    │        │        │        ├──> Scan toàn bộ sector
    │        │        │        ├──> Tìm block_id khớp
    │        │        │        ├──> So sánh write_counter
    │        │        │        └──> Return address của block mới nhất
    │        │        │
    │        │        ├──> Block found?
    │        │        │     YES │          NO
    │        │        │         │           │
    │        │        │    read_block_    Load ROM defaults
    │        │        │    from_flash()    (rom_address)
    │        │        │         │           │
    │        │        │    Load to RAM     Copy to RAM
    │        │        │         │           │
    │        │        │         └───────────┴──> RAM mirror ready
    │        │        │                           │
    │        │        └─────────────────── Write defaults to flash
    │        │                              (if not found)
    │        └──> NVM Ready
    │
    └──> Application uses RAM mirrors
```

### Read Operation Flow
```
dev_nvm_read_block(block_id, data, length)
    │
    ├──> Find block config by block_id
    │
    ├──> Copy from RAM mirror (FAST - no flash access)
    │
    └──> Return data
```

### Write Operation Flow
```
dev_nvm_write_block(block_id, data, length)
    │
    ├──> Find block config + runtime index
    │
    ├──> Update RAM mirror
    │
    ├──> Increment write_counter
    │
    ├──> get_next_write_address()
    │        │
    │        ├──> current_address + block_size
    │        │
    │        ├──> Check if exceeds sector end
    │        │     YES │          NO
    │        │         │           │
    │        │    Erase sector   Use next address
    │        │         │           │
    │        │    Return base    Return next addr
    │        │         │           │
    │        └─────────┴───────────┘
    │
    ├──> write_block_to_flash()
    │        │
    │        ├──> Prepare header (block_id, length, WC, CRC32)
    │        │
    │        ├──> NATIVE type?
    │        │     YES │          NO (REDUNDANT)
    │        │         │           │
    │        │    Write header   Write primary copy
    │        │    Write data         (header + data)
    │        │         │           │
    │        │         │       Write secondary copy
    │        │         │           (header + data)
    │        │         │           │
    │        └─────────┴───────────┘
    │
    ├──> Update current_flash_address
    │
    └──> Return status
```

## Block Lookup Mechanism

### 1. Configuration Lookup (by block_id)
```c
find_block_config(0x0001)  // VIN
    │
    ├──> Iterate dev_nvm_block_config_table[]
    │
    ├──> Match block_id == 0x0001?
    │
    └──> Return &config
              │
              ├──> rom_address = default_vin (const data)
              ├──> ram_address = nvm_ram_vin
              ├──> flash_sector = 7
              ├──> block_size = 17
              └──> block_type = REDUNDANT
```

### 2. Flash Lookup (find latest valid copy)
```c
find_latest_block_in_sector(config)
    │
    ├──> sector_base = 0x081E0000
    ├──> sector_end = 0x08200000
    │
    ├──> For addr = sector_base to sector_end:
    │        │
    │        ├──> Read header at addr
    │        │
    │        ├──> Valid? (block_id match, valid_flag=0xFF)
    │        │     YES │
    │        │         │
    │        │    Compare write_counter
    │        │         │
    │        │    If higher → Update best_address
    │        │         │
    │        └─────────┘
    │
    └──> Return best_address, max_write_counter
```

## Memory Layout Example

### Configuration Table (ROM - Read Only)
```c
// In dev_nvm_config.c
static const uint8_t default_vin[17] = "WVWZZZ1KZXW123456";
static const uint8_t default_ecu_serial[4] = {0x00, 0x00, 0x00, 0x01};

const dev_nvm_block_config_t dev_nvm_block_config_table[] = {
    {
        .block_id = 0x0001,          // VIN
        .block_size = 17,
        .rom_address = default_vin,  // ← Pointer to const default
        .ram_address = nvm_ram_vin,  // ← Pointer to RAM mirror
        .flash_sector = 7,           // ← Dynamic circular storage
        .block_type = REDUNDANT
    },
    // ...
};
```

### Runtime State (RAM - Read/Write)
```c
// In dev_nvm.c
static dev_nvm_block_runtime_t block_runtime[6] = {
    [0] = {  // VIN
        .state = VALID,
        .current_flash_address = 0x081E0090,  // Last write position
        .last_write_counter = 3,              // Number of writes
        .ram_changed = false
    },
    [1] = {  // ECU_SERIAL
        .state = VALID,
        .current_flash_address = 0x081E1020,
        .last_write_counter = 2,
        .ram_changed = false
    },
    // ...
};
```

### RAM Mirrors (Fast Access)
```c
// In dev_nvm_config.c
uint8_t nvm_ram_vin[17] = {0};           // Working copy
uint8_t nvm_ram_ecu_serial[4] = {0};     // Working copy
// ...
```

### Flash Sector 7 (Persistent Storage)
```
Address      | Block ID | WC | Data
-------------|----------|----|-----------------
0x081E0000   | 0x0001   | 1  | VIN data (old)
0x081E0048   | 0x0001   | 2  | VIN data (old)
0x081E0090   | 0x0001   | 3  | VIN data ← LATEST
0x081E00D8   | [empty]  |    |
...
0x081E1000   | 0x0002   | 1  | Serial (old)
0x081E1020   | 0x0002   | 2  | Serial ← LATEST
...
0x081FFFFC   | [end]    |    |
```

## Circular Buffer Mechanism

### Write Sequence
```
Write #1: 0x081E0000 ─┐
Write #2: 0x081E0048  │ Growing sequence
Write #3: 0x081E0090  │
Write #4: 0x081E00D8 ─┘
...
Write #N: 0x081FFFF0 ← Sector almost full
                 │
                 ├─> Next write would exceed sector
                 │
                 ├─> flash_erase_sector(7)
                 │
                 └─> Next write: 0x081E0000 (wrap around)
```

### Wear Leveling Benefits
- Không ghi vào cùng 1 address → tránh flash wear-out
- Write counter tăng dần → dễ track số lần ghi
- Sector đầy → auto erase → circular write

## Redundant Block Storage

### NATIVE Type (Single Copy)
```
0x081E0000: ┌──────────────┐
            │ Header       │ 16 bytes
            ├──────────────┤
            │ Data         │ N bytes
            └──────────────┘
Next: 0x081E0000 + 16 + N
```

### REDUNDANT Type (Dual Copy)
```
0x081E0000: ┌──────────────┐
            │ Primary      │
            │  - Header    │ 16 bytes
            │  - Data      │ N bytes
            ├──────────────┤
            │ Secondary    │
            │  - Header    │ 16 bytes
            │  - Data      │ N bytes
            └──────────────┘
Next: 0x081E0000 + 2*(16+N)
```

### Read from Redundant Block
```
read_block_from_flash(REDUNDANT)
    │
    ├──> Read primary header + data
    ├──> Validate CRC32 → primary_valid?
    │
    ├──> Read secondary header + data
    ├──> Validate CRC32 → secondary_valid?
    │
    ├──> Both valid?
    │     YES │                    NO
    │         │                     │
    │    Use newer one         One valid?
    │    (higher WC)                │
    │         │                YES │        NO
    │         │                    │         │
    │         │              Use valid   Return ERROR
    │         │                copy      (CRC_ERROR)
    │         │                    │         │
    └─────────┴────────────────────┴─────────┘
```

## API Usage Example

### Initialization
```c
// At boot
dev_nvm_init();
// → Scans flash, loads all blocks to RAM
// → Missing blocks get ROM defaults
```

### Read (Fast - From RAM)
```c
uint8_t vin[17];
dev_nvm_read_block(DEV_NVM_BLOCK_VIN, vin, 17);
// → Instant copy from nvm_ram_vin[]
```

### Write (Updates RAM + Flash)
```c
uint8_t new_vin[17] = "WVWZZZ1KZXW999999";
dev_nvm_write_block(DEV_NVM_BLOCK_VIN, new_vin, 17);
// → Updates nvm_ram_vin[]
// → Writes to next circular position in flash
// → Increments write_counter
```

### Restore (Reload from Flash)
```c
dev_nvm_restore_block(DEV_NVM_BLOCK_VIN);
// → Discards RAM changes
// → Reloads latest valid copy from flash
// → If flash invalid, loads ROM defaults
```

## Key Design Decisions

### 1. ROM vs Flash vs RAM
- **ROM** (`rom_address`): Const default data, never changes
- **Flash** (`flash_sector`): Persistent circular storage, survives power loss
- **RAM** (`ram_address`): Fast working copy, cleared on reset

### 2. Write Counter Purpose
- **Find latest**: Highest WC = newest data
- **Wear tracking**: Monitor flash endurance
- **Redundancy**: Compare primary/secondary WC

### 3. Block Identification
- **block_id**: Unique identifier (0x0001 = VIN, 0x0002 = Serial)
- **Config table**: Maps block_id → addresses, size, type
- **Runtime table**: Tracks current flash position, WC

### 4. Circular Buffer Benefits
- **No fixed addresses**: Dynamic allocation in sector
- **Wear leveling**: Distributes writes across sector
- **Simple erase**: One sector erase clears all old copies

## Performance Characteristics

### Read Performance
- **RAM read**: ~1 cycle (instant)
- **Flash read**: ~10-20 cycles (rare, only at init)

### Write Performance
- **Flash write**: ~100-500 cycles per byte
- **Flash erase**: ~5-10ms per sector (only when full)

### Endurance
- **STM32H7 Flash**: ~100,000 erase cycles
- **Sector size**: 128KB
- **Block size**: ~50 bytes average
- **Writes per erase**: ~2500
- **Total writes**: 100K × 2500 = 250M writes
- **Lifetime**: 250M writes / 1 write per day = 685,000 days = 1,876 years

## Error Handling

### CRC Mismatch (Redundant Block)
```
Primary invalid → Use secondary
Secondary invalid → Use primary
Both invalid → Load ROM defaults
```

### Flash Full
```
Sector full → Erase sector → Start from base
```

### Write Protection
```
Write attempt → Check config.write_protection
Protected → Return PERMISSION_DENIED
```

## Future Enhancements

1. **Multi-sector support**: Use multiple sectors for different blocks
2. **Background writes**: Queue writes, execute in main_function()
3. **Defragmentation**: Compact sector when fragmented
4. **Statistics**: Track sector usage, erase counts per block
5. **HAL integration**: Implement flash_write() / flash_erase_sector() with STM32 HAL

---

**Summary**: NVM driver là một AUTOSAR-compliant circular buffer storage system với ROM defaults, RAM mirrors, và flash persistence, designed cho embedded systems cần reliable non-volatile storage với wear leveling.
