# Copilot Instructions - GachBoot Project

## Project Overview
This is an automotive bootloader project implementing UDS (Unified Diagnostic Services) protocol based on ISO 14229-1 standard for STM32H743 microcontroller. The architecture follows AUTOSAR DCM (Diagnostic Communication Manager) layered approach.

## Code Style & Naming Conventions

### General Rules
- **Language**: C (C99 standard)
- **Line Length**: Maximum 120 characters
- **Indentation**: 4 spaces (no tabs)
- **Braces**: K&R style (opening brace on same line for functions/control structures)
- **Comments**: Use `//` for single-line, `/* */` for multi-line documentation
- **CRITICAL**: DO NOT create example files (e.g., *_example.c, *_example.json) unless explicitly requested by the user
  - Update existing files or documentation instead
  - Only create example files when user specifically asks for examples

### Naming Conventions

#### Variables
- **Local variables**: `snake_case`
  ```c
  uint8_t request_buffer[256];
  uint16_t response_len = 0;
  ```
- **Global/Static variables**: `snake_case` with descriptive prefix
  ```c
  static dcmdsd_pending_state_t pending_state = {0};
  static const uds_did_entry_t did_registry[] = {...};
  ```
- **Pointer variables**: Suffix with `_p` for pointers
  ```c
  dev_com_tp_sdu_t *sdu_info_p;
  const uint8_t *data_p;
  ```

#### Functions
- **Public API functions**: `module_action_object` pattern
  ```c
  dev_err_t dcmdsd_process_request(dev_com_tp_sdu_t *sdu_info_p);
  Std_ReturnType uds_service_0x22_handler(const uds_message_t *message, uint8_t *error_code);
  ```
- **Private/Static functions**: Same pattern but with `static` keyword
  ```c
  static Std_ReturnType did_read_vin(uint8_t *data);
  static void process_pending_internal(void);
  ```
- **Callback functions**: `module_callback_purpose` pattern
  ```c
  static Std_ReturnType security_compare_key_level_1(uint8_t level, const uint8_t *key, const uint8_t *seed);
  ```

#### Constants & Macros
- **Macros**: `UPPER_CASE_WITH_UNDERSCORES`
  ```c
  #define UDS_NRC_SERVICE_NOT_SUPPORTED    0x11
  #define DCMDSD_MAX_PENDING_NRC78_COUNT   15u
  ```
- **Configuration macros**: Prefix with module name
  ```c
  #define SVC_DCM_CONFIG_USE_RTOS          1
  #define DCMDSD_PENDING_CALLBACK_RETRY_MS 10u
  ```
- **Bitmask macros**: Use `(1u << n)` pattern
  ```c
  #define UDS_SESSION_MASK_DEFAULT      (1u << 0)   // 0x00000001
  #define UDS_SECURITY_MASK_LEVEL_1     (1u << 1)   // 0x00000002
  ```

#### Types
- **Typedefs**: `snake_case_t` suffix
  ```c
  typedef struct {
      uint16_t did;
      uds_did_read_callback_t read_callback;
  } uds_did_entry_t;
  
  typedef Std_ReturnType (*uds_did_read_callback_t)(uint8_t *data);
  ```
- **Enums**: `UPPER_CASE` for values, `snake_case_t` for type
  ```c
  typedef enum {
      SECURITY_STATE_LOCKED = 0,
      SECURITY_STATE_SEED_REQUESTED,
      SECURITY_STATE_UNLOCKED
  } security_state_t;
  ```

#### Files
- **Source files**: `module_submodule.c` pattern
  ```
  uds_service_0x22.c
  uds_rdbi_did_registry.c
  dcmdsp.c
  ```
- **Header files**: Matching `.h` with include guards
  ```c
  #ifndef UDS_SERVICE_0X22_H
  #define UDS_SERVICE_0X22_H
  // ... content
  #endif // UDS_SERVICE_0X22_H
  ```

### Logging
- **CRITICAL RULE**: NEVER use raw `dev_log()` or `dev_log_hex()` functions directly
- **ALWAYS** use the logging macros defined in `dev_common.h` for all logging operations
- **APPLIES TO**: All C source files (`.c`), including:
  - Component modules (`dev_*`, `svc_*`)
  - Generated code from ConfigTool
  - UDS service handlers
  - Application code
  - Test code
- Use `CONFIG_LOG_TAG` macro at the top of each `.c` file (after includes):
  ```c
  #include "dev_common.h"
  
  CONFIG_LOG_TAG(MODULE_NAME, true)  // Enable/disable logging per module
  ```
- **Required Logging Macros**:
  ```c
  DBG_OUT_I("Info message: %d", value);      // Information (green)
  DBG_OUT_W("Warning: 0x%02X", code);        // Warning (yellow)
  DBG_OUT_E("Error: %s", error_msg);         // Error (red)
  DBG_OUT("Debug: state=%d", state);         // Generic debug with tag
  DBG_OUT_RAW("Raw text");                   // Raw output (no formatting)
  DBG_OUT_HEX(data, length);                 // Hex dump of data buffer
  ```
- **Benefits of using macros**:
  - Automatic module tagging (shows file name and line number)
  - Color coding for log levels
  - Centralized enable/disable via `CONFIG_LOG_TAG` 
  - Compile-time removal when `CONFIG_LOG_DEFAULT_LEVEL_NONE` is defined
