# GachBoot ConfigTool

AUTOSAR-style configuration tool for GachBoot project. Generate C/H files from JSON configuration.

## Features

- ✅ JSON-based configuration (like AUTOSAR ARXML)
- ✅ Auto-generate NVM block descriptors
- ✅ Auto-generate DID registry with callbacks
- ✅ Type-safe configuration with JSON schema validation
- ✅ Version control friendly (JSON diff)
- 🚧 GUI editor (future)

## Directory Structure

```
ConfigTool/
├── config_schema.json              # JSON schema definition
├── gachboot_config.json            # Main configuration file
├── code_generator.py               # Code generator script
├── config_editor.py                # GUI editor (future)
└── README.md                       # This file
```

## Usage

### Option 1: GUI Editor (Recommended)

```bash
cd Tool/ConfigTool
python config_editor.py
```

**Features:**
- 🖥️ User-friendly Tkinter interface
- ✏️ Add/Edit/Delete NVM blocks and DIDs
- ✅ Real-time validation
- 💾 Save/Load configurations
- 🚀 One-click code generation

### Option 2: Manual Edit

Edit `gachboot_config.json`:

```json
{
  "project": {
    "name": "GachBoot",
    "version": "1.0.0",
    "generated_path": "../../service/svc_dcm/generated"
  },
  "nvm_blocks": [
    {
      "block_id": 0,
      "block_name": "NVM_BLOCK_VIN",
      "data_length": 4,
      "default_value": [0x11, 0x22, 0x33, 0x44],
      "description": "Vehicle Identification Number"
    }
  ],
  "dids": [
    {
      "did": "0xF190",
      "did_name": "DID_VIN",
      "description": "Vehicle Identification Number",
      "data_type": "NVM",
      "nvm_block_id": 0,
      "data_length": 4,
      "read_access": true,
      "write_access": true,
      "session_required": ["DEFAULT", "EXTENDED_DIAGNOSTIC"],
      "security_level": 0
    }
  ]
}
```

### 2. Generate Code

```bash
cd Tool/ConfigTool
python code_generator.py gachboot_config.json
```

### 3. Generated Files

Output in `service/svc_dcm/generated/`:
- `dev_nvm_config_generated.h` - NVM block configuration
- `uds_did_registry_generated.c` - DID registry table
- `uds_did_callbacks_generated.h` - Callback declarations
- `uds_did_callbacks_generated.c` - Callback implementations

### 4. Integration

Include generated files in your CMakeLists.txt:

```cmake
target_sources(${PROJECT_NAME} PRIVATE
    service/svc_dcm/generated/uds_did_registry_generated.c
    service/svc_dcm/generated/uds_did_callbacks_generated.c
)
```

## Configuration Options

### NVM Block

| Field | Type | Description |
|-------|------|-------------|
| `block_id` | integer | Unique block identifier |
| `block_name` | string | Uppercase block name |
| `data_length` | integer | Data size in bytes |
| `default_value` | array | Default data (hex) |
| `description` | string | Human-readable description |

### DID Entry

| Field | Type | Description |
|-------|------|-------------|
| `did` | string | DID identifier (e.g., "0xF190") |
| `did_name` | string | Constant name |
| `description` | string | Human-readable description |
| `data_type` | enum | STATIC/NVM/DYNAMIC |
| `nvm_block_id` | integer | NVM block reference (if data_type=NVM) |
| `data_length` | integer | Data size in bytes |
| `read_access` | boolean | Enable 0x22 ReadDataByID |
| `write_access` | boolean | Enable 0x2E WriteDataByID |
| `session_required` | array | Required sessions |
| `security_level` | integer | Required security (0=none) |

## Adding New DID

1. Open `gachboot_config.json`
2. Add entry to `dids` array:

```json
{
  "did": "0xF1A0",
  "did_name": "DID_MY_NEW_DATA",
  "description": "My new diagnostic data",
  "data_type": "NVM",
  "nvm_block_id": 5,
  "data_length": 8,
  "read_access": true,
  "write_access": true,
  "session_required": ["EXTENDED_DIAGNOSTIC"],
  "security_level": 1
}
```

3. Run generator: `python code_generator.py`
4. Rebuild project

## GUI Screenshots

**Main Window:**
- Project info (name, version, output path)
- NVM Blocks tab with treeview
- DIDs tab with detailed info
- Toolbar: Add/Edit/Delete operations
- Menu: File, Generate, Help

**Dialogs:**
- NVM Block Editor: ID, name, length, default values, description
- DID Editor: DID, name, type, NVM mapping, access control, sessions

## Future Enhancements

- [x] GUI editor (Tkinter)
- [ ] JSON schema validation with jsonschema library
- [ ] Import/Export from ARXML
- [ ] Code diff preview
- [ ] Undo/Redo support
- [ ] Multi-language support

## License

Part of GachBoot project.
