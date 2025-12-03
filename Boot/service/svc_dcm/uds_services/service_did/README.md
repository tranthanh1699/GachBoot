# Service DID - Unified DID Registry

## Overview

**Service DID** is a centralized DID (Data Identifier) configuration system that provides a single source of truth for all UDS services that use DIDs (0x22, 0x2E, 0x2F).

### Key Benefits

✅ **Single Configuration** - Define each DID once, use in multiple services  
✅ **Per-Service Control** - Different callbacks and access control for read/write/IO  
✅ **Reduced Duplication** - No more separate registries for 0x22 and 0x2E  
✅ **Easy Extension** - Add new DIDs or services without code duplication  
✅ **Type Safety** - Strong typing with clear callback interfaces  

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Application / UDS Services                  │
│         (Service 0x22, 0x2E, 0x2F handlers)             │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ uds_did_registry_find()
                        │ uds_did_validate_access()
                        │ uds_did_get_length()
                        ▼
┌─────────────────────────────────────────────────────────┐
│               uds_did_registry.c                         │
│                                                          │
│  DID Registry Table (uds_did_entry_t[])                 │
│  ┌────────────────────────────────────────────┐        │
│  │ DID 0xF190 (VIN)                           │        │
│  │   Read:  ✓ (callback, session, security)  │        │
│  │   Write: ✗                                 │        │
│  │   IO:    ✗                                 │        │
│  ├────────────────────────────────────────────┤        │
│  │ DID 0xF15A (Fingerprint)                   │        │
│  │   Read:  ✗                                 │        │
│  │   Write: ✓ (callback, session, security)  │        │
│  │   IO:    ✗                                 │        │
│  └────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ Callbacks
                        ▼
┌─────────────────────────────────────────────────────────┐
│            uds_did_callbacks.c                           │
│                                                          │
│  • did_read_vin()                                       │
│  • did_read_boot_sw_id()                                │
│  • did_write_fingerprint()                              │
│  • did_write_programming_date()                         │
│  • ... (all DID callbacks)                              │
└─────────────────────────────────────────────────────────┘
```

---

## File Structure

```
service_did/
├── uds_did_registry.h          # Registry API & data structures
├── uds_did_registry.c          # Registry implementation & table
├── uds_did_callbacks.h         # Callback function declarations
├── uds_did_callbacks.c         # Callback implementations
├── CMakeLists.txt              # Build configuration
└── README.md                   # This file
```

---

## Configuration Format

### DID Entry Structure

Each DID is configured once with all service-specific settings:

```c
{
    // Basic properties
    .did = 0xF190,
    .expected_length = 17,      // 0 = variable length
    .min_length = 17,
    .max_length = 17,
    
    // Service 0x22 (Read) config
    .read_config = {
        .callback = did_read_vin,
        .length_getter = NULL,  // For variable length
        .session_mask = UDS_SESSION_MASK_ALL,
        .security_mask = UDS_SECURITY_MASK_ALL
    },
    
    // Service 0x2E (Write) config
    .write_config = {
        .callback = NULL,       // NULL = not supported
        .session_mask = 0,
        .security_mask = 0,
        .semantic_validation = false
    },
    
    // Service 0x2F (IO Control) config - Future
    .io_control_config = {
        .callback = NULL,
        .session_mask = 0,
        .security_mask = 0,
        .supported_options = 0
    }
}
```

---

## Adding New DID

### Step 1: Declare Callback in `uds_did_callbacks.h`

```c
/**
 * @brief Read Custom DID - DID 0xF200
 * @param data Output buffer (size guaranteed by registry)
 * @return Std_ReturnType E_OK if success
 */
Std_ReturnType did_read_custom_data(uint8_t *data);
```

### Step 2: Implement Callback in `uds_did_callbacks.c`

```c
Std_ReturnType did_read_custom_data(uint8_t *data)
{
    // Read from NVM, sensors, etc.
    uint32_t value = 0x12345678;
    
    data[0] = (value >> 24) & 0xFF;
    data[1] = (value >> 16) & 0xFF;
    data[2] = (value >> 8) & 0xFF;
    data[3] = value & 0xFF;
    
    DBG_OUT_I("[DID 0xF200] Custom data read: 0x%08X", value);
    return E_OK;
}
```

### Step 3: Add to Registry in `uds_did_registry.c`

```c
static const uds_did_entry_t did_registry[] = {
    // ... existing DIDs ...
    
    /* ====================================================================== */
    /* DID 0xF200: Custom Data                                               */
    /* - Read: All sessions, Level 1 security                                */
    /* - Write: Not supported                                                */
    /* ====================================================================== */
    {
        .did = 0xF200,
        .expected_length = 4,
        .min_length = 4,
        .max_length = 4,
        
        .read_config = {
            .callback = did_read_custom_data,
            .length_getter = NULL,
            .session_mask = UDS_SESSION_MASK_ALL,
            .security_mask = UDS_SECURITY_MASK_LEVEL_1
        },
        
        .write_config = {
            .callback = NULL,  // Read-only
            .session_mask = 0,
            .security_mask = 0,
            .semantic_validation = false
        },
        
        .io_control_config = {
            .callback = NULL,
            .session_mask = 0,
            .security_mask = 0,
            .supported_options = 0
        }
    }
};
```

### Step 4: Rebuild

```bash
cmake --build build/Debug --target Boot -j 8
```

**That's it!** No changes needed to service handlers (0x22, 0x2E, 0x2F).

---

## Usage in Service Handlers

### Service 0x22 (Read Data By Identifier)

```c
// In uds_service_0x22.c
#include "../service_did/uds_did_registry.h"

