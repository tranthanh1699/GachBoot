"""
Memory Layout Module - Validation and Code Generation
Defines bootloader, application, and download memory regions
"""

def validate_memory_layout(memory_layout):
    """Validate memory layout configuration"""
    errors = []
    
    if not memory_layout:
        return ["Memory layout configuration is missing"]
    
    # Validate bootloader region
    bootloader = memory_layout.get('bootloader_region', {})
    if not bootloader:
        errors.append("Bootloader region is not defined")
    else:
        if 'start_address' not in bootloader:
            errors.append("Bootloader start address is missing")
        if 'size' not in bootloader:
            errors.append("Bootloader size is missing")
        
        try:
            bl_start = int(bootloader.get('start_address', '0x08000000'), 16)
            bl_size = int(bootloader.get('size', '0x40000'), 16)
            
            if bl_start < 0x08000000 or bl_start >= 0x08200000:
                errors.append(f"Bootloader start address 0x{bl_start:08X} is out of valid range")
            
            if bl_size <= 0 or bl_size > 0x200000:
                errors.append(f"Bootloader size 0x{bl_size:X} is invalid")
                
        except ValueError as e:
            errors.append(f"Invalid bootloader address/size format: {e}")
    
    # Validate application region
    application = memory_layout.get('application_region', {})
    if not application:
        errors.append("Application region is not defined")
    else:
        if 'start_address' not in application:
            errors.append("Application start address is missing")
        if 'size' not in application:
            errors.append("Application size is missing")
        
        try:
            app_start = int(application.get('start_address', '0x08100000'), 16)
            app_size = int(application.get('size', '0x100000'), 16)
            
            if app_start < 0x08000000 or app_start >= 0x08200000:
                errors.append(f"Application start address 0x{app_start:08X} is out of valid range")
            
            if app_size <= 0 or app_size > 0x200000:
                errors.append(f"Application size 0x{app_size:X} is invalid")
            
            # Check for overlap with bootloader
            if bootloader:
                bl_start = int(bootloader.get('start_address', '0x08000000'), 16)
                bl_size = int(bootloader.get('size', '0x40000'), 16)
                bl_end = bl_start + bl_size
                app_end = app_start + app_size
                
                if app_start < bl_end and app_end > bl_start:
                    errors.append(f"Application region overlaps with bootloader region")
                    
        except ValueError as e:
            errors.append(f"Invalid application address/size format: {e}")
    
    # Validate download region (optional - can match application)
    download = memory_layout.get('download_region', {})
    if download:
        if 'start_address' not in download:
            errors.append("Download start address is missing")
        if 'size' not in download:
            errors.append("Download size is missing")
        if 'alignment' not in download:
            errors.append("Download alignment is missing")
        
        try:
            dl_start = int(download.get('start_address', '0x08100000'), 16)
            dl_size = int(download.get('size', '0x100000'), 16)
            dl_align = int(download.get('alignment', '32'))
            
            if dl_start < 0x08000000 or dl_start >= 0x08200000:
                errors.append(f"Download start address 0x{dl_start:08X} is out of valid range")
            
            if dl_size <= 0 or dl_size > 0x200000:
                errors.append(f"Download size 0x{dl_size:X} is invalid")
            
            if dl_align not in [1, 2, 4, 8, 16, 32]:
                errors.append(f"Download alignment {dl_align} is invalid (must be 1, 2, 4, 8, 16, or 32)")
                
            # Check alignment of start address
            if dl_start % dl_align != 0:
                errors.append(f"Download start address 0x{dl_start:08X} is not aligned to {dl_align} bytes")
                
        except ValueError as e:
            errors.append(f"Invalid download address/size format: {e}")
    
    return errors


