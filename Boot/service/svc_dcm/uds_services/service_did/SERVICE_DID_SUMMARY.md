# Service DID - Unified DID Registry System

## 🎯 Overview

**Service DID** là hệ thống quản lý DID tập trung cho tất cả UDS services (0x22, 0x2E, 0x2F). Thay vì mỗi service có registry riêng, tất cả đều dùng chung một config table.

## 📁 Files Created

```
service_did/
├── uds_did_registry.h          # API & data structures (180 lines)
├── uds_did_registry.c          # Implementation & registry table (550 lines)
├── uds_did_callbacks.h         # Callback declarations (80 lines)
├── uds_did_callbacks.c         # Callback implementations (180 lines)
├── CMakeLists.txt              # Build config
└── README.md                   # Complete documentation (600+ lines)
```

## 🔑 Key Features

### 1. **Single DID Configuration**

Mỗi DID chỉ config **1 lần**, với settings cho TẤT CẢ services:

```c
{
    .did = 0xF190,              // VIN
    .expected_length = 17,
    
    // Service 0x22 config
    .read_config = {
        .callback = did_read_vin,
        .session_mask = UDS_SESSION_MASK_ALL,
        .security_mask = UDS_SECURITY_MASK_ALL
    },
    
    // Service 0x2E config
    .write_config = {
        .callback = NULL,       // NULL = not supported
        .session_mask = 0,
        .security_mask = 0
    },
    
    // Service 0x2F config (Future)
    .io_control_config = {
        .callback = NULL,
        .session_mask = 0,
        .security_mask = 0
    }
}
```

### 2. **Per-Service Access Control**

Mỗi service có session & security mask riêng:

```c
// DID 0xF15A: Fingerprint
.read_config = {
    .callback = NULL,           // Không cho đọc
},
.write_config = {
    .callback = did_write_fingerprint,
    .session_mask = UDS_SESSION_MASK_PROG | UDS_SESSION_MASK_EXTENDED,
    .security_mask = UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2
}
```

### 3. **Variable Length Support**

```c
{
    .did = 0xF15A,
    .expected_length = 0,       // Variable
    .min_length = 1,
    .max_length = 32,
    
    .read_config = {
        .length_getter = did_get_fingerprint_length  // Dynamic length
    }
}
```

### 4. **Semantic Validation**

```c
.write_config = {
    .semantic_validation = true,    // Enable app-level validation
    .callback = did_write_programming_date  // Validates date format
}
```

## 🚀 Usage in Service Handlers

### Service 0x22 (Read)

```c
#include "../service_did/uds_did_registry.h"

// 1. Find DID
const uds_did_entry_t *entry = uds_did_registry_find(did);

// 2. Check support
if (entry->read_config.callback == NULL) {
    return E_NOT_OK;  // Not readable
}

// 3. Validate access
if (uds_did_validate_access(did, 0x22, session, security) != E_OK) {
    return E_NOT_OK;  // Access denied
}

// 4. Call callback
uint8_t data[256];
Std_ReturnType result = entry->read_config.callback(data);
```

### Service 0x2E (Write)

```c
// 1. Find & validate
const uds_did_entry_t *entry = uds_did_registry_find(did);
if (entry->write_config.callback == NULL) {
    return E_NOT_OK;
}

// 2. Validate length
if (!uds_did_validate_length(did, 0x2E, length)) {
    return E_NOT_OK;
}

// 3. Validate access
if (uds_did_validate_access(did, 0x2E, session, security) != E_OK) {
    return E_NOT_OK;
}

// 4. Call callback
Std_ReturnType result = entry->write_config.callback(data, length);
```

## 📝 Adding New DID (3 Steps)

### Step 1: Declare Callback

```c
// uds_did_callbacks.h
Std_ReturnType did_read_my_data(uint8_t *data);
```

### Step 2: Implement Callback

```c
// uds_did_callbacks.c
Std_ReturnType did_read_my_data(uint8_t *data)
{
    // Read from NVM/sensors/etc
    memcpy(data, my_buffer, my_length);
    return E_OK;
}
```