- **Do NOT** include module name or "[MODULE]" prefix in log messages - macros handle this automatically
- **Do NOT** include `\n` newline characters - macros add them automatically
- **Example** (WRONG vs CORRECT):
  ```c
  // ❌ WRONG - Do not use raw dev_log
  dev_log("[FLASHBLOCK] ERROR: Invalid address 0x%08X\n", addr);
  
  // ❌ WRONG - Redundant module tag and manual newline
  DBG_OUT_E("[QUEUE] Error: Invalid size\n");
  
  // ✅ CORRECT - Use DBG_OUT_E macro (no manual newlines or tags)
  DBG_OUT_E("Invalid address 0x%08X", addr);
  
  // ✅ CORRECT - Clean message without redundant info
  DBG_OUT_I("Queue initialized - capacity=%u", capacity);
  ```

## Architecture Patterns

### UDS Service Structure
Each UDS service follows this pattern:

1. **Service Folder Structure**:
   ```
   uds_services/
   └── service_0xXX/
       ├── uds_service_0xXX.h       // Handler declaration
       ├── uds_service_0xXX.c       // Handler implementation
       └── uds_XX_config.h/.c       // Optional: Service-specific config/registry
   ```

2. **Handler Function Signature** (Standardized):
   ```c
   Std_ReturnType uds_service_0xXX_handler(const uds_message_t *message, uint8_t *error_code)
   ```
   - **Returns**:
     - `E_OK`: Success (DCMDSP adds positive SID automatically)
     - `E_NOT_OK`: Error (DCMDSP builds negative response with error_code)
     - `DCM_E_PENDING`: Operation pending (DCMDSP sends NRC 0x78, retries every 10ms)
   - **Response Building**: Handler fills `message->response` with DATA ONLY (no SID)
     - DCMDSP automatically prepends positive SID (request SID + 0x40)
     - Example: Handler returns `[01 00 32 01 F4]` → Final: `[50 01 00 32 01 F4]`

3. **Processing Phases**:
   ```c
   // Phase 1: Validate request length
   if (message->request_len < min_length) {
       *error_code = UDS_NRC_INCORRECT_MESSAGE_LENGTH;
       return E_NOT_OK;
   }
   
   // Phase 2: Check session/security support
   if ((config->session_mask & current_session_mask) == 0) {
       *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
       return E_NOT_OK;
   }
   
   // Phase 3: Process service-specific logic
   // ...
   
   // Phase 4: Build positive response (data only)
   message->response[0] = sub_function;
   *(message->response_len) = data_length;
   return E_OK;
   ```

### Registry/Configuration Pattern
For services with multiple identifiers (DIDs, RIDs, Security Levels), use **callback registry**:

```c
// 1. Define callback type
typedef Std_ReturnType (*uds_did_read_callback_t)(uint8_t *data);

// 2. Define entry structure
typedef struct {
    uint16_t did;                           // Identifier
    uint16_t expected_length;               // Data length
    uds_did_read_callback_t read_callback;  // Callback
    uint32_t session_mask;                  // Session support bitmask
    uint32_t security_mask;                 // Security support bitmask
} uds_did_entry_t;

// 3. Create registry array
static const uds_did_entry_t did_registry[] = {
    {0xF190, 17, did_read_vin, NULL, UDS_SESSION_MASK_ALL, UDS_SECURITY_MASK_ALL},
    // ... more entries
};

// 4. Implement lookup function
const uds_did_entry_t* uds_rdbi_find_did(uint16_t did) {
    for (uint16_t i = 0; i < REGISTRY_SIZE; i++) {
        if (registry[i].did == did) return &registry[i];
    }
    return NULL;
}
```

**Callback Implementation Rules**:
- Callbacks receive **validated data only** (no DID parameter needed)
- Service handler performs ALL validation (length, session, security)
- Callbacks focus ONLY on business logic
- Return `DCM_E_PENDING` for async operations (e.g., Flash read)
- Example:
  ```c
  static Std_ReturnType did_read_vin(uint8_t *data) {
      // Service handler guarantees buffer has 17 bytes available
      memcpy(data, vin_string, 17);
      return E_OK;
  }
  ```

### Pending Request Handling
- **Callback retry**: Every 10ms (fast check for completion)
- **NRC 0x78 transmission**: Every 5 seconds (avoid tester spam)
- **Max retries**: 15 NRC 0x78 before sending NRC 0x10
- **Busy protection**: Reject new requests with NRC 0x21 when pending

### AUTOSAR-like Types
```c
typedef uint8_t Std_ReturnType;
#define E_OK        0x00u
#define E_NOT_OK    0x01u
#define DCM_E_PENDING  0x10u
```

## Error Handling

### Return Value Pattern
```c
// Use AUTOSAR return types for service handlers
Std_ReturnType result = process_data();
if (result != E_OK) {
    *error_code = UDS_NRC_CONDITIONS_NOT_CORRECT;
    return E_NOT_OK;
}

// Use dev_err_t for application layer
dev_err_t err = dcmdsd_init();
DEV_RETURN_ON_FALSE(err == DEV_OK, err, "Initialization failed");
```

### Error Macros
```c
DEV_RETURN_ON_FALSE(condition, ret_val, "Error message");
DEV_RETURN_ON_NULL(ptr, DEV_ERR_INVALID_ARG, "Null pointer");
```

## Memory Management

### Buffer Handling
- Use **stack buffers** for temporary data (< 256 bytes)
- Avoid dynamic allocation in embedded context
- Always validate buffer sizes before operations
- Example:
  ```c
  uint8_t response_buffer[256];  // Max UDS message size
  uint16_t response_len = 0;
  ```

