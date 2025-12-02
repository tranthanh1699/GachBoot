# NVM Module - Code Flow Documentation

## 1. WRITE OPERATION FLOW

### Complete Write Flow (VIN Block Example)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Application Layer                                       │
└─────────────────────────────────────────────────────────────────┘

Application calls:
  dev_nvm_write_block(DEV_NVM_BLOCK_VIN, "WVWZZZ1KZXW123456", 17)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: NvM Layer (dev_nvm.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_nvm_write_block(block_id=0x0001, data="WVWZZZ...", length=17)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: data != NULL? ✓
  ├─> Find config: block_id=0x0001 → VIN block
  ├─> Validate: length == 17? ✓
  ├─> Validate: write_protection == false? ✓
  ├─> Find runtime index: idx=0
  │
  ├─> Update RAM mirror:
  │     memcpy(nvm_ram_vin, "WVWZZZ...", 17)
  │
  ├─> Call write_block_to_nv():
  │     ├─> Calculate CRC32:
  │     │     crc = dev_crc32_calculate("WVWZZZ...", 17)
  │     │     // Result: crc = 0x12345678
  │     │
  │     ├─> Check block type: REDUNDANT
  │     │
  │     ├─> Write PRIMARY copy:
  │     │     dev_memif_write(0, "WVWZZZ...", 17, &primary_addr)
  │     │       │
  │     │       └─> Returns: primary_addr = 0x081C0000
  │     │
  │     ├─> Write PRIMARY CRC:
  │     │     dev_memif_write(0, &crc, 4, &crc_addr)
  │     │       │
  │     │       └─> Returns: crc_addr = 0x081C0020
  │     │
  │     ├─> Write SECONDARY copy:
  │     │     dev_memif_write(0, "WVWZZZ...", 17, &secondary_addr)
  │     │       │
  │     │       └─> Returns: secondary_addr = 0x081C0040
  │     │
  │     └─> Write SECONDARY CRC:
  │           dev_memif_write(0, &crc, 4, &crc_addr)
  │             │
  │             └─> Returns: crc_addr = 0x081C0060
  │
  ├─> Store returned address:
  │     block_runtime[0].nv_address = 0x081C0000 (primary_addr)
  │     block_runtime[0].state = DEV_NVM_BLOCK_VALID
  │     block_runtime[0].ram_changed = false
  │
  ├─> Update statistics:
  │     nvm_stats.total_writes++
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: MemIf Layer (dev_memif.c)                               │
└─────────────────────────────────────────────────────────────────┘

dev_memif_write(address=0, data="WVWZZZ...", length=17, &out_addr)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: data != NULL? ✓
  ├─> Validate: length > 0? ✓
  │
  ├─> Set status: DEV_MEMIF_BUSY
  │
  ├─> Route to Fee:
  │     dev_fee_write("WVWZZZ...", 17, &out_addr)
  │       │
  │       └─> Returns: out_addr = 0x081C0000
  │
  ├─> Update status: DEV_MEMIF_JOB_OK
  ├─> Update job_result: DEV_MEMIF_JOB_OK
  │
  └─> Return: DEV_OK (with out_addr = 0x081C0000)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Fee Layer (dev_fee.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_fee_write(data="WVWZZZ...", length=17, &out_address)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: data != NULL? ✓
  ├─> Validate: out_address != NULL? ✓
  ├─> Validate: length > 0 && <= 128KB? ✓
  │
  ├─> Calculate aligned length:
  │     aligned_length = ((17 + 31) / 32) * 32 = 32 bytes
  │
  ├─> Check sector space:
  │     active_sector = 0x081C0000
  │     write_position = 0x081C0000
  │     sector_end = 0x081E0000
  │     available = 0x20000 bytes (128KB) ✓
  │
  ├─> Get write address:
  │     write_addr = fee_state.write_position = 0x081C0000
  │
  ├─> Call Fls write:
  │     dev_fls_write(0x081C0000, "WVWZZZ...", 17)
  │       │
  │       └─> Returns: DEV_OK
  │
  ├─> Update write position:
  │     fee_state.write_position += 32  // aligned_length
  │     // New position: 0x081C0020
  │
  ├─> Update statistics:
  │     fee_stats.total_writes++
  │     fee_stats.active_sector_usage = 32
  │     fee_stats.write_position = 0x081C0020
  │
  ├─> Return address:
  │     *out_address = 0x081C0000
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Fls Layer (dev_fls.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_fls_write(address=0x081C0000, data="WVWZZZ...", length=17)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: data != NULL? ✓
  ├─> Validate: length > 0? ✓
  ├─> Validate: address in managed range? ✓
  │
  ├─> Check alignment:
  │     0x081C0000 % 32 == 0? ✓
  │
  ├─> Calculate aligned length:
  │     aligned_length = ((17 + 31) / 32) * 32 = 32 bytes
  │
  ├─> Check sector boundary:
  │     sector_base = 0x081C0000
  │     sector_end = 0x081E0000
  │     0x081C0000 + 32 <= 0x081E0000? ✓
  │
  ├─> Create padded buffer:
  │     write_buffer[32]:
  │       [0-16]:  "WVWZZZ1KZXW123456"  // Original data
  │       [17-31]: 0xFF, 0xFF, ...       // Padding (erased state)
  │
  ├─> Call HAL write:
  │     fls_hal_write(0x081C0000, write_buffer, 32)
  │       │
  │       └─> Returns: DEV_OK
  │
  ├─> Update statistics:
  │     fls_stats.total_writes++
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: HAL Layer (STM32H7)                                     │
└─────────────────────────────────────────────────────────────────┘

fls_hal_write(address=0x081C0000, data=write_buffer, length=32)
  │
  ├─> Unlock flash:
  │     HAL_FLASH_Unlock()
  │
  ├─> Calculate words to write:
  │     words = 32 / 32 = 1 flash word (256 bits)
  │
  ├─> Write flash word:
  │     HAL_FLASH_Program(
  │       FLASH_TYPEPROGRAM_FLASHWORD,
  │       0x081C0000,
  │       (uint32_t)&write_buffer[0]  // 8x 32-bit words
  │     )
  │       │
  │       └─> Hardware writes 256-bit word to flash
  │
  ├─> Lock flash:
  │     HAL_FLASH_Lock()
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ RESULT: Flash Memory State                                      │
└─────────────────────────────────────────────────────────────────┘

Address: 0x081C0000-0x081C001F (32 bytes written)
┌───────────────────┬────┬─────────────────┐
│ VIN Data (17)     │ PAD│                 │
│ "WVWZZZ1KZXW12345"│ 0xFF...             │
└───────────────────┴────┴─────────────────┘

Next write position: 0x081C0020
```

---

## 2. READ OPERATION FLOW

### Complete Read Flow (VIN Block Example)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Application Layer                                       │
└─────────────────────────────────────────────────────────────────┘

Application calls:
  uint8_t buffer[17];
  dev_nvm_read_block(DEV_NVM_BLOCK_VIN, buffer, 17)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: NvM Layer (dev_nvm.c) - Fast Path                       │
└─────────────────────────────────────────────────────────────────┘

dev_nvm_read_block(block_id=0x0001, data=buffer, length=17)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: data != NULL? ✓
  ├─> Find config: block_id=0x0001 → VIN block
  ├─> Validate: length == 17? ✓
  │
  ├─> Copy from RAM mirror:
  │     memcpy(buffer, nvm_ram_vin, 17)
  │     // Fast read - no flash access!
  │
  ├─> Update statistics:
  │     nvm_stats.total_reads++
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ RESULT: Data in buffer                                          │
└─────────────────────────────────────────────────────────────────┘

buffer[] = "WVWZZZ1KZXW123456"
```

### Restore From Flash (when RAM mirror invalid)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Application Layer                                       │
└─────────────────────────────────────────────────────────────────┘

Application calls:
  dev_nvm_restore_block(DEV_NVM_BLOCK_VIN)

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: NvM Layer (dev_nvm.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_nvm_restore_block(block_id=0x0001)
  │
  ├─> Validate: initialized? ✓
  ├─> Find config: block_id=0x0001 → VIN block
  ├─> Find runtime: idx=0
  │
  ├─> Get stored NV address:
  │     nv_address = block_runtime[0].nv_address = 0x081C0000
  │
  ├─> Call read_block_from_nv():
  │     │
  │     ├─> Check address valid:
  │     │     nv_address == 0? No → proceed
  │     │
  │     ├─> Check block type: REDUNDANT
  │     │
  │     ├─> Calculate addresses:
  │     │     primary_addr = 0x081C0000
  │     │     secondary_addr = 0x081C0000 + 17 + 4 = 0x081C0015
  │     │
  │     ├─> Read PRIMARY copy:
  │     │     dev_memif_read(0x081C0000, data_primary, 17)
  │     │       │
  │     │       └─> Returns: DEV_OK
  │     │
  │     ├─> Validate PRIMARY CRC:
  │     │     validate_block_crc(0x081C0000, data_primary, 17)
  │     │       ├─> Read stored CRC:
  │     │       │     dev_memif_read(0x081C0011, &stored_crc, 4)
  │     │       │       └─> stored_crc = 0x12345678
  │     │       │
  │     │       ├─> Calculate CRC:
  │     │       │     calc_crc = dev_crc32_calculate(data_primary, 17)
  │     │       │       └─> calc_crc = 0x12345678
  │     │       │
  │     │       └─> Compare: calc_crc == stored_crc? ✓
  │     │             primary_valid = true
  │     │
  │     ├─> Read SECONDARY copy:
  │     │     dev_memif_read(0x081C0015, data_secondary, 17)
  │     │       │
  │     │       └─> Returns: DEV_OK
  │     │
  │     ├─> Validate SECONDARY CRC:
  │     │     validate_block_crc(0x081C0015, data_secondary, 17)
  │     │       └─> secondary_valid = true
  │     │
  │     ├─> Decision logic:
  │     │     Both valid? ✓
  │     │     Compare primary vs secondary:
  │     │       memcmp(data_primary, data_secondary, 17) == 0? ✓
  │     │     
  │     │     → Use primary copy
  │     │
  │     └─> Copy to RAM mirror:
  │           memcpy(nvm_ram_vin, data_primary, 17)
  │
  ├─> Update runtime state:
  │     block_runtime[0].state = DEV_NVM_BLOCK_VALID
  │     block_runtime[0].ram_changed = false
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: MemIf Layer (dev_memif.c)                               │
└─────────────────────────────────────────────────────────────────┘

dev_memif_read(address=0x081C0000, data=buffer, length=17)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: data != NULL? ✓
  ├─> Validate: length > 0? ✓
  │
  ├─> Set status: DEV_MEMIF_BUSY
  │
  ├─> Route to Fee:
  │     dev_fee_read(0x081C0000, buffer, 17)
  │       │
  │       └─> Returns: DEV_OK
  │
  ├─> Update status: DEV_MEMIF_JOB_OK
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Fee Layer (dev_fee.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_fee_read(address=0x081C0000, data=buffer, length=17)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: data != NULL? ✓
  ├─> Validate: length > 0? ✓
  │
  ├─> Route to Fls:
  │     dev_fls_read(0x081C0000, buffer, 17)
  │       │
  │       └─> Returns: DEV_OK
  │
  ├─> Update statistics:
  │     fee_stats.total_reads++
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Fls Layer (dev_fls.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_fls_read(address=0x081C0000, data=buffer, length=17)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: data != NULL? ✓
  ├─> Validate: length > 0? ✓
  ├─> Validate: address in managed range? ✓
  │
  ├─> Direct memory read:
  │     memcpy(buffer, (void*)0x081C0000, 17)
  │     // Flash memory mapped, direct access
  │
  ├─> Update statistics:
  │     fls_stats.total_reads++
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ RESULT: Data restored to RAM                                    │
└─────────────────────────────────────────────────────────────────┘

nvm_ram_vin[] = "WVWZZZ1KZXW123456"
```

---

## 3. SECTOR SWITCH FLOW

### Automatic Sector Switch (when sector full)

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: Sector Full Detection                                  │
└─────────────────────────────────────────────────────────────────┘

During write operation:
  Fee detects: write_position >= (active_sector + 127KB)
  
  OR
  
  Available space < aligned_length needed

┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Fee Layer (dev_fee.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_fee_write() detects sector full:
  │
  ├─> Check space:
  │     active_sector = 0x081C0000 (Sector A)
  │     write_position = 0x081DFFE0 (127KB used)
  │     sector_end = 0x081E0000
  │     available = 32 bytes
  │     needed = 64 bytes → NOT ENOUGH!
  │
  ├─> Log warning:
  │     "Sector 0x081C0000 full (130560 bytes used), switching..."
  │
  ├─> Call sector switch:
  │     fee_switch_sector()
  │       │
  │       ├─> Get current sector:
  │       │     old_sector = 0x081C0000 (Sector A)
  │       │
  │       ├─> Calculate alternate sector:
  │       │     new_sector = dev_fee_get_alternate_sector(0x081C0000)
  │       │       └─> Returns: 0x081E0000 (Sector B)
  │       │
  │       ├─> Log switch:
  │       │     "Switching from 0x081C0000 to 0x081E0000"
  │       │
  │       ├─> Erase new sector via Fls:
  │       │     dev_fls_erase_sector(0x081E0000)
  │       │       │
  │       │       └─> [See ERASE FLOW below]
  │       │
  │       ├─> Update Fee state:
  │       │     fee_state.active_sector = 0x081E0000
  │       │     fee_state.write_position = 0x081E0000
  │       │
  │       ├─> Update statistics:
  │       │     fee_stats.sector_switches++
  │       │     fee_stats.active_sector_address = 0x081E0000
  │       │     fee_stats.active_sector_usage = 0
  │       │     fee_stats.write_position = 0x081E0000
  │       │
  │       ├─> Log completion:
  │       │     "Sector switch complete - New sector: 0x081E0000"
  │       │
  │       └─> Return: DEV_OK
  │
  ├─> Resume write operation:
  │     Write to new sector at 0x081E0000
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ RESULT: Sector Switch Complete                                  │
└─────────────────────────────────────────────────────────────────┘

Old State:
  Sector A (0x081C0000): FULL (127KB used)
  Sector B (0x081E0000): Not erased

New State:
  Sector A (0x081C0000): FULL (old data preserved)
  Sector B (0x081E0000): ERASED + ACTIVE (ready for writes)
  
Write position: 0x081E0000 (start of Sector B)

Note: Old sector data NOT copied (Fee doesn't do data migration)
      NvM tracks addresses, so old data still accessible
```

---

## 4. ERASE OPERATION FLOW

### Complete Erase Flow (Sector Erase)

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Fee Layer (dev_fee.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_fls_erase_sector(sector_address=0x081E0000)
  │
  ├─> Called from:
  │     - fee_switch_sector() → Automatic sector switch
  │     - dev_fee_erase_all() → Manual erase all
  │
  └─> Forward to Fls

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Fls Layer (dev_fls.c)                                   │
└─────────────────────────────────────────────────────────────────┘

dev_fls_erase_sector(sector_address=0x081E0000)
  │
  ├─> Validate: initialized? ✓
  ├─> Validate: address in managed range? ✓
  │
  ├─> Get sector index:
  │     sector_idx = dev_fls_get_sector_index(0x081E0000)
  │       └─> Returns: 7 (Sector B)
  │
  ├─> Validate sector index:
  │     sector_idx == 0xFF? No → Valid
  │
  ├─> Call HAL erase:
  │     fls_hal_erase_sector(sector_idx=7)
  │       │
  │       └─> [See HAL erase below]
  │
  ├─> Update statistics:
  │     fls_stats.total_erases++
  │
  ├─> Log success:
  │     "Sector 0x081E0000 erased"
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: HAL Layer (STM32H7)                                     │
└─────────────────────────────────────────────────────────────────┘

fls_hal_erase_sector(sector_index=7)
  │
  ├─> Unlock flash:
  │     HAL_FLASH_Unlock()
  │
  ├─> Configure erase:
  │     FLASH_EraseInitTypeDef erase_init = {
  │       .TypeErase = FLASH_TYPEERASE_SECTORS,
  │       .Banks = FLASH_BANK_2,
  │       .Sector = 7,                    // Sector B
  │       .NbSectors = 1,
  │       .VoltageRange = FLASH_VOLTAGE_RANGE_3  // 2.7V-3.6V
  │     }
  │
  ├─> Execute erase:
  │     HAL_FLASHEx_Erase(&erase_init, &sector_error)
  │       │
  │       ├─> Hardware erases entire 128KB sector
  │       │   (Takes ~1-2 seconds)
  │       │
  │       └─> Returns: HAL_OK
  │
  ├─> Lock flash:
  │     HAL_FLASH_Lock()
  │
  ├─> Check result:
  │     status == HAL_OK? ✓
  │     sector_error == 0xFFFFFFFF? ✓
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ RESULT: Sector Erased                                           │
└─────────────────────────────────────────────────────────────────┘

Address: 0x081E0000-0x081FFFFF (128KB)
All bytes: 0xFF (erased state)

Ready for new writes at 0x081E0000
```

### Erase All Sectors

```
┌─────────────────────────────────────────────────────────────────┐
│ Application → NvM → MemIf → Fee                                 │
└─────────────────────────────────────────────────────────────────┘

dev_fee_erase_all()
  │
  ├─> Call Fls erase all:
  │     dev_fls_erase_all()
  │       │
  │       ├─> Erase Sector A:
  │       │     dev_fls_erase_sector(0x081C0000)
  │       │       └─> [Erase flow as above]
  │       │
  │       └─> Erase Sector B:
  │             dev_fls_erase_sector(0x081E0000)
  │               └─> [Erase flow as above]
  │
  ├─> Reset Fee state to Sector A:
  │     fee_state.active_sector = 0x081C0000
  │     fee_state.write_position = 0x081C0000
  │
  ├─> Reset statistics:
  │     fee_stats.active_sector_usage = 0
  │     fee_stats.write_position = 0x081C0000
  │
  └─> Return: DEV_OK

┌─────────────────────────────────────────────────────────────────┐
│ RESULT: Both Sectors Erased                                     │
└─────────────────────────────────────────────────────────────────┘

Sector A (0x081C0000): All 0xFF (erased)
Sector B (0x081E0000): All 0xFF (erased)

Active sector: Sector A
Write position: 0x081C0000 (start)

All NvM blocks will reload from ROM defaults on next init
```

---

## 5. INITIALIZATION FLOW

### System Boot Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Application calls dev_nvm_init()                        │
└─────────────────────────────────────────────────────────────────┘

main()
  │
  └─> dev_nvm_init()

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: NvM initializes chain                                   │
└─────────────────────────────────────────────────────────────────┘

dev_nvm_init()
  │
  ├─> Check already initialized? No → proceed
  │
  ├─> Initialize MemIf (which initializes Fee → Fls):
  │     dev_memif_init()
  │       │
  │       ├─> dev_fee_init()
  │       │     │
  │       │     ├─> dev_fls_init()
  │       │     │     │
  │       │     │     ├─> Clear state
  │       │     │     ├─> Mark initialized
  │       │     │     └─> Log: "FLS initialized"
  │       │     │
  │       │     ├─> Scan sectors:
  │       │     │     fee_scan_sectors_and_init()
  │       │     │       │
  │       │     │       ├─> Check Sector A (0x081C0000):
  │       │     │       │     blank_check(0x081C0000, 32)
  │       │     │       │       → Has data (not all 0xFF)
  │       │     │       │
  │       │     │       ├─> Check Sector B (0x081E0000):
  │       │     │       │     blank_check(0x081E0000, 32)
  │       │     │       │       → Empty (all 0xFF)
  │       │     │       │
  │       │     │       ├─> Decision: Use Sector A (has data)
  │       │     │       │     active_sector = 0x081C0000
  │       │     │       │
  │       │     │       ├─> Scan for write position:
  │       │     │       │     scan_addr = 0x081C0000
  │       │     │       │     while (scan_addr < sector_end):
  │       │     │       │       if blank_check(scan_addr, 32):
  │       │     │       │         Found empty at 0x081C0080
  │       │     │       │         break
  │       │     │       │       scan_addr += 32
  │       │     │       │
  │       │     │       ├─> Set write position:
  │       │     │       │     write_position = 0x081C0080
  │       │     │       │
  │       │     │       └─> Log: "Active sector: 0x081C0000, Write position: 0x081C0080"
  │       │     │
  │       │     └─> Log: "Fee initialized - Active sector: 0x081C0000, Usage: 128 bytes"
  │       │
  │       └─> Log: "MemIf initialized"
  │
  ├─> Restore all NvM blocks from flash:
  │     for (i = 0; i < 6; i++):  // 6 blocks configured
  │       │
  │       ├─> Block 0 (VIN):
  │       │     nv_address = block_runtime[0].nv_address = 0
  │       │     read_block_from_nv(..., nv_address=0)
  │       │       └─> Returns: DEV_ERR_NOT_FOUND (never written)
  │       │     
  │       │     Load ROM default:
  │       │       memcpy(nvm_ram_vin, default_vin, 17)
  │       │       state = DEV_NVM_BLOCK_INVALID
  │       │     
  │       │     Log: "Block 0x0001 not found, loaded ROM defaults"
  │       │
  │       ├─> Block 1 (ECU Serial):
  │       │     nv_address = 0x081C0000 (previously written)
  │       │     read_block_from_nv(..., nv_address=0x081C0000)
  │       │       └─> Returns: DEV_OK (data valid)
  │       │     
  │       │     Copy to RAM mirror:
  │       │       memcpy(nvm_ram_ecu_serial, data, 4)
  │       │       state = DEV_NVM_BLOCK_VALID
  │       │     
  │       │     Log: "Block 0x0002 restored from 0x081C0000"
  │       │
  │       └─> ... (continue for all blocks)
  │
  ├─> Mark NvM initialized
  │
  └─> Log: "NVM initialization complete"

┌─────────────────────────────────────────────────────────────────┐
│ RESULT: System Ready                                            │
└─────────────────────────────────────────────────────────────────┘

Layers initialized:
  ✓ Fls  - Hardware driver ready
  ✓ Fee  - Active sector: 0x081C0000, Write pos: 0x081C0080
  ✓ MemIf - Routing layer ready
  ✓ NvM  - All blocks restored to RAM

RAM mirrors populated:
  - Blocks with NV data: Restored from flash
  - Blocks without NV data: Loaded from ROM defaults

Ready for read/write operations
```

---

## Summary of Layer Responsibilities

| Layer | Responsibilities | Key Operations |
|-------|-----------------|----------------|
| **NvM** | Block management, CRC, redundancy, RAM mirrors | Read from RAM (fast), Write to RAM+NV, Restore from NV |
| **MemIf** | Routing, job status | Forward calls to Fee |
| **Fee** | Sector management, wear leveling, addressing | Allocate addresses, switch sectors, track position |
| **Fls** | Hardware operations | Read/write/erase with alignment/padding |
| **HAL** | STM32 hardware control | Direct flash programming |