def generate_memory_layout_code(memory_layout, output_path, project_name):
    """Generate memory layout header file"""
    
    bootloader = memory_layout.get('bootloader_region', {})
    application = memory_layout.get('application_region', {})
    download = memory_layout.get('download_region', {})
    
    # Parse values
    bl_start = bootloader.get('start_address', '0x08000000')
    bl_size = bootloader.get('size', '0x40000')
    bl_name = bootloader.get('name', 'Bootloader')
    bl_desc = bootloader.get('description', 'Bootloader region')
    
    app_start = application.get('start_address', '0x08100000')
    app_size = application.get('size', '0x100000')
    app_name = application.get('name', 'Application')
    app_desc = application.get('description', 'Application region')
    
    dl_start = download.get('start_address', app_start) if download else app_start
    dl_size = download.get('size', app_size) if download else app_size
    dl_align = download.get('alignment', '32') if download else '32'
    dl_max_block = download.get('max_block_length', '256') if download else '256'
    
    content = f'''/**
 * @file Memory_Layout_Config.h
 * @brief Memory Layout Configuration
 * @date Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 * 
 * Auto-generated from gachboot_config.json
 * DO NOT EDIT MANUALLY
 */

#ifndef MEMORY_LAYOUT_CONFIG_H
#define MEMORY_LAYOUT_CONFIG_H

#include <stdint.h>

/* ========================================================================== */
/*                         Bootloader Region                                  */
/* ========================================================================== */

#define BOOTLOADER_START_ADDRESS        {bl_start}U    /* {bl_name}: {bl_desc} */
#define BOOTLOADER_SIZE                 {bl_size}U
#define BOOTLOADER_END_ADDRESS          (BOOTLOADER_START_ADDRESS + BOOTLOADER_SIZE - 1)

/* ========================================================================== */
/*                         Application Region                                 */
/* ========================================================================== */

#define APPLICATION_START_ADDRESS       {app_start}U   /* {app_name}: {app_desc} */
#define APPLICATION_SIZE                {app_size}U
#define APPLICATION_END_ADDRESS         (APPLICATION_START_ADDRESS + APPLICATION_SIZE - 1)

/* ========================================================================== */
/*                         Download Region (UDS 0x34)                        */
/* ========================================================================== */

#define DOWNLOAD_BASE_ADDRESS           {dl_start}U
#define DOWNLOAD_MAX_SIZE_BYTES         {dl_size}U
#define DOWNLOAD_ALIGNMENT_BYTES        {dl_align}U
#define DOWNLOAD_MAX_BLOCK_LENGTH_BYTES {dl_max_block}U

/* ========================================================================== */
/*                         Memory Region Validation                           */
/* ========================================================================== */

/**
 * @brief Check if address is in bootloader region
 */
static inline uint8_t is_address_in_bootloader(uint32_t address)
{{
    return (address >= BOOTLOADER_START_ADDRESS && address <= BOOTLOADER_END_ADDRESS);
}}

/**
 * @brief Check if address is in application region
 */
static inline uint8_t is_address_in_application(uint32_t address)
{{
    return (address >= APPLICATION_START_ADDRESS && address <= APPLICATION_END_ADDRESS);
}}

/**
 * @brief Check if address is valid for download
 */
static inline uint8_t is_address_valid_for_download(uint32_t address, uint32_t size)
{{
    if (address < DOWNLOAD_BASE_ADDRESS)
        return 0;
    
    if ((address + size) > (DOWNLOAD_BASE_ADDRESS + DOWNLOAD_MAX_SIZE_BYTES))
        return 0;
    
    if ((address % DOWNLOAD_ALIGNMENT_BYTES) != 0)
        return 0;
    
    return 1;
}}

#endif /* MEMORY_LAYOUT_CONFIG_H */
'''
    
    # Write to file in Memory_Layout_Gen subdirectory
    import os
    gen_dir = os.path.join(output_path, 'Memory_Layout_Gen')
    os.makedirs(gen_dir, exist_ok=True)
    
    output_file = os.path.join(gen_dir, 'Memory_Layout_Config.h')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return output_file