### Structure Initialization
```c
// Zero-initialize structures
static dcmdsd_pending_state_t pending_state = {0};
memset(&pending_state, 0, sizeof(pending_state));

// Array initialization
static const uds_did_entry_t registry[] = {
    {0xF190, 17, did_read_vin, NULL, UDS_SESSION_MASK_ALL, UDS_SECURITY_MASK_ALL},
};
```

## Documentation

### Function Documentation
```c
/**
 * @brief Brief description of function purpose
 * @param param1 Description of parameter 1
 * @param param2 Description of parameter 2
 * @return Return value description
 */
Std_ReturnType function_name(type param1, type param2);
```

### File Header
```c
/**
 * @file filename.c
 * @brief Brief description of file purpose
 */
```

### Inline Comments
- Use inline comments for complex logic
- Explain WHY, not WHAT (code should be self-documenting)
- Comment phases in service handlers
```c
// Phase 1: Validate request length
// Phase 2: Check session/security support
// Phase 3: Process service logic
```

## Testing & Debugging

### Test Patterns
- Use static counters for pending simulation:
  ```c
  static uint8_t test_counter = 0;
  if (test_counter < 5) {
      test_counter++;
      return DCM_E_PENDING;
  }
  ```

### Debug Output
- Add descriptive logs at key points
- Include hex values for protocol data
- Log timing information for pending operations
```c
DBG_OUT_I("Service 0x%02X pending - sending NRC 0x78 (%d/%d)", 
          service_id, nrc78_count, max_count);
```

## Project-Specific Rules

### DCM Layer Responsibilities
1. **DCMDSL (Session Layer)**: Session management, S3 timeout, timing parameters
2. **DCMDSD (Dispatcher)**: Request routing, pending management, response building
3. **DCMDSP (Service Processing)**: Service handler dispatch, positive SID injection

### UDS Message Flow
```
Request → DCMDSD → DCMDSP → Service Handler → Callback
                                              ↓
Response ← DCMDSD ← DCMDSP ← (add +0x40 SID) ← Data only
```

### Security & Session Masks
- Use `uint32_t` bitmasks for session/security requirements
- Check support: `if ((entry->session_mask & current_session_mask) == 0)`
- Combine masks: `UDS_SESSION_MASK_PROGRAMMING | UDS_SESSION_MASK_EXTENDED`

### Timing Constants
```c
#define DCMDSD_PENDING_CALLBACK_RETRY_MS  10u    // Fast callback retry
#define DCMDSD_PENDING_NRC78_INTERVAL_MS  5000u  // Slow NRC 0x78 transmission
#define DCMDSD_MAX_PENDING_NRC78_COUNT    15u    // Max retries before timeout
```

## Build System
- CMake-based build
- Uses `file(GLOB_RECURSE)` for automatic source discovery
- Service folders auto-included via `uds_services/**/*.c` pattern

## Common Pitfalls to Avoid
1. **DO NOT** add positive response SID in service handlers (DCMDSP does this)
2. **DO NOT** validate in callbacks (service handler validates)
3. **DO NOT** use long delays in callbacks (return `DCM_E_PENDING` instead)
4. **DO NOT** forget to update `nrc78_count` when sending NRC 0x78
5. **DO NOT** mix `dev_err_t` and `Std_ReturnType` inappropriately
6. **DO NOT** use autosave in complex dynamic UIs (causes race conditions)
7. **DO NOT** recreate UI widgets dynamically (use grid_remove()/grid() instead)
8. **DO NOT** add fields to generated structs without updating library interface
9. **DO NOT** add Save buttons in ConfigTool GUI forms - use FocusOut/Enter events to auto-save instead
10. **DO NOT** manually create or edit files in `GenerateCode/` folder - use ConfigTool to generate them
11. **DO NOT** hardcode configuration values in component modules - use generated `*_PBCfg.h` files instead

---

## ConfigTool Code Generation Best Practices

### When Generating C Code from Python

**1. Match Library Interface First**
- Reference existing library headers before designing generator
- Copy exact struct definitions from library
- Don't add fields unless library code also updated
- Test compilation after every generator change

Example:
```python
# routine_module.py
# NOTE: This struct MUST match uds_routine_entry_t in:
#       service/svc_dcm/uds_services/service_0x31/uds_routine_control_registry.h
typedef_code = """
typedef struct {
    uint16_t rid;                    /* MUST match library */
    uds_routine_callback_t callback; /* MUST match library */
    uint32_t session_mask;           /* MUST match library */
    uint32_t security_mask;          /* MUST match library */
} uds_routine_entry_t;
"""
```

**2. Use Raw Strings for C Code Templates**
```python
# Fixed C code without placeholders - use raw string
code = """
void function(void) {
    printf("test");
}
"""

# With placeholders - use f-string, escape braces around non-placeholders
code = f"""
void {func_name}(void) {{  // {{ for literal {{
    {function_body}
}}  // }} for literal }}
"""
```

**3. Wrapper Pattern for Callback Dispatch**

When library expects generic callback but per-case callbacks are cleaner:

```python
# Generate per-case callback declarations
for case in cases:
    header += f"extern Std_ReturnType {base_name}_{case.lower()}(...);\n"

# Generate wrapper dispatch function
source += f"""
static Std_ReturnType {base_name}(uint8_t type, ...) {{
    switch (type) {{
"""
for case in cases:
    source += f"""
        case {case}_TYPE:
            return {base_name}_{case.lower()}(...);
"""
source += """
        default:
            return E_NOT_OK;
    }
}
"""

# Registry points to wrapper
source += f"""
    .callback = {base_name},  // Wrapper, not user function
"""
```

**Benefits:**
- User implements focused functions without switch-case
- Wrapper handles validation and routing
- Library interface preserved
- Zero runtime overhead

**4. Per-Config Parameter Pattern**

For entities with sub-types needing different parameters:

```json
{
  "routines": [{
    "rid": "0xFF00",
    "name": "ERASE_MEMORY",
    "supported_subfunctions": ["START", "STOP"],
    "subfunction_parameters": {
      "START": {
        "option_length": 8,
        "option_description": "Address + Length",
        "status_length": 1,
        "status_description": "Status byte"
      },
      "STOP": {
        "option_length": 0,
        "option_description": "No parameters",
        "status_length": 1,
        "status_description": "Status byte"
      }
    }
  }]
}
```

Code generation validates per-subfunction:
```c
if (option_record_len != subfunction_params[subfunc].option_length) {
    return E_NOT_OK;
}
```

---

## UI Development Best Practices

### Dynamic Forms with Conditional Sections

**1. Create All UI Elements Upfront**

❌ **WRONG** - Conditional creation:
```python
if feature_enabled:
    create_feature_ui()  # Can't show later if user enables
```

✅ **CORRECT** - Create all, hide unused:
```python
# Create frames for all possible sections
for section in all_sections:
    section_frame = ttk.Frame(parent)
    section_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E))
    section_frames[section] = section_frame
    
    # Create all widgets inside frame
    ttk.Label(section_frame, text=f"{section}:").grid(...)
    ttk.Entry(section_frame, textvariable=section_vars[section]).grid(...)
    
    # Hide if not currently enabled
    if section not in enabled_sections:
        section_frame.grid_remove()  # Hide but keep grid config
```

**2. Toggle Visibility, Don't Destroy/Recreate**

```python
def toggle_section(section):
    """Show/hide section UI based on checkbox"""
    if enabled_vars[section].get():
        section_frames[section].grid()  # Restore to previous position
    else:
        section_frames[section].grid_remove()  # Hide without destroying

# Bind to checkbox (visibility toggle, NOT save)
for section in all_sections:
    enabled_vars[section].trace_add('write', 
        lambda *args, s=section: toggle_section(s))
```

**Why grid_remove()?**
- Preserves grid configuration (row, column, sticky, etc.)
- Fast show/hide without re-layout calculations
- Preserves user input if they toggle back
- No memory allocation/deallocation

**3. Avoid Autosave for Dynamic UIs**

❌ **WRONG** - Autosave on every change:
```python
# Trace callbacks fire immediately, cause race conditions
for var in all_vars.values():
    var.trace_add('write', save_callback)  # ❌ Fires during init!

def save_callback(*args):
    # May execute before UI fully initialized
    # May try to access widgets that don't exist yet
    selected = [s for s, v in section_vars.items() if v.get()]
    for s in selected:
        params = section_params[s]  # ❌ KeyError if s just enabled!
```

✅ **CORRECT** - Manual save at defined points:
```python
# No trace callbacks for save

def save_changes():
    """Explicit save - called when closing/generating/validating"""
    try:
        # All vars guaranteed to exist
        selected = [s for s, v in section_vars.items() if v.get()]
        
        for s in selected:
            if s not in section_params:
                # Provide defaults for newly enabled sections
                section_params[s] = get_default_params(s)
            else:
                # Save actual values
                section_params[s] = {
                    'param1': section_vars[s]['param1'].get(),
                    'param2': section_vars[s]['param2'].get(),
                }
        
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Save failed: {e}")
        return False

# Store save function for external access
form_frame.save_changes = save_changes

# Call save before validation/generation
def generate_code():
    save_current_form()  # Find and call save_changes() on active form
    validate_config()
    generate()
```

**When to Save:**
- Form close
- Generate/Validate buttons clicked
- Navigate away from form
- User explicitly clicks Save button

**Benefits:**
- No race conditions
- Predictable control flow
- Form fully initialized before save
- Easier debugging (no hidden callbacks)

**4. Canvas Layout for Scrollable Forms**

```python
# Create canvas WITHOUT fixed width
canvas = tk.Canvas(config_panel_frame)  # ❌ Don't: width=800
scrollbar = ttk.Scrollbar(config_panel_frame, orient=tk.VERTICAL, 
                          command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

# Pack scrollbar first (right side)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
# Pack canvas to fill remaining space
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create form frame inside canvas
form_frame = ttk.Frame(canvas)
canvas_frame = canvas.create_window((0, 0), window=form_frame, anchor=tk.NW)

# Update scroll region when form size changes
def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

# Resize form to canvas width when canvas resizes
def on_canvas_configure(event):
    canvas.itemconfig(canvas_frame, width=event.width)

form_frame.bind('<Configure>', on_frame_configure)
canvas.bind('<Configure>', on_canvas_configure)

# Initial update
form_frame.update_idletasks()
canvas.configure(scrollregion=canvas.bbox("all"))

# Mouse wheel scrolling
def on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)
```

**Key Points:**
- No fixed canvas width (let it expand with window)
- `on_canvas_configure` updates form width to match canvas
- `on_frame_configure` updates scroll region when form content changes
- Initial update needed to set correct scrollregion

