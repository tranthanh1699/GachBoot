# 🚀 GachBoot - Professional STM32H743 Bootloader

<div align="center">

![STM32](https://img.shields.io/badge/STM32-H743-blue?logo=stmicroelectronics)
![UDS](https://img.shields.io/badge/UDS-ISO%2014229--1-green)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![License](https://img.shields.io/badge/License-Educational-yellow)

**A modular, production-ready bootloader with full UDS diagnostic protocol support**

[Features](#-key-features) • [Architecture](#-architecture-overview) • [Services](#-uds-services) • [Tools](#-diagnostic-tools) • [Quick Start](#-quick-start) • [Documentation](#-documentation)

</div>

---

## 📋 Table of Contents

- [Overview](#-project-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture-overview)
  - [Bootloader Stack](#bootloader-stack)
  - [Layer Design](#three-layer-architecture)
  - [NVM Memory Stack](#nvm-memory-stack-autosar)
  - [Directory Structure](#directory-structure)
- [UDS Services](#-uds-services)
  - [Session Control (0x10)](#service-0x10---diagnostic-session-control)
  - [ECU Reset (0x11)](#service-0x11---ecu-reset)
  - [Read DID (0x22)](#service-0x22---read-data-by-identifier)
  - [Security Access (0x27)](#service-0x27---security-access)
  - [Write DID (0x2E)](#service-0x2e---write-data-by-identifier)
  - [Routine Control (0x31)](#service-0x31---routine-control)
  - [Tester Present (0x3E)](#service-0x3e---tester-present)
- [Security System](#-security-system)
- [Diagnostic Tools](#-diagnostic-tools)
  - [MinTool](#mintool---gui-diagnostic-application)
  - [SecurityUnlock](#securityunlock---key-calculator)
- [Configuration](#-configuration)
- [Build & Deploy](#-build--deployment)
- [Testing](#-testing)
- [Development](#-development-guide)
- [References](#-references)

---

## 🎯 Project Overview

**GachBoot** is an automotive-grade bootloader for STM32H743 microcontroller, implementing the complete **UDS (Unified Diagnostic Services)** protocol stack according to **ISO 14229-1** standard. The project combines embedded firmware with modern Python tooling for a complete diagnostic solution.

### Why GachBoot?

- ✅ **ISO 14229-1 Compliant** - Full UDS protocol implementation
- ✅ **AUTOSAR-Inspired** - Industry-standard architecture (DSL/DSP layers)
- ✅ **Production-Ready** - Session management, security, error handling
- ✅ **Modular Design** - Easy to extend with new services/DIDs/RIDs
- ✅ **Modern Tooling** - Python GUI with automation support
- ✅ **Well-Documented** - Comprehensive inline documentation

---

## ✨ Key Features

### Firmware Features
| Feature | Description |
|---------|-------------|
| **UDS Protocol Stack** | 7 diagnostic services (0x10, 0x11, 0x22, 0x27, 0x2E, 0x31, 0x3E) |
| **Session Management** | Default, Programming, Extended Diagnostic modes |
| **Security Access** | Multi-level (Level 1/2) with pluggable algorithms |
| **NVM Module** | AUTOSAR 4-layer memory stack (NvM → MemIf → Fee → Fls) |
| **Block Management** | NATIVE/REDUNDANT types with CRC32 validation |
| **Wear Leveling** | 2-sector ping-pong strategy (256KB flash) |
| **MIN Protocol** | Lightweight transport layer over UART |
| **Registry System** | Configurable DIDs, RIDs with access control |
| **Timing Control** | P2/P2*/S3 timeout management |
| **Pending Support** | Non-blocking operations with NRC 0x78 |

### Tool Features
| Feature | Description |
|---------|-------------|
| **MinTool GUI** | Modern tkinter-based diagnostic application |
| **One-Click Security** | Auto seed/key handling with callback system |
| **Script Automation** | Text-based scripting with SA command |
| **Live Logging** | TX/RX monitoring with timestamps |
| **Configuration** | JSON-based settings for easy customization |
| **Standalone Exe** | Portable executables for Windows |

---

## 🏗️ Architecture Overview

### Bootloader Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│              (UDS Service Handlers 0x10-0x3E)           │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────┐
│              DCMDSP (Service Processor)                  │
│   • Service routing & dispatch                          │
│   • Positive/negative response building                 │
│   • Pending request management (NRC 0x78)               │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────┐
│              DCMDSL (Session Layer)                      │
│   • Session management (Default/Prog/Extended)          │
│   • Security state tracking                             │
│   • S3 timeout monitoring (5 seconds)                   │
│   • Timing parameter control (P2/P2*)                   │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────┐
│              DCMDSD (Transport Dispatcher)               │
│   • Request queuing & forwarding                        │
│   • Response transmission                               │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────┐
│                  MIN Protocol Layer                      │
│   • Framing (8-bit ID + payload + CRC-8)                │
│   • UART transport                                      │
└─────────────────────────────────────────────────────────┘
```

### Three-Layer Architecture

**Inspired by AUTOSAR DCM Module:**

1. **Session Layer (DSL)**
   - Maintains diagnostic session state
   - Monitors S3 timeout (5 seconds)
   - Resets security on session change
   - Provides timing parameters

2. **Service Processor (DSP)**
   - Routes requests to service handlers
   - Builds positive/negative responses
   - Handles pending operations (0x78)
   - Validates service support

3. **Service Handlers**
   - Implements service-specific logic
   - Validates session/security requirements
   - Accesses DID/RID registries
   - Returns standardized responses

---

### NVM Memory Stack (AUTOSAR)

**Four-layer architecture for non-volatile memory management:**

```
┌─────────────────────────────────────────────────────────┐
│                   NvM (NV Manager)                       │
│   • Block management (NATIVE/REDUNDANT)                 │
│   • CRC32 validation & inline storage                   │
│   • RAM mirrors for fast read access                    │
│   • Power-loss protection                               │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────┐
│            MemIf (Memory Abstraction Interface)          │
│   • AUTOSAR routing layer                               │
│   • Device-agnostic API                                 │
│   • Job status tracking                                 │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────┐
│              Fee (Flash EEPROM Emulation)                │
│   • Logical sector management                           │
│   • Dynamic address allocation                          │
│   • Wear leveling (2-sector ping-pong)                  │
│   • Automatic sector switching                          │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────┐
│              Fls (Flash Hardware Driver)                 │
│   • STM32H7 flash operations (read/write/erase)         │
│   • 32-byte write alignment & padding                   │
│   • Sector boundary protection                          │
│   • 128KB sector management                             │
└─────────────────────────────────────────────────────────┘
```

#### NVM Block Configuration

**Supported Block Types:**

| Block ID | Name | Type | Length | Description |
|----------|------|------|--------|-------------|
| `0x0001` | VIN | REDUNDANT | 17 bytes | Vehicle Identification Number (2 copies) |
| `0x0002` | ECU Serial | REDUNDANT | 4 bytes | ECU serial number (2 copies) |
| `0x0003` | Fingerprint | NATIVE | 32 bytes | Programming fingerprint (single copy) |
| `0x0004` | Boot SW | NATIVE | 11 bytes | Bootloader software ID |
| `0x0005` | App SW | NATIVE | 10 bytes | Application software ID |
| `0x0006` | Prog Date | REDUNDANT | 4 bytes | Programming date (2 copies) |

**Memory Layout (STM32H743 Bank 2):**

```
Flash Bank 2: 0x08100000 - 0x081FFFFF (1MB)
NVM Sectors:  0x081C0000 - 0x081FFFFF (256KB, 2x 128KB sectors)

Sector A: 0x081C0000 - 0x081DFFFF (128KB)
Sector B: 0x081E0000 - 0x081FFFFF (128KB)

Wear Leveling: Ping-pong between Sector A ↔ Sector B
```

**Key Features:**

✅ **Automatic Redundancy** - REDUNDANT blocks write 2 copies with independent CRCs  
✅ **Dynamic Addressing** - Fee allocates addresses, NvM tracks per block  
✅ **Fast Reads** - NvM maintains RAM mirrors (no flash access)  
✅ **Wear Leveling** - Automatic sector switching when full (>127KB used)  
✅ **Power-Loss Protection** - Inline CRC32 after each write  
✅ **Alignment Handling** - Fls auto-pads writes to 32-byte boundaries with 0xFF  

**Code Flow Documentation:** See [NVM_CODE_FLOW.md](./NVM_CODE_FLOW.md) for detailed write/read/erase flows

---

### Directory Structure

```
Boot/
├── 📁 Core/                          # STM32 HAL & system init
│   ├── Inc/                          # System headers
│   └── Src/                          # Startup & main
│
├── 📁 Drivers/                       # STM32H7 HAL & CMSIS
│   ├── STM32H7xx_HAL_Driver/        # HAL drivers
│   └── CMSIS/                        # ARM CMSIS headers
│
├── 📁 components/                    # Reusable components
│   ├── dev_app/                      # Device abstraction layer
│   │   ├── include/                  # Common headers
│   │   └── dev_common.c              # Logging, delays, etc.
│   ├── dev_nvm/                      # Non-Volatile Memory Manager
│   │   ├── dev_nvm.c/.h             # Block management, CRC, redundancy
│   │   └── include/dev_nvm_config.h  # Block configuration
│   ├── dev_memif/                    # Memory Abstraction Interface (AUTOSAR MemIf)
│   │   └── dev_memif.c/.h           # Routing layer for memory devices
│   ├── dev_fee/                      # Flash EEPROM Emulation (AUTOSAR Fee)
│   │   ├── dev_fee.c/.h             # Sector management, wear leveling
│   │   └── include/dev_fee_config.h  # Sector configuration
│   └── dev_fls/                      # Flash Driver (AUTOSAR Fls)
│       ├── dev_fls.c/.h             # STM32H7 flash hardware operations
│       └── include/dev_fls_config.h  # Flash memory layout
│
├── 📁 service/                       # UDS services
│   └── svc_dcm/                      # Diagnostic Communication Manager
│       ├── 📄 svc_dcm.c/.h          # DCM main interface
│       ├── dcmdsl/                   # Session Layer
│       ├── dcmdsp/                   # Service Processor
│       ├── dcmdsd/                   # Transport Dispatcher
│       └── uds_services/             # Service implementations
│           ├── service_0x10/         # Session Control
│           ├── service_0x11/         # ECU Reset
│           ├── service_0x22/         # Read DID
│           ├── service_0x27/         # Security Access
│           ├── service_0x2E/         # Write DID
│           ├── service_0x31/         # Routine Control
│           └── service_0x3E/         # Tester Present
│
└── 📁 Tool/                          # Python diagnostic tools
    ├── 📄 MinTool_modular.py        # GUI app entry point
    ├── config/                       # Configuration management
    ├── core/                         # MIN protocol handler
    ├── ui/                           # GUI windows & dialogs
    ├── utils/                        # Automation & helpers
    └── SecurityUnlock/               # Key calculator
        ├── SecurityUnlock.py         # CLI tool
        ├── algorithms/               # Pluggable algorithms
        └── dist/SecurityUnlock.exe   # Standalone executable
```

---

## 🛠️ UDS Services

### Service 0x10 - Diagnostic Session Control

**Control diagnostic session modes.**

#### Supported Sessions
| Session | ID | Description | P2 | P2* |
|---------|-------|-------------|-----|-----|
| Default | `0x01` | Standard mode | 50ms | 5000ms |
| Programming | `0x02` | Flash programming | 50ms | 5000ms |
| Extended Diagnostic | `0x03` | Advanced diagnostics | 50ms | 5000ms |

#### Features
- ✅ Automatic S3 timeout reset on session change
- ✅ Security level reset (except Default → Programming)
- ✅ Timing parameter configuration

#### Example
```
Request:  10 02           # Switch to Programming Session
Response: 50 02 00 32 01 F4  # Success (P2=50ms, P2*=5000ms)
```

---

### Service 0x11 - ECU Reset

**Reset the ECU with various modes.**

#### Reset Types
| Sub-Function | ID | Description | Security Required |
|--------------|-----|-------------|-------------------|
| Hard Reset | `0x01` | System reset | Programming: Yes<br>Extended: No |
| Key Off/On Reset | `0x02` | Simulated power cycle | Programming: Yes<br>Extended: No |
| Soft Reset | `0x03` | Soft restart | No |
| Enable Rapid Shutdown | `0x04` | Enable quick power-down | No |
| Disable Rapid Shutdown | `0x05` | Disable quick power-down | No |

#### Features
- ✅ 1 second power-down time before reset
- ✅ Session validation (not allowed in Default)
- ✅ Security enforcement for Programming session
- ✅ Safe scheduled reset (response sent before reset)

#### Example
```
Request:  11 01           # Hard Reset
Response: 51 01           # Success (reset in 1 second)
```

---

### Service 0x22 - Read Data By Identifier

**Read diagnostic data from ECU.**

#### Implemented DIDs
| DID | Name | Length | Session | Security | Description |
|-----|------|--------|---------|----------|-------------|
| `0xF190` | VIN | 17 bytes | All | All | Vehicle Identification Number |
| `0xF183` | Boot SW ID | 11 bytes | All | All | Bootloader software ID |
| `0xF184` | App SW ID | 10 bytes | All | All | Application software ID |
| `0xF18C` | ECU Serial | 4 bytes | Default/Extended | All | ECU serial number |

#### Features
- ✅ Multiple DID support in single request
- ✅ Session-based access control
- ✅ Security-based access control
- ✅ Fixed/variable length DIDs

#### Example
```
Request:  22 F1 90                # Read VIN
Response: 62 F1 90 [17 bytes]     # VIN data
```

---

### Service 0x27 - Security Access

**Unlock security levels for protected operations.**

#### Security Levels
| Level | ID (Seed/Key) | Algorithm | Seed Size | Key Size | Sessions | Lockout |
|-------|---------------|-----------|-----------|----------|----------|---------|
| Level 1 | `0x01`/`0x02` | XOR U32 | 4 bytes | 4 bytes | Programming/Extended | 10s |
| Level 2 | `0x03`/`0x04` | XOR U64 | 8 bytes | 8 bytes | Programming | 30s |

#### Algorithm Details

**Level 1 (XOR U32):**
```c
key = seed XOR 0x12345678
```

**Level 2 (XOR U64):**
```c
key = seed XOR 0x123456789ABCDEF0
```

#### Features
- ✅ Attempt counter (max 3 attempts)
- ✅ Lockout timer after failed attempts
- ✅ Automatic reset on session change/timeout
- ✅ Crypto-grade seed generation (based on RNG)

#### Example
```
Request:  27 01                   # Request seed Level 1
Response: 67 01 DE AD 94 AB       # Seed: DEAD94AB

# Calculate key: DEAD94AB XOR 12345678 = CC99C2D3

Request:  27 02 CC 99 C2 D3       # Send key
Response: 67 02                   # Security unlocked!
```

---

### Service 0x2E - Write Data By Identifier

**Write configuration data to ECU.**

#### Implemented DIDs
| DID | Name | Length | Session | Security | Description |
|-----|------|--------|---------|----------|-------------|
| `0xF15A` | Fingerprint | 1-32 bytes | Programming/Extended | Level 1 or 2 | Programming fingerprint |
| `0xF199` | Programming Date | 4 bytes | Programming | Level 2 | Date of last programming |
| `0xF100` | ECU Config | 2 bytes | Extended | Level 1 or 2 | ECU configuration value |

#### Features
- ✅ Fixed/variable length validation
- ✅ Session enforcement
- ✅ Security enforcement
- ✅ Semantic data validation

#### Example
```
Request:  2E F1 00 12 34          # Write ECU config = 0x1234
Response: 6E F1 00                # Success
```

---

### Service 0x31 - Routine Control

**Execute diagnostic routines.**

#### Implemented Routines
| RID | Name | Sub-Functions | Session | Security | Description |
|-----|------|---------------|---------|----------|-------------|
| `0xFF00` | Erase Memory | Start, Results | Programming | Level 1 or 2 | Flash erase operation |
| `0xFF01` | Check Dependencies | Start | Programming | Level 1 or 2 | Pre-programming checks |
| `0x0202` | Check Memory | Start | Extended/Programming | All | CRC/checksum verification |

#### Sub-Functions
| ID | Name | Description |
|----|------|-------------|
| `0x01` | Start Routine | Begin routine execution |
| `0x02` | Stop Routine | Stop running routine |
| `0x03` | Request Results | Get routine status/results |

#### Features
- ✅ Session/security validation
- ✅ Option record parsing
- ✅ Status record generation
- ✅ Pending operation support

#### Example
```
Request:  31 01 FF 00 08 00 00 00 00 01 00 00  # Erase 64KB at 0x08000000
Response: 71 01 FF 00 00                        # Success (Status: 0x00)
```

---

### Service 0x3E - Tester Present

**Keep diagnostic session alive.**

#### Features
- ✅ Suppress response bit support (`0x80`)
- ✅ Prevents S3 timeout
- ✅ Silent operation (logs disabled)
- ✅ Works in all sessions

#### Example
```
Request:  3E 00           # Tester present
Response: 7E 00           # Acknowledged

Request:  3E 80           # Tester present (suppress response)
Response: (none)          # No response sent
```

---

## 🔐 Security System

### Multi-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│            Security Level Configuration              │
├─────────────────────────────────────────────────────┤
│  Level 1 (Programming Session)                      │
│  • Algorithm: XOR U32 (seed XOR 0x12345678)         │
│  • Seed: 4 bytes (32-bit)                           │
│  • Key: 4 bytes (32-bit)                            │
│  • Max attempts: 3                                  │
│  • Lockout: 10 seconds                              │
├─────────────────────────────────────────────────────┤
│  Level 2 (Extended Diagnostic)                      │
│  • Algorithm: XOR U64 (seed XOR 0x123456789ABCDEF0) │
│  • Seed: 8 bytes (64-bit)                           │
│  • Key: 8 bytes (64-bit)                            │
│  • Max attempts: 3                                  │
│  • Lockout: 30 seconds                              │
└─────────────────────────────────────────────────────┘
```

### Design Patterns

**Factory + Strategy Pattern:**
- Abstract algorithm interface (`SecurityAlgorithm`)
- Factory for algorithm instantiation (`AlgorithmFactory`)
- Configuration-driven algorithm selection
- Easy to add new algorithms without code changes

### Adding New Security Level

1. **Create algorithm class:**
   ```python
   class CustomAlgorithm(SecurityAlgorithm):
       def calculate_key(self, seed: bytes) -> bytes:
           # Your algorithm here
           return key
   ```

2. **Register in config.py:**
   ```python
   SECURITY_LEVELS = {
       0x05: {
           'algorithm': 'custom',
           'config': {'param': value},
           'description': 'Custom security'
       }
   }
   ```

3. **Update ECU firmware:**
   ```c
   // In uds_security_config.c
   static Std_ReturnType security_compare_key_level_5(...) {
       // Match algorithm from Python tool
   }
   ```

---

## 🖥️ Diagnostic Tools

### MinTool - GUI Diagnostic Application

<div align="center">

**Modern Python GUI for UDS diagnostics**

</div>

#### Architecture

```
MinTool_modular.py (Entry Point)
    │
    ├── 📁 config/
    │   └── config_manager.py       # JSON configuration
    │
    ├── 📁 core/
    │   └── min_handler.py          # MIN protocol with callbacks
    │
    ├── 📁 ui/
    │   ├── main_window.py          # Main application (387 lines)
    │   ├── config_dialog.py        # Settings dialog (381 lines)
    │   └── security_dialog.py      # One-click unlock (264 lines)
    │
    └── 📁 utils/
        └── automation.py           # Script runner (220+ lines)
```

#### Key Features

**1. UDS Communication**
- Send raw hex commands: `22 F1 90`
- Auto positive/negative response parsing
- NRC decoding with descriptions
- Live TX/RX logging with timestamps

**2. One-Click Security Unlock**
```
Click "Unlock Security Level 1"
    ↓
Auto send: 27 01 (Request seed)
    ↓
Receive: 67 01 [seed]
    ↓
Calculate key using SecurityUnlock.exe
    ↓
Auto send: 27 02 [key]
    ↓
Done! Security unlocked ✓
```

**3. Automation Scripting**

Create `.txt` scripts with simple commands:

```txt
# Switch to programming session
10 02
DELAY 100

# Unlock security
SA 01

# Erase flash
31 01 FF 00 08000000 00010000

# Verify
31 03 FF 00
```

**Commands:**
- `DELAY <ms>` - Wait specified milliseconds
- `SA <level>` or `SECURITY_UNLOCK <level>` - Auto security unlock
- `<hex>` - Send UDS command

**4. Configuration Management**

JSON-based settings:
```json
{
  "default_min_id": "0x01",
  "tester_present_enabled": true,
  "tester_present_interval_ms": 2000,
  "security_exe_path": "Tool/SecurityUnlock/dist/SecurityUnlock.exe",
  "security_levels": [
    {"level": 1, "name": "Programming", "color": "lightblue"},
    {"level": 2, "name": "Extended", "color": "lightgreen"}
  ]
}
```

#### UI Features
- 📊 Real-time session/security status
- 🎨 Color-coded responses (green=positive, red=negative)
- 📝 TX/RX log with timestamps
- 🔌 COM port selection with auto-refresh
- ⚡ Baudrate presets (115200-921600)
- 🔄 Auto tester present

---

### SecurityUnlock - Key Calculator

<div align="center">

**Standalone CLI tool for security key calculation**

</div>

#### Architecture

```
SecurityUnlock/
├── SecurityUnlock.py          # CLI entry point
├── config.py                  # Level → algorithm mapping
├── algorithms/
│   ├── base.py               # Abstract base class
│   ├── factory.py            # Factory pattern
│   ├── xor_u32.py           # Level 1 algorithm
│   └── xor_u64.py           # Level 2 algorithm
└── dist/
    └── SecurityUnlock.exe    # Portable executable (~7MB)
```

#### Usage

```bash
# Level 1 (32-bit)
> SecurityUnlock.exe 0x01 DEAD94AB
CC99C2D3

# Level 2 (64-bit)
> SecurityUnlock.exe 0x02 CAFEBABE12345678
D98AECCED88AA988

# Default to Level 1
> SecurityUnlock.exe DEAD94AB
CC99C2D3
```

#### Integration with MinTool

MinTool automatically calls SecurityUnlock.exe via subprocess:
```python
# In automation.py
result = subprocess.run(
    [security_exe_path, hex(level), seed_hex],
    capture_output=True, text=True, timeout=5
)
key = result.stdout.strip()
```

---

## ⚙️ Configuration

### Bootloader Configuration

**Session Timing (svc_dcm.h):**
```c
#define UDS_S3_SERVER_TIMEOUT_MS    5000u   // S3 timeout
#define UDS_P2_SERVER_MAX_MS        50u     // P2 time
#define UDS_P2_STAR_SERVER_MAX_MS   5000u   // P2* time
```

**Security Configuration (uds_security_config.c):**
```c
static const dcm_security_level_config_t security_level_config[] = {
    // Level  Seed SubF  Key SubF  SeedSize  KeySize  Attempts  Delay  SessionMask  ...
    {1,       0x01,      0x02,     4,        4,       3,        10000, PROG|EXT, ...},
    {2,       0x03,      0x04,     8,        8,       3,        30000, PROG,     ...},
};
```

### MinTool Configuration

**mintool_config.json:**
```json
{
  "default_min_id": "0x01",
  "tester_present_enabled": true,
  "tester_present_interval_ms": 2000,
  "tester_present_suppress_response": true,
  "security_exe_path": "Tool/SecurityUnlock/dist/SecurityUnlock.exe",
  "automation_script_path": "Tool/automation_example.txt",
  "security_levels": [
    {
      "level": 1,
      "name": "Programming Session",
      "color": "lightblue"
    },
    {
      "level": 2,
      "name": "Extended Diagnostic",
      "color": "lightgreen"
    }
  ]
}
```

### SecurityUnlock Configuration

**config.py:**
```python
SECURITY_LEVELS = {
    0x01: {
        'algorithm': 'xor_u32',
        'config': {
            'xor_value': 0x12345678,  # Must match ECU!
        },
        'description': 'Programming session security'
    },
    0x02: {
        'algorithm': 'xor_u64',
        'config': {
            'xor_value': 0x123456789ABCDEF0,  # Must match ECU!
        },
        'description': 'Extended diagnostic security'
    }
}
```

---

## 🔨 Build & Deployment

### Prerequisites

**For Bootloader:**
- CMake 3.20+
- ARM GCC toolchain
- ST-Link debugger

**For Tools:**
- Python 3.13+
- pip packages: `pyserial`, `Pillow`, `PyInstaller`

### Build Bootloader

```bash
# Configure
cd Boot
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# Build
cmake --build build

# Flash to STM32H743
# Use ST-Link Utility or OpenOCD
st-flash write build/Boot.bin 0x08000000
```

### Build MinTool

```bash
cd Tool
python build_mintool.bat

# Output: dist/MinTool.exe (~15MB)
```

### Build SecurityUnlock

```bash
cd Tool/SecurityUnlock
python build.bat

# Output: dist/SecurityUnlock.exe (~7MB)
```

---

## 🧪 Testing

### Manual Testing with MinTool

**Basic Flow:**
1. Connect ECU via UART (default: 115200 baud)
2. Launch `MinTool.exe`
3. Select COM port → Connect
4. Test sequence:

```
10 03           # Switch to Extended session
✓ 50 03 ...     # Success

27 01           # Request seed Level 1
✓ 67 01 [seed]  # Seed received

27 02 [key]     # Send key (or use Security dialog)
✓ 67 02         # Unlocked!

22 F190         # Read VIN
✓ 62 F190 ...   # VIN data

2E F100 1234    # Write ECU config
✓ 6E F100       # Written

11 01           # Hard reset
✓ 51 01         # Reset scheduled
```

### Automation Testing

**Create test script (`test.txt`):**
```txt
# Test script for GachBoot
10 02
DELAY 100
SA 01
DELAY 500
22 F183
22 F184
22 F190
31 01 FF 01
DELAY 2000
31 03 FF 01
```

**Run in MinTool:**
1. Tools → Load Automation Script
2. Select `test.txt`
3. Click Run
4. Watch execution in log

### Unit Testing

**SecurityUnlock tests:**
```bash
cd Tool/SecurityUnlock
python test_security.py

# Output:
# test_xor_u32_algorithm ... ok
# test_xor_u64_algorithm ... ok
# test_factory_creation ... ok
# ... (9/9 tests passing) ✓
```

---

## 👨‍💻 Development Guide

### Code Style

**C Firmware:**
```c
// Use snake_case
void uds_service_handler(const uint8_t *data);

// Logging with tags
CONFIG_LOG_TAG(UDS_0x22, true)
DBG_OUT_I("Info: DID=0x%04X", did);
DBG_OUT_W("Warning: NRC=0x%02X", nrc);
DBG_OUT_E("Error: %s", message);

// File naming: module_submodule.c
uds_service_0x22.c
uds_rdbi_did_registry.c
```

**Python Tools:**
```python
# Use PEP 8
class ConfigManager:
    def load_config(self):
        pass

# Logging
logging.info("Message")
logging.warning("Warning")
logging.error("Error")
```

### Adding New UDS Service

1. **Create service folder:**
   ```
   service/svc_dcm/uds_services/service_0xXX/
   ├── uds_service_0xXX.h
   ├── uds_service_0xXX.c
   └── uds_xx_registry.h/.c (if needed)
   ```

2. **Implement handler:**
   ```c
   Std_ReturnType uds_service_0xXX_handler(
       const uds_message_t *message,
       uint8_t *error_code
   );
   ```

3. **Register in DCMDSP:**
   ```c
   // dcmdsp.c
   #include "uds_services/service_0xXX/uds_service_0xXX.h"
   
   static const uds_service_entry_t service_table[] = {
       // ...
       {UDS_SID_YOUR_SERVICE, uds_service_0xXX_handler},
   };
   ```

4. **Add SID constant:**
   ```c
   // svc_dcm.h
   #define UDS_SID_YOUR_SERVICE    0xXX
   ```

### Adding New DID

**For Read (0x22):**

1. Add to `uds_rdbi_did_registry.c`:
```c
static const uds_did_entry_t rdbi_did_registry[] = {
    // DID      ExpLen  Callback        LengthGetter  SessionMask  SecurityMask
    {0xF1XX,    10,     did_read_data,  NULL,         SESSION_ALL, SECURITY_ALL},
};
```

2. Implement callback:
```c
static Std_ReturnType did_read_data(uint8_t *data) {
    // Fill data buffer
    return E_OK;
}
```

**For Write (0x2E):**

1. Add to `uds_wdbi_did_registry.c`:
```c
{0xF1XX, 4, 0, 0, did_write_data, UDS_SESSION_MASK_EXTENDED, UDS_SECURITY_MASK_LEVEL_1},
```

2. Implement callback:
```c
static Std_ReturnType did_write_data(const uint8_t *data, uint16_t len) {
    // Process data
    return E_OK;
}
```

### Adding New Routine

1. Add to `uds_routine_control_registry.c`:
```c
{0xXXXX, routine_handler, UDS_SESSION_MASK_PROGRAMMING, UDS_SECURITY_MASK_LEVEL_1},
```

2. Implement callback:
```c
static Std_ReturnType routine_handler(
    uint8_t sub_function,
    const uint8_t *option_record, uint16_t option_len,
    uint8_t *status_record, uint16_t *status_len
) {
    if (sub_function == UDS_ROUTINE_CONTROL_START) {
        // Execute routine
        *status_len = 1;
        status_record[0] = 0x00;  // Success
        return E_OK;
    }
    return E_NOT_OK;
}
```

---

## 📚 References

### Standards & Specifications

| Document | Title | Description |
|----------|-------|-------------|
| **ISO 14229-1** | UDS - Part 1: Application Layer | Service definitions, NRCs, timing |
| **ISO 14229-2** | UDS - Part 2: Session Layer | Session management, security |
| **AUTOSAR DCM** | Diagnostic Communication Manager | Architecture reference |

### MIN Protocol

- **Framing:** `ID (1 byte) + Length (1 byte) + Payload (0-255) + CRC-8`
- **Advantages:** Lightweight, simple, reliable
- **Use case:** Embedded diagnostics over UART

### Useful Resources

- [ISO 14229 Overview](https://www.iso.org/standard/72439.html)
- [AUTOSAR Documentation](https://www.autosar.org/)
- [STM32H743 Reference Manual](https://www.st.com/resource/en/reference_manual/rm0433-stm32h742-stm32h743753-and-stm32h750-value-line-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)

---

## 🎯 Project Status

### ✅ Completed Features

- [x] **Core Services:** 0x10, 0x11, 0x22, 0x27, 0x2E, 0x31, 0x3E
- [x] **Session Management:** Default/Programming/Extended with S3 timeout
- [x] **Security System:** Multi-level with pluggable algorithms
- [x] **NVM Module:** AUTOSAR-compliant 4-layer memory stack (NvM → MemIf → Fee → Fls)
  - Block management with CRC32 validation
  - NATIVE/REDUNDANT block types with automatic redundancy
  - Wear leveling with 2-sector ping-pong strategy
  - Dynamic address allocation with Fee sector management
  - RAM mirrors for fast read access
  - Power-loss protection with inline CRC
- [x] **MinTool GUI:** Full-featured diagnostic application
- [x] **SecurityUnlock:** Standalone key calculator
- [x] **Automation:** Script runner with SA command
- [x] **Registry System:** Configurable DIDs/RIDs with access control
- [x] **Transport Layer:** MIN protocol over UART
- [x] **Documentation:** Comprehensive inline and README docs

### 🔄 Future Enhancements

- [ ] **Service 0x34/0x36/0x37:** Request Download, Transfer Data, Transfer Exit
- [ ] **Flash Programming:** Complete bootloader download flow
- [ ] **CAN Transport:** UDS over CAN-TP (ISO 15765)
- [ ] **Secure Boot:** Signature verification
- [ ] **HSM Integration:** Hardware security module support
- [ ] **Bootloader Update:** Self-upgrade capability
- [ ] **Multi-session Downloads:** Parallel programming support

---

## 📄 License

This project is developed for **educational and automotive diagnostics purposes**.

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Follow existing code style (AUTOSAR naming, logging patterns)
4. Test thoroughly (firmware + tools)
5. Commit changes (`git commit -m 'Add AmazingFeature'`)
6. Push to branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

---

## 👨‍💻 Author

**Thanh Tran**

- 🌐 GitHub: [@tranthanh1699](https://github.com/tranthanh1699)
- 📧 Email: tranthanh1699@example.com
- 📦 Repository: [GachBoot](https://github.com/tranthanh1699/GachBoot)

---

## 🙏 Acknowledgments

- **STMicroelectronics** - STM32H7 HAL drivers
- **ISO/SAE** - UDS standard specification
- **AUTOSAR** - DCM architecture inspiration
- **Python Community** - tkinter, pyserial, PyInstaller

---

<div align="center">

**⭐ Star this repository if you find it useful! ⭐**

**Made with ❤️ for automotive diagnostics**

[Back to Top ↑](#-gachboot---professional-stm32h743-bootloader)

</div>
