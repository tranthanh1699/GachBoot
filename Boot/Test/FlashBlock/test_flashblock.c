/**
 * @file test_flashblock.c
 * @brief Test example for dev_flashblock module
 * 
 * Demonstrates usage of flash block operations with automatic
 * sector erase and 32-byte aligned write.
 */

#include "dev_flashblock.h"
#include "dev_log.h"
#include <string.h>

/* Test configuration */
#define TEST_FLASH_ADDRESS      0x08100000U  /* Application region start */
#define TEST_DATA_SIZE          1000U        /* Test data size (not 32-byte aligned) */

/* ===== Progress Callback Example ===== */

static void flash_progress_callback(uint32_t current, uint32_t total, void *context)
{
    uint32_t percent = (current * 100) / total;
    DEV_LOG_INFO("Flash Progress: %u%% (%u/%u bytes)", percent, current, total);
}

/* ===== Test Functions ===== */

/**
 * @brief Test basic erase and write
 */
static void test_erase_and_write(void)
{
    DEV_LOG_INFO("=== Test 1: Erase and Write ===");
    
    // Prepare test data (not aligned)
    uint8_t test_data[TEST_DATA_SIZE];
    for (uint32_t i = 0; i < TEST_DATA_SIZE; i++) {
        test_data[i] = (uint8_t)(i & 0xFF);
    }
    
    // Initialize flash block module with progress callback
    dev_flashblock_config_t config = {
        .write_alignment = 32,
        .erase_timeout_ms = 2000,
        .write_timeout_ms = 100,
        .auto_verify = true,
        .progress_cb = flash_progress_callback,
        .context = NULL
    };
    
    dev_flashblock_result_t result = dev_flashblock_init(&config);
    if (result != DEV_FLASHBLOCK_OK) {
        DEV_LOG_ERROR("Failed to initialize flashblock: %s", 
                      dev_flashblock_get_error_string(result));
        return;
    }
    
    // Erase and write in one operation
    DEV_LOG_INFO("Writing %u bytes to 0x%08X...", TEST_DATA_SIZE, TEST_FLASH_ADDRESS);
    result = dev_flashblock_erase_and_write(TEST_FLASH_ADDRESS, test_data, TEST_DATA_SIZE);
    
    if (result == DEV_FLASHBLOCK_OK) {
        DEV_LOG_INFO("✓ Erase and write successful!");
    } else {
        DEV_LOG_ERROR("✗ Erase and write failed: %s", 
                      dev_flashblock_get_error_string(result));
    }
}

/**
 * @brief Test separate erase and write operations
 */
static void test_separate_operations(void)
{
    DEV_LOG_INFO("=== Test 2: Separate Erase and Write ===");
    
    // Prepare test data
    const char *message = "Hello, Flash Block Module! This is a test message.";
    uint32_t msg_len = strlen(message) + 1;  // Include null terminator
    
    // Erase first
    DEV_LOG_INFO("Erasing %u bytes at 0x%08X...", msg_len, TEST_FLASH_ADDRESS);
    dev_flashblock_result_t result = dev_flashblock_erase(TEST_FLASH_ADDRESS, msg_len);
    
    if (result != DEV_FLASHBLOCK_OK) {
        DEV_LOG_ERROR("Erase failed: %s", dev_flashblock_get_error_string(result));
        return;
    }
    
    // Then write
    DEV_LOG_INFO("Writing message...");
    result = dev_flashblock_write(TEST_FLASH_ADDRESS, (const uint8_t*)message, msg_len);
    
    if (result != DEV_FLASHBLOCK_OK) {
        DEV_LOG_ERROR("Write failed: %s", dev_flashblock_get_error_string(result));
        return;
    }
    
    DEV_LOG_INFO("✓ Write successful!");
    
    // Read back and verify
    char read_buffer[100];
    result = dev_flashblock_read(TEST_FLASH_ADDRESS, (uint8_t*)read_buffer, msg_len);
    
    if (result == DEV_FLASHBLOCK_OK) {
        if (strcmp(message, read_buffer) == 0) {
            DEV_LOG_INFO("✓ Read back matches: \"%s\"", read_buffer);
        } else {
            DEV_LOG_ERROR("✗ Read back mismatch!");
        }
    } else {
        DEV_LOG_ERROR("Read failed: %s", dev_flashblock_get_error_string(result));
    }
}