Std_ReturnType uds_service_0x22_handler(const uds_message_t *message, uint8_t *error_code)
{
    uint16_t did = (message->data[1] << 8) | message->data[2];
    
    // 1. Find DID in registry
    const uds_did_entry_t *entry = uds_did_registry_find(did);
    if (entry == NULL) {
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }
    
    // 2. Check if read is supported
    if (entry->read_config.callback == NULL) {
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }
    
    // 3. Validate access (session & security)
    if (uds_did_validate_access(did, 0x22, current_session, current_security) != E_OK) {
        *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
        return E_NOT_OK;
    }
    
    // 4. Call read callback
    uint8_t data_buffer[256];
    Std_ReturnType result = entry->read_config.callback(data_buffer);
    
    if (result == E_OK) {
        // Build positive response
        uint16_t length = uds_did_get_length(did, 0x22);
        // ... build response with data_buffer ...
    }
    
    return result;
}
```

### Service 0x2E (Write Data By Identifier)

```c
// In uds_service_0x2E.c
#include "../service_did/uds_did_registry.h"

Std_ReturnType uds_service_0x2E_handler(const uds_message_t *message, uint8_t *error_code)
{
    uint16_t did = (message->data[1] << 8) | message->data[2];
    uint16_t data_len = message->length - 3;
    const uint8_t *data = &message->data[3];
    
    // 1. Find DID in registry
    const uds_did_entry_t *entry = uds_did_registry_find(did);
    if (entry == NULL) {
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }
    
    // 2. Check if write is supported
    if (entry->write_config.callback == NULL) {
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;
        return E_NOT_OK;
    }
    
    // 3. Validate length
    if (!uds_did_validate_length(did, 0x2E, data_len)) {
        *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
        return E_NOT_OK;
    }
    
    // 4. Validate access
    if (uds_did_validate_access(did, 0x2E, current_session, current_security) != E_OK) {
        *error_code = UDS_NRC_SECURITY_ACCESS_DENIED;
        return E_NOT_OK;
    }
    
    // 5. Call write callback
    Std_ReturnType result = entry->write_config.callback(data, data_len);
    
    if (result == E_OK) {
        // Build positive response
    } else if (entry->write_config.semantic_validation) {
        *error_code = UDS_NRC_REQUEST_OUT_OF_RANGE;  // Semantic error
    }
    
    return result;
}
```

---

## Access Control

### Session Masks

Control which sessions can access the DID for each service:

```c
#define UDS_SESSION_MASK_DEFAULT    0x01  // Default session
#define UDS_SESSION_MASK_PROG       0x02  // Programming session
#define UDS_SESSION_MASK_EXTENDED   0x04  // Extended diagnostic session
#define UDS_SESSION_MASK_ALL        0xFF  // All sessions

// Example: Allow read in Default and Extended sessions
.read_config = {
    .session_mask = UDS_SESSION_MASK_DEFAULT | UDS_SESSION_MASK_EXTENDED,
    // ...
}
```

### Security Masks

Control which security levels are required:

```c
#define UDS_SECURITY_MASK_LOCKED    0x00  // No security required
#define UDS_SECURITY_MASK_LEVEL_1   0x01  // Level 1 required
#define UDS_SECURITY_MASK_LEVEL_2   0x02  // Level 2 required
#define UDS_SECURITY_MASK_ALL       0xFF  // All levels allowed (no lock)

// Example: Require Level 1 or Level 2 for write
.write_config = {
    .security_mask = UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2,
    // ...
}

// Example: No security required for read
.read_config = {
    .security_mask = UDS_SECURITY_MASK_ALL,
    // ...
}
```

---

## Variable Length DIDs

For DIDs with variable length (e.g., logs, dynamic data):

### Step 1: Set expected_length = 0

```c
{
    .did = 0xF300,
    .expected_length = 0,       // Variable length
    .min_length = 1,
    .max_length = 255,
    // ...
}
```

### Step 2: Provide length_getter for Read

```c
static uint16_t did_get_log_length(void)
{
    // Return current log size
    return get_current_log_size();
}

