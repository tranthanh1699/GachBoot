# MinTool - UDS Diagnostic Tool

## Overview
MinTool is a Python-based GUI application for sending UDS (Unified Diagnostic Services) requests over UART using the MIN protocol.

## Features

### 1. Basic Communication
- Connect to UART ports with configurable baudrate
- Send/receive UDS messages with MIN protocol
- Real-time message logging with timestamps
- Tester Present auto-enable via configuration

### 2. Configuration (Config Menu)
Access via **Config → Settings**

#### Configurable Parameters:
- **Default MIN ID**: The default MIN protocol ID (0-63)
- **Tester Present Interval**: Auto-send interval in milliseconds (100-60000ms)
- **Enable Tester Present on Connect**: Auto-start tester present when connecting
- **Suppress Positive Response**: Use 3E 80 instead of 3E 00
- **Security Access EXE**: Path to external executable for key calculation
- **Automation Script**: Path to TXT file containing automation commands

Configuration is saved to `mintool_config.json` in the application directory.

### 3. Security Access Tool (Tools Menu)
Access via **Tools → Security Access (0x27)**

#### Features:
- **Request Seed**: Automatically sends `27 01` to request seed
- **Calculate Key**: Runs external EXE to calculate key from seed
- **Send Key**: Automatically sends `27 02 <key>` to unlock security level

#### EXE Requirements:
The external security access executable must:
1. Accept seed as command line argument (hex string)
2. Output key to stdout (hex string)
3. Return exit code 0 on success

Example:
```
SecurityCalc.exe 0102030405060708
> AABBCCDDEEFF0011
```

### 4. Automation Script (Tools Menu)
Access via **Tools → Run Automation Script**

#### Script Format (TXT file):
```
# Lines starting with # are comments
# Use DELAY <milliseconds> for delays
# Other lines are hex data to send (spaces optional)

10 03          # Enter Extended Session
DELAY 100      # Wait 100ms
27 01          # Request Seed
DELAY 500      # Wait 500ms
22 F1 90       # Read DID F190
```

#### Commands:
- **HEX data**: Any hex string (e.g., `10 03`, `22F190`)
- **DELAY**: `DELAY <milliseconds>` - pause execution
- **Comments**: Lines starting with `#` are ignored
- **Empty lines**: Ignored

## Usage

### Quick Start
1. Launch MinTool.py
2. Select COM port and baudrate
3. Click **Connect**
4. Enter hex data in the input field
5. Click **Send** or press Enter

### Configuration
1. Go to **Config → Settings**
2. Set default MIN ID and baudrate
3. Configure Security Access EXE path
4. Configure Automation Script path
5. Click **Save**

### Security Access Workflow
1. Connect to device
2. Go to **Tools → Security Access**
3. Click **Request Seed** (sends `27 01`)
4. Wait for response in log (e.g., `67 01 <seed>`)
5. Copy seed to input field
6. Click **Calculate & Send Key**
7. Check log for positive response (`67 02`)

### Automation Script Workflow
1. Create TXT file with commands (see `automation_example.txt`)
2. Go to **Config → Settings**
3. Set **Automation Script Path**
4. Click **Save**
5. Connect to device
6. Go to **Tools → Run Automation Script**
7. Monitor execution in log window

## File Structure
```
Tool/
├── MinTool.py                  # Main application
├── min.py                      # MIN protocol library
├── mintool_config.json         # Configuration file (auto-generated)
├── automation_example.txt      # Example automation script
└── README_MinTool.md          # This file
```

## Configuration File Format
```json
{
    "default_min_id": 16,
    "default_baudrate": "115200",
    "security_exe_path": "C:/path/to/SecurityCalc.exe",
    "automation_script_path": "C:/path/to/script.txt"
}
```

## Log Color Coding
- **Orange**: TX (Transmitted messages)
- **Blue**: RX (Received messages)
- **Green**: Info messages
- **Red**: Error messages

## Keyboard Shortcuts
- **Enter**: Send data from input field

## Tips
1. Use **Tester Present** to keep the session alive during diagnostics
2. Use `3E 80` for suppress positive response (reduces log noise)
3. MIN ID must be between 0 and 63 (0x00-0x3F)
4. Always clear log before starting new test session
5. Automation scripts run in background - don't disconnect during execution

## Troubleshooting

### "Not connected to any port"
- Check if device is connected
- Try **Refresh Ports** button
- Verify correct COM port and baudrate

### "Security Access EXE failed"
- Check EXE path in Config
- Verify EXE accepts seed as argument
- Test EXE manually from command line

### "Script file not found"
- Check script path in Config
- Verify file exists and has .txt extension
- Use absolute path or place in same folder as MinTool.py

### No response from device
- Check **Tester Present** to maintain session
- Verify MIN ID matches device configuration
- Check baudrate matches device settings

## Requirements
- Python 3.x
- tkinter (usually included with Python)
- pyserial
- MIN protocol library (min.py)

## Installation
```bash
pip install pyserial
```

## License
Part of GachBoot project - Automotive Bootloader for STM32H743

---
Last Updated: December 1, 2025