/**
 * @brief Test write with unaligned address
 */
static void test_unaligned_write(void)
{
    DEV_LOG_INFO("=== Test 3: Unaligned Address Write ===");
    
    // Write to unaligned address (not 32-byte boundary)
    uint32_t unaligned_addr = TEST_FLASH_ADDRESS + 5;
    const char *data = "Unaligned test";
    uint32_t data_len = strlen(data) + 1;
    
    DEV_LOG_INFO("Writing to unaligned address 0x%08X...", unaligned_addr);
    
    // The module will automatically align this
    dev_flashblock_result_t result = dev_flashblock_erase_and_write(
        unaligned_addr, 
        (const uint8_t*)data, 
        data_len
    );
    
    if (result == DEV_FLASHBLOCK_OK) {
        DEV_LOG_INFO("✓ Unaligned write successful (auto-aligned by module)");
        
        // Verify
        char verify_buffer[32];
        result = dev_flashblock_read(unaligned_addr, (uint8_t*)verify_buffer, data_len);
        if (result == DEV_FLASHBLOCK_OK && strcmp(data, verify_buffer) == 0) {
            DEV_LOG_INFO("✓ Verification passed");
        }
    } else {
        DEV_LOG_ERROR("✗ Unaligned write failed: %s", 
                      dev_flashblock_get_error_string(result));
    }
}

/**
 * @brief Test large data write (multiple chunks)
 */
static void test_large_write(void)
{
    DEV_LOG_INFO("=== Test 4: Large Data Write ===");
    
    // Allocate larger buffer (1KB)
    #define LARGE_SIZE 1024
    uint8_t large_data[LARGE_SIZE];
    
    // Fill with pattern
    for (uint32_t i = 0; i < LARGE_SIZE; i++) {
        large_data[i] = (uint8_t)((i * 7 + 13) & 0xFF);
    }
    
    DEV_LOG_INFO("Writing %u bytes (will be split into chunks)...", LARGE_SIZE);
    
    dev_flashblock_result_t result = dev_flashblock_erase_and_write(
        TEST_FLASH_ADDRESS, 
        large_data, 
        LARGE_SIZE
    );
    
    if (result == DEV_FLASHBLOCK_OK) {
        DEV_LOG_INFO("✓ Large write successful!");
        
        // Verify a portion
        uint8_t verify_buffer[64];
        result = dev_flashblock_read(TEST_FLASH_ADDRESS + 512, verify_buffer, 64);
        if (result == DEV_FLASHBLOCK_OK) {
            bool match = true;
            for (uint32_t i = 0; i < 64; i++) {
                if (verify_buffer[i] != large_data[512 + i]) {
                    match = false;
                    break;
                }
            }
            if (match) {
                DEV_LOG_INFO("✓ Verification passed");
            } else {
                DEV_LOG_ERROR("✗ Verification failed");
            }
        }
    } else {
        DEV_LOG_ERROR("✗ Large write failed: %s", 
                      dev_flashblock_get_error_string(result));
    }
}

/* ===== Main Test Runner ===== */

void run_flashblock_tests(void)
{
    DEV_LOG_INFO("========================================");
    DEV_LOG_INFO("   Flash Block Module Test Suite");
    DEV_LOG_INFO("========================================");
    
    // Run all tests
    test_erase_and_write();
    test_separate_operations();
    test_unaligned_write();
    test_large_write();
    
    DEV_LOG_INFO("========================================");
    DEV_LOG_INFO("   All tests completed!");
    DEV_LOG_INFO("========================================");
}

/* Example usage in main.c:
 * 
 * #include "test_flashblock.h"
 * 
 * int main(void) {
 *     // ... HAL initialization ...
 *     
 *     // Run flash block tests
 *     run_flashblock_tests();
 *     
 *     while(1) {
 *         // Main loop
 *     }
 * }
 */