### Step 3: Add to Registry

```c
// uds_did_registry.c
static const uds_did_entry_t did_registry[] = {
    // ... existing DIDs ...
    
    {
        .did = 0xF200,
        .expected_length = 10,
        
        .read_config = {
            .callback = did_read_my_data,
            .session_mask = UDS_SESSION_MASK_ALL,
            .security_mask = UDS_SECURITY_MASK_LEVEL_1
        },
        
        .write_config = {
            .callback = NULL  // Read-only
        }
    }
};
```

**Done!** No changes to service handlers needed.

## 🔧 Migration Path

### Old Approach

```
service_0x22/
  ├── uds_rdbi_did_registry.h
  └── uds_rdbi_did_registry.c

service_0x2E/
  ├── uds_wdbi_did_registry.h
  └── uds_wdbi_did_registry.c

service_0x2F/  (Future)
  ├── uds_ioctl_did_registry.h
  └── uds_ioctl_did_registry.c
```

**Problems:**
- ❌ DID config duplicated across services
- ❌ Hard to maintain consistency
- ❌ Callback code duplicated

### New Approach

```
service_did/
  ├── uds_did_registry.h        # Single registry API
  ├── uds_did_registry.c        # Single registry table
  ├── uds_did_callbacks.h
  └── uds_did_callbacks.c
```

**Benefits:**
- ✅ Single source of truth
- ✅ Easy to add new services
- ✅ No code duplication

## 🎨 Registry Table Structure

```c
static const uds_did_entry_t did_registry[] = {
    /* DID 0xF190: VIN - Read Only */
    {
        .did = 0xF190,
        .expected_length = 17,
        .read_config = {did_read_vin, NULL, ALL_SESSIONS, ALL_SECURITY},
        .write_config = {NULL, 0, 0, false},
        .io_control_config = {NULL, 0, 0, 0}
    },
    
    /* DID 0xF15A: Fingerprint - Write Only */
    {
        .did = 0xF15A,
        .expected_length = 0,  // Variable 1-32 bytes
        .min_length = 1,
        .max_length = 32,
        .read_config = {NULL, NULL, 0, 0},
        .write_config = {did_write_fingerprint, PROG|EXT, L1|L2, false},
        .io_control_config = {NULL, 0, 0, 0}
    },
    
    /* DID 0xF199: Programming Date - Write Only with Validation */
    {
        .did = 0xF199,
        .expected_length = 4,
        .read_config = {NULL, NULL, 0, 0},
        .write_config = {did_write_programming_date, PROG, L2, true},  // Semantic validation
        .io_control_config = {NULL, 0, 0, 0}
    }
};
```

## 📊 Current DIDs

| DID | Name | Read | Write | Length | Sessions | Security |
|-----|------|------|-------|--------|----------|----------|
| 0xF190 | VIN | ✓ | ✗ | 17 | All | All |
| 0xF183 | Boot SW ID | ✓ | ✗ | 11 | All | All |
| 0xF184 | App SW ID | ✓ | ✗ | 10 | All | All |
| 0xF18C | ECU Serial | ✓ | ✗ | 4 | Default/Ext | All |
| 0xF15A | Fingerprint | ✗ | ✓ | 1-32 | Prog/Ext | L1/L2 |
| 0xF199 | Prog Date | ✗ | ✓ | 4 | Prog | L2 |
| 0xF100 | ECU Config | ✓ | ✓ | 2 | Extended | L1/L2 |

## 🔐 Access Control

### Session Masks

```c
#define UDS_SESSION_MASK_DEFAULT    0x01
#define UDS_SESSION_MASK_PROG       0x02
#define UDS_SESSION_MASK_EXTENDED   0x04
#define UDS_SESSION_MASK_ALL        0xFF

// Usage: Allow Prog OR Extended
.session_mask = UDS_SESSION_MASK_PROG | UDS_SESSION_MASK_EXTENDED
```

### Security Masks