---

## ConfigTool Architecture Patterns

### Module Structure

Every configuration module follows this pattern:

```
Tool/ConfigTool/
├── Module/
│   └── {name}_module.py          # Validation + Code generation
│       ├── validate_{name}_config()
│       ├── generate_{name}_header()
│       ├── generate_{name}_source()
│       └── generate_{name}_code()
│
├── Module_UI/
│   └── {name}_ui.py               # UI components
│       ├── {Name}UI class
│       ├── setup_tab()            # TreeView + toolbar
│       ├── show_edit_form()       # Edit form in config panel
│       └── show_info_panel()      # Info display in info panel
│
├── config_editor.py               # Main GUI
│   ├── setup_{name}_tab()
│   ├── show_{name}_edit_form()
│   ├── add_{name}()
│   ├── edit_{name}()
│   └── delete_{name}()
│
└── gachboot_config.json           # Configuration data
    └── "{name}s": [...]
```

### Generator Function Pattern

```python
def generate_{module}_code(config_data: Dict, output_dir: str) -> Tuple[bool, List[str]]:
    """
    Generate C code for {module}.
    
    Args:
        config_data: Full configuration dict
        output_dir: Base output directory (usually "GenerateCode/")
    
    Returns:
        (success: bool, messages: List[str])
    """
    # 1. Extract module config
    items = config_data.get('{module}s', [])
    
    # 2. Validate
    valid, errors = validate_{module}_config(items)
    if not valid:
        return False, errors
    
    # 3. Create output directory
    module_dir = os.path.join(output_dir, '{Module}_Gen')
    os.makedirs(module_dir, exist_ok=True)
    
    # 4. Generate header
    header_content = generate_{module}_header(items)
    header_path = os.path.join(module_dir, '{Module}_PBCfg.h')
    with open(header_path, 'w', encoding='utf-8') as f:
        f.write(header_content)
    
    # 5. Generate source
    source_content = generate_{module}_source(items, other_tables)
    source_path = os.path.join(module_dir, '{Module}_PBCfg.c')
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(source_content)
    
    # 6. Return success messages
    return True, [
        f"Generated: {header_path}",
        f"Generated: {source_path}",
        f"Total {module}s: {len(items)}"
    ]
```

### Validation Pattern

```python
class {Module}Validator:
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_{module}_config(self, items: List[Dict]) -> Tuple[bool, List[str], List[str]]:
        """Validate all items"""
        self.errors = []
        self.warnings = []
        
        # Check empty
        if not items:
            self.warnings.append("No {module}s configured")
            return True, [], self.warnings
        
        # Validate each item
        for i, item in enumerate(items):
            self._validate_item(i, item)
        
        # Check for duplicates
        self._check_duplicates(items)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_item(self, index: int, item: Dict):
        """Validate single item"""
        # Required fields
        required = ['id', 'name', 'type']
        for field in required:
            if field not in item:
                self.errors.append(f"Item [{index}]: Missing '{field}'")
        
        # Value validation
        if 'id' in item:
            if not isinstance(item['id'], int) or item['id'] < 0:
                self.errors.append(f"Item [{index}]: Invalid ID")
        
        # ... more validation
    
    def _check_duplicates(self, items: List[Dict]):
        """Check for duplicate IDs"""
        seen_ids = set()
        for i, item in enumerate(items):
            id_val = item.get('id')
            if id_val in seen_ids:
                self.errors.append(f"Item [{i}]: Duplicate ID {id_val}")
            seen_ids.add(id_val)

# Export function for import
def validate_{module}_config(items):
    validator = {Module}Validator()
    return validator.validate_{module}_config(items)
```

---

## Common Pitfalls to Avoid (Updated)

## CMake Build System Patterns

### Component Module Structure (dev_*)

All `components/dev_*` modules follow this pattern:

```
components/
└── dev_{module}/
    ├── CMakeLists.txt
    ├── dev_{module}.c
    └── include/
        └── dev_{module}.h
```

**CMakeLists.txt Template** (Simple Module - Standard Pattern):
```cmake
# Automatically find all .c files in the current directory
file(GLOB DEV_{MODULE}_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_{module} library
add_library(dev_{module} STATIC ${DEV_{MODULE}_SOURCES})

# Add include directories for dev_{module}
target_include_directories(dev_{module} PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_{module} PUBLIC stm32cubemx)
target_link_libraries(dev_{module} PUBLIC dev_app)
```

**Add GenerateCode dependency if module uses generated config:**
```cmake
# Only add this line if module needs *_PBCfg.h files
target_link_libraries(dev_{module} PUBLIC GenerateCode)
```

**Add cross-module dependencies:**
```cmake
# Example: dev_flashblock needs dev_fls
target_link_libraries(dev_{module} PUBLIC dev_fls)
```

**Complete Example (dev_flashblock):**
```cmake
# Automatically find all .c files in the current directory
file(GLOB DEV_FLASHBLOCK_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_flashblock library
add_library(dev_flashblock STATIC ${DEV_FLASHBLOCK_SOURCES})

# Add include directories for dev_flashblock
target_include_directories(dev_flashblock PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_flashblock PUBLIC stm32cubemx)
target_link_libraries(dev_flashblock PUBLIC dev_app)
target_link_libraries(dev_flashblock PUBLIC GenerateCode)  # For Fls_PBCfg.h
target_link_libraries(dev_flashblock PUBLIC dev_fls)       # For dev_fls API
```