.read_config = {
    .callback = did_read_log_data,
    .length_getter = did_get_log_length,  // Dynamic length
    // ...
}
```

### Step 3: Validate length in Write callback

```c
Std_ReturnType did_write_variable_data(const uint8_t *data, uint16_t data_len)
{
    // Length already validated by registry (1-255 bytes)
    // Just process the data
    return E_OK;
}
```

---

## Semantic Validation

For DIDs that require application-level validation (beyond length checking):

### Enable semantic_validation flag

```c
.write_config = {
    .callback = did_write_programming_date,
    .semantic_validation = true,  // Enable semantic checks
    // ...
}
```

### Return E_NOT_OK for invalid data

```c
Std_ReturnType did_write_programming_date(const uint8_t *data, uint16_t data_len)
{
    uint16_t year = (data[0] << 8) | data[1];
    uint8_t month = data[2];
    uint8_t day = data[3];
    
    // Semantic validation
    if (year < 2000 || year > 2099 || month < 1 || month > 12 || day < 1 || day > 31) {
        return E_NOT_OK;  // Service handler returns NRC 0x31 (request out of range)
    }
    
    return E_OK;
}
```

---

## Migration from Separate Registries

### Old Approach (Separate Registries)

```c
// uds_rdbi_did_registry.c
static const uds_did_entry_t rdbi_did_registry[] = {
    {0xF190, 17, did_read_vin, NULL, SESSION_ALL, SECURITY_ALL},
    // ...
};

// uds_wdbi_did_registry.c
static const uds_wdbi_did_entry_t wdbi_did_registry[] = {
    {0xF15A, 0, 1, 32, did_write_fingerprint, SESSION_PROG, SECURITY_L1},
    // ...
};
```

### New Approach (Unified Registry)

```c
// uds_did_registry.c
static const uds_did_entry_t did_registry[] = {
    {
        .did = 0xF190,
        .expected_length = 17,
        .read_config = {did_read_vin, NULL, SESSION_ALL, SECURITY_ALL},
        .write_config = {NULL, 0, 0, false},  // Not writable
        .io_control_config = {NULL, 0, 0, 0}
    },
    {
        .did = 0xF15A,
        .expected_length = 0,
        .min_length = 1,
        .max_length = 32,
        .read_config = {NULL, NULL, 0, 0},  // Not readable
        .write_config = {did_write_fingerprint, SESSION_PROG, SECURITY_L1, false},
        .io_control_config = {NULL, 0, 0, 0}
    }
};
```

**Benefits:**
- Single source of truth
- Clear service support (NULL callback = not supported)
- Easy to add new services (just add new config struct)

---

## API Reference

### Registry Functions

```c
// Find DID entry
const uds_did_entry_t* uds_did_registry_find(uint16_t did);

// Get registry size
uint16_t uds_did_registry_get_count(void);

// Check service support
bool uds_did_supports_service(uint16_t did, uint8_t service);

// Validate access
Std_ReturnType uds_did_validate_access(uint16_t did, uint8_t service, 
                                        uint8_t session, uint8_t security);

// Get/validate length
uint16_t uds_did_get_length(uint16_t did, uint8_t service);
bool uds_did_validate_length(uint16_t did, uint8_t service, uint16_t length);
```

### Callback Types

```c
// Read callback
typedef Std_ReturnType (*uds_did_read_callback_t)(uint8_t *data);

// Write callback
typedef Std_ReturnType (*uds_did_write_callback_t)(const uint8_t *data, uint16_t length);

// IO control callback (Future: Service 0x2F)
typedef Std_ReturnType (*uds_did_io_control_callback_t)(
    uint8_t control_option,
    const uint8_t *control_param,
    uint16_t param_length,
    uint8_t *state_record,
    uint16_t *state_length
);

// Dynamic length getter
typedef uint16_t (*uds_did_length_getter_t)(void);
```

---

## Best Practices

### 1. Callback Return Values

- `E_OK` - Operation successful
- `E_NOT_OK` - Operation failed (use for semantic validation failures)
- `DCM_E_PENDING` - Operation pending (will be retried)

### 2. Logging

Use specific tags for DID operations:

```c
DBG_OUT_I("[DID 0xF190] VIN read successfully");
DBG_OUT_E("[DID 0xF15A] Fingerprint write failed: invalid data");
```

### 3. NULL Checks

Always check callback != NULL before calling (registry functions do this automatically).

### 4. Security First

For sensitive DIDs (calibration, keys), always require security:

```c
.write_config = {
    .security_mask = UDS_SECURITY_MASK_LEVEL_2,  // Highest level
    // ...
}
```

---

## Future Extensions

### Service 0x2F (IO Control)

When implementing Service 0x2F, just add io_control callbacks:

```c
{
    .did = 0x0100,
    // ...
    .io_control_config = {
        .callback = did_io_control_actuator,
        .session_mask = UDS_SESSION_MASK_EXTENDED,
        .security_mask = UDS_SECURITY_MASK_LEVEL_1,
        .supported_options = 0x01 | 0x02 | 0x03  // Return control, reset, freeze
    }
}
```

No changes needed to registry structure!

---

## Summary

**Service DID** provides a clean, scalable solution for DID management:

✅ **Single config** per DID for all services  
✅ **Type-safe** callbacks with clear interfaces  
✅ **Flexible** access control per service  
✅ **Easy to extend** with new DIDs or services  
✅ **No code duplication** across service handlers  

Perfect for automotive bootloaders and diagnostic systems! 🚗