```c
#define UDS_SECURITY_MASK_LOCKED    0x00  // No security needed
#define UDS_SECURITY_MASK_LEVEL_1   0x01
#define UDS_SECURITY_MASK_LEVEL_2   0x02
#define UDS_SECURITY_MASK_ALL       0xFF  // All levels allowed

// Usage: Require Level 1 OR Level 2
.security_mask = UDS_SECURITY_MASK_LEVEL_1 | UDS_SECURITY_MASK_LEVEL_2
```

## 🛠️ API Reference

### Registry Functions

```c
// Find DID entry
const uds_did_entry_t* uds_did_registry_find(uint16_t did);

// Get count
uint16_t uds_did_registry_get_count(void);

// Check service support
bool uds_did_supports_service(uint16_t did, uint8_t service);

// Validate access
Std_ReturnType uds_did_validate_access(
    uint16_t did,
    uint8_t service,
    uint8_t session,
    uint8_t security
);

// Length operations
uint16_t uds_did_get_length(uint16_t did, uint8_t service);
bool uds_did_validate_length(uint16_t did, uint8_t service, uint16_t length);
```

### Callback Types

```c
// Read callback
typedef Std_ReturnType (*uds_did_read_callback_t)(uint8_t *data);

// Write callback
typedef Std_ReturnType (*uds_did_write_callback_t)(const uint8_t *data, uint16_t length);

// IO control callback (Future)
typedef Std_ReturnType (*uds_did_io_control_callback_t)(
    uint8_t control_option,
    const uint8_t *control_param,
    uint16_t param_length,
    uint8_t *state_record,
    uint16_t *state_length
);

// Length getter (for variable length DIDs)
typedef uint16_t (*uds_did_length_getter_t)(void);
```

## 📦 Build Integration

### CMakeLists.txt

```cmake
# In service/svc_dcm/uds_services/CMakeLists.txt

# Add service_did subdirectory
add_subdirectory(service_did)

# Link to services that use DIDs
target_link_libraries(service_0x22
    service_did  # Shared DID registry
)

target_link_libraries(service_0x2E
    service_did  # Shared DID registry
)
```

## 🎯 Benefits Summary

| Aspect | Old (Separate) | New (Unified) |
|--------|---------------|---------------|
| **Config** | 3 files (0x22, 0x2E, 0x2F) | 1 file |
| **Add DID** | Edit 3 files | Edit 1 file |
| **Consistency** | Manual sync needed | Automatic |
| **Callbacks** | May duplicate | Single implementation |
| **Maintenance** | Hard | Easy |
| **Extension** | Add new registry | Add new field |

## 🚀 Future: Service 0x2F Support

Khi implement Service 0x2F (IO Control), chỉ cần:

1. **Add callback** vào `uds_did_callbacks.c`
2. **Update registry** với io_control_config
3. **Update service handler** để dùng registry

**Không cần** sửa registry structure hay API!

```c
// Example: Future IO Control
{
    .did = 0x0100,
    // ...
    .io_control_config = {
        .callback = did_io_control_actuator,
        .session_mask = UDS_SESSION_MASK_EXTENDED,
        .security_mask = UDS_SECURITY_MASK_LEVEL_1,
        .supported_options = 0x01 | 0x02 | 0x03  // Return/Reset/Freeze
    }
}
```

## 📚 Documentation

- **README.md**: 600+ lines comprehensive guide
- **Code comments**: Full documentation in all files
- **API examples**: Usage examples in service handlers
- **Migration guide**: How to move from old approach

---

## ✅ Summary

**Service DID** provides:

✅ **Centralized DID configuration** - Single source of truth  
✅ **Per-service control** - Different callbacks & access per service  
✅ **Easy to extend** - Add DIDs or services without duplication  
✅ **Type-safe** - Clear callback interfaces  
✅ **Future-proof** - Ready for Service 0x2F  
✅ **Well-documented** - Complete guide & examples  

Perfect cho automotive diagnostic systems với multiple DID services! 🚗✨