**CMakeLists.txt Template** (Multi-Layer Module - e.g., dev_memstack):
```cmake
# Add all sub-layers
add_subdirectory(dev_fls)    # Bottom layer
add_subdirectory(dev_fee)    # Middle layer
add_subdirectory(dev_memif)  # Abstraction layer
add_subdirectory(dev_nvm)    # Top layer

# Create a combined library (INTERFACE for header-only aggregation)
add_library(dev_memstack INTERFACE)

# Link all layers in correct dependency order
target_link_libraries(dev_memstack INTERFACE
    dev_fls
    dev_fee
    dev_memif
    dev_nvm
)

# Expose include directories from all layers
target_include_directories(dev_memstack INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_fls/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_fee/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_memif/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_nvm/include
)
```

### Dependency Rules (Link Order Matters)

**Step 1: Core Dependencies (Always Required):**
```cmake
target_link_libraries(dev_{module} PUBLIC stm32cubemx)  # HAL drivers, CMSIS
target_link_libraries(dev_{module} PUBLIC dev_app)      # dev_log, dev_delay, dev_common
```

**Step 2: Generated Code Dependency (If Needed):**
```cmake
# Only add if module uses *_PBCfg.h files from ConfigTool
target_link_libraries(dev_{module} PUBLIC GenerateCode)
```

**Step 3: Cross-Module Dependencies (If Needed):**
```cmake
# Add other dev_* modules that this module depends on
target_link_libraries(dev_{module} PUBLIC dev_fls)
target_link_libraries(dev_{module} PUBLIC dev_memstack)
```

**Common Dependency Patterns:**

| Module Type | Dependencies |
|-------------|--------------|
| Basic module (dev_crc, dev_com) | `stm32cubemx` + `dev_app` |
| Uses generated config (dev_fls, dev_fee, dev_nvm) | `stm32cubemx` + `dev_app` + `GenerateCode` |
| Uses other modules (dev_flashblock) | `stm32cubemx` + `dev_app` + `GenerateCode` + `dev_fls` |
| Transport layer (dev_com_tp) | `stm32cubemx` + `dev_app` + `dev_com` + `dev_com_if` |

**Avoid:**
- ❌ Combining multiple `target_link_libraries()` into one line (use separate lines for clarity)
- ❌ Circular dependencies (A depends on B, B depends on A)
- ❌ Forgetting `PUBLIC` keyword (makes includes unavailable to dependents)

### Include File Patterns

**When Using Generated Config:**
```c
// In dev_{module}.c
#include "dev_{module}.h"
#include "dev_fls.h"
#include "dev_log.h"
#include "Fls_PBCfg.h"      // From GenerateCode - needs GenerateCode link
#include <string.h>
```

**Accessing Generated Config Structs:**
```c
// In dev_{module}.c

// Method 1: Use extern declaration (recommended)
extern const dev_fls_config_t dev_fls_config;  // Defined in Fls_PBCfg.c

// Then access directly:
for (uint32_t i = 0; i < dev_fls_config.num_sectors; i++) {
    uint32_t sector_addr = dev_fls_config.sectors[i].address;
}

// Method 2: Avoid - don't copy or cache large config structs
```

### Root CMakeLists.txt Integration

**Add Component to Build:**
```cmake
# In root CMakeLists.txt

# 1. Add subdirectory (alphabetical order)
add_subdirectory(components/dev_app)
add_subdirectory(components/dev_com)
add_subdirectory(components/dev_flashblock)  # <-- Add here
add_subdirectory(components/dev_memstack)

# 2. Link to main executable
target_link_libraries(${CMAKE_PROJECT_NAME}
    stm32cubemx
    dev_app
    dev_com
    dev_flashblock  # <-- Add here
    dev_memstack
    GenerateCode
    svc_app
    svc_dcm
)
```

### Common CMake Build Errors

**Error 1: Undefined reference to `dev_fls_config`**
- **Cause**: Missing `GenerateCode` link or missing `#include "Fls_PBCfg.h"`
- **Fix**: Add `target_link_libraries(dev_{module} PUBLIC GenerateCode)`

**Error 2: Cannot find `dev_log.h`**
- **Cause**: Missing `dev_app` link
- **Fix**: Add `target_link_libraries(dev_{module} PUBLIC dev_app)`

**Error 3: Multiple definition of `dev_{module}_init`**
- **Cause**: `.c` file added to multiple libraries or included in header
- **Fix**: Use `STATIC` library type, ensure `.c` only in one `add_library()`

**Error 4: Circular dependency detected**
- **Cause**: A depends on B, B depends on A
- **Fix**: Refactor to extract common interface into third module

**Error 5: Header not found in subdirectory**
- **Cause**: Missing `target_include_directories(... PUBLIC include)`
- **Fix**: All modules must expose their `include/` directory publicly

### ConfigTool Code Generation Integration

