#include "platform_flash.h"
#include "bl_hw_config.h"
#include "bl_memory_map.h"
#include "stm32h7xx_hal.h"

#define BL_FLASH_ERASE_ERROR_NONE        0xFFFFFFFFu
#define BL_FLASH_ERASED_WORD             0xFFFFFFFFu
#define BL_METADATA_CRC32_INIT_VALUE     0xFFFFFFFFu
#define BL_METADATA_CRC32_POLY           0xEDB88320u

static bool platform_flash_range_is_valid(uint32_t address, uint32_t length)
{
    uint32_t app_end = BL_APP_START_ADDR + BL_APP_MAX_SIZE;
    uint32_t end_address = address + length;

    if (length == 0u)
    {
        return false;
    }

    if (end_address < address)
    {
        return false;
    }

    return ((address >= BL_APP_START_ADDR) && (end_address <= app_end));
}

static bool platform_flash_get_padded_length(uint32_t length, uint32_t *padded_length)
{
    uint32_t remainder;

    if ((length == 0u) || (padded_length == (uint32_t *)0))
    {
        return false;
    }

    remainder = length % BL_PLATFORM_FLASH_WRITE_ALIGN;
    if (remainder == 0u)
    {
        *padded_length = length;
    }
    else
    {
        uint32_t padding = BL_PLATFORM_FLASH_WRITE_ALIGN - remainder;
        *padded_length = length + padding;
        if (*padded_length < length)
        {
            return false;
        }
    }

    return true;
}

static uint32_t platform_flash_get_bank(uint32_t address)
{
#if defined(FLASH_BANK2_BASE)
    if (address >= FLASH_BANK2_BASE)
    {
        return FLASH_BANK_2;
    }
#endif

    return FLASH_BANK_1;
}

static uint32_t platform_flash_get_bank_base(uint32_t bank)
{
#if defined(FLASH_BANK2_BASE)
    if (bank == FLASH_BANK_2)
    {
        return FLASH_BANK2_BASE;
    }
#else
    (void)bank;
#endif

    return FLASH_BANK1_BASE;
}

static uint32_t platform_flash_get_sector(uint32_t address)
{
    uint32_t bank = platform_flash_get_bank(address);
    uint32_t bank_base = platform_flash_get_bank_base(bank);

    return (address - bank_base) / FLASH_SECTOR_SIZE;
}

static uint32_t platform_flash_crc32_update_byte(uint32_t crc, uint8_t data)
{
    uint8_t bit_index = 0u;

    crc ^= (uint32_t)data;
    for (bit_index = 0u; bit_index < 8u; bit_index++)
    {
        if ((crc & 1u) != 0u)
        {
            crc = (crc >> 1u) ^ BL_METADATA_CRC32_POLY;
        }
        else
        {
            crc >>= 1u;
        }
    }

    return crc;
}

static uint32_t platform_flash_metadata_crc32(const uint8_t *data, uint32_t length)
{
    uint32_t crc = BL_METADATA_CRC32_INIT_VALUE;
    uint32_t index = 0u;

    for (index = 0u; index < length; index++)
    {
        crc = platform_flash_crc32_update_byte(crc, data[index]);
    }

    return ~crc;
}

static bl_status_t platform_flash_program_flashword(uint32_t address, const uint32_t *flash_word)
{
    if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_FLASHWORD, address, (uint32_t)((uintptr_t)flash_word)) != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    return BL_STATUS_OK;
}