**Generated CMakeLists.txt Pattern:**
```cmake
# GenerateCode/CMakeLists.txt

# Automatically find all generated .c files
file(GLOB_RECURSE GENERATED_SOURCES 
    "${CMAKE_CURRENT_SOURCE_DIR}/**/*.c"
)

# Create library for generated code
add_library(GenerateCode STATIC ${GENERATED_SOURCES})

# Expose all generated include directories
target_include_directories(GenerateCode PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/Fls_Gen
    ${CMAKE_CURRENT_SOURCE_DIR}/Fee_Gen
    ${CMAKE_CURRENT_SOURCE_DIR}/NvM_Gen
    ${CMAKE_CURRENT_SOURCE_DIR}/DID_Gen
    ${CMAKE_CURRENT_SOURCE_DIR}/Service_Gen
    ${CMAKE_CURRENT_SOURCE_DIR}/Routine_Gen
    ${CMAKE_CURRENT_SOURCE_DIR}/Security_Gen
    ${CMAKE_CURRENT_SOURCE_DIR}/DCM_Session_Gen
)

# Link to dependencies
target_link_libraries(GenerateCode PUBLIC
    stm32cubemx
    dev_app  # For dev_log used in callbacks
)
```

**Naming Convention for Generated Files:**

**CRITICAL RULE: All generated modules MUST follow this naming pattern:**

| Module | Folder | Header | Source |
|--------|--------|--------|--------|
| Flash | `Fls_Gen/` | `Fls_PBCfg.h` | `Fls_PBCfg.c` |
| Fee | `Fee_Gen/` | `Fee_PBCfg.h` | `Fee_PBCfg.c` |
| NvM | `NvM_Gen/` | `NvM_PBCfg.h` | `NvM_PBCfg.c` |
| DID | `DID_Gen/` | `DID_PBCfg.h` | `DID_PBCfg.c` |
| Routine | `Routine_Gen/` | `Routine_PBCfg.h` | `Routine_PBCfg.c` |
| Security | `Security_Gen/` | `Security_PBCfg.h` | `Security_PBCfg.c` |
| Service | `Service_Gen/` | `Service_PBCfg.h` | `Service_PBCfg.c` |
| DCM Session | `DCM_Session_Gen/` | `DCM_Session_PBCfg.h` | `DCM_Session_PBCfg.c` |
| Memory Layout | `Memory_Layout_Gen/` | `Memory_Layout_Config.h` | (header-only) |
| **OS** | `Os_Gen/` | `Os_PBCfg.h` | `Os_PBCfg.c` |

**Pattern:**
- Folder: `{ModuleName}_Gen/`
- Header: `{ModuleName}_PBCfg.h`
- Source: `{ModuleName}_PBCfg.c`

**DO NOT:**
- ❌ Put generated files in root `GenerateCode/` folder
- ❌ Use `dev_*_config.h` naming (wrong pattern)
- ❌ Skip creating subfolder for any module

**Directory Structure:**
```
GenerateCode/
├── Fls_Gen/
│   ├── Fls_PBCfg.h        # Config header
│   └── Fls_PBCfg.c        # Config implementation
├── Fee_Gen/
│   ├── Fee_PBCfg.h
│   └── Fee_PBCfg.c
├── NvM_Gen/
│   ├── NvM_PBCfg.h
│   └── NvM_PBCfg.c
├── Os_Gen/
│   ├── Os_PBCfg.h         # OS task configuration
│   └── Os_PBCfg.c         # OS task registration
└── ... (other modules)
```

**Config Struct Pattern:**
```c
// In {Module}_PBCfg.h
typedef struct {
    // Module-specific config fields
} dev_{module}_config_t;

// Export config instance (defined in .c)
extern const dev_{module}_config_t dev_{module}_config;
```

```c
// In {Module}_PBCfg.c
const dev_{module}_config_t dev_{module}_config = {
    // Initialized from Python-generated values
};
```

---

## When Adding New Features

### New UDS Service
1. Create `service_0xXX/` folder
2. Implement handler with standard signature
3. Add to service table in `dcmdsp.c`
4. Update CMakeLists.txt (if not using GLOB_RECURSE)

### New DID/RID
1. Add entry to appropriate registry
2. Implement callback (data processing only)
3. Set session/security masks
4. Document expected data length

### New Configuration Parameter
1. Use `#define` in module header
2. Suffix numeric values with `u` (unsigned)
3. Add descriptive comment
4. Document in this file if project-wide

### New Component Module (dev_*)

**Steps:**
1. Create folder structure:
   ```
   components/dev_{module}/
   ├── CMakeLists.txt
   ├── dev_{module}.c
   └── include/
       └── dev_{module}.h
   ```

2. Create CMakeLists.txt (use template above)

3. Add to root CMakeLists.txt:
   ```cmake
   add_subdirectory(components/dev_{module})
   target_link_libraries(${CMAKE_PROJECT_NAME} dev_{module})
   ```

4. Link dependencies:
   - Always: `stm32cubemx`, `dev_app`
   - If using config: `GenerateCode`
   - If using other modules: `dev_xxx`

5. Include necessary headers:
   ```c
   #include "dev_{module}.h"
   #include "dev_log.h"          // From dev_app
   #include "{Module}_PBCfg.h"  // If using generated config
   ```

6. Declare extern for generated config:
   ```c
   extern const dev_{module}_config_t dev_{module}_config;
   ```

---

## ConfigTool CMake Generation Rules

### CRITICAL: Always Generate CMakeLists.txt

**Rule 1: CMake is Required for Every Module**
- ⚠️ **NEVER** skip CMake generation when generating code
- ConfigTool MUST generate `GenerateCode/CMakeLists.txt` to register all *_Gen folders
- Without CMakeLists.txt, generated code won't compile