static bl_status_t platform_flash_erase_bank_range(uint32_t start_address, uint32_t end_address)
{
    FLASH_EraseInitTypeDef erase_init;
    uint32_t sector_error = BL_FLASH_ERASE_ERROR_NONE;
    uint32_t first_sector = platform_flash_get_sector(start_address);
    uint32_t last_sector = platform_flash_get_sector(end_address - 1u);

    erase_init.TypeErase = FLASH_TYPEERASE_SECTORS;
    erase_init.Banks = platform_flash_get_bank(start_address);
    erase_init.Sector = first_sector;
    erase_init.NbSectors = (last_sector - first_sector) + 1u;
    erase_init.VoltageRange = FLASH_VOLTAGE_RANGE_4;

    if (HAL_FLASHEx_Erase(&erase_init, &sector_error) != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    if (sector_error != BL_FLASH_ERASE_ERROR_NONE)
    {
        return BL_STATUS_IO;
    }

    return BL_STATUS_OK;
}

bl_status_t platform_flash_erase_app_area(void)
{
    bl_status_t status;
    uint32_t app_end = BL_APP_START_ADDR + BL_APP_MAX_SIZE;

    if (HAL_FLASH_Unlock() != HAL_OK)
    {
        return BL_STATUS_IO;
    }

#if defined(FLASH_BANK2_BASE)
    if ((BL_APP_START_ADDR < FLASH_BANK2_BASE) && (app_end > FLASH_BANK2_BASE))
    {
        status = platform_flash_erase_bank_range(BL_APP_START_ADDR, FLASH_BANK2_BASE);
        if (status == BL_STATUS_OK)
        {
            status = platform_flash_erase_bank_range(FLASH_BANK2_BASE, app_end);
        }
    }
    else
#endif
    {
        status = platform_flash_erase_bank_range(BL_APP_START_ADDR, app_end);
    }

    if (HAL_FLASH_Lock() != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    return status;
}

bl_status_t platform_flash_invalidate_app_marker(void)
{
    bl_status_t status;
    uint32_t metadata_sector_start = BL_APP_METADATA_ADDR - (BL_APP_METADATA_ADDR % FLASH_SECTOR_SIZE);
    uint32_t metadata_sector_end = metadata_sector_start + FLASH_SECTOR_SIZE;

    if ((BL_APP_METADATA_ADDR % BL_PLATFORM_FLASH_WRITE_ALIGN) != 0u)
    {
        return BL_STATUS_PARAM;
    }

    if (metadata_sector_end < metadata_sector_start)
    {
        return BL_STATUS_PARAM;
    }

    if (HAL_FLASH_Unlock() != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    status = platform_flash_erase_bank_range(metadata_sector_start, metadata_sector_end);

    if (HAL_FLASH_Lock() != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    return status;
}

bl_status_t platform_flash_mark_app_valid(uint32_t app_size, const uint8_t *signature, uint16_t signature_length)
{
    uint32_t metadata_crc = 0u;
    bl_status_t status;
    uint32_t flash_buffer[288 / sizeof(uint32_t)];
    bl_app_metadata_t *metadata = (bl_app_metadata_t *)flash_buffer;
    uint32_t offset = 0u;

    if ((signature_length > BL_APP_METADATA_SIGNATURE_SIZE) ||
        ((signature_length > 0u) && (signature == (const uint8_t *)0)))
    {
        return BL_STATUS_PARAM;
    }

    status = platform_flash_invalidate_app_marker();
    if (status != BL_STATUS_OK)
    {
        return status;
    }

    for (uint32_t i = 0u; i < (sizeof(flash_buffer) / sizeof(uint32_t)); i++)
    {
        flash_buffer[i] = BL_FLASH_ERASED_WORD;
    }

    metadata->app_size = app_size;
    metadata->valid_marker = BL_APP_VALID_MARKER;
    for (uint32_t i = 0u; i < BL_APP_METADATA_SIGNATURE_SIZE; i++)
    {
        if (i < signature_length) {
            metadata->signature[i] = signature[i];
        } else {
            metadata->signature[i] = 0xFF;
        }
    }

    // Calculate CRC over everything except the crc field itself
    // CRC runs over app_size, valid_marker, and signature.
    metadata_crc = platform_flash_metadata_crc32(
        (const uint8_t *)&metadata->app_size,
        sizeof(bl_app_metadata_t) - sizeof(uint32_t)
    );
    metadata->crc = metadata_crc;

    if (HAL_FLASH_Unlock() != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    while (offset < sizeof(flash_buffer))
    {
        status = platform_flash_program_flashword(BL_APP_METADATA_ADDR + offset, &flash_buffer[offset / sizeof(uint32_t)]);
        if (status != BL_STATUS_OK)
        {
            (void)HAL_FLASH_Lock();
            return status;
        }
        offset += BL_PLATFORM_FLASH_WRITE_ALIGN;
    }

    if (HAL_FLASH_Lock() != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    return BL_STATUS_OK;
}

bl_status_t platform_flash_write(uint32_t address, const uint8_t *data, uint16_t length)
{
    uint32_t offset = 0u;
    uint32_t program_address = address;
    uint32_t padded_length = 0u;
    uint32_t flash_word[BL_PLATFORM_FLASH_WRITE_ALIGN / sizeof(uint32_t)];

    if ((data == (const uint8_t *)0) || (length == 0u))
    {
        return BL_STATUS_PARAM;
    }

    if (platform_flash_get_padded_length((uint32_t)length, &padded_length) == false)
    {
        return BL_STATUS_PARAM;
    }

    if (platform_flash_range_is_valid(address, padded_length) == false)
    {
        return BL_STATUS_PARAM;
    }

    if ((address % BL_PLATFORM_FLASH_WRITE_ALIGN) != 0u)
    {
        return BL_STATUS_PARAM;
    }

    if (HAL_FLASH_Unlock() != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    while (offset < padded_length)
    {
        uint32_t word_index = 0u;
        uint32_t byte_index = 0u;

        for (word_index = 0u; word_index < (BL_PLATFORM_FLASH_WRITE_ALIGN / sizeof(uint32_t)); word_index++)
        {
            flash_word[word_index] = 0xFFFFFFFFu;
        }

        for (byte_index = 0u; byte_index < BL_PLATFORM_FLASH_WRITE_ALIGN; byte_index++)
        {
            uint32_t source_index = offset + byte_index;

            if (source_index < (uint32_t)length)
            {
                uint32_t shift = (byte_index % sizeof(uint32_t)) * 8u;
                word_index = byte_index / sizeof(uint32_t);
                flash_word[word_index] &= ~(0xFFu << shift);
                flash_word[word_index] |= ((uint32_t)data[source_index] << shift);
            }
        }

        if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_FLASHWORD, program_address, (uint32_t)((uintptr_t)flash_word)) != HAL_OK)
        {
            (void)HAL_FLASH_Lock();
            return BL_STATUS_IO;
        }

        offset += BL_PLATFORM_FLASH_WRITE_ALIGN;
        program_address += BL_PLATFORM_FLASH_WRITE_ALIGN;
    }

    if (HAL_FLASH_Lock() != HAL_OK)
    {
        return BL_STATUS_IO;
    }

    return BL_STATUS_OK;
}

bl_status_t platform_flash_read(uint32_t address, uint8_t *data, uint16_t length)
{
    uint16_t index = 0u;
    const uint8_t *flash_ptr = (const uint8_t *)(uintptr_t)address;

    if ((data == (uint8_t *)0) || (length == 0u))
    {
        return BL_STATUS_PARAM;
    }

    for (index = 0u; index < length; index++)
    {
        data[index] = flash_ptr[index];
    }

    return BL_STATUS_OK;
}