**Rule 2: Module Registration Pattern**
```cmake
# Each module follows this pattern in CMakeLists.txt:
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/ModuleName_Gen)
    file(GLOB MODULE_GEN_SOURCES 
        "${CMAKE_CURRENT_SOURCE_DIR}/ModuleName_Gen/*.c"
    )
    list(APPEND GENERATED_SOURCES ${MODULE_GEN_SOURCES})
    message(STATUS "Added ModuleName_Gen sources")
endif()
```

**Rule 3: Exclude Circular Dependency Sources**
- Service_PBCfg.c and Routine_PBCfg.c are compiled with svc_dcm module
- Use `list(FILTER)` to exclude them from GenerateCode library:
```cmake
list(FILTER SERVICE_GEN_SOURCES EXCLUDE REGEX "Service_PBCfg\\.c$")
list(FILTER ROUTINE_GEN_SOURCES EXCLUDE REGEX "Routine_PBCfg\\.c$")
```

**Rule 4: Header-Only Modules**
- Memory_Layout_Gen only contains Memory_Layout_Config.h (no .c files)
- Still include directory for headers:
```cmake
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/Memory_Layout_Gen)
    target_include_directories(GenerateCode PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/Memory_Layout_Gen
    )
endif()
```

**Rule 5: OS Module Integration**

When generating OS task configuration, follow this pattern:

```c
// In dev_os_config.h (generated by ConfigTool)

// Include OS header
#include "dev_os.h"

// Declare external task functions (user implements)
extern void hardware_init_task(void);
extern void sensor_read_task(void);
extern void can_process_task(void);
extern void flash_program_task(void);

// Init tasks configuration
#define OS_INIT_TASKS_CONFIG \
    {hardware_init_task},     /* Priority order */ \
    {software_init_task}

// Cyclic tasks configuration (with cycle time)
#define OS_CYCLIC_TASKS_CONFIG \
    {sensor_read_task, DEV_OS_CYCLE_1MS},      /* 1ms */ \
    {can_process_task, DEV_OS_CYCLE_10MS},     /* 10ms */ \
    {diagnostics_task, DEV_OS_CYCLE_100MS},    /* 100ms */ \
    {heartbeat_task, DEV_OS_CYCLE_1000MS}      /* 1000ms */

// Background tasks configuration
#define OS_BG_TASKS_CONFIG \
    {flash_program_task},    /* Run when idle */ \
    {crc_calculate_task}

// Auto-registration helper function
static inline void os_config_register_all_tasks(void) {
    // Register init tasks
    dev_os_task_func_t init_tasks[] = {OS_INIT_TASKS_CONFIG};
    for (uint8_t i = 0; i < sizeof(init_tasks)/sizeof(init_tasks[0]); i++) {
        dev_os_register_init_task(init_tasks[i]);
    }
    
    // Register cyclic tasks
    dev_os_cyclic_task_t cyclic_tasks[] = {{OS_CYCLIC_TASKS_CONFIG}};
    for (uint8_t i = 0; i < sizeof(cyclic_tasks)/sizeof(cyclic_tasks[0]); i++) {
        dev_os_register_cyclic_task(cyclic_tasks[i].func, cyclic_tasks[i].cycle);
    }
    
    // Register background tasks
    dev_os_task_func_t bg_tasks[] = {OS_BG_TASKS_CONFIG};
    for (uint8_t i = 0; i < sizeof(bg_tasks)/sizeof(bg_tasks[0]); i++) {
        dev_os_register_bg_task(bg_tasks[i]);
    }
}
```

**Usage in main.c:**
```c
#include "dev_os.h"
#include "dev_os_config.h"  // Generated config

int main(void) {
    // Initialize hardware
    HAL_Init();
    SystemClock_Config();
    
    // Initialize OS module
    dev_os_init();
    
    // Register all tasks from generated config
    os_config_register_all_tasks();
    
    // Start OS scheduler in main loop
    while (1) {
        dev_os_process_bg_tasks();  // Process background tasks
        __WFI();  // Wait for interrupt (timer tick)
    }
}

// Timer interrupt (1ms tick)
void TIM6_DAC_IRQHandler(void) {
    if (__HAL_TIM_GET_FLAG(&htim6, TIM_FLAG_UPDATE)) {
        __HAL_TIM_CLEAR_FLAG(&htim6, TIM_FLAG_UPDATE);
        dev_os_tick_handler();  // OS tick handler
    }
}
```

**OS Configuration JSON Schema:**
```json
{
  "os_tasks": [
    {
      "task_name": "hardware_init_task",
      "task_type": "init",
      "function_name": "hardware_init_task",
      "enabled": true,
      "description": "Initialize peripherals"
    },
    {
      "task_name": "sensor_read_task",
      "task_type": "cyclic",
      "function_name": "sensor_read_task",
      "cycle_time": 1,
      "enabled": true,
      "description": "Read sensors at 1ms"
    },
    {
      "task_name": "flash_program_task",
      "task_type": "background",
      "function_name": "flash_program_task",
      "enabled": true,
      "description": "Program flash when idle"
    }
  ]
}
```

**Key Points:**
- User implements actual task functions (extern declarations in generated config)
- ConfigTool generates macro tables and registration helper
- Main.c calls `os_config_register_all_tasks()` once at startup
- OS scheduler handles execution based on task type and cycle time
- No manual registration needed - all automated via generated config

---

**Last Updated**: December 27, 2025
**Project**: GachBoot - Automotive Bootloader
**Standard**: ISO 14229-1 (UDS), AUTOSAR DCM Architecture
